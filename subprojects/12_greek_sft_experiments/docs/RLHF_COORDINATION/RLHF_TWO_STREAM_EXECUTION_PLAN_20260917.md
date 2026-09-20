# RLHF preparation: two parallel workstreams

Date: 17 September 2026
Status: execution plan and delegation brief; no agents dispatched and no generation/training launched by creating it.
Main executor: Opus or Sol — owns maths corrections, orchestration, cumulative pool and training readiness.
Second executor: another Opus or Sol agent — owns dialogue improvements and the distinct demo.

## 0. Two aspects: prompt generation and RLHF

Every item in this plan is tagged with the aspect it belongs to.

**[PG] Prompt generation** — producing the inputs the model will answer:
- the declared target distribution over cells (primary purpose × language: 42 cells = 6 purposes × 7 languages; spec §5.4);
- forum prompts: gate, selection, forum weights;
- seeded prompts: seeds, labels and their definitions, the generator prompt, a reviewer pass on the prompts, instance-key uniqueness with similarity screening, languages;
- prompt versioning when a prompt is clarified or corrected;
- dialogue prompts: openings, the adaptive user simulator and user state, reference-guided scenarios (user, world and learner views), and the raw trajectory rollout with one unselected Apertus reply per turn, because the recorded conversation is the dialogue's prompt material.

**[RLHF] RLHF** — what happens to a prompt or a saved conversation prefix:
- replies: the number and mode of generating them (sampling settings, replies per prompt, escalation from 4 to 32, branching from saved prefixes), and the choice of sampling points after turn annotation;
- judging: rubric v2.4, the specialist maths judge and its verified references, turn annotation, calibration and root review;
- pairs and eligibility: pair rule, active view, supersession, audits;
- pool assembly (quotas on accepted pairs, deduplication, decontamination, splits), DPO training and evaluation.

**[shared]** — coordination, versions, terms and budget that both aspects depend on.

The two aspects meet in one loop: PG fills the declared distribution; RLHF measures accepted pairs per cell; the deficits in accepted pairs decide how many more prompts PG makes in each cell.

Order (owner, 17 Sept): work on prompt generation first. RLHF items wait, apart from evidence that already exists.

### 0.1 Prompt generation track — work order [PG]
- **PG1 Terms.** Resolve the label-spec decisions that touch prompt generation (spec §7) and freeze spec and glossary (frozen v1.0.2, 17 Sept 2026; R-PG1 cycle-2 fixes applied without a third cycle). → review R-PG1 (§10).
- **PG2 Target distribution — agreed.** Primary purposes: dialogue 35, everyday 25, instruction 15, factual 10, safety 10, maths 5. Languages: Greek 70, English 20, French, German, Spanish, Italian and Portuguese 2 each. Source: Codex's REVIEW_HANDOFF_20260916.md §2 and the generator design file. Owner, 17 Sept: the foreign-language shares must actually be generated this time (round 2 had none). Recorded in `data/rlhf/target_distribution_v1.json`; targets count accepted pairs per cell. Still open: the first-run size (500 pairs is a checkpoint only).
- **PG3 Register what exists, then fill to the target.** Existing forum and seeded prompts are kept; generation continues towards the target distribution.
  - PG3a Inventory: one record per existing prompt and dialogue with the shared labels, generator version, defunct flag, pair state and maths flags (`data/rlhf/inventory.py` → `data/rlhf/pool/inventory.jsonl`; spec §5.5). First register, 17 Sept: 611 live records (314 forum, 167 seeded by 0.2, 102 seeded by defunct 0.1, 28 pilot dialogues); keepable single-turn prompts are 93 % Greek, 7 % English and 0 % other languages.
  - PG3b Relabel existing records where a label was undefined when assigned (forum task_type, seeded attitude and register) with the defined vocabulary, without changing the prompts.
  - PG3c Deficits: use joint purpose × language cells and validated active pairs, with deduplication and maths holds. The first inventory's marginal “pairable” counts are historical diagnostics, not eligible-pair credit or a generation schedule. The 17 Sept audit found 17 identical cross-round forum prompts under different IDs, leaving 464 unique keepable single-turn message payloads before semantic review. Import the saved seeds too: all 167 round-2 generated prompts bind to their original seeds. See PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md for the audit and required reconciliation.
  - PG3d Forum part: define task_type in the gate prompt, apply forum weights in the selector (astrovox ≤ 3 %), and draw forum prompts only for cells in deficit.
  → review R-PG2 after the import reconciliation (ingestion plan §5 step 1); R-PG3 after PG3d, PG4 code and the dry-run manifest (§10).
- **PG4 Seeded part: generator 0.2 release.**
  - Glossary definitions in the seed prompt.
  - Wide axis value pools (people, situations, topics), plus restored target languages.
  - Instance-key uniqueness registry with similarity screening; source lineage and task family recorded (spec §5.4).
  - Independent reviewer pass on the prompts: labels realised, no framing text, self-contained, correct language.
  - Maths prompts follow the maths definition and its seven kinds (spec §4.5 T5): worked reasoning only when the request asks for it; ambiguous or underspecified maths flagged, never given invented assumptions; maths content flagged inside other purposes; all maths handed to RLHF for reference verification.
  - Code, tests and a receipt.
- **PG5 Fill.** First 50 production slots → review R-PG4; the remaining ~450 and the review page → review R-PG5 (§10). Plan approximately **500 additional unique requests/starting seeds**, as requested on 17 Sept, separately from the still-open first DPO pair count. First credit existing forum material and reconcile seeds; allocate joint-cell quotas using eligible-pair deficits and explicitly provisional yields where unmeasured. Validate the first 50 production slots before the remaining approximately 450, preserving reserved dialogue slots and keeping the distinct demo outside this target. During PG-only work, update prompt quality/diversity counts; new pair-yield measurement waits for RLHF. Follow PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md; publish the prompt review page before new reply sampling.
- **PG6 Dialogue prompt generation (generator 0.3).** Openings from 0.2 seeds; adaptive user simulator and user state; reference-guided scenario packets; raw trajectory protocol. Stream B follows DIALOGUE_V2_EXECUTION_PLAN_20260917.md.

Dependencies: PG1 before PG3 to PG6; PG2 before PG5; PG3 and PG4 can run in parallel. PG6 integration → review R-PG6 (§10). RLHF on CSCS is gated by R-RL1 to R-RL5 (§10.3).

## 1. Decision

Proceed incrementally. Reuse valid existing prompt/response material and valid old judgements. Replace the mathematical judgements that need correction in the active dataset; preserve their historical records. Continue adding new valid judgements and preference pairs rather than rebuilding everything.

These corrections are enough to justify the next controlled DPO preparation phase, not proof that every existing judgement is sound or that DPO will improve the model. A judgement count is not a training-size count. Count only distinct, eligible preference pairs with a verified acceptable chosen reply, a meaningful rejected alternative and complete provenance.

Three qualifications:
- [RLHF] Rejudge mathematical content across categories, not only rows carrying a math label. This includes all pre-existing mathematics, because the maths evaluation changes: the inventory flags 77 records (round 1 and 2 maths prompts, forum calculation and mathematica posts, pilot dialogues with arithmetic).
- [PG + RLHF] A changed/clarified prompt needs a new version (PG) and newly sampled replies (RLHF). Relabelling alone is insufficient for an ambiguous or defective task.
- [PG + RLHF] New dialogue collection follows the corrected method. Previously collected dialogue is retained only when the actual pair remains valid; a repetitive user simulator does not automatically invalidate every historical example.

## 2. Ownership and links

| Workstream | Owner | Scope | Detailed plan |
| --- | --- | --- | --- |
| A — Maths, generator 0.2 corrections and orchestration | Main execution agent | [RLHF] specialist maths judge; replace affected active verdicts; retain valid old rows. [PG] correct generator 0.2 before new non-dialogue collection (§4a). [RLHF] grow, deduplicate, balance and freeze the cumulative pool; final training readiness. [shared] budget and orchestration | MATH_JUDGING_EXECUTION_PLAN_20260917.md; §4a below; ../SEED_LABEL_SPEC_20260917.md |
| B — Dialogues (generator 0.3 corrections) | Second Opus/Sol agent | [PG] adaptive users; reference-guided writing/troubleshooting/learning scenarios; raw trajectories. [RLHF] saved-prefix sampling; healthy continuation and recovery points; evaluator view. [shared] own review evidence | DIALOGUE_V2_EXECUTION_PLAN_20260917.md; §4a below; ../SEED_LABEL_SPEC_20260917.md §4.4, §4.7, §4.8 |

Shared evidence: OPUS_FEEDBACK_20260917.md.
Shared terms: ../SEED_LABEL_SPEC_20260917.md (labels and terms both streams use; spec v1.0.2, frozen 17 Sept 2026; R-PG1 cycle-2 fixes applied without a third cycle) and its prompt-ready glossary data/rlhf/prompts/seed_label_definitions_v1.md.
Shared versions: CURRENT_VERSIONS.md (current version of every component, data set and page; generator 0.1 is defunct; 0.2 = a declared target distribution over cells (primary purpose × language) filled by forum prompts plus person-and-story seeds; 0.3 = 0.2 plus multi-turn dialogue data). The target checkpoint G4F6P1 is the R4_full epoch 1 model listed there.
Historical six-case demo: REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md. Current dialogue scope and call controls: DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md (at least 30 existing-type + 15 troubleshooting + 15 learning; A/B sampling at first error and subsequent instruction change, not helpful-only).

The main agent delegates B with the scope above, not an unrestricted instruction to launch resources or train. The dialogue agent provides import-ready reviewed output; only the main agent promotes eligible production data into the cumulative pool.

## 3. Initial coordination contract — [shared]

Before either changes shared code:
- Main agent reads live coordination state, current source changes, approved experiment manifest and budget ledger.
- Record paths each agent owns and any shared interface files.
- Main owns the maths rubric/integration and active-pool manifests.
- Dialogue agent owns isolated dialogue_v2 and reference_guided_dialogue_demo development paths from its plan.
- Only one named owner controls provider lifecycle and shared budget. Resource use by B is scheduled with the main agent; parallel preparation does not imply competing GPU launches.
- Put progress and blockers in docs/RLHF_COORDINATION/messages/ with readable timestamps. Main produces one current summary and a next-action list.
- Existing old scripts/rubrics remain versioned; neither agent silently overwrites the other's records.

Agree one judgement/import contract:
[PG fields] prompt ID/version/hash; prefix hash; primary purpose and language (the cell); forum task_type where applicable; source lineage; task family; `generator_version`; `source_route`; `dialogue_protocol_version`; `opening_generator_version`; glossary version; user-policy version. [RLHF fields] candidate IDs/hashes; target checkpoint; sampling config; judge/reference versions; eligibility; rejection/hold reason; supersedes ID where applicable; sampling point kind and assistance level for dialogue rows; origin (original sample or resample). [shared] split; development/production status. Provenance fields use the closed lists of spec §5.4: `generator_version` ∈ {0.1 (defunct, archival), 0.2-prototype (round 2 seed script, and forum gate v3 selections of rounds 1–2; archival), 0.2, 0.3}, and new rows record 0.2 or 0.3; `source_route` ∈ {forum-gate-v3, seeded, dialogue}; `dialogue_protocol_version` ∈ {none, dialogue-quality-depth-v1, dialogue-v2}; `opening_generator_version` is the generator version that produced a dialogue's opening (none for single-turn rows). A combined registry value such as "dialogue-quality-depth-v1 (0.1 seeds)" maps to dialogue_protocol_version=dialogue-quality-depth-v1 + opening_generator_version=0.1. Glossary version is the sha16 of the prompt-ready glossary. Every label value in the contract uses the vocabulary of ../SEED_LABEL_SPEC_20260917.md.

## 4. Parallel workflow

Main agent A:
1. [RLHF] Snapshot current pool and counts; quarantine affected maths from active positives.
2. [RLHF] Build specialist verification and judging, calibrate on existing candidates.
3. [RLHF] Rejudge affected mathematics, including all pre-existing maths flagged in the inventory, and regenerate its pair eligibility.
4. [PG, then RLHF] While dialogue work proceeds, correct generator 0.2 (§4a), then collect/review new non-dialogue material in underfilled cells (primary purpose × language, ../SEED_LABEL_SPEC_20260917.md §5.4).
5. [RLHF] Audit retained old material, integrate corrected maths and later eligible dialogue releases.
6. [RLHF] Freeze a training-ready manifest and prepare the priced first DPO comparison.

Dialogue agent B:
1. [PG; evaluator view RLHF] Implement adaptive user/state and role-separated references, using the move labels, turn metadata, user-state scales, role views, sampling point kinds and ending reasons defined in ../SEED_LABEL_SPEC_20260917.md §4.7–§4.8.
2. [RLHF] Implement saved-prefix selection and same-prefix candidate comparisons.
3. [shared] Run meaningful offline checks.
4. [PG: raw trajectories; RLHF: branch candidates] Execute the corrected 30/15/15 dialogue collection under DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md when readiness/budget permit; the original ten-case development run is historical evidence.
5. [shared] Review complete transcripts and export evidence to the main agent.
6. [shared] Stop at the specified owner review for the new-category demo. Do not silently turn its development cases into production data.

These paths converge at dataset integration, not at code editing. A can keep adding valid single-turn data while B is under review. A mixed dialogue experiment cannot be declared ready by substituting more single-turn rows for missing dialogue.

## 4a. Terms and generator corrections

### Shared terms (both streams) — [shared]
- Both streams use the labels and terms of ../SEED_LABEL_SPEC_20260917.md. Any prompt that sends a label sends its definition, copied from the glossary (spec §6); every exported row records the glossary version.
- Gate before paid collection in either stream: the spec's decisions are resolved by the owner, or deferred with a stated default recorded in the spec's change log. New label values enter the glossary before they enter a prompt.
- CURRENT_VERSIONS.md is updated in the same step as any component change.

### Generator 0.2 corrections (stream A, before new non-dialogue collection) — [PG]
Round 2 was generator 0.2's prototype run. Before it is used for new collection:
1. Declare one target distribution over cells (primary purpose × language; 42 cells = 6 purposes × 7 languages), with approved quotas on accepted pairs (§6).
2. Adopt one primary-purpose taxonomy for forum and seeded prompts (spec §4.5; forum task_type maps to a primary purpose by spec §5.1 and stays an analysis label), so forum prompts count against the same targets and deficits are computed per cell.
3. Send label definitions with every label in the seed prompt (attitude, register, detail, task; spec §4.1–§4.6); `anxious` is defined, not drawn (spec decision 1).
4. Add an independent reviewer pass on generated prompts using the same glossary.
5. [RLHF, listed here because every generated maths prompt needs it] Route maths prompts to verified reference solutions (MATH_JUDGING_EXECUTION_PLAN_20260917.md §A2).
6. Enforce instance-key uniqueness with similarity screening across runs (spec §5.4), and apply the forum weights in code (astrovox ≤ 3 %, RLHF_PLAN_20260916.md §31).
7. Restore non-Greek target languages in the seeded share; round 2 had 374 Greek and 33 English prompts and none in the other target languages.

### Dialogue data generation corrections (stream B, generator 0.3) — [PG] for openings, user simulator, scenarios and raw trajectories; [RLHF] for sampling points
The dialogue v2 plan implements these with the spec's terms: adaptive user moves and turn metadata (§4.7); user state, role views, sampling point kinds and ending reasons (§4.8); dataset and eligibility terms (§5.4). The dialogue pilot's P/R/C labels map to prevention, supported recovery and healthy continuation as stated in spec §4.8. Openings come from generator 0.2 seeds, not from the defunct 0.1 fixtures still referenced by the pilot manifest.

## 5. Replace judgements without destroying history — [RLHF]

Use an append-only judgement history plus an explicit active-view selection:
- Each new maths judgement refers to the exact existing prompt and candidates and identifies what it supersedes.
- Active maths records select the approved specialist version. Historical general-rubric maths verdicts no longer determine eligibility.
- Valid non-maths judgements retain their existing versions/provenance; do not rerun them just to make all hashes identical.
- Multiple rubric versions may coexist if they have a documented domain role and compatible acceptance criteria.
- Rejudging one prompt does not create another training example. Exact candidate duplicates do not create extra diversity.
- Rebuild paired outputs and audit counts after replacement; some prior pairs may disappear or change chosen/rejected.
- Write a before/after report: retained, superseded, corrected, held, excluded and newly added.

For retained non-maths rows, inspect a stratified sample of 50 proposed pairs (or all if fewer): task, language, source and known failure modes. Apply existing executable constraint checks where available. Remove known invalid positives immediately; if the audit exposes a systematic issue, quarantine/review the affected group rather than inferring all old data is invalid. This audit is quality control, not proof of zero label error.

## 6. Grow towards the first DPO run — [RLHF], with PG metrics marked

Maintain separate counts:
- [PG] Raw prompts.
- Sampled responses.
- Judged prompts.
- Eligible preference pairs.
- [PG] Unique prompts, source lineages and task families.
- Unique dialogue trajectories, depths and assistance levels.
- Held/excluded and development-only rows.
- Coverage and remaining deficits per cell, primary purpose × language (RLHF measures them; PG acts on them).

Select new work from the deficits in accepted pairs, not raw prompts. Pair-yield differences otherwise distort the final mix.

Default constraints:
- One selected pair per single-turn prompt for the first pilot unless a justified design says otherwise.
- Cap dialogue contribution per trajectory; multiple prefixes are correlated and do not count as independent conversations.
- Exact and near-duplicate/family checks and benchmark decontamination before freezing.
- [PG + RLHF] Keep each source lineage (renderings, translated variants, versions and branches) in one split.
- Preserve sufficient non-Greek coverage and benign safety cases; don't fill every gap with easy Greek prompts or refusals.
- Do not infer absent capability from no success in a small candidate set.

### Size and the meaning of “critical size”

There is no established universal critical count. The earlier discussion proposed 500 vetted pairs as a manageable first controlled pilot; it was a proposal, not a reduction of the originally planned larger run.

Main must identify the current owner-approved first-experiment target and preserve it. The historical RLHF_PLAN_20260916.md contains a much larger approximately 20,000-pair recipe; do not silently treat that old recipe or the later 500-pair suggestion as a new approval.

Use 500 eligible pairs as a progress/readiness checkpoint if useful, with cell (primary purpose × language) and trajectory coverage reported. If the first run has an existing approved larger target, continue towards it unchanged. If no first-pilot size is actually fixed, propose the 500-pair controlled pilot explicitly with measured cost and coverage before the training decision; do not claim 500 guarantees statistical power or improvement.

The previous suggested 35/25/15/10/10/5 purpose mix and 70/20/2/2/2/2/2 language mix are planning proposals to reconcile with the active manifest. Do not silently rebalance approved quotas.

## 7. Dialogue release and review gate — [PG + RLHF]

B delivers:
- Versioned code/prompts/configuration and tests; prompts carry the glossary definition of every label they send.
- Current collection: at least 30 existing-type, 15 troubleshooting and 15 learning dialogues; separate group accounting and A/B sampling under DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md.
- Complete transcripts, reference/user/world state views, consistency assessment and proposed sampling points.
- Candidate/pair evidence for the improvements diagnostic where applicable.
- Known failures, limits, cost and recommendation.

The historical ten-case demo remains training-ineligible and zero-credit toward first-experiment quotas. The current 30/15/15 collection is governed by DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md; its additional categories do not replace the first 30. The user explicitly requested a distinct demo before reviewing results. Neither agent may reduce the first experiments to pay for demo slots or silently import the demo rows.

After user review, apply the accepted dialogue method to new production conversations. Already valid historical dialogue pairs may remain in the cumulative pool; flag provenance and known simulator limitations. Invalid chosen answers, oracle leakage, mismatched prefixes or unresolved correctness exclude a pair.

## 8. First DPO readiness and experiment interpretation — [RLHF]

Prepare, without claiming that training is already authorized by this planning request:
- Frozen eligible train/dev manifests, source hashes and per-cell coverage.
- Independent evaluation prompts and conversations with source-lineage/trajectory separation.
- Actual tokenized-batch checks: same prefix for both alternatives, history excluded from target loss, target reply included, no silent truncation or answer leakage.
- Pinned starting checkpoint and reference-model configuration; reproducible recipe and cost estimate including evaluation.
- Fresh financial capacity check. Do not reuse old CHF or provider estimates as current balances.
- A comparison with the unchanged starting model using fresh one-response evaluation at matched decoding conditions.
- If budget permits and the owner retains the earlier proposal, a positive-only SFT control on the same chosen answers distinguishes preference-learning benefit from additional supervised practice.

Beware the historical recipe includes an SFT term alongside DPO. State the actual loss and controls: do not describe a combined objective as an isolated test of pure DPO. Agree evaluation outcomes and acceptable retention tolerances before looking at model comparisons.

Measure task completion, factual/mathematical errors, instruction following, Greek quality, dialogue outcomes and other-language retention, alongside the unchanged benchmark protocols. Pair count alone is not the launch gate.

## 9. Budget, reporting and done — [shared]

The main executor owns shared accounting. Development tags are separate but all provider spending still counts against existing global ceilings. The old dialogue ledger/call cap must be refreshed; new planning files do not grant new money, reset Sol limits or reserve GPU time.

Before paid work, complete an itemised forecast for A and B, reserve required first-experiment resources, and schedule sessions with teardown/watchdog protections. If scope cannot fit existing authorization, finish free preparation and report the exact shortfall rather than silently borrowing from first-experiment reserves.

Main status should answer:
- What changed in maths eligibility?
- How many valid old pairs remain?
- How many new eligible pairs were added?
- Which coverage cells remain short?
- What is B doing, and which review gate is next?
- What was spent and what remains?
- What exact condition separates the current state from first-training readiness?

Workstream A done: specialist maths judgements active, old valid records retained, pool accounting trustworthy, new judgement pipeline correct.
Workstream B development done: specified improvements and separate demo ready for user review, with evidence and limits.
Combined preparation done: approved-size and coverage dataset frozen, production dialogue accepted where required, trainer/evaluation/budget checks complete.

Do not claim the research objective achieved merely because the dataset is large enough. Only the trained-model comparison can establish whether the new preference data improves behaviour.

## 10. Review checkpoints — independent Sol xhigh reviewer [shared]

Owner, 17 Sept: before the next work starts, fix in advance the points where an independent Sol reviewer (gpt-5.6-sol, reasoning
effort xhigh) reviews the work done up to that point, with the context and the goals of that stage.

### 10.1 Protocol
- Tool: `python3 data/rlhf/sol_review.py <ID> [--cycle N]` — a fresh, read-only Codex session run from the repository root. It reads the
  brief `docs/RLHF_COORDINATION/reviews/<ID>_brief.md` and, from cycle 2, the previous review and the implementer's reply
  `<ID>_reply_<N-1>.md`. The verdict goes to `<ID>_review_<N>.md` and a line in `reviews/INDEX.md`.
- Every brief has these sections: **stage goal** (what this stage must achieve for the programme); **scope since the previous
  checkpoint** (exact changes, files and runs); **context to read** (plan sections, spec sections, registry, code, data, logs, owner
  decisions that apply); **acceptance criteria** (blocking and major); **evidence** (tests, counts, samples, receipts, hashes);
  **known limitations**; **out of scope**.
- Verdict: PASS, or HOLD with blocking or major findings. On HOLD: fix, write a reply per finding (changed, or disagreed with evidence),
  rerun the same checkpoint as the next cycle. Three HOLD cycles without convergence go to the owner with both sides' arguments.
- A HOLD blocks the step that follows the checkpoint. A PASS is not an owner go: any paid launch on CSCS still needs the owner's
  explicit go, and training needs the recipe table against the previous run.
- The reviewer never sees the orchestrator's conclusions as facts: briefs point to files and evidence, and the reviewer verifies them.
- Each checkpoint result is posted on the board and the registry is updated in the same step.

### 10.2 Track 1 — creating generator 0.3 (prompt generation) [PG]

| ID | When | Stage goal | Context to send | Blocking criteria |
|---|---|---|---|---|
| R-PG1 Terms frozen | after PG1; before any relabelling or generation | one vocabulary for every label and term the plans and code use, frozen as spec v1.0 and glossary v1.0 | spec, glossary, this plan §0/§0.1/§3/§4a, dialogue v2 plan, maths plan §A3, registry, owner decisions on spec §7, a term-coverage check over the plans and code | every term used is defined once; spec and glossary agree; no contradiction with the plans (maths definition, P/R/C mapping, primary purposes); each spec decision resolved or deferred with a recorded default |
| R-PG2 Import reconciliation and joint coverage | after PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md §5 step 1 (aliases, seeds, source lineages, relabelling, joint coverage); before any forum draw or seeded generation | one registry of everything that exists, with stable identities, bound seeds and honest joint coverage in three separate ledgers (reviewed prompts, validated eligible pairs, forecast yield) | ingestion plan §1–§4 and §6, `target_distribution_v1.json`, the import and registry code and its outputs, the alias table, the seed registry, the joint coverage report, `inventory.py` and its outputs as the superseded first register, round 1/2 pools, saved `round2_batch*.json`, dialogue pilot manifests, spec v1.0.2 | reimporting twice changes no unique count and no pair credit; all 167 round-2 prompts bound to exact saved seeds and the unused seed accounted for; all 17 identical forum pairs resolved to aliases with candidate history kept; relabelling changed no prompt text; deficits computed per joint purpose × language cell; pairability heuristics not counted as eligible pairs; the E and A ledgers disjoint; maths content flags complete on a stratified sample |
| R-PG3 Generator 0.2 release and the 500-slot dry-run manifest | after PG3d, PG4 code with offline tests, and ingestion plan §5 steps 2–3 (forum draws against the registry, dry-run quota manifest); before any production generation | a generator and a quota manifest that realise the agreed joint distribution, send definitions with every label, and cannot reproduce the 0.1 or round-2 seed defects | generator code, tests and output, prompts as sent for a dry-run batch, glossary, the reservation registry, compatibility rules, forum selector with weights, the dry-run manifest with cell totals, subtype and difficulty allocation, concrete seeds, source coverage, provisional yields and the separate dialogue reservation; spec §4–§5; ingestion plan §3–§4 and §6 | quotas total exactly the requested number with joint cells and margins agreeing; category frequencies independent of subtype counts; incompatible labels (English with Greeklish) rejected before generation; identical substantive seeds caught across IDs and versions; reservations atomic across workers; seeds carry concrete substantive preconditions per task (ingestion plan §3); glossary definitions in every prompt; the five foreign languages present; maths per spec T5; no framing text or JSON leak possible; receipts hash-bound |
| R-PG4 First 50 production slots | after ingestion plan §5 steps 4–5 (generate and review the first 50 slots, repair systematic defects); before the remaining ~450 | evidence that production output keeps each seed's substance and is natural, unique and correctly labelled before scaling | the 50 prompts with seeds, reservation records, seed-to-message check results and reason codes, reviewer outputs, near-duplicate nominations and their resolution, repair log (at most two attempts per slot), the dry-run manifest | required givens, text, constraints and task survive in every message; no two seeds collapse into one request; language and texture realised without changing the task; no invented facts that change answerability; detail levels distinguishable; maths items follow T5 with ambiguity flags; every systematic defect found is fixed in code before continuing |
| R-PG5 Remaining ~450 and the owner review page | after ingestion plan §5 steps 6–7; before any new reply sampling | about 500 new unique requests or dialogue starting seeds whose coverage, diversity and provenance are reported honestly for the owner's review | batch receipts, per-batch count and diversity checks, the before/after distribution view, the joint coverage report, the owner prompt review page, held or unresolved identities, decontamination report | every slot accounted for (generated, held with reason, or reserved for dialogue); counts per joint cell match the manifest or deviations are explained; diversity reported across task forms, instances and task families separately from languages and personas; no new accepted-pair yields claimed; nothing from a defunct generator credited; the review page published before sampling |
| R-PG6 Dialogue integration (generator 0.3) | after the owner reviews the dialogue v2 package and the accepted method is integrated into production; before production dialogue collection | a production dialogue generator that implements the accepted design and nothing the owner rejected | dialogue v2 review package and the owner's decisions, integrated code and tests, prompts as sent, dialogue v2 plan, spec §4.7–§4.8, import contract §3 | openings from 0.2 seeds; adaptive user and role views as accepted; information barriers tested; import contract fields present; development rows excluded from production |

### 10.3 Track 2 — running RLHF on CSCS [RLHF]

| ID | When | Stage goal | Context to send | Blocking criteria |
|---|---|---|---|---|
| R-RL1 Sampling readiness | before the first CSCS reply-sampling job | correct, reproducible, affordable reply sampling for the frozen prompt set | frozen prompt manifest and hash, sampling config (replies per prompt, escalation), CSCS job scripts (`cluster/rlhf_sample.sh`, workbench and vLLM serving), checkpoint identity and sha, receipts design, fresh CHF ledger and forecast (`execution_state.json`: CHF 222.92 of the CHF 240 cap used on 17 Sept), import contract | checkpoint sha verified on the cluster; sampling settings declared and identical to the stated baseline or changes disclosed; outputs carry the §3 fields; forecast within the approved CHF cap or the shortfall stated for the owner; no maths item sampled into positives while held |
| R-RL2 Maths judge calibration | after maths plan A2–A4 on the 20 round-2 maths prompts and the required examples; before rejudging the 77 pre-existing maths items and new maths | a specialist maths judgement that matches spec T5 and catches the known false positives | specialist rubric and schema, references with statuses, calibration report, verdict diff, the required cases (g2:R2B1_006, g2:R2B12_005, PAIR-RS001), spec §4.5 T5 and §5.6, maths plan | references built without candidate replies; correctness separate from explanation length; invalid reasoning never positive; ambiguous items held; diff reproducible; the required cases handled as the plan states |
| R-RL3 Judging, pairs and active view | after judging new replies, bulk maths rejudging and pair building; before freezing the pool | an eligible-pair set that is correct, traceable and counted against the target | judgement history, active view, pair builder and outputs, before/after report, the 50-pair audit of retained rows, per-cell accepted-pair counts against `target_distribution_v1.json`, inventory | supersession history intact and no superseded positive active; eligibility per spec §5.4; no development or defunct-generator rows unless the owner kept them; audit issues resolved; counts reproducible |
| R-RL4 Trainer and freeze | after building `cluster/dpo_train.py` and freezing train/dev manifests; before any training launch | a training run whose data, loss, masks and evaluation are exactly what we claim | trainer code, tokenized-batch check outputs, train/dev manifests and hashes, loss specification (including any SFT term), recipe table against the previous run, reference-model config, evaluation protocol with tolerances fixed in advance, CHF forecast and cap status | history tokens masked and both sides share the prefix on real batches; no silent truncation; loss stated honestly; splits by source lineage and trajectory; decontamination passed; evaluation and tolerances fixed before training; forecast within the approved cap |
| R-RL5 Results | after training and the evaluation chain | conclusions that follow from the evidence | results table, logs, receipts, criteria fixed in R-RL4, comparison with the unchanged starting model | every claim traceable to a result; failing criteria reported as failing; no conclusion beyond what the comparison shows |

