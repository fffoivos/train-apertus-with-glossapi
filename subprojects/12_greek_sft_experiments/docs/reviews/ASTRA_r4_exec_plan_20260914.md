# Astra review: r4_exec_plan

Date 2026-09-14 08:58 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T08-51-04-01a09e78-1436-7632-b0c5-6a55a975274c.jsonl) · effort xhigh · 7.0 min · prompt 12,657 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_r4_exec_plan.md`

**1. Verdict**

**NO-GO for Phase B as written; the plan is repairable within its stated reserve.** The three arms can screen training packages, but they do not cleanly separate derivation style, token dose, answer formatting, and Level-5 content. More seriously, the fallback advances M2 even after a failed guardrail, and the translation gate explicitly checks problems without explicitly checking translated derivations. The 500-item decision rule is a useful screen for larger gains, not a well-powered test of a true 3-point improvement. **Scope:** I reviewed the supplied plan and independently calculated the arithmetic and statistical examples below. No sample rows, row IDs, manifests, predictions, or ledger were supplied. Consequently, I cannot report independently verified row-level failure rates. The stated 9/300 translation failures and 343/500 unboxed outputs remain owner-reported counts; the latter concerns model outputs, not inspected training targets. I have not re-reviewed the previously reviewed datasets.

**2. Findings ranked by severity**

**F1 — BLOCKER: The decision rule advances a potentially harmful arm.**

Evidence: §4 says:

> “Otherwise report inconclusive and take M2 to the pass anyway”

“Otherwise” includes M2 losing to M0, exceeding the 2-point IFEval/MGSM regression limit, and failing to demonstrate improvement. These outcomes are materially different from an underpowered positive result. Moreover, comparing both candidates only against M0 does not answer whether Level 5 improves on M1.

**Fix:** Freeze separate outcomes before launch:

- **Harm/guardrail failure:** that arm cannot advance.
- **Positive but statistically inconclusive:** retain its checkpoint; use the reserve for a predefined confirmation or dose check.
- **Qualified improvement:** advance the eligible arm.

Predeclare **M1−M0** as the worked-target contrast and **M2−M1** as the Level-5 contrast. An unqualified M2 may remain an explicitly exploratory candidate, but cannot bypass the safety criteria or become the default winner.

**F2 — HIGH: The stated verification does not cover the central intervention.**

Evidence: §3 A1 specifies fidelity of:

> “every problem translation”

The intervention is principally **solution translation**. Meanwhile, §7 asserts:

> “they are correct by construction”

A published derivation can acquire a reversed inequality, missing condition, changed variable, or omitted step during translation while retaining the correct boxed answer. Polish happens after the listed checks, creating another opportunity for changes.

**Fix:** Explicitly verify **both problem and complete derivation against the pinned source**, including step correspondence, assumptions, equations, and final answer. Preserve mathematical spans during polish and rerun relevant checks on the final exported text.

This respects the owner’s rule: **source-fidelity verification is not an independent-solver agreement filter**. Resolve failures against the source; do not reject a faithful derivation because another model produces a different answer.

Also:

- Specify semantic answer normalization; superficial string normalization can reject equivalent answers.
- Treat length ratio as an anomaly signal. A **median** of 0.8–1.25 cannot identify individual omitted derivations.
- Replace “correct by construction” with “source-backed, subject to translation and export verification.”

No actual translation error is independently established here: the failure is in the specified gate.

**F3 — HIGH: The contrasts identify packages, not all the variables claimed.**

Evidence: §4 promises:

> “Only the Greek maths block varies”

But M0 uses terse targets, while M1 uses longer worked targets with preserved boxes. One epoch therefore changes supervised token exposure, optimizer steps, potentially answer extraction, and the effective fraction of background replay. M2 additionally changes both difficulty composition and total training dose.

Matching problem IDs is also insufficient if prompts differ or solution/mechanical filtering removes different rows. The plan explicitly synchronizes **problem-fidelity drops**, not every subsequent exclusion.

**Fix:**

1. Freeze byte-identical prompts and the same retained source-problem IDs for M0/M1, using the intersection after all relevant checks.
2. Standardize the final-answer convention across arms so boxing is not an additional treatment.
3. Publish per-arm processed tokens, supervised tokens, updates, exposures per source problem, and learning-rate trajectory.
4. State the estimand honestly: **one exposure to terse versus worked targets**, including their different lengths.

That is a legitimate practical experiment. If the intended claim is improvement **at equal compute**, add a token-matched control or redesign around fixed token budgets, explicitly acknowledging the resulting difference in example repetitions. For Level 5, either test its addition as a package or replace an equal token quota of lower-level examples to test content composition.

**F4 — HIGH: “10% replay” understates its role, and one epoch has not been qualified as a screen.**

Evidence: §4 specifies approximately **12M background replay tokens**, alongside **6.7M English maths** and approximately **1.31–2.6M Greek maths**.

Using those estimates, background replay occupies approximately **56–60% of pilot tokens**. “10%” describes sampling from the historical pool, not the final training mixture.

If 21M denotes processed tokens, the stated batch of \(16\times4096\) implies approximately **320 updates**, with roughly **10 warmup updates**. That is a plausible inexpensive screen, but the plan supplies no evidence that rankings after this exposure predict rankings after the final pass.

**Fix:** Rename and report both quantities: historical sampling fraction and final mixture fraction. Freeze the intended maths dose and schedule. Evaluate the unchanged stage-1 parent under the same protocol, reusing predictions only when configurations match exactly.

An inconclusive pilot should trigger a predefined continuation of a saved checkpoint or a dose diagnostic—not a conclusion that worked targets failed. The common English rebuild and replay do not invalidate pairwise package comparisons, but absolute improvement cannot be attributed to Greek worked targets alone.

**F5 — HIGH: The statistical rule is not adequately powered for a true 3-point gain without additional assumptions.**

Evidence: §4 requires ≥3 percentage points and a paired bootstrap 90% lower bound above zero.

At \(n=500\), **3 points means 15 net additional correct answers**. Baseline accuracy alone does not determine paired power. Let \(q\) be the fraction of items on which the two models disagree about correctness. The approximate standard error of their difference is:

\[
SE(\hat\Delta)\approx\sqrt{\frac{q-\hat\Delta^2}{500}}.
\]

For an observed improvement of exactly 3 points:

| Discordant fraction \(q\) | Approximate SE | Approximate lower end of a central 90% CI |
|---:|---:|---:|
| 10% | 1.41 pp | +0.68 pp |
| 20% | 2.00 pp | −0.28 pp |
| 25% | 2.23 pp | −0.67 pp |

These are calculated normal approximations, **not bootstrap results from model predictions**.

At a true effect of exactly 3 points, requiring the observed effect to reach 3 points gives roughly 50% passage probability before the other gates; significance can reduce it further. For illustration, at 20% discordance, approximately **1,368 paired items** would provide 80% power for a positive lower bound alone under this approximation. That does not remove the separate observed-3-point threshold issue.

**Fix:** Specify whether “90%” means a central two-sided interval or a one-sided lower bound, estimate plausible discordance from existing paired predictions, and publish the resulting operating characteristics. Predeclare a testing hierarchy or multiplicity treatment for the two contrasts.

Also, observed IFEval/MGSM differences within 2 points are **screening tolerances, not demonstrated noninferiority**. Report paired uncertainty and distinguish “no observed breach” from “retention established.” Bootstrapping items does not measure training-seed variability.

**F6 — HIGH: Final-pass retention and promotion criteria do not protect the claimed objective.**

Evidence: §5 includes:

> “2,000 worked maths rows as replay”

The plan itself reports a prior pass reducing maths from **12.8 to 7.6**, a **5.2-point loss**. There is no token-based justification for why 2,000 rows, repeated across two epochs, will prevent recurrence.

The promotion rule also states:

> “MATH-500-el ≥ 15 (double R3_pass’s 10.0…)”

**15 is 1.5×10, not double.** It remains **17.2 points below** the quoted Krikri score of 32.2. Furthermore, the IF floor references R3_pass rather than necessarily protecting the incumbent arm B; final promotion does not explicitly retain the pilot’s MGSM guardrail or bind the English-maths safeguard.

**Fix:** Make maths an explicit token-weighted component of the final pass, with documented source/level coverage. Freeze a permissible pre-pass→post-pass maths loss and evaluate it alongside the absolute promotion floor.

Protect IF, MGSM, English maths, and dialogue against the relevant incumbent/pre-pass comparators. Specify denominators and protocols for “loops ≤7” and “coherence ≥90%.”

Keep 15% if it is an intentional **intermediate improvement threshold**, but label it accordingly. Beating Krikri is a separate milestone requiring a comparable evaluation.

**F7 — HIGH: Benchmark provenance and protocol need explicit launch receipts.**

Evidence: §2 targets:

> “the 172 families with 13-gram/exact hits”

§3 A4 additionally lists generic “decontamination,” without defining coverage or supplying the excluded IDs. This does not establish that filtering propagates across English examples, Greek translations, repeated copies, and replay. Nor does it establish whether the stage-1 parent already encountered overlapping material.

**Fix:** Require a source-family exclusion manifest covering all queued representations and copies. Audit and disclose inherited exposure; do not pretend descendant filtering removes prior training exposure.

Freeze benchmark item IDs, prompt/template, decoding, output-token limits, extraction, equivalence grading, and unresolved-adjudication policy. Reuse comparator scores only with matching receipts. Longer-output training makes truncation and extraction particularly relevant.

Repeatedly selecting on MATH-500 also makes it a development benchmark. Reserve a separate uncontaminated confirmation set for the eventual claim of beating Krikri.

**F8 — HIGH: The correcting-data fallback contradicts an accepted finding.**

Evidence: §3 A3 says:

> “Falls back to v1 if the conversion fails checks.”

The plan simultaneously accepts H10 as a reason to replace v1.

**Fix:** Remove automatic fallback. Repair the conversion before Phase C, or explicitly stop that assembly path. This is an integration-policy finding, **not a new review or requested alteration of the completed correcting dataset**.

**MEDIUM/LOW — log in §7**

- **Budget arithmetic is sound:** 3.9 + 7.3 + 1.5 = **12.7 node-hours**, leaving **11.7**. The cited R3 figures imply approximately **32.6M tokens/hour**; planning at 28M is conservative if token definitions and execution conditions match. Startup, checkpointing, evaluation and retry estimates remain unverified.
- **Row estimate needs reconciliation:** A2 plus M0 totals approximately **51,070 rows before replay and filtering**, versus §4’s approximately 45k. Use assembled counts, not these estimates, for scheduling.
- **The calendar is conditional:** A1 lists **18,069 remaining translation/fidelity calls before polish**, excluding the missing derivation-fidelity work. A concurrency ceiling of 100 is not measured throughput. The certificate, queue availability, retries and review turnaround prevent a firm 15 September morning promise.
- **Gate placement is ambiguous:** §6 explicitly mentions gate 1 before pilots; gate 2 appears under Phase C. Include pilot launch readiness in the existing pre-pilot review rather than adding reviews at every artifact boundary.
- **Sixty-row samples are qualitative audits:** An independent random 60-row sample has approximately a **29.8% chance of missing every error** at a true 2% error rate. Do not use it alone to certify the residual error threshold.
- **Native terse targets dilute the intervention:** 4,071 native rows are **28.9% of the nominal 14,070-row M0 Greek block** before filtering. Keeping them fixed is appropriate for the contrast; report this limitation and do not rewrite them mid-pilot.

**3. What is good and should not be changed**

- The same parent checkpoint and shared background data are useful controls.
- Using published derivations directly targets H9 and avoids unnecessary synthetic re-solving.
- Limiting GSM8K repetitions by source problem addresses the verified concentration problem.
- Keeping IFBench-el untargeted preserves a valuable external check.
- Saving intermediate checkpoints and testing maths before and after the Greek pass supports diagnosis.
- Source-based fidelity checks are compatible with the prohibition on answer-agreement filters.
- The substantial reserve makes conditional follow-up feasible. Preserve it until the pilot readout.

**4. Answers to the specific questions**

1. **Do the three arms isolate the claimed variables?** Partially. They compare replacement/addition packages. They do not isolate derivation style from dose and formatting, or Level-5 content from added exposure. M2−M1 needs its own declared comparison.
2. **Is one epoch with 10% replay a valid screen?** Yes, provisionally. It is actually approximately 56–60% background replay in the stated mixture. Without dose qualification, a negative result is inconclusive.
3. **Is the rule adequately powered?** Not for reliably detecting a true 3-point gain as written. Paired discordance, interval convention, multiplicity and guardrail uncertainty must be specified.
4. **Is fidelity-all plus mechanical verification sufficient?** Not as specified: derivation fidelity and final post-polish verification are missing. Add source comparison, not solver-agreement filtering.
5. **Is stacking sound, or should maths go into the pass?** Stacking is plausible but unproven. The plan already puts some maths into the pass; the unresolved issue is its dose. Make final-pass maths a defined mixture component. A direct mixed-pass comparator is a useful reserve experiment if the stacked candidate loses its gains.
6. **Are budget and timeline realistic?** The node-hour budget is plausible on paper. The dates are conditional and currently insufficiently evidenced.
7. **What critical work is missing?** Binding retention gates, derivation verification, complete provenance, comparable evaluation, direct Level-5 testing, and a diagnosis of the remaining gap to Krikri. Produce a paired error breakdown by level, subject, reasoning failure, extraction failure and truncation. More polished targets alone may not address that gap.

**5. Open questions for the owner**

- Where are the frozen source IDs, final paired manifests, and post-polish samples supporting A1/A2?
- What are the **processed versus supervised** token counts and optimizer steps for each arm?
- What paired prediction files support the baseline scores, and do Krikri and Apertus use identical evaluation protocols?
- What maths token fraction and maximum acceptable maths loss will govern Phase C?
- Is 15% explicitly an interim promotion target, and which independent benchmark will support the eventual “beats Krikri” claim?
- Does the CHF 230 cap cover only CSCS usage, and what measured generation/evaluation throughput supports the dated schedule?