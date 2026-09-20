# Development-8 authoring preparation

Prepared at `2026-09-13T14:14:24.967174+00:00`. This package contains the eight frozen development decisions only: four outcomes for `cf05_cafe_order` and four for `cf09_library_hold`. No model calls were made and no run-state directory was created.

## Source-contract review

The package records three repair groups separately. All four coffee cases now identify an in-dialogue order draft in both visible context and decision wording, and their action contract permits only a text-record edit. The false coffee case also replaces its historically true clause with an explicitly false assertion about the current draft while keeping the second sentence as an authoritative new update. All four library cases now state that two copies are loaned and the third is reserved, so the three statuses form a supplied partition. The unresolved Friday claim is explicitly an inference from that displayed record rather than new user-provided return-date evidence.

The original development file is unchanged. `source_semantic_repairs.jsonl` binds every row-level delta, and the prior prepared package is preserved at `../development8_prelaunch_revisions/revision1`.

## Dispatch envelope

The primary envelope is eight authoring calls followed, only after full semantic review, by eight Greek language checks. Up to two observed semantic defects may use the existing semantic-repair contract, and up to two failed jobs may retry. That is 16 primary plus at most four conditional calls, or 20 additional calls. With 68 pilot calls already consumed, the maximum becomes 88 of the unchanged global cap of 118, leaving 30 calls of headroom.

`queue_author8.jsonl` is the first dispatch. `queue_author8_then_greek8.jsonl` reuses the accepted author envelopes and exposes the Greek jobs only through their dependencies. Schema acceptance is not a semantic quality verdict; all eight author outputs must be read before the second queue. Both stages retain high effort, at most eight workers, and the frozen generic runner.

If semantic repair is needed, the corresponding Greek job must be rebound to the accepted repair's `candidate_messages`; the current combined queue must not be used for that row because it deliberately points to the original author result. The reviewed queue variant and its new hashes must be frozen without resetting the 20-call package cap.

## Partition boundary

The accepted train32 package is referenced by receipt and is not copied here. Final-confirmation content was not read or materialized by this builder: its frozen gate still reports seven dispatchable rows, while the one silence case remains quarantined. The prior revision2 family-disjoint verification is inherited; this preparation does not reopen sealed final identities.
