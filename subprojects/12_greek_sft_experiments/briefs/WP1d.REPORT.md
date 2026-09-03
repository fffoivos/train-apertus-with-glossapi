# WP1d report — ILSP Greek IFEval and MGSM

Date: 2026-09-04

## Built

- `evals/ilsp/tasks/ifeval_greek/`: a 541-prompt, zero-shot generation task for `ilsp/ifeval_greek` (`train`) with all 25 observed instruction IDs registered and the four upstream IFEval strict/loose metrics.
- Greek-aware constraints for Unicode upper/lower case (including tonos-bearing capitals), all-capital Greek words, accent-insensitive Greek letter frequency, whitespace word counts with Unicode/Greek punctuation, optional `langdetect` language classification with the specified 0.6 Greek-script fallback, accent-insensitive/casefolded keywords and forbidden words, and row-provided end/first-word/postscript markers. Structural format checks retain the upstream IFEval rules.
- `evals/ilsp/tasks/mgsm_greek/`: `mgsm_greek` zero-shot chat and deterministic `mgsm_greek_4shot` (first four `train` exemplars, with their supplied worked answers) on the 250-row `test` split. The scorer extracts the final number, handles Unicode minus, period/comma thousands notation and comma decimals, and compares with `answer_number` using `Decimal`.
- `evals/ilsp/run.sh`: HF default and optional four-GPU vLLM paths, `--limit`, `--max-steps` probe alias, `--dry-run`, `--mgsm-4shot`, offline/input preflight, heartbeat, raw harness output, and compact `results/<run_name>/ilsp.json` aggregation.
- `evals/ilsp/tests/`: 17 tests covering pass/fail cases for every requested Greek-aware checker category, all-capital word frequency, all 541 dataset rows and registry resolution/building, and MGSM extraction/scoring.
- `evals/ilsp/README.md`: task, checker, localization, dependency, score, and launcher documentation.

No files were written under `results/` while building or testing this package.

## ILSP kwarg audit

I compared `ilsp/ifeval_greek` with `google/IFEval` by the shared `key` field. All 541 keys matched.

Localized non-empty values:

| kwarg | changed occurrences |
| --- | ---: |
| `end_phrase` | 26 |
| `first_word` | 12 |
| `forbidden_words` | 44 |
| `keyword` | 42 |
| `keywords` | 36 |
| `letter` | 31 |
| `postscript_marker` | 26 |
| `prompt_to_repeat` | 41 |
| `section_spliter` | 14 |

The localized postscript marker is `Υ.Γ.`. The localized section splitters are `ΕΝΟΤΗΤΑ`, `Ενότητα`, `Ημέρα`, `Κοινό`, and `ΠΑΡΑΓΡΑΦΟΣ`. End phrases and first words are passed directly from each row rather than copied into code.

Unchanged values are the numeric thresholds, `less than` / `at least` relations, and response-language codes. Five forbidden-word lists, three keyword lists, and two letter targets also happen to be unchanged from the English source. The 31 response-language rows request 22 non-Greek language codes (`ar`, `bg`, `bn`, `de`, `fa`, `fi`, `gu`, `hi`, `it`, `kn`, `ko`, `mr`, `ne`, `pa`, `pt`, `ru`, `sw`, `ta`, `te`, `th`, `ur`, `vi`); those kwargs are honored verbatim.

No observed instruction ID remains unregistered or knowingly untranslated in checker behavior. Full classification of those 31 non-Greek response-language constraints requires `langdetect`; without it, the mandated script fallback can classify Greek only and conservatively fails other language codes.

## Commands run and outputs

The specified Python executable was used throughout:

```text
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
```

Harness availability:

```bash
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m pip show lm_eval lm-eval lm_eval_harness
```

Output (apart from pip's cache-permission warning):

```text
WARNING: Package(s) not found: lm-eval, lm_eval, lm_eval_harness
```

I then fetched the five upstream IFEval files from `EleutherAI/lm-evaluation-harness` main as the brief's prescribed fallback. The inspected main revision was:

```text
b954108c9baaaa934b4ad842033b31a97ee30816 2026-09-01T13:51:28Z
```

Dataset cards were fetched with `hf_hub_download(..., repo_type='dataset')` into `/private/tmp/wp1d_hf`. Output:

```text
ilsp/ifeval_greek /private/tmp/wp1d_hf/datasets--ilsp--ifeval_greek/snapshots/3ed53c2a790ce48020bf54aee70e1ea6c6b689b7/README.md
ilsp/mgsm_greek /private/tmp/wp1d_hf/datasets--ilsp--mgsm_greek/snapshots/27b0f7bf1732f9ff2cfc3e26d43293ba9d49ecd3/README.md
```

The dataset schema/registry audit used `datasets.load_dataset` for both ILSP repositories. Material output:

```text
IFEval rows: 541
IFEval columns: ['key', 'prompt', 'instruction_id_list', 'kwargs', 'prompt_en']
Instruction IDs (25)
MGSM splits: {'train': 8, 'test': 250}
train ['question', 'answer', 'answer_number', 'equation_solution']
test ['question', 'answer', 'answer_number', 'equation_solution']
```

The key-by-key comparison command loaded `ilsp/ifeval_greek` and `google/IFEval`, mapped rows by `key`, and compared aligned kwargs. Output:

```text
English rows 541 missing keys 0
Changed non-empty kwargs by key:
  end_phrase: 26
  first_word: 12
  forbidden_words: 44
  keyword: 42
  keywords: 36
  letter: 31
  postscript_marker: 26
  prompt_to_repeat: 41
  section_spliter: 14
Unchanged non-empty kwargs by key:
  capital_frequency: 25
  capital_relation: 25
  forbidden_words: 5
  frequency: 42
  keywords: 3
  language: 31
  let_frequency: 33
  let_relation: 33
  letter: 2
  nth_paragraph: 12
  num_bullets: 31
  num_highlights: 48
  num_paragraphs: 39
  num_placeholders: 27
  num_sections: 14
  num_sentences: 52
  num_words: 52
  relation: 146
```

Two intermediate pytest runs were made while fixing test-only issues. The first ended `2 failed, 14 passed in 2.81s` (a synthetic fixture changed inflection, and the sandbox rejected a home-cache lock); the second ended `1 failed, 15 passed in 3.56s` (the dataset download still inherited the home Hub cache). I corrected the fixture and set all HF test caches in `conftest.py` before importing `datasets`.

Final combined local verification:

```bash
bash -n evals/ilsp/run.sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m py_compile evals/ilsp/tasks/ifeval_greek/*.py evals/ilsp/tasks/mgsm_greek/*.py evals/ilsp/tests/*.py
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m pytest evals/ilsp/tests -q
bash evals/ilsp/run.sh x y --dry-run
```

Output (`bash -n` and `py_compile` emitted nothing):

```text
.................                                                        [100%]
17 passed in 2.59s
Resolved model: x
Resolved tasks: ifeval_greek,mgsm_greek
Dataset splits: ilsp/ifeval_greek:train=541; ilsp/mgsm_greek:test=250
Output summary: results/y/ilsp.json
Command: lm_eval --model hf --model_args pretrained=x\,dtype=bfloat16 --tasks ifeval_greek\,mgsm_greek --apply_chat_template --include_path evals/ilsp/tasks --output_path results/y/ilsp/
```

I also loaded all three YAML files with a local simulation of the current harness's path-based `!function` loader. Output:

```text
evals/ilsp/tasks/ifeval_greek/ifeval_greek.yaml ifeval_greek ilsp/ifeval_greek train
evals/ilsp/tasks/mgsm_greek/mgsm_greek.yaml mgsm_greek ilsp/mgsm_greek test
evals/ilsp/tasks/mgsm_greek/mgsm_greek_4shot.yaml mgsm_greek_4shot ilsp/mgsm_greek test
```

Optional vLLM/4-shot dry run:

```bash
bash evals/ilsp/run.sh x base-check --dry-run --vllm --mgsm-4shot --limit 3
```

Output:

```text
Resolved model: x
Resolved tasks: ifeval_greek,mgsm_greek_4shot
Dataset splits: ilsp/ifeval_greek:train=541; ilsp/mgsm_greek:test=250
Output summary: results/base-check/ilsp.json
Command: lm_eval --model vllm --model_args pretrained=x\,dtype=bfloat16\,tensor_parallel_size=4 --tasks ifeval_greek\,mgsm_greek_4shot --apply_chat_template --include_path evals/ilsp/tasks --output_path results/base-check/ilsp/ --limit 3
```

After the final import cleanup I reran the acceptance paths without bytecode writes:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m pytest evals/ilsp/tests -q
bash -n evals/ilsp/run.sh
bash evals/ilsp/run.sh x y --dry-run
```

Output (`bash -n` emitted nothing):

```text
.................                                                        [100%]
17 passed in 2.76s
Resolved model: x
Resolved tasks: ifeval_greek,mgsm_greek
Dataset splits: ilsp/ifeval_greek:train=541; ilsp/mgsm_greek:test=250
Output summary: results/y/ilsp.json
Command: lm_eval --model hf --model_args pretrained=x\,dtype=bfloat16 --tasks ifeval_greek\,mgsm_greek --apply_chat_template --include_path evals/ilsp/tasks --output_path results/y/ilsp/
```

## Not tested locally

- No real `lm_eval` invocation, model generation, model/tokenizer preflight, raw-result discovery, or final summary write: `lm_eval` is absent from the prescribed venv and the brief prohibits installing packages and writing under `results/`.
- No `langdetect` execution: the package is absent. The deterministic Greek script-share fallback is unit-tested. Install/provide `langdetect` in the actual harness environment for the non-Greek response-language rows.
- No vLLM/CUDA/GH200 execution and no cluster commands, per the cluster clause.
- No model-quality claim or metric value was produced.

Packages required beyond the prescribed local venv: `lm-eval` (actual harness run), `langdetect` (complete response-language scoring), and `vllm` only when `--vllm` is selected. No package was installed.

## Open questions / handoff checks

1. Before the first real run, confirm the selected cluster harness exposes the `lm_eval` executable and includes `langdetect`.
2. Pre-cache both ILSP datasets and the checkpoint/tokenizer. Actual runs force `HF_HUB_OFFLINE=1` and `HF_DATASETS_OFFLINE=1`.
3. The checkpoint tokenizer must contain a non-empty chat template; the launcher fails before model loading otherwise.
4. Run a small `--limit` probe to confirm the installed harness version accepts these external YAMLs and emits the expected result JSON shape before scoring all 791 prompts.
