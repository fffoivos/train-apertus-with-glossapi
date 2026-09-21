#!/usr/bin/env python3
"""Answers R-DPO6's open questions 2-6 from artifacts we already hold.

The reviewer asked us to resolve from existing evidence where possible and to narrow only where
it is not. This prints the numbers behind each contested claim so they can go in the write-up
verbatim, and emits evidence_bundle.json for the artifact.
"""
import json, os, statistics as st, itertools, random

H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(H, "..", ".."))
A = json.load(open(os.path.join(ROOT, "results/G4F6P1--DPO01/all_results.json")))

A0 = ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"]
A25 = ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"]
BAL = ["armBAL_ep3", "armBALs43_ep3", "armBALs44_ep3"]
IPO = ["armIPO42_ep3", "armIPO43_ep3"]
out = {}

def col(labels, m):
    return [A[l][m] for l in labels if A.get(l, {}).get(m) is not None]

print("=" * 78)
print("Q2a  The three dispersion quantities the brief conflated")
print("=" * 78)
# (i) between-training-seed SD at n=5; (ii) one same-seed repeat gap; (iii) benchmark item SE.
q2 = {}
for name, labels in (("alpha 0 n=5", A0), ("alpha 0.25 n=5", A25), ("balanced n=3", BAL)):
    for m, N in (("ifeval", 541), ("mgsm", 250), ("greekmmlu", 250)):
        xs = col(labels, m)
        if len(xs) < 2: continue
        sd = st.stdev(xs)
        p = st.mean(xs)
        se = (p * (1 - p) / N) ** 0.5            # binomial SE of ONE score on N items
        q2["%s|%s" % (name, m)] = {"n": len(xs), "mean": p, "seed_sd_pp": sd * 100,
                                   "item_se_pp": se * 100, "N_items": N}
        print("  %-16s %-10s n=%d  mean %.4f  between-seed SD %.2f pp   item SE (1 run, N=%d) %.2f pp"
              % (name, m, len(xs), p, sd * 100, N, se * 100))
print("\n  The same-seed repeat is ONE contrast, not a distribution:")
for m in ("ifeval", "mgsm", "greekmmlu"):
    a, b = A["arm05_ep3"].get(m), A["arm07_ep3"].get(m)
    if a is None or b is None: continue
    q2.setdefault("same_seed_repeat", {})[m] = {"arm05_ep3": a, "arm07_ep3": b, "gap_pp": (b - a) * 100}
    print("    %-10s arm05_ep3 %.4f  arm07_ep3 %.4f   gap %+.1f pp  (n=1 contrast)" % (m, a, b, (b - a) * 100))
out["dispersion"] = q2

print("\n" + "=" * 78)
print("Q2b  The four far-end IFEval values, named, against BOTH baselines")
print("=" * 78)
FAR = [("arm07_ep4", 2e-6, 172), ("arm08_ep2", 4e-6, 86), ("arm07_ep5", 2e-6, 215), ("arm08_ep3", 4e-6, 129)]
far = []
pn, pf = A["parent"], A["parent_ckptcfg"]
print("  %-11s %10s %9s %10s %10s" % ("model", "lr x steps", "IFEval", "vs parent", "vs ckptcfg"))
for l, lr, s in FAR:
    v = A[l]["ifeval"]
    far.append({"label": l, "movement": lr * s, "ifeval": v,
                "d_naive_pp": (v - pn["ifeval"]) * 100, "d_fair_pp": (v - pf["ifeval"]) * 100})
    print("  %-11s %10.2e %9.4f %+10.1f %+10.1f" % (l, lr * s, v, (v - pn["ifeval"]) * 100, (v - pf["ifeval"]) * 100))
mn = st.mean([f["d_naive_pp"] for f in far]); mf = st.mean([f["d_fair_pp"] for f in far])
print("  mean %+.2f pp vs parent, %+.2f pp vs parent_ckptcfg   spread %.1f pp"
      % (mn, mf, max(f["ifeval"] for f in far) * 100 - min(f["ifeval"] for f in far) * 100))
print("  -> the -0.97 pp figure was vs the NAIVE parent; the '0.9 pp' it was compared to was the")
print("     same-seed repeat gap. Different baselines and different quantities: the brief was wrong")
print("     to set them against each other. Against the fair baseline the same four are %+.2f pp." % mf)
out["far_end"] = {"points": far, "mean_vs_naive_pp": mn, "mean_vs_fair_pp": mf}

print("\n" + "=" * 78)
print("Q3  The alpha interval: resampling unit and level")
print("=" * 78)
x0, x25 = col(A0, "ifeval"), col(A25, "ifeval")
random.seed(20260919)
B = 10000
diffs = []
for _ in range(B):
    a = [random.choice(x0) for _ in x0]; b = [random.choice(x25) for _ in x25]
    diffs.append(st.mean(b) - st.mean(a))
diffs.sort()
lo, hi = diffs[int(.025 * B)], diffs[int(.975 * B)]
obs = st.mean(x25) - st.mean(x0)
print("  unit = one TRAINING SEED (a whole run), resampled independently within each arm,")
print("  %d resamples, 95%% percentile interval. Seeds are NOT matched across arms." % B)
print("  observed %+.2f pp   CI [%+.2f, %+.2f] pp   -> crosses zero" % (obs * 100, lo * 100, hi * 100))
# matched-seed variant, since both arms ran seeds 42-46
pairs = [(A[a]["ifeval"], A[b]["ifeval"]) for a, b in zip(A0, A25)]
md = [b - a for a, b in pairs]
print("  matched-by-seed paired differences (pp): %s" % ", ".join("%+.1f" % (d * 100) for d in md))
print("  paired mean %+.2f pp, paired SD %.2f pp, %d/%d positive"
      % (st.mean(md) * 100, st.stdev(md) * 100, sum(1 for d in md if d > 0), len(md)))
out["alpha"] = {"unit": "training seed", "B": B, "level": 0.95, "obs_pp": obs * 100,
                "ci_pp": [lo * 100, hi * 100], "paired_diffs_pp": [d * 100 for d in md]}

print("\n" + "=" * 78)
print("Q4  armBAL: per-seed scores, exposure, selection rule")
print("=" * 78)
print("  %-14s %9s %9s %11s" % ("run", "IFEval", "MGSM", "GreekMMLU"))
for l in BAL:
    m = A[l]
    print("  %-14s %9.4f %9.4f %11.3f" % (l, m["ifeval"], m["mgsm"], m.get("greekmmlu") or 0))
for m in ("ifeval", "mgsm", "greekmmlu"):
    xs = col(BAL, m)
    print("  %-10s mean %.4f  SD %.2f pp  vs parent_ckptcfg %s" % (
        m, st.mean(xs), st.stdev(xs) * 100,
        ("%+.1f pp" % ((st.mean(xs) - pf[m]) * 100)) if pf.get(m) is not None else "(no fair baseline)"))
print("\n  EXPOSURE, which is NOT held constant:")
print("    standard arms  343 pairs, 43 optimiser steps/epoch, 129 steps at ep3")
print("    armBAL         274 pairs, 35 optimiser steps/epoch, 105 steps at ep3  (-18.6%% of steps)")
print("    at lr 2e-6 that is 2.58e-4 of nominal movement against 2.10e-4, i.e. armBAL also moved LESS.")
print("  SELECTION RULE: greedy match on |chosen words - rejected words| over the 397 provenance-joined")
print("    pairs, keeping 274; it changes the length distribution AND which examples are present.")
out["bal"] = {l: {k: A[l].get(k) for k in ("ifeval", "mgsm", "greekmmlu")} for l in BAL}
out["bal"]["exposure"] = {"pairs": 274, "steps_ep3": 105, "std_pairs": 343, "std_steps_ep3": 129,
                          "movement": 2.10e-4, "std_movement": 2.58e-4}

print("\n" + "=" * 78)
print("Q6  What one served-lane sign is")
print("=" * 78)
SERVED = ["math500_el", "math500_en", "ifbench"]
signs = {"pos": 0, "neg": 0, "tie": 0, "missing": 0}
rows = []
for l in sorted(set(A0 + A25 + BAL + IPO)):
    for m in SERVED:
        v, p = A.get(l, {}).get(m), pn.get(m)
        if v is None or p is None: signs["missing"] += 1; continue
        k = "pos" if v > p else ("neg" if v < p else "tie")
        signs[k] += 1; rows.append((l, m, v, p, k))
print("  unit = one (model, served benchmark) cell vs the parent on the SAME benchmark.")
print("  over the %d epoch-3 replication runs x %d benchmarks: %d positive, %d negative, %d TIED, %d missing"
      % (len(set(A0 + A25 + BAL + IPO)), len(SERVED), signs["pos"], signs["neg"], signs["tie"], signs["missing"]))
print("  Ties were previously dropped. The cells are NOT independent: the same 500/300 items are")
print("  reused for every model, and the 5 seeds within an arm share data and recipe.")
print("  This is a DESCRIPTIVE tally. It is not a valid sign test and no p-value is quoted from it.")
out["served_signs"] = signs

json.dump(out, open(os.path.join(ROOT, "results/G4F6P1--DPO01/evidence_bundle.json"), "w"), indent=1)
print("\nwrote results/G4F6P1--DPO01/evidence_bundle.json")
