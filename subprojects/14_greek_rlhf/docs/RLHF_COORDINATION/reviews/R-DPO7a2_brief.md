# Review brief R-DPO7a cycle 2 (Sol) — verify the fixes, then look for what cycle 1 missed

Your cycle-1 review is at `docs/RLHF_COORDINATION/reviews/R-DPO7a_review_1.md` (1 HIGH, 2 MEDIUM,
1 LOW). Read it first. Two jobs, in order:

**(1) Verify each fix is actually correct** — not merely present. A wrong fix is worse than the bug.
**(2) Then audit for anything cycle 1 did not reach.** New code has landed since, and the data file
changed. Do not restrict yourself to re-checking your own findings.

Read-only, but run whatever you need. Everything is local.

## What changed in response to cycle 1

| finding | change |
|---|---|
| HIGH Global-MMLU misaggregation | `consolidate.py` `lm()` now averages only the six `LANG_GROUPS`; emits `gmmlu_lite_incomplete` instead of averaging a partial set. `all_results.json` was recomputed in place from the retained `gmmlu_cells` (backup: `all_results.json.bak_gmmlu`). |
| MEDIUM baseline fallback | `curves_page.py` now has an explicit `BASELINE` map per metric; generated lanes require `parent_ckptcfg`. Row `n` shows a range when per-metric coverage differs. |
| MEDIUM partial input | root is now `$DPO01_RESULTS`. **Deliberately NOT fixed:** deterministic selection among multiple `results_*.json`, and a hard fail on zero models. Logged as backlog. Say if you think that deferral is wrong. |
| LOW flip IDs in prose | `greekmmlu_paired.py` now computes and emits `common_flips` (gained/lost IDs, unions, signature count); the artifact says "shared core" and reports the 10/5 union and 5 signatures. |

## Verify specifically

1. **Is the recomputed `all_results.json` right?** Diff it against `all_results.json.bak_gmmlu`.
   Confirm ONLY `gmmlu_lite` changed, that every one of the 51 models got the six-group value, and
   that nothing else was perturbed. Recompute parent = 0.6200 and the group deltas
   (−5.77 / −5.30 / −8.39 / −5.42) independently.
2. **Is averaging the six group rows the right choice** versus the 36 leaf cells, given the group
   rows are item-weighted within a language and the leaves are not? State which is correct for a
   claim worded "Global-MMLU-Lite across six non-Greek languages" and whether the artifact's wording
   now matches what is computed.
3. **`common_flips`** — verify the emitted IDs equal your cycle-1 independent derivation, and that
   the union/signature counts are right.
4. **The `BASELINE` map** — check it cannot silently mislabel, and that `not measured` renders
   wherever a required baseline is genuinely absent.

## New since cycle 1 — audit fresh

- **`arm05_ep3_parentcfg` and `arm01_ep3_parentcfg` are new rows in `all_results.json`**, added by
  hand from a cluster job, and they complete a 2×2. `config_grid()` in `curves_page.py` renders it.
  **This reverses the artifact's headline** — the IFEval training effect is +1.85/+1.48 pp under one
  configuration and −1.66/−2.59 pp under the other. Check the arithmetic, check that each delta
  compares the correct pair of cells (same configuration, weights the only difference), and check
  the rendering is not mislabelled. These are n=1 per cell; say whether the page treats them with
  appropriate weight given no replication and no uncertainty attached.
- `cluster/eval_jobs/finalize_greekmmlu_full.py` is NEW and unreviewed. It will compute the
  published numbers for a 16,632-row run. Check its scoring, duplicate detection, manifest parsing
  (the `ids` discovery is heuristic), and the population guard.

## Disposition

BLOCKER/HIGH are fixed before the artifact is republished. MEDIUM/LOW logged.

## Deliverable

Markdown. Header → one-line verdict → **a fix-verification table (each cycle-1 finding: correctly
fixed / wrongly fixed / not fixed)** → new findings most-severe-first with `path:line` and raw
numbers → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
