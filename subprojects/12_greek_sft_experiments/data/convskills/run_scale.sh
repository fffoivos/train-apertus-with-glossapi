#!/bin/zsh
# Conversation-suite scale run (v2, seed 4): the 4k-attempt allocation of DIALOGUE_REVIEW_AND_SUITE §7, lanes one after the other at 24 workers.
export PYTHONHASHSEED=0 WORKERS=24
cd "$(dirname "$0")"
for spec in S1:800 S2:1000 S3:500 S3c:500 S4:400 S5m:800; do
  lane=${spec%%:*}; n=${spec##*:}
  ~/venvs/sftdata/bin/python gen_suite.py v2 --lane $lane --n $n --seed 4 >> v2_run.log 2>&1
done
echo SUITE_SCALE_DONE >> v2_run.log
