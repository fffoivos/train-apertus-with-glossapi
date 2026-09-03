# Brief WP0 — the training and dev files for every arm, plus the contamination report

**Goal.** One script that turns the HF dataset into per-arm `train.jsonl` / `dev.jsonl` in the
Apertus chat format, with a fixed 2% held-out split per config, token statistics, and a
contamination report against the evaluation prompt sets.

**Read first:** `briefs/_COMMON.md`; `EXECUTION_PLAN_20260904.md` §1–2 (WP0 row); `SFT_PLAN_20260903.md`
§5c and §5a′; `references/apertus-finetuning-recipes/sft_train.py` (to see what the trainer consumes:
a dataset with a `messages` column, chat template applied by TRL).

**Deliverable paths (only these):** `data/build_sft_mix.py`, `data/README.md`, `data/splits/` (row-id
lists per config, committed), `data/arms/<arm>/{train,dev}.jsonl` (bulk, gitignored), `data/stats.json`,
`data/contamination_report.md`, `briefs/WP0.REPORT.md`.

**Spec.**
1. `build_sft_mix.py` downloads the eleven configs with `datasets` (`load_dataset(repo, config)` or
   `hf_hub_download` of the jsonl files), deterministic; caches under `data/cache/` (gitignored).
2. Per config: fixed-seed (`1234`) 2% held-out by `row_id`, written to `data/splits/<config>.dev.txt`
   (committed); train/dev disjoint by construction. The eleven dev lists are the same for every arm.
3. Rows become `{"messages": [{"role":..., "content":...}], "row_id":..., "config":..., "category":...}`
   with roles `system|user|assistant` only; drop rows with an empty assistant turn; keep multi-turn.
   For `no_robots_en_pov` the conversation is `messages`; for the others `el_messages`; for E3′ the
   raw `en.messages` of `apertus_en`, `euroblocks_fr`, `euroblocks_de`.
4. Arms: `E1`, `E2`, `E3`, `E3prime` (see _COMMON). Shuffle train with seed 1234. Also write
   `data/arms/dev_all.jsonl` = the union of dev rows tagged by config (used by every arm's dev loss).
5. `data/stats.json`: rows and tokens per config and per arm (tokens = the rendered Apertus template,
   tokenized with the CPT tokenizer; report assistant-token share), plus max length and the count of
   rows over 4096 tokens (must be 0 — the data was filtered at 4096 with this template; if not 0,
   report, don't drop silently).
6. **Contamination report**: exact and near-duplicate overlap between every train row's user turns and
   the prompt sets of: ellinika-bench (`~/Projects/apertus-local-chat/benchmark/data/`), GreekMMLU
   (`dascim/GreekMMLU` test split via `datasets`), the native-Greek suite (`fffoivos/native-greek-suite`
   if accessible, else report as unavailable), GSM8K test (`openai/gsm8k`), IFEval (`google/IFEval`).
   Method: normalized 8-gram containment ≥ 0.5 on the user text; list every hit with row_id and eval id;
   exact hits must be 0 in the final files (drop the row and record it in the report).
7. `--check` mode re-derives the splits and stats and prints `OK` iff: splits disjoint, no over-length
   rows, zero exact contamination hits, per-arm token totals within 2% of §5a′ (E1 ≈ 9.34 M,
   E2 ≈ 12.60 M, E3 ≈ 12.19 M).

**Acceptance (Claude runs):** `python data/build_sft_mix.py --check` prints `OK`; `data/stats.json`
and `data/contamination_report.md` exist; `head -1 data/arms/E1/train.jsonl` parses and has the
schema above.
