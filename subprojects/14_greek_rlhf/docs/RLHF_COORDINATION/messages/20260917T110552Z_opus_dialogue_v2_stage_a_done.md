# Opus (dialogue v2, Workstream B): Stage A done — baseline and contracts [shared]

Protocol: dialogue-v2-dev-0.1, generator 0.3-dev. No target-model generation, no GPU, no training.

Owned paths: data/rlhf/dialogue_v2/ (code, prompts, seeds, runtime), data/rlhf/reference_guided_dialogue_demo/ (six RGD seed packets and runtime), logs/dialogue_v2_*.log, my board messages, my own rows in CURRENT_VERSIONS.md (added at readiness).

Evidence (data/rlhf/dialogue_v2/runtime/baseline.json, run_manifest.json):
- Model G4F6P1 = fffoivos/greek-apertus-8b-sft-r4-full, pinned Hub revision 3a557e0842b146ccb6d24427e20b08c52fb368d5; Hub API LFS sha256 of model.safetensors = 54d445bc…6763 (matches). The pod setup will download the pinned revision and refuse to serve on a sha mismatch.
- ME021 reproduced from the latest snapshot (12 snapshots in the append-only log): 5 assistant turns; user turn 2 restates, 3 points to the defect, 4–5 add exclusions, 6 gives the first concrete alternative; the sixth reply was never generated (2,597 + 1,500 reserved > 4,096). Consecutive assistant replies 3–5 are near-identical (similarity 0.90, 0.99, 1.00). The unobserved reply is not a model failure.
- Chat-template overhead measured exactly on 126 pilot replies: prompt tokens = content tokens + 59 + 2 per message.
- Sampling-config change recorded: max_tokens 1,500 → 1,024 for every D1/D2 reply and branch candidate (pilot rollout completion p99 486 tokens; only one runaway exceeded 800). T 0.8, top-p 0.95, n=1, no system prompt unchanged.
- First-experiment quota pointers hashed (target_distribution_v1.json, inventory, round1/round2 pools, pilot manifest and 24 pilot pairs, CURRENT_VERSIONS.md); development rows never decrement them; re-checked before the review package.
- Prime Intellect: GET /pods = 0 active; programme ledger EUR 1.9484 spent (pilot, 8 sessions), EUR 2.0516 before the EUR 4.00 operational stop. My GPU ledger: data/rlhf/dialogue_v2/runtime/gpu_ledger.jsonl (tag development_demo), charged as an upper bound from POST/API createdAt to API terminatedAt.
- Sol: no call cap (owner, 17 Sept); every call recorded in per-run call registries (dialogue_v2/runtime and reference_guided_dialogue_demo/runtime). Calls so far: 2 (latency probe excluded: 6 scratch calls, no data).
- Glossary: recomputed sha16 877e694faf05b3c5 (spec v0.5 sync; the brief's 84b30fabd02a15cc is stale); every call records the sha16 it read.

D1/D2 counts: 0/0 collected. EUR spent by this workstream: 0. First-experiment quotas unchanged.
Next: B1 adaptive user (policy v2.0 + state transitions), B2 role views, worlds and learner state, B3 selection and branch sampling, then Stage C offline gates.
