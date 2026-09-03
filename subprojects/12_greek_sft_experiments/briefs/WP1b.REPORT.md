# WP1b report — Greek evaluation launcher

## Built

- `evals/greek/run.sh`: the requested positional shell interface and fixed Python default.
- `evals/greek/run_greek_evals.py`: a sequential, offline-compatible launcher for ellinika-bench,
  decontaminated GreekMMLU, and the strict native-Greek eight; it also imports card metrics.
- `evals/greek/schema.md`: the common `greek-evals-v1` contract.
- `evals/greek/README.md`: node inputs, environment overrides, invocation, and failure boundaries.

The measured run writes `results/<run>/greek.json`, records exact argv/shell commands, UTC timestamps,
model ID/revision, source paths, SHA-256 hashes and source Git commits. It runs with no scheduler calls,
sets both Hugging Face offline variables for runtime children, emits heartbeats, and refuses overwrite.

Ellinika-bench uses the unchanged functions in
`~/Projects/apertus-local-chat/benchmark/clariden_eval.py`. The wrapper calls `run_lang` per pillar
after one model load because the upstream CLI only emits a language-wide MCQ likelihood result; this
produces the requested per-pillar generative and MCQ-likelihood accuracies without editing upstream.

The authoritative frozen native scorer is
`../09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py`:

- source Git commit: `05d1a724581c997eb9f2b6dd769fbad3b933c217`
- file SHA-256: `b8dd47a224cd9024d8c18241077d01e6f9373d5657dc005c021d3b142ca5761c`

It is invoked unchanged in FP32 `legacy` mode, candidate batch size 1. GreekMMLU uses the unchanged
underlying scorer
`../03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py`:

- source Git commit: `5b6dd2605dae3b714c662ac48eeeeace69b6cd53`
- file SHA-256: `c0e3e64d2bbd83fc8eb20dc2491b9aa7f8f1450ca7937bd247402159fe33f20e`

## Local commands and observed output

Command:

```sh
bash -n evals/greek/run.sh
```

Output: none; exit 0.

Command (the brief's dry-run acceptance):

```sh
bash evals/greek/run.sh x y --dry-run
```

Output: a resolved JSON configuration followed by exactly two lines beginning:

```text
CMD ellinika-bench: /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python ... --internal-ellinika ... --clariden-eval /Users/foivoskarounos-zamparloukos/Projects/apertus-local-chat/benchmark/clariden_eval.py ...
CMD greekmmlu+native: /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python ... --internal-score ... --scorer /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py ...
```

`rg -c '^CMD ' /tmp/wp1b-dry-run.out` printed `2`.

Command (card acceptance, using the mandated Python and a permitted temporary output rather than
writing under `results/`):

```sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python \
  evals/greek/run_greek_evals.py \
  --pull-card 18-avg-uniform5-tokens30B-50B \
  --out /tmp/wp1b-card-greek.json
```

Output:

```json
{"greekmmlu": 0.5677950368215855, "native_macro": 0.4992749999999999, "ok": true, "out": "/private/tmp/wp1b-card-greek.json"}
```

Command:

```sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python - <<'PY'
import json
p=json.load(open('/tmp/wp1b-card-greek.json'))
print(json.dumps({'source':p['source'],'schema':p['schema_version'],'greekmmlu':p['greekmmlu'],'native_macro':p['native_greek']['macro_accuracy'],'native_keys':list(p['native_greek']['benchmarks'])},sort_keys=True))
PY
```

Output:

```text
{"greekmmlu": {"accuracy": 0.5677950368215855, "n": 16159}, "native_keys": ["asep_mcqa", "demosqa", "gpcr", "medical_mcqa", "oyxoy_metaphor", "oyxoy_nli", "oyxoy_wic", "oyxoy_wsd_definition"], "native_macro": 0.4992749999999999, "schema": "greek-evals-v1", "source": "card"}
```

A second dry run with `--revision rev --mode base --limit 3` exited 0, printed two command lines,
and resolved `model: "x@rev"`, `mode: "base"`, and `limit: 3`. Local unit assertions over the card
schema, GreekMMLU value, eight-task coverage, macro, run-name validation and scorer provenance printed
`unit assertions: PASS`.

The bare `python` command is absent in this shell (`zsh: command not found: python`); all successful
Python checks used the interpreter required by the brief.

## Not tested locally

- No measured model evaluation was run: the Mac has no CUDA device and the brief assigns cluster
  execution to Claude.
- The Mac does not mount the strict 73,894-row native manifest/examples or the 16,159-row GreekMMLU
  clean-ID assets. Their matching contract/manifest paths must be supplied on the node. The launcher
  validates existence, hashes, row counts, and the offline GreekMMLU cache before loading weights.
- No full checkpoint was resolved or loaded and no output was written under `results/`.

No additional packages were needed locally. The upstream native scorer requires its established
Clariden runtime (including `accelerate` for `device_map="auto"`); this was not installed or changed.

## Open question for node acceptance

Claude must bind `NATIVE_GREEK_CONTRACT` and `NATIVE_GREEK_MANIFEST` to the matching strict 73,894-row
rebound asset pair. The repository's historical three-checkpoint default manifest is the 83,970-row
pre-filter population and is deliberately rejected rather than silently producing incomparable scores.
