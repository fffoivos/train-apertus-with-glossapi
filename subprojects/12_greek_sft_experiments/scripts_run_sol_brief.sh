#!/usr/bin/env bash
# Run one Sol work package from its brief, inside this subproject, with file-write + network access.
# Usage: scripts_run_sol_brief.sh WP0 [effort]
set -u
WP="$1"; EFFORT="${2:-high}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PROMPT="$(cat briefs/_COMMON.md; echo; echo; cat "briefs/$WP.md")"
echo "[$(date '+%H:%M:%S')] SOL START $WP effort=$EFFORT" | tee -a EXECUTION_LOG.raw
codex exec -m gpt-5.6-sol -c "model_reasoning_effort=$EFFORT" -c project_doc_max_bytes=0 \
  -c sandbox_workspace_write.network_access=true -c features.code_mode_host=false --sandbox workspace-write --skip-git-repo-check \
  -C "$DIR" -o "briefs/$WP.out.md" - <<<"$PROMPT"
RC=$?
echo "[$(date '+%H:%M:%S')] SOL END $WP rc=$RC" | tee -a EXECUTION_LOG.raw
exit $RC
