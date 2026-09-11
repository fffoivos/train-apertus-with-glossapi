#!/bin/zsh
# Owner rule 2026-09-11: never more than 48 concurrent codex processes. Waits for the stopped runs' codex children to drain, relaunches the two
# correcting shards (24 workers each = 48), and then starts the suite scale run only after the shards have finished.
cd "$(dirname "$0")"
for i in $(seq 1 24); do n=$(pgrep -f '[c]odex exec' | wc -l | tr -d ' '); [ "$n" -le 4 ] && break; sleep 5; done
echo "$(date +%H:%M) drained to $n codex procs; launching shards s2 s3 (24 each)"
for SEED in 2 3; do echo "shard $SEED pid $(python3 launch_detached.py robustness/correcting/scale_s$SEED.log robustness ~/venvs/sftdata/bin/python build_correcting.py correcting/scale/s$SEED --n 300 --seed $SEED --concurrency 24 --role-plant-share 0.35)"; done
while pgrep -f '[b]uild_correcting.py correcting/scale' > /dev/null; do sleep 120; done
echo "$(date +%H:%M) shards finished; launching the suite (24 workers)"
echo "suite pid $(python3 launch_detached.py convskills/v2_run.log convskills /bin/zsh ./run_scale.sh)"
