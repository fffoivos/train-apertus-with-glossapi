#!/usr/bin/env bash
# Runs on the provisioned pod. Secret tracing is deliberately never enabled.
set -Eeuo pipefail

MODEL_ID="fffoivos/greek-apertus-8b-sft-r4-full"
EXPECTED_SHA="54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763"
MIN_FREE_GB=40
MIN_GPU_MEMORY_MB=38000
# Consume the token from stdin before any child command can read it. It remains
# a non-exported shell value until the single Hub download command below.
# `read` returns non-zero at EOF even when it successfully populated an
# unterminated final line. Keep those bytes; the explicit non-empty gate below
# distinguishes a valid no-newline token from genuinely empty stdin.
hub_token=""
IFS= read -r hub_token || true

fail() {
  local code="$1" reason="$2"
  printf 'DQP_SETUP_FAIL code=%s reason=%s\n' "$code" "$reason" >&2
  exit "$code"
}

# Every preflight check is complete before curl, uv, pip, or Hub access.
WORK="${DQD_POD_WORK_PRIMARY:-/workspace}"
if ! { sudo -n mkdir -p "$WORK" && sudo -n chown "$(id -u):$(id -g)" "$WORK"; } 2>/dev/null; then
  WORK="${DQD_POD_WORK_FALLBACK:-$HOME/work}"
fi
mkdir -p "$WORK" 2>/dev/null || fail 41 "work_directory_create:$WORK"
probe="$WORK/.dqd-write-probe"
: > "$probe" 2>/dev/null || fail 41 "work_directory_not_writable:$WORK"
rm -f "$probe"

free_kb="$(df -Pk "$WORK" 2>/dev/null | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || fail 42 "disk_free_unreadable:$WORK"
free_gb=$((free_kb / 1048576))
(( free_gb >= MIN_FREE_GB )) || fail 42 "disk_free_below_${MIN_FREE_GB}GB:actual_${free_gb}GB"

driver_version="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | tr -d '[:space:]')"
driver_major="${driver_version%%.*}"
[[ "$driver_major" =~ ^[0-9]+$ ]] || fail 43 "driver_version_unreadable"
if (( driver_major >= 580 )); then
  cuda_track=13
  vllm_version="0.29.0"
else
  cuda_track=12
  vllm_version="0.19.1"
fi

gpu_memory_mb="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -dc '0-9')"
[[ "$gpu_memory_mb" =~ ^[0-9]+$ ]] || fail 44 "gpu_memory_unreadable"
(( gpu_memory_mb >= MIN_GPU_MEMORY_MB )) || fail 44 "gpu_memory_below_${MIN_GPU_MEMORY_MB}MB:actual_${gpu_memory_mb}MB"

printf 'DQP_PREFLIGHT_OK work=%s free_gb=%s driver=%s cuda_track=%s gpu_memory_mb=%s vllm=%s\n' \
  "$WORK" "$free_gb" "$driver_version" "$cuda_track" "$gpu_memory_mb" "$vllm_version"

export PATH="$HOME/.local/bin:$PATH"
# Images may already provide uv.  Do not make a second network endpoint a
# prerequisite in that case.  If it is absent, make the standalone bootstrap
# resilient to a transient astral.sh failure and fall back to the image's pip;
# the following vLLM install remains the same for each CUDA track.
if ! command -v uv >/dev/null 2>&1; then
  uv_installer="$WORK/uv-installer.sh"
  if curl -LsSf --retry 5 --retry-all-errors --connect-timeout 20 --max-time 120 \
      -o "$uv_installer" https://astral.sh/uv/install.sh \
      && sh "$uv_installer" >/dev/null 2>&1; then
    :
  fi
  rm -f "$uv_installer"
  if ! command -v uv >/dev/null 2>&1; then
    python3 -m pip install --user --disable-pip-version-check uv >/dev/null \
      || fail 45 "uv_install"
  fi
fi
command -v uv >/dev/null 2>&1 || fail 45 "uv_missing"
uv venv "$WORK/vllmenv" --python 3.12 >/dev/null || fail 45 "venv_create"
if (( cuda_track == 13 )); then
  uv pip install --python "$WORK/vllmenv/bin/python" "vllm==$vllm_version" 'huggingface_hub[cli]' \
    || fail 45 "vllm_install_cuda13"
else
  uv pip install --python "$WORK/vllmenv/bin/python" --torch-backend=cu128 \
    --override <(echo torchcodec) "vllm==$vllm_version" 'huggingface_hub[cli]' \
    || fail 45 "vllm_install_cuda12"
fi
"$WORK/vllmenv/bin/python" -c \
  "import torch,vllm; print('DQP_VLLM_OK version='+vllm.__version__+' torch='+torch.__version__+' cuda='+str(torch.version.cuda))" \
  || fail 45 "vllm_import"

MODEL_DIR="$WORK/R4_full_ep1"
mkdir -p "$MODEL_DIR"
[[ -n "$hub_token" ]] || fail 45 "hf_token_missing"
HF_TOKEN="$hub_token" HF_HUB_ENABLE_HF_TRANSFER=0 \
  "$WORK/vllmenv/bin/hf" download "$MODEL_ID" --local-dir "$MODEL_DIR" >/dev/null \
  || fail 45 "model_download"
unset hub_token

[[ -f "$MODEL_DIR/model.safetensors" ]] || fail 46 "model_safetensors_missing"
actual_sha="$(sha256sum "$MODEL_DIR/model.safetensors" | awk '{print $1}')"
[[ "$actual_sha" == "$EXPECTED_SHA" ]] || fail 46 "model_sha256_mismatch:actual_$actual_sha"
printf 'DQP_MODEL_SHA_OK sha256=%s\n' "$actual_sha"

[[ -f "$MODEL_DIR/config.json" ]] || fail 47 "config_json_missing"
max_model_len="$("$WORK/vllmenv/bin/python" - "$MODEL_DIR/config.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8")).get("max_position_embeddings")
if not isinstance(value, int) or value <= 0:
    raise SystemExit(1)
print(value)
PY
)" || fail 47 "max_position_embeddings_invalid"
[[ "$max_model_len" =~ ^[0-9]+$ ]] || fail 47 "max_position_embeddings_invalid"
printf 'DQP_MODEL_CONFIG_OK max_position_embeddings=%s\n' "$max_model_len"

cat > "$WORK/serve.sh" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
export VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
exec "$WORK/vllmenv/bin/vllm" serve "$MODEL_DIR" \\
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len "$max_model_len" \\
  --gpu-memory-utilization 0.88 --port 8000 --host 127.0.0.1
EOF
chmod +x "$WORK/serve.sh"
nohup "$WORK/serve.sh" >"$WORK/serve.log" 2>&1 &
server_pid=$!
printf '%s\n' "$server_pid" > "$WORK/serve.pid"

for _ in $(seq 1 60); do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    printf 'DQP_SETUP_FAIL code=48 reason=serve_process_died\n' >&2
    tail -20 "$WORK/serve.log" >&2 || true
    exit 48
  fi
  if curl -fsS --max-time 2 http://127.0.0.1:8000/v1/models 2>/dev/null | grep -Fq "$MODEL_ID"; then
    printf 'DQP_SERVE_READY model=%s max_model_len=%s pid=%s\n' "$MODEL_ID" "$max_model_len" "$server_pid"
    exit 0
  fi
  sleep 2
done
printf 'DQP_SETUP_FAIL code=49 reason=serve_ready_timeout\n' >&2
tail -20 "$WORK/serve.log" >&2 || true
exit 49
