#!/usr/bin/env bash
# Part A of EVALUATION_PLAN_20260904: Greek IFEval + Greek MGSM on four peer models, one per GPU, in one debug workbench.
# Runs on the Mac; ships commands to the login node. Usage: bash cluster/peer_ilsp.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd); cd "$HERE"
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; HUB=$R/hf_home/hub
declare -A M=(
 [peer_krikri]=$HUB/models--ilsp--Llama-Krikri-8B-Instruct/snapshots/06d813157ba5f19deb17d70c3862ce64035431ec
 [peer_meltemi]=$HUB/models--ilsp--Meltemi-7B-Instruct-v1.5/snapshots/77d7fa68ee9f9c0addf6ed93acdc32ebafde9394
 [peer_apertus_instruct]=$HUB/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f
 [peer_gemma3_12b]=$HUB/models--google--gemma-3-12b-it/snapshots/96b6f1eccf38110c56df3a15bffe176da04bfd80
)
sshc() { ssh -n -o BatchMode=yes clariden "$@" 2>&1 | grep -v "WARNING\|store now\|openssh" || true; }
bash cluster/preflight.sh 1.2 peer_ilsp | tail -2
J=$(sshc "bash $R/workbench.sh open peer_ilsp debug 01:29:00" | tail -1); echo "workbench $J"; echo "$J" > results/.peer_ilsp_job
gpu=0
for L in peer_krikri peer_meltemi peer_apertus_instruct peer_gemma3_12b; do
  CK=${M[$L]}; EV=$R/evals/$L; 
  sshc "mkdir -p $EV/ilsp $EV/logs; nohup srun --jobid=$J --overlap --ntasks=1 --cpus-per-task=64 --gpus-per-node=4 --export=ALL bash -c 'export CUDA_VISIBLE_DEVICES=$gpu HF_HOME=$R/hf_home HF_HUB_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); cd $R/evals_code; uenv run --view=default pytorch/v2.9.1:v2 -- bash -c \"export PYTHONPATH=$S/python_envs/lm_eval; python3 -m lm_eval --model hf --model_args pretrained=$CK,dtype=bfloat16 --tasks ifeval_greek,mgsm_greek --apply_chat_template --include_path $R/evals_code/ilsp/tasks --batch_size 32 --output_path $EV/ilsp/ --log_samples\"' > $EV/logs/ilsp.log 2>&1 &"
  echo "lane $L on gpu $gpu"; gpu=$((gpu+1))
done
