#!/usr/bin/env bash
# RESOURCES: nodes=1 gpus=4 walltime=02:00 mem=480GB
set -euo pipefail

usage() {
  echo "Usage: $0 <model_dir> <run_name> [--limit N] [--max-steps N] [--dry-run] [--vllm] [--mgsm-4shot]" >&2
}

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

model_dir=$1
run_name=$2
shift 2

limit=""
dry_run=0
use_vllm=0
use_mgsm_4shot=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit|--max-steps)
      if [[ $# -lt 2 || ! $2 =~ ^[1-9][0-9]*$ ]]; then
        echo "ERROR: $1 requires a positive integer" >&2
        exit 2
      fi
      limit=$2
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --vllm)
      use_vllm=1
      shift
      ;;
    --mgsm-4shot)
      use_mgsm_4shot=1
      shift
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! $run_name =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "ERROR: run_name must contain only letters, digits, dot, underscore, or hyphen" >&2
  exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/../.." && pwd)
cd "$repo_root"

backend=hf
model_args="pretrained=${model_dir},dtype=bfloat16"
if [[ $use_vllm -eq 1 ]]; then
  backend=vllm
  model_args="${model_args},tensor_parallel_size=4"
fi

mgsm_task=mgsm_greek
if [[ $use_mgsm_4shot -eq 1 ]]; then
  mgsm_task=mgsm_greek_4shot
fi
tasks="ifeval_greek,${mgsm_task}"
raw_dir="results/${run_name}/ilsp/"
summary_path="results/${run_name}/ilsp.json"

command=(
  lm_eval
  --model "$backend"
  --model_args "$model_args"
  --tasks "$tasks"
  --apply_chat_template
  --include_path evals/ilsp/tasks
  --output_path "$raw_dir"
)
if [[ -n $limit ]]; then
  command+=(--limit "$limit")
fi

printf 'Resolved model: %s\n' "$model_dir"
printf 'Resolved tasks: %s\n' "$tasks"
printf 'Dataset splits: ilsp/ifeval_greek:train=541; ilsp/mgsm_greek:test=250\n'
printf 'Output summary: %s\n' "$summary_path"
printf 'Command:'
printf ' %q' "${command[@]}"
printf '\n'

if [[ $dry_run -eq 1 ]]; then
  exit 0
fi

if [[ ! -d $model_dir ]]; then
  echo "ERROR: model_dir is not a directory: $model_dir" >&2
  exit 1
fi
if ! command -v lm_eval >/dev/null 2>&1; then
  echo "ERROR: lm_eval is not on PATH" >&2
  exit 1
fi

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
mkdir -p "$raw_dir"

ILSP_MODEL_DIR=$model_dir "${PYTHON:-python3}" - <<'PY'
import os

from datasets import load_dataset
from transformers import AutoTokenizer

model_dir = os.environ["ILSP_MODEL_DIR"]
tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
if not tokenizer.chat_template:
    raise SystemExit("ERROR: tokenizer has no chat_template")

expected = (("ilsp/ifeval_greek", "train", 541), ("ilsp/mgsm_greek", "test", 250))
for dataset_name, split, expected_rows in expected:
    rows = len(load_dataset(dataset_name, split=split))
    if rows != expected_rows:
        raise SystemExit(
            f"ERROR: {dataset_name}:{split} has {rows} rows; expected {expected_rows}"
        )
print("Preflight OK: tokenizer chat template and cached dataset row counts")
PY

heartbeat() {
  while true; do
    sleep 60
    echo "HB step=0 loss=na tok/s=na mem=na"
  done
}
heartbeat &
heartbeat_pid=$!
cleanup_heartbeat() {
  kill "$heartbeat_pid" >/dev/null 2>&1 || true
  wait "$heartbeat_pid" 2>/dev/null || true
}
trap cleanup_heartbeat EXIT

"${command[@]}"
cleanup_heartbeat
trap - EXIT

ILSP_RAW_DIR=$raw_dir ILSP_SUMMARY_PATH=$summary_path "${PYTHON:-python3}" - <<'PY'
import json
import os
from pathlib import Path

raw_dir = Path(os.environ["ILSP_RAW_DIR"])
summary_path = Path(os.environ["ILSP_SUMMARY_PATH"])
candidates = []
for path in raw_dir.rglob("*.json"):
    if "samples_" in path.name:
        continue
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        continue
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        candidates.append((path.stat().st_mtime_ns, path, payload))
if not candidates:
    raise SystemExit("ERROR: lm_eval produced no result JSON under " + str(raw_dir))

_, source_path, result_payload = max(candidates, key=lambda item: item[0])
results = result_payload["results"]

def metric(task, name):
    task_results = results.get(task)
    if not isinstance(task_results, dict):
        raise SystemExit(f"ERROR: result JSON has no task {task!r}")
    for key, value in task_results.items():
        if key == name or key.startswith(name + ","):
            return value
    raise SystemExit(f"ERROR: result JSON has no metric {task}.{name}")

mgsm_task = "mgsm_greek_4shot" if "mgsm_greek_4shot" in results else "mgsm_greek"
summary = {
    "ifeval_greek": {
        name: metric("ifeval_greek", name)
        for name in (
            "prompt_level_strict_acc",
            "inst_level_strict_acc",
            "prompt_level_loose_acc",
            "inst_level_loose_acc",
        )
    },
    mgsm_task: {"exact_match": metric(mgsm_task, "exact_match")},
    "source": str(source_path),
}
temporary = summary_path.with_suffix(summary_path.suffix + ".tmp")
temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
temporary.replace(summary_path)
print(f"Wrote {summary_path}")
PY
