# CK3 cycle 2 implementation response

All four findings were correct and have been fixed.

1. **Real setup-script coverage — fixed.** `test_pod_runner.py::_real_setup_environment()` and `::_run_real_setup()` now execute the actual `pod/dqd_pod_setup.sh` in an isolated temporary fake-pod environment. The harness supplies controlled shims for `sudo`, `df`, `nvidia-smi`, `curl`, `uv`, the venv `hf`/Python/vLLM commands, `sha256sum`, and `nohup`/readiness behavior. `::test_real_setup_preflight_failures_precede_all_downloads()` asserts the real script returns 41, 42, 43, and 44 and that none of `curl`, `uv`, or `hf` ran. `::test_real_setup_sha_and_server_process_failures()` asserts real exits 46 and 48 and checks the server-error tail. `::test_real_setup_happy_path_runs_real_script()` exercises checksum, config parsing, and serve readiness. `pod/dqd_pod_setup.sh` gained `DQD_POD_WORK_PRIMARY`/`DQD_POD_WORK_FALLBACK` path overrides solely so this execution can remain isolated; production defaults remain `/workspace` and `$HOME/work`.

2. **Single-GPU invariant — fixed.** `pod/dqd_provision.py::_configure()` now unconditionally sets `GREEK_GPU_COUNT=1` before `prime_provision` is imported. `test_pod_runner.py::test_provision_adapter_overrides_hostile_gpu_count_before_helper_import()` begins with `GREEK_GPU_COUNT=8`, injects the helper at its import boundary, and proves the helper observes `1` when provisioning is called.

3. **Frozen forecast authentication — fixed.** `pod/run_stage.sh` now requires both `runtime/forecast.json` and `runtime/receipt.json` before provisioning, requires `artifacts["forecast.json"]["frozen"]` to be true, and compares the receipt SHA-256 with the exact forecast file bytes. `test_pod_runner.py::test_forecast_receipt_gate_precedes_provisioning()` covers a missing receipt and a mismatched hash and proves the provisioning event never occurs. The checked-in runtime receipt is frozen and its byte hash currently matches the forecast.

4. **Setup exit-code preservation — fixed.** `pod/run_stage.sh` now captures both elements of `PIPESTATUS` immediately after the SSH-to-`tee` pipeline, prints the diagnostic tail on remote failure, and exits with the SSH/setup status instead of replacing it with 71. The runner tests now assert exact return codes 41–44, 46, and 48 while also checking cleanup; code 71 is retained only for a local failure to persist setup output.

Testing:

```text
$ python3 -m unittest discover -p 'test_*.py'
................................................
----------------------------------------------------------------------
Ran 48 tests in 14.970s

OK
```

The suite also runs `bash -n` over every script in `pod/` and checks that none enables `set -x`.

Could not do: no live Prime pod, network access, model download, or live vLLM launch was attempted because CK3 explicitly limits this checkpoint to offline work. Those remain operational validation for the orchestrator's subsequent run; all requested offline branches now execute the production setup script itself.
