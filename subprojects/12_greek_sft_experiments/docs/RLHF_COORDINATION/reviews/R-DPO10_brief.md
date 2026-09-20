# Review brief R-DPO10 (Astra) — launch gate, second pass

Your R-DPO9 (`R-DPO9_review_1.md`) held both jobs: B1 (checkpoint RoPE mis-resolved under transformers
4.57), B2 (guard bypassable through builder arguments / mutable policies / receipt substitution),
H1 (contradictory active claims), H2 (official validator), H3 (shutdown read a failed query as success).
The owner has authorised launch once a review is clear. Read-only; `ssh clariden` works; launch nothing.
Working dir: `subprojects/12_greek_sft_experiments/`. The author's claimed dispositions are the `R-DPO9`
block at the end of `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. Trust none of them.

## What to verify

1. **B1.** We confirmed your finding firsthand and against the owner's reference contract
   (`github.com/eellak/greek-apertus`, `scripts/validate_full_8b_contract.py:111`: base 500000, scaling
   factor 8.0, 4096). The ledger has a new **E6** section and the page opens §6 with it. Check both are
   accurate and complete — in particular the table of which lanes are affected, and that nothing still
   presents a parent-vs-arm lm_eval contrast as a training effect.
2. **The rebuilt job** `cluster/eval_jobs/dpo01_frozen_rescore.sh`, list `dpo01_frozen_models.txt` (35
   models, `EXPECT=35`), helpers `run_receipt.py`, `weights_receipt.py`. Every model is scored from a
   job-unique stage whose `config.json` has the legacy `rope_theta`/`rope_scaling` restored; a CPU
   geometry gate requires the rotary table built IN THE SCORING ENVIRONMENT to equal the parent's
   (`export:` mode requires it to differ; `verbatim:` to equal). Is the repair faithful — does restoring
   those two keys reproduce exactly the geometry the model was trained with under 5.16.1 (check
   `original_max_position_embeddings`, `rope_type`, factors; consider whether `rope_parameters` left in
   the config can still influence 4.57)? Is `inv_freq` a sufficient witness, or can attention scaling /
   another derived quantity still differ? A full `DRYRUN=1` of this job already ran on the cluster:
   35/35 passed the gate. Re-run it if you wish (it needs no GPU).
   Is the design right: `parent_exportcfg` (parent weights, an arm's config verbatim, unrepaired) as the
   direct measurement of the artefact; `parent_ckptgen`; 16 arms `own|full`; the same 16 `parent|gen`?
3. **B2.** `rlhf/evals/`: builders take no identity arguments; `run_receipt.json` is written in-job after
   scoring and binds weights id, generation config, effective geometry, tokenizer hash and a hash of
   every output; `geometry` is an identity key; `POLICIES` is a read-only mapping. 38 tests
   (`rlhf/tests/`). Repeat your three defeats and try new ones through the public surface. Note the tests
   mint receipts for historic runs from cluster-verified facts (`mint_receipt`) — say whether that is an
   acceptable test device or a hole.
4. **H2 / H3.** `cluster/eval_jobs/validate_official_result.py` (+ pinned `greekmmlu_gold.tsv`) — repeat
   your four mutations. `cluster/greekmmlu_official.sh` `release()` — repeat the ssh-failure case, and
   check the dirty-node path and the `sacct` fallback for a job id that has aged out of `squeue`.
5. **H1 and the record.** `results/G4F6P1--DPO01/curves_page.py` → `docs/DPO01_CURVES_20260918.html`.
   Anything still false, overstated or over-withdrawn — including the new E6 wording ("probably largely
   this artefact" style claims: is any of it stronger than the evidence, given the artefact's size is
   unmeasured?).
6. **Staged files** under `/iopsstor/scratch/cscs/fffoivos/sft_round1/` (`cluster/eval_jobs/` and
   `rlhf/`) match the repository.

## The decision

State a launch decision for each job separately:
- **frozen re-score** (35 models, ≈5 node-hours): `LIST=$R/cluster/eval_jobs/dpo01_frozen_models.txt EXPECT=35 sbatch cluster/eval_jobs/dpo01_frozen_rescore.sh`
- **official GreekMMLU rest** (12 models, ≈2.5 node-hours): `bash cluster/dpo01_official_gmmlu_rest.sh`

BLOCKER/HIGH block a launch. MEDIUM/LOW are logged and do not. If a job may launch with a named
condition, say so precisely.

## Deliverable

Markdown. Header (what you ran) → verdict → fix-verification table → new findings most-severe-first
with `path:line` → explicit decision per job → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | LAUNCH frozen: <yes/no> | LAUNCH official: <yes/no>`
