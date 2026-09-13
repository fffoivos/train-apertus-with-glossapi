set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; OUT=$PWD/results/peers_20260913; LOG=$OUT/judge.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
dedupe(){ python3 - "$1" <<'PY'
import json,sys; p=sys.argv[1]; seen=set(); out=[]
for l in open(p):
    r=json.loads(l)
    if r['id'] in seen: continue
    seen.add(r['id']); out.append(l)
open(p,'w').writelines(out); print(p.split('/')[-2:], len(out))
PY
}
say "sequential per peer, 8 + 6 workers (concurrency kept low while the dialogues run)"
for M in "$@"; do for f in $OUT/bench_$M/*.jsonl; do [ -s "$f" ] && dedupe "$f"; done; rm -f $OUT/bench_$M/*_judged_sol.jsonl
  (WORKERS=6 $PY data/benchmarks_el/multichallenge/judge.py $OUT/bench_$M/multichallenge_el.jsonl $OUT/bench_$M/multichallenge_el_judged_sol.jsonl --backend sol --rubric en > $OUT/bench_$M/multichallenge_el_judge_sol.log 2>&1; say "multichallenge $M: $(tail -1 $OUT/bench_$M/multichallenge_el_judge_sol.log | cut -c1-200)") &
  ($PY data/benchmarks_el/xstest/judge.py $OUT/bench_$M/xstest_el.jsonl $OUT/bench_$M/xstest_el_judged_sol.jsonl --backend sol --workers 8 > $OUT/bench_$M/xstest_el_judge_sol.log 2>&1; say "xstest $M: $(grep -E 'safe n|unsafe n' $OUT/bench_$M/xstest_el_judge_sol.log | tr '\n' ' ' | cut -c1-240)") &
  wait
done; say "JUDGE_DONE $*"
