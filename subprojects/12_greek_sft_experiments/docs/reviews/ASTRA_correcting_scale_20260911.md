# Astra review: correcting_scale

Date 2026-09-11 11:58 · model gpt-6-astra (asserted from rollout rollout-2026-09-11T11-49-01-01a08fa7-eac1-7f53-889b-b3815f29cc67.jsonl) · effort xhigh · 9.4 min · prompt 374,658 chars · limit deltas {('codex', '10080'): 4.0} · brief `../docs/reviews/briefs/astra_correcting_scale.md` · sample 60 rows of `robustness/correcting/scale/rows/rows.jsonl` seed 2

**1. Verdict**

**The parity fix landed, but I would not run the unchanged generator and assembler for the queued 1,500 dialogues.** The clearest HIGH defect is that eligibility checks reject requested task content—questions in scripts, quizzes, and games—while retaining summaries of that content. Retained targets also contain a wrong self-report, an unsound monthly-to-weekly budget conversion, and unmarked assumptions about user facts. I counted **60 rows, 426 assistant turns, 361 supervised targets, 21 masked plants, and 44 other rejected targets**. Retained recoveries and misquote recoveries are **12:12** in this sample. These are counts from a manually audited transcript ledger, with numerical calculations checked separately. I reviewed the supplied rows, not the implementation or omitted contract. External verification could not run because the tool host is disabled and no browser is connected; current procedures, URLs, and Excel localization remain explicitly unverified.

**2. Findings ranked by severity**

**HIGH — H1. Eligibility checks systematically confuse fulfilling the request with undesirable assistant behavior.**

**Evidence:** **17/44 rejected non-plant turns (38.6%)** have question-count or question-only rejection reasons; **15 of those 17 have `assessment:"ok"`**.

- `corr_3_00078`: all **three requested two-person dialogues** are rejected with `questions=15`, `16`, and `26`. The retained training content is the original monologue, two explanatory summaries, and the closing. The requested transformation receives no supervised demonstration.
- `corr_2_00030`: the requested Byzantine dialogue is rejected for two questions.
- `corr_3_00057`: the expanded dialogue and the first explicitly requested oral-exam question are rejected.
- `corr_3_00192`: «1/5: Ποια φάση χρειάζεται άμεσα φως…» is rejected even though the user explicitly requested questions one at a time.
- `corr_2_00223`: the recovery acknowledging reversed speaker attribution, followed by the requested A/B game, is rejected as `question_only`.
- `corr_2_00153`: a requested email/telephone enquiry is rejected because the **drafted message** contains two questions.

Other checks show the same problem. In `corr_2_00263`, a truthful denial containing the quotation «δεν βλέπω τίποτα από πριν» is rejected as `forbidden_selfclaim`. Quoting and denying a forbidden claim is not asserting it.

**Concrete fix:** Apply solicitation limits to questions the assistant asks **the current user for information**, with explicit exceptions for requested quizzes, games, dialogue scripts, and drafted correspondence. Make self-claim checks sensitive to quotation and negation. Re-evaluate rejected turns after fixing the checks; do not automatically reinstate every example, because some have independent defects.

---

**HIGH — H2. The responder sometimes judges against information unavailable to the writer, or against the wrong turn.**

**Evidence:** Four first answers explicitly state conditional assumptions but receive `assessment:"wrong"` when the user subsequently supplies different facts:

- `corr_3_00289`: «Υποθέτω ότι θα έχετε αυτοκίνητο…»
- `corr_2_00284`: «Αν στο A2 είναι το ποσό…»
- `corr_3_00041`: conditional cell assignments, followed by a question asking where the real values are.
- `corr_2_00248`: «Αν έχεις…», followed by example columns and two discount representations.

These answers may deserve other criticism, but the later revelation of different facts does not retroactively make a clearly conditional example false.

Separately, `corr_3_00212` rejects an **accurate recap** of the preceding attachment refusal as `assessment:"contradiction"`. The user’s next complaint concerns an earlier misleading description of a template, not an inaccurate recap.

**Concrete fix:** Judge the answer against the prefix available when it was written. Separate:

- factual error;
- reasonable assumption requiring revision;
- dissatisfaction with usefulness;
- complaint about an earlier answer.

Attach each assessment to a specific assistant turn. The responder’s hidden profile must not function as undisclosed grading criteria.

---

**HIGH — H3. Numerical and executable-answer validation remains insufficient.**

**Verified budget defect:** `corr_2_00085` treats a month as four weeks in **four retained turns**: the first answer, recovery, final summary, and closing.

The recovery allocates €280/month to food, transport, and outings, then promises €70 **each week**. But:

- €70 × 52 ÷ 12 = **€303.33/month**;
- €280 × 12 ÷ 52 = **€64.62/week**.

Four envelopes can cover a pay period, but calling each envelope a week leaves the remaining days unfunded. This matters because the monthly plan otherwise spends the entire salary.

**Static formula defect:** `corr_3_00113` retains:

`=ΑΝ(ΚΑΙ(E2<>"";F2<>"";E2+F2=0);"Εξοφλήθηκε";"Εκκρεμεί")`

Earlier formulas return `""` for missing inputs. The `E2+F2` expression can therefore produce an error; `AND` is not a safe short-circuit guard. This is static analysis, **not an executed Greek Excel test**.

**Unverified but consequential localization problem:** `corr_3_00059` accepts:

> «στο ελληνικό Excel 2021 η συνάρτηση είναι `ΕΑΝ`, όχι `ΑΝ`»

Other rows prescribe `ΑΝ` for the same stated locale/version. `corr_3_00221` also supplies `ΕΑΝ`. I cannot certify either localization here. **This correction must not be counted as successful resistance to false corrections until independently resolved.**

**Concrete fix:** Add deterministic arithmetic and unit checks, plus executable spreadsheet fixtures covering missing values, zero payments, duplicates, and the claimed locale/version. Validate both the original formula and any user-proposed correction. Recheck summaries that propagate numerical claims.

For balance: the **€64.20 shopping total in `corr_3_00172` is correct**. The approximately €9,825 purchase ceiling in `corr_3_00229` is also consistent with the unrounded assumptions; I would not flag its small rounding discrepancy.

---

**HIGH — H4. User facts and planning assumptions still become asserted facts.**

Four concrete cases:

| Row | Unsupported step in retained content | Fix |
|---|---|---|
| `corr_3_00136` | Treats the €650 budget as available entirely for expenses excluding accommodation. The user said the room was **booked**, not that its cost was outside the budget. | Ask the accommodation cost or explicitly condition the calculation on its exclusion. |
| `corr_3_00270` | Converts the lease start date, **1/9/2026**, into the date of the actual business-address change. | Keep lease commencement and actual relocation separate; confirm the filing date. |
| `corr_2_00191` | Draft states that care instructions were followed and photos are attached; later says «Σου στέλνω και φωτογραφίες». These facts were not supplied. | Use placeholders or “if applicable” wording for factual representations in outgoing correspondence. |
| `corr_2_00154` | Expands the child’s reported nut allergy into a **severe allergy to all nuts**, then repeats that expanded description in retained turns. | Preserve the reported scope; request clarification where severity or allergens matter. |

These are information-boundary defects even where the assumption might happen to be true. The exported rows omit the writer’s `assumption` field, so that field cannot be audited.

**Concrete fix:** Track whether each consequential fact was supplied, assumed, or proposed. Require visible qualification for material assumptions, particularly dates, budget exclusions, medical descriptions, and statements written in the user’s name.

---

**HIGH — H5. A retained recovery makes an incorrect self-report.**

**Evidence:** In `corr_3_00289`, the second recovery says:

> «Επανέλαβα άσκοπα το “Σκεφτείτε” τρεις φορές.»

The immediately preceding plant contains **four** occurrences, including its opener. This target is retained with `assessment:"ok"`.

That is **one directly verified wrong self-report among 361 retained targets**. The analogous “three times” claim in `corr_3_00108` is also wrong, but that recovery is masked; I have not counted it as retained.

**Concrete fix:** Derive exact counts and quotations from the referenced message. If an exact count is unnecessary, write «Επανέλαβα άσκοπα το “Σκεφτείτε”». Add a deterministic check whenever a self-report claims an exact occurrence count.

---

**HIGH — H6. Precise external claims and correction truth lack reviewable evidence.**

`corr_3_00234` contains an unresolved fee change: **€84.40 initially, €80 later**, without identifying or explaining the correction. Its recovery also supplies two addresses, two phone numbers, detailed office hours, an August 2026 identity-card requirement, and four non-root URLs:

- `astynomia.gr/anazitisi-ypiresion/nomos-achaias/`
- `passport.gov.gr/tools/faq/klopiapoleia.html`
- `www.passport.gov.gr/inner.php/grafeia-kai-orario/grafeia-diavatirion-ellada/dytiki-ellada/nomos-achaias/patra.html?print=1`
- `passport.gov.gr/diadikasia-ekdosis/documents/dikaiologitika.html`

**All four require verification. I have not established that they are fabricated.** A plausible official domain is not evidence that a path exists or supports the claim.

Other priority checks include the myAADE routes and document requirements in `corr_2_00180`, `corr_3_00063`, and `corr_3_00153`. In `corr_3_00270`, a retained answer itself later admits that its previously definite menu path was not verified as current.

The sample also omits `claim_truth` and claim-linked identifiers. Consequently, the reported **20 targets after false corrections and six after partial corrections cannot be located or audited as those subsets**.

**Concrete fix:** Give generators a dated, verified reference pack for unstable procedures and identifiers, with provenance stored outside the training conversation. Export correction claims, truth labels, evidence, and target-turn links. Independently adjudicate those labels rather than relying on the same responder that invented the claim.

---

**HIGH — H7. The pending editor pass can break currently correct conversational evidence.**

This is a **prospective defect**, not an observed post-editor failure.

In `corr_2_00182`, a retained assistant answer is quoted by a later retained answer, which is then quoted again. Editing the earlier answer while preserving downstream quotations can make those later “exactly what I said” targets false. Preserving `train=false` context verbatim does not solve dependencies between supervised turns.

**Concrete fix:** After editing, revalidate quotations, speaker attribution, first/previous-message references, correction truth, numbers, and eligibility against the **final transcript**. Protect code and factual invariants. Also demonstrate that the actual training serializer masks every planted/rejected assistant span while retaining it as context; the JSON flags alone do not prove the trainer honors them.

---

**MEDIUM — M1. Coverage and recovery accounting remain narrower than the headline parity suggests.**

**Evidence:**

- Sample plants: **7 verbatim-repeat, 6 wrong-self-report, 6 rote-frame, 2 empty-ack, 0 repeat-error**.
- Both “empty-ack” plants actually prepend «Σωστά, μου ξέφυγε» to a repeated substantive answer: `corr_2_00085`, `corr_3_00289`. They chiefly exercise repetition.
- A genuine recovery appears under `kind:"closing"` in `corr_3_00229`.
- Genuine corrections also appear under `kind:"ideal"`: for example, the eventual Greeklish fix in `corr_3_00006` and spreadsheet recovery in `corr_3_00176`.

Thus `kind:"recovery"` is not a complete measure of recovery behavior.

The absolute “no planted text reused” claim is also unsuitable: `corr_3_00041` later retains the **correct formula** contained inside its wrong-self-report plant. `corr_3_00158` similarly reuses valid formulas. This should be allowed.

**Concrete fix:** Track the faulty span separately from the valid surrounding content, and label conversational functions independently of closing/ideal serialization. Add genuine recoveries for dropped qualifiers, misunderstood requests, over-asking, and question-only failures. A polarity reversal is already present in `corr_3_00238`; qualifier handling is not wholly absent.

---

**MEDIUM — M2. User-side realism and surface consistency need targeted improvement.**

I flagged **three context-mismatched transitions**, not three wholly off-topic user turns:

- `corr_2_00085`: «οι διακοπές είναι για δύο» introduces holidays as though already discussed.
- `corr_3_00172`: “telika katholou psari” follows a chicken recommendation.
- `corr_2_00029`: asks to switch to Greek when the draft was already Greek.

Four especially staged user turns are `corr_2_00067`’s «Να βάλουμε και μια μικρή ανατροπή», `corr_2_00154`’s explicit grading of the misquote clarification, and the “I was testing you” turns in `corr_2_00182` and `corr_3_00275`. **That is an editorial judgment, not an objective naturalness metric.**

There are **six clear surface slips across six rows**:

- Greeklish: `corr_3_00172` — `μυrodia`; `corr_2_00029` — `Epeστρεψα`; `corr_2_00223` — `σηκώνομαι`.
- Atonic: `corr_2_00151` — `αποκάλυψη`; `corr_3_00223` and `corr_3_00234` contain accented `ή`.

These are **6/429 user turns, 1.4%**. I excluded Greek quotations copied from assistant messages.

**Concrete fix:** Check writing surface outside quoted spans. Ground transitions in the previous answer. Vary probe placement and wording; preserve deliberate adversarial users, but reduce repeated evaluator-style commentary.

---

**LOW — L1. The editor is needed, but cannot repair the substantive defects above.**

One unambiguous corrupted retained string appears in `corr_2_00222`:

> «χαίρομαι που σου ταιd.»

Other editing candidates include «σταθερό δωρεάν πρόσωπο» in `corr_2_00067`, the slash-heavy «Ο/η δεύτερος/η ταξιδιώτης/ισσα» in `corr_3_00136`, and «στη 18η Ιουνίου» in `corr_3_00060`.

I would budget light editing for roughly **5–10% of targets**, an editorial estimate rather than a measured failure rate. The directly counted corruption rate is **1/361**.

**Concrete fix:** Run the planned language pass, followed by the transcript-dependent validation in H7.

**3. What is good and should not be changed**

- **Misquote discrimination works in the supplied examples:** all **13 misquote constructions** differ substantively from the actual answer; all **12 retained misquote recoveries** correctly reject the attribution. I found no retained denial of a quotation the assistant actually wrote.
- All **21 planted assistant turns are marked `train:false`**. No retained target has an empty answer, a disallowed assessment, or a `wrong/evasive` verdict.
- The genuine corrections in `corr_3_00238`, `corr_2_00282`, and `corr_3_00041` name the specific mistake and correct it.
- I found **no clear invented internal cause** in the retained recoveries. Acknowledging a visible repetition is appropriate; it should not be banned as introspection.
- Preserve requested repetition, quotations, game questions, and complete final drafts. These are useful demonstrations of following the user.
- Preserve conditional general knowledge and honest limits. `corr_2_00153` eventually distinguishes unverified municipal requirements from confirmed instructions; `corr_3_00212` offers pasteable spreadsheet content after explaining the attachment limitation.
- The approximately **200-word** claim in `corr_3_00060` checks out: I counted **201 spoken words**, excluding speaker labels and standalone punctuation.

**4. Answers to the specific questions**

| Question | Assessment |
|---|---|
| **1. User side** | Mostly reacts to the preceding answer. Three mismatched transitions and six surface slips identified above. Hidden-fact leakage cannot be established without the profiles. Scheduled probing is conspicuous; every row contains an explicit conversational or identity check. |
| **2. Ideal targets** | Not consistently ideal. Four retained budget-conversion defects, one exact-count self-report error, consequential assumptions in four rows, and a statically identified spreadsheet edge-case failure. External factual-error rates cannot be responsibly reported without verification. |
| **3. Recoveries** | Sample parity is **12 genuine : 12 misquote**, plus one genuine recovery labeled closing. No clear invented causes. Openers have some variety: **8/12** genuine recoveries begin with “Ναι” or “Σωστά”; only **2/12** use “έχεις/έχετε δίκιο”. |
| **4. Plants** | All masked in JSON. I found **0/7 verbatim-repeat plants** that were made valid by a preceding request merely to repeat that answer. Both empty-ack plants overlap repetition. No repeat-error example is available to test its new prerequisite. Correct material from plants is reused; faulty-span imitation is the relevant criterion. |
| **5. Self-report** | **One definitely wrong retained self-report:** `corr_3_00289`’s three-versus-four count. Many first-question and previous-answer reports are accurate. The responder’s “correct” label is not sufficient evidence. |
| **6. Change of direction** | Most retained answers follow explicit changes. A clear Greeklish-format failure in `corr_3_00006` is correctly masked. The larger systematic failure is that the assembler masks successful changes into dialogue/quiz formats. |
| **7. Contract** | The seven identity-focused rows consistently identify Greek Apertus. No retained literal human-body/location claim found outside fictional content. Exact conformance is unassessable because the contract is omitted. `corr_3_00152` also needs a distinction between access to instructions and permission to disclose them. |
| **8. Greek** | Generally readable, with isolated corruption, awkward phrasing, and some mechanical closing language. Estimated 5–10% needing light editing; one definite corrupted target counted. |
| **9. Distribution and length** | Actual sample masked-plant prevalence is **18/60 = 30%**; reported full prevalence is **176/600 = 29.3%**, not 35%. Sample mean is **7.10 assistant turns**, or **14.25 total messages**, per dialogue. The sample contains nine distinct intent strings; all ten code/data-task rows concern Excel. |
| **10. Behavioral risk** | Strongest risks: learning to summarize instead of perform, treating valid questions as errors, accepting unsupported correction claims, and presenting assumptions as user facts. Blanket lexical bans would worsen several of these. |

For the additional scaled-set questions:

- **Pilot fixes landed partly.** Role masking and misquote distinctness are visible; recovery parity is real. False-correction resistance is demonstrated for the retained misquotes, but **not verified for the reported 20 after-false-correction targets**.
- **Full-set balance, using owner-supplied counts:** ideal **74.7%**, closing **15.9%**, genuine recovery **4.6%**, misquote recovery **4.7%**, clarify **0.14%**. Parity is sensible; it does not establish adequate recovery coverage. Measure token/loss weight before changing closing frequency.
- **Clarify turns:** **zero in this sample**; their use cannot be judged.
- **New defects:** over-terse question filtering is demonstrated. I found no definite inappropriate retained refusal to accept a substantively correct quotation.
- **Stopping:** no row exceeds 12 user messages. However, `corr_2_00223` ends on an unanswered request and `corr_3_00057` on an unassessed quiz answer, both at the cap. Cap complete exchanges or label truncation explicitly. There is no evidence here that approximately seven assistant turns is sufficient for the intended long-conversation failures.
- **Probe scheduling:** under a strict reading of explicit self-report/identity probes, `corr_2_00067`, `corr_2_00180`, and `corr_2_00200` contain only one. Confirm against the omitted probe metadata.
- **D1–D13 and observed failure shares:** unassessable without the actual dimension definitions and catalogue frequencies. I will not invent that mapping.

**5. Open questions for the owner**

1. What are the complete, versioned `CONTRACT`, `POLICY`, `ROLE_PLANT`, `FAIL`, and D1–D13 definitions?
2. Can the review export include profiles, stable turn IDs, `claim_truth`, claim text, probe metadata, assumptions, and assessment reasons—especially all false/partial-correction targets?
3. Why is this sample headed “seed 2” when it contains **22 seed-2 and 38 seed-3 rows**? How was it selected?
4. What independent evidence supports the passport details, myAADE procedures, and localized Excel function names?
5. Does the actual training pipeline demonstrably honor per-turn masking, including after chat templating and packing?
6. What validates conversational truth after editing, and what held-out evaluation measures recovery at substantially longer distances?

Apply H1–H7 to the queued pipeline and selectively repair or re-mask affected material. The findings do not justify wholesale disposal of already completed datasets.