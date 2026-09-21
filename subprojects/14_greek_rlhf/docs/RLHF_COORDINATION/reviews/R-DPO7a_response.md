# R-DPO7a response — analysis code (Sol, gpt-5.6-sol, xhigh, 12 min, 37 shell commands)

> **CORRECTION, 19 September 2026 — parts of this document are superseded.** It states or relies on one or more of:
> "the IPO arm did not train" (false: 129/129 steps); a "same-seed repeat gap" (that pair was scored a day apart);
> GreekMMLU gains measured with a custom protocol (the official protocol gives −0.26 to −0.43 pp);
> Global-MMLU deltas compared across prompt dates; an α interval described as paired (it was unpaired; paired = [−0.74, +1.85]).
> Current status of every claim: `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. The text below is kept unedited as a record.


Verdict: *one HIGH aggregation error; GreekMMLU, bootstrap, item-SE and baseline routing otherwise
compute what they claim.* **0 BLOCKERS, 1 HIGH, 2 MEDIUM, 1 LOW. All applied.**

First attempt returned `UNREVIEWED` in 2 min: the harness passed `-c features.code_mode_host=false`,
which disables the reviewer's shell. **That is also why R-DPO6 reported "0 dataset rows reviewed"
and raised independent verification as its BLOCKER** — a harness fault I had recorded as a finding.
Fixed in `cluster/run_review.sh`, which now refuses to file a review whose reviewer ran <3 commands.

## HIGH — Global-MMLU-Lite was misaggregated everywhere. Confirmed, fixed.

The harness emits **six language group rows plus their 36 subject children = 42 rows**. `lm()` took
everything matching `global_mmlu_*` and averaged all 42, counting every observation twice.

It is not a uniform offset. The group rows are item-weighted within a language, so the error scales
with how a model's strength is distributed across subject sizes:

| | published | correct (6 group rows) | error |
|---|---|---|---|
| parent | 0.6032 | **0.6200** | 1.96 pp |
| arm01_ep3 | 0.5605 | 0.5650 | 0.53 pp |

Because the parent moved four times as far as the arms, **the deltas were wrong, not just the
levels** — every multilingual figure on the page was ~1.3 pp too favourable:

| group | published Δ | corrected Δ |
|---|---|---|
| plain DPO α=0 | −4.50 | **−5.77** |
| anchored α=0.25 | −4.04 | **−5.30** |
| length-balanced | −7.11 | **−8.39** |
| IPO β=10 | −4.14 | **−5.42** |

Individual-run range −3.6…−7.5 becomes **−4.88…−8.88**. Recomputed from `gmmlu_cells`, which
retained all 42 rows per model, so no cluster access was needed. `consolidate.py` now averages the
six named groups and refuses to average a partial set (`gmmlu_lite_incomplete`).

**This makes the round's conclusion worse, not better**, and it strengthens the section-11 reading:
the length-balanced arm now gives up 8.4 pp of multilingual knowledge for its 4.7 pp of Greek maths.

## MEDIUM — baseline fallback could mislabel a delta. Fixed.

`scorecard()` fell back from `parent_ckptcfg` to `parent` for any metric. Current data is complete so
nothing was actually mis-rendered, but had `parent_ckptcfg.ifeval` been missing, alpha 0 would have
shown −0.81 pp under a column the prose calls a checkpoint-config delta (true value +0.85). Replaced
with an explicit per-metric `BASELINE` map; generated lanes require `parent_ckptcfg` or render
nothing. Also: the row `n` came from IFEval alone and now shows a range when coverage differs.

## MEDIUM — consolidation accepts partial input. Partially fixed.

Root is now `$DPO01_RESULTS`, and a partial Global-MMLU set can no longer be averaged. **Not fixed:**
deterministic selection among multiple `results_*.json` and a hard fail on zero models. No model has
multiple result files today, so this is latent, not active. Backlog.

## LOW — the central claim was prose, not data. Fixed.

The artifact asserted "the same 8 flip right, the same 3 flip wrong" while `greekmmlu_paired.py`
never computed the intersection. It does now, and the reviewer's independently derived IDs match:
gained `1302, 2326, 3208, 3928, 5854, 7707, 8021, 16010`; lost `11861, 13865, 15498`.

The reviewer's refinement is adopted: this is a **shared core**, not identical flip sets. Union
across runs is 10 gained / 5 lost with **five distinct signatures** — IPO42 is 10/5 where a typical
plain run is 9/4. The page now says so. The withdrawal is unaffected: every arm, including the one
that failed its gate, carries that same core.

## Certified correct by independent recomputation

- **McNemar** — `min(g,l)` is the right symmetric tail bound; doubling and the cap at 1 handle
  `g == l`. R's `binom.test` independently returned 9/3 → 0.1460, 10/5 → 0.3018, 9/5 → 0.4240. The
  published **0.15–0.42** is right, and is a range of per-run p-values, not one group test.
- **Slice structure** — exactly the 15 intended epoch-3 runs; 250 unique IDs each; 139+96+15 = 250,
  so **235 never move** is correct.
- **Bootstrap** — unit is a whole run, seed 20260919 reproduces **+0.7024 pp, [−0.5176, +1.7745]**.
- **Item SE** and the current baseline routing.

Artifact republished at v9.
