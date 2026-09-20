# Development-8 authoring preparation

Prepared at `2026-09-13T14:12:13.107696+00:00`. This package contains the eight frozen development decisions only: four outcomes for `cf05_cafe_order` and four for `cf09_library_hold`. No model calls were made and no run-state directory was created.

## Semantic source review

Seven source decisions recompute cleanly from visible user evidence. `pilot48_05_false` needed one narrow candidate source repair before authoring. Its old wording, “Είχα πει κανονικό καφέ”, is historically true because the initial order was regular coffee; the false oracle concerns the current record after the later decaf update. The prepared wording explicitly asserts the current record and keeps the second sentence as an authoritative new update to regular coffee. The original development file is unchanged, and `source_semantic_repairs.jsonl` binds both versions.

## Dispatch envelope

The primary envelope is eight authoring calls followed, only after full semantic review, by eight Greek language checks. Up to two observed semantic defects may use the existing semantic-repair contract, and up to two failed jobs may retry. That is 16 primary plus at most four conditional calls, or 20 additional calls. With 68 pilot calls already consumed, the maximum becomes 88 of the unchanged global cap of 118, leaving 30 calls of headroom.

`queue_author8.jsonl` is the first dispatch. `queue_author8_then_greek8.jsonl` reuses the accepted author envelopes and exposes the Greek jobs only through their dependencies. Schema acceptance is not a semantic quality verdict; all eight author outputs must be read before the second queue. Both stages retain high effort, at most eight workers, and the frozen generic runner.

If semantic repair is needed, the corresponding Greek job must be rebound to the accepted repair's `candidate_messages`; the current combined queue must not be used for that row because it deliberately points to the original author result. The reviewed queue variant and its new hashes must be frozen without resetting the 20-call package cap.

## Partition boundary

The accepted train32 package is referenced by receipt and is not copied here. Final-confirmation content was not read or materialized by this builder: its frozen gate still reports seven dispatchable rows, while the one silence case remains quarantined. The prior revision2 family-disjoint verification is inherited; this preparation does not reopen sealed final identities.
