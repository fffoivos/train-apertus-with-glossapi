# Review brief R-RL1 — sampling readiness for round 3 (generator 0.2 release)

## Stage goal
Correct, reproducible and affordable reply sampling for the round-3 prompt set, so that every new prompt gets replies from the target checkpoint
that can be judged and paired. Final product of the phase: all new prompts with their replies evaluated, on a votes-style review page.

## Scope
- Prompt set: `data/rlhf/round3/round3_all.jsonl` built by `data/rlhf/round3/stage.py build` from active prompts of `data/rlhf/generator_v02/runs/*/prompts.jsonl` plus the 39 forum maths selections of `manifest_round3.json` (manifest v2). Frozen at build time; hash in the receipt.
- Sampler: `data/rlhf/sample.py` (T 0.8, top-p 0.95, max 1,500 tokens, no system prompt, per-row n). Same settings as rounds 1 and 2.
- Change disclosed: n=32 replies per prompt sampled up front in one cluster window (round 2: 8, with later escalation). Judging is staged: replies 0–7 for all prompts; 8–15 only for prompts without an eligible positive and a lower reply; 16–31 only if still none (owner rule: escalate up to 32). Rationale: one CSCS window instead of three; judging cost is only spent where needed.
- Cluster: `cluster/rlhf_sample.sh` (preflight budget guard, one workbench on `debug`, vLLM via `serve_models.sh`, tunnel, sampler, close, ledger). Checkpoint `eval_copies/R4_full_ep1` (G4F6P1 = `fffoivos/greek-apertus-8b-sft-r4-full`).
- Routing after sampling (`stage.py split`): maths_content maths → maths judge only; embedded → maths judge and general judge v2.4; none → general judge v2.4.

## Context to read
- Two-stream plan §3 (import contract) and §10 (R-RL1 row); maths plan A1–A5; spec v1.0.2 §5.4, §5.6.
- `docs/RLHF_COORDINATION/CURRENT_VERSIONS.md` (model, sampler, budget rows); `execution_state.json`; `cluster/preflight.sh`, `cluster/ledger.sh`.

## Acceptance criteria
Blocking:
1. The served checkpoint is G4F6P1 (sha256 verified on the cluster, recorded below).
2. Sampling settings equal the round-2 baseline except the disclosed n change.
3. Staged judging cannot credit a maths or embedded-maths prompt from the general judge alone, and cannot use a held (ambiguous or unresolved reference) maths prompt as positive.
4. The forecast fits the CSCS cap, or the shortfall is stated.
Major:
5. Outputs carry prompt id, logical id, generator version, labels and routing needed by the import contract.

## Evidence
- Checkpoint verification: see `R-RL1_evidence.txt`.
- Budget: CHF 222.92 of CHF 240 used before this window; previous sampling windows cost about CHF 0.1 each.
