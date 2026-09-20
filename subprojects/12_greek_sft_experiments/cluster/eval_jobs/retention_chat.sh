#!/usr/bin/env bash
# Retention (cached suite) under lm_eval's chat-template mode (instruct-adapted protocol, plan §9c): --apply_chat_template --fewshot_as_multiturn.
# Usage: MODEL=<dir> LABEL=<run> GPU=0 bash retention_chat.sh   [TASKS=...]   → $OUT/retention_chat/
set -euo pipefail; source "$(dirname "$0")/common.sh"; GPU=${GPU:-0}; TASKS=${TASKS:-arc_challenge,arc_easy,hellaswag,winogrande,piqa,mmlu,global_mmlu,xnli,xcopa}
cache=$ROUND/cache/retention_chat_$LABEL; rm -rf "$cache"; mkdir -p "$cache"; cp -r "$RETENTION_CACHE_SRC"/. "$cache"/
hb "retention_chat start $LABEL gpu=$GPU tasks=$TASKS"
CUDA_VISIBLE_DEVICES=$GPU uenv run --view=default $UENV_IMAGE -- bash -c "
  set -euo pipefail
  export PYTHONPATH=$PYENV LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
  export HF_HOME=$cache/hf_home HF_DATASETS_CACHE=$cache/hf_datasets XDG_CACHE_HOME=$cache/xdg TMPDIR=$cache/tmp HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
  python3 '$LM_EVAL_REPAIR_SCRIPT' --target '$PYENV' || true
  python3 -m lm_eval --model hf --model_args pretrained=$MODEL,dtype=bfloat16,trust_remote_code=True --tasks $TASKS --batch_size auto --apply_chat_template --fewshot_as_multiturn --output_path $OUT/retention_chat/results.json --log_samples
"
hb "retention_chat done $LABEL"
