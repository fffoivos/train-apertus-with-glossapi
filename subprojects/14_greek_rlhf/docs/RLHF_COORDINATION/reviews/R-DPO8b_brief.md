# Review brief R-DPO8 cycle 2 (Sol) — verify the fixes, then pre-launch review of the re-run jobs

Your cycle-1 review is `R-DPO8_review_1.md` (1 BLOCKER, 10 HIGH, 2 MEDIUM, 2 LOW). The owner has
authorised the re-runs to launch once the reviews are clear, so **this review gates real spend**.
Two jobs, in order. Read-only; `ssh clariden` works; launch nothing.

## 1. Verify each fix is correct, not merely present

The author's claimed status for every finding is the `R-DPO8` block at the end of
`docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. For each: correctly fixed / wrongly fixed /
not fixed. In particular:

- **Guard** (`rlhf/evals/{manifest,compare,weights,stats,store}.py`, tests in `rlhf/tests/`): run the
  tests (24 should pass), then **repeat every defeat from your cycle-1 table** and try new ones. The
  public surface is now `compare(a, items_a, b, items_b, policy=...)` with a closed `POLICIES`, and
  unknowns are declared by the builder from `UNRECORDABLE_BY_PROTOCOL`. Can a caller still get an
  uncontrolled comparison accepted through the public API — e.g. by editing a manifest dict before the
  call, by constructing a `RunManifest` by hand, through `Store.put`/`Store.group`, or via `check`?
  Decide which of those are in scope for a library guard and which are not, and say so.
  `_pathless()` drops `metadata.pretrained` and `metadata.tokenizer` from the task-config digest — is
  that exactly right, too much, or too little?
- **Weights identity**: `rlhf/evals/weights.py`; real receipts are in
  `results/G4F6P1--DPO01/full_local/weights/` and on the cluster under `receipts/weights/`. Check the
  parent and the symlinked `R4_full_ep1_ckptcfg` stage share an id and the arms do not.
- **Finalizer** (`cluster/eval_jobs/finalize_greekmmlu_full.py`): pinned raw frame, pinned 250-slice
  file, pinned dataset identity, structural metadata binding, mandatory `--expect`. Note a factual
  correction: the custom-protocol job had **completed all 8 models**, not 4; output is
  `results/G4F6P1--DPO01/greekmmlu_full_partial.json`. Recompute a few rows.
- **Launchers**: the four legacy scripts are retired with `exit 64` rather than patched again. Is
  retirement an adequate answer to findings 9–10, given nothing will be re-run through them?
- **Official driver** (`cluster/greekmmlu_official.sh`): per-run directory, `.exit` receipts, WALL vs
  MAXWAIT, ≤4 models, local validation. Trace the quoting of the `echo $? > ….exit` through
  local shell → ssh → `bash -c`; trace a scorer that fails, and one that outlives MAXWAIT.
- **Ledger + page + banners**: α interval now paired ([−0.74, +1.85], `alpha_interval.json`); the
  ledger's re-run section rewritten; correction banners on three documents.

## 2. Pre-launch review of what will actually be run

- `cluster/eval_jobs/dpo01_frozen_rescore.sh` + `dpo01_frozen_models.txt` (22 models; launch will be
  `LIST=… EXPECT=22 sbatch …`). Frozen date 2026-09-19 so that the 26 runs already dated the 19th can
  be reused after the guard confirms equal request digests. Check: the tokenizer freeze (JSON-escaped
  template inside `tokenizer_config.json` — does the `NEEDLE` actually match the bytes on disk? check
  the real file on the cluster); the **canary** (step 1b) and its quoting through `uenv run … bash -c "…
  <<'PY'"`; whether lm_eval really uses `tokenizer=$TOK`'s template; `config=parent` staging (no
  symlink can be written through; arm weights retained); per-model validation; failure accounting;
  cleanup scope; walltime (full battery ≈ 36–40 min/model 4-parallel; gen-only ≈ 25 min).
  **Is the reuse premise sound** — will a run rendered by the *unfrozen* template on the 19th be
  byte-identical to one rendered by the frozen template, and does anything else differ between the old
  and new runs (e.g. `tokenizer=` path in model_args, lm_eval/transformers versions) that the guard will
  or should flag?
- `cluster/dpo01_official_gmmlu_rest.sh` — staging + three sequential driver invocations for the 12
  remaining runs.
- Is the model list right for what the ledger says R1/R2/R3 must cure? Anything missing or wasted?

## Disposition

BLOCKER/HIGH are fixed before launch. MEDIUM/LOW logged. If you find nothing at BLOCKER/HIGH, say
plainly that the jobs may launch.

## Deliverable

Markdown. Header → one-line verdict → fix-verification table → defeat attempts and outcomes →
pre-launch findings most-severe-first with `path:line` → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
