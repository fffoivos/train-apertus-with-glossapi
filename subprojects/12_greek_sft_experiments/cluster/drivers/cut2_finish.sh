set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log; O=data/math/cut2/out; RB="data/math/cut2/run_batches.py"
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
run(){ local name=$1; shift; "$@" > $O/$name.log 2>&1; local rc=$?; say "$name exit $rc: $(tail -1 $O/$name.log | cut -c1-140)"; [ $rc -eq 0 ] || { say "CUT2_CHAIN_FAILED at $name"; exit 1; }; }
say "FINISH: retry failed polish -> validate new texts -> strict assembly"
WORKERS=32 run polish4 $PY data/math/cut2/polish_targets.py
WORKERS=32 run validate4 $PY $RB validate
run assemble_final $PY data/math/cut2/assemble_cut2.py
say "CUT2_CHAIN_DONE (strict assembly succeeded)"
