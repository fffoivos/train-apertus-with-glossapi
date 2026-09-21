#!/usr/bin/env bash
# GreekMMLU under the official (or another named) protocol for up to FOUR models on one workbench, one
# GPU each, fp32. Mac-orchestrated.
# Usage: [PROTOCOLS=official_label] [SUFFIX=] [WALL=02:00:00] [MAXWAIT=100] bash cluster/greekmmlu_official.sh <label>=<dir> [...]
#        -> results/greekmmlu_official/<label><SUFFIX>.json
# Measured 19 Sept: official_label on all 16,632 items takes ~43 min per model.
# Receipts, not exit codes (R-DPO8 finding 11): every invocation scores into its OWN run directory, so
# a result file left by an earlier run can never satisfy the poll; every scorer writes <label>.exit
# with its status; the workbench is closed only after all have reported, or - at MAXWAIT - after
# saying which scorers are being killed, and then the driver exits non-zero.
if [ -z "${GMMLU_COPY:-}" ]; then c=$(mktemp -t gmmlu_official.XXXXXX.sh); cp "$0" "$c"; GMMLU_COPY=1 exec bash "$c" "$@"; fi   # per-launch copy: editing this file cannot corrupt a running instance
[ $# -ge 1 ] && [ $# -le 4 ] || { echo "gmmlu_official: between 1 and 4 models per workbench (one GPU each), got $#"; exit 1; }
WALL=${WALL:-02:00:00}; MAXWAIT=${MAXWAIT:-100}
python3 -c "h,m,s='$WALL'.split(':'); import sys; sys.exit(0 if int(h)*60+int(m) >= $MAXWAIT+15 else 1)" || { echo "gmmlu_official: WALL ($WALL) must exceed MAXWAIT ($MAXWAIT min) by 15 min, or the allocation dies under live scorers"; exit 1; }
RUNID=$(date +%Y%m%dT%H%M%S)_$$
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; HERE=$PWD; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/greekmmlu_official; mkdir -p $OUT
PQ=$R/wave2_greekmmlu_protocol/greekmmlu_all.jsonl   # JSONL projection of the pinned parquet (converted on the cluster with the sft5 venv; no pandas in the vllm venv)
release(){   # $1 = job id. Returns 0 only when the SCHEDULER has said the job is gone (R-DPO9 H3).
  # A failed ssh or squeue prints nothing, and "nothing" used to be read as "released". The remote command
  # therefore always appends a sentinel carrying squeue's own status; without it the answer is UNKNOWN.
  local w=$1 t out st; sshc "bash $R/workbench.sh close $w" | tail -1; sshc "scancel $w" >/dev/null 2>&1
  for t in $(seq 1 30); do
    out=$(sshc "squeue -h -j $w -o %T 2>/dev/null; echo SENTINEL=\$?")
    case "$out" in
      *SENTINEL=0) st=$(printf '%s' "$out" | sed '$d' | head -1); [ -z "$st" ] && { say "workbench $w confirmed released ($(sshc "sacct -j $w -n -X -o State,Elapsed" | head -1 | tr -s ' '))"; return 0; };;
      *SENTINEL=*) st="squeue-error";;      # e.g. "Invalid job id" once the job has aged out: confirm through sacct instead
      *)           st="no-answer";;          # ssh failed: we know NOTHING
    esac
    if [ "$st" = squeue-error ]; then
      # Parse accounting records one per line and require EVERY one to be terminal. A substring match let
      # "CANCELLED by 123" swallow a trailing RUNNING record (R-DPO11 finding 4).
      fin=$(sshc "sacct -j $w -n -X -P -o State 2>/dev/null; echo SENTINEL=\$?")
      case "$fin" in *SENTINEL=0)
        recs=$(printf '%s' "$fin" | sed '$d' | sed 's/ by [0-9]*$//' | tr -d ' ' | grep -v '^$')
        if [ -n "$recs" ] && ! printf '%s\n' "$recs" | grep -qvE '^(CANCELLED|COMPLETED|TIMEOUT|FAILED|NODE_FAIL|OUT_OF_MEMORY|PREEMPTED|BOOT_FAIL|DEADLINE|REVOKED)$'; then
          say "workbench $w confirmed ended (sacct: $(printf '%s' "$recs" | tr '\n' ','))"; return 0
        fi;;
      esac
    fi
    sleep 10
  done
  say "FATAL: could not confirm workbench $w is released (last state: ${st:-unknown}). It may still be SPENDING. Run: ssh clariden scancel $w"; return 1
}
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] gmmlu_official: $*"; }
scp -4 -q cluster/eval_jobs/greekmmlu_official.py clariden:$R/eval_jobs/greekmmlu_official.py || { say "upload failed"; exit 1; }
cp ../14_greek_rlhf/rlhf/evals/weights.py /tmp/weights_receipt.$$.py && scp -4 -q /tmp/weights_receipt.$$.py clariden:$R/cluster/eval_jobs/weights_receipt.py && scp -4 -q cluster/eval_jobs/official_receipt.py clariden:$R/cluster/eval_jobs/ || { say "receipt tools upload failed"; exit 1; }; rm -f /tmp/weights_receipt.$$.py
bash cluster/preflight.sh $(python3 -c "h,m,s='$WALL'.split(':'); print(int(h)+int(m)/60)") "gmmlu_official" | tail -1 | grep -q '^OK' || { say "preflight refused"; exit 1; }
W=$(sshc "bash $R/workbench.sh open gmmlu_off normal $WALL" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "no workbench [$W]"; exit 1; }; say "workbench $W"
# clean-GPU precheck (14 Sept: nid006573 carried orphaned sglang processes holding 78 GB per GPU from another job): refuse a dirty node and close it
used=$(sshc "srun --jobid=$W --overlap --ntasks=1 --export=ALL nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits" | sort -n | tail -1); if [ "${used:-99999}" -gt 4000 ]; then say "dirty node (max GPU memory used ${used} MiB before launch): closing $W"; if release $W; then bash $HERE/cluster/ledger.sh $W gmmlu_official_dirty "closed: dirty node" | tail -1; else bash $HERE/cluster/ledger.sh $W gmmlu_official_dirty "DIRTY NODE - RELEASE NOT CONFIRMED, check scancel $W" | tail -1; fi; exit 2; fi; say "GPUs clean (max ${used} MiB used)"
RUN=$R/evals/greekmmlu_official/run_$RUNID; sshc "mkdir -p $RUN"
i=0; for spec in "$@"; do L=${spec%%=*}; D=${spec#*=}
  sshc "cd $R; nohup setsid bash -c \"CUDA_VISIBLE_DEVICES=$i srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=64 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'source $S/venvs/vllm/bin/activate; CUDA_VISIBLE_DEVICES=$i exec python $R/eval_jobs/greekmmlu_official.py --parquet $PQ --model $L=$D --output $RUN/$L${SUFFIX:-}.json --protocols ${PROTOCOLS:-official_label} ${EXTRA_ARGS:-}'; echo \\\$? > $RUN/$L.exit\" > $R/logs/gmmlu_official_${RUNID}_$L.log 2>&1 &"; i=$((i+1)); done
LABELS=""; for spec in "$@"; do LABELS="$LABELS ${spec%%=*}"; done
for k in $(seq 1 $MAXWAIT); do n=0; for L in $LABELS; do sshc "test -s $RUN/$L.exit" && n=$((n+1)); done; [ "$n" -ge $# ] && break; sleep 60; done
FAIL=0
for L in $LABELS; do rc=$(sshc "cat $RUN/$L.exit 2>/dev/null"); if [ -z "$rc" ]; then say "$L: STILL RUNNING at MAXWAIT - closing the workbench will kill it"; FAIL=1; elif [ "$rc" != 0 ]; then say "$L: scorer exited $rc"; sshc "tail -5 $R/logs/gmmlu_official_${RUNID}_$L.log"; FAIL=1; fi; done
say "$n of $# scorers reported after $k min (run $RUNID)"
# Shut the allocation down and PROVE it is down; an unanswered query is not proof.
release $W || FAIL=1
bash cluster/ledger.sh $W gmmlu_official "GreekMMLU ${PROTOCOLS:-official_label}: $*" | tail -1
for spec in "$@"; do L=${spec%%=*}; D=${spec#*=}; f=$OUT/$L${SUFFIX:-}.json; tmp=$f.$RUNID.tmp
  scp -4 -q clariden:$RUN/$L${SUFFIX:-}.json $tmp 2>/dev/null || { say "$L: no result file in this run"; FAIL=1; continue; }
  if [ "${PROTOCOLS:-official_label}" = official_label ]; then
    csha=$(sshc "sha256sum $D/config.json" | cut -d" " -f1)
    # the evaluator-side receipt binds this result to the weight bytes it was scored from; without it rlhf.evals refuses the result
    sshc "cd $R && python3 cluster/eval_jobs/official_receipt.py $RUN/$L${SUFFIX:-}.json $RUN/$L${SUFFIX:-}.json.receipt.json" | tail -1
    scp -4 -q clariden:$RUN/$L${SUFFIX:-}.json.receipt.json $f.receipt.json.$RUNID.tmp 2>/dev/null || { say "$L: no evaluator receipt"; rm -f "$tmp"; FAIL=1; continue; }
    python3 cluster/eval_jobs/validate_official_result.py "$tmp" "$L" "$D" "$csha" && mv "$tmp" "$f" && mv "$f.receipt.json.$RUNID.tmp" "$f.receipt.json" || { say "$L: result REJECTED by validate_official_result.py"; rm -f "$tmp"; FAIL=1; }
  else mv "$tmp" "$f"; say "$L: protocol ${PROTOCOLS} copied without official-protocol validation"; fi
done
[ $FAIL -eq 0 ] || { say "INCOMPLETE"; exit 1; }
