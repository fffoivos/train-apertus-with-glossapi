#!/bin/bash
# 14 batches of 12 prompts (168), tilted: instruction 38%, everyday 19%, factual 15%, math 15%, safety 13%; three workers in parallel.
cd /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/gen02_demo
W='{"instruction":38,"everyday":19,"factual":15,"math":15,"safety":13}'
run(){ for b in "$@"; do python3 seed_demo.py 12 round2_batch$b.json --seed $((3000+b)) --id-prefix "R2B${b}_" --task-weights "$W" 2>&1 | tail -1; done; }
run 1 2 3 4 5 & run 6 7 8 9 10 & run 11 12 13 14 & wait
echo GEN_ROUND2_DONE
