# Checkpoint CK3 — take over the pod runner and make it robust; the orchestrator will execute your entry command

Owner's instruction: Sol implements and debugs the Prime Intellect runs; the orchestrator only starts checkpoints, executes the single
entry command you provide, and returns logs. Until now the orchestrator wrote the pod scripts by hand and wasted two sessions
(root-owned /workspace; --max-model-len above the checkpoint's 4,096). Those scripts, with the two fixes, are in ./pod/
(dqd_provision.py, dqd_pod_setup.sh, dqd_pod_stage.sh). Take them over and harden them. Offline work only in this checkpoint: no network,
no pod, no Sol call. Secrets stay where they are (~/.config/prime/key, ~/.cache/huggingface/token, ~/.ssh/prime_intellect_key): scripts
read them and pass them as environment variables to the one command that needs them; never print, echo, log or copy them.
Provisioning helper, import read-only, do not modify: /Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts/prime_provision.py
(get_availability, cmd_provision, cmd_teardown; env PRIME_INTELLECT_CONTROL_KEY, GREEK_SWEEP_POD_STATE, GREEK_SWEEP_GPU_WHITELIST,
PRIME_MAX_PRICE_HR, PRIME_MAX_HOURS, GREEK_SWEEP_IMAGE).

Deliver in ./pod/ one entry command: `bash pod/run_stage.sh <measurement|candidates>` that does everything:
- Provision A100_40GB (price cap $2.5/h, any secure single-GPU datacenter; A100_80GB or L40S acceptable if cheaper), wait for ssh.
- Preflight ON THE POD before any download: writable work dir (chown /workspace or fall back to $HOME/work), ≥ 40 GB free, driver CUDA
  major → vLLM wheel (0.29.0 on CUDA 13 drivers = driver ≥ 580; vllm==0.19.1 + `--torch-backend=cu128 --override <(echo torchcodec)` on
  CUDA 12 drivers), GPU memory ≥ 38 GB. Abort with a clear code on any failure.
- Model from the Hub (fffoivos/greek-apertus-8b-sft-r4-full); sha256 of model.safetensors must equal
  54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763 or abort; read max_position_embeddings from the downloaded config.json
  and serve with exactly that --max-model-len; served model name = the Hub id; VLLM_USE_FLASHINFER_SAMPLER=0; port 8000; ssh tunnel to
  local 8000; a serve-ready loop that fails within seconds if the server process dies (print its last error lines).
- `dqd.py ledger gpu-start` right after provisioning, then the stage: measurement = `dqd.py rollout measurement --endpoint
  http://127.0.0.1:8000/v1 --model fffoivos/greek-apertus-8b-sft-r4-full --checkpoint-sha256 <sha> --max-turns 8 --concurrency 8`;
  candidates = `dqd.py candidates measurement ...`.
- ALWAYS on exit (trap): `dqd.py ledger gpu-stop`, DELETE the pod, confirm deletion, print a one-line receipt. Plus an independent
  watchdog process started at provisioning that tears the pod down at the budget deadline from `runtime/forecast.json`/budget.py even
  if the rollout hangs, and logs that it did. Logs under runtime/pod/<stage>_<utc>.log; never the secrets.
- Offline tests: bash -n on the scripts; a Python test that drives run_stage.sh's decision logic with a fake pod (fake ssh/curl shims on
  PATH) through: preflight failure paths, sha mismatch abort, serve death, happy path, and trap teardown on failure.
Write messages/impl_CK3_1.md: what changed, how to run, what the tests cover, known limits. The orchestrator will then run
`bash pod/run_stage.sh measurement` and, if it fails, send you the log in the next cycle.
