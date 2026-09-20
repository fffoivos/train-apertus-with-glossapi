# RLHF coordination board — Codex and Fable 5.1

Shared local board, established at the user's request on 16 September 2026.

## Ownership

| Owner | Owns | Current state |
|---|---|---|
| Codex | Prompt generator API, constrained seed construction, fixtures, validation, bounded development pilot, fixes, implementation handoff | Single-turn pilot release ready; dialogue deferred |
| Fable 5.1 | Forum generation/import decisions, production execution of released generator, Apertus sampling and dialogue rollouts, judging/RLHF training and schedule | Assigned by user; acknowledgement pending |

Fable: please write your own status to FABLE_STATUS.md and post questions/messages as new files in messages/. Do not edit CODEX_STATUS.json. Codex will not edit your status file or imply acknowledgement.
Only take over a release explicitly marked ready with version, hashes, commands, pilot result and limitations. Development fixtures are not a release.

## Communication protocol

- Each owner writes its own status atomically: current work, touched paths, next checkpoint, ETA range or dependency, blockers, release being consumed.
- New messages use UTC timestamp + sender + subject filenames. Do not overwrite the other owner's messages.
- Check the other status before integration changes; update on interface changes, milestones, blockers and handoff.
- Expected changes appear in CODEX_STATUS.json; timing estimates are provisional and revised with measured pilot timing.
- Do not modify each other's active files. Propose contract changes in a message.
- Fable owns production datasets and RLHF/cluster state. Codex owns data/rlhf/prompt_generator/ during development.
- Natural forum requests retain provenance and wording. Import them into accepted task/language cells; no double-counting.
- Dialogue openings do not count as completed multi-turn prompts. All assistant turns must be Apertus-generated and provenance-bound.

## Paths

Generator:
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/prompt_generator

Design review handoff:
/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/rlhf50_20260916/REVIEW_HANDOFF_20260916.md

Local artifact: http://127.0.0.1:8768/

## Pending Fable input

- Confirm target checkpoint identity and whether a ready inference endpoint exists for the 35 dialogue slots in the 100-slot demonstration. Codex will not launch cluster jobs or fabricate assistant history.
- Confirm forum import schema, accepted labels and upstream record/version hashes.
- State intended execution environment and desired frozen-release receipt location.

## Pilot scope

100 is the minimum size with exact 35/25/15/10/10/5 task and 70/20/2/2/2/2/2 language percentages. It demonstrates all primary purposes/languages, not every family/difficulty cross-product. Other families receive deterministic fixture tests separately.
New bounded development pilot: maximum 48 Sol calls including review/repair; concurrency 3 initially, fresh fictional/formal fixtures only. This is a new run under the user's request, separate from the old 24-call pilot. No CSCS spending.

## Owner clarification
Finish the single-turn API, run/review its 65 single-turn pilot requests, and hand off to Fable before Codex begins dialogue work. The 35 dialogue slots are reserved only. No Apertus endpoint is required for this stage.

## Current implementation handoff

/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/prompt_generator/IMPLEMENTATION_HANDOFF_20260916.md

Release scope and limitations are defined there.35 dialogue slots remain deferred. Fable acknowledgement is pending.

## Dialogue quality and depth addendum

/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_SAMPLING_QUALITY_DEPTH_20260916.md

Select prevention/recovery training prefixes after annotating complete raw Apertus trajectories. Best-of-N histories are a separate policy. This addendum leaves the frozen single-turn release unchanged.

## Concrete dialogue execution plan

/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_EXPERIMENT_PLAN_20260916.md

Configuration: /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_PILOT_CONFIG_20260916.json

Status: planned, not run;6 smoke chats then budget-admitted full trajectories, annotation, and selected-prefix preference sampling.
