#!/bin/bash
# Waits for the cut1 post-fix (astra math review) to finish, rebuilds cut1 from the corrected results, and releases the queue marker
# (build.log.hold → build.log with 'MATH BUILD DONE') so queue_runner starts the math correction pass. Run under nohup from data/.
cd "$(dirname "$0")/.." || exit 1
PY=~/venvs/sftdata/bin/python; LOG=math/cut1/postfix_then_rebuild.log; B2=math/cut1/build2.log
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
say "waiting for POSTFIX DONE"
until grep -q 'POSTFIX DONE' math/cut1/postfix.log 2>/dev/null; do sleep 120; done
say "postfix done: $(tail -1 math/cut1/postfix.log | cut -c1-200)"
rm -rf math/cut1/out; : > "$B2"; $PY math/build_math.py math/cut1 6000 4000 6000 >> "$B2" 2>&1
if grep -q 'MATH BUILD DONE' "$B2"; then cat "$B2" >> math/cut1/build.log.hold; mv math/cut1/build.log.hold math/cut1/build.log; say "rebuilt: $(cat math/cut1/out/summary.json 2>/dev/null | cut -c1-300) — queue released"; else say "REBUILD FAILED: $(tail -3 "$B2")"; fi
