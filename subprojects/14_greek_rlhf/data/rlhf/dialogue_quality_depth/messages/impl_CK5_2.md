# CK5 cycle 2 implementation response

## Cause

The failure was in the uv bootstrap, before either CUDA-specific vLLM installation command ran. The decisive sequence is:

```text
DQP_PREFLIGHT_OK ... driver=580.126.09 cuda_track=13 ... vllm=0.29.0
DQP_SETUP_FAIL code=45 reason=uv_install
```

In `pod/dqd_pod_setup.sh`, `reason=uv_install` could only come from the unconditional pipeline:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The script had not yet reached `uv venv` or either `uv pip install` branch. Therefore the failure is not evidence of a bad `vllm==0.29.0` pin, a CUDA-13 wheel failure, or CUDA-12 `--torch-backend`/`--override` flags leaking into CUDA 13. The suppressed installer pipeline failed after preflight; the log cannot distinguish its curl and installer-shell components more narrowly.

Cleanup was complete: the ledger stop recorded EUR 0.0017422830530555552 for the failed pod and Prime deletion was confirmed. A read-only state check shows no active GPU session and no resample selections or candidates from the failed attempt.

## Fix

- `pod/dqd_pod_setup.sh`, uv bootstrap block:
  - reuses `uv` when the pod image already supplies it, eliminating an unnecessary dependency on `astral.sh`;
  - when uv is absent, downloads the standalone installer to the work directory with bounded retries (`--retry 5 --retry-all-errors`, 20-second connect timeout, 120-second total timeout) and runs it;
  - if that endpoint or installer still fails, falls back to `python3 -m pip install --user --disable-pip-version-check uv`;
  - still fails closed with setup code 45 if neither route produces an executable `uv`.
- The CUDA-specific vLLM commands themselves are unchanged:
  - driver 580+: plain `uv pip install --python ... vllm==0.29.0 huggingface_hub[cli]`, with no override or torch-backend flags;
  - older/CUDA-12: `vllm==0.19.1 --torch-backend=cu128 --override <(echo torchcodec)` exactly as before.
- `test_pod_runner.py::_real_setup_environment()` now models driver 580 and driver 570 independently, records the actual uv command lines, can start without uv, and can inject an Astral download failure.
- `test_pod_runner.py::test_real_setup_cuda_tracks_use_exact_dependency_commands()` proves the CUDA-13 command has the 0.29.0 pin and no leaked CUDA-12 flags, and proves the CUDA-12 command retains its 0.19.1/backend/override arguments.
- `test_pod_runner.py::test_real_setup_bootstraps_uv_only_when_missing()` proves both successful standalone bootstrapping and pip fallback after an installer-download failure.

Full offline suite:

```text
$ python3 -m unittest discover -p 'test_*.py'
..............................................................
----------------------------------------------------------------------
Ran 62 tests in 24.313s

OK
```

## Next orchestrator command

No separate teardown or resume repair is needed. Run the same entry command again:

```bash
bash pod/run_stage.sh resample
```

I did not exclude driver-580 offers: the observed failure happened before the CUDA-13 vLLM install branch, the requested plain 0.29.0 command is intact and now tested, and the prior round-1 580-driver run establishes that this vLLM path can work. Excluding those offers would not address the logged cause.
