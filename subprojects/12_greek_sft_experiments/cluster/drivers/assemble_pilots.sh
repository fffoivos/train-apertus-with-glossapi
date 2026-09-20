#!/usr/bin/env bash
# Assemble the three pilot arms (G4F6P0--00/--01/--02 = M0/M1/M2) from the strict cut-2 export, then run the final-manifest checker. Fail-closed.
# Prerequisites: data/math/cut2/final/arm_M{0,1,2}.jsonl + dev_problems_en.json (strict assembly), data/cache/evals/math200_confirm.jsonl (confirmation set built).
set -u -o pipefail; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=results/pilots/assemble.log; mkdir -p results/pilots
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
for f in data/math/cut2/final/arm_M0.jsonl data/math/cut2/final/arm_M1.jsonl data/math/cut2/final/arm_M2.jsonl data/math/cut2/final/dev_problems_en.json data/cache/evals/math200_confirm.jsonl data/math/en/gsm8k_dedup3.jsonl data/math/en/math_train_published.jsonl; do [ -s $f ] || { say "FAILED: missing $f"; exit 1; }; done
[ -f data/math/cut2/final/_incomplete_receipt.json ] && [ data/math/cut2/final/_incomplete_receipt.json -nt data/math/cut2/final/receipt.json ] && { say "FAILED: the last cut-2 assembly was refused as incomplete"; exit 1; }
EN="--block math_en_gsm=data/math/en/gsm8k_dedup3.jsonl:openmath:1 --block math_en_math=data/math/en/math_train_published.jsonl:openmath:2"
for A in M0 M1 M2; do
  $PY data/assemble_continuation.py --arm $A --parent data/arms/R2_stage1/train.jsonl --replay-frac 0.10 --exclude-replay openmath_gsm --dev-problems data/math/cut2/final/dev_problems_en.json $EN --block greek_math=data/math/cut2/final/arm_$A.jsonl:ua:1 --seed 42 > results/pilots/assemble_$A.log 2>&1 || { say "FAILED: assembly $A: $(tail -2 results/pilots/assemble_$A.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }
  say "$A assembled: $(tail -1 results/pilots/assemble_$A.log | cut -c1-200)"
done
python3 data/check_pilot_arms.py M0 M1 M2 > results/pilots/check_arms.log 2>&1; rc=$?; say "final-manifest check exit $rc: $(grep -E 'RESULT|FAIL' results/pilots/check_arms.log | tr '\n' ' ' | cut -c1-300)"; [ $rc -eq 0 ] || exit 1
python3 - <<'PY'
import json, hashlib
reg = json.load(open('data/gfp_registry.json'))
for leg in ('M0', 'M1', 'M2'):
    rc = json.load(open(f'data/arms/{leg}/receipt.json'))
    for e in reg['entries']:
        if e['legacy_run'] == leg: e['bound_manifest_sha256'] = rc['train']['sha256']; e['status'] = 'bound_to_frozen_manifest'; e['train_rows'] = rc['train']['rows']; e['supervised_tokens'] = rc['train']['supervised_tokens']
json.dump(reg, open('data/gfp_registry.json', 'w'), indent=1, ensure_ascii=False); print('G/F/P names bound to the frozen manifests')
PY
say "ASSEMBLE_PILOTS_DONE"
