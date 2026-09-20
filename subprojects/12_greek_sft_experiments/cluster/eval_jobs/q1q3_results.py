#!/usr/bin/env python3
"""Q1 and Q3, read through the same guard as the main scorecard.

DECISION RULES, WRITTEN BEFORE THE NUMBERS EXISTED (committed 2026-09-20, pre-results).
The round has already been read wrong four times by fitting a story to whatever landed; these are
fixed in advance so the reading cannot be.

Q1 - does the MGSM gain come from the 56 embedded-quantitative pairs?
  Three groups, all anchored alpha=0.25, all 3 epochs, differing ONLY in which pairs are present:
    FULL = arm05 group   343 train pairs          (5 seeds, already scored)
    NM   = nomaths       287, the 56 maths pairs removed   (3 seeds)
    RC   = randomcut     287, 56 RANDOM pairs removed      (3 seeds)  <- the "less data" control
  RC is what makes NM interpretable. Read the MGSM group means:
    (a) NM below RC, by more than the two groups' seed spread   -> the quantitative pairs carry the
        gain. This is the hypothesis.
    (b) NM ~= RC, both below FULL                               -> data VOLUME, not maths content.
    (c) NM ~= RC ~= FULL                                        -> those pairs are not the lever at
        all, and the MGSM gain comes from something we have not identified.
  "~=" means the 95% interval on the group difference contains zero. With 3 seeds a bootstrap
  interval is wide; a null here is weak evidence, and is reported as such rather than as (c).
  IFEval and Global-MMLU-Lite are reported alongside but are not what Q1 asks.

Q3 - IPO, actually run this time.
  TRUEIPO (loss_type=ipo, beta=10) against armIPO (the same config that SAID ipo and trained sigmoid,
  because the trainer hardcoded it) and against FULL (sigmoid, beta=0.1).
    * TRUEIPO vs armIPO isolates the OBJECTIVE at matched beta.
    * Any earlier claim about "IPO" on this page was about armIPO, i.e. about sigmoid at beta=10.
  No pass/fail gate is asserted here: the round's original IPO gate was written against runs that
  never used the objective, so it is not a pre-registration that survived. This measures; it does
  not adjudicate.

  q1q3_results.py <frozen_dir> [--json OUT]
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from rlhf.evals import from_lm_eval, compare, ComparabilityError, stats
from frozen_results import GEN, rundir, acc_of, gmmlu_lite

GROUPS = [("FULL  343 pairs (arm05)", ["arm05_ep3", "arm05s43_ep3", "arm05s44_ep3", "arm05s45_ep3", "arm05s46_ep3"]),
          ("NM    287, maths removed", ["armNM42_ep3", "armNM43_ep3", "armNM44_ep3"]),
          ("RC    287, random removed", ["armRC42_ep3", "armRC43_ep3", "armRC44_ep3"]),
          ("TRUEIPO  ipo, beta 10", ["armTRUEIPO42_ep3", "armTRUEIPO43_ep3"]),
          ("armIPO   sigmoid, beta 10", ["armIPO42_ep3", "armIPO43_ep3"])]

def group_scores(root, P, labels, task, metric):
    """Per-seed accuracies, each one gated against the parent. A refused run is NOT silently dropped."""
    accs, refused = [], []
    for l in labels:
        try:
            d = rundir(root, l)
        except SystemExit:
            refused.append("%s: no run directory" % l); continue
        try:
            accs.append(compare(from_lm_eval(P, task, metric), from_lm_eval(d, task, metric))["acc_b"])
        except ComparabilityError as e:
            refused.append("%s: %s" % (l, str(e).splitlines()[-1].strip(" -")))
    return accs, refused

def main():
    root = sys.argv[1]
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    P = rundir(root, "parent")
    res, table = {"groups": {}, "contrasts": {}, "refused": {}}, {}

    print("=" * 100)
    print("Q1 / Q3 arms, frozen date, geometry repaired, weights the only difference from the parent")
    print("=" * 100)
    print("%-28s %5s %11s %8s %11s %8s %12s" % ("group", "seeds", "IFEval", "sd", "MGSM", "sd", "gMMLU-Lite"))
    print("-" * 100)
    pb = {t: acc_of(P, t, m)[0] for t, m, _ in GEN}
    pb["gmmlu_lite"] = gmmlu_lite(P)
    print("%-28s %5s %11.4f %8s %11.4f %8s %12.4f" % ("parent", "1", pb["ifeval_greek"], "-", pb["mgsm_greek"], "-", pb["gmmlu_lite"]))
    for name, labels in GROUPS:
        cells, g = [], {}
        for task, metric, _ in GEN:
            accs, ref = group_scores(root, P, labels, task, metric)
            if ref: res["refused"].setdefault(name, []).extend(ref)
            g[task] = accs
            cells += ["%11.4f" % (sum(accs) / len(accs)) if accs else "%11s" % "-",
                      "%8.2f" % stats.seed_sd_pp(accs) if len(accs) > 1 else "%8s" % "-"]
        gm = []
        for l in labels:
            try:
                v, _ = gmmlu_lite(rundir(root, l), P)
                if v is not None: gm.append(v)
            except SystemExit: pass
        g["gmmlu_lite"] = gm
        table[name] = g; res["groups"][name] = {k: v for k, v in g.items()}
        print("%-28s %5d %s %12s" % (name, len(g["mgsm_greek"]), " ".join(cells),
                                     "%.4f" % (sum(gm) / len(gm)) if gm else "-"))

    def contrast(a, b, task, why):
        xa, xb = table.get(a, {}).get(task, []), table.get(b, {}).get(task, [])
        if not xa or not xb:
            print("  %-46s INCOMPLETE (%d vs %d runs)" % (why, len(xa), len(xb))); return
        d = (sum(xb) / len(xb) - sum(xa) / len(xa)) * 100
        ci = stats.seed_bootstrap(xa, xb)
        lo, hi = ci["lo_pp"], ci["hi_pp"]
        verdict = "contains zero" if lo <= 0 <= hi else "excludes zero"
        res["contrasts"]["%s|%s|%s" % (a, b, task)] = {"delta_pp": d, "lo_pp": lo, "hi_pp": hi, "n_a": len(xa), "n_b": len(xb)}
        print("  %-46s %+7.2f pp   95%% [%+.2f, %+.2f]  %s" % (why, d, lo, hi, verdict))

    for task, _, nice in GEN:
        print("\n" + "=" * 100); print("Q1 on %s  (the question is MGSM; IFEval is context)" % nice); print("=" * 100)
        contrast("FULL  343 pairs (arm05)", "NM    287, maths removed", task, "NM - FULL   (removing the 56 maths pairs)")
        contrast("FULL  343 pairs (arm05)", "RC    287, random removed", task, "RC - FULL   (removing 56 random pairs)")
        contrast("RC    287, random removed", "NM    287, maths removed", task, "NM - RC     <- Q1's actual contrast")

    print("\n" + "=" * 100); print("Q3  IPO, at matched beta"); print("=" * 100)
    for task, _, nice in GEN:
        contrast("armIPO   sigmoid, beta 10", "TRUEIPO  ipo, beta 10", task, "%s: TRUEIPO - armIPO (objective)" % nice)
        contrast("FULL  343 pairs (arm05)", "TRUEIPO  ipo, beta 10", task, "%s: TRUEIPO - FULL (vs the best sigmoid)" % nice)

    if res["refused"]:
        print("\n" + "=" * 100); print("REFUSED by the comparability guard -- these did NOT contribute to any mean above")
        for k, v in res["refused"].items():
            for m in v: print("  %-28s %s" % (k, m))
    if out:
        with open(out, "w") as fh: json.dump(res, fh, indent=1, sort_keys=True)
        print("\nwrote %s" % out)

main()
