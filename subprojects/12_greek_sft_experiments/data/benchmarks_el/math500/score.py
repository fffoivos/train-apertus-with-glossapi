#!/usr/bin/env python3
"""MATH-500-el scorer: extraction + equiv500 (extended Greek metric) and the vendored upstream grader (upstream metric), reported separately; primary comparison
= the 486 items without a template sibling in our SFT set (astra F6), full 500 and the flagged 14 alongside; by level and subject.
Usage: python3 score.py <responses.jsonl: {id, response}> <out.jsonl>   |   python3 score.py --selftest"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE); import bench_lib as B
from equiv500 import equiv500, extract, upstream_equiv


def selftest(rows):
    res = dict(n=len(rows))
    res['equiv_self'] = sum(bool(equiv500(r['answer'], r['answer'])) for r in rows)
    pn = [r for r in rows if re.search(r'\d', r['answer'])]
    def pert(a): m = re.search(r'\d', a); i = m.start(); return a[:i] + str((int(a[i]) + 1) % 10) + a[i + 1:]
    res['perturbed_rejected'] = f"{sum(not equiv500(r['answer'], pert(r['answer'])) for r in pn)}/{len(pn)}"
    res['no_digit_answers'] = [r['answer'] for r in rows if not re.search(r'\d', r['answer'])]
    cases = [('\\text{ellipse}', 'έλλειψη', True), ('\\text{ellipse}', '\\text{έλλειψη}', True), ('\\text{ellipse}', 'υπερβολή', False), ('\\text{even}', 'άρτιος', True), ('\\text{even}', 'περιττός', False), ('\\text{east}', 'ανατολικά', True),
             ('\\text{Evelyn}', 'Evelyn', True), ('\\text{Evelyn}', 'Navin', False), ('3.5', '3,5', True), ('(1,5)', '(1,5)', True), ('(1,5)', '1.5', False), ('1,000', '1000', True), ('15\\mbox{ cm}^2', '15', True), ('\\frac{270}7\\text{ degrees}', '\\frac{270}{7}', True),
             ('\\cot x', '\\cot x', True), ('\\begin{pmatrix} -7 \\\\ 16 \\\\ 5 \\end{pmatrix}', '\\begin{pmatrix} -7 \\\\ 16 \\\\ 5 \\end{pmatrix}', True), ('\\begin{pmatrix} -7 \\\\ 16 \\\\ 5 \\end{pmatrix}', '\\begin{pmatrix} -7 \\\\ 16 \\\\ 6 \\end{pmatrix}', False)]
    res['categorical_and_format_cases'] = f"{sum(bool(equiv500(a, b)) == e for a, b, e in cases)}/{len(cases)}"; res['failed_cases'] = [(a, b, e) for a, b, e in cases if bool(equiv500(a, b)) != e]
    resp = [("Υπολογίζουμε πρώτα $x=3$. Άρα $\\boxed{7}$. Τελικά $\\boxed{12}$.", '12'), ("Λύση…\nΑπάντηση: 3,5", '3.5'), ("Σκέψη χωρίς τελική απάντηση", None), ("Το αποτέλεσμα είναι $\\boxed{\\frac{1}{2}}$ ή αλλιώς 0,5", '0.5'), ("**Απάντηση:** έλλειψη", '\\text{ellipse}')]
    ok = 0
    for text, ref in resp:
        got = extract(text); ok += (equiv500(ref, got) if ref else got in ('Σκέψη χωρίς τελική απάντηση',) and not equiv500('7', got))
    res['full_response_cases'] = f"{ok}/{len(resp)}"
    up = [upstream_equiv(r['answer'], r['answer']) for r in rows[:50]]; res['upstream_grader_available'] = up[0] is not None; res['upstream_self_50'] = sum(bool(x) for x in up)
    print(json.dumps(res, ensure_ascii=False))


def main():
    rows = B.load(os.path.join(HERE, 'problems_el_final.jsonl'))
    if '--selftest' in sys.argv: return selftest(rows)
    bench = {r['id']: r for r in rows}; resp = B.load(sys.argv[1]); out = []
    for x in resp:
        b = bench[x['id']]; pred = extract(x['response']); out.append(dict(id=x['id'], level=b['level'], subject=b['subject'], sibling=b.get('template_sibling_in_sft', False), pred=pred, ref=b['answer'], correct=bool(equiv500(b['answer'], pred)), correct_upstream=upstream_equiv(b['answer'], pred), extracted=bool(pred)))
    with open(sys.argv[2], 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in out]
    def acc(rs, k='correct'): return round(sum(bool(r[k]) for r in rs) / max(1, len(rs)), 3)
    prim = [r for r in out if not r['sibling']]; by = collections.defaultdict(list); [by[f"L{r['level']}"].append(r) for r in prim]; bs = collections.defaultdict(list); [bs[r['subject']].append(r) for r in prim]
    print(json.dumps(dict(primary_486=dict(n=len(prim), acc=acc(prim), acc_upstream=acc(prim, 'correct_upstream'), extraction_rate=acc(prim, 'extracted')), full_500=dict(n=len(out), acc=acc(out)), flagged_14=dict(n=len(out) - len(prim), acc=acc([r for r in out if r['sibling']])),
                          by_level={k: acc(v) for k, v in sorted(by.items())}, by_subject={k: acc(v) for k, v in bs.items()}), ensure_ascii=False))


if __name__ == '__main__': main()
