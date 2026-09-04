#!/usr/bin/env bash
# Launch one arm on a normal workbench when a slot frees (open retried); writes results/.<run>_job. Evals are someone else's job.
# Usage: cluster/launch_arm.sh <run_label> <config.yaml> <wb_label>
set -u
RUN=$1; CFG=$2; WB=$3; HERE="$(cd "$(dirname "$0")/.." && pwd)"; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1
sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] $RUN: $*"; }
J=""
for attempt in $(seq 1 40); do
  n=$(sshc "squeue -u fffoivos -h -p normal -o %T" | grep -c -E 'RUNNING|PENDING'); [ "${n:-9}" -ge 4 ] && { sleep 120; continue; }
  bash $HERE/cluster/preflight.sh 1.5 $RUN | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
  J=$(sshc "bash $R/workbench.sh open $WB normal 01:30:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] && break
  say "open failed [$J] (attempt $attempt)"; sleep 180
done
[[ "$J" =~ ^[0-9]+$ ]] || { say "no workbench"; exit 1; }
sshc "bash $R/train_launch.sh $J cluster/configs/$CFG $RUN" | tail -1; echo "$J" > $HERE/results/.${RUN}_job
printf "| $(date '+%Y-%m-%d %H:%M') | $RUN | job $J | claude | launched (lr 1e-5, 2 ep, cosine) on normal | 1.5/— | — |\n" >> $HERE/EXECUTION_LOG.md
cd $HERE && git add EXECUTION_LOG.md && git commit -q -m "ledger: $RUN launched" >/dev/null; say "workbench $J launched"
