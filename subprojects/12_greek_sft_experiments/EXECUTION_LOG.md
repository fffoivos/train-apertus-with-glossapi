# Execution log — Greek SFT round one

One line per attempt: `date | WP | attempt | executor | verdict | nh projected/actual | CHF cumulative`.
Cap: CHF 90 ≈ 33.5 node-hours at CHF 2.69/nh (owner, 2026-09-04). Rate to be confirmed on the portal after the first job.

| date | WP | attempt | executor | verdict | nh proj/actual | CHF cum |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04 00:40 | G0 | — | owner | "keep arming your loop until the plan completes … finish by morning" = GO within the CHF 90 cap; blind reading + seeds' final say stay with the owner | 0/0 | 0.00 |
| 2026-09-04 01:45 | wave1 | 1 | sol | all six briefs FAILED before any command: codex tool bridge "unknown field code_mode_host_duration_ns" (CLI 0.144.1 vs the ChatGPT app-server); fixed by `-c features.code_mode_host=false` (probe OK); relaunched | 0/0 | 0.00 |
