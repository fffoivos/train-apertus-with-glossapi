#!/usr/bin/env bash
# Native-Greek suite (fp32, 21 shards over 4 GPU lanes, ~40 min) for one checkpoint, on its own workbench or a reused one.
# Usage: cluster/native_only.sh <ckpt_dir_on_cluster> <label>   [EVAL_JOB=<id> to reuse an open workbench]
set -u
CK_RAW=$1; LABEL=$2; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; EV=$R/evals/$LABEL; CK=$R/eval_copies/$LABEL
HERE="$(cd "$(dirname "$0")/.." && pwd)"; sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] native $LABEL: $*"; }
sshc "bash $R/make_eval_copy.sh $CK_RAW $CK" | tail -1
if [ -n "${EVAL_JOB:-}" ]; then J=$EVAL_JOB; else bash $HERE/cluster/preflight.sh 1.0 "native_$LABEL" | tail -1 | grep -q '^OK' || exit 1; J=$(sshc "bash $R/workbench.sh open nat_$LABEL normal 01:30:00" | tail -1); fi
[[ "$J" =~ ^[0-9]+$ ]] || { say "no workbench [$J]"; exit 1; }; say "workbench $J"
sshc "cd $R; mkdir -p $EV logs; nohup setsid bash -c \"MODEL=$CK LABEL=$LABEL srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=96 --export=ALL bash $R/eval_jobs/native.sh\" > $R/logs/${LABEL}_native.launch.log 2>&1 & echo launched"
for i in $(seq 1 80); do ok=$(sshc "n=0; for d in $EV/native/*; do [ -f \$d/metrics.csv ] && n=\$((n+1)); done; echo \$n"); [ "${ok:-0}" -ge 21 ] && break; grep -q "native done" <(sshc "tail -n 2 $R/logs/${LABEL}_native.launch.log") && break; sleep 60; done
say "shards complete: ${ok:-?}/21"; mkdir -p $HERE/results/$LABEL; scp -rq clariden:$EV/native $HERE/results/$LABEL/ 2>/dev/null
if [ -z "${EVAL_JOB:-}" ]; then sshc "bash $R/workbench.sh close $J" | tail -1; bash $HERE/cluster/ledger.sh $J "native_$LABEL" "native suite" | tail -1; fi
say DONE
