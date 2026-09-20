set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
say "LEVEL-5 HIGH relaunch (duplicate ids deduped, first occurrence): all Level-5 solutions at HIGH (16 workers)"
WORKERS=16 $PY data/math/cut2/run_batches.py level5_solutions_high > data/math/cut2/out/level5_solutions_high.log 2>&1; say "level5 solutions HIGH exit $?: $(tail -1 data/math/cut2/out/level5_solutions_high.log | cut -c1-120)"
