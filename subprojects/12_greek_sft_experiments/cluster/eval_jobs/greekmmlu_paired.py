#!/usr/bin/env python3
"""GreekMMLU-250 as a PAIRED comparison on a fixed slice (R-DPO6 HIGH #6).

The brief quoted a between-seed SD of 0.002 as if it were the precision of the +2 pp gain. It is
not: it measures how stably seeds answer THE SAME 250 items. The uncertainty that matters for
"is the arm better than the parent" on a fixed slice is the DISCORDANT-pair uncertainty, because
both models answer the identical items -- so we run McNemar on wrong->right vs right->wrong.
"""
import json, glob, os, math, statistics as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
D = os.path.join(ROOT, "results/G4F6P1--DPO01/greekmmlu_items")

def items(label):
    fs = glob.glob(os.path.join(D, label, "*_native_mcq_predictions.jsonl"))
    if not fs: return {}
    return {r["example_id"]: bool(r["correct"]) for r in (json.loads(l) for l in open(fs[0]) if l.strip())}

par = items("parent")
print("parent: %d items, %d correct (%.3f)\n" % (len(par), sum(par.values()), sum(par.values()) / len(par)))

GROUPS = {
    "alpha 0        n=5": ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"],
    "alpha 0.25     n=5": ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"],
    "length-balanced n=3": ["armBAL_ep3", "armBALs43_ep3", "armBALs44_ep3"],
    "IPO beta 10    n=2": ["armIPO42_ep3", "armIPO43_ep3"],
}

def mcnemar(a, b):
    """b vs a on shared items -> (gained, lost, p two-sided exact)."""
    ks = set(a) & set(b)
    g = sum(1 for k in ks if not a[k] and b[k])      # wrong -> right
    l = sum(1 for k in ks if a[k] and not b[k])      # right -> wrong
    n = g + l
    if n == 0: return g, l, 1.0
    # exact binomial two-sided at q=0.5 over discordant pairs
    p = sum(math.comb(n, i) for i in range(0, min(g, l) + 1)) / 2 ** n * 2
    return g, l, min(1.0, p)

print("%-21s %7s %7s %7s %9s %9s" % ("group / run", "acc", "w->r", "r->w", "net", "McNemar p"))
print("-" * 70)
out = {}
for name, labels in GROUPS.items():
    gs, ls, ps, accs = [], [], [], []
    for lab in labels:
        it = items(lab)
        if not it: continue
        g, l, p = mcnemar(par, it)
        acc = sum(it.values()) / len(it)
        gs.append(g); ls.append(l); ps.append(p); accs.append(acc)
        print("  %-19s %7.3f %7d %7d %+9d %9.3f" % (lab, acc, g, l, g - l, p))
    if not accs: continue
    print("%-21s %7.3f %7.1f %7.1f %+9.1f   %s" % (
        name, st.mean(accs), st.mean(gs), st.mean(ls), st.mean(gs) - st.mean(ls),
        "p range %.3f..%.3f" % (min(ps), max(ps))))
    out[name] = {"mean_acc": st.mean(accs), "mean_gained": st.mean(gs), "mean_lost": st.mean(ls),
                 "p_min": min(ps), "p_max": max(ps), "n_runs": len(accs)}
    print()

# How much of the slice is even in play? Items ALL arms get right / wrong regardless.
allr = [items(l) for g in GROUPS.values() for l in g if items(l)]
ks = set(par)
for a in allr: ks &= set(a)
stuck_right = sum(1 for k in ks if par[k] and all(a[k] for a in allr))
stuck_wrong = sum(1 for k in ks if not par[k] and all(not a[k] for a in allr))
moving = len(ks) - stuck_right - stuck_wrong
print("slice structure over %d items and %d runs:" % (len(ks), len(allr)))
print("  %d always right, %d always wrong, %d ever move (%.0f%% of the slice)"
      % (stuck_right, stuck_wrong, moving, 100 * moving / len(ks)))
print("  a +2 pp shift is ~5 net items, drawn from the %d that move at all." % moving)
out["slice"] = {"n": len(ks), "always_right": stuck_right, "always_wrong": stuck_wrong, "moving": moving}
# R-DPO7a [LOW]: the artifact asserted "the same 8 flip right, the same 3 flip wrong" in prose while
# this script never computed the intersection. Emit it, so the claim is rendered from data. Note the
# intersection is a SHARED CORE: individual runs carry extra flips of their own (IPO42 is 10/5, a
# typical alpha-0 run 9/4), so the shared set is what every arm has in common, not the whole story.
runs = {l: items(l) for g in GROUPS.values() for l in g if items(l)}
cg = set(par) ; cl = set(par)
ug, ul = set(), set()
for it in runs.values():
    g = {k for k in it if not par[k] and it[k]}
    l = {k for k in it if par[k] and not it[k]}
    cg &= g; cl &= l; ug |= g; ul |= l
sigs = {(tuple(sorted(k for k in it if not par[k] and it[k])),
         tuple(sorted(k for k in it if par[k] and not it[k]))) for it in runs.values()}
print("\ncommon flips across all %d runs: %d gained, %d lost (net %+d)" % (len(runs), len(cg), len(cl), len(cg)-len(cl)))
print("  gained ids: %s" % ", ".join(sorted(cg, key=lambda x: int(x.split(':')[1]))))
print("  lost ids:   %s" % ", ".join(sorted(cl, key=lambda x: int(x.split(':')[1]))))
print("  union across runs: %d gained, %d lost; %d distinct flip signatures" % (len(ug), len(ul), len(sigs)))
out["common_flips"] = {"gained_ids": sorted(cg), "lost_ids": sorted(cl), "n_runs": len(runs),
                       "union_gained": len(ug), "union_lost": len(ul), "n_signatures": len(sigs)}
json.dump(out, open(os.path.join(ROOT, "results/G4F6P1--DPO01/greekmmlu_paired.json"), "w"), indent=1)
print("\nwrote results/G4F6P1--DPO01/greekmmlu_paired.json")
