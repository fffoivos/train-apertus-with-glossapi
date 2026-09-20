#!/usr/bin/env bash
# Phase C (R4 plan §5): the Greek pass. Mac-orchestrated, launch DETACHED. Usage: [FORMAT_BLOCK=path] bash cluster/r4_chain.sh <parent run, e.g. R2_stage1> <greek maths arm: M1|M2|none>
#  0 set the parent, assemble data/arms/R4_pass (maths 15% of supervised tokens, correcting v2, suite x2), preflight
#  A upload + sbatch (normal, 3:00) → TRAIN_OK → ledger → eval copy
#  B in parallel: light evals (debug; ILSP, dev50, interviews) + full battery (native, GreekMMLU, retention; normal)
#  C vLLM window (normal 2:30): four Greek benchmarks el+en + MATH-200-el-confirm (once) + 60 mixed-profile dialogues
#  D scoring: math500/math200/ifbench local; xstest + multichallenge judged on Sol; interviews scored on Sol
set -u; cd "$(dirname "$0")/.."; HERE=$PWD; WIN=$1; GREEK=${2:?greek maths arm: M1|M2|none}; LABEL=R4_pass_ep2; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/R4_pass; mkdir -p $OUT; LOG=$OUT/chain.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
say "PHASE 0: parent = runs/$WIN/epoch1; assembling R4_pass"
sshc "ls $R/runs/$WIN/epoch1/config.json >/dev/null" || { say "FAILED: no checkpoint runs/$WIN/epoch1"; exit 1; }
sed -i '' "s#runs/PILOT_WINNER/epoch1.*#runs/$WIN/epoch1#" cluster/configs/R4_pass.yaml; grep -q "runs/$WIN/epoch1" cluster/configs/R4_pass.yaml || { say "FAILED: config parent not set"; exit 1; }
[ -s data/robustness/correcting/v2/rows_v2.jsonl ] || { say "correcting v2 missing: pass runs WITHOUT a correcting block (no v1 fallback, astra F8)"; CORR="--correcting /dev/null"; }
GK=none; [ "$GREEK" != none ] && GK=data/math/cut2/final/arm_$GREEK.jsonl; FB=""; [ -n "${FORMAT_BLOCK:-}" ] && FB="--format-block $FORMAT_BLOCK"; $PY data/assemble_pass_r4.py --arm R4_pass --greek $GK $FB ${CORR:-} > $OUT/assemble.log 2>&1 || { say "FAILED: assembly ($(tail -2 $OUT/assemble.log | tr '\n' ' '))"; exit 1; }; say "assembled: $(tail -1 $OUT/assemble.log | cut -c1-300)"
bash cluster/preflight.sh 8 "R4_pass" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused (8 nh)"; exit 1; }
say "PHASE A: upload + LAUNCH training (1 node, walltime 3:00, 2 epochs, lr 1e-5 cosine from runs/$WIN/epoch1; $(wc -l < data/arms/R4_pass/train.jsonl) rows)"
sshc "mkdir -p $R/data/arms/R4_pass"; scp -4 -q data/arms/R4_pass/train.jsonl data/arms/R4_pass/dev.jsonl clariden:$R/data/arms/R4_pass/ && scp -4 -q cluster/configs/R4_pass.yaml clariden:$R/cluster/configs/R4_pass.yaml || { say "FAILED: upload"; exit 1; }
[ "$(sshc "cd $R && md5sum data/arms/R4_pass/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/R4_pass/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch"; exit 1; }
J=$(sshc "cd $R && bash cluster/train_sbatch.sh cluster/configs/R4_pass.yaml R4_pass 03:00:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "FAILED: sbatch [$J]"; exit 1; }; say "training job $J"; echo $J > $OUT/.train_job
while true; do st=$(sshc "squeue -h -j $J -o %T"); [ -z "$st" ] && break; sleep 180; done
if ! sshc "grep -q TRAIN_OK $R/runs/R4_pass.ctl/train.log"; then term=$(sshc "grep -E -m1 'RUN_EXIT|Traceback|TIME LIMIT|CANCELLED|OutOfMemory' $R/runs/R4_pass.ctl/train.log | cut -c1-120"); say "FAILED: training ended without TRAIN_OK [$term]"; exit 1; fi
rt=$(sshc "grep -oE \"train_runtime.: .[0-9.]+\" $R/runs/R4_pass.ctl/train.log | tail -1"); tl=$(sshc "grep -oE \"train_loss.: .[0-9.]+\" $R/runs/R4_pass.ctl/train.log | tail -1"); say "TRAIN_OK [$rt] [$tl]"; bash cluster/ledger.sh $J R4_pass training | tail -1 | tee -a $LOG
CK=$R/runs/R4_pass/epoch2; sshc "ls $CK/config.json >/dev/null" || CK=$(sshc "ls -d $R/runs/R4_pass/epoch* | tail -1"); say "checkpoint $CK"
sshc "bash $R/make_eval_copy.sh $CK $R/eval_copies/$LABEL" | tail -1 | tee -a $LOG
say "PHASE B: light evals (with interviews) + full battery in parallel"
(bash cluster/eval_checkpoint.sh $CK $LABEL > $OUT/light_evals.log 2>&1; echo "light_evals exit $?" >> $LOG) & B1=$!
sleep 120; (bash cluster/full_battery.sh $CK $LABEL > $OUT/battery.log 2>&1; echo "battery exit $?" >> $LOG) & B2=$!
wait $B1; say "light evals done; scoring interviews on Sol"; (cd evals && SCORER=sol ../cluster/nsft_python.sh interviews/score.py --run $LABEL --out-dir $HERE/results/$LABEL/interviews > $OUT/interview_score.log 2>&1); say "interviews scored: $(tail -1 $OUT/interview_score.log | cut -c1-160)"
$PY evals/ilsp/rescore_ifeval_langdetect.py results/$LABEL > $OUT/rescore.log 2>&1; say "ifeval rescored: $(tail -1 $OUT/rescore.log | cut -c1-160)"
say "PHASE C: vLLM window (2:30): four benchmarks el+en + MATH-200 confirm + 60 mixed dialogues"
bash cluster/preflight.sh 3.0 "bench_$LABEL" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the benchmark window"; wait $B2; exit 1; }
W=$(sshc "bash $R/workbench.sh open bench_$LABEL normal 03:00:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED: no workbench [$W]"; wait $B2; exit 1; }; say "workbench $W"
KR15=$(sshc "ls -d $R/hf_home/hub/models--ilsp--Llama-Krikri-8B-Instruct-v1.5/snapshots/* | head -1"); AP=$(sshc "ls -d $R/hf_home/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/* | head -1")
[ -n "$KR15" ] && [ -n "$AP" ] || { say "FAILED: Krikri v1.5 or Apertus-Instruct snapshot not found on the cluster"; wait $B2; exit 1; }
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh R4=$R/eval_copies/$LABEL krikri15=$KR15 apertus=$AP\" > $R/serve_R4.log 2>&1 &"
NODE=""; for k in $(seq 1 20); do NODE=$(sshc "squeue -h -j $W -o %N"); [ -n "$NODE" ] && break; sleep 10; done
ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 -L 8001:$NODE:8001 -L 8002:$NODE:8002 clariden & TUN=$!
for k in $(seq 1 80); do ok=1; for pt in 8000 8001 8002; do curl -s -m 10 http://127.0.0.1:$pt/v1/models | grep -q '"id"' || ok=0; done; [ $ok = 1 ] && break; sleep 15; done
[ $ok = 1 ] || { say "FAILED: model did not come up: $(sshc "tail -2 $R/serve_R4.log" | tr '\n' ' ')"; kill $TUN; sshc "bash $R/workbench.sh close $W"; wait $B2; exit 1; }
say "endpoint ready; generating four benchmarks + math200 (greedy, frozen protocol)"
$PY data/benchmarks_el/generate.py http://127.0.0.1:8000/v1 R4 $OUT/bench_R4 --sets math500,ifbench,xstest,multichallenge,math200 --langs el,en --workers 24 > $OUT/bench_R4.log 2>&1 & G1=$!
$PY data/benchmarks_el/generate.py http://127.0.0.1:8001/v1 krikri15 $OUT/bench_krikri15 --sets math500,ifbench,xstest,multichallenge,math200 --langs el,en --workers 24 > $OUT/bench_krikri15.log 2>&1 & G2=$!   # strongest Krikri release, never measured before (checklist §9)
$PY data/benchmarks_el/generate.py http://127.0.0.1:8002/v1 apertus $OUT/bench_apertus --sets math200 --langs el,en --workers 24 > $OUT/bench_apertus.log 2>&1 & G3=$!   # Apertus already has the four benchmarks (peers_20260913); confirm set only
wait $G1 $G2 $G3; say "benchmarks generated: R4 $(tail -1 $OUT/bench_R4.log | cut -c1-80) | krikri15 $(tail -1 $OUT/bench_krikri15.log | cut -c1-80) | apertus $(tail -1 $OUT/bench_apertus.log | cut -c1-60)"
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_R4 --target R4=http://127.0.0.1:8000/v1/R4 --profile mixed --n 60 > $OUT/sim_R4.log 2>&1 & S1=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_krikri15 --target krikri15=http://127.0.0.1:8001/v1/krikri15 --profile mixed --n 60 > $OUT/sim_krikri15.log 2>&1 & S2=$!
wait $S1 $S2; say "mixed dialogues: R4 $(tail -1 $OUT/sim_R4.log | cut -c1-80) | krikri15 $(tail -1 $OUT/sim_krikri15.log | cut -c1-80)"
$PY data/benchmarks_el/mtbench/run.py http://127.0.0.1:8000/v1 R4 $OUT/bench_R4 --workers 8 > $OUT/mtbench_R4.log 2>&1 & T1=$!
$PY data/benchmarks_el/mtbench/run.py http://127.0.0.1:8001/v1 krikri15 $OUT/bench_krikri15 --workers 8 > $OUT/mtbench_krikri15.log 2>&1 & T2=$!
$PY data/benchmarks_el/mtbench/run.py http://127.0.0.1:8002/v1 apertus $OUT/bench_apertus --workers 8 > $OUT/mtbench_apertus.log 2>&1 & T3=$!
wait $T1 $T2 $T3; say "MT-Bench el+en generated for R4, krikri15, apertus (80 x 2 turns each)"
kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W "bench_$LABEL" "four benchmarks + math200 + dialogues" | tail -1 | tee -a $LOG
say "PHASE D: scoring (R4 and Krikri v1.5; Apertus math200)"
for M in krikri15 apertus; do for L in el en; do [ -s $OUT/bench_$M/math200_$L.jsonl ] && MATH_BENCH_FILE=$HERE/data/benchmarks_el/math200_confirm/problems_el_final.jsonl $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_$M/math200_$L.jsonl $OUT/bench_$M/math200_${L}_score.json | tail -1 | cut -c1-160 | sed "s/^/math200 $M $L: /" | tee -a $LOG; done; done
for L in el en; do $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_krikri15/math500_$L.jsonl $OUT/bench_krikri15/math500_${L}_score.json | tail -1 | cut -c1-160 | sed "s/^/math500 krikri15 $L: /" | tee -a $LOG; $PY data/benchmarks_el/ifbench/score.py $OUT/bench_krikri15/ifbench_$L.jsonl $OUT/bench_krikri15/ifbench_${L}_score.jsonl | tail -1 | cut -c1-160 | sed "s/^/ifbench krikri15 $L: /" | tee -a $LOG; done
for L in el en; do $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_R4/math500_$L.jsonl $OUT/bench_R4/math500_${L}_score.json | tail -1 | cut -c1-160 | sed "s/^/math500 $L: /" | tee -a $LOG
  MATH_BENCH_FILE=$HERE/data/benchmarks_el/math200_confirm/problems_el_final.jsonl $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_R4/math200_$L.jsonl $OUT/bench_R4/math200_${L}_score.json | tail -1 | cut -c1-160 | sed "s/^/math200 $L: /" | tee -a $LOG
  $PY data/benchmarks_el/ifbench/score.py $OUT/bench_R4/ifbench_$L.jsonl $OUT/bench_R4/ifbench_${L}_score.jsonl | tail -1 | cut -c1-160 | sed "s/^/ifbench $L: /" | tee -a $LOG; done
WORKERS=24 $PY data/benchmarks_el/multichallenge/judge.py $OUT/bench_R4/multichallenge_el.jsonl $OUT/bench_R4/multichallenge_el_judged_sol.jsonl --backend sol --rubric en > $OUT/bench_R4/mc_judge.log 2>&1; say "multichallenge judged: $(tail -1 $OUT/bench_R4/mc_judge.log | cut -c1-160)"
$PY data/benchmarks_el/xstest/judge.py $OUT/bench_R4/xstest_el.jsonl $OUT/bench_R4/xstest_el_judged_sol.jsonl --backend sol --workers 24 > $OUT/bench_R4/xstest_judge.log 2>&1; say "xstest judged: $(tail -1 $OUT/bench_R4/xstest_judge.log | cut -c1-160)"
WORKERS=24 $PY data/benchmarks_el/multichallenge/judge.py $OUT/bench_krikri15/multichallenge_el.jsonl $OUT/bench_krikri15/multichallenge_el_judged_sol.jsonl --backend sol --rubric en > $OUT/bench_krikri15/mc_judge.log 2>&1; $PY data/benchmarks_el/xstest/judge.py $OUT/bench_krikri15/xstest_el.jsonl $OUT/bench_krikri15/xstest_el_judged_sol.jsonl --backend sol --workers 24 > $OUT/bench_krikri15/xstest_judge.log 2>&1; say "krikri15 judged"
ARMB=$(ls results/robustness_r1_20260909/armB.jsonl 2>/dev/null | head -1); WORKERS=24 $PY data/greek_quality_review.py $OUT/greek_quality R4=$OUT/r_R4/R4.jsonl krikri=results/peers_20260913/r_krikri/krikri.jsonl krikri15=$OUT/r_krikri15/krikri15.jsonl ${ARMB:+armB=$ARMB} --ref krikri > $OUT/greek_quality.log 2>&1; say "Greek-quality blind review: $(tail -1 $OUT/greek_quality.log | cut -c1-200)"
for M in R4 krikri15 apertus; do for L in el en; do WORKERS=24 $PY data/benchmarks_el/mtbench/judge.py $OUT/bench_$M/mtbench_$L.jsonl $OUT/bench_$M/mtbench_${L}_judged_sol.jsonl --lang $L > $OUT/bench_$M/mtbench_judge_$L.log 2>&1; say "mtbench $M $L: $(tail -1 $OUT/bench_$M/mtbench_judge_$L.log | cut -c1-160)"; done; done
say "PHASE E0: GreekMMLU official + chat_official (instruct protocol of record, plan §9g) for G4F6P1--00, the two round-three passes and Apertus-Instruct (one workbench, ≈2.6 nh)"; WALL=03:30:00 PROTOCOLS=official_label,chat_official bash cluster/greekmmlu_official.sh "G4F6P1=$R/eval_copies/$LABEL" "G3F2P2_00=$R/eval_copies/R3_pass_ep2" "G3F2P2_01=$R/eval_copies/R3_passB_ep2" "apertus=$AP" > $OUT/gmmlu_official.log 2>&1; say "gmmlu official: $(grep -E '^[A-Za-z0-9_]+ [0-9]+ ' $OUT/gmmlu_official.log | tr '\n' ' ' | cut -c1-300)"
say "PHASE E: Apertus-Instruct retention on the cached suite (matched comparison, checklist §9)"; bash cluster/retention_only.sh "$AP" apertus_instruct > $OUT/retention_apertus.log 2>&1; say "apertus retention: $(tail -1 $OUT/retention_apertus.log | cut -c1-160)"
wait $B2; say "battery done ($(grep -c 'exit 0' $LOG) sub-drivers exited 0)"; say "R4_CHAIN_DONE"
