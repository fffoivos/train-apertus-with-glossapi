# Pilot readout, 14 Sept 2026 (1-G4F6P0--00 / --01 / --02)

Question (plan §4, H9): do Sol-written worked Greek solutions (cut-2) raise MATH-500-el by at least 3 pp over terse cut-1 targets, at a one-epoch continuation from 1-G2F1P0@epoch1 with the same replay and English maths blocks? Secondary: does adding Level 5 help further?

## Result: no arm advances
Readout under the frozen rule (`results/pilots/summary.md`, readout v3.2, scorer v2, all inputs hash-bound):

| arm | MATH-500-el | loops | truncated | MATH-500-en | IFEval-el | MGSM-el | train loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1-G2F1P0@epoch1 (reference) | 12.8 | 27 | 60 | 16.4 | 54.2 | 46.8 | — |
| --00 terse targets | 13.4 | 82 | 132 | 13.8 | 55.3 | 46.0 | 0.756 |
| --01 worked solutions | 12.0 | 37 | 59 | 15.2 | 56.6 | 47.2 | 0.738 |
| --02 worked + Level 5 | 13.0 | 45 | 62 | 12.6 | 56.0 | 44.8 | 0.733 |

- Primary --01 vs --00 on MATH-500-el: −1.4 pp, one-sided 90% LB −3.6, two-sided 90% CI [−4.2, +1.6], 15.8% discordant items. Not qualified (gain < 3 pp, LB ≤ 0).
- Secondary --02 vs --01: +1.0 pp (LB −1.0); not evaluated for action under the hierarchy.
- Versus the stage-1 reference (paired, same 500 items): --00 +0.6, --01 −0.8, --02 +0.2 pp on Greek; −2.6 / −1.2 / −3.8 pp on English. All within noise of zero on Greek; English drifts down with the maths continuation.
- Guardrails pass for both candidates (IFEval-el paired +1.3 / +0.7 pp vs --00; MGSM-el +1.2 / −1.2 pp; loops and truncations far below --00).

## What the pilot did show
1. Terse targets damage generation behaviour: --00 finished 132 of 500 Greek responses by length (reference 60) and 82 looped (reference 27), typically an equation line repeated to the token limit. Worked solutions restore the reference behaviour (--01: 59 / 37; --02: 62 / 45). Terse maths targets should not be used again.
2. Accuracy is flat at 12–13% for every arm. One epoch over ~9k Greek worked solutions (with 57% replay) does not move MATH-500-el for this 8B model; neither does adding 1.4k Level-5 rows. The dose-check branch of the rule existed only for an inconclusive positive; a negative primary stops it.
3. English MATH-500 falls in every arm relative to the reference (largest for --02, −3.8 pp), so the Greek maths continuation is not free.

## Consequence
Under the frozen rule the negative outcome stops Phase C as planned (the 15 Sept pass 1-G4F6P1 with the new maths block) and calls for a write-up and a re-plan of the maths lane. The rest of the R4 candidate (correcting v2, the English maths block, the personality overlays, the Krikri-suite and GreekMMLU protocol work) is unaffected by this result but was scheduled inside the same pass.

## Options for the re-plan (owner decision)
A. Run the 15 Sept pass without a Greek maths block (correcting v2 + the other R4 changes on the incumbent recipe); keep --01's worked solutions as a small behaviour-repair block only if a later screen justifies it. Cheapest (≈7 nh as planned), gives the retention/GreekMMLU/Krikri-suite numbers the checklist needs.
B. Dose test before deciding: continue --01 for one more epoch over the maths blocks only (≈1 nh) and re-read MATH-500-el; the plan reserved this only for the inconclusive branch, so it would be an explicit override.
C. Change the maths lever: English-first (the published MATH/GSM solutions already in F6) with Greek problems only at inference, or larger and more diverse Greek maths data at the pass scale rather than a continuation; needs a new pilot design and Sol budget.
D. Deprioritise the maths objective for this round and spend the remaining CHF 38 on the evaluation programme (Krikri suite, native adapted rerun, MT audit) and the correcting-attribution arm.

Recommendation: A for tomorrow (it keeps the day useful and honours the rule), with B run in parallel only if the owner wants the dose question answered before dropping the lever.
