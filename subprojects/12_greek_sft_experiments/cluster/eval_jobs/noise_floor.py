#!/usr/bin/env python3
"""The noise floor on the primary endpoint, and what survives it.

Two floors:
  cross-seed  - the same arm trained at 5 different seeds
  same-seed   - two runs that should be bit-identical (arm05_ep3 vs arm07_ep3), differing only
                through ZeRO-3 reduction order under bf16

Then the alpha test: is the arm01-vs-arm05 difference larger than the within-arm spread?
"""
import glob, json, os, statistics as st, random

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/full"

def get(label):
    fs = glob.glob(os.path.join(R, label, "**", "results_*.json"), recursive=True)
    if not fs:
        return None
    d = json.load(open(fs[0]))["results"]
    cells = [v for t, mm in d.items() if t.startswith("global_mmlu_")
             for k, v in mm.items() if k.startswith("acc,") and isinstance(v, float)]
    return {
        "ifeval": d.get("ifeval_greek", {}).get("prompt_level_strict_acc,none"),
        "mgsm": d.get("mgsm_greek", {}).get("exact_match,none"),
        "gmmlu": (sum(cells) / len(cells)) if cells else None,
    }

FAMILY = {
    "alpha 0    (arm01)": ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"],
    "alpha 0.25 (arm05)": ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"],
}
par = get("parent")
print("parent: IFEval %.4f  MGSM %.4f  gMMLU %.4f\n" % (par["ifeval"], par["mgsm"], par["gmmlu"]))

vals = {}
for name, labels in FAMILY.items():
    got = [(l, get(l)) for l in labels]
    got = [(l, g) for l, g in got if g and g["ifeval"] is not None]
    vals[name] = got
    print("%s  — n=%d" % (name, len(got)))
    for metric in ("ifeval", "mgsm", "gmmlu"):
        xs = [g[metric] for _, g in got if g[metric] is not None]
        if len(xs) < 2:
            continue
        print("   %-7s mean %.4f  sd %.4f  range %.4f..%.4f  (spread %.1f pp)" % (
            metric, st.mean(xs), st.stdev(xs), min(xs), max(xs), (max(xs) - min(xs)) * 100))
    print("     per-seed IFEval:", ", ".join("%s %.4f" % (l.replace("_ep3", ""), g["ifeval"]) for l, g in got))
    print()

a, b = get("arm05_ep3"), get("arm07_ep3")
if a and b:
    print("SAME-SEED floor (arm05_ep3 vs arm07_ep3, identical in intent):")
    for m in ("ifeval", "mgsm", "gmmlu"):
        if a[m] is not None and b[m] is not None:
            print("   %-7s %.4f vs %.4f   = %+.1f pp" % (m, a[m], b[m], (b[m] - a[m]) * 100))
    print()

k = list(FAMILY)
A = [g["ifeval"] for _, g in vals[k[0]]]
B = [g["ifeval"] for _, g in vals[k[1]]]
if len(A) >= 2 and len(B) >= 2:
    diff = (st.mean(B) - st.mean(A)) * 100
    pooled = ((st.stdev(A) ** 2 + st.stdev(B) ** 2) / 2) ** 0.5 * 100
    rnd = random.Random(42)
    ds = []
    for _ in range(10000):
        sa = [rnd.choice(A) for _ in A]; sb = [rnd.choice(B) for _ in B]
        ds.append((st.mean(sb) - st.mean(sa)) * 100)
    ds.sort()
    lo, hi = ds[250], ds[9750]
    print("THE ALPHA TEST — does alpha 0.25 beat alpha 0 on IFEval?")
    print("   difference of means %+.2f pp   within-arm sd %.2f pp" % (diff, pooled))
    print("   95%% bootstrap CI [%+.2f, %+.2f]" % (lo, hi))
    print("   VERDICT:", "SURVIVES — interval excludes zero" if (lo > 0 or hi < 0)
          else "INSIDE THE NOISE FLOOR — 'alpha 0.25 is best' is withdrawn")
