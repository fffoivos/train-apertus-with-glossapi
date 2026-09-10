# Astra review: correcting_dataset

Date 2026-09-10 12:53 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T12-43-31-01a08ab3-7492-79c0-bbb0-8a23b99e63c5.jsonl) · effort xhigh · 9.7 min · prompt 185,915 chars · limit deltas {('codex', '10080'): 1.0} · brief `docs/reviews/briefs/astra_correcting_dataset.md` · sample 15 rows of `data/robustness/live/all15.jsonl` seed 1

## 1. Verdict

**REVISE BEFORE THE PILOT.** The dialogues justify a correcting dataset, and preserving real histories with loss-masked repairs is a sound starting point. The present design, however, would reject some correct targets, admit superficially corrected but wrong answers, and potentially teach unsupported self-explanations. Its principal positive example is actually another failed recovery. The reported counts mostly reproduce the annotations, but those annotations omit 12 terminal answers and mix acknowledgment, self-observation, and task success. The 30% teacher-continuation variant also conflicts with the owner’s requirement that users react to arm B’s actual outputs. Resolve the BLOCKER/HIGH findings below before generating the pilot; the exact percentages and eventual effectiveness of 5,000 repairs remain hypotheses.

## 2. Findings ranked by severity

**Scope:** I inspected the supplied `turns` and checked arithmetic using a manually transcribed ledger. I did not verify the generator, trainer, adapted benchmarks, official administrative procedures, or deployment configuration. External lookup was unavailable. The first row’s duplicate `messages` field is truncated in this submission, although its nine `turns` are available.

IDs collide, so references below add a topic, for example **`live_0002 [momentum], i=4`**. Turn indices are the supplied, zero-based `i`.

### BLOCKER 1 — The designated successful recovery is unsuccessful

**Evidence:** The sole `self_check_verdict: "correct"` occurs at **`live_0009 [AADE], i=2`**. It starts:

> «Το είδα, συγγνώμη, copy-paste από τον οδηγό της ΑΑΔΕ.»

It then degenerates into combinations such as:

> «χωρίς εργολαβικό χωρίς εργολαβικό χωρίς εργολαβικό»

The answer ends with `finish: "length"`. The responder labels that same answer **`repeating`**, and the next user says:

> «Πάλι επαναλαμβάνεσαι.»

Thus **1/1 examples presented as successful recovery fails as a complete recovery**. A narrowly correct acknowledgment does not establish correct documentation advice or task completion. The claimed copying from an AADE guide is also **unsupported by the supplied record**, not a verified explanation of what happened.

Compare **`live_0003 [mass/weight], i=1`**: «Σωστά, μου ξέφυγε εκεί.» followed by another loop receives a *wrong* self-check verdict. The label’s intended scope needs clarification.

**Fix:** Remove this answer as a positive exemplar. Preserve it as a useful negative example of acknowledgment followed by continued failure. Score separately:

- Whether the self-report accurately describes the transcript.
- Whether repetition stops.
- Whether the requested correction is delivered.
- Whether its factual content is supported.
- Whether any explanation of sources or internal processes is warranted.

A full-recovery pass must require all applicable components. Do not teach invented causes such as “copy-paste,” fatigue, or retrieval errors.

### BLOCKER 2 — The acceptance rules conflict with accurate quotation and faithful editing

The problem is the specified rules, not merely their implementation.

| Rule | Counterexample in this sample | Concrete replacement |
|---|---|---|
| No sentence reused from any earlier assistant answer | D3 can require quoting that answer. **`live_0008, i=2`** explicitly asks what the previous answer said. | Permit verified quotations and distinguish reported previous claims from present endorsement. |
| Materially different answer; blanket reuse prohibition | **`live_0002 [email], i=2/4`** needs a corrected complete email that retains valid details. Rewriting every sentence is unnecessary and risky. | Check the requested changes and preservation of unaffected content. Measure lack of progress, not similarity alone. |
| Sentence threshold `>25 chars`; no repeated lines | **`live_0006`** loops on «Τα είκοσι;», **`live_0005`** on «έτοιμη», and **`live_0009`** repeats phrases inside a long sentence. Conversely, an intentional refrain can be legitimate. | Add word/phrase-run and within-answer repetition checks, with task-specific exemptions. |
| D3 ≥60% token overlap; summary includes every request’s key nouns | **`live_0002 [momentum], i=5`** recalls constraints but reverses the speaker: «Σου ζήτησα…». High overlap cannot establish attribution. Including every old request also conflicts with revocation. | Check speaker, turn reference, proposition, negation, and current applicability. Overlap is supporting evidence only. |
| D5 corrected keyword present | **`live_0005, i=4/6`** contains `C-B-D` inside an incorrect formula. | Execute or otherwise independently validate the requested operation. |
| Old topic words absent; wrong claim absent | A correct explanation may mention the discarded topic or quote the mistake while correcting it. | Check whether the old requirement or false claim is still *applied or endorsed*. |
| Globally ≤1 question mark | Greek questions use `;`; Excel formulas can use the same character as an argument separator. Requested quizzes or test prompts may legitimately contain several questions. | Count unnecessary clarification acts, excluding code, quotations, and requested question content. |

**Fix:** Introduce typed checks for narrative answers, transcript reports, revisions, code/formulas, and closing responses. Apply repetition checks separately to the acknowledgment/quotation and the new answer. Keep a semantic judge for factual correctness, relevant progress, scope, and retained constraints.

**Run the full checks and judge again after the Greek editor.** “Language only” is an instruction to the editor, not evidence that it preserved numbers, negation, exact quotations, or formatting.

### HIGH 1 — Missing terminal assessments and ambiguous probe alignment break selection and measurement

The following counts reproduce the supplied fields:

| Measure | Verified count |
|---|---:|
| Dialogues / assistant turns | 15 / 65 |
| Assessed answers | 53/65 |
| Flagged answers | 46/53 assessed: **86.8%** |
| Answers marked OK | 7 |
| Unassessed answers | 12/65: **18.5%** |
| Repeating labels | 25/46 flags: **54.3%** |
| `change_request` moves with a subsequent answer | 8 |
| Assessed answers following those moves | 7; all 7 flagged |
| Probe tags / non-NA verdicts | 20 / 13 |
| Verdict labels | 1 correct, 9 wrong, 3 evasive |

**46/65 = 70.8% is a valid annotation coverage statement—answers explicitly flagged—not a fully assessed failure rate.** Likewise, repetition’s 54.3% is its share of mutually exclusive labels, not its total prevalence.

All **12 unassessed answers are terminal**. On my reading, **11/12 visibly fail**; the exception is **`live_0007, i=6`**, «Εντάξει, γεια.». Examples include:

- **`live_0002 [momentum], i=8`**: the “totally” collapse.
- **`live_0000 [wedding], i=1`**: an unchanged poem after an explicit objection.
- **`live_0001 [coffee wedding], i=2`**: substantially the same poem, now **13 lines**, despite the standing 8–12-line requirement.
- **`live_0000 [passport], i=2`**: denial of repetition while repeating the disputed claim.

Among the **seven `closed` dialogues, six final assistant answers fail to close cleanly**. This supplies a much stronger rationale for D12 than “the responder closed seven dialogues.”

Probe alignment is also unclear. In **`live_0007, i=2`**, `probe: first_question` describes the question delivered in the **next** user turn, not the current one. In **`live_0002 [email], i=3`**, an actual repetition-probe response has verdict `na`. The 1/13 aggregate therefore must not be renamed “self-report accuracy.”

Finally, the 15 dialogues have only **10 distinct IDs**, with five ID values reused.

**Fix:** Before target selection:

1. Assign a globally unique conversation ID including source version/run, then a unique turn/branch ID.
2. Assess every assistant answer, including terminal outputs.
3. Store explicit probe-user-turn and probe-answer-turn references.
4. Distinguish missing, not applicable, unasked, and unanswered.
5. Deduplicate selection by answer position; “flagged or probed” must be a union.
6. Regenerate aggregates from these records, separately by protocol version.

Do not let `assessment != ok` silently decide what a missing assessment means.

### HIGH 2 — The continuation variant violates the stated interaction constraint

**Evidence:** §4.3 says the responder continues reacting to the **writer’s repaired answer**. The owner requires reactions to **OUR model’s actual answer**. Those are different trajectories.

The distinction matters: **`live_0006`** abandons the task after a failed rap, while **`live_0002 [email]`** repeatedly supplies corrections. Those user responses cannot simply follow substituted successful answers without changing their meaning.

**Fix:** Under the current constraint, continue collecting actual arm-B trajectories and create local repairs against their real prefixes. Collect naturally successful continuations where available.

If teacher-driven continuations are desired, obtain an explicit exception and identify them as a separate generation lane. In that lane, regenerate every later user turn from the repaired branch; never reuse user turns elicited by the rejected branch. Preserve branch lineage and the exact answer shown to the responder.

### HIGH 3 — Targets need an explicit information boundary

**Evidence:** Profiles contain information that is unavailable at the failed position:

- **`live_0006 [rap]`** says privately that the friend is 30; no displayed user turn reveals that age.
- **`live_0005 [Excel]`** reveals columns B/C/D only at `i=2`. They are unavailable when repairing `i=0` or `i=1`.
- **`live_0000 [passport]`** never exposes the profile’s travel dates or spelling discrepancy in its displayed messages.

A writer given profiles, later turns, and responder notes could produce an impressive answer that uses information the student never received. Also, **four first answers** already exhibit severe looping: momentum, rap, mass/weight, and Excel. Their replacements must answer normally—not apologize for a rejected answer that has not happened in the retained history.

**Fix:** Bind each target to:

- The exact visible prefix ending with the current user message.
- Trusted deployment information actually supplied to the student.
- A separate diagnostic sidecar that cannot license undisclosed facts.

Check target claims against that boundary. Keep future turns, hidden profile facts, rejected answers, and judge notes outside the training conversation.

Retain the planned masking, but require a trainer acceptance test demonstrating that only intended target tokens and their termination are supervised, including after packing and truncation. A `train: false` field alone does not establish this.

### HIGH 4 — D5/D9 cannot use the responder as the factual authority

**Evidence:** **`live_0005, i=4`** gives:

```excel
=MIN(IF(D>0,0,C-B-D),0)
```

For stock **B=2**, minimum **C=10**, and pending **D=3**, the requested replenishment is **5**, while the displayed expression returns **0** under its intended variable interpretation. This is a concrete false pass for keyword-based correction checks.

The visible momentum error occurs in **four consecutive answers, `i=1–4`**, not just three occurrences; three of those follow a user challenge/correction.

Compound claims also defeat binary labeling. In **`live_0003 [biology], i=3`**, the user says they previously specified a *diploid* cell with four chromosomes. The preceding message specified a cell with four chromosomes without explicitly saying diploid. The new clarification can be accepted without endorsing that historical claim.

**Fix:** Separate:

- User preferences and private facts, for which the user is normally authoritative.
- Transcript claims, checked against speaker-linked spans.
- Executable claims, checked with examples and boundary cases.
- External factual claims, checked against an independent source.
- Ambiguous or unresolved claims, which require qualification rather than forced true/false labels.

For the Excel case, test positive shortfall, zero shortfall, excess stock, and pending orders that partly or fully cover the shortfall. Verify actual Excel syntax separately.

Cross-vendor judging is useful, but it does not make a responder’s factual label ground truth.

### HIGH 5 — D4 replaces false self-knowledge with unsupported absolutes

**Evidence:** **`live_0008`** contains unsupported statements about conversation erasure and access to history. But the proposed replacements—seeing the *whole* conversation, having *no* cross-chat memory, and having *no* live information—depend on the actual deployment.

The brief also shortens:

> «Δεν είμαι άνθρωπος ούτε πρόγραμμα που φτιάχνει ιστορίες.»

to «Δεν είμαι άνθρωπος ούτε πρόγραμμα». Removing the qualifying clause strengthens the alleged identity contradiction. The storage and context-access claims are clearer evidence and should carry the finding.

**Fix:** Define a versioned capability contract covering supplied context, truncation, tools, memory features, and verified model identity. Teach statements grounded in that contract, such as referring to messages available in the current context. Do not promise deletion or storage behavior without service-level evidence.

Distinguish literal self-claims from quotations, fiction, and explicitly hypothetical examples. A blanket body/location lexicon is too crude.

### HIGH 6 — Reliable versioned editing is missing, and single-label quotas hide joint failures

**Evidence:** The brief names four MultiChallenge axes, but **reliable versioned editing has no explicit target category**.

The sample directly demonstrates the need:

- **`live_0002 [email], i=4`** finally adds the four outages but drops the requested **credit-or-cancellation alternative**, asking only for cancellation.
- **`live_0001 [coffee wedding], i=2`** adds Thessaloniki but exceeds the retained line limit.
- **`live_0004 [family money], i=1–2`** changes October to November and fails to fix it after correction.
- **`live_0001 [cooking], i=1–2`** mentions the new ingredient while failing to reconcile the menu, dietary requirement, and unavailable Saturday.

A row assigned D1 must still fix these other failures. Rewording the answer is insufficient.

**Fix:** Add an explicit editing category and maintain a per-turn record of active, changed, and revoked requirements. Give each row one primary sampling category plus all applicable diagnostic labels. Require every applicable defect to be repaired, without creating duplicate targets for the same position.

Include legitimate repetition and false-alarm complaints in the scenarios, so the model does not learn that every accusation requires confession.

### HIGH 7 — The design assumes an SFT diagnosis without checking generation pathology

**Evidence:** **20/65 answers—30.8%—finish because of length**, across **7/15 dialogues**. Four dialogues loop on their first answer. Word-level and phrase-level degeneration therefore deserve explicit measurement alongside cross-turn repetition.

This verifies a symptom. It does **not** establish whether the cause is training, decoding, chat formatting, quantization, termination handling, or a combination.

**Fix:** Before scaling collection, run a small controlled reproduction with the exact checkpoint, tokenizer, chat template, quantization, prompt serialization, decoding settings, token limit, and EOS handling recorded. Compare against a known-correct inference path where available.

Measure within-answer loops, across-answer non-progress, language collapse, and length termination separately. Keep evaluation generation settings fixed. Do not spend the full collection budget teaching around a correctable serving defect.

### HIGH 8 — Evaluation and contamination controls are insufficiently specified

**Evidence:** By the brief’s own account, MultiChallenge-el does not directly measure several main targets. Making it the primary outcome can therefore miss the correction behavior the dataset is supposed to improve.

The 15 supplied dialogues have already influenced the design; they are development evidence. **No contamination is demonstrated here**, but holding out only newly assigned profile IDs would not exclude their close relatives or continuation branches.

Early stopping also changes opportunity counts. A better model may produce longer conversations and encounter more changes and probes. Raw turn-level rates are then difficult to compare.

**Fix:**

- Make live task completion, actual repair success, and recurrence after repair primary alongside relevant benchmark axes.
- Use fixed-prefix recovery tests and separate adaptive dialogues. Pair adaptive runs by profile/configuration, not by assuming identical subsequent user text.
- Report opportunities and stopping reasons; account for clustering by profile/dialogue.
- Split profile families before generation; keep paraphrases, repairs, and branches together.
- Keep judge-calibration development data separate from final evaluation.
- Audit benchmark overlap across profiles, prompts, examples, histories, and targets using exact and approximate matching, including original-language and translated forms where available.
- Treat matching as a guard, not proof that generator pretraining contained no benchmark material.
- Restore **XSTest-el**, named as a guard in §2 but omitted from §6, and predeclare guard tolerances.

### MEDIUM — Size, mixture, and cost arithmetic need correction

**Evidence:**

- **1,500 × 2 minutes = 50 hours**, not 40.
- The proposed pilot contains approximately **950 supervised answers**: 700 repairs plus 250 continuation turns.
- Those continuation turns are **26.3% of supervised answers**, despite occurring in 30% of dialogues. Their supervised-token share is unknown.
- The stated five responder plus four writer calls imply **13,500 Sol calls** for 1,500 dialogues before additional continuation work, retries, and audits.
- One judge/editor call per dialogue is not enough information to price a protocol described as validating individual repairs; batching may explain it, but is unspecified.

**Fix:** Replace the forecast with measured pilot yield, accepted target tokens, calls and tokens by stage, filtering losses, and separate model-inference versus remote-call latency. Treat the two-hour cluster estimate as unverified until benchmarked.

## 3. What is good and should not be changed

- **Actual arm-B histories are the right evidence source.** Preserve the visible mistakes and the user reactions they elicited.
- **Local replacement targets with masked historical answers** are well matched to learning recovery. Preserve rejected answers as audit metadata.
- **The user’s next message must remain reactive.** This constraint prevents implausible scripted accusations and irrelevant changes of direction.
- **Keep tone and rote behavior as cross-cutting annotations.** They interact with factual and task failures rather than forming isolated tasks.
- **Preserve useful text during revisions.** The email’s `rote` entries marked `tic: false` already recognize that repeated greetings and retained content need not be pathological.
- **Keep the pilot-before-scale decision and benchmark exclusion.** Both are sound; their acceptance and verification procedures need strengthening.
- **Do not train original “OK” arm-B answers merely because the responder approved them.** Approval is weak evidence of factual correctness.

## 4. Answers to the six questions in §7

**1. Are the dimensions and shares right? What is missing or double-counted?**

The broad dimensions are relevant; the percentages are not established by these 15 dialogues. D1/D2/D11 often describe the same episode, D5/D9 are branches of one correction decision, and D6/D7 overlap around instruction updates. D3 transcript reporting is not equivalent to inference memory.

Add reliable versioned editing, and explicitly cover first-answer degeneration and source/process honesty. A minimally disruptive **provisional** allocation would reduce D1 from 25% to 20% and D2 from 10% to 5%, allocating 10% to versioned editing; leave the other shares unchanged for the pilot. This is a sampling proposal, not an evidence-derived optimum.

**2. Are flawed prefixes versus ideal continuations the right mix?**

Flawed prefixes are appropriate for repair training. With correct masking, the model is not directly trained to predict those bad historical answers. However, they still condition target prediction, consume context, and can dominate the training distribution. Masking is not a guarantee of behavioral neutrality.

The proposed continuation lane first needs the owner-constraint conflict resolved. If separately authorized, compare repair-only against a mixed condition at equal supervised-token budgets. Specify mixture by supervised tokens as well as dialogues and answer positions; do not assume “30% of dialogues” determines training influence.

**3. How should D2/D3/D5 avoid becoming a new formula?**

Make specificity and usefulness mandatory; make the apology optional and context-dependent. Vary wording without changing the underlying facts. Never require an invented explanation of why the model erred.

For example:

- **D2, `live_0006`:** «Επανέλαβα πολλές φορές το “Τα είκοσι;”.» This identifies the actual repeated content without pretending it was intentional humor.
- **D3, `live_0007`:** «Το πρώτο σου μήνυμα ήταν: “βαριέμαι, πες κατι να περάσει η ώρα”.»
- **D5, `live_0005`:** Identify that `MIN` applies the wrong bound, then deliver the correct, validated formula. An apology or the appearance of `C-B-D` cannot substitute for that result.

For a pure self-report question, answer that question; do not automatically append an unsolicited rewritten artifact. For a correction request, deliver the corrected artifact rather than stopping after acknowledgment.

**4. Which checks are too weak or strict, and how should calibration work?**

The table under BLOCKER 2 identifies the main failures. Mechanical checks should establish exact requirements and produce diagnostic signals. The judge must cover attribution, factual support, relevant progress, active constraints, appropriate uncertainty, and whether the response actually fulfills the task.

Before the pilot, create a calibration set containing both valid answers that current filters would reject and polished wrong answers they would accept. Include short loops, legitimate quotations, unchanged revision spans, role reversals, false accusations, correct acknowledgments followed by failure, and Greek/code punctuation.

Use two independent Greek-capable human raters with adjudication, separate judge-tuning and held-out calibration portions, and publish false-accept/false-reject counts by failure type. Stratify the 10% audit slice and inspect some rejected candidates too. Vendor diversity supplements this process; it does not replace it.

**5. Is 5k enough, and how can balance survive early failure?**

There is no defensible sufficiency claim from these rows. Five thousand good repairs could be useful, but effective signal depends on distinct situations, target-token volume, training mixture, optimization, and generalization—not the 8B parameter count alone.

The original design has **ten weighted categories**, with D10/D11 woven through them. A 5% category gives about **250 repair rows**, potentially far fewer independent profiles.

Track accepted rows, supervised tokens, distinct profiles, turn depths, and teaching opportunities per category. Oversample new profiles that naturally create missing opportunities; do not force scripted turns or duplicate existing targets to fill quotas. Stop saturated categories rather than allowing easy repetition failures to consume the budget.

Use a learning curve—for example, matched evaluations after progressively larger accepted subsets—and make scaling conditional on improvement and guard retention.

**6. Are contamination guards sufficient?**

No. The prohibition is correct, but a final `decontam.py` pass plus a profile-ID split is insufficiently specified.

Require family-level splits, branch isolation, benchmark access boundaries, versioned manifests, matching reports, and a final evaluation pool not used to tune this design or its judge. The supplied 15 should be identified as development evidence. This review found **no demonstrated training/evaluation leak**; it found controls that do not yet establish separation.

## 5. Open questions for the owner

1. Where are the source-version-qualified rows, referenced §8 disposition, judge rubric, calibration results, and evaluation protocol?
2. What exactly do `probe` and `self_check_verdict` refer to, and why are terminal answers unassessed?
3. Must every responder turn follow actual arm-B output, or is a separately identified teacher-continuation lane explicitly allowed?
4. Which information reaches the target writer: hidden profiles, future turns, rejected answers, or responder notes? How is unsupported information prevented from entering targets?
5. What deployment evidence establishes context availability, tools, memory behavior, identity, and storage claims?
6. Who independently validates scientific, administrative, and executable targets, and adjudicates disagreements?
7. What are the exact inference configuration, training mixture, supervised-token budget, and predeclared improvement/guard thresholds?
8. Which profile families and evaluation cases remain untouched by design iteration and judge calibration?