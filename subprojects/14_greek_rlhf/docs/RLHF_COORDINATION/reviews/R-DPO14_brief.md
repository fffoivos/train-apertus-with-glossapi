# Review brief R-DPO14 (Astra) — the corrected result, and whether the page now tells the truth

You reviewed this work three times today (R-DPO7c, R-DPO9, R-DPO10/11). Your R-DPO9 found the RoPE
loading fault that reversed the round. It has now been repaired and everything re-measured, and a Sol
review (`R-DPO13_review_1.md`) judged the corrected result **real** with three corrections, all applied.
This is the final conclusions review. Read-only; `ssh clariden` works; launch nothing.
Working dir: `subprojects/12_greek_sft_experiments/`.

## What changed since you last looked

- 19 models re-scored: prompt date frozen, rotary settings restored, each model's **effective geometry
  verified equal to the parent's before scoring**, identity written by the evaluator into
  `run_receipt.json` and bound to a hash of every output file.
- **Every arm now scores above the parent on both generated lanes** (`results/G4F6P1--DPO01/frozen_results.json`):

| group | runs | IFEval Δ | MGSM Δ | Global-MMLU-Lite Δ |
|---|---|---|---|---|
| plain DPO α=0 | 5 | +4.03 | +8.48 | +1.10 |
| anchored α=0.25 | 5 | +3.96 | +9.04 | +1.49 |
| length-balanced | 3 | +5.48 | +11.20 | −0.19 |
| anchored sigmoid β=10 (was labelled IPO) | 2 | +1.94 | +5.00 | +1.77 |

- Artefact measured directly on the parent's OWN weights: **−4.07 / −9.60 / −7.63 pp**.
- Sol's three HIGH corrections, all applied: (a) "maths was excluded" is **false** — 66 pairs retain
  embedded quantitative content; (b) the "IPO" arms **never ran IPO** — the trainer hardcoded
  `loss_type="sigmoid"`; (c) official GreekMMLU **declines** (−0.26…−0.43 pp, p ≤ 0.0065) and belongs
  in the headline. Plus: about half the IFEval gain is output-length/termination mediated
  (+1.98 pp uncapped vs +13.79 pp on capped items).
- Page rewritten (v20, `docs/DPO01_CURVES_20260918.html`), ledger updated, trainer fixed to honour
  `loss_type`, `frozen_results.py` now passes every Global-MMLU leaf through the guard (540, 0 refused).

## What to adjudicate

1. **Is the corrected result stated at the right strength?** Read sections 6–14 and the disposition
   table. You have twice caught this page reversing too far — first over-claiming damage, then
   over-withdrawing. Check both directions again. Is "DPO round 1 worked" supportable, or is the
   defensible claim narrower than the page makes it?
2. **Does the page now contain anything false?** Every earlier review found live contradictions it had
   already been told to remove. Assume there are more.
3. **The MGSM gain.** 79 of 250 items move for net +17; gains replicate across seeds (Jaccard
   0.65–0.72); only 4 of 48 are extraction; response lengths unchanged. We claim "MGSM exact match
   increased" and explicitly decline to claim a reasoning improvement. Is that the right line? Given
   the 66 embedded-quantitative pairs, is there a plausible mechanism we should be naming — or a test
   we should be demanding before the number is published at all?
4. **The GreekMMLU contradiction.** Greek knowledge down, non-Greek Global-MMLU up, generated lanes up.
   Sol reads this as a task/language/protocol trade-off. Is that adequate, or does it undermine the
   headline? Note 12 more models are being scored under that protocol right now.
5. **The IFEval brevity finding.** Is "about half the gain is learned termination" the right reading of
   the cap split, and is the remaining ~2 pp meaningful?
6. **What the round may now be said to have produced**, for a reader deciding whether to run round 2.

## Disposition

BLOCKER/HIGH change the artifact before it stands. MEDIUM/LOW logged. If the page is now honest, say so
plainly — this has run to thirteen reviews and the cost of another cycle is real.

## Deliverable

Markdown. Header → one-line verdict → claim-by-claim adjudication with the deciding numbers → findings
most-severe-first with `path:line` → permissible wording for the headline → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
