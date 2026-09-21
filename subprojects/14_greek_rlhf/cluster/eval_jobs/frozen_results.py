#!/usr/bin/env python3
"""The corrected DPO01 scorecard, read through the guard.

Every number here comes from `rlhf.evals.compare()`, so a comparison that is not controlled REFUSES
instead of printing: same frozen prompts, same effective generation settings, same rotary geometry,
same items and gold, only the weights differing. Run on the cluster after dpo01_frozen_rescore.sh.

  frozen_results.py <frozen_dir> [--json OUT]
"""
import glob, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from rlhf.evals import from_lm_eval, compare, ComparabilityError, stats

GEN = [("ifeval_greek", "prompt_level_strict_acc", "Greek IFEval"), ("mgsm_greek", "exact_match", "Greek MGSM")]
GROUPS = [("plain DPO, alpha 0", ["arm01_ep3", "arm01s43_ep3", "arm01s44_ep3", "arm01s45_ep3", "arm01s46_ep3"]),
          ("anchored, alpha 0.25", ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"]),
          ("length-balanced subset", ["armBAL_ep3", "armBALs43_ep3", "armBALs44_ep3"]),
          ("IPO, beta 10", ["armIPO42_ep3", "armIPO43_ep3"])]

def rundir(root, label):
    """A model's run directory. The suffix is its config mode (own / verbatim / export), so resolve it."""
    ds = sorted(d for d in glob.glob(os.path.join(root, label + "__*cfg")) if os.path.isdir(d))
    if len(ds) != 1:
        raise SystemExit("expected exactly one run directory for %s, found %d" % (label, len(ds)))
    return ds[0]

def mmlu_lanes(d):
    return sorted(os.path.basename(f).split("samples_")[1].rsplit("_", 1)[0]
                  for f in glob.glob(os.path.join(d, "**", "samples_global_mmlu_*.jsonl"), recursive=True))

def acc_of(d, task, metric):
    r = from_lm_eval(d, task, metric); return sum(r.items.values()) / float(len(r.items)), r

def gmmlu_lite(d, ref=None):
    """The six language groups, item-weighted -- never the 42 rows (R-DPO7a).

    R-DPO13 [MEDIUM]: this used to read the leaves directly, bypassing the comparability gate the rest
    of the file advertises. When `ref` is given every leaf goes through compare(), so a lane that is not
    a controlled comparison raises instead of quietly contributing to a mean.
    """
    langs = ["global_mmlu_%s" % l for l in ("de", "en", "es", "fr", "it", "pt")]
    EXPECTED_LEAVES, EXPECTED_ITEMS = 36, 2400
    leaves = mmlu_lanes(d)
    if len(leaves) != EXPECTED_LEAVES:
        msg = ["%s: %d leaves, expected %d" % (os.path.basename(d), len(leaves), EXPECTED_LEAVES)]
        return (None, msg) if ref is not None else None
    per, refused, total_items = {}, [], 0
    for lang in langs:
        ls = [t for t in leaves if t.startswith(lang + "_")]
        if not ls:
            return (None, ["%s: no leaves" % lang]) if ref is not None else None
        n = c = 0
        for t in ls:
            r = from_lm_eval(d, t, "acc")
            if ref is not None:
                try:
                    compare(from_lm_eval(ref, t, "acc"), r)
                except ComparabilityError as e:
                    # R-DPO14 [MEDIUM]: a refused leaf used to be skipped, and the surviving leaves still
                    # produced a mean. An aggregate missing a lane is not the benchmark: refuse the whole thing.
                    refused.append("%s: %s" % (t, str(e).splitlines()[-1].strip(" -")))
                    return None, refused
            n += len(r.items); c += sum(r.items.values())
        if not n:
            return (None, refused) if ref is not None else None
        per[lang] = c / float(n); total_items += n
    if total_items != EXPECTED_ITEMS:
        refused.append("%s: %d items, expected %d" % (os.path.basename(d), total_items, EXPECTED_ITEMS))
        return (None, refused) if ref is not None else None
    val = sum(per.values()) / len(per)
    return (val, refused) if ref is not None else val

def main():
    root = sys.argv[1]
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    P = rundir(root, "parent")
    res = {"controlled": {}, "refused": {}, "artefact": {}, "equality_check": {}}

    print("=" * 96)
    print("E6 measured directly: the parent's OWN weights, mis-loaded exactly as every arm was")
    print("=" * 96)
    a, b = rundir(root, "parent_ckptgen"), rundir(root, "parent_exportcfg")
    for task, metric, nice in GEN:
        try:
            r = compare(from_lm_eval(a, task, metric), from_lm_eval(b, task, metric), policy="geometry")
            res["artefact"][task] = r
            print("  %-14s correct geometry %.4f -> mis-loaded %.4f   %+.2f pp   (%d gained / %d lost, p=%.3f)"
                  % (nice, r["acc_a"], r["acc_b"], r["delta_pp"], r["gained"], r["lost"], r["p_mcnemar"]))
        except ComparabilityError as e:
            print("  %-14s REFUSED: %s" % (nice, str(e).splitlines()[-1].strip(" -")))
    gp, gx = gmmlu_lite(a), gmmlu_lite(b)   # geometry policy: the two differ by design, so no per-lane gate here
    if gp and gx:
        res["artefact"]["gmmlu_lite"] = {"acc_a": gp, "acc_b": gx, "delta_pp": (gx - gp) * 100}
        print("  %-14s correct geometry %.4f -> mis-loaded %.4f   %+.2f pp" % ("Global-MMLU", gp, gx, (gx - gp) * 100))
    print("\n  ^ this is the size of the artefact ON THE PARENT'S WEIGHTS. Whether the same size applies to")
    print("    trained weights is an assumption; the arm rows below are what measure the arms.\n")

    print("=" * 96)
    print("Is the generation-config axis inert?  parent vs parent_ckptgen, same weights")
    print("=" * 96)
    for task, metric, nice in GEN:
        pa, _ = acc_of(P, task, metric); pb, _ = acc_of(rundir(root, "parent_ckptgen"), task, metric)
        same = "IDENTICAL" if abs(pa - pb) < 1e-12 else "DIFFER by %+.2f pp" % ((pb - pa) * 100)
        res["equality_check"][task] = {"parent": pa, "parent_ckptgen": pb}
        print("  %-14s %.4f vs %.4f   %s" % (nice, pa, pb, same))

    print("\n" + "=" * 96)
    print("THE CORRECTED SCORECARD  (frozen date, geometry repaired, weights the only difference)")
    print("=" * 96)
    print("%-24s %5s %10s %9s %10s %9s %12s %9s" % ("group", "runs", "IFEval", "d", "MGSM", "d", "gMMLU-Lite", "d"))
    print("-" * 96)
    pbase = {}
    for task, metric, _ in GEN: pbase[task] = acc_of(P, task, metric)[0]
    pbase["gmmlu_lite"] = gmmlu_lite(P)
    gmmlu_refused = []
    print("%-24s %5s %10.4f %9s %10.4f %9s %12.4f %9s"
          % ("parent", "1", pbase["ifeval_greek"], "-", pbase["mgsm_greek"], "-", pbase["gmmlu_lite"], "-"))
    for name, labels in GROUPS:
        cells, runs = [], 0
        for task, metric, _ in GEN:
            accs = []
            for l in labels:
                d = rundir(root, l)
                if not os.path.isdir(d): continue
                try:
                    r = compare(from_lm_eval(P, task, metric), from_lm_eval(d, task, metric))
                    accs.append(r["acc_b"]); res["controlled"].setdefault(task, {})[l] = r
                except ComparabilityError as e:
                    res["refused"].setdefault(task, {})[l] = str(e); print("  REFUSED %s/%s: %s" % (l, task, str(e).splitlines()[-1].strip(" -")))
            runs = max(runs, len(accs))
            cells.append((st.mean(accs), (st.mean(accs) - pbase[task]) * 100, stats.seed_sd_pp(accs)) if accs else None)
        gs = []
        for l in labels:
            try: d = rundir(root, l)
            except SystemExit: continue
            v, ref = gmmlu_lite(d, ref=P)          # every leaf must pass the gate against the parent
            gmmlu_refused += ["%s/%s" % (l, x) for x in ref]
            if v: gs.append(v)
        gcell = (st.mean(gs), (st.mean(gs) - pbase["gmmlu_lite"]) * 100, stats.seed_sd_pp(gs)) if gs else None
        row = "%-24s %5d" % (name, runs)
        for c in cells + [gcell]:
            row += (" %10.4f %+9.2f" % (c[0], c[1])) if c else (" %10s %9s" % ("-", "-"))
        print(row)
        for (task, _, _), c in zip(GEN, cells):
            if c and c[2] is not None: res.setdefault("groups", {}).setdefault(name, {})[task] = {"mean": c[0], "delta_pp": c[1], "across_run_sd_pp": c[2]}
        if gcell: res.setdefault("groups", {}).setdefault(name, {})["gmmlu_lite"] = {"mean": gcell[0], "delta_pp": gcell[1], "across_run_sd_pp": gcell[2], "n_runs": len(gs)}
    res["gmmlu_lanes_refused"] = gmmlu_refused
    print("\nGlobal-MMLU leaves refused by the comparability gate: %d" % len(gmmlu_refused))
    print("\nacross-run SD (pp), now free of evaluation-date mixing:")
    for name, _ in GROUPS:
        g = (res.get("groups") or {}).get(name, {})
        if g: print("  %-24s %s" % (name, "  ".join("%s %.2f" % (t.split('_')[0], v["across_run_sd_pp"]) for t, v in sorted(g.items()) if "across_run_sd_pp" in v)))
    print("\nNOTE: seeds 42-43 and 44-46 were TRAINED with different dates in their prompts. This re-score")
    print("removes evaluation-date mixing; it cannot repair that retrospectively.")
    if out:
        with open(out, "w") as fh: json.dump(res, fh, indent=1, default=str)
        print("\nwrote %s" % out)

main()
