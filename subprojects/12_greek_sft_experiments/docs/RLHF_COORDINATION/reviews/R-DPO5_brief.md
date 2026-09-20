# Review brief R-DPO5 — DPO01 follow-up design, and the IPO parameterisation

**BLOCKING before any GPU is spent on the IPO arm.** Other arms in the programme are plain DPO and
are already running; only the IPO specification is gated on this review.

## Stage goal

DPO01 trained 7 arms × 3 epochs from one parent on 397 preference pairs and evaluated all 22 models
on full-size batteries. The follow-up programme tests a diagnosis. This review is asked to check the
diagnosis and, above all, the IPO arm's parameterisation, which we have already found mis-specified
once.

## What DPO01 measured (all numbers from the full battery, today)

- Damage tracks **total update** (lr × steps), r = +0.92 to +0.97 over 21 checkpoints. Learning rate
  alone correlates far less (+0.68 to +0.79). At matched movement the two learning rates are
  indistinguishable: 5e-7@ep3 (6.45e-5) gives IFEval −6.1/−5.7, 2e-6@ep1 (8.60e-5) gives −5.0/−4.6/−5.2.
- **Median response length predicts MGSM accuracy, r = +0.952 over 8 models.** Parent 59.5 words /
  0.448; worst arm 46.0 words / 0.328.
- Damage is confined to the response **envelope**: language −22.6, startend −16.4, length_constraints
  −13.3, while content families are flat or better (detectable_content +11.3).
- The pairs are the suspected cause: **chosen is shorter in 59%** of them (everyday .65, safety .66,
  instruction .49). A content-blind "pick the shorter reply" rule scores .611 on the 54-pair dev set
  against .643 for the best arm.
- Served lanes disagree with lm_eval lanes: MATH-500 and IFBench give **44 positive vs 3 negative**
  deltas (sign test p < 0.0001, mean +0.91pp), while IFEval/MGSM/Global-MMLU are negative everywhere.

## The IPO arm, and the error we already found

Intent: stop over-optimisation. DPO drove **train** separation far past what generalises, and that
surplus is where we think the length shortcut was learned.

The original specification was **beta 0.1**, on the belief that TRL's IPO loss is
`(gap − 1/(2β))²` with the gap in **summed nats**, so beta 0.1 targets 5.0 nats.

Reading the installed source (`trl/trainer/dpo_trainer.py`, TRL 1.12.0, lines 1431–1481) we found:

```python
chosen_scores = chosen_logratios          # log pi_policy - log pi_ref, summed over completion
...
chosen_avg_score   = chosen_scores   / chosen_mask.sum(dim=1)
rejected_avg_score = rejected_scores / rejected_mask.sum(dim=1)
ipo_delta = chosen_avg_score - rejected_avg_score
per_sequence_loss = (ipo_delta - 1 / (2 * self.beta)) ** 2
```

So `ipo_delta` is a **per-token** difference of two independently length-normalised log-ratios, not a
summed-nat gap. Measured on our own runs (mean completion 162.2 chosen / 206.8 rejected tokens):

| | ipo_delta |
|---|---|
| parent | 0 exactly (policy is the reference) |
| DPO, train, epoch 3 | **0.135–0.139** at every alpha |
| DPO, dev | **0.006–0.011** |
| target implied by beta 0.1 | **5.000** |

beta 0.1 would therefore demand ~37× what DPO reached on memorised data and ~500× what generalised,
under a squared loss. **Our corrected proposal is beta 10 (target 0.050)** — above the 0.008 that
generalises, about a third of the 0.135 that did not — with beta 15 (0.033) as the fallback if length
collapse persists.

## Questions

1. **Verify the parameterisation against the installed source, not the paper.** Is `ipo_delta`
   per-token as we read it? Is our beta 10 → target 0.050 arithmetic right? Is there a reason to
   prefer a different target given the measured 0.135 train / 0.008 dev?
2. **Is per-token normalisation hazardous for this pair set specifically?** Chosen is shorter in 59%
   of pairs, and the two sides are normalised by *different* denominators. Does that make IPO a poor
   instrument for a length-confounded set, or does it help by removing length from the objective?
3. **Is the length diagnosis over-read?** Every arm is n=1; the alpha ranking spans 2.0pp against a
   round-one seed noise floor of ±1.0pp on IFEval. Seed replicates are queued. Are we treating
   correlational evidence (r = +0.952, n=8 highly correlated models) as causal?
4. **Do the five arms answer distinguishable questions, or do they overlap?** They are: IPO;
   arm05 recipe at 5 epochs (fresh, doubles as a determinism check); seed replicates of arm05 and
   arm01; 4e-6 at alpha 0.25; IPO at a second beta.
5. Are the pre-registered predictions falsifiable as written? In particular: "if separation drops to
   target and the benchmarks still degrade, the over-optimisation diagnosis is WRONG."

## Disposition

BLOCKER/HIGH findings on the IPO parameterisation change the config before it runs. Findings on
interpretation are logged and carried into the write-up. The other four arms are not gated on this.
Maximum two review cycles on this checkpoint.
