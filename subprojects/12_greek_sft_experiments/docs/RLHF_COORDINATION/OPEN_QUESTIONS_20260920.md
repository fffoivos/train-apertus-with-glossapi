# DPO01 — the open questions, and how to attack them

20 September 2026. Written so these are not lost between sessions. The round's measurement is
finished (`DPO01_POISON_LEDGER_20260919.md`, artifact v21). These are what it did **not** settle.

Status of the round in one line: all 15 checkpoints beat the parent on both generated lanes
(+1.94…+5.48 pp IFEval, +5.00…+11.20 pp MGSM group means), non-Greek knowledge is up 1.1–1.8 pp,
Greek knowledge is **unchanged** once scored on answer content instead of bare labels, and the only
measured cost is a drift in the label prior.

---

## Q1 — Why did MGSM move 8 to 11 points?

**The biggest unknown, and the one that decides whether any of this transfers.**

What we know: 79 of 250 items change for a net +17 on one arm. They are real answer changes, not
extraction — only 4 of 48 gains had the gold number already in the parent's text. Response lengths
are unchanged (121.1 tokens both sides) and the gained answers are *longer*, so it is not brevity.
The changed items replicate across runs (gain-set Jaccard 0.646 / 0.702 / 0.717). Manual reading
shows genuine arithmetic corrections **and** newly introduced arithmetic errors.

What makes it suspicious: 343 preference pairs should not move a third of a mathematics benchmark.

**Attack: ablate the 66 embedded-quantitative pairs.** The set is not maths-free — 24 dedicated
maths tasks were excluded but 66 pairs keep embedded numerical content (56 train, 10 dev), recorded
in `data/rlhf/dpo01/manifest.json` as `embedded_maths`. Retrain with exactly those removed, same
seeds, same everything else.
- gain survives → it is not the quantitative content; something general is happening and it is worth
  chasing (preference training redistributing probability toward better existing solution behaviour).
- gain collapses → we have found the lever, and round 2 gets a design instead of a guess.

Cost: 2 training runs + 1 evaluation wave. Also worth: a **pre-registered held-out quantitative
benchmark**, because MGSM's 250 items are now thoroughly looked at and cannot confirm themselves.

---

## Q2 — Is the IFEval gain compliance, or is it just terminating?

*(partly answered 20 Sept — see the bottom of this section)*

IFEval allows **1,280 generated tokens with no stop strings at all** (`until: []`), so generation ends
only at EOS or the wall. The parent hits that wall on **81 of 541 items (15%)**; the arms on ~26 (5%).
About 57% of one arm's net gain sits in the cap-affected stratum.

Evidence so far that it is a real fix, not gaming:
- Accuracy on *uncapped* items also rises, 62.6% → 64.7%.
- On the parent's 81 runaway items the largest constraint family is `length_constraints` (28, 18 in
  failed items) — a model asked for brevity that emits 1,280 tokens fails on merit at any cap.
- The one unambiguous artefact is `startend`: **8 of 8 failed**, because "end with exactly this
  phrase" cannot succeed under truncation.
- On those 81 items the arm stops in time on 61 and passes 50 against the parent's 38.

**Attack (running, job 3452746): re-score at a 4,096-token cap.** Parent, arm01, armBAL, IFEval+MGSM.
If the parent recovers most of the gap the wall was doing the work; if it does not, the parent simply
does not terminate and the gain is a genuine behavioural improvement.

Note: a different cap is a different measurement. `rlhf.evals` records `gen_kwargs` in the manifest
and will refuse to compare across caps — the valid contrast is parent-vs-arm *within* each cap.

---

## Q3 — IPO has still never been run

The two runs labelled "IPO β=10" trained **anchored sigmoid DPO**: `cluster/dpo_train.py` passed
`loss_type="sigmoid"` as a literal and silently ignored `loss_type: ipo` in the config. Everything
this programme concluded about IPO — a pre-registered falsification, a dev-separation gate reported
as unmet, an argument about β scaling the initial gradient by 1/β — described a loss that never ran.

The trainer now reads the objective from the config and refuses an unsupported value
(`cluster/configs/G4F6P1_DPO01_IPO42.yaml` keeps its header saying what actually executed), so the
test is unblocked.

**Attack: run it.** Two training runs at the corrected β. The point was to test whether held-out
likelihood displacement is an artefact of summing over length: IPO normalises per token, so if the
displacement is a length artefact IPO should not show it. That hypothesis is still untested, and it
is the one question from the original round design that remains genuinely open.

---

## Q4 — Can a few label-format pairs remove the only measured cost? *(new, 20 Sept)*

The Greek MMLU "knowledge loss" is not knowledge loss. On the **same 16,632 items, same weights, same
environment**, changing only the scoring form:

| | bare labels Α/Β/Γ/Δ | answer content |
|---|---|---|
| plain DPO | −0.41 pp, p = 0.00018 | −0.04 pp, p = 0.82 |
| anchored | −0.43 pp, p = 0.000038 | +0.02 pp, p = 0.89 |
| length-balanced | −0.32 pp, p = 0.00059 | −0.09 pp, p = 0.41 |
| Holm-adjusted | all ≤ 0.0006 | **all 1.0** |

The mechanism: DPO amplifies a label bias the parent already has. The parent over-picks Β (34.3% vs
29.5% gold) and under-picks Α and Δ; every arm pushes further the same way, and **the size of the
loss tracks the size of the shift monotonically across all four recipes** (Β-shift +1.06 / +0.96 /
+0.85 / +0.81 against losses −0.38 / −0.38 / −0.32 / −0.25).

The pairs contain **no multiple-choice items at all**, so nothing anchors the label prior and DPO is
free to drift it as a side effect.

**Attack, cheapest first:**
1. Calibrate the label prior at inference (free, no training) and see whether the deficit disappears.
2. Add a small slice of label-answer pairs to round 2 and check the drift does not recur.

If either works, the knowledge cost of preference training here is **zero**, and we should say so.

---

## Sequencing

Q2 is running. Q4(1) is free and can be done from existing prediction files. Q1 is the one that
decides round 2's design and costs 2 training runs. Q3 costs 2 training runs and closes the original
round's unfinished business.
