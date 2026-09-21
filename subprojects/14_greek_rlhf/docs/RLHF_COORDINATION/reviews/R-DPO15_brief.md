# Review brief R-DPO15 (Sol) — is the label-prior calibration sound, and is Q2 read correctly?

Narrow scope, two results that both land in the round's favour. That is exactly when we want
scrutiny, not less. Read-only; `ssh clariden` works; launch nothing.
Working dir: `subprojects/12_greek_sft_experiments/`.

## Q4 — the claim: Greek knowledge was never lost

Official GreekMMLU had the arms 0.25–0.38 pp below the parent, highly significant (Holm p ≤ 0.0006,
16,632 items, five seeds per group, SD 0.03–0.06 pp). We now say that is a **label-position
artefact** and the true knowledge cost is zero, on two independent grounds:

1. **Score content instead of letters.** Same items, same weights, same environment, one pass each
   (`results/greekmmlu_official/*.json` vs `*_custom.json`): ranking bare Α/Β/Γ/Δ gives
   −0.41 / −0.43 / −0.32 pp (p = 0.00018 / 0.000038 / 0.00059); ranking the full answer text gives
   −0.04 / +0.02 / −0.09 pp (**Holm-adjusted all 1.0**).
2. **Remove the prior, keep the protocol.** `cluster/eval_jobs/label_calibration.py` subtracts each
   model's mean per-position log-prob and re-ranks (`*_scores.json`, produced with
   `--save-choice-scores`; results in `label_calibration.json`). Deficits become +0.04 / +0.06 / +0.01.

Mechanism offered: the parent already over-picks Β (34.3% vs 29.5% gold) and under-picks Α and Δ;
every arm pushes further the same way, and loss size tracks shift size across all four recipes.

**Attack this specifically:**
- **Is the calibration estimator legitimate?** It estimates the prior from the model's own scores on
  the same 16,632 items it then re-ranks. We claim no gold leakage (it uses log-probs, not labels),
  but a correction fitted on the evaluation set is the obvious objection. Canonical contextual
  calibration uses content-free dummy inputs. Is our version sound, is it fitting, and would a
  content-free estimate or a held-out split change the answer? Recompute if you can.
- Calibration raises *every* model (+1.01 parent, +1.34…+1.50 arms). Is "it helps whoever has more
  bias" the right reading, or could subtracting a mean log-prob per position favour arms mechanically?
- Is the content-scoring result really independent of the calibration one, or do they share an
  assumption?
- Does "the knowledge cost is zero" follow, or only "the label-protocol deficit is explained"? A
  model that has drifted its label prior IS worse at answering multiple-choice questions as posed.

## Q2 — the claim: the IFEval gain is not the output cap

IFEval allows 1,280 tokens with **no stop strings**; the parent hits that wall on 81 of 541 items,
the arms on ~26, and 57% of the net gain sits in the cap-affected stratum. We re-scored at 3,500
tokens (the most a 4,096 context allows; longest prompt is 509).

Result (`results/G4F6P1--DPO01/cap3500/` vs `frozen/`): the parent used the room — mean output 330 →
661 tokens, 83 items generated materially more — and **not one item changed outcome for any model**.
IFEval deltas identical to four decimals at both caps (+3.88 arm01, +5.73 armBAL). Of the parent's
83 grown items, 40 passed before and 40 after.

**Attack:** is zero flips across three models credible, or does it suggest the runs are not what we
think (e.g. reused outputs)? Note 458 of 541 responses are byte-identical between caps and exactly
the 83 truncated ones differ, which we read as correct. Does this really license "the cap is
irrelevant", or only "raising it to 3,500 changes nothing"? Could a model be failing for a reason
correlated with, but not caused by, length?

## Disposition

BLOCKER/HIGH change what we publish (artifact v22). MEDIUM/LOW logged.

## Deliverable

Markdown. Header (what you ran) → one-line verdict → Q4 findings → Q2 findings → permissible wording
for each → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | Q4: <sound|unsound|qualified> | Q2: <sound|unsound|qualified>`
