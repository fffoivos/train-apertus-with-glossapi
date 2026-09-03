# ILSP Greek evaluation tasks

This package adds two external tasks for EleutherAI's `lm-evaluation-harness`:

- `ifeval_greek`: all 541 rows from the `train` split of `ilsp/ifeval_greek`, with the upstream four strict/loose prompt- and instruction-level metrics.
- `mgsm_greek`: zero-shot chat generation on the 250-row `test` split of `ilsp/mgsm_greek`, scored by exact match on the last generated number.
- `mgsm_greek_4shot`: the same MGSM test with the first four exemplars from the eight-row `train` split and their supplied worked answers. With `--apply_chat_template`, harness few-shot examples are formatted as chat turns.

The implementation was checked against EleutherAI `lm-evaluation-harness` main at commit `b954108c9baaaa934b4ad842033b31a97ee30816` (2026-09-01). The task data are CC BY-NC-SA 4.0; the checker structure derives from the Apache-2.0 Google Research/EleutherAI IFEval implementation.

## Greek IFEval semantics

The ILSP rows contain the same 25 instruction IDs as English IFEval, with two renamed case IDs: `change_case:capital` and `change_case:lowercase`. Every ID is registered locally.

Language-bound checks use these rules:

- Upper/lower-case checks inspect Greek alphabetic characters with Python's Unicode-aware `str.isupper()` and `str.islower()`. Tonos-bearing capitals such as `Ά` are uppercase. The all-capital-word frequency checker counts whitespace-delimited words containing Greek letters.
- Letter frequency is Unicode-casefolded and accent-insensitive. Thus an unaccented Greek target letter also counts its tonos-bearing form. The two punctuation targets present in the data are counted literally.
- Word counts use whitespace-delimited tokens after stripping Unicode punctuation/symbols at token edges; punctuation-only tokens do not count.
- Language detection uses `langdetect` when installed. If it is absent or cannot classify a response, only Greek can be recovered: Greek alphabetic script share must be at least 0.6. The dataset's 31 `language:response_language` constraints retain their original non-Greek ISO codes, so full scoring of those rows requires `langdetect`.
- Required keywords, keyword frequency, and forbidden words use Unicode casefold plus accent removal. Required keyword checks are literal substring checks; forbidden terms use Unicode word boundaries.
- `end_phrase`, `first_word`, `postscript_marker`, `prompt_to_repeat`, and `section_spliter` are taken verbatim from each row's kwargs. End/first-word comparisons are case-insensitive but accent-sensitive. `Υ.Γ.` is recognized only at the start of a line.
- JSON, title, placeholder, section, bullet, highlight, paragraph-divider, two-response, quotation, and comma constraints retain the upstream structural rules. Sentence splitting additionally recognizes the Greek question-mark semicolon.

Comparison with `google/IFEval` by row key found localized values in `end_phrase` (26), `first_word` (12), `forbidden_words` (44), `keyword` (42), `keywords` (36), `letter` (31), `postscript_marker` (26), `prompt_to_repeat` (41), and `section_spliter` (14). Five forbidden-word lists, three keyword lists, and two letter targets remain unchanged. Numeric thresholds, `less than`/`at least` relations, and response-language codes remain unchanged. The postscript marker is `Υ.Γ.`; localized section splitters are `ΕΝΟΤΗΤΑ`, `Ενότητα`, `Ημέρα`, `Κοινό`, and `ΠΑΡΑΓΡΑΦΟΣ`. End phrases and first words are used row-by-row without a hard-coded translated inventory.

## Greek MGSM semantics

The zero-shot task prepends the requested Greek step-by-step instruction and asks for a final line of the form `Απάντηση: <αριθμός>`. Scoring extracts the last numeric token, accepts Unicode minus, removes spaces/apostrophes and Greek-style period thousands separators, accepts comma decimals, converts with `Decimal`, and compares numerically with `answer_number`.

## Running

The launcher assumes the model, both datasets, and harness are already cached/installed. Actual evaluation forces Hugging Face offline mode.

```bash
bash evals/ilsp/run.sh /path/to/model run-name
bash evals/ilsp/run.sh /path/to/base-model run-name --mgsm-4shot
bash evals/ilsp/run.sh /path/to/model run-name --vllm --limit 20
bash evals/ilsp/run.sh x y --dry-run
```

Raw harness output goes to `results/<run-name>/ilsp/`. The launcher then writes `results/<run-name>/ilsp.json` containing the four IFEval metrics and MGSM exact match. `--max-steps N` is accepted as an evaluation-probe alias for `--limit N`.

Run the local tests with the brief's Python environment:

```bash
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m pytest evals/ilsp/tests -q
```
