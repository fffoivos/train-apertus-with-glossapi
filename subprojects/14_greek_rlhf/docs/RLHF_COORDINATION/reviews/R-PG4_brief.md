# Review brief R-PG4 — the first 50 generated slots

## Stage goal
Before generating the remaining slots, establish that the generator's output is what the plan asks for: real requests a real person could send, faithful to the task instance, realising the frozen labels, varied in scenario, and with every defect of generator 0.1 and of the round-2 prototype absent. Final product of the phase: all new prompts with their replies sampled and evaluated on a review page.

## What happened since R-PG3
The first validation run (50 slots, manifest v1) was abandoned after inspection, not repaired: instances were built without the slot's detail level, so bare and terse slots received rich instances (30 of 50 failed detail), and the renderer marked the whole message as pasted material on non-packet slots, which emptied the language check (36 of 50). Evidence and released reservations: `data/rlhf/generator_v02/runs_abandoned/R3-validation-50/`.

Changes then made (replies `reviews/R-PG2_reply_1.md`, `R-PG3_reply_1.md`):
- Registry: yield counted from eligible pairs only; maths yield from the specialist-judge calibration; exact two-way rounding of the joint targets (N=500: el 350, en 100, fr/de/es/it/pt 10 each); maths-content forum posts kept available.
- Manifest v2 (`manifest_round3.json`): 444 generated slots + all 39 available forum maths posts; multi-constraint writing may not be bare.
- Generator: instances are sized to the detail level; `scenario` tag per instance with a run-wide similarity screen (catches the cross-language duplicates seen before); packets only for packet subtypes and never containing the request; pasted material ignored on non-packet slots; same-round duplicate screen; instance key covers packet, constraint parameters, check values, ambiguity and answer conditions; safety decision order sent with every safety call; `maths_content` (none | embedded | maths) required for every purpose; two repairs maximum.
- Terms: spec and glossary v1.0.2 (`R-PG1_reply_2.md`, term manifest `R-PG1_term_manifest_v1.0.2.md`).

## Scope to review
`data/rlhf/generator_v02/runs/R3-validation-50/` (instances, renderings, reviews, prompts, receipt) against `generate.py`, `manifest_round3.json`, spec v1.0.2 and glossary v1.0.2. Run receipt: 41 active, 9 held, repairs 34/6/1, 63 Sol calls.

## Acceptance criteria
Blocking:
1. Each accepted message realises its slot's labels (language, register, attitude, detail) and carries the instance faithfully: no changed or missing value, no dropped constraint, no added fact that changes the correct answer.
2. No framing, meta text, label names, placeholders or private fields (`answer_conditions`) in any message.
3. Detail ceilings hold for bare and terse counting only the person's own words; packets appear only where the subtype needs them.
4. No two accepted prompts describe the same scenario, across subtypes and languages.
5. Maths slots follow spec T5; `maths_content` marks embedded maths in non-maths prompts correctly.
Major:
6. Held slots are held for real defects, and the held reasons are accurate.
7. Receipts bind code, glossary, manifest, task kinds; reservations match the accepted instances.
8. The accepted set is fit for sampling: a Greek assistant could be judged fairly on these requests.

## Notes for the reviewer
Report what is wrong with the output, not only with the code. If a criterion passes, say so plainly. The remaining slots are already generating with this same code: findings will be applied to the output (regeneration of affected slots), so identify defects precisely enough to select the affected slot IDs.
