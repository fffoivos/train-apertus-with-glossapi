#!/usr/bin/env python3
"""Paired item comparison of Greek maths between two runs: exact McNemar + paired item bootstrap.

Produces the intervals quoted in docs/pages/SFT_RECIPE_SHAREABLE_20260918.html ("Mathematics, in both
directions"). The R4 plan required "95% paired item-bootstrap interval (10,000 resamples, seed 42)"
for every automatically scored task; it was never run for MGSM-el or MATH-500-el, so the reported
-8.0 / +5.4 point differences were bare point estimates until now.

  python3 evals/paired_maths_delta.py
"""
import glob, json, math, random, sys

SEED, RESAMPLES = 42, 10_000
# label -> (MGSM samples glob, MATH-500-el score.json)
RUNS = {
    "stage 1":            ("results/R2_stage1_ep1/ilsp/*/samples_mgsm_greek_*.jsonl", "results/R3_single/bench_S1/math500_el_score.json"),
    "round 3":            ("results/R3_single/ilsp/*/samples_mgsm_greek_*.jsonl",     "results/R3_single/bench_R3/math500_el_score.json"),
    "previous (G2F1P1)":  ("results/R2_idB_ep2/ilsp/*/samples_mgsm_greek_*.jsonl",    "results/R3_single/bench_B/math500_el_score.json"),
    "this run (G4F6P1)":  ("results/R4_full_ep1/ilsp/*/samples_mgsm_greek_*.jsonl",   "results/R4_full/bench_R4/math500_el_score.json"),
}
BASE, NEW = "previous (G2F1P1)", "this run (G4F6P1)"

def mgsm(pat):
    hits = sorted(glob.glob(pat))
    if not hits: return None
    return {json.loads(l)["doc_id"]: bool(json.loads(l)["exact_match"]) for l in open(hits[-1], encoding="utf-8")}

def math500(path):
    try: s = json.load(open(path))
    except FileNotFoundError: return None, None
    got = lambda r: bool(r["equiv500"] if r.get("equiv500") is not None else r.get("correct"))
    return {r["id"]: got(r) for r in s["rows"]}, s.get("truncated")

def compare(new, old, name):
    ids = sorted(set(new) & set(old))
    n = len(ids)
    a_new = sum(new[i] for i in ids) / n * 100
    a_old = sum(old[i] for i in ids) / n * 100
    b = sum(1 for i in ids if new[i] and not old[i])      # new correct, old wrong
    c = sum(1 for i in ids if old[i] and not new[i])      # old correct, new wrong
    d = b + c
    p = 2 * sum(math.comb(d, j) for j in range(min(b, c) + 1)) / 2 ** d if d else 1.0
    rng = random.Random(SEED); deltas = []
    for _ in range(RESAMPLES):
        s = [ids[rng.randrange(n)] for _ in range(n)]
        deltas.append((sum(new[i] for i in s) - sum(old[i] for i in s)) / n * 100)
    deltas.sort()
    lo, hi = deltas[int(.025 * RESAMPLES)], deltas[int(.975 * RESAMPLES)]
    print(f"\n{name}  (paired on {n} items)")
    print(f"  {NEW}: {a_new:.1f}%   {BASE}: {a_old:.1f}%")
    print(f"  discordant: new-only {b}, old-only {c}")
    print(f"  delta {a_new - a_old:+.1f} pp   95% CI [{lo:+.1f}, {hi:+.1f}]   McNemar exact p = {min(p,1.0):.4f}")

def main():
    print(f"seed {SEED}, {RESAMPLES} resamples\n")
    print(f"{'run':<22}{'MGSM-el':>10}{'MATH-500-el':>14}{'truncated':>11}")
    sets = {}
    for label, (mp, xp) in RUNS.items():
        m = mgsm(mp); x, trunc = math500(xp)
        sets[label] = (m, x)
        f = lambda d: f"{sum(d.values())/len(d)*100:.1f}%" if d else "—"
        print(f"{label:<22}{f(m):>10}{f(x):>14}{(str(trunc) if trunc is not None else '—'):>11}")
    for name, idx in (("MGSM Greek", 0), ("MATH-500 Greek", 1)):
        new, old = sets[NEW][idx], sets[BASE][idx]
        if new and old: compare(new, old, name)
        else: print(f"\n{name}: missing per-item outputs, skipped", file=sys.stderr)

if __name__ == "__main__":
    main()
