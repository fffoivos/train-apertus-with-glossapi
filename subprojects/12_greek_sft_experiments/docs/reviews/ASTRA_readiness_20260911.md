# Astra review: readiness

Date 2026-09-11 14:23 · model gpt-6-astra (asserted from rollout rollout-2026-09-11T14-19-10-01a09031-627c-7f11-9b7b-6232fdbbc635.jsonl) · effort xhigh · 4.3 min · prompt 63,707 chars · limit deltas {('codex', '10080'): 0.0} · brief `../docs/reviews/briefs/astra_readiness.md`

**1. Verdict: NO-GO for launch on the supplied evidence.** The assembled totals reconcile, the masking test addresses the right pipeline, and the correcting set’s reported recovery balance is substantially improved. Nevertheless, B3 remains explicitly open because OYXOY is missing; B1 still has unexplained source-to-assembly differences; and B2 needs its results bound to the final files with unambiguous supervision counts. The dose comparison also contains a material error. These require completing and correcting the launch evidence, not redesigning the experiment. **Scope:** I reviewed the supplied documents and recalculated their figures. No sample rows, complete receipts, code or label dumps were available for inspection; local tool access failed. Consequently, **zero training rows were independently audited**, and I cannot supply row IDs or a newly measured content-error rate. Earlier reviews are reported history, not verification performed here.

**2. Findings, ranked by severity**

**F1 — BLOCKER: B3 is incomplete, and the decontamination rule is described inconsistently.**

Evidence:

- OYXOY NLI/WiC/WSD/metaphor is explicitly absent, although the native suite is part of evaluation.
- The launch sequence proceeds from certificate renewal to transfer without fetching OYXOY and repeating final-snapshot decontamination.
- Document 1 describes containment “of a user turn”; Document 2 §4 describes the fraction of an **evaluation prompt’s** distinct 8-grams contained in training text. Those denominators are not interchangeable.
- The descriptions alternate between `≥ 0.5` and `> 0.5`, and the final totals do not establish whether **any shared 13-gram** remains an active rejection rule.
- No supplied evidence demonstrates source-ID checks for GSM8K/MATH split membership or complete English-original coverage for the translated benchmarks.

**Fix:** fetch the frozen missing evaluation sets; freeze an inventory of dataset versions, splits, item counts and hashes; run the declared rule against the final mixture; then regenerate the receipt and output hashes. Record the normalization, containment denominator, thresholds, 13-gram rule and short-prompt handling. Produce a match ledger with training row ID, evaluation item ID, matched text and exclusion reason.

Also assess benchmark overlap against **arm B’s complete training history**, and freeze common clean evaluation subsets for the comparison. Do not modify completed arm B. The CPT-corpus audit remains a separate, nonblocking limitation, as previously agreed.

**F2 — BLOCKER: B1 passes aggregate arithmetic but not complete accounting or leakage verification.**

I independently reconciled all 20 table entries:

| Quantity | Recalculated total |
|---|---:|
| Unique train rows | 376,776 |
| Extra copies | 27,690 |
| Effective train rows | 404,466 |
| Dev rows | 3,852 |
| Contamination drops | 1,519 |
| Duplicate drops | 1,077 |
| Reported masked turns | 1,187 |
| Rounded rendered / supervised tokens | 228.6M / 140.2M |

However, the supplied source counts leave these gaps:

| Block | Reconciliation using disclosed dispositions | Unexplained |
|---|---|---:|
| Suite | 3,284 − 433 review removals − 9 duplicates − 2,813 train − 28 dev | **1 row** |
| Correcting | 600 − 565 train − 5 dev | **30 rows, 5.0%** |
| Personality | 1,388 + 192 − 1 contamination drop − 1,504 train − 69 dev | **6 rows** |

These could be legitimate length or validity exclusions. The documents do not identify them.

Furthermore, “train∩dev = 0” does not specify whether it compares IDs or content. **Suffixing colliding IDs cannot establish content disjointness.** Per-block deduplication alone also does not establish cross-block disjointness.

**Fix:** supply the full `data/arms/R3_single/receipt.json` and a row-level inclusion/exclusion ledger accounting for those differences. Record separately:

- Unique input, rejection reasons, dev allocation, unique train and replicated train.
- ID overlap, canonical conversation-content overlap and relevant shared-source families across train/dev.
- The exact 69 personality holdout IDs and content hashes, checked against every final block before and after replication.
- Full output hashes and exact token totals.

Historical puzzle duplication warrants notes on affected R2 dev losses, not retraining a completed run.

**F3 — BLOCKER pending verification: B2’s test scope is appropriate, but the final supervision contract remains ambiguous.**

The claimed test on **40 real rows through template, packing and collator**, with **20 decoded examples**, is a substantial improvement. I have no evidence that it failed. However:

- The named dump is `docs/receipts_label_dump_g2_pilot.json`; no supplied binding identifies the final R3 input hashes, trainer commit, template hash or package versions it tested.
- Correcting reports **226 masked plants** before assembly and **431 masked context turns** in a block replicated exactly ×2. **431 cannot be the effective training total of replicated masked turns** under that definition. It may count something else, including rejected targets; that definition is missing.
- Suite masking is **756**, exactly the source S4 count of `378 × 2` planted turns. That coincidence does not prove recomputation after review filtering, splitting and replication.
- Suite rows allegedly supervise only one target, and personality v4 supervises only the last assistant turn. Yet personality reports **zero masked context turns**, despite **110 multi-turn v4 rows**. The table may count only planted failures rather than all masked assistant context.

**Fix:** distinguish unique/effective counts and planted/ordinary/rejected assistant context. Validate each row’s intended supervised turns against its actual labels. Bind the dump to the final snapshot and training environment, explicitly demonstrating:

- Every masked assistant turn **and its end marker** has label −100.
- Intended targets and their stop token retain supervision.
- Packing and length handling preserve recovery context.
- Ordinary earlier assistant turns obey the documented last-turn-only policy.
- Every retained training example has positive supervised-token count.

The three identity-exempt blocks also need a **supervised-target audit**. `post_scan_identity_hits: 0` with those exemptions is not a zero-hit result for the whole mixture.

**F4 — HIGH: H2’s historical dose comparison is materially misleading.**

R2 stage 1 already trained `greek_ours` at ×2. Using the disclosed split, both R2 stage 1 and R3 have **19,800 × 2 = 39,600 effective rows**. Thus the table’s **“+98% tokens” does not demonstrate a doubled training dose**; it compares quantities with inconsistent weighting/accounting.

Personality exposure also changes substantially:

- Arm B: **1,319 × 4 × 2 = 10,552 row presentations**.
- R3: **1,504 × 4 × 1 = 6,016 presentations**, including new v4 rows.
- Each retained v3 row receives **four instead of eight presentations**.

The historical explanation that the entire **192.0M → 197.9M** difference is template overhead also needs reconciliation with splitting and replication.

**Fix:** compare R2 and R3 using the same post-split, post-weighting token definitions. Include both **R2 stage 1 alone** and **the complete stage-1-plus-arm-B path**. Describe personality ×4 as a reduced-exposure, changed-schedule experiment. I do **not** recommend automatically increasing it to ×8: repetition count alone would not recreate the previous optimization schedule.

**F5 — HIGH: H3’s accepted coverage and factual dispositions are not demonstrated.**

The promised accepted-row coverage matrix is absent. The current description still lists supplied-source QA, insufficient-evidence answers and memory updates as uncovered, without an explicit owner disposition.

Personality v4’s **192 rows** are described as **144 manner + 48 contract rows**. That does not demonstrate delivery of the seven registered factual corrections. The Sol sample produced **16 edits out of 48 rows, 33.3%**, and **two factual doubts, 4.2%**. These are reported intervention rates, not independently established error rates; the doubts nevertheless need dispositions.

**Fix:** attach the coverage matrix for the final accepted rows and record which gaps the owner explicitly defers. Resolve factual doubts in queued v4 targets through named evidence or exclude those unresolved targets. Identify any delivered factual corrections by row ID and source. Preserve completed v3 and its correction registry; do not describe that registry as completed remediation.

**F6 — HIGH: H4’s promotion plan is directionally correct but not yet operational.**

The proposed plan includes the missing arm B knowledge evaluations and IFEval rescoring, but:

- “Improvement” across conversation instruments has no frozen primary endpoint, minimum effect or adjudication rule.
- Native-suite retention, identity/capability behavior and XSTest safety/adequacy have no explicit promotion floors.
- The pivotal picky-user judge still lacks human calibration.
- All currently quoted IFEval scores use the environment with the known language-checker defect.
- Historical MultiChallenge counts vary across the document; the decision subset must be specified by item IDs.

**Fix:** freeze evaluation manifests, scorer versions, serving settings, primary endpoints, floors and uncertainty procedures before inspecting R3 results. Validate the language checker, then rescore arm B and relevant peers. Use paired comparisons, with dialogue-level clustering for conversation results, and blinded human adjudication of pivotal judgments.

Write GreekMMLU’s floor as **“at least arm B minus 0.5 percentage points”**; “within 0.5” unnecessarily suggests an upper bound. Preserve the declared IFEval and MGSM floors, but interpret small changes with their uncertainty. Completing the full battery can follow training; its executable plan and promotion rules should precede launch.

**F7 — MEDIUM: the narrative contains stale or overstated completion claims.**

Examples include suite review “pending,” sets still “planned,” new sets “not yet tokenised,” and the sentence **“Greek vantage … matters and its language does not”**, although §10 says that sentence was withdrawn.

**Fix:** update the description from the final receipts and dispositions. The adaptation result supports a bounded observation from that experiment, not the general causal claim.

**3. What is good and should not be changed**

- Keep the single-stage run as a controlled experiment against arm B; its value does not depend on identifying which individual change caused the result.
- Keep per-turn masking, guarded editing and post-edit re-verification.
- Keep exact deduplication, split-before-replication and the unchanged 69-row personality holdout for longitudinal comparison.
- Keep the correcting set’s shift toward genuine recovery. Reported counts improved to approximately **166 genuine versus 200 misquote recoveries**, or **1.20 misquotes per genuine recovery**, compared with the earlier 11:1 imbalance.
- Keep the **486-item primary MATH-500-el subset**, reporting the 14 flagged siblings separately.
- Keep MCQ augmentation deferred and preference optimization conditional on evaluation.
- Preserve completed datasets and runs; the required changes concern queued assembly, unresolved new targets and launch evidence.

The suite’s post-edit gate rejected **153/3,437 rows, 4.45%**: **56 empty targets, 1.63%**, and **97 constraint failures, 2.82%**. That is useful evidence that re-verification catches consequential editing damage.

**4. Answers to the specific questions**

**Q1 — Status against B1–B3 and H1–H4**

| Prior finding | Assessment |
|---|---|
| B1 accounting | **Partial:** table arithmetic passes; complete exclusion accounting and content-level split evidence remain missing. |
| B2 masking | **Substantially addressed on paper; not signed off:** supply the final-bound dump and resolve supervision-count definitions. |
| B3 decontamination | **Open:** OYXOY explicitly missing; rule, inventory and source-split evidence incomplete. |
| H1 recovery balance | **Provisionally satisfied at source-set level:** approximately 166:200 is credible progress; require exact counts after final assembly. |
| H2 recipe/dose/budget | **Partial:** weights and token totals disclosed; historical dose comparison and budget scope need correction. |
| H3 grounded usefulness | **Open:** final coverage matrix, explicit deferrals and factual-target dispositions missing. |
| H4 evaluation | **Partial:** useful battery outline; frozen operational scoring and promotion contract missing. |

**Q2 — What is surprising in the block table?**

Shares below use the rounded **140.2M supervised-token** total:

| Blocks | Supervised tokens | Share |
|---|---:|---:|
| Seven explicitly Greek-oriented blocks | 22.9M | **16.3%** |
| Five added blocks, including personality | 13.7M | **9.8%** |
| Greek IF | 6.0M | **4.3%** |
| English ifeval-like | 6.5M | **4.6%** |
| OpenMath / Greek math | 15.3M / 1.3M | **10.9% / 0.9%** |
| Suite + correcting | 5.4M | **3.9%** |
| Personality | 1.0M | **0.7%** |
| Nemotron A+B + tool use | 71.8M | **51.2%** |

Thus Greek IF and English ifeval-like are nearly balanced by supervised tokens despite different row counts. The three explicit IF blocks, including Precise IF, total **13.8M supervised tokens, 9.8%**, or **26.2M rendered tokens, 11.5%**—the statement “about a fifth of tokens” needs a different, explicit category definition.

**16.3% is a block-based proxy, not measured Greek-language share.** The remainder includes multilingual data, code and other content; it cannot all be called English. Measure language over supervised spans and report mixed/unknown separately.

The **1,348 ifeval-like drops account for 88.7% of all contamination exclusions**. They are 2.81% of that block’s disclosed retained-plus-contaminated dispositions, but the full input rejection rate cannot be established without the input ledger. Audit matches by evaluation source and inspect examples; neither accidental deletion of common instruction templates nor genuine benchmark leakage can be diagnosed from the count alone.

The duplicate total reconciles. The **69-row holdout** is valuable, but it does not supply held-out coverage of the newly added v4 behaviors.

**Q3 — Should weights or the single-stage plan change?**

My recommendation is to **retain the proposed weights provisionally**, after the blocking evidence is repaired.

- **Masking:** retain it; fix verification and accounting.
- **Greek IF ×1:** defensible given its near parity with English ifeval-like in supervised tokens.
- **Greek math ×1:** improvement is plausible, but reaching Krikri is not supported by these counts. Moving from 0.524 to 0.676 on 250 MGSM items requires **38 additional correct answers**. Do not shrink OpenMath merely because its row count is large; this review supplies no evidence that doing so would help.
- **Suite and correcting ×2:** their combined 3.9% supervised-token share is meaningful. The effective row count is **6,756**, not the stale approximately 8,500.
- **Personality ×4:** retain as provisional, explicitly accepting reduced exposure and testing identity retention. Do not describe it as the same dose as arm B.

A single run can establish whether the **combined recipe** improves on arm B. It cannot attribute effects separately to weighting, new data, masking or removal of staging.

**Q4 — What must happen between assembled and launched?**

1. Renew access and retrieve the missing frozen evaluation data.
2. Finish decontamination, exclusion reconciliation and queued factual dispositions; regenerate and freeze the mixture.
3. Bind receipt, configuration, trainer, tokenizer/template and environment versions; verify transferred file hashes.
4. Run the 5% dry run against that snapshot, checking rendered **and supervised** accounting.
5. Run the mandatory GPU probe with representative masked rows. Check finite loss/gradients, actual labels, distributed loss handling, memory, throughput and a save/reload path.
6. Freeze the battery and promotion contract; validate the corrected scorer environment.
7. Run preflight against an explicit cost cap, then launch only after all receipts pass.

The training estimate is **228.559561M / 32.5M ≈ 7.03 node-hours**. Adding the quoted **0.3-node-hour probe** and **4.3-node-hour battery** gives approximately **11.6–13.4 node-hours** across the stated central/conservative training range, before any evaluation work excluded from that battery estimate. A **7–9-node-hour total budget does not cover the disclosed plan**.

**Q5 — Residual risks, one line each**

- Personality behavior may weaken because retained v3 examples receive half as many presentations under a different schedule.
- Native Greek behavioral supervision remains a minority of the mixture; actual language shares are unmeasured.
- Nemotron’s previously unseen response tails remain a quality risk in a block carrying 44.7% of supervised tokens.
- Synthetic generators and judges can share errors; cross-vendor review does not replace independent ground truth.
- A single seed leaves small score differences difficult to distinguish from training variation.
- Completed personality v3 retains known factual concerns; new corrections do not automatically remove conflicting older supervision.
- Shared CPT contamination remains an unresolved limitation on benchmark interpretation.
- Textual function-call demonstrations remain unevaluated as native tool competence.

**5. Open questions for the owner**

1. Does the cap cover training alone, or also the probe, complete R3 battery and missing arm B evaluations?
2. What explains the **one suite, 30 correcting and six personality rows** absent from the disclosed accounting?
3. Does `train∩dev = 0` mean IDs, canonical content or source families—and what exactly does “masked context turns” count?
4. Which grounded-usefulness gaps are explicitly deferred, and what are the row-ID dispositions for the two v4 factual doubts and seven registered corrections?
5. What frozen conversation improvement threshold, safety/identity/retention floors and human-adjudication procedure will determine promotion?