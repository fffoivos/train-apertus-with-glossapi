# Review brief R-DPO1 — the frozen preference data for the DPO comparison

## Stage goal
Training data that is exactly what the owner decided to train on, traceable to the judgements that produced it, with no leakage between the
training set and the held-out screen. A fault here invalidates all four arms, so this review blocks the production runs.

## Scope
- `data/rlhf/dpo01/export.py` and its outputs: `train.jsonl` (373), `dev.jsonl` (25), `provenance.jsonl`, `exclusions.jsonl`, `manifest.json`.
- Sources: `data/rlhf/registry/registry.sqlite` (pair_credit, judgements, prompts, aliases), `data/rlhf/pool/round{1,2}_all{,_samples}.jsonl`, `data/rlhf/round3/round3_{all,pairs,samples}.jsonl`.
- Plans: `DPO01_EXECUTION_PLAN_20260918.md` §4, `DPO_EXPERIMENT_COMPARISON_20260918.md` §1-§2.

## Owner decisions this export must reflect
1. Round 1 is excluded entirely (18 September: round 1 was not considered good, round 2 carried the improvements). 25 pairs dropped, all forum, recorded as `round1_excluded_by_owner`.
2. The maths task is excluded: purpose maths, maths task type, maths-route pairs and prompts whose maths content is the task. 24 dropped. Embedded maths inside ordinary assistance stays and is counted (66 rows).
3. Development-only dialogue pairs stay out, keeping their `training_eligible=false` flags.

## Acceptance criteria
Blocking:
1. Every exported row's chosen and rejected text is byte-identical to the sampled reply that the recorded judgement ranked, read from the sample file that judgement names, joined by that judgement's alias, not by a coincidentally equal id across pools.
2. The exclusions are exactly the decisions above plus structural drops; nothing semantic was re-decided, and no held or superseded row is in the training set.
3. One pair per logical prompt and per normalised prefix; where both a banked and a round-3 version existed, the active sampled version won and the discarded alias is recorded.
4. The split is group-frozen: no source family, seed sibling or shared prompt prefix appears on both sides. The split function is the recorded hash rule, applied before any model saw the data.
5. `prompt` ends on a user turn, `chosen` and `rejected` are single assistant messages, no judge rationale, reference, scenario state or label leaks into the training text.
Major:
6. The manifest's counts, hashes and distributions match the files it describes.
7. Known-benchmark overlap and any prompt that cannot fit intact in 4,096 tokens are excluded rather than truncated.

## Notes for the reviewer
Report data faults, not preferences about which data we should have collected. If a criterion passes, say so plainly. Training for arm 00 is
already running on frozen inputs: a blocking finding stops the remaining arms and invalidates what has run, so be specific about which rows are affected.
