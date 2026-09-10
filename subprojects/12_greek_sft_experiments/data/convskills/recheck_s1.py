#!/usr/bin/env python3
"""Re-verify S1 list rows with the current s1_list_ok (no new calls). Usage: python3 recheck_s1.py <dir with S1.jsonl>"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import gen_suite as G
d = sys.argv[1]; rows = [json.loads(l) for l in open(f'{d}/S1.jsonl')]; flips = collections.Counter()
for r in rows:
    if r['kind'] != 'list': continue
    users = [m['content'] for m in r['turns'] if m['role'] == 'user'][:-1]; a = r['turns'][-1]['content']
    ok = bool(G.s1_list_ok(a, users)) and 'δεν έχω πρόσβαση' not in a and 'δεν βλέπω' not in a
    flips[(r['verified'], ok)] += 1; r['verified'] = ok
with open(f'{d}/S1.jsonl', 'w') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
by = collections.defaultdict(list)
for r in rows: by[r['kind']].append(r['verified'])
summ = dict(lane='S1', rows=len(rows), verified=sum(r['verified'] for r in rows), verified_rate=round(sum(r['verified'] for r in rows) / max(1, len(rows)), 3), by_kind={k: (len(v), round(sum(v) / len(v), 3)) for k, v in by.items()}, mean_turns=round(sum(len(r['turns']) for r in rows) / max(1, len(rows)), 1), recheck='s1_list_ok stem-tolerant')
json.dump(summ, open(f'{d}/S1_summary.json', 'w'), ensure_ascii=False, indent=1); print('flips (old, new):', dict(flips)); print(json.dumps(summ, ensure_ascii=False))
