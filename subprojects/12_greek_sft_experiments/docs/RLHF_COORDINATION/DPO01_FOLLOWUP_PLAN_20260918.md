# DPO01 follow-up: plan and review checkpoints

Written 18 September 2026 evening, after the full 22-model battery. Budget cap raised 275 → 525 on
the owner's instruction; CHF 251.30 spent, ~CHF 274 available. Budget is no longer the binding
constraint, so the programme is ordered by **what makes the other results interpretable**, not by cost.

## What today established, and how firmly

| finding | strength |
|---|---|
| Damage tracks total update (lr × steps), r = +0.92 to +0.97 over 21 checkpoints; learning rate alone is much weaker | strong, but every point is n=1 |
| Response length predicts MGSM accuracy, r = +0.952 over 8 models; median falls 59.5 → 46 words | strong |
| Damage is confined to the response *envelope* (language −22.6, startend −16.4, length −13.3); content families flat or better | strong |
| Served lanes (MATH-500, IFBench): 44 positive vs 3 negative deltas, sign test p < 0.0001, mean +0.91pp | strong in aggregate, no single comparison significant |
| lm_eval lanes (IFEval, MGSM, Global-MMLU): every checkpoint below the parent | strong |
| **alpha 0.25 is the best setting** | **weak — 1.1pp over arm06, 2.0pp over arm03, against a round-one seed noise floor of ±1.0pp on IFEval** |

That last row is the problem. Three of the proposed arms use alpha 0.25 as their base recipe, and the
claim rests on gaps at or under the noise floor with **zero replicates across 21 checkpoints**.

## Order of execution

1. **R-DPO5 review — BLOCKING, before any GPU.** See below.
2. **IPO, 2e-6, alpha 0.25, beta 0.1, 3 epochs.** Tests the diagnosed cause directly: DPO drove train
   separation to 25–27 nats with only 1–4.6 generalising (ratio 0.04–0.17), and that surplus is where
   the length shortcut was learned. IPO stops at a target margin of 1/(2β) = 5.0 nats.
3. **Arm 07 — arm05 recipe at 5 epochs, run FRESH.** Owner requested. Under constant LR and seed 42
   its first 129 steps are identical to arm05, so epoch 3 must reproduce arm05_ep3. Determinism check.
4. **Seed replicates: arm05 at seed 43, arm01 at seed 43.** The cheapest item on the list (~12 min
   training, ~CHF 2.5) and the only one that makes the other four interpretable. Arm 07 gives
   determinism at a fixed seed; these give the actual noise floor for this pipeline.
5. **4e-6, alpha 0.25, 3 epochs.** Clean movement manipulation with repetition held at 3×.
6. **IPO at beta 0.25** (target 2.0 nats), only if (2) still shows length collapse at 5.0.
7. **GreekMMLU 250 lane** and the **generation_config control**, whenever they fit.

Also queued and already built: the **length-balanced control arm** (274 magnitude-matched pairs,
chosen/rejected word ratio 0.992 vs 0.785), which tests the length mechanism against the pairs we
already have.

## Pre-registered predictions

**IPO arm.** Median MGSM response length holds near the parent's 59.5 words rather than collapsing to
46; train separation sits near 5 nats rather than 27; train-to-dev ratio approaches 1.0 rather than
0.13. **If separation drops to 5 and the benchmarks still degrade, the over-optimisation diagnosis is
WRONG.** That is to be recorded as a falsification, not explained away.

**Arm 07.** Epoch 3 reproduces arm05_ep3 on IFEval, MGSM and Global-MMLU. If it does not, every small
difference measured today is unreadable and that finding outranks the extension itself.

**Seed replicates.** If arm05@43 differs from arm05@42 by more than ~1pp on IFEval, the alpha ranking
is noise and the follow-up programme should be rebuilt on whatever survives.

## Review checkpoints

Two, both placed immediately before a decision that is expensive to get wrong. Reviewer effort
**xhigh** (pipeline calls stay medium). **Maximum two cycles per checkpoint**: cycle 1 is the review,
cycle 2 is the re-review after fixes. A third cycle is not diligence — it means the checkpoint was
placed wrong or the brief was too broad, and the correct response is to say so and escalate in one
message rather than run it.

### R-DPO5 — BLOCKING, before any GPU is spent

Subject: the experiment design, and specifically the IPO parameterisation.

The single thing most likely to waste the whole programme is the claim that TRL's IPO loss is
`(gap − 1/(2β))²` with the gap in nats, so that β = 0.1 targets 5.0. **If the installed TRL
parameterises it differently, the IPO arm is mis-specified and teaches us nothing.** The reviewer must
check the installed source rather than the paper.

Also asked: are the pre-registered predictions falsifiable as written, and do the arms answer
distinguishable questions or do they overlap?

### R-DPO6 — after the first two arms report

Subject: interpretation, before the programme's remaining arms are committed.

Specifically: does the length mechanism survive contact with the new data; is the
movement-versus-learning-rate correlation being over-read from n=1 arms; and did arm07_ep3 actually
reproduce arm05_ep3.

### Deliberately no review before the write-up

Everything such a review would catch is caught by R-DPO6. Adding one would be exactly the third pass
the owner's rule is aimed at.

## Registered for future work — NOT in this programme

Owner decision, 18 September: record these and proceed with the five arms as planned.

**The judged pool is 46% unused.** Of 857 prompts judged across rounds 2 and 3, only the 461 with a
reinforce reply can form a pair under the current rule. The other 396 are discarded despite being
fully judged and paid for:

| a prompt's best reply | prompts | usable today |
|---|---|---|
| reinforce | 461 | yes — these became the 397 pairs |
| neutral | 210 | no |
| discourage | 186 | no |

1. **Neutral-over-discourage pairs (owner's proposal).** Pair a neutral reply against a discourage
   one: discourage the worse reply without endorsing a mediocre one. Today's data supports the
   premise — on dev, arm01 moved rejected −15.84 nats against chosen −11.22, so the rejected side
   carries most of the gradient. 210 prompts, a 53% increase on the current pool, no new generation
   or judging.
2. **KTO or NPO on the all-discourage prompts (owner's proposal).** 186 prompts where every sampled
   reply was bad cannot form a pair by construction, but an unpaired objective can use them as
   negative-only signal. Also already paid for.
3. **A KL-to-parent or SFT-replay arm.** The Global-MMLU loss concentrates in German and Portuguese
   humanities while Spanish and English STEM gain — an axis that maps onto no pair category we could
   add and that we would not have thought to enumerate. A constraint defending the parent everywhere
   addresses it without enumeration.

## On a denser alpha sweep

Considered and **not recommended**. We already have a five-point alpha sweep — 0, 0.1, 0.25, 0.5, 1.0
(arms 01, 04, 05, 06, 03). The gap in the evidence is not resolution, it is replication: every point
is n=1 and the spread across them at epoch 3 is 2.0pp against a ±1.0pp noise floor. Adding alpha
values would produce more unreplicated points at higher density and would not make the existing ones
readable. Two seed replicates cost less and answer the prior question — whether any of the five
points differ at all. If the replicates show the ranking is real, a denser sweep becomes worth
considering; until then it would be measuring more precisely something we cannot yet detect.

## Standing caveat

Every arm so far is n=1 and the alpha ranking spans 2.0pp against a ±1.0pp noise floor. Until the
replicates report, **all of today's small differences are provisional** — including "alpha 0.25 is
best", which three of these arms currently assume.
