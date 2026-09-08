#!/usr/bin/env bash
# Serve up to four chat models with vLLM on one Clariden node (one model per GPU, OpenAI-compatible, ports 8000–8003), for the picky-user
# benchmark and math M3. Run INSIDE an allocation (workbench/salloc) or via sbatch; prints the node name so the Mac can open a tunnel:
#   ssh -N -L 8000:<node>:8000 -L 8001:<node>:8001 -L 8002:<node>:8002 -L 8003:<node>:8003 clariden
# Usage: bash serve_models.sh NAME=PATH [NAME=PATH ...]     (PATH = local dir or HF id present in the offline cache)
set -u
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; export HF_HOME=$R/hf_home HF_HUB_OFFLINE=1
source /iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/activate
echo "NODE $(hostname)"; i=0; pids=()
for spec in "$@"; do
  name=${spec%%=*}; path=${spec#*=}; port=$((8000 + i))
  CUDA_VISIBLE_DEVICES=$i vllm serve "$path" --served-model-name "$name" --port "$port" --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.85 > "$R/serve_${name}.log" 2>&1 &
  pids+=($!); echo "$name → :$port (GPU $i, pid ${pids[-1]})"; i=$((i + 1))
done
for p in "${pids[@]}"; do wait "$p"; done
