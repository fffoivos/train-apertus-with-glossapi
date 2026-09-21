# 12_greek_sft_experiments / docs

SFT documentation only. **The RLHF / DPO work moved to [`../../14_greek_rlhf/`](../../14_greek_rlhf/README.md)
on 2026-09-21** — its pages, the `RLHF_COORDINATION/` tree, the DPO review series and the poison
ledger are all there now. If you are looking for the DPO01 result, start at
[`14_greek_rlhf/docs/pages/DPO01_CORRECTIONS_20260920.html`](../../14_greek_rlhf/docs/pages/DPO01_CORRECTIONS_20260920.html).

## Layout

```
docs/
  pages/       generated HTML: SFT plan, recipe, dataset examples
  tools/       the scripts that build the markdown/HTML docs
  receipts/    dataset assembly receipts (JSON) + R3_single/
  reviews/     Astra benchmark reviews, Sept 10 era
  lit/         literature notes
  PRE_DPO_PROGRAMME_20260913*/   the pilot waves run BEFORE any DPO existed; SFT work, so they stay
```

`../reviews/` at the subproject root holds R1/R1b, the early data-and-trainer reviews. It and
`docs/reviews/` are two different review programmes, not duplicates; the third one (R-DPO1..16) went
to subproject 14 with the work it reviewed.

## Dated files

Almost every filename carries a date. Where two files share a stem, the later date supersedes.

The ~45 markdown files here stay flat on purpose: nearly all are referenced by path from other
documents and review briefs, and regrouping them would break those references to buy a tidier
directory listing.

## Shared with subproject 14

14 does not copy shared infrastructure; it reaches into this subproject for `cluster/preflight.sh`,
`cluster/ledger.sh`, the GreekMMLU-official instrument (`cluster/greekmmlu_official.sh` + scorer,
validator, receipt, gold), `results/greekmmlu_official/`, `data/math/` (via a symlink) and the
benchmark task code. **Moving any of those breaks 14** — see the table in its README.
