#!/usr/bin/env bash
# The owner's queue (9 September): after the IF generation completes → merge v1+v2 → Greek correction pass on ALL IF rows;
# after the math build completes → Greek correction pass on ALL math rows. Polls every 5 minutes; every step is resumable. Run under nohup.
set -u; cd "$(dirname "$0")"; LOG=queue_runner.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
wait_for(){ local f=$1 pat=$2; while ! grep -q "$pat" "$f" 2>/dev/null; do sleep 300; done; }
say "queue started: waiting for IF v2"
wait_for greek_if/v2/run.log 'GENERATION DONE'; say "IF v2 done → merge"
[ -s greek_if/v1v2/summary.json ] || python3 greek_if/merge_versions.py greek_if/v1v2 greek_if/v1 greek_if/v2 | tee -a "$LOG"
say "correction pass on IF ($(wc -l < greek_if/v1v2/greek_if_sft.jsonl) rows)"
WORKERS=24 python3 edit_pass.py greek_if/v1v2/greek_if_sft.jsonl greek_if/v1v2/edited --kind if >> "$LOG" 2>&1; say "IF correction done: $(cat greek_if/v1v2/edited/summary.json 2>/dev/null)"
say "waiting for the math build"
wait_for math/cut1/build.log 'MATH BUILD DONE'; say "math build done → correction pass ($(wc -l < math/cut1/out/greek_math_sft.jsonl) rows)"
WORKERS=24 python3 edit_pass.py math/cut1/out/greek_math_sft.jsonl math/cut1/edited --kind math >> "$LOG" 2>&1; say "math correction done: $(cat math/cut1/edited/summary.json 2>/dev/null)"
say "QUEUE DONE"
