#!/bin/bash
# Finish the pilot after the KeyError crash (edit_pass guard assumed meta.constraints): resume both correction passes with small batches
# (long dialogues timed out at batch 15), merge, then the standing-rule astra review. Run under nohup from data/.
cd "$(dirname "$0")/.." || exit 1; LOG=convskills/v1/finish_pilot.log
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
say "finish_pilot2: resuming corrections at batch 5"
WORKERS=24 BATCH=5 python3 edit_pass.py convskills/v1/convskills_sft.jsonl convskills/v1/edited --kind if >> "$LOG" 2>&1; say "main lanes: $(cat convskills/v1/edited/summary.json 2>/dev/null)"
WORKERS=24 BATCH=5 python3 edit_pass.py convskills/v1/convskills_sft_extra.jsonl convskills/v1/edited_extra --kind if >> "$LOG" 2>&1; say "extra lanes: $(cat convskills/v1/edited_extra/summary.json 2>/dev/null)"
cat convskills/v1/edited/rows_edited.jsonl convskills/v1/edited_extra/rows_edited.jsonl > convskills/v1/rows_all.jsonl; say "rows_all: $(wc -l < convskills/v1/rows_all.jsonl) rows"
say "astra review start"; python3 review_astra.py convskills_pilot ../docs/reviews/briefs/astra_convskills_pilot.md ../docs/reviews/ASTRA_convskills_pilot_20260910.md --rows convskills/v1/rows_all.jsonl --n 60 --seed 1 --fields id,turns,meta,edit_changes >> "$LOG" 2>&1; say "astra review done: $(wc -c < ../docs/reviews/ASTRA_convskills_pilot_20260910.md 2>/dev/null) chars"
