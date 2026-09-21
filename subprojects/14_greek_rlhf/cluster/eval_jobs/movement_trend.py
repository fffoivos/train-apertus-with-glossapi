#!/usr/bin/env python3
"""Does 'more movement -> less damage' keep going, or turn over?

The two arms that extend the axis past 3 epochs at 2e-6:
  arm08  4e-6 x 129 steps = 5.16e-4   (double the learning rate)
  arm07  2e-6 x 172/215   = 3.44/4.30e-4  (4 and 5 epochs)
Read against the noise floor measured at n=5: IFEval sd ~1.0pp, MGSM sd ~1.6pp.
"""
import glob, json, os, statistics as st

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/full"

def get(label):
    fs = glob.glob(os.path.join(R, label, "**", "results_*.json"), recursive=True)
    if not fs:
        return None
    d = json.load(open(fs[0]))["results"]
    cells = [v for t, mm in d.items() if t.startswith("global_mmlu_")
             for k, v in mm.items() if k.startswith("acc,") and isinstance(v, float)]
    return {"ifeval": d.get("ifeval_greek", {}).get("prompt_level_strict_acc,none"),
            "mgsm": d.get("mgsm_greek", {}).get("exact_match,none"),
            "gmmlu": (sum(cells) / len(cells)) if cells else None}

# (label, lr, steps) along the movement axis
POINTS = [
    ("arm01_ep1", 2e-6, 43), ("arm05_ep1", 2e-6, 43),
    ("arm01_ep2", 2e-6, 86), ("arm05_ep2", 2e-6, 86),
    ("arm01_ep3", 2e-6, 129), ("arm05_ep3", 2e-6, 129),
    ("arm07_ep3", 2e-6, 129),
    ("arm08_ep1", 4e-6, 43),
    ("arm07_ep4", 2e-6, 172),
    ("arm08_ep2", 4e-6, 86),
    ("arm07_ep5", 2e-6, 215),
    ("arm08_ep3", 4e-6, 129),
]
par = get("parent")
print("parent   IFEval %.4f   MGSM %.4f   gMMLU %.4f" % (par["ifeval"], par["mgsm"], par["gmmlu"]))
print("noise floor at n=5: IFEval sd ~1.0pp, MGSM sd ~1.6pp (pooled)\n")
print("%-11s %10s %11s %11s %11s" % ("model", "lr x steps", "IFEval d", "MGSM d", "gMMLU d"))
print("-" * 58)
rows = []
for label, lr, steps in sorted(POINTS, key=lambda t: t[1] * t[2]):
    g = get(label)
    if not g or g["ifeval"] is None:
        continue
    mv = lr * steps
    di = (g["ifeval"] - par["ifeval"]) * 100
    dm = (g["mgsm"] - par["mgsm"]) * 100
    dg = (g["gmmlu"] - par["gmmlu"]) * 100
    rows.append((mv, label, di, dm, dg))
    print("%-11s %10.2e %+11.1f %+11.1f %+11.1f" % (label, mv, di, dm, dg))

print("\nfar end only (movement > 2.6e-4, i.e. past 3 epochs at 2e-6):")
far = [r for r in rows if r[0] > 2.6e-4]
for mv, label, di, dm, dg in far:
    print("   %-11s %.2e  IFEval %+.1f  MGSM %+.1f  gMMLU %+.1f" % (label, mv, di, dm, dg))
if far:
    print("   mean IFEval delta at the far end: %+.2f pp" % st.mean([r[2] for r in far]))
    print("   mean MGSM   delta at the far end: %+.2f pp" % st.mean([r[3] for r in far]))
