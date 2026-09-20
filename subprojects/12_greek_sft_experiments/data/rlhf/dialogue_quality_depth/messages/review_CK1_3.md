VERDICT: HOLD

1. [blocking] `rollout.py:174-191`; `dqd.py:87` — measurement still accepts `--max-turns 3`, despite the plan and manifest fixing measurement at the explicit eight-turn override. The parser accepts it, and `rollout()` permits `{3, 8}` for measurement. Validation also occurs after target preflight, so an invalid three-turn measurement can make a provider request before failing elsewhere. Required fix: enforce exactly 3 for smoke and exactly 8 for measurement before generator checks, client preflight, or any provider call; add an offline test proving measurement/3 is rejected without calling either client.

Verified correct:

- All three cycle-2 findings were otherwise fixed:
  - Reduced admissions now attempt exact largest-remainder margins, prove infeasibility, and record all deviations and omitted cells. Sizes 35, 21, and 14 are exact; size 28 records its proven joint infeasibility, 11 deviations, and omitted playful-attitude cell.
  - Control allocation now uses trajectory-aware depth matching and receipts infeasible depth redistributions. The prior early/late conflict selects three early plus one late control.
  - Report freezing recomputes effective first-serious/recovery boundaries and requires repeated review until the boundary set is stable.
- Information barriers hold across opening, simulator, annotation, and ranking prompt construction.
- Raw and candidate sampling remains `n=1`, temperature `0.8`, `top_p=0.95`, 1500 tokens, with no system message; exact completion text and hashes are retained.
- Restart handling reuses observed target and Sol results across all persisted crash boundaries.
- Terminal codes, Sol reservation accounting, cumulative caps, and failed-attempt counting are correctly separated.
- The manifest contains deterministic joint counts, compatible family assignments, 41 unique family reservations, and explicit 3/8 planned horizons. The current runtime has zero model calls and no generator-family or instance overlap.
- Forecasting reserves the full eight-turn measurement horizon, funds complete annotation conservatively, freezes admission before measurement, and records the EUR 5/4/1 budget and GPU deadline inputs.
- Selection otherwise enforces P/R/C eligibility, largest-remainder P/R allocation, prefix uniqueness, per-kind and per-trajectory caps, redistribution receipts, and the frozen-report gate.
- Export and `ADAPTER_CONTRACT.md` satisfy the same-prefix, acceptable-chosen, substantive-preference, rejected-set, and completion-only-mask requirements.
- Prompt semantics, runbook command forms, and machine-readable success/failure output are correct.
- The supplied transcript reports 32 passing tests. Static inspection found no test socket, Codex process, or `~/.codex` access.
- All frozen prompt-generator release hashes verify. The protected external files retain their previously observed mtimes and hashes.