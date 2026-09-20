#!/usr/bin/env python3
"""Export (1) a ground-truth candidate pool and (2) the core annotation subset as jsonl, one row = {source, bucket, id, user, assistant, meta}.
Reads evenly spaced parquet shards (source-ordered datasets) and streaming splits. CPU only.
Usage: python3 export_core.py <out_dir>"""
import json, sys, os, random, time, collections, re
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download
from datasets import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'vantage_scan.py')).read(); exec(src[:src.index('SOURCES = [')])  # text_of, assistant_text, user_text
OUT = sys.argv[1]; random.seed(2026); api = HfApi()
ONLY = set(os.environ.get('ONLY', '').split(',')) - {''}  # re-export only these blocks, then rebuild gt_pool
THIN = float(os.environ.get('THIN', '0.6'))  # keep probability per matching row; 1.0 takes rows in shard order until the target
REVISION_FILE = os.environ.get('SOURCE_REVISIONS_FILE')
if not REVISION_FILE:
    raise SystemExit('SOURCE_REVISIONS_FILE is required (JSON object: dataset repo -> immutable 40-hex commit)')
with open(REVISION_FILE, encoding='utf-8') as _rf:
    SOURCE_REVISIONS = json.load(_rf)
if not isinstance(SOURCE_REVISIONS, dict):
    raise SystemExit('SOURCE_REVISIONS_FILE must contain a JSON object')
def revision_for(repo):
    revision = SOURCE_REVISIONS.get(repo)
    if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise SystemExit(f'missing immutable 40-hex revision for {repo}')
    return revision

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

TOOL_FIELDS = ('functions', 'function_calls', 'tool_calls', 'tool_call_id', 'name')
def _json_text(value):
    if isinstance(value, str): return value
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
def _tag(name, value):
    return f'<{name}>\n{_json_text(value)}\n</{name}>'
def _export_turn(m):
    role = m.get('role'); original_content = m.get('content'); c = text_of(original_content)
    turn = dict(role=role, content=c)
    for field in TOOL_FIELDS:
        if field in m: turn[field] = m[field]
    if original_content is not None and not isinstance(original_content, str):
        turn['native_content'] = original_content
    if role in ('tool', 'environment'):
        result = {'content': original_content}
        for field in ('tool_call_id', 'name'):
            if field in m: result[field] = m[field]
        turn['content'] = _json_text(result)
    if role == 'system' and m.get('functions'):
        turn['content'] = (c.rstrip() + '\n' + _tag('functions', m['functions'])).lstrip()
    rendered_calls = {}
    # Preserve a truthy upstream function_calls field in the rendered turn
    # regardless of role. Some Dolci records carry an actual call or the raw
    # string "null" on a user turn. Candidate selection can quarantine those
    # semantics, but the lossless export must not silently drop the field.
    if m.get('function_calls'):
        rendered_calls['function_calls'] = m['function_calls']
    if role == 'assistant' and m.get('tool_calls'):
        rendered_calls['tool_calls'] = m['tool_calls']
    if role == 'assistant' and isinstance(original_content, dict) and original_content.get('blocks'):
        calls = [b for b in original_content['blocks'] if isinstance(b, dict) and b.get('calls')]
        if calls:
            turn['block_calls'] = calls
            rendered_calls['block_calls'] = calls
    if rendered_calls:
        turn['content'] = (c.rstrip() + '\n' + _tag('function_calls', rendered_calls)).lstrip()
    return turn
def _source_id(row, fallback):
    for field in ('id', 'conversation_id'):
        if field in row and row[field] is not None and row[field] != '': return row[field]
    return fallback
def _prepare_output(path):
    if os.path.exists(path):
        if os.listdir(path): raise SystemExit(f'output directory must be new or empty: {path}')
    else: os.makedirs(path)
def _export_row(label, bucket, rid, u, a, turns, source_revision, source_locator):
    return dict(source=label, bucket=bucket, id=str(rid), source_id=rid,
                source_revision=source_revision, source_locator=source_locator,
                user=u, assistant=a, turns=turns, n_turns=len(turns) or 1)
def emit(fh, label, bucket, rid, row, source_revision, source_locator):
    u, a = user_text(row), assistant_text(row)
    msgs = row.get('messages')
    if isinstance(msgs, str):
        try: msgs = json.loads(msgs)
        except Exception: msgs = None
    turns = []
    if isinstance(msgs, list):
        for m in msgs:
            if isinstance(m, dict): turns.append(_export_turn(m))
    if turns and not next((t['content'] for t in turns if t['role'] == 'user'), '').strip(): return False  # first user prompt missing (Nemotron chat: seed prompts withheld, 41%)
    if not a.strip(): a = next((t['content'] for t in reversed(turns) if t['role'] == 'assistant' and t['content'].strip()), '')
    if not u.strip(): u = next((t['content'] for t in turns if t['role'] == 'user' and t['content'].strip()), '')
    if not a.strip() or not u.strip(): return False
    out = _export_row(label, bucket, rid, u, a, turns, source_revision, source_locator)
    fh.write(json.dumps(out, ensure_ascii=False) + '\n'); return True

# parquet blocks, grouped per repo so each shard is read once
by_repo = collections.defaultdict(list)
if ONLY: BLOCKS = {k: v for k, v in BLOCKS.items() if k in ONLY}; STREAMS = {k: v for k, v in STREAMS.items() if k in ONLY}
selected_repos = {spec[0] for spec in BLOCKS.values()} | {spec[0] for spec in STREAMS.values()}
PINNED_REVISIONS = {repo: revision_for(repo) for repo in sorted(selected_repos)}
_prepare_output(OUT)
for label, (repo, col, vals, target, k) in BLOCKS.items(): by_repo[repo].append((label, col, vals, target, k))
counts = collections.Counter(); files_h = {label: open(f'{OUT}/{label}.jsonl', 'w') for label in BLOCKS}
for repo, specs in by_repo.items():
    revision = PINNED_REVISIONS[repo]
    files = sorted(f for f in api.list_repo_files(repo, repo_type='dataset', revision=revision) if f.endswith('.parquet') and 'train' in f)
    k = min(max(s[4] for s in specs), len(files)); pick = sorted(set(files[int(i * (len(files) - 1) / max(1, k - 1))] for i in range(k)))  # evenly spaced over ALL shards
    print(f'{repo}: {len(files)} files, reading {len(pick)}', flush=True); t0 = time.time()
    for f in pick:
        if all(counts[s[0]] >= s[3] for s in specs): break
        path = hf_hub_download(repo, f, repo_type='dataset', revision=revision); pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            for row_in_group, row in enumerate(pf.read_row_group(rg).to_pylist()):
                for label, col, vals, target, _ in specs:
                    if counts[label] < target and row.get(col) in vals:
                        # thin uniformly so the target spreads across shards
                        locator = dict(file=f, row_group=rg, row_in_group=row_in_group)
                        if random.random() < THIN and emit(files_h[label], label, row.get(col), _source_id(row, f'{f}:rg{rg}:row{row_in_group}'), row, revision, locator): counts[label] += 1
        print(f'  {f}: ' + ', '.join(f'{s[0]}={counts[s[0]]}' for s in specs) + f' ({round(time.time()-t0)}s)', flush=True)
for fh in files_h.values(): fh.close()
for label, (repo, cfg, split, target) in STREAMS.items():
    t0 = time.time(); n = 0
    with open(f'{OUT}/{label}.jsonl', 'w') as fh:
        try:
            revision = PINNED_REVISIONS[repo]
            for i, row in enumerate(load_dataset(repo, cfg, split=split, streaming=True, revision=revision)):
                if n >= target: break
                if random.random() < 0.5 and emit(fh, label, split, _source_id(row, i), row, revision, dict(split=split, source_index=i)): n += 1
        except Exception as e: print(label, 'ERROR', str(e)[:200], flush=True)
    print(f'{label}: {n} rows in {round(time.time()-t0)}s', flush=True)
# ground-truth candidate pool: 30 random rows per block, disjoint ids written to gt_pool.jsonl
with open(f'{OUT}/gt_pool.jsonl', 'w') as gt:
    for label in sorted(os.path.basename(f)[:-6] for f in os.listdir(OUT) if f.endswith('.jsonl') and f != 'gt_pool.jsonl'):
        rows = [l for l in open(f'{OUT}/{label}.jsonl')]
        random.shuffle(rows)
        for l in rows[:40]: gt.write(l)
print('DONE', flush=True)
