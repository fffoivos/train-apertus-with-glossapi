#!/usr/bin/env bash
# RESOURCES: nodes=1 gpus=4 walltime=02:00 mem=220GB

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <model_dir_or_hf_id> <run_name> [--revision R] [--mode chat|base] [--limit N] [--dry-run]" >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python_bin=${PYTHON:-/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python}
model=$1
run_name=$2
shift 2

exec "$python_bin" "$script_dir/run_greek_evals.py" \
  --model "$model" \
  --run-name "$run_name" \
  "$@"
