# WP0 report

## What I built

- `data/build_sft_mix.py`: a deterministic builder for E1, E2, E3, and
  E3prime. It binds immutable Hub revisions, caches the eleven source JSONL
  files under `data/cache/`, validates roles/content, derives exact rounded 2%
  dev selections by SHA-256 rank of seed/config/row ID, and shuffles train rows
  with seed 1234.
- Eleven `data/splits/<config>.dev.txt` files and a common 658-row
  `data/arms/dev_all.jsonl`. Every arm's `dev.jsonl` is byte-identical to this
  common file.
- Per-arm train JSONL files with only `messages`, `row_id`, `config`, and
  `category`. E3prime reads `en.messages` for its three imported train slices;
  the other variants use the brief's adapted fields.
- `data/stats.json`: source/file hashes, immutable dataset/model revisions,
  control-token ID checks, per-config and per-arm train/dev counts, Greek-CPT
  token counts, assistant-content shares, reference-tokenizer planning counts,
  maximum lengths, and explicit exclusions.
- `data/contamination_report.md`: identifier-only overlap findings against
  ellinika-bench, GreekMMLU test, GSM8K test, and IFEval. The private native
  suite was unavailable and is recorded as such.
- `data/README.md`: build/check commands and the data contract.

Final outputs contain zero rows over 4096 Greek-CPT tokens. Ten source variants
were explicitly excluded for length (one `no_robots_en_pov` adapted row and
nine `apertus_en` raw rows); they were not truncated. One `personas_if` row
without an assistant turn was excluded before splitting. The contamination scan
found five exact GreekMMLU matches, removed those five `(config, row_id)` values
from every applicable train arm/variant, and found zero additional near hits at
the stated threshold. Final exact overlap is zero.

Final train receipts:

| arm | rows | Greek-CPT tokens | assistant-content share | max length |
| --- | ---: | ---: | ---: | ---: |
| E1 | 17,602 | 6,182,367 | 0.57011902 | 3,035 |
| E2 | 26,910 | 9,359,190 | 0.56497186 | 3,112 |
| E3 | 22,919 | 8,973,164 | 0.57989155 | 4,024 |
| E3prime | 22,910 | 10,469,389 | 0.62961430 | 4,075 |

## Important planning-count finding

The supplied §5a-prime totals are not Greek-CPT tokenizer totals. A direct
same-render comparison showed that the Greek-CPT tokenizer gives 151 tokens for
one inspected row while the unextended Apertus Instruct tokenizer gives 236.
No row text was printed. The §5a-prime figures track the reference tokenizer:
E1 9.164728M, E2 12.345952M, and E3 11.955866M after required removals, all
within 2% of the approximate figures when compared at their reported 0.01M
precision. `stats.json` therefore keeps:

- `tokens`: the authoritative rendered Greek-CPT count required by WP0;
- `planning_reference_tokens`: a separately named audit count used only for
  the legacy §5a-prime estimate check.

The builder does not relabel or substitute the reference count as training
tokens.

## Commands and observed output

Syntax and diff-whitespace preflight:

```text
$ /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m py_compile data/build_sft_mix.py
[no output; exit 0]

$ git diff --check -- data/build_sft_mix.py data/README.md
[no output; exit 0]
```

The initial end-to-end attempts found and were used to fix three issues:

```text
$ /usr/bin/time -p /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
ERROR: [Errno 1] Operation not permitted: '/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/datasets--dascim--GreekMMLU'
real 24.71
user 3.51
sys 1.38

$ /usr/bin/time -p /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
ERROR: tokenizer returned an unexpected batch size
real 30.02
user 5.44
sys 0.87

$ /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
ERROR: E2 has 1 rows over 4096 tokens (max=7173); E3prime has 9 rows over 4096 tokens (max=5234); E1 token total 6182367 is outside the 2% window around 9340000; E2 token total 9366363 is outside the 2% window around 12600000; E3 token total 8973164 is outside the 2% window around 12190000

$ /usr/bin/time -p /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
ERROR: E2 planning-reference token total 12345952 is outside the 2% window around 12600000 (Greek-CPT total is 9359190)
real 43.34
user 39.37
sys 1.70
```

The fixes route transient Hugging Face metadata to `/private/tmp`, request
batched template IDs rather than a `BatchEncoding`, explicitly remove and count
overlength variants, distinguish the two tokenizer counts, and compare the
approximate planning totals at their stated precision.

Successful build:

```text
$ /usr/bin/time -p /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
BUILT E1=6182367 E2=9359190 E3=8973164 E3prime=10469389
real 43.00
user 39.33
sys 1.09
```

Required check:

```text
$ /usr/bin/time -p /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py --check
OK
real 41.51
user 39.00
sys 1.37

$ /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py --check
OK
```

Independent schema/dev check (the command parsed every train row without
printing content):

```text
dev_all_sha256 16edc116bf0be777666356dadc3da1786b52fae0daaec681994caa9aef8056e3
E1 dev_identical True train_dev_intersections 0 unique_train_ids 17602
E2 dev_identical True train_dev_intersections 0 unique_train_ids 26910
E3 dev_identical True train_dev_intersections 0 unique_train_ids 22919
E3prime dev_identical True train_dev_intersections 0 unique_train_ids 22910
```

Control/evaluation receipt inspection:

```text
contamination {'final_exact_hits': 0, 'pre_drop_exact_hits': 5, 'pre_drop_near_hits': 0, 'train_rows_dropped': 5}
evals {'ellinika_bench': ('available', 1788), 'greek_mmlu': ('available', 16632), 'gsm8k': ('available', 1319), 'ifeval': ('available', 541), 'native_greek_suite': ('unavailable', 0)}
controls 13 True
```

Final assertion-only validation (no row content printed):

```text
FINAL_LOCAL_OK controls=13 exact=0 overlength=0 dev_sha256=16edc116bf0be777666356dadc3da1786b52fae0daaec681994caa9aef8056e3
```

The reference template emits 13 textual control tokens: BOS `<s>` plus 12
role/tool delimiters. All 13 emitted tokens are in both added-token
vocabularies with identical IDs. `<|image|>` is not a vocabulary token in
either tokenizer and is never emitted for these text-only rows; it is recorded
separately as a validation sentinel, not counted as a control token.

## What I could not test

- `fffoivos/native-greek-suite` did not exist or was not accessible with the
  available Hugging Face credential, so no native-suite prompt could be scanned.
- I did not run trainer integration, GPU execution, or any cluster command; the
  cluster clause forbids those in WP0.
- I did not test a single uninterrupted build from a completely empty cache.
  The failed early attempts populated source/evaluation caches; the successful
  build and `--check` both used those immutable cached files.
- I did not stage or commit files. No additional package was needed.

## Open questions / handoff

1. The parent repository's `.gitignore` line 20 ignores
   `subprojects/**/data/`, including the script, README, stats, report, and split
   lists—not only the intended bulk JSONL/cache outputs. This WP was forbidden
   from editing paths outside its deliverables, so Claude must force-add the
   small intended files (or separately fix the parent ignore rules) when
   committing. Keep `data/cache/` and `data/arms/**/*.jsonl` ignored.
2. Confirm that the planning/budget ledger should be corrected from the
   reference-tokenizer estimates to the Greek-CPT totals above before computing
   steps and node-hour forecasts.
3. If the private native suite is renamed or access is granted, rerun with
   `--refresh-revisions` to bind it and regenerate the overlap report.
