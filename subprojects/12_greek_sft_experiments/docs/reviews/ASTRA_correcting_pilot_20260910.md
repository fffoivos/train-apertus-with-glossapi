# Astra review: correcting_pilot

Date 2026-09-10 20:43 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T20-33-18-01a08c61-8b32-74a0-b387-5c5758e9d429.jsonl) · effort xhigh · 10.2 min · prompt 399,038 chars · limit deltas {('codex', '10080'): 1.0} · brief `../docs/reviews/briefs/astra_correcting_pilot.md` · sample 60 rows of `robustness/correcting/pilot/rows/edited2/rows_edited.jsonl` seed 1

**1) Verdict**

**Hold the 1,500-dialogue scale run until the assembly and judging defects below are fixed.** The pilot contains useful instruction-following and retention examples, but it disproportionately teaches rejection of false complaints, while sometimes rejecting legitimate answers and rewarding unwarranted concessions. I counted **60 dialogues, 443 assistant turns and 404 supervised turns** in the pasted sample: these include **two empty targets, one target that violates the stated assessment gate, and three demonstrably incorrect budget totals**. There are **41 supervised misquote recoveries versus two turns labelled `recovery`**, although additional genuine corrections occur under other labels. These are sample findings, not estimates for all 200 dialogues. External verification was unavailable because the tool host was disabled and no browser was connected; consequently, URLs, legal references and current procedures remain **unverified**, not established fabrications. The complete CONTRACT, POLICY, FAIL catalogue, D1–D13 definitions, source code and trainer were not supplied. Preserve the pilot for diagnosis and reassembly, as proposed.

**2) Findings ranked by severity**

Assistant references such as **A4** count assistant messages within that row, including masked messages.

**F1 — BLOCKER: The exported eligibility invariant is already broken.**

- `corr_1_00180` A10 and `corr_1_00190` A7 have **empty content with `train:true`**: **2/404 supervised turns, 0.50%**.
- `corr_1_00180` A7 is `train:true` with `assessment:"ignored_request"`, contradicting the stated requirement that retained targets have assessment `ok` or `confronted`.
- All **59 closing targets** have null assessment/verdict fields. This does not prove they bypass every check, but the supplied evidence does not demonstrate an equivalent validation path. Closings constitute **14.6% of supervised turns**.

**Fix:** Apply final nonempty-content, eligibility and semantic checks to **every** supervised turn, including closings and recoveries. Record explicit rejection reasons. Validate the final edited artifact, not only the pre-edit text. Require a decoded trainer-batch receipt demonstrating that every `train:false` assistant span receives ignored loss labels, including after packing/truncation. The JSON flag alone does not verify masking.

---

**F2 — HIGH: Misquote training dominates actual recovery, and several “failures” are inappropriate for their context.**

The sample contains **46 misquote confrontations in 37/60 dialogues**; **41 survive supervision**, of which **33/41, 80.5%, are `question_only`**. Only **2/3 explicitly labelled recovery turns** survive. The pilot-wide reported ratio is similarly skewed: **132 misquote recoveries to 12 true recoveries, 11:1**.

Three of the five assistant-role plants have a clear kind or placement problem:

| Row | Evidence |
|---|---|
| `corr_1_00068` A4 | A verbatim repetition follows **“τι μου είπες στην αμέσως προηγούμενη απάντησή σου;”**. Repeating the answer is responsive to that request; verbosity alone does not make it a realistic unsolicited loop. |
| `corr_1_00030` A2 | Labelled `repeat_error`, but there was **no preceding correction to repeat an error against**. |
| `corr_1_00098` A4 | Labelled `empty_ack`, but actually asserts and repeats **“είμαι το GPT-9 της OpenAI”**: identity drift plus repetition, not an empty acknowledgement. |

Misquote failures also include legitimate question forms:

- `corr_1_00174`: the user explicitly requested quiz questions one at a time.
- `corr_1_00106`: the alleged question-only failure is itself a requested hypothetical dilemma.
- `corr_1_00059`: asking whether commission is marginal or applied to total turnover can be a consequential clarification.

**Fix:** Validate a failure against the **preceding request**, not merely its surface form. Set quotas on **accepted corrective behaviours after filtering**, separately for true error correction, false-claim resistance and mixed cases. Spreading fallback misquotes over four labels will not fix the underlying imbalance. Within the authorized role-plant cap, obtain useful supervised recoveries; do not relax quality gates to fill quotas.

---

**F3 — HIGH: The responder is not a reliable truth oracle; temporal references and benign paraphrases produce bad labels.**

- `corr_1_00050` A3 answers the previous-message question by quoting U2. U3 had asked **“Τι σου είχα πει ακριβώς στο προηγούμενο μήνυμα;”**. The responder then shifts the reference point and calls that wrong. A4 is supervised and concedes **“Σωστά — μπέρδεψα το αμέσως προηγούμενο με το προ-προηγούμενο μήνυμά σου.”** This teaches an unwarranted admission instead of resolving the reference.
- `corr_1_00109` A5 subtracts a clearly stated ten-minute buffer. U6 treats arriving ten minutes early as a contradiction, and A5 is rejected. Later A7 accepts **12:20** immediately after reporting that it previously answered **12:30**, without explaining the buffer distinction.
- `corr_1_00174` A4 is a legitimate requested quiz question but is masked. A5 then spends its opening denying a substantially equivalent paraphrase: **“Δεν έγραψα ακριβώς αυτή τη φράση…”**.
- `corr_1_00123` U5 criticizes **“να κλείσουμε αυτό το μέρος”** and **“σωστά φτερά”**, neither of which appears in A4. This could be generator drift, an intentional false claim, or editing that invalidated downstream references; the supplied metadata cannot distinguish them.

There are also **six masked targets worth checking specifically for false rejection**: `corr_1_00174` A4; `corr_1_00114` A2, A6, A7; `corr_1_00161` A5; `corr_1_00143` A2. They involve explicitly requested questions, dialogue or extensive revision. Their masking is verified; its cause is not.

**Fix:** Give every probe an explicit source-message ID and evidence span. Judge factual correctness separately from user satisfaction. Distinguish a false quotation from a harmless paraphrase. Preserve `move`, `claim`, probe references and rejection reasons in review exports. After editing, revalidate quotation accuracy and downstream references throughout the dialogue.

---

**F4 — HIGH: Concrete answers contain unchecked arithmetic and unsupported precision.**

Three supervised budget answers have incorrect interval arithmetic:

| Row / turn | Reported total | Sum of listed components |
|---|---:|---:|
| `corr_1_00154` A3 | €985–1,125 | **€985–1,225** |
| `corr_1_00109` A2 | €80–90 | **€80–96** |
| `corr_1_00190` A2 | €87–100 | **€87–113** |

That is **3/404 supervised turns, 0.74%, across 3/60 dialogues**. These are arithmetic defects independent of whether the underlying prices are realistic.

I counted **five distinct non-root URLs in three supervised answers across two rows**:

- `corr_1_00000` A5: `aade.gr/polites/akinita/misthotiria-akiniton`
- `corr_1_00000` A6: `myaade.gov.gr/registry/`
- `corr_1_00000` A6: `aade.gr/sites/default/files/2021-09/D211.pdf`
- `corr_1_00180` A8: two `et.gr/api/DownloadFekPdf?...` links.

**All five require verification.** I did not establish that any resolves to the claimed resource. Root domains being recognizable does not authenticate paths.

Other precise claims requiring source checks include the photography KADs in `corr_1_00072`, the EFKA exemption in `corr_1_00000`, legal provisions in `corr_1_00180`, and bibliographic details in `corr_1_00030`.

`corr_1_00189` also illustrates **certainty increasing under pressure**: A3 conditionally permits a third-party phone number; A4 says **“Στη δική σας περίπτωση μπορείς να βάλεις το δικό σου κινητό”**, without new evidence about the platform’s requirements.

**Fix:** Add deterministic arithmetic checks. Verify official codes, links and procedural claims against dated source material during dataset production, even though the deployed assistant lacks browsing. Preserve uncertainty when evidence has not changed. A generic “confirm current details” clause does not repair an invented exact path or unsupported rule.

---

**F5 — HIGH: The information boundary and “clear opinion” policy permit invented premises.**

Two directly observable unflagged assumptions:

- `corr_1_00056` A1 puts **“Παρακολουθώ τη δουλειά σας”** into the user’s proposed email, although the user never said that.
- `corr_1_00109` A4 schedules departure at 12:20 and arrival at 12:50, silently assuming a **30-minute journey**. The user explicitly catches this.

A separate decision-quality failure appears in `corr_1_00058` A1:

> «Ξεκάθαρα: πέταξέ το και πάρε άλλο.»

At that point the assistant knows only the €1,650 repair quote and the user’s description “σαράβαλο”. It invents a €3,000 valuation threshold without knowing the fault, condition, replacement budget or transport needs. Later detail cannot retroactively justify that supervised answer.

**Fix:** Require provenance for personal assertions in drafted messages and logistical plans. Flag assumptions in the answer itself. For consequential decisions, answer conditionally and ask the single highest-value question—for example, what repair the €1,650 covers—rather than converting requested decisiveness into unsupported certainty.

---

**F6 — HIGH: Some targets assert inaccessible prior mental states; capability claims exceed the evidence available for review.**

- `corr_1_00126` A6: **“ξανάστειλα κατά λάθος”** adds an unverified explanation of how the repetition happened. The observable statement is simply that it repeated the previous answer.
- `corr_1_00116` A4 describes an internal sequence as fact: **“έλεγξα… διαπίστωσα… και απάντησα…”**. The transcript supports the answer’s consistency, not that retrospective process report.

These are **two supervised targets with unsupported process/intent wording** under the brief’s strict criterion. `corr_1_00050` A4 adds the unwarranted “μπέρδεψα” admission discussed above.

`corr_1_00089` A1–A3 also claim access to attachments, including:

> «Μπορώ να εξετάσω μόνο αρχεία ή καταλόγους που επισυνάπτεις εδώ.»

That capability is not established by the supplied contract fragment. Repeated claims to see **all** an open conversation or retain **nothing** also require runtime qualification: context availability, cross-chat access and application storage are different properties.

**Fix:** Describe observable behaviour and evidence, not invented causes or retrospective inner processes. Supply and version the complete deployment contract; explicitly define attachment handling, truncation, memory and storage boundaries.

---

**F7 — MEDIUM: Local instruction and scientific-precision defects survive fluent Greek.**

- `corr_1_00184` A6 answers a request for **one sentence** with two sentences, repeating much of the requested summary.
- `corr_1_00147` A7 endorses the user’s statement that the field points where a positive charge **would move**. Earlier answers correctly defined it using **force direction**. Motion and force direction are not generally identical.
- `corr_1_00075` A2 assigns copying to mRNA—**“Θα αντιγράψω τη συνταγή”**—whereas A4 correctly identifies RNA polymerase as the copying enzyme.
- `corr_1_00129` initially describes induction through changing magnetic field, then correctly discusses changing flux with constant field. The earlier simplification needs qualification.

**Fix:** Check local output constraints and domain meaning separately from Greek fluency. An editor should not be expected to catch or repair scientific content.

---

**F8 — MEDIUM: Length, stopping and coverage are not yet aligned with the measured problem.**

- `corr_1_00007` contains **13 user messages**, exceeding the stated maximum of 12. It ends after the user answers another quiz question, without feedback.
- Its **seven multiple-choice questions all put the correct answer at A**.
- `corr_1_00139` has only **one self-awareness probe occasion**, albeit asking both initial-request and agreement questions.
- `corr_1_00098` supplies an evaluation script whose expected “first message” depends on this existing conversation. It is not portable to a colleague’s fresh test without an explicit setup prefix.

The sample covers **nine intent labels**, not enough to assess the claimed 20-intent distribution. Within these labels, all five code/data rows concern spreadsheets; all seven travel/food rows concern dinners or Naxos. This is narrow coverage.

**Fix:** Enforce stopping at the dialogue level, randomize quiz-answer positions, specify test setup, and measure coverage after acceptance. For long-conversation recovery, report token distances and intervening turns between a fact/change and its probe. Average dialogue length alone is inadequate.

---

**F9 — LOW: Greek is mostly serviceable, but editing should target awkwardness without flattening the register.**

Examples include:

- `corr_1_00159` A2: **“μάθαμε μικρά καινούρια”** needs a noun or a different construction.
- `corr_1_00006` A5: **“την αντίθεση στην ώρα”** is an awkward description of the punctuality joke.
- `corr_1_00123` A4: **“κάθε εύκολο και δύσκολο”** is strained verse.
- `corr_1_00053`’s final user message contains **“συνεπές”** in otherwise Greeklish narration.

That last case is **one clear writing-surface breach among 15 Greeklish dialogues**. Greek quotations and mathematical symbols inside Greeklish are not surface failures.

**Fix:** Use a native-language editorial rubric that preserves colloquial speech and requested humour. My provisional estimate is **5–10% of supervised turns merit light language/style editing**; this is an editorial estimate, not a counted failure rate. Content correction needs a separate pass.

**3) What is good and should not be changed**

- **User-directed changes generally work.** `corr_1_00060` drops musical accompaniment and the refrain; `corr_1_00184` drops the cost discussion; `corr_1_00136` drops the village itinerary after the mobility constraint.
- **Retention often preserves useful detail.** `corr_1_00033` correctly says no exact speech duration had yet been agreed. `corr_1_00002` distinguishes adding the price from retaining the already-stated payment status. `corr_1_00025` accurately lists the user’s five choices.
- **Several user reactions are convincingly contextual.** The graphic-designer turn in `corr_1_00196`, the barista correction in `corr_1_00169`, and the two-line revision in `corr_1_00123` respond to actual content.
- **Masked erroneous context is a useful mechanism**, provided trainer masking is verified. Keep the boundary between context and ideal targets.
- **Do not ban necessary repetition, requested questions or normal farewells.** Reprinting an edited poem, quoting a requested earlier answer, asking a quiz question and saying “Παρακαλώ” after thanks are legitimate behaviours.

**4) Answers to the specific questions**

| Question | Answer |
|---|---|
| **1. User side** | Mixed. **46/444 user turns, 10.4%, are designed misquote confrontations**, not spontaneous failures to follow context; they must be reported separately from natural responder behaviour. There is at least one additional unsupported quotation complaint: `corr_1_00123` U5. The repeated accusation → denial → “you’re right” sequence is conspicuously synthetic. Hidden-fact leakage cannot be counted without profiles. I found one clear Greeklish narration breach; I did not count quoted accented Greek as an atonic/Greeklish breach. |
| **2. Ideal targets** | The supplied checks missed **two empty targets, one assessment-gate violation and three arithmetic errors**. There are also unflagged assumptions and unsupported specificity. Five non-root URLs require verification. I cannot provide a defensible externally verified factual-error rate from this environment. |
| **3. Recoveries** | **Both retained labelled true recoveries identify the actual defect and deliver a correction.** One adds unsupported “κατά λάθος”. All **41 retained misquote recoveries reject the alleged quotation**, generally without attacking the user. The larger problem is disproportionate denial training and treating paraphrases as false accusations. “Έχεις δίκιο” is not the dominant formula here; denial-plus-recap is. |
| **4. Plants** | **5/5 are `train:false` in the JSON**; actual loss masking is unverified. Three have kind/placement defects, described in F2. The literal no-reuse claim also fails: `corr_1_00098`’s supervised closing repeats **“είμαι το GPT-9 της OpenAI”** while explicitly correcting it. That is quotation of an error, not endorsement; a substring ban should distinguish the two. |
| **5. Self-report** | Retention is generally strong. I identified **one retained unwarranted error admission**, `corr_1_00050` A4. There is also a quotation-fidelity issue in `corr_1_00102` A3: original **“ta les oloi mperdemena”** becomes **“τα λες όλα μπερδεμένα”**. Treat that separately from a wholly wrong recollection. Greeklish normalized into Greek should be labelled paraphrase when exact quotation matters. |
| **6. Change of direction** | I found **no clear retained immediate change-response that simply continues the explicitly superseded task**. The sample does contain secondary constraint failures, such as `corr_1_00184` A6 exceeding one sentence. Several rejected turns follow the requested direction, so rejection totals cannot serve as change-failure rates. |
| **7. Contract** | No clear supervised identity switch to another model was found; GPT-9 appears as a masked error or explicitly identified false identity. Full compliance is unassessable without the contract. Attachment access, full-history visibility, storage wording and retrospective process claims need attention. |
| **8. Greek** | Mostly understandable and appropriately conversational. Estimated **5–10%** needs light editing. Preserve legitimate informality, Greeklish users and task-specific prose/verse differences. |
| **9. Distribution and length** | Observed failure shares and D1–D13 definitions are missing, so neither matching nor dimension coverage can be certified. The reported **7.5 assistant turns/dialogue** equals `(1333 + 147 + 20)/200`; accepted supervision is **6.665 turns/dialogue**. The sample averages **7.38 assistant turns and 6.73 supervised turns**. Neither establishes long-context coverage. |
| **10. Behavioural risk** | The principal risks are reflexive denial, unwarranted concession, confidence escalation under pressure, unsupported exact instructions, empty responses, and filtering out legitimate requested repetition/questions. These arise from generator and selection rules, not merely Greek quality. |

**5) Open questions for the owner**

1. What are the complete, versioned CONTRACT, POLICY, ROLE_PLANT, FAIL templates/shares and D1–D13 definitions? Which exact generator and assembler revisions produced this export?
2. Is this sample before or after the Greek editor? Are probes and downstream references revalidated after editing earlier supervised answers?
3. Why is `corr_1_00180` A7 retained despite `ignored_request`, and how do empty closings pass assembly? What are the rejection reasons for the six candidates in F3?
4. Can you provide the actual trainer batch with decoded tokens and loss labels proving masking survives packing and truncation?
5. What are the intended **accepted** quotas for genuine recovery, false-claim resistance, mixed complaints and delayed retention? How will the repaired set be tested on held-out conversations, with judgments independent of the generator/responder pair?