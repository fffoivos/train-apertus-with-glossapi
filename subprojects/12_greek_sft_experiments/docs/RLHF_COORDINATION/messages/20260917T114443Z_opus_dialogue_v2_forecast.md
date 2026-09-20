# Opus (dialogue v2, Workstream B): EUR forecast — admitted [shared]

Frozen forecast: data/rlhf/dialogue_v2/runtime/forecast.json (receipt sha256 in runtime/receipt.json).
Basis: upper bound: provisioning counted as billed; setup from three pilot sessions + 2.5 min; collection = six turns x (target p90 x3 + Sol user-step max latency from the dry run + 25% repair allowance + troubleshooting actions and resolver max latency) x 1.3 for the slowest of ten concurrent conversations; branch session samples 64 replies with 16 concurrent requests; VAT/FX: EUR/USD 0.95 as in the pilot ledger.
Sol latency measured in the dry run (seconds): {"user_actions": {"max": 10.3, "median": 9.7, "n": 2, "p90": 10.3}, "user_simulation": {"max": 21.7, "median": 9.9, "n": 20, "p90": 15.7}, "world_resolver": {"max": 8.6, "median": 6.8, "n": 2, "p90": 8.6}}.
- Session 1 (D1 + D2 raw collection, one pod): upper bound 29.6 min, EUR 0.9318 at the USD 1.99/h price cap.
- Session 2 (D1 branch candidates, at most 64 replies): upper bound 18.1 min, EUR 0.5703.
- Total upper bound EUR 1.5021 against EUR 2.0516 remaining before the EUR 4.00 operational stop (programme spent EUR 1.9484); safety margin EUR 0.25 → admitted, shortfall EUR 0.
- Watchdog caps: collect 50.0 min, branch 30.0 min, further bounded by the ledger deadline (operational stop − EUR 0.25, 15% price margin).
- Current offers: L40S_48GB massedcompute USD 0.82/h (cheapest, tried first), A100_80GB USD 1.20–1.23/h, A100_40GB USD 1.99/h. GET /pods: 0 active.
Sol: no call cap (owner); calls are recorded, not a gate.
D1/D2 counts: 0/0. EUR spent: 0. First-experiment quotas unchanged.
Next: bash data/rlhf/dialogue_v2/pod/run_stage.sh collect.
