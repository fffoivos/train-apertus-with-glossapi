#!/usr/bin/env bash
# Q1 (does the MGSM gain come from the 56 embedded-quantitative pairs?) and Q3 (run IPO, finally).
# Six runs inside ONE workbench, sequentially; DPO here is ~6 min a run.
#   NM42/43/44  anchored alpha=0.25 on dpo01_nomaths   (56 embedded-quantitative pairs removed)
#   RC42        the same on dpo01_randomcut            (56 RANDOM pairs removed: the "less data" control)
#   TRUEIPO42/43  loss_type: ipo, beta 10              (the objective the round thought it had tested)
# Every config is identical to G4F6P1_DPO01_05 apart from the file it trains on and the seed, except
# the IPO pair which also changes beta and the objective. Dev is unchanged everywhere.
set -u
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; JOB=$1
ARMS="${ARMS:-NM42 NM43 NM44 RC42 TRUEIPO42 TRUEIPO43}"
FAIL=0
for ARM in $ARMS; do
  d=$R/runs/G4F6P1--DPO01--${ARM}
  if ls -d $d/checkpoint-* >/dev/null 2>&1; then echo "=== skip $ARM (checkpoints exist)"; continue; fi
  echo "=== $ARM start $(date -u +%FT%TZ)"
  bash $R/cluster/dpo01_run.sh $ARM $JOB > /dev/null 2>&1
  line=$(grep -ohE 'DPO_DONE.*' $R/logs/dpo01_${ARM}.out 2>/dev/null | tail -1)
  if [ -z "$line" ]; then echo "  FAILED $ARM"; tail -6 $R/logs/dpo01_${ARM}.out 2>/dev/null; FAIL=$((FAIL+1)); continue; fi
  # Q3 gate: the receipt must show the objective that was ASKED for, not the one the trainer used to force
  lt=$(grep -ohE '"loss_type": *"[a-z_]+"' $R/logs/dpo01_${ARM}.out | tail -1)
  echo "  $(echo "$line" | cut -c1-90)"
  echo "  plan says ${lt:-<loss_type absent from the plan - trainer fix not deployed?>}"
  case "$ARM" in TRUEIPO*) echo "$lt" | grep -q '"ipo"' || { echo "  FAILED $ARM: asked for ipo, plan says $lt"; FAIL=$((FAIL+1)); };; esac
  ls -d $d/checkpoint-* 2>/dev/null | sed 's|.*/|    ckpt |'
done
[ $FAIL -eq 0 ] && echo "Q1Q3_TRAIN_DONE $(date -u +%FT%TZ)" || { echo "Q1Q3_TRAIN_INCOMPLETE: $FAIL failed"; exit 1; }
