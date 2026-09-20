set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=logs/sol_after_l5.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
say "queued: waits for the Level-5 HIGH stage to exit, then correcting-v1 classification (600 calls, medium, 16 workers) and the MATH-200-el-confirm build (200 translate + ~200 polish, 16 workers)"
while pgrep -f "run_batches.py level5_solutions_high" >/dev/null; do sleep 60; done; say "Level-5 HIGH done: $(grep -c . data/math/cut2/out/level5_solutions_el_high.jsonl) rows"
WORKERS=16 $PY data/robustness/correcting/v2/classify_v1.py > data/robustness/correcting/v2/classify.log 2>&1; say "classify exit $?: $(tail -2 data/robustness/correcting/v2/classify.log | tr '\n' ' ' | cut -c1-200)"
python3 data/robustness/correcting/v2/build_v2.py > data/robustness/correcting/v2/build.log 2>&1; say "build_v2 exit $?: $(tail -1 data/robustness/correcting/v2/build.log | cut -c1-300)"
WORKERS=16 $PY data/benchmarks_el/math200_confirm/build.py > data/benchmarks_el/math200_confirm/build.log 2>&1; say "math200 build exit $?: $(tail -1 data/benchmarks_el/math200_confirm/build.log | cut -c1-300)"
say "SOL_AFTER_L5_DONE"
