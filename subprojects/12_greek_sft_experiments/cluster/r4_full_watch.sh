#!/usr/bin/env bash
# 15-minute watchdog for the R4_full chain (owner rule: never fire-and-forget Slurm work). Appends one line per tick to results/R4_full/watch.log:
# job state + elapsed/limit, last loss line, failure signatures in train.log, chain phase, certificate hours left. Exits when the chain log says DONE or FAILED
# and no job of ours is left. Usage: bash cluster/r4_full_watch.sh <train_jobid>
J=$1; cd "$(dirname "$0")/.."; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; W=results/R4_full/watch.log; C=logs/r4_full_chain.log
C0=$(wc -l < $C)   # only chain lines written AFTER this watchdog started count as its end (older FAILED lines from earlier attempts made the first watchdog exit at TRAIN_OK)
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 clariden "$@" 2>/dev/null; }
while true; do
  now=$(date '+%m-%d %H:%M'); q=$(sshc "squeue -h -u \$USER -o '%i %j %T %M/%l %R'" | tr '\n' ';'); rc=$?
  if [ $rc -ne 0 ]; then echo "[$now] SSH FAILED (certificate? network) — cluster state unknown; chain: $(tail -1 $C | cut -c1-120)" >> $W
  else
    tl=$(sshc "tail -400 $R/runs/R4_full.ctl/train.log 2>/dev/null | grep -E \"'loss'|TRAIN_OK|RUN_EXIT|Traceback|OutOfMemory|TIME LIMIT|CANCELLED|Error\" | tail -3 | tr '\n' ' ' | cut -c1-300")
    exp=$(ssh-keygen -Lf ~/.ssh/cscs-key-cert.pub 2>/dev/null | grep -oE 'to [0-9T:-]+' | cut -c4-); left=$(python3 -c "from datetime import datetime as d; print(round((d.fromisoformat('$exp')-d.now()).total_seconds()/3600,1))" 2>/dev/null)
    echo "[$now] jobs[$q] cert_h_left=$left | train.log: ${tl:-no loss line yet} | chain: $(tail -1 $C | cut -c1-140)" >> $W
    echo "$tl" | grep -qE "Traceback|OutOfMemory|TIME LIMIT|CANCELLED|RUN_EXIT [1-9]" && echo "[$now] ALERT training failure signature: $tl" >> $W
  fi
  tail -n +$((C0+1)) $C | grep -qE "R4_FULL_CHAIN_DONE|FAILED" && [ -z "$q" ] && { echo "[$now] watchdog exit: chain ended and no jobs left" >> $W; exit 0; }
  sleep 900
done
