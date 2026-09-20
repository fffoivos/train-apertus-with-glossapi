# Review brief R-DPO7c (Astra) — are the CONCLUSIONS supported by the data?

**Scope: inference from data to claim.** Four Sol reviews have certified the analysis code and the
measurement protocol: `R-DPO7a_review_1.md`, `R-DPO7a2_review_1.md`, `R-DPO7b_review_1.md`,
`R-DPO7b2_review_1.md`. Read them and treat any unresolved finding as a constraint on what may be
concluded. Your question is the next one: **given the numbers, is each published claim right?**

Read-only. Data is local; `ssh clariden` works if you want the raw cluster artifacts.

## Background

DPO round 1, 397 Greek preference pairs, one SFT parent. A prior conclusions review (R-DPO6,
gpt-6-astra) returned HOLD for overclaiming from n=1 aggregates; `R-DPO6_response.md` records the
response. Since then four code/protocol reviews found real defects, all now fixed, and two new
measurements landed that **reversed two headline claims**. Do not assume the current page is right —
it is the thing under review.

## What to read

- `results/G4F6P1--DPO01/curves_page.py` — generates the artifact; sections 6–14 are the conclusions,
  `DISPOSITION` is the survives/withdrawn table.
- `docs/DPO01_CURVES_20260918.html` — the rendered page.
- Data: `results/G4F6P1--DPO01/{all_results.json,evidence_bundle.json,greekmmlu_paired.json,greekmmlu_full_partial.json}`,
  per-item predictions in `greekmmlu_items/`.

## The claims to adjudicate

For each: **supported / overstated / understated / wrong**, with the number that decides it.

1. **The GreekMMLU withdrawal, now with the full benchmark.** We scored all 16,632 items. On the 250
   already reported every arm gains exactly +2.00 pp; on the 16,382 held-out items the same arms gain
   +0.44 / +0.36 / +0.52 — and `armIPO42`, which reached 2% of its training target, is the largest in
   every column. We withdraw "+2 pp of Greek knowledge" but acknowledge a ~0.5 pp held-out effect
   that we also decline to attribute to preference learning, since the failed arm shares it. **Is
   that the right call on both halves?** Is there a reading in which the half-point IS a training
   effect? Note only 4 of 8 models had finished at the time of writing.
2. **The configuration interaction.** The completed 2×2 shows the IFEval training effect is +1.85 /
   +1.48 pp under the checkpoint config and −1.66 / −2.59 pp under the parent's. We now say there is
   no configuration-free statement of an instruction-following gain, and that under the deployment
   configuration both arms are worse. **n=1 per cell, two checkpoints.** Is the page's weighting right?
3. **MGSM as the contrast.** −6.40 pp in *both* columns for the anchored arm, which we use to argue
   the maths damage is real while the IFEval gain is not. Is that contrast doing legitimate work?
4. **The length-balanced arm** — −1.6 pp MGSM vs −6.3, but −8.4 pp Global-MMLU-Lite, the worst of any
   arm. Called "a trade, not a win", with length/selection/exposure confounded. Right reading?
5. **The disposition table.** Twelve claims marked survives / withdrawn / confounded / inconclusive /
   config-dependent. Is each right? Flag anything still stronger than the evidence carries **and
   anything we have now understated** — over-withdrawal is also an error.
6. **The protocol caveat.** Our GreekMMLU is `custom_full_text`, not the official label protocol; the
   parent scores ~54.2% here vs ~69.4% official. We state this and claim internal comparability. Is
   that sufficient, or does it undermine conclusions we still draw from these numbers?
7. **The overall verdict** — "nothing shippable; the round's output is instrumentation". Fair?

## A specific worry to test

The artifact's author is the same agent that produced the results and then withdrew most of them
under criticism. Test for **the opposite failure from R-DPO6**: claims narrowed until they say
nothing, uncertainty invoked selectively, or withdrawal used to avoid defending a result the data
supports. Two positive findings have now been withdrawn in two days; check that each withdrawal is
driven by evidence and not by a preference for appearing rigorous.

## Disposition

BLOCKER/HIGH change the artifact before it is republished. MEDIUM/LOW logged. This is the final
conclusions checkpoint for this round.

## Deliverable

Markdown. Header (what you read/ran) → one-line verdict → findings most-severe-first with the
deciding number and the permissible wording → a claim-by-claim disposition table → what is correct
and must not change → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`
