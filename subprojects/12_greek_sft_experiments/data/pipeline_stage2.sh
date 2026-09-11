#!/bin/zsh
# After both correcting shards finish: the suite's remaining lanes at 48 workers (the day's measured cap), then hand over to Claude for editor passes and reviews.
cd "$(dirname "$0")"; LOG=pipeline_sequence.log; say() { echo "$(date '+%F %H:%M') $*" >> $LOG; }
say "stage 1b: link healthy after the catalog fix (ping 21 ms, Wi-Fi 271 KB/s); shard s3 added, 48 workers"
while pgrep -f '[b]uild_correcting.py correcting/scale' > /dev/null; do sleep 120; done
say "stage 2: shards finished ($(cat robustness/correcting/scale/s2/dialogues.jsonl robustness/correcting/scale/s3/dialogues.jsonl | wc -l | tr -d ' ') dialogues); suite lanes at 48 workers"
WORKERS=48 python3 launch_detached.py convskills/v2_run.log convskills /bin/zsh ./run_scale.sh > /dev/null
while pgrep -f '[g]en_suite.py v2' > /dev/null || pgrep -f '[r]un_scale.sh' > /dev/null; do sleep 120; done
say "stage 2 done: suite lanes finished; editor passes and reviews next (Claude)"
