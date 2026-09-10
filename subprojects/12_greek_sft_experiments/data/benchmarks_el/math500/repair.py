#!/usr/bin/env python3
"""Repair MATH-500-el rows that failed the programmatic checks (LaTeX spans or numbers changed — typically backslashes lost in JSON output):
(1) if the translation has the same number of math spans, splice the ORIGINAL spans back in (the prose is kept); (2) otherwise re-translate at high effort with an
explicit warning; rows still failing are flagged `needs_review` for the cross-check. Rewrites problems_el.jsonl in place (backup kept). Usage: python3 repair.py"""
import json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE); import bench_lib as B
from translate import spans, numbers, translate, MATH


def splice(en, el):
    orig = spans(en); i = iter(orig)
    return MATH.sub(lambda m: next(i), el) if len(spans(el)) == len(orig) else None


def main():
    path = os.path.join(HERE, 'problems_el.jsonl'); rows = B.load(path); shutil.copy(path, path + '.bak'); fixed = retried = flagged = 0
    for r in rows:
        if r['check_math_spans'] and r['check_numbers']: continue
        new = splice(r['problem_en'], r['problem_el'])
        if new is not None and spans(new) == spans(r['problem_en']) and sorted(numbers(new)) == sorted(numbers(r['problem_en'])):
            r.update(problem_el=new, check_math_spans=True, check_numbers=True, repair='spliced'); fixed += 1; continue
        src = dict(unique_id=r['id'], problem=r['problem_en'] + '\n\n(ΠΡΟΣΟΧΗ: σε προηγούμενη προσπάθεια χάθηκαν ανάστροφες κάθετοι «\\» ή αριθμοί μέσα στο LaTeX. Κάθε $...$ πρέπει να επιστραφεί ΧΑΡΑΚΤΗΡΑ ΠΡΟΣ ΧΑΡΑΚΤΗΡΑ, με τις ανάστροφες καθέτους.)', subject=r['subject'], level=r['level'], solution=r['solution_en'], answer=r['answer'])
        t = None
        for _ in range(2):
            t = translate(src)
            if t and t['check_math_spans'] and t['check_numbers']: break
        retried += 1
        if t and t['check_math_spans'] and t['check_numbers']: r.update(problem_el=t['problem_el'], terms=t['terms'], issue=t['issue'], check_math_spans=True, check_numbers=True, greek_share=t['greek_share'], repair='retranslated')
        else:
            new = splice(r['problem_en'], (t or r)['problem_el'])
            if new is not None: r.update(problem_el=new, check_math_spans=spans(new) == spans(r['problem_en']), check_numbers=sorted(numbers(new)) == sorted(numbers(r['problem_en'])), repair='spliced-after-retry')
            if not (r['check_math_spans'] and r['check_numbers']): r['needs_review'] = True; flagged += 1
    with open(path, 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    print(json.dumps(dict(rows=len(rows), spliced=fixed, retried=retried, still_flagged=flagged, all_ok=sum(r['check_math_spans'] and r['check_numbers'] for r in rows))))


if __name__ == '__main__': main()
