# CK5 implementation response

## What I built

- Added `resample.py` with the complete escalating-resampling workflow:
  - `register_targets()` validates the supplied P/R targets, reconstructs the exact history before assistant turn `depth`, checks the standard prefix SHA-256 (including equality with any existing same-depth selection), and appends stable `RS###` selections with a resample receipt. Existing selection rows and the frozen quality-depth report are not rewritten.
  - `sample_responses()` stores 32 individually requested `n=1` completions per target under the frozen sampling settings. Every byte-exact response has its SHA-256, sampling index, batch index 0–7, model/usage/timing data, and immutable call receipt in `resample_candidates.jsonl`. Completed calls are recovered from the ledger after a crash, so a restart neither repeats the request nor duplicates the row.
  - `judge_resamples()` judges batches of four in sampling order using deterministic randomized A–D labels, hidden provenance, and the frozen v2.4 rubric verbatim. It stops at the first batch containing `reinforce`, records `4 × batches` samples needed (or `no_reinforce_at_32`), and selects the globally lowest candidate across judged batches by verdict class and rank.
  - `export_resamples()` atomically appends/replaces only resample-origin rows in `preferences.jsonl` and `rejected_pairs.jsonl`. A pair requires a reinforce and clear margin; chosen is the first ranked reinforce in the first successful batch and rejected is the global lowest judged candidate. It writes an idempotent per-target/aggregate `resample_report.json` with samples-needed histogram, no-reinforce share, P/R breakdown, and cost counters, then receipts all changed artifacts.
- Added the `resample`, `resample-judge`, and `resample-export` commands in `dqd.py`. The GPU command can take endpoint/model/checkpoint arguments or reuse the frozen `runtime_config.json` values.
- Extended `rank.py` with the strict four-candidate schema and prompt while retaining the exact frozen rubric text. The original ranking path now ignores resample selections.
- Updated `candidates.py` and `export_pairs.py` to keep the original three-candidate/export workflow isolated from appended resample selections.
- Updated `budget.py::CallLedger._sol_limits()` to validate and add authorized forecast extensions to both the total cap and named phase reservation while preserving reserve-before-request accounting.
- Added the exact owner authorization to `runtime/forecast.json`:

  ```json
  "extensions": {
    "resample": {
      "authorised_by": "owner 2026-09-17",
      "max_new_sol_calls": 128
    }
  }
  ```

  The base reservations still total 120. `runtime/receipt.json` records the updated frozen forecast SHA-256 `6b53e08b66af1da76a9e43c2964219d0c2925ff3d01a6dcad5c1ee6e6a716805`.
- Extended `pod/run_stage.sh` with `resample`. It uses the same provision, preflight, serve, tunnel, ledger, watchdog, teardown, and EUR 5 cap path as the existing GPU stages, then invokes the 32-sample command in that one session.
- Added `test_resample.py` and expanded `test_pod_runner.py`. Offline tests cover prefix byte/hash identity, frozen `n=1` sampling and response SHA, crash recovery and idempotent reruns, batch stop behavior, sample arithmetic, global-lowest export, `no_reinforce_at_32`, byte-identical repeated export, additive/phase-bounded extension accounting, CLI routing, and the pod resample entry point.

Read-only validation against the supplied runtime data found 15 target rows, all resolvable; the four targets with an existing same-depth selection have identical prefix messages and prefix SHA-256.

## Commands for the orchestrator, in order

Openings are not needed because the measurement trajectories already exist.

```bash
bash pod/run_stage.sh resample
python3 dqd.py --state runtime resample-judge measurement
python3 dqd.py --state runtime resample-export measurement
```

The first command internally runs the equivalent of:

```bash
python3 dqd.py --state runtime resample measurement \
  --targets runtime/measurement/resample_targets.json --max-fresh 32 \
  --endpoint http://127.0.0.1:8000/v1 \
  --model fffoivos/greek-apertus-8b-sft-r4-full \
  --checkpoint-sha256 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763
```

## How I tested it

```text
$ python3 -m unittest discover -p 'test_*.py'
............................................................
----------------------------------------------------------------------
Ran 60 tests in 18.349s

OK
```

Additional read-only runtime checks verified all supplied target/depth lookups, existing-prefix equality, shell syntax, forecast base/extension arithmetic, and the forecast receipt hash.

## What I could not do

I did not execute the live GPU, target-model, or Sol stages: CK5 requires the implementation and tests to remain offline, and those calls are the orchestrator's next three commands above. Consequently, real resample candidates, judgments, pairs, report statistics, and incremental live cost do not exist yet.

The supplied `runtime/measurement/resample_targets.json` contains 15 targets, while plan §30 describes a first run of 16. I processed and validated the supplied target file exactly and did not invent a sixteenth target because no authoritative missing target is identified in the CK5 brief or runtime artifacts.
