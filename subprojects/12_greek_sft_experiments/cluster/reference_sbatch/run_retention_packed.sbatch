#!/usr/bin/env bash
#SBATCH --job-name=full8_retention_packed
#SBATCH --account=a0140
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=08:00:00
#SBATCH --output=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.out
#SBATCH --error=/capstor/scratch/cscs/fffoivos/runs/eval/%x-%j.err
#
# Packed retention+Greek (Apertus Table-14 suite) eval of five full-8B CPT
# trajectory checkpoints, one lm-eval per GPU, adapted from the proven
# init_bakeoff/eval/run_eval.sbatch (V4 job 2335100 pattern; packed pattern
# per submit_bakeoff_checkpoint_eval_packed.sh). Experiment-side evaluation
# only: no canonical-runner paths are touched.
#
# GPU0: iter 0 (init), then iter 18284 (terminal) sequentially
# GPU1: iter 2384   GPU2: iter 9536 (peak)   GPU3: iter 14627 (cooldown start)

set -euo pipefail

EVAL_ROOT=/iopsstor/scratch/cscs/fffoivos/evals/full8_retention_20260819
STAGED=/capstor/scratch/cscs/fffoivos/releases/full8_trajectory_release_20260818/artifacts/model_private_branches_v1/staged
INIT_MODEL=/capstor/scratch/cscs/fffoivos/runs/07_full_8b_cpt/_preflight/20260808T023300Z-sanitized-v45/initial_hf_anchor/model

LM_EVAL_PYTHONPATH=/iopsstor/scratch/cscs/fffoivos/python_envs/lm_eval
LM_EVAL_REPAIR_SCRIPT=/iopsstor/scratch/cscs/fffoivos/repo/train-apertus-with-glossapi-cpt25b-a04c68a8/subprojects/05_token_distillation_cpt/03_training_experiments/scripts/repair_lm_eval_cli_install.py
UENV_IMAGE=pytorch/v2.9.1:v2
TASK_LIST="arc_challenge,arc_easy,hellaswag,winogrande,piqa,mmlu,global_mmlu,xnli,xcopa,arc_challenge_mt_el,xnli_el,xquad_el,belebele_ell_Grek,global_mmlu_full_el,include_base_44_greek_few_shot_en,global_piqa_completions_ell_grek"

run_one() {
    local gpu="$1" label="$2" model="$3"
    local out="$EVAL_ROOT/$label"
    local cache="$EVAL_ROOT/cache/${SLURM_JOB_ID}_${label}"
    mkdir -p "$out" "$cache"/{hf_home,hf_datasets,xdg,tmp}
    echo "[slot] gpu=$gpu label=$label model=$model start=$(date -u +%H:%M:%S)"
    CUDA_VISIBLE_DEVICES="$gpu" uenv run --view=default "$UENV_IMAGE" -- bash -c "
        set -euo pipefail
        export PYTHONPATH=$LM_EVAL_PYTHONPATH
        export LD_LIBRARY_PATH=$LM_EVAL_PYTHONPATH/scipy.libs:$LM_EVAL_PYTHONPATH/numpy.libs:$LM_EVAL_PYTHONPATH/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
        export HF_HOME=$cache/hf_home
        export HF_DATASETS_CACHE=$cache/hf_datasets
        export XDG_CACHE_HOME=$cache/xdg
        export TMPDIR=$cache/tmp
        python3 '$LM_EVAL_REPAIR_SCRIPT' --target '$LM_EVAL_PYTHONPATH' || true
        python3 -m lm_eval \
            --model hf \
            --model_args pretrained=$model,dtype=bfloat16,trust_remote_code=True \
            --tasks $TASK_LIST \
            --batch_size auto \
            --output_path $out/results.json \
            --log_samples
    " > "$out/slot.log" 2>&1
    echo "[slot] gpu=$gpu label=$label done=$(date -u +%H:%M:%S)"
}

mkdir -p "$EVAL_ROOT"
echo "=== full8_retention_packed job ${SLURM_JOB_ID:-manual} $(date -u) ==="

run_one 1 iter_0002384 "$STAGED/step2384-tokens10B" &
P1=$!
run_one 2 iter_0009536 "$STAGED/step9536-tokens40B" &
P2=$!
run_one 3 iter_0014627 "$STAGED/step14627-tokens61B" &
P3=$!
( run_one 0 iter_0000000 "$INIT_MODEL"
  run_one 0 iter_0018284 "$STAGED/main" ) &
P0=$!

FAIL=0
for p in $P0 $P1 $P2 $P3; do wait "$p" || FAIL=1; done
echo "=== all slots finished, fail=$FAIL $(date -u) ==="
exit $FAIL
