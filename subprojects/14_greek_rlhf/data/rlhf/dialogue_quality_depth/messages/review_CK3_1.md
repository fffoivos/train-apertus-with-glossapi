VERDICT: HOLD

1. [blocking] `test_pod_runner.py:80-96,136-159` — the fake SSH shim only prints canned setup markers and never executes `pod/dqd_pod_setup.sh`. Consequently, the tests would still pass if the real preflight, checksum, configuration, or serve-death logic were broken. This does not satisfy the explicit requirement that fake-shim tests cover those paths. Required fix: execute the real setup script in an isolated fake pod environment with shims for `sudo`, `df`, `nvidia-smi`, `curl`, `uv`, `hf`, `sha256sum`, and server/process checks; assert actual exit codes 41–44, 46, and 48, and verify no download occurs before successful preflight.

2. [blocking] `pod/dqd_provision.py:16-21,33-43` — the adapter does not force `GREEK_GPU_COUNT=1` before importing the external helper. That helper reads an inherited `GREEK_GPU_COUNT`, so an environment left by another workflow can select a multi-GPU node, violating the required secure single-GPU provisioning policy. Required fix: set `os.environ["GREEK_GPU_COUNT"] = "1"` before importing `prime_provision`, and add a test that starts with a hostile inherited value and verifies the helper receives one GPU.

3. [blocking] `pod/run_stage.sh:110-119` — the purported frozen-forecast gate checks only mutable fields inside `forecast.json`; it never verifies `runtime/receipt.json`, the `frozen` flag, or the recorded SHA-256. A tampered forecast can therefore trigger provisioning, and the happy-path test succeeds without any receipt at all. Required fix: before provisioning, require a frozen `forecast.json` receipt and verify its SHA-256 byte-for-byte; add missing-receipt and hash-mismatch tests proving provisioning is not invoked.

4. [blocking] `pod/run_stage.sh:161-167` — every remote setup failure is converted to runner exit code 71. The actual preflight/checkpoint/serve codes 41–49 survive only as log text, so the single required entry command does not preserve the specified abort codes. Required fix: capture the SSH side of the pipeline’s exit status and exit with that code after printing the diagnostic tail; assert exact runner return codes in the tests.

Verified correct:

- Static inspection confirms the real setup script performs work-directory, disk, driver, and GPU-memory checks before network downloads.
- The model file is hashed before serving; `max_position_embeddings` is read from `config.json`; the Hub ID is used as the served model name; FlashInfer sampling is disabled; and the server loop checks process death every two seconds.
- The normal EXIT trap attempts ledger stop and confirmed deletion, preserves stage failures, and turns cleanup failures into failures on otherwise successful runs.
- The independent watchdog reads the budget-generated deadline, stops accounting, invokes deletion, logs a receipt, and signals the parent. The external two-hour self-kill remains an additional backstop.
- No pod script enables shell tracing. Static secret-flow inspection found no command that prints, logs, or copies the Prime key, Hub token, or SSH private key.
- The supplied transcript reports 43 passing offline tests, including runner happy paths and normal failure cleanup; the blocker is that several required production-script branches are simulated rather than exercised.
- The external `prime_provision.py` retains its July 15 mtime and SHA-256 `218dff7e…`; no CK3-timestamped file outside `dialogue_quality_depth` was found.