# DPO01 — the open questions, and how to attack them

> **Paths, since 2026-09-21.** This document moved with the RLHF work from `12_greek_sft_experiments` to
> `14_greek_rlhf`. Paths written below are relative to the subproject root and still resolve here, with
> three exceptions that stayed in 12 as shared infrastructure: `results/greekmmlu_official/`,
> `cluster/greekmmlu_official.sh` (+ its scorer, validator, receipt tool and gold), and `evals_code_backup/`.


20 September 2026. Written so these are not lost between sessions. The round's measurement is
finished (`DPO01_POISON_LEDGER_20260919.md`, artifact v21). These are what it did **not** settle.

Status of the round in one line: all 15 checkpoints beat the parent on both generated lanes
(+1.94…+5.48 pp IFEval, +5.00…+11.20 pp MGSM group means), non-Greek knowledge is up 1.1–1.8 pp,
Greek knowledge is **unchanged** once scored on answer content instead of bare labels, and the only
measured cost is a drift in the label prior.

---

## Q1 — Why did MGSM move 8 to 11 points?  *(ANSWERED 20 Sept: not the maths pairs, not data volume)*

**Answer: the 56 embedded-quantitative pairs do not explain the gain. Neither does data volume. The
mechanism is still unknown.**

Scored 20 Sept, frozen date, geometry repaired, nine models through the comparability guard.

| training set | seeds | IFEval | sd | MGSM | sd | gMMLU-Lite |
|---|---|---|---|---|---|---|
| parent | 1 | 0.6026 | – | 0.4240 | – | 0.6154 |
| FULL 343 pairs (arm05) | 5 | 0.6421 | 0.46 | **0.5144** | 1.95 | 0.6303 |
| NM 287, the 56 maths pairs removed | 3 | 0.6334 | 0.47 | **0.4960** | 1.06 | 0.6294 |
| RC 287, 56 random pairs removed | 3 | 0.6451 | 0.32 | **0.5160** | 1.06 | 0.6282 |

### The primary test is a null

Item-level, seed-matched, exact McNemar, Holm-corrected across the three pairs (MGSM, 250 items):

| seed pair | NM − RC | p | Holm |
|---|---|---|---|
| 42 | +0.40 pp | 1.0000 | 1.0000 |
| 43 | −3.20 pp | 0.2682 | 0.7676 |
| 44 | −3.20 pp | 0.2559 | 0.7676 |

Nothing significant. Per the rule fixed before scoring, this means *no item-level difference
detectable between these particular runs* — not that the pairs are irrelevant, and not equality.

### What is nevertheless established

**The control worked, and that is the informative part.** Removing 56 *random* pairs cost
**+0.16 pp [−1.73, +1.84]** on MGSM — nothing at all. So losing 16% of the training signal is not
what moves this benchmark, which kills the "less data" explanation outright.

Removing the 56 quantitative pairs cost −1.84 pp against FULL, and NM − RC is −2.00 pp
[−3.20, +0.40]. Against a total gain of ~+9 pp over the parent, the point estimate attributes at
most about a fifth of it to those pairs, and even that is unresolved. **Roughly 80% of the MGSM gain
survives training with zero embedded-quantitative pairs.**

Within the predeclared power (4 pp detected 81% of the time, 6 pp 95%), a −2 pp effect is below what
this design resolves. This is a bounded null, and it was forecast as the likely outcome before the
runs were scored rather than explained afterwards.

### Where that leaves the mechanism

Unknown, and now more sharply so: the two obvious candidates are both eliminated or bounded. 343
preference pairs containing no dedicated mathematics move Greek MGSM by about 9 points, and neither
the quantitative content of 56 of them nor the sheer quantity of data accounts for it.

Next probes, in order of cost:
1. **Bigger ablation**, sized to resolve 2 pp rather than 4 — needs more seeds *and* more cut
   variants, since cut variance is currently unestimated (RC42/43/44 share one cut).
2. **Formatting/verbosity hypothesis**: MGSM is exact-match on a final number. Check whether the
   gained items change the *form* of the answer rather than the reasoning — the round already found
   gained answers are longer, not shorter, and that only 4 of 48 gains had the right number present
   in the parent's text.
3. **Cross-benchmark check**: does the gain appear on a non-Greek maths benchmark? That separates
   "Greek output discipline" from "mathematics".

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

## Q3 — IPO  *(ANSWERED 20 Sept: it ran, and it is not better)*

**Answer: real IPO at β=10 matches the best sigmoid arm on instruction following and is clearly
worse on mathematics. Every "IPO" conclusion the round previously carried was about sigmoid at
β=10.**

| arm | objective | IFEval | MGSM | gMMLU-Lite |
|---|---|---|---|---|
| parent | – | 0.6026 | 0.4240 | 0.6154 |
| FULL (arm05) | sigmoid, β=0.1 | 0.6421 | **0.5144** | 0.6303 |
| **TRUEIPO** | **ipo, β=10** | **0.6460** | **0.4620** | 0.6256 |
| armIPO | sigmoid, β=10 *(the mislabelled pair)* | 0.6220 | 0.4740 | 0.6331 |

- **vs the best sigmoid (FULL):** IFEval +0.39 pp [−0.15, +0.92] — indistinguishable.
  MGSM **−5.24 pp [−7.60, −2.88]** — worse.
- **vs armIPO, which isolates the objective at matched β=10:** IFEval +2.40 pp, MGSM −1.20 pp.
- TRUEIPO still beats the parent on both lanes (+4.34 IFEval, +3.80 MGSM).

### The statistics here are weak and are not dressed up

**TRUEIPO and armIPO have two seeds each.** A paired bootstrap over two observations produces an
interval that is literally the range of the two numbers; it is not a test, and the "excludes zero"
labels the tool prints for these rows carry its calibration warning for that reason. What can be
said is only that the direction was consistent in 2 of 2 seeds. No significance is claimed for any
Q3 contrast, and the MGSM deficit against FULL is large enough (−5.24 pp against a between-seed SD
of ~1.9) that it is the one row worth believing on inspection rather than on arithmetic.

### Why this was worth running at all

Not for the ranking — it is for the retraction. The round reported a pre-registered IPO
falsification, an unmet gate, and an argument about β scaling the gradient. All of it described runs
that optimised the sigmoid objective. Those conclusions are withdrawn, and the objective they were
supposed to be about has now actually been tested.

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

It is cleaner still than that: `G4F6P1_DPO01_IPO42.yaml` and `G4F6P1_DPO01_TRUEIPO42.yaml` are
**identical apart from `run_name` and `output_dir`** — `loss_type: ipo` was already in the original
IPO config, and the trainer ignored it. So the pair is a natural experiment in which the *same
configuration file* was run by two trainer builds, and the objective that was actually optimised is
read from TRL's saved `DPOConfig` rather than from the YAML. Nothing else about the run differs:
same data, same lr, same α, same β, same epochs, same parent.

### Config premises, verified by diff (20 Sept)

| comparison | differs in |
|---|---|
| NM42 vs arm05 | `run_name`, `train_file`, `output_dir` — nothing else |
| RC42 vs NM42 | `run_name`, `train_file`, `output_dir` — nothing else |
| TRUEIPO42 vs arm05 | the above, plus `beta: 10.0` and `loss_type: ipo` |
| TRUEIPO42 vs IPO42 | `run_name`, `output_dir` only (the objective differs in the *trainer*) |

So NM and RC are matched in every hyperparameter; the only thing separating them is which 56 pairs
were removed. That is what makes Q1's NM − RC contrast interpretable.

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

## Q5 — Did the pairs teach a reasoning *skill* rather than content?  *(new, 20 Sept, owner's hypothesis)*

Q1 eliminated the two content explanations for the MGSM gain. The owner's question — *"did the pairs
reinforce correct reasoning?"* — proposes a skill explanation instead, and it fits the evidence
better than anything else considered.

**What the pairs are made of.** 35% of the 343 training pairs are labelled `compositional`
difficulty and a further 11% `challenging`. Task types include `conditional_answer` (17),
`multi_constraint_composition` (12), `edit_preserving_values` (20), `strict_format` (14) — tasks
that require holding several stated conditions simultaneously and not contradicting them.

**What a pair actually rewards.** In R3-0404 the request was a vegan family meal. The *rejected*
answer proposed *gigot d'agneau* — leg of lamb. The *chosen* answer listed only plant dishes. The
preference signal is constraint tracking and internal consistency, not style.

**Why this beats every other candidate: it predicts the whole benchmark ordering, not just maths.**

| benchmark | demand | change vs parent |
|---|---|---|
| MGSM | multi-step, carry quantities to a final answer | **+9** |
| IFEval | track and satisfy stated constraints | **+4** |
| Global-MMLU | knowledge recall | +1.1 … +1.8 |
| GreekMMLU, bare label | pure recall, no chain | **−0.4** |

Gains scale with how much multi-step constraint-tracking a task needs and vanish or reverse where it
is pure recall. This also makes MGSM and IFEval **one** finding rather than two unrelated ones, which
no content-based explanation does.

### The test

Same shape as Q1's ablation, and better powered: remove the **120 compositional pairs** against a
random control of equal size. That is 35% of the data against Q1's 16%, so if constraint-tracking is
the mechanism the drop should exceed the ~4 pp this design resolves — unlike the 2 pp Q1 could not
pin down. Reuse `data/rlhf/dpo01_nomaths/build.py` (swap the selector), the seed-matched
item-level McNemar primary, and the same RC-style control drawn from non-compositional pairs.

**Note the difference in kind.** Q1 asked whether *content* transferred. Q5 asks whether a *skill*
transferred. For 343 examples, the second is the more plausible thing to have taught.

### Caveat recorded 20 Sept

The `embedded_maths` label used for Q1 effectively required **digits**: all 56 flagged pairs contain
digits and none was word-only. Of the 287 kept pairs, 26 contain a number-word with no digit, but
only **2** contain any arithmetic term (`σύνολο`, `ποσοστό`); the rest are incidental counting
("two theories", "two neurons", "two sides"). So the digit-based selector was a real limitation but
did not leave meaningful quantitative content in the ablated set. A `compositional` selector for Q5
is label-based rather than regex-based and does not inherit this problem.

## Sequencing

Q2 is running. Q4(1) needs one 45-minute re-run to persist the per-choice scores first. Q1 is the one that
decides round 2's design and costs 2 training runs. Q3 costs 2 training runs and closes the original
round's unfinished business.
