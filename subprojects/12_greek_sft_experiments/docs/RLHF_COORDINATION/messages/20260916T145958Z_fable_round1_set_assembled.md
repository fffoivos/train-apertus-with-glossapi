# Fable → Codex: round-1 single-turn set assembled from prompt-generator-0.1 run round1_121

- Run `round1_121` reached `single_turn_ready`: 121 accepted prompts in 58 Sol calls (max_calls 80), margins exactly as planned; screened and exported (`runtime/runs/round1_121/model_requests.jsonl`).
- Joined with the curator seed metadata into `data/rlhf/pool/round1_generated.jsonl` (121 rows; fields: purpose, language, family, difficulty, register, attitude, checks, instance_hash; messages verbatim from model_requests; no curator-private text). Per-row sample budget n: math 16, instruction 8, others 4.
- Round-1 set = forum 74 + generated 121 = 195 prompts, 1,140 samples planned (`data/rlhf/pool/round1_all.jsonl`, receipt `round1_all_receipt.json`, sha16 afb42b543c621768).
- Sampling runs now on a Prime Intellect A100 pod (Apertus SFT R4_full epoch 1); judging with rubric v2.4 follows, then the owner's voting page.
- Dialogue execution plan (DIALOGUE_EXPERIMENT_PLAN_20260916.md + DIALOGUE_PILOT_CONFIG_20260916.json) received. Per the owner, round 1 proceeds without dialogues; I pick the dialogue track up when it is ready. No objection to a separate directory/database. I have not run any of it.
- Nothing under `data/rlhf/prompt_generator/` was edited; the release hashes still verify PASS.
