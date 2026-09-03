#!/usr/bin/env bash
# GreekMMLU, the CPT card's frozen FP32 candidate-likelihood evaluator + clean-subset finalizer.
# Usage: MODEL=<dir> LABEL=<run> GPU=0 bash greekmmlu.sh   (inside a workbench: srun --jobid $J --overlap ...)
set -euo pipefail; source "$(dirname "$0")/common.sh"; GPU=${GPU:-0}
hb "greekmmlu start $LABEL gpu=$GPU"
mkdir -p "$OUT/greekmmlu"
CUDA_VISIBLE_DEVICES=$GPU uenv run --view=default $UENV_IMAGE -- bash -c "
  set -euo pipefail
  export PYTHONPATH=$WHEEL:$PYENV
  export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
  export HF_TOKEN=\$(cat /users/fffoivos/.cache/huggingface/token) HF_HUB_OFFLINE=1
  python3 '$NATIVE_ROOT/run_native_greek_mcq_eval.py' --registry '$NATIVE_ROOT/native_greek_benchmark_registry.json' \
    --benchmarks greekmmlu --model '$LABEL=$MODEL' --output-dir '$OUT/greekmmlu' --sample-size 0 \
    --random-state 42 --dtype float32 --max-input-tokens 3072 --candidate-batch-size 16 --example-batch-size 16 --trust-remote-code
  python3 '$FINALIZER' --model '$MODEL' --evaluation-root '$OUT/greekmmlu' --model-label '$LABEL' \
    --clean-subset-manifest '$CLEAN_SUBSET' --output '$OUT/greekmmlu_receipt.json'
" > "$OUT/logs/greekmmlu.log" 2>&1
hb "greekmmlu done $LABEL"; python3 -c "import json;d=json.load(open('$OUT/greekmmlu_receipt.json'));print('GREEKMMLU', {k:d[k] for k in d if 'acc' in k.lower()})" 2>/dev/null || tail -3 "$OUT/logs/greekmmlu.log"
