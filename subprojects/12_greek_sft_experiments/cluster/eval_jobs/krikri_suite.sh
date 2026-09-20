#!/usr/bin/env bash
# Krikri base-card Greek suite (ARC-Challenge-el 25-shot, HellaSwag-el 10-shot, TruthfulQA-MC2-el 0-shot, Medical MCQA 15-shot, Belebele-el 5-shot, translated MMLU-el 5-shot)
# under PROTO=base (card protocol, plain few-shot prompts) or PROTO=chat (instruct-adapted: --apply_chat_template --fewshot_as_multiturn).
# Usage: MODEL=<dir> LABEL=<run> GPU=0 PROTO=base|chat bash krikri_suite.sh   → $OUT/krikri_suite_$PROTO/
set -euo pipefail; source "$(dirname "$0")/common.sh"; GPU=${GPU:-0}; PROTO=${PROTO:-base}
TASKS=${TASKS:-arc_challenge_el,hellaswag_el,truthfulqa_mc2_el,medical_mcqa_el,belebele_el_5shot,mmlu_el_all}
INC=$ROUND/evals_code/krikri_suite/tasks; FLAGS=""; [ "$PROTO" = chat ] && FLAGS="--apply_chat_template --fewshot_as_multiturn"
cache=$ROUND/cache/krikri_${PROTO}_$LABEL; rm -rf "$cache"; mkdir -p "$cache"; cp -r "$RETENTION_CACHE_SRC"/. "$cache"/
hb "krikri_suite start $LABEL proto=$PROTO gpu=$GPU"
CUDA_VISIBLE_DEVICES=$GPU uenv run --view=default $UENV_IMAGE -- bash -c "
  set -euo pipefail
  export PYTHONPATH=$PYENV LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
  export HF_HOME=$cache/hf_home HF_DATASETS_CACHE=$cache/hf_datasets XDG_CACHE_HOME=$cache/xdg TMPDIR=$cache/tmp HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
  python3 '$LM_EVAL_REPAIR_SCRIPT' --target '$PYENV' || true
  python3 -m lm_eval --model hf --model_args pretrained=$MODEL,dtype=bfloat16,trust_remote_code=True --tasks $TASKS --include_path $INC --batch_size auto $FLAGS --output_path $OUT/krikri_suite_$PROTO/results.json --log_samples
"
hb "krikri_suite done $LABEL proto=$PROTO"
