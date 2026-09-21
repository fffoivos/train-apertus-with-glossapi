#!/usr/bin/env bash
# Retrain RC44 after its save died mid-write (poison ledger E7), verify the WEIGHT FILES rather than
# the directory, close the allocation whatever happens, and relaunch the 9-model re-score only if the
# checkpoint is genuinely complete.
set -u
R=/iopsstor/scratch/cscs/fffoivos/sft_round1
W=""
cleanup(){ [ -n "$W" ] && { echo "=== closing workbench $W"; bash $R/workbench.sh close "$W" 2>/dev/null | tail -1; scancel "$W" 2>/dev/null; }; }
trap cleanup EXIT

echo "=== removing the broken RC44 run"
rm -rf $R/runs/G4F6P1--DPO01--RC44

W=$(bash $R/workbench.sh open rc44 normal 00:40:00 | tail -1)
echo "workbench=[$W]"
if ! printf '%s' "$W" | grep -qE '^[0-9]+$'; then echo "NO WORKBENCH"; W=""; exit 1; fi

ARMS="RC44" bash $R/cluster/dpo01_q1q3_train.sh "$W" 2>&1 | tail -8

echo "=== completeness check: weight files, not a directory"
d=$R/runs/G4F6P1--DPO01--RC44/checkpoint-108
OK=1
for f in model.safetensors tokenizer.json training_args.bin trainer_state.json config.json; do
  if [ -s "$d/$f" ]; then printf '  ok   %-22s %s\n' "$f" "$(du -h "$d/$f" | cut -f1)"
  else printf '  MISS %s\n' "$f"; OK=0; fi
done
if ls "$d"/.tmp* >/dev/null 2>&1; then echo "  LEFTOVER .tmp present"; OK=0; fi
if cmp -s "$d/tokenizer.json" $R/eval_copies/R4_full_ep1/tokenizer.json; then echo "  ok   tokenizer byte-matches parent"
else echo "  MISS tokenizer differs from parent"; OK=0; fi

cleanup; W=""
sleep 8
[ "$OK" -eq 1 ] || { echo "RC44 STILL BROKEN - eval NOT relaunched"; exit 1; }
echo "=== relaunching 9-model re-score"
cd $R && LIST=$R/cluster/eval_jobs/dpo01_q1q3_models.txt EXPECT=9 sbatch $R/cluster/eval_jobs/dpo01_frozen_rescore.sh
