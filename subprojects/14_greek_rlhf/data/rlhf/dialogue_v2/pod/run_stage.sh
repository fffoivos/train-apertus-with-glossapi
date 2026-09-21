#!/usr/bin/env bash
# Sole GPU entry point for dialogue v2: bash data/rlhf/dialogue_v2/pod/run_stage.sh <collect|branch>
# Copied from data/rlhf/dialogue_quality_depth/pod/run_stage.sh (CK3/CK5-reviewed discipline): frozen-forecast gate,
# GET /pods gate, ranked offers with HTTP-error fallback, remote preflight + pinned model sha check, fail-fast serve,
# ssh tunnel, programme ledger gpu-start/gpu-stop, EXIT trap, independent watchdog, GET-confirmed deletion.
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^(collect|branch)$ ]]; then
  printf 'usage: bash pod/run_stage.sh <collect|branch>\n' >&2
  exit 64
fi

STAGE="$1"
export DV2_STAGE="$STAGE"
POD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$POD_DIR/.." && pwd)"
SUBPROJECT="$(cd "$V2_DIR/../../.." && pwd)"
RUNTIME="${DV2_RUNTIME_DIR:-$V2_DIR/runtime}"
POD_RUNTIME="$RUNTIME/pod"
mkdir -p "$POD_RUNTIME" "$SUBPROJECT/logs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="${DV2_LOG_FILE:-$SUBPROJECT/logs/dialogue_v2_${STAGE}_${STAMP}.log}"
touch "$LOG"
chmod 600 "$LOG"
LOG_PIPE="$POD_RUNTIME/.runner_log_$$.pipe"
mkfifo "$LOG_PIPE"
tee -a "$LOG" < "$LOG_PIPE" &
TEE_PID=$!
exec > "$LOG_PIPE" 2>&1

MODEL_ID="fffoivos/greek-apertus-8b-sft-r4-full"
MODEL_SHA="54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763"
POD_STATE="$POD_RUNTIME/prime_state.json"
TEARDOWN_RECORD="$POD_RUNTIME/teardown_records.jsonl"
CONTROL_KEY_FILE="${DV2_CONTROL_KEY_FILE:-$HOME/.config/prime/key}"
HF_TOKEN_FILE="${DV2_HF_TOKEN_FILE:-$HOME/.cache/huggingface/token}"
SSH_KEY="${DV2_SSH_KEY:-$HOME/.ssh/prime_intellect_key}"
SSH_BIN="${DV2_SSH_BIN:-ssh}"
SCP_BIN="${DV2_SCP_BIN:-scp}"
CURL_BIN="${DV2_CURL_BIN:-curl}"
PYTHON_BIN="${DV2_PYTHON_BIN:-python3}"
LOCAL_PORT="${DV2_LOCAL_PORT:-8000}"

POD_ID=""
TUNNEL_PID=""
WATCHDOG_PID=""
GPU_STARTED=0
TEARDOWN_STATUS="not_needed"
LEDGER_STOP_STATUS="not_started"

say() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*"; }

provision_py() {
  PRIME_INTELLECT_CONTROL_KEY="$(<"$CONTROL_KEY_FILE")" "$PYTHON_BIN" "$POD_DIR/dv2_provision.py" "$@"
}

dv2() {
  "$PYTHON_BIN" "$V2_DIR/dv2.py" "$@"
}

cleanup() {
  local original_rc=$? final_rc teardown_rc=0
  final_rc=$original_rc
  trap - EXIT INT TERM
  set +e
  [[ -n "$TUNNEL_PID" ]] && kill "$TUNNEL_PID" 2>/dev/null
  [[ -n "$TUNNEL_PID" ]] && wait "$TUNNEL_PID" 2>/dev/null

  local watchdog_marker="$POD_RUNTIME/watchdog_teardown_${POD_ID:-unknown}"
  if [[ -f "$watchdog_marker" ]]; then
    TEARDOWN_STATUS="watchdog_confirmed"
    LEDGER_STOP_STATUS="watchdog"
  else
    if [[ -n "$POD_ID" || -f "$POD_STATE" ]]; then
      if [[ -n "$POD_ID" ]]; then
        provision_py teardown "$POD_STATE" --pod-id "$POD_ID" --record "$TEARDOWN_RECORD"
      else
        provision_py teardown "$POD_STATE" --record "$TEARDOWN_RECORD"
      fi
      teardown_rc=$?
      if (( teardown_rc == 0 )); then
        TEARDOWN_STATUS="confirmed"
      else
        TEARDOWN_STATUS="failed:$teardown_rc"
        (( final_rc == 0 )) && final_rc=92
      fi
    fi
    if (( GPU_STARTED )); then
      if dv2 ledger gpu-stop --pod-id "$POD_ID" --teardown-record "$TEARDOWN_RECORD"; then
        LEDGER_STOP_STATUS="ok"
      else
        LEDGER_STOP_STATUS="failed"
        (( final_rc == 0 )) && final_rc=91
      fi
    fi
  fi
  # The watchdog stays armed unless deletion is confirmed.
  if [[ -n "$WATCHDOG_PID" && "$TEARDOWN_STATUS" != failed* ]]; then
    kill "$WATCHDOG_PID" 2>/dev/null
    wait "$WATCHDOG_PID" 2>/dev/null
  fi
  printf 'DV2_STAGE_RECEIPT stage=%s exit=%s ledger_stop=%s teardown=%s pod_id=%s log=%s\n' \
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
if lsof -nP -iTCP:"$LOCAL_PORT" -sTCP:LISTEN >/dev/null 2>&1; then say "local port $LOCAL_PORT busy"; exit 75; fi

GATE_JSON="$(dv2 gate --stage "$STAGE" | tail -1)"
say "gate $GATE_JSON"
[[ "$GATE_JSON" == DV2_OK* ]] || { say "frozen forecast or ledger gate failed"; exit 68; }
MAX_SESSION_MINUTES="$("$PYTHON_BIN" -c 'import json,sys; print(json.loads(sys.argv[1].split(" ",2)[2])["max_session_minutes"])' "$GATE_JSON")"
PRICE_CAP="$("$PYTHON_BIN" -c 'import json,sys; print(json.loads(sys.argv[1].split(" ",2)[2])["price_cap_usd_hr"])' "$GATE_JSON")"
[[ ! -f "$POD_STATE" ]] || { say "stale pod state file exists; refusing to provision"; exit 76; }

say "provision_begin allowed_gpus=A100_40GB,A100_80GB,L40S_48GB max_price_usd_hr=$PRICE_CAP max_session_minutes=$MAX_SESSION_MINUTES"
set +e
provision_py provision "$POD_STATE" --max-price "$PRICE_CAP"
provision_rc=$?
set -e
if [[ -f "$POD_STATE" ]]; then
  POD_ID="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["pod_id"])' "$POD_STATE")"
fi
(( provision_rc == 0 )) || { say "provisioning failed rc=$provision_rc"; exit "$provision_rc"; }
HOST="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["ssh_host"])' "$POD_STATE")"
USER_NAME="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("ssh_user") or "ubuntu")' "$POD_STATE")"
PORT="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("ssh_port") or 22)' "$POD_STATE")"
PRICE="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["price_hr"])' "$POD_STATE")"
POST_UTC="$("$PYTHON_BIN" -c 'import json,sys,datetime as d; print(d.datetime.fromtimestamp(json.load(open(sys.argv[1]))["created_at"], d.timezone.utc).isoformat())' "$POD_STATE")"
say "provisioned pod_id=$POD_ID endpoint=$USER_NAME@$HOST:$PORT price_usd_hr=$PRICE post_utc=$POST_UTC"

dv2 ledger gpu-start --pod-id "$POD_ID" --stage "$STAGE" --price-usd-hr "$PRICE" --post-utc "$POST_UTC" \
  --max-session-minutes "$MAX_SESSION_MINUTES"
GPU_STARTED=1
nohup bash "$POD_DIR/watchdog.sh" "$STAGE" "$RUNTIME" "$POD_ID" "$POD_STATE" "$LOG" "$$" >/dev/null 2>&1 &
WATCHDOG_PID=$!
say "watchdog_armed pid=$WATCHDOG_PID"

SSH_ARGS=(-i "$SSH_KEY" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
          -o LogLevel=ERROR -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30
          -o ServerAliveCountMax=3 "$USER_NAME@$HOST")
ssh_ready=0
for _ in $(seq 1 40); do
  if "$SSH_BIN" "${SSH_ARGS[@]}" true >/dev/null 2>&1; then ssh_ready=1; break; fi
  sleep 5
done
(( ssh_ready )) || { say "ssh readiness timeout"; exit 70; }

"$SCP_BIN" -i "$SSH_KEY" -P "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o LogLevel=ERROR "$POD_DIR/dv2_pod_setup.sh" "$USER_NAME@$HOST:~/dv2_pod_setup.sh"
say "remote_preflight_setup_begin"
setup_output="$POD_RUNTIME/${STAGE}_${STAMP}_setup.log"
set +e
"$SSH_BIN" "${SSH_ARGS[@]}" 'bash ~/dv2_pod_setup.sh' < "$HF_TOKEN_FILE" 2>&1 | tee "$setup_output"
setup_status=("${PIPESTATUS[@]}")
set -e
setup_rc="${setup_status[0]}"
if (( setup_rc != 0 )); then
  say "remote setup failed rc=$setup_rc; last lines follow"
  tail -20 "$setup_output" || true
  exit "$setup_rc"
fi
grep -Fq 'DV2_SERVE_READY' "$setup_output" || { say "remote setup returned without serve-ready marker"; exit 72; }
grep -Fq "DV2_MODEL_SHA_OK sha256=$MODEL_SHA" "$setup_output" || { say "model sha marker missing"; exit 72; }

"$SSH_BIN" -i "$SSH_KEY" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o LogLevel=ERROR -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N \
  -L "$LOCAL_PORT:127.0.0.1:8000" "$USER_NAME@$HOST" &
TUNNEL_PID=$!
local_ready=0
for _ in $(seq 1 30); do
  kill -0 "$TUNNEL_PID" 2>/dev/null || { say "ssh tunnel died before readiness"; exit 73; }
  if "$CURL_BIN" -fsS --max-time 2 "http://127.0.0.1:$LOCAL_PORT/v1/models" 2>/dev/null | grep -Fq "$MODEL_ID"; then
    local_ready=1; break
  fi
  sleep 1
done
(( local_ready )) || { say "local tunneled model readiness timeout"; exit 74; }
say "local_serve_ready model=$MODEL_ID"

ENDPOINT="http://127.0.0.1:$LOCAL_PORT/v1"
dv2 preflight --stage "$STAGE" --endpoint "$ENDPOINT" --model "$MODEL_ID" --checkpoint-sha256 "$MODEL_SHA"
case "$STAGE" in
  collect)
    # DV2_CASES: optional space-separated case ids (e.g. a rerun of conversations that failed on infrastructure)
    dv2 collect --set "${DV2_CASE_SET:-v2}" --endpoint "$ENDPOINT" --model "$MODEL_ID" --checkpoint-sha256 "$MODEL_SHA" ${DV2_CASES:+--cases $DV2_CASES}
    ;;
  branch)
    # DV2_TOPUP_POINTS: optional space-separated point ids that get four extra candidates (never automatic)
    dv2 branch-sample --set "${DV2_CASE_SET:-v2}" --endpoint "$ENDPOINT" --model "$MODEL_ID" --checkpoint-sha256 "$MODEL_SHA" \
      ${DV2_TOPUP_POINTS:+--topup-points $DV2_TOPUP_POINTS} ${DV2_CANDIDATES:+--candidates $DV2_CANDIDATES}
    ;;
esac
say "stage=$STAGE gpu_work_complete"
