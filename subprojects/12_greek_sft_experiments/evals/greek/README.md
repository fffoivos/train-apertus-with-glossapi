# WP1b Greek evaluation launcher

Run from the repository root:

```sh
bash evals/greek/run.sh /path/to/hf-checkpoint E1-epoch1 --mode chat
bash evals/greek/run.sh fffoivos/model E1-epoch1 --revision revision-name --mode chat
bash evals/greek/run.sh x smoke --mode base --limit 8 --dry-run
```

The launcher is single-process and sequential at the evaluation level. It runs ellinika-bench first,
then GreekMMLU and the native-eight guard, prints heartbeat lines while each child tool runs, and
writes `results/<run_name>/greek.json`. It refuses to overwrite an existing run directory. `chat`
uses the tokenizer's chat template automatically; `base` uses raw prompts.

`--dry-run` prints one resolved configuration followed by exactly two stage commands and exits before
checking the model or loading any weights. On a real run, an HF model ID is accepted only if the exact
ID/revision snapshot is already in the Hugging Face cache. Child processes set `HF_HUB_OFFLINE=1` and
`HF_DATASETS_OFFLINE=1`.

## Frozen evaluator inputs

The repository supplies defaults for the source scripts, registry, and original three-checkpoint
contract. The large frozen data assets remain on CSCS. The launcher requires the strict 73,894-row
population; therefore set both contract and manifest when the default three-checkpoint manifest is
the older 83,970-row pre-filter population:

```sh
export ELLINIKA_CLARIDEN_EVAL=/path/to/apertus-local-chat/benchmark/clariden_eval.py
export NATIVE_GREEK_SCORER=/path/to/run_checkpoint_suite.py
export NATIVE_GREEK_RUNNER=/path/to/run_native_greek_mcq_eval.py
export NATIVE_GREEK_REGISTRY=/path/to/native_greek_benchmark_registry.json
export NATIVE_GREEK_CONTRACT=/path/to/contract.json
export NATIVE_GREEK_MANIFEST=/path/to/manifest.json
export GREEKMMLU_CLEAN_MANIFEST=/path/to/greekmmlu_clean_subset_manifest.json
```

Before loading a model, the launcher verifies every source file, all four ellinika data directories,
the native manifest-to-contract hash, the frozen example payload hash, the GreekMMLU clean-ID payload
hash and count, and the offline GreekMMLU dataset cache. The measured output records paths, SHA-256
hashes, and Git commits for both upstream scorer files.

The authoritative native scorer is
`../09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py`, invoked unchanged in FP32
legacy mode with candidate batch size 1. Its model contract intentionally rejects checkpoint geometry
or tokenizer drift. GreekMMLU uses the unchanged evaluator at
`../03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py`
and the same frozen clean-ID population used by the CPT card.

## Card import

The base checkpoint is not evaluated again:

```sh
python evals/greek/run_greek_evals.py \
  --pull-card 18-avg-uniform5-tokens30B-50B \
  --out results/E0b/greek.json
```

This fetches `checkpoint-index.json` from `fffoivos/apertus-8b-greek-cpt` at `main`, selects either a
checkpoint or average by revision/branch, and writes the same top-level schema with `source: "card"`.
The card has no ellinika-bench measurements, so that section is present with `available: false`.
