#!/usr/bin/env python3
"""Representative random samples (full turns) from every block of the round-two training mix. CPU only.
Usage: python3 sample_blocks.py <out.jsonl>"""
import json, sys, os, random, time, glob
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download
from datasets import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'vantage_scan.py')).read(); exec(src[:src.index('SOURCES = [')])
OUT = sys.argv[1]; random.seed(99); api = HfApi()

def turns_of(row):
    msgs = row.get('messages')
    if isinstance(msgs, str):
        try: msgs = json.loads(msgs)
        except Exception: msgs = None
    out = []
    if isinstance(msgs, list):
        for m in msgs:
            if not isinstance(m, dict): continue
            c = text_of(m.get('content'))
            if m.get('role') == 'assistant' and not c.strip():
                if m.get('tool_calls'): c = 'TOOL_CALLS: ' + json.dumps(m.get('tool_calls'), ensure_ascii=False)[:2000]
                elif isinstance(m.get('content'), dict) and m['content'].get('blocks'):
                    calls = [b for b in m['content']['blocks'] if isinstance(b, dict) and b.get('calls')]
                    if calls: c = 'TOOL_CALLS: ' + json.dumps(calls, ensure_ascii=False)[:2000]
            out.append(dict(role=m.get('role'), content=c))
        return out
    u, a = user_text(row), assistant_text(row)
    return [dict(role='user', content=u), dict(role='assistant', content=a)] if u or a else []

def reservoir(items_iter, k, limit):
    res = []; n = 0
    for it in items_iter:
        n += 1
        if len(res) < k: res.append(it)
        else:
            j = random.randint(0, n - 1)
            if j < k: res[j] = it
        if n >= limit: break
    return res

samples = []
def add(block, rows, meta=None):
    for r in rows:
        t = turns_of(r)
        if not t or not any(x['content'].strip() for x in t): continue
        samples.append(dict(block=block, turns=t, meta=meta or {}))
    print(f'{block}: {sum(1 for s in samples if s["block"]==block)} samples', flush=True)
    json.dump(samples, open(OUT, 'w'), ensure_ascii=False)

# --- parquet-backed: Dolci by (domain, source_dataset), Tulu by source
def parquet_rows(repo, k_files, pred, want, limit_per_file=60000):
    files = sorted(f for f in api.list_repo_files(repo, repo_type='dataset') if f.endswith('.parquet') and 'train' in f)
    pick = [files[int(i * (len(files) - 1) / max(1, k_files - 1))] for i in range(min(k_files, len(files)))]
    def gen():
        for f in pick:
            path = hf_hub_download(repo, f, repo_type='dataset'); pf = pq.ParquetFile(path); n = 0
            for rg in range(pf.num_row_groups):
                for row in pf.read_row_group(rg).to_pylist():
                    n += 1
                    if pred(row): yield row
                    if n >= limit_per_file: break
                if n >= limit_per_file: break
    return reservoir(gen(), want, 10**9)

D = 'allenai/Dolci-Instruct-SFT'
dolci_blocks = {
 'Dolci · Precise IF (verified constraints)': lambda r: r.get('domain') == 'Precise IF',
 'Dolci · Math, persona GSM and algebra': lambda r: r.get('domain') == 'Math' and 'Persona' in str(r.get('source_dataset')),
 'Dolci · Math, OpenMathInstruct-2 slice': lambda r: r.get('source_dataset') == 'OpenMathInstruct 2',
 'Dolci · Coding': lambda r: r.get('domain') == 'Coding',
 'Dolci · Reasoning (verifiable, traces removed)': lambda r: r.get('domain') == 'Reasoning',
 'Dolci · Other, logic puzzles': lambda r: r.get('source_dataset') == 'Logic Puzzles',
 'Dolci · Other, FLAN': lambda r: r.get('source_dataset') == 'FLAN',
 'Dolci · Tool Use': lambda r: r.get('domain') == 'Tool Use',
 'Dolci · Science': lambda r: r.get('domain') == 'Science',
 'Dolci · Safety, WildGuardMix': lambda r: r.get('source_dataset') == 'WildGuardMix',
 'Dolci · Safety, CoCoNot': lambda r: r.get('source_dataset') == 'CoCoNot',
 'Dolci · Chat (OpenAssistant)': lambda r: r.get('domain') == 'Chat',
 'Dolci · Multilingual (Aya)': lambda r: r.get('domain') == 'Multilingual',
}
files = sorted(f for f in api.list_repo_files(D, repo_type='dataset') if f.endswith('.parquet') and 'train' in f)
buckets = {b: [] for b in dolci_blocks}; seen = {b: 0 for b in dolci_blocks}
t0 = time.time()
for f in files:
    path = hf_hub_download(D, f, repo_type='dataset'); pf = pq.ParquetFile(path)
    for rg in range(pf.num_row_groups):
        for row in pf.read_row_group(rg).to_pylist():
            for b, pred in dolci_blocks.items():
                if pred(row):
                    seen[b] += 1; k = 5
                    if len(buckets[b]) < k: buckets[b].append(row)
                    else:
                        j = random.randint(0, seen[b] - 1)
                        if j < k: buckets[b][j] = row
    print(f'  {f} done ({round(time.time()-t0)}s)', flush=True)
for b, rows in buckets.items(): add(b, rows, {'repo': D, 'seen_in_pass': seen[b]})

T = 'allenai/tulu-3-sft-mixture'
add('Tulu 3 · WildChat (GPT-4 answers)', parquet_rows(T, 6, lambda r: r.get('source') == 'ai2-adapt-dev/tulu_v3.9_wildchat_100k', 5), {'repo': T})
add('Tulu 3 · persona instruction following', parquet_rows(T, 6, lambda r: 'personahub_ifdata' in str(r.get('source')), 4), {'repo': T})

# --- streaming blocks
def stream_rows(repo, cfg, split, want, limit=6000, filt=None):
    ds = load_dataset(repo, cfg, split=split, streaming=True)
    def gen():
        for r in ds:
            if filt is None or filt(r): yield r
    return reservoir(gen(), want, limit)
add('IFEval-like, filtered (Qwen2.5-72B, checker-verified)', stream_rows('argilla/ifeval-like-data', 'filtered', 'train', 5, 3000), {'repo': 'argilla/ifeval-like-data'})
add('Nemotron IF-Chat v3 · chat split (GLM-5 answers)', stream_rows('nvidia/Nemotron-SFT-Instruction-Following-Chat-v3', 'default', 'chat', 6, 4000), {'repo': 'nvidia/Nemotron-SFT-Instruction-Following-Chat-v3'})
add('Nemotron IF-Chat v3 · instruction-following split', stream_rows('nvidia/Nemotron-SFT-Instruction-Following-Chat-v3', 'default', 'instruction_following', 4, 4000), {'repo': 'nvidia/Nemotron-SFT-Instruction-Following-Chat-v3'})
add('SmolTalk2 · Magpie Ultra', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_smol_magpie_ultra_no_think', 4, 4000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('SmolTalk2 · OpenHermes 2.5', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'OpenHermes_2.5_no_think', 4, 4000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('SmolTalk2 · rewrite', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_smol_rewrite_no_think', 3, 3000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('SmolTalk2 · summarize', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_smol_summarize_no_think', 3, 3000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('SmolTalk2 · table tasks', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'table_gpt_no_think', 2, 3000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('SmolTalk2 · multilingual, eight languages', stream_rows('HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_multilingual_8languages_lang_5_no_think', 4, 4000), {'repo': 'HuggingFaceTB/smoltalk2'})
add('OpenMathInstruct-2 (GSM8K-style)', stream_rows('nvidia/OpenMathInstruct-2', 'default', 'train', 4, 4000), {'repo': 'nvidia/OpenMathInstruct-2'})
add('EuroBlocks · French and German', stream_rows('utter-project/EuroBlocks-SFT-Synthetic-1124', 'default', 'train', 4, 6000, lambda r: str(r.get('language', '')).lower()[:2] in ('fr', 'de', 'ge')), {'repo': 'utter-project/EuroBlocks-SFT-Synthetic-1124'})
# --- our Greek data (private HF dataset cached under HF_HOME)
try:
    cands = sorted(glob.glob(os.environ.get('HF_HOME', '') + '/hub/datasets--fffoivos--Greek-SFT-translated-and-adapted/snapshots/*/**/*.jsonl', recursive=True))
    rows = []
    for f in cands[:8]:
        for l in open(f):
            try: rows.append(json.loads(l))
            except Exception: pass
    random.shuffle(rows); add('Ours · Greek, adapted (no_robots, everyday, skills…)', rows[:8], {'repo': 'fffoivos/Greek-SFT-translated-and-adapted', 'files': [os.path.basename(c) for c in cands[:8]]})
except Exception as e: print('greek ERROR', e, flush=True)
print('DONE', len(samples), flush=True)
