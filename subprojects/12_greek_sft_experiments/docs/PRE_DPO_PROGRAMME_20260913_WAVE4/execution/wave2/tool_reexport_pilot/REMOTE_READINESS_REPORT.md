# Remote readiness result

Both bounded CPU data-stage tasks are staged, strictly bound, canonically compiled and accepted by Slurm `--test-only`. No source pilot or ordinary Slurm job was launched. Both bound contracts remain nonlaunching with `allow_preparation_submission=false`.

## Dolci Tool Use 200

The target directories are owned by `fffoivos:a0140` with mode 750. The canonical runner is an exact archive of commit `01f4b7e21f39f346df61485bd1818f7ed07c7f44`; its compiled code-tree digest is `6a444277d60a09b0d7e517d7973c7b6204a76513cf80c38b22a650fad095a1d7`.

No row locator inventory crossed from the Mac. `inventory_source.py` ran against the already-cached public Dolci revision on CSCS and retained its inventory remotely only after the complete file SHA-256 matched `ee76456f63a7921a2311d45ad7a33cfea2f41dff58b539d4670b27584d47924e`. Its content-free summary matches the local freeze: 200 rows, 100 per relevant source shard, locator digest `41b0c7bca817986ac0bfb79a822678dad52427530308b590bb02b0cdf51a5302`.

The two selected parquet shard hashes and all three tokenizer/template hashes were rechecked directly against the cached CSCS files and match the frozen pilot contract.

The final compiled manifest is `88c7918c070b5db04927447ad88eec6b7346fd8c6b4627ceb17de1f3a392c4d1`, with contract digest `fb281d559d3657318c8028d7c074415ede1d532e26b0243b87573ed434fc1649`. The final scheduler-test receipt is `remote_readiness/dolci/scheduler_test_only_v2.json`, SHA-256 `4072ea8658afbf4638e6cb0546524b0e5f364d7e8f2869be6a3a98f0c9328a06`.

## OpenMath first-shard intake

The exact worker and contract plus three reviewed inputs were staged. `math_train.jsonl` is the documented public MATH training source with problems and reference solutions. The two family files contain source hashes, lineage and lane metadata without problem or solution text. Their classification and exact hashes are in `OPENMATH_INPUT_CLASSIFICATION.json`. The 212.93 MB public OpenMathInstruct shard remains unstaged and will be downloaded only inside this task if root launches it.

The final compiled manifest is `88ddd0202ce09e3189065c37c5fd94ac548389313abd4b7808da6ed6ce13c133`, with contract digest `9c51a08a74b5a437b775d65ec4b7bb49395ffdcf06d454ae9eec231188703ef4`. The final scheduler-test receipt is `remote_readiness/openmath/scheduler_test_only_v2.json`, SHA-256 `ce4eb2daaf16cb66a94f7c6690e03dc64ac2d21178b7ea850e6d33fa9ee20883`.

## Runtime and scheduler boundary

The task payload runtime is the pinned UENV plus `sft5` Python. A direct remote probe imports PyArrow 25.0.1, Datasets 5.0.1 and Transformers 5.16.1. The canonical array worker starts before that task UENV, so a separate system-Python worker environment was created at `/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_data_stage_runner_venv`. It uses Python 3.11.13 and only the six exact JSON Schema dependency versions in the canonical lockfile. The canonical module import passed. Training, evaluation and canonical code environments were not modified.

The final test-only receipts bind `APERTUS_DATA_STAGE_PYTHON` to that worker interpreter through the canonical command's `--export=ALL`. Each command asks for one debug node, 30 minutes, 8 CPUs, 64 GB, array `0%1`, no requeue and no GPU/GRES argument. Slurm accepted both commands. Its diagnostic describes a full debug node with 288 processors; this is scheduler placement on a GPU-equipped node even though the commands request no GPU resource. Planning remains CHF 1.345 per independent half-hour task and CHF 2.69 only if both launch.

The displayed Slurm test IDs have no `squeue` or `sacct` records, confirming `--test-only` created no jobs.

## Root review and apply boundary

The current manifests cannot submit because their approval flag is false. After review, root must rebind each contract with submission enabled, recompile, and repeat scheduler `--test-only` against those approved manifest bytes. The apply environment must export:

```text
APERTUS_DATA_STAGE_PYTHON=/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_data_stage_runner_venv/bin/python
```

The approved manifests remain independent and each permits one attempt only. A scheduler test does not authorize either source pilot or any later corpus promotion.
