#!/usr/bin/env bash
# Independent local watchdog for dialogue v2 (copy of dialogue_quality_depth/pod/watchdog.sh). It owns teardown if the
# stage runner hangs: at the ledger deadline it deletes the pod (GET-confirmed), stops the ledger and signals the runner.
set -Eeuo pipefail

if [[ $# -ne 6 ]]; then exit 64; fi
STAGE="$1"; RUNTIME="$2"; POD_ID="$3"; POD_STATE="$4"; LOG="$5"; PARENT_PID="$6"
POD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$POD_DIR/.." && pwd)"
PYTHON_BIN="${DV2_PYTHON_BIN:-python3}"
CONTROL_KEY_FILE="${DV2_CONTROL_KEY_FILE:-$HOME/.config/prime/key}"
MARKER="$RUNTIME/pod/watchdog_teardown_$POD_ID"
RECORD="$RUNTIME/pod/teardown_records.jsonl"

log() { printf '[%s] WATCHDOG %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }

seconds="$("$PYTHON_BIN" - "$RUNTIME/gpu_ledger.jsonl" "$POD_ID" <<'PY'
import datetime as dt, json, sys
rows=[json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
starts=[r for r in rows if r.get("record")=="gpu_start" and r.get("pod_id")==sys.argv[2]]
if not starts:
    raise SystemExit(1)
deadline=dt.datetime.fromisoformat(starts[-1]["shutdown_deadline_utc"])
print(max(0, int((deadline-dt.datetime.now(dt.timezone.utc)).total_seconds())))
PY
)" || { log "cannot read the ledger deadline; refusing silent watchdog failure"; exit 69; }

log "armed stage=$STAGE pod_id=$POD_ID seconds_to_deadline=$seconds"
sleep "$seconds"
log "deadline reached; deleting pod and stopping the ledger"
if PRIME_INTELLECT_CONTROL_KEY="$(<"$CONTROL_KEY_FILE")" \
    "$PYTHON_BIN" "$POD_DIR/dv2_provision.py" teardown "$POD_STATE" --pod-id "$POD_ID" --record "$RECORD" >> "$LOG" 2>&1; then
  : > "$MARKER"
  log "DV2_WATCHDOG_RECEIPT stage=$STAGE pod_id=$POD_ID teardown=confirmed"
else
  log "DV2_WATCHDOG_RECEIPT stage=$STAGE pod_id=$POD_ID teardown=FAILED"
fi
"$PYTHON_BIN" "$V2_DIR/dv2.py" ledger gpu-stop --pod-id "$POD_ID" --teardown-record "$RECORD" >> "$LOG" 2>&1 || true
kill -TERM "$PARENT_PID" 2>/dev/null || true
