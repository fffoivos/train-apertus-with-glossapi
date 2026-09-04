#!/usr/bin/env python3
"""Raw exports that keep the columns a checker needs. Usage: python3 export_raw.py <ifeval_like|openmath> <out.jsonl> <n>"""
import json, sys
from datasets import load_dataset
mode, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
if mode == 'ifeval_like':
    ds = load_dataset('argilla/ifeval-like-data', 'filtered', split='train', streaming=True); keep = None
elif mode == 'openmath':
    ds = load_dataset('nvidia/OpenMathInstruct-2', 'default', split='train', streaming=True); keep = None
else: raise SystemExit('mode?')
k = 0; seen = 0
with open(out, 'w') as f:
    for i, r in enumerate(ds):
        seen += 1
        if mode == 'openmath' and str(r.get('problem_source', '')).lower() != 'gsm8k': continue
        r = {kk: (v if isinstance(v, (str, int, float, list, dict, type(None), bool)) else str(v)) for kk, v in r.items()}
        r['_row'] = i; f.write(json.dumps(r, ensure_ascii=False) + '\n'); k += 1
        if k % 10000 == 0: print(mode, k, 'kept of', seen, flush=True)
        if k >= n: break
print('DONE', mode, k, 'rows kept of', seen, 'read', flush=True)
