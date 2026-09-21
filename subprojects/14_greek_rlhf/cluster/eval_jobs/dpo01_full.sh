#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_full
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=11:45:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_full_%j.out
# FULL-SIZE suite, no item reduction: Greek IFEval 541, Greek MGSM 250, Global-MMLU-Lite 6 languages.
# Parent + 7 arms x 3 epochs = 22 models, four at a time, one per GPU.
#
# Model order is epoch 3 -> 2 -> 1, so that if the walltime or the budget cuts the run short we hold
# COMPLETE coverage of the most-trained checkpoints rather than a ragged partial across all epochs.
# Every model is resumable: a model with a results json is skipped on resubmit.
#
# Greek is absent from the cached Global-MMLU-Lite and is recorded as unmeasured, not substituted.
# MATH-500 and IFBench need a served vLLM endpoint and run as a separate job (dpo01_served.sh).
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
OUT=$ROUND/results/G4F6P1--DPO01/full
mkdir -p "$OUT"
PARENT=$ROUND/eval_copies/R4_full_ep1
[ -d "$PARENT" ] || { echo "FATAL: parent not found at $PARENT"; exit 1; }

TASKS=ifeval_greek,mgsm_greek,global_mmlu_en,global_mmlu_de,global_mmlu_es,global_mmlu_fr,global_mmlu_it,global_mmlu_pt

MODELS=("parent|$PARENT")
for ep in 3:129 2:86 1:43; do
  for arm in 00 01 02 03 04 05 06; do
    d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}
    [ -d "$d" ] && MODELS+=("arm${arm}_ep${ep%%:*}|$d")
  done
done
# follow-up arms. Seed replicates and the 4e-6 movement arm share the 43/86/129 step grid; the
# length-balanced arm has 274 pairs so its epochs land at 35/70/105; arm 07 runs to 5 epochs and
# only 4 and 5 are new (its 1-3 duplicate arm 05 by construction).
for arm in 05s43 01s43 08; do
  for ep in 3:129 2:86 1:43; do
    d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}
    [ -d "$d" ] && MODELS+=("arm${arm}_ep${ep%%:*}|$d")
  done
done
for ep in 3:105 2:70 1:35; do
  d=$ROUND/runs/G4F6P1--DPO01--BAL/checkpoint-${ep##*:}
  [ -d "$d" ] && MODELS+=("armBAL_ep${ep%%:*}|$d")
done
for ep in 5:215 4:172 3:129; do
  d=$ROUND/runs/G4F6P1--DPO01--07/checkpoint-${ep##*:}
  [ -d "$d" ] && MODELS+=("arm07_ep${ep%%:*}|$d")
done
# overnight replication set. Seed replicates are scored at EPOCH 3 ONLY - that is the comparison
# point, and scoring all three would treble the cost for no extra statistical power on the question
# "does alpha do anything". IPO is scored at every epoch because R-DPO5 requires movement to be read
# alongside the benchmarks (beta scales the gradient as well as the target).
for arm in 01s44 01s45 01s46 05s44 05s45 05s46; do
  d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-129
  [ -d "$d" ] && MODELS+=("arm${arm}_ep3|$d")
done
for arm in IPO42 IPO43; do
  for ep in 3:129 2:86 1:43; do
    d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}
    [ -d "$d" ] && MODELS+=("arm${arm}_ep${ep%%:*}|$d")
  done
done
for arm in BALs43 BALs44; do
  d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-105
  [ -d "$d" ] && MODELS+=("arm${arm}_ep3|$d")
done
echo "HB $(date -u +%FT%TZ) full suite start: ${#MODELS[@]} models, tasks=$TASKS"

run_one() {
  local label=${1%%|*} path=${1##*|} gpu=$2
  local dir="$OUT/$label"
  if find "$dir" -name 'results_*.json' 2>/dev/null | grep -q .; then echo "HB skip $label (has results)"; return 0; fi
  mkdir -p "$dir"
  local t0=$(date +%s)
  echo "HB $(date -u +%FT%TZ) start $label gpu=$gpu"
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    export PYTHONPATH=$WHEEL:$PYENV
    export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    export HF_HOME=$ROUND/hf_home HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
    export TOKENIZERS_PARALLELISM=false
    cd $ROUND
    python3 -m lm_eval --model hf \
      --model_args pretrained=$path,tokenizer=$PARENT,dtype=bfloat16 \
      --tasks $TASKS \
      --apply_chat_template \
      --include_path evals_code/ilsp/tasks \
      --batch_size 16 \
      --log_samples \
      --output_path $dir
  " > "$dir/run.log" 2>&1
  local rc=$? el=$(( $(date +%s) - t0 ))
  local got=$(find "$dir" -name 'results_*.json' 2>/dev/null | head -1)
  if [ -n "$got" ]; then
    echo "$(date -u +%FT%TZ) rc=$rc elapsed=${el}s" > "$dir/DONE"
    echo "HB $(date -u +%FT%TZ) done $label in ${el}s"
  else
    echo "HB $(date -u +%FT%TZ) FAILED $label rc=$rc in ${el}s"; tail -12 "$dir/run.log"
  fi
}

i=0
while [ $i -lt ${#MODELS[@]} ]; do
  pids=()
  for g in 0 1 2 3; do
    idx=$(( i + g )); [ $idx -ge ${#MODELS[@]} ] && break
    run_one "${MODELS[$idx]}" "$g" & pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done
  i=$(( i + 4 ))
  echo "HB $(date -u +%FT%TZ) wave complete, $i/${#MODELS[@]} dispatched"
done
echo "HB $(date -u +%FT%TZ) FULL_SUITE_DONE"
