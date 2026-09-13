# Astra review: astra_ds_convskills

Date 2026-09-13 10:36 · model gpt-6-astra (asserted from rollout rollout-2026-09-13T10-28-09-01a099aa-9776-7862-bcbf-02e1b7ed467a.jsonl) · effort xhigh · 8.1 min · prompt 307,431 chars · limit deltas {('codex', '10080'): -78.0} · brief `docs/reviews/briefs/astra_ds_convskills.md` · sample 60 rows of `data/convskills/v2/final/rows_final.jsonl` seed 3

1) **Verdict: keep convskills, but change its coverage and verification before expanding it.** The sample supports keeping its basic retrieval, instruction persistence, and tic-removal exercises: I found no visible retrieval mismatch in the 14 S1 targets, and all 10 S4 targets omit the prohibited tic. It does **not** support treating the suite as sufficient training for version editing, inference memory, or resisting false corrections. There are concrete semantic defects, substantial template concentration, and an unreconciled row-count discrepancy. The reported IFEval and picky-user gains justify controlled ablations, not automatic continuation at ×2 or a heavier finishing pass. Treat the already-trained R3 artifacts as completed: retain them and attach these notes; apply fixes to queued successors.

My evidence is the pasted sample. I counted 60 distinct row IDs: S1 **14**, S2 **9**, S3 **9**, S3c **4**, S4 **10**, S5m **14**. **33/60 records are cut off before their JSON record ends**, although many still show enough context to check the target. This is a limitation of the supplied extract, not evidence that the source JSONL is corrupt. Tool access failed, so I could not inspect the local artifact, training code, evaluation receipts, or external sources. Public-dataset recommendations below are therefore provisional. Counts are descriptive sample findings, not estimated corpus-wide failure rates.

2) **Findings, ranked by severity**

**BLOCKER — The dataset manifest does not reconcile.**

The six reported lane counts sum to:

`661 + 675 + 414 + 447 + 378 + 709 = 3,284`

That exceeds the stated **2,851** final rows by **433**. At ×2, the difference becomes **866 row exposures**: 6,568 versus 5,702.

This could be pre-filter versus post-filter accounting, overlapping labels, or a stale brief. I cannot identify which.

**Concrete fix:** before allocating further generation, produce a manifest from the exact final artifact: file hash, unique IDs, exclusive primary-lane counts, secondary labels if applicable, removals by reason, and actual sampler weights. Report input tokens and loss-bearing assistant tokens per lane. Do not allocate the next batch from the unreconciled counts.

**HIGH — A personal-memory target converts an implication into an asserted fact.**

In **S5m_00078**, the user introduces herself as:

> «είμαι η/ο Ελένη από Πάτρα»

Later:

> «Θα ταξιδέψω από Βρυξέλλες»

The target asserts:

> «αφού τώρα μένεις στις Βρυξέλλες αλλά είσαι από την Πάτρα»

Travelling from Brussels does not establish residence there. The target chooses a plausible interpretation and presents it as remembered fact.

**Count:** **1/14 S5m targets, 7.1%,** contains this clear unsupported residence assertion. This is not a wrong-city rate for the entire lane.

**Concrete fix:** represent personal facts with their supporting turn, subject, scope, and certainty. Distinguish residence, origin, temporary location, departure point, and another person’s location. Here, ask which city the user means, or explicitly condition the itinerary on Brussels. Add matched examples where the same departure statement accompanies different residences.

Importantly, do not ban legitimate contextual inference: **S5m_00190** explicitly says «σπουδάζω στη Λυών», which provides substantially stronger support for a local Lyon plan.

**HIGH — “Verified” does not establish preservation of the user’s meaning.**

Two visible examples expose different gaps:

- **S1_00674**, an earlier assistant turn: the user requests «δεν τραβάμε φωτογραφίες». The poem changes that to «Φωτογραφίες δεν τραβάμε κρυφά». A prohibition on photography becomes a prohibition on secret photography. The final S1 quotation target can be correct while an earlier assistant answer violates its own instruction.
- **S3c_00450**, final target: replacing «λιμάνι» with «στενό» satisfies word avoidance but introduces a different geographical feature. The result says the ship departs «λίγο πριν κλείσει το στενό». This row explicitly has `verified_final: true`.

**Counts:** one identified instruction-weakening error in an earlier assistant turn among the 60 rows; **1/4 S3c targets, 25%,** has this semantic substitution defect. These are separate checks, not an aggregate dataset error rate.

**Concrete fix:** validate every assistant turn that actually receives loss, against its own conversation prefix. For transformations, check protected propositions—negation, quantities, entities, conditions, and causal relations—alongside formatting. For the ship example, use a weather-based ending without inventing a strait. Preserve the rest of the text.

Regex checks remain valuable; their certification should say exactly what passed, such as `forbidden_word_absent`, rather than implying complete task correctness.

**HIGH — The suite concentrates on easy proxies for the missing capabilities.**

The sample’s task coverage is narrow:

| Subset | Counted coverage | Missing from those examples |
|---|---|---|
| S3 | **7/9** list conversions, one single-item rewrite, one shortening | Actual ambiguity resolution or information-seeking clarification |
| S3c | **4/4** combine shortening and word removal; two examples in each order | Named versions, branches, rollback, selective edits across intervening turns |
| S5m | **14/14** leisure plans: nine weekends, three day trips, two Saturdays | Memory applied to ongoing documents, commitments, budgets after spending, or operational decisions |

Across **S3 + S3c, 0/13** examples exercise genuine clarification. Calling S3 “clarification” overstates what these rows teach.

There is elementary revision training, so “no version-editing lane” should not mean “no rewriting whatsoever.” The missing capability is maintaining and selectively changing a document state. Likewise, S5m contains contextual inference, but not a systematic inference-memory curriculum.

**Concrete fix:** retain a smaller foundation of these exercises and redirect expansion toward explicit version state, evidence-bound inference, correction adjudication, and scoped cancellation. Do not generate more city/name/budget substitutions as the main response to the 5% version-editing and 12% inference-memory results.

The flat unseen-constraint IFBench result is **consistent with** narrow transfer. It does not prove that convskills caused it.

**HIGH — Shared donor content requires family-level splitting and exposure accounting.**

The same seaman-at-Psara story prompt appears in at least four distinct rows:

**S5m_00387, S3c_00450, S4_00205, S2_00673.**

This is verified donor reuse, not four duplicate full conversations. Reuse can be intentional, especially for controlled transformations, but row-ID splitting will not prevent related content from crossing evaluation boundaries.

There is also a potentially large mismatch between row weights and skill supervision. In the five S1 counting examples—**S1_00647, S1_00333, S1_00165, S1_00498, S1_00193**—there are **19 preceding assistant answers and five counting targets**. If all unmasked assistant messages receive loss, **19/24 assistant messages, 79.2%,** teach other tasks. The token imbalance would likely be larger, but I did not measure it.

**Concrete fix:** assign donor pools to splits before constructing conversations; keep all derived versions and both-order variants together. Track donor IDs and repeated supervised spans. Explicitly choose which turns teach each lane and verify the resulting token labels. If preceding answers are already masked, document that—the supervision concern would then be resolved.

**Not verified:** train–test leakage, broken masking, or the actual effective dose. These should not be reported as established failures.

**MEDIUM — A relative-date target depends on missing temporal context.**

**S5m_00373** answers “next Saturday” with:

> «το επόμενο Σάββατο, 12 Σεπτεμβρίου»

No reference date appears in the visible conversation. On the review date, 13 September, that date is already past. It could have been correct when generated.

**Count:** **1/14 S5m targets, 7.1%,** visibly depends on an unprovided date anchor; this is not a proven generation-time calendar error.

**Concrete fix:** serialize the reference date and timezone into the training input and check date arithmetic, or leave the itinerary undated. Event-specific recommendations also need dated evidence. Separately, **S5m_00674** proposes a museum visit without explicitly accounting for its admission cost; check cost coverage, not just whether the listed numbers sum to €120.

**MEDIUM — Generated profile boilerplate retains obvious artifacts.**

Four S5m rows contain unresolved template notation or malformed city inflection:

- **S5m_00078:** «είμαι η/ο Ελένη»
- **S5m_00452:** «Είμαι η/ο Μαρία, από Βόλος»
- **S5m_00670:** «Είμαι η/ο Μαρία»
- **S5m_00190:** «Γεια, Νίκος εδώ από Βόλος»

**Count:** **4/14, 28.6%,** contain at least one such artifact. This is a generated-input quality finding, not an assistant-target error rate.

**Concrete fix:** repair profile templates before rendering conversations. Preserve authentic Greeklish, missing accents, and informal user language; do not confuse those useful variations with unresolved generator placeholders.

3) **What is good and should remain**

- **S1’s observable retrieval targets work.** All five counting targets match the visible preceding user-message counts; the five quotation targets reproduce the requested messages on inspection; the two ordered lists and two recalled answers match their antecedents. **0/14 visible retrieval mismatches.** Keep these exercises, while varying distance and competing referents.
- **S4’s basic construction is sound.** All **20/20 planted assistant turns** visibly carry `train: false`, and **10/10 final targets** omit the prohibited tic. Preserve this design, subject to verifying that the loader honors the flags.
- **Revocation is represented.** **S2_00473** drops «Καλή συνέχεια» after cancellation. **S2_00339** exceeds 20 words only after the user withdraws that limit; its five intervening task answers remain within the limit. Neither final answer should be flagged as a persistence failure.
- **Both operation orders are useful.** S3c includes two examples of each order in this sample. Preserve the paired design and expand the operations.
- **Several transformations preserve substance well.** **S3_00341** converts the satellite-latency explanation into bullets without losing its central distinctions. **S3_00203** preserves the lullaby’s stanza structure.
- **The editor provides real value.** **S5m_00065** corrects «έχω μαζί ένα παιδί» to «έχεις μαζί ένα παιδί» in the assistant’s reference to the user. Keep guarded Greek polish and its change log.

Two traps to avoid in automated review: **S2_00542** ends with a follow-up question, but its truncated history prevents checking whether the earlier prohibition was revoked. **S2_00852** contains questions inside the requested fictional dialogue; those are not automatically questions directed back to the user.

4) **Answers to the brief**

**Keep/change/remove by lane**

| Lane | Disposition for queued data | Concrete direction |
|---|---|---|
| S1 | **Keep; change coverage and dose** | Longer retrieval distances, competing versions, exact suffix copying, missing-reference cases, user versus assistant attribution |
| S2 | **Keep; expand** | Multiple simultaneous constraints; scoped exceptions, replacement and cancellation; genuine stop instructions; quoted instructions that should not become active |
| S3 | **Keep a smaller portion; relabel** | Call it immediate revision. Add a separate clarification lane with necessary-question and sufficient-information controls |
| S3c | **Keep; expand substantially** | More operation pairs and longer chains; preserve propositions; include edits where order changes the correct result |
| S4 | **Keep at modest dose** | Unseen tics and paraphrases; distinguish unwanted assistant habits from permitted quotation or requested dialogue |
| S5m | **Change substantially** | Evidence-bound facts, temporal updates, multiple people, competing locations, and diverse downstream tasks |

**Remove no whole lane on this evidence.** Repair erroneous labels and reduce redundant expansion. There is insufficient evidence to remove convskills from completed R3 retrospectively.

**New lanes to invent**

**A. Version editing with an executable preservation oracle.** Store an immutable starting document and an explicit edit sequence. Construct the expected next version programmatically. Require:

`output == apply_permitted_edits(selected_base_version)`

Also verify that all protected text remains byte-identical under a declared serialization convention. A length or similarity threshold is insufficient.

Include named-version selection, editing an older version, undoing one change, preserving a previous change, distractor turns, and requests that change only one occurrence. In Greek, declare the permitted span broadly enough for necessary agreement changes; do not allow unconstrained “polish” outside it. Freeze the source text after its initial polish.

**B. Inference memory with evidence and abstention.** Generate facts and decisions from a controlled state model: remaining budget after purchases, available meeting times, eligible transport options, or commitments attached to different people. Store supporting turns and valid deductions. Include underdetermined cases where clarification or a conditional answer is correct.

Evaluate actual decisions, not whether the response repeats the name, city, constraint, and budget.

**C. Premise and correction handling.** Balance four cases: valid correction, invalid correction, unresolved claim, and explicitly fictional/counterfactual premise. Cross these with user confidence and whether the assistant’s previous answer was correct.

Use verified source packets or executable facts. Reward changing an incorrect answer and maintaining a correct answer under unsupported pressure. Avoid a dataset where “Όχι” is the shortcut to success.

**D. Stop, cancellation, and exact-output boundaries.** Add scope-sensitive withdrawal, “stop this task,” exact tail copying, and output-only edits. Define the expected behavior for genuinely empty responses at the application level; stopping a task and producing an empty message are different targets.

**Public datasets worth considering**

These are design recommendations from prior knowledge, **not live-verified release or license assessments**. The links are starting points for owner verification.

| Candidate | Suitable use | Adaptation and checks |
|---|---|---|
| **Parrot, specifically the multi-turn instruction-following project** | Constraint-carrying dialogue patterns | Pin the exact project/release first. Reconstruct executable state checks; do not assume its original answers or labels satisfy the Greek contract |
| **MT-Bench-101 style** | Broader dialogue structures and capability coverage | Use the task taxonomy to create fresh Greek training scenarios. Keep original benchmark items and translations out of training |
| **[UltraChat](https://github.com/thunlp/UltraChat), including the [H4 derivative](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k)** | More natural continuation and topic development | Select complete conversations, regenerate targets under explicit checks, and control repeated content. Weak replacement for exact version-state training |
| **[LMSYS-Chat-1M](https://huggingface.co/datasets/lmsys/lmsys-chat-1m)** | Realistic user phrasing, corrections, and difficult follow-ups | Use appropriately licensed conversation structures as seeds; review privacy/provenance and replace unreliable assistant answers. Logs are not gold labels |
| **[LongMemEval](https://github.com/xiaowu0162/LongMemEval) / [LoCoMo](https://github.com/snap-research/locomo)** | Memory-task design and longer-context evaluation | Borrow task mechanisms; create fresh facts and conversations with known evidence. Preserve benchmark separation |

My priority would be **invented, verifiable version and inference tasks first**, then selected public dialogue structures for diversity. Bulk translation of generic multi-turn chat is unlikely to close these particular gaps.

Every adaptation should receive the required Greek polish pass, followed by rerunning its semantic and programmatic checks. Recheck Greek word boundaries, inflections, prohibited forms, dates, and currencies after translation.

**Dose in the mix versus a finishing pass**

The supplied results do not establish an optimum. R3’s IFEval improvement over arm B is **4.1 percentage points**; the Greek pass adds **3.8 points**. Neither isolates convskills. The false-claim outcome also confounds the suite with the correcting set.

For the next experiment:

1. Compare **no convskills**, **current convskills**, and **revised convskills**, using the same starting checkpoint and matched training budgets.
2. Compare the revised suite at the current effective dose and **half that dose**. Treat the lower dose as a proposed ablation, not a proven optimum.
3. Compare mixed placement with late placement at equal suite exposure. Account for learning-rate differences; otherwise call the result a placement-plus-schedule comparison.
4. Test the finishing-stage interaction separately: neither addition, suite only, correcting set only, both.

Replace removed tokens with the same neutral replay pool. Report loss-bearing tokens per lane, not merely row multipliers. I would **not increase finishing-pass dose** before these comparisons.

**Acceptance checks before queued data advances**

- Reconciled artifact manifest and reproducible sampling.
- Token-label inspection proving that masked turns receive zero loss, intended targets receive loss, and target answers are not accidentally included in evaluation inputs.
- **100% pass on deterministic teacher-target checks**, evaluated after final polish: exact edits, counts, copies, scope transitions, arithmetic, and prohibited forms.
- Mutation tests proving the validators reject wrong-base versions, unauthorized edits, lost negations, stale facts, and incorrect cancellation.
- A blinded, stratified semantic audit of **200 examples per changed/new lane**, or all examples if fewer. Proposed gate: zero unresolved HIGH defects and at least 98% task correctness, with uncertainty reported.
- Filter reports showing input, repair, rejection, and retained counts by difficulty: context distance, constraint count, version depth, ambiguity, and correction type. Never silently remove judge-disfavored hard examples.
- Source or executable evidence takes precedence over judges. Use qualified human adjudication or a demonstrably adequate checker; model/vendor names alone do not establish the owner’s “no weaker checker” requirement.

**A/B read-out that would justify adoption**

Use fresh Greek task families, donor-disjoint splits, paired evaluation, and preferably three training seeds. Measure both fixed-history responses and full rollouts where earlier model errors remain in context.

Proposed preregistered success criteria:

- **Version editing and inference memory:** each improves by at least **10 absolute percentage points** over the current-suite control, with paired confidence intervals excluding zero.
- **Existing useful skills:** preserve strict instruction following, redirects, request honoring, and tic suppression.
- **Regression gates:** false-correction handling, premise accuracy, stop compliance, exact tail copying, MGSM, and MATH must satisfy a predefined non-inferiority margin—suggested starting point **2 percentage points**, with sufficient evaluation size to assess it.
- Report all-constraints-pass and whole-dialogue success, not only average per-constraint accuracy.
- Require improvement on held-out constraint families before claiming general instruction-following transfer. Another IFEval gain alone would not resolve the flat IFBench result.

The reported mathematical and coherence regressions are reasons to include those gates. They are not evidence that convskills specifically caused them.

5) **Open questions for the owner**

1. Are the six lane counts pre-filter counts, overlapping labels, or from a different artifact? What is the final file hash?
2. Which assistant turns receive loss, and what do the actual token masks look like after packing and truncation?
3. What do `verified` and `verified_final` certify? Which checks cover semantics, and which only inspect strings?
4. How many unique donor conversations remain, and are donor families shared with any evaluation set or its Greek adaptation?
5. What did each filter remove by difficulty, and can you provide Astra review decisions and override logs?
6. Were reference dates and source-retrieval evidence available to generators but omitted from the serialized training input?
7. What are the effective token doses, exact Greek-pass ingredients, benchmark sample sizes, and uncertainty estimates?
8. Which artifacts are completed versus queued, and which common checkpoint can support the controlled comparisons above?