# Dialogue v2 runbook — exact commands implemented and verified (17 Sept 2026)

Protocol dialogue-v2-dev-0.1 (generator 0.3-dev). Every row is `purpose=development_demo`, `training_eligible=false`,
`experiment_credit=0`. Working directory for the `dv2.py` commands: `data/rlhf/dialogue_v2/`. The two GPU commands are
run from the subproject root. Nothing here trains or imports anything.

## Free (no GPU)

    python3 dv2.py baseline            # Stage A: runtime/baseline.json + run_manifest.json (quota pointers, ME021, model identity)
    python3 dv2.py openings            # D1 openings from seeds/dvi_seed_specs.json -> seeds/dvi_seeds.json (one Sol call, cached on rerun)
    python3 dv2.py seeds-check         # validates the ten seed packets and both troubleshooting world tables
    python3 -m unittest test_dialogue_v2      # 21 offline gate tests (plan §7 gates 1-10 + the pod runner)
    python3 readiness.py               # runtime/readiness.json + readiness_report.md (gate results, dry run, reviewer verdict)
    python3 dv2.py dry-run --turns 2   # real Sol user/world/learner calls against stand-in replies; writes runtime/dryrun/ only
    python3 dv2.py forecast --price-cap 1.99 --freeze   # runtime/forecast.json + receipt.json (the pod runner refuses to start without it)
    python3 dv2.py gate --stage collect|branch          # frozen-forecast, active-session and operational-stop checks
    python3 dv2.py evaluate            # prefix-local turn evaluations, then one conversation review per case (Sol)
    python3 dv2.py points              # possible sampling points for all ten cases; selects at most two per D1 conversation
    python3 dv2.py branch-judge        # blinded fours with rubric v2.4, verification, pair export (Sol)
    python3 dv2.py report              # review/dialogue_v2_review.html
    python3 dv2.py status              # programme spend and per-run call counts
    python3 pod/dv2_provision.py pods|availability      # read-only Prime Intellect checks

## Paid (one pod each, from the subproject root)

    bash data/rlhf/dialogue_v2/pod/run_stage.sh collect   # D1+D2 raw trajectories in one session
    bash data/rlhf/dialogue_v2/pod/run_stage.sh branch    # 8 branch candidates per selected D1 point

Each run: frozen-forecast gate → GET /pods must show no active pod → ranked offers (cheapest first, Low stock
de-prioritised, HTTP-error fallback) → ledger `gpu_start` with the POST time and a watchdog deadline → independent
`watchdog.sh` → remote preflight, pinned revision `3a557e08…`, sha256 check, vLLM serve → ssh tunnel → the stage
command → EXIT trap: teardown (DELETE + GET-confirmed TERMINATED) → ledger `gpu_stop` from the API timestamps →
`DV2_STAGE_RECEIPT`. Logs: `logs/dialogue_v2_<stage>_<stamp>.log`; setup output and teardown records under
`runtime/pod/`.

Resumption: rerun the same command. Completed calls are replayed from the call registry, a failed Sol call is retried
once under `<call_id>:retry1`, and ambiguous or reserved calls are never retried (the conversation ends
`ambiguous_timeout`).

## What ran on 17 Sept 2026

| Stage | Command | Result |
|---|---|---|
| collect | `run_stage.sh collect` | pod ad466297113a4252922ae3c22c5d3430 (L40S_48GB, USD 0.82/h), 43 replies, EUR 0.1320, DELETE confirmed |
| branch | `run_stage.sh branch` | pod d3ba0acabd85427580ee7058b6b70cbf (A100_40GB, USD 1.99/h), 56 candidates, EUR 0.2747, DELETE confirmed |

Outputs: `data/rlhf/dialogue_v2/runtime/` (D1) and `data/rlhf/reference_guided_dialogue_demo/runtime/` (D2):
`trajectories.jsonl`, `assistant_turns.jsonl`, `user_turns.jsonl`, `user_state_snapshots.jsonl`, `world_events.jsonl`,
`turn_evaluations.jsonl`, `conversation_reviews.jsonl`, `sampling_points.jsonl`, plus D1 `branch_points.jsonl`,
`branch_candidates.jsonl`, `branch_judgements.jsonl`, `branch_pairs.jsonl`; prompts as sent in `prompts_sent/`;
call ledgers in `call_ledger.jsonl` / `call_registry.sqlite`; GPU ledger `runtime/gpu_ledger.jsonl`.
