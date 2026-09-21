# Review brief R-PG1 — terms frozen

## Stage goal
One vocabulary for every label and term that the plans and the code use, frozen as spec v1.0 and prompt-ready glossary v1.0, so that
generator 0.2 corrections, the import registry, dialogue work and RLHF judging all use the same definitions. The programme's final
product for this phase: about 500 new prompts generated to the agreed distribution, with their replies sampled and evaluated, shown on a
review page.

## Scope since the previous checkpoint (none before this one)
- `docs/SEED_LABEL_SPEC_20260917.md` v1.0: audit of four pipelines (§3); definitions (§4–§5); rules for prompts (§6); eleven decisions
  resolved by recorded orchestrator defaults at the owner's go (§7); owner's maths definition (§4.5 T5); identity and planning terms (§5.7).
- `data/rlhf/prompts/seed_label_definitions_v1.md` v1.0: the prompt-ready subset (no dataset, distribution or judging terms).

## Context to read
- Spec and glossary above.
- Plans: `docs/RLHF_COORDINATION/RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md` (§0, §0.1, §3, §4a, §10), `DIALOGUE_V2_EXECUTION_PLAN_20260917.md`,
  `MATH_JUDGING_EXECUTION_PLAN_20260917.md` (§A3), `REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md`, `PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md`.
- `docs/RLHF_COORDINATION/CURRENT_VERSIONS.md`; `data/rlhf/target_distribution_v1.json`.
- Code that emits labels: `data/rlhf/gen02_demo/seed_demo.py`, `data/rlhf/prompts/forum_gate_rewrite_el.txt`, `data/rlhf/inventory.py`.
- Owner rulings embodied: maths definition (§4.5 T5, owner's text), generator version definitions (registry §0), the agreed distribution.

## Acceptance criteria
Blocking:
1. Every term the five plan files use is defined in the spec (evidence: `R-PG1_term_coverage.txt`; spot-check beyond the scripted list).
2. Spec and glossary agree for every definition the glossary carries (values, word ceilings, maths text, dialogue purpose).
3. No definition contradicts a plan it serves (maths T5 vs maths plan §A3; sampling points vs dialogue v2 plan §6; ledgers vs ingestion plan §4; primary purposes vs the target distribution).
4. Each §7 decision is resolved or deferred with a stated default, and none silently changes an owner-agreed number (distribution shares, attitude/register/difficulty weights).
Major:
5. Definitions are specific enough for Sol to write and for a reviewer to check (especially detail ceilings, task types F1–F9, safety sub-kinds).
6. Known gaps in current code (for example seed_demo.py's undefined labels) are listed as gaps, not described as fixed.

## Evidence
- `docs/RLHF_COORDINATION/reviews/R-PG1_term_coverage.txt` (69 terms, none missing).

## Known limitations
- The glossary's section headers name spec sections; only the definition lines are meant to be copied into prompts.
- Code has not yet been changed to use the glossary; that is R-PG3's scope.

## Out of scope
Generator code, the registry, reply sampling and judging.
