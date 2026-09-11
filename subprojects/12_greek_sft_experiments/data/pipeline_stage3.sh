#!/bin/zsh
# Stage 3 (after the suite lanes finish): editor passes — correcting rows (kind dialogue, 24 workers) then the suite v2 rows (kind if, 48 workers),
# then the suite's post-edit re-verification. Reviews are launched by Claude.
cd "$(dirname "$0")"; LOG=pipeline_sequence.log; say() { echo "$(date '+%F %H:%M') $*" >> $LOG; }; PY=~/venvs/sftdata/bin/python
while pgrep -f '[g]en_suite.py v2' > /dev/null || pgrep -f '[r]un_scale.sh' > /dev/null; do sleep 120; done
say "stage 3a: suite lanes done; editor pass on the correcting rows (600, 24 workers)"
WORKERS=24 $PY edit_pass.py robustness/correcting/scale/rows/rows.jsonl robustness/correcting/scale/rows/edited --kind dialogue --model gpt-5.6-sol --effort medium >> robustness/correcting/scale/edit.log 2>&1
say "stage 3a done: $(cat robustness/correcting/scale/rows/edited/summary.json 2>/dev/null | tr -d '\n')"
say "stage 3b: assembling suite v2 rows"
cat convskills/v2/S1.jsonl convskills/v2/S2.jsonl convskills/v2/S3.jsonl convskills/v2/S3c.jsonl convskills/v2/S4.jsonl convskills/v2/S5m.jsonl 2>/dev/null | $PY -c "
import json,sys
for l in sys.stdin:
    r=json.loads(l)
    if not r.get('verified'): continue
    t=r['turns']; print(json.dumps(dict(source='convskills', bucket=r['lane'], id=r['id'], user=t[-2]['content'], assistant=t[-1]['content'], turns=t, n_turns=len(t), verified=True, meta=dict(lane=r['lane'], kind=r.get('kind'))), ensure_ascii=False))" > convskills/v2/rows_verified.jsonl
say "stage 3b: $(wc -l < convskills/v2/rows_verified.jsonl | tr -d ' ') verified suite rows; editor pass (kind if, 48 workers)"
WORKERS=48 BATCH=5 $PY edit_pass.py convskills/v2/rows_verified.jsonl convskills/v2/edited --kind if >> convskills/v2/edit.log 2>&1
say "stage 3b done: $(cat convskills/v2/edited/summary.json 2>/dev/null | tr -d '\n')"
$PY convskills/reverify_suite.py convskills/v2/edited/rows_edited.jsonl convskills/v2/reverify >> convskills/v2/edit.log 2>&1
say "stage 3c: suite re-verified: $(python3 -c "import json; m=json.load(open('convskills/v2/reverify/manifest.json')); print(m['final_rows'], 'of', m['rows'])" 2>/dev/null)"
say "stage 3 done; reviews next (Claude)"
