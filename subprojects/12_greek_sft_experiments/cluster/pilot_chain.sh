#!/usr/bin/env bash
# R4 plan §4: train the pilot continuations sequentially (sbatch, normal), light-eval each (ILSP IFEval/MGSM + dev50 format gate; interviews skipped),
# then ONE vLLM window serving all arms for MATH-500 el/en (generate.py, frozen protocol), scored on the Mac, summarised with the frozen decision rule.
# Mac-orchestrated; launch DETACHED (data/launch_detached.py). Usage: bash cluster/pilot_chain.sh M0 M1 M2   (arms assembled under data/arms/<arm>, configs cluster/configs/<arm>.yaml)
set -u -o pipefail; cd "$(dirname "$0")/.."; HERE=$PWD; ARMS=("$@"); S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/pilots; mkdir -p $OUT; LOG=$OUT/chain.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
sshc "echo ok" | grep -q ok || { say "FAILED: ssh clariden not available (certificate?)"; exit 1; }
for A in "${ARMS[@]}"; do
  [ -f data/arms/$A/train.jsonl ] && [ -f cluster/configs/$A.yaml ] || { say "FAILED: missing data/arms/$A or config"; exit 1; }
done
python3 data/check_pilot_arms.py "${ARMS[@]}" > $OUT/check_arms.log 2>&1 || { say "FAILED: final-manifest check ($(grep FAIL $OUT/check_arms.log | head -3 | tr '\n' ' '))"; exit 1; }; say "final-manifest check PASS: $(grep -c ^OK $OUT/check_arms.log) assertions"
for A in "${ARMS[@]}"; do   # upload + trainer dry-run for EVERY arm before any submission
  say "$A: uploading $(wc -l < data/arms/$A/train.jsonl) train rows + config"; sshc "mkdir -p $R/data/arms/$A"; scp -4 -q data/arms/$A/train.jsonl data/arms/$A/dev.jsonl clariden:$R/data/arms/$A/ && scp -4 -q cluster/configs/$A.yaml clariden:$R/cluster/configs/$A.yaml || { say "FAILED: upload $A"; exit 1; }
  [ "$(sshc "cd $R && md5sum data/arms/$A/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/$A/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch after upload $A"; exit 1; }
  sshc "cd $R && uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_DATASETS_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft5/bin/activate; python cluster/sft_train.py --config cluster/configs/$A.yaml --dry-run'" > $OUT/dryrun_$A.log 2>&1 || { say "FAILED: trainer dry-run for $A: $(tail -3 $OUT/dryrun_$A.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }
  grep -qiE "drop|truncat|skipp" $OUT/dryrun_$A.log && grep -iE "drop|truncat|skipp" $OUT/dryrun_$A.log | grep -vqE "(: |=)0\b" && { say "FAILED: dry-run for $A reports dropped/truncated rows: $(grep -iE 'drop|truncat|skipp' $OUT/dryrun_$A.log | head -2 | tr '\n' ' ')"; exit 1; }
  say "$A: trainer dry-run OK: $(grep -iE 'rows|tokens|steps' $OUT/dryrun_$A.log | tail -3 | tr '\n' ' ' | cut -c1-300)"
done
bash cluster/preflight.sh $(python3 -c "print(1.5*${#ARMS[@]})") "pilots_${ARMS[*]// /_}" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the pilot set"; exit 1; }
declare -A JOB
for A in "${ARMS[@]}"; do   # submit ALL arms (checked + dry-run above)
  J=$(sshc "cd $R && bash cluster/train_sbatch.sh cluster/configs/$A.yaml $A 01:30:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "FAILED: sbatch $A [$J]"; exit 1; }
  JOB[$A]=$J; echo "$J" > $OUT/.${A}_job; say "$A: LAUNCHED training job $J (1 node, walltime 1:30, 1 epoch, lr 1e-5 cosine from R2_stage1/epoch1)"
done
for A in "${ARMS[@]}"; do
  J=${JOB[$A]}; while true; do st=$(sshc "squeue -h -j $J -o %T"); [ -z "$st" ] && break; sleep 120; done
  if ! sshc "grep -q TRAIN_OK $R/runs/$A.ctl/train.log"; then term=$(sshc "grep -E -m1 'RUN_EXIT|Traceback|TIME LIMIT|CANCELLED|OutOfMemory' $R/runs/$A.ctl/train.log | cut -c1-120"); say "FAILED: $A ended without TRAIN_OK: [$term]"; exit 1; fi
  rt=$(sshc "grep -oE \"train_runtime.: .[0-9.]+\" $R/runs/$A.ctl/train.log | tail -1"); tl=$(sshc "grep -oE \"train_loss.: .[0-9.]+\" $R/runs/$A.ctl/train.log | tail -1")
  say "$A: TRAIN_OK [$rt] [$tl]"; bash cluster/ledger.sh $J "pilot_$A" "training" | tail -1 | tee -a $LOG
  sshc "bash $R/make_eval_copy.sh $R/runs/$A/epoch1 $R/eval_copies/${A}_ep1" | tail -1 | tee -a $LOG
done
say "light evals for all arms in parallel (normal partition workbenches, ILSP + dev50, interviews skipped)"; EP=""
for A in "${ARMS[@]}"; do (SKIP_INTERVIEWS=1 EVAL_PARTITION=normal bash cluster/eval_checkpoint.sh $R/runs/$A/epoch1 ${A}_ep1 > $OUT/light_$A.log 2>&1; echo $? > $OUT/.light_${A}_rc) & EP="$EP $!"; sleep 90; done
wait $EP
for A in "${ARMS[@]}"; do rc=$(cat $OUT/.light_${A}_rc 2>/dev/null || echo 99); [ "$rc" = 0 ] || { say "FAILED: light evals for $A exit $rc"; exit 1; }; [ -n "$(ls results/${A}_ep1/ilsp/*/results*.json 2>/dev/null)" ] || { say "FAILED: no ILSP results for $A"; exit 1; }; done
$PY evals/ilsp/rescore_ifeval_langdetect.py results > $OUT/rescore.log 2>&1 || { say "FAILED: ifeval rescoring"; exit 1; }   # the script scans results/<label>/ilsp and writes the multi-label file results/ifeval_el_rescored.json (with per-prompt items)
for A in "${ARMS[@]}"; do python3 -c "import json,sys; d=json.load(open('results/ifeval_el_rescored.json')); sys.exit(0 if '${A}_ep1' in d and 'prompt_strict_items' in d['${A}_ep1'] else 1)" || { say "FAILED: no rescored IFEval entry for ${A}_ep1"; exit 1; }; say "$A: ifeval rescored: $(grep "^${A}_ep1" $OUT/rescore.log | cut -c1-120)"; done
say "all arms trained; MATH-500 window for ${ARMS[*]}"
bash cluster/preflight.sh 1.5 "pilot_bench" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the benchmark window"; exit 1; }
W=$(sshc "bash $R/workbench.sh open pilot_bench normal 01:30:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED: no workbench [$W]"; exit 1; }; say "workbench $W"
SPEC=""; i=0; for A in "${ARMS[@]}"; do SPEC="$SPEC $A=$R/eval_copies/${A}_ep1"; i=$((i+1)); done
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh $SPEC\" > $R/serve_pilots.log 2>&1 &"
NODE=""; for k in $(seq 1 20); do NODE=$(sshc "squeue -h -j $W -o %N"); [ -n "$NODE" ] && break; sleep 10; done
TUNARGS=""; i=0; for A in "${ARMS[@]}"; do TUNARGS="$TUNARGS -L $((8000+i)):$NODE:$((8000+i))"; i=$((i+1)); done
ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 $TUNARGS clariden & TUN=$!
ok=0; for k in $(seq 1 80); do ok=1; i=0; for A in "${ARMS[@]}"; do curl -s -m 10 http://127.0.0.1:$((8000+i))/v1/models | grep -q '"id"' || ok=0; i=$((i+1)); done; [ $ok = 1 ] && break; sleep 15; done
[ $ok = 1 ] || { say "FAILED: models did not come up: $(sshc "tail -2 $R/serve_pilots.log" | tr '\n' ' ')"; kill $TUN; sshc "bash $R/workbench.sh close $W"; exit 1; }
say "endpoints ready after $((k*15)) s; generating MATH-500 el+en for all arms (greedy, max_tokens 2048)"
PIDS=""; i=0; for A in "${ARMS[@]}"; do $PY data/benchmarks_el/generate.py http://127.0.0.1:$((8000+i))/v1 $A $OUT/bench_$A --sets math500 --langs el,en --workers 24 > $OUT/bench_$A.log 2>&1 & PIDS="$PIDS $!"; i=$((i+1)); done
wait $PIDS; kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W "pilot_bench" "MATH-500 window for ${ARMS[*]}" | tail -1 | tee -a $LOG
for A in "${ARMS[@]}"; do for L in el en; do [ "$(grep -c . $OUT/bench_$A/math500_$L.jsonl)" -eq 500 ] || { say "FAILED: $A math500_$L has $(grep -c . $OUT/bench_$A/math500_$L.jsonl) rows, expected 500"; exit 1; }; python3 data/benchmarks_el/math500/score_math500.py $OUT/bench_$A/math500_$L.jsonl $OUT/bench_$A/math500_${L}_score.json > $OUT/bench_$A/score_$L.log 2>&1 || { say "FAILED: scoring $A $L"; exit 1; }; tail -1 $OUT/bench_$A/score_$L.log | cut -c1-160 | tee -a $LOG; done; done
for A in "${ARMS[@]}"; do WORKERS=24 $PY data/benchmarks_el/math500/adjudicate_unresolved.py $OUT/bench_$A/math500_el.jsonl $OUT/bench_$A/math500_el_score.json > $OUT/bench_$A/adjudicate_el.log 2>&1 || { say "FAILED: adjudication $A"; exit 1; }; say "$A: $(tail -1 $OUT/bench_$A/adjudicate_el.log | cut -c1-120)"; done
python3 data/pilot_summary.py "${ARMS[@]}" > $OUT/summary.log 2>&1 || { say "FAILED: readout ($(tail -2 $OUT/summary.log | tr '\n' ' ')); PILOT_CHAIN_FAILED"; exit 1; }; cat $OUT/summary.log | tee -a $LOG; say "PILOT_CHAIN_DONE"
