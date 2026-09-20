#!/usr/bin/env bash
#SBATCH --account=a0140
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=72
#SBATCH --mem=640G
#SBATCH --time=00:30:00
#SBATCH --job-name=gmmlu200_protocol
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/gmmlu200_protocol_%j.out
set -euo pipefail
: "${GREEKMMLU_BUNDLE:?set immutable bundle path}"
: "${GREEKMMLU_OUTPUT:?set a new output directory}"
: "${GREEKMMLU_PARQUET:?set pinned All/test parquet path}"
: "${ORIGINAL_KRIKRI:?set pinned original Krikri snapshot}"
: "${G3F2P1:?set pinned G3F2P1 evaluation checkpoint}"
test ! -e "$GREEKMMLU_OUTPUT"
test -f "$GREEKMMLU_PARQUET"
test -f "$GREEKMMLU_BUNDLE/diagnostic200_ids.jsonl"
test -d "$ORIGINAL_KRIKRI"
test -d "$G3F2P1"
mkdir "$GREEKMMLU_OUTPUT"

srun --exclusive --nodes=1 --ntasks=1 --gpus-per-task=1 --cpus-per-task=72 \
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc \
  'source /iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/activate; exec python "$@"' bash \
  "$GREEKMMLU_BUNDLE/greekmmlu200_dual_protocol.py" \
  --parquet "$GREEKMMLU_PARQUET" --ids "$GREEKMMLU_BUNDLE/diagnostic200_ids.jsonl" \
  --model "original_krikri=$ORIGINAL_KRIKRI" --output "$GREEKMMLU_OUTPUT/original_krikri.json" &
pid_original=$!

srun --exclusive --nodes=1 --ntasks=1 --gpus-per-task=1 --cpus-per-task=72 \
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc \
  'source /iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/activate; exec python "$@"' bash \
  "$GREEKMMLU_BUNDLE/greekmmlu200_dual_protocol.py" \
  --parquet "$GREEKMMLU_PARQUET" --ids "$GREEKMMLU_BUNDLE/diagnostic200_ids.jsonl" \
  --model "G3F2P1=$G3F2P1" --output "$GREEKMMLU_OUTPUT/G3F2P1.json" &
pid_g3f2p1=$!

wait "$pid_original"
wait "$pid_g3f2p1"
uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc \
  'source /iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/activate; exec python "$@"' bash \
  "$GREEKMMLU_BUNDLE/verify_greekmmlu200_results.py" \
  --ids "$GREEKMMLU_BUNDLE/diagnostic200_ids.jsonl" \
  --original "$GREEKMMLU_OUTPUT/original_krikri.json" \
  --g3f2p1 "$GREEKMMLU_OUTPUT/G3F2P1.json" \
  --output "$GREEKMMLU_OUTPUT/verification.json"
