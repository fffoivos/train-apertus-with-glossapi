#!/usr/bin/env bash
# Retention under the chat-template mode for up to four models on ONE normal workbench (one GPU each). Per-launch copy. Usage: bash cluster/retention_chat_run.sh <label>=<dir> [...]
if [ -z "${RC_COPY:-}" ]; then c=$(mktemp -t retention_chat.XXXXXX.sh); cp "$0" "$c"; RC_COPY=1 exec bash "$c" "$@"; fi
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; HERE=$PWD; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] retention_chat: $*"; }
scp -4 -q cluster/eval_jobs/retention_chat.sh clariden:$R/eval_jobs/retention_chat.sh || { say "upload failed"; exit 1; }
bash cluster/preflight.sh 1.5 "retention_chat" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
W=$(sshc "bash $R/workbench.sh open ret_chat normal 01:30:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "no workbench [$W]"; exit 1; }; say "workbench $W"
used=$(sshc "srun --jobid=$W --overlap --ntasks=1 --export=ALL nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits" | sort -n | tail -1); if [ "${used:-99999}" -gt 4000 ]; then say "dirty node (${used} MiB): closing $W"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W retention_chat_dirty "closed: dirty node" | tail -1; exit 2; fi; say "GPUs clean (max ${used} MiB)"
LABELS=""; i=0; for spec in "$@"; do L=${spec%%=*}; D=${spec#*=}; LABELS="$LABELS $L"
  sshc "cd $R; mkdir -p evals/$L logs; nohup setsid bash -c \"MODEL=$D LABEL=$L GPU=$i srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL bash $R/eval_jobs/retention_chat.sh\" > $R/logs/${L}_retention_chat.log 2>&1 &"; i=$((i+1)); done
for k in $(seq 1 85); do n=0; for L in $LABELS; do sshc "ls $R/evals/$L/retention_chat/*/results*.json $R/evals/$L/retention_chat/results*.json 2>/dev/null | grep -q ." && n=$((n+1)); done; [ "$n" -ge $# ] && break; sleep 60; done
say "$n of $# result sets after $k min"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W retention_chat "retention chat-template mode: $*" | tail -1
for L in $LABELS; do mkdir -p results/$L; scp -rq clariden:$R/evals/$L/retention_chat results/$L/ 2>/dev/null; f=$(ls results/$L/retention_chat/*/results*.json results/$L/retention_chat/results*.json 2>/dev/null | head -1); [ -n "$f" ] && python3 -c "
import json; d=json.load(open('$f')); r=d.get('results',{}); print('$L', {k: round(v.get('acc_norm,none', v.get('acc,none', 0)), 4) for k,v in r.items()})"; [ -n "$f" ] || { echo "$L: no results; tail:"; sshc "tail -3 $R/logs/${L}_retention_chat.log" | cut -c1-200; }; done
