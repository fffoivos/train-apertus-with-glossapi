# Review brief R-DPO7b (Sol) — do the MEASUREMENT SCRIPTS measure what we say they measure?

**Scope: the cluster job scripts, i.e. the protocol.** Not the analysis (covered by R-DPO7a), not the
conclusions (covered by R-DPO7c). Your question: **when we claim two numbers are comparable, does the
code make them comparable?** A protocol difference between a model and its baseline becomes a fake
training effect, and we have already been burned by exactly that once.

You are read-only. Cluster files are NOT reachable; review the scripts as source. Compare scripts
against each other — that is where the answer is.

Working dir: `subprojects/12_greek_sft_experiments/`

## Files under review

| file | claim |
|---|---|
| `cluster/eval_jobs/dpo01_greekmmlu_full.sh` | **RUNNING NOW.** Full 16,159-item GreekMMLU on 8 models, protocol byte-identical to the 250 job except `--sample-size`/`--random-state` removed |
| `cluster/eval_jobs/dpo01_greekmmlu.sh` | the 250-item job it must match |
| `cluster/eval_jobs/dpo01_armcfg_cell.sh` | **RUNNING NOW.** An arm's WEIGHTS under the PARENT's generation config — the missing cell of a 2×2 |
| `cluster/eval_jobs/dpo01_gencfg_control.sh` | the mirror cell: parent's weights under a checkpoint's config |
| `cluster/eval_jobs/dpo01_full.sh` | the main lm_eval lane |

## The specific things to check, hardest first

1. **Is the full job actually comparable to the 250 job?** Diff them. Every flag that affects scoring
   must be identical: `--dtype float32`, `--max-input-tokens 3072`, `--candidate-batch-size 16`,
   `--example-batch-size 16`, `--trust-remote-code`, the registry, the prompt form. Confirm
   `--sample-size`/`--random-state` are genuinely gone and nothing else moved. **If anything else
   differs, the 8 full-run numbers cannot be compared to the 66 slice numbers and that is a BLOCKER**
   — the run is live, so say so immediately and plainly.
2. **Does the missing-cell script actually isolate the generation config?** Read the staging block in
   `dpo01_armcfg_cell.sh` closely. It symlinks the arm's files, then overwrites `generation_config.json`,
   the tokenizer files, and rewrites `config.json` copying `eos_token_id`, `pad_token_id`,
   `bos_token_id`, `use_cache` from the parent. Questions: does the symlink-then-overwrite order
   ever leave an arm file in place that should have been replaced (note `rm -f` before `cp`, and that
   `ln -sf` of a directory entry behaves differently)? Could it **overwrite the real checkpoint through
   a symlink** — i.e. is there a path where writing to `$STAGE/config.json` writes through to
   `$SRC/config.json` and corrupts a checkpoint? That would be destructive and is the single worst
   outcome here. Does deleting a field absent from the parent (`elif f in c: del c[f]`) do the right
   thing? Is the resulting model still the ARM's weights?
3. **Tokenizer staging.** Both GreekMMLU scripts stage the parent's tokenizer over a checkpoint
   because transformers 5.16.1 wrote a `tokenizer_class` the container can't load. Is the claim
   "this changes no tokenisation" actually safe as coded? What if `tokenizer.json` is NOT identical?
4. **Success detection.** The GreekMMLU scripts key success on `*_native_mcq_headline.json` existing,
   deliberately ignoring a finalizer that fails on Apertus. Can a **partial or crashed** run leave a
   headline file and be recorded as done? In `dpo01_greekmmlu_full.sh` the skip-if-scored guard uses
   the same test — with the new `greekmmlu_full` output dir, is there any way it reads the 250-item
   results and skips the full run, silently republishing slice numbers as full ones?
5. **Parallel-wave correctness.** The 4-GPU wave loop: is `wait` collecting correctly, does a failure
   in one GPU's model abort or silently continue, and is `CUDA_VISIBLE_DEVICES` assignment right?
6. **Walltime.** 8 models × ~2.8 h on 4 GPUs = 2 waves ≈ 6 h against `--time=12:00:00`. Is that
   sound, and does the script lose completed models if it hits the wall?
7. **Model selection.** The `for spec in ...` list builds 8 models incl. `armBAL_ep3` at
   checkpoint-105 (274 pairs → 35 steps/epoch) vs 129 for the others. Is the checkpoint mapping right,
   and does `IFS='|' read` parse as intended? Does a missing dir fail loudly or silently?

## Disposition

BLOCKER/HIGH are fixed before the artifact is republished; a BLOCKER on item 1 or 2 may mean killing
a live job, so be direct. MEDIUM/LOW logged.

## Deliverable

Markdown. Header → one-line verdict → findings most-severe-first, each `[BLOCKER]/[HIGH]/[MEDIUM]/[LOW]`
with `path:line`, the concrete failure scenario, and the fix → what you verified as correct → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
