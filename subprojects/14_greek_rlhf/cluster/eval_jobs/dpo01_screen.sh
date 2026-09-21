#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_screen
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=03:30:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_screen_%j.out
# DPO01 selection lane: Greek IFEval (150) + MGSM (50) from the frozen screen manifest,
# for the parent and all 12 epoch checkpoints. Four models at a time, one per GPU.
# Scorers, few-shot, decoding and chat template are the frozen ilsp ones; only the
# document set is restricted, by evals/ilsp/tasks/*/screen_filter.py.
# --log_samples is REQUIRED, not optional: plan section 8 needs paired item-level bootstrap and
# improved/regressed counts, and the confirmed IFEval baseline applies rescore_ifeval_langdetect.py
# to saved samples. Aggregate-only scores cannot be made comparable to that baseline afterwards. The screen yamls live
# INSIDE the production task dirs so the frozen utils.py resolves its sibling package as designed.
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
OUT=$ROUND/results/G4F6P1--DPO01/screen
MANIFEST=$ROUND/results/G4F6P1--DPO01/screen_manifest.json
mkdir -p "$OUT"

# The parent is the exact directory the four DPO arms initialised from (see the arm configs).
PARENT=$ROUND/eval_copies/R4_full_ep1
[ -d "$PARENT" ] || { echo "FATAL: parent not found at $PARENT"; exit 1; }

MODELS=()
MODELS+=("parent|$PARENT")
for arm in 00 01 02 03; do
  for ep in 1:43 2:86 3:129; do
    MODELS+=("arm${arm}_ep${ep%%:*}|$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}")
  done
done
echo "HB $(date -u +%FT%TZ) screen start: ${#MODELS[@]} models, manifest $(sha256sum "$MANIFEST" | cut -c1-16)"

# Every model is scored with the PARENT's tokenizer. transformers 5.16.1 (used for DPO) re-serialised
# the tokenizer with tokenizer_class TokenizersBackend, which the container's transformers 4.57.0 cannot
# load. tokenizer.json is byte-identical between parent and checkpoints, and the checkpoint chat template
# equals the parent's exactly once the training-only {% generation %} markers are stripped (verified:
# 14601 chars both), so this changes no prompt - and it guarantees one identical protocol across all 13.
run_one() {  # $1 = "label|path", $2 = gpu index
  local label=${1%%|*} path=${1##*|} gpu=$2
  local dir="$OUT/$label"
  if [ -s "$dir/DONE" ]; then echo "HB skip $label (done)"; return 0; fi
  if [ ! -d "$path" ]; then echo "HB MISSING $label -> $path"; return 1; fi
  mkdir -p "$dir"
  local t0=$(date +%s)
  echo "HB $(date -u +%FT%TZ) start $label gpu=$gpu"
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    export PYTHONPATH=$WHEEL:$S/python_envs/lm_eval
    # scipy/sklearn load bundled shared objects that live in these wheel .libs dirs (see eval_jobs/greekmmlu.sh);
    # without this, sklearn -> scipy.special fails on libgfortran and every model dies in ~20s.
    export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    export HF_HOME=$ROUND/hf_home HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
    export SCREEN_MANIFEST=$MANIFEST
    export TOKENIZERS_PARALLELISM=false
    cd $ROUND
    python3 -m lm_eval --model hf \
      --model_args pretrained=$path,tokenizer=$PARENT,dtype=bfloat16 \
      --tasks ifeval_greek_screen,mgsm_greek_screen \
      --apply_chat_template \
      --include_path evals_code/ilsp/tasks \
      --batch_size 8 \
      --log_samples \
      --output_path $dir
  " > "$dir/run.log" 2>&1
  local rc=$? el=$(( $(date +%s) - t0 ))
  # lm_eval saves results, THEN prints a summary table; that print dies on a broken chardet in
  # pytablewriter (AttributeError: module 'chardet' has no attribute 'detect'). The scores are
  # already on disk at that point, so success is "a results json exists", not "rc == 0".
  local got=$(find "$dir" -name "results_*.json" 2>/dev/null | head -1)
  if [ -n "$got" ]; then
    echo "$(date -u +%FT%TZ) rc=$rc elapsed=${el}s results=$got" > "$dir/DONE"
    echo "HB $(date -u +%FT%TZ) done $label in ${el}s"
  else
    echo "HB $(date -u +%FT%TZ) FAILED $label rc=$rc in ${el}s (see $dir/run.log)"
    tail -15 "$dir/run.log"
  fi
  return $rc
}

i=0
while [ $i -lt ${#MODELS[@]} ]; do
  pids=()
  for g in 0 1 2 3; do
    idx=$(( i + g ))
    [ $idx -ge ${#MODELS[@]} ] && break
    run_one "${MODELS[$idx]}" "$g" &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done
  i=$(( i + 4 ))
  echo "HB $(date -u +%FT%TZ) wave complete, $i/${#MODELS[@]} dispatched"
done

echo "HB $(date -u +%FT%TZ) screen finished"
ls -d "$OUT"/*/ 2>/dev/null | while read d; do
  printf '%-14s %s\n' "$(basename $d)" "$([ -s "$d/DONE" ] && cat "$d/DONE" || echo INCOMPLETE)"
done
