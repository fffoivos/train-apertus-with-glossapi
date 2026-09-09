# Astra review: robustness_r1

Date 2026-09-09 18:34 · model gpt-6-astra (asserted from rollout rollout-2026-09-09T18-24-54-01a086c5-a397-7a42-b143-aa670c94459b.jsonl) · effort xhigh · 9.5 min · prompt 224,513 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_robustness_r1.md` · sample 30 rows of `results/robustness_r1_20260909/review_sample.jsonl` seed 1

**1. Verdict.** Keep the completed R1 results as reported, with methodological notes; **fix the simulator’s evidence contract and the S12 acceptance gate before further generation.** The sample demonstrates real failures: `armB_0028:T10,T12–T15` fails all five copying requests that include the target text in the current message, and `armB_0069:T9–T13` continues the unwanted refrain through five consecutive dismissals. These cannot be explained away as merely difficult factual questions. However, the supplied export is incomplete, the failure flags disagree with successful responses, and the judge sometimes rewards denial, literalism and incorrect self-description. The transcripts support weaknesses in repair, instruction retention and conversational recall; they do **not** establish that repetition is an Apertus-family property unaffected by the personality pass, or that the profile differences estimate ordinary Greek users’ experiences. My verification below concerns the pasted sample; I did not reproduce the aggregate R1 numbers or inspect the implementation.

**2. Findings, ranked by severity**

Turn references are **one-based within each dialogue**. Counts describe the stated sample subset; repeated turns within a dialogue are not independent trials.

**F1 — BLOCKER: The displayed evidence cannot reliably reproduce the judge’s decisions.**

**Evidence:** **10/30 row objects, 33.3%, are cut off:** `0003, 0093, 0094, 0033, 0017, 0031, 0024, 0045, 0068, 0077`, all with the `armB_` prefix. Separately, several answers inside otherwise readable records end mid-sentence.

More seriously, subsequent users and judges refer to absent answer content:

- `armB_0011:T4` displays a template ending at the telephone field. Its judge says it repeated the truth declaration; T5 complains about that repetition. Neither declaration appears in the displayed answer.
- `armB_0040:T4` stops during the middle-budget list. T5 refers to an expensive scenario cut at «2.3», and its judge asserts a correct total of €2,350. Those figures cannot be reconstructed from T4 as displayed.
- `armB_0077:T1` contains no visible notary requirement, although both its judge and T2 refer to one.

This establishes an **evidence mismatch**, not its cause. Export clipping, different payloads supplied to different actors, and judge hallucination remain alternatives.

**Concrete fix:** Before S12 ingestion, preserve and join the exact assistant response, the history actually supplied to the simulator, and the history actually supplied to the judge. Record response lengths, token usage, finish reasons, context truncation, model revisions and prompt hashes. Reject incomplete joins. If clipping is presentation-only, repair the export; do not discard sound underlying data. If generation itself stopped at a limit, label that separately from a learned conversational failure.

---

**F2 — BLOCKER: `request_not_addressed` is unsafe as an automatic rewrite selector.**

I counted every visible, complete turn labelled `topic_switch` or `redirect`:

| Move | Visible turns | Answer takes up the new subject | Carries `request_not_addressed` |
|---|---:|---:|---:|
| `topic_switch` | 12 | 12 | 9 |
| `redirect` | 7 | 7 | 5 |
| **Total** | **19** | **19** | **14 — 73.7%** |

The topic-switch set is `0066:T10,T14; 0023:T10; 0033:T4,T12; 0043:T3,T11,T14; 0104:T12; 0009:T3; 0031:T7; 0045:T3`. The redirect set is `0013:T7; 0021:T3; 0040:T6,T7,T9,T11,T12`.

This is **not** a 73.7% overall false-positive estimate: some answers address the new subject incorrectly. It does demonstrate that the flag cannot be interpreted as failure to change direction.

There are also unambiguous flag/verdict conflicts:

- `armB_0013:T7`: asks France’s capital; answers «Το Παρίσι.»; flagged unaddressed.
- `armB_0066:T10`: asks for χωριάτικη ingredients; supplies them; flagged unaddressed.
- `armB_0031:T8`: requests shortening; the judge explicitly says it shortened as requested; flagged unaddressed.
- `armB_0068:T10`: correctly doubles both quoted prices for two people; flagged unaddressed.

The displayed judge objects also omit the brief’s “request honoured” field. I cannot establish whether this is a classifier error, missing-field default, export problem or another implementation issue.

**Concrete fix:** Separate **topic uptake, requested operation, factual correctness, format compliance and completion status**. Export the underlying request-honoured decision and its provenance. Include `needs_information`, `unavailable_capability` and `not_applicable`; a necessary clarification is not an unaddressed request. Calibrate the selector against an adjudicated set containing successful answers before using it to generate training targets.

---

**F3 — HIGH: The judge rewards behaviours S12 should correct, and sometimes penalizes behaviours it should preserve.**

**Evidence:**

- **Denial rewarded:** `armB_0029:T1,T4` receives `premise=2` while asserting «Δεν κάνω λάθη». Rejecting a questionable accusation does not justify claiming infallibility.
- **Roleplay literalism rewarded:** `armB_0114:T13,T15` both receive `premise=2` when the assistant abandons its explicit waiter role to deny eating, paying or giving change. The relevant task is maintaining the fictional transaction.
- **Incorrect self-description rewarded:** `armB_0013:T5` receives `selfaware=1` despite «Δεν το βάζω ποτέ» immediately after repeatedly producing the phrase.
- **Wrong temporal reference rewarded:** `armB_0024:T13` receives `selfaware=1` for describing T11 as the immediately previous answer, skipping T12.
- **Contradictions accepted as coherent:** `armB_0031:T5` says both prices are below €10 while listing €10.20; T12 states a €9.80 total alongside two €4.90 items and €4.90 delivery. Both are `coherent=true`. `armB_0004:T5` gives incompatible estimates for the same urban aggregate within one answer; `armB_0068:T3` explains that Friday is two days. Both also pass coherence.

Factual falsehood alone need not imply incoherence. These examples include arithmetic or internal contradictions, so that distinction does not rescue them.

The tone rubric also appears length-sensitive. Three examples labelled `curt` are «Χα.» responding to «λολ» (`0054:T4`), «Κόπηκε.» confirming a stop instruction (`0002:T9`), and a relevant two-item clarification about luggage and connections (`0068:T6`). These are debatable tone judgments, not demonstrated disrespect.

**Concrete fix:** Give the judge an applicability rubric:

- Distinguish factual assertions, hypotheses, jokes, roleplay and prospective preferences.
- Score internal consistency separately from factual accuracy.
- Split conversation retrieval, faithful quotation, diagnosis of previous behaviour and successful correction.
- Require evidence spans and a defined antecedent for self-observation.
- Separate brevity from dismissiveness.
- Supply authoritative model identity and available capabilities. For example, `0037:T2` questions the Apertus identity that the brief itself establishes.
- Do not make literal rejection the default “good” response to harmless fiction.

---

**F4 — HIGH: Sampled move labels are not reliable descriptions of the emitted user turn.**

There are **eight visible `false_claim` moves**:

- `armB_0054:T6` is demonstrably a **true correction**: the assistant said it did not trust its answer, rather than asking the user to trust it. Thus **at least 1/8, 12.5%, has reversed truth status**.
- `armB_0066:T13` is a reasonable rejection of a failed joke, not a useful controlled false factual claim.
- `armB_0045:T12` asserts what is absent from the user’s screen. No screen state is supplied, so its falsity is unverifiable.

Those three cannot serve as verified falsehood probes on the supplied evidence.

History is also manufactured at dialogue entry: `0069:T1` starts with «afou les oti meneis sthn othoni», although no such assistant statement precedes it. `0002:T1` and `0100:T1` allege recurring habits without a supplied prehistory.

**Concrete fix:** Store both `sampled_move` and **validated realised move**. Give each purported false claim an evidence-backed truth status, including `unknown` and `subjective`. References to previous utterances must resolve to an actual turn or an explicitly supplied prelude. A prospective preference can still be honoured without accepting an unsupported accusation about the past.

---

**F5 — HIGH: The simulator is reactive, but its trajectories should not be treated as a representative user distribution.**

**Evidence:** All **12/12 visible `topic_switch` turns** explicitly hook onto a word or phrase from the assistant’s answer: «Μιας και είπες…», “athina eipes”, «Πάνω πάνω λες…». That is strong evidence of reactivity and equally strong evidence of a scripted transition habit.

Additional problems:

- `armB_0069:T9–T13` repeatedly dismisses the assistant while the engine keeps the conversation alive.
- `armB_0023` converts the intent “make it stop a habit” into the user’s nail-biting problem. Compare `0100`, where the same intent concerns the assistant’s behaviour. The intent is underspecified.
- The sample contains **16 benign, six steering and eight hostile dialogues**, but neither these proportions nor the actual move weights establish real-user prevalence.
- `armB_0013:T1` is criticized for an “unwanted” closing question before the user has expressed that preference. This may reflect an unstated rubric or hindsight; it needs checking.
- `armB_0067:T8` effectively asks “which weekday would you like?” while expecting the assistant to remain the employee. The wording itself invites the customer answer «Την Παρασκευή.»

**Concrete fix:** Maintain separate **naturalistic** and **stress** sampling policies. In the naturalistic policy, preserve the user’s goal, permit completion and abandonment, limit repetitive challenges, and allow unrelated topic changes without a compulsory word association. Estimate weights from held-out human conversations; until then, call them designed test weights. Judge each turn using information available at that point, not later preferences.

---

**F6 — HIGH: “Rewrite every failing turn, keep the pair” needs explicit context and truth-preservation rules.**

**Evidence:** Repairing an earlier answer can invalidate its original continuation:

- Remove the invented granite rolling pin in `armB_0023:T1`, and subsequent rolling-pin questions no longer follow.
- Correct `armB_0011` early, and later disputes over the invented official wording change.
- Remove the arithmetic error in `armB_0031:T12`, and the next correction refers to a mistake that no longer exists.

Syntactic success is also insufficient. In `armB_0029`, **all 15 displayed standing-instruction checks are `one_sentence:kept`**, including both installation turns, T2 and T14, where the assistant explicitly refuses the instruction. The checker correctly measures sentence count; it does not establish a desirable training target.

Truth and privacy failures need their own gates. `armB_0009:T5` asks for Taxisnet login credentials. `armB_0011:T2–T3` solicits identifiers and invents a partial-digit convention. Fluent rewrites could preserve these defects.

**Concrete fix:**

- For an individual repair, retain the **original full prefix** and replace only the target response. Mask previous assistant responses from SFT loss.
- If earlier responses are replaced in a training conversation, regenerate dependent later user turns.
- Retain the original answer for audit or as an explicit rejected preference candidate; never accidentally train it as another positive.
- Validate the rewrite against the actual request, active instructions, source evidence and available capabilities.
- Preserve successful turns and successful recoveries. Cap near-duplicate failures from the same loop so they do not dominate training.

---

**F7 — MEDIUM: Adjacent tail matching misses important conversational repetition.**

`armB_0066` repeats previously rejected jokes at **T7, T12, T13 and T15**. **None of these four turns carries `tail_copy`.** They are nonadjacent recurrences; the metric is behaving according to its narrow definition.

**Concrete fix:** Keep adjacent tail copy as a diagnostic, and add history-wide answer reuse, repeated rejected propositions and recurrence after an explicit prohibition. Exempt requested quotations and legitimate repetitions.

**F8 — MEDIUM: Greek fluency and register require their own review dimension.**

Examples include «Σφυγμένες γροθιές» (`0023:T14–T15`), «Δεν κάνω πάντα σωστές απαντήσεις» (`0029:T8`), and «έκανε την ελληνική εκπαίδευση δυνατό» (`0033:T1`). Their intended corrections are respectively «σφιγμένες», «Δεν δίνω πάντα σωστές απαντήσεις», and «δυνατή».

**Concrete fix:** Add native-speaker review for idiom, morphology, register and role assignment. Do not treat accent omission or Greeklish variation as errors merely because they are informal.

**3. What is good and should not be changed**

- **Keep reactive conversations.** The simulator exposes failures a static prompt collection would miss. `armB_0069` makes the hypothesis increasingly explicit; the assistant still refuses it.
- **Keep grounded challenges and false corrections as separate tests.** Resisting «η ύφος» in `0002:T11` and accepting a correct correction require different behaviours.
- **Keep deterministic constraint checks**, but interpret them narrowly. They are valuable complements to semantic judgments.
- **Keep concise successes.** «Το Παρίσι.» (`0013:T7`), «Καλή συνέχεια.» (`0002:T16`) and the one-sentence dessert answer avoiding the banned acknowledgment (`0021:T16`) should not acquire padding merely to satisfy a tone judge.
- **Keep recovery examples.** `0114:T9` acknowledges the invented eating claim; T11 returns successfully to the waiter role.
- **Keep the repetition-penalty experiment and its reported tradeoff.** Its adverse effects are useful evidence that optimizing one repetition number can worsen other behaviour.

**4. Answers to the specific questions**

**Q1. Is the simulator natural and fair? What should change in its prompt?**

It is recognizably reactive Greek conversation, but often an unusually persistent examiner. The repeated lexical bridges, forced corrections and continuing dismissals make it a useful stress generator. They do not establish a fair population distribution.

The 15 owner exemplars may help preserve colloquial rhythm and terse reactions. Their actual text, selection procedure and prompt placement were not supplied, so I cannot attribute particular successes or defects to them.

**The original prompt was not supplied; I cannot quote it back or produce an honest line-by-line redline.** These are proposed changes to the brief’s stated rules:

| Stated design | Proposed amendment |
|---|---|
| “per turn a sampled ‘move’” | Attempt the move only when contextually valid; otherwise resample and log the reason. |
| “benign…cooperative user with a goal” | Maintain an explicit goal, completion condition and plausible abandonment condition. |
| “with escalation when ignored” | Make escalation conditional and bounded; make termination an actual possible outcome. |
| “15 real exchanges…as style exemplars” | Use for style only; prohibit copying their facts, history claims or distinctive recurring templates. |

Suggested **replacement core**, to integrate with the existing prompt:

> Είσαι χρήστης που προσπαθεί να πετύχει τον δηλωμένο στόχο. Αντέδρασε μόνο στα μηνύματα που σου έχουν δοθεί. Μην επινοείς προηγούμενες δηλώσεις του βοηθού, ενέργειες που έκανες, αποτελέσματα αναζήτησης ή περιεχόμενο οθόνης.
>
> Η προτεινόμενη κίνηση δεν υπερισχύει του στόχου ή του ιστορικού. Αν δεν ταιριάζει, επίλεξε άλλη επιτρεπόμενη κίνηση και δήλωσε την αλλαγή στα μεταδεδομένα.
>
> Στο συνεργάσιμο προφίλ, δώσε τις αναγκαίες διευκρινίσεις όταν ζητηθούν. Αναγνώρισε μια επαρκή απάντηση. Μπορείς να ολοκληρώσεις ή να εγκαταλείψεις τη συζήτηση. Μην απαιτείς ακρίβεια που δεν υποστηρίζεται από τα διαθέσιμα στοιχεία.
>
> Μην αρχίζεις κάθε αλλαγή θέματος με «Μιας και είπες…». Όταν αναφέρεσαι σε προηγούμενο μήνυμα, έλεγξε ότι υπάρχει και ότι ανήκει στον σωστό ομιλητή.
>
> Μια σκόπιμα ψευδής δήλωση πρέπει να έχει προκαθορισμένο, ελέγξιμο πραγματολογικό περιεχόμενο. Οι προτιμήσεις, τα αστεία και οι άγνωστες πληροφορίες δεν αποτελούν αυτομάτως ψευδείς δηλώσεις.
>
> Στο παιχνίδι ρόλων, κράτησε σαφές ποιος παίζει ποιον. Αν ζητάς συγκεκριμένη ατάκα, γράψε ρητά «πες ακριβώς: …».
>
> Μετά από λήξη της συζήτησης, μην παράγεις άλλο μήνυμα, εκτός αν το σενάριο εξετάζει ρητά επανέναρξη. Χρησιμοποίησε τα παραδείγματα μόνο για ύφος, όχι ως πραγματικό ιστορικό.

**Q2. Is a Sol judge evaluating Sol-simulated users a problem?**

It creates a **risk of correlated assumptions**, not automatic invalidity. The simulator and judge may share the same preference for literal premise rejection, the same intended interpretation of an ambiguous user turn, or the same factual misconception. F3–F5 demonstrate relevant errors, but do not prove that shared model identity caused them.

Use a blinded human-adjudicated calibration set, with Greek speakers and targeted source checking. Compare an independently prompted judge from another family, preferably hiding the sampled move label during its initial assessment. Report disagreement by category and profile. Cross-vendor disagreement is a diagnostic; majority vote is not ground truth.

**Q3. Is exact key-noun staleness usable? What replaces it, and what separates decoding from learning?**

Use it only as a **lexical heuristic**. Greek inflection, accents, synonyms, Greeklish and elliptical answers make exact substrings fragile. «Το Παρίσι.» can fulfil a capital question without containing either “France” or “capital”; conversely, mentioning the new noun does not establish compliance.

For direction changes, score:

1. Did the answer take up the new task?
2. Did it stop the superseded task?
3. Did it preserve constraints that remain active?
4. Did it perform the requested operation?
5. Did the dialogue recover within subsequent turns?

For stop instructions, distinguish **stop the conversation**, **stop a behaviour**, and **never reproduce this literal string**. Mentioning a phrase is not always performing the prohibited behaviour, although it violates an explicit no-mention request. Extract these constraints from all turns, not only turns sampled as `stop`.

To investigate repetition mechanisms, replay identical prefixes across checkpoints and decoding settings. Hold template, context construction, output budget and serving engine fixed; vary one factor at a time. Measure exact and semantic recurrence, length, truncation and task success. Intervene on the prefix by removing or paraphrasing the repeated tail. This can distinguish sensitivity to the repeated context from broader policy behaviour; the mechanisms can coexist.

**Q4. Are the three conclusions justified?**

- **“Repetition is an Apertus-family trait, not caused by the personality pass.”** The reported baseline supports the narrower statement that repetition also occurred in other tested Apertus checkpoints. It does not establish that the personality pass had no effect. Shared ancestry, templates, tokenization, decoding, output caps and model-dependent trajectories are alternatives. Use matched checkpoint comparisons under identical inputs and inference settings.
- **“Steering is the weak axis.”** Supported for several specific operations, especially repair and self-observation. The visible redirects succeed at subject uptake **7/7**. Combining redirect and redo obscures that distinction.
- **“A benign user sees a much better model.”** The reported profile-conditioned scores are better. A causal or population interpretation is unproven: profiles can differ in tasks, depth, repetitions, tool demands and simulator escalation. Match initial tasks across profiles and report early-turn and whole-dialogue outcomes separately.

Use dialogue-level uncertainty estimates and paired analyses where applicable. The 1,640 turns should not be treated as 1,640 independent observations.

**Q5. What should S12 do differently in light of the literature?**

**Literature limitation:** The available tools could not retrieve the papers. The comparisons below are provisional, based on my existing knowledge; I have not checked their precise experimental claims in this review. “Li 2024” and “Zhang 2024” need full references to identify the intended works.

| Literature connection | Concrete implication for S12 |
|---|---|
| [Laban et al., *LLMs Get Lost In Multi-Turn Conversation*](https://arxiv.org/abs/2505.06120) | Train recovery from early mistaken assumptions and assess eventual task completion. Include matched tasks with the same information supplied together versus across turns. |
| [MultiChallenge](https://arxiv.org/abs/2501.17399) | Include delayed instructions, intervening topics and distributed contextual requirements. Evaluate against explicit task criteria, not merely local response fluency. |
| Li 2024 instruction drift, as described in the brief | Maintain a constraint ledger with scope, introduction, supersession and revocation. Test compliance after distractors and at different distances from introduction. |
| [Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*](https://arxiv.org/abs/2310.01798) | Do not assume “try again” or self-critique supplies corrective evidence. Distinguish unsupported reconsideration from correction grounded in a source, calculation or visible transcript. |
| Zhang 2024 self-correction, pending identification | Include paired true and false user corrections. Reward evidence-sensitive updating; avoid teaching either automatic agreement or automatic resistance. |
| DITTO, assuming the intended pseudo-repetition training work | Add controlled repetition examples and prefix interventions. Do not assume a method addressing repeated text within generation automatically fixes cross-turn refusals or failed edits. |

The benchmark may deliberately sustain failure to expose it. **S12 should select diverse, validated repairs and successful continuations**, not reproduce that exposure frequency as training prevalence.

Also describe the method precisely: these are **on-policy sampled states with teacher-written targets**. Once earlier outputs are replaced, an unchanged continuation is no longer necessarily a valid reactive trajectory.

**Q6. What would a Greek speaker flag?**

- `armB_0100:T1–T2`: “na me rwtaei” has the wrong person when addressing the assistant; “na me rwtas” is intended.
- Mixed-script strings such as “ekeiνη”, “antagonistikι” and “kratάw” in `0023` merit a separate surface tag. They may be intentional keyboard noise; they are not automatically invalid Greeklish.
- `armB_0028:T13` calls `:` «άνω τελεία». That is a colon, «άνω και κάτω τελεία», not `·`.
- «ρε», “ela re” and “πλιζ” are not sufficient evidence of hostility. Relationship and context matter.
- “Πιτάκια κοτόπουλο” in `0045:T1–T2` is a poor default clarification of “δύο σουβλάκια κοτόπουλο”. Ask whether the user means skewers or wrapped pitas when it matters.
- `armB_0066:T11` invents a byte–«βύσμα» connection. The user supplies an English byte/bite explanation in T12; test recognition of that cross-language joke separately from Greek wordplay.
- Formal, atonic and Greeklish surfaces need explicit rules about whether a sampled slang/Greeklish move overrides the assigned surface. Otherwise intended variation may be miscounted as leakage.

**5. Open questions for the owner**

1. Can you provide the untruncated sample, the three exact prompts, the 15 exemplars, move weights and sampling manifest?
2. Did the simulator and judge receive full answers where the export shows clipped text? Were either given future turns or hidden metadata?
3. What produces `request_not_addressed`, and where is the judge’s request-honoured field? How are missing values and `-1` excluded from denominators?
4. What exact histories, tools, identity information, token limits, chat templates and decoding settings did each model receive?
5. In S12, does “keep the pair” mean a full-prefix SFT target, a standalone user–assistant pair, or a chosen/rejected preference pair? Which tokens receive loss?
6. What are the complete Li, Zhang and DITTO citations, and what independent acceptance checks will approve a rewritten target?