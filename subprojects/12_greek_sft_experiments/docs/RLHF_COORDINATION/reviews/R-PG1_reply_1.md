# Reply to R-PG1 review cycle 1

1. Accepted. Forum `calculation` now maps to `math` (spec §5.1, decision 5); the registry mapping is changed in the same step and the relabel run (relabel_v1.jsonl) supplies a defined task_type and a maths content flag for every forum post.
2. Accepted. "Serious error" is defined in spec §4.8 with the annotator's threshold; maths claims are judged for seriousness by the specialist judge.
3. Accepted. Decision 8 now states the interim default: deterministic move selection from visible history and user state per dialogue v2 plan §4, realised mixture recorded, no targeted mixture.
4. Accepted. `generator version` is a closed list covering 0.1, 0.2-prototype, 0.2, 0.3, forum-gate-v3 and dialogue-quality-depth-v1 (spec §5.4); the registry already emits these values. The superseded inventory.py is not changed (it is marked superseded in the registry).
5. Accepted. Exclusive decision order for safety sub-kinds added to spec §5.3 and the glossary.
6. Accepted. Generic difficulty definitions are authoritative for generator 0.2 and later; the concrete realisation lives in the seed instance (task_kinds.json preconditions); design.json definitions apply only to archived 0.1 rows.
7. Accepted. Detail is content-defined with hard ceilings for bare and terse counting only the user's own words; pasted material excluded; packet tasks cannot be `short`. Spec §4.6 and glossary aligned.
8. Accepted. Glossary status of `anxious` aligned with decision 1.
