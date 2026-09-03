# Greek SFT mixture data

`build_sft_mix.py` materializes the four round-one arms from the immutable
Hugging Face and tokenizer revisions recorded in `stats.json`.

Run it with the project Python:

```sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python data/build_sft_mix.py --check
```

The first command writes:

- `splits/<config>.dev.txt`: the fixed 2% dev row IDs. The split is the exact
  rounded 2% count with the lowest SHA-256 ranks of
  `1234\0<config>\0<row_id>`.
- `arms/<arm>/train.jsonl`: shuffled with seed 1234.
- `arms/dev_all.jsonl` and each arm's byte-identical `dev.jsonl`: the union of
  the eleven adapted dev subsets. This common set is intentional so dev loss
  stays comparable across arms. E3prime changes only its three train slices to
  the raw `en.messages` conversations.
- `stats.json`: source identities, template/control-token checks, and row/token
  statistics. Token counts render the Apertus template with a fixed
  `strftime_now` result of `2026-09-04`; this avoids date-dependent receipts.
- `contamination_report.md`: identifier-only exact and 8-gram containment hits.

Output rows contain only `messages`, `row_id`, `config`, and `category`. Messages
retain multiple turns and only the `system`, `user`, and `assistant` roles.
Rows without a usable non-empty assistant turn are excluded before splitting.
Exact train/evaluation prompt matches remove the complete `(config, row_id)`
from every arm and adapted/raw variant. Near matches are listed but retained.
Rows above 4096 Greek-CPT tokens are also explicitly excluded, with per-config
counts in `stats.json`, rather than being silently truncated.

Source and evaluation downloads are materialized as ignored JSONL files under
`data/cache/`; temporary Hugging Face download metadata is staged outside the
repository. The existing `data/**/*.jsonl` ignore rule covers both bulk outputs
and caches. Delete `data/cache/` to force a redownload of the recorded immutable
revisions. Use `--refresh-revisions` deliberately to bind a new source snapshot.

The builder does not apply the template to stored rows. TRL receives the
`messages` column and applies the recorded Apertus Instruct template at training
time. `assistant_content_tokens` counts assistant content only, excluding role
control tokens.

`tokens` is always the required Greek-CPT tokenizer count. The supplied §5a′
estimates were made with the less Greek-efficient reference Instruct tokenizer;
`planning_reference_tokens` preserves that second count solely so `--check`
can audit the stated ±2% planning estimate without relabeling it as the training
token count.
