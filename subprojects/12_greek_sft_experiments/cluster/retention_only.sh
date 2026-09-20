#!/usr/bin/env bash
# Retention on the cached suite for ONE model dir (e.g. the Apertus-Instruct snapshot) on a 1:30 normal workbench; mirrors full_battery.sh's retention lane.
# Usage: bash cluster/retention_only.sh <model_dir_on_cluster> <label>   → results/<label>/retention/
CK=$1; LABEL=$2; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; EV=$R/evals/$LABEL; HERE="$(cd "$(dirname "$0")/.." && pwd)"
sshc() { ssh -4 -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] retention $LABEL: $*"; }
bash $HERE/cluster/preflight.sh 1.5 "ret_$LABEL" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
J=$(sshc "bash $R/workbench.sh open ret_$LABEL normal 01:30:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "no workbench [$J]"; exit 1; }; say "workbench $J"
sshc "cd $R; mkdir -p $EV logs; nohup setsid bash -c \"MODEL=$CK LABEL=$LABEL GPU=0 srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL bash $R/eval_jobs/retention.sh\" > $R/logs/${LABEL}_retention.log 2>&1 &"
for i in $(seq 1 85); do r=$(sshc "ls $EV/retention/*/results*.json $EV/retention/results*.json 2>/dev/null | wc -l"); [ "${r:-0}" -ge 1 ] && break; sleep 60; done
say "retention files: ${r:-0} after $i min"; sshc "bash $R/workbench.sh close $J" | tail -1; bash $HERE/cluster/ledger.sh $J "retention_$LABEL" "retention (cached suite) for $LABEL" | tail -1
mkdir -p $HERE/results/$LABEL; scp -rq clariden:$EV/retention $HERE/results/$LABEL/ 2>/dev/null; say DONE
