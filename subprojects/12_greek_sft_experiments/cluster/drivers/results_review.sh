set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; LOG=results/R3_single/results_review.log
echo "[$(date '+%m-%d %H:%M')] start results review (astra xhigh, 1 call)" | tee -a $LOG
python3 data/review_astra.py results_r3 docs/reviews/briefs/astra_results_r3.md docs/reviews/ASTRA_results_r3_20260913.md --effort xhigh > results/R3_single/results_review_run.log 2>&1; echo "[$(date '+%m-%d %H:%M')] exit $?: $(tail -1 results/R3_single/results_review_run.log | cut -c1-140)" | tee -a $LOG; echo "RESULTS_REVIEW_DONE" | tee -a $LOG
