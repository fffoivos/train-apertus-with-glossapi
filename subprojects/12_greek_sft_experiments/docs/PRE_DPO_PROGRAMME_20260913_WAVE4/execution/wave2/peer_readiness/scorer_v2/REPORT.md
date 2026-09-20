# Superseded MATH-500 scorer candidate v2

**Do not pin this implementation.** Independent review found that language does not determine numeric notation, the following-line extraction was implicit rather than correctly implemented, and the inherited general SymPy parser remained unsafe and mathematically unsound. The replacement is `equiv500_v3_candidate.py`; current findings are in `V3_REPORT.md`. This file is retained as the audit trail for the rejected intermediate candidate.

Status: the frozen `equiv500` scores remain historical results. Candidate v2 is a review artifact; it has not replaced the frozen scorer or any published result.

## Reproduced defects

The frozen implementation removes every trailing `\\text{...}` or `\\mbox{...}` block before comparing strings. It therefore maps both `\\text{ellipse}` and `\\text{circle}` to the empty string and returns true at the exact-match branch. The same executable path was reproduced locally.

It also fails to extract the explicit English answer in `The final answer is: $9$`, leaving the whole sentence for comparison and returning false. Finally, its numeric parser returns two values for each ambiguous token: both `1.000` and `1,000` can match either 1 or 1000. The regression file records all six positive/negative separator cases.

Concrete actual false positives include:

- `test/intermediate_algebra/860.json`: reference `\\text{ellipse}`, extracted prediction `\\text{circle}` in two stored English G/F/P experiment cells; frozen=true, v2=false.
- `test/algebra/1349.json`: reference `\\text{Evelyn}`, extracted prediction `\\text{Angela}` or `\\text{Carla}` in stored Krikri/control cells; frozen=true, v2=false.
- `test/prealgebra/105.json`: reference `\\text{east}`, extracted prediction `\\text{West}`, `\\text{North-East}`, or `\\text{βορρά}`; frozen=true, v2=false.
- `test/prealgebra/993.json`: reference `1250`, Greek extracted prediction `1,250`; frozen=true because it tries both 1.25 and 1250, v2=false under the declared Greek locale.

## Full frozen-output audit

The audit evaluated exactly 500 unique benchmark IDs in each of 22 language/model cells: 10 stored local model columns plus the new pinned Krikri v1.5 column, for 11,000 responses. Every input file hash is in `complete_audit_final.json`; the Krikri v1.5 hashes match job 3390957's recovery receipt.

Across those response cells, frozen v1 marked 3,112 passes and candidate v2 marked 3,226. This net difference is not an adjusted benchmark result. It decomposes into 19 v1-only and 133 v2-only decisions:

- 20 v1 passes traversed the empty-string collapse; v2 retained 2 semantically equal cases and rejected 18 mismatches.
- 476 responses contained an explicit final-answer construction whose extraction changed; 124 known false negatives became passes.
- One locale-sensitive separator response was accepted only by v1's dual reading.
- The remaining nine v2-only decisions are recoveries from explicit answer prose without a colon or a formatted numeric reference; sampled examples in the audit are consistent with the reference answer.

| Stored column | Language | Frozen v1 | Candidate v2 | v1 only | v2 only |
|---|---:|---:|---:|---:|---:|
| Apertus | el | 61/500 | 77/500 | 0 | 16 |
| Apertus | en | 9/500 | 120/500 | 0 | 111 |
| Gemma | el | 391/500 | 392/500 | 0 | 1 |
| Gemma | en | 405/500 | 406/500 | 0 | 1 |
| original Krikri | el | 161/500 | 159/500 | 2 | 0 |
| original Krikri | en | 156/500 | 153/500 | 3 | 0 |
| Meltemi | el | 42/500 | 43/500 | 0 | 1 |
| Meltemi | en | 44/500 | 47/500 | 0 | 3 |
| Qwen | el | 394/500 | 394/500 | 0 | 0 |
| Qwen | en | 408/500 | 408/500 | 0 | 0 |
| stored `bench_B` | el | 38/500 | 37/500 | 1 | 0 |
| stored `bench_B` | en | 79/500 | 76/500 | 3 | 0 |
| stored `bench_P` | el | 50/500 | 50/500 | 0 | 0 |
| stored `bench_P` | en | 79/500 | 77/500 | 2 | 0 |
| stored `bench_PB` | el | 56/500 | 56/500 | 0 | 0 |
| stored `bench_PB` | en | 68/500 | 68/500 | 0 | 0 |
| G3F2P1 (stored `bench_R3`) | el | 40/500 | 40/500 | 0 | 0 |
| G3F2P1 (stored `bench_R3`) | en | 90/500 | 89/500 | 1 | 0 |
| stored `bench_S1` | el | 64/500 | 63/500 | 1 | 0 |
| stored `bench_S1` | en | 82/500 | 81/500 | 1 | 0 |
| Krikri v1.5 | el | 191/500 | 189/500 | 2 | 0 |
| Krikri v1.5 | en | 204/500 | 201/500 | 3 | 0 |

## Candidate behavior and release gate

Candidate v2 changes only experiment-side scoring:

1. It recognizes categorical text before normalization and strips a trailing text block only when its content is a recognized unit expression.
2. It extracts `Answer:`, `Απάντηση:`, `The final answer is`, and `Η τελική απάντηση είναι`, including a value on the following nonempty line.
3. It requires `prediction_locale=el|en`. A single separator with exactly three trailing digits follows that locale; other single-separator decimals remain accepted. It never emits two numeric readings.
4. The score wrapper requires 500 unique IDs exactly matching the benchmark and refuses to overwrite its output.

The five regression groups pass. Before adoption, review the locale policy and the complete changed-decision list, then pin one scorer digest and rescore every selected frozen response file. All 22 cells have been processed by this candidate audit, but their candidate values should remain diagnostic until that scientific review is complete. Preserve v1 under a clearly named historical metric rather than overwriting it.
