#!/bin/bash
# Waits for the 40 constructed pairs, then judges the 80 responses with Claude Opus (English rubric) and with the Greek rubric, and reports false-pass/false-fail.
cd "$(dirname "$0")"; until [ "$(wc -l < constructed_pairs.jsonl 2>/dev/null)" -ge 40 ] || ! pgrep -f 'calibrate.py mak[e]' > /dev/null; do sleep 30; done
~/venvs/sftdata/bin/python calibrate.py make 10 > /dev/null 2>&1   # rebuild constructed.jsonl from whatever completed
~/venvs/sftdata/bin/python judge.py constructed.jsonl judged_en.jsonl --backend claude --model claude-opus-5 --rubric en --workers 4 > judge_en.log 2>&1; ~/venvs/sftdata/bin/python calibrate.py report judged_en.jsonl > calibration_en.txt 2>&1
~/venvs/sftdata/bin/python judge.py constructed.jsonl judged_el.jsonl --backend claude --model claude-opus-5 --rubric el --workers 4 > judge_el.log 2>&1; ~/venvs/sftdata/bin/python calibrate.py report judged_el.jsonl > calibration_el.txt 2>&1
echo "CALIBRATION DONE" >> judge_el.log
