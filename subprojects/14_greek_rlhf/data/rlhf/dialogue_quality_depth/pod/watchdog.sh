#!/usr/bin/env bash
# Independent local budget watchdog. It owns teardown if the stage runner hangs.
set -Eeuo pipefail

if [[ $# -ne 6 ]]; then exit 64; fi
STAGE="$1"; STATE_DIR="$2"; POD_ID="$3"; POD_STATE="$4"; LOG="$5"; PARENT_PID="$6"
POD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DQD_DIR="$(cd "$POD_DIR/.." && pwd)"
PYTHON_BIN="${DQD_PYTHON_BIN:-python3}"
CONTROL_KEY_FILE="${DQD_CONTROL_KEY_FILE:-$HOME/.config/prime/key}"
MARKER="$STATE_DIR/pod/watchdog_teardown_$POD_ID"

log() { printf '[%s] WATCHDOG %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }

seconds="$("$PYTHON_BIN" - "$STATE_DIR/ledger.jsonl" "$POD_ID" <<'PY'
import datetime as dt, json, sys
rows=[json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
starts=[r for r in rows if r.get("record")=="gpu_start" and r.get("pod_id")==sys.argv[2]]
if not starts:
    raise SystemExit(1)
deadline=dt.datetime.fromisoformat(starts[-1]["shutdown_deadline_utc"])
now=dt.datetime.now(dt.timezone.utc)
print(max(0, int((deadline-now).total_seconds())))
PY
)" || { log "cannot read budget.py deadline; refusing silent watchdog failure"; exit 69; }

log "armed stage=$STAGE pod_id=$POD_ID seconds_to_deadline=$seconds"
sleep "$seconds"
log "deadline reached; stopping ledger and deleting pod"
"$PYTHON_BIN" "$DQD_DIR/dqd.py" --state "$STATE_DIR" ledger gpu-stop --pod-id "$POD_ID" >> "$LOG" 2>&1 || true
if PRIME_INTELLECT_CONTROL_KEY="$(<"$CONTROL_KEY_FILE")" \
    "$PYTHON_BIN" "$POD_DIR/dqd_provision.py" teardown "$POD_STATE" --pod-id "$POD_ID" >> "$LOG" 2>&1; then
  : > "$MARKER"
  log "DQP_WATCHDOG_RECEIPT stage=$STAGE pod_id=$POD_ID teardown=confirmed"
else
  log "DQP_WATCHDOG_RECEIPT stage=$STAGE pod_id=$POD_ID teardown=FAILED"
fi
kill -TERM "$PARENT_PID" 2>/dev/null || true
