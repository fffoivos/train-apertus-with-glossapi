#!/usr/bin/env bash
# The from-scratch pass 1-G4F6P1 (owner decision 15 Sept 01:30): train from the CPT base on data/arms/R4_full, then the full battery, the peers and Krikri's six. Mac-orchestrated, launch DETACHED. Usage: bash cluster/r4_full_chain.sh
#  0 set the parent, assemble data/arms/R4_full (maths 15% of supervised tokens, correcting v2, suite x2), preflight
#  A upload + sbatch (normal, 3:00) → TRAIN_OK → ledger → eval copy
#  B in parallel: light evals (debug; ILSP, dev50, interviews) + full battery (native, GreekMMLU, retention; normal)
#  C vLLM window (normal 2:30): four Greek benchmarks el+en + MATH-200-el-confirm (once) + 60 mixed-profile dialogues
#  D scoring: math500/math200/ifbench local; xstest + multichallenge judged on Sol; interviews scored on Sol
set -u; cd "$(dirname "$0")/.."; HERE=$PWD; LABEL=R4_full_ep1; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/R4_full; mkdir -p $OUT; LOG=$OUT/chain.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
say "PHASE 0: readiness of data/arms/R4_full (assembled by data/assemble_full_r4.py)"
for f in data/arms/R4_full/train.jsonl data/arms/R4_full/dev.jsonl data/arms/R4_full/receipt.json data/math/cut2/final/label_disagreements.json cluster/configs/R4_full.yaml; do [ -s $f ] || { say "FAILED: missing $f"; exit 1; }; done
grep -q "ALLOW-UNCONFIRMED" data/arms/R4_full/receipt.json && { say "FAILED: receipt is a dry run (unconfirmed references)"; exit 1; }
bash cluster/preflight.sh 7 "R4_full_train" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused (7 nh)"; exit 1; }
say "PHASE A: upload + LAUNCH training (1 node, walltime 8:00, 1 epoch, lr 1e-5 cosine from the CPT base; $(wc -l < data/arms/R4_full/train.jsonl) rows)"
sshc "mkdir -p $R/data/arms/R4_full"; scp -4 -q data/arms/R4_full/train.jsonl data/arms/R4_full/dev.jsonl clariden:$R/data/arms/R4_full/ && scp -4 -q cluster/configs/R4_full.yaml clariden:$R/cluster/configs/R4_full.yaml || { say "FAILED: upload"; exit 1; }
[ "$(sshc "cd $R && md5sum data/arms/R4_full/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/R4_full/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch"; exit 1; }
for F in train dev; do RS=$(python3 -c "import json; print(json.load(open('data/arms/R4_full/receipt.json'))['$F']['sha256'])"); CS=$(sshc "cd $R && sha256sum data/arms/R4_full/$F.jsonl | cut -d' ' -f1"); [ "$RS" = "$CS" ] || { say "FAILED: $F.jsonl sha256 on the cluster ($CS) differs from the receipt ($RS)"; exit 1; }; say "$F.jsonl sha256 bound to the receipt: $CS"; done
grep -q "^expected_train_rows: $(wc -l < data/arms/R4_full/train.jsonl | tr -d ' ')$" cluster/configs/R4_full.yaml || { say "FAILED: config expected_train_rows does not match the manifest"; exit 1; }
for F in cluster/sft_train.py cluster/configs/R4_full.yaml; do LS=$(shasum -a 256 $F | cut -d' ' -f1); CS=$(sshc "cd $R && sha256sum $F | cut -d' ' -f1"); RS=$(python3 -c "import json; d=json.load(open('data/arms/R4_full/receipt.json'))['identities']; import sys; print([v for k,v in {**d.get('inputs',{}), **d.get('code',{})}.items() if k.endswith('$(basename $F)')][0])" 2>/dev/null); [ -n "$RS" ] && [ "$LS" = "$CS" ] && [ "$RS" = "$LS" ] || { say "FAILED: $F hash mismatch (local $LS, cluster $CS, receipt ${RS:-n/a})"; exit 1; }; say "$F bound: $LS"; done
J=$(sshc "cd $R && bash cluster/train_sbatch.sh cluster/configs/R4_full.yaml R4_full 08:00:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "FAILED: sbatch [$J]"; exit 1; }; say "training job $J"; echo $J > $OUT/.train_job
fails=0; while true; do st=$(sshc "squeue -h -j $J -o %T"); rc=$?; if [ $rc -ne 0 ]; then if sshc true; then break; fi; fails=$((fails+1)); [ $((fails % 10)) = 1 ] && say "WARNING: ssh to clariden failing ($fails x 3 min; CSCS certificate expired? re-sign with: cscs-key sign); training job $J is unaffected, still waiting"; sleep 180; continue; fi; fails=0; [ -z "$st" ] && break; sleep 180; done
fails=0; until sshc true; do fails=$((fails+1)); [ $((fails % 10)) = 1 ] && say "WARNING: job $J left the queue but ssh to clariden is failing ($fails x 3 min; re-sign the certificate); waiting before reading train.log"; sleep 180; done
if ! sshc "grep -q TRAIN_OK $R/runs/R4_full.ctl/train.log"; then term=$(sshc "grep -E -m1 'RUN_EXIT|Traceback|TIME LIMIT|CANCELLED|OutOfMemory' $R/runs/R4_full.ctl/train.log | cut -c1-120"); say "FAILED: training ended without TRAIN_OK [$term]"; exit 1; fi
rt=$(sshc "grep -oE \"train_runtime.: .[0-9.]+\" $R/runs/R4_full.ctl/train.log | tail -1"); tl=$(sshc "grep -oE \"train_loss.: .[0-9.]+\" $R/runs/R4_full.ctl/train.log | tail -1"); say "TRAIN_OK [$rt] [$tl]"; bash cluster/ledger.sh $J R4_full training | tail -1 | tee -a $LOG
CK=$R/runs/R4_full/epoch1; sshc "ls $CK/config.json >/dev/null" || CK=$(sshc "ls -d $R/runs/R4_full/epoch* | tail -1"); say "checkpoint $CK"
sshc "bash $R/make_eval_copy.sh $CK $R/eval_copies/$LABEL" | tail -1 | tee -a $LOG
say "PHASE B: light evals (with interviews) + full battery in parallel"
(bash cluster/eval_checkpoint.sh $CK $LABEL > $OUT/light_evals.log 2>&1; echo "light_evals exit $?" >> $LOG) & B1=$!
sleep 120; (bash cluster/native_only.sh $CK $LABEL > $OUT/native.log 2>&1; echo "native exit $?" >> $LOG; bash cluster/retention_chat_run.sh "$LABEL=$R/eval_copies/$LABEL" > $OUT/retention_chat.log 2>&1; echo "retention_chat exit $?" >> $LOG) & B2=$!
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
say "PHASE E0: GreekMMLU official + chat_official for the new model and Apertus-Instruct (one workbench, WALL 3:30)"; WALL=03:30:00 PROTOCOLS=official_label,chat_official bash cluster/greekmmlu_official.sh "R4_full=$R/eval_copies/$LABEL" "apertus=$AP" > $OUT/gmmlu_official.log 2>&1; say "gmmlu official: $(grep -E '^[A-Za-z0-9_]+ [0-9]+ ' $OUT/gmmlu_official.log | tr '\n' ' ' | cut -c1-300)"
KR10=$(sshc "ls -d $R/hf_home/hub/models--ilsp--Llama-Krikri-8B-Instruct/snapshots/* | head -1")
say "PHASE K: Krikri's six benchmarks (ILSP prompts) on four models: new model (chat), Apertus-Instruct (chat), Krikri 1.5 (base, card reproduction), Krikri 1.0 (base)"; WALL=03:00:00 bash cluster/krikri_suite_run.sh "R4_full=$R/eval_copies/$LABEL:chat" "apertus=$AP:chat" "krikri15=$KR15:base" "krikri10=$KR10:base" > $OUT/krikri_suite.log 2>&1; say "krikri suite: $(grep -E '^[a-zA-Z0-9_]+/(base|chat) ' $OUT/krikri_suite.log | tr '\n' ' ' | cut -c1-400)"
wait $B2; say "battery done ($(grep -c 'exit 0' $LOG) sub-drivers exited 0)"; say "R4_FULL_CHAIN_DONE"
