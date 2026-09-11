#!/bin/zsh
# Sequential Sol pipeline (owner, 2026-09-11: decide priority, never exceed 48 concurrent codex processes, protect the home connection).
# Stage 1: correcting shard s2 (24 workers). After 4 min, if the link is healthy (ping avg < 100 ms, few retries), add shard s3 (48 total).
# Stage 2: when the shards are done, the suite lanes (WORKERS=48 alone, or 24 if the link was unhealthy).
# Stages 3+ (editor passes, reviews) are launched by me when each set is complete. Log: pipeline_sequence.log
cd "$(dirname "$0")"; LOG=pipeline_sequence.log; say() { echo "$(date '+%F %H:%M') $*" >> $LOG; }
PY=~/venvs/sftdata/bin/python; HEALTHY=1
link_ok() { avg=$(ping -c 5 -t 3 1.1.1.1 2>/dev/null | tail -1 | awk -F/ '{print $5}' | cut -d. -f1); r=$(tail -120 robustness/correcting/scale_s2.log | grep -c retry); say "link check: ping avg ${avg:-NA} ms, retries in last 120 lines $r"; [ -n "$avg" ] && [ "$avg" -lt 100 ] && [ "$r" -lt 12 ]; }
say "stage 1: shard s2 at 24 workers"; python3 launch_detached.py robustness/correcting/scale_s2.log robustness $PY build_correcting.py correcting/scale/s2 --n 300 --seed 2 --concurrency 24 --role-plant-share 0.35 > /dev/null
sleep 240
if link_ok; then say "link healthy: adding shard s3 (48 total)"; python3 launch_detached.py robustness/correcting/scale_s3.log robustness $PY build_correcting.py correcting/scale/s3 --n 300 --seed 3 --concurrency 24 --role-plant-share 0.35 > /dev/null; else HEALTHY=0; say "link NOT healthy: staying at 24 workers; s3 runs after s2"; fi
while pgrep -f '[b]uild_correcting.py correcting/scale/s2 ' > /dev/null; do sleep 120; done
if [ "$HEALTHY" = 0 ]; then say "s2 done; shard s3 at 24"; python3 launch_detached.py robustness/correcting/scale_s3.log robustness $PY build_correcting.py correcting/scale/s3 --n 300 --seed 3 --concurrency 24 --role-plant-share 0.35 > /dev/null; fi
while pgrep -f '[b]uild_correcting.py correcting/scale' > /dev/null; do sleep 120; done
W=$([ "$HEALTHY" = 1 ] && echo 48 || echo 24); say "stage 2: correcting shards finished ($(cat robustness/correcting/scale/s2/dialogues.jsonl robustness/correcting/scale/s3/dialogues.jsonl | wc -l | tr -d ' ') dialogues); suite lanes at $W workers"
WORKERS=$W python3 launch_detached.py convskills/v2_run.log convskills /bin/zsh ./run_scale.sh > /dev/null
while pgrep -f '[g]en_suite.py v2' > /dev/null || pgrep -f '[r]un_scale.sh' > /dev/null; do sleep 120; done
say "stage 2 done: suite lanes finished; editor passes and reviews are launched by Claude"
