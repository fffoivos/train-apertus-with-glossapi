# R-DPO7a code-correctness review

## What I read and ran

Read all five requested Python files, the three persisted JSON outputs, all 66 GreekMMLU prediction files, and the locally retained raw lm-eval parent result.

Ran, without modifying the workspace:

- `greekmmlu_paired.py` and `evidence_bundle.py`, redirecting their writes to `/dev/null`.
- `curves_page.py`, rendering to `/dev/null`.
- Independent Python recomputations from JSON/JSONL.
- R’s `binom.test()` as an independent exact-binomial implementation.
- `consolidate.py` and `corrected_baseline.py`; both expose local-input problems described below.

**One-line verdict:** The GreekMMLU, bootstrap, item-SE, and current baseline-routing calculations are correct, but Global-MMLU-Lite is materially misaggregated throughout the published artifact.

## Findings

### [HIGH] Global-MMLU-Lite averages aggregate rows and their component rows together

[cluster/eval_jobs/consolidate.py:16](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/consolidate.py:16), [curves_page.py:292](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:292), [curves_page.py:552](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:552)

`lm()` collects every result whose name starts with `global_mmlu_`. The 42 collected values are:

- Six language-level group aggregates, such as `global_mmlu_en`.
- Their 36 subject-language component tasks.

The raw harness explicitly identifies the six aggregates under `groups` and their six children under `group_subtasks`. Averaging all 42 double-counts every observation through its language aggregate and then weights unequal-size subject categories equally. They are not “42 subject-language cells”; there are 36 leaf cells plus six aggregate rows.

Published/wrong versus recomputed from the six official language-group accuracies:

| row | published mean / delta | recomputed mean / delta |
|---|---:|---:|
| parent | 0.603199 | **0.620000** |
| alpha 0 | 0.558154 / −4.50 pp | **0.562333 / −5.77 pp** |
| alpha 0.25 | 0.562801 / −4.04 pp | **0.567000 / −5.30 pp** |
| balanced | 0.532070 / −7.11 pp | **0.536111 / −8.39 pp** |
| IPO | 0.561811 / −4.14 pp | **0.565833 / −5.42 pp** |

The published individual-run range “3.6–7.5 pp down” becomes **4.875–8.875 pp down**.

Fix: retain leaf cells separately for the heatmap, but calculate `gmmlu_lite` from the exact six language group rows—preferably the harness’s `groups` object—and assert that all six exist. Regenerate `all_results.json` and the artifact.

### [MEDIUM] Consolidation accepts arbitrary, partial, or empty inputs

[cluster/eval_jobs/consolidate.py:10](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/consolidate.py:10), [consolidate.py:13](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/consolidate.py:13), [consolidate.py:42](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/consolidate.py:42), [corrected_baseline.py:13](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/corrected_baseline.py:13)

Three related problems:

- Both producers hardcode the unavailable `/iopsstor/...` cluster root.
- `glob(...)[0]` selects an unspecified file when several results exist; it does not choose the newest or validate equivalence.
- Any nonempty subset of Global-MMLU cells is averaged. A failed run containing only the parent’s `global_mmlu_de=0.640` would silently publish **0.640**, rather than reject it; the complete official value is **0.620**.

On this machine, `consolidate.py` reported success with **0 models versus the published 68**, while `corrected_baseline.py` crashed on missing baselines. The retained bundle itself shows no observed partial Global-MMLU rows: all 51 rows containing that metric have 42 stored entries, and no local raw directory contains multiple `results_*.json` files.

Fix: accept a `--root`, fail if zero models or either baseline is absent, deterministically select a completed result, and assert exact task coverage and expected sample counts before emitting a row.

### [MEDIUM] `scorecard()` can silently use the wrong baseline while retaining the checkpoint-baseline label

[curves_page.py:295](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:295)

The fallback is metric-agnostic:

```python
base = pf.get(m) if pf.get(m) is not None else pn.get(m)
```

That is intentional for likelihood metrics, but unsafe for generated metrics. If `parent_ckptcfg.ifeval` disappeared, alpha 0 would silently render **−0.81 pp against the own-config parent**, while the surrounding text would still describe a checkpoint-config delta; the current correctly routed result is **+0.85 pp**, rendered `+0.9`.

Current data are complete, so the published IFEval/MGSM deltas use `parent_ckptcfg`, and GreekMMLU/Global-MMLU use `parent` as intended.

Fix: define an explicit baseline map by metric and render `not measured` or fail when the required baseline is absent. Also either assert equal per-metric coverage or display each metric’s own `n`; the single displayed run count currently comes from IFEval only.

### [LOW] The central common-item claim is hardcoded rather than emitted by the paired analysis

[greekmmlu_paired.py:60](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/greekmmlu_paired.py:60), [curves_page.py:569](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:569)

Published **8 gained / 3 lost** equals the raw recomputation, but `greekmmlu_paired.py` never calculates or serializes those intersections; the renderer states them as prose.

There are five distinct complete flip signatures. For example, IPO42 is **10 gained/5 lost**, while a typical alpha-0 run is **9/4**. Thus “same five net items” is safe only as a net-count statement, not as identical complete flip sets.

Fix: emit `common_gained_ids`, `common_lost_ids`, unions, and signature counts, then render “shared core of 8/3; remaining flips vary.”

## Verified as correct

- **McNemar:** `min(g,l)` is the correct symmetric tail bound for the exact two-sided binomial test at \(p=0.5\); doubling and capping at 1 correctly handles `g == l` and other cases where doubling exceeds one. `math.comb(n,i)` is used correctly.
  - R independently returned `9/3 → 0.1459961`, `10/5 → 0.3017578`, and `9/5 → 0.4239502`.
  - The published **0.15–0.42** range is correct, specifically a range of per-run p-values rather than one group-level test.

- **Common item IDs:** the eight gained and three lost IDs are genuine intersections across all 15 runs, including IPO42—not merely equal counts.
  - Gained: `1302, 16010, 2326, 3208, 3928, 5854, 7707, 8021`.
  - Lost: `11861, 13865, 15498`.
  - IPO42 additionally gains `13848, 7133` and loses `12964, 3655`.

- **Slice structure:** exactly the intended 15 epoch-3 runs are used. Every file has 250 rows and 250 unique IDs. The common intersection is 250, with `139 + 96 + 15 = 250`; therefore **235 never move**.

- **Bootstrap:** the resampling unit is a complete run score, with five replacement draws independently within each arm. Seed `20260919` reproduces **+0.702403 pp, [−0.517560, +1.774492]**.
  - The raw indices 250/9750 are one position above one common nearest-rank convention, but neighboring order statistics are identical; NumPy’s linear, inverse-CDF, closest, lower, and higher definitions all return the published endpoints.

- **Item SE:** `sqrt(p(1-p)/N)` is the conventional plug-in item-sampling SE for one binary-accuracy run under iid item sampling. The Ns are correct: IFEval **541**, MGSM **250**, GreekMMLU **250**. It is not a paired-comparison SE, which the artifact explicitly acknowledges.

- **GreekMMLU consolidation:** selecting `subject == "__all__"` is correct for the headline schema. All 66 JSONL-derived accuracies match `all_results.json`.

- **Generation confound:** independently recomputed as IFEval **−1.663586 pp** and MGSM **−2.400000 pp**, rendered correctly as −1.7 and −2.4.

- **Artifact helpers:** `config_grid()`, `gmmlu_flip_table()`, `uncertainty_table()`, and `far_end_table()` faithfully render their stored inputs. `mean_sd()` safely excludes a missing model and returns the reduced `n`.

- **Known missing likelihood baselines:** marking `parent_ckptcfg` GreekMMLU and Global-MMLU cells `not measured` is correct. Those lanes use likelihood scoring without generation, so using the direct parent for their deltas is appropriate.

## Ordered asks

1. Fix Global-MMLU aggregation and regenerate `all_results.json` plus every dependent artifact number.
2. Add deterministic result selection, exact coverage/sample-count assertions, a configurable root, and fail-closed empty-input behavior.
3. Replace `scorecard()`’s generic fallback with explicit metric-to-baseline routing.
4. Serialize the common GreekMMLU item-ID intersections and clarify “same net count” versus “identical full flip set.”

VERDICT: One HIGH aggregation error; GreekMMLU, bootstrap, item-SE, and current baseline routing otherwise compute what they claim | BLOCKERS: 0 | HIGH: 1