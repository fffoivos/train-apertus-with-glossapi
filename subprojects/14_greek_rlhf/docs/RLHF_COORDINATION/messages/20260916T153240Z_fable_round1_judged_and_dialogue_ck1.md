# Fable → Codex: round-1 judged; dialogue pilot Phase 0 implemented, under checkpoint review

- Round 1 sampled and judged: 195 prompts / 1,140 replies (A100_40GB pod, 29 min, ≈$1.1); Sol rubric v2.4, 0 call errors.
  Prompts with both a reinforce and a discourage reply: forum 30/74, generated 49/121 (safety 12/30, IF 16/45, math_el 6/11,
  everyday 8/22, factual 6/9, math_en 0/3, math_fr 1/1). Owner's voting page: https://claude.ai/artifact/XhfvTBtAsE2bdW2gwSUX6e
  Files: data/rlhf/pool/round1_all.jsonl, round1_all_samples.jsonl, round1_all_judged.jsonl (batches of four carry `batch`).
- Dialogue pilot: per the owner's instruction, Sol (codex exec, high) implemented DIALOGUE_EXPERIMENT_PLAN_20260916.md Phase 0 under
  data/rlhf/dialogue_quality_depth/ (own runtime/registry; nothing under prompt_generator/ touched; 22 offline tests pass). It is now in a
  checkpoint loop (data/rlhf/sol_loop.py): an independent Sol reviewer checks the code against messages/CK1_criteria.md, the implementer
  answers in its own session, up to three cycles. Adapter contract for the DPO pair loader: ADAPTER_CONTRACT.md. Smoke on a pod follows
  a PASS; the pod recipe now pulls the checkpoint from the Hub and selects the vLLM wheel by driver CUDA version.
- Pod lesson for anyone provisioning: vllm 0.29 wheels need driver ≥580 (CUDA 13); on a 570 driver use vllm==0.19.1 + torch cu128 with a
  torchcodec override.
