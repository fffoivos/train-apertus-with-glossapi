#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_cell
#SBATCH --nodes=1 --ntasks-per-node=1 --gpus-per-node=4 --cpus-per-task=288 --mem=640G
#SBATCH --time=02:00:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_cell_%j.out
# R-DPO6 HIGH: the config 2x2 was incomplete. We had parent@own-config, parent@ckpt-config and
# arm@ckpt-config, but never arm@PARENT-config - so "the arms beat a fairly-compared parent" rested
# on correcting the parent rather than on measuring the arms under the parent's serving config.
# This fills the missing cell: an arm's WEIGHTS under the PARENT's generation config.
# ---------------------------------------------------------------------------------------------
# RETIRED 2026-09-19. R-DPO7b, R-DPO7b2 and R-DPO8 each traced fail-open paths through this script
# (success on a failed model, tokenizer checks that could be skipped, stage cleanup that could
# cross jobs). It is kept as the record of how the published numbers were produced and must not
# be run again: superseded by cluster/eval_jobs/dpo01_frozen_rescore.sh (config=parent), which freezes the prompt date, stages per job and fails closed.
echo "RETIRED: $(basename "$0") - see the header"; exit 64
# ---------------------------------------------------------------------------------------------
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos; ROUND=$S/sft_round1
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
PARENT=$ROUND/eval_copies/R4_full_ep1
for ARM in arm05_ep3 arm01_ep3; do
  case $ARM in arm05_ep3) SRC=$ROUND/runs/G4F6P1--DPO01--05/checkpoint-129;; arm01_ep3) SRC=$ROUND/runs/G4F6P1--DPO01--01/checkpoint-129;; esac
  OUT=$ROUND/results/G4F6P1--DPO01/full/${ARM}_parentcfg
  if find "$OUT" -name 'results_*.json' 2>/dev/null | grep -q .; then echo "skip $ARM"; continue; fi
  # R-DPO7b [HIGH]: a fixed shared stage path lets a duplicate invocation re-create the config
  # symlink between our rm and our open, so the write lands on $SRC/config.json and TRUNCATES A
  # REAL CHECKPOINT. Make the stage unique per job and assert the target is a regular file.
  STAGE=$ROUND/eval_copies/stage_${SLURM_JOB_ID:-$$}_${ARM}_parentcfg
  rm -rf "$STAGE"; mkdir -p "$STAGE"
  for f in "$SRC"/*; do ln -sf "$f" "$STAGE/$(basename "$f")" 2>/dev/null; done
  # the ARM's weights, the PARENT's generation config and tokenizer
  rm -f "$STAGE/generation_config.json" "$STAGE/config.json" "$STAGE/tokenizer_config.json" "$STAGE/tokenizer.json" "$STAGE/special_tokens_map.json"
  for t in generation_config.json tokenizer_config.json tokenizer.json special_tokens_map.json; do
    [ -f "$PARENT/$t" ] && cp "$PARENT/$t" "$STAGE/$t"
  done
  for t in generation_config.json config.json tokenizer.json; do
    [ -e "$STAGE/$t" ] && [ -L "$STAGE/$t" ] && { echo "FATAL $t is still a symlink; refusing to write through it"; exit 1; }
  done
  python3 - "$SRC" "$PARENT" "$STAGE" <<'PY' || { echo "FATAL config overlay failed for $ARM"; exit 1; }
import json, sys, os
src, par, stage = sys.argv[1:4]
c = json.load(open(os.path.join(src, "config.json")))          # arm's architecture
p = json.load(open(os.path.join(par, "config.json")))          # parent's serving fields
# R-DPO7b [MEDIUM]: SYMMETRIC overlay -- take the field when the source has it, and DELETE it when
# the source does not. The mirror script (dpo01_gencfg_control.sh) only assigned, so a field the
# checkpoint lacked was silently retained from the parent and that cell was not truly "under the
# checkpoint config". Both directions now use this same rule.
FIELDS = ("eos_token_id", "pad_token_id", "bos_token_id", "use_cache")
for f in FIELDS:
    if f in p: c[f] = p[f]
    elif f in c: del c[f]
tgt = os.path.join(stage, "config.json")
assert not os.path.islink(tgt), "refusing to write through a symlink: " + tgt
json.dump(c, open(tgt, "w"), indent=1)
print("  staged", stage, "overlay:", {f: c.get(f, "<deleted>") for f in FIELDS})
PY
  mkdir -p "$OUT"
  echo "=== $ARM under the PARENT's generation config $(date -u +%FT%TZ) ==="
  CUDA_VISIBLE_DEVICES=0 uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    export PYTHONPATH=$WHEEL:$PYENV
    export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    export HF_HOME=$ROUND/hf_home HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
    cd $ROUND
    python3 -m lm_eval --model hf --model_args pretrained=$STAGE,tokenizer=$PARENT,dtype=bfloat16 \
      --tasks ifeval_greek,mgsm_greek --apply_chat_template --include_path evals_code/ilsp/tasks \
      --batch_size 16 --log_samples --output_path $OUT
  " > "$OUT/run.log" 2>&1
  echo "  -> $(find $OUT -name 'results_*.json' | wc -l) result file(s)"
done
echo "CELL_DONE $(date -u +%FT%TZ)"
