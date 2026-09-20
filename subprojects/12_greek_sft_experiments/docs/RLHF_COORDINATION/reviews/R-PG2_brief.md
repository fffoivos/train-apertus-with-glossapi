# Review brief R-PG2 — import reconciliation and joint coverage

## Stage goal
One registry of everything that exists (prompts, seeds, sources, judgements, pair credit) with stable identities, bound seeds and honest joint
coverage in three separate ledgers, so that the next ~500 slots are allocated to real per-cell shortfalls. Final product of the phase: about
500 new prompts to the agreed distribution, their replies sampled and evaluated, on a review page.

## Scope since R-PG1
- `data/rlhf/registry/registry.py` (import, ledgers, frontier) and `registry.sqlite` (derived).
- `data/rlhf/registry/relabel_v1.py` → `relabel_v1.jsonl`: forum task_type, maths_content and maths ambiguity for 1,551 gate-accepted forum posts and maths content for 167 round-2 seeded prompts, using glossary definitions (Sol, 287 calls). No prompt text changed.
- Registry report `data/rlhf/registry/registry_report.json` (copy: `R-PG2_registry_report.json`).
- The first register `data/rlhf/inventory.py` is superseded (known defects listed in CURRENT_VERSIONS.md).

## Context to read
- `docs/RLHF_COORDINATION/PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md` §1–§4, §6 (the requirements this stage implements).
- Spec `docs/SEED_LABEL_SPEC_20260917.md` §5.4–§5.7 (terms: keepable, ledgers, keys, aliases, seed status, generator version).
- `data/rlhf/target_distribution_v1.json`; `docs/RLHF_COORDINATION/CURRENT_VERSIONS.md`.
- Inputs: `data/rlhf/pool/round1_all.jsonl`, `round2_all.jsonl`, `*_judged.jsonl`, `*_samples.jsonl`, `forum_gated_v3.jsonl`, `round1_excluded_json_leak.json`, `data/rlhf/gen02_demo/round2_batch*.json`, `data/rlhf/prompt_generator/runtime/runs/round1_121/curator.jsonl`, `data/rlhf/dialogue_quality_depth/runtime/manifest.json` and measurement trajectories.

## Acceptance criteria
Blocking:
1. Reimporting twice changes no unique count and no pair credit.
2. All 167 round-2 prompts bound to their exact saved seeds; the unused seed accounted for; the 6 Greeklish-with-English seeds reported as compatibility issues.
3. The 17 identical forum prompts resolved to aliases of one logical prompt, with all their judgements attached.
4. Relabelling changed no prompt text.
5. Pair credit E follows the pair rule (top reinforce vs lowest non-reinforce within one judged batch, clear margin, current rubric, distinct texts), one pair per single-turn prompt, zero credit for maths content (held), defunct 0.1 rows, dialogue pilot rows and excluded rows.
6. Targets are joint per purpose × language cell with margins respected; A and E never count the same prompt; unmeasured cells use a stated provisional prior with a range.
Major:
7. Maths content flags are plausible on a stratified sample of forum and seeded prompts (especially calculation posts and budget arithmetic inside everyday prompts).
8. Known simplifications are stated rather than hidden (for example: A counts gate-accepted forum posts that the owner has not reviewed; the yield prior widens the lower bound by 25 %).

## Evidence
- `R-PG2_evidence.txt` (idempotence result, counts, duplicate groups, seed binding, compatibility issues, per-cell keepable counts, pair credit reasons, prompt-text check).

## Known limitations
- Ledger E uses judged batches from rounds 1–2 only; no reply was re-sampled.
- Forum source identity is the thread URL (gate v3 rows with the same URL are grouped).

## Out of scope
Generator code and the manifest (R-PG3), reply sampling and judging.
