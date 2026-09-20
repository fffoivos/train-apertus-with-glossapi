#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_alpha
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=01:30:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_alpha_%j.out
# Anchor dose-response at lr 2e-6: alpha 0.1 / 0.25 / 0.5, everything else identical to arm 03.
# Endpoints already trained: alpha 0 = arm 01, alpha 1.0 = arm 03.
set -u
R=/iopsstor/scratch/cscs/fffoivos/sft_round1
for ARM in 04 05 06; do
  a=$(grep -oP 'chosen_nll_alpha: \K\S+' $R/cluster/configs/G4F6P1_DPO01_${ARM}.yaml)
  echo "=== arm $ARM (alpha $a) start $(date -u +%FT%TZ) ==="
  bash $R/cluster/dpo01_run.sh $ARM $SLURM_JOB_ID
  echo "--- arm $ARM receipt ---"
  grep -ohE 'DPO_DONE.*' $R/logs/dpo01_${ARM}.out | tail -1 | cut -c1-300
  ls -d $R/runs/G4F6P1--DPO01--${ARM}/checkpoint-* 2>/dev/null | sed 's|.*/|  ckpt |'
done
echo "ALPHA_SWEEP_DONE $(date -u +%FT%TZ)"
