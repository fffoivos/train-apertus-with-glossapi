set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log; mkdir -p data/math/cut2/out
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
say "stage A (parallel): Greek CoT solutions for the 9,999 (72 workers) + Level-5 problem translations (48 workers)"
(WORKERS=72 $PY data/math/cut2/run_batches.py solutions > data/math/cut2/out/solutions.log 2>&1; say "solutions exit $?: $(tail -1 data/math/cut2/out/solutions.log | cut -c1-120)") &
(WORKERS=48 $PY data/math/cut2/run_batches.py level5_problems > data/math/cut2/out/level5_problems.log 2>&1; say "level5 problems exit $?: $(tail -1 data/math/cut2/out/level5_problems.log | cut -c1-120)"; WORKERS=48 $PY data/math/cut2/run_batches.py level5_solutions > data/math/cut2/out/level5_solutions.log 2>&1; say "level5 solutions exit $?: $(tail -1 data/math/cut2/out/level5_solutions.log | cut -c1-120)") &
wait; say "CUT2_SOL_DONE"
