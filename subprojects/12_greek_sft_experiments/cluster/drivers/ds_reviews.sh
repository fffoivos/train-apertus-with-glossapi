set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; LOG=results/R3_single/ds_reviews.log
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
run(){ name=$1; rows=$2; n=$3; extra=$4; say "start $name"; python3 data/review_astra.py $name docs/reviews/briefs/$name.md docs/reviews/ASTRA_${name#astra_}_20260913.md --rows $rows --n $n --seed 3 --max-chars 6000 --effort xhigh $extra > results/R3_single/$name.log 2>&1; say "$name exit $?: $(tail -1 results/R3_single/$name.log | cut -c1-120)"; }
run astra_ds_greek_if data/greek_if/final/greek_if_sft.jsonl 60 "" &
run astra_ds_math_cut1 data/math/cut1/edited/rows_edited.jsonl 60 "" &
run astra_ds_convskills data/convskills/v2/final/rows_final.jsonl 60 "" &
run astra_ds_correcting data/robustness/correcting/scale/rows/rows_final.jsonl 40 "" &
run astra_ds_personality data/personality/personality_v3v4_final.jsonl 50 "" &
run astra_ds_imports data/arms/R3_single/train.jsonl 80 "--fields config,id,messages" &
wait; say "DS_REVIEWS_DONE"
