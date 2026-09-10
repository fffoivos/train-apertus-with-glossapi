#!/usr/bin/env python3
"""MATH-500-el freeze: apply the second cross-check's fixes; enforce byte-equality of every [asy]…[/asy] block (restore the source blocks in order when the count
matches; the second cross-check found two rows whose diagrams had been edited or deleted, which no earlier check covered); clear stale translator notes on
re-translated rows; recompute all checks; write problems_el_final.jsonl + summary.json. Usage: python3 finalize.py"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE); import bench_lib as B
from redo import checks, ASY


def main():
    rows = B.load(os.path.join(HERE, 'problems_el.jsonl')); cc2 = {c['id']: c for c in B.load(os.path.join(HERE, 'crosscheck2_claude.jsonl'))}
    n_fix = n_asy = 0
    for r in rows:
        c = cc2.get(r['id'])
        if c and c.get('fix'): r['problem_el'] = c['fix']; r['crosscheck2_fix'] = True; n_fix += 1
        asy_en, asy_el = ASY.findall(r['problem_en']), ASY.findall(r['problem_el'])
        if asy_en != asy_el:
            if len(asy_en) == len(asy_el): it = iter(asy_en); r['problem_el'] = ASY.sub(lambda m: next(it), r['problem_el']); n_asy += 1
            else: r['asy_mismatch'] = True
        r['check_asy'] = ASY.findall(r['problem_en']) == ASY.findall(r['problem_el'])
        if r.get('repair') == 'retranslated_v2' or r.get('crosscheck_fix') or r.get('crosscheck2_fix'): r['terms'] = ''; r['issue'] = ''   # stale after re-translation (cross-check 2)
        checks(r); r['final_ok'] = r['check_math_spans'] and r['check_numbers'] and r['check_asy'] and not r['english_run']
    with open(os.path.join(HERE, 'problems_el_final.jsonl'), 'w') as f:
        for r in rows: f.write(json.dumps(dict(id=r['id'], problem_el=r['problem_el'], problem_en=r['problem_en'], answer=r['answer'], subject=r['subject'], level=r['level'], solution_en=r['solution_en'], checks=dict(math_spans=r['check_math_spans'], numbers=r['check_numbers'], asy=r['check_asy'], english_run=r['english_run'], greek_share=r['greek_share']), provenance=dict(repair=r.get('repair'), crosscheck_fix=bool(r.get('crosscheck_fix')), crosscheck2_fix=bool(r.get('crosscheck2_fix'))), final_ok=r['final_ok']), ensure_ascii=False) + '\n')
    with open(os.path.join(HERE, 'problems_el.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    summ = dict(rows=len(rows), final_ok=sum(r['final_ok'] for r in rows), spans_by_design_diff=sum(not r['check_math_spans'] for r in rows), asy_restored=n_asy, asy_mismatch=sum(bool(r.get('asy_mismatch')) for r in rows), crosscheck2_fixes=n_fix,
                pipeline='Sol translate → splice repair (buggy, reverted) → Claude cross-check 1 (162 rows: 11 corrupt) → escaped-dollar scanner + \\text rule + 23 fixes + 49 re-translations → Claude cross-check 2 (72 rows: 3 meaning defects) → 5 fixes + [asy] byte-equality → frozen')
    json.dump(summ, open(os.path.join(HERE, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
