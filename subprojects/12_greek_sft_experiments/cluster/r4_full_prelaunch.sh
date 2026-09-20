#!/usr/bin/env bash
# Pre-launch for the from-scratch pass: wait for the blind solve, finalize the label check, assemble R4_full, fill the config, upload + trainer dry-run, preflight,
# recipe table, astra gate-2 review. Stops before the launch (the launch is a separate command). Fail-closed. Usage: bash cluster/r4_full_prelaunch.sh
set -u -o pipefail; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=results/R4_full; mkdir -p $OUT
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] prelaunch: $*"; }
say "waiting for the independent solve"; until grep -q "written final/label_disagreements.json\|^STOP:" logs/independent_solve.log 2>/dev/null || ! pgrep -f independent_solve.py >/dev/null; do sleep 60; done
grep -q "^STOP:" logs/independent_solve.log && say "NOTE: the solve stopped at the meter ceiling; unsolved problems are dropped"
$PY data/math/cut2/finalize_label_check.py | tail -1 | tee $OUT/label_check.txt
say "assembling R4_full"; $PY data/assemble_full_r4.py --arm R4_full > $OUT/assemble.log 2>&1 || { say "FAILED: assembly: $(tail -3 $OUT/assemble.log | tr '\n' ' ' | cut -c1-400)"; exit 1; }; tail -2 $OUT/assemble.log | cut -c1-400
ROWS=$(wc -l < data/arms/R4_full/train.jsonl | tr -d ' '); sed -i '' "s/^expected_train_rows: .*/expected_train_rows: $ROWS/" cluster/configs/R4_full.yaml; say "config rows $ROWS"
say "upload + trainer dry-run"; sshc "mkdir -p $R/data/arms/R4_full"; scp -4 -q data/arms/R4_full/train.jsonl data/arms/R4_full/dev.jsonl clariden:$R/data/arms/R4_full/ && scp -4 -q cluster/configs/R4_full.yaml clariden:$R/cluster/configs/R4_full.yaml || { say "FAILED: upload"; exit 1; }
[ "$(sshc "cd $R && md5sum data/arms/R4_full/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/R4_full/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch"; exit 1; }; say "md5 verified"
sshc "cd $R && uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_DATASETS_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft5/bin/activate; python cluster/sft_train.py --config cluster/configs/R4_full.yaml --dry-run'" > $OUT/dryrun.log 2>&1
grep -q DRY_RUN_OK $OUT/dryrun.log || { say "FAILED: dry-run: $(tail -3 $OUT/dryrun.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }; say "dry-run OK: $(grep -oE 'PLAN \{.*\}' $OUT/dryrun.log | cut -c1-300)"
bash cluster/preflight.sh 7 "R4_full_train" | tail -1 > $OUT/preflight.txt; cat $OUT/preflight.txt; grep -q '^OK' $OUT/preflight.txt || { say "FAILED: preflight refused"; exit 1; }
python3 data/recipe_table_r4_full.py | tail -1; python3 data/make_gate2_brief.py || { say "FAILED: brief"; exit 1; }
say "astra gate-2 review"; python3 data/review_astra.py gate2_full docs/reviews/briefs/astra_gate2_full.md docs/reviews/ASTRA_gate2_full_20260915.md --model gpt-6-astra --effort xhigh > logs/astra_gate2_full.log 2>&1 || { say "FAILED: review call"; exit 1; }
say "verdict: $(grep -m1 -i 'verdict' docs/reviews/ASTRA_gate2_full_20260915.md | cut -c1-300)"; say "PRELAUNCH_DONE"
