# R-DPO7b — measurement-protocol review

**Verdict:** HOLD publication, but do **not** kill the full GreekMMLU job: its predictions are salvageable. The job scores 16,632 raw items, not the claimed 16,159 clean subset. The scoring flags otherwise match the 250-item job.

## Findings

### [BLOCKER] The “16,159-item” job produces a 16,632-item raw headline

[`cluster/eval_jobs/dpo01_greekmmlu_full.sh:89`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:89), [`run_native_greek_mcq_eval.py:39`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py:39), [`finalize_hf_greekmmlu.py:73`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/07_full_8b_cpt/evaluation/finalize_hf_greekmmlu.py:73)

Removing `--sample-size` selects the runner’s default `0`, which means all **16,632 raw test rows**. The headline is calculated from all those rows. The 16,159 clean subset is applied only by the downstream finalizer.

That finalizer is exactly the known `ca0b18b342e3…` version. It requires 16,632 predictions, then filters them to 16,159. It also rejects checkpoint configs lacking top-level `rope_theta`; the job deliberately treats the raw headline as success when that happens.

Concrete failure scenario: the artifact labels a raw 16,632-item headline as the clean 16,159 result—or uses the parent’s clean receipt while falling back to raw headlines for arms—creating a fake parent/arm difference.

Fix: preserve the running job. Its 16,632 predictions contain the clean subset. Before publication, run a geometry-independent finalization step that validates 16,632 unique raw IDs, verifies the clean-manifest hash, requires exactly 16,159 unique clean IDs, and atomically emits the clean result for every model. Alternatively, publish all eight numbers explicitly as **raw 16,632**. The existing 250 slice was sampled from the raw 16,632 frame, so raw-full is the directly matched population; a clean-full comparison also requires checking/filtering the 250 IDs.

### [HIGH] Fixed shared symlink stages admit checkpoint corruption under a race or failed unlink

[`cluster/eval_jobs/dpo01_armcfg_cell.sh:20`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_armcfg_cell.sh:20), [`cluster/eval_jobs/dpo01_gencfg_control.sh:16`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:16)

For one non-racing invocation, the order is safe: `rm -f` unlinks `STAGE/config.json`, and Python creates a regular file rather than following the old symlink.

It is not fail-closed. The stage name is shared across invocations and the outer shell lacks `-e`. A duplicate job can recreate the config symlink after job A removes it but before job A opens it for writing; job A then truncates `$SRC/config.json`. An unlink failure produces the same path. Pre-existing directory symlinks also expose `ln -sf`’s destination-directory dereferencing behavior.

Fix: use a job-unique temporary stage, symlink only weight shards/indexes, copy configuration files as regular files from the outset, enable `set -euo pipefail`, and assert every writable staged file is regular and not a symlink before opening it. Use `ln -sfn`/`-T` where directory entries must be linked.

For the live job, immediately confirm there is only one invocation and inspect staging logs. Verify hashes of source `config.json` and tokenizer files against pre-run receipts. A sole run with successful removals does not need to be killed.

### [HIGH] “Tokenizer unchanged” is asserted in comments but not enforced

[`cluster/eval_jobs/dpo01_greekmmlu.sh:68`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu.sh:68), [`cluster/eval_jobs/dpo01_greekmmlu_full.sh:68`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:68)

Both scripts replace `tokenizer.json`, `tokenizer_config.json`, and `special_tokens_map.json` without comparing them. If the checkpoint’s `tokenizer.json` differs, this changes token IDs or segmentation. Copying the complete tokenizer configuration can also change special-token behavior beyond correcting `tokenizer_class`.

Fix: fail unless `tokenizer.json` and the special-token map are byte-identical; normalize only the expected `tokenizer_class` field and require every other tokenizer-config field to match. Record both source hashes in the result metadata. If equality cannot be proved, patch only the incompatible class field and run a token-ID equivalence probe over the actual prompts.

### [HIGH] Missing models and worker failures still produce a successful job

[`cluster/eval_jobs/dpo01_greekmmlu_full.sh:58`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:58), [`cluster/eval_jobs/dpo01_greekmmlu_full.sh:95`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:95), [`cluster/eval_jobs/dpo01_full.sh:98`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_full.sh:98), [`cluster/eval_jobs/dpo01_armcfg_cell.sh:41`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_armcfg_cell.sh:41)

A missing selected checkpoint prints `WARN` and is omitted; there is no assertion that eight models were assembled. After an evaluator failure, `run_one` ends with a successful `tail` or `echo`, so the background process returns zero. Even a nonzero `wait` would not abort because the outer script lacks `-e`. The scripts subsequently print `GREEKMMLU_DONE`, `FULL_SUITE_DONE`, or `CELL_DONE` and exit successfully.

Fix: preflight all expected labels, directories, indexes, shards, and configurations before launching; require exactly eight full-run models. Return nonzero for an invalid result, collect every `wait` status explicitly so all four workers can finish, and exit nonzero after the wave if any failed.

### [MEDIUM] Headline existence alone can accept a malformed or wrong-size result

[`cluster/eval_jobs/dpo01_greekmmlu_full.sh:65`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:65), [`run_native_greek_mcq_eval.py:581`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py:581)

An ordinary crash during scoring leaves no headline—the runner writes it only after all scoring, predictions, and summary output. But `write_text` is not atomic, so interruption during the final write can leave an existing malformed file that the resubmission skips. No JSON, metadata, item-count, or unique-ID validation is performed.

Fix: write the headline via temporary file plus `os.replace`, and have the shell validate schema, population, unique IDs, revision/fingerprint, and expected label before accepting or skipping it.

The new `greekmmlu_full` directory is distinct from `greekmmlu`; there is no code path that automatically reads the 250-result directory.

### [MEDIUM] The reverse config overlay is not fully symmetric

[`cluster/eval_jobs/dpo01_armcfg_cell.sh:33`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_armcfg_cell.sh:33), [`cluster/eval_jobs/dpo01_gencfg_control.sh:35`](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:35)

The arm-under-parent script correctly deletes fields absent from the parent. The parent-under-checkpoint script only assigns fields present in the checkpoint; it does not delete a parent field absent from the checkpoint. It also assumes without checking that arm01 and arm05 have identical checkpoint configuration bundles.

Concrete failure scenario: a checkpoint lacks `bos_token_id` while the parent contains it; `parent_ckptcfg` silently retains the parent value and is not truly under the checkpoint configuration.

Fix: use one shared overlay routine in both directions: assign fields present in the source and delete fields absent from it. Assert that the relevant configuration bundle is identical across every arm represented by the common checkpoint-config cell.

## Verified correct

- The full and 250 scoring commands have identical registry, benchmark, model/prompt route, `float32`, 3072-token limit, candidate batch 16, example batch 16, and remote-code setting. Only the two sampling arguments were removed. The prompt function and pinned dataset revision are therefore identical.
- The full runner defaults to `sample_size=0`; omitted `random_state` still defaults to 42 but has no effect when no sampling occurs.
- On the single-job happy path, `rm -f` removes the replacement symlinks before copying/writing. No arm version of the five replaced files remains. Missing fields are correctly deleted in the arm-under-parent direction.
- The staged model retains the arm’s weight shards and index; no parent weights are copied. The main lane and both 2×2 cells explicitly use the parent tokenizer, so tokenizer choice is constant across those generated-task cells.
- `wait` provides a proper four-process wave barrier, and GPUs 0–3 are assigned one per worker through `CUDA_VISIBLE_DEVICES`. Status propagation is the defect.
- The model list parses correctly with `IFS='|' read`: seven arms plus the parent gives eight models.
- Checkpoint mapping is correct: `ceil(343/8)=43` updates per standard epoch, hence epoch 3 is checkpoint 129; `ceil(274/8)=35`, hence `armBAL` epoch 3 is checkpoint 105.
- Two estimated 2.8-hour waves are about 5.6 hours; 12 hours gives ample forecast headroom even for the actual 16,632 rows. Completed model files survive walltime. An in-flight model has no incremental prediction checkpoint and must restart.
- `bash -n` passes on all five scripts.
- Following the CSCS exact-profile guidance, I treated protocol identity as a hard gate and the six-hour walltime calculation as a forecast rather than a scheduler guarantee.

## Ordered asks

1. Let the current full job finish, but quarantine its numbers from publication. Finalize every 16,632-row prediction file into one consistently labelled raw or clean metric.
2. Check immediately that only one instance of each staging job ran; inspect staging errors and verify source checkpoint/config/tokenizer hashes.
3. Before republishing, add tokenizer equivalence checks, unique stage directories, exact eight-model preflight, validated completion receipts, and aggregated nonzero exit status.
4. Make the config overlay symmetric and verify arm01/arm05 configuration-bundle identity.
5. Re-run only missing or invalid models/cells; valid 16,632-row predictions do not need another GPU pass.

VERDICT: HOLD: the live full run measures 16,632 raw items, not the claimed 16,159 clean subset; outputs are salvageable but must not be republished until finalization and three HIGH protocol defects are fixed | BLOCKERS: 1 | HIGH: 3

