# Competition-maths stage-one preparation

Prepared locally at `2026-09-13T17:04:09+03:00`. No model subprocess, queue dispatch, production write, GPU allocation, or CSCS job was run.

## Phase A: seven historical Greek Level-5 pairs

Every selected pair was matched to its exact MATH source line and reference solution. All saved Greek problem and solution records were inspected; the full source, full reference, every historical record, line number, record hash, and chosen full text are stored in `phaseA_bound_pairs.jsonl`. Selection never relies on the last record for an ID.

| ID | Subject | Disposition | Finding |
|---|---|---|---|
| math5_173 | Algebra | keep | Complete factor-pair proof; minimum is 205. |
| math5_528 | Intermediate Algebra | repair | Mathematics and 517 are correct; change the single typo `Πολλασιάζοντας` to `Πολλαπλασιάζοντας`. |
| math5_534 | Prealgebra | keep | Complete double-counting proof; 96 handshakes. |
| math5_492 | Geometry | keep | Auxiliary construction, cosine law, and 150 are correct. |
| math5_488 | Number Theory | keep | Valuation lower bound and candidate verification are correct; executable search confirms first pair `(286,121)` at sum 407. |
| math5_473 | Counting & Probability | keep | Ordered substitution recurrence and remainder 122 are correct. |
| math5_138 | Precalculus | keep | Candidate correctly uses `x=1/√3`; the English reference's isolated `x=1/3` equality is a typo contradicted by its own next expression. |

The result is six unchanged keeps and one language-only repair. There are no regenerate or hold decisions. `phaseA_candidate_rows.jsonl` contains the seven review candidates without modifying historical files.

## Phase B: frozen train-only 14-row queue

The earlier proposal contained four problems with an Asymptote or explicit figure dependency. The current pilot's source gate rejects these. `phaseB_selection_delta.jsonl` records four deterministic same-subject, same-level train-only replacements. Development and final-confirmation identities remain unchanged. No final-confirmation problem or solution content was read into or materialized in this bundle.

The primary queue contains exactly:

- 14 high-effort Greek adaptations;
- 14 high-effort blind solves;
- 14 independent high-effort blind verifications.

The solve and verification jobs depend only on the accepted Greek adaptation and do not see each other. Reference solutions are frozen in `inputs.jsonl` for post-solve human comparison but occur in no queued payload. There is no automatic xhigh lane.

The absolute envelope is **72 calls**: 42 primary, at most 14 Greek corrections, a shared maximum of 8 source-review/semantic-repair/observed-case escalation calls, and at most 8 retries. An xhigh solve can be instantiated only for a human-observed unresolved case inside that shared eight-call pool. Conditional jobs require a separate reviewed queue and retain the same cumulative cap.

The copied generic runner is byte-identical to the verified maths-pilot runner, SHA-256 `c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005`. It defaults to plan mode, permits at most eight workers, and requires the explicit execution flag plus its reviewed-payload acknowledgement. Root will review and dispatch after the current Greek dialogue queue; this preparation does not launch it.

## Files

- `phaseA_bound_pairs.jsonl`: complete, explicit source/attempt/selection bindings.
- `phaseA_adjudications.jsonl`: seven full semantic and Greek verdicts.
- `phaseA_candidate_rows.jsonl`: six unchanged candidates and one proposed typo repair.
- `inputs.jsonl`, `queue.jsonl`, `payload_bindings.jsonl`: frozen phase-B inputs and 42 primary jobs.
- `conditional_jobs.json`: shared conditional and retry caps.
- `partition_receipt.json`: preserved development/final identity digests and sealing assertion.
- `manifest.json`: source and artifact hashes.
- `verify_stage1.py`, `verification.json`: executable lineage, queue, mask, and mathematical checks.
