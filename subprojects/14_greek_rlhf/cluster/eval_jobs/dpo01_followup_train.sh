#!/bin/bash
# All non-IPO follow-up arms, back to back inside ONE allocation (owner: use salloc, do not lose the
# node between runs). The IPO arm is NOT here: it is gated on review R-DPO5.
#   bash dpo01_followup_train.sh <JOBID>
set -u
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; JOB=$1
for ARM in 07 05s43 01s43 08 BAL; do
  d=$R/runs/G4F6P1--DPO01--${ARM}
  if ls -d $d/checkpoint-* >/dev/null 2>&1; then echo "=== skip $ARM (checkpoints exist) ==="; continue; fi
  echo "=== arm $ARM start $(date -u +%FT%TZ) ==="
  bash $R/cluster/dpo01_run.sh $ARM $JOB
  grep -ohE 'DPO_DONE.*' $R/logs/dpo01_${ARM}.out 2>/dev/null | tail -1 | cut -c1-240
  ls -d $d/checkpoint-* 2>/dev/null | sed 's|.*/|  ckpt |'
done
echo "FOLLOWUP_TRAIN_DONE $(date -u +%FT%TZ)"
