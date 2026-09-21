# Import existing prompts and seeds; plan approximately 500 additional requests

Date: 17 September 2026
Status: audited requirements and execution plan, not implemented or run.
Owner: main execution agent (generator 0.2 and cumulative inventory), with the dialogue agent supplying the same import contract for generator 0.3.
Scope: [PG] first. No new sampling, judging, training, resource launch or monitoring is authorised by this document.
Companion: RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md, PG3–PG6.

## 1. What the audit actually found

Inspected inventory.py, target_distribution_v1.json, gen02_demo/seed_demo.py, gen_round2.sh, the 14 saved round2_batch*.json artifacts, both single-turn pools and the current versions/plan.

| Finding | Evidence and consequence |
| --- | --- |
| Existing seeds are not imported | inventory.py retains labels and a prompt hash, but not the seed object, its task parameters or full source lineage. This cannot prevent semantic task reuse across batches. |
| Seed recovery is feasible | All 167 round-2 generated prompts match a saved batch seed by ID and match its message exactly after whitespace normalisation. There are 168 saved seed records; account for the unused one explicitly. |
| Existing prompts are double-counted | 17 cross-round forum pairs have identical complete messages under different IDs: 11 everyday, 6 factual. The advertised 481 keepable single-turn rows represent 464 unique message payloads: 297 forum + 167 generated, 431 Greek + 33 English. These are input counts, not verified eligible pairs. |
| Existing deficit tables are not joint | inventory.py computes purpose and language separately. For example, a surplus of Greek factual items cannot satisfy an English factual deficit. |
| Pairability is overclaimed | The current heuristic merely detects a reinforce verdict and another verdict. It does not prove a valid exported pair, clear margin, active judge version, candidate uniqueness or completed maths verification. Treat its numbers as historical yield evidence, not eligible-pair credit. |
| Dialogue counts use a different unit | The inventory counts one pairable trajectory as one item even when it contains several preference pairs. Track both distinct trajectories and eligible saved-prefix pairs; do not put first-turn-only pairs in the dialogue quota. |
| Task weighting is biased by subtype count | gen_round2.sh requests instruction/everyday/factual/math/safety weights 38/19/15/15/13. seed_demo.py applies each weight to every matching subtype. With 2/4/2/2/2 subtypes, effective category probabilities are approximately 31.93/31.93/12.61/12.61/10.92 percent. Draw category quotas first, then subtype quotas. |
| The current seed hash is not a uniqueness guarantee | It includes the generated ID. The same substantive seed with a new ID produces a different hash. No persistent collision registry is consulted. |
| Random labels do not enforce compatibility | Six saved seeds combine English with Greeklish. These are contradictory specifications, regardless of what language Sol ultimately produced. |
| Concrete differentiation remains under-specified | A specific field such as “a number, date or amount” does not bind an actual number, date or amount. Sol chooses it. Private stories and unique persona combinations do not establish unique task instances. |

There were no exact duplicate seed objects among the 168 saved seeds after removing ID and seed_hash. This is a narrow finding: it does not establish semantic diversity or demonstrate that the differences survive in the generated requests.

## 2. Import contract [PG; pair credit is RLHF]

Import everything for provenance and collision checking, but distinguish archival presence from eligibility.

1. Ingest all round pools, the complete accepted forum pool, saved generation batches, development/demo seeds and dialogue manifests. Record rejected/defunct material as such; do not silently promote it into training.
2. Retain immutable original records and file hashes. Assign a stable logical prompt ID with an alias table for historical IDs. Merge duplicate prompt identities without deleting distinct response samples or judgement history.
3. For the 167 round-2 prompts, bind the full saved seed and batch provenance. Register the unused seed as generated-but-unselected until its disposition is explained.
4. For forums, bind the actual source post/thread identity and gate version. A rewritten question is a rendering of that source instance. Recover identity from source evidence and full message hashes, not solely historical IDs, which have changed.
5. For older records with no recoverable seed, set seed_status=unknown and retain source/prompt fingerprints. Do not invent a seed retrospectively and claim it was the generation input.
6. Mark source lineages (spec §5.4: prompts derived from the same original source, such as the same forum post or the same seed) consistently across translations, revisions, dialogue continuations and branches. Group each lineage into one split before training.
7. Import candidate/judgement/pair artifacts separately. Only an active, validated pair contributes eligible-pair credit; held maths and superseded judgements do not.

Minimum records:

- Source: source ID, source lineage, task family, file/row and hash, source status, source document or scenario packet identity.
- Seed: seed ID/version, full JSON, task/subtype, substantive parameters, supplied content/reference identity, language, attitude, register, detail, glossary version, generator/RNG provenance.
- Prompt: logical ID/version, original aliases, complete messages, raw and canonical hashes, realised labels, seed/source binding, review/eligibility status.
- Pair: prompt/prefix identity, distinct candidates and hashes, active judgement/reference versions, actual acceptance and hold reasons, split and dialogue trajectory ID.
- Reservation: instance key, rendering key, worker/run, pending/completed/rejected status and explicit retry lineage.

Idempotent import means that ingesting the same artifacts again changes neither the number of unique prompts nor the number of eligible pairs.

## 3. Differentiation before and after Sol [PG]

Use distinct keys for distinct questions:

| Key | Meaning | Policy |
| --- | --- | --- |
| Source lineage | Prompts derived from the same original source (same forum post, same seed), with their renderings, versions and branches | Controls split assignment (one lineage, one split) and duplicate-alias grouping. |
| Task family | Shared underlying task, scenario or mathematical structure across sources | Controls coverage caps and near-duplicate screening; reuse is allowed within the caps. This is not a ban on all problems using the same operation. |
| Task instance | Actual task, content, givens, entities, operations, constraints and intended answer conditions | Reject unintended reuse even if the persona, language, attitude, ID or generator version changes. |
| Rendering | Task instance plus language and requested user texture | Allows explicitly planned multilingual variants, which remain one source lineage and one task family and do not count as new semantic coverage. |
| Realised prompt | Complete user-visible input/prefix | Catch exact and near duplicates, including Sol converging on the same task from different seeds. |

Deduplication of generated instances uses the instance key plus similarity screening of the realised prompts (spec §5.4).

Canonical semantic keys exclude arbitrary IDs, timestamps, RNG seeds, generator versions and decorative persona details. Include persona properties when they genuinely alter the task, such as relevant prior knowledge or accessibility needs. Preserve numbers, units, negations, operations and constraints during normalisation.

Every seed must carry the substantive preconditions needed for its task:

- Maths: task form, mathematical family and difficulty, actual values/domains/units/operations or theorem assumptions, required deliverable and verification conditions. Cover explanation, proof and checking as well as numerical problems. A reference can be verified in the maths stream; unresolved references remain held for RLHF.
- Instruction following: actual base task and source content, named constraints and values, compatibility checks, checker definitions, and a feasible reference witness when needed. Constraint count alone is not task diversity.
- Summarisation/editing/translation: a concrete source-content packet, its facts and hash, task objective and transformation requirements. Do not leave the source text to unspecified random invention.
- Factual: bound subject/entities/time scope and evidence/answerability conditions; annotate false premises explicitly. Sol must not invent real-world facts to satisfy a random location/date combination.
- Everyday assistance: goal, setting, available resources, relevant constraints and any text or records needed to do the task.
- Safety: concrete intent, requested action, context and a specified benign/harmful/ambiguous distinction. Do not equate suspicious vocabulary with harmful intent.
- Dialogue: scenario and reference/user/world state, linked to the opening seed; all assistant turns are generated by the target model. Branches retain the parent task-instance and trajectory identity.

Content may be drawn from a vetted content database or prepared as a separate bounded content-generation step. If newly generated, validate it and freeze its concrete values before prompt realisation; record that lineage.

Reserve task-instance/rendering keys atomically before sending a batch to Sol. A failed call retries the same reservation; a second worker cannot reserve it independently.

After generation, compare the actual message with the seed:

- Did the required givens, text, constraints and task survive?
- Did language and requested texture survive without changing the task?
- Did Sol add facts or remove context that changes answerability?
- Did distinct seeds collapse into the same request?

Use executable checks for exact values/constraints where possible plus semantic review for meaning. Embeddings or similarity scores nominate potential duplicates; they do not prove equivalence. Translations require source-lineage checking beyond same-language text similarity. Return reason codes and repair a failed rendering without silently changing its seed.

Report diversity across task forms, substantive instances, source lineages, task families, difficulty and constraint combinations, separately from languages/personas. Large Cartesian products are potential capacity, not demonstrated coverage.

## 4. How to calculate the next approximately 500 [PG feeding RLHF]

The owner requested approximately 500 more requests, not a final dataset of 500 accepted pairs.

Planning unit: one additional unique single-turn request or dialogue starting seed. Dialogue follow-ups and reply candidates are separate units and costs. The distinct development demo stays outside this production target. Existing unused forum prompts are already-produced inventory: credit their available coverage before commissioning new synthesis, and report how many are newly selected rather than newly generated.

Keep three separate ledgers:
1. Reviewed unique prompts available by cell (primary purpose × language).
2. Validated eligible pairs available by cell (primary purpose × language).
3. Forecast pair yield and uncertainty for prompts not yet through RLHF.

Use the agreed six-purpose × seven-language grid: 42 cells. Topic/subtype/difficulty and texture are additional constraints, not substitutes for joint cell quotas.

For a proposed pair target N, compute:
- q[c] = agreed purpose share × language share.
- T[c] = jointly integer-rounded N × q[c], with total exactly N and rounded purpose/language margins respected.
- E[c] = deduplicated, eligible, active pair credit, subject to one-pair-per-single-turn policy and the declared dialogue cap.
- A[c] = reviewed, unused prompts already available.
- y[c] = estimated selected eligible pairs per newly processed prompt/trajectory, under the actual response budget and pair-selection policy.
- forecast deficit D[c] = max(0, T[c] - E[c] - y[c] × A[c]).
- initial new-prompt need G[c] = ceil(D[c] / y[c]), where the yield estimate is usable.

E and A must be disjoint: do not count a prompt already credited through E again through A. Rejudging and retries add evidence, not new prompts.

For unmeasured cells, use an explicitly provisional pooled prior with a range, not zero or a claim of measured yield. Report expected and conservative coverage. Dialogue yield needs its own model because several prefixes can come from one trajectory; also enforce independent-trajectory coverage.

The first training size remains open. The planner should therefore produce a size/coverage frontier under the approximately 500-new-request budget and recommend a provisional coverage checkpoint. That checkpoint is a planning scenario, not approval of a DPO run size. Once N is selected for planning, allocate the finite generation budget against joint deficits and yields; show any cells that cannot be filled.

Do not apply the headline percentages directly to the next batch. As an illustration only, adding 350 Greek requests among 500 to the present deduplicated 464 gives 781/964 = 81.0% Greek, not 70%. This is a prompt-count illustration, not an accepted-pair forecast.

Nor can addition alone necessarily rebalance the entire archive. Current deduplicated factual inputs number 132; with 500 added inputs, 132/964 is already 13.7%, above the 10% purpose target before any new factual generation. Labels and eligibility may change, but this demonstrates why we must retain surplus material in the archive while selecting a balanced active training subset.

## 5. Execution sequence for the approximately 500 [PG first]

1. Reconcile aliases, seeds and source lineages; relabel using the frozen glossary. Publish counts and the 17 duplicate groups. Rebuild joint coverage without pretending pairability equals eligibility.
2. Draw usable forum material for genuine gaps, respecting the source cap (Astrovox at most 3% of selected forum prompts). Check against the same registry.
3. Produce a dry-run quota manifest for approximately 500 new request slots, with cell totals, subtype/difficulty allocation, concrete seeds, source coverage, known/estimated yield and a separate dialogue reservation. Do not fill dialogue slots with extra single-turn requests while dialogue work is pending.
4. Generate the first 50 production slots as a validation batch, selected to exercise the single-turn cells and task mechanisms most at risk. These 50 count toward the 500; this is not an extra demo. If dialogue is not ready, keep its slots reserved for later. Broad coverage is more useful here than pretending this small batch alone matches every percentage.
5. Review realised seed fidelity, unique content, language, naturalness and source completeness. Repair systematic defects before using the remaining approximately 450 slots. Limit automatic repair attempts to two per failed slot, then hold/report it; a completion target must not become unlimited calls.
6. Process the remaining slots in bounded batches, rechecking PG counts and realised diversity after each. Use historical RLHF evidence only while RLHF is paused; do not claim new accepted-pair yields have been measured during PG-only work.
7. Present the prompt review page and distribution report for owner review before new reply sampling, in accordance with the master plan. When RLHF resumes, update actual yields and pair deficits; the 500 prompts do not guarantee any particular number of accepted pairs.

The dialogue agent supplies the same seed/source identities and separately reports starting scenarios, raw turns and saved-prefix candidates. Its separate development demo does not consume the approximately 500 production slots.

## 6. Acceptance checks and deliverables

Before collection:
- Reimport all artifacts twice: identical unique counts and no duplicated pair credit.
- All 167 round-2 generated prompts bound to exact saved seeds; unused seed accounted for.
- All 17 identical forum pairs resolve to aliases; candidate history remains accessible.
- Identical substantive seed with a changed ID/version/persona is caught.
- A legitimate changed mathematical instance is distinguishable; a translation stays in the same source lineage and task family.
- Two workers racing for the same instance produce only one reservation.
- Quotas total exactly the requested number; joint cells and margins agree; category frequencies do not depend accidentally on subtype count.
- Compatibility rules reject English/Greeklish before generation.
- Seed-to-message checks catch changed values, missing source text, dropped instructions and two different seeds realised as one request.
- Report held/unresolved legacy identities and semantic-duplicate candidates explicitly.
- No active maths pair credit from pending/superseded verification.

Deliver import reconciliation, seed registry, joint coverage report, provisional 500-slot manifest, review receipts and a before/after distribution view. The executor owns implementation; this audit did not change generator code, rewrite datasets or launch generation.
