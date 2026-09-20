# Active audit programme and Sol parallelism

13 September 2026. The owner instructed us to fold the adaptation/correction prompts into the plan and start work. Initial audit agents and maths batch calls have started. This document governs the audit order; completed data and historical results remain immutable.

## Audit order and method

Audit the actual files consumed by assembly, plus explicitly identified candidate data. A polished intermediate export is not automatically the training artifact. Record source hashes, sample IDs, selection seed, denominator, generation/editor prompt lineage, and whether a finding survives into the assembled data.

| Priority and source | Whole-file checks | Semantic review and resulting action |
|---|---|---|
| First: unfinished worked-maths candidates | IDs, missing outputs, duplicate problem/solution versions, join provenance, source/difficulty coverage, complete target structure | Frozen 300-row audit: 150 GSM, 100 Level-5 with stable problem text, 50 Level-5 with multiple saved problem versions. Check derivation, final answer, units, premises, completeness, Greek and cultural adaptation separately. Adjudicate findings before any promotion. |
| First: trained Greek maths | Final manifest, verification coverage, final-unit/part handling, source exclusion and length | Next audit: 120 rows stratified by translated GSM, translated MATH levels 1–4, native grade/topic and verification status; keep known failures in a separate targeted set. Compare pre/post Greek correction. Correct content defects before the language pass. |
| First: correcting dialogues and conversation suite | Exact final-export identity, role/turn counts, category-count units, masks, empty turns, quote/state preservation | 24 full dialogues in the initial Sol audit, with stratified and targeted observations reported separately. Reconcile raw category occurrences versus actual turns. Check truth categories and evidence, useful continuation, revision state and speaker ownership. |
| First: Greek IF and IFBench words checker | Run actual checkers, including Greek positive/negative controls, exact-string and contradiction checks; distinguish training checker from benchmark checker | Initial words-family audit plus 20-row Greek IF review where feasible. Repair checker semantics before using its failures to design data. Recheck candidate targets after language correction. |
| First inventory: large imported blocks | Exact final paths/weights, full-record role/schema validity, language, truncation, duplicate exposure, source identity | Initial 24-row review across Nemotron chat, Dolci chat/think, tools, foreign-language and personality risk areas. Subsequent 120-row sample proportional to supervised-token exposure, with minimum coverage per retained source/language and separate risk oversampling. Do not infer whole-source harm from a few defects. |
| Next: original adapted core and paired languages | Confirm compiled adaptation prompt and editor versions against actual receipts; paired IDs and cultural moves; code/constraint preservation | 60 rows stratified over no_robots and the six original added sources, plus 60 paired foreign-language rows. Audit preservation of the source's teaching and any unwanted adaptation/editor drift. Reuse historical human review; do not restart a complete corpus review. |
| Next: personality and identity | Compare every capability/identity statement with the current deployment fact sheet; identify repeated targets and contradictory facts | Review every distinct factual claim; 24 varied dialogue examples for naturalness, instruction compatibility and gratuitous repetition. No blanket deletion of useful first-person content. |
| New knowledge/MC and non-maths reasoning pilots | Family decontamination, source provenance, unique MC keys, answer-position counts, executable reasoning/constraint checks | Review every row in the small pilot before scale. Validate new Greek facts after cultural substitution. Train on separate families from benchmark questions. |
| New safe-request adequacy examples | Independent scenario families, no copied XSTest items, valid target/mask structure | Review the complete pilot for substantive helpfulness and appropriate boundaries. Separate mistaken refusal from unsafe compliance. |

The unfinished ordinary solution file contains 3,718 GSM records and **no MATH levels 1–4 solutions**. Level-5 has 3,010 solution records for 1,168 IDs and 2,146 problem records for 1,457 IDs. Of the solved IDs, 356 have multiple Greek problem texts. These are direct inventory findings, not mathematical-error counts. Last-record joins are used only to define the audit candidate; ambiguous historical pairing remains flagged.

## What correction means during these audits

Use the [prompt pack](../prompts/README.md). Audit semantic validity and adaptation first; propose a semantic repair only where the defect and permitted scope are established. Greek correction then repairs genuine language errors while preserving the settled adaptation and task. Run domain checks again after editing. No generic personality brief is appended to the correction prompt.

The 300-row maths audit is an error report, not a success filter. Keep all sampled cases, including uncertainties and provenance problems. Report rates by stratum; a pooled estimate requires population weights. Model judgments remain provisional until evidence-based adjudication. Do not extend rates from successful partial outputs to missing generations or to the trained corpus.

## Parallelism and ETA policy

- Start with three Sol/high audit agents and four Sol/high maths workers: at most seven simultaneous Sol calls in this task. Agents do not spawn additional model calls. This overlaps checker/inventory work with semantic review.
- The first four maths batches are a throughput and output-validation probe. Each has at most three complete problems, with an input-size bound. The frozen 300-row audit contains 100 batches.
- After successful probe output and a fresh quota/process check, use up to eight maths workers while the audit agents remain active (eleven Sol calls total). When agent audits finish, increase to twelve maths workers if errors, memory and quota remain healthy. Sixteen is a later ceiling requiring another measurement, not the launch default. The inherited hard limit of 100 is never a target.
- One shared task concurrency count includes audit agents, generation, correction and judging. Use one active batch queue at a time initially. Do not launch another detached worker pool after an interrupted command until exact process IDs and the run lock are checked.
- The maths wave has a hard ceiling of **180 calls including retries**, two attempts maximum per batch. Its 100 primary calls leave bounded room for transport failures and adjudication, not hidden bulk generation. The three agent audits are counted separately. Subsequent packets retain their stated ceilings; the 1,080-call menu is not dispatched at once.
- Quota/rate failures stop new dispatch. Completed outputs and individual attempts are retained. IDs must match exactly; missing or malformed outputs do not count as reviewed. Record elapsed time, usage and failures per call.
- Estimate remaining time as pending calls × observed mean duration ÷ sustainable workers, with a separate tail/retry allowance. For planning, 30–120 seconds per three-row call gives about 6–25 minutes for 100 calls at eight workers, before adjudication; this range is an assumption until replaced by actual timings. Long hard-maths calls can dominate the finish even when the mean is low.

Initial live Codex reading: 31% used / 69% remaining in the weekly core window; the short window was not reported. Recheck during ramp-up and after this wave. Reasoning effort is high for semantic maths review; testing medium/high/xhigh output quality remains a separate controlled experiment rather than silently mixing settings in this audit.

## Overlap with CSCS

The fresh whole-account `a0140` queue check returned no running or pending jobs. These audits consume **zero CSCS node-hours**. Current cluster limits are being refreshed through the canonical CSCS probe while audits run. Prepare frozen measurement inputs and reuse existing generations concurrently; allocate GPUs only when those inputs and the measurement protocol are ready.

The owner has authorized starting the programme within the existing budget. Keep the cumulative SFT cap at CHF 230. The first measurement and two screening comparisons have a proposed combined ceiling of 14 node-hours / CHF 37.66 at the planning rate, within the previous estimated headroom. Reconcile live accounting before each allocation. The larger combined main/finish programme still exceeds that headroom and must be repriced within the cap or receive an explicit cap change; starting audits does not change the cap.

Next dependency: first audit findings → prompt/checker repairs and small validated data variants → the competition-coverage comparison. Correcting and dialogue preparation can continue while that CSCS comparison runs. No GPU allocation is held idle for Sol to finish a dataset.

## Where to follow execution

- [Execution log](EXECUTION_LOG.md)
- [Frozen maths audit manifest](maths/manifest.json)
- [Maths progress](maths/progress.json)

Agent reports will land under `dialogue/`, `instruction_following/` and `imports/` in this execution directory. Their filenames are linked into the consolidated status when complete.

## First-wave measured result

The frozen 300-row maths audit completed in 100 primary calls, with zero retries and no schema failures. It took 11.3 minutes including the probe and ramp; the eight-worker continuation took 7.6 minutes. Three Sol agents handled other audits and repairs concurrently. The 19-row targeted maths adjudication and 12-dialogue pilot review/semantic repair are also complete. Remaining work is listed in [STATUS.md](STATUS.md). The optional twelve-worker ramp was not needed for this wave.
