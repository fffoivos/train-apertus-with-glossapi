#!/usr/bin/env bash
# Krikri Greek suite lanes on ONE normal workbench (one GPU per lane, up to 4 lanes; extra lanes queue on GPU 0..3 round-robin sequentially). Per-launch copy.
# Usage: [WALL=03:00:00] bash cluster/krikri_suite_run.sh <label>=<dir>:<base|chat> [...]   → results/<label>/krikri_suite_<proto>/
if [ -z "${KS_COPY:-}" ]; then c=$(mktemp -t krikri_suite.XXXXXX.sh); cp "$0" "$c"; KS_COPY=1 exec bash "$c" "$@"; fi
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; HERE=$PWD; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; WALL=${WALL:-03:00:00}
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] krikri_suite: $*"; }
scp -4 -q cluster/eval_jobs/krikri_suite.sh clariden:$R/eval_jobs/krikri_suite.sh || { say "upload failed"; exit 1; }
hours=$(python3 -c "h,m,s='$WALL'.split(':'); print(int(h)+int(m)/60)"); bash cluster/preflight.sh $hours "krikri_suite" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
W=$(sshc "bash $R/workbench.sh open krikri_suite normal $WALL" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "no workbench [$W]"; exit 1; }; say "workbench $W"
used=$(sshc "srun --jobid=$W --overlap --ntasks=1 --export=ALL nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits" | sort -n | tail -1); if [ "${used:-99999}" -gt 4000 ]; then say "dirty node (${used} MiB): closing $W"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W krikri_suite_dirty "closed: dirty node" | tail -1; exit 2; fi; say "GPUs clean (max ${used} MiB)"
# lanes: GPU g runs its assigned specs sequentially
declare -a LANE0 LANE1 LANE2 LANE3; i=0; KEYS=""
for spec in "$@"; do L=${spec%%=*}; rest=${spec#*=}; D=${rest%:*}; PR=${rest##*:}; KEYS="$KEYS $L:$PR"; g=$((i % 4)); cmd="MODEL=$D LABEL=$L GPU=$g PROTO=$PR srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL bash $R/eval_jobs/krikri_suite.sh > $R/logs/${L}_krikri_${PR}.log 2>&1"; eval "LANE$g+=(\"$cmd\")"; i=$((i+1)); done
for g in 0 1 2 3; do eval "n=\${#LANE$g[@]}"; [ "$n" -gt 0 ] || continue; eval "cmds=(\"\${LANE$g[@]}\")"; joined=$(printf '%s; ' "${cmds[@]}"); sshc "cd $R; mkdir -p logs; nohup setsid bash -c \"$joined\" > $R/logs/krikri_lane_$g.log 2>&1 &"; done
total=$#; for k in $(seq 1 $((hours*60+5))); do n=0; for key in $KEYS; do L=${key%%:*}; PR=${key##*:}; sshc "ls $R/evals/$L/krikri_suite_$PR/*/results*.json $R/evals/$L/krikri_suite_$PR/results*.json 2>/dev/null | grep -q ." && n=$((n+1)); done; [ "$n" -ge $total ] && break; sleep 60; done
say "$n of $total result sets after $k min"; sshc "bash $R/workbench.sh close $W" | tail -1; bash $HERE/cluster/ledger.sh $W krikri_suite "Krikri Greek suite: $*" | tail -1
for key in $KEYS; do L=${key%%:*}; PR=${key##*:}; mkdir -p results/$L; scp -rq clariden:$R/evals/$L/krikri_suite_$PR results/$L/ 2>/dev/null; f=$(ls results/$L/krikri_suite_$PR/*/results*.json results/$L/krikri_suite_$PR/results*.json 2>/dev/null | head -1); [ -n "$f" ] && python3 -c "
import json; d=json.load(open('$f')); r=d.get('results',{}); print('$L/$PR', {k: round(v.get('acc_norm,none', v.get('acc,none', 0))*100, 1) for k,v in r.items() if not k.startswith('mmlu_el_')})" || { echo "$L/$PR: no results; tail:"; sshc "tail -3 $R/logs/${L}_krikri_${PR}.log" | cut -c1-200; }; done
