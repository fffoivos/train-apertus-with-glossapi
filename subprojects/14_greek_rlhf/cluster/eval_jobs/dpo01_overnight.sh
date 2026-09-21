#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_night
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=11:45:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_night_%j.out
# Overnight chain: finish the measurement programme already in flight. Nothing new.
# Every stage is independently resumable (each skips models that already have results), so a
# walltime cut or a resubmit costs nothing. Stages run in priority order: the lm_eval lane carries
# the primary endpoint and the noise floor, so it goes first.
set -uo pipefail
R=/iopsstor/scratch/cscs/fffoivos/sft_round1
echo "NIGHT start $(date -u +%FT%TZ)"

echo "=== S1: lm_eval lane (IFEval 541, MGSM 250, Global-MMLU) ==="
bash $R/cluster/eval_jobs/dpo01_full.sh
echo "S1 done $(date -u +%FT%TZ): $(find $R/results/G4F6P1--DPO01/full -name 'results_*.json' | wc -l) models"

echo "=== S2: GreekMMLU 250 ==="
bash $R/cluster/eval_jobs/dpo01_greekmmlu.sh
echo "S2 done $(date -u +%FT%TZ): $(find $R/results/G4F6P1--DPO01/greekmmlu -name 'receipt.json' | wc -l) models"

echo "=== S3: generation_config control ==="
bash $R/cluster/eval_jobs/dpo01_gencfg_control.sh
echo "S3 done $(date -u +%FT%TZ)"

echo "NIGHT_DONE $(date -u +%FT%TZ)"
