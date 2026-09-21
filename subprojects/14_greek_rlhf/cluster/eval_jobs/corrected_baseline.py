#!/usr/bin/env python3
"""Every arm against a FAIR parent baseline.

transformers 5.16.1 re-serialised the checkpoints, so the parent and the arms differ in
generation-relevant config (eos_token_id 2 vs 68, pad absent vs 3, use_cache true vs false).
`parent_ckptcfg` is the parent's own weights scored under a checkpoint's generation config, so the
difference between it and `parent` is the tooling artefact, isolated from any training effect.

Comparing arms to `parent` therefore charges training for a penalty the tooling created.
"""
import glob, json, os, statistics as st

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/full"

def get(label):
    fs = glob.glob(os.path.join(R, label, "**", "results_*.json"), recursive=True)
    if not fs:
        return None
    d = json.load(open(fs[0]))["results"]
    return {"ifeval": d.get("ifeval_greek", {}).get("prompt_level_strict_acc,none"),
            "mgsm": d.get("mgsm_greek", {}).get("exact_match,none")}

naive, fair = get("parent"), get("parent_ckptcfg")
print("THE CONFOUND, isolated (same weights, different generation config):")
for m in ("ifeval", "mgsm"):
    print("   %-7s parent %.4f  vs parent_ckptcfg %.4f   = %+.1f pp of TOOLING, not training"
          % (m, naive[m], fair[m], (fair[m] - naive[m]) * 100))

GROUPS = {
    "alpha 0     n=5": ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"],
    "alpha 0.25  n=5": ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"],
    "length-balanced n=3": ["armBAL_ep3", "armBALs43_ep3", "armBALs44_ep3"],
    "IPO beta 10 n=2": ["armIPO42_ep3", "armIPO43_ep3"],
    "4e-6 movement n=1": ["arm08_ep3"],
}
print("\n%-22s %8s %9s %9s   %8s %9s %9s" % ("group", "IFEval", "vs naive", "vs FAIR", "MGSM", "vs naive", "vs FAIR"))
print("-" * 82)
for name, labels in GROUPS.items():
    gs = [g for g in (get(l) for l in labels) if g and g["ifeval"] is not None]
    if not gs:
        continue
    mi = st.mean([g["ifeval"] for g in gs]); mm = st.mean([g["mgsm"] for g in gs])
    print("%-22s %8.4f %+9.1f %+9.1f   %8.4f %+9.1f %+9.1f" % (
        name, mi, (mi - naive["ifeval"]) * 100, (mi - fair["ifeval"]) * 100,
        mm, (mm - naive["mgsm"]) * 100, (mm - fair["mgsm"]) * 100))
print("\nnoise floor at n=5: IFEval sd ~1.0pp, MGSM sd ~1.6pp")
