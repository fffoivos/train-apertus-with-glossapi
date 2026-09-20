#!/usr/bin/env bash
# Native Greek suite under the instruct-adapted protocol for up to four models on ONE normal workbench (one GPU each, fp32). Mac-orchestrated; per-launch copy.
# Usage: bash cluster/native_chat.sh <label>=<dir_on_cluster> [...]   → results/native_chat/<label>.json
if [ -z "${NC_COPY:-}" ]; then c=$(mktemp -t native_chat.XXXXXX.sh); cp "$0" "$c"; NC_COPY=1 exec bash "$c" "$@"; fi
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; HERE=$PWD; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/native_chat; mkdir -p $OUT
EX=$S/evals/full8_native_greek_peak_window_20260817/clean_assets_v5/clean_examples.jsonl
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] native_chat: $*"; }
scp -4 -q cluster/eval_jobs/native_chat.py cluster/eval_jobs/greekmmlu_official.py clariden:$R/eval_jobs/ || { say "upload failed"; exit 1; }
bash cluster/preflight.sh ${NH:-3.5} "native_chat" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
W=$(sshc "bash $R/workbench.sh open native_chat normal ${WALL:-03:30:00}" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "no workbench [$W]"; exit 1; }; say "workbench $W"
used=$(sshc "srun --jobid=$W --overlap --ntasks=1 --export=ALL nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits" | sort -n | tail -1); if [ "${used:-99999}" -gt 4000 ]; then say "dirty node (${used} MiB used): closing $W"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W native_chat_dirty "closed: dirty node" | tail -1; exit 2; fi; say "GPUs clean (max ${used} MiB)"
LABELS=""; i=0; for spec in "$@"; do L=${spec%%=*}; D=${spec#*=}; LABELS="$LABELS $L"
  sshc "cd $R; mkdir -p evals/native_chat; rm -f evals/native_chat/$L.json; nohup setsid bash -c \"CUDA_VISIBLE_DEVICES=$i srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'source $S/venvs/vllm/bin/activate; CUDA_VISIBLE_DEVICES=$i exec python $R/eval_jobs/native_chat.py --examples $EX --model $L=$D --output $R/evals/native_chat/$L.json'\" > $R/logs/native_chat_$L.log 2>&1 &"; i=$((i+1)); done
for k in $(seq 1 ${MINUTES:-205}); do n=0; for L in $LABELS; do sshc "test -s $R/evals/native_chat/$L.json" && n=$((n+1)); done; [ "$n" -ge $# ] && break; sleep 60; done
say "$n of $# result files after $k min"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W native_chat "native suite, instruct-adapted protocol: $*" | tail -1
for L in $LABELS; do scp -4 -q clariden:$R/evals/native_chat/$L.json $OUT/ 2>/dev/null; f=$OUT/$L.json; [ -s $f ] && python3 -c "import json; d=json.load(open('$f')); print(d['model_label'], d['items'], d['accuracy_by_benchmark'], 'macro', d['macro'])"; done
