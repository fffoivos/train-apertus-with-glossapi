#!/usr/bin/env bash
# Second queue stage (owner, 9 Sep; revised after the astra review): after the IF v1+v2 and math corrections (QUEUE DONE), wait for IF v3
# (the re-drawn half of v2 with the review fixes), correct v3, assemble the final IF set (edited v1v2 + edited v3, fidelity-filtered), then
# the conversation-skills lanes S1–S4 at halved sizes and their correction pass. Resumable; run under nohup.
set -u; cd "$(dirname "$0")"; LOG=queue_runner2.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
say "queue2 started: waiting for QUEUE DONE and IF v3"
while ! grep -q 'QUEUE DONE' queue_runner.log 2>/dev/null; do sleep 300; done; say "queue1 done"
while ! grep -q 'GENERATION DONE' greek_if/v3/run.log 2>/dev/null; do sleep 300; done; say "IF v3 done → correction pass ($(wc -l < greek_if/v3/out/greek_if_sft.jsonl) rows)"
WORKERS=24 python3 edit_pass.py greek_if/v3/out/greek_if_sft.jsonl greek_if/v3/edited --kind if >> "$LOG" 2>&1; say "v3 correction: $(cat greek_if/v3/edited/summary.json 2>/dev/null)"
python3 - <<'PY' >> "$LOG" 2>&1
import json, re, sys, os
sys.path.insert(0, 'greek_if'); from build_dataset import fidelity_ok, FIDELITY_FORMS
os.makedirs('greek_if/final', exist_ok=True); seen = set(); n = 0; fid = 0
with open('greek_if/final/greek_if_sft.jsonl', 'w') as out:
    for src in ('greek_if/v1v2/edited/rows_edited.jsonl', 'greek_if/v3/edited/rows_edited.jsonl'):
        for l in open(src):
            r = json.loads(l); key = re.sub(r'\s+', ' ', r['user']).strip().lower()
            if key in seen: continue
            if r['meta']['form'] in FIDELITY_FORMS and not fidelity_ok(r['user'], r['assistant']): fid += 1; continue
            seen.add(key); out.write(json.dumps(r, ensure_ascii=False) + '\n'); n += 1
print('FINAL greek_if_sft rows', n, 'fidelity dropped', fid)
PY
say "final IF set: $(tail -1 "$LOG")"
# lane sizes: a 1,000-dialogue PILOT first (astra review 2026-09-09), scale after review and after the Codex reset
for L in S1:150 S2:250 S3:250 S3c:100 S4:75 S5m:150; do lane=${L%%:*}; n=${L##*:}; say "lane $lane × $n"; WORKERS=24 python3 convskills/gen_suite.py convskills/v1 --lane $lane --n $n --seed 3 >> "$LOG" 2>&1; say "$lane: $(cat convskills/v1/${lane}_summary.json 2>/dev/null | cut -c1-200)"; done
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
