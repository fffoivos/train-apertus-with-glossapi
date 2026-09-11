#!/usr/bin/env bash
# Sequenced post-training driver for R3_single (Mac-side, launch DETACHED via data/launch_detached.py). Phases, each logged, each stopping the driver on failure:
#  A wait for the training job to finish with TRAIN_OK; ledger it
#  B eval copy of runs/R3_single/epoch1 → eval_copies/R3_single_ep1
#  C in parallel: light evals of R3 (debug workbench, eval_checkpoint.sh), full battery of R3 (normal), full battery of arm B (normal)
#  D vLLM window (normal, 2:00): serve R3 + arm B, the four Greek benchmarks (generate.py, el+en, both models), then 60 hostile picky-user dialogues on R3 if the Sol bucket allows
#  E programmatic scoring on the Mac (MATH-500-el, IFBench-el); judged scoring (XSTest-el, MultiChallenge-el, claude -p) is left for a manual step because of its Claude-usage cost
# Usage: bash cluster/post_train_R3.sh <train_jobid>
set -u; cd "$(dirname "$0")/.."; HERE=$PWD; J=$1; LABEL=R3_single_ep1; BLABEL=R2_idB_ep2
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/R3_single; mkdir -p $OUT; LOG=$OUT/post_driver.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
say "PHASE A: waiting for training job $J"
while true; do st=$(sshc "squeue -h -j $J -o %T"); [ -z "$st" ] && break; sleep 300; done
term=$(sshc "grep -E -m1 'TRAIN_OK|RUN_EXIT|Traceback|TIME LIMIT|CANCELLED|OutOfMemory' $R/runs/R3_single.ctl/train.log | cut -c1-120")
sshc "grep -q TRAIN_OK $R/runs/R3_single.ctl/train.log" || { say "FAILED: training ended without TRAIN_OK: [$term]; driver stops"; exit 1; }
say "training TRAIN_OK: $(sshc "grep -o \"'train_runtime': '[0-9.]*'\" $R/runs/R3_single.ctl/train.log | tail -1")"; bash cluster/ledger.sh $J R3_single "training" | tail -1 | tee -a "$LOG"
say "PHASE B: eval copy"; sshc "ls $R/runs/R3_single/epoch1/config.json >/dev/null" || { say "FAILED: no epoch1 checkpoint"; exit 1; }
sshc "bash $R/make_eval_copy.sh $R/runs/R3_single/epoch1 $R/eval_copies/$LABEL" | tail -1 | tee -a "$LOG"
say "PHASE C: light evals + two full batteries in parallel"
(bash cluster/eval_checkpoint.sh $R/runs/R3_single/epoch1 $LABEL > $OUT/light_evals.log 2>&1; echo "light_evals exit $?" >> $LOG) &
sleep 120   # let the debug workbench open before the normal ones queue
(bash cluster/full_battery.sh $R/runs/R3_single/epoch1 $LABEL > $OUT/battery_R3.log 2>&1; echo "battery_R3 exit $?" >> $LOG) &
sleep 60
(bash cluster/full_battery.sh $R/runs/R2_idB/epoch2 $BLABEL > $OUT/battery_B.log 2>&1; echo "battery_B exit $?" >> $LOG) &
wait; say "PHASE C done: $(grep -c 'exit 0' $LOG) of 3 sub-drivers exited 0 (see light_evals.log, battery_R3.log, battery_B.log)"
(bash cluster/finish_eval.sh $LABEL > $OUT/finish_eval.log 2>&1; echo "finish_eval exit $?" >> $LOG)
say "PHASE D: vLLM window for the four Greek benchmarks (+ hostile dialogues)"
bash cluster/preflight.sh 2.0 "bench_$LABEL" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the benchmark window"; exit 1; }
W=$(sshc "bash $R/workbench.sh open bench_$LABEL normal 02:00:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED: no workbench [$W]"; exit 1; }; say "workbench $W"
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh R3=$R/eval_copies/$LABEL B=$R/eval_copies/$BLABEL\" > $R/logs/serve_bench_$LABEL.log 2>&1 &"
NODE=$(sshc "squeue -h -j $W -o %N"); ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 -L 8001:$NODE:8001 clariden & TUN=$!
for i in $(seq 1 60); do curl -s -m 10 http://127.0.0.1:8001/v1/models | grep -q '"id"' && curl -s -m 10 http://127.0.0.1:8000/v1/models | grep -q '"id"' && break; sleep 15; done
curl -s -m 10 http://127.0.0.1:8001/v1/models | grep -q '"id"' || { say "FAILED: models did not come up"; sshc "tail -3 $R/serve_R3.log; tail -3 $R/serve_B.log" | tee -a $LOG; kill $TUN; sshc "bash $R/workbench.sh close $W"; exit 1; }
say "endpoints ready after $((i*15)) s; generating the four benchmarks, el+en, both models"
$PY data/benchmarks_el/generate.py http://127.0.0.1:8000/v1 R3 $OUT/bench_R3 --workers 24 > $OUT/bench_R3.log 2>&1 &
$PY data/benchmarks_el/generate.py http://127.0.0.1:8001/v1 B $OUT/bench_B --workers 24 > $OUT/bench_B.log 2>&1 &
wait; say "benchmark generation done: $(tail -4 $OUT/bench_R3.log | tr '\n' ' ') | B: $(tail -4 $OUT/bench_B.log | tr '\n' ' ')"
used=$(tail -1 $HOME/sft_annot/limit_probe.log 2>/dev/null | grep -o 'used=[0-9.]*' | cut -d= -f2); used=${used:-100}
if [ "$(python3 -c "print(1 if float('$used') <= 92 else 0)")" = 1 ]; then
  say "Sol bucket at ${used}%: running 60 hostile dialogues on R3"; WORKERS=16 python3 data/robustness/simulate.py $OUT/r0_hostile --target R3=http://127.0.0.1:8000/v1/R3 --n 60 > $OUT/sim_r0.log 2>&1; say "dialogues done: $(tail -2 $OUT/sim_r0.log | tr '\n' ' ' | cut -c1-300)"
else say "Sol bucket at ${used}%: hostile dialogues SKIPPED (run after the Friday reset)"; fi
kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W "bench_$LABEL" "four Greek benchmarks + dialogues" | tail -1 | tee -a $LOG
say "PHASE E: programmatic scoring"
for M in R3 B; do for L in el en; do
  [ -s $OUT/bench_$M/math500_$L.jsonl ] && $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_$M/math500_$L.jsonl $OUT/bench_$M/math500_${L}_score.json 2>&1 | tail -1 | sed "s/^/math500 $M $L: /" | tee -a $LOG
  [ -s $OUT/bench_$M/ifbench_$L.jsonl ] && $PY data/benchmarks_el/ifbench/score.py $OUT/bench_$M/ifbench_$L.jsonl $OUT/bench_$M/ifbench_${L}_score.jsonl 2>&1 | tail -1 | cut -c1-200 | sed "s/^/ifbench $M $L: /" | tee -a $LOG
done; done
say "DONE. Manual next: xstest/multichallenge judges (claude -p), picky-user benign run after the Sol reset, results doc."
