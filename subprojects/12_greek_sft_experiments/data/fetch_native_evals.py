#!/usr/bin/env python3
"""G3: fetch the native-Greek suite sets from the Hub and write their question texts to cache/evals/native_<set>.jsonl ({eval_id, text}).
Sets: ilsp/mcqa_greek_asep, ilsp/medical_mcqa_greek (validation), ilsp/greek_pcr, IMISLab/DemosQA. The OYXOY sets are added when their source is located."""
import json, io
from pathlib import Path
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq, csv
OUT = Path(__file__).resolve().parent / 'cache' / 'evals'
def write(name, rows):
    p = OUT / f'native_{name}.jsonl'
    with open(p, 'w') as f:
        for eid, text in rows:
            if text and str(text).strip(): f.write(json.dumps(dict(eval_id=eid, text=str(text)), ensure_ascii=False) + '\n')
    print(f'{p.name}: {sum(1 for _ in open(p))} rows')
def parquet_rows(repo, fname):
    p = hf_hub_download(repo, fname, repo_type='dataset'); t = pq.read_table(p); return t.to_pylist(), t.column_names
def textify(r, keys):
    parts = [str(r[k]) for k in keys if k in r and r[k] is not None and not isinstance(r[k], (list, dict))]
    for k in keys:
        if isinstance(r.get(k), list): parts += [str(x) for x in r[k] if isinstance(x, str)]
    return ' '.join(parts)
for repo, fname, name in [('ilsp/mcqa_greek_asep', 'data/default-00000-of-00001.parquet', 'asep_mcqa'), ('ilsp/medical_mcqa_greek', 'data/validation-00000-of-00001.parquet', 'medical_mcqa'), ('ilsp/greek_pcr', 'data/default-00000-of-00001.parquet', 'gpcr')]:
    rows, cols = parquet_rows(repo, fname); print(repo, cols[:10])
    keys = [c for c in cols if any(k in c.lower() for k in ('question', 'goal', 'sol', 'choice', 'option', 'prompt', 'text', 'answer'))]
    write(name, [(f'{name}:{i}', textify(r, keys)) for i, r in enumerate(rows)])
p = hf_hub_download('IMISLab/DemosQA', 'DemosQA.csv', repo_type='dataset'); rd = list(csv.DictReader(open(p, encoding='utf-8')))
print('DemosQA', list(rd[0].keys())[:10] if rd else 'empty')
keys = [k for k in (rd[0].keys() if rd else []) if any(x in k.lower() for x in ('question', 'answer', 'text', 'title', 'body'))]
write('demosqa', [(f'demosqa:{i}', ' '.join(str(r[k]) for k in keys if r.get(k))) for i, r in enumerate(rd)])
