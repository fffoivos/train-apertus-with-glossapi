# Dialogue quality-depth pilot runbook

Run every command from `data/rlhf/dialogue_quality_depth`. Commands stop with a final `DQD_OK ...` line; any `DQD_FAIL ...` line is a gate failure. Do not proceed past a failed gate. The commands below do not authorize a provider or GPU launch; Fable supplies and controls the serving route.

## 0. Offline build gate

```sh
python3 -m unittest discover -p 'test_*.py'
python3 dqd.py --state runtime init --config ../../../docs/RLHF_COORDINATION/DIALOGUE_PILOT_CONFIG_20260916.json
python3 dqd.py --state runtime status
```

Confirm `manifest.json` reports seed `9162602`, 6 smoke rows in split `smoke`, 35 measurement rows in split `train`, horizons 3/8, unique content families, and the actual joint counts. Initialization only reads the frozen generator registry in SQLite read-only mode.

## 1. Smoke, accounting and forecast

After Fable has independently verified the serving checkpoint, model/template, provider pricing, termination semantics and EUR cap:

```sh
python3 dqd.py --state runtime ledger gpu-start --pod-id POD_ID --price-usd-hr PRICE --eur-per-usd RATE
python3 dqd.py --state runtime openings smoke
python3 dqd.py --state runtime rollout smoke --endpoint http://127.0.0.1:8000/v1 --model fffoivos/greek-apertus-8b-sft-r4-full --checkpoint-sha256 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763 --max-turns 3 --concurrency 8
python3 dqd.py --state runtime annotate smoke
python3 dqd.py --state runtime calibration smoke --n 24
```

Root reviews the entire smoke calibration file. Put decisions in JSONL rows with `annotation_id`, `decision`, `evidence`, and `reviewer`, then:

```sh
python3 dqd.py --state runtime adjudicate smoke --decisions SMOKE_DECISIONS.jsonl
python3 dqd.py --state runtime ledger gpu-stop --pod-id POD_ID
python3 dqd.py --state runtime report smoke
python3 dqd.py --state runtime forecast smoke
python3 dqd.py --state runtime status
```

Gate: no plumbing errors; all smoke responses annotated; GPU stop confirmed; `forecast.json` admits one of 35/28/21/14 and fully funds annotation within its reservation. If no size is admitted, stop with smoke evidence and revise the plan.

## 2. Measurement collection

The admitted size is frozen before measurement outcomes are observed. If the default forecast is acceptable, use it as written; `--admit N` is only for choosing a smaller already-admissible predeclared size.

```sh
python3 dqd.py --state runtime openings measurement
python3 dqd.py --state runtime ledger gpu-start --pod-id POD_ID --price-usd-hr PRICE --eur-per-usd RATE
python3 dqd.py --state runtime rollout measurement --endpoint http://127.0.0.1:8000/v1 --model fffoivos/greek-apertus-8b-sft-r4-full --checkpoint-sha256 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763 --max-turns 8 --concurrency 8
python3 dqd.py --state runtime ledger gpu-stop --pod-id POD_ID
python3 dqd.py --state runtime annotate measurement
python3 dqd.py --state runtime calibration measurement --n 24
```

Root reviews the stratified sample plus every boundary row and then records decisions:

```sh
python3 dqd.py --state runtime adjudicate measurement --decisions MEASUREMENT_DECISIONS.jsonl
python3 dqd.py --state runtime report measurement
```

Gate: every admitted trajectory has a terminal reason; every assistant response is annotated or explicitly unjudgeable; substantive calibration changes do not exceed 20%, or the affected class is reannotated; the JSON/HTML report receipt is frozen.

## 3. Prefix branch and export

```sh
python3 dqd.py --state runtime select measurement
python3 dqd.py --state runtime ledger gpu-start --pod-id POD_ID --price-usd-hr PRICE --eur-per-usd RATE
python3 dqd.py --state runtime candidates measurement --endpoint http://127.0.0.1:8000/v1 --model fffoivos/greek-apertus-8b-sft-r4-full --checkpoint-sha256 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763
python3 dqd.py --state runtime ledger gpu-stop --pod-id POD_ID
python3 dqd.py --state runtime rank measurement
python3 dqd.py --state runtime export measurement
python3 dqd.py --state runtime status
```

Gate: three candidates per prefix share the exact prefix hash; rankings hide provenance and use rubric SHA16; ties, all-bad and no-substantive-preference sets appear only in `rejected_pairs.jsonl`; root reviews every exported pair and Fable validates the external loader against `ADAPTER_CONTRACT.md`.

The independent provider watchdog should terminate the pod at the deadline computed from the live all-in hourly price and the operational EUR 4 stop. This CLI records and reports the deadline inputs but cannot terminate an external provider without a provider-specific control surface.

