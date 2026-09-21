# Execution brief for the dialogue executor (Opus) — 17 Sept 2026

Owner instruction: send an Opus agent to Prime Intellect to start the dialogue work, with the previous Prime Intellect work and the
execution plan. You are that agent. You run autonomously: nobody answers questions mid-run. Decide within this brief, record decisions,
and stop only at the gates named below.

## 1. What you execute (Workstream B, generator 0.3 corrections)
- Primary specification: `docs/RLHF_COORDINATION/DIALOGUE_V2_EXECUTION_PLAN_20260917.md` (Stages A, B1, B2, B3, C, D, budget §9, handoff §10).
- Six demo cases: `docs/RLHF_COORDINATION/REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md`.
- Parent plan: `docs/RLHF_COORDINATION/RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md` — §0 aspects ([PG] prompt generation vs [RLHF]), §3 import contract, §4a terms and dialogue corrections, §7 release gate, §9 budget.
- Terms: `docs/SEED_LABEL_SPEC_20260917.md` (v0.4; the owner approved the terminology) and the prompt-ready glossary `data/rlhf/prompts/seed_label_definitions_v1.md` (sha16 84b30fabd02a15cc at brief time; recompute and record it).
- Versions: `docs/RLHF_COORDINATION/CURRENT_VERSIONS.md`. Target checkpoint G4F6P1 = R4_full epoch 1 = `fffoivos/greek-apertus-8b-sft-r4-full`, model.safetensors sha256 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763.
- Evidence to read first: `docs/RLHF_COORDINATION/OPUS_FEEDBACK_20260917.md` (§2 adaptive user, ME021; §4 branch selection); the pilot's result `data/rlhf/dialogue_quality_depth/runtime/measurement/final_recommendation.md`; the pilot prompts as sent (render with `python3 data/rlhf/dialogue_pipeline_page.py /tmp/x.html` or read `user_policy.txt`, `turn_quality.txt`, `openings.py`, `rank.py` in `data/rlhf/dialogue_quality_depth/`).

## 2. How we ran Prime Intellect before (read all of it before provisioning)
1. `logs/prime_round2.log` — manual run that worked first time; line starting "RECIPE (verbatim, for the next agent)" is the step list.
2. `logs/prime_round1.log` — five failed vLLM starts and their causes.
3. `data/rlhf/dialogue_quality_depth/pod/` — the Sol-built, reviewed runner: `run_stage.sh` (offer fallback on HTTP 503, remote preflight, driver-to-vLLM wheel, Hub download with sha check, max_model_len read from config.json, fail-fast serve loop, ssh tunnel, ledger gpu-start/gpu-stop, EXIT trap, independent `watchdog.sh`, DELETE_CONFIRMED receipt), `dqd_pod_setup.sh`, `dqd_provision.py`. It implements only the old protocol's stages (measurement, candidates, resample). Do not modify it in place: copy what you need into `data/rlhf/dialogue_v2/pod/` and add your own stage entry with the same trap, watchdog and ledger discipline.
4. Attempt logs `data/rlhf/dialogue_quality_depth/runtime/pod/*.log` and the failure notes with their fixes in `data/rlhf/dialogue_quality_depth/messages/`: CK3_failure_1.md (runpod 503 → offer fallback), CK3_failure_2.md (Hub token file without trailing newline), CK5_failure_1.md + impl_CK5_2.md (uv installer bootstrap failure on a CUDA-13 L40S; then success).
5. Lessons file: `/Users/foivoskarounos-zamparloukos/.claude/projects/-Users-foivoskarounos-zamparloukos/memory/prime_vllm_cuda_driver.md`.
Short list of what broke before: driver ≥ 580 (CUDA 13) → vllm==0.29.0, driver 570 (CUDA 12.8) → vllm==0.19.1 with `--torch-backend=cu128 --override <(echo torchcodec)`; /workspace may be root-owned (chown or use $HOME/work); serve with `--max-model-len 4096` (the checkpoint maximum); check the server PID in the ready loop; `VLLM_USE_FLASHINFER_SAMPLER=0`; runpod offers with stock=Low return 503, prefer stock=Available; the uv install script can fail, verify it; pull the model from the Hub (under a minute), not from CSCS; always DELETE and confirm with GET.
Provisioning helper (import read-only, never edit): `/Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts/prime_provision.py`. Credentials: `~/.config/prime/key`, `~/.cache/huggingface/token`, `~/.ssh/prime_intellect_key`.

## 3. Budget and limits, as verified at brief time
- Prime Intellect: the dialogue programme's total cap is EUR 5, operational stop EUR 4.00, reserve EUR 1.00. The pilot ledger (`data/rlhf/dialogue_quality_depth/runtime/ledger.jsonl`) records EUR 1.9484 over 8 sessions, all stopped, so about EUR 2.05 remains before the operational stop. GET /pods returned 0 active pods. Keep your own ledger under `data/rlhf/dialogue_v2/runtime/` with a development tag and count it against the same cap; re-check GET /pods and the ledger before every provisioning.
- Sol: **no call cap** (owner, 17 Sept: "let it run as much as it needs"). The earlier 120-call pilot allocation does not limit this work. Record every call and report the totals; a Sol call forecast is not a gate.
- If the bounded runs cannot fit the Prime Intellect money limit: finish all free work (code, seeds, offline gates, dry-run packets), post the exact shortfall on the board, and end with your report. Do not borrow from first-experiment resources.
- Sol access: `data/math/codex_server.py` (`CodexServer().call(prompt, schema, model='gpt-5.6-sol', effort=...)`), codex-cli 0.154.0. If you use `codex exec`, do not pass `-c features.code_mode_host=false` (it disables tools on 0.154). Do not use astra (gpt-6-astra).
- No CSCS work.

## 4. Order and gates
Stage A (baseline, contracts; no GPU) → B1 adaptive user → B2 role views and consistent state → B3 selection and branch sampling → C offline gates and readiness report → forecast (EUR) → D1 (4 development trajectories) and D2 (6 demo conversations) raw collection in one pod session where economical → teardown confirmed → annotation, evaluation and review → D1 branch candidates only where genuine points exist (second short session if needed) → review package → **stop at the owner review**. No training, no promotion into any pool, no extra cases.
Minimise idle GPU time: batch Sol user turns across conversations by depth wave, as the pilot's rollout did.

## 5. Interpretations fixed for this run
1. Candidates per sampling point: follow the dialogue v2 plan as written (4, then 4 more, at most 8). Pilot evidence: 6 of the 14 resampled prefixes that found an acceptable reply needed 12 or 16 samples, so report "no verified acceptable reply within 8", never incapacity.
2. D1 openings: write fresh openings for the four specified kinds with labels from the spec; do not copy generator 0.1 fixture text. D2 openings: verbatim from the demo spec.
3. Context: served context is 4,096 tokens. If you lower the per-reply token cap from the pilot baseline (T 0.8, top-p 0.95, max 1,500 new tokens, n=1, no system prompt), record it as a sampling-config change and apply it to every D1/D2 reply.
4. A serious error at turn 1 is single-turn material; later points in that conversation remain dialogue material.
5. Mathematics inside a conversation is flagged for the specialist maths judge (Workstream A) and held; do not decide its eligibility with the general rubric.
6. Every label sent to Sol carries its glossary definition; every row records glossary sha16, generator version (0.3-dev), user-policy version, sampling point kind and assistance level (import contract, parent plan §3).
7. Tag deliverables [PG] or [RLHF] as in the parent plan §0.
8. All rows: purpose=development_demo, training_eligible=false, experiment_credit=0.

## 6. Ownership and safety
- Write only under `data/rlhf/dialogue_v2/`, `data/rlhf/reference_guided_dialogue_demo/`, `logs/dialogue_v2_*.log`, `docs/RLHF_COORDINATION/messages/`, and your own component rows in `CURRENT_VERSIONS.md` (update them in the same step as the component changes).
- Read-only: `data/rlhf/dialogue_quality_depth/` (import or copy, never edit), `data/rlhf/prompt_generator/`, rubric files, the parent and maths plans, the spec.
- Secrets: scripts read them and pass them as environment or stdin to the one command that needs them; never print, echo, log or copy them.
- Pods: never leave one running; EXIT trap plus independent watchdog; confirm deletion. Kill processes only by PID; never `pkill -f`.

## 7. Reporting
- A board message (`docs/RLHF_COORDINATION/messages/<UTC>_opus_dialogue_v2_<topic>.md`) at each gate: Stage A done; readiness (Stage C); forecast; raw collection done; review package ready; or a blocker. Include owned paths, protocol version, evidence, next action, D1/D2 counts, Sol calls, EUR spent, and confirmation that first-experiment quotas are unchanged.
- The review package is a standalone HTML file under `data/rlhf/dialogue_v2/review/` (public transcript, private reference and state in labelled panels, user strategy changes, target versus simulator errors, possible and selected sampling points, ending reasons, cost). The orchestrator publishes it.
- End with a report: what ran, counts, calls, spend, gates passed or failed, blockers, and the exact commands implemented.
