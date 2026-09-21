#!/usr/bin/env bash
# One cross-vendor review. Read-only sandbox: a certifier that can edit what it certifies is not one.
# The model is asserted from the session ROLLOUT FILE, never from what the reviewer says about itself.
# Usage: run_review.sh <label> <brief.md> <model> <effort>
#
# DO NOT add `-c features.code_mode_host=false` here. That flag fixes a codex crash elsewhere in this
# repo, but in a REVIEW it disables the reviewer's shell entirely: the model cannot read a single file
# and returns an honest "UNREVIEWED". It silently cost us R-DPO6 (which reported 0 rows inspected and
# raised that as its BLOCKER) and the first attempt at R-DPO7a. A review with no shell is not a review.
set -u
LABEL="$1"; BRIEF="$2"; MODEL="${3:-gpt-5.6-sol}"; EFFORT="${4:-xhigh}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"; cd "$DIR"
OUT="docs/RLHF_COORDINATION/reviews/${LABEL}_review_1.md"
LOG="docs/RLHF_COORDINATION/reviews/${LABEL}_review_1.codexlog"
BEFORE=$(date +%s)
echo "[$(date '+%H:%M:%S')] REVIEW START $LABEL model=$MODEL effort=$EFFORT"
codex exec -m "$MODEL" -c "model_reasoning_effort=$EFFORT" \
  -c project_doc_max_bytes=0 \
  -c features.remote_plugin=false -c features.apps=false \
  --sandbox read-only --skip-git-repo-check -C "$DIR" -o "$OUT" - < "$BRIEF" > "$LOG" 2>&1
RC=$?
# assert the model that actually ran, from the rollout the CLI wrote for THIS session
ROLL=$(find "$HOME/.codex/sessions" -name 'rollout-*.jsonl' -newermt "@$BEFORE" 2>/dev/null | sort | head -1)
ACTUAL=$(python3 -c "
import json,sys
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'model' and isinstance(v, str): return v
            r = walk(v)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = walk(v)
            if r: return r
    return None
try:
    for l in open(sys.argv[1]):
        try: m = walk(json.loads(l))
        except Exception: continue
        if m: print(m); break
except Exception: pass
" "$ROLL" 2>/dev/null)
echo "[$(date '+%H:%M:%S')] REVIEW END $LABEL rc=$RC elapsed=$(( ($(date +%s)-BEFORE)/60 ))m"
echo "  requested=$MODEL  asserted=${ACTUAL:-UNKNOWN}  rollout=${ROLL##*/}"
if [ -n "$ACTUAL" ] && [ "$ACTUAL" != "$MODEL" ]; then
  echo "  !! MODEL MISMATCH — requested $MODEL, ran $ACTUAL. Treat as NOT independently certified."; exit 9
fi
case "${ACTUAL:-}" in *claude*|*opus*) echo "  !! SAME-FAMILY AS IMPLEMENTER — not a cross-vendor review."; exit 9;; esac
[ -s "$OUT" ] || { echo "  !! no review produced"; exit 9; }
if grep -qiE 'UNREVIEWED|code-mode host is disabled|access (failed|denied)' "$OUT"; then
  echo "  !! REVIEWER COULD NOT READ THE REPO — this is NOT a certification. Fix access and re-run."; exit 9
fi
RAN=$(grep -c '^exec' "$LOG" 2>/dev/null || echo 0)
echo "  shell commands the reviewer actually ran: $RAN"
[ "$RAN" -ge 3 ] || { echo "  !! reviewer ran almost nothing ($RAN cmds) — treat as unverified."; exit 9; }
echo "  -> $OUT ($(wc -c < "$OUT") bytes)"; tail -1 "$OUT"
