#!/usr/bin/env bash
#SBATCH --job-name=full8_merged_native
#SBATCH --account=a0140
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=01:29:00
#SBATCH --output=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.out
#SBATCH --error=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.err
#
# Clean native-Greek suite (frozen FP32 legacy scorer, strict 73,894-example
# subset) for ONE checkpoint-average model. Mirrors the authoritative
# peak-window/remaining12 invocation exactly (same frozen code bundle,
# contract, manifest, dtype float32, scorer-mode legacy, 21 shard layout);
# resume-safe: completed shards are skipped.
# Required env: MERGED_LABEL (avg_peak5|avg_cooldown5), MERGED_MODEL (HF dir).

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
: "${MERGED_LABEL:?}"; : "${MERGED_MODEL:?}"

SOURCE_ROOT=/iopsstor/scratch/cscs/fffoivos/evals/full8_native_greek_3cp_20260812
EVAL_CODE_ROOT="$SOURCE_ROOT/code/036e1e2e53e13d3cd58cc8cb22b3c38a52881580"
runner="$EVAL_CODE_ROOT/subprojects/09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py"
native_runner="$EVAL_CODE_ROOT/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py"
assets=/iopsstor/scratch/cscs/fffoivos/evals/full8_native_greek_peak_window_20260817/clean_assets_v5
contract="$assets/peak_window_missing4_contract.json"
manifest="$assets/peak_window_examples_manifest.json"
wheel=/iopsstor/scratch/cscs/fffoivos/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
OUT=/iopsstor/scratch/cscs/fffoivos/evals/full8_merged_native_20260819/$MERGED_LABEL
mkdir -p "$OUT" "$OUT/logs"

for p in "$runner" "$native_runner" "$contract" "$manifest" "$wheel" "$MERGED_MODEL/config.json"; do
  [[ -e "$p" ]] || { echo "missing $p" >&2; exit 2; }
done

shards=(demos other_mcq oyxoy_other oyxoy_wsd{0..9} oyxoy_wic{0..7})

run_task() {
  local shard=$1 benchmarks row_index=0 row_count=1
  case "$shard" in
    demos) benchmarks=demosqa ;;
    other_mcq) benchmarks=medical_mcqa,asep_mcqa,gpcr ;;
    oyxoy_other) benchmarks=oyxoy_nli,oyxoy_metaphor ;;
    oyxoy_wsd*) benchmarks=oyxoy_wsd_definition; row_index=${shard#oyxoy_wsd}; row_count=10 ;;
    oyxoy_wic*) benchmarks=oyxoy_wic; row_index=${shard#oyxoy_wic}; row_count=8 ;;
  esac
  local d="$OUT/$shard"
  if [[ -f "$d/predictions.jsonl" && -f "$d/metrics.csv" ]]; then
    echo "[skip] $shard complete"; return 0
  fi
  [[ ! -e "$d" ]] || mv "$d" "$OUT/incomplete_${shard}_$(date +%s)"
  CUDA_VISIBLE_DEVICES=$2 uenv run --view=default pytorch/v2.9.1:v2 -- \
    env PYTHONPATH="$wheel" python3 \
      "$runner" --contract "$contract" --manifest "$manifest" \
      --native-runner "$native_runner" --model "$MERGED_LABEL=$MERGED_MODEL" \
      --output-dir "$d" --dtype float32 \
      --scorer-mode legacy --benchmarks "$benchmarks" \
      --candidate-batch-size 1 --example-batch-size 16 \
      --max-examples-per-benchmark 0 --row-shard-index "$row_index" \
      --row-shard-count "$row_count" \
      > "$OUT/logs/${shard}.log" 2>&1
  echo "[done] $shard $(date -u +%H:%M:%S)"
}

echo "=== merged native eval $MERGED_LABEL job ${SLURM_JOB_ID:-manual} $(date -u) ==="
pids=()
for g in 0 1 2 3; do
  (
    for i in "${!shards[@]}"; do
      [[ $((i % 4)) -eq $g ]] && run_task "${shards[$i]}" "$g"
    done
  ) &
  pids+=("$!")
done
FAIL=0
for p in "${pids[@]}"; do wait "$p" || FAIL=1; done
echo "=== finished fail=$FAIL $(date -u) ==="
exit $FAIL
