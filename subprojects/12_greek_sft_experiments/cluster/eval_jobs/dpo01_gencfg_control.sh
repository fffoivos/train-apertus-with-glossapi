#!/bin/bash
# R-DPO5 / fork finding: transformers 5.16.1 re-serialised the checkpoints, so the parent and the
# arms differ in generation-relevant config (eos_token_id 2 vs 68, pad absent vs 3, use_cache true vs
# false). It is identical across arms so it cannot explain any arm-vs-arm result, but it IS a
# parent-vs-arm difference sitting exactly on the stopping axis that is damaged (startend, length).
# This scores the PARENT's weights under a CHECKPOINT's generation_config, isolating the effect for
# the price of one model. If parent_ckptcfg == parent, the confound is empty.
# ---------------------------------------------------------------------------------------------
# RETIRED 2026-09-19. R-DPO7b, R-DPO7b2 and R-DPO8 each traced fail-open paths through this script
# (success on a failed model, tokenizer checks that could be skipped, stage cleanup that could
# cross jobs). It is kept as the record of how the published numbers were produced and must not
# be run again: superseded by cluster/eval_jobs/dpo01_frozen_rescore.sh, which freezes the prompt date, stages per job and fails closed.
echo "RETIRED: $(basename "$0") - see the header"; exit 64
# ---------------------------------------------------------------------------------------------
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
OUT=$ROUND/results/G4F6P1--DPO01/full/parent_ckptcfg
PARENT=$ROUND/eval_copies/R4_full_ep1
SRC=$ROUND/runs/G4F6P1--DPO01--01/checkpoint-129
STAGE=$ROUND/eval_copies/${SLURM_JOB_ID:-$$}_R4_full_ep1_ckptcfg

if find "$OUT" -name 'results_*.json' 2>/dev/null | grep -q .; then echo "gencfg control already scored"; exit 0; fi
# a copy of the PARENT's weights with the CHECKPOINT's generation config; weights untouched
rm -rf "$STAGE"; mkdir -p "$STAGE"
for f in "$PARENT"/*; do ln -s "$f" "$STAGE/$(basename $f)" 2>/dev/null; done
# R-DPO7b2 [HIGH]: never write through a symlink into a real checkpoint or the parent.
for t in config.json generation_config.json; do
  [ -e "$STAGE/$t" ] && [ -L "$STAGE/$t" ] && rm -f "$STAGE/$t"
done
rm -f "$STAGE/generation_config.json" "$STAGE/config.json"
cp "$PARENT/config.json" "$STAGE/config.json"
python3 - "$SRC" "$STAGE" <<'PY'
import json, sys, os
src, stage = sys.argv[1], sys.argv[2]
for name in ("generation_config.json",):
    p = os.path.join(src, name)
    if os.path.exists(p):
        json.dump(json.load(open(p)), open(os.path.join(stage, name), "w"), indent=1)
        print("  took", name, "from the checkpoint")
# and the checkpoint's eos/pad into config.json, leaving every weight-bearing field alone
c = json.load(open(os.path.join(stage, "config.json")))
k = json.load(open(os.path.join(src, "config.json")))
# R-DPO7b [MEDIUM]: this direction only ASSIGNED. A field the checkpoint lacks but the parent has was
# silently retained from the parent, so the cell was not truly "under the checkpoint config" and the
# isolated confound would be understated. Mirror dpo01_armcfg_cell.sh exactly: assign what the source
# has, delete what it lacks.
for f in ("eos_token_id", "pad_token_id", "bos_token_id", "use_cache"):
    if f in k:
        print(f"  config.{f}: {c.get(f)} -> {k[f]}")
        c[f] = k[f]
    elif f in c:
        print(f"  config.{f}: {c.get(f)} -> <deleted, absent from the checkpoint>")
        del c[f]
json.dump(c, open(os.path.join(stage, "config.json"), "w"), indent=1)
PY
mkdir -p "$OUT"
CUDA_VISIBLE_DEVICES=0 uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
  set -euo pipefail
  export PYTHONPATH=$WHEEL:$PYENV
  export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
  export HF_HOME=$ROUND/hf_home HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
  cd $ROUND
  python3 -m lm_eval --model hf \
    --model_args pretrained=$STAGE,tokenizer=$PARENT,dtype=bfloat16 \
    --tasks ifeval_greek,mgsm_greek --apply_chat_template \
    --include_path evals_code/ilsp/tasks --batch_size 16 --log_samples --output_path $OUT
" > "$OUT/run.log" 2>&1
echo "gencfg control rc=$? -> $(find $OUT -name 'results_*.json' | wc -l) result file(s)"
