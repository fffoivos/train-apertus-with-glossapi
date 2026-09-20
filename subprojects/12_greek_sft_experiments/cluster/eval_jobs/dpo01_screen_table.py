#!/usr/bin/env python3
"""Turn the DPO01 screen outputs into the §5 table and apply the pre-registered selection rules.

Reports the full 2x2 at each epoch, not only the best cell (DPO_EXPERIMENT_COMPARISON_20260918.md §5).
Selection is mechanical: no eyeballing of curves, no checkpoint shopping.

  python3 dpo01_screen_table.py [--screen DIR] [--json OUT]
"""
import argparse, glob, json, math, pathlib, sys

# alpha is the chosen_nll_alpha of each arm; the 2e-6 arms form the anchor dose-response curve.
ARMS = {"00": ("5e-7", "alpha 0"),    "01": ("2e-6", "alpha 0"),
        "02": ("5e-7", "alpha 1.0"),  "03": ("2e-6", "alpha 1.0"),
        "04": ("2e-6", "alpha 0.1"),  "05": ("2e-6", "alpha 0.25"),
        "06": ("2e-6", "alpha 0.5")}
PRIMARY = "prompt_level_strict_acc"          # §5 rule 3
RETENTION_FLAG_PP = 10.0                     # §5 rule 2, coarse screening threshold

def wilson(p, n, z=1.96):
    if not n: return (float("nan"),) * 2
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h

def load(screen):
    """lm_eval writes results_<timestamp>.json under a per-model dir; take the newest."""
    rows = {}
    for d in sorted(pathlib.Path(screen).iterdir()):
        if not d.is_dir():
            continue
        files = sorted(glob.glob(str(d / "**" / "results_*.json"), recursive=True))
        if not files:
            rows[d.name] = {"error": "no results json"}
            continue
        res = json.load(open(files[-1]))["results"]
        # the reduced screen used *_screen task names, the full suite uses the production ones
        def get(task, metric):
            for t in (task, task + "_screen"):
                for k, v in res.get(t, {}).items():
                    if k.split(",")[0] == metric:
                        return v
            return None
        gm = [v for t, mm in res.items() if t.startswith("global_mmlu")
              for k, v in mm.items() if k.split(",")[0] == "acc" and isinstance(v, float)]
        rows[d.name] = {
            "ifeval_prompt_strict": get("ifeval_greek", PRIMARY),
            "ifeval_inst_strict": get("ifeval_greek", "inst_level_strict_acc"),
            "ifeval_prompt_loose": get("ifeval_greek", "prompt_level_loose_acc"),
            "mgsm": get("mgsm_greek", "exact_match"),
            "global_mmlu": (sum(gm) / len(gm)) if gm else None,
            "n_ifeval": (res.get("ifeval_greek") or res.get("ifeval_greek_screen") or {}).get("n", None),
            "source": files[-1],
        }
    return rows

def label(name):
    if name == "parent":
        return ("parent", "-", "-", "-")
    arm, ep = name.replace("arm", "").split("_ep")
    lr, kind = ARMS[arm]
    return (name, lr, kind, ep)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", default="results/G4F6P1--DPO01/screen")
    ap.add_argument("--json", default="")
    ap.add_argument("--n-ifeval", type=int, default=541)  # full Greek IFEval; pass 150 for the reduced screen
    a = ap.parse_args()
    rows = load(a.screen)
    if "parent" not in rows or rows["parent"].get("error"):
        print("parent result missing: every delta below would be unanchored", file=sys.stderr)

    base = rows.get("parent", {}).get("ifeval_prompt_strict")
    print(f"\n{'model':<12}{'lr':>7}{'obj':>10}{'ep':>4}"
          f"{'IFEval-ps':>11}{'95% CI':>16}{'vs parent':>11}{'inst':>8}{'MGSM':>8}{'gMMLU':>8}")
    print("-" * 87)
    order = ["parent"] + [f"arm{a_}_ep{e}" for e in (1, 2, 3) for a_ in ARMS]
    for name in order:
        r = rows.get(name)
        if not r:
            continue
        if r.get("error"):
            print(f"{name:<12}{'':>7}{'':>10}{'':>4}  {r['error']}")
            continue
        nm, lr, kind, ep = label(name)
        p = r["ifeval_prompt_strict"]
        if p is None:
            print(f"{nm:<12}{lr:>7}{kind:>10}{ep:>4}   (no IFEval metric)")
            continue
        lo, hi = wilson(p, a.n_ifeval)
        d = "" if base is None or name == "parent" else f"{(p-base)*100:+.1f}pp"
        print(f"{nm:<12}{lr:>7}{kind:>10}{ep:>4}{p:>11.3f}"
              f"{f'[{lo:.2f},{hi:.2f}]':>16}{d:>11}"
              f"{(r['ifeval_inst_strict'] or float('nan')):>8.3f}{(r['mgsm'] or float('nan')):>8.3f}"
              f"{(r['global_mmlu'] if r['global_mmlu'] is not None else float('nan')):>8.3f}")

    # ---- §5 rule 3/4: highest IFEval prompt-strict per objective family, explicit tie-breaks
    print("\nFinalists (§5: highest IFEval prompt-strict per family; "
          "ties -> earlier epoch, then lower LR)")
    cand = {n: r for n, r in rows.items()
            if n != "parent" and not r.get("error") and r.get("ifeval_prompt_strict") is not None}
    if not cand:
        print("  no scored candidates yet")
    else:
        for fam in ("alpha 0", "anchored family"):
            f = [(n, r) for n, r in cand.items()
                 if (ARMS[n.replace('arm', '').split('_ep')[0]][1] == "alpha 0") == (fam == "alpha 0")]
            if not f:
                print(f"  {fam:<9} none"); continue
            best = sorted(f, key=lambda kv: (-kv[1]["ifeval_prompt_strict"],
                                             int(kv[0].split("_ep")[1]),
                                             ARMS[kv[0].replace('arm', '').split('_ep')[0]][0]))[0]
            p = best[1]["ifeval_prompt_strict"]
            d = "" if base is None else f" ({(p-base)*100:+.1f}pp vs parent)"
            print(f"  {fam:<9} {best[0]:<12} IFEval-ps {p:.3f}{d}")
    print("\nNote: retention flags (§5 rule 2) need the GreekMMLU/Global-MMLU lanes; "
          "a finalist here is provisional until those run.")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {a.json}")

if __name__ == "__main__":
    main()
