# Astra review: R-DPO5

Date 2026-09-18 22:34 · model gpt-6-astra (asserted from rollout rollout-2026-09-18T22-29-44-01a0b5ff-06c6-7301-a9cb-f7af0daaf7b1.jsonl) · effort xhigh · 4.5 min · prompt 5,717 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/RLHF_COORDINATION/reviews/R-DPO5_brief.md`

(1) **Verdict: HOLD the IPO launch pending implementation and configuration verification; beta 10 is mathematically coherent, but not empirically validated.** The supplied excerpt defines a difference of separately length-normalised log-ratios, so beta 10 targets **0.050 per token**, and beta 15 targets **0.0333**. The original beta 0.1 rationale was wrong for this implementation. However, neither the proposed target nor the claim that excessive separation caused the benchmark damage follows from the reported correlations. I independently checked the algebra and arithmetic; I could not inspect the installed source because command execution was unavailable and terminal/browser access was denied. **No sample rows or row IDs were supplied: row-level defect counts and failure rates are therefore unavailable.** This review does not recommend stopping the running DPO arms or modifying completed datasets.

(2) **Findings, ranked by severity.**

**BLOCKER — The installed loss path and executable IPO configuration remain unverified.**  
**Evidence:** The only implementation evidence available is the pasted excerpt, with an ellipsis between score construction and normalisation. It supports your interpretation, conditional on those scores actually being summed completion log-ratios. It does not establish the imported implementation, preceding transformations, active loss combination, or runtime overrides.

**Fix before IPO launch:** Provide the actual imported module path, version and file hash, the complete relevant scoring/loss path, and the resolved configuration. Run a CPU test through that implementation using unequal completion lengths. One discriminating synthetic fixture is:

- Chosen and rejected summed log-ratios: **10 each**.
- Token counts: **100 chosen, 200 rejected**.
- Expected IPO delta: **10/100 − 10/200 = 0.050**, despite a summed gap of **zero**.
- Expected IPO loss at beta 10: **zero**.

This fixture is a proposed test, not an inspected dataset row. Verify that the scoring diagnostic uses exactly the trainer’s masks and denominators.

**HIGH — Beta changes the optimisation dynamics as well as the target; benchmark preservation could reflect insufficient learning.**  
**Evidence:** For the supplied loss,

\[
L=(\delta-1/(2\beta))^2,\qquad
\left.\frac{\partial L}{\partial\delta}\right|_{\delta=0}=-1/\beta.
\]

| Beta | Target | Initial derivative with respect to delta |
|---:|---:|---:|
| 0.1 | 5.000 | −10.000 |
| 10 | 0.050 | −0.100 |
| 15 | 0.0333 | −0.0667 |

The correction changes the initial scalar derivative **100-fold**. IPO also changes sequence weighting through token normalisation. This does **not** imply 100-fold smaller Adam updates: adaptive normalisation, clipping, other loss terms and subsequent gradients matter.

**Fix before IPO launch:** Pin the learning rate, scheduler, loss weights, clipping, optimiser settings and update budget. Pre-register measurements of actual policy movement—such as reference-relative KL and parameter-update norms—alongside preference improvement. Include a weakly updated DPO checkpoint as a comparator. Do not mechanically compensate with a 100-fold learning-rate increase.

**HIGH — “Separation reaches target but benchmarks degrade ⇒ over-optimisation is WRONG” rejects a much broader hypothesis than this intervention tests.**  
**Evidence:** The squared loss supplies a **per-pair optimum, not a hard ceiling**. A train **mean** of 0.050 does not establish that individual margins are near target, that memorisation disappeared, or that a length shortcut disappeared. Moreover, beta 10’s target is **6.25 times** the supplied dev mean of 0.008. Moving train margins toward this target could still leave substantial overfitting.

**Concrete fix, interpretation only:** Replace the prediction with:

> Under the specified IPO recipe, bringing training margins near target T, while producing nontrivial preference learning, is sufficient to keep the pre-registered primary benchmark degradation within ε of the parent.

Specify ε, endpoints, checkpoint selection, seed aggregation and uncertainty intervals beforehand. Record per-pair loss, margin quantiles, negative-margin fraction and train/dev separation. Failure rejects **the sufficiency of this target and recipe**, not every over-optimisation explanation.

**HIGH — The causal and “envelope-only” conclusions exceed the reported evidence.**  
**Evidence:** The update correlations use **21 checkpoints from seven trajectories**; the length correlation uses **eight related models**. These are not independent experimental replications. Also:

- The purportedly matched update budgets, **6.45e−5 and 8.60e−5**, differ by **33.3%**.
- Learning rate × steps is a nominal optimisation-budget proxy, not measured parameter or policy movement.
- Parent-to-worst MGSM accuracy falls **12.0 percentage points**. The IFEval family pattern alone cannot establish that this, or the reported Global-MMLU damage, is entirely an output-format effect.

**Concrete fix, interpretation only:** Describe length as a strong candidate mediator or shortcut. Use paired seed comparisons and checkpoint comparisons at measured movement. Audit failed answers for formatting, truncation, missing reasoning and substantive errors. A controlled length-balanced preference intervention would test the proposed data mechanism more directly than IPO alone.

**MEDIUM — The dev accuracy comparison has an unresolved denominator or metric mismatch.**  
**Evidence:** On **54 equally weighted binary pairs**, 0.611 corresponds to **33/54**. But 0.643 cannot be a single accuracy: **34/54 = 0.630**, while **35/54 = 0.648**, rounded to three decimals.

**Fix:** Report numerator, denominator, ties, exclusions and any averaging or weighting. Provide paired outcomes for the shorter-response heuristic and trained model. Their aggregate scores alone cannot establish that they succeed on the same pairs.

**MEDIUM — The served-versus-lm_eval result confounds task with evaluation lane and overstates independent evidence.**  
**Evidence:** The **44 positive versus three negative deltas** support the stated small binomial p-value *if signs are independent*. Shared checkpoints, parent and evaluation items undermine that assumption. MATH-500/IFBench versus IFEval/MGSM/Global-MMLU also changes the task, not just the serving route.

**Fix:** Treat the sign count as descriptive. Supply the complete delta matrix and its aggregation units. Compare at least one identical task through both lanes with matched prompt formatting, decoding and scoring. Use uncertainty estimates that preserve shared-item and shared-seed dependence.

**MEDIUM — A fresh five-epoch run is not automatically a determinism check.**  
**Evidence:** Only its first three epochs could reproduce the original three-epoch run. If the scheduler depends on the planned five-epoch horizon, even that prefix can change.

**Fix:** Preserve the original learning-rate sequence, seed, data order and other training conditions through epoch three. Separate “reproduction of the original prefix” from “effect of additional training.”

(3) **What is good and should not be changed.**

- Catching the unit error by inspecting implementation was essential. Preserve the distinction between summed and per-token diagnostics.
- Retain the parent, full evaluation batteries and all intermediate checkpoints; they enable more informative comparisons than endpoint-only results.
- Keep the shorter-response baseline and train/dev separation measurements. They expose plausible shortcuts and generalisation gaps.
- Keep the queued seed replicates. A **2.0pp ranking spread** against a reported **±1.0pp noise floor** warrants replication before selecting an alpha winner.
- Preserve the disagreement between evaluation suites in the write-up. It is useful evidence even before its cause is resolved.

(4) **Answers to the five specific questions.**

**Q1 — Parameterisation and target choice.**  
**Yes, conditional on the supplied source:** the statistic is

\[
\delta=
\frac{\log\pi_\theta(y_c|x)-\log\pi_{\rm ref}(y_c|x)}{N_c}
-
\frac{\log\pi_\theta(y_r|x)-\log\pi_{\rm ref}(y_r|x)}{N_r}.
\]

Beta 10 → **0.050** is correct. Installed-source verification remains outstanding.

There is no demonstrated optimal target in the reported train/dev means. The dev value **0.008** is an outcome under another trained policy, not an estimate of an ideal training target. Matching it arithmetically would give beta **62.5**, but that does not justify selecting 62.5. Beta 10 is defensible as an exploratory target; beta 15 is a relatively narrow local sensitivity check.

**Q2 — Does normalisation help or hurt this pair set?**  
It removes direct accumulation of log-ratio contributions with sequence length. It **does not remove length information or preference-label confounding**.

For each fixed training pair, normalisation gives individual tokens on the shorter side larger coefficients. The denominators are fixed by the supplied completions; the optimiser is not directly choosing a shorter denominator. Learned stopping behaviour, content and length can nevertheless remain entangled.

Therefore, **59% shorter chosen responses does not by itself make IPO unsuitable**, and it certainly does not establish that IPO fixes the confound. Report preference performance and margins by length difference, including comparable-length pairs. Audit whether short chosen responses actually omit requested content before changing labels.

**Q3 — Is the length diagnosis over-read?**  
**Yes, if presented causally.** The correlations and heuristic are consistent with the diagnosis, but also with a common cause—for example, training simultaneously changing brevity and reasoning behaviour. Seed replication tests reproducibility; a controlled intervention on the length confound is needed to identify that mechanism.

**Q4 — Are the five programme components distinguishable?**

| Component | Distinct question | Main limitation |
|---|---|---|
| IPO | Does this finite-target, normalised objective improve the trade-off? | Changes objective, token weighting and optimisation dynamics |
| Fresh arm05, five epochs | Does damage continue with exposure? Can the original prefix reproduce? | Scheduler-prefix caveat |
| Seed replicates, arm05/arm01 | Are effects and rankings reproducible? | Must report paired seed effects, not just pooled checkpoint counts |
| 4e−6, alpha 0.25 | Does learning rate alter the trajectory or attainable trade-off? | Same-epoch comparisons also change nominal update budget |
| Second IPO beta | Is the result sensitive to target choice? | Overlaps with the first IPO arm and also changes gradients |

These are **five experimental components**, not necessarily five individual training runs. They answer useful questions, but the programme still lacks a direct intervention on the suspected preference-length confound.

**Q5 — Are the predictions falsifiable?**  
The quoted prediction is observable in a loose sense but **logically overbroad and operationally incomplete**. Define “reaches target,” “degrades,” the benchmark endpoints, tolerances, seed rule and checkpoint-selection rule. Also distinguish “IPO preserved benchmarks while learning preferences” from “IPO stayed close to the parent.” Use the narrower prediction proposed above.

(5) **Open questions for the owner.**

- What are the imported source path/hash, complete IPO loss path and resolved configuration? What exactly does alpha control?
- Are reported margins measured with the same completion masks, truncation, EOS handling and fixed reference as training?
- Can you provide row IDs with lengths, preference labels and train/dev margins, plus the exact dev-score numerator and aggregation rule?
- What independent groups define the split—prompt, source, template or generated variant—and were near-duplicates checked?
- What produces the 47 served-lane signs, and are any identical tasks evaluated through both lanes?
- What precise seed, scheduler-prefix and acceptance criteria are pre-registered for the follow-up?

The remaining launch gate is confined to **verifying and specifying IPO**. Findings about DPO01’s interpretation should be logged; they do not justify drastic action on completed data.