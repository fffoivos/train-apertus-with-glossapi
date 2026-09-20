# Final pilot review — pilot100_v2
Status: bounded single-turn demonstration accepted, not production/training promotion.

Initial audit: PILOT_INDEPENDENT_AUDIT.md. Its findings describe the pre-repair snapshot and remain preserved.
Final model-call reviews: runtime/runs/pilot100_v2/curator.jsonl.
Archived accepted versions: revision_history.jsonl.

| Row | Finding | Final disposition |
|---|---|---|
| S0050 | Irrelevant JSON translation branch | Removed; Greek-to-English request now only preserves actual-source constraints; separate review passed. |
| S0043 | Formal register used singular imperatives | Polite plural Greek; separate review passed. |
| S0047 | “an shared” in source | Source corrected, archived prior row, new wrapper reviewed. |
| S0068 | Phone call called a message | Source consistently a call; request required another repair for informal register; final review passed. |
| S0028 | Greek element name grammar; authoring guidance echoed | Quoted canonical element name and atomic-number-only requirement; review passed. |
| S0056 | Indirect harmful request wrapper | Direct first-person guidance request, no methods added; review passed. |
| S0067 | Asked assistant to access account directly | Guidance request rather than direct execution; review passed. |
| S0087 | Both IF conditional examples selected open branch | Replaced source with full-event instance; re-reviewed. Pilot now includes open and full; future planner alternates. |

S0039 and S0044 also received automatic attitude/register repairs during the initial run.
All65 final source attachments match frozen manifests; private reference fields are excluded from the wording/model-input packets.
The five math rows have deterministic checks and were independently inspected; this does not validate all mathematical problem classes.
Final benchmark scan found no lexical hits across14 caches. Exact identity and source-family split checks are enforced transactionally.

Accepted reservations:
- S0010 French editing includes translation from English. Treat as cross-language editing.
- S0021/S0028 use a wrapper plus a standalone factual question; slightly artificial.
- S0024/S0034 have identical request wrappers over distinct source instances: exact full messages differ, wording diversity is limited.
- Grounded factual requests often expose the remaining-place count in the source; they test source use more than new reasoning.
- Initial audit counted31/65 notice-like sources; the final source corrections do not broaden that domain.
- Observed labels are reviewer judgements, not human-calibrated measurements.
- 65 single turns do not demonstrate35 dialogue trajectories or the full language-by-purpose cross-product.

Validation:34 regression tests passed and9 final loopback HTTP checks passed. Runtime state is single_turn_ready with no active worker. Calls complete36, failed0, reserved0. The pilot remains development-only and training_eligible=false.
