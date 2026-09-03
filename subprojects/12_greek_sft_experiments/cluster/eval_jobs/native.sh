#!/usr/bin/env bash
# Native-Greek suite (8 benchmarks), the card's frozen FP32 legacy scorer, 21 shards, resume-safe.
# Usage: MODEL=<dir> LABEL=<run> bash native.sh   (uses all 4 GPUs of the node, shards round-robin)
set -euo pipefail; source "$(dirname "$0")/common.sh"
contract=$SUITE_ASSETS/peak_window_missing4_contract.json; manifest=$SUITE_ASSETS/peak_window_examples_manifest.json
for p in "$SUITE_RUNNER" "$SUITE_NATIVE_RUNNER" "$contract" "$manifest" "$WHEEL" "$MODEL/config.json"; do [[ -e "$p" ]] || { echo "missing $p" >&2; exit 2; }; done
shards=(demos other_mcq oyxoy_other oyxoy_wsd{0..9} oyxoy_wic{0..7})
run_task() {
  local shard=$1 gpu=$2 benchmarks row_index=0 row_count=1
  case "$shard" in
    demos) benchmarks=demosqa ;; other_mcq) benchmarks=medical_mcqa,asep_mcqa,gpcr ;; oyxoy_other) benchmarks=oyxoy_nli,oyxoy_metaphor ;;
    oyxoy_wsd*) benchmarks=oyxoy_wsd_definition; row_index=${shard#oyxoy_wsd}; row_count=10 ;;
    oyxoy_wic*) benchmarks=oyxoy_wic; row_index=${shard#oyxoy_wic}; row_count=8 ;;
  esac
  local d="$OUT/native/$shard"
  if [[ -f "$d/predictions.jsonl" && -f "$d/metrics.csv" ]]; then echo "[skip] $shard"; return 0; fi
  [[ ! -e "$d" ]] || mv "$d" "$OUT/native/incomplete_${shard}_$(date +%s)"
  hb "native shard $shard gpu=$gpu"
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default $UENV_IMAGE -- env PYTHONPATH="$WHEEL" HF_HUB_OFFLINE=1 python3 \
    "$SUITE_RUNNER" --contract "$contract" --manifest "$manifest" --native-runner "$SUITE_NATIVE_RUNNER" \
    --model "$LABEL=$MODEL" --output-dir "$d" --dtype float32 --scorer-mode legacy --benchmarks "$benchmarks" \
    --candidate-batch-size 1 --example-batch-size 16 --max-examples-per-benchmark 0 --row-shard-index "$row_index" --row-shard-count "$row_count" > "$OUT/logs/native_$shard.log" 2>&1
}
mkdir -p "$OUT/native"
# four GPU lanes, shards dealt round-robin
for g in 0 1 2 3; do ( i=$g; while [ $i -lt ${#shards[@]} ]; do run_task "${shards[$i]}" $g || echo "FAIL ${shards[$i]}"; i=$((i+4)); done ) & done; wait
hb "native done $LABEL"; ls "$OUT/native" | wc -l
