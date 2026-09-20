#!/usr/bin/env python3
"""MATH-500-el scorer: equiv500 (our Greek-extended equivalence) and the upstream grader, by level and subject.
Usage: python3 score_math500.py <responses.jsonl: {id, response}> <out.json>"""
import json, os, sys, collections, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import equiv500 as E
bench = {json.loads(l)['id']: json.loads(l) for l in open(os.environ.get('MATH_BENCH_FILE', os.path.join(HERE, 'problems_el_final.jsonl')))}   # MATH_BENCH_FILE: e.g. ../math200_confirm/problems_el_final.jsonl
resp = [json.loads(l) for l in open(sys.argv[1])]
rows = []; by_level = collections.defaultdict(lambda: [0, 0]); by_subj = collections.defaultdict(lambda: [0, 0]); n_ok = n_up = n_trunc = 0
for r in resp:
    b = bench[r['id']]; pred = E.extract(r['response'] or ''); ok = bool(E.equiv500(b['answer'], pred)); up = E.upstream_equiv(b['answer'], pred)
    up = bool(up) if up is not None else None
    n_ok += ok; n_up += bool(up); n_trunc += (r.get('finish_reason') == 'length')
    by_level[b['level']][0] += ok; by_level[b['level']][1] += 1; by_subj[b['subject']][0] += ok; by_subj[b['subject']][1] += 1
    rows.append(dict(id=r['id'], level=b['level'], subject=b['subject'], answer=b['answer'], extracted=pred, equiv500=ok, upstream=up, truncated=r.get('finish_reason') == 'length', response_sha256=hashlib.sha256((r['response'] or '').encode('utf-8')).hexdigest()))
n = len(resp); n_up_avail = sum(1 for r in rows if r['upstream'] is not None)
out = dict(scorer_version=2, responses_sha256=hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest(), n=n, equiv500_acc=round(n_ok / n, 4) if n else None, upstream_acc=(round(n_up / n, 4) if n_up_avail == n else None), upstream_grader_available=n_up_avail == n, truncated=n_trunc,
                          by_level={str(k): round(v[0] / v[1], 4) for k, v in sorted(by_level.items())}, by_subject={k: round(v[0] / v[1], 4) for k, v in sorted(by_subj.items())}, rows=rows)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1); print({k: v for k, v in out.items() if k != 'rows'})
