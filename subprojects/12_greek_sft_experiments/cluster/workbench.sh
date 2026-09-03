#!/usr/bin/env bash
# Workbench allocations per CLUSTER_PROTOCOL.md §1. Runs ON the login node (Claude ships it via ssh).
#   workbench.sh open  <label> [partition=debug] [time=01:29:00]   → prints JOBID once RUNNING
#   workbench.sh run   <jobid> <cmd...>                            → srun --overlap one command on the node
#   workbench.sh idle  <jobid>                                     → seconds since the last GPU process (watchdog input)
#   workbench.sh close <jobid>                                     → scancel + accounting line
set -euo pipefail
S=/iopsstor/scratch/cscs/fffoivos; LOG=$S/sft_round1/logs/workbench.log; mkdir -p "$(dirname "$LOG")"
case "${1:-}" in
  open)
    label=$2; part=${3:-debug}; tl=${4:-01:29:00}
    secs=$(echo "$tl" | awk -F: '{print $1*3600+$2*60+$3}')
    jid=$(sbatch --parsable --account=a0140 --partition="$part" --nodes=1 --ntasks-per-node=1 --gpus-per-node=4 --cpus-per-task=288 --mem=640G \
          --time="$tl" --job-name="wb_$label" --output="$S/sft_round1/logs/wb_${label}_%j.out" --wrap="sleep $secs")
    echo "$(date -u +%FT%TZ) OPEN $label job=$jid part=$part time=$tl" >> "$LOG"
    for i in $(seq 1 720); do st=$(squeue -h -j "$jid" -o %T 2>/dev/null || echo GONE); [ "$st" = RUNNING ] && break; [ "$st" = GONE ] && { echo "job $jid vanished" >&2; exit 2; }; sleep 10; done
    node=$(squeue -h -j "$jid" -o %N); echo "$(date -u +%FT%TZ) RUNNING $label job=$jid node=$node" >> "$LOG"; echo "$jid";;
  run)
    jid=$2; shift 2; srun --jobid="$jid" --overlap --ntasks=1 --cpus-per-task=288 --gpus-per-node=4 --export=ALL "$@";;
  idle)
    jid=$2; srun --jobid="$jid" --overlap --ntasks=1 --quiet bash -c 'nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q . && echo 0 || { f=/tmp/wb_last_busy; [ -f $f ] || date +%s > $f; echo $(( $(date +%s) - $(cat $f) )); }';;
  close)
    jid=$2; el=$(sacct -j "$jid" -n -o Elapsed -X 2>/dev/null | head -1 | tr -d ' '); scancel "$jid" || true
    echo "$(date -u +%FT%TZ) CLOSE job=$jid elapsed=$el" >> "$LOG"; echo "closed $jid elapsed=$el";;
  *) echo "usage: workbench.sh open|run|idle|close ..." >&2; exit 1;;
esac
