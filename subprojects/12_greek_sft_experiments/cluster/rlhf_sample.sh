#!/usr/bin/env bash
# RLHF sampling window: serve the SFT model with vLLM on one workbench, sample n replies per prompt through a tunnel, close. Mac-orchestrated.
# Usage: bash cluster/rlhf_sample.sh <prompts.jsonl> <out samples.jsonl> [partition=debug] [walltime=01:00:00] [n=4]
set -u; cd "$(dirname "$0")/.."; HERE=$PWD; PROMPTS=$1; OUT=$2; PART=${3:-debug}; WALL=${4:-01:00:00}; N=${5:-4}
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; MODEL=$R/eval_copies/R4_full_ep1; LOG=logs/rlhf_sample.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
hours=$(python3 -c "h,m,s='$WALL'.split(':'); print(int(h)+int(m)/60)"); bash cluster/preflight.sh $hours "rlhf_sample" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused"; exit 1; }
W=$(sshc "bash $R/workbench.sh open rlhf_sample $PART $WALL" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED: no workbench [$W]"; exit 1; }; say "workbench $W ($PART $WALL)"
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh R4=$MODEL\" > $R/serve_rlhf.log 2>&1 &"
NODE=""; for k in $(seq 1 20); do NODE=$(sshc "squeue -h -j $W -o %N"); [ -n "$NODE" ] && break; sleep 10; done; say "node $NODE"
ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 clariden & TUN=$!
ok=0; for k in $(seq 1 80); do curl -s -m 10 http://127.0.0.1:8000/v1/models | grep -q '"id"' && { ok=1; break; }; sleep 15; done
[ $ok = 1 ] || { say "FAILED: model did not come up: $(sshc "tail -2 $R/serve_rlhf.log" | tr '\n' ' ' | cut -c1-200)"; kill $TUN; sshc "bash $R/workbench.sh close $W"; exit 1; }
say "endpoint ready; sampling n=$N for $(wc -l < $PROMPTS | tr -d ' ') prompts"
$HOME/Projects/apertus-local-chat/.venv/bin/python data/rlhf/sample.py http://127.0.0.1:8000/v1 R4 $PROMPTS $OUT --n $N --workers 8 2>&1 | tail -3 | tee -a $LOG
kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W rlhf_sample "RLHF sampling window" | tail -1 | tee -a $LOG; say "RLHF_SAMPLE_DONE"
