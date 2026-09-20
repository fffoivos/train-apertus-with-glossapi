#!/usr/bin/env bash
# Pre-launch v13 for the from-scratch pass (after astra gate-2 v12 HOLD). Stage local: comparator self-tests, fingerprint backfill (idempotent), finalize, label-check delta,
# format-block rebuild, assemble (writes expected_train_rows), recipe. Stage cluster: upload (manifest, config, trainer, scripts), in parallel {trainer dry-run, rendered lengths,
# label audits (a) launch/4 rows (b) launch/40 exposure rows (c) raw path/40 rows expect-deficit}, validator inspection, preflight, brief, THIRTEENTH astra review. Stops before the launch.
# Usage: bash cluster/r4_full_prelaunch_v13.sh local|cluster|all
set -u -o pipefail; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=results/R4_full; mkdir -p $OUT
PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] prelaunch13: $*"; }
ENV="export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_DATASETS_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft5/bin/activate"
remote(){ sshc "cd $R && uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc '$ENV; $1'"; }
STAGE=${1:-all}
if [ "$STAGE" = local ] || [ "$STAGE" = all ]; then
  say "self-tests"; $PY data/math/cut2/labelcheck_lib.py --selftest || { say "FAILED: comparator self-tests"; exit 1; }
  say "fingerprint backfill"; $PY data/math/cut2/backfill_solve_fingerprints.py | tail -1 || { say "FAILED: backfill"; exit 1; }
  cp data/math/cut2/final/label_disagreements.json $OUT/label_disagreements_prev.json
  say "finalize"; $PY data/math/cut2/finalize_label_check.py > $OUT/label_check.txt 2>&1 || { say "FAILED: finalize: $(tail -2 $OUT/label_check.txt | tr '\n' ' ' | cut -c1-300)"; exit 1; }; sed -n '2,3p' $OUT/label_check.txt | cut -c1-400
  $PY data/math/cut2/label_check_delta.py $OUT/label_disagreements_prev.json data/math/cut2/final/label_disagreements.json $OUT/label_check_delta.json | head -8
  $PY data/math/cut2/label_delta_pairs.py $OUT/label_disagreements_v5.json data/math/cut2/final/label_disagreements.json $OUT/label_check_delta_vs_v7.json $OUT/label_check_delta_vs_v7_pairs.txt | tail -1
  say "format block rebuild"; (cd data/format_block && $PY build_mc_fewshot.py 2>&1 | tail -1 | cut -c1-300) || { say "FAILED: format block"; exit 1; }
  say "assembling R4_full"; $PY data/assemble_full_r4.py --arm R4_full > $OUT/assemble.log 2>&1 || { say "FAILED: assembly: $(tail -3 $OUT/assemble.log | tr '\n' ' ' | cut -c1-400)"; exit 1; }; tail -2 $OUT/assemble.log | cut -c1-400
  ROWS=$(wc -l < data/arms/R4_full/train.jsonl | tr -d ' '); grep -q "^expected_train_rows: $ROWS$" cluster/configs/R4_full.yaml || { say "FAILED: config rows not written by the assembler"; exit 1; }; say "config rows $ROWS (written by the assembler)"
  python3 data/recipe_table_r4_full.py | tail -1 | cut -c1-200
  say "cohort + exposure from the final manifest"; $PY data/select_deficit_sample.py | tail -1 || { say "FAILED: cohort"; exit 1; }; $PY data/byte_exposure.py | tail -1 || { say "FAILED: exposure"; exit 1; }
  say "LOCAL_DONE"
fi
if [ "$STAGE" = cluster ] || [ "$STAGE" = all ]; then
  say "upload"; sshc "mkdir -p $R/data/arms/R4_full" || { say "FAILED: ssh (certificate?)"; exit 1; }
  scp -4 -q data/arms/R4_full/train.jsonl data/arms/R4_full/dev.jsonl clariden:$R/data/arms/R4_full/ && scp -4 -q cluster/configs/R4_full.yaml clariden:$R/cluster/configs/R4_full.yaml && scp -4 -q cluster/sft_train.py cluster/rendered_lengths.py cluster/inspect_trl_labels.py cluster/inspect_labels.py clariden:$R/cluster/ || { say "FAILED: upload"; exit 1; }
  [ "$(sshc "cd $R && md5sum data/arms/R4_full/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/R4_full/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch"; exit 1; }; say "md5 verified"
  IDS=$(cat $OUT/deficit_sample_ids.txt)
  remote "python cluster/sft_train.py --config cluster/configs/R4_full.yaml --dry-run 2>&1" > $OUT/dryrun.log & D1=$!
  remote "python cluster/rendered_lengths.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl --dev data/arms/R4_full/dev.jsonl 2>/dev/null" | grep -oE 'RENDERED_LENGTHS \{.*\}' | cut -c18- > $OUT/rendered_lengths.json & D2=$!
  remote "python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_launch4.txt & D3=$!
  remote "python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl --ids $IDS 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_launch40.txt & D4=$!
  remote "sed /^pretokenized_masks/d cluster/configs/R4_full.yaml > /tmp/R4_full_raw.yaml; python cluster/inspect_trl_labels.py --config /tmp/R4_full_raw.yaml --train data/arms/R4_full/train.jsonl --ids $IDS --expect-deficit 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_raw40.txt & D5=$!
  remote "python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl --expect-deficit 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_negcontrol.txt & D6=$!
  say "dry-run, rendered lengths and three label audits and the negative control running in parallel on the login node"; wait $D1 $D2 $D3 $D4 $D5 $D6
  grep -q DRY_RUN_OK $OUT/dryrun.log || { say "FAILED: dry-run: $(tail -3 $OUT/dryrun.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }; say "dry-run OK: $(grep -oE 'PLAN \{.*\}' $OUT/dryrun.log | cut -c1-300)"
  grep -q '"max"' $OUT/rendered_lengths.json || { say "FAILED: rendered lengths"; exit 1; }; say "rendered lengths: $(python3 -c "import json; d=json.load(open('$OUT/rendered_lengths.json')); print('train max', d['train']['max'], 'over', d['train']['over_max_length'], 'p99', d['train']['p99'], '| dev max', d['dev']['max'], 'over', d['dev']['over_max_length'])")"
  grep -q 'TRL_LABELS_CHECK OK' $OUT/trl_audit_launch4.txt || { say "FAILED: audit (a): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_launch4.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (a): $(grep TRL_LABELS_CHECK $OUT/trl_audit_launch4.txt | cut -c1-200)"
  grep -q 'TRL_LABELS_CHECK OK' $OUT/trl_audit_launch40.txt || { say "FAILED: audit (b): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_launch40.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (b): $(grep TRL_LABELS_CHECK $OUT/trl_audit_launch40.txt | cut -c1-200)"
  grep -q 'TRL_LABELS_CHECK DEFICIT' $OUT/trl_audit_raw40.txt || { say "FAILED: audit (c): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_raw40.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (c): $(grep TRL_LABELS_CHECK $OUT/trl_audit_raw40.txt | cut -c1-250)"
  grep -q 'TRL_LABELS_CHECK FAIL (deficit mode)' $OUT/trl_audit_negcontrol.txt || { say "FAILED: negative control did not fail: $(grep TRL_LABELS_CHECK $OUT/trl_audit_negcontrol.txt | cut -c1-200)"; exit 1; }; say "audit (d) negative control: $(grep TRL_LABELS_CHECK $OUT/trl_audit_negcontrol.txt | cut -c1-160)"
  remote "python cluster/inspect_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl 2>/dev/null" | grep -v "rope_parameters" > $OUT/labels_inspection.txt; say "label inspection: $(grep -c "^===" $OUT/labels_inspection.txt) rows inspected"
  bash cluster/preflight.sh 7 "R4_full_train" | tail -1 > $OUT/preflight.txt; cat $OUT/preflight.txt; grep -q '^OK' $OUT/preflight.txt || { say "FAILED: preflight refused"; exit 1; }
  python3 data/make_gate2_brief.py || { say "FAILED: brief"; exit 1; }
  say "astra gate-2 review (thirteenth)"; python3 data/review_astra.py gate2_full_v13 docs/reviews/briefs/astra_gate2_full_v13.md docs/reviews/ASTRA_gate2_full_v13_20260915.md --model gpt-6-astra --effort xhigh > logs/astra_gate2_full_v13.log 2>&1 || { say "FAILED: review: $(tail -2 logs/astra_gate2_full_v13.log | tr '\n' ' ' | cut -c1-200)"; exit 1; }
  say "verdict: $(grep -m1 -A2 -i '## 1. Verdict' docs/reviews/ASTRA_gate2_full_v13_20260915.md | tail -1 | cut -c1-300)"; say "PRELAUNCH_DONE"
fi
if [ "$STAGE" = resume ]; then   # after a failed audit: scripts re-uploaded, audits re-run in parallel, then inspection, preflight, brief, review (dry-run + rendered lengths of THIS manifest must already be OK)
  grep -q DRY_RUN_OK $OUT/dryrun.log && [ $OUT/dryrun.log -nt data/arms/R4_full/train.jsonl ] && grep -q '"max"' $OUT/rendered_lengths.json && [ $OUT/rendered_lengths.json -nt data/arms/R4_full/train.jsonl ] || { say "FAILED: resume needs DRY_RUN_OK and rendered lengths newer than the manifest"; exit 1; }
  scp -4 -q cluster/inspect_trl_labels.py cluster/inspect_labels.py clariden:$R/cluster/ || { say "FAILED: script upload"; exit 1; }; say "scripts uploaded; dry-run and rendered lengths already OK for this manifest"
  IDS=$(cat $OUT/deficit_sample_ids.txt)
  remote "python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_launch4.txt & D3=$!
  remote "python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl --ids $IDS 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_launch40.txt & D4=$!
  remote "sed /^pretokenized_masks/d cluster/configs/R4_full.yaml > /tmp/R4_full_raw.yaml; python cluster/inspect_trl_labels.py --config /tmp/R4_full_raw.yaml --train data/arms/R4_full/train.jsonl --ids $IDS --expect-deficit 2>&1 | grep -v rope_parameters | grep -vE \"^(Tokenizing|Building|Packing|Truncating|Dropping|\\[RANK|Warning)\"" > $OUT/trl_audit_raw40.txt & D5=$!
  say "three label audits running in parallel on the login node"; wait $D3 $D4 $D5
  grep -q 'TRL_LABELS_CHECK OK' $OUT/trl_audit_launch4.txt || { say "FAILED: audit (a): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_launch4.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (a): $(grep TRL_LABELS_CHECK $OUT/trl_audit_launch4.txt | cut -c1-200)"
  grep -q 'TRL_LABELS_CHECK OK' $OUT/trl_audit_launch40.txt || { say "FAILED: audit (b): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_launch40.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (b): $(grep TRL_LABELS_CHECK $OUT/trl_audit_launch40.txt | cut -c1-200)"
  grep -q 'TRL_LABELS_CHECK DEFICIT' $OUT/trl_audit_raw40.txt || { say "FAILED: audit (c): $(grep -E 'TRL_LABELS_CHECK|AUDIT|Traceback|Error' $OUT/trl_audit_raw40.txt | tail -3 | cut -c1-300)"; exit 1; }; say "audit (c): $(grep TRL_LABELS_CHECK $OUT/trl_audit_raw40.txt | cut -c1-250)"
  remote "python cluster/inspect_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl 2>/dev/null" | grep -v "rope_parameters" > $OUT/labels_inspection.txt; say "label inspection: $(grep -c "^===" $OUT/labels_inspection.txt) rows inspected"
  bash cluster/preflight.sh 7 "R4_full_train" | tail -1 > $OUT/preflight.txt; cat $OUT/preflight.txt; grep -q '^OK' $OUT/preflight.txt || { say "FAILED: preflight refused"; exit 1; }
  python3 data/make_gate2_brief.py || { say "FAILED: brief"; exit 1; }
  say "astra gate-2 review (thirteenth)"; python3 data/review_astra.py gate2_full_v13 docs/reviews/briefs/astra_gate2_full_v13.md docs/reviews/ASTRA_gate2_full_v13_20260915.md --model gpt-6-astra --effort xhigh > logs/astra_gate2_full_v13.log 2>&1 || { say "FAILED: review: $(tail -2 logs/astra_gate2_full_v13.log | tr '\n' ' ' | cut -c1-200)"; exit 1; }
  say "verdict: $(grep -m1 -A2 -i '## 1. Verdict' docs/reviews/ASTRA_gate2_full_v13_20260915.md | tail -1 | cut -c1-300)"; say "PRELAUNCH_DONE"
fi
