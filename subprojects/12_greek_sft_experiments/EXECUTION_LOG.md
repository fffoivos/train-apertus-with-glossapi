# Execution log — Greek SFT round one

One line per attempt: `date | WP | attempt | executor | verdict | nh projected/actual | CHF cumulative`.
Cap: CHF 90 ≈ 33.5 node-hours at CHF 2.69/nh (owner, 2026-09-04). Rate to be confirmed on the portal after the first job.

| date | WP | attempt | executor | verdict | nh proj/actual | CHF cum |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04 00:40 | G0 | — | owner | "keep arming your loop until the plan completes … finish by morning" = GO within the CHF 90 cap; blind reading + seeds' final say stay with the owner | 0/0 | 0.00 |
| 2026-09-04 01:45 | wave1 | 1 | sol | all six briefs FAILED before any command: codex tool bridge "unknown field code_mode_host_duration_ns" (CLI 0.144.1 vs the ChatGPT app-server); fixed by `-c features.code_mode_host=false` (probe OK); relaunched | 0/0 | 0.00 |
| 2026-09-04 01:55 | WP1d/e | — | claude | ILSP public Greek IFEval (541) + MGSM (250) found → WP1d becomes an lm-eval wrap, WP1e dropped; WP1d launched | 0/0 | 0.00 |
| 2026-09-04 01:52 | cluster prep | 1 | claude | venv build + model prefetch on the login node (uenv pytorch/v2.9.1, $SCRATCH/venvs/sft); first attempt failed (no pip / wrong uenv syntax), relaunched | 0/0 | 0.00 |
| 2026-09-04 02:06 | WP1b | 2 | sol | GREEN: dry-run prints both commands; card pull reproduces GreekMMLU 0.5678 / native macro 0.4993 for E0b (and E0b_last 0.5485/0.4341) | 0/0 | 0.00 |
| 2026-09-04 02:12 | E0a | job 3285828 | claude | workbench opened (debug 01:29, preflight OK CHF 4.04 projected); GreekMMLU + native suite + retention on Apertus-8B-Instruct launched | 1.5/— | 0.00 |
| 2026-09-04 02:14 | WP1c, WP1f | 2 | sol | GREEN (offline tests OK, dry runs exit 0) | 0/0 | 0.00 |
| 2026-09-04 02:24 | WP3 | 2 | sol | GREEN (offline test OK, dry run exit 0) | 0/0 | 0.00 |
| 2026-09-04 02:24 | E0a | job 3285828 | claude | native suite cannot score Instruct (frozen model contract = CPT vocab) — dropped for E0a; retention relaunched with the 9 Table-14 tasks (offline cache); GreekMMLU running | 1.5/— | 0.00 |
| 2026-09-04 02:30 | E0a | job 3285828 | claude | GreekMMLU killed (too slow for the debug walltime: ~100 q/min); retention (9 Table-14 tasks) running on GPU1; workbench closes when retention ends | 1.5/— | 0.00 |
