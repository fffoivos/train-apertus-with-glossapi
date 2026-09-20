# RLHF feedback for Opus — 17 September 2026

Status: review notes for handoff, not an instruction to launch jobs. The user requested preservation of the mathematics feedback and is discussing dialogue changes. Maths proposal is recorded below; dialogue design and numerical pilot choices remain recommendations. Distribution remains a separate open review topic. No production prompt, data or training configuration was changed by creating this file.

## 1. Mathematics judging

### Evidence

Reviewed data/rlhf/prompts/judge_rank4_v2_en.txt, rubric v2.4. The general judge says:
- Do not solve the task yourself first (line 47).
- “Right in the main” and minor imprecision can qualify for reinforce (lines 16, 25, 38).
- Mathematical quality competes with general personality and style preferences.

Round 2 examples:
- g2:R2B1_006 sample 4 (zero-based k=3): reinforce despite the false equality “8 + 6 + 5 = 19 + 5 = 24”. Other candidates, including sample 3, give a correct full solution. Select an existing clean response rather than promoting this flawed one.
- g2:R2B12_005 sample 5 (k=4): average 14.9 is correct, but “You need 15 points out of 20” does not resolve the likely intended gap. Clarify whether the prompt asks for 0.1 average points or 0.4 total marks; do not silently repair its ambiguity in scoring.

### Proposed priority

Use ordered criteria, not a weighted average that lets style compensate for incorrect mathematics:
1. Correct interpretation and requested results.
2. Valid mathematical statements, calculations and reasoning.
3. Completion of all requested parts.
4. Clear notation, readable explanation and appropriate detail.
5. Stylistic polish.

A clean, terse correct answer can qualify when only an answer was requested. A proof/worked-solution request requires the requested justification. Correct final results do not excuse invalid derivations. Harmless numbering or language imperfections do not disqualify a mathematically correct response. A false equation is not a cosmetic typo merely because the final answer is correct.

Keep benchmark final-answer accuracy separate from positive-target eligibility.

### Proposed maths judge instruction

Evaluate these replies primarily for mathematical correctness and completion of the user's actual task.

Establish the requested quantities, assumptions, domain restrictions and acceptable answers. Use the independently verified solution supplied with the problem, but flag any inconsistency rather than treating the reference as infallible.

For each candidate, assess separately:
- Whether every requested final result is correct.
- Whether the mathematical statements and steps it presents are valid.
- Whether it completes the requested task.
- Whether its explanation is understandable and proportionate.

Accept equivalent expressions, alternative valid methods and justified approximations. Check units, signs, rounding, missing cases and whether the answer addresses the quantity actually requested.

A wrong result or invalid mathematical step cannot be compensated for by fluency, confidence, length or attractive formatting. A correct final result with an invalid derivation is not eligible as a positive worked-solution example.

Do not require a derivation when the user asks only for an answer. When the user requests a proof or worked solution, a bare correct answer is incomplete.

Ignore harmless stylistic imperfections. Distinguish a numbering typo from a false equation. If the problem is ambiguous or correctness cannot be established, flag it for review rather than forcing a positive verdict.

Rank candidates by correctness, mathematical validity and task completion first; use clarity and concision to distinguish otherwise comparable answers. Several candidates may qualify, or none may qualify. Report the decisive error or verified difference.

### Implementation and validation proposal

- Route mathematical content to this specialist rubric, including maths embedded in everyday/forum/dialogue tasks, not only rows labelled math.
- Verify each problem once without candidate replies in the verifier's input. Reuse the result across candidate batches. A single judge call that already contains candidates is not a genuinely blind reference solve.
- Use arithmetic/symbolic checks where applicable, independent mathematical review for proof validity, and an unresolved state for disagreements. A model-produced reference is not automatically ground truth.
- Record outcome correctness, reasoning validity, task completion, error evidence, confidence and positive eligibility separately. This needs schema/consumer integration; adding fields to the text alone is insufficient.
- Freeze a new rubric identity; retain prior results. Rejudge the existing 20 generated maths prompts and all their candidates before new generation.
- Check whether judgement changes reflect real errors, not stylistic perfectionism. Wrong attempts can be ranked for diagnosis without becoming positives.

Research context: https://arxiv.org/abs/2305.20050 compares outcome and process supervision for mathematics. It motivates checking worked reasoning, not a claim that this exact pilot recipe is proven.

## 2. Dialogue user behaviour: repeated requests versus adaptive help

### Verified ME021 evidence

Latest snapshot in data/rlhf/dialogue_quality_depth/runtime/measurement/trajectories.jsonl:
- Five assistant turns; terminal_code=context_limit.
- Initial request: 240–300-word story, quiet librarian, folded map in a rooftop greenhouse; significance revealed through dialogue.
- User turns 2 and 3 mainly restate the dialogue requirement.
- Turns 4 and 5 add exclusions of the repeatedly reused manor/father/hidden-passage plot.
- Turn 6 finally supplies a concrete alternative: the map locates rare plants that must be saved before demolition.
- The next assistant completion was not generated: 2,597 input tokens plus the 1,500-token requested output allowance exceeded the configured 4,096-token context by one token. This is a scheduling/context-reservation cutoff, not evidence of failure on the helpful final request.

The user simulator in data/rlhf/dialogue_quality_depth/user_policy.txt asks it to advance the task naturally and correct visible errors, but lacks explicit repeated-failure strategy, user knowledge limits and an abandonment condition for unresolved tasks. Its completion rule alone can keep an unsatisfied user restating requests.

### User's proposal

After repeated failures an ordinary user may explain by example, decompose the task or provide a scaffold. Example for ME021: show two short lines of actual character dialogue and ask for a story developed in that form. Try alternative assistant replies at the first serious error; if none improve enough, try again after the user's helpful follow-up.

### Recommended simulator changes

- Track what failed, what the user has already tried, user expertise, patience and what new information the next turn contributes.
- After one unsuccessful restatement, normally change strategy: point to a precise defect, give a short example, break the task into parts, supply missing context, narrow the scope, or abandon naturally.
- Do not make every user a competent tutor. Vary willingness/ability to diagnose errors. Some users ask clarification, become frustrated, accept imperfect progress or leave.
- Give examples only from the user's plausible knowledge and visible conversation. No hidden reference-answer or judge-label access.
- A creative user's invented story detail is a new preference, not leaked ground truth; record when it narrows the task. Do not silently pretend it was required earlier.
- Retain occasional repeated requests as realistic behaviour, but not as the default response to every failure.
- Avoid converting all recovery into copying a complete solution supplied by the user.
- Add terminal reasons for abandonment/unresolved task. Preserve original intent and safety boundaries.
- Track assistance level: restatement, pointed defect, partial scaffold/example, supplied solution. Report results separately.

Illustrative revised ME021 turn after repeated failure:
«Πάλι περιγράφεις τι έμαθε αντί να το δείχνεις σε διάλογο. Εννοώ κάτι σαν:
— Γιατί έχεις κυκλώσει αυτά τα φυτά στον χάρτη;
— Αύριο γκρεμίζουν το κτίριο. Αν δεν τα μεταφέρουμε απόψε, χάνονται.
Χρησιμοποίησε αυτό ως παράδειγμα του είδους διαλόγου που ζητάω και γράψε μια νέα ιστορία 240–300 λέξεων με τον βιβλιοθηκάριο και το θερμοκήπιο.»
This is a proposed replacement branch, not a claim that the recorded user said it.

## 3. Context errors and what DPO trains

For a recovery example:
- prompt x = original conversation, including actual earlier bad assistant replies, plus latest user follow-up.
- chosen/rejected = two alternative next assistant replies to exactly the same x.
- Score only chosen/rejected completion tokens. History is conditioning input, not a positive target to imitate.

The objective trains a preference conditional on a flawed history; it does not directly reward producing those earlier flaws. However, context influences the computation and gradients through shared parameters. “Masked” does not mean history has no effect, nor that prefill is a separate model. A corpus dominated by error-filled histories can still skew the contexts on which the model learns to act.

Current export_pairs.py and resample.py declare completion-only masking in their receipts. That is not proof of the eventual trainer's behavior. Verify the actual tokenized batches and loss mask: historical assistant tokens excluded, target reply included, identical prefixes in both alternatives, no hidden truncation or unintended full-chat SFT loss. Current export evidence does not establish this integration gate is closed.

Technical reference: https://huggingface.co/docs/trl/dpo_trainer (conditional preference objective and explicit prompt/chosen/rejected format).

## 4. Branch selection: prevention plus supported recovery

Separate three decisions:
1. How natural raw trajectories are generated.
2. Which prefixes receive additional candidate replies.
3. Which verified preference pairs enter training.

Recommended first pilot:
- Generate complete raw trajectories with the revised user policy, one unselected Apertus reply per assistant turn; stop naturally or at a declared context/horizon limit. Keep all assistant history authentic.
- Annotate the observed turns and retain the full quality-by-depth record BEFORE deciding which prefixes to resample. Do not replace raw failed replies with selected winners in this measurement pool.
- At the first serious error, branch from the prefix immediately BEFORE that assistant response. This teaches prevention of that error at that point; no bad reply needs to appear in this prefix.
- Start with 4 new candidates; extend to 8 if no verified acceptable candidate. A proposed 8-candidate initial budget is an experimental choice, not an optimum. Existing evidence shows some successes require 12–16; no success at 8 is not proof of incapacity.
- Next branch after a naturally helpful user follow-up in the original trajectory. Its prefix contains the original bad reply, not a sampled winner.
- Prefer allocating extra sampling there when the first prefix remains unsuccessful, but also sample helpful follow-ups for a preselected subset of successful first-prefix cases. Otherwise “recovery” gets only the hardest cases and its yield cannot be compared fairly with prevention.
- For a small comparison, evaluate both prefixes on the SAME 12 eligible conversations with the same 8-candidate budget per prefix (192 new replies maximum, not authorized by this note). Keep this diagnostic separate from a later adaptive production scheduler.
- Where a restatement is already available, compare it with a helpful-follow-up branch from the same failed history. All compared branches must preserve prior history; only the user follow-up differs. Log extra information/task simplification, so improved success is not mistaken for pure self-correction.
- Require a correct/acceptable chosen reply and a meaningful preference gap, not merely improvement relative to nonsense.
- Keep each chosen/rejected pair within one exact prefix. Never pair an answer before a hint against an answer after a hint.
- First-turn prevention belongs in the single-turn share. Keep deeper recovery examples from those same conversations when valid; do not discard a trajectory because its first error occurred at turn 1.
- Include healthy deeper continuations as well as failures. A successful prevention branch does not by itself demonstrate sustained improvement; test later dialogue on fresh trained-model rollouts.
- Keep all branches, translated variants and related source families in the same train/eval split. Cap per-conversation contribution.

If a future production process stops early or preferentially continues failures, it cannot claim an unbiased full-depth distribution. Keep a separate randomly selected full-rollout measurement cohort. The present user's requirement for full quality-by-depth information takes precedence over cheap early-stopping shortcuts.

## 5. Dialogue coverage to broaden

Keep user task and interaction behaviour as distinct axes:
- Collaborative writing/editing with examples and revisions.
- Planning under changing requirements.
- Troubleshooting with user-reported observations.
- Explanation/tutoring with partial understanding.
- Source-grounded questions and uncertainty.
- Ordinary conversation/opinion and interpersonal assistance.
Cross these with clarification, adding information, constraint retention, changed goals, justified correction, false correction, partial success, frustration and natural completion. Route comparisons and notice editing are useful but insufficient proxies for all dialogue.

Current 24 exported pairs come from 16 trajectories; 4 are depth 1. Do not count all 24 as independent multiturn cases or inflate their weight to meet the dialogue quota.

## 6. Distribution issue — recorded, still open

Round 2 has 407 prompts: 374 el and 33 en. Other target languages are absent in that single-turn round. Category acceptance rates differ, so impose and report quotas on accepted pairs as well as on generated prompts. Preserve forum-source diversity and avoid excessive narrow-hobby representation. The previous 500-pair pilot and language/category counts are proposals, not a launch authorization.

## Handoff boundaries

This feedback file is for the user to pass to Opus. No message was sent, no API/cluster generation was launched, no rubric was replaced, and no existing results were overwritten. Dialogue recommendations require implementation and comparison; do not record them as validated improvements.


## Owner clarification after review — agreed user model and sampling interpretation

The owner explicitly endorsed an adaptive user model: after failure, a user may explain with an example, break the task into steps, express frustration, simplify the request or abandon it. Treat this behavioural principle as agreed. The exact mixture, transition probabilities and pilot sizes remain to be determined and tested.

Clarification of the proposed sampling workflow:
1. Generate and retain the natural conversation first, with one unselected Apertus response per assistant turn and the adaptive simulated user. Stop at natural completion/abandonment or the declared horizon/context limit.
2. Annotate the observed conversation for serious errors, helpful user interventions and healthy continuations.
3. Select one or several saved prefixes for additional alternative assistant replies. For prevention, the prefix ends immediately BEFORE the first seriously erroneous assistant reply. For supported recovery, it ends AFTER the first genuinely helpful user suggestion, if one exists.
4. These are alternative sampling points on the same recorded trajectory, not a requirement to interrupt or truncate it at its first error. Each point gets its own same-prefix preference pair.
5. Do not overwrite the original assistant history with sampled winners or attach an old suffix to a changed response as if it were a natural continuation. A continuation from a replacement response is a new branch whose user turns must be generated afresh.
6. Selecting both points permits within-conversation diagnosis; production may allocate samples adaptively, while retaining a full-trajectory measurement cohort. Absence of a helpful suggestion is recorded rather than filled with a forced artificial hint.

This clarification records the discussion; it does not authorize generation spending or make the proposed numerical pilot an accepted requirement.


## Separate reference-guided demo requested by owner

The owner requested a demo of reference-guided writing, troubleshooting and learning before review, explicitly additional to the first experiments. See REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md in this directory for six concrete cases, access separation, reporting and execution prerequisites.

The six conversations receive no experiment quota credit and remain training-ineligible development data. First-experiment sizes remain unchanged. Their provider costs, when executed, still count against the shared spending ceiling. Status: specification prepared for Opus; not executed.


## Consolidated dialogue execution plan

Start with DIALOGUE_V2_EXECUTION_PLAN_20260917.md for the three dialogue directions: adaptive user behaviour, sampling at saved prevention/recovery/healthy prefixes, and the separate reference-guided category demo. It defines implementation, offline gates, a four-conversation improvements diagnostic plus six distinct demo cases, budget checks and the owner-review stop. Maths judging and global distribution remain separate workstreams. No execution was performed when writing this plan.


## Consolidated handoff — maths and dialogue as two work items

Owner instruction: group all dialogue-specific feedback as one point alongside the maths work. Use these two work items for the handoff; the earlier sections retain their supporting evidence and discussion.

1. **Mathematics evaluation corrections.** Introduce a specialist rubric that prioritises correct interpretation/results, valid reasoning and task completion before clarity and stylistic polish. Independently verify the problem/reference without seeing candidate replies; references can themselves be wrong. Check calculations, intermediate steps, units and applicable cases, not only the final answer. A false mathematical statement or invalid derivation is not excused as stylistic imprecision. Accept equivalent valid methods and harmless language/formatting imperfections. Require a worked solution only when the task calls for it. Flag ambiguity and unresolved correctness rather than forcing a positive. Keep benchmark answer credit separate from eligibility as a positive training target. Apply this to mathematical content across task categories, integrate the structured findings into the export gate, and rejudge the existing 20 generated maths prompts and their candidates under a new recorded rubric before scaling.

2. **Dialogue generation and preference collection improvements.** Treat the following as components of one dialogue work item: (a) adaptive users who can explain, give examples, decompose, simplify, express frustration, accept progress or abandon instead of endlessly repeating; (b) full natural trajectories followed by selection of saved prefixes before first serious error, after helpful guidance and during healthy continuation, with same-prefix preference pairs and completion-only loss; (c) broader reference-guided conversation types, first tested as a separate six-conversation writing/troubleshooting/learning demo with role-appropriate access to desired outcomes, hidden world state and learner knowledge. See [DIALOGUE_V2_EXECUTION_PLAN_20260917.md](DIALOGUE_V2_EXECUTION_PLAN_20260917.md) for the implementation, four-case improvements diagnostic, separate six-case demo, budget checks and owner-review gate. All development conversations are additional to the first experiments and do not reduce their sizes or quotas. No automatic training promotion or scale-up before review.

The overall task/language distribution question remains a separate open item; it is not implicitly settled by either work item. This consolidation changes the handoff organisation only, not code, prompts, generated data or execution status.


## Two-stream orchestration plan

Use [RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md](RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md) as the top-level handoff. Main executor owns maths correction, retaining valid old judgements, cumulative collection and DPO readiness; a second Opus/Sol owns the dialogue plan and separate demo. Maths details are in [MATH_JUDGING_EXECUTION_PLAN_20260917.md](MATH_JUDGING_EXECUTION_PLAN_20260917.md). Active maths verdicts are superseded, not blindly accumulated; development demos never reduce first-experiment quotas. Existing approved target sizes take precedence over provisional pilot suggestions.
