# Astra review: convskills_prompts

Date 2026-09-09 18:15 · model gpt-6-astra (asserted from rollout rollout-2026-09-09T18-09-05-01a086b7-2961-7450-91a8-c0e468aced08.jsonl) · effort xhigh · 6.9 min · prompt 62,957 chars · limit deltas {('codex', '10080'): 9.0, ('codex_bengalfox', '300'): 0.0} · brief `docs/reviews/briefs/astra_convskills_prompts.md` · sample 12 rows of `data/convskills/smoke/all.jsonl` seed 1

**(1) Verdict.** **Revise before scaling the queued suite.** The skills are worth training, but these samples establish local compliance more convincingly than transferable conversation competence. There is a definite target-construction failure in S1, visible Greeklish violations in S2, and lost information in S3; S4 performs its narrow task well. Of 12 supplied records, nine are complete and carry `verified: true`; at least one of those nine is unequivocally defective despite that flag. Three records are truncated in the paste, so their endings and verification metadata cannot be assessed. These are sample findings, not estimated population failure rates. I inspected the supplied text and computed the counts below; validator code, training masks, baseline evaluations, and literature claims remain independently unverified because they were not supplied and browsing was unavailable.

**(2) Findings ranked by severity**

**BLOCKER — S1 is supervising truncated prefixes as completed request lists.**

- In `S1_00002`, **4/4 list entries are exactly 60-character prefixes**, all ending mid-word: «ελληνόφωνη ερ», «καταλόγους ετεροδ», «που πρέπει να πε», «με χαμηλό μέ».
- The `must` field contains those same fragments. This is an observed defect in the stored target, not merely an inference that the generator misunderstood the task.
- The first entry does not even reach the request to learn the alto part. Prefix overlap and correct list length therefore reward an answer that omits what the user requested.
- `S1_00000` visibly exhibits the same pattern, but its truncated record prevents a full-row assessment.

**Count:** the sole complete S1 list example fails, **1/1**; the other visible list example supplies supporting partial evidence.

**Fix:** separate exact quotation from summarization. For quotations, select complete transcript spans mechanically. For request lists, store complete request units and required meaning, then require coverage, correct order, and no additions. Do not make character prefixes the desired output.

A suitable first item for `S1_00002` would be:

> «Να σου δώσω βήματα για να μάθεις τη γραμμή της άλτο στο “Τζιβαέρι” μέσα σε δέκα ημέρες, χωρίς προηγούμενη γνώση παρτιτούρας.»

That answers the request-list question; copying its opening biographical sentence does not.

**BLOCKER, conditional on the training configuration — Planted failures must be context, not positive training targets.**

Each complete S4 row contains two assistant messages with the deliberately unwanted tic: **six messages across three rows**. If every assistant turn receives ordinary SFT loss, those six messages positively train the behavior the later turns are supposed to suppress. They represent **6/20 assistant messages in the visible S4 sample**, although that is not their token-weight share.

The sample does not expose loss masks, so **I have not established that this training bug exists**. It must nevertheless be resolved before release.

**Fix:** explicitly mask the planted S4 answers and other context-only turns. Preserve them in the context so later answers can attend to them. Supervise the intended acceptance and subsequent compliant answers. Inspect the actual collator output, including after packing and truncation; a JSON-level convention is insufficient. If clean source answers are also desired as replay, weight that replay deliberately.

**HIGH — S2’s “compress, never violate” instruction can reward incomplete or distorted answers.**

`S2_00002` passes its surface constraint: the acceptance and nine subsequent answers contain **15–19 whitespace-delimited tokens each; 0/10 exceed 20**. That does not establish answer adequacy.

Concrete problems:

- The commercial-calls answer says human calls are permitted unless an objection was registered «στο μητρώο». The longer answer in `S4_00002` also includes objection made directly to the advertiser: «ή έχει δηλώσει ειδικά στον διαφημιζόμενο ότι δεν τις επιθυμεί». **The compressed answer loses a qualification present in your own comparison answer.** I have not independently adjudicated the applicable law.
- The meal-plan answer is a menu sketch followed by «έως 3€/μερίδα, δύο μάγειρες». The arithmetic is compatible with the ceiling—270/(18×5) = €3—but repeating the ceiling does not establish ingredient-cost feasibility or a preparation plan.
- That answer has no finite verb and uses constructions such as «γάλα/αράπικο-φιστίκι». This is observable tension with the promised natural, complete-sentence voice, and it creates an incentive to pack information into whitespace-efficient compounds.

**Fix:** validate content separately from length. Before generation, assign each task a small set of essential facts and qualifications. Use tasks that can be answered adequately within the active restriction. Where that cannot be done, train a truthful concise statement of the limitation or an explicit user-authorized relaxation. Do not teach fabricated completeness.

This does **not** justify routinely dropping the user’s restriction: most training examples should satisfy both content and form.

**HIGH — `verified` is much weaker than “correct,” and two observed failures expose missing checks.**

- `S2_00000`: **2/6 fully visible post-acceptance answers contain Greek-script characters** despite the Greeklish instruction: «κιτrinismena» contains Greek κ, ι, τ; «IΧ» contains Greek Χ. Including acceptance gives 2/7. The row’s verification flag is not visible, so these are observed output failures, **not proven validator false positives**.
- `S3_00001`: the simplified answer removes both «με συμβατό βύσμα» and «επαρκή ισχύ» from charger selection. The result is shorter—98 versus 125 whitespace-delimited words, excluding list numbers—but omits two useful selection requirements. This is **1/1 child-simplification example with those omissions**, despite `verified: true`.

The other mechanical checks have predictable limitations:

| Check | Wrong answers it can accept | Correct answers it can reject |
|---|---|---|
| Required substring / overlap | Correct quote embedded in a contradictory answer; wrong attribution; incomplete summary | Faithful paraphrase when quotation was not requested |
| Count match | Expected numeral appears in an unrelated date or alongside another count | Number written in words; an explicit “before this message / including this message” distinction |
| Sentence punctuation | Run-on punctuation avoidance | Greek abbreviations, decimals, URLs, quoted punctuation |
| No questions | «Πες μου περισσότερα.» still solicits a reply | A quoted question when quoting is the task |
| One bullet / bullets present | One bullet containing several unrelated items; bullets with altered facts | Valid alternative list syntax |
| Forbidden substring | Inflected or paraphrased habit survives | A forbidden standalone word occurring inside a different word |
| Latin-only output | English or meaningless Latin strings | Legitimate quoted text or URLs, if the instruction permits exceptions |

**Fix:** retain fast mechanical checks, but give them precise names and add separate semantic, language-quality, and factuality results. For Greeklish, use Unicode script checks plus Greek-language/transliteration review. For S3, check protected facts and requested transformations. Validate the **final corrected artifact** again; freeze verbatim transcript spans against the Greek correction pass.

**HIGH — The described instruction lifecycle is too narrow to establish retention and selective updating.**

All three visible S2 instructions occur after one exchange. All three S4 corrections follow two tic-bearing answers and use the same construction:

> «Κόψε το «…», το γράφεις κάθε φορά.»

No completed revoke sequence is visible. The only complete S2 record, `S2_00002`, explicitly has `revoked: false`; the other two are truncated. This does not disprove the planned 50% revoke rate, but provides no evidence that revocation works.

**Fix:** add controlled variations before generating thousands of rows:

- Instructions embedded in an ordinary request, issued later, or phrased indirectly.
- One-turn exceptions followed by automatic resumption.
- Two standing instructions, followed by revocation of only one.
- Replacement instructions and explicit expiry conditions.
- Quoted instructions and pasted documents that should not change the active instruction.
- Earlier assistant commitments that implement a user preference, followed by delayed tests of that commitment.

Assistant promises should establish conversational expectations, not a new authority capable of overriding later user instructions.

**HIGH — Reused content order and simple edit templates create substantial shortcut and evaluation-leakage risks.**

The exact five-request sequence—Athens cultural centres → borehole water → greens → tutoring hours → uphill driving—appears in `S1_00000`, `S2_00000`, and `S4_00000`. That reuse is directly visible; whether it reflects consecutive indexing through the source set is an inference.

Also, **2/3 S3 examples are `to_list`**, both using «Ξαναπές το σε κουκκίδες.» They primarily require layout conversion. Neither demonstrates choosing among versions, preserving a previous edit, or editing after a distracting exchange.

**Fix:** split the 853 source families into train/development/test **before** constructing dialogues, keeping related paraphrases and derived variants together. Vary topic ordering, requested positions, correction locations, and instruction phrasing. Maintain coherent user facts in some dialogues rather than relying entirely on unrelated requests.

Add counterfactual pairs: identical final request, but one earlier fact, instruction, or selected version differs, requiring a different answer. This makes reading the transcript necessary.

**HIGH — The source pool shows artifacts that a Greek correction pass cannot reliably repair.**

The claim that the selected base answers do not have distorted shapes needs another audit:

- `S1_00002` contains the repeated acoustics metaphor «σαν κύματα σε θάλασσα» and «Η θάλασσα της αντήχησης». The same answer appears in `S2_00002`.
- The hospital answer in `S1_00002` and `S4_00002` contains long lists stripped of useful separating punctuation: «φροντίδα τραύματος μπάνιο διατροφή ενυδάτωση δραστηριότητα…».
- The borehole answer in `S1_00000` and `S4_00000` introduces «Η ΑΑΔΕ δεν είναι η αρμόδια αρχή…», although neither visible user request mentions ΑΑΔΕ.
- `S3_00002` introduces the unrequested example date «15 Ιουλίου 2026», which the edit faithfully preserves.

These are observable anomalies. **A leftover constraint from the source instruction-following task is a plausible explanation, not a verified provenance finding.**

**Fix:** audit each selected answer against the plain user request actually retained. Remove inherited lexical/format constraints and irrelevant material before building dialogues. Check substantive claims separately; grammar correction cannot establish truth. Preserve source IDs and review decisions so contamination is traceable across lanes.

**MEDIUM — The voice and acceptance rules are unnecessarily rigid.**

All three S4 acceptances avoid both the stopped phrase and «δικό μου λάθος», which is good. However, «τη συγκεκριμένη καταληκτική φράση» and «αυτή την καταληκτική διατύπωση» sound more administrative than conversational.

The global prohibition on self-reference also needs an exception for the suite’s core tasks: “what did you say?” and grounded acknowledgement require references to the assistant’s earlier output.

**Fix:** prefer concise, ordinary Greek, with controlled variety: «Δεν θα το ξαναγράφω.» or «Θα το παραλείπω.» Allow necessary conversation references and specific error acknowledgement. Avoid turning a stylistic preference against one apology phrase into a general suppression of accountability.

**(3) What is good and should remain**

- **Keep transcript-grounded targets.** `S1_00001` correctly quotes the entire first user request, including its later sentences. That is **1/1 complete `first` example correct**, and it directly addresses false claims of unavailable context.
- **Keep sustained follow-up turns.** S2’s duration is useful for a failure reported to emerge after 2–4 turns. Randomize distance rather than shortening everything.
- **Keep the narrow S4 intervention.** Across all three S4 dialogues, **0/14 post-correction assistant answers repeat the prohibited phrase**, including three acceptances and eleven substantive answers. This verifies literal suppression in this sample, not general suppression of all variants.
- **Keep faithful formatting edits.** `S3_00000` and `S3_00002` preserve the supplied answer’s content while introducing bullets. Their underlying factual content requires separate assessment, but the transformations are useful.
- **Keep ordinary Greek topics and the combination of structural checks with language review.** The architecture is valuable once “structurally compliant,” “semantically adequate,” and “factually checked” are separate judgments.
- **Keep brief acknowledgement without compulsory apology.** A style preference is not automatically an error requiring confession.

**(4) Answers to the six questions**

**1. Skill or template?**

Both are plausible, but the current sample cannot demonstrate transfer. It clearly supplies useful local behaviors; it also offers strong shortcuts through fixed positions, repeated phrasing, repeated source sequences, and shallow transformations.

S1 needs arbitrary positions, assistant-message retrieval, repeated topics with different answers, corrections to earlier facts, and questions whose answer lies beyond the opening sentence. S2 needs held-out paraphrases and limits other than 20. S3 needs selection among versions. S4 needs indirect complaints, non-final tics, and cases distinguishing a habitual phrase from a legitimate requested quotation.

The decisive evaluation should change the relevant history while holding the final user message constant.

**2. Are the mechanical targets right, and are the formats natural?**

Exact copying is right for «Αντίγραψε αυτολεξεί…». It is usually unnecessary for «Ποια ήταν τα αιτήματά μου;». Sixty-character fragments are wrong for either a complete quotation or a summary.

“Number of questions” is underspecified: one user message can contain multiple questions, or requests expressed entirely as imperatives—as `S1_00001` demonstrates. It also leaves inclusion of the current question ambiguous. Prefer an explicit task such as:

> «Πόσα μηνύματα σου έστειλα πριν από αυτό;»

For S3, distinguish «Κράτησε μόνο το σημαντικότερο βήμα» from «Συμπύκνωσε όλα τα βήματα σε μία κουκκίδα». Those require different targets. Greek bullet lists are natural; chopped prefixes and word-budget-driven compounds are not good defaults.

**3. What does the suite miss relative to MultiChallenge and the literature?**

Using the four axes as described in the brief:

| Axis | Present contribution | Main missing capability |
|---|---|---|
| Instruction retention | S2 and S4 | Scope, competing instructions, exceptions, partial updates |
| Inference memory | Little direct coverage | Applying earlier user facts without being explicitly asked to retrieve them |
| Reliable version editing | S3 single-step edits | Multiple versions, cumulative constraints, targeted changes to older versions |
| Self-coherence | Some S1 retrieval | Tracking prior claims and commitments; warranted correction versus false accusation |

**Best new lane per row: inference memory with explicit fact updates.** For example, establish a budget and mobility limitation, insert unrelated exchanges, then request a plan without restating either constraint. Pair it with a dialogue where only the budget changes. The target should preserve the mobility constraint and use the updated budget.

**Best variation within an existing lane: chained S3 edits.** Generate a draft, remove X, shorten it, then change one detail while retaining the removal of X.

The literature argument needs narrower wording. A reported multi-turn degradation does not establish that this recipe repairs it; an attention-decay account does not validate fixed-length training; and “no intrinsic self-correction at ≤13B” should not be treated as a universal parameter threshold. Grounded feedback is a defensible design choice without that sweeping claim. DITTO, sycophancy, and abstention references also do not make S4 phrase suppression evidence of general repetition control, resistance to false correction, or calibrated abstention. Exact papers and experimental settings are needed to authenticate those connections.

**4. Revoke turns, acceptances, and “no δικό μου λάθος”?**

Revocation is the right inclusion. Add selective revocation and temporary exceptions. An unrestricted answer may still naturally be short, so “exceeds 20 words” must not become the definition of successful revocation.

Acceptances should usually be short and already compliant:

- One sentence: «Θα απαντώ με μία πρόταση.»
- Maximum 20 words: «Θα κρατώ τις απαντήσεις μου έως 20 λέξεις.»
- Formal plural: «Θα σας απευθύνομαι στον πληθυντικό.»
- Greeklish: «Tha apanto se greeklish.»

When the instruction accompanies a substantive request, often answer the request directly under the new instruction rather than inserting a separate acceptance.

Avoiding automatic «δικό μου λάθος» is sensible. Prohibiting grounded acknowledgement is not. In S5, include both real errors and false accusations, with transcript evidence determining the response.

**5. Is 7,000 the right size, and should S5/S8 move forward?**

There is no supplied evidence establishing 7,000 as the right dose. The reported 63.7% Greek IFEval score measures a different capability and does not determine a multi-turn training budget.

Dialogue counts also hide a large imbalance. Assuming seven later S2 requests, an acceptance, and an additional revoke response in half the dialogues, the plan produces approximately:

- S1: 2,000 new assistant answers.
- S2: 17,000.
- S3: 2,000.
- S4: 4,000, assuming three later requests plus acceptance.

Thus S2 supplies **about 68% of new assistant answers**, before accounting for lengths, masks, or sampling weights.

I would first generate a corrected **1,000-dialogue pilot**, as a pragmatic allocation rather than an evidence-derived optimum:

| Component | Dialogues |
|---|---:|
| S1 | 150 |
| S2 | 250 |
| S3, including chained edits | 250 |
| S4 | 75 |
| Inference memory / fact updates | 150 |
| S5 grounded self-observation | 125 |
| **Total** | **1,000** |

Pull S5 forward because the brief reports a direct self-observation deficit. Pull **S8 evaluation** forward to detect identity regressions; substantial S8 training is not justified without its design and failure evidence.

Use held-out, source-disjoint evaluations and training ablations to allocate the remaining budget. Report supervised tokens and per-skill exposure, not just dialogue totals.

**6. Could the suite damage existing capabilities?**

Yes, plausibly:

- Supervised planted turns could strengthen unwanted tics.
- Heavy short-answer exposure could reduce completeness without a user-imposed limit.
- Frequent acceptances could add unnecessary preambles.
- Greeklish could leak into ordinary Greek answers.
- Unconditional persistence could become failure to obey later revisions.
- Weak simplification targets could teach deletion of important qualifications.
- Repeated identity and voice boilerplate could leak into unrelated answers.

These are **risks, not observed training regressions**. Test ordinary unconstrained answers, existing Greek IFEval, Greek-script defaults, identity answers, false corrections, and post-revocation behavior alongside the targeted conversational metrics.

**(5) Open questions for the owner**

1. Can you provide the complete `S1_00000`, `S2_00000`, and `S2_00001` records, including their endings and verification metadata?
2. What are the exact target-building and validator functions—especially the apparent 60-character S1 slicing—and which checks produce `verified`?
3. Which assistant tokens receive loss? Does the final packed training batch preserve the intended masks and relevant conversation history?
4. Were the 853 answers reviewed against the plain prompts after removing their original constraints? Are source-family splits performed before dialogue generation?
5. Does generation have retrieval access for its citations? Which claims and links are actually verified, and by whom?
6. What are the exact S5/S8 prompts, model revisions, generation settings, and correction-pass rules?
7. What denominators, rubrics, uncertainty estimates, and held-out splits underlie the reported 68%, 35%, 26%, and 63.7% results—and which exact papers support the literature claims?