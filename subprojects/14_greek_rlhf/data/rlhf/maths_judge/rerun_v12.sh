#!/bin/bash
cd /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/14_greek_rlhf
M=data/rlhf/maths_judge; C=$M/calibration; P=$M/rejudge_preexisting
python3 $M/maths_judge.py judge $C/prompts.jsonl $C/samples.jsonl $C/references.jsonl $C/judged_v12.jsonl
python3 $M/maths_judge.py judge $P/prompts.jsonl $P/samples.jsonl $P/references.jsonl $P/judged_v12.jsonl
echo MATHS_V12_DONE
