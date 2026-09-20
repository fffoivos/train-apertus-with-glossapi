#!/usr/bin/env bash
# After the cut-2 rerun (escape repair): re-assemble the arms, check, upload, dry-run, preflight, build the evidence pack and run astra's third gate-1 review. Fail-closed.
set -u -o pipefail; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; OUT=results/pilots; mkdir -p $OUT
say(){ echo "[$(date '+%m-%d %H:%M')] post_repair: $*"; }
grep -q RERUN_DONE logs/cut2_rerun_after_repair.log || { say "FAILED: the rerun chain did not finish (no RERUN_DONE)"; exit 1; }
grep "rows with C0 controls" logs/cut2_rerun_after_repair.log | tail -1 > $OUT/ctrl_audit.txt; cat $OUT/ctrl_audit.txt
say "assembling arms"; bash cluster/drivers/assemble_pilots.sh > $OUT/assemble_after_repair.log 2>&1; grep -q ASSEMBLE_PILOTS_DONE $OUT/assemble_after_repair.log || { say "FAILED: assembly ($(grep -E 'FAIL|exit' $OUT/assemble_after_repair.log | tail -2 | tr '\n' ' ' | cut -c1-300))"; exit 1; }
say "arms: $(grep -E 'rows|tokens' $OUT/assemble_after_repair.log | tail -3 | tr '\n' ' ' | cut -c1-300)"
say "upload + dry-runs"; bash cluster/drivers/dryrun_pilots.sh M0 M1 M2 || { say "FAILED: dry-runs"; exit 1; }
bash cluster/preflight.sh 4.5 "pilots_M0_M1_M2" | tail -1 > $OUT/preflight.txt; cat $OUT/preflight.txt; grep -q '^OK' $OUT/preflight.txt || { say "FAILED: preflight refused"; exit 1; }
say "evidence pack"; python3 data/make_gate1_brief.py || { say "FAILED: brief"; exit 1; }
say "astra review R3c (gpt-6-astra, xhigh)"; python3 data/review_astra.py gate1_pilots_v3 docs/reviews/briefs/astra_gate1_pilots_v3.md docs/reviews/ASTRA_gate1_pilots_v3_20260914.md --model gpt-6-astra --effort xhigh > logs/astra_gate1_review3.log 2>&1 || { say "FAILED: review call ($(tail -2 logs/astra_gate1_review3.log | tr '\n' ' ' | cut -c1-200))"; exit 1; }
say "review verdict: $(grep -m1 -i 'Verdict' docs/reviews/ASTRA_gate1_pilots_v3_20260914.md | cut -c1-300)"
say "POST_REPAIR_DONE"
