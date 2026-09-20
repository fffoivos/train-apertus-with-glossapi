# Review brief R-DPO8 (Sol) — the poison ledger, the new evaluation guard, and the unre-reviewed fixes

Six reviews on 19 September found five distinct errors in the DPO01 evaluation. In response we wrote
(1) a **poison ledger** stating which published numbers each error reaches and what must be re-run,
(2) a new package, **`rlhf/evals`**, meant to make that class of error impossible, and (3) fixes to
scripts after R-DPO7b2 that **no reviewer has yet seen**. Review all three. Be adversarial: the
author has been wrong in both directions today, and this ledger will decide what gets re-run.

Read-only, but run whatever you need. `ssh clariden` works (results under
`/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/`). Launch nothing on the cluster.
Working dir: `subprojects/12_greek_sft_experiments/`.

## Part A — `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`

1. **Is the taint map right?** Verify the 18/19-September split yourself from the samples on the
   cluster (`full/*/…/samples_*.jsonl`, the `Current date:` line) — including that **Global-MMLU-Lite
   likelihood prompts carry the date**. Verify the root cause in the parent's `tokenizer_config.json`
   (`strftime_now`). Check the claims about the served lane (prompts not saved; serve dates) and about
   training prompts (`cluster/dpo_train.py` uses `apply_chat_template`; trainer_state mtimes).
2. **Is anything marked CLEAN that is not?** Especially: (a) "α contrast is clean as a seed-paired
   contrast" — are seeds really paired one-to-one by date across the two arms? (b) the official
   GreekMMLU result (`results/greekmmlu_official/*.json`, analysis in
   `results/G4F6P1--DPO01/greekmmlu_official_paired.json`) — confirm no chat template, no date, one
   dataset hash, and that the staged arm directories really held the ARM weights (symlinks into
   `runs/…/checkpoint-129`), not the parent's. Recompute the three deltas and McNemar p-values.
   (c) the §3–4 displacement result — can the training-prompt date touch it?
3. **Is anything marked POISONED that is actually fine**, or anything missing entirely? Look for
   published numbers the ledger does not mention (`results/G4F6P1--DPO01/curves_page.py`,
   `docs/DPO01_CURVES_20260918.html`, `docs/RLHF_COORDINATION/OVERNIGHT_20260918.md`,
   `R-DPO6_response.md`, `R-DPO7a_response.md`). Stale numbers in those documents count.
4. **Is the re-run list necessary and sufficient?** Would R1 (frozen-date re-score of 17 models)
   actually cure every E1 entry? Is replacing `strftime_now(...)` with a literal in a staged
   tokenizer config a sound way to freeze the date for lm_eval, and what is the equivalent for vLLM?
   Is any re-run missing, or any proposed re-run unnecessary?

## Part B — `rlhf/evals/` (manifest.py, compare.py, stats.py, tests/test_evals.py)

Design intent: `docs/RLHF_API_DESIGN_20260919.md`. A result carries a manifest; `compare()` refuses
unless manifests agree on everything except the declared variable; unknown ≠ equal.

5. Run the tests. Then **try to defeat the guard**: construct two runs that differ in a way that
   matters but that `compare()` accepts. Candidates: same prompts but different `max_gen_toks` or
   stop sequences; different few-shot; different chat-template application with coincidentally equal
   text; `doc_hash` collisions or reordered docs; a `gen_config` of `None` on both sides; a caller
   passing `varying=IDENTITY_KEYS`. Which of these get through, and which matter?
6. `prompt_digest` hashes `doc_id + prompt strings`. Is `_prompt_strings()` complete for both
   generate_until and loglikelihood rows in real lm_eval sample files (check one of each on disk)?
   For loglikelihood rows, are the continuations included, and should they be?
7. `weights_id` is a caller-supplied label. Is that a hole — can two different checkpoints share one,
   or one checkpoint carry two? What should it be derived from?
8. `stats.py`: exact McNemar now uses `Fraction` (it overflowed at n≈1,100). Verify against an
   independent implementation at small and large n. Check `holm`, `seed_bootstrap`, `paired`.

## Part C — fixes made after R-DPO7b2 that nobody has reviewed

9. `cluster/eval_jobs/finalize_greekmmlu_full.py` — identity binding (`check_metadata`), exact raw
   frame (first model defines the frame — is that sound, or should the frame be pinned?), strict
   booleans, mandatory manifest fields, held-out set. Run it against the real data if useful.
10. `cluster/eval_jobs/dpo01_greekmmlu_full.sh`, `dpo01_greekmmlu.sh`, `dpo01_gencfg_control.sh`,
    `dpo01_armcfg_cell.sh` — unique stages, tokenizer checks (now fail-closed? the
    `tokenizer_config` comparison with `tokenizer_class` normalised away), exit-status handling.
    `bash -n` is not enough: trace the control flow for a failing model.
11. `cluster/greekmmlu_official.sh` — `MAXWAIT` change, and whether the driver can close a workbench
    while models are still scoring.

## Disposition

BLOCKER/HIGH are fixed before anything is re-run or republished. MEDIUM/LOW are logged. A finding
that the LEDGER is wrong (in either direction) is at least HIGH, because it decides spend.

## Deliverable

Markdown. Header (what you ran) → one-line verdict → Part A: a table of ledger rows you checked, each
confirmed / wrong / incomplete, with the deciding evidence → Part B: each defeat attempt and its
outcome → Part C findings → all findings most-severe-first with `path:line` → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
