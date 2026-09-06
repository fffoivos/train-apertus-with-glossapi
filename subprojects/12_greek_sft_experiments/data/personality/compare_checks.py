#!/usr/bin/env python3
"""Compare two Γ checks of the same rows (e.g. Sol vs Opus): verdict agreement, Greekness, whether both changed the answer, and named rows.
Usage: python3 compare_checks.py <rows.jsonl> <check_a.jsonl> <check_b.jsonl> [row_id ...]"""
import json, sys, collections, difflib
ROWS, CA, CB = sys.argv[1], sys.argv[2], sys.argv[3]; NAMED = sys.argv[4:]
rows = {json.loads(l)['id']: json.loads(l) for l in open(ROWS)}
def load(p):
    d = {}
    for l in open(p):
        j = json.loads(l)
        if j.get('verdict'): d[j['id']] = j
    return d
A, B = load(CA), load(CB); na, nb = next(iter(A.values()))['judge'], next(iter(B.values()))['judge']; common = sorted(set(A) & set(B))
conf = collections.Counter((A[i]['verdict'], B[i]['verdict']) for i in common)
print(f"{len(common)} rows checked by both ({na} vs {nb})\n\n| {na} \\ {nb} | ok | edited | rewrite |\n|---|---|---|---|")
for va in ('ok', 'edited', 'rewrite'): print(f"| {va} | " + ' | '.join(str(conf[(va, vb)]) for vb in ('ok', 'edited', 'rewrite')) + ' |')
agree = sum(conf[(v, v)] for v in ('ok', 'edited', 'rewrite')); print(f"\nsame verdict: {agree}/{len(common)} ({agree/len(common):.0%}); {na} non-ok {sum(1 for i in common if A[i]['verdict']!='ok')}, {nb} non-ok {sum(1 for i in common if B[i]['verdict']!='ok')}")
ga = [A[i]['greekness'] for i in common if isinstance(A[i].get('greekness'), int)]; gb = [B[i]['greekness'] for i in common if isinstance(B[i].get('greekness'), int)]
print(f"Greekness mean: {na} {sum(ga)/len(ga):.2f}, {nb} {sum(gb)/len(gb):.2f}; fact doubts: {na} {sum(1 for i in common if (A[i].get('fact_doubt') or '').strip())}, {nb} {sum(1 for i in common if (B[i].get('fact_doubt') or '').strip())}")
def changed(j, orig): return (j.get('edited_last_answer') or '').strip() not in ('', orig.strip())
both = [i for i in common if changed(A[i], rows[i]['messages'][-1]['content']) and changed(B[i], rows[i]['messages'][-1]['content'])]
sim = []
for i in both: sim.append(difflib.SequenceMatcher(None, A[i]['edited_last_answer'], B[i]['edited_last_answer']).ratio())
print(f"rows where both changed the text: {len(both)}; similarity of the two edited answers: mean {sum(sim)/max(1,len(sim)):.2f}")
bycat = collections.defaultdict(list)
for i in common: bycat[(A[i].get('category') or '?')[0]].append(i)
print("\n| cat | rows | same verdict | " + f"{na} non-ok | {nb} non-ok |\n|---|---|---|---|---|")
for c in sorted(bycat): ids = bycat[c]; print(f"| {c} | {len(ids)} | {sum(1 for i in ids if A[i]['verdict']==B[i]['verdict'])} | {sum(1 for i in ids if A[i]['verdict']!='ok')} | {sum(1 for i in ids if B[i]['verdict']!='ok')} |")
for i in NAMED:
    if i in rows:
        print(f"\n=== {i}\nORIGINAL: {rows[i]['messages'][-1]['content']}")
        for name, d in ((na, A), (nb, B)):
            if i in d: j = d[i]; print(f"{name}: {j['verdict']} | changes: {j.get('changes')} | doubt: {j.get('fact_doubt')!r}\n  edited: {j.get('edited_last_answer')}")
