# CK3 implementation response

## What I built

### Single entry command

The orchestrator entry point is now:

`bash pod/run_stage.sh <measurement|candidates>`

`pod/run_stage.sh` owns the complete paid-window lifecycle:

- validates the frozen admitted forecast before provisioning;
- provisions through the read-only imported Prime helper with a $2.50/hour cap, one secure-cloud GPU, and the cheapest permitted `A100_40GB`, `A100_80GB`, or `L40S_48GB` offer;
- records `dqd.py ledger gpu-start` immediately after provisioning;
- arms an independent local deadline watchdog using the shutdown deadline persisted by `budget.py`;
- waits for SSH, uploads the secret-free setup script, sends the Hub token only over setup stdin, and opens an `ExitOnForwardFailure` tunnel from local port 8000 to pod port 8000;
- runs exactly the required measurement rollout or candidate-generation command with the frozen model ID, checkpoint SHA, and measurement horizon;
- logs to `runtime/pod/<stage>_<UTC>.log` and emits a final one-line `DQP_STAGE_RECEIPT`;
- on every exit after GPU accounting, stops the GPU ledger, invokes the Prime DELETE path, and requires `DELETE_CONFIRMED`. Cleanup failure changes an otherwise successful exit into a failure.

The old `pod/dqd_pod_stage.sh` is now only a compatibility wrapper to the CK3 entry point.

### Provisioning adapter

Replaced `pod/dqd_provision.py` with a narrow adapter around the unmodified external `prime_provision.py`:

- imports it read-only only after setting its documented environment;
- permits only `A100_40GB`, `A100_80GB`, and `L40S_48GB`;
- retains secure-cloud, single-GPU, global cheapest-offer ranking from the helper;
- fixes the hard price ceiling at $2.50/hour and its independent pod self-kill at two hours;
- stores state under this project’s `runtime/pod` tree;
- exposes only `provision` and `teardown`, and reports deletion confirmed only after the helper succeeds and clears the pod-state file.

The external Prime helper was not modified.

### Pod preflight, model verification, and serving

Hardened `pod/dqd_pod_setup.sh`. Before its first download it now checks, in order:

- `/workspace` can be created/chowned and written, otherwise `$HOME/work` is used;
- the chosen work filesystem has at least 40 GB free;
- the NVIDIA driver version is readable;
- GPU memory is at least 38,000 MB;
- driver major 580 or newer selects `vllm==0.29.0`; older CUDA-12 drivers select `vllm==0.19.1 --torch-backend=cu128 --override <(echo torchcodec)`.

Failures use explicit `DQP_SETUP_FAIL` codes 41–44 before any download. Dependency/setup failures use 45.

After setup, the script:

- passes the Hub token as an environment variable only to the single `hf download` command, then removes the shell value;
- requires `model.safetensors` and compares its SHA-256 exactly with `54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763` (code 46 on failure);
- reads and validates `max_position_embeddings` from downloaded `config.json` (code 47), and uses exactly that value for `--max-model-len`;
- serves with the Hub ID as `--served-model-name`, `VLLM_USE_FLASHINFER_SAMPLER=0`, localhost port 8000, and no hard-coded context length;
- polls every two seconds, aborts with code 48 if the server process dies, and prints the last 20 server-log lines; readiness timeout is code 49.

No pod script enables shell tracing. The Prime key is supplied only to provisioning/deletion command environments. The Hub token is sent through stdin and supplied only to the download command. Neither value is printed, echoed, logged, or copied to a file or pod path. The SSH private key remains a local SSH argument and is never copied.

### Independent watchdog

Added `pod/watchdog.sh`. It is launched with `nohup` immediately after `gpu-start`, independently reads the `budget.py` deadline from the immutable GPU-start ledger row, sleeps to that deadline, then performs ledger stop and Prime DELETE itself. It records `DQP_WATCHDOG_RECEIPT` and terminates the hung parent so the parent EXIT trap can finish. A marker prevents a second DELETE race when watchdog teardown already succeeded. The imported Prime helper’s on-pod two-hour self-kill remains an additional backstop.

## How I tested it

Added `test_pod_runner.py`, which invokes the real `pod/run_stage.sh` with fake `python3`, SSH, SCP, and curl shims on `PATH`. It covers:

- unwritable work directory (setup code 41);
- less than 40 GB free (42);
- unreadable driver (43);
- less than 38 GB GPU memory (44);
- checkpoint SHA mismatch (46);
- server-process death with last error lines (48);
- successful measurement and candidates paths;
- stage-command failure with preservation of the original exit code;
- GPU ledger stop and confirmed teardown on every post-provision failure;
- absence of sentinel Prime/Hugging Face secrets from captured output and every generated log;
- `bash -n` and no `set -x` for every shell script under `pod/`.

Validation commands:

`bash -n pod/*.sh`

`python3 -m py_compile pod/dqd_provision.py test_pod_runner.py`

`python3 -m unittest discover -p 'test_*.py'`

Result:

`Ran 43 tests in 7.418s`

`OK`

## What I could not do and why

- I did not contact Prime Intellect, provision a pod, use SSH/network access, download the model, start vLLM, or call Apertus/Sol. CK3 explicitly requires offline work. The fake-pod tests verify local orchestration and decision paths, not provider behavior, actual image contents, live driver/wheel compatibility, Hub layout, SSH readiness, or real teardown API semantics.
- The checkpoint assumes the Hub repository contains the required single file named `model.safetensors`, as CK3 specifies. If the live repository layout differs, setup deliberately aborts rather than hashing a different artifact.
- The next live evidence must come from the orchestrator’s exact entry command. A failure should be returned with the generated `runtime/pod/measurement_<UTC>.log`; the runner is designed to preserve and report that failure while still stopping accounting and confirming deletion.
