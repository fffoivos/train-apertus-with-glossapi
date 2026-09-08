#!/usr/bin/env bash
# Evaluate one checkpoint end to end (Mac-orchestrated, one debug workbench ≤ 1:29):
#   native suite (4 lanes, fp32) + ILSP ifeval_greek/mgsm_greek (GPU0) + dev50 gen/format gate + reading40 (GPU1)
#   + interviews rounds 1–3 (GPU2) with the interviewer/scorer on the Mac between rounds; voice score on the Mac.
# Usage: cluster/eval_checkpoint.sh <ckpt_dir_on_cluster> <label> [skip_native=1]
# NOTE (2026-09-04 rehearsal): the fp32 native suite fills all four GPUs (76–97 GB each) and OOMs the other lanes →
# run the LIGHT evals here (default) and the native suite separately with cluster/native_only.sh.
set -u
# Never run this file directly while it may be edited: bash reads scripts incrementally (a live edit killed the ep3 driver
# with a phantom syntax error, 2026-09-04). Launch through a per-label copy:
if [ -z "${EVAL_DRIVER_COPY:-}" ]; then
  HERE0="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$HERE0/results/$2"; cp "$0" "$HERE0/results/$2/driver.sh"
  EVAL_ROOT="$HERE0" EVAL_DRIVER_COPY=1 exec bash "$HERE0/results/$2/driver.sh" "$@"
fi
CK_RAW=$1; LABEL=$2; SKIP_NATIVE=${3:-1}
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; EV=$R/evals/$LABEL
HERE="${EVAL_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"; P=/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
LOCAL=$HERE/results/$LABEL; mkdir -p $LOCAL/interviews
CK=$R/eval_copies/$LABEL   # transformers-4-compatible copy (base config/tokenizer + chat template, weights symlinked)
sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }
say() { echo "[$(date '+%H:%M')] eval $LABEL: $*"; }
sshc "bash $R/make_eval_copy.sh $CK_RAW $CK" | tail -2
bash $HERE/cluster/preflight.sh 1.2 "eval_$LABEL" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
if [ -n "${EVAL_JOB:-}" ]; then J=$EVAL_JOB; else J=$(sshc "bash $R/workbench.sh open ev_$LABEL debug 01:29:00" | tail -1); fi; [[ "$J" =~ ^[0-9]+$ ]] || { say "workbench open failed: [$J]"; exit 1; }; say "workbench $J"
NODE_ENV="export HF_HOME=$R/hf_home HF_HUB_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft/bin/activate; cd $R/evals_code"
lane() { # lane <name> <gpu> <cmd-inside-uenv-bash>
  local name=$1 gpu=$2 cmd=$3
  sshc "cd $R; mkdir -p $EV logs; nohup setsid bash -c \"srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=48 --export=ALL bash -c 'CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c \\\"$NODE_ENV; $cmd\\\"'\" > $R/logs/${LABEL}_$name.launch.log 2>&1 & echo launched $name"
}
if [ "$SKIP_NATIVE" = 0 ]; then sshc "cd $R; nohup setsid bash -c \"MODEL=$CK LABEL=$LABEL srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=96 --export=ALL bash $R/eval_jobs/native.sh\" > $R/logs/${LABEL}_native.launch.log 2>&1 & echo launched native"; fi
lane ilsp 0 "export PYTHONPATH=$S/python_envs/lm_eval LD_LIBRARY_PATH=$S/python_envs/lm_eval/scipy.libs:$S/python_envs/lm_eval/numpy.libs:$S/python_envs/lm_eval/scikit_learn.libs:\${LD_LIBRARY_PATH:-}; deactivate 2>/dev/null; python3 -m lm_eval --model hf --model_args pretrained=$CK,dtype=bfloat16 --tasks ifeval_greek,mgsm_greek --apply_chat_template --include_path $R/evals_code/ilsp/tasks --batch_size 32 --output_path $EV/ilsp/ --log_samples"
if [ -n "${EXTRA_ILSP_LABEL:-}" ]; then XEV=$R/evals/$EXTRA_ILSP_LABEL; lane ilsp_x 3 "export PYTHONPATH=$S/python_envs/lm_eval LD_LIBRARY_PATH=$S/python_envs/lm_eval/scipy.libs:$S/python_envs/lm_eval/numpy.libs:$S/python_envs/lm_eval/scikit_learn.libs:\${LD_LIBRARY_PATH:-}; deactivate 2>/dev/null; mkdir -p $XEV/ilsp; python3 -m lm_eval --model hf --model_args pretrained=$EXTRA_ILSP_CK,dtype=bfloat16 --tasks ifeval_greek,mgsm_greek --apply_chat_template --include_path $R/evals_code/ilsp/tasks --batch_size 32 --output_path $XEV/ilsp/ --log_samples"; fi  # optional 4th lane: IFEval/MGSM of another eval copy (e.g. the previous stage) on GPU 3
lane dev 1 "mkdir -p $EV/dev; python dev/dev_generate.py --model $CK --prompts $R/dev/dev50.jsonl --out $EV/dev/dev_gen.jsonl && python dev/format_gate.py $EV/dev/dev_gen.jsonl; python dev/dev_generate.py --model $CK --prompts $R/dev/reading40.jsonl --out $EV/dev/reading40_gen.jsonl; python dev/dev_generate.py --model $CK --prompts $R/dev/identity40.jsonl --out $EV/dev/identity40_gen.jsonl"
lane int1 2 "mkdir -p $EV/interviews; python interviews/driver.py --model $CK --seeds $R/evals_code/interviews/seeds.jsonl --run $LABEL --round 1 --out-dir $EV/interviews"
wait_file() { local f=$1 max=${2:-70}; for i in $(seq 1 $max); do sshc "[ -s $f ] && echo yes" | grep -q yes && return 0; sleep 60; done; return 1; }
for k in 2 3; do
  wait_file $EV/interviews/turn$((k-1)).jsonl 40 || { say "round $((k-1)) transcript missing"; break; }
  scp -q clariden:$EV/interviews/turn$((k-1)).jsonl $LOCAL/interviews/ 2>/dev/null; [ $k = 3 ] && scp -q clariden:$EV/interviews/followups2.jsonl $LOCAL/interviews/ 2>/dev/null
  (cd $HERE/evals && $P interviews/interviewer.py --run $LABEL --turn $k --out-dir $LOCAL/interviews) > $LOCAL/interviews/interviewer$k.log 2>&1; say "interviewer turn $k done ($(grep -c . $LOCAL/interviews/followups$k.jsonl 2>/dev/null) follow-ups)"
  scp -q $LOCAL/interviews/followups$k.jsonl clariden:$EV/interviews/ 2>/dev/null
  lane int$k 2 "python interviews/driver.py --model $CK --seeds $R/evals_code/interviews/seeds.jsonl --run $LABEL --round $k --out-dir $EV/interviews"
done
wait_file $EV/interviews/turn3.jsonl 30 && scp -q clariden:$EV/interviews/turn3.jsonl $LOCAL/interviews/ 2>/dev/null
wait_file "$EV/ilsp/*/results*.json" 40 || say "ILSP results missing"
if [ -n "${EXTRA_ILSP_LABEL:-}" ]; then wait_file "$XEV/ilsp/*/results*.json" 25 || say "extra ILSP ($EXTRA_ILSP_LABEL) missing"; mkdir -p $HERE/results/$EXTRA_ILSP_LABEL; scp -rq clariden:$XEV/ilsp $HERE/results/$EXTRA_ILSP_LABEL/ 2>/dev/null; fi
wait_file $EV/dev/reading40_gen.jsonl 20 || say "reading40 missing"
wait_file $EV/dev/identity40_gen.jsonl 10 || say "identity40 missing"
if [ "$SKIP_NATIVE" = 0 ]; then for i in $(seq 1 60); do n=$(sshc "ls $EV/native 2>/dev/null | grep -c -E '^(demos|other_mcq|oyxoy)'"); [ "${n:-0}" -ge 21 ] && sshc "for d in $EV/native/*; do [ -f \$d/metrics.csv ] || exit 1; done" && break; sleep 60; done; fi
if [ -z "${EVAL_JOB:-}" ]; then sshc "bash $R/workbench.sh close $J" | tail -1; bash $HERE/cluster/ledger.sh $J "eval_$LABEL" "checkpoint evals (native/ILSP/dev/interviews)" | tail -1; else say "reused workbench $J left open"; fi
scp -rq clariden:$EV/dev clariden:$EV/ilsp $LOCAL/ 2>/dev/null; [ "$SKIP_NATIVE" = 0 ] && scp -rq clariden:$EV/native $LOCAL/ 2>/dev/null
(cd $HERE/evals && $P dev/voice_score.py $LOCAL/dev/dev_gen.jsonl) > $LOCAL/dev/voice.log 2>&1; say "voice: $(tail -n 1 $LOCAL/dev/voice.log | cut -c1-120)"
(cd $HERE/evals && $P interviews/score.py --run $LABEL --out-dir $LOCAL/interviews) > $LOCAL/interviews/score.log 2>&1; say "interview score: $(tail -n 1 $LOCAL/interviews/score.log | cut -c1-120)"
say "DONE"
