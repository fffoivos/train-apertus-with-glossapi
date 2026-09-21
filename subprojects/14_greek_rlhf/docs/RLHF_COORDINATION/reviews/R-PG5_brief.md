# Review brief R-PG5 — the full round-3 prompt set and the owner review page

## Stage goal
The complete set of new prompts for round 3, generated to the agreed joint distribution, with labels that describe what the prompts actually are, and
a page on which the owner can inspect every prompt with its replies and judgements. This is the prompt-generation half of the final product.

## Scope
- Runs: `data/rlhf/generator_v02/runs/R3-validation-50`, `R3-main`, `R3-fix` (verification regenerations), `R3-held` (retries of held slots). Each run directory holds `generate.snapshot.py`, the exact code it executed, plus instances, renderings, reviews, prompts and a receipt.
- Manifest v2 `manifest_round3.json` (444 generated slots + 39 forum maths selections), registry `data/rlhf/registry/registry.sqlite` and `registry_report.json`.
- Independent verification: `data/rlhf/generator_v02/verify.py` and `verification.jsonl` (labels observed per prompt, maths-content detection, fidelity).
- Round-3 assembly: `data/rlhf/round3/stage.py`, `round3_all.jsonl`.
- Terms: spec and glossary v1.0.3.

## What changed since R-PG4
Labels are now verified rather than assigned: an independent pass read every accepted message and reported the labels it realises; assigned values are
kept as `labels_assigned`. Prompts whose message drifted from its task instance were superseded and regenerated. Detail was clarified in v1.0.3 (pasted
material never raises the detail level). `maths_content` is detected for every purpose, routing embedded maths to the specialist judge.

## Acceptance criteria
Blocking:
1. Every active prompt traces to a slot in the manifest, a reserved instance, a passing review and a run receipt; superseded prompts are excluded from the active set and from the registry's keepable rows.
2. The realised set matches the agreed distribution within stated tolerance, or the deviation is reported with its reason (purpose, language, and the within-seeded axes).
3. Labels in the exported rows describe the prompts as written; where verification changed a label, both values are present.
4. No duplicate scenario across the whole set; no prompt contains framing, meta text or private fields.
5. Maths routing is correct and complete: purpose maths and embedded maths both reach the specialist judge; nothing marked maths is judged only by the general rubric.
Major:
6. The held slots are genuinely defective, and the held rate is reported honestly per cell.
7. The review page shows, per prompt: the seed and story, the labels, the message, every judged reply with its verdict and reasons, the chosen and rejected reply of the pair, and the maths reference where one exists.

## Notes for the reviewer
The owner's final product is this page plus the evaluated replies. Judge whether an owner could, from the page alone, see what was collected, what was
judged, and what was thrown away. Report what is wrong with the data, not only with the code.
