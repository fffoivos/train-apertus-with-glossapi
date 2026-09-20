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
  AMENDED 20 Sept, BEFORE any Q1 result was scored, because the original plan could not work:
  a run-level test on 3 seeds cannot support significance at all. Simulating at arm05's observed
  MGSM between-seed SD (1.95 pp, so ~2.76 pp per seed-matched difference), the 95% percentile
  bootstrap excludes zero 24.9% of the time when the true effect is ZERO. That is not a 5% test.
  The reason is structural: with 3 paired observations an exact sign/permutation test has minimum
  two-sided p = 2/2^3 = 0.25, so no calibrated run-level test can reach 0.05 here.

  Therefore:
    PRIMARY   item-level, seed-matched: NM_s vs RC_s for s = 42, 43, 44 on MGSM's 250 items,
              exact McNemar per pair, Holm-corrected across the three pairs. This is properly
              calibrated and has real power, at the cost of treating each run as fixed.
    SECONDARY run-level group means and every per-seed value, reported DESCRIPTIVELY with the
              per-seed numbers shown. No significance is claimed from 3 runs, and the run-level
              bootstrap interval is printed only as a dispersion summary, labelled as such.
  A null on the primary means "no item-level difference detectable between these particular runs",
  not "the pairs are irrelevant" and not equality.
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

    def contrast(a, b, task, why, paired=False):
        """paired=True only when the two groups are seed-matched run-for-run (NM42<->RC42, etc.);
        stats.seed_bootstrap returns ci_pp as a [lo, hi] LIST, not lo_pp/hi_pp keys."""
        xa, xb = table.get(a, {}).get(task, []), table.get(b, {}).get(task, [])
        if len(xa) < 2 or len(xb) < 2:
            print("  %-46s INCOMPLETE (%d vs %d runs)" % (why, len(xa), len(xb))); return
        if paired and len(xa) != len(xb):
            print("  %-46s NOT PAIRABLE (%d vs %d runs) - falling back to unpaired" % (why, len(xa), len(xb)))
            paired = False
        r = stats.paired_seed_bootstrap(xa, xb) if paired else stats.seed_bootstrap(xa, xb)
        lo, hi = r["ci_pp"]
        verdict = "contains zero" if lo <= 0 <= hi else "excludes zero (SEE CALIBRATION WARNING)"
        res["contrasts"]["%s|%s|%s" % (a, b, task)] = dict(r, design=r["design"])
        print("  %-46s %+7.2f pp   95%% [%+.2f, %+.2f]  %-13s %s"
              % (why, r["delta_pp"], lo, hi, verdict, r["design"]))

    def item_level(a_labels, b_labels, task, metric, why):
        """Seed-matched item-level comparison: the only properly calibrated test available at n=3."""
        print("  %s" % why)
        pv, rows = [], []
        for la, lb in zip(a_labels, b_labels):
            try:
                ra = from_lm_eval(rundir(root, la), task, metric); rb = from_lm_eval(rundir(root, lb), task, metric)
                r = compare(ra, rb)
            except (ComparabilityError, SystemExit) as e:
                print("    %-22s REFUSED: %s" % (la + " vs " + lb, str(e).splitlines()[-1].strip(" -"))); continue
            pv.append(r["p_mcnemar"]); rows.append((la, lb, r))
        if not rows: return
        adj = stats.holm(pv)
        for (la, lb, r), q in zip(rows, adj):
            print("    %-26s %+6.2f pp  %3d gained / %3d lost  p=%.4f  Holm=%.4f%s"
                  % (la.replace("_ep3", "") + " vs " + lb.replace("_ep3", ""), r["delta_pp"], r["gained"],
                     r["lost"], r["p_mcnemar"], q, "  *" if q < 0.05 else ""))
        res["contrasts"]["itemlevel|%s|%s" % (why, task)] = [
            {"a": la, "b": lb, "delta_pp": r["delta_pp"], "gained": r["gained"], "lost": r["lost"],
             "p": r["p_mcnemar"], "holm": q} for (la, lb, r), q in zip(rows, adj)]

    NMS = ["armNM42_ep3", "armNM43_ep3", "armNM44_ep3"]
    RCS = ["armRC42_ep3", "armRC43_ep3", "armRC44_ep3"]
    for task, metric, nice in GEN:
        print("\n" + "=" * 100); print("Q1 PRIMARY on %s -- item level, seed-matched, exact McNemar + Holm" % nice); print("=" * 100)
        item_level(RCS, NMS, task, metric, "NM - RC, per seed (the maths pairs, holding row count fixed)")

    print("\n" + "=" * 100)
    print("Q1 SECONDARY -- run-level means. DESCRIPTIVE ONLY: at n=3 the interval below excludes zero")
    print("~25%% of the time under a true null, so it is a dispersion summary, not a test.")
    print("=" * 100)
    for name, labels in GROUPS:
        for task, _, nice in GEN:
            xs = table.get(name, {}).get(task, [])
            if xs: print("  %-28s %-12s %s" % (name, nice, " ".join("%.4f" % x for x in xs)))
    for task, _, nice in GEN:
        print("\n" + "=" * 100); print("Q1 on %s  (the question is MGSM; IFEval is context)" % nice); print("=" * 100)
        contrast("FULL  343 pairs (arm05)", "NM    287, maths removed", task, "NM - FULL   (removing the 56 maths pairs)")
        contrast("FULL  343 pairs (arm05)", "RC    287, random removed", task, "RC - FULL   (removing 56 random pairs)")
        contrast("RC    287, random removed", "NM    287, maths removed", task, "NM - RC     <- Q1 PRIMARY (seed-matched)", paired=True)

    print("\n" + "=" * 100); print("Q3  IPO, at matched beta"); print("=" * 100)
    for task, _, nice in GEN:
        contrast("armIPO   sigmoid, beta 10", "TRUEIPO  ipo, beta 10", task, "%s: TRUEIPO - armIPO (objective)" % nice, paired=True)
        contrast("FULL  343 pairs (arm05)", "TRUEIPO  ipo, beta 10", task, "%s: TRUEIPO - FULL (vs the best sigmoid)" % nice)

    if res["refused"]:
        print("\n" + "=" * 100); print("REFUSED by the comparability guard -- these did NOT contribute to any mean above")
        for k, v in res["refused"].items():
            for m in v: print("  %-28s %s" % (k, m))
    if out:
        with open(out, "w") as fh: json.dump(res, fh, indent=1, sort_keys=True)
        print("\nwrote %s" % out)

main()
