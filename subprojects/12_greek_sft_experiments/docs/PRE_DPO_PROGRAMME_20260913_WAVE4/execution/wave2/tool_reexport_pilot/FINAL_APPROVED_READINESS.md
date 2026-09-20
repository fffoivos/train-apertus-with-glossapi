# Final approved preparation readiness

Both root-reviewed CPU preparation contracts were rebound with `allow_preparation_submission=true`, compiled with the frozen canonical runner, and accepted by Slurm `--test-only` on their final manifest bytes. This step did not submit either job.

## Dolci Tool Use 200

- Approved contract SHA-256: `45f646258665067b814b3706ef580bc5669d3fb3462ea24d55e200544a54ea2d`
- Canonically compiled manifest SHA-256: `62670ea9d50284a5b758c21971faeace43c140bb9e1121fb2caf49177ca330fb`
- Contract digest: `953b052353217ae9d53dfee34abf15c30d8231a75c3878a17789243e8f25d4c4`
- Exact scheduler-test receipt SHA-256: `b412c481dad7a93403eef845b13867aef03483066a60b6c20ccc78c858316596`
- Slurm test-only display ID: `3391276`

## OpenMath original-solution intake

- Approved contract SHA-256: `def6b28bd300a5b0d9f316164a291edf98dd30f00fdc5348bdbbe42675505dd2`
- Canonically compiled manifest SHA-256: `53a0710412c799ad5bdafe05dae6e5b276d048058fca4b3692617646d3a631d6`
- Contract digest: `462a925790a5dbd76d0b4a627ea90e8ebe69c92f480a7141ac98fa10257b9c1d`
- Exact scheduler-test receipt SHA-256: `bfed866eb6354d1bfeb4323c0d40f3b5d2d40e949c043b162c31a969f261a24b`
- Slurm test-only display ID: `3391277`

## Frozen common bindings

- Canonical runner commit: `01f4b7e21f39f346df61485bd1818f7ed07c7f44`
- Compiled canonical code-tree SHA-256: `6a444277d60a09b0d7e517d7973c7b6204a76513cf80c38b22a650fad095a1d7`
- Exact scheduler-test wrapper SHA-256: `1f10d5d9d144075ea12ad86156495a5c570b02c977da00958cead44c4daef60d`
- Fresh live-cluster receipt SHA-256: `87977dd501ba1dea3ad488a01cb0f5c133ebc12dab3177962b97b05a15359274`
- Canonical worker interpreter: `/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_data_stage_runner_venv/bin/python`

Each manifest requests account `a0140`, one `debug` node, 30 minutes, 8 CPUs, 64 GB, array `0%1`, one attempt, and no requeue. Neither command contains a GPU or GRES argument. Slurm's test-only diagnostic still describes placement on a full node with 288 processors; this does not add a GPU resource request.

The displayed test-only IDs have no rows in either `squeue` or `sacct`. The prepared canonical commands in `final_approved_staging_receipt.json` remain unexecuted.

The maximum planned charge is CHF 1.345 for each independent pilot, or CHF 2.69 if root launches both. Any retry, extension, later export, or production mutation remains outside this freeze.

## Verification artifacts

- `remote_readiness/dolci/data_stage_contract.approved.json`
- `remote_readiness/dolci/compiled_data_stage.approved.json`
- `remote_readiness/dolci/scheduler_test_only_approved.json`
- `remote_readiness/openmath/data_stage_contract.approved.json`
- `remote_readiness/openmath/compiled_data_stage.approved.json`
- `remote_readiness/openmath/scheduler_test_only_approved.json`
- `final_approved_staging_receipt.json`
- `validation_receipt_approved.json`

The validator parses the source and preparation artifacts, rechecks the immutable selection and worker bindings, confirms both approval objects and resource caps, compares each canonical compiler output to its approved contract apart from the compiler's documented reduction of the live receipt binding to its verified path, and binds each scheduler receipt to the exact approved manifest hash and contract digest.
