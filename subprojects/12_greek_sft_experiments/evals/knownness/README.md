# Greek-reality knownness scorer

This pipeline labels factual claims in the SFT data using two separate signals:

1. **Corpus presence:** the number of sampled CPT documents containing every key entity extracted
   from the claim. This is exposure evidence, not proof that the model memorized the fact.
2. **Model answers:** a fixed four-shot short-answer prompt, one greedy completion and four
   temperature-0.5 completions from the base model.

The model-side protocol follows the Known/Unknown idea of Gekhman et al. (2024): convert a factual
statement into a question whose answer can be checked, probe the pre-fine-tuning model repeatedly,
and distinguish consistently retrievable knowledge from facts it does not retrieve. This
implementation uses the brief's operational rule rather than claiming exact reproduction of every
paper setting: `known` means the greedy answer contains the normalized short gold answer;
`weakly_known` means at least one of four samples contains it; otherwise the claim is `unknown`.
Normalization applies Unicode case-folding, removes combining marks and punctuation, and matches
whole token sequences. Four fixed exemplars are written separately in Greek, English, French and
German; none comes from the SFT data.

## 1. Make questions

```bash
python evals/knownness/make_questions.py \
  --claims ~/Projects/natural-greek-sft/data/exports/reality_claims.jsonl \
  --out /path/to/questions.jsonl \
  --limit 200
```

Sol receives batches of at most 20 claims, grouped by output language. It must return strict JSON
containing one question, one short answer, and an entity list for every input id. Responses are
cached by the exact prompt SHA-256 under `evals/knownness/cache/`, which is ignored by Git. Invalid,
partial, reordered, fenced, or otherwise nonconforming responses stop the run. Re-running the same
input and prompt version reuses only validated cache entries.

The output preserves `row_index` and `row_occurrence`. These are needed because the current export
contains repeated `(source, row_id)` keys; `claim_id` and `row_key` therefore remain unambiguous.

## 2. Measure corpus presence

The default reads the cached public snapshot in offline streaming mode and deterministically samples
one percent of documents:

```bash
HF_HUB_OFFLINE=1 python evals/knownness/corpus_presence.py \
  --questions /path/to/questions.jsonl \
  --out /path/to/presence.jsonl \
  --sample-fraction 0.01
```

For a full local corpus, use a quoted glob and scan every document:

```bash
python evals/knownness/corpus_presence.py \
  --questions /path/to/questions.jsonl \
  --corpus-glob '/path/to/corpus/**/*.jsonl*' \
  --sample-fraction 1 \
  --out /path/to/presence.jsonl
```

Supported glob inputs are JSONL (optionally gzip-compressed), JSON, Parquet, or text. Homogeneous
non-JSONL inputs are streamed through `datasets`. `--text-field text` selects a field explicitly;
without it, common text fields are tried before recursively joining string values.

Sampling is a deterministic hash sample over document index and a text prefix. The script still
streams the corpus once, but expensive entity matching runs only on selected documents. It reports
the empirical `sampled_fraction`; `observed_doc_count` is the actual sample count and `doc_count` is
the rounded estimate `observed_doc_count / sampled_fraction`. A document counts for a claim only
when **all** of that claim's normalized entity strings occur in the same document. Claims with no
entities receive zero rather than the vacuous count of every document. The dependency-free
Aho–Corasick matcher scans all entity strings together.

## 3. Probe the base model and aggregate rows

Run inside the E0b node allocation with a local model directory and the pre-populated HF cache:

```bash
HF_HUB_OFFLINE=1 python evals/knownness/score_claims.py \
  --model /path/to/base-model \
  --questions /path/to/questions.jsonl \
  --presence /path/to/presence.jsonl \
  --rows-glob 'data/natural_greek_sft_*.jsonl' \
  --out results/e0b
```

The scorer automatically uses `data/natural_greek_sft_*.jsonl` as the row universe when those files
are present. `--rows-glob` overrides that default and may be repeated. A row universe is required to
emit explicit `none` records for SFT rows absent from the claims export; without one the scorer emits
a warning and can cover only rows represented in the question file. Files need `row_id` and `source`
or `config`; for the named data files the source is inferred from the filename when neither field
exists. With `--limit`, only that many question records are scored; with `--max-steps`, at most that
many generation batches run.

The output directory receives:

- `knownness.jsonl`: question, gold answer, five model answers, claim label, and corpus signal;
- `knownness_rows.jsonl`: one row-side-table record with `none | known | mixed | unknown`;
- `knownness_summary.json`: total distributions, claim labels per config and per declared `basis`,
  corpus-presence coverage, and protocol settings.

A row is `known` when every claim is `known` or `weakly_known`, `unknown` when every claim is
`unknown`, `mixed` otherwise, and `none` when it has no claims. Corpus counts remain a separate
signal: text occurrence can be false support, absence in a sample is not evidence of corpus absence,
and neither result overrides the answer-based Gekhman label.

The scorer is single-process and emits the required heartbeat at least every 60 seconds. It uses
only local model/tokenizer files and verifies the bound Apertus vocabulary size plus BOS/EOS identity
before loading weights. `--dry-run` prints the resolved plan and deliberately permits placeholder
paths for the acceptance command; a real run validates question/presence/row files and tokenizer
identity before loading model weights. Prompt token counts are intentionally reported as not computed
when the placeholder paths do not exist. With real local model and question paths, dry-run loads and
validates the tokenizer (never the model), reports the exact four-shot prompt-token total, question
count, five planned generations per question, and the maximum number of new tokens.

## Tests

```bash
python evals/knownness/test_knownness.py
python evals/knownness/score_claims.py --dry-run --model x --questions x --out x
```

The unit test uses a fake generator and five synthetic claims; it makes no model or network calls.
