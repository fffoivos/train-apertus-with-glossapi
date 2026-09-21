# 14 — Greek RLHF: preference data, DPO, and the evaluation guard

> **In one line:** everything after supervised fine-tuning — building Greek preference pairs,
> training DPO arms on the SFT parent from subproject 12, and measuring them under a comparison
> guard that refuses any pair of runs differing in more than one declared variable.
> **Period:** work began 2026-09-11 inside `12_greek_sft_experiments`; split out 2026-09-21.
> **Status:** DPO round 1 complete and corrected. Four questions answered, one open (Q5).

## Why this is its own subproject

For ten days the RLHF work lived under the SFT umbrella because it started as "the next stage of
the same experiment". It stopped being that: it has its own data pipeline, its own trainer, its own
evaluation library and 115 coordination documents. Keeping it inside 12 meant nobody could tell
which half of `cluster/` or `docs/` they were looking at.

The rule used for the split: **whatever exists because of preference training lives here; whatever
an SFT run needs lives in 12.** Where something is genuinely shared, it stayed in 12 and this
subproject reaches for it explicitly (see *What is shared* below) rather than being copied.

## Start here

| | |
|---|---|
| **The result, and why it was first reported backwards** | [`docs/pages/DPO01_CORRECTIONS_20260920.html`](docs/pages/DPO01_CORRECTIONS_20260920.html) |
| **The measurement record** | [`docs/pages/DPO01_CURVES_20260920.html`](docs/pages/DPO01_CURVES_20260920.html) |
| **What is still open** | [`docs/RLHF_COORDINATION/OPEN_QUESTIONS_20260920.md`](docs/RLHF_COORDINATION/OPEN_QUESTIONS_20260920.md) — Q1–Q5 |
| **Every fault found, and what each poisoned** | [`docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`](docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md) |
| **How prompts are made, and the structure that tracks them** | [`docs/PROMPT_BANK_20260921.md`](docs/PROMPT_BANK_20260921.md) |
| **Current versions of everything** | [`docs/RLHF_COORDINATION/CURRENT_VERSIONS.md`](docs/RLHF_COORDINATION/CURRENT_VERSIONS.md) |

## Layout

```
rlhf/                 the library
  prompts/            the prompt bank: every prompt tied to one source; no duplicates; quotas enforced
  evals/              the comparison guard: sealed Results, compare(), weights receipts, stats
  sol.py              the one Sol client (effort is policy, not a parameter)
  tests/              81 tests
data/rlhf/            the preference-data pipeline
  generator_v02/      seed-prompt generator          prompt_generator/   forum prompts (Codex-owned)
  dialogue_v2/        on-policy multi-turn           dialogue_quality_depth/
  maths_judge/        judge_rank4.py  registry/      pool/  round3/
  dpo01/              the round-1 pair set (343 train / 54 dev) + provenance
  dpo01_nomaths/  dpo01_randomcut/  dpo01_balanced/   the ablation sets
  math -> ../../12…/data/math      SYMLINK, see below
cluster/
  dpo_train.py        the trainer          configs/G4F6P1_DPO01_*   31 arm configs
  dpo01_*.sh  rc44_fix.sh  rlhf_sample.sh  run_review.sh  dqd_*
  eval_jobs/          frozen re-score, receipts, scorecards, Q1/Q3 analysis, calibration, instrument check
results/G4F6P1--DPO01/  summary JSON + the two page generators (curves_page.py, corrections_page.py)
docs/
  pages/              generated HTML         RLHF_COORDINATION/   plans, ledger, 18 reviews
```

Pages are generated; do not edit them by hand:

```
python3 results/G4F6P1--DPO01/curves_page.py      docs/pages/DPO01_CURVES_20260920.html      --standalone
python3 results/G4F6P1--DPO01/corrections_page.py docs/pages/DPO01_CORRECTIONS_20260920.html --standalone
```

## What is shared with 12, and deliberately not copied

| this subproject uses | which lives in | why it stayed there |
|---|---|---|
| `cluster/preflight.sh`, `ledger.sh`, the remote `workbench.sh` | `12/cluster/` | allocation + spend accounting for every job, SFT or not |
| `cluster/greekmmlu_official.sh` and its scorer, validator, receipt tool, gold | `12/cluster/` | one GreekMMLU instrument, also used by SFT-era chains |
| `results/greekmmlu_official/` (incl. `label_calibration.json`) | `12/results/` | holds SFT models, peers (Krikri) *and* DPO arms in one place |
| `data/math/` — `mathlib`, `codex_server.py` | `12/data/math/` | the maths SFT dataset library; RLHF only borrows the Sol client |
| `evals_code_backup/`, `evals/ilsp/tasks` | `12/` | the benchmark task code is not RLHF-specific |

`data/math` is a **symlink**. Seven modules here import `mathlib` / `codex_server` via
`<data>/math`, two of them in Codex-owned paths that must not be edited, so one documented link
replaced seven patches. If 12 ever moves `data/math`, this link is the only thing to update.

There is exactly one dependency in the other direction: `12/cluster/greekmmlu_official.sh` copies
`rlhf/evals/weights.py` from here to build the evaluator-side weights receipt.

**The cluster layout did not change.** Everything still deploys under
`/iopsstor/scratch/cscs/fffoivos/sft_round1/` — that name is historical and jobs, receipts and
checkpoints all point at it. Only the local tree was reorganised.

## Known test state (2026-09-21)

`rlhf/tests` 81/81, `maths_judge` 15/15, `generator_v02` 9/9, `prompt_generator` 34/34.
Two failures predate the split and were left alone: `dialogue_v2` has a deliberate tripwire
(*"a DPO trainer now exists: inspect its masks"*) that has fired since the trainer was written, and
`dialogue_quality_depth/select.py` shadows the stdlib `select` when pytest is run from inside that
directory.

## Ownership

`docs/RLHF_COORDINATION/CODEX_STATUS.json` and `data/rlhf/prompt_generator/` belong to the Codex
agent. They were moved with everything else but not edited.
