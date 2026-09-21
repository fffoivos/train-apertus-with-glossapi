# Overnight run, 18→19 September: replication, then finish the measurement programme

> **CORRECTION, 19 September 2026 — parts of this document are superseded.** It states or relies on one or more of:
> "the IPO arm did not train" (false: 129/129 steps); a "same-seed repeat gap" (that pair was scored a day apart);
> GreekMMLU gains measured with a custom protocol (the official protocol gives −0.26 to −0.43 pp);
> Global-MMLU deltas compared across prompt dates; an α interval described as paired (it was unpaired; paired = [−0.74, +1.85]).
> Current status of every claim: `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md`. The text below is kept unedited as a record.


~10 hours of node time, cap 525 CHF with ~CHF 272 free. The binding constraint is **evaluation, not
training**: an arm trains in ~6 minutes and a model scores in ~36. So the programme buys statistics,
not breadth.

## Why replication is the top priority

Two independent measurements say run-to-run variation is large:

| source | measured | effect |
|---|---|---|
| seed 42 → 43 | 2 arm pairs, dev reward accuracy | **5.4pp**, identical in both |
| **nothing at all** (same seed, same config) | arm05_ep3 vs arm07_ep3 prefix | diverges at optimiser step 3; **1.0–1.4pp** on the served lanes |

The same-seed divergence is `set_seed` fixing the RNG but not floating-point reduction order under
ZeRO-3 + bf16 — expected, not a bug, and not worth eliminating. The consequence is that **every
single-run comparison made on 18 September is unreadable**, including "alpha 0.25 is best", which
spanned 2.0pp against a round-one floor of ±1.0pp.

## T1 — the replication set (configs written, 10 arms)

| arm | seeds | purpose |
|---|---|---|
| `01s44` `01s45` `01s46` | 44, 45, 46 | takes alpha 0 to **n=5** with 42, 43 |
| `05s44` `05s45` `05s46` | 44, 45, 46 | takes alpha 0.25 to **n=5** |
| `IPO42` `IPO43` | 42, 43 | IPO at the corrected **beta 10** (target 0.050 per token) |
| `BALs43` `BALs44` | 43, 44 | length-balanced arm to n=3, so the mechanism test is not n=1 |

Scoring: replicates at **epoch 3 only** — the comparison point; scoring all three epochs trebles cost
for no extra power on the alpha question. IPO at **every epoch**, because R-DPO5's HIGH requires
movement to be read alongside the benchmarks.

## T2–T5 — already in flight or built

T2 lm_eval lane (IFEval 541, MGSM 250, Global-MMLU) for the 16 follow-up checkpoints · T3 served lane
for the new arms · T4 GreekMMLU 250, all models · T5 generation_config control (parent's weights under
a checkpoint's generation config, isolating the eos/pad/use_cache confound).

## The noise floor — the deliverable, and how it is computed

This is the number the whole programme depends on and it does not yet exist for the primary endpoint.

1. **Within-arm spread across seeds.** For arm01 and arm05 separately, at epoch 3, compute the mean
   and standard deviation of IFEval prompt-strict over the five seeds; likewise MGSM and Global-MMLU.
   Report the **standard deviation and the full range**, not a summary.
2. **Same-seed floor.** `arm05_ep3` vs `arm07_ep3` are bit-identical in intent and differ only through
   reduction order. Their difference on every lane is the irreducible floor.
3. **The alpha test.** Does the arm01 vs arm05 difference exceed the within-arm spread? A paired
   comparison across the five seeds, with a bootstrap interval. **If it does not, "alpha 0.25 is best"
   is formally withdrawn**, along with every ranking built on it.
4. **Restate every 18 September claim against the floor.** Each one is marked *survives*, *inside the
   floor*, or *withdrawn*. No claim below the floor is reported as a result.

## Reviewer checkpoints

**R-DPO5 — done.** Verdict HOLD on IPO; the BLOCKER is discharged (two fixtures now drive the
installed `_compute_loss`: the branch normalises per token, and beta 10 gives exactly zero loss on the
reviewer's unequal-length case). Its HIGH stands and is carried into R-DPO6.

**R-DPO6 — after the replication set reports. BLOCKING on conclusions, not on further compute.**
Subject: the statistics, not the design. Specifically — is the within-arm spread computed and applied
correctly; which 18 September claims survive it; is the movement correlation (r = +0.92–0.97) still
supportable once n=1 points are pooled; and does the IPO result reflect the target or merely the
100-fold weaker gradient that beta 10 implies. This is the checkpoint that decides what the write-up
may assert.

**No third checkpoint.** A review before the write-up would catch nothing R-DPO6 does not, and the
owner's rule is aimed exactly at that pass.

**Cycle rule, operationally.** Cycle 1 is the review; cycle 2 is the re-review after fixes. A third
cycle means the checkpoint was placed wrong or the brief was too broad — say so and escalate in one
message rather than running it. Reviewer effort xhigh; pipeline calls stay medium.

## Not doing overnight

Blind better/equal/worse comparison (a new instrument, and it draws on the shared Codex window at 31%
with the data-generation session also drawing) · neutral-over-discourage pairs, KTO/NPO, KL-replay
(registered future work) · any further hyperparameter conditions — with the floor unmeasured, more
unreplicated points would add unreadable results.

## Halt conditions

Spend approaching the 525 cap · a stage failing twice for the same reason · a review returning
BLOCKERS with no mechanical fix. Otherwise decide and log.

---

## Outcome, 2026-09-19

All measurement complete: 68 model directories scored, GreekMMLU on 66. Queue empty apart from
job 3443153 (the config 2×2 missing cell, added in response to R-DPO6).

**R-DPO6 returned HOLD** (1 BLOCKER, 6 HIGH) and all findings were applied — see
`reviews/R-DPO6_response.md`. Five resolved from existing artifacts, two narrowed, and one
**withdrawn further than the review asked**.

### The headline change

GreekMMLU +2 pp was the round's only positive knowledge result. Pairing the per-item predictions
withdrew it: McNemar p = 0.15–0.42, 235 of 250 items never move across 16 models, and the same 8
items flip right / same 3 flip wrong in every arm — **including the IPO arm that reached 2% of its
training target**. A run that did not train posts the identical gain.

### Where the round stands

| | vs parent @ checkpoint config | |
|---|---|---|
| plain DPO α=0, n=5 | IFEval +0.9 · MGSM −6.3 · gMMLU-Lite −4.5 | no |
| anchored α=0.25, n=5 | IFEval +1.6 · MGSM −6.3 · gMMLU-Lite −4.0 | no |
| length-balanced, n=3 | IFEval +1.4 · MGSM **−1.6** · gMMLU-Lite **−7.1** | trade, not a win |
| IPO β=10, n=2 | gate unmet, inconclusive | — |

**Nothing is shippable.** The balanced subset is the only interesting arm and it does not dominate:
it buys ~5 pp of Greek mathematics and gives up ~3 pp more multilingual knowledge than any other arm.

### What the round actually produced

Instrumentation, not a model: frozen-reference displacement measurement, the generation-config
control, the paired item analysis, and the replication design itself. Next round's claims are
checkable at a fraction of the cost because of these.

### Carried to the next round

1. Item-level pairing for MGSM and IFEval (log-samples exist; envelope-vs-content is withdrawn, not tested).
2. A matched control for the length claim — 274 pairs sampled at random from 397, one training run.
3. Independent recomputation by a second party. **This is the open BLOCKER**; it is labelled on the
   artifact, not closed.
4. Decide the deployment configuration explicitly, and the acceptable regressions, before the next
   shipping question is asked.
