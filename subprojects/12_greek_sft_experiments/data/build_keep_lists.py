#!/usr/bin/env python3
"""Merge every screen output into per-block keep / adapt / drop id lists and one summary table.
Precedence per row: checker verdict > Sol label (block judged by Sol, or Sol category pass) > Luna label.
Usage: python3 build_keep_lists.py <labels_dir> <verified_dir> <out_dir>"""
import json, sys, os, glob, collections
LAB, VER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)
rows_summary = []
def load(path):
    d = {}
    if os.path.exists(path):
        for l in open(path):
            j = json.loads(l); d[j['id']] = j
    return d
blocks = sorted(set(os.path.basename(f).split('.')[0] for f in glob.glob(f'{LAB}/*.labels.jsonl')))
for b in blocks:
    luna_or_sol = load(f'{LAB}/{b}.labels.jsonl'); routed = load(f'{LAB}/{b}.sol_routed.jsonl')
    final = {}
    for i, j in luna_or_sol.items():
        j2 = routed.get(i, j); final[i] = (j2.get('disposition') or 'unlabelled', j2.get('judge', 'gpt-5.6-luna'), j2)
    c = collections.Counter(v[0] for v in final.values()); judges = collections.Counter(v[1] for v in final.values())
    ident = sum(1 for v in final.values() if v[2].get('frame_type') == 'identity'); q1 = sum(1 for v in final.values() if v[2].get('quality') == 1)
    for k in ('keep', 'adapt', 'drop'):
        with open(f'{OUT}/{b}.{k}_ids.txt', 'w') as f:
            for i, v in final.items():
                if v[0] == k: f.write(i + '\n')
    rows_summary.append(dict(block=b, labelled=len(final), keep=c['keep'], adapt=c['adapt'], drop=c['drop'], identity=ident, quality1=q1, judges=dict(judges)))
# checker-verified blocks
for name in sorted(glob.glob(f'{VER}/*/keep_ids.txt')):
    d = os.path.dirname(name); k = len(open(name).read().split()); w = len(open(f'{d}/wrong_ids.txt').read().split()); u = len(open(f'{d}/unchecked_ids.txt').read().split())
    rows_summary.append(dict(block=os.path.basename(d) + ' (checker)', labelled=k + w + u, keep=k, adapt=0, drop=w, identity=0, quality1=w, judges={'checker': k + w + u}))
json.dump(rows_summary, open(f'{OUT}/summary.json', 'w'), indent=1)
print(f"{'block':28s} {'labelled':>9s} {'keep':>7s} {'adapt':>6s} {'drop':>6s} {'identity':>8s} {'wrong':>6s}  judges")
for r in rows_summary:
    print(f"{r['block']:28s} {r['labelled']:9d} {r['keep']:7d} {r['adapt']:6d} {r['drop']:6d} {r['identity']:8d} {r['quality1']:6d}  {r['judges']}")
