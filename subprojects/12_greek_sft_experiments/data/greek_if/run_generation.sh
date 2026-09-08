#!/usr/bin/env bash
# The scaled Greek IF generation, resumable stage by stage (each stage skips when its output exists). Usage: bash run_generation.sh <run_dir> [n_prompts=12000]
set -u; cd "$(dirname "$0")"; RUN=$1; N=${2:-12000}; mkdir -p "$RUN"; export CLAUDE_JOB_DIR=${CLAUDE_JOB_DIR:-/tmp}
log(){ echo "$(date '+%F %T') $*"; }
CHECKABLE=$(python3 -c "import constraints as C; print(','.join(C.CHECKABLE))")
[ -s subtopics.json ] || { log "stage 1: subtopics"; python3 gen_subtopics.py 50 || exit 1; }
[ -s "$RUN/request_bank.jsonl" ] && [ "$(wc -l < "$RUN/request_bank.jsonl")" -ge $((N + 2000)) ] || { log "stage 2: request bank"; python3 gen_requests.py "$RUN/request_bank.jsonl" 2 || exit 1; }
[ -s "$RUN/prompts.jsonl" ] || { log "stage 3: prompts"; python3 gen_prompts.py "$RUN/prompts.jsonl" --n "$N" --seed 2026 --level-weights .25,.30,.25,.12,.08 --families "$CHECKABLE" --requests "$RUN/request_bank.jsonl" || exit 1; }
log "stage 4: answers"; python3 run_pilot.py "$RUN/answers.jsonl" "$RUN/prompts.jsonl" || exit 1
log "stage 5: score"; python3 score_pilot.py "$RUN/answers.jsonl" "$RUN/scores.jsonl" "$RUN/summary_first.json" "$RUN/prompts.jsonl" > "$RUN/score_first.txt" || exit 1
log "stage 6: retry"; python3 retry_pass.py "$RUN/prompts.jsonl" "$RUN/scores.jsonl" "$RUN/retry_answers.jsonl" || exit 1
log "stage 7: build"; python3 build_dataset.py "$RUN/prompts.jsonl" "$RUN/answers.jsonl" "$RUN/retry_answers.jsonl" "$RUN/out" || exit 1
log "GENERATION DONE"
