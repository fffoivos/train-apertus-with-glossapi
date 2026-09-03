# Brief WP1c — dev generation, format gate, voice score, blind reading page

**Goal.** The tools that turn a checkpoint into (a) generations on the held-out dev prompts,
(b) a format gate, (c) a voice score against no_robots-el, and (d) the blind reading page the owner
rates — with ratings saved in place.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5 (for the generation script);
`EXECUTION_PLAN_20260904.md` §0a and the WP1c row; `SFT_PLAN_20260903.md` §11;
`~/Projects/natural-greek-sft/scripts/style_compare.py` and `scripts/build_style_site.py` (the
stylometry: Burrows's Delta + Biber-style rates; reuse by import or subprocess, do not copy);
`~/Projects/natural-greek-sft/docs/PERSONALITY.md` §6 (what the voice is).

**Deliverable paths (only these):** `evals/dev/dev_generate.py`, `evals/dev/format_gate.py`,
`evals/dev/voice_score.py`, `evals/dev/reading_page.py`, `evals/dev/prompts/` (the fixed 40 reading
prompts: choose them from `data/arms/dev_all.jsonl` when it exists — WP0 — stratified over the eleven
configs; until then, write the selector and a placeholder list), `evals/dev/test_dev_harness.py`,
`evals/dev/README.md`, `briefs/WP1c.REPORT.md`.

**Spec.**
1. `dev_generate.py --model <dir> --prompts <jsonl> --out results/<run>/dev_gen.jsonl [--limit] [--dry-run]`:
   greedy, 512 new tokens, chat template from the model dir (or imposed as in _COMMON for a base),
   stop on `<|assistant_end|>`; batched with transformers (vLLM optional if present); heartbeat;
   single process. Records raw text, stop reason, token counts.
2. `format_gate.py results/<run>/dev_gen.jsonl`: share of generations that (a) ended on the stop token
   (not max-length), (b) are in the prompt's language (Greek script share ≥ 0.9 for el; < 0.02 Greek
   script for en/fr/de), (c) keep a single assistant turn (no role-token leakage). Writes
   `results/<run>/format_gate.json`; threshold 0.95 on (a) and (c), 0.98 on (b); prints PASS/FAIL.
3. `voice_score.py results/<run>/dev_gen.jsonl`: Burrows's Delta and the Biber-style rates of the
   Greek generations vs no_robots-el's assistant turns (reference = the HF config `no_robots`,
   assistant turns), plus the reference's own split-half distance as the "parroting floor";
   `results/<run>/voice.json`.
4. `reading_page.py --runs A B C ... --out results/reading/<date>.html`: 40 fixed prompts × the runs'
   answers, unlabeled, order shuffled per prompt with a hidden mapping stored in the page; per prompt
   the owner marks best/worst and per answer toggles flags {not Greek, American underneath,
   assistant mannerism, wrong fact, too long, too short}; a "save" that keeps ratings in
   `localStorage` AND offers a JSON download of `{prompt_id, run, best, worst, flags}` with the
   mapping resolved. Multi-turn interview transcripts (WP1f) must be renderable on the same page
   (3 assistant turns per item). Self-contained HTML, both light and dark themes, no external assets
   beyond Google Fonts.
5. `test_dev_harness.py`: builds a fake `dev_gen.jsonl` (no model) and checks the gate, the voice
   score, and that the page renders with two fake runs; prints `OK`.

**Acceptance (Claude runs):** `python evals/dev/test_dev_harness.py` prints `OK`;
`python evals/dev/dev_generate.py --dry-run --model x --prompts evals/dev/prompts/reading40.jsonl` exits 0.
