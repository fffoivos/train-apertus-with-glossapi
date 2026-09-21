#!/usr/bin/env python3
"""GreekMMLU 250 for every DPO01 model.

The CPT-card finalizer refuses these checkpoints ("HF evaluation geometry drift: rope_theta nan")
because it guards on a field Apertus does not use — it stores rope config under `rope_parameters`.
That step only writes a receipt; the native runner had already scored every model, so the headline
file is the score of record here.
"""
import glob, json, os, statistics as st

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/greekmmlu"

def acc(label):
    fs = glob.glob(os.path.join(R, label, "*_native_mcq_headline.json"))
    if not fs:
        return None
    rows = json.load(open(fs[0]))
    for r in rows:
        if r.get("subject") == "__all__":
            return r["accuracy"], r.get("n"), r.get("correct")
    return None

par = acc("parent")
if not par:
    raise SystemExit("no parent score")
print("parent  GreekMMLU %.3f  (%d/%d)\n" % (par[0], par[2], par[1]))

GROUPS = {
    "alpha 0        n=5": ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"],
    "alpha 0.25     n=5": ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"],
    "length-balanced n=3": ["armBAL_ep3", "armBALs43_ep3", "armBALs44_ep3"],
    "IPO beta 10    n=2": ["armIPO42_ep3", "armIPO43_ep3"],
    "4e-6           n=1": ["arm08_ep3"],
    "5 epochs       n=1": ["arm07_ep5"],
}
print("%-22s %9s %8s %9s %9s" % ("group", "mean", "sd", "vs parent", "range"))
print("-" * 64)
for name, labels in GROUPS.items():
    xs = [a[0] for a in (acc(l) for l in labels) if a]
    if not xs:
        print("%-22s (none scored)" % name); continue
    sd = st.stdev(xs) if len(xs) > 1 else 0.0
    print("%-22s %9.3f %8.3f %+9.1f  %.3f..%.3f" % (
        name, st.mean(xs), sd, (st.mean(xs) - par[0]) * 100, min(xs), max(xs)))
n = len(glob.glob(os.path.join(R, "*", "*_native_mcq_headline.json")))
print("\n%d models scored, 250 items each" % n)
