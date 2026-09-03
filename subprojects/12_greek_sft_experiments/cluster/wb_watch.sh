#!/usr/bin/env bash
# Watch a workbench from the Mac: poll job state + GPU compute processes ON THE NODE (never login-node pgrep).
# Usage: wb_watch.sh <jobid> <done-file-on-cluster> [poll_s=120] [idle_limit_s=900]
# Exits 0 when <done-file> exists, 1 when the job is gone, 2 after idle_limit with no GPU process (and closes it).
set -u
jid=$1; done_file=$2; poll=${3:-120}; idle_limit=${4:-900}; idle=0
while true; do
  out=$(ssh -o BatchMode=yes clariden "st=\$(squeue -h -j $jid -o %T 2>/dev/null || echo GONE); [ -z \"\$st\" ] && st=GONE; apps=\$(srun --jobid=$jid --overlap --ntasks=1 --quiet nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c .); df=\$([ -e $done_file ] && echo yes || echo no); echo \"\$st apps=\$apps done=\$df\"" 2>/dev/null | tail -1)
  echo "$(date '+%H:%M') job $jid: $out"
  case "$out" in
    *done=yes*) exit 0;;
    GONE*|"") exit 1;;
  esac
  apps=${out##*apps=}; apps=${apps%% *}
  if [ "${apps:-0}" -eq 0 ]; then idle=$((idle+poll)); else idle=0; fi
  if [ $idle -ge $idle_limit ]; then echo "idle ${idle}s → closing"; ssh -o BatchMode=yes clariden "bash /iopsstor/scratch/cscs/fffoivos/sft_round1/workbench.sh close $jid" 2>/dev/null; exit 2; fi
  sleep $poll
done
