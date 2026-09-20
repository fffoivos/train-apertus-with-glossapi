# Review brief R-DPO6 — DPO01 conclusions after replication

**Blocking on conclusions, not on compute.** All measurement is complete. This review decides what
the write-up may assert. Second and final checkpoint of this programme (R-DPO5 covered design).

## What changed since R-DPO5

R-DPO5's BLOCKER is discharged: two fixtures now drive the installed `_compute_loss` and confirm
`ipo_delta` is a difference of two independently length-normalised log-ratios, so beta 10 targets
0.050 per token (`cluster/test_dpo_local.py`, 9/9 pass, TRL 1.12.0 sha `bb0b8baa…`).

R-DPO5's HIGH — that beta also scales the initial gradient by 1/beta — turned out to be decisive.
See finding 4.

## The evidence

**1. Noise floor, measured at n=5 per arm (epoch 3, seeds 42–46).**

| metric | alpha 0 | alpha 0.25 | same-seed floor |
|---|---|---|---|
| IFEval prompt-strict | mean .6111, sd .0076, range .5989–.6174 | mean .6181, sd .0125, range .5970–.6303 | 0.9 pp |
| MGSM | mean .3608, sd .0230 | mean .3608, sd .0095 | 2.8 pp |
| GreekMMLU 250 | mean .597, **sd .002** | mean .595, **sd .002** | — |

The same-seed floor is `arm05_ep3` vs `arm07_ep3`: identical config and seed, differing only through
ZeRO-3 reduction order under bf16 (`set_seed` fixes RNG, not reduction order). They share 3 of 129
training loss values and diverge from optimiser step 3.

**2. Alpha is withdrawn.** arm01 vs arm05 on IFEval: difference of means +0.70 pp, within-arm sd
1.03 pp, 10,000-sample bootstrap CI **[−0.48, +1.77]**. "alpha 0.25 is best", asserted repeatedly on
18 September and used as the base recipe for three follow-up arms, does not survive.

**3. A third of the apparent damage was our own tooling.** transformers 5.16.1 re-serialised the
checkpoints with a different `eos_token_id` (2 → 68), a `pad_token_id`, and `use_cache` false.
Scoring the PARENT'S OWN WEIGHTS under a checkpoint's generation config (`parent_ckptcfg`) costs
**−1.7 pp IFEval and −2.4 pp MGSM**. Against that fair baseline:

| group | IFEval vs naive | IFEval vs FAIR | MGSM vs naive | MGSM vs FAIR |
|---|---|---|---|---|
| alpha 0, n=5 | −0.8 | **+0.9** | −8.7 | −6.3 |
| alpha 0.25, n=5 | −0.1 | **+1.6** | −8.7 | −6.3 |
| length-balanced, n=3 | −0.3 | **+1.4** | −4.0 | **−1.6** |
| IPO beta 10, n=2 | −4.0 | −2.3 | −12.2 | −9.8 |

GreekMMLU (250 items, fp32 candidate likelihood, no generation): parent .576, arms **.595–.597**,
i.e. **+2.0 pp at sd .002**. Global-MMLU-Lite over six non-Greek languages moves the other way,
−4 to −7 pp.

**4. The IPO arm is uninformative.** Dev `ipo_delta` reached **0.0010 and 0.0013** against a target
of **0.0500** — 2% of the way — and dev reward accuracy fell to 0.429/0.446, below chance. beta 10
gives dL/ddelta at 0 of −0.1 versus −10 at beta 0.1. The arm barely trained. **The pre-registered
falsification therefore does NOT fire**: its precondition (separation reaches target) was never met.

**5. The movement trend does not overshoot.** Damage recedes with total update (lr × steps) up to
~2.6e-4 and then flattens at the parent: far-end mean IFEval −0.97 pp across four points spanning
3.4e-4 to 5.2e-4, every point inside the floor. MGSM never recovers (far-end mean −6.70 pp). Tested
at double learning rate and five epochs.

**6. Length is supported by intervention, not only correlation.** `armBAL` trained on 274
magnitude-matched pairs (chosen/rejected mean word ratio 0.992 vs 0.785; chosen shorter in 50% vs
59%) loses **−1.6 pp MGSM against −6.3** for the standard arms, at n=3, against a 1.6 pp floor,
while IFEval holds at +1.4.

## Questions

1. **Is the fair-baseline correction legitimate?** We now compare arms to `parent_ckptcfg` rather
   than `parent`. Is that the right control, or does it over-correct — e.g. could the config change
   interact with trained weights differently than with the parent's?
2. **Does the length result survive n=3?** −1.6 vs −6.3 pp MGSM is a 4.7 pp difference against a
   1.6 pp floor, but the balanced arm also has 274 pairs against 343, so it moved less. Is the
   comparison confounded by movement, and does the GreekMMLU/Global-MMLU split affect the reading?
3. **Is GreekMMLU +2.0 pp at sd 0.002 believable**, or does a floor that small indicate the metric is
   insensitive rather than precise? It disagrees in sign with Global-MMLU-Lite.
4. **Which 18 September claims survive?** We ask for each to be marked survives / inside-the-floor /
   withdrawn, including: movement governs damage (r = +0.92–0.97 over 21 checkpoints, all n=1);
   length predicts MGSM (r = +0.952, n=8 correlated models); envelope-not-content; the served-lane
   sign test (44 positive / 3 negative).
5. **Is anything here shippable?** Best case is roughly +1.5 pp IFEval, +2 pp GreekMMLU, −6 pp MGSM
   against a fair baseline, or −1.6 pp MGSM with balanced pairs.

## Disposition

BLOCKER/HIGH change what the write-up asserts and are applied before it is published. MEDIUM/LOW are
logged. **Maximum two cycles on this checkpoint**; a third means the checkpoint was placed wrong and
should be escalated rather than run.
