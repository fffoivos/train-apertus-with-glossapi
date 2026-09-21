# Astra review: R-DPO6

Date 2026-09-19 13:08 · model gpt-6-astra (asserted from rollout rollout-2026-09-19T13-01-25-01a0b91d-137e-7a80-99b2-810ff9089cb2.jsonl) · effort xhigh · 6.7 min · prompt 5,999 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/RLHF_COORDINATION/reviews/R-DPO6_brief.md`

## 1. Verdict

**Hold the current conclusions for revision; preserve the completed experiments.** The brief supports withdrawing the alpha ranking, treating the IPO falsification as inconclusive, and reporting mixed benchmark outcomes. The common-config baseline is legitimate for a clearly defined comparison, but it does not establish improvement over the originally served parent. The balanced subset is promising without isolating a causal length effect; GreekMMLU supports a small, stable gain on one fixed slice, not a general knowledge improvement. **This is an aggregate-level review:** no dataset rows, item-level predictions, or underlying artifacts were available for inspection. Dataset rows reviewed: **0**; row-level failure rate: **not estimable**, not 0%. Experiment identifiers below are not dataset row IDs.

## 2. Findings ranked by severity

### BLOCKER — Independent verification is missing

**Evidence:** The supplied material contains aggregate results and references to `cluster/test_dpo_local.py`, but no sample rows, per-seed score table, per-item predictions, bootstrap implementation, or complete implementation fingerprint. I cannot independently confirm the reported **9/9 fixtures**, reproduce the confidence interval, or verify the **44/3** signs.

**Concrete fix:** Attach the existing evidence bundle to the write-up: dataset IDs and hashes; full run/config identities; per-seed scores; item IDs, predictions and correctness; bootstrap code and confidence level; and fixture output tied to the full TRL commit. Until then, label these results **owner-reported**, not independently verified. Missing artifacts can be handled by narrowing claims; they do not require restarting completed experiments.

### HIGH — The “noise floor” is being used as a significance and equivalence threshold

**Evidence:**

- `arm05_ep3` versus `arm07_ep3` provides **one same-seed contrast**, not a distribution of execution variability.
- The MGSM reference changes from **2.8 pp** in finding 1 to **1.6 pp** in finding 6 without an explanation.
- Four values each within **±0.9 pp** cannot have a mean of **−0.97 pp**. Therefore, “every point inside the floor” is inconsistent with the quoted IFEval floor unless a different definition is intended.
- The alpha interval **[−0.48, +1.77] pp** crosses zero. That undermines the ranking; it does not establish equivalence.

**Concrete fix:** Separate training-seed SD, the observed same-seed repeat gap, and uncertainty from benchmark items. Replace “inside the floor” with the actual contrast and uncertainty. Supply the four endpoint values and identify the source of the 1.6 pp figure. Describe the plateau as **“no reliable improvement demonstrated over the tested range,”** not proven recovery to, or equality with, the parent.

### HIGH — The fair baseline answers a conditional question, not the deployment question

**Evidence:** All **8/8** correction cells are arithmetically consistent with adding **1.7 pp IFEval** or **2.4 pp MGSM**.

Let \(P\) denote parent weights, \(A\) trained weights, and \(g_0,g_1\) the original and checkpoint configurations. Your corrected contrast is:

\[
Y(A,g_1)-Y(P,g_1).
\]

That is a valid comparison under \(g_1\). It does **not** require assuming that config effects are identical for parent and trained weights. However, it does not identify \(Y(A,g_0)-Y(P,g_0)\), or establish improvement over the existing deployment \(Y(P,g_0)\).

The phrase **“a third of the apparent damage”** also lacks a consistent denominator. For MGSM, the correction accounts for approximately **28%** of the standard-arm deficit, **60%** of the balanced deficit, and **20%** of the IPO deficit.

**Concrete fix:** Report both the common-config comparison and the comparison against the original parent. Name the configuration in every headline result. Attribute the measured effect to the **configuration bundle**; the brief does not isolate EOS, padding, or caching individually. If trained-weight results under \(g_0\) do not already exist, mark them unmeasured.

### HIGH — The balanced intervention does not isolate length

**Evidence:** `armBAL` changes both the length distribution and the example population:

- **274 versus 343 pairs:** 69 fewer, or **20.1% fewer**.
- Chosen/rejected mean word ratio: **0.992 versus 0.785**.
- Chosen shorter: **50% versus 59%**.
- Reported MGSM deficit: **−1.6 versus −6.3 pp**, a **4.7 pp** improvement.

The three-run mean is useful evidence for this **subset recipe**. It cannot attribute the improvement specifically to length. Selection can also change task composition, difficulty and preference quality. Word balance does not establish balance in model tokens.

Fewer pairs also do not establish less actual parameter movement. Even fewer optimizer steps would establish only a change in nominal training exposure.

**Concrete fix:** Write: **“The selected length-balanced subset reduced the observed MGSM deficit; length, selection and training exposure remain confounded.”** Report its individual seed scores, SD, steps and selection rule from existing records. Unless an existing control separates these factors, withdraw the causal interpretation.

### HIGH — IPO failed its gate, but “barely trained because of beta” is not established

**Evidence:** Both reported IPO runs failed to approach the target:

- \(0.0010/0.0500 = 2.0\%\)
- \(0.0013/0.0500 = 2.6\%\)

Thus **2/2 reported runs** missed the separation gate; both reward-accuracy values were below 0.5. Their statistical departure from chance cannot be assessed without the dev-set denominator and uncertainty.

For the stated loss,

\[
L=(\delta-1/(2\beta))^2,
\qquad
\left.\frac{\partial L}{\partial\delta}\right|_{\delta=0}=-1/\beta,
\]

the initial derivative comparison is correct: **100× smaller magnitude** at beta 10 than beta 0.1. But raw gradient scaling does not imply proportional optimizer updates. If Adam/AdamW was used, normalization can substantially cancel a common gradient scale. Small **dev** separation can also reflect failed generalization or heterogeneous margins rather than negligible training.

**Concrete fix:** Retain **“the preregistered falsification is inconclusive because its gate was unmet.”** Replace “barely trained” with **“failed to achieve the required dev separation.”** Treat beta-induced under-training as a hypothesis unless existing training-margin and optimizer-update evidence establishes it.

### HIGH — GreekMMLU seed stability is being mistaken for broad precision

**Evidence:** On **250 items**, one answer is **0.4 pp**. The parent’s `.576` corresponds to **144 correct**; arm means around `.595–.597` represent approximately **five additional correct answers per run**, net.

An SD of `.002`—**0.2 pp**—is entirely plausible when seeds produce almost identical answer choices. It measures stability on those same items. It does not measure uncertainty about broader Greek knowledge or establish that the benchmark is insensitive.

The reported **−4 to −7 pp Global-MMLU-Lite** movement also prevents a general capability-improvement claim. Its per-language breakdown and comparability are not supplied.

**Concrete fix:** State **“approximately +2 pp on this fixed GreekMMLU-250 slice, with low between-seed variation.”** Show item-level wrong→right and right→wrong changes, scoring consistency, and the slice’s role in model selection. Keep multilingual results beside the Greek result. Do not present seed SD as the uncertainty of task-level generalization.

### HIGH — Correlations and the sign tally do not establish the proposed mechanisms

**Evidence:**

- **21 checkpoints** are not 21 independent experiment replications.
- The length correlation uses **8 correlated models**.
- `lr × steps` is nominal training exposure, not measured parameter movement.
- **44 positive / 3 negative** gives **93.6% positive among 47 counted signs**, but the units, ties, exclusions and dependency structure are unspecified.
- Aggregate MGSM and MMLU scores cannot distinguish formatting, truncation, answer extraction, changed choice preferences and reasoning errors.

**Concrete fix:** Preserve correlations as exploratory descriptions of the selected runs, with their dependency structure explicit. Withdraw causal wording such as **“governs”** and the exclusive **“envelope-not-content”** explanation. Retain the sign tally descriptively; restore inferential claims only if existing records establish valid units and analysis.

## 3. What is good and should not be changed

- **Retain the parent-under-checkpoint-config control.** It exposes a consequential evaluation confound.
- **Retain all replication results**, including the same-seed repeat and unfavorable seeds. They materially change the interpretation.
- **Keep alpha superiority withdrawn.** The observed +0.70 pp does not support selecting a winner.
- **Keep the IPO gate explicit.** An unmet gate prevents the preregistered falsification from being declared.
- **Keep the balanced subset and multilingual results in the report.** Both constrain the explanation.
- **Preserve the implementation fixtures and completed artifacts.** Their reported design addresses the earlier normalization ambiguity, although I have not inspected their execution.

## 4. Answers to the specific questions

**1. Is the fair-baseline correction legitimate?**

**Yes, for the effect of training under the checkpoint configuration.** Config–weight interaction does not invalidate that direct comparison. It prevents transporting the result to another configuration without evidence. It becomes misleading if the corrected result is presented as improvement over the originally served parent, or if the checkpoint configuration is chosen because it makes the trained arms look better.

**2. Does the length result survive n=3?**

**The observed subset-recipe improvement survives as preliminary evidence; the isolated length explanation does not.** Three runs are not automatically inadequate, but the balanced-arm dispersion and individual contrasts are missing. A 4.7 pp difference divided by a purported 1.6 pp floor is not a significance test.

The GreekMMLU/Global-MMLU split neither validates nor refutes the length mechanism. It shows that an MGSM improvement cannot stand in for preservation of broader capabilities.

**3. Is GreekMMLU +2 pp at SD .002 believable?**

**Yes.** It is consistent with roughly five additional correct answers and very similar predictions across seeds. The small SD establishes reproducibility on this slice, conditional on the reported scoring. It establishes neither broad precision nor insensitivity. Those require different evidence.

**4. Which 18 September claims survive?**

| Claim | Disposition | Permissible wording |
|---|---|---|
| “Alpha 0.25 is best” | **Withdrawn** | Its observed +0.70 pp advantage remains unresolved; the reported interval crosses zero. |
| “Movement governs damage,” r = .92–.97 | **Withdrawn as a governing mechanism** | Nominal training exposure correlated with scores across the selected, dependent checkpoints. |
| “Length predicts MGSM,” r = .952 | **Survives only as an exploratory association** | Association within eight related models; predictive generalization and causality remain unestablished. |
| “Envelope-not-content” | **Withdrawn** | Error mechanisms have not been separated with item-level evidence. |
| Served-lane sign test, 44/3 | **Withdrawn as inferential evidence pending unit audit** | The supplied tally is 44 positive and 3 negative; its statistical interpretation is unverified. |
| Extra movement produces an IFEval improvement beyond the parent | **Inside-the-floor / unresolved** | No reliable positive overshoot has been demonstrated; reconcile the endpoint arithmetic. |
| IPO falsifies the hypothesis | **Withdrawn** | The required separation gate was unmet in both runs. |
| GreekMMLU improves by approximately 2 pp | **Survives as a fixed-slice observation** | Low seed variation on GreekMMLU-250, alongside reported multilingual declines. |

Here, “inside-the-floor” follows your requested disposition vocabulary; it does **not** mean a single repeat gap establishes statistical equivalence.

**5. Is anything shippable?**

**This evidence does not establish a shippable general replacement for the parent.** The standard recipes retain a roughly **6.3 pp MGSM deficit** under the common configuration, and the multilingual regression must be included in the decision.

`armBAL` is the strongest candidate for a narrowly defined application, but its **−1.6 pp MGSM** mean is not demonstrated non-inferiority. Nor does the brief establish that its GreekMMLU gain matches the standard arms. A shipping claim needs one complete scorecard for the actual candidate and deployment configuration, assessed against explicit acceptable regressions. Do not construct a “best case” from different arms.

## 5. Open questions for the owner

1. Where are the existing sample rows, immutable run manifests, per-seed tables and item-level outputs? These are needed for row-ID evidence and countable failure rates.
2. What precisely are the **0.9, 2.8 and 1.6 pp** quantities? What are the four far-end IFEval values?
3. What confidence level and resampling unit produced the alpha interval? Were matched seeds resampled together?
4. What did “magnitude-matched” mean, and what were `armBAL`’s seed scores, optimizer steps and selection criteria?
5. Which optimizer was used for IPO, and what do the existing training margins and update measurements show?
6. What constitutes one served-lane sign? Were there ties, exclusions or repeated measurements of the same underlying unit?
7. Which configuration is intended for deployment, and what losses in MGSM and multilingual performance are acceptable?

Resolve these from existing artifacts in the remaining review cycle. Where evidence is unavailable, narrow the assertion rather than declaring the uncertainty resolved.

*Access limitation: the execution host was disabled and computer-use access was denied. No local artifacts were opened and no tests were rerun.*