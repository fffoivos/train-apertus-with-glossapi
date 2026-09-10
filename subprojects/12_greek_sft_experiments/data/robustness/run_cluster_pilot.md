# Live-dialogue collection on the cluster (prepared 2026-09-10; NOT launched — needs the owner's go and a cap raise)
1. Serve arm B (bf16) with vLLM on one GPU of a workbench: `bash cluster/serve_models.sh` (one model per GPU; served-model name = the checkpoint dir name), then the SSH tunnel with -4: `ssh -4 -N -L 8092:localhost:<port> clariden`.
2. Pathology check on fixed prefixes: `LIVE_MODEL=<served name> python3 loop_check.py live/loop_check_vllm.json bf16` after pointing PORTS['bf16'] at http://127.0.0.1:8092/v1 (compare with the 8-bit MLX rows already in the dialogues).
3. Pilot: `LIVE_MODEL=<served name> python3 live_dialogues.py live/pilot --n 200 --seed 3 --stratified --concurrency 8 --url http://127.0.0.1:8092/v1` (≤ 8 streams through the tunnel; ~1 nh).
4. Then targets/checks per docs/CORRECTING_DATASET_DESIGN_20260910.md §8 (typed checks, information boundary, calibration set) — not yet written.
