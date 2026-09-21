# Review brief R-DPO11 (Astra) — launch gate, third pass (narrow)

Your R-DPO10 cleared the RoPE repair and held both jobs on: (1) BLOCKER official/native builders still took
identity as arguments; (2) HIGH the generation-config axis is inert and receipts recorded inactive fields;
(3) HIGH the page still reinstated withdrawn conclusions; plus MEDIUMs. Claimed dispositions: the `R-DPO10`
block at the end of `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. Trust none of it.
Read-only; `ssh clariden` works; launch nothing. Working dir: `subprojects/12_greek_sft_experiments/`.

This pass exists to decide two launches. Please keep BLOCKER/HIGH for things that would make a launched job
produce a wrong or unattributable number, waste the spend, or leave a false statement in the published
record. Hardening that does not affect these two jobs' outputs is MEDIUM and must not block.

## Verify

1. **Finding 1.** `rlhf/evals/manifest.py`: `from_official_greekmmlu(path, *, keep_ids, population)` takes no
   identity; it requires `<path>.receipt.json`, written on the cluster by
   `cluster/eval_jobs/official_receipt.py` (hashes the result file and the weight shards the scored
   directory resolves to). Receipts now exist for the four completed official results
   (`results/greekmmlu_official/*.receipt.json`). `from_native_mcq` is no longer public; legacy results are
   `caller-asserted` and `compare()` refuses them. Repeat your same-file/two-models defeat and try others.
   40 tests: `python3 rlhf/tests/test_evals.py; python3 rlhf/tests/test_store.py`.
   `cluster/greekmmlu_official.sh` now generates and fetches that receipt for every new result — check that
   path, since it is what the official job will execute.
2. **Finding 2.** `cluster/eval_jobs/run_receipt.py` `effective_generation()` records what generation uses
   after lm_eval's overrides; verified on the cluster identical for parent, `R4_full_ep1_ckptcfg` and arms.
   The list is now **19 models, all `full`**: `parent`, `parent_ckptgen` (verbatim: expected identical to
   `parent` — the empirical check that the axis is inert), `parent_exportcfg` (export: the artefact, on the
   parent's weights), and 16 repaired arms. `DRYRUN=1 … EXPECT=19` passed 19/19 on the staged files. Is this
   matrix right and sufficient for the stated purpose: a date-frozen, correctly loaded, weights-only
   parent-vs-arm comparison on IFEval, MGSM and Global-MMLU-Lite, plus a direct measurement of E6?
   Will `rlhf.evals.compare(parent, arm)` actually ACCEPT those results (same frozen prompts, same effective
   generation settings, same geometry, same tokenizer, runtime) — trace it, because a guard that refuses
   the very comparison the job exists to enable would waste the run.
3. **Finding 3 + MEDIUM 4.** The page (`results/G4F6P1--DPO01/curves_page.py` →
   `docs/DPO01_CURVES_20260918.html`) and the ledger's E6 / "E2 withdrawn" sections. Anything still false,
   overstated, or over-withdrawn.
4. **MEDIUMs 5–7**: resume bound to the list entry; store key; dirty-node record and sacct; staged tree
   (`cluster/eval_jobs/` synced wholesale — the retired launchers on the cluster should now exit 64).

## Decide, per job

- **frozen re-score**: `LIST=$R/cluster/eval_jobs/dpo01_frozen_models.txt EXPECT=19 sbatch cluster/eval_jobs/dpo01_frozen_rescore.sh` (19 models ≈ 5 waves ≈ 3.5 node-hours)
- **official GreekMMLU rest**: `bash cluster/dpo01_official_gmmlu_rest.sh` (12 models, 3 workbenches ≈ 2.5 node-hours)

## Deliverable

Markdown. Header → verdict → fix-verification table → new findings most-severe-first with `path:line` →
decision per job (with any precise condition) → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | LAUNCH frozen: <yes/no> | LAUNCH official: <yes/no>`
