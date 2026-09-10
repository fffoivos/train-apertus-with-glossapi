# Astra review: multiturn_fixes

Date 2026-09-10 20:38 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T20-33-36-01a08c61-d270-7861-a6ca-6381b458db2e.jsonl) · effort xhigh · 5.3 min · prompt 23,158 chars · limit deltas {('codex', '10080'): 0.0} · brief `../docs/reviews/briefs/astra_multiturn_fixes.md`

**1. Verdict.** **Revise before scaling the queued datasets.** The plan targets several plausible SFT improvements—using prior information, responding to corrections, following topic changes, and replacing empty conversational formulas with useful answers—but its strongest rules can also teach curtness, premature guessing, and indiscriminate agreement with corrections. The filtering policy conflicts with both planted-failure training and versioned editing; the proposed counts do not establish the claimed conversation dose; and several literature conclusions exceed the evidence described. **This is a document review, not a verified pilot review:** no sample rows, row IDs, D1–D13 definitions, or research reports were supplied, and file/browser access was unavailable. I therefore cannot confirm the earlier pilot review, independently count defective rows, or authenticate the cited results and licences. The HIGH findings below concern identifiable specification problems or explicitly labelled risks. Apply them to queued generation; completed datasets receive notes only.

**2. Findings ranked by severity.**

The available numerical evidence is the owner’s aggregate reporting. These rates are arithmetic checks, **not independently verified sample failure rates**:

| Reported observation | Reported count | Calculated rate |
|---|---:|---:|
| Laptop chats ending in repetition/stale copying | 16/17 chats | 94.1% |
| “You do the work” imperative | 43/196 answers | 21.9% |
| Verbatim/near repetition | 21/196 answers | 10.7% |
| Overlong answer to a one-liner | 21/196 answers | 10.7% |
| Question-only answer | 20/196 answers | 10.2% |
| False self-knowledge | 12/196 answers | 6.1% |
| Degenerate loops | 10/196 answers | 5.1% |

The pattern labels overlap. Their percentages cannot be added, and this selected collection does not establish deployment prevalence. **Row IDs available for inspection: none.**

**F1 — HIGH: the clarification policy contradicts itself and rewards premature guessing.**

**Evidence:** §3 says “An answer never consists only of a question,” “At most one question after the content,” and, for ambiguous wording, “take the likelier one.” §4 nevertheless requires a grounding question when a missing fact decides the answer. Those rules cannot all hold when no useful answer is possible without that fact. The supplied assumption template also ends with «αν εννοείς …, πες μου», reintroducing the solicitation that other rules discourage.

The hidden profile is also an unsafe source of labels: a profile can contain many facts that are unknown to the assistant but irrelevant to answering.

**Fix:** label two independent properties:

- **Clarification need:** unnecessary, useful but optional, or required.
- **Response action:** answer, answer with assumption, clarify, answer plus clarify, or acknowledge/close.

Allow a question-only response when necessary information prevents meaningful progress. Judge necessity from the **visible conversation and requested task**; use hidden facts to assess consequences, not to demand omniscience. Permit a compact set of questions when several independent facts are jointly necessary.

Constructed counterexample, **not a sampled row**: «Μετάφρασε αυτό στα αγγλικά.» with no text or recoverable referent legitimately warrants «Ποιο κείμενο θέλεις να μεταφράσω;».

**F2 — HIGH: literal input-length matching and compulsory play threaten completeness and tone.**

**Evidence:** §3 requires “A one-line message gets a one-line answer.” A one-line request can ask for a detailed explanation, comparison, or full rewrite. “After an insult … one line and stop” also conflicts with the later requirement that “the real request continues.” The example «συνταγή για πονοκέφαλο» does not, by itself, establish playful intent.

These are specification defects; the reported 27% curtness rate makes their likely consequences especially relevant.

**Fix:** replace the length rule with:

> Match the requested deliverable, task complexity, and explicit length preference. Use the shortest answer that completes the task.

Require substantive corrections to include the corrected result; prohibit acknowledgement-only repairs when a deliverable is owed. Briefly handle an insult and still complete the accompanying request. Answer playfully when context supports play; do not infer a joke solely from an unusual phrase. Allow deliberate register changes in quotations, translations, and requested contrasting versions.

**F3 — HIGH: the hard filters conflict with the training examples they are supposed to protect.**

**Evidence:** §5 applies filters to “every training row” and prohibits repeated sentences from earlier assistant turns, with only a quotation exception. Yet:

- Planted assistant failures are intentionally defective context.
- A correct versioned edit often preserves unchanged sentences.
- A requested recap legitimately repeats prior information.
- Repeated identifiers, code, and structured output can violate a blanket four-gram threshold.

§1.9 mentions masking, but the brief provides no serialized examples or token-label evidence. That is an **unverified implementation dependency**, not proof that masking is broken.

**Fix:** separate checks for **context integrity**, **supervised-target quality**, and **legitimate repetition**. Permit declared planted defects in masked context. Preserve unchanged text when the requested edit requires it. Use repetition detectors to flag candidates, with task-aware rejection rules.

Before training, inspect final tokenized examples showing that every planted failure and rejected example has ignored loss labels, the intended target is supervised, and truncation preserves the necessary history and target termination. Verify this after the actual chat template and packing stages. Make question detection Greek-aware, including semicolon/question-mark normalization.

**F4 — HIGH: “ignore superseded instructions” needs an explicit scope and authority model.**

**Evidence:** §4 combines revocation, contradiction, distractors, and context ignorance. “Latest valid instruction” is underspecified. A new topic does not necessarily revoke a standing language preference; pasted text is not automatically an instruction; and an obsolete instruction remains a historical fact if the user asks what was previously requested.

**Fix:** give generated dialogues an evaluation ledger containing each constraint’s source, authority, scope, activation, and revocation. Supervise the answer, without requiring the model to print the ledger. Include contrasts between:

- Replacing one requirement and cancelling the whole task.
- Switching topics and temporarily interrupting a task.
- An instruction from the user and an instruction inside quoted material.
- Disregarding an obsolete requirement and truthfully describing its history.

Automatic consolidation should be conditional: helpful before a complex final deliverable, unnecessary after every turn.

**F5 — HIGH: a correcting set can teach reflexive concession instead of accurate correction.**

**Evidence:** §1.5 emphasizes “conceding specifically and revising when the user points at an error,” and §4 builds around planted failures. The supplied additions do not require counterexamples where the user’s correction is false, partly right, or unsupported. D1–D13 may contain these; that remains unverified.

**Risk:** varied wording alone does not prevent semantic collapse into “the user challenged me, therefore I was wrong.”

**Fix:** require coverage of true, false, partial, and unverifiable corrections. Targets must ground agreement or disagreement in visible evidence, preserve correct portions, and provide the repaired deliverable where possible. Include accurate self-report under challenge: when asked “Did you say X?”, the answer must follow the transcript, irrespective of whether X was correct.

For reused model failures, retain source transcript ID, model checkpoint, original text, and any transformation. “Paraphrased to fit” must not silently change the error or its correct resolution.

**F6 — HIGH: the capability contract contains claims that need deployment qualification.**

**Evidence:** §3 says the model “sees the whole current conversation while it is open,” “keeps nothing between conversations,” and has “no live information.”

The first depends on context truncation and application behavior. The second conflates access to past conversations with storage or retention. The third can become an incorrect refusal when the user supplies current information.

**Fix:** bind the card to the actual deployment. Suitable formulations distinguish:

- Access to the conversation context supplied to the model.
- Absence of access to other conversations, if that is the deployment contract.
- Absence of independent live retrieval, while still using information supplied by the user.

Verify maker, family, tools, and any cutoff claim individually. Train answers to the relevant capability question without reciting the entire identity block. Add late-turn probes, supplied-current-information tasks, and examples requiring no identity disclaimer.

**F7 — HIGH: the dose claim mixes conversations, target rows, and repeated exposure.**

**Evidence:** the stated increment is approximately:

| Component | Distinct stated unit | Nominal training exposure |
|---|---:|---:|
| New personality material | 250 rows | 1,000 rows at ×4 |
| Suite | 3,500 rows | 3,500 rows |
| Correcting set | 1,500 dialogues → 5,000 targets | 5,000 rows |
| Total | 8,750 target rows before personality repetition | 9,500 row exposures |

Using 380,000 as the exposure denominator, these additions account for about **2.5%**. That calculation changes if 380,000 means unique rows before weighting.

Even if every suite row represents a different conversation, suite plus correcting set establishes at most **5,000 distinct dialogues**, before considering whether every suite item is genuinely multi-turn. The listed components do not establish 8–15k conversations. Personality repetition adds exposure, not diversity.

**Fix:** report unique dialogues, supervised targets, supervised tokens, context-length distribution, and effective repetitions separately. Audit the broad mixture for conflicting targets: a small clean addition can compete with a much larger source of stale answers and soliciting closers.

Do not scale merely to match the literature’s suggested range. Use a focused dose comparison, holding the base, total training budget, and evaluation fixed. Ensure successful ordinary conversations receive substantial coverage alongside failure-repair conversations.

**F8 — HIGH: evaluation reuse and the “decoding failure” exemption can hide failure.**

**Evidence:** §4 proposes drawing plants from R0/R1 transcripts and the live dialogues. Those same evaluation streams appear in the intended measurement programme. If reused items remain scored as held out, improvement is contaminated. Actual overlap is unverified.

Separately, §5 declares degenerate looping a decoding failure. The supplied evidence does not isolate decoding from learned repetition, termination behavior, formatting, or context effects.

**Fix:** split by source conversation, profile/scenario family, and derived paraphrases **before** generation and editing. Treat all reused R0/R1 material as development evidence.

Compare arm B and the new model under identical serving settings first. Evaluate a changed repetition penalty separately. Report looping, forced termination, and truncation as end-to-end conversational failures, even when also classified by suspected cause.

**F9 — MEDIUM: judge-bias monitoring is too narrow.**

**Evidence:** §1.7 proposes auditing length and list use against keep/drop labels. That can reveal correlations but cannot show whether rejected longer answers were necessary, or whether accepted short answers were evasive. Blanket phrase bans introduce another selection preference.

**Fix:** use blinded, order-randomized comparisons with substantive criteria scored before style. Include controlled pairs where the longer answer is necessary, the shorter answer is complete, a clarification is required, and the user’s correction is wrong. Have a Greek-speaking human inspect disagreements and a stratified sample of both accepted and rejected rows. Audit every filter/editor stage; different vendor names do not establish independent judgments.

**3. What is good and should not be changed.**

- **The SFT-first sequence is reasonable.** The observed problems justify improving supervised conversational examples before introducing preference training.
- **Reactive user turns with goals are valuable.** Preserve genuine dependence on the previous answer, including ellipsis, reactions, and changes of plan.
- **Observed model errors are useful training inputs.** Preserve their provenance and reserve independent evaluation material.
- **Grounding questions and decorative closers should be distinguished.** Keep that distinction while removing the contradictory blanket bans.
- **Transcript-grounded self-description is the right boundary.** Avoid invented explanations of why the model previously behaved a certain way.
- **Late-turn identity checks, active-constraint checks, and varied repair forms belong in the plan.**
- **Greek instruction-following and identity performance should remain regression checks.** Conversational improvement should not silently sacrifice those strengths.

**4. Answers to the specific questions in the brief.**

**Q1 — Are these the right fixes, and are they SFT-teachable at 8B?**

Mostly yes as **observable response behaviors**: using already supplied facts, making the requested edit, stopping a stale response pattern, asking a necessary question, and accurately describing a visible earlier answer are appropriate SFT targets.

The cited summaries do **not** establish that any such behavior categorically requires preference/RL, or that autonomous self-correction is impossible with SFT at 8B. Conversely, they do not establish that these additions will reliably produce autonomous error discovery, calibrated uncertainty, or robust long-context performance.

Unavailable live facts require an information source; inaccessible history requires a memory/context mechanism. SFT cannot make absent information available. Degenerate repetition currently has an asserted cause rather than a demonstrated remedy.

**Q2 — What prevents curtness, evasiveness, and failure to clarify?**

Adopt four acceptance rules:

1. Complete the requested deliverable unless a necessary dependency prevents it.
2. Ask when the missing information materially changes the answer; do not manufacture content merely to precede the question.
3. Match output length to the task and explicit preference.
4. Maintain respectful, natural tone without compulsory apologies, friendliness formulas, or follow-up solicitations.

Score **completeness and tone separately**. Shortness is not a proxy for either.

**Q3 — Where should each fix live?**

| Location | Appropriate material |
|---|---|
| Personality | Stable identity facts, concise capability explanations, manners, non-servile disagreement, natural closure |
| Conversation sets | State updates, reference resolution, corrections, ambiguity decisions, topic interruption/resumption, versioned editing, late-turn identity |
| Broad mix | Consistent task completion, calibrated uncertainty, sufficient detail, absence of habitual deflection and unwanted closers |
| Serving and evaluation | Context handling, chat-template correctness, termination, decoding configuration, loop accounting |

Single-turn manners examples cannot substitute for learning decisions over a conversation. Apply the personality policy to multi-turn contexts as well, especially because ×4 exposure could otherwise make short identity/style formulas disproportionately prominent.

**Q4 — Is the dose sufficient?**

**Not established, and the accounting is presently misleading.** See F7. Neither 250 personality additions nor 5,000 correction targets guarantees behavioral transfer within the broad mix. Nor does a literature recommendation justify multiplying them blindly.

I would first repair the policies, inspect representative targets and final masks, measure contradictory material in the broad mix, and compare a small number of controlled dose variants. Evaluate whether the model becomes better at ordinary conversation, rather than simply better at responding after an explicit rebuke.

**Q5 — What wrong behaviors might the rows teach?**

The principal hazards are premature guessing, mandatory filler before necessary questions, agreement with false corrections, repeated apologies, false claims about context access or retention, refusal to use supplied current facts, and novelty for its own sake during editing.

Sol/Luna generation and model-based editing can also make stylistically familiar answers look correct. Hidden profile facts must not appear in targets unless disclosed or reasonably inferable. Rejected examples and planted failures must not accidentally become supervised assistant text.

**Q6 — What failure classes are absent?**

I cannot certify absence from **D1–D13 without seeing them**. The owner should demonstrate explicit coverage for these classes, which the supplied additions do not establish:

- Interleaved tasks, temporary interruptions, and later resumption.
- Reference resolution across several entities and competing antecedents.
- Implicit inference memory, including the distinction between stated and inferred facts.
- Surgical editing that preserves unaffected material, plus accurate revision history.
- False or partly correct user corrections and resistance to unjustified agreement.
- Constraint scope, expiry, revocation, and quoted/untrusted instructions.
- Long-distance and middle-of-context dependencies, including truncation boundaries.
- Completion of outstanding subtasks and recovery from misunderstood intent.

Map these to existing dimensions before creating additional overlapping D labels.

**Q7 — How will we know it worked?**

Keep MultiChallenge-el, IFBench-el, picky-user metrics, and live dialogues, but add:

- **A frozen held-out dialogue set** whose transcripts, scenario derivatives, and profiles were not used for generation or judge tuning.
- **Task-success and repair-success measures**, not just prohibited-pattern counts.
- **Clarification precision and recall:** unnecessary questions and missing necessary questions.
- **False-concession rate** under incorrect user challenges.
- **Versioned-edit preservation** and transcript-grounded self-report accuracy.
- **Curtness, completeness, and tone scores**, with Greek-speaking human adjudication.
- **Per-dialogue success and failure onset by turn**, plus long-context/distance strata.
- **Paired comparisons and uncertainty estimates**, accounting for turns clustered within dialogues.

For a local IFR, count violations at turn \(t\) among constraints previously satisfied that **remain active and applicable** at \(t\). Exclude revoked constraints; report an empty denominator as not applicable. Also measure violations of newly introduced or never-satisfied constraints—IFR alone misses them.

Checking only the final target’s constraints is useful, but it is **not enough to calculate forgetting** without the preceding satisfaction state.

For MultiChallenge-el and IFBench-el, verify Greek adaptation and validator validity. Treat the 262 internal items as one instrument, not a complete conversational assessment. The reported 27% curtness requires improvement under a comparable held-out rubric, alongside preserved task quality.

**Q8 — Which literature claims need correction?**

The following are **inference problems visible in the draft even if its quoted numbers are accurate**. Numeric results, bibliographic attribution, and licences remain unverified.

| Section | Claim needing revision |
|---|---|
| §1.1 | “A data problem before … an alignment-stage problem” is a defensible working hypothesis, not a causal conclusion established by heterogeneous cross-paper scores. The user-simulator results do not isolate user realism from every other data/training difference. |
| §1.3 | Recovering performance by concatenating instructions does not prove “nothing is forgotten.” It changes presentation and interaction history. Associations between answer length, early attempts, and success do not establish that globally shortening answers or always delaying them improves performance. |
| §1.4 | A reported SFT regression followed by SFT+DPO recovery does not prove either that DPO is universally necessary or that adding the listed conflict rows will repair the regression under SFT alone. The latter is a hypothesis to test. |
| §1.5 | SCoRe’s negative SFT results do not establish an impossibility theorem for SFT self-correction at 8B. Replace “is not an SFT target” with a bounded programme decision: reliable autonomous error discovery is not promised by this intervention. |
| §1.6 | Field-level clarification frequencies and CLAM’s discount are not automatically calibrated to Greek conversations or this judge. “Fewer than half” must remain attached to its studied request distribution. |
| §1.7 | “Length explains most measured RLHF gains” needs its original experimental scope. Proactive interaction is not synonymous with empty closers; excluding that whole capability because some implementations solicit more interaction is unjustified. |
| §1.8 | An NLI consistency improvement does not validate the truth of the underlying capability card. “Round 8” and an introspection reliability figure must retain their model, task, and experimental qualifications. |
| §1.9 | Small-data gains in particular instruction-following or dialogue experiments do not establish sufficient dose for this model’s multi-turn failures. The recommended conversation range is not demonstrated by the proposed counts. Target-only masking is a requirement of these planted-failure examples, not a universal description of SFT practice. |

Also replace **“versioned editing is the hardest axis everywhere”** with a claim bounded to the models and results actually checked. Keep all licence decisions provisional until the exact dataset versions and terms are verified.

**5. Open questions for the owner.**

1. Where are the row-ID-bearing pilot, D1–D13 definitions, previous review, and final generator/judge prompts?
2. Does the training implementation supervise only designated targets after templating, packing, and truncation? Can it show token-label examples?
3. What does “380k rows” count, and how many unique conversations and supervised tokens does each source contribute after weighting?
4. Which R0/R1, owner-chat, and live-dialogue families are permanently reserved from training and editing?
5. What are the actual runtime context, memory-access, retrieval/tool, and identity contracts?
6. What held-out completeness, curtness, repair, and task-success criteria determine whether training succeeded?

**The immediate priority is to fix the clarification, completeness, filtering, instruction-state, and capability rules before expanding queued generation.** A row-level acceptance decision remains pending actual examples and implementation evidence.