# CK3 cycle 5 implementation response

## Cause

Provisioning fallback succeeded and the real pod passed preflight and installed/imported vLLM. The failure was token ingestion at the start of `pod/dqd_pod_setup.sh`. The local Hugging Face token file is non-empty but has no trailing newline. Bash `read` assigns the unterminated final line to `hub_token` and then returns non-zero because it reached EOF. The existing `IFS= read -r hub_token || hub_token=""` consequently erased the valid token, producing `DQP_SETUP_FAIL code=45 reason=hf_token_missing` before the Hub download.

The run cleaned up correctly: ledger stop recorded EUR 0.015043622241666665 and deletion of pod `27bd2cbb87904a27874cd0d6f6d64cc3` was confirmed.

## Fix

- `pod/dqd_pod_setup.sh` token-ingestion block: initialize `hub_token`, then run `IFS= read -r hub_token || true`. This retains bytes read from an unterminated final line. The existing `[[ -n "$hub_token" ]] || fail 45 "hf_token_missing"` check remains in place, so empty stdin still fails closed. Token logging/export behavior is unchanged.
- `test_pod_runner.py::_run_real_setup()` now accepts a `token_trailing_newline` fixture option.
- `test_pod_runner.py::test_real_setup_happy_path_runs_real_script()` executes the actual production setup script twice: once with a token file containing no trailing newline and once with a newline. Both cases must reach the fake `hf download`, checksum/config checks, and serve-ready marker without exposing the token.

Validation:

```text
$ python3 -m unittest discover -p 'test_*.py'
..................................................
----------------------------------------------------------------------
Ran 50 tests in 22.126s

OK
```

## Next orchestrator command

No separate teardown is required because the failed run's deletion was confirmed. Run:

```bash
bash pod/run_stage.sh measurement
```
