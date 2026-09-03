#!/usr/bin/env bash
#SBATCH --job-name=full8_merged_greekmmlu
#SBATCH --account=a0140
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=2
#SBATCH --cpus-per-task=144
#SBATCH --mem=480G
#SBATCH --time=01:25:00
#SBATCH --output=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.out
#SBATCH --error=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.err
#
# Clean GreekMMLU (frozen FP32 exact evaluator + 16,159-question clean-subset
# finalizer) for the two checkpoint-average models. Mirrors
# 07/clariden/run_initial_greekmmlu.sbatch exactly (same runner flags, same
# registry, same clean-subset manifest), one model per GPU.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

B=/iopsstor/scratch/cscs/fffoivos/orchestration/full8b-cpt/20260807T221007Z-sanitized-v43
NATIVE_ROOT="$B/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval"
FINALIZER="$B/subprojects/07_full_8b_cpt/evaluation/finalize_hf_greekmmlu.py"
CLEAN_SUBSET=/capstor/scratch/cscs/fffoivos/cpt_runs/dataset-scheduling-0p5b/20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json
PYENV=/iopsstor/scratch/cscs/fffoivos/python_envs/lm_eval
WHEEL=/iopsstor/scratch/cscs/fffoivos/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
MERGED=/capstor/scratch/cscs/fffoivos/experiments/full8_checkpoint_averaging_20260819
OUT=/iopsstor/scratch/cscs/fffoivos/evals/full8_merged_greekmmlu_20260819

run_one() {
  local gpu="$1" label="$2" model="$3"
  local root="$OUT/$label"
  mkdir -p "$root/greekmmlu"
  echo "[slot] gpu=$gpu $label start=$(date -u +%H:%M:%S)"
  CUDA_VISIBLE_DEVICES="$gpu" uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    export PYTHONPATH=$WHEEL:$PYENV
    export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    export HF_TOKEN=\$(cat /users/fffoivos/.cache/huggingface/token)
    python3 '$NATIVE_ROOT/run_native_greek_mcq_eval.py' \
      --registry '$NATIVE_ROOT/native_greek_benchmark_registry.json' \
      --benchmarks greekmmlu --model '$label=$model' \
      --output-dir '$root/greekmmlu' --sample-size 0 \
      --random-state 42 --dtype float32 --max-input-tokens 3072 \
      --candidate-batch-size 16 --example-batch-size 16 --trust-remote-code
    python3 '$FINALIZER' \
      --model '$model' --evaluation-root '$root/greekmmlu' \
      --model-label '$label' --clean-subset-manifest '$CLEAN_SUBSET' \
      --output '$root/greekmmlu_receipt.json'
  " > "$root/slot.log" 2>&1
  echo "[slot] gpu=$gpu $label done=$(date -u +%H:%M:%S)"
}

mkdir -p "$OUT"
echo "=== merged GreekMMLU job ${SLURM_JOB_ID:-manual} $(date -u) ==="
run_one 0 avg_peak5 "$MERGED/peak5_uniform" &
P0=$!
run_one 1 avg_cooldown5 "$MERGED/cooldown5_uniform" &
P1=$!
FAIL=0
wait $P0 || FAIL=1
wait $P1 || FAIL=1
echo "=== finished fail=$FAIL $(date -u) ==="
exit $FAIL
