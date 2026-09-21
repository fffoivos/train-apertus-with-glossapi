VERDICT: HOLD

1. [blocking] `manifest.py:168-199` — reduced admissions compute largest-remainder targets but do not enforce them. With the current manifest, size 28 targets revision=6, cooperative=20, and playful=1, while the selected subset has revision=8, cooperative=24, and playful=0. Only zero-target task/language cells are recorded; omitted or deviating interaction/style cells are not. Required fix: deterministically solve for the largest-remainder margins across all required axes when feasible; otherwise record explicit infeasibility, every target-versus-actual deviation, and every omitted cell. Add tests for 35/28/21/14, not only subset length.

2. [blocking] `select.py:112-144` — control depth spreading uses row counts rather than distinct-trajectory feasibility and can discard an available depth bin without recording redistribution. In a production-sized 14-trajectory case with four control trajectories, where one trajectory offers early and late controls and three offer early controls, the allocator selects four early controls although a late control is available; the redistribution receipt is empty. This violates the required depth-bin spread and “every redistribution logged” rule. Required fix: allocate control depth quotas with trajectory-cap-aware matching, then recompute and receipt any infeasible depth quota. Add this conflict case to the tests.

3. [blocking] `annotate.py:222-255`; `analyse.py:173-195` — mandatory calibration boundaries are frozen before adjudication and never recomputed. If the reviewed first-serious label is changed to minor, a later unreviewed serious label can become the effective first-serious boundary, yet report freezing checks only the original receipt and succeeds. Required fix: recompute first-serious and recovery boundary IDs from effective annotations at the report gate, require adjudication of every resulting boundary, and repeat until the boundary set is stable.

Verified correct:

- Information barriers hold: openings exclude reference/check/parameter data; simulator prompts use public state and visible prefixes; annotation packets exclude suffixes and same-trajectory batching; ranking hides provenance.
- Raw and candidate decoding is fixed at `n=1`, temperature `0.8`, `top_p=0.95`, and 1500 tokens with no system message. Exact text and hashes are retained, and terminal codes are distinct.
- Restart recovery now covers target completion, assistant snapshot, and completed Sol-follow-up boundaries without target re-sampling.
- Sol reservations precede requests; failures count; total and phase caps remain cumulative and immutable.
- The regenerated manifest has 41 unique reservations, explicit 3/8 horizons, compatible interaction/family assignments, repair evidence, and full joint counts. It has zero model calls and currently overlaps neither generator families nor instances.
- Live generator checks use a read-only SQLite connection and run before measurement openings and rollout.
- Forecasting now reserves the full eight-turn horizon, batches continuation per depth wave, measures annotation calls specifically, freezes the forecast, and refuses post-measurement forecasting.
- P/R/C eligibility, prefix uniqueness, per-kind/per-trajectory caps, frozen-report gate, and capacity-shortfall receipts are otherwise implemented.
- Export enforces same-prefix pairs, acceptable chosen answers, substantive preferences, and rejection of tied/all-bad sets. The adapter contract correctly masks all history, including earlier bad assistant turns.
- Budget constants, GPU ledger, and conservative deadline are correct.
- Prompts contain the required severity, repair, completion, visible-mistake, and no-padding semantics. Runbook commands match the CLI, and parse failures now end with `DQD_FAIL`.
- The supplied transcript reports 29 passing tests. Static inspection found no test socket, Codex process, or `~/.codex` access.
- All `prompt_generator/RELEASE.json` hashes verify. The protected external files retain their earlier mtimes and previously observed hashes.