#!/usr/bin/env bash
# Train one arm on a normal workbench when a slot frees, then dev losses + light evals of its epoch2 on the leftover, close, ledger.
# Usage: cluster/run_and_eval.sh <run_label> <config.yaml> [wb_label]
set -u
RUN=$1; CFG=$2; WB=${3:-$RUN}; HERE="$(cd "$(dirname "$0")/.." && pwd)"; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1
sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] $RUN: $*"; }
for i in $(seq 1 60); do n=$(sshc "squeue -u fffoivos -h -p normal -o %T" | grep -c -E 'RUNNING|PENDING'); [ "${n:-9}" -lt 4 ] && break; sleep 120; done
bash $HERE/cluster/preflight.sh 1.5 $RUN | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
J=""; for i in 1 2 3 4 5; do J=$(sshc "bash $R/workbench.sh open $WB normal 01:30:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] && break; say "open failed [$J], retry $i"; sleep 240; done
[[ "$J" =~ ^[0-9]+$ ]] || { say "no workbench"; exit 1; }
say "workbench $J"; echo "$J" > $HERE/results/.${RUN}_job
sshc "bash $R/train_launch.sh $J cluster/configs/$CFG $RUN"; printf "| $(date '+%Y-%m-%d %H:%M') | $RUN | job $J | claude | launched (lr 1e-5, 2 ep, cosine) on normal | 1.5/— | — |\n" >> $HERE/EXECUTION_LOG.md
until sshc "grep -q RUN_EXIT $R/runs/$RUN.ctl/train.log && echo yes" | grep -q yes; do sleep 90; done; say "exited"
mkdir -p $HERE/results/$RUN $HERE/results/${RUN}_ep2
sshc "grep -o \"{'eval_[a-z_0-9]*_loss': '[0-9.]*'[^}]*'epoch': '[0-9.]*'\" $R/runs/$RUN.ctl/train.log" | python3 -c "
import sys,re,json
out={}
for l in sys.stdin:
    m=re.search(r\"eval_([a-z_0-9]+)_loss': '([0-9.]+)'\",l); e=re.search(r\"'epoch': '([0-9.]+)'\",l)
    if m and e: out.setdefault(m.group(1),{})[str(int(round(float(e.group(1)))))]=float(m.group(2))
json.dump(out,open('$HERE/results/$RUN/dev_losses.json','w'),indent=1); print({k:v.get('2') for k,v in out.items()})"
EVAL_JOB=$J bash $HERE/cluster/eval_checkpoint.sh $R/runs/$RUN/epoch2 ${RUN}_ep2 1 > $HERE/results/${RUN}_ep2/driver.log 2>&1; say "driver exit $?: $(tail -n 1 $HERE/results/${RUN}_ep2/driver.log | cut -c1-100)"
sshc "bash $R/workbench.sh close $J" | tail -1; bash $HERE/cluster/ledger.sh $J "$RUN + light eval" "training + light evals of epoch2" | tail -1
cd $HERE && git add -f results/$RUN/dev_losses.json && git add EXECUTION_LOG.md execution_state.json && git commit -q -m "$RUN done + light evals" >/dev/null; say DONE
