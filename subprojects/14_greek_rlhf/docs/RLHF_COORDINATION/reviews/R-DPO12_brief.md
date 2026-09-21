# Review brief R-DPO12 (Astra) — launch gate, fourth pass (final)

R-DPO11 returned **0 BLOCKERS, 2 HIGH**, both now fixed. This pass decides the two launches. Read-only;
`ssh clariden` works; launch nothing. Working dir: `subprojects/12_greek_sft_experiments/`.
Claimed dispositions: the `R-DPO11` block at the end of `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`.

**Scope.** Please reserve BLOCKER/HIGH for things that would make a launched job produce a wrong or
unattributable number, waste the spend, or leave a false statement in the published record. Anything that
would only harden code these two jobs do not exercise is MEDIUM and must not block. If the remaining items
are MEDIUM, say so and clear the launches — the owner has authorised them on a clear review.

## Verify

1. **Finding 1 (task identity).** `rlhf/evals/manifest.py` `_stable()` strips ` at 0x…` from callable reprs,
   keeping function name, module and partial arguments. Repeat your experiment: two separately serialised
   runs of the same 38 lanes must all compare, and a genuinely different task must still be refused. The
   regression is `AllLanesCompareAcrossProcesses` in `rlhf/tests/test_evals.py` (42 tests total across the
   two files). Is stripping only the address the right normalisation — anything else volatile left in, or
   anything behavioural now lost? Note one fixture change you should check: `mint_receipt` now records the
   *effective* generation settings verified on the cluster, and the historic-run test expectation changed
   from "generation config differs" to "geometry differs", because that is the true reason.
2. **Finding 2 (record).** The page (`results/G4F6P1--DPO01/curves_page.py` →
   `docs/DPO01_CURVES_20260918.html`, published v19) and the ledger's E6 / E2 sections. Anything still
   false, overstated or over-withdrawn.
3. **The two MEDIUMs you logged**: resume binding (full config spec + geometry; official resume now also
   requires the evaluator receipt to load) and `sacct` terminal-state parsing (`CANCELLED by 123` + RUNNING
   now refused; five cases simulated against the real `release()`).
4. **The launch path itself.** `DRYRUN=1 … EXPECT=19` passes 19/19 on the staged files; staged and local
   hashes match for the execution files. Trace once more that a *successful* frozen run yields results the
   guard accepts for the comparisons the job exists to make (parent vs each arm, all 38 lanes), and that
   `parent_exportcfg` vs `parent_ckptgen` is accepted under `policy="geometry"`.

## Decide, per job

- **frozen re-score**: `LIST=$R/cluster/eval_jobs/dpo01_frozen_models.txt EXPECT=19 sbatch cluster/eval_jobs/dpo01_frozen_rescore.sh` (19 models, ≈3.5 node-hours)
- **official GreekMMLU rest**: `bash cluster/dpo01_official_gmmlu_rest.sh` (12 models, ≈2.5 node-hours)

## Deliverable

Markdown. Header → verdict → fix-verification table → any new findings with `path:line` and severity →
decision per job → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | LAUNCH frozen: <yes/no> | LAUNCH official: <yes/no>`
