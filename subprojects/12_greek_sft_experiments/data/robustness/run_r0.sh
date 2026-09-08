#!/usr/bin/env bash
# The R0/R1/M3 cluster window (docs/ROBUSTNESS_PROGRAM_20260909.md §7). Runs on the Mac against an OPEN workbench job.
# Usage: bash run_r0.sh <jobid> [n_dialogues=120] [rep_penalty_R1=1.1]
set -u; cd "$(dirname "$0")/../.."; J=$1; N=${2:-120}; RP=${3:-1.1}
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; OUT=results/robustness_r0_$(date +%Y%m%d); mkdir -p "$OUT"; LOG=$OUT/run.log
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
sshc(){ ssh -o BatchMode=yes -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
# 1. serve four models on the node (detached on the login node, as the eval lanes do)
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh armB=$R/eval_copies/R2_idB_ep2 stage1=$R/eval_copies/R2_stage1_ep1 apertus=swiss-ai/Apertus-8B-Instruct-2509 krikri=ilsp/Llama-Krikri-8B-Instruct\" > $R/logs/serve_r0.out 2>&1 &"
NODE=$(sshc "squeue -h -j $J -o %N"); say "job $J on node $NODE; serving started"
# 2. tunnel
ssh -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 -L 8001:$NODE:8001 -L 8002:$NODE:8002 -L 8003:$NODE:8003 clariden & TUN=$!; say "tunnel pid $TUN"
ready(){ curl -s -m 5 "http://127.0.0.1:$1/v1/models" | grep -q '"id"'; }
for i in $(seq 1 60); do ok=0; for p in 8000 8001 8002 8003; do ready $p && ok=$((ok+1)); done; [ $ok -eq 4 ] && break; sleep 20; done
say "endpoints ready: $ok/4 after $((i*20)) s"; [ $ok -ge 1 ] || { say "no endpoint came up; see $R/logs/serve_r0.out and $R/serve_*.log"; sshc "tail -5 $R/serve_armB.log"; kill $TUN; exit 1; }
sshc "tail -2 $R/serve_armB.log" | tee -a "$LOG"
# 3. R0: four targets, two parallel invocations of 24 workers; M3 on arm B concurrently; R1 after
python3 data/robustness/simulate.py "$OUT" --target armB=http://127.0.0.1:8000/v1/armB --target apertus=http://127.0.0.1:8002/v1/apertus --n "$N" > "$OUT/sim_a.log" 2>&1 &
python3 data/robustness/simulate.py "$OUT" --target stage1=http://127.0.0.1:8001/v1/stage1 --target krikri=http://127.0.0.1:8003/v1/krikri --n "$N" > "$OUT/sim_b.log" 2>&1 &
( for i in $(seq 1 50); do [ -s ~/sft_annot/math_pilot/M2/results.jsonl ] && break; sleep 60; done; [ -s ~/sft_annot/math_pilot/M2/results.jsonl ] && ~/venvs/sftdata/bin/python data/math/m3_armb.py ~/sft_annot/math_pilot/M2 "$OUT/m3" --target armB=http://127.0.0.1:8000/v1/armB --samples 4 > "$OUT/m3.log" 2>&1 || echo "M3 skipped: M2 results not ready" >> "$LOG" ) &
wait; say "R0 + M3 done"
python3 data/robustness/simulate.py "$OUT/r1_rp$RP" --target armB=http://127.0.0.1:8000/v1/armB --n "$N" --rep-penalty "$RP" > "$OUT/sim_r1.log" 2>&1; say "R1 done"
# 4. close and account
kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $J" | tee -a "$LOG"; sleep 20; bash cluster/ledger.sh "$J" R0 "picky-user benchmark R0/R1 + math M3 serving window" | tee -a "$LOG"
for f in "$OUT"/*_summary.json "$OUT"/r1_rp$RP/*_summary.json "$OUT"/m3/*_summary.json; do [ -s "$f" ] && { echo "== $f"; python3 -c "import json; d=json.load(open('$f')); print({k:v for k,v in d.items() if k not in ('by_grade','by_topic','by_surface','tone')}); print('tone', d.get('tone'))"; }; done | tee -a "$LOG"
say "WINDOW DONE"
