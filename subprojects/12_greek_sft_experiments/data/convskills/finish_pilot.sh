#!/bin/bash
# After queue 2: correct the two lanes the assembly glob missed (S3c, S5m), merge all edited rows, then run the standing-rule astra review of the pilot.
cd "$(dirname "$0")/.." || exit 1; LOG=convskills/v1/finish_pilot.log
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
say "waiting for QUEUE2 DONE"; until grep -q 'QUEUE2 DONE' queue_runner2.log 2>/dev/null; do sleep 120; done
python3 - <<'PY' >> "$LOG" 2>&1
import json
rows = [json.loads(l) for f in ('convskills/v1/S3c.jsonl', 'convskills/v1/S5m.jsonl') for l in open(f)]
keep = [r for r in rows if r['verified']]
with open('convskills/v1/convskills_sft_extra.jsonl', 'w') as f:
    for r in keep: f.write(json.dumps(dict(source='convskills', bucket=r['lane'], id=r['id'], user=r['turns'][-2]['content'], assistant=r['turns'][-1]['content'], turns=r['turns'], n_turns=len(r['turns']), verified='regex', meta=dict(lane=r['lane'], kind=r['kind'])), ensure_ascii=False) + '\n')
print('extra rows', len(keep), 'of', len(rows))
PY
say "correction pass on the extra lanes"; WORKERS=24 python3 edit_pass.py convskills/v1/convskills_sft_extra.jsonl convskills/v1/edited_extra --kind if >> "$LOG" 2>&1
cat convskills/v1/edited/rows_edited.jsonl convskills/v1/edited_extra/rows_edited.jsonl > convskills/v1/rows_all.jsonl; say "rows_all: $(wc -l < convskills/v1/rows_all.jsonl) rows; extra summary: $(cat convskills/v1/edited_extra/summary.json)"
say "astra review start"; python3 review_astra.py convskills_pilot ../docs/reviews/briefs/astra_convskills_pilot.md ../docs/reviews/ASTRA_convskills_pilot_20260910.md --rows convskills/v1/rows_all.jsonl --n 60 --seed 1 --fields id,turns,meta,edit_changes >> "$LOG" 2>&1; say "astra review done: $(wc -c < ../docs/reviews/ASTRA_convskills_pilot_20260910.md) chars"
