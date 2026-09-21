# Workstream A: mathematics judging correction

Date: 17 September 2026
Owner: main execution agent (Opus or Sol), who also owns orchestration and final dataset integration.
Parent plan: RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md.
Aspect: [RLHF] (judging). Its only prompt-generation touchpoint is A1: a corrected or clarified maths prompt becomes a new prompt version, which is prompt generation.
Status: planned; no new rubric, judgement or training result has been produced by writing this plan.

## Objective

Correct the mathematical preference signal while reusing existing prompt/response samples. Supersede affected verdicts in the active dataset, retain historical evidence, then apply the corrected method to new mathematics judgements.

Read OPUS_FEEDBACK_20260917.md section 1 and its concrete proposed maths prompt. Do not merely append a maths paragraph beneath contradictory general instructions: use a distinct, versioned specialist rubric with explicit precedence.

## A1. Inventory and quarantine affected active judgements

- Scope = all pre-existing mathematics, because the maths evaluation changes (owner, 17 Sept): every inventory record with `maths_rejudge_required` (`data/rlhf/pool/inventory.jsonl`; 77 on 17 Sept): round 2's 20 generated maths prompts, round 1's maths prompts (from defunct generator 0.1; rejudge only if the owner keeps them), forum calculation and mathematica posts from both rounds, and the pilot dialogues with arithmetic.
- Start with the 20 generated Round 2 maths prompts (18 Greek, 2 English) and all their saved candidates.
- Scan metadata and content for mathematics embedded in forum, everyday, planning and dialogue requests across pools intended for this DPO run. Export a reviewable scope manifest; do not rely only on the slice label.
- Preserve prompt IDs/text hashes, exact prefix hashes, candidate IDs/text hashes, model SHA, sampling settings and original judgement versions.
- Pending specialist review, affected records cannot continue to contribute an old positive to the active training view.
- Keep known ambiguous prompts on hold. Correcting a prompt creates a new prompt version requiring fresh target replies; do not attach old replies to altered wording.

Deliver: maths_scope.jsonl and a short scope summary, including coverage gaps.

## A2. Verification (superseded 17 September 2026)

**Owner decision, 17 September:** there is no separate reference stage. The specialist judge does the mathematics itself: with the maths-v2 prompt it writes its own worked solution and the question status (determinate, ambiguous, underspecified, unresolvable) before it may say anything about a candidate, and only then evaluates the replies. The independence that matters is preserved inside the prompt: the judge must commit to its own solution and is told that several candidates agreeing is not evidence.

What was built before this decision, and is withdrawn: two independent blind solves per prompt plus a comparison call (maths-v1). It cost 921 high-effort calls, and the second solve changed the outcome on 13 of 307 references (4%). The 246 round-3 references already built are kept as an offline cross-check, not as a gate. The paragraphs below describe that withdrawn design and are retained as the record of what was done.

## A2 (withdrawn). Verify references independently

- Solve/check each problem without candidate replies in the reference verifier's input. Use supplied solutions only as checkable evidence, not unquestionable gold.
- Record requested quantities, assumptions, domain, units, acceptable equivalent forms, precision/tolerance and the level of explanation requested.
- Verify arithmetic or symbolic results with executable checks when applicable. Numerical spot checks alone are not proof of a general theorem.
- For proofs, verify the argument independently. For unresolved disagreement, quarantine the case rather than invent certainty.
- Cache verified references by exact prompt/context version. A new user hint or changed premise may require a new reference even if the topic is unchanged.
- Never feed private verifier answers into Apertus prompts during on-policy candidate collection.

Deliver: references.jsonl with evidence, provenance and verified/ambiguous/unresolved status.

## A3. Implement the specialist judge and export contract

Priority order:
1. Correct interpretation and requested results.
2. Valid mathematical statements and reasoning.
3. Completion of the actual request.
4. Clear notation, intelligibility and suitable detail.
5. Stylistic polish.

Rules:
- Correct final answer plus invalid derivation is not an eligible positive worked solution.
- Wrong answer with useful partial work can rank above a worse wrong answer but is not made positive solely by that relative ranking.
- A short correct answer can qualify if no explanation was requested. Do not require a proof for every arithmetic question.
- Equivalent methods, exact forms and justified approximations are acceptable.
- Harmless wording/numbering imperfections do not disqualify correctness.
- A false equation is not harmless stylistic imprecision.
- Unverified cases remain held: solver disagreement (unresolved) is a hard hold.
- Ambiguous or underspecified questions whose two independent solvers agree are NOT held as a class (change of 17 Sept, maths-v1.1, after the pre-existing rejudge held 25 of 41 items purely on underspecification). Such a question keeps its reference and its alternative readings; a reply may be an eligible positive only if it names the ambiguity or the missing information, asks for it or states the assumption it proceeds under, and is correct under that reading (`handled_ambiguity` = yes). A confident single answer to an ambiguous question is never a positive. This keeps the behaviour we actually want to teach on real forum questions, which are frequently underspecified.
- Format and language requirements still matter, but polished wrong mathematics cannot beat correct mathematics on mathematical quality.

Suggested structured fields (integrate schema, validator and consumers):
- outcome: correct | partial | incorrect | unresolved.
- reasoning: valid | invalid | not_provided | unresolved.
- task_completion: complete | partial | unresolved.
- requested_explanation: boolean.
- errors: exact quoted span plus concise checkable reason.
- reference_id/reference_status.
- verdict and eligible_positive.
- confidence and judgement version/hash.

Separate mathematical quality from presentation and explicit-request compliance; export eligibility considers both. A mathematically correct reply that misses a critical explicit requirement can remain ineligible without being called mathematically wrong.

Preserve general preference output fields where existing readers need them. Add validation preventing a positive with incorrect outcome, invalid reasoning, unresolved reference or unmet required worked explanation.

Deliver: versioned rubric, schema/validator updates and meaningful regression tests.

## A4. Calibrate and rejudge existing candidates

First rejudge all candidates for the 20 generated maths prompts. Inspect every proposed chosen answer in this bounded calibration set against its reference; include correct alternatives, wrong intermediate steps, no-reasoning answers, wrong final results, equivalence and ambiguity cases.

Required examples:
- g2:R2B1_006 sample 4: false final equality must not be selected over existing clean worked solutions.
- g2:R2B12_005: resolve/hold the ambiguity about reaching 15; a confidently phrased non-answer to the gap must not be automatically reinforced.
- Include at least one maths-in-dialogue case such as PAIR-RS001: correct route choice does not excuse the false equal-capacity/equal-duration explanation.

Keep prior judgements immutable. Write new records with supersedes identifiers. Produce a diff of verdicts, pair eligibility and reasons. Any evidence-backed false positive discovered in calibration is corrected before bulk use. Low confidence or material judge disagreement routes to review.

After calibration passes, apply the same method to every affected record in the intended training pool, including forum mathematics. A hold never falls back to the superseded positive.

Deliver: corrected_judgements.jsonl, verdict_diff.jsonl, calibration_report.md, and status ready_for_integration or specific unresolved cases.

## A5. Integration and continued growth

Rebuild only affected pairs from eligible candidates. Do not rewrite sampled answers to make them correct; if no acceptable answer exists, hold the prompt or resample within budget.

Once the active view uses corrected maths judgements, new maths records use this same verified protocol. Non-maths collection can continue in parallel under its valid existing rubric. Track accepted-pair yield, not just judged-prompt count.

Keep benchmark final-answer scoring separate from whole-response training eligibility. No training or benchmark-score improvement is established by changing the judge.

Done: the selected pool contains no superseded mathematical positive, corrected judgement evidence is reproducible, and new mathematical collection routes through the corrected verifier/judge.
