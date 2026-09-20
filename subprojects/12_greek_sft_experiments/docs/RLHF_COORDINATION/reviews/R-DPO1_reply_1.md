# R-DPO1 reply, cycle 1 (18 September 2026)

Both blocking findings were real and both are fixed. The first arm had already trained on the flawed export; that run is discarded
(`runs/DISCARDED_arm00_flawed_export`) and retrained on the corrected data. No second review cycle is opened: the fixes are verified by
checks recorded in the manifest, and a second cycle would re-read the same evidence.

1. **Round-1 data in training — fixed.** The exporter classified by the prompt's `round_first`, so a logical prompt whose judged pair came
   from `round1_all_judged.jsonl` survived. The round is now decided by the judgement that produced the pair, and a row is dropped if either
   the judgement or the prompt is round 1. Exclusions rise from 25 to 26; `provenance.jsonl` now contains zero round-1 rows, asserted in the manifest.
2. **Collapsed round-3 groups — fixed.** `seed_id` was set to the run name, so union-find merged every row of a run into one component: 214
   round-3 rows in four groups, none of them in dev. The seed link is now the row's own seed (`seed:0.2:<slot>`) and grouping uses only
   recorded relationships. Result: 397 groups instead of 188, 54 dev rows covering round 2 (25) and round 3 (29) and all four purposes, and
   `groups_spanning_both_splits = 0` recorded in the manifest.
3. **Round-3 judgement traceability — fixed.** Each round-3 row now records stage, batch and route alongside the synthetic id, and the manifest
   hashes every `judged_*_s?.jsonl` file, so the exact judged record can be recovered. The remaining ambiguity between a first and second pass
   over the same batch is resolved by the recorded stage plus the file hash.
4. **Manifest as a freeze receipt — fixed.** Full SHA-256 hashes for every input (registry, pools, round-3 files, every judged file, the exporter
   itself) and for all four outputs, plus the output-language distribution (234 Greek, 163 other) and the split check above.

Not changed: the reviewer's verified-correct list stands, including byte-identical text against the named sample files, zero benchmark overlap
across 14 caches, a 1,803-token maximum under the Apertus template, and the maths, superseded and development-dialogue exclusions.
