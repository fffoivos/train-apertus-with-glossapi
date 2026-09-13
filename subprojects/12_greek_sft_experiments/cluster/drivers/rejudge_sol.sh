set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; OUT=$PWD/results/R3_single; LOG=$OUT/rejudge_sol.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
for M in R3 B; do
  (WORKERS=24 $PY data/benchmarks_el/multichallenge/judge.py $OUT/bench_$M/multichallenge_el.jsonl $OUT/bench_$M/multichallenge_el_judged_sol.jsonl --backend sol --rubric en > $OUT/bench_$M/multichallenge_el_judge_sol.log 2>&1; say "multichallenge $M sol: $(tail -1 $OUT/bench_$M/multichallenge_el_judge_sol.log | cut -c1-200)") &
  ($PY data/benchmarks_el/xstest/judge.py $OUT/bench_$M/xstest_el.jsonl $OUT/bench_$M/xstest_el_judged_sol.jsonl --backend sol --workers 24 > $OUT/bench_$M/xstest_el_judge_sol.log 2>&1; say "xstest $M sol: $(grep -E 'safe n|unsafe n' $OUT/bench_$M/xstest_el_judge_sol.log | tr '\n' ' ' | cut -c1-240)") &
done; wait; say "REJUDGE_SOL_DONE"
