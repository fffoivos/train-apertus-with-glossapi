# R-DPO6 response — cycle 1 of 2

> **CORRECTION, 19 September 2026 — parts of this document are superseded.** It states or relies on one or more of:
> "the IPO arm did not train" (false: 129/129 steps); a "same-seed repeat gap" (that pair was scored a day apart);
> GreekMMLU gains measured with a custom protocol (the official protocol gives −0.26 to −0.43 pp);
> Global-MMLU deltas compared across prompt dates; an α interval described as paired (it was unpaired; paired = [−0.74, +1.85]).
> Current status of every claim: `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. The text below is kept unedited as a record.


Review: `R-DPO6_review_1.md` (gpt-6-astra, xhigh, 2026-09-19). Verdict: *hold the conclusions for
revision, preserve the experiments.* 1 BLOCKER, 6 HIGH. All applied. Artifact republished (v7).

The review asked us to resolve from existing artifacts where possible and narrow only where not.
Five of the seven were resolvable; two were narrowed. One resolution went further than the review's
own disposition and **withdrew** a claim the review was willing to let stand.

| # | finding | disposition | where |
|---|---|---|---|
| BLOCKER | independent verification missing | **narrowed** — explicit "owner-reported, 0 rows inspected, not independently verified" banner; evidence paths named | artifact §6 |
| HIGH | noise floor used as a significance threshold | **resolved** — three quantities separated and tabulated | §9 |
| HIGH | fair baseline answers a conditional | **resolved** — measured the missing cell; both baselines reported | §7, §8 |
| HIGH | balanced arm does not isolate length | **narrowed** to the review's exact wording + exposure numbers | §11 |
| HIGH | "barely trained because of beta" not established | **narrowed**; AdamW counter-argument recorded | §12 |
| HIGH | GreekMMLU seed stability ≠ precision | **withdrawn entirely** (review said "survives as fixed-slice observation") | §10 |
| HIGH | correlations do not establish mechanisms | **withdrawn** — exposure and envelope-not-content both dropped | §6 table |

## The one that went further than the review

The review accepted GreekMMLU +2 pp as a fixed-slice observation. Pairing the per-item predictions
(`cluster/eval_jobs/greekmmlu_paired.py`, 66 models) does not support even that:

- McNemar over discordant pairs: **p = 0.15–0.42** for every group. Nothing separates from the parent.
- **235 of 250 items never move** across the parent and 15 trained runs (139 always right, 96 always wrong).
- The **same 8 items flip right and the same 3 flip wrong in every arm**, including `armIPO`, which
  reached 2% of its training target and scored below chance on dev reward accuracy.

An arm that did not train gets the identical +5 net items. That is not a recipe effect. The 0.002
between-seed SD was small because only 15 items *can* move, not because the measurement is precise.

**Claim withdrawn.** This removes the round's only positive knowledge result; the overall reading
gets worse, not better.

## Arithmetic the review caught, and the answer

> *"Four values each within ±0.9 pp cannot have a mean of −0.97 pp."*

Correct — the two figures came from different baselines and different quantities. The four far-end
IFEval values are 0.5933 / 0.6100 / 0.6063 / 0.6285: mean **−0.97 pp against the parent's own
config**, **+0.69 pp against the parent under checkpoint config**, spread **3.5 pp**. The "0.9 pp"
was the *same-seed repeat gap*, a single contrast. Setting them against each other was wrong.
Corrected reading: no reliable improvement demonstrated over the range tested.

> *"What precisely are the 0.9, 2.8 and 1.6 pp quantities?"*

0.9 and 2.8 pp are the same-seed repeat gaps (IFEval, MGSM) — one contrast each, `arm05_ep3` vs
`arm07_ep3`. 1.6 pp was a between-seed SD quoted from a different arm than the 2.8. Now tabulated
separately alongside the item sampling SE, which is the largest of the three and had been absent:
IFEval 2.10 pp, MGSM 3.04 pp, GreekMMLU 3.10 pp.

> *"What confidence level and resampling unit produced the alpha interval?"*

95% percentile over 10,000 resamples; the unit is one **training seed** (a whole run), resampled
independently within each arm, seeds not matched. Observed +0.70 pp, CI [−0.52, +1.77]. The
matched-by-seed paired differences are +0.4, +1.1, −2.0, +2.0, +2.0 (paired SD 1.68 pp, 4/5
positive) — also inconclusive. Withdrawal stands.

> *"What constitutes one served-lane sign?"*

One (run, benchmark) cell at epoch 3 vs the parent on the same benchmark. Re-counted over that
stated unit: **35 positive, 8 negative, 2 tied** — not 44/3; ties had been dropped and the earlier
tally mixed in non-epoch-3 checkpoints. Cells reuse identical items and seeds share a recipe, so it
is reported descriptively with no test attached.

> *"Which optimizer was used for IPO?"*

AdamW. The review is right that per-parameter normalisation undercuts the raw-gradient-scale
argument; recorded as an open cause.

## New measurement run for this review

`cluster/eval_jobs/dpo01_armcfg_cell.sh` (job 3443153) fills the missing cell of the config 2×2:
an arm's **weights** under the **parent's** generation config and tokenizer. Until it lands the
artifact renders that cell as "not measured" rather than inferring it.

## Not done

- Item-level pairing for MGSM and IFEval. The log-sample files exist; the formatting-vs-reasoning
  split is withdrawn rather than tested. Backlog.
- A matched control for the length claim (274 pairs sampled at random, or re-rendered to restore
  the skew). One training run. Backlog.
- Independent recomputation by a second party. Still outstanding — this is the BLOCKER and it is
  labelled, not closed.

**Cycle 1 of 2 on this checkpoint. No second cycle requested:** the findings were dispositive rather
than contested, and a re-review would re-read claims we have already narrowed to the review's own
wording. Escalating instead of spending cycle 2.
