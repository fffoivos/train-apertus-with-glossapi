# DPO01 analysis close-out — plan and execution

20 September 2026. Owner: finish this aspect of analysis/experimentation end to end. Standing
authorisation to spend against a raised cap, recording the cost. Nothing here needs approval.

## Where the round stands

| lane | corrected result | status |
|---|---|---|
| Greek IFEval | +1.94…+5.48 pp group means | real; **Q2 closed** — the output cap is irrelevant |
| Greek MGSM | +5.00…+11.20 pp | real; **mechanism unknown (Q1)** |
| Global-MMLU-Lite (non-Greek) | +1.10…+1.77 (balanced −0.19) | real |
| Official GreekMMLU (Greek) | −0.25…−0.38 as scored | **artefact (Q4)** — ≈0 calibrated, ≈0 on content |

Two faults, both closed: the RoPE loading mismatch that inverted the round, and the trainer silently
overriding `loss_type`.

## The plan

### Phase A — close Q2 and Q4 (no GPU)
A1. Write Q2 and Q4 into the artifact and the ledger.
A2. **Sol review, narrow scope: is the Q4 calibration sound?** My estimator subtracts each model's mean
    per-position log-prob, estimated on the same 16,632 items being scored. No gold leakage (the prior
    comes from the model's scores, not the labels), but estimating a correction on the evaluation set
    needs an independent opinion. Canonical contextual calibration uses content-free inputs instead.
    Two results that both favour the round is exactly when to invite scrutiny.
A3. Apply findings.

### Phase B — Q1: why did MGSM move 8–11 points?
The pair set is not maths-free: 56 training pairs and 10 dev pairs carry embedded quantitative
content (`provenance.jsonl`, `embedded_maths`; purposes: instruction 34, everyday 20, safety 7,
factual 5). All 56 join to `train.jsonl` by content hash, so the ablation is exact.

B1. Build `dpo01_nomaths`: the same 343 pairs minus the 56, same group-frozen split rule, dev
    likewise minus its 10. Record the manifest and hashes.
B2. Train 3 seeds at the anchored recipe (α=0.25, lr 2e-6, 3 epochs) — matched to the existing
    `arm05` seeds so the only difference is the removed pairs.
B3. Score with the frozen job (geometry repaired, date frozen), generated lanes.
B4. Read: gain survives → not the quantitative content, something general is moving MGSM.
    Gain collapses → 56 pairs are the lever, and round 2 gets a design.
    **Either answer is publishable; neither is assumed.**

A matched control matters: removing 56 of 343 pairs also removes 16% of the training signal. So B2
also trains **one seed with 56 RANDOM pairs removed**, to separate "less data" from "less maths".

### Phase C — Q3: run IPO, for the first time
The trainer now honours `loss_type`. Two runs at the corrected β=10 (the target is per-token, so
β=10 targets 0.050), same seeds as the mislabelled pair, so the comparison is like-for-like against
anchored sigmoid at the same β.
C1. Verify the objective actually executes: dry-run, check the receipt records `loss_type: ipo`.
C2. Train 2 seeds. C3. Score. C4. Read against the displacement hypothesis the round meant to test.

### Phase D — close
D1. Fold B and C into the artifact and ledger.
D2. **Astra review of the whole corrected round**, final.
D3. Record total spend.

## Order and cost

Phase A is free and runs first. B1 is free and can be built while A's review runs. B2/C2 are training;
B3/C3 are evaluation waves. Estimated 5 training runs and 2 evaluation waves, roughly 8–10 node-hours,
about CHF 25–30 against the raised cap.

## Standing rules for this close-out
- Every comparison goes through `rlhf.evals.compare()`; a refusal is a finding, not an obstacle.
- Every training run discloses its parameter table against the previous run before launch.
- No result is written up before it is reviewed, and a result that favours the round gets more
  scrutiny, not less.
