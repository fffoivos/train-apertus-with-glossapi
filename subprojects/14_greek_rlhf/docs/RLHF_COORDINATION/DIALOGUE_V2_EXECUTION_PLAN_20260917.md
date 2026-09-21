# Dialogue improvements and separate category demo: execution plan

Date: 17 September 2026
> **Owner amendment, 17 September:** DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md supersedes the four-plus-six development run as the next collection target: at least 30 existing-type, 15 troubleshooting and 15 learning dialogues. It also replaces helpful-only recovery selection with sampling after a substantive user instruction change, whether helpful or otherwise. Stage D below records the completed small pilot; it is not the next-run quota. Use the amendment for current sizes, intervention timing and call controls.

Executor: Opus or Sol.
Status: executable work specification; implementation and live collection have not been performed by the author of this document.
Start here. Background: OPUS_FEEDBACK_20260917.md. Concrete new-category cases: REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md.
Aspects (see the parent plan §0): [PG] prompt generation = Stage B1, Stage B2 user, world and learner views, and the raw trajectories of Stage D; [RLHF] = Stage B2 evaluator view, Stage B3, the branch candidates of D1 and the pair review; [shared] = Stages A and C.
Terms and labels: ../SEED_LABEL_SPEC_20260917.md §4.4 (interactions), §4.7 (user moves, assistance levels, turn metadata), §4.8 (sampling points, ending reasons, user state, role views, dialogue categories), §5.4 (dataset and eligibility terms). Versions: CURRENT_VERSIONS.md. Parent plan: RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md §4a.

## 1. The three agreed directions

1. Improve the simulated user. React to the actual reply; change strategy when repetition does not help. Possible reactions include clarification, a concrete example, decomposition, simplification, frustration, acceptance and abandonment.
2. Improve selection of preference-training points. Generate and retain full natural trajectories first. Then select saved prefixes before the first serious error, after helpful user guidance, and during healthy continuation. Each prefix has its own alternative replies and preference comparison.
3. Expand dialogue types through a separate reference-guided demo. Writing has a desired result; troubleshooting has a consistent hidden world; learning has a learner knowledge state and evaluator-only correct subject knowledge.

Directions 1–2 improve the existing dialogue method. Direction 3 is a distinct development demo. None of these development cases subtract from the first experiments' size, task/language quotas or promised dialogue allocation. Do not silently relabel pilot cases as experiment cases.

The maths-judge revision and global language/task distribution review remain separate recorded workstreams in OPUS_FEEDBACK_20260917.md. They are not superseded by this plan.

## 2. Work boundaries and output locations

Repository root:
 /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments

Read/reuse:
- data/rlhf/dialogue_quality_depth/user_policy.txt
- data/rlhf/dialogue_quality_depth/rollout.py
- data/rlhf/dialogue_quality_depth/clients.py
- data/rlhf/dialogue_quality_depth/manifest.py
- data/rlhf/dialogue_quality_depth/export_pairs.py
- data/rlhf/dialogue_quality_depth/resample.py
- data/rlhf/dialogue_quality_depth/runtime/measurement/
- docs/RLHF_COORDINATION/FABLE_STATUS.md

Create isolated development code under:
- data/rlhf/dialogue_v2/ — adaptive user, state contracts, prefix selection and test helpers.
- data/rlhf/dialogue_v2/runtime/ — improvements pilot, IDs DVI001–DVI004.
- data/rlhf/reference_guided_dialogue_demo/ — six reference cases and separate configuration.
- data/rlhf/reference_guided_dialogue_demo/runtime/ — new-category demo, IDs RGD001–RGD006.

Keep code shared where useful, but use separate manifests, transcripts, reports, counters and ledger tags. Every development row carries purpose=development_demo, training_eligible=false and experiment_credit=0.

Do not overwrite existing raw conversations, annotations, rankings, exported pairs or frozen rubrics. Reuse existing clients and provider lifecycle safeguards without changing the old protocol in place. No training launch is part of this plan.

## 3. Stage A: establish the baseline and contracts — [shared]

Before coding:
1. Inspect current repository changes and coordination messages. Identify another executor's active files; do not overwrite them.
2. Read the latest snapshot per trajectory ID, not the first line of an append-only trajectory log.
3. Inspect ME021 and reproduce the observation: repeated requests, useful detail only at user turn 6, next assistant call stopped by context reservation. Do not label that unobserved response as a model failure.
4. Verify exact target checkpoint identity. User-facing model name: G4F6P1. Existing saved SHA is 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763; validate current serving evidence rather than trusting a model alias alone.
5. Record the main experiments' existing quota manifests or their authoritative pointers as a baseline. Development work must not decrement those quotas.
6. Write a small run manifest with protocol version, seed IDs, source-family reservation, language, task, model identity, budgets and output directories.

Deliver: baseline.json, schemas/configuration, and a short status entry. This stage uses no target-model generation.

## 4. Stage B1: adaptive user implementation — [PG]

Represent separately:
- Stable user goal and known facts.
- Initial knowledge/expertise and any misconception.
- Preferences already disclosed versus private preferences.
- Patience and ability/willingness to help.
- Previous user strategies, repeated defect count and task progress.
- Newly revealed facts/preferences at each turn.

Select behaviour based on actual visible history:
- Continue or finish after useful progress.
- Identify a defect when the user can plausibly recognise it.
- After an unsuccessful restatement, normally change strategy rather than paraphrase the same instruction again.
- Use a short example, decomposition, missing fact or narrower request when appropriate.
- Permit frustration and abandonment without requiring either.
- Do not force all users to teach, detect every error or give correct solutions.
- Do not manufacture failure or continue a completed task to hit a turn target.

Save each user turn with exactly four fields, `move`, `new_information`, `trigger` and `changes_task` (earlier drafts: strategy, what_visible_event_triggered_it, whether it changes the task), using the move labels and field names defined in ../SEED_LABEL_SPEC_20260917.md §4.7. These are metadata, not text shown to Apertus.

Deliver:
- Versioned adaptive user prompt.
- User-state schema and transition logic.
- Explicit natural-completion and abandonment reasons.
- Regression case for ME021: after repeated failure, a helpful alternative is possible without requiring that exact wording or forcing a failure first.

## 5. Stage B2: reference access and consistent state — [PG]; evaluator view [RLHF]

Build explicit views; do not put all private material into one universal simulation prompt.

Apertus view:
 public conversation only, using the same verified serving/chat-template conditions as the baseline.

Writing-user view:
 own goal/preferences and optionally a reference draft. Reference wording is illustrative. It is legitimate to request a new preference later, but earlier replies cannot fail undisclosed hard constraints.

Troubleshooting-user view:
 initial symptoms, expertise, observations already obtained and visible conversation. Root cause and unobserved test results are withheld.

Troubleshooting world resolver:
 maintains fixed cause, supported checks and outcomes. It supplies observations for actions the user could plausibly take. Unknown actions produce an unresolved event or reviewed extension of the world; never convenient invented success. Synthetic device/filesystem actions must not execute on a real machine.

Learner view:
 current knowledge, misconception, goal and visible teaching. Withhold gold answers to transfer questions. Apply knowledge-state changes justified by teaching and learner attempts.

Evaluator view:
 verified facts/solutions, visible history and relevant state. Judge subject correctness and whether claimed learning is supported. A simulator saying “I understand” is not by itself evidence of learning.

Deliver:
- Six complete RGD seed packets from REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md.
- Concrete RGD002 reference draft and deterministic supported observation outputs for troubleshooting cases.
- Packet builder for each role.
- Progress/consistency evaluator recording uncertainty and separating simulator errors from target-model errors.

## 6. Stage B3: selection and branch sampling — [RLHF]

Keep trajectory collection separate from candidate sampling. A failed assistant answer stays in the original raw trajectory.

Annotate:
- Serious-error turn and decisive evidence.
- Helpful user interventions and assistance level: restatement, pointed defect, partial example/scaffold, supplied solution.
- Healthy continuation, completion/abandonment, and observed turn depth.
- Unknown or ambiguous judgements requiring review.

Select:
- Prevention: prefix ends immediately before the first seriously erroneous assistant answer, including turn 1 if that is where it occurs.
- Supported recovery: prefix ends after the first genuinely helpful user suggestion, if present.
- Healthy continuation: eligible deeper turn without preceding serious failure, where there is a meaningful next task.

Do not invent helpful suggestions or errors solely to fill cells. Keep first-turn prevention classified as single-turn; later valid examples from that conversation remain eligible for multiturn analysis.

For each selected prefix:
- Preserve byte-identical history and record a hash.
- Generate 4 alternatives first. If no verified acceptable reply is found, permit 4 more within the configured cap.
- In a within-conversation comparison, use the same fixed candidate count for both points; do not compare a 4-sample yield against an 8-sample yield as equivalent.
- Candidate order is blinded for judgement.
- Accept only genuinely acceptable chosen answers with a meaningful preference gap. “Less bad” is insufficient.
- Verify substantive errors and checkable constraints. Route mathematical content to specialist verification.
- Never form a pair with one answer before a hint and another after it.
- Never splice the old suffix onto a replacement winner. Continuing a winner requires a new branch and newly generated user follow-ups.

Record matched comparisons as descriptive case evidence, not proof of prevention/recovery superiority. Recovery after a complete supplied answer is reported separately from recovery after a small hint.

Deliver: prefix selector, candidate exporter, branching metadata and rejection reasons.

## 7. Stage C: offline gates before paid collection — [shared]

Use small meaningful tests and manual packet inspection:
1. Distinct role views cannot leak a hidden diagnosis or gold transfer answer into the user/learner or Apertus prompt.
2. Revealed observations remain consistent across turns.
3. A hidden writing preference is not treated as an earlier explicit instruction.
4. Adaptive user can finish, help, change strategy or abandon; it cannot only repeat.
5. ME021 saved-history example can request a concrete illustrative dialogue without copying a reference solution into Apertus history.
6. Prevention and recovery prefixes have the correct end boundary; chosen/rejected histories hash identically.
7. Context overflow is distinct from model failure; history is not silently trimmed.
8. All development outputs are excluded from experiment counters and automatic training import.
9. Resumption does not duplicate charged calls, and ambiguous timeouts are not retried blindly.
10. Export metadata states completion-only training; where an actual trainer is available, inspect tokenized masks so historical assistant tokens are excluded from target loss. Otherwise mark trainer integration unverified rather than claiming it passes.

Publish a concise readiness report. Fix any access-separation or state-consistency issue before launching the demo.

## 8. Stage D: bounded generation and review — [PG] raw trajectories; [RLHF] branch candidates and pairs

### D1 — improvements on existing dialogue types

Four fresh development trajectories:
- One ME021-like creative-writing task from the same development family.
- One constrained planning task.
- One editing/format-retention task.
- One explanation or grounded-information task.

Use new run IDs; pin source-lineage links (spec v1.0.2) and keep them out of held-out evaluation. Assign 3 Greek and 1 English for this small diagnostic; it is not a language-distribution estimate.

Generate one Apertus reply per turn, up to six assistant turns: at most 24 raw replies. Then annotate and review the saved full conversations.

Where genuine eligible points exist, compare prevention and helpful-follow-up points within a conversation. Up to two points per conversation, eight candidates per point: at most 64 additional replies. No forced filling of missing points. The 12-conversation/192-reply comparison in earlier feedback is a possible later extension, not an additional mandatory run.

### D2 — distinct reference-guided category demo

Six conversations RGD001–RGD006: 2 writing, 2 troubleshooting, 2 learning; 4 Greek and 2 English as specified. One Apertus reply per turn, at most six assistant turns: at most 36 raw replies.

Do not generate extra preference candidates for these six yet. Mark possible sampling points, but first review whether the reference/user/world design itself works.

Together D1 and D2 allow at most 60 raw assistant replies and 64 branch replies = 124 target completions, plus only necessary model-identity preflight. Fewer are expected when conversations finish naturally. This is a count bound, not a price forecast or an authorization to exceed the shared budget.

### Review procedure

Read every complete trajectory and any accepted candidate pair. Show:
- Public transcript.
- Private reference/state in a separately labelled panel.
- User strategy changes and what new information was added.
- Target errors versus simulator/world/learner errors.
- Possible and selected sampling points.
- Ending reason and cost.

Questions:
- Did helpful guidance arise plausibly rather than through hidden oracle knowledge?
- Did the user react to a real defect instead of a scripted complaint?
- Did some conversations progress without failure?
- Did the assistant use guidance, retain earlier constraints and finish the task?
- Did the simulator remain consistent, including when the assistant went off-script?
- For learning, did the learner attempt demonstrate progress on an unsupplied example?
- Did a “positive” answer still contain incorrect factual/mathematical claims?

Repair narrow implementation defects and rerun only affected cases with explicit supersession links and remaining-budget checks. Do not bury failures by regenerating until the report looks good.

Stop at the user review after these bounded development runs. Do not enlarge the sample, promote rows into training, or start DPO automatically. The user explicitly wants to review the demo first.

## 9. Budget and efficiency — [shared]

- No CSCS jobs in this development plan.
- Preserve the existing total EUR 5 Prime Intellect ceiling; separate demo accounting is not a fresh allowance.
- Saved ledger last inspected: EUR 1.9483674086334721 spent, no active session recorded, operational stop EUR 4 and EUR 1 reserve. Refresh actual provider state, shared obligations and usage before provisioning.
- Build a forecast including model startup/download, rollout, possible waiting for Sol, collection, teardown and taxes/FX basis as relevant. Measure instead of quoting token counts as GPU cost.
- Reuse one qualified target session for D1/D2 when economical, with separate tags/outputs and explicit shutdown. Avoid leaving a GPU idle during long review work.
- Verify remaining Sol allocation. Prior dialogue records reported 94 calls under a 120-call allocation; do not assume this plan resets that cap or grants new quota. Account for user simulation, observation resolution, annotation, ranking, retries and independent review before execution.
- Exact model-call budget is a readiness output. If the bounded run cannot fit existing authority, finish code, seeds and dry-run packet validation, report the specific shortfall, and obtain the missing budget authorization. Do not consume the first experiments' reserved resources to hide the shortfall.
- Batch independent user/evaluator packets of compatible visibility where safe, keeping each packet's state separate. Never batch a learner input with its hidden answer in the same model-visible prompt.
- Reuse deterministic observations and verified references rather than paying to regenerate them.
- Preserve model checkpoint and sampling metadata so any behaviour change is not confused with a model/decoding change.

## 10. Parallel execution and handoff

If multiple executors are available:
- Workstream A: adaptive user/state and old-family regression checks.
- Workstream B: six reference fixtures, observation resolver and learner access separation.
- Workstream C: saved-prefix selection, candidate export and report rendering.
All agree on schemas first, then one integration owner performs readiness and paid execution. Only one owner controls provider lifecycle and shared budget accounting. A single Opus/Sol executor can perform these sequentially.

Report status in docs/RLHF_COORDINATION/messages/ with:
- Owned paths and protocol version.
- Completed evidence and remaining gates.
- Planned next action and measured ETA where available.
- Separate D1/D2 counts, call use and provider spending.
- Confirmation that main experiment quotas remain unchanged.

Required final deliverables:
- Versioned code/configuration and passed offline gates.
- Four DVI development trajectories and six RGD demo trajectories, or explicit per-case blockers.
- Selected/candidate prefixes for D1 where available.
- Full review artifact with visible references and all failures.
- Independent accounting for D1 and D2, tied to the shared cap.
- Short recommendation: retain, change or reject each of the three directions, based on evidence.
- Handoff note listing exact run commands implemented and verified. Do not invent command-line flags in advance; existing legacy entry points do not implement this protocol.

Done means the bounded demo/improvements evidence is ready for owner review, not that the model has been trained or improved.
