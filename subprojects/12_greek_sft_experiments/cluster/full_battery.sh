#!/usr/bin/env bash
# Full battery for one checkpoint (round two): native suite on its own 1:30 normal workbench (all 4 GPUs, fp32, ~40 min), then
# GreekMMLU (GPU 0, ~2.8 h, unshardable) + retention (GPU 1, ~1 h) on one 3:20 normal workbench. ~4.3 nh ≈ CHF 11.6.
# Usage: bash cluster/full_battery.sh <ckpt_dir_on_cluster> <label>      (Mac-orchestrated; preflight per workbench; closes each when done)
set -u
CK_RAW=$1; LABEL=$2; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; EV=$R/evals/$LABEL; CK=$R/eval_copies/$LABEL
HERE="$(cd "$(dirname "$0")/.." && pwd)"; sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] battery $LABEL: $*"; }
# 1. native suite (its own workbench, closed by native_only.sh's caller = us)
bash $HERE/cluster/native_only.sh $CK_RAW $LABEL; say "native_only exit $?"
# 2. GreekMMLU + retention on one workbench
bash $HERE/cluster/preflight.sh 3.3 "gmmlu_ret_$LABEL" | tail -1 | grep -q '^OK' || { say "preflight refused (cap)"; exit 1; }
J=$(sshc "bash $R/workbench.sh open gm_$LABEL normal 03:20:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "no workbench [$J]"; exit 1; }; say "workbench $J"
sshc "cd $R; mkdir -p $EV logs; nohup setsid bash -c \"MODEL=$CK LABEL=$LABEL GPU=0 srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL bash $R/eval_jobs/greekmmlu.sh\" > $R/logs/${LABEL}_greekmmlu.launch.log 2>&1 & echo launched greekmmlu"
sshc "cd $R; nohup setsid bash -c \"MODEL=$CK LABEL=$LABEL GPU=1 srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL bash $R/eval_jobs/retention.sh\" > $R/logs/${LABEL}_retention.launch.log 2>&1 & echo launched retention"
# wait for both (greekmmlu writes $EV/greekmmlu/*headline*.json via its finalizer; retention writes $EV/retention/**/results*.json)
for i in $(seq 1 190); do
  g=$(sshc "ls $EV/greekmmlu/*headline*.json 2>/dev/null | wc -l"); r=$(sshc "ls $EV/retention/*/results*.json $EV/retention/results*.json 2>/dev/null | wc -l")
  [ "${g:-0}" -ge 1 ] && [ "${r:-0}" -ge 1 ] && break
  idle=$(sshc "bash $R/workbench.sh idle $J" | tail -1); [ "${idle:-0}" -gt 900 ] 2>/dev/null && { say "GPU idle >15 min, closing"; break; }
  sleep 60
done
say "greekmmlu files: ${g:-0}, retention files: ${r:-0}"
sshc "bash $R/workbench.sh close $J" | tail -1; bash $HERE/cluster/ledger.sh $J "battery_$LABEL" "GreekMMLU + retention" | tail -1
mkdir -p $HERE/results/$LABEL; scp -rq clariden:$EV/greekmmlu clariden:$EV/retention $HERE/results/$LABEL/ 2>/dev/null; say DONE
