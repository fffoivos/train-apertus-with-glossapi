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

### Dataset premise, verified 20 Sept (before the arms were scored)

Q1 is only readable if the two ablations are what they claim, so this was checked against the files
rather than the build script's intent:

* Both are exact 287-row **subsets** of the 343-row base; each removes exactly 56.
* The two removed sets are **disjoint**.
* `dev.jsonl` is byte-identical across all three configs, so dev metrics stay comparable.

The manipulation is strong and in the intended direction:

| training set | digits/pair | embedded-maths pairs retained |
|---|---|---|
| FULL 343 | 26.6 | 56 |
| **NM 287** | **19.5** | **0** |
| **RC 287** | **28.2** | **56** |

RC retains *every* embedded-maths pair while NM retains none, at identical row counts — row count
held constant, quantitative content maximally varied. That is the contrast Q1 needs.

One check worth recording because it nearly caused a wrong move: RC's removed pairs average 18.4
digits/pair against the *whole* set's 26.6, which looks like an unusually maths-light draw (2.6th
percentile) and would have biased NM−RC toward confirming the hypothesis. It is not. The builder
samples `others`, the non-maths pairs only, so the correct null is draws from that pool — against
which RC's cut sits at the **39.7th percentile**, entirely typical. The apparent anomaly was an
artefact of comparing against a pool the control is defined to exclude.

Note on the seeds: RC42/43/44 vary the **training seed** over one fixed cut, so they measure
optimisation variance, not which-56-were-removed variance. Cut variance is not estimated here. It
matters less than it would otherwise, because the cut is drawn from non-maths pairs and so cannot
change the maths content of what remains — which is the variable Q1 turns on.

## Q2 — Is the IFEval gain compliance, or is it just terminating?

*(answered 20 Sept for the tested range; see the bottom of this section. Narrowed by R-DPO15.)*

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

**Attack (DONE 20 Sept): re-scored at a 3,500-token cap** — 2.7x the room, and as much as the model's
4,096-token context allows (the first attempt asked for 4,096 generated tokens and died on the context
assertion). Parent, arm01, armBAL, IFEval.

**Result: zero prompt-level strict pass/fail flips for any model.** Parent 326/541 at both caps,
arm01 347/541, armBAL 357/541; the gaps are +3.88 and +5.73 pp at either cap. The parent genuinely
used the room, doubling mean output from 330 to 661 tokens.

Run authenticity is not in doubt: R-DPO15 checked every response and found each old one is a strict
*prefix* of the new one — the fingerprint of deterministic decoding with a raised wall. Parent 458
byte-identical / 83 extended; arm01 and armBAL 514 / 27.

**What this does and does not support** (R-DPO15, HIGH; the page's "the output cap is irrelevant" and
"not one item changed outcome" are withdrawn):
- It **rules out** sensitivity of the headline score to the 1,280 cutoff *within the tested range*.
- It does **not** rule out output-length effects in general: 78 of the parent's 83 extended outputs,
  and 25 of each arm's 27, still ran into the 3,500 wall. The experiment usually *moves* the
  truncation point rather than observing natural completion. Unrestricted-length behaviour is
  unresolved.
- "Not one item changed outcome" was true only of prompt-level strict results. Parent item 95 and
  arm01 item 161 changed *instruction-level* strict and loose outcomes while still failing overall.
- Cap-affected status may therefore mark a correlated failure-to-terminate phenotype (nontermination,
  repetition, verbosity) rather than a cause of failing. Length can correlate with failure without
  causing it; supplying 2,220 more tokens does not repair it.

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

---

### Verified 20 Sept: IPO has now actually run

The Q1/Q3 training gate checks that the *plan* says `ipo`. That is the input, not the behaviour, and
"a config that asked for IPO and trained sigmoid" is exactly the bug that created this question — so
the gate alone is not evidence. The decisive artefact is `training_args.bin`, the `DPOConfig` object
TRL actually constructed, saved inside each checkpoint:

| arm | `loss_type` | `beta` | `label_smoothing` |
|---|---|---|---|
| **TRUEIPO42** | **`['ipo']`** | 10.0 | 0.0 |
| armIPO42 (the round's "IPO" arm) | `['sigmoid']` | 10.0 | 0.0 |
| arm05 (reference) | `['sigmoid']` | 0.1 | 0.0 |

Two things this establishes, both from artefacts rather than from reading the trainer source:

1. **TRUEIPO42 genuinely optimised the IPO objective.** First time in this round.
2. **armIPO42's own checkpoint confirms it trained sigmoid**, independently of the code inspection
   that first caught the hardcode. Every "IPO" conclusion the page carried was about sigmoid at
   β = 10.

TRUEIPO vs armIPO is therefore a clean isolation of the *objective* at matched β = 10, which is what
Q3 needed and never had. Checkpoint arithmetic confirmed: 343 pairs → step 129.

## Q4 — Is the GreekMMLU deficit a label-position shift? *(new, 20 Sept; ANSWERED, narrowly, 20 Sept)*

**Status: measured, then narrowed by R-DPO15 (Sol, xhigh). The earlier heading here — "the Greek MMLU
knowledge loss is not knowledge loss" — was an overclaim and is withdrawn.**

### What was run

All 16,632 items, same weights, same environment. Two families of evidence.

**(a) A second scorer that ranks answer content instead of bare letters:**

| | bare labels Α/Β/Γ/Δ | answer content | content-scorer 95% CI |
|---|---|---|---|
| plain DPO | −0.41 pp, p = 0.00018 | −0.04 pp, p = 0.82 | [−0.30, +0.22] |
| anchored | −0.43 pp, p = 0.000038 | +0.02 pp, p = 0.89 | [−0.24, +0.29] |
| length-balanced | −0.32 pp, p = 0.00059 | −0.09 pp, p = 0.41 | [−0.29, +0.10] |
| Holm-adjusted | all ≤ 0.0006 | **all 1.0** | paired item bootstrap, 4,000 resamples |

**(b) Model-specific batch log-score centering** (`cluster/eval_jobs/label_calibration.py`), five
estimators, delta vs parent in pp:

| estimator | plain | anchored | length-balanced |
|---|---|---|---|
| raw | −0.415 | −0.433 | −0.325 |
| centered, in-sample | +0.036 | +0.060 | +0.006 |
| centered, 5-fold out-of-fold | +0.054 | +0.054 | +0.060 |
| centered, OOF within choice-count strata | +0.054 | +0.078 | +0.108 |
| **centered by the PARENT's bias** | **−0.162** | **−0.247** | **−0.150** |

The mechanism still looks right: the parent over-picks Β (34.3% vs 29.5% gold) and under-picks Α and
Δ; every arm pushes further the same way, and the size of the loss tracks the size of the shift
monotonically across all four recipes (Β-shift +1.06 / +0.96 / +0.85 / +0.81 against losses −0.38 /
−0.38 / −0.32 / −0.25).

### What R-DPO15 established, and I confirmed firsthand

1. **"Knowledge cost is zero" does not follow.** Holm p = 1.0 is a failure to reject; no equivalence
   margin was predeclared, and every content-scorer CI above is wide enough to contain the raw deficit
   it was being used to dismiss. Precision is about ±0.3 pp — too coarse to detect a 0.4 pp effect.
2. **The two families are not independent confirmations, and (a) is not a clean intervention.**
   `custom_full_text` uses `old_prompt()`, `official_label` uses `official_prompt()`
   (`greekmmlu_official.py:46` vs `:124`): they differ in prompt text, subject framing, answer cue,
   candidate continuation (full choice vs bare letter) **and** ranking statistic (`avg_logprob` vs
   `sum_logprob`). Parent scores 54.28% under one and 69.41% under the other — different instruments.
3. **The correction is model-specific and that does material work.** Out-of-fold estimation rules out
   in-sample fitting (the obvious worry, and it is genuinely ruled out). But a common parent-derived
   correction leaves roughly half the deficit. A per-model correction can absorb genuine ability
   differences along with prior drift.
4. **Doc/code mismatch, fixed.** The old docstring described two estimators (probability-marginal and
   additive) and implemented only the additive one, and called it "contextual calibration". Renamed to
   *model-specific batch log-score centering*; the tool now emits all five rows above.

One place I did **not** accept R-DPO15 as written: it attributed part of the sensitivity to pooling
the 2-/3-/4-choice populations (3,152 / 3,478 / 10,002). Cross-fitting *within* choice-count strata
leaves the deficit removed (+0.054 / +0.078 / +0.108), so stratification is not the lever — the
**estimator form** is.

### Supportable statement

> Official bare-label GreekMMLU falls by 0.32–0.43 pp after preference training. The deficit is
> protocol-sensitive and consistent with a model-specific label-position score shift: it disappears
> under model-specific batch log-score centering including out-of-fold estimation, and a separate
> full-text scorer does not detect it. This does not establish zero Greek-knowledge loss — the
> full-text scorer also changes the prompt, and the raw official-label degradation remains a real
> multiple-choice performance cost.

### What would actually settle it (not run)

1. **A clean scoring-form isolation:** hold `official_prompt` byte-identical and change *only* the
   candidate continuation (bare letter → full choice text), keeping the ranking statistic fixed.
   This is the experiment we claimed to have run and did not.
2. **A choice-permutation experiment**, predefined: if the deficit is positional, permuting the
   presentation order of the choices moves it in a predictable way; if it is knowledge, it does not.
   Stronger than any post-hoc correction because nothing is fitted.
3. **Add a small slice of label-answer pairs to round 2** and check the drift does not recur — now a
   hypothesis to test, not a diagnosis to act on.

## Sequencing

Q2 is running. Q4(1) needs one 45-minute re-run to persist the per-choice scores first. Q1 is the one that
decides round 2's design and costs 2 training runs. Q3 costs 2 training runs and closes the original
round's unfinished business.
