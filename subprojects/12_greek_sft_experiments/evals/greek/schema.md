# Greek evaluation result schema

`greek.json` uses `schema_version: "greek-evals-v1"` for both measured runs and card imports.

## Top level

| field | meaning |
| --- | --- |
| `source` | `measured` for a model run, `card` for `--pull-card` |
| `model` | requested model ID/path, optional revision, and the offline-resolved path for measured runs |
| `timestamps` | UTC start and completion timestamps |
| `limit` | per-benchmark smoke limit, or `null` for a full evaluation |
| `mode` | `chat` or `base` |
| `commands` | ordered argv arrays and shell-rendered forms for every command run |
| `ellinika` | four-language ellinika-bench results, or `available: false` when absent from the card |
| `greekmmlu` | decontaminated GreekMMLU `accuracy` and `n` |
| `native_greek` | eight benchmark records plus their unweighted accuracy macro |
| `provenance` | paths, SHA-256 values, and source-file Git commits where available |

## Ellinika-bench

`ellinika.languages` has exactly `el`, `en`, `fr`, and `de`. Each language contains `n_items` and a
`pillars` object. A pillar record has:

- `accuracy_gen`, `n_gen`: accuracy and denominator over all auto-gradable items in that pillar.
- `accuracy_ll`, `n_ll`: likelihood accuracy and denominator over the pillar's MCQ items only.
- `ll_population: "mcq_only"`: an explicit warning that likelihood is not defined for free-form,
  exact-string, or numeric items.
- `format_valid_rate` and `flags`: the unchanged `clariden_eval.py` diagnostics for that pillar.

The launcher imports `clariden_eval.py` and calls its unchanged `run_lang` separately for each pillar.
This is necessary because its command-line JSON reports likelihood only for the language-wide MCQ
population, whereas this schema requires pillar-level likelihood.

## Native-Greek suite

`native_greek.benchmarks` has exactly these keys: `asep_mcqa`, `demosqa`, `gpcr`, `medical_mcqa`,
`oyxoy_metaphor`, `oyxoy_nli`, `oyxoy_wic`, and `oyxoy_wsd_definition`. Each contains `accuracy` and
`n`. `native_greek.macro_accuracy` is the unweighted arithmetic mean of those eight accuracies.

The measured path is FP32, zero-shot, length-normalized candidate continuation likelihood. It runs
the frozen `run_checkpoint_suite.py` in `legacy` mode with candidate batch size 1. GreekMMLU is run
through the original `run_native_greek_mcq_eval.py` and restricted to the frozen 16,159-ID clean
subset before aggregation.
