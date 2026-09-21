#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_night2
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=11:45:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_night2_%j.out
# Plan: docs/RLHF_COORDINATION/OVERNIGHT_20260918.md
# Replication first, because it is what makes every other result readable. Every stage skips work
# that already has results, so the chain restarts cleanly and a walltime cut costs nothing.
set -uo pipefail
R=/iopsstor/scratch/cscs/fffoivos/sft_round1
echo "NIGHT2 start $(date -u +%FT%TZ)"
echo "=== T1: replication set ==="
for ARM in 01s44 01s45 01s46 05s44 05s45 05s46 IPO42 IPO43 BALs43 BALs44; do
  if ls -d $R/runs/G4F6P1--DPO01--${ARM}/checkpoint-* >/dev/null 2>&1; then echo "  skip $ARM"; continue; fi
  echo "  === $ARM $(date -u +%FT%TZ) ==="
  bash $R/cluster/dpo01_run.sh $ARM $SLURM_JOB_ID
  grep -ohE 'DPO_DONE.*' $R/logs/dpo01_${ARM}.out 2>/dev/null | tail -1 | cut -c1-200
done
echo "T1 done $(date -u +%FT%TZ)"
for stage in full served greekmmlu gencfg_control; do
  echo "=== $stage $(date -u +%FT%TZ) ==="
  bash $R/cluster/eval_jobs/dpo01_${stage}.sh
done
echo "NIGHT2_DONE $(date -u +%FT%TZ)"
