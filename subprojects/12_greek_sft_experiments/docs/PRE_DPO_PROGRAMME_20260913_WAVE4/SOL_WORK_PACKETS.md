# Parallel Sol work packets

13 September 2026 · Dispatch specifications; the owner has now directed execution. Initial audit launches are recorded in the [execution log](execution/EXECUTION_LOG.md); other packets remain queued behind their dependencies.

## Shared contract

Before drafting or repairing adaptation prompts, read the [no_robots adaptation reference](ADAPTATION_REFERENCE.md) and its saved production prompt. Preserve the source's teaching objective while making the cultural adaptation; Greek polishing protects the result. Specify mathematical, factual and dialogue invariants per source. A benchmark's measurement contract is separate. These reference documents do not authorize generation.

Use the [task prompt pack and composition table](prompts/README.md) for the initial pilots. Do not append the modified personality brief to its correction prompt. The domain prompt supplies the single output contract; strict schemas, source-derived invariant lists and guards must be bound during driver integration. Preserve the existing package call ceilings. These are written prompts awaiting pilot validation, not evidence that a job ran.

Every packet receives immutable source IDs and a separate output directory. It returns proposed changes, reasons, evidence and validation results; it never edits completed training data or result files in place. Stable row IDs bind originals to patches and reviews. Each input belongs to one worker at a time. Retries are bounded and charged to the same package.

Use the [active concurrency ramp and audit order](execution/AUDIT_AND_PARALLELISM.md): seven initial Sol calls across agents and maths workers, then eight maths workers alongside agents, and twelve after agents finish if quota and errors permit. Reserve reviewer contexts for validation, not continuation of the editor's conversation. Numeric, state and schema checks remain external to Sol. Measure throughput before asserting an ETA.

The initial allowances below total **1,080 calls across distinct packages**, not one automatically permitted batch. Start only the highest-value packages within the available quota; refresh quota first. Each dispatch is bounded at 200 calls or less under the retained handoff limit, and cumulative package totals remain visible. Multi-row calls require explicit context-size checks. Subsequent generation, polish, review and retries need their own ceilings; do not hide thousands of calls behind “scale”. This document is not launch approval.

| Packet | Can start after | First bounded output | Initial call ceiling | Acceptance gate |
|---|---|---|---:|---|
| Maths audit | Existing candidate rows and source answers selected | Audit 300 rows, stratified across source/difficulty; separate correctness, premise, units, translation and length findings | 180, batching where context permits | Retain denominators and all findings; independently verify flagged maths; this is an audit, not a filter of convenient successes |
| Competition-source pilot | Source revision and exclusion families frozen | Review up to 200 original-MATH examples and propose a balanced token manifest | 120 | Source problem IDs, reference-backed answers, bounded duplicates, no benchmark lineage, complete solutions within length budget |
| Correction taxonomy and pilot | Exact existing records available | Reconcile decisions vs turns vs dialogues; author 120 verified decisions, 40 false/40 true/20 partly/20 unresolved, for later growth to 600 | 200 | Correct speaker ownership, verified truth labels, varied tone, useful continuation, no automatic agreement/disagreement shortcut |
| Dialogue state pilot | Scenario family split frozen | 20 training examples per lane: edits, inference memory, premises, stopping; 80 total, distinct from evaluation cases | 200 | Exact expected edit/state results; protected spans; sufficient vs insufficient evidence; well-defined stop semantics |
| IF and imported target repair | Full rendered flagged rows supplied | Repair a bounded sample of known contradictions/schema defects; report impacts by block and language | 100 | All deterministic checks pass after polish; distinguish excerpt clipping from real record corruption |
| Knowledge pilot | Training source families excluded from evaluation families | 30 sourced fact families in three answer formats; 90 training examples, plus a subject/format plan | 120 | Source supports answer and explanation; aliases/distractors valid; balanced answer positions; no benchmark rephrases |
| Independent audit / rating rubric | Patches or saved outputs exist | Blind review of pivotal defects, 40–60 preference examples and disagreement register | 160 | Evidence-backed adjudication; both-wrong pairs rejected; lengths and styles not used as truth proxies |

The 600-decision correction target and larger dataset builds require a new counted scope after pilot review. The 120 pilot examples are training candidates, not the held-out correction evaluation panel. Similarly, the knowledge packet's training families must be disjoint from the evaluation fact families.

## Required outputs per packet

1. `manifest.json`: source hashes/revisions, family IDs, split, language, row counts, input and supervised-token counts, and intended downstream experiment.
2. `findings.jsonl`: original ID, defect, severity, evidence, proposed disposition and whether the evidence was independently checked.
3. `candidate_rows.jsonl`: only proposed new/changed records, preserving provenance; untouched originals remain accessible.
4. `validation.json`: deterministic checks, reviewed sample IDs, known unresolved defects, exclusions and retry counts.
5. `review.md`: what changed, what remains uncertain, and whether the package is ready for scale, needs revision or should be deferred.

Greek polishing occurs after semantic repair. Protect equations, negation, named entities, exact strings and document spans, then rerun the relevant checks. A fluent rewrite cannot overrule a failed semantic check. For training dialogue histories, specify exactly which assistant turns receive loss and mask erroneous context where it should not be taught.

## Coordinator and CSCS responsibilities

The coordinator freezes the benchmark protocol and family splits first, maintains the adopted experiment registry, and records costs and dependencies. Mathematical/state oracles, tokenization, duplicate detection and checks are code tasks; Sol assists with semantic and language review. Bulk work uses the existing data host or appropriately budgeted remote CPU resources, not the Mac or cluster login nodes.

The CSCS operator stages validated artifacts, reuses the canonical runner and compatible readiness evidence, and submits only the explicitly scoped experiment. Work already running consumes a fixed input snapshot; later Sol corrections become a new version, never an in-place modification to that job's training file.

Before reusing historical drivers, fix the inspected over-concurrent maths launch and score-file deletion behaviour. Use a global concurrency lock and append/version score outputs. Check exact detached process IDs after interruptions before restarting. Do not run old scripts unchanged because their filenames look reusable.

## Handoffs that allow actual overlap

| CSCS activity | Useful parallel work | What must wait |
|---|---|---|
| Missing baseline generations | Correct existing maths/IF targets; reconcile correction labels; compute old-score aggregates | Judging those new outputs |
| Competition-maths screening | Build correction and state pilots; prepare knowledge sources | Selecting the winning maths recipe |
| Correction screening | Complete independent reviews; freeze accepted imports and retention slices | Choosing whether correcting enters the final mix |
| Main SFT training | Prepare DPO prompt families and rating rubric; judge already completed outputs | Preferences requiring the final SFT checkpoint's responses |
| Selected-model confirmation | Human review of sampled dialogue; pilot preference-pair validation | DPO training until SFT and preference gates pass |
| DPO generation/training | Offline pair review and final-report preparation | Judging a response that has not yet been generated |

The model editor, simulated user and score judge can share the Sol model but must have separate contexts and roles. Use external truth/state checks and a small human audit for calibration; agreement between two Sol calls alone is not independent evidence.
