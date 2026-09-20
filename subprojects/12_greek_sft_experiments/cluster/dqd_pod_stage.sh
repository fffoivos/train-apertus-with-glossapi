#!/bin/bash
# Dialogue pilot: one paid GPU window. Usage: cluster/dqd_pod_stage.sh <smoke|measurement|candidates> [max-turns]
# Provisions an A100_40GB pod, serves the checkpoint from the Hub, tunnels port 8000, runs the stage's GPU commands through dqd.py,
# then ALWAYS stops the ledger and tears the pod down (trap). Sol-only stages (openings, annotate, report, forecast) run outside this script.
set -u
STAGE=$1; TURNS=${2:-}; SUB=/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments
DQD=$SUB/data/rlhf/dialogue_quality_depth; STATE=$SUB/logs/dqd_pod.json; LOG=$SUB/logs/dqd_pod_${STAGE}.log
MODEL=fffoivos/greek-apertus-8b-sft-r4-full; SHA=54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763; EUR_PER_USD=0.95
KEY=$HOME/.ssh/prime_intellect_key; PP=/Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts/prime_provision.py
say(){ printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }
POD_ID=""; TUNNEL_PID=""
cleanup(){
  say "cleanup: stopping ledger + tearing down pod ${POD_ID:-none}"
  [ -n "$TUNNEL_PID" ] && kill "$TUNNEL_PID" 2>/dev/null
  if [ -n "$POD_ID" ]; then
    (cd $DQD && python3 dqd.py --state runtime ledger gpu-stop --pod-id "$POD_ID" 2>&1 | tail -1 | tee -a "$LOG")
    PRIME_INTELLECT_CONTROL_KEY=$(cat ~/.config/prime/key) GREEK_SWEEP_POD_STATE=$STATE python3 $PP teardown --no-save --force 2>&1 | tail -3 | tee -a "$LOG"
  fi
  say "cleanup done"
}
trap cleanup EXIT
say "=== stage $STAGE start ==="
cd $DQD
# 1. pod
python3 $SUB/cluster/dqd_provision.py $STATE 2>&1 | tail -5 | tee -a "$LOG"
POD_ID=$(python3 -c "import json;print(json.load(open('$STATE'))['pod_id'])") || { say "no pod state; abort"; exit 1; }
HOST=$(python3 -c "import json;d=json.load(open('$STATE'));print(d['ssh_host'])"); USER=$(python3 -c "import json;d=json.load(open('$STATE'));print(d.get('ssh_user','ubuntu'))"); PORT=$(python3 -c "import json;d=json.load(open('$STATE'));print(d.get('ssh_port',22))"); PRICE=$(python3 -c "import json;d=json.load(open('$STATE'));print(d.get('price_hr',1.99))")
say "pod $POD_ID $USER@$HOST:$PORT \$$PRICE/h"
SSH="ssh -i $KEY -p $PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o BatchMode=yes -o ConnectTimeout=25 -o ServerAliveInterval=30 $USER@$HOST"
for i in $(seq 1 20); do $SSH true 2>/dev/null && break; sleep 15; done; $SSH true || { say "ssh never came up"; exit 1; }
python3 dqd.py --state runtime ledger gpu-start --pod-id "$POD_ID" --price-usd-hr "$PRICE" --eur-per-usd $EUR_PER_USD 2>&1 | tail -1 | tee -a "$LOG"
# 2. setup + serve (HF token passed as an env var over ssh, never printed)
scp -i $KEY -P $PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR $SUB/cluster/dqd_pod_setup.sh $USER@$HOST:/home/ubuntu/setup.sh
$SSH "HF_TOKEN=$(cat ~/.cache/huggingface/token) bash /home/ubuntu/setup.sh" > $SUB/logs/dqd_pod_${STAGE}_setup.log 2>&1
grep -q SERVE_READY $SUB/logs/dqd_pod_${STAGE}_setup.log || { say "serve not ready; see setup log"; grep -E "VLLM_VERSION|DRIVER|sha256|Error|error" $SUB/logs/dqd_pod_${STAGE}_setup.log | tail -8 | tee -a "$LOG"; exit 1; }
say "serve ready: $(grep -E 'VLLM_VERSION|DRIVER_CUDA' $SUB/logs/dqd_pod_${STAGE}_setup.log | tr '\n' ' ')"; grep "safetensors" $SUB/logs/dqd_pod_${STAGE}_setup.log | tee -a "$LOG"
ssh -i $KEY -p $PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -N -L 8000:127.0.0.1:8000 $USER@$HOST & TUNNEL_PID=$!
sleep 5; curl -s http://127.0.0.1:8000/v1/models | head -c 200 | tee -a "$LOG"; echo
# 3. stage commands
case $STAGE in
  smoke)       python3 dqd.py --state runtime rollout smoke --endpoint http://127.0.0.1:8000/v1 --model $MODEL --checkpoint-sha256 $SHA --max-turns ${TURNS:-3} --concurrency 6 2>&1 | tee -a "$LOG" ;;
  measurement) python3 dqd.py --state runtime rollout measurement --endpoint http://127.0.0.1:8000/v1 --model $MODEL --checkpoint-sha256 $SHA --max-turns ${TURNS:-8} --concurrency 8 2>&1 | tee -a "$LOG" ;;
  candidates)  python3 dqd.py --state runtime candidates measurement --endpoint http://127.0.0.1:8000/v1 --model $MODEL --checkpoint-sha256 $SHA 2>&1 | tee -a "$LOG" ;;
  *) say "unknown stage"; exit 1 ;;
esac
say "=== stage $STAGE GPU work finished ==="
