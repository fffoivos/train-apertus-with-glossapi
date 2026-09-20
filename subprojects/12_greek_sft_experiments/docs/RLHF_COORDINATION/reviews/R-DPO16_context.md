# R-DPO16 — closing out the DPO01 analysis round

You are an independent fresh-eyes CERTIFIER. The implementer is Claude Opus 5; you are not it.
Be adversarial, verify everything FIRSTHAND, recompute claimed numbers from the artefacts, and
report failing numbers RAW. Do not trust the summary below — it is the claim under test, not evidence.

## Disposition

BLOCKER/HIGH are fixed before this round is called done. MEDIUM/LOW are logged and may be deferred.
Calibrate severity honestly: do not bury a must-fix as MEDIUM, do not inflate polish to HIGH.

## What this round is

DPO round 1 on a Greek Apertus 8B SFT parent: 343 training preference pairs, 54 dev, fifteen arms.
A day of measurement was invalidated by a checkpoint-loading fault (transformers 5.16 writes RoPE
settings under `rope_parameters`; the 4.57 scoring environment ignores that key and silently used
rope_theta 12e6 instead of 500k). After repair the round is a success on the generated lanes. Four
open questions were then attacked. This review is about whether the answers are legitimate.

## Read first

- `docs/RLHF_COORDINATION/OPEN_QUESTIONS_20260920.md` — Q1–Q4, each with its evidence
- `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md` — every error found, what each poisoned, spend
- `docs/RLHF_COORDINATION/reviews/R-DPO15_review_1.md` — the previous review, whose findings were applied
- `results/G4F6P1--DPO01/curves_page.py` — the artifact generator; the published page is built from it
- `rlhf/evals/` — the comparability guard (42 tests). `compare()` refuses any pair differing in more
  than the one declared variable.

## Where the data is (read-only)

Cluster `clariden`, `/iopsstor/scratch/cscs/fffoivos/sft_round1`:
- `results/G4F6P1--DPO01/frozen/<label>__<cfg>cfg/` — lm_eval outputs + `run_receipt.json` per model
- `runs/G4F6P1--DPO01--<ARM>/checkpoint-*/` — checkpoints incl. `training_args.bin` (TRL's real config)
- Local: `results/greekmmlu_official/*.json`, `label_calibration.json`

## The four claims under test

### Q4 — the GreekMMLU deficit
Claimed: official bare-label GreekMMLU falls 0.32–0.43 pp; the fall is protocol-sensitive and
consistent with a label-position score shift; it disappears under model-specific batch log-score
centering including 5-fold out-of-fold; a full-text scorer does not detect it. Explicitly NOT
claimed: zero knowledge loss.
R-DPO15 forced this narrowing. Check the narrowing is complete and that no residual wording on the
page still implies the stronger claim. The published page is the artifact built from `curves_page.py`.

### Q2 — the IFEval output cap
Claimed: raising the cap 1,280 → 3,500 produced zero prompt-level strict flips; the +3.88/+5.73 pp
gaps are unchanged; this rules out sensitivity to the 1,280 cutoff WITHIN THE TESTED RANGE only,
because most extended outputs still hit 3,500.

### Q1 — does the MGSM gain come from the 56 embedded-quantitative pairs?
Design: NM (those 56 removed) vs RC (56 random non-maths pairs removed) vs FULL, all anchored
α=0.25, identical hyperparameters, seed-matched 42/43/44.
The analysis plan was AMENDED before results were scored, because a run-level test on 3 seeds
excludes zero 24.9% of the time under a true null (structural: exact sign test floors at p=0.25).
Primary is now item-level seed-matched McNemar + Holm. **Check this reasoning.** If it is wrong,
say so. If it is right, check the result is read within the stated power.

### Q3 — IPO
Claimed: the round's "IPO" arms trained sigmoid because the trainer hardcoded `loss_type`; TRUEIPO
now runs the real objective. Evidence is `training_args.bin` (`['ipo']` vs `['sigmoid']`, both β=10),
and the two YAMLs are identical apart from names.

## Specific things to attack

1. **Is the Q4 narrowing actually complete**, or does the page still carry the artefact reading
   somewhere? Grep the built page, not just the source.
2. **Is the model-specific centering defensible at all**, given a common parent-derived correction
   leaves about half the deficit? Is reporting five estimators honest, or is it burying the one that
   disagrees?
3. **Q1's amended plan.** Is item-level McNemar the right primary here? It treats each run as fixed,
   which understates run-to-run variance. Is the trade stated clearly enough, and is the conclusion
   drawn within it?
4. **Is the Q1 control valid?** RC samples only non-maths pairs, so it retains all 56 maths pairs
   while NM retains none, at equal row counts. Verify from the data files.
5. **Anything averaged that should have been refused.** The guard is supposed to make this
   impossible; check it actually did, including for Global-MMLU-Lite's 36 leaves / 2,400 items.
6. **The spend and error ledger** — is anything omitted that a reader would want to know?

## Deliverable

Markdown. Header (what/scope/evidence) → one-line verdict → findings most-severe-first, each
`[BLOCKER]/[HIGH]/[MEDIUM]/[LOW]` with a concrete `path:line` or number, a failure scenario, and a
fix → what you verified as correct → ordered asks. Give the real number wherever a claim is wrong.
Mark anything you could not verify "unverified".

Last line exactly: `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
