# Stage 1 Phase C: frozen train-only maths queue

Prepared at 2026-09-13T17:34:46+03:00. The queue is ready for root review and has not been launched. No model call, GPU allocation, CSCS job, production transform, or source mutation occurred.

## Selection

The 14 `C_complete_stage1` train identities were read from the frozen 133-family split manifest. Source lines 63 and 2670 were replaced because their problem text depends on a diagram. `replacement_delta.jsonl` records the deterministic `phaseC-replacement-v1` selection:

- Algebra Level 4: line 63 -> text-only line 627.
- Geometry Level 1: line 2670 -> text-only line 2758.

Each replacement is from the same subject and level. The candidate pool excluded all 133 reserved families, all four Phase B replacement families, current Greek gradient-train and development families, assembly exclusions, prior pilot families, cut2 candidates, frozen MATH-500 gate failures, metadata conflicts, and diagram-dependent problem text. `repair_math5_77` resolves to `mathfam_f91a56318d28452a3d95` and remains quarantined by the frozen 13-gram gate; it was explicitly excluded and was not reselected.

The other 12 Phase C identities remain exactly as proposed. Development and final-confirmation identity sets are unchanged, and no development or final-confirmation source content appears in this bundle.

## Source read

All 14 selected English tasks and complete reference solutions were read for obvious ambiguity and internal inconsistency. Each is self-contained in its problem text and accepted for adaptation. `source_read_receipt.jsonl` records the task and reference hashes plus a concise mathematical check for every row. This is a source suitability read, not approval of any future generated Greek problem or solution.

## Queue and cap

The primary queue has 42 high-effort jobs: 14 adaptations, 14 blind solves, and 14 independent blind verifications. Solve and verification share only the accepted adaptation dependency and cannot see each other or the frozen reference solution. There is no automatic xhigh selection.

The absolute cap is 72 calls: 42 primary, at most 14 Greek corrections, a shared maximum of 8 semantic/source-repair or observed-unresolved escalation calls, and at most 8 retries. Conditional work must use the same cumulative ledger, so a new state directory cannot reset the cap. Maximum concurrency remains eight workers.

The runner, prompts, and schemas are byte-identical copies of the proven Stage 1 assets. `manifest.json`, `payload_bindings.jsonl`, and `verification.json` bind and check the exact queue.
