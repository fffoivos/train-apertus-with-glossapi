#!/bin/bash
# Judge the frozen constructed responses with Claude Opus 5: English rubric, then Greek rubric; report false-pass / false-fail per axis.
cd "$(dirname "$0")"
~/venvs/sftdata/bin/python judge.py constructed.jsonl judged_en.jsonl --backend claude --model claude-opus-5 --rubric en --workers 4 > judge_en.log 2>&1; ~/venvs/sftdata/bin/python calibrate.py report judged_en.jsonl > calibration_en.txt 2>&1
~/venvs/sftdata/bin/python judge.py constructed.jsonl judged_el.jsonl --backend claude --model claude-opus-5 --rubric el --workers 4 > judge_el.log 2>&1; ~/venvs/sftdata/bin/python calibrate.py report judged_el.jsonl > calibration_el.txt 2>&1
echo "CALIBRATION DONE" >> judge_el.log
