#!/usr/bin/env bash
# Sole GPU entry point: bash pod/run_stage.sh <measurement|candidates|resample>
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^(measurement|candidates|resample)$ ]]; then
  printf 'usage: bash pod/run_stage.sh <measurement|candidates|resample>\n' >&2
  exit 64
fi

STAGE="$1"
POD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DQD_DIR="$(cd "$POD_DIR/.." && pwd)"
STATE_DIR="${DQD_STATE_DIR:-$DQD_DIR/runtime}"
POD_RUNTIME="$STATE_DIR/pod"
mkdir -p "$POD_RUNTIME"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$POD_RUNTIME/${STAGE}_${STAMP}.log"
touch "$LOG"
chmod 600 "$LOG"
LOG_PIPE="$POD_RUNTIME/.runner_log_$$.pipe"
mkfifo "$LOG_PIPE"
tee -a "$LOG" < "$LOG_PIPE" &
TEE_PID=$!
exec > "$LOG_PIPE" 2>&1

MODEL_ID="fffoivos/greek-apertus-8b-sft-r4-full"
MODEL_SHA="54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763"
EUR_PER_USD="${DQD_EUR_PER_USD:-0.95}"
POD_STATE="$POD_RUNTIME/prime_state.json"
CONTROL_KEY_FILE="${DQD_CONTROL_KEY_FILE:-$HOME/.config/prime/key}"
HF_TOKEN_FILE="${DQD_HF_TOKEN_FILE:-$HOME/.cache/huggingface/token}"
SSH_KEY="${DQD_SSH_KEY:-$HOME/.ssh/prime_intellect_key}"
SSH_BIN="${DQD_SSH_BIN:-ssh}"
SCP_BIN="${DQD_SCP_BIN:-scp}"
CURL_BIN="${DQD_CURL_BIN:-curl}"
PYTHON_BIN="${DQD_PYTHON_BIN:-python3}"

POD_ID=""
TUNNEL_PID=""
WATCHDOG_PID=""
GPU_STARTED=0
TEARDOWN_STATUS="not_needed"
LEDGER_STOP_STATUS="not_started"

say() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*"; }

prime() {
  PRIME_INTELLECT_CONTROL_KEY="$(<"$CONTROL_KEY_FILE")" \
    "$PYTHON_BIN" "$POD_DIR/dqd_provision.py" "$@"
}

dqd() {
  "$PYTHON_BIN" "$DQD_DIR/dqd.py" --state "$STATE_DIR" "$@"
}

cleanup() {
  local original_rc=$? final_rc teardown_rc=0
  final_rc=$original_rc
  trap - EXIT INT TERM
  set +e
  [[ -n "$WATCHDOG_PID" ]] && kill "$WATCHDOG_PID" 2>/dev/null
  [[ -n "$WATCHDOG_PID" ]] && wait "$WATCHDOG_PID" 2>/dev/null
  [[ -n "$TUNNEL_PID" ]] && kill "$TUNNEL_PID" 2>/dev/null
  [[ -n "$TUNNEL_PID" ]] && wait "$TUNNEL_PID" 2>/dev/null

  local watchdog_marker="$POD_RUNTIME/watchdog_teardown_${POD_ID:-unknown}"
  if [[ -f "$watchdog_marker" ]]; then
    LEDGER_STOP_STATUS="watchdog"
    TEARDOWN_STATUS="watchdog_confirmed"
  else
    if (( GPU_STARTED )); then
      if dqd ledger gpu-stop --pod-id "$POD_ID"; then
        LEDGER_STOP_STATUS="ok"
      else
        LEDGER_STOP_STATUS="failed"
        (( final_rc == 0 )) && final_rc=91
      fi
    fi
    if [[ -n "$POD_ID" || -f "$POD_STATE" ]]; then
      if [[ -n "$POD_ID" ]]; then
        prime teardown "$POD_STATE" --pod-id "$POD_ID"
        teardown_rc=$?
      else
        prime teardown "$POD_STATE"
        teardown_rc=$?
      fi
      if (( teardown_rc == 0 )); then
        TEARDOWN_STATUS="confirmed"
      else
        TEARDOWN_STATUS="failed:$teardown_rc"
        (( final_rc == 0 )) && final_rc=92
      fi
    fi
  fi
  printf 'DQP_STAGE_RECEIPT stage=%s exit=%s ledger_stop=%s teardown=%s pod_id=%s log=%s\n' \
    "$STAGE" "$final_rc" "$LEDGER_STOP_STATUS" "$TEARDOWN_STATUS" "${POD_ID:-none}" "$LOG"
  exec 1>&- 2>&-
  wait "$TEE_PID" 2>/dev/null
  rm -f "$LOG_PIPE"
  exit "$final_rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

say "stage=$STAGE runner_start"
[[ -r "$CONTROL_KEY_FILE" && -s "$CONTROL_KEY_FILE" ]] || { say "missing Prime control key file"; exit 65; }
[[ -r "$HF_TOKEN_FILE" && -s "$HF_TOKEN_FILE" ]] || { say "missing Hugging Face token file"; exit 66; }
[[ -r "$SSH_KEY" ]] || { say "missing SSH identity"; exit 67; }
[[ -f "$STATE_DIR/forecast.json" ]] || { say "missing frozen forecast"; exit 68; }
[[ -f "$STATE_DIR/receipt.json" ]] || { say "missing frozen forecast receipt"; exit 68; }

"$PYTHON_BIN" - "$STATE_DIR/forecast.json" "$STATE_DIR/receipt.json" <<'PY'
import hashlib, json, pathlib, sys

forecast_path = pathlib.Path(sys.argv[1])
receipt_path = pathlib.Path(sys.argv[2])
forecast_bytes = forecast_path.read_bytes()
value = json.loads(forecast_bytes)
if value.get("admission_status") != "admitted" or not value.get("admitted_size"):
    raise SystemExit("forecast has no admitted measurement size")
if sum(int(v) for v in value.get("sol_reservations", {}).values()) != 120:
    raise SystemExit("forecast Sol reservations do not total 120")
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
artifact = receipt.get("artifacts", {}).get("forecast.json", {})
if artifact.get("frozen") is not True:
    raise SystemExit("forecast receipt is not frozen")
actual_sha = hashlib.sha256(forecast_bytes).hexdigest()
if artifact.get("sha256") != actual_sha:
    raise SystemExit("forecast receipt SHA-256 does not match forecast.json")
PY

say "provision_begin allowed_gpus=A100_40GB,A100_80GB,L40S_48GB max_price_usd_hr=2.5"
prime provision "$POD_STATE"
POD_ID="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["pod_id"])' "$POD_STATE")"
HOST="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["ssh_host"])' "$POD_STATE")"
USER="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("ssh_user") or "ubuntu")' "$POD_STATE")"
PORT="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("ssh_port") or 22)' "$POD_STATE")"
PRICE="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["price_hr"])' "$POD_STATE")"
say "provisioned pod_id=$POD_ID gpu_endpoint=$USER@$HOST:$PORT price_usd_hr=$PRICE"

dqd ledger gpu-start --pod-id "$POD_ID" --price-usd-hr "$PRICE" --eur-per-usd "$EUR_PER_USD"
GPU_STARTED=1

DEADLINE="$("$PYTHON_BIN" - "$STATE_DIR/ledger.jsonl" "$POD_ID" <<'PY'
import json, sys
rows=[json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
matches=[r for r in rows if r.get("record")=="gpu_start" and r.get("pod_id")==sys.argv[2]]
if not matches or not matches[-1].get("shutdown_deadline_utc"):
    raise SystemExit(1)
print(matches[-1]["shutdown_deadline_utc"])
PY
)" || { say "gpu-start did not persist a watchdog deadline"; exit 69; }
say "watchdog_arm deadline_utc=$DEADLINE"
nohup bash "$POD_DIR/watchdog.sh" "$STAGE" "$STATE_DIR" "$POD_ID" "$POD_STATE" "$LOG" "$$" \
  >/dev/null 2>&1 &
WATCHDOG_PID=$!

SSH_ARGS=(-i "$SSH_KEY" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
          -o LogLevel=ERROR -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30
          -o ServerAliveCountMax=3 "$USER@$HOST")
ssh_ready=0
for _ in $(seq 1 40); do
  if "$SSH_BIN" "${SSH_ARGS[@]}" true >/dev/null 2>&1; then ssh_ready=1; break; fi
  sleep 5
done
(( ssh_ready )) || { say "ssh readiness timeout"; exit 70; }

"$SCP_BIN" -i "$SSH_KEY" -P "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o LogLevel=ERROR "$POD_DIR/dqd_pod_setup.sh" "$USER@$HOST:~/dqd_pod_setup.sh"
say "remote_preflight_setup_begin"
setup_output="$POD_RUNTIME/${STAGE}_${STAMP}_setup.log"
set +e
"$SSH_BIN" "${SSH_ARGS[@]}" \
  'bash ~/dqd_pod_setup.sh' \
  < "$HF_TOKEN_FILE" 2>&1 | tee "$setup_output"
setup_status=("${PIPESTATUS[@]}")
set -e
setup_rc="${setup_status[0]}"
tee_rc="${setup_status[1]}"
if (( setup_rc != 0 )); then
  say "remote setup failed; last lines follow"
  tail -20 "$setup_output" || true
  exit "$setup_rc"
fi
(( tee_rc == 0 )) || { say "could not persist remote setup output"; exit 71; }
grep -Fq 'DQP_SERVE_READY' "$setup_output" || { say "remote setup returned without serve-ready marker"; exit 72; }

"$SSH_BIN" -i "$SSH_KEY" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o LogLevel=ERROR -o BatchMode=yes -o ExitOnForwardFailure=yes -N \
  -L 8000:127.0.0.1:8000 "$USER@$HOST" &
TUNNEL_PID=$!
local_ready=0
for _ in $(seq 1 20); do
  kill -0 "$TUNNEL_PID" 2>/dev/null || { say "ssh tunnel died before readiness"; exit 73; }
  if "$CURL_BIN" -fsS --max-time 2 http://127.0.0.1:8000/v1/models 2>/dev/null | grep -Fq "$MODEL_ID"; then
    local_ready=1; break
  fi
  sleep 1
done
(( local_ready )) || { say "local tunneled model readiness timeout"; exit 74; }
say "local_serve_ready model=$MODEL_ID"

case "$STAGE" in
  measurement)
    dqd rollout measurement --endpoint http://127.0.0.1:8000/v1 --model "$MODEL_ID" \
      --checkpoint-sha256 "$MODEL_SHA" --max-turns 8 --concurrency 8
    ;;
  candidates)
    dqd candidates measurement --endpoint http://127.0.0.1:8000/v1 --model "$MODEL_ID" \
      --checkpoint-sha256 "$MODEL_SHA"
    ;;
  resample)
    dqd resample measurement --targets "$STATE_DIR/measurement/resample_targets.json" --max-fresh 32 \
      --endpoint http://127.0.0.1:8000/v1 --model "$MODEL_ID" --checkpoint-sha256 "$MODEL_SHA"
    ;;
esac
say "stage=$STAGE gpu_work_complete"
