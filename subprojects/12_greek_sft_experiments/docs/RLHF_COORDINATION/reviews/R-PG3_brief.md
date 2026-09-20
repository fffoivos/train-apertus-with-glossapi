# Review brief R-PG3 — generator 0.2 release and the 500-slot dry-run manifest

## Stage goal
A generator and a quota manifest that realise the agreed joint distribution for about 500 new slots, send the frozen definitions with every
label, keep each seed's concrete substance, and cannot reproduce the defects of generator 0.1 or of the round-2 prototype. Final product of the
phase: the new prompts with their replies sampled and evaluated, on a review page.

## Scope since R-PG2
- `data/rlhf/generator_v02/`: `build_axes.py` + `axes/*.json` (frozen pools: people per language, 130 situations, 290 topics); `task_kinds.json`
  (subtypes with required preconditions, packet flag); `manifest.py` → `manifest_round3.json`; `generate.py` (instances → atomic reservation →
  rendering with glossary definitions → code checks → independent Sol review → at most two repairs → registry); `fake_sol.py`; `test_generator.py`.
- Manifest: planning size 500 pairs (provisional checkpoint, not a training size), 377 generated single-turn slots, 20 forum selections (math/el, from
  unused gate-accepted posts), 103 dialogue starting seeds reserved (not generated).

## Context to read
- `docs/RLHF_COORDINATION/PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md` §3–§6; two-stream plan §0.1 (PG3d, PG4) and §4a.
- Spec v1.0.1 §4 (labels), §4.5 T5 (maths), §5.3 (safety order), §5.5–§5.7; glossary `data/rlhf/prompts/seed_label_definitions_v1.md`.
- Defects the release must not repeat: spec §3.1–§3.2 (0.1 and round-2 prototype audits) and the board message `20260916T155641Z_fable_generator_02_requirements.md`.
- `data/rlhf/registry/registry_report.json` (frontier inputs to the manifest).

## Acceptance criteria
Blocking:
1. Manifest: slots total exactly the budget; per-cell totals follow the frontier's conservative needs; category counts do not depend on subtype counts; no Greeklish outside Greek; no packet subtype with detail `short`.
2. Identical substantive instances are caught across slot IDs and personas (instance key), and reservations are atomic across workers.
3. Every label sent to Sol carries its glossary definition; no private field (answer_conditions) reaches the rendering or the final message.
4. Seed-to-message checks catch changed or missing values, missing packets, wrong language or script, detail ceilings (own words only), framing or meta text, near-duplicates; the independent reviewer checks task fidelity with fixed reason codes; repairs are bounded to two and never change the instance.
5. Maths follows spec T5 (deliverable chosen per request, ambiguity recorded, no forced worked solution); the five foreign languages are present.
Major:
6. Subtype preconditions in `task_kinds.json` are concrete enough to produce distinct task instances (ingestion plan §3).
7. Receipts bind code, glossary, manifest, task kinds and axes by hash.

## Evidence
- `R-PG3_tests.txt` (offline tests), `R-PG3_fake_run_receipt.json` and `R-PG3_fake_renderings_sample.jsonl` (fake-Sol dry run against an isolated registry copy).
- The first real validation run (`data/rlhf/generator_v02/runs/R3-validation-50/`) is starting in parallel; it is R-PG4's scope.

## Known limitations
- Near-duplicate screening is word-set overlap only (nominations, not proof); semantic duplicates are left to the reviewer.
- Pasted-packet presence is checked on the first 60 characters of the packet.

## Out of scope
The first 50 slots' quality (R-PG4); reply sampling and judging.
