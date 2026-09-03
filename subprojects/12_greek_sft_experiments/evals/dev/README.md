# WP1c development-generation harness

This directory turns a checkpoint into deterministic dev generations, applies the three format
guards, measures Greek voice distance, and builds the owner's blind reading page. All model runtime
is single-process. `dev_generate.py` forces offline Hugging Face access and never loads a model in
`--dry-run` mode.

## Fixed prompts

`prompts/reading40.jsonl` currently contains 40 explicit placeholder slots because WP0's
`data/arms/dev_all.jsonl` does not exist yet. A real generation refuses those placeholders. Once WP0
lands, replace the manifest deterministically with:

```sh
python evals/dev/prompts/select_reading40.py
```

The selector allocates four prompts to each of the seven Greek configs and three to each of
`no_robots_en_pov`, `apertus_en`, `euroblocks_fr`, and `euroblocks_de` (40 total). It hashes the seed,
config, and row ID to choose rows, retains the conversation only through the last user turn, and does
not copy the held-out assistant answer.

## Generate and gate

```sh
python evals/dev/dev_generate.py \
  --model /path/to/checkpoint \
  --prompts evals/dev/prompts/reading40.jsonl \
  --out results/RUN/dev_gen.jsonl
python evals/dev/format_gate.py results/RUN/dev_gen.jsonl
```

Generation is greedy, batched, capped at 512 new tokens, and stops on
`<|assistant_end|>` (token 68). The tokenizer is validated before model loading: BOS `<s>` must be ID
1 and the 12 Apertus role/control tokens must occupy IDs 61–72 (13 format tokens total). If the checkpoint has no chat template, the script imports the
cached `swiss-ai/Apertus-8B-Instruct-2509` template. `--limit N` and `--max-steps N` both cap the
number of prompts for a probe. Records include the prompt metadata/messages, display text, raw text,
stop reason, prompt-token count, and generated-token count.

`format_gate.py` writes `format_gate.json` next to its input and exits nonzero on failure. Its gates
are:

- at least 0.95 ended on `<|assistant_end|>` rather than at 512 tokens;
- at least 0.98 obey the requested script (Greek alphabetic-character share at least 0.90 for `el`,
  below 0.02 for `en`, `fr`, and `de`);
- at least 0.95 contain one assistant turn, defined as exactly one final assistant-end token and no
  other leaked role/control token.

## Voice score

```sh
python evals/dev/voice_score.py results/RUN/dev_gen.jsonl
```

The default reference is the private HF dataset's `no_robots` config, assistant turns from
`el_messages`. `--reference path/to/no_robots.jsonl` selects a local export for an air-gapped run.
The implementation imports (does not copy) `~/Projects/natural-greek-sft/scripts/style_compare.py`
and uses its text cleaning, tokenization, Biber-style feature rates, chunking, z-scoring, centroids,
and Burrows's Delta. `voice.json` contains the generated-to-reference Delta and the deterministic
reference split-half Delta as the parroting floor. A distance below that floor is marked, not treated
as an automatic success.

## Blind reading

```sh
python evals/dev/reading_page.py \
  --runs results/A/dev_gen.jsonl results/B/dev_gen.jsonl \
  --out results/reading/2026-09-04.html
```

Run names such as `A B` also resolve to `results/A/dev_gen.jsonl` and
`results/B/dev_gen.jsonl`. All runs must have the same 40 prompt IDs. Answer order is independently
shuffled for each prompt and run names are absent from the visible cards. The page stores every
change in `localStorage`; **Save + JSON** persists again and downloads resolved records shaped as
`{prompt_id, run, best, worst, flags}` for every answer. A record containing `transcript` messages or
`assistant_turns` is rendered as a multi-turn item, including WP1f's three assistant turns. CSS and
JavaScript are embedded; only Google Fonts is external. The theme follows the system and has a manual
light/dark toggle.

## Local self-test

```sh
python evals/dev/test_dev_harness.py
```

The self-test writes only to a temporary directory. It makes 40 synthetic generation records, checks
the gate and voice JSON, and builds a two-run page including a three-assistant-turn transcript.
