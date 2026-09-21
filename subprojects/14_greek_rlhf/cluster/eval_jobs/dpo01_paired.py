#!/usr/bin/env python3
"""Paired item-level comparison of every DPO01 screen model against the parent (plan §8).

Consumes the per-prompt booleans that rescore_ifeval_langdetect.py emits (prompt_strict_items),
so the language:response_language instructions are scored with langdetect rather than silently
failing as they do on the cluster harness. Reports the paired delta, a 10,000-resample paired
item bootstrap at seed 42, and improved/regressed/unchanged counts.

  python3 dpo01_paired.py --rescored <root>/ifeval_el_rescored.json [--mgsm <screen dir>]
"""
import argparse, glob, json, os, random, statistics as st

ARMS = {"00": ("5e-7", "plain"), "01": ("2e-6", "plain"),
        "02": ("5e-7", "anchored"), "03": ("2e-6", "anchored"),
        "04": ("2e-6", "alpha0.1"), "05": ("2e-6", "alpha0.25"), "06": ("2e-6", "alpha0.5")}
B, SEED = 10000, 42

def label(name):
    if name == "parent":
        return ("parent", "-", "-", "-")
    arm, ep = name.replace("arm", "").split("_ep")
    lr, kind = ARMS.get(arm, ("?", "?"))
    return (name, lr, kind, ep)

def paired_bootstrap(pairs, n=B, seed=SEED):
    """pairs: list of (parent_bool, arm_bool) for the SAME item. Resample items, not models."""
    rnd = random.Random(seed)
    k = len(pairs)
    deltas = []
    idx = range(k)
    for _ in range(n):
        s = [pairs[rnd.randrange(k)] for _ in idx]
        deltas.append(sum(b for _, b in s) / k - sum(a for a, _ in s) / k)
    deltas.sort()
    return deltas[int(0.025 * n)], deltas[int(0.975 * n)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescored", required=True)
    ap.add_argument("--mgsm", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    R = json.load(open(a.rescored))
    if "parent" not in R:
        raise SystemExit("no parent entry in the rescored file: every delta would be unanchored")

    base = {str(i["key"]): bool(i["prompt_strict"]) for i in R["parent"]["prompt_strict_items"]}
    print(f"\nparent: prompt-strict {R['parent']['prompt_strict']:.3f} "
          f"(harness said {R['parent']['orig_prompt_strict']:.3f} before the langdetect rescore), "
          f"n={R['parent']['n']}, {R['parent']['language_instructions']} language instructions\n")
    print(f"{'model':<12}{'lr':>7}{'objective':>11}{'ep':>4}"
          f"{'IFEval-ps':>11}{'delta':>9}{'95% paired CI':>18}{'+':>5}{'-':>5}{'=':>5}")
    print("-" * 87)
    rows, out = [], {}
    order = ["parent"] + sorted([k for k in R if k != "parent"],
                                key=lambda k: (k.split("_ep")[1], k))
    for name in order:
        r = R[name]
        items = {str(i["key"]): bool(i["prompt_strict"]) for i in r["prompt_strict_items"]}
        shared = sorted(set(base) & set(items))
        if len(shared) != len(base):
            print(f"  {name}: only {len(shared)} of {len(base)} items shared with parent — skipped")
            continue
        pairs = [(base[k], items[k]) for k in shared]
        up = sum(1 for p, q in pairs if q and not p)
        dn = sum(1 for p, q in pairs if p and not q)
        same = len(pairs) - up - dn
        d = r["prompt_strict"] - R["parent"]["prompt_strict"]
        nm, lr, kind, ep = label(name)
        if name == "parent":
            print(f"{nm:<12}{lr:>7}{kind:>11}{ep:>4}{r['prompt_strict']:>11.3f}"
                  f"{'':>9}{'(reference)':>18}{'':>5}{'':>5}{'':>5}")
            continue
        lo, hi = paired_bootstrap(pairs)
        sig = "" if lo <= 0 <= hi else "  *"
        print(f"{nm:<12}{lr:>7}{kind:>11}{ep:>4}{r['prompt_strict']:>11.3f}"
              f"{d*100:>+8.1f}p{f'[{lo*100:+.1f},{hi*100:+.1f}]':>18}{up:>5}{dn:>5}{same:>5}{sig}")
        out[name] = dict(prompt_strict=r["prompt_strict"], delta_pp=round(d * 100, 2),
                         ci_pp=[round(lo * 100, 2), round(hi * 100, 2)],
                         improved=up, regressed=dn, unchanged=same,
                         excludes_zero=not (lo <= 0 <= hi))
    print("\n  * = 95% paired interval excludes zero. Interval crossing zero is inconclusive,")
    print("    even when the point estimate moves (plan §8).")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"\nwrote {a.json}")

if __name__ == "__main__":
    main()
