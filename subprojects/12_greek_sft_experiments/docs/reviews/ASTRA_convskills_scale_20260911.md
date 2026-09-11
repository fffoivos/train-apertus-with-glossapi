# Astra review: convskills_scale

Date 2026-09-11 13:21 · model gpt-6-astra (asserted from rollout rollout-2026-09-11T13-16-16-01a08ff7-cd28-7c03-ad28-990320de4898.jsonl) · effort xhigh · 4.7 min · prompt 332,475 chars · limit deltas {('codex', '10080'): 1.0} · brief `../docs/reviews/briefs/astra_convskills_scale_full.md` · sample 60 rows of `convskills/v2/reverify/rows_final.jsonl` seed 3

**1. Verdict**

**Accept only after targeted repairs or filtering; the final packet is not clean enough to approve unchanged.** I reviewed all 60 supplied records: S1 14, S2 7, S3 7, S3c 7, S4 12, and S5m 13. The strongest failures are **four S3c rows that lose a material qualifier or condition—4/7, 57.1% of sampled S3c rows**. Separately, two S5m histories make the starting location ambiguous, one S5m plan merely repeats its budget without constraining expenditure, and one reused answer weakens an explicit photography prohibition. S1 recall and S4 habit removal look substantially improved. These are sample findings, not estimates of prevalence across all 3,284 rows. Verification covers the pasted final text, edit logs, and manifest arithmetic; file and web access were unavailable, so I could not execute the verifier, validate hashes or external claims, or independently inspect the pilot report.

**2. Findings ranked by severity**

**HIGH — Four chained edits lose protected meaning despite final verification.**

| Row | Evidence in the final dialogue | Concrete repair |
|---|---|---|
| `S3c_00223` | Removing «απαλλαγή» changes «Η μηδενική απαλλαγή» into «Η πλήρης ασφάλιση». “Full insurance” does not preserve the specific zero-deductible condition. | Preserve that condition without the banned word: «Η κάλυψη με μηδενική δική σου συμμετοχή…». |
| `S3c_00189` | «σε αριθμό που γνωρίζετε ήδη» becomes «στον αριθμό του» in both edited answers. The requirement to use an independently known number disappears. | Use «σε αριθμό που είχατε ήδη πριν από το τηλεφώνημα». Retain it through both edits. |
| `S3c_00441` | «Δεν φαίνεται να υπάρχει μία ενιαία, αυτόματη ημερομηνία λήξης» becomes «Δεν υπάρχει…». Shortening removes the epistemic qualification and strengthens the claim. | Restore «Δεν φαίνεται να υπάρχει…» in both derivatives. Any factual strengthening needs separate justification. |
| `S3c_00205` | «Επιβεβαιώστε **πριν από τη μεταφορά**…» becomes «Επιβεβαιώστε… ποιο είναι αρμόδιο». The timing condition disappears from both derivatives. | Restore «Πριν από τη μεταφορά, επιβεβαιώστε…». |

These are **four distinct failing rows**, not eight independent failures merely because several errors propagate through two answers.

**Disposition:** repair these four rows and inspect existing S3c rows for the same transformations; filter unresolved cases. Protected propositions must represent **conditions, temporal ordering, uncertainty, and scope**, not just surviving nouns and numbers. Check each intermediate answer against its immediate predecessor and the surviving obligations from earlier turns.

**HIGH — S5m sometimes rewards selecting the planted city despite competing conversation evidence.**

Two of 13 sampled S5m rows have a concrete location ambiguity:

- `S5m_00053`: the introduction gives «Κατερίνα, Ιωάννινα», but a later user message says «Μένω τρεις μήνες σε Airbnb στη Νάξο». The target nevertheless asserts «αφού βρίσκεσαι στα Ιωάννινα».
- `S5m_00383`: «Αντώνης εδώ από Κομοτηνή» is followed by «Δουλεύω για καλοκαίρι σε ξενοδοχείο στη Ρόδο». The target assumes departure from Komotini without resolving the distinction between hometown and present location.

**Verified:** the conflicting or differently scoped location statements exist. **Not established:** that either named hometown has ceased to be the user’s home. The defect is treating an ambiguous departure point as settled.

**Disposition:** filter these two rows unless the owner resolves the intended location and repairs the dialogue accordingly. For existing rows, inspect distractors for first-person residence, travel, age, occupation, and family claims. Unrelated questions are useful distractors; unmarked changes to the user’s circumstances need explicit handling.

**HIGH — One S5m budget demonstration is unverifiable from its own answer.**

`S5m_00044` repeats the **€400** limit, then proposes taxis or a rental car, meals, an attraction, an excursion, and alternatively a private driver. It gives **no allocation, total, spending ceiling for transport, or condition binding the booking to the budget**.

That is **1/13 S5m rows, 7.7%, lacking a checkable budget demonstration**. It is **not evidence of an actual €400 overrun**.

**Disposition:** add category caps covering all proposed activities, a total within €400, and a cheaper fallback if the transport quote exceeds its allocation. Merely mentioning the original budget must not satisfy the budget invariant.

**HIGH — A reused answer weakens an explicit user prohibition.**

In `S1_00674`, the user requests a poem saying:

> «δεν τραβάμε φωτογραφίες»

The earlier assistant answer instead says:

> «Φωτογραφίες δεν τραβάμε κρυφά»

This changes “no photographs” into “no secret photographs.” The S1 quote target is correct, but the record contains a separate instruction-following failure in an assistant turn **without an explicit `train:false` flag**.

**Count:** one directly verified example in 60 records; this is not an exhaustive base-answer defect rate.

**Disposition:** repair the poem’s prohibition wherever that source answer is reused. Confirm whether this turn receives training loss. Passing the lane’s final target cannot certify every other supervised answer in the record.

**MEDIUM — The editor changes conversational function, and the claimed quoted-span protection is overstated.**

Three concrete examples:

- `S5m_00411`: the editor removes «πες μου τι κινητό έχεις και ποια εφαρμογή χρησιμοποιείς» specifically to remove assistant self-reference. That was a useful request for information needed to give accurate UI instructions.
- `S1_00731`: the log records «υπεύθυνος και για το .» → «υπεύθυνος και για το εμπόριο ή τα ταξίδια του.» in recalled material. This is substantive reconstruction, not punctuation. The final source and recall agree, but that does **not** establish preservation of the pre-edit answer.
- `S5m_00608`: «Ο Γιώργος μπορεί» → «Μπορείς» removes the name from the target entirely. That is **1/13 S5m targets** not using the name, if using all four planted facts is literally required. It is not, by itself, evidence that the assistant forgot the name.

**Fix:** remove any blanket prohibition on assistant self-reference. Preserve useful conversational acts. Distinguish “final recall matches final source” from “the source span was never changed,” and retain actual before/after text for substantive repairs.

**MEDIUM — Two additional S3c rows change scope.**

- `S3c_00196`: «τρόφιμα που τρώγονται ωμά» becomes «ωμά τρόφιμα». Foods eaten uncooked and all uncooked ingredients are different categories. This broadens the instruction; I am **not** claiming that this wording alone creates unsafe handling.
- `S3c_00076`: avoiding «σκηνοθετημένης πολιτικής εκμετάλλευσης» becomes requiring «μη σκηνοθετημένη χρήση». Avoiding staged political exploitation is narrower than avoiding any staged photograph.

**Count:** two additional rows, **2/7 S3c**, separate from the four HIGH cases.

**Fix:** retain «τρόφιμα που καταναλώνονται ωμά» and «αποφυγή πολιτικής εκμετάλλευσης». Compression should remove elaboration before changing the category or scope of a proposition.

**MEDIUM — Revocation coverage is weaker than the revoked-row count suggests.**

Five of seven S2 rows contain revocation: **71.4% of this sample**.

Only two clearly demonstrate a relevant behavioral change:

- `S2_00473` stops appending «Καλή συνέχεια».
- `S2_00542` subsequently asks the user a direct question.

Three are non-diagnostic:

- `S2_00426` continues without asking the user a question.
- `S2_00852` contains questions spoken by fictional characters; those would already be permissible under the stated `no_questions` interpretation.
- `S2_00673` continues using formal plural.

**These are not revocation violations.** Removing a restriction does not require its opposite. They simply provide weak evidence that revocation was learned.

**Fix:** label revocations as behaviorally diagnostic or non-diagnostic and report both counts. In future construction, use follow-ups that naturally distinguish the two states. Do not mechanically force questions or informal address into existing answers.

**MEDIUM — Template residue and source reuse remain conspicuous.**

- **5/13 S5m introductions** retain the literal template artifact «η/ο»: `S5m_00608`, `S5m_00713`, `S5m_00411`, `S5m_00390`, `S5m_00465`. This concerns unresolved template syntax, not the user’s gender.
- **8/13 S5m targets** quote the user’s limitation verbatim, often with wording such as «ισχύει ο περιορισμός»: `S5m_00383`, `S5m_00044`, `S5m_00535`, `S5m_00198`, `S5m_00713`, `S5m_00411`, `S5m_00465`, `S5m_00785`.
- The identical Vyronas renovation prompt appears in **four records**: `S1_00078`, `S1_00741`, `S4_00054`, `S5m_00785`.
- `S5m_00465` abruptly changes from a retired shopkeeper to someone preparing for Πανελλαδικές whose parents want them to attend a festival. This is conspicuous persona discontinuity, although not a logically impossible biography.

**Fix:** resolve template syntax, express remembered facts naturally, and group dataset splits by source-row identity. Report reuse across the whole training assembly. Reuse here is verified; benchmark leakage is not.

**3. What is good and should not be changed**

- **S1 final-text recall is sound in this sample.** All five counts are correct; all five user-message quotations match; both lists preserve order and summarize; both “what did you say” answers match the earlier final answer.
- **S4’s visible construction is correct in all 12 sampled rows:** both planted context answers contain the tic and explicitly carry `train:false`—**24/24 context answers**. All **12 acknowledgements are non-empty**, and the tic is absent from the acknowledgements and **42 subsequent substantive answers**. Preserve this design and verify its mask survives training conversion.
- **S3 format conversion is generally faithful.** `S3_00313` retains the emergency conditions and service-availability qualifications; `S3_00336` retains the ramp’s conditional recommendation; `S3_00341` preserves the physics explanation.
- Both S3c operation orders occur: **five shorter-then-without, two without-then-shorter**.
- S5m contains actual adaptation, not just repetition: vegetarian food and stock checks in `S5m_00390`, transport without driving in `S5m_00198`, and child-paced activities in `S5m_00692`.
- Keep uncertainty, conditional availability, and spending estimates where present. Do not remove them merely to make answers shorter.
- Do not ban ordinary acknowledgements globally. Only **1/12 S4 acknowledgements** begins «Εντάξει»; this sample does not demonstrate an epidemic of that opener.

**4. Answers to the specific questions in the brief**

**Q1 — Are the FINAL demonstrations correct per lane?**

| Lane | Final population, from manifest | Sample | Audit result |
|---|---:|---:|---|
| S1 | 661 — 20.1% | 14 | **0/14** identified recall/count/order failures. Separate earlier-answer defect in `S1_00674`. |
| S2 | 675 — 20.6% | 7 | **0/7** identified standing-instruction violations. Checked 44 substantive answers under the instruction plus seven acknowledgements. Three revoked rows are non-diagnostic. |
| S3 | 414 — 12.6% | 7 | **0/7** identified material edit failures. Coverage is mostly formatting: five list conversions, one one-item edit, one shortening. |
| S3c | 447 — 13.6% | 7 | **4/7** clear qualifier/condition failures; **2/7** additional scope concerns. |
| S4 | 378 — 11.5% | 12 | **0/12** tic-removal or empty-acknowledgement failures. Visible mask annotations correct in 24/24 planted answers. |
| S5m | 709 — 21.6% | 13 | No demonstrated arithmetic overrun or direct violation of the stated limitation; **1/13** uncosted plan, **2/13** location ambiguities, **1/13** omitted target name. These are different measures, not one combined failure rate. |

For a concrete shortening check, `S3_00293` goes from **58 to 33 whitespace-delimited words: 56.9%**, inside the advertised band. I did not execute the production length checker.

**Q2 — Does the user side read naturally?**

Often it reads as a sequence of independent test prompts. Topic changes are acceptable for retention training, but persona and location changes can undermine the target itself. Source reuse is readily visible, including the four identical renovation prompts above. The packet supports those specific observations, not a precise corpus-wide naturalness or duplication rate.

**Q3 — Is there editor damage?**

Yes, the logs show removal of a useful clarification request and reconstruction of recalled content. They also show successful grammatical repairs. The four HIGH S3c failures are verified on final text, but **their origin cannot generally be assigned to the editor** without pre-edit rows.

In `S3c_00189`, the log indicates that a broken intermediate phrase already existed before the repair. The editor made it grammatical while failing to restore the known-number condition. That is failed semantic recovery, not proof that the editor originally deleted the condition.

**Q4 — Is coverage balanced against the named MultiChallenge-el skills?**

At lane level, the population is reasonably distributed: S2+S4 account for **32.1%**, S3+S3c **26.2%**, S5m **21.6%**, and S1 **20.1%**. Row counts alone do not establish balanced training exposure; long S2 records may contribute much more supervised text.

The important gaps are within lanes:

- **S2:** four `no_questions`, one `end_phrase`, one `bullets`, one `formal_plural`. **Zero sampled `one_sentence`, ≤20-word, or greeklish rows.** Full subtype balance is unknown.
- **Versioned editing:** the sample tests short local chains, not selecting an older version, undoing one change while retaining another, or editing after intervening discussion.
- **Inference memory:** all 13 targets are local leisure plans. Four use “does not speak English” within Greece, where ordinary Greek-language activities can satisfy the condition without much substantive adaptation.
- **Self-coherence:** S1 mostly tests retrieval. Ten of 14 rows are literal quotes or counts; another two reproduce earlier answers. This provides little evidence about reconciling contradictions or updating earlier commitments.
- **Split facts:** visible in **8/13 S5m rows**, supporting that construction change.

This maps the packet to the skill categories named in the brief; it does not establish benchmark coverage or performance.

**Q5 — What wrong habits could it teach?**

The priorities are dropping qualifiers during edits, treating the planted profile as authoritative despite later evidence, and treating budget mention as budget compliance. Lower-priority habits are awkward limitation recitation, unnecessary suppression of clarification questions, and formulaic acknowledgements.

I found **no verbatim list-copying in the two S1 list targets**. Copying during an explicitly requested quotation or format conversion is appropriate.

**Q6 — What changed relative to the pilot?**

Using the brief’s account of the pilot, rather than claiming independent access to that report:

- **Supported as fixed in this sample:** complete records; S4 tic placement and visible masking; non-empty S4 acknowledgements; S1 summary lists; both S3c orders; split S5m facts; corrected vocatives in displayed assistant text.
- **Persisting:** incomplete semantic preservation, conspicuous stitching, template residue, and shallow forms of memory/retention.
- **Newly exposed here:** editor suppression of useful conversational acts, substantive reconstruction of recalled content, weakly diagnostic revocations, and an uncosted plan passing final verification.
- **Not established:** all advertised S2 checker improvements, full subtype balance, three phrasings for every operation, or end-to-end preservation of training masks.

The manifest arithmetic reconciles: **4,000 original attempts → 3,437 generation-accepted → 3,284 final**, an **82.1% final yield**. Re-verification removes **153/3,437, 4.45%**. The manifest’s `attempted` fields sum to 3,437, so they describe its input/re-verification stage rather than the original generation attempts.

The **56 `empty_target` flags**—27 S2, five S4, 24 S5m—need explanation. They do not prove that any empty target survived into the final dataset. Likewise, `agree == verified_final` is not independent evidence of semantic correctness.

**5. Open questions for the owner**

1. What exactly does `empty_target` measure, at which stage, and were all 56 flagged records excluded? Which rejection reasons account for the other removals?
2. What protected propositions were attached to the four HIGH S3c rows, and which final checks passed them?
3. Does the training converter honor `train:false` at token level? Which other assistant turns receive loss, and what is the lane balance by supervised tokens?
4. What is the complete S2 subtype × revoked-status table before and after filtering? How many revocations are behaviorally diagnostic?
5. Are hometown, current location, temporary residence, and departure point represented separately when selecting distractors and judging S5m?
6. Are source-row families grouped across train/evaluation splits and the broader single-turn assembly? Has overlap with MultiChallenge-el been checked?
7. Are pre-edit rows and actual diffs retained, and are time-sensitive prices, event dates, accessibility claims, and source links bound to a recorded verification date?