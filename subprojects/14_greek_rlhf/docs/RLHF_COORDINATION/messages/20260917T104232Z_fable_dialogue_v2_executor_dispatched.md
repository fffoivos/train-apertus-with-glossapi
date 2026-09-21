# Fable: dialogue v2 executor dispatched (Workstream B, generator 0.3 corrections)

Owner instruction (17 Sept): send an Opus agent to Prime Intellect to start the dialogue work, with the previous Prime Intellect work and
the execution plan. Dispatched now.
- Brief: docs/RLHF_COORDINATION/DIALOGUE_V2_EXECUTION_BRIEF_OPUS_20260917.md (plan pointers, prior pod recipe/runner/failures, verified
  budget: EUR ~2.05 before the operational stop, 66 Sol calls in the base allocation, 0 active pods; order and gates; fixed interpretations;
  ownership; reporting).
- Executes: DIALOGUE_V2_EXECUTION_PLAN_20260917.md + REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md, stopping at the owner review.
- Writes under data/rlhf/dialogue_v2/ and data/rlhf/reference_guided_dialogue_demo/; development rows only; posts its own gate messages here.
- Workstream A (prompt generation PG1–PG6, maths rejudging) is not dispatched; the orchestrator continues prompt generation.
