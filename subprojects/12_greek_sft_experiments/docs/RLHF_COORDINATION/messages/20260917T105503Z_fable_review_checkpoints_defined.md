# Fable: review checkpoints defined in advance (owner, 17 Sept)

The two-stream plan §10 now fixes where an independent Sol reviewer (gpt-5.6-sol, xhigh, fresh read-only session) reviews the work so far:
- Generator 0.3 track: R-PG1 terms frozen; R-PG2 import reconciliation and joint coverage; R-PG3 generator 0.2 release and the 500-slot
  dry-run manifest; R-PG4 first 50 production slots; R-PG5 remaining ~450 and the owner review page; R-PG6 dialogue integration.
- RLHF on CSCS track: R-RL1 sampling readiness; R-RL2 maths judge calibration; R-RL3 judging, pairs and active view; R-RL4 trainer and
  freeze; R-RL5 results.
Each checkpoint has a stage goal, the context to send and blocking criteria; §10.2 follows PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md.
Tool: data/rlhf/sol_review.py <ID> (briefs, reviews and INDEX.md under docs/RLHF_COORDINATION/reviews/). A HOLD blocks the next step; a
PASS is not an owner go for paid launches.
