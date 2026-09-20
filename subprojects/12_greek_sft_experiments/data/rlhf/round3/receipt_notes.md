# Round 3 receipt notes (generator 0.2 release, 17 September 2026)

## Judging
- Runner: `data/rlhf/judge_batches.py` → `judge_rank4.py`, schema v2, batches of four, medium effort, 16 workers.
- Routing (owner decision, 17 Sept): prompts whose purpose is maths (115, including the 39 forum maths posts) use the maths reviewer prompt `data/rlhf/prompts/judge_rank4_maths_en.txt` (sha16 41e99a8f2dfa9e79). Every other prompt, including the 128 with maths embedded in another task, uses `judge_rank4_v2_en.txt` (sha16 8aa32f266afd08b4). One rubric per prompt; no double judging.
- Maths rubric calibration (20 round-2 maths prompts, 41 batches): 35 reinforce / 1 neutral / 128 discourage; 11 prompts can form a pair; `g2:R2B1_006` reply 3 (false chain of equalities) discouraged and tagged wrong_main_point; `g2:R2B12_005` reinforces nothing.
- Pair rule, both routes: top-ranked reinforce against lowest-ranked non-reinforce inside one batch, clear margin, distinct texts.
- Escalation: replies 1–8 judged for all prompts; 9–16 and 17–32 only where no batch yet holds a reinforce and a non-reinforce. Forum maths posts stop at 8 except a fixed sample of 8 posts.

## Known limitation, accepted by the owner
The v2.4 rubric tells the judge not to solve the task itself, so on the 128 prompts with embedded maths (budgets, dosages, date arithmetic inside everyday, instruction, factual or safety requests) an arithmetic slip inside otherwise good advice can be reinforced. The owner chose this routing with the risk stated. If the review page shows embedded-maths prompts reinforcing replies with visibly wrong numbers, that is evidence to bring back to the owner, not a reason to change routing mid-round.

## Withdrawn during the round
The specialist maths pipeline (blind reference solves, own-solution fields, deterministic eligibility, reconciliation) was built and then withdrawn by the owner; it stays on disk under `data/rlhf/maths_judge/` as the record and is not called by round 3.

## Provenance note: the detail paragraph missing from three runs (found 17 Sept, not re-run)

Glossary v1.0.3 reworded the shared detail paragraph to begin "Detail is defined by how much the person themselves says". `generate.py` and `verify.py` looked it up by the old opening words ("Detail is defined by content"), so on glossary `ecdc0ec9ef56b184` the lookup returned an empty string and that paragraph was silently absent from the prompts.

- Affected: runs R3-held (29 accepted prompts), R3-fix (12) and R3-fix2 (2) — 43 of the 450 in this round — and the verification passes run after the v1.0.3 edit.
- Not affected: R3-validation-50 (41) and R3-main (345), which used glossary `ab7c697aca9f08ed`.
- What was still sent: the per-level definitions (bare ≤12 own words, terse ≤30, short, medium, detailed, rambling). What was missing: the clarification that pasted material never raises the detail level and that task-defining values belong to the ask. The word ceilings are enforced in code regardless, and the label-correction guard for packet prompts is in code, not in the prompt.
- Fixed in `generate.py`/`verify.py` (lookup by the prefix "Detail is defined by", asserted by a test) from sha16 `ecef7ea616ce5db8`.
- Decision: not regenerated. 43 prompts had a weaker instruction, not a wrong one; regenerating after sampling would change the prompt set mid-round. Their detail labels carry the same verification as the rest.
- Cause: a documentation edit made in one session while the code that reads that text was owned by another. Text that code matches on should be matched by a stable prefix, and a test should assert the paragraph reaches the prompt.

