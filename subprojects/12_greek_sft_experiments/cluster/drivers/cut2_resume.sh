set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
say "RESUME 14 Sept: solutions (80 workers, medium) then fidelity_all (96 workers, high); Level-5 problems then solutions (16 workers)"
(WORKERS=80 $PY data/math/cut2/run_batches.py solutions > data/math/cut2/out/solutions.log 2>&1; say "solutions exit $?: $(tail -1 data/math/cut2/out/solutions.log | cut -c1-120)"
 while pgrep -f "run_batches.py level5" >/dev/null; do sleep 60; done
 WORKERS=96 $PY data/math/cut2/run_batches.py fidelity_all > data/math/cut2/out/fidelity_all.log 2>&1; say "fidelity_all exit $?: $(tail -1 data/math/cut2/out/fidelity_all.log | cut -c1-120)") &
(WORKERS=16 $PY data/math/cut2/run_batches.py level5_problems > data/math/cut2/out/level5_problems.log 2>&1; say "level5 problems exit $?: $(tail -1 data/math/cut2/out/level5_problems.log | cut -c1-120)"; WORKERS=16 $PY data/math/cut2/run_batches.py level5_solutions > data/math/cut2/out/level5_solutions.log 2>&1; say "level5 solutions exit $?: $(tail -1 data/math/cut2/out/level5_solutions.log | cut -c1-120)") &
wait; say "CUT2_RESUME_DONE"
