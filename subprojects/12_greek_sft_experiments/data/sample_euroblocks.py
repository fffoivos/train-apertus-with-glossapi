#!/usr/bin/env python3
"""Add French/German EuroBlocks rows to block_samples.json (the language rows sit deep inside two parquet files).
Usage: python3 sample_euroblocks.py <block_samples.json> [n]"""
import json, sys, random
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download
OUT = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 4; random.seed(5)
REPO = 'utter-project/EuroBlocks-SFT-Synthetic-1124'; BLOCK = 'EuroBlocks · French and German'
hits = []  # (file, row_group, index_in_group)
for f in ('data/train-00000-of-00002.parquet', 'data/train-00001-of-00002.parquet'):
    p = hf_hub_download(REPO, f, repo_type='dataset'); pf = pq.ParquetFile(p)
    for rg in range(pf.num_row_groups):
        col = pf.read_row_group(rg, columns=['langid']).column('langid').to_pylist()
        hits += [(p, rg, i) for i, v in enumerate(col) if v in ('fr', 'de')]
    print(f, 'row groups', pf.num_row_groups, 'fr/de so far', len(hits), flush=True)
pick = random.sample(hits, min(N, len(hits))); rows = []
for p, rg, i in pick:
    r = pq.ParquetFile(p).read_row_group(rg).slice(i, 1).to_pylist()[0]
    msgs = r.get('messages')
    if not isinstance(msgs, (list, str)): msgs = r.get('conversations')
    if isinstance(msgs, str): msgs = json.loads(msgs)
    if not isinstance(msgs, list): print('skip row without messages', r.get('langid'), type(r.get('conversations'))); continue
    turns = [dict(role={'human': 'user', 'gpt': 'assistant'}.get(m.get('role') or m.get('from'), m.get('role') or m.get('from')), content=m.get('content') or m.get('value') or '') for m in msgs]
    rows.append(dict(block=BLOCK, turns=turns, meta=dict(repo=REPO, langid=r.get('langid'), dataset=r.get('dataset'), task=r.get('task'), fr_de_rows_total=len(hits))))
S = json.load(open(OUT)); S = [s for s in S if s['block'] != BLOCK] + rows
json.dump(S, open(OUT, 'w'), ensure_ascii=False); print('DONE', len(rows), 'added; total', len(S), flush=True)
