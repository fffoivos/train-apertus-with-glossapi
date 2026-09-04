#!/usr/bin/env python3
"""Export (1) a ground-truth candidate pool and (2) the core annotation subset as jsonl, one row = {source, bucket, id, user, assistant, meta}.
Reads evenly spaced parquet shards (source-ordered datasets) and streaming splits. CPU only.
Usage: python3 export_core.py <out_dir>"""
import json, sys, os, random, time, collections
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download
from datasets import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'vantage_scan.py')).read(); exec(src[:src.index('SOURCES = [')])  # text_of, assistant_text, user_text
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); random.seed(2026); api = HfApi()
ONLY = set(os.environ.get('ONLY', '').split(',')) - {''}  # re-export only these blocks, then rebuild gt_pool
THIN = float(os.environ.get('THIN', '0.6'))  # keep probability per matching row; 1.0 takes rows in shard order until the target

# block -> (repo, bucket column, wanted bucket values, target rows, shards to read)
BLOCKS = {
 'dolci_chat':    ('allenai/Dolci-Instruct-SFT', 'domain', {'Chat'}, 20000, 24),
 'dolci_tooluse': ('allenai/Dolci-Instruct-SFT', 'domain', {'Tool Use'}, 40000, 24),
 'dolci_safety':  ('allenai/Dolci-Instruct-SFT', 'domain', {'Safety'}, 20000, 24),
 'dolci_other':   ('allenai/Dolci-Instruct-SFT', 'domain', {'Other'}, 20000, 24),
 'dolci_science': ('allenai/Dolci-Instruct-SFT', 'domain', {'Science'}, 20000, 15),
 'dolci_code_algo': ('allenai/Dolci-Instruct-SFT', 'source_dataset', {'Dolci Instruct Python Algorithms'}, 60000, 15),
 'dolci_reasoning': ('allenai/Dolci-Instruct-SFT', 'source_dataset', {'Verifiable Reasoning'}, 30000, 15),
 'dolci_precise_if': ('allenai/Dolci-Instruct-SFT', 'domain', {'Precise IF'}, 137000, 15),
 'dolci_code_algo_sample': ('allenai/Dolci-Instruct-SFT', 'source_dataset', {'Dolci Instruct Python Algorithms'}, 300, 15),
 'dolci_reasoning_sample': ('allenai/Dolci-Instruct-SFT', 'source_dataset', {'Verifiable Reasoning'}, 300, 15),
 'tulu_flan':     ('allenai/tulu-3-sft-mixture', 'source', {'ai2-adapt-dev/flan_v2_converted'}, 10000, 6),
 'tulu_wildchat': ('allenai/tulu-3-sft-mixture', 'source', {'ai2-adapt-dev/tulu_v3.9_wildchat_100k'}, 40000, 6),
}
STREAMS = {  # label -> (repo, config, split, target)
 'smoltalk2_magpie': ('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_smol_magpie_ultra_no_think', 40000),
 'smoltalk2_openhermes': ('HuggingFaceTB/smoltalk2', 'SFT', 'OpenHermes_2.5_no_think', 20000),
 'nemotron_chat': ('nvidia/Nemotron-SFT-Instruction-Following-Chat-v3', 'default', 'chat', 150000),
 'smoltalk2_multilingual': ('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_multilingual_8languages_lang_5_no_think', 25000),
}
def emit(fh, label, bucket, rid, row):
    u, a = user_text(row), assistant_text(row)
    msgs = row.get('messages')
    if isinstance(msgs, str):
        try: msgs = json.loads(msgs)
        except Exception: msgs = None
    turns = []
    if isinstance(msgs, list):
        for m in msgs:
            if not isinstance(m, dict): continue
            c = text_of(m.get('content'))
            if m.get('role') == 'system' and m.get('functions'): c = (c + '\n<functions> ' + str(m['functions'])[:1500] + ' </functions>').strip()
            if m.get('role') == 'assistant' and not c.strip() and m.get('function_calls'): c = 'TOOL_CALLS: ' + str(m['function_calls'])[:1500]
            if m.get('role') == 'assistant' and not c.strip() and m.get('tool_calls'): c = 'TOOL_CALLS: ' + json.dumps(m.get('tool_calls'), ensure_ascii=False)[:1500]
            if m.get('role') == 'assistant' and isinstance(m.get('content'), dict) and m['content'].get('blocks'):
                calls = [b for b in m['content']['blocks'] if isinstance(b, dict) and b.get('calls')]
                if calls and not c.strip(): c = 'TOOL_CALLS: ' + json.dumps(calls, ensure_ascii=False)[:1500]
            turns.append(dict(role=m.get('role'), content=c))
    if turns and not next((t['content'] for t in turns if t['role'] == 'user'), '').strip(): return False  # first user prompt missing (Nemotron chat: seed prompts withheld, 41%)
    if not a.strip(): a = next((t['content'] for t in reversed(turns) if t['role'] == 'assistant' and t['content'].strip()), '')
    if not u.strip(): u = next((t['content'] for t in turns if t['role'] == 'user' and t['content'].strip()), '')
    if not a.strip() or not u.strip(): return False
    fh.write(json.dumps(dict(source=label, bucket=bucket, id=str(rid), user=u, assistant=a, turns=turns, n_turns=len(turns) or 1), ensure_ascii=False) + '\n'); return True

# parquet blocks, grouped per repo so each shard is read once
by_repo = collections.defaultdict(list)
if ONLY: BLOCKS = {k: v for k, v in BLOCKS.items() if k in ONLY}; STREAMS = {k: v for k, v in STREAMS.items() if k in ONLY}
for label, (repo, col, vals, target, k) in BLOCKS.items(): by_repo[repo].append((label, col, vals, target, k))
counts = collections.Counter(); files_h = {label: open(f'{OUT}/{label}.jsonl', 'w') for label in BLOCKS}
for repo, specs in by_repo.items():
    files = sorted(f for f in api.list_repo_files(repo, repo_type='dataset') if f.endswith('.parquet') and 'train' in f)
    k = min(max(s[4] for s in specs), len(files)); pick = sorted(set(files[int(i * (len(files) - 1) / max(1, k - 1))] for i in range(k)))  # evenly spaced over ALL shards
    print(f'{repo}: {len(files)} files, reading {len(pick)}', flush=True); t0 = time.time()
    for f in pick:
        if all(counts[s[0]] >= s[3] for s in specs): break
        path = hf_hub_download(repo, f, repo_type='dataset'); pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            for row in pf.read_row_group(rg).to_pylist():
                for label, col, vals, target, _ in specs:
                    if counts[label] < target and row.get(col) in vals:
                        # thin uniformly so the target spreads across shards
                        if random.random() < THIN and emit(files_h[label], label, row.get(col), row.get('id') or row.get('conversation_id') or rg, row): counts[label] += 1
        print(f'  {f}: ' + ', '.join(f'{s[0]}={counts[s[0]]}' for s in specs) + f' ({round(time.time()-t0)}s)', flush=True)
for fh in files_h.values(): fh.close()
for label, (repo, cfg, split, target) in STREAMS.items():
    t0 = time.time(); n = 0
    with open(f'{OUT}/{label}.jsonl', 'w') as fh:
        try:
            for i, row in enumerate(load_dataset(repo, cfg, split=split, streaming=True)):
                if n >= target: break
                if random.random() < 0.5 and emit(fh, label, split, i, row): n += 1
        except Exception as e: print(label, 'ERROR', str(e)[:200], flush=True)
    print(f'{label}: {n} rows in {round(time.time()-t0)}s', flush=True)
# ground-truth candidate pool: 30 random rows per block, disjoint ids written to gt_pool.jsonl
with open(f'{OUT}/gt_pool.jsonl', 'w') as gt:
    for label in sorted(os.path.basename(f)[:-6] for f in os.listdir(OUT) if f.endswith('.jsonl') and f != 'gt_pool.jsonl'):
        rows = [l for l in open(f'{OUT}/{label}.jsonl')]
        random.shuffle(rows)
        for l in rows[:40]: gt.write(l)
print('DONE', flush=True)
