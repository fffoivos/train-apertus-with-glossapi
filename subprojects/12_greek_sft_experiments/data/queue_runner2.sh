#!/usr/bin/env bash
# Second queue stage (owner, 9 Sep): after the IF and math correction passes finish (QUEUE DONE in queue_runner.log), build the
# conversation-skills lanes S1–S4, then their Greek correction pass. Resumable; run under nohup.
set -u; cd "$(dirname "$0")"; LOG=queue_runner2.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
say "queue2 started: waiting for QUEUE DONE"; while ! grep -q 'QUEUE DONE' queue_runner.log 2>/dev/null; do sleep 300; done
for L in S1:2000 S2:2000 S3:2000 S4:1000; do lane=${L%%:*}; n=${L##*:}; say "lane $lane × $n"; WORKERS=24 python3 convskills/gen_suite.py convskills/v1 --lane $lane --n $n --seed 3 >> "$LOG" 2>&1; say "$lane: $(cat convskills/v1/${lane}_summary.json 2>/dev/null | cut -c1-200)"; done
python3 - <<'PY' >> "$LOG" 2>&1
import json, glob
rows = [json.loads(l) for f in sorted(glob.glob('convskills/v1/S[1-4].jsonl')) for l in open(f)]
keep = [r for r in rows if r['verified']]
with open('convskills/v1/convskills_sft.jsonl', 'w') as f:
    for r in keep:
        f.write(json.dumps(dict(source='convskills', bucket=r['lane'], id=r['id'], user=r['turns'][-2]['content'], assistant=r['turns'][-1]['content'], turns=r['turns'], n_turns=len(r['turns']), verified='regex', meta=dict(lane=r['lane'], kind=r['kind'])), ensure_ascii=False) + '\n')
print('convskills_sft rows', len(keep), 'of', len(rows))
PY
say "correction pass on convskills"; WORKERS=24 python3 edit_pass.py convskills/v1/convskills_sft.jsonl convskills/v1/edited --kind if >> "$LOG" 2>&1; say "QUEUE2 DONE: $(cat convskills/v1/edited/summary.json 2>/dev/null)"
