# R-DPO7a cycle-2 code-correctness review

**Verdict:** The cycle-1 numerical corrections are mostly valid, but publication must remain on hold: the new full-run finalizer cannot read the actual clean-subset manifest and can certify the wrong or an incomplete population.

## Fix verification

| Cycle-1 finding | Status | Verification |
|---|---|---|
| HIGH — Global-MMLU misaggregation | **Correctly fixed** | All 51 rows containing `gmmlu_cells` now equal the mean of exactly the six language groups. Against the backup, the 68 existing models differ only at 51 `gmmlu_lite` fields; the only other changes are the two disclosed new `*_parentcfg` rows. |
| MEDIUM — baseline fallback | **Correctly fixed** | The explicit metric map routes IFEval/MGSM to `parent_ckptcfg` and both likelihood metrics to `parent`. Removing `parent_ckptcfg.ifeval` in memory renders its baseline as `not measured` and leaves derived deltas blank; it does not fall back. Unequal coverage renders `4–5`, as intended. |
| MEDIUM — arbitrary/partial consolidation | **Not fixed** | `$DPO01_RESULTS` and six-language completeness are fixed, but `glob()[0]`, zero-model success, and expected sample-count validation remain. Deferral is consistent with the stated MEDIUM disposition for this frozen artifact, but the producer remains unsafe for the next regeneration. |
| LOW — hardcoded flip claim | **Wrongly fixed** | `common_flips` is computed correctly, but the renderer never reads it: [curves_page.py:589](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:589) still hardcodes 8/3, 10/5, and five signatures. The present prose is numerically right but can become stale again. |

The aggregation choice is correct. Each language contains 400 items, so averaging the six item-weighted group accuracies is also the item-weighted mean over all 2,400 observations:

- Parent groups: `0.6400, 0.6550, 0.6075, 0.6325, 0.6300, 0.5550`
- Six-group mean: **0.620000**
- Item-weighted 36-leaf mean: **0.620000**
- Unweighted 36-leaf mean: **0.600399**
- Erroneous unweighted six groups plus 36 leaves: **0.603199**

Thus “Global-MMLU-Lite across six non-Greek languages” matches the new computation. The artifact does not fully match: [curves_page.py:570](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:570) still calls these “42 subject-language cells”; there are 36 leaf cells plus six aggregate rows.

The independently recomputed group deltas are:

- Plain α=0: **−5.7667 pp**
- Anchored α=0.25: **−5.3000 pp**
- Length-balanced: **−8.3889 pp**
- IPO β=10: **−5.4167 pp**

`common_flips` also matches independently: gained `1302, 2326, 3208, 3928, 5854, 7707, 8021, 16010`; lost `11861, 13865, 15498`; union **10/5**, **five** signatures across 15 runs.

## New findings

### [BLOCKER] The finalizer cannot parse the actual clean-subset manifest

[finalize_greekmmlu_full.py:24](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:24)

The real manifest stores a descriptor:

```json
"clean_example_ids": {
  "path": ".../greekmmlu_clean_example_ids.txt",
  "bytes": ...,
  "sha256": "..."
}
```

This is established by the manifest producer at [build_greekmmlu_clean_subset.py:151](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/06_dataset_scheduling_experiments/evaluation/build_greekmmlu_clean_subset.py:151).

The new loader treats that dictionary itself as the ID iterable. My direct function test returned:

```text
actual_schema {'path', 'sha256'}
```

It therefore looks for two example IDs literally named `path` and `sha256`, skips every model, writes `{}`, and then exits nonzero. It never opens or hashes the referenced 16,159-ID file. Its claimed top-level-list fallback is broken too: it calls `d.get(...)` before testing `isinstance(d, list)`, producing `AttributeError`.

### [HIGH] The population guard validates counts, not the intended dataset or complete model population

[finalize_greekmmlu_full.py:38](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:38), [finalize_greekmmlu_full.py:64](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:64), [finalize_greekmmlu_full.py:90](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:90)

Duplicate detection is correct and occurs before filtering; it also catches numeric `1` versus string `"1"`. But 16,632 unique IDs are accepted without checking `run_metadata.json`, dataset source, pinned revision, split, fingerprint, or the exact expected ID population.

After repairing manifest loading, **16,159 genuine clean IDs plus 473 arbitrary IDs** would pass both the raw-count and clean-subset guards.

The model population also fails open: an incomplete model is skipped, then any nonempty remainder is written successfully. Seven valid models out of the expected eight produce a seven-model `finalized.json` with exit status zero. Multiple prediction files are again selected through unspecified `glob()[0]`.

For valid runner output, accuracy scoring is correct because the runner emits a JSON boolean. The finalizer nevertheless accepts malformed values: `"correct": "false"` counts as true; my three-row test with `"false"`, `false`, and `1` returned **2/3**.

### [MEDIUM] The 2×2 arithmetic is right, but “weights only” and the headline strength are not fully supported

[curves_page.py:312](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:312), [curves_page.py:556](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:556), [dpo01_gencfg_control.sh:15](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:15)

The values and column labels are arithmetically correct:

| Arm | Parent config | Checkpoint config |
|---|---:|---:|
| Anchored | `(326−335)/541 = −1.6636 pp` | `(336−326)/541 = +1.8484 pp` |
| Plain | `(321−335)/541 = −2.5878 pp` | `(334−326)/541 = +1.4787 pp` |

MGSM also renders correctly: anchored `−6.40/−6.40 pp`; plain `−5.60/−4.00 pp`.

However:

- `parent_ckptcfg` is constructed from arm01’s checkpoint configuration. Arm05 is compared against that same baseline without an assertion or retained hash proving arm01 and arm05’s serialized configuration bundles are identical.
- The locally retained inputs contain only the hand-added aggregate rows at [all_results.json:2803](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/all_results.json:2803); the two raw cluster results and configuration receipts are absent.
- The page acknowledges `n=1 each` at line 559, but its bold “the configuration does not act the same” headline carries no seed or paired-item uncertainty. The observed reversal is valid for these two fixed checkpoints; it is not yet a replicated recipe-level effect.

### [LOW] Corrected data are still described and rendered through stale constants

[curves_page.py:570](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:570), [curves_page.py:589](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:589)

Replace “42 subject-language cells” with “six item-weighted language groups, comprising 36 leaf cells / 2,400 items,” and render the shared-core/union/signature values from `GMP["common_flips"]`.

## Ordered asks

1. Replace heuristic manifest discovery with the frozen manifest contract; verify schema, status, dataset revision, `full_count=16632`, `clean_count=16159`, referenced ID-file SHA-256, uniqueness, and exact ID count.
2. Bind predictions to `run_metadata.json` and the pinned dataset fingerprint; require the exact eight labels and exactly one prediction file each; fail the entire finalization on any invalid model and write atomically only after all checks pass.
3. Retain the raw 2×2 result files plus config/tokenizer hashes, assert arm01/arm05 checkpoint-config equivalence, and limit the headline to the two measured checkpoints unless the parent-config cells are replicated.
4. Wire `common_flips` into rendering and correct the 42-cell wording.
5. Before the next consolidation run, resolve deterministic result selection, zero-model failure, and expected sample-count validation.

VERDICT: HOLD: cycle-1 numbers are repaired, but the full-run finalizer is not publication-safe | BLOCKERS: 1 | HIGH: 1

