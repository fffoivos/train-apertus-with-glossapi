# Dolci Tool Use lossless re-export pilot

> This report records the initial local freeze. Remote staging, binding, canonical compilation and scheduler-only testing were later completed; see `REMOTE_READINESS_REPORT.md` for the current state. No source pilot has run.

## Status

The 200-row pilot is prepared and locally validated, but not staged, submitted or run. Production corpora and the quarantined 29,700-row block are unchanged. The candidate uses the applied `export_core.py` helpers, the actual current assembler consumer and the canonical Apertus tokenizer path.

Remote launch remains intentionally disabled in `data_stage_contract.prebind.json`: `allow_preparation_submission` is false, the live receipt is a placeholder until the staged paths are rebound, and the canonical runner bundle must be frozen from commit `01f4b7e21f39f346df61485bd1818f7ed07c7f44`. A local-path substitution compiled successfully only to validate the canonical contract shape; `compiled_data_stage.local_validation.json` is not a remote launch manifest.

## Allocation-free source inventory

The cached immutable source is `allenai/Dolci-Instruct-SFT` at revision `bd3c8f3a9b2cc5a9682e44b96ddd0bb2ff027221`.

- 15 parquet shards contain 2,152,112 rows.
- 227,579 rows have `domain="Tool Use"`.
- Tool Use rows occur only in shard 13 (84,105 rows) and shard 14 (143,474 rows). The frozen pilot selects 100 from each.
- Selection is per-shard minimum SHA-256 over revision, parquet locator and typed source ID. It is deterministic and frozen by locator digest `41b0c7bca817986ac0bfb79a822678dad52427530308b590bb02b0cdf51a5302`.
- Upstream columns are exactly `id`, `messages`, `source_dataset` and `domain`. `messages` is a list of structs with string fields `content`, `function_calls`, `functions` and `role`.
- An eight-row, content-redacted native-shape probe found eight parseable JSON schema strings and 19 `function_calls` strings. None of the calls is JSON; all 19 parse as one or more legacy Python-style named-argument call expressions, representing 29 calls total.
- The upstream parquet schema has no `tool_calls`, `tool_call_id` or standalone `name` fields. ID-preservation checks are therefore conditional on native presence; the pilot does not invent IDs.

The cached dataset card declares ODC-BY and says the collection is intended for research and educational use under Ai2's Responsible Use Guidelines. That card evidence is recorded separately from the immutable commit identity; release review remains a separate gate.

## Executable pilot

`remote_bundle/pilot_run.py` verifies its own hash, the pilot contract hash, frozen science/consumer/trainer hashes, the 200-locator inventory, both selected shard hashes, and tokenizer/template hashes before creating attempt-specific output. It then:

1. Resolves every selected parquet locator and verifies exact typed source ID, `domain`, `source_dataset` and revision.
2. Calls the exact applied `_export_turn`, `_source_id` and `_export_row` helpers and adds the exact upstream `source_dataset`, which the applied canonical helper does not yet retain.
3. Requires 200/200 native field JSONL round-trips.
4. Parses visible function schemas, parses legacy or JSON call representations, requires every call name to be declared, and validates named literal arguments against a fail-closed supported JSON Schema subset. Unsupported schema keywords fail rather than being ignored.
5. Runs the actual `assemble_mix_r2.py::to_messages` function and checks rendered schema, call and result survival. Native structured fields are expected to be stripped by this consumer; acceptance proves the complete text protocol, not structured-tool trainer input.
6. Imports the complete frozen `sft_train.py` module, calls `prepare_tokenizer` and `tokenize_messages` with the cached Apertus revision, and excludes rather than clips rows above 4,032 rendered tokens.
7. Writes all 200 lossless exports, row metrics, the structurally and length-accepted subset, a token inventory, and 40 deterministic full-message rows stratified by schema length, call count, turn count and grammar for subsequent human semantic review.

The job receipt passes only if all 200 rows satisfy native round-trip and protocol checks. Rows above 4,032 tokens may be reported and excluded without clipping. The 40-row semantic review remains required before any promotion even when the structural job passes.

## Validation performed

- The helper parser tests pass for JSON calls, single and multiple legacy calls, lowercase JSON literals and fail-closed positional arguments.
- A 40-row synthetic parquet ran end to end through the frozen exporter helpers, actual consumer and canonical tokenizer path; 40/40 were structurally accepted and within the length gate.
- The nonlaunching data-stage draft validates and compiles through canonical `apertus-data-stage` after a local-path substitution. It produces one `cpu-debug` batch with one task and one allowed attempt.
- The source schema/domain/locator inventories ran read-only on `clariden-ln004`; no source row text was emitted by the allocation-free probes.

## Resource and launch boundary

The planned task requests one node for at most 30 minutes, 8 CPUs, 64 GB memory, `gpus_per_node=0`, array parallelism 1 and `max_attempts=1`. Canonical rendering contains no GPU or GRES flag. The `debug` CPU profile is used because the available validated UENV plus project environment supplies PyArrow 25.0.1, Datasets 5.0.1 and Transformers 5.16.1; bare login Python 3.6 and `/usr/bin/python3.11` do not supply PyArrow, while canonical xfer tasks may not invoke UENV. This is a CPU-only pilot on a debug node, not a GPU workload. Its standalone maximum planning charge is CHF 1.345 for the single half-node-hour bound.

Before launch, root must stage `remote_bundle` at its frozen path, freeze or reuse the exact canonical runner commit at the declared remote code root, refresh and stage the live cluster receipt, run `bind_data_stage.py` with the reviewed authority, compile on Clariden, inspect the exact generated batch, and then explicitly use the apply verb. Any changed byte requires rebinding and recompilation. No automatic retry is authorized.

The independently prepared OpenMath first-shard intake uses `openmath_data_stage_contract.prebind.json`. It has its own task, run root, receipt, one-attempt budget and standalone maximum planning charge of CHF 1.345. There is no dependency in either direction. If both tasks are separately launched, the combined planning ceiling is CHF 2.69; either task may run or fail without changing the other's acceptance result. The OpenMath source-network transfer occurs only inside its own bound worker.

Both prebind templates remain nonlaunching. Their local canonical compiles prove contract shape and routing only. Exact `sbatch --test-only` evidence is pending remote staging, a fresh live receipt and compilation against the staged bytes. No scheduler test was inferred from the local results.

The reusable missing `source_dataset` preservation is recorded in `CANONICAL_ISSUE_DRAFT.md`; the experiment adapter supplies the field for this pilot without changing canonical code.
