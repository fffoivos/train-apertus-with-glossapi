#!/usr/bin/env bash
# Part B of EVALUATION_PLAN_20260904: GreekMMLU (frozen fp32 scorer) on four models, one per GPU, one normal-partition workbench (~3 h).
# Owner notice for the >2 h job: EVALUATION_PLAN_20260904.md Part B ("the evaluations are in", 2026-09-04). Usage: bash cluster/greekmmlu_batch.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd); cd "$HERE"
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; HUB=$R/hf_home/hub
sshc() { ssh -o BatchMode=yes clariden "$@" 2>&1 | grep -v "WARNING\|store now\|openssh" || true; }
bash cluster/preflight.sh 3.4 greekmmlu_batch | tail -2 | grep -q '^OK' || { echo "preflight refused"; exit 1; }
J=$(sshc "bash $R/workbench.sh open greekmmlu normal 03:20:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { echo "open failed: $J"; exit 1; }
echo "workbench $J"; echo "$J" > results/.greekmmlu_job
gpu=0
while read -r L CK; do
  sshc "mkdir -p $R/evals/$L/logs; nohup srun --jobid=$J --overlap --ntasks=1 --cpus-per-task=64 --gpus-per-node=4 --export=ALL bash -c 'MODEL=$CK LABEL=$L GPU=$gpu bash $R/cluster/eval_jobs/greekmmlu.sh' > $R/evals/$L/logs/greekmmlu_lane.log 2>&1 &"
  echo "lane $L gpu $gpu"; gpu=$((gpu+1))
done <<LANES
E1_lr1e-5_ep2 $R/eval_copies/E1_lr1e-5_ep2
E3_cos_ep2 $R/eval_copies/E3_cos_ep2
peer_krikri $HUB/models--ilsp--Llama-Krikri-8B-Instruct/snapshots/06d813157ba5f19deb17d70c3862ce64035431ec
peer_apertus_instruct $HUB/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f
LANES
printf "| $(date '+%Y-%m-%d %H:%M') | eval plan | B | claude | GreekMMLU batch launched on normal wb $J (pick, adapted imports, Krikri-Instruct, Apertus-Instruct) | 3.3 proj | — |\n" >> EXECUTION_LOG.md
