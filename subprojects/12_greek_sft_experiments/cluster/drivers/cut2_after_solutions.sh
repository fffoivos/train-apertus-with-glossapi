#!/usr/bin/env bash
# CHAIN v6 (astra R2: fail-closed; validity on the FINAL text): every stage must exit 0 or the chain stops with CUT2_CHAIN_FAILED; CUT2_CHAIN_DONE only after a strict assembly.
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log; O=data/math/cut2/out; RB="data/math/cut2/run_batches.py"
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
run(){ local name=$1; shift; "$@" > $O/$name.log 2>&1; local rc=$?; say "$name exit $rc: $(tail -1 $O/$name.log | cut -c1-140)"; [ $rc -eq 0 ] || { say "CUT2_CHAIN_FAILED at $name"; exit 1; }; }
say "CHAIN v6 queued: waits for fidelity_all (pid 91791) and Level-4 HIGH (pid 91792); then stragglers(high,32) -> audit(64) -> adjudicate(64) -> polish(64) -> validate(64) -> repair(32) -> polish -> validate -> assemble(strict); second pass after Level-5; fail-closed"
while kill -0 91791 2>/dev/null || kill -0 91792 2>/dev/null; do sleep 30; done; say "fidelity_all + Level-4 HIGH ended: $(grep -c . $O/fidelity_all.jsonl) fidelity rows, $(grep -c . $O/solutions_el_l4_high.jsonl) L4 rows"
[ "$(grep -c . $O/fidelity_all.jsonl)" -ge 11000 ] || { say "CUT2_CHAIN_FAILED: fidelity_all incomplete"; exit 1; }
WORKERS=32 run solutions_resume $PY $RB solutions --effort high
WORKERS=64 run fidelity_audit $PY $RB fidelity_audit_passes
WORKERS=64 run fidelity_adjudicate $PY $RB fidelity_adjudicate
WORKERS=64 run polish $PY data/math/cut2/polish_targets.py
WORKERS=64 run validate $PY $RB validate
WORKERS=32 run repair_high $PY $RB repair_high
WORKERS=64 run polish_r $PY data/math/cut2/polish_targets.py
WORKERS=64 run validate_r $PY $RB validate
$PY data/math/cut2/assemble_cut2.py --allow-incomplete > $O/assemble_pass1.log 2>&1; say "assemble pass 1 (Level 5 may still be pending): $(tail -1 $O/assemble_pass1.log | cut -c1-200)"
while pgrep -f "run_batches.py level5_solutions_high" >/dev/null; do sleep 60; done; say "Level-5 HIGH complete: $(grep -c . $O/level5_solutions_el_high.jsonl) rows"
[ "$(grep -c . $O/level5_solutions_el_high.jsonl)" -ge 1450 ] || { say "CUT2_CHAIN_FAILED: Level-5 HIGH incomplete"; exit 1; }
WORKERS=64 run polish2 $PY data/math/cut2/polish_targets.py
WORKERS=64 run validate2 $PY $RB validate
WORKERS=32 run repair_high2 $PY $RB repair_high
WORKERS=64 run polish3 $PY data/math/cut2/polish_targets.py
WORKERS=64 run validate3 $PY $RB validate
run assemble_final $PY data/math/cut2/assemble_cut2.py
say "CUT2_CHAIN_DONE (strict assembly succeeded)"
