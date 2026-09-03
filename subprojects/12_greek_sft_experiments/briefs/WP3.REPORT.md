# WP3 report — knownness scorer

## Built

- `evals/knownness/make_questions.py`
  - Reads the reality-claims JSONL and gives every claim an unambiguous ID using source, row ID,
    repeated-row occurrence, and claim index.
  - Groups claims by Greek, English, French, or German; sends at most 20 per `run_sol` call; rejects
    anything except the exact JSON schema and input order.
  - Uses a prompt-versioned SHA-256 cache under the gitignored `evals/knownness/cache/` and writes the
    final question JSONL atomically.
- `evals/knownness/corpus_presence.py`
  - Streams either the offline HF snapshot or local JSONL/JSON/Parquet/text shards.
  - Uses deterministic hash sampling (1% by default) and a dependency-free Aho–Corasick matcher.
  - Counts a document only when all normalized entities for a claim occur in that document; records
    observed and scaled counts, empirical sample fraction, seed, and corpus totals.
- `evals/knownness/score_claims.py`
  - Uses four fixed, non-data exemplars in the question's language, one greedy generation, and four
    temperature-0.5 generations.
  - Applies normalized whole-token-sequence containment and labels claims `known`, `weakly_known`, or
    `unknown`; aggregates rows to `none`, `known`, `mixed`, or `unknown`.
  - Merges corpus presence without using it to override the answer label, emits distributions by
    config and `basis`, supports automatic or explicit row-universe files, and writes the three
    requested files under `--out`.
  - Is single-process, local-files-only, supports `--dry-run`, `--limit`, and `--max-steps`, and emits
    the required heartbeat form. Before model-weight loading it verifies the expected Apertus
    vocabulary size, BOS, and EOS.
- `evals/knownness/test_knownness.py`
  - Exercises five synthetic claims through a fake generator, all claim and row label cases, answer
    normalization, prompt-language isolation, strict response parsing, JSONL corpus streaming, and
    multi-entity matching. It makes no model or network call.
- `evals/knownness/README.md`
  - Documents the operational Known/Unknown protocol, commands, schemas, sampling/count scaling,
    row rollup, limitations, and cluster handoff.

No packages were installed. The supplied environment already provides every imported runtime
dependency for the documented JSONL/JSON/Parquet/text paths (`datasets`, `transformers`, and
`torch`).

## Commands run locally and observed output

Python used throughout:

```text
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
```

Syntax check:

```bash
$PY -m py_compile evals/knownness/make_questions.py evals/knownness/corpus_presence.py evals/knownness/score_claims.py evals/knownness/test_knownness.py
```

Output: none; exit code 0.

Pytest and the brief's direct test command:

```bash
$PY -m pytest -q evals/knownness/test_knownness.py
$PY evals/knownness/test_knownness.py
```

```text
.                                                                        [100%]
1 passed in 0.01s
OK
```

Exact dry-run acceptance command:

```bash
$PY evals/knownness/score_claims.py --dry-run --model x --questions x --out x
```

```text
{"batch_size": 4, "dry_run": true, "limit": null, "max_new_tokens": 48, "model": "x", "model_exists": false, "out_dir": "x", "planned_generations": null, "planned_max_new_tokens": null, "presence": null, "prompt_token_count": "unavailable: model or questions path does not exist", "question_count": null, "questions": "x", "questions_exist": false, "rows_glob": ["data/natural_greek_sft_*.jsonl (auto if present)"], "steps": ["validate inputs", "load tokenizer", "load model", "greedy plus four samples", "aggregate rows"]}
```

Exit code 0. This did not create `x` or load a tokenizer/model.

Question-generation dry run over the requested first 200 claims:

```bash
$PY evals/knownness/make_questions.py \
  --claims /Users/foivoskarounos-zamparloukos/Projects/natural-greek-sft/data/exports/reality_claims.jsonl \
  --out /tmp/wp3-questions.jsonl --limit 200 --dry-run
```

```text
{"batch_size": 20, "by_language": {"el": 200}, "cache_dir": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/evals/knownness/cache", "claims": 200, "dry_run": true, "out": "/tmp/wp3-questions.jsonl"}
```

Full-export dry run:

```bash
$PY evals/knownness/make_questions.py \
  --claims /Users/foivoskarounos-zamparloukos/Projects/natural-greek-sft/data/exports/reality_claims.jsonl \
  --out /tmp/wp3-questions.jsonl --dry-run
```

```text
{"batch_size": 20, "by_language": {"de": 262, "el": 8226, "en": 1620, "fr": 284}, "cache_dir": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/evals/knownness/cache", "claims": 10392, "dry_run": true, "out": "/tmp/wp3-questions.jsonl"}
```

ID preservation check on the real export:

```bash
$PY - <<'PY'
import sys
sys.path.insert(0, 'evals/knownness')
from make_questions import load_rows
from pathlib import Path
p=Path('/Users/foivoskarounos-zamparloukos/Projects/natural-greek-sft/data/exports/reality_claims.jsonl')
rows=load_rows(p)
ids=[r['claim_id'] for r in rows]
print({'claims':len(rows),'unique_claim_ids':len(set(ids)),'row_keys':len(set(r['row_key'] for r in rows))})
PY
```

```text
{'claims': 10392, 'unique_claim_ids': 10392, 'row_keys': 5688}
```

Whitespace/error check:

```bash
git diff --check -- evals/knownness
```

Output: none; exit code 0.

One deliberate negative-path dry run was also made:

```bash
$PY evals/knownness/corpus_presence.py --questions /tmp/does-not-exist --out /tmp/wp3-presence.jsonl --dry-run
```

```text
ERROR: questions file not found: /tmp/does-not-exist
```

Exit code 1, as intended: unlike the scorer's explicitly required placeholder-path acceptance mode,
the corpus tool validates its input before its dry-run plan.

## Not run / not verified

- I did not call Sol. Therefore no 200-question artifact exists yet and no generated question sample
  was hand-checked. The `--limit 200` invocation above was dry-run only.
- I did not load or stream the public HF corpus, and did not inspect or scan the Clariden full corpus.
  No corpus-presence counts have been produced.
- I did not load the 8B base model or perform any real generation. The model/tokenizer path, CUDA
  execution, memory use, generation speed, heartbeat timing under load, and final label distribution
  remain unverified.
- The named `data/natural_greek_sft_*.jsonl` row-universe files were not present in this checkout at
  test time. Explicit `none` rows were verified only with the synthetic unit-test universe.
- I did not write under `results/`, use cluster commands, or install packages.

## Open questions for the cluster handoff

1. Claude must choose the full-corpus glob and, if auto-detection is inappropriate, its text field.
   The current reader supports JSONL/JSON/Parquet/text; another shard format needs a reader decision.
2. The default public-snapshot sample is a deterministic 1%. Claude should inspect the observed hit
   rate from the 200-claim probe before retaining that fraction for all 10,392 claims.
3. The first 200 Sol-produced question/answer/entity triples need the requested language and factual
   hand-check before corpus or model scoring.
4. For explicit `none` labels, pass the completed SFT row universe (or leave the default named data
   files present). If no row universe is found, the scorer warns and can label only claim-bearing rows.
