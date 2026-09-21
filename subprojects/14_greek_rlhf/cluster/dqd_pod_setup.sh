#!/bin/bash
# Runs ON THE POD (dialogue pilot). uv + vLLM, model from the HF Hub (token via env HF_TOKEN, never echoed), sha256 check, serve.
set -x
export HOME=/home/ubuntu; export PATH="$HOME/.local/bin:$PATH"
# work dir: /workspace if we can own it (some images mount it root-owned), else $HOME/work; need >= 40 GB free
WORK=/workspace; (sudo mkdir -p $WORK && sudo chown -R $(id -u):$(id -g) $WORK) 2>/dev/null || WORK=$HOME/work; mkdir -p $WORK || WORK=$HOME/work; mkdir -p $WORK
touch $WORK/.w || { echo "WORK_NOT_WRITABLE $WORK"; exit 1; }; df -h $WORK $HOME | tail -2; echo WORK_DIR $WORK
FREE_GB=$(df -Pk $WORK | awk 'NR==2{print int($4/1048576)}'); [ "$FREE_GB" -ge 40 ] || { echo "WORK_TOO_SMALL ${FREE_GB}GB"; exit 1; }
curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
CUDA_MAJOR=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | awk -F. '{print ($1>=580)?13:12}'); echo DRIVER_CUDA_MAJOR $CUDA_MAJOR
uv venv $WORK/vllmenv --python 3.12 || { echo VENV_FAILED; exit 1; }
if [ "$CUDA_MAJOR" = "13" ]; then uv pip install --python $WORK/vllmenv/bin/python vllm==0.29.0 'huggingface_hub[cli]' 2>&1 | tail -3
else uv pip install --python $WORK/vllmenv/bin/python --torch-backend=cu128 --override <(echo torchcodec) vllm==0.19.1 'huggingface_hub[cli]' 2>&1 | tail -3; fi
$WORK/vllmenv/bin/python -c "import vllm, torch; print('VLLM_VERSION', vllm.__version__, 'TORCH', torch.__version__, 'cuda', torch.version.cuda)"
set +x; export HF_HUB_ENABLE_HF_TRANSFER=0; $WORK/vllmenv/bin/hf download fffoivos/greek-apertus-8b-sft-r4-full --local-dir $WORK/R4_full_ep1 --token "$HF_TOKEN" 2>&1 | tail -2; set -x
ls -la $WORK/R4_full_ep1 | head -20
sha256sum $WORK/R4_full_ep1/*.safetensors
cat > $WORK/serve.sh <<S
#!/bin/bash
export HOME=/home/ubuntu; export VLLM_USE_FLASHINFER_SAMPLER=0; export VLLM_NO_USAGE_STATS=1; export DO_NOT_TRACK=1
cd $WORK; exec $WORK/vllmenv/bin/vllm serve $WORK/R4_full_ep1 --served-model-name fffoivos/greek-apertus-8b-sft-r4-full --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.88 --port 8000 --host 127.0.0.1
S
chmod +x $WORK/serve.sh; nohup $WORK/serve.sh > $WORK/serve.log 2>&1 &
SPID=$!
for i in $(seq 1 60); do curl -s http://127.0.0.1:8000/v1/models | grep -q "greek-apertus-8b-sft-r4-full" && { echo SERVE_READY; break; }; kill -0 $SPID 2>/dev/null || { echo SERVE_DIED; grep -E "Error|error" $WORK/serve.log | tail -3; break; }; sleep 10; done
tail -3 $WORK/serve.log; echo SETUP_DONE
