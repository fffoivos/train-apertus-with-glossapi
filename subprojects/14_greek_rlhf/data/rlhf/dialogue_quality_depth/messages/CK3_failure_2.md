# Execution failure 2 — `bash pod/run_stage.sh measurement` (2026-09-16T17:52:48Z)

Good: the provisioning fallback worked (runpod 503 → lambdalabs A100_40GB), preflight passed, vLLM 0.19.1 installed
(DQP_VLLM_OK), teardown confirmed, cost EUR 0.015. Then: `DQP_SETUP_FAIL code=45 reason=hf_token_missing`.
Log: runtime/pod/measurement_20260916T175248Z.log.

Diagnosis (orchestrator): the local token file exists and is non-empty (run_stage.sh line 108 passed) and is piped over ssh to
dqd_pod_setup.sh, which does `IFS= read -r hub_token || hub_token=""`. The token file has NO trailing newline, so `read` hits EOF,
returns non-zero, and the `||` branch erases the token it had already read. Fix: keep what was read (`IFS= read -r hub_token || true`,
then test `-n`), and add an offline test with a token fixture without a trailing newline (and one with). Nothing else changed; rerun
should proceed to download, sha check, serve, rollout.
