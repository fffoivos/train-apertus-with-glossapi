#!/usr/bin/env bash
#SBATCH --account=a0140
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=01:25:00
#SBATCH --job-name=krikri_v15_peer
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/krikri_v15_peer_%j.out
set -euo pipefail
: "${PEER_BUNDLE:?set PEER_BUNDLE to the immutable deployed bundle}"
: "${PEER_OUTPUT:?set PEER_OUTPUT to a new attempt result path}"
uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc \
  'source /iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/activate; exec python "$@"' bash \
  "$PEER_BUNDLE/peer_eval_adapter.py" \
    --manifest "$PEER_BUNDLE/peer_eval_science_manifest.json" \
    --output "$PEER_OUTPUT" \
    --campaign-id wave2-krikri-v15-peer \
    --evaluator-id krikri-v15-fixed \
    --iteration 0 \
    --attempt 1 \
    --contract-digest "$(sha256sum "$PEER_BUNDLE/peer_eval_science_manifest.json" | cut -d' ' -f1)"
