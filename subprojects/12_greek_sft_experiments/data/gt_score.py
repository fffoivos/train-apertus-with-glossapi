#!/usr/bin/env python3
"""Score an annotation run against the hand labels. Usage: python3 gt_score.py <labels.json from the probe> <gt_v2_labels.json> <gt_v2_rows.jsonl>"""
import json, sys, collections
L = json.load(open(sys.argv[1])); G = json.load(open(sys.argv[2]))['labels']; R = [json.loads(l) for l in open(sys.argv[3])]
assert len(L) == len(R), (len(L), len(R))
flag = lambda d: d in ('adapt', 'drop')
tp = fp = fn = tn = 0; id_tp = id_fn = 0; exact = 0; n = 0; rows = []
conf = collections.Counter()
for i, (l, r) in enumerate(zip(L, R)):
    g = G[str(i)]
    if g['disposition'] == 'excluded': continue
    n += 1; ld = l.get('disposition'); gd = g['disposition']
    conf[(gd, ld)] += 1
    if ld == gd: exact += 1
    if flag(gd) and flag(ld): tp += 1
    elif flag(ld) and not flag(gd): fp += 1
    elif flag(gd) and not flag(ld): fn += 1
    else: tn += 1
    if g['vantage'] == 3:
        if l.get('vantage') == 3: id_tp += 1
        else: id_fn += 1
    if ld != gd or (g['vantage'] == 3) != (l.get('vantage') == 3):
        rows.append(f"[{i}] {r['source']:20s} gt={gd}/v{g['vantage']}  luna={ld}/v{l.get('vantage')} ({l.get('frame_type')}) | {g['note'][:70]} | luna: {str(l.get('why'))[:80]}")
P = tp / max(1, tp + fp); Rc = tp / max(1, tp + fn)
print(f"rows scored {n}; disposition exact {exact}/{n} = {exact/n:.2f}")
print(f"flagged (adapt|drop): gt {tp+fn}, luna {tp+fp}; precision {P:.2f} ({tp}/{tp+fp}), recall {Rc:.2f} ({tp}/{tp+fn})")
print(f"identity (vantage 3): recall {id_tp}/{id_tp+id_fn}; luna vantage-3 total {sum(1 for l in L if l.get('vantage') == 3)}")
print("confusion (gt, luna):", dict(conf))
print("\nDISAGREEMENTS"); print('\n'.join(rows) if rows else 'none')
