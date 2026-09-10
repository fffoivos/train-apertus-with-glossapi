#!/usr/bin/env python3
"""MATH-500-el second pass after the Claude cross-check: apply the cross-checker's corrected problems where given; detect leftover English prose outside math
(a run of ≥ 3 Latin-alphabet words outside math spans, names excepted by the 3-word rule) which the span scanner cannot see; re-translate under the amended rules
every row that fails any check or matches the global-rule patterns (\\text{} prose, ordinals, modulo, 'common fraction', invented units, tables). Then re-check all.
Usage: python3 redo.py"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE); import bench_lib as B
from translate import span_skeletons, numbers, translate, MATH, TEXT
GLOB = re.compile(r'\\text(bf)?\{|tabular|\b\d+(st|nd|rd|th)\b|\^\{?\\?(mathrm|text)\{th\}|modulo|common fraction|\b(daps|yaps|baps|treeks|squigs|goolees)\b', re.I)


ASY = re.compile(r'\[asy\].*?\[/asy\]', re.S)


def english_run(el):
    """A run of ≥ 3 Latin-alphabet words outside math, Asymptote code and \\text{}; runs made only of capitalised words (names, titles) do not count."""
    prose = TEXT.sub(' ', MATH.sub(' ', ASY.sub(' ', el)))
    for m in re.finditer(r'(?:\b[A-Za-z]{2,}\b[\s,.;:()\'"-]*){3,}', prose):
        words = re.findall(r'[A-Za-z]{2,}', m.group(0))
        if sum(w[0].islower() for w in words) >= 2: return True
    return False


def checks(r):
    el = r['problem_el']; r['check_math_spans'] = span_skeletons(el) == span_skeletons(r['problem_en']); r['check_numbers'] = sorted(numbers(el)) == sorted(numbers(r['problem_en']))
    r['english_run'] = english_run(el); prose = MATH.sub('', el); r['greek_share'] = round(len(re.findall(r'[Ά-ώ]', prose)) / max(1, len(re.findall(r'[A-Za-zΆ-ώ]', prose))), 3); return r


def main():
    path = os.path.join(HERE, 'problems_el.jsonl'); rows = B.load(path); shutil.copy(path, path + '.v1'); fixes = {c['id']: c['fix'] for c in B.load(os.path.join(HERE, 'crosscheck_claude.jsonl')) if c.get('fix')}
    for r in rows:
        if r['id'] in fixes: r['problem_el'] = fixes[r['id']]; r['crosscheck_fix'] = True
        checks(r)
    redo = [r for r in rows if not r.get('crosscheck_fix') and (not r['check_math_spans'] or not r['check_numbers'] or r['english_run'] or GLOB.search(r['problem_en']))]
    print('claude fixes applied', len(fixes), '| re-translating', len(redo), flush=True)
    def one(r):
        src = dict(unique_id=r['id'], problem=r['problem_en'], subject=r['subject'], level=r['level'], solution=r['solution_en'], answer=r['answer'])
        for _ in range(2):
            t = translate(src)
            if t and t['check_math_spans'] and t['check_numbers'] and not english_run(t['problem_el']): return dict(id=r['id'], problem_el=t['problem_el'], terms=t['terms'], issue=t['issue'])
        return dict(id=r['id'], problem_el=(t or {}).get('problem_el', r['problem_el']), terms=(t or {}).get('terms', r['terms']), issue=(t or {}).get('issue', r['issue']), weak=True)
    done = {d['id']: d for d in B.run_jobs(redo, one, os.path.join(HERE, 'redo_out.jsonl'), stage='math500 redo')}
    for r in rows:
        if r['id'] in done: d = done[r['id']]; r.update(problem_el=d['problem_el'], terms=d['terms'], issue=d['issue'], repair='retranslated_v2'); r['needs_review'] = bool(d.get('weak'))
        r.pop('crosscheck_fix', None) if False else None; checks(r)
    with open(path, 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    print(json.dumps(dict(rows=len(rows), all_ok=sum(r['check_math_spans'] and r['check_numbers'] and not r['english_run'] for r in rows), english_run=sum(r['english_run'] for r in rows), needs_review=sum(bool(r.get('needs_review')) for r in rows), claude_fixed=len(fixes), retranslated=len(done))))


if __name__ == '__main__': main()
