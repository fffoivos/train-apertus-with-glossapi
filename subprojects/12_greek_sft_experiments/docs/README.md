# 12_greek_sft_experiments / docs

Start here. This folder accumulated 70 loose files across three phases of work; what follows is
where things are and, more usefully, **which ones are current**.

## Read this first

| | |
|---|---|
| **The current result** | [`pages/DPO01_CORRECTIONS_20260920.html`](pages/DPO01_CORRECTIONS_20260920.html) — why the round was reported backwards, the corrected numbers, and the nine hypotheses eliminated |
| **The measurement record** | [`pages/DPO01_CURVES_20260920.html`](pages/DPO01_CURVES_20260920.html) — every curve, table and receipt behind it |
| **What is still open** | [`RLHF_COORDINATION/OPEN_QUESTIONS_20260920.md`](RLHF_COORDINATION/OPEN_QUESTIONS_20260920.md) — Q1–Q5, each with its evidence and what would settle it |
| **Every error found** | [`RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`](RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md) — nine faults, what each poisoned, and the spend |

Both HTML pages are generated. Do not edit them by hand:

```
python3 results/G4F6P1--DPO01/curves_page.py      docs/pages/DPO01_CURVES_20260920.html      --standalone
python3 results/G4F6P1--DPO01/corrections_page.py docs/pages/DPO01_CORRECTIONS_20260920.html --standalone
```

`corrections_page.py` imports `curves_page.py`'s chart builders, so both plot identical curves from
identical data. Omitting `--standalone` emits an artifact body instead of a full document.

## Layout

```
docs/
  pages/       generated HTML (the two above, plus the SFT-era pages)
  tools/       the scripts that build the markdown/HTML docs
  receipts/    dataset assembly receipts (JSON) + R3_single/
  reviews/     Astra benchmark reviews, Sept 10 era
  lit/         literature notes
  RLHF_COORDINATION/
    reviews/   the DPO/RLHF review series, R-DPO1..16 — see its INDEX.md
    messages/  cross-agent coordination
```

### The three `reviews/` directories are not duplicates

They are three different review programmes and each belongs where it is:

- `../reviews/` (repo root of this subproject) — R1/R1b, the early data-and-trainer reviews
- `docs/reviews/` — the Astra benchmark reviews from around 10 September
- `docs/RLHF_COORDINATION/reviews/` — the DPO round-1 series, R-DPO1 through R-DPO16, with an `INDEX.md`

## Dated files, and which date wins

Almost every filename carries a date. Where two files share a stem, **the later date supersedes** —
with one deliberate exception:

- `pages/DPO01_CURVES_20260918.html` **stays where it is, in `docs/`, not in `pages/`.** It is the
  snapshot of what was published on the day the round was reported as damage, and twelve review
  briefs plus `execution_state.json` point at that path. Moving it would break the record of what
  each reviewer was actually shown. It is superseded by the 20260920 page for every purpose except
  that one.

## Conventions

- Anything under `pages/` is generated; edit the generator in `results/G4F6P1--DPO01/`.
- `RLHF_COORDINATION/CODEX_STATUS.json` and `prompt_generator/` are owned by another agent — do not edit.
- Receipts are immutable once written; a re-run writes a new dated file.
