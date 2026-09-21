# Review brief R-DPO9 (Astra) — closing review: is the record honest, and may the re-runs launch?

The owner's instruction: clear every issue the reviews raised, then one Astra review at the end;
**the re-runs are authorised to launch if this review is clear.** So this review is both the final
check on the published record and the launch gate. Read-only; `ssh clariden` works; launch nothing.
Working dir: `subprojects/12_greek_sft_experiments/`.

## What has happened since your R-DPO7c

- Your date-confound finding was traced to its root (`strftime_now` in the chat template) and mapped
  across every run: `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md` — which published claims
  each of five errors reaches, what is clean, what must be re-run, and the status of every finding
  from eight reviews (R-DPO6, 7a, 7a2, 7b, 7b2, 7c, 8, 8b).
- **GreekMMLU was re-scored under the official label protocol** (the owner objected that a custom
  runner's number "is not worth much"). Result: all three arms slightly BELOW the parent,
  −0.41 / −0.43 / −0.26 pp, each significant after Holm; independently recomputed in R-DPO8. The
  custom-protocol full run in fact completed 8/8 models.
- Your other R-DPO7c findings (IPO is not untrained; equal standards for MGSM; α equivalence; stale
  verification banner; "nothing shippable / only instrumentation"; 235 items as a ceiling) were applied
  to the page: `results/G4F6P1--DPO01/curves_page.py` → `docs/DPO01_CURVES_20260918.html`.
- A new evaluation layer, `rlhf/evals/` (design: `docs/RLHF_API_DESIGN_20260919.md`), makes a result
  carry its identity and refuses uncontrolled comparisons. Two Sol cycles attacked it; every defeat is
  now a regression test (`rlhf/tests/`, 31 tests).
- Two Sol cycles (R-DPO8, R-DPO8b) held the launch; their findings are listed as fixed at the end of
  the ledger. **Nobody has reviewed the R-DPO8b fixes.** You are the first.

## Part 1 — the record

1. Read the page's sections 6–14 and the ledger against the data
   (`results/G4F6P1--DPO01/{all_results,greekmmlu_official_paired,greekmmlu_full_partial,alpha_interval,run_dates}.json`).
   For each surviving claim: supported / overstated / understated / wrong. Last time you found
   over-withdrawal; check **both** directions again. In particular:
   - §10 now ends on "preference training moved official GreekMMLU down by about 0.3–0.4 points". Is
     that the right strength for one checkpoint per recipe? Is the custom-vs-official sign disagreement
     handled honestly, including the explicitly untested hypothesis offered for it?
   - §7 (date confound), the date-matched scorecard in §8, the banner on §9, the cross-date caveat in §11.
   - The ledger's CLEAN / POISONED calls, and whether anything is still missing from it.
2. Is any published statement anywhere (page, ledger, the three bannered documents) still false?

## Part 2 — the launch gate

3. Verify the R-DPO8b fixes (ledger, final block): the sealed `Result` API — try to get an uncontrolled
   comparison accepted through the public surface; self-consistent weight receipts; the corrected
   24-model list against what the ledger says R1/R2 must cure, including the stated reason
   `parent_ckptcfg` is kept; R3 staging for single-shard checkpoints;
   `cluster/eval_jobs/validate_official_result.py`; verified workbench shutdown in
   `cluster/greekmmlu_official.sh`; manifest-based `.validated` in
   `cluster/eval_jobs/dpo01_frozen_rescore.sh` (plus its canary and tokenizer freeze, which Sol cleared).
4. The exact files staged on the cluster are under `/iopsstor/scratch/cscs/fffoivos/sft_round1/`
   (`cluster/eval_jobs/dpo01_frozen_rescore.sh`, `dpo01_frozen_models.txt`, `weights_receipt.py`, `rlhf/`).
   Confirm they match the repository copies.
5. **Is the plan worth its cost?** About 24 models ≈ 4 h of one node, plus 12 official-GreekMMLU models
   ≈ 2.5 h. Given that training-time dates cannot be repaired, will these re-runs actually let a claim
   be made that cannot be made now? Name any run that buys nothing, and any missing run that matters.
   If the honest answer is "the round's conclusions would not change", say so.

## Disposition

BLOCKER/HIGH block the launch and are fixed first. MEDIUM/LOW are logged and do not block. State the
launch decision explicitly for each of the two jobs (frozen re-score; official GreekMMLU rest).

## Deliverable

Markdown. Header (what you ran) → one-line verdict → Part 1 claim table + findings → Part 2 findings →
explicit launch decision per job → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | LAUNCH frozen: <yes/no> | LAUNCH official: <yes/no>`
