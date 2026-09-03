# Brief WP1b — the Greek evaluation launcher (ellinika-bench, GreekMMLU, native suite)

**Goal.** One launcher, run by Claude on a node, that evaluates an HF checkpoint directory on the
Greek evals and writes `results/<run>/greek.json` in one schema — reusing the existing tools
unchanged.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5; `EXECUTION_PLAN_20260904.md` (WP1b row);
`SFT_PLAN_20260903.md` §6 and §11; `~/Projects/apertus-local-chat/benchmark/clariden_eval.py` (+ `bench.py`,
`config.json`, `docs/`); the CPT card scorer: locate the FP32 zero-shot candidate-likelihood scorer for
GreekMMLU + the native-Greek suite under `../09_full_8b_cpt_results_analysis/` (start from
`09_2_checkpoint_trajectory_release/`, `evaluation/`, `09_1_*/evaluation/`; the card's numbers came from
it — find the script that produces `greekmmlu.accuracy` and the eight `native_greek.*` accuracies) and
`evals/knownness` is NOT yours.

**Deliverable paths (only these):** `evals/greek/run.sh`, `evals/greek/run_greek_evals.py`,
`evals/greek/schema.md`, `evals/greek/README.md`, `briefs/WP1b.REPORT.md`.

**Spec.**
1. `run.sh <model_dir_or_hf_id> <run_name> [--revision R] [--mode chat|base] [--limit N] [--dry-run]`
   → runs, in order: (a) ellinika-bench via `clariden_eval.py` for `--lang el,en,fr,de`, chat template
   `auto` in chat mode / raw in base mode; (b) GreekMMLU + native suite with the located scorer,
   **unchanged** (wrap, don't edit; record its path and git hash in the output); writes
   `results/<run_name>/greek.json` with: per-pillar ellinika accuracies (gen and ll) per language,
   `greekmmlu.accuracy`, the eight native accuracies + macro, model id/revision, timestamps, and the
   exact commands run. `--dry-run` prints the commands and exits 0.
2. The base's numbers are NOT re-run (owner): `run_greek_evals.py --pull-card <revision>` fetches
   `checkpoint-index.json` from `fffoivos/apertus-8b-greek-cpt` and writes the same schema for the
   base from the card (mark `source: card`).
3. Keep everything single-process (the launcher may call the two tools sequentially); no scheduler
   calls; heartbeat lines between stages; fail fast if the scorer or the benchmark data is missing.

**Acceptance (Claude runs):** `bash evals/greek/run.sh x y --dry-run` exits 0 printing the two commands;
`python evals/greek/run_greek_evals.py --pull-card 18-avg-uniform5-tokens30B-50B --out results/E0b/greek.json`
writes GreekMMLU 0.5678 and native macro ≈ 0.499; the report names the scorer script and its hash.
