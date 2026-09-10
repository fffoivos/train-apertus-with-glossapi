#!/usr/bin/env python3
"""MATH-500-el scorer: boxed-answer extraction (mathlib.boxed / final_answer) + mathlib.equiv against the upstream reference answer. Reports by level and subject.
Also `python3 score.py --selftest` validates the checker on the 500 reference answers: equiv(ref, ref) must hold, equiv(ref, perturbed) must fail, and
Greek-format variants (decimal comma) must hold — the validation the astra review asked for before calling the scoring language-neutral.
Usage: python3 score.py <responses.jsonl: {id, response}> <out.jsonl>"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE); import bench_lib as B; M = B.M; from equiv500 import equiv500


def extract(resp: str) -> str:
    b = M.boxed(resp)
    if b: return b
    m = re.search(r'Απάντηση\s*:\s*(.+)$', resp.strip(), re.M | re.I)
    return m.group(1).strip() if m else M.final_answer(resp)


def selftest(rows):
    ok_same = sum(bool(equiv500(r['answer'], r['answer'])) for r in rows)
    pert = 0; pert_n = 0
    for r in rows:
        a = r['answer']; m = re.search(r'\d', a)
        if not m: continue
        pert_n += 1; i = m.start(); d = a[i]; a2 = a[:i] + str((int(d) + 1) % 10) + a[i + 1:]
        pert += not equiv500(a, a2)
    comma = 0; comma_n = 0
    for r in rows:
        a = r['answer']
        if re.fullmatch(r'-?\d+\.\d+', a): comma_n += 1; comma += bool(equiv500(a, a.replace('.', ',')))
    boxed_ok = sum(extract(f"Λύση... άρα $\\boxed{{{r['answer']}}}$") == r['answer'] for r in rows)
    print(json.dumps(dict(n=len(rows), equiv_self=ok_same, perturbed_rejected=f'{pert}/{pert_n}', decimal_comma_accepted=f'{comma}/{comma_n}', boxed_extraction=boxed_ok)))
    bad = [r['answer'] for r in rows if not equiv500(r['answer'], r['answer'])][:10]; print('self-equiv failures (sample):', bad)


def main():
    rows = B.load(os.path.join(HERE, 'problems_el.jsonl')) if os.path.exists(os.path.join(HERE, 'problems_el.jsonl')) else [dict(id=r['unique_id'], **r) for r in B.load(os.path.join(HERE, 'source', 'test.jsonl'))]
    if '--selftest' in sys.argv: return selftest(rows)
    bench = {r['id']: r for r in rows}; resp = B.load(sys.argv[1]); out = []
    for x in resp:
        b = bench[x['id']]; pred = extract(x['response']); out.append(dict(id=x['id'], level=b['level'], subject=b['subject'], pred=pred, ref=b['answer'], correct=bool(equiv500(b['answer'], pred))))
    with open(sys.argv[2], 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in out]
    by = collections.defaultdict(list); [by[f"L{r['level']}"].append(r['correct']) for r in out]; bs = collections.defaultdict(list); [bs[r['subject']].append(r['correct']) for r in out]
    print(json.dumps(dict(n=len(out), acc=round(sum(r['correct'] for r in out) / max(1, len(out)), 3), by_level={k: round(sum(v) / len(v), 3) for k, v in sorted(by.items())}, by_subject={k: round(sum(v) / len(v), 3) for k, v in bs.items()}), ensure_ascii=False))


if __name__ == '__main__': main()
