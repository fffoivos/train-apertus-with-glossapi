#!/usr/bin/env python3
"""Q4: how much of the GreekMMLU official-label decline survives a label-position correction?

NOT "contextual calibration", and NOT a demonstration that knowledge is intact (R-DPO15 BLOCKER).
What this implements is **model-specific batch log-score centering**: for each model, take the mean
sum_logprob it assigns to each label POSITION across the whole scored batch, and subtract it before
ranking. Additive in log space; there is one estimator here, not two -- an earlier docstring described
a probability-marginal variant (divide by exp(mean)) that was never written.

  pred = argmax_i ( sum_logprob_i - bias_i ),  bias_i = mean over the batch of sum_logprob at position i

Three things this cannot do, all of which the page once claimed it did:
  * It cannot show the deficit is not real. The raw official-label loss IS a real multiple-choice
    performance cost; re-ranking under a different rule defines a different evaluator.
  * The correction is MODEL-SPECIFIC, so it can absorb genuine ability differences along with prior
    drift. Holding the correction fixed at the parent's own bias leaves roughly half the deficit
    (--parent-bias below).
  * bias_i pooled over all rows mixes the 2-, 3- and 4-choice populations (3,152 / 3,478 / 10,002),
    so position 3 is estimated from 4-choice items alone while position 0 uses every item. The
    stratified estimator below checks this; it does not change the conclusion.

Reported per model: raw, in-sample centered, 5-fold out-of-fold centered (rules out in-sample
fitting), out-of-fold centered within choice-count strata, and centered by the PARENT's bias.
Needs results produced with --save-choice-scores.
  label_calibration.py <dir-with-*_scores.json> [--suffix _scores] [--folds 5] [--seed 11]
"""
import glob, json, os, random, statistics as st, sys

def load(path):
    with open(path) as fh:
        d = json.load(fh)
    rows = []
    for r in d["rows"]:
        o = r["official_label"]
        cs = o.get("choice_scores")
        if not cs:
            raise SystemExit("%s has no choice_scores: re-run with --save-choice-scores" % os.path.basename(path))
        rows.append({"gold": r["answer_index"], "pred": o["pred_index"],
                     "lp": [c["sum_logprob"] for c in cs]})
    return d["model_label"], rows

def acc(rows, key):
    return sum(1 for r in rows if key(r) == r["gold"]) / float(len(rows))

def _bias(rows, idxs, n):
    per = [[rows[j]["lp"][i] for j in idxs if len(rows[j]["lp"]) > i] for i in range(n)]
    return [st.mean(x) if x else 0.0 for x in per]

def _bias_strat(rows, idxs):
    """One bias vector per choice-count stratum, so position 3 is never estimated from a population
    that position 0 does not share."""
    out = {}
    for k in sorted({len(r["lp"]) for r in rows}):
        sel = [j for j in idxs if len(rows[j]["lp"]) == k]
        if sel: out[k] = [st.mean([rows[j]["lp"][i] for j in sel]) for i in range(k)]
    return out

def _folds(n, k, seed):
    order = list(range(n)); random.Random(seed).shuffle(order)
    return [order[i::k] for i in range(k)]

def _acc(rows, bias_for):
    return 100.0 * sum(1 for j, r in enumerate(rows)
                       if max(range(len(r["lp"])), key=lambda i: r["lp"][i] - bias_for(j, r)[i]) == r["gold"]) / len(rows)

def estimators(rows, k, seed, parent_bias=None):
    """raw / in-sample / out-of-fold / out-of-fold within choice-count strata / parent-derived."""
    n = max(len(r["lp"]) for r in rows); zero = [0.0] * n
    fold = _folds(len(rows), k, seed)
    oof, oofs = {}, {}
    for fi, held in enumerate(fold):
        tr = [j for fj, g in enumerate(fold) if fj != fi for j in g]
        b, bs = _bias(rows, tr, n), _bias_strat(rows, tr)
        for j in held: oof[j], oofs[j] = b, bs[len(rows[j]["lp"])]
    all_b = _bias(rows, range(len(rows)), n)
    out = {"raw": _acc(rows, lambda j, r: zero), "in_sample": _acc(rows, lambda j, r: all_b),
           "out_of_fold": _acc(rows, lambda j, r: oof[j]),
           "out_of_fold_stratified": _acc(rows, lambda j, r: oofs[j]), "bias": all_b}
    if parent_bias is not None: out["parent_bias"] = _acc(rows, lambda j, r: parent_bias)
    return out

ESTS = ("raw", "in_sample", "out_of_fold", "out_of_fold_stratified", "parent_bias")

def main():
    d = sys.argv[1]
    suf = sys.argv[sys.argv.index("--suffix") + 1] if "--suffix" in sys.argv else "_scores"
    k = int(sys.argv[sys.argv.index("--folds") + 1]) if "--folds" in sys.argv else 5
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 11
    files = sorted(glob.glob(os.path.join(d, "*%s.json" % suf)))
    if not files: raise SystemExit("no *%s.json under %s" % (suf, d))
    loaded = [load(f) for f in files]
    pr = next((r for lab, r in loaded if lab == "parent"), None)
    if pr is None: raise SystemExit("no parent among %s: every estimator here is relative to it" % [l for l, _ in loaded])
    pbias = _bias(pr, range(len(pr)), max(len(r["lp"]) for r in pr))
    out = {}
    for lab, rows in loaded:
        n = max(len(r["lp"]) for r in rows)
        v = estimators(rows, k, seed, pbias)
        v["n"] = len(rows)
        v["choice_counts"] = {str(c): sum(1 for r in rows if len(r["lp"]) == c) for c in sorted({len(r["lp"]) for r in rows})}
        v["pred_share"] = [100.0 * sum(1 for r in rows if r["pred"] == i) / len(rows) for i in range(n)]
        v["gold_share"] = [100.0 * sum(1 for r in rows if r["gold"] == i) / len(rows) for i in range(n)]
        out[lab] = v
    p = out["parent"]
    hdr = ("model", "raw", "in-sample", "OOF", "OOF-strat", "parent-bias")
    print("%-16s %9s %10s %10s %11s %12s" % hdr)
    for lab, v in out.items(): print("%-16s %9.3f %10.3f %10.3f %11.3f %12.3f" % ((lab,) + tuple(v[e] for e in ESTS)))
    print("\nDELTA vs parent (pp) -- the deficit is removed by every MODEL-SPECIFIC estimator and")
    print("only about halved by the common parent-derived one, which is why this is not a zero-loss proof:")
    print("%-16s %9s %10s %10s %11s %12s" % hdr)
    for lab, v in out.items():
        if lab != "parent": print("%-16s %+9.3f %+10.3f %+10.3f %+11.3f %+12.3f" % ((lab,) + tuple(v[e] - p[e] for e in ESTS)))
    print("\n%-16s %s   (gold %s)" % ("label share", " ".join("%.1f%%" % x for x in p["pred_share"]),
                                      " ".join("%.1f%%" % x for x in p["gold_share"])))
    print("choice-count census: %s" % p["choice_counts"])
    with open(os.path.join(d, "label_calibration.json"), "w") as fh: json.dump(out, fh, indent=1, sort_keys=True)
    print("\nwrote %s" % os.path.join(d, "label_calibration.json"))

main()
