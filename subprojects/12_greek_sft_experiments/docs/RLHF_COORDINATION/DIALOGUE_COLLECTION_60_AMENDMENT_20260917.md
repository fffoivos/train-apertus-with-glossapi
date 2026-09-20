# Dialogue collection amendment: 30 + 15 + 15

Date: 17 September 2026
Status: owner-directed scope and sampling correction; implementation/collection pending.
This supersedes the small-run sizes and helpful-only selection rule in DIALOGUE_V2_EXECUTION_PLAN_20260917.md. The completed ten-case package remains historical development evidence.

## Scope

- At least 30 dialogues of the existing correction/revision type (including writing, editing, planning and grounded assistance).
- 15 troubleshooting dialogues.
- 15 learning dialogues.
- Minimum total: 60 distinct dialogue scenarios. Writing is part of the first group, not a fourth group.
- The two added groups do not replace any of the first 30 or consume the main experiments' existing production allocation. Keep group counts separate.
- Existing development cases can count only if they satisfy the corrected protocol and review; do not mechanically credit the old ten. Preserve their evidence and report any reused cases, superseded rollouts and new cases.
- Completed successful conversations count as dialogues even if they contain no error and therefore offer no error-prevention point. Do not keep generating only failures to force a paired sample.
- The first 30 are a correction-focused experimental group, not an estimate of the natural population mix. Freeze task/language/difficulty allocation before collection; reuse the current approved taxonomy. No automatic training promotion.

## User intervention and sampling

For the correction-focused first group, if the first two assistant attempts fail, the next user request (before assistant reply 3) must change strategy and contain an actionable example, decomposition, simplification or other instruction change. It can occur earlier. Preserve plausible user knowledge and finish if already successful.

Save all actual user and target-model turns. Enumerate instruction changes after a serious error without filtering them by a helpfulness verdict. Sample:
A. Immediately BEFORE the first seriously erroneous assistant reply.
B. Immediately AFTER the first substantive subsequent change in user instructions: a clarification, example, simplification, new constraint or changed goal. It does not have to be helpful. A complaint or verbatim restatement alone is not an instruction change.

The first group's scheduled strategy change is the intended B point unless an earlier substantive change already meets the rule. Record later alternatives so selection remains inspectable. Labels describe the change (including unhelpful, contradictory, or supplied solution); they do not silently remove it from the diagnostic. No A or B is invented when it does not exist. Healthy continuations remain recorded but do not incur a third candidate batch by default.

For a contradictory or ambiguous changed request, an acceptable answer may identify the conflict or ask for clarification; do not reward impossible literal compliance. Unexpected simulator contradictions are flagged as simulator defects, not silently treated as intentional negative-user tests or added to training.

A and B use equal initial candidate budgets. Each chosen/rejected pair shares its own byte-identical prefix. A response from A is never paired against a response from B. Compare descriptive outcomes within conversations, stratified by change type and task change; do not claim a causal effect of guidance alone when history, depth and task changed together.

## Minimal checks, using existing calls

1. Code checks (no Sol calls): stable seed/source identities, exact prompt and candidate duplicates, word counts, explicit values and simple constraint compatibility, unchanged prefix hashes, counters and terminal metadata. Feed computed counts to the existing simulator request instead of asking it to estimate them.
2. Existing user-simulation output carries perceived defect, instruction change, added information and assistance level. Do not add a second critic at every turn.
3. One post-trajectory review request per conversation can return prefix-local turn annotations, simulator defects, all change points, proposed A/B points and learner-state consistency together. Do not expose this evaluator output to the user simulator. Earlier replies are assessed only against requirements disclosed by their own prefix; later preferences are not retroactive instructions.
4. Candidate ranking returns absolute acceptability, ranking, substantive errors and pair eligibility in the same call. Deterministic checks apply to all candidates. Independently verify proposed positives where semantic/subject correctness requires it; specialist maths verification is retained and cached by exact prompt/prefix. Do not verify every rejected alternative with another call.
5. Track sampled completions, distinct candidate texts, verified acceptable replies and eligible pairs separately. A tied ranking or missing rejected alternative is not evidence that no acceptable answer exists.
6. Silent departure is a valid ending. Distinguish it from explicit abandonment, success and turn/context cutoff. Do not spend calls inventing farewells.
7. Learning-state checks share the post-trajectory review. No separate learning-review pipeline is required for every turn. Gold transfer answers stay outside learner inputs.

These checks prevent spending on duplicate alternatives and training on false corrections. They are not a new collection of per-turn review gates.

## Call budget proposal

Use four alternatives at each A/B prefix initially, rather than automatically doubling every point to sixteen.

For 60 dialogues, at most six assistant turns and at most two selected points:
- Raw target replies: up to 360 completions.
- Initial branch replies: up to 120 prefixes × 4 = 480 completions.
- Initial target total: at most 840 completions, excluding any explicitly itemised preflight or repairs.
- Optional four additional candidates per selected prefix: at most 480 extra completions if every point is extended; do not commission all top-ups automatically.
- User simulation: at most five follow-up-generation requests per six-turn dialogue, or 300, when the same output supplies its own state update and terminal decision. Do not add a final-assessment request solely because a turn cap was reached; label the cap. Troubleshooting action parsing/resolution should be included in existing calls where access separation permits, otherwise itemise the extra calls.
- Combined post-trajectory review: approximately 60 Sol calls rather than a separate evaluation call for each of up to 360 assistant turns plus another full review.
- Initial candidate judging: up to 120 Sol calls with four candidates each. Compatible independent packets can be batched further after a format check; keep context and provenance separate.
- Additional calls: seed/content preparation, maths references, necessary semantic positive verification, repairs and independent stage reviews. Forecast these explicitly; the numbers above are not an all-inclusive total.

API request batching does not reduce the number of model completions or tokens. Use provider n=4 only if supported and verified; otherwise parallel individual requests. Hold the sampling configuration fixed for comparisons. Exact-duplicate answers require no new semantic judgement.

Top-ups are allocated after checking initial unique-answer and acceptable-answer yield. Preserve matched within-4 results everywhere; compare within-8 only where both points received eight candidates and mark how those cases were selected.

The orchestrator must price this larger scope against remaining shared resources. The original EUR5 ceiling is unchanged; no automatic extra spend, cluster launch or unlimited replacement is implied. Preparation can proceed without restarting monitoring.

## Deliverable

One page with 30/15/15 completion counters, excluded/replaced cases, A/B eligibility and absence reasons, instruction-change types, generated/unique/acceptable/paired candidate counts, independent-conversation denominators and actual calls/cost. Keep original failures visible. Do not substitute a ten- or twelve-case smoke test for this collection.
