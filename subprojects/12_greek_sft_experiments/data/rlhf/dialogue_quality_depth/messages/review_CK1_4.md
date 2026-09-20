VERDICT: PASS

1. Findings: none. No blocking, major, or minor acceptance-criteria violations remain.

Verified correct:

- The cycle-3 blocker is fixed: `rollout.py:174-194` enforces smoke=3 and measurement=8 before state access, isolation checks, ledger construction, preflight, or provider calls. `dqd.py:31-42,113-131` rejects mismatched CLI horizons before constructing either client. Tests at `test_dqd.py:133-147,596-608` cover both paths.
- Opening, simulator, annotation, and ranking code preserve all required information barriers.
- Raw and candidate sampling remains `n=1`, temperature `0.8`, `top_p=0.95`, 1500 tokens, without system messages. Exact text and hashes are retained; terminal reasons and restart recovery remain distinct and immutable.
- Sol reservations precede requests; failed attempts count; total and phase caps are cumulative and forecast reallocations retain the 120-call total.
- The runtime manifest contains 41 unique family/instance reservations, deterministic seed `9162602`, 6 smoke and 35 measurement seeds, explicit 3/8 horizons, repaired compatible assignments, and complete joint counts. The registry contains zero model calls and has no family or instance overlap with the generator registry.
- Reduced admissions implement largest-remainder margins for 35/28/21/14, with exact solutions where feasible and explicit proof, deviations, and omitted cells where not.
- Selection enforces P/R/C eligibility, control depth spreading, trajectory-aware quota matching, largest-remainder allocation, prefix uniqueness, per-trajectory caps, redistribution receipts, and the frozen-report gate.
- Calibration boundaries are recomputed from effective adjudicated labels and must stabilize before report freezing.
- Export enforces one substantive same-prefix pair per selection, acceptable chosen answers, and rejection of ties/all-bad sets. `ADAPTER_CONTRACT.md:7-11` correctly requires completion-only loss masking, including masking earlier bad assistant turns.
- Forecasting reserves the complete eight-turn measurement horizon and full annotation cost before admission. EUR 5 total, EUR 4 operational stop, EUR 1 reserve, GPU accounting, and conservative deadlines are implemented.
- The prompts contain the required seriousness, repair-opportunity, visible-mistake, genuine-completion, and no-padding semantics. `RUNBOOK.md` commands match the CLI, and all command paths end in `DQD_OK` or `DQD_FAIL`.
- The supplied transcript reports all 34 offline tests passing. Static inspection found no test that spawns Codex, opens a socket, or reads `~/.codex`.
- All 62 hashes in `../prompt_generator/RELEASE.json` verify. The protected external files retain their previously reviewed hashes and mtimes: `../sample.py` (`6825c947…`), `../judge_rank4.py` (`e7e61e79…`), and `../../math/codex_server.py` (`6d706385…`).