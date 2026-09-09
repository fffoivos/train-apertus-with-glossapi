#!/usr/bin/env python3
"""Post-review fixes for math cut1 (astra 2026-09-09): quarantine [asy] diagram problems; require complete multi-part finals;
extra second solves (Sol high, batches of 10) for native rows flagged by features (multi-part, probability, systems, units, geometry) regardless
of grade; then agreement is recomputed and the cut rebuilt. Usage: python3 postfix_cut1.py <cut_dir>"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import mathlib as M, math_pilots as P
from concurrent.futures import ThreadPoolExecutor
cut = sys.argv[1]; nat = f'{cut}/native'
probs = [json.loads(l) for l in open(f'{nat}/problems.jsonl')]; s2 = {json.loads(l)['id']: json.loads(l) for l in open(f'{nat}/solved2.jsonl')} if os.path.exists(f'{nat}/solved2.jsonl') else {}
RISK_TOPICS = ('πιθανότητες', 'συστήματα', 'μονάδες', 'γεωμετρία', 'τριγωνομετρία', 'στατιστική')
def risky(r): return bool(re.search(r'\(α\)|\(β\)|α\)|β\)', r['problem_el'])) or any(t in r['topic'] for t in RISK_TOPICS) or 'πίνακα' in r['surface']
todo = [r for r in probs if r['id'] not in s2 and risky(r)]; print(len(todo), 'native rows get an extra second solve (feature-routed)', flush=True)
def sbatch(ch):
    body = '\n\n'.join(f'=== id: {r["id"]} ===\n{r["problem_el"]}' for r in ch); j = P.call(P.SOLVE.format(n=len(ch), body=body), P.S_SOLVE, effort='high')
    if j and {x['id'] for x in j['items']} == {r['id'] for r in ch}: P.append(f'{nat}/solved2.jsonl', [dict(id=x['id'], solution2=x['solution_el'], final2=x['final_answer']) for x in j['items']])
with ThreadPoolExecutor(24) as pool: list(pool.map(sbatch, [todo[i:i + 10] for i in range(0, len(todo), 10)]))
s2 = {json.loads(l)['id']: json.loads(l) for l in open(f'{nat}/solved2.jsonl')}
def multipart_ok(r):
    if not re.search(r'\(α\)|α\)', r['problem_el']) or not re.search(r'\(β\)|β\)', r['problem_el']): return True
    fa = r['final_answer'] or ''; return bool(re.search(r'α\)', fa)) and bool(re.search(r'β\)', fa))
res, st = [], collections.Counter()
for r in probs:
    s = s2.get(r['id']); f1 = r['final_answer'] or M.final_answer(r['solution_el'])
    if s: f2 = s['final2'] or M.final_answer(s['solution2']); agree = M.equiv(f1, f2) and (multipart_ok(r) and (not re.search(r'α\)', f1) or bool(re.search(r'β\)', f2 or ''))))
    else: f2, agree = '', None
    if not multipart_ok(r): st['multipart_incomplete'] += 1; agree = False
    res.append(dict(r, solution2=s['solution2'] if s else '', final2=f2, agree=agree, numeric=M.norm_num(f1) is not None, fmt=M.fmt_checks(r['solution_el'])))
with open(f'{nat}/results.jsonl', 'w') as f:
    for r in res: f.write(json.dumps(r, ensure_ascii=False) + '\n')
ver = [r for r in res if r['agree'] is not None]; print('native verified', len(ver), 'agree', round(sum(r['agree'] for r in ver) / max(1, len(ver)), 3), dict(st))
# translated: quarantine diagram code
tr = [json.loads(l) for l in open(f'{cut}/translated/results.jsonl')]; asy = sum('[asy]' in r['problem_en'] or '[asy]' in r['problem_el'] for r in tr)
with open(f'{cut}/translated/results.jsonl', 'w') as f:
    for r in tr:
        if '[asy]' in r['problem_en'] or '[asy]' in r['problem_el']: r['correct'] = False; r['quarantined'] = 'asy_diagram'
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print('translated rows quarantined for [asy]:', asy); print('POSTFIX DONE')
