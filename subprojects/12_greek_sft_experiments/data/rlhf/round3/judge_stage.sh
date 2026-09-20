#!/bin/bash
# Judge one escalation stage of round 3 with the existing runner (judge_batches.py → judge_rank4.py), batches of four, medium effort.
# Owner, 17 Sept: the only judging change from 0.2 is a maths reviewer prompt. Prompts carrying maths content use
# prompts/judge_rank4_maths_en.txt; every other prompt uses prompts/judge_rank4_v2_en.txt. Same schema, same pair rule.
# Usage: bash data/rlhf/round3/judge_stage.sh <1|2|3>
set -eu; cd "$(dirname "$0")/../../.."; S=$1; D=data/rlhf/round3; R=data/rlhf/prompts
python3 $D/stage.py split $S
if [ -s $D/maths_s${S}_prompts.jsonl ]; then
  python3 data/rlhf/judge_batches.py $D/maths_s${S}_prompts.jsonl $D/maths_s${S}_samples.jsonl $D/judged_maths_s${S}.jsonl --rubric $R/judge_rank4_maths_en.txt --schema v2 --workers 16
fi
if [ -s $D/general_s${S}_prompts.jsonl ]; then
  python3 data/rlhf/judge_batches.py $D/general_s${S}_prompts.jsonl $D/general_s${S}_samples.jsonl $D/judged_general_s${S}.jsonl --rubric $R/judge_rank4_v2_en.txt --schema v2 --workers 16
fi
python3 $D/pairs.py --dir $D
echo "JUDGE_STAGE_${S}_DONE"
