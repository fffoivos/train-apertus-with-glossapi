#!/usr/bin/env python3
"""Build the v2 ground-truth set (7 rows per block from gt_pool_v2) and print a batch for hand labelling.
Usage: python3 gt_render.py build | show <start> <end>"""
import json, sys, collections
POOL = 'results/ground_truth/gt_pool_v2.jsonl'; GT = 'results/ground_truth/gt_v2_rows.jsonl'; PER = 7; CAP = 3500
if sys.argv[1] == 'build':
    by = collections.defaultdict(list)
    for l in open(POOL):
        r = json.loads(l); by[r['source']].append(r)
    rows = []
    for src in sorted(by):
        for r in by[src][:PER]: r['gt_idx'] = len(rows); rows.append(r)
    with open(GT, 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(len(rows), 'rows', collections.Counter(r['source'] for r in rows))
else:
    a, b = int(sys.argv[2]), int(sys.argv[3])
    for l in open(GT):
        r = json.loads(l)
        if not (a <= r['gt_idx'] < b): continue
        print(f"\n######## [{r['gt_idx']}] {r['source']} id={r['id'][:40]}")
        turns = r['turns'] or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]
        for t in turns:
            c = t['content'] or ''
            if len(c) > CAP: c = c[:CAP * 2 // 3] + f"\n[... {len(c) - CAP} chars cut ...]\n" + c[-CAP // 3:]
            print(f"--- {t['role']}:\n{c}")
