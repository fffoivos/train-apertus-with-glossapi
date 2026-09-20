# Review brief R-DPO7a (Sol) — does the ANALYSIS CODE compute what it claims?

**Scope: code correctness only.** Do not assess whether the conclusions are interesting or whether
the research design is good. A separate review covers conclusions. Your question is narrow:
**for each claim below, does the code that produced it actually compute that quantity?**

You are read-only but you CAN and SHOULD run these scripts and recompute their numbers yourself.
Everything needed is local — no cluster access required.

Working dir: `subprojects/12_greek_sft_experiments/`

## Files under review

| file | what it is claimed to do |
|---|---|
| `cluster/eval_jobs/greekmmlu_paired.py` | paired per-item comparison + McNemar on GreekMMLU-250 |
| `cluster/eval_jobs/evidence_bundle.py` | separates 3 dispersion quantities; bootstrap CI; far-end table; served-lane sign audit |
| `cluster/eval_jobs/consolidate.py` | builds `all_results.json` from raw harness output |
| `cluster/eval_jobs/corrected_baseline.py` | the generation-config confound |
| `results/G4F6P1--DPO01/curves_page.py` | renders the artifact; `scorecard()`, `config_grid()`, `gmmlu_flip_table()`, `uncertainty_table()`, `far_end_table()` |

## Data

- `results/G4F6P1--DPO01/all_results.json` — 68 model dirs, every benchmark
- `results/G4F6P1--DPO01/greekmmlu_items/<label>/*_native_mcq_predictions.jsonl` — per-item
  predictions, 66 models, 250 rows each, field `correct` (bool) keyed by `example_id`
- `results/G4F6P1--DPO01/{evidence_bundle,greekmmlu_paired}.json` — outputs to verify

## The specific claims to check, hardest first

1. **McNemar.** `greekmmlu_paired.py:mcnemar()` claims a two-sided exact binomial test over discordant
   pairs. Check the formula — especially the doubling and the `min(g,l)` summation bound. Is it
   correct when `g == l`? When the two-sided doubling exceeds 1? Is `math.comb` used right? Recompute
   at least one group's p by an independent route (e.g. `scipy.stats.binomtest`) and say whether the
   published range **0.15–0.42** is right.
2. **The "same 8 items flip" claim.** We assert the SAME 8 items go wrong→right and the SAME 3 go
   right→wrong in every arm including `armIPO42_ep3`. Verify this directly from the jsonl files.
   Is it genuinely the same item IDs, or only the same counts? This claim carries the withdrawal of
   the whole GreekMMLU result, so check it hardest.
3. **Slice structure.** "235 of 250 items never move across the parent and 15 runs." Confirm the
   intersection logic in `greekmmlu_paired.py` is over the right set of runs and that
   `always_right + always_wrong + moving == n`.
4. **Bootstrap.** `evidence_bundle.py` Q3 claims a 95% percentile CI resampling whole training runs.
   Check the resampling unit is actually the run, the percentile indices (`int(.025*B)`,
   `int(.975*B)`) are right, and that seeding makes it reproducible. Published: +0.70 pp, [−0.52, +1.77].
5. **Item SE.** We compute a binomial SE `sqrt(p(1-p)/N)` and call it "item sampling SE, one run".
   Is that the right quantity for what the artifact says it is, and is N right per benchmark
   (IFEval 541, MGSM 250, GreekMMLU 250)?
6. **`consolidate.py`.** Does it pick the right file when `glob` returns several `results_*.json`?
   Does `lm()` correctly average Global-MMLU cells, and can a partial/failed run silently produce a
   wrong mean? Is `gmmlu_el()` reading the right row (`subject == "__all__"`)?
7. **Artifact rendering.** In `curves_page.py`, does `scorecard()` use the intended baseline per
   metric — `parent_ckptcfg` for generated lanes (IFEval/MGSM) and `parent` for likelihood lanes
   (GreekMMLU/Global-MMLU-Lite)? Does it silently fall back in a way that could mislabel a delta?
   Check `mean_sd` handles a missing model without skewing n.

## Known-and-declared

The `parent_ckptcfg` baseline has no GreekMMLU / Global-MMLU-Lite entry; the page renders those cells
"not measured" deliberately, because both are likelihood-scored with no generation. Say if you think
that reasoning is wrong, but it is not an oversight.

## Disposition

BLOCKER/HIGH are fixed before the artifact is republished. MEDIUM/LOW are logged. Calibrate honestly:
do not inflate style issues to HIGH, and do not bury a real computational error as MEDIUM.

## Deliverable

Markdown. Header (what you ran, what you read) → one-line verdict → findings most-severe-first, each
`[BLOCKER]/[HIGH]/[MEDIUM]/[LOW]` with `path:line`, the RAW wrong number next to the published one,
and the fix → what you verified as correct → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
