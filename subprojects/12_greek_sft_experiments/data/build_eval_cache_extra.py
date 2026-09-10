#!/usr/bin/env python3
"""Launch gate G3 (completeness review B3): add the evaluations missing from cache/evals/ so the final mixture is decontaminated against
the full inventory. Rows are {eval_id, text}; the suite name is the file-name prefix. Greek and English variants are separate rows.
Sources: local benchmark finals (data/benchmarks_el/*), Greek MGSM test (~/sft_annot/math_src/mgsm_el_test.jsonl), and the native
suite sets fetched from the Hub by fetch_native_evals.py (run separately)."""
import json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent; OUT = HERE / 'cache' / 'evals'; OUT.mkdir(parents=True, exist_ok=True)
def write(name, rows):
    p = OUT / f'{name}.jsonl'
    with open(p, 'w') as f:
        for eid, text in rows:
            if text and text.strip(): f.write(json.dumps(dict(eval_id=eid, text=text), ensure_ascii=False) + '\n')
    print(f'{p.name}: {sum(1 for _ in open(p))} rows')
B = HERE / 'benchmarks_el'
# MGSM Greek (250) — the English source (GSM8K test) is already cached
mg = Path(os.path.expanduser('~/sft_annot/math_src/mgsm_el_test.jsonl'))
if mg.exists(): write('mgsm_el', [(f'mgsm_el:{i}', json.loads(l).get('question', '')) for i, l in enumerate(open(mg))])
# MATH-500-el (Greek + English)
rows = []
for l in open(B / 'math500' / 'problems_el_final.jsonl'):
    r = json.loads(l); rows += [(f"{r['id']}:el", r.get('problem_el', '')), (f"{r['id']}:en", r.get('problem_en', ''))]
write('math500_el', rows)
# XSTest-el
rows = []
for l in open(B / 'xstest' / 'prompts_el_final.jsonl'):
    r = json.loads(l); rows += [(f"{r['id']}:el", r.get('prompt_el', '')), (f"{r['id']}:en", r.get('prompt_en', ''))]
write('xstest_el', rows)
# IFBench-el
rows = []
for l in open(B / 'ifbench' / 'prompts_el_final.jsonl'):
    r = json.loads(l); rows += [(f"{r['id']}:el", r.get('prompt_el') or r.get('body_el', '')), (f"{r['id']}:en", r.get('prompt_en', ''))]
write('ifbench_el', rows)
# MultiChallenge-el: every user turn, Greek and English
rows = []
for l in open(B / 'multichallenge' / 'conversations_el_final.jsonl'):
    r = json.loads(l)
    for lang in ('el', 'en'):
        for k, t in enumerate(r.get(f'turns_{lang}') or []):
            if isinstance(t, dict) and t.get('role') == 'user': rows.append((f"{r['id']}:{lang}:{k}", t.get('content', '')))
            elif isinstance(t, str): rows.append((f"{r['id']}:{lang}:{k}", t))
        rows.append((f"{r['id']}:{lang}:target", r.get(f'target_question_{lang}', '')))
write('multichallenge_el', rows)
