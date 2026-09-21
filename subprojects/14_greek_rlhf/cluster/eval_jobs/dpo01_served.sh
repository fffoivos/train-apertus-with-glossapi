#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_served
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=11:45:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_served_%j.out
# MATH-500 (500 el + 500 en) and Greek IFBench (300) at FULL size, for the parent and every arm
# checkpoint. These lanes need generation against an OpenAI-compatible endpoint, so each model is
# served by vLLM from its OWN venv as a separate process and driven over HTTP by
# data/benchmarks_el/generate.py. Nothing here imports vllm into the eval environment: that install
# cannot load it (missing ray, aiohttp shadowed, sourceless .pyc modules), and the HTTP boundary is
# precisely what avoids the problem.
#
# Four models at a time, one GPU and one port each, tensor-parallel 1.
# Resumable: a model whose scores exist is skipped; generate.py itself skips ids already written.
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
BE=$ROUND/data/benchmarks_el
OUT=$ROUND/results/G4F6P1--DPO01/served
mkdir -p "$OUT"
PARENT=$ROUND/eval_copies/R4_full_ep1
[ -d "$PARENT" ] || { echo "FATAL: parent missing"; exit 1; }

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
echo "HB $(date -u +%FT%TZ) served lanes start: ${#MODELS[@]} models (math500 el+en, ifbench el)"

serve_and_score() {
  local label=${1%%|*} path=${1##*|} gpu=$2
  local dir="$OUT/$label" port=$(( 8000 + gpu ))
  if [ -s "$dir/math500_el_score.json" ] && [ -s "$dir/ifbench_el_score.jsonl" ]; then
    echo "HB skip $label (scored)"; return 0
  fi
  mkdir -p "$dir"
  local t0=$(date +%s)
  echo "HB $(date -u +%FT%TZ) serve $label gpu=$gpu port=$port"
  # the tokenizer is the parent's for every model: transformers 5.16 wrote TokenizersBackend into the
  # checkpoints and the chat template is identical once the training-only {% generation %} markers are
  # stripped, so this changes no prompt and keeps one protocol across all models.
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    source $S/venvs/vllm/bin/activate
    export HF_HOME=$ROUND/hf_home HF_HUB_OFFLINE=1
    exec python3 -m vllm.entrypoints.openai.api_server \
      --model $path --tokenizer $PARENT --served-model-name $label \
      --port $port --tensor-parallel-size 1 --max-model-len 4096 \
      --gpu-memory-utilization 0.85 --no-enable-log-requests
  " > "$dir/server.log" 2>&1 &
  local srv=$!
  echo "$srv" >> "$PIDFILE"
  # wait for readiness, but give up rather than hang the whole wave
  # $srv is the PID of the `uenv run` wrapper, NOT the server: when the wrapper's process tree
  # shifts, kill -0 reports death while the server is still coming up. So a liveness failure only
  # ARMS a countdown - three further health probes must also fail before we give up. Without the
  # countdown this produced a false "died early" on a healthy model; without the liveness check at
  # all, a genuinely bad invocation would burn the full 15-minute timeout on every model.
  local ok=0 grace=0
  for i in $(seq 1 180); do
    if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then ok=1; break; fi
    if ! kill -0 $srv 2>/dev/null; then
      grace=$(( grace + 1 ))
      [ $grace -ge 3 ] && { echo "HB $label server gone (3 consecutive probes after PID vanished)"; break; }
    else
      grace=0
    fi
    sleep 5
  done
  if [ $ok -ne 1 ]; then
    echo "HB $(date -u +%FT%TZ) FAILED $label: server never became ready"; tail -15 "$dir/server.log"
    kill $srv 2>/dev/null; wait $srv 2>/dev/null; return 1
  fi
  echo "HB $(date -u +%FT%TZ) serving $label after $(( $(date +%s) - t0 ))s, generating"
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    cd $ROUND
    python3 $BE/generate.py http://127.0.0.1:$port/v1 $label $dir --sets math500 --langs el,en --workers 16
    python3 $BE/generate.py http://127.0.0.1:$port/v1 $label $dir --sets ifbench --langs el   --workers 16
  " >> "$dir/gen.log" 2>&1
  # the server is only needed for generation; free the GPU before scoring
  kill $srv 2>/dev/null; wait $srv 2>/dev/null
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    export PYTHONPATH=$S/python_envs/lm_eval
    export LD_LIBRARY_PATH=$S/python_envs/lm_eval/scipy.libs:$S/python_envs/lm_eval/numpy.libs:$S/python_envs/lm_eval/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    cd $ROUND
    python3 $BE/math500/score_math500.py $dir/math500_el.jsonl $dir/math500_el_score.json
    python3 $BE/math500/score_math500.py $dir/math500_en.jsonl $dir/math500_en_score.json
    python3 $BE/ifbench/score.py         $dir/ifbench_el.jsonl $dir/ifbench_el_score.jsonl
  " >> "$dir/score.log" 2>&1
  echo "HB $(date -u +%FT%TZ) done $label in $(( $(date +%s) - t0 ))s"
}

# Never leave a server holding a GPU if the job is cancelled or times out.
# Kill by recorded PID only - never pkill -f, which can match unrelated processes on a shared node.
PIDFILE=$OUT/.server_pids
: > "$PIDFILE"
reap() {  # kill any server still holding a GPU; does NOT change the exit status
  [ -s "$PIDFILE" ] || return 0
  echo "HB reap: killing servers recorded in $PIDFILE"
  while read -r pid; do [ -n "$pid" ] && kill "$pid" 2>/dev/null; done < "$PIDFILE"
}
trap 'reap; exit 1' TERM INT
trap reap EXIT

i=0
while [ $i -lt ${#MODELS[@]} ]; do
  pids=()
  for g in 0 1 2 3; do
    idx=$(( i + g )); [ $idx -ge ${#MODELS[@]} ] && break
    serve_and_score "${MODELS[$idx]}" "$g" & pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done
  i=$(( i + 4 ))
  echo "HB $(date -u +%FT%TZ) wave complete, $i/${#MODELS[@]} dispatched"
done
echo "HB $(date -u +%FT%TZ) SERVED_LANES_DONE"
