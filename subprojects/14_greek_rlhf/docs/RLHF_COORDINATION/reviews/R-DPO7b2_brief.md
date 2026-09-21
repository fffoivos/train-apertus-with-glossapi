# Review brief R-DPO7b cycle 2 (Sol) — verify the protocol fixes, then audit what cycle 1 missed

Your cycle-1 review is `R-DPO7b_review_1.md` (1 BLOCKER, 3 HIGH, 2 MEDIUM). A parallel review of the
analysis code, `R-DPO7a2_review_1.md`, then raised a BLOCKER against the finalizer written to answer
your BLOCKER. Read both. Two jobs, in order:

**(1) Verify each fix is correct**, not merely present. **(2) Audit for anything neither cycle reached.**

Read-only. **You now have working cluster access** — `ssh clariden` is live again, so you can and
should inspect the real artifacts, manifests and checkpoints rather than reasoning from source alone.
The full GreekMMLU job **3443296 is still running** (log:
`/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_gmmlu_full_3443296.out`).

## What changed

| finding | change |
|---|---|
| **7b BLOCKER** raw 16,632 vs clean 16,159 | `cluster/eval_jobs/finalize_greekmmlu_full.py` recomputes BOTH from one code path. Job unchanged and still running; its numbers are quarantined until this runs. |
| **7a2 BLOCKER** manifest is a descriptor | Finalizer rewritten to the frozen contract: asserts `schema_version`, `status=frozen`, reads the referenced id file, verifies its sha256 and byte count, checks uniqueness and `clean_count`. |
| **7a2 HIGH** guard validates counts not identity; fails open | Now fail-closed: `--expect` requires an exact label set, exactly one prediction file per model, non-boolean `correct` aborts, any invalid model aborts everything, atomic `os.replace` only after all models pass. |
| **7b HIGH** shared stage → checkpoint truncation | Stages are `${SLURM_JOB_ID:-$$}`-unique; explicit symlink refusal before writing. **Verified on the cluster: no checkpoint config was truncated** (all 899B/26 keys). |
| **7b HIGH** tokenizer swap unchecked | `cmp` against the parent, job fails on mismatch. **Verified: arm01/arm05 tokenizer.json byte-identical to parent.** |
| **7b HIGH** failures exited 0 | `EXPECT=8` preflight, `run_one` returns non-zero, statuses collected, `GREEKMMLU_INCOMPLETE` + exit 1. |
| **7b MEDIUM** asymmetric overlay | Both directions assign-and-delete. **Verified: all four fields present in both configs, so the bug never bit and `parent_ckptcfg` is correct.** |
| **7a2 MEDIUM** arm01-built baseline used for arm05 | **Verified on the cluster: six arms share one identical config bundle** (eos 68, pad 3, bos 1, use_cache false). |

## Verify specifically

1. **Re-check my verification claims above against the cluster yourself.** They are the basis for
   keeping published numbers; if any is wrong, that is a BLOCKER. In particular re-derive that no
   checkpoint config is damaged and that the arms' config bundles really are identical.
2. **The finalizer against the REAL manifest**
   (`/capstor/scratch/cscs/fffoivos/cpt_runs/dataset-scheduling-0p5b/20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json`)
   and the REAL completed prediction files in
   `/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/greekmmlu_full/`. Run it. Does
   it produce correct raw and clean numbers? Is `clean_acc` genuinely restricted to the 16,159 ids?
   Does the id-file fallback (basename next to the manifest) introduce a way to validate against the
   wrong file?
3. **Is raw-16,632 genuinely the population the 250-item slice was drawn from?** Your cycle-1 review
   asserted this and the artifact now rests on it. Confirm from the runner's sampling code and the
   250 job's `--random-state 42`, and confirm the 250 ids are a subset of the 16,632.
4. **The running job.** Will it now terminate correctly? Check the wave loop, `FAILED` accounting and
   the exit path as they exist in the RUNNING copy (Slurm snapshotted the script at submit, so the
   live job may predate these fixes — say clearly which version is running and whether that matters).

## Audit fresh

Anything in the measurement path neither cycle reached: the registry and dataset bindings, the
`run_metadata.json` contract, prompt construction, fp32 candidate scoring, or how `greekmmlu_full`
results will be joined to the existing 250-item numbers.

## Disposition

BLOCKER/HIGH fixed before publication. MEDIUM/LOW logged.

## Deliverable

Markdown. Header → one-line verdict → **fix-verification table (correctly fixed / wrongly fixed /
not fixed)** → new findings most-severe-first with `path:line` and raw numbers → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
