# WP1c report — dev generation, format gate, voice score, blind reading page

## What I built

- `evals/dev/dev_generate.py`: a single-process, offline-compatible Transformers generator. It
  validates the prompt JSONL, the Apertus BOS/control-token IDs, and the chat template before model
  loading; imports the cached Apertus-Instruct template when the checkpoint has none; performs
  greedy batched generation for at most 512 new tokens; stops on `<|assistant_end|>` ID 68; emits
  heartbeats and per-record raw/display text, stop reason, and token counts. `--limit` and
  `--max-steps` both provide probe caps. `--dry-run` validates and prints the plan without loading a
  tokenizer/model or writing output.
- `evals/dev/format_gate.py`: computes and writes the three requested shares and fails unless
  termination and single-turn structure are each at least 0.95 and language/script compliance is at
  least 0.98. Per-item failures and measured Greek-script shares are retained in
  `format_gate.json`.
- `evals/dev/voice_score.py`: imports the stylometry implementation from
  `~/Projects/natural-greek-sft/scripts/style_compare.py`; it does not copy those calculations. It
  compares only Greek generations with assistant turns from the HF `no_robots` config, writes the
  original Biber-style rates, Burrows's Delta, and a deterministic reference split-half Delta as the
  parroting floor. A local reference export can be supplied for air-gapped testing.
- `evals/dev/prompts/select_reading40.py`: deterministically selects 40 rows from WP0's dev union,
  stratified as four from each of the seven Greek configs and three from each of the four non-Greek
  configs. It removes the held-out final assistant response. `reading40.jsonl` is currently an
  explicit 40-slot placeholder and real generation refuses it.
- `evals/dev/reading_page.py`: produces one self-contained HTML page for exactly 40 matching prompt
  IDs across two or more runs. Answer order is independently shuffled and visible cards omit run
  identity. Best/worst choices and all six flags persist to `localStorage`; Save also downloads
  resolved `{prompt_id, run, best, worst, flags}` rows. Both single answers and multi-turn
  `transcript`/`assistant_turns` records render. CSS/JS are inline, with only Google Fonts external,
  and light/dark themes are included.
- `evals/dev/test_dev_harness.py`: constructs two 40-item synthetic runs and a synthetic local voice
  reference in a temporary directory. It checks the gate JSON, voice JSON, prompt selection and
  target removal, reading-page generation, three-assistant-turn rendering, JavaScript syntax via
  Node when available, and the required dry-run path. It prints only `OK` on success.
- `evals/dev/README.md`: schemas, thresholds, commands, placeholder handoff, and operational notes.

No packages were installed, and no additional package is needed for the tested paths.

## Commands run locally and outputs

The required Python was used throughout:

```sh
PY=/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
```

Final harness acceptance:

```sh
$PY evals/dev/test_dev_harness.py
```

Output:

```text
OK
```

Final required generator dry run:

```sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python evals/dev/dev_generate.py --dry-run --model x --prompts evals/dev/prompts/reading40.jsonl
```

Output:

```text
{
  "model": "x",
  "prompts": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/evals/dev/prompts/reading40.jsonl",
  "out": null,
  "prompt_records": 40,
  "placeholder_records": 40,
  "prompt_messages": 0,
  "prompt_characters": 0,
  "prompt_token_counts": "computed after tokenizer validation; unavailable in no-model dry-run",
  "planned_steps": 40,
  "batch_size": 4,
  "do_sample": false,
  "max_new_tokens": 512,
  "stop_token": "<|assistant_end|>",
  "stop_token_id": 68,
  "offline": true,
  "single_process": true
}
DRY RUN OK (model not loaded; no output written)
```

Syntax compilation was run during implementation:

```sh
$PY -m py_compile evals/dev/dev_generate.py evals/dev/format_gate.py evals/dev/voice_score.py evals/dev/reading_page.py evals/dev/prompts/select_reading40.py
```

Output: none; exit status 0. Generated `__pycache__` directories were removed afterward.

The cached base snapshot's tokenizer and imposed template were validated without loading model
weights:

```sh
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python - <<'PY'
import importlib.util
from pathlib import Path
p=Path('evals/dev/dev_generate.py')
s=importlib.util.spec_from_file_location('dev_generate',p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
model='/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--fffoivos--apertus-8b-greek-cpt/snapshots/c7f806e268083c64ce831bc46483bf98e5ddcee1'
tok, origin=m.load_and_validate_tokenizer(model)
rendered=tok.apply_chat_template([{'role':'system','content':'S'},{'role':'user','content':'U'}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
print('TOKENIZER_OK', origin, tok.convert_tokens_to_ids('<|assistant_end|>'), len(tok))
print('TEMPLATE_OK', rendered.startswith('<s><|system_start|>S<|system_end|>'), rendered.endswith('<|assistant_start|>'), len(tok.encode(rendered,add_special_tokens=False)))
PY
```

Output:

```text
[transformers] `rope_parameters`'s original_max_position_embeddings field must be less than max_position_embeddings, got 8192 and max_position_embeddings=4096
TOKENIZER_OK swiss-ai/Apertus-8B-Instruct-2509 68 148992
TEMPLATE_OK True True 21
```

Whitespace validation:

```sh
git diff --check -- evals/dev briefs/WP1c.REPORT.md
```

Output: none; exit status 0.

During implementation, the first harness run failed in `format_gate.py` with
`KeyError: 'language_ok'`. I added the missing per-record field and reran the same command to the
final `OK` above. I also tried tokenizer validation with the unrevisioned offline model ID
`fffoivos/apertus-8b-greek-cpt`; Transformers reported that the requested files could not be resolved
from that offline identifier. Passing the explicit cached snapshot directory, as required by the
`--model <dir>` interface, produced the successful tokenizer/template output above.

## What I could not test

- WP0 has not produced `data/arms/dev_all.jsonl`, so the selector was tested against a synthetic
  eleven-config dev union; the checked-in 40 records remain placeholders rather than real prompts.
- I did not load the 8B weights or run a real generation on CPU/MPS. Claude still needs to run the
  real checkpoint probe and cluster generation under the cluster protocol.
- The default private-HF reference-loading branch in `voice_score.py` was not called. The same scoring
  path was run with a synthetic local `--reference`; live HF auth/cache availability remains for
  Claude to verify.
- No real WP1f transcript exists yet. Three-turn rendering was tested with the documented synthetic
  `transcript` shape.
- I did not perform an interactive browser rating/download. The generated JavaScript was parsed with
  `node --check`, and the harness asserted the storage, download, mapping, flags, and transcript
  content.

## Open questions

1. Once WP0 lands, should the fixed config-stratified sample also be balanced by `category` within
   each config? The present deterministic rule satisfies the requested eleven-config stratification
   and records category, but it does not impose a second quota.
2. WP1f should confirm its final transcript field shape. The page accepts either `transcript` as a
   message list/object or `assistant_turns` as a list, so no change is expected unless WP1f chooses a
   different schema.
3. The cached base config emitted the shown Transformers rope-parameter warning during tokenizer
   construction. It did not prevent tokenizer/template validation, but model loading was not run here
   to determine whether the same warning has runtime consequences.
