# R-DPO14 — corrected result and final conclusions

**The corrected benchmark gains are real and publishable; the page still needs three HIGH corrections before its conclusions stand.**

Read-only review; nothing launched or changed. I verified all **741 output hashes across 19 receipts**, reproduced the generated-lane group means and MGSM overlap statistics, confirmed identical parent-repeat responses, and rechecked the three official GreekMMLU comparisons.

**Claim-by-claim adjudication**

1. **“DPO round 1 worked”: supportable with an explicit benchmark scope.**

   All **15 reported checkpoints** outscore the parent on both frozen generated benchmarks. The corrected group means are supported:

   | Group | IFEval Δ pp | MGSM Δ pp | Global-MMLU-Lite Δ pp |
   |---|---:|---:|---:|
   | Plain | +4.03 | +8.48 | +1.10 |
   | Anchored | +3.96 | +9.04 | +1.49 |
   | Balanced subset | +5.48 | +11.20 | −0.19 |
   | Anchored sigmoid β=10 | +1.94 | +5.00 | +1.77 |

   “Worked on the frozen IFEval and MGSM protocols” is justified. “Produced a generally better Greek model” is not. These are **group-mean ranges**, not individual-checkpoint ranges or independently significant improvements for every checkpoint.

   The disposition table correctly withdraws the earlier large regressions and the blanket “nothing shippable” conclusion. Its IFEval mechanism row still overclaims.

2. **Does the page now tell the truth throughout? No.**

   Section 6 largely does. Sections 7–14 still contain active statements that contradict it, including unfinished re-scoring, unresolved MGSM damage, obsolete balanced-subset trade-offs, and an IPO experiment that supposedly ran but missed its gate. These are not all clearly quarantined historical quotations. Specific corrections follow below.

3. **MGSM: “exact match increased” is the right line, and no new experiment is required before publishing that number.**

   Arm 01 gains **48**, loses **31**, and improves **17/250 = 6.8 pp**; its individual paired test is **p=0.071**. The plain-group improvement is **+8.48 pp**, with the reported item-bootstrap interval **[+2.24,+14.72]**. Replication across training runs strengthens the observation, but the runs reuse the same 250 questions; they are not independent benchmark confirmations.

   A plausible mechanism worth naming is **preference-induced redistribution toward better existing solution behaviors**, potentially assisted by the retained quantitative examples. There are **56 embedded-quantitative training pairs**, plus **10 development pairs**. That is ordinary task-related exposure, not evidence of contamination or a demonstrated mechanism.

   Equal mean response lengths, absence of relevant truncation, and substantial replicated item changes weaken simple extraction/length explanations. However, finding the gold number somewhere in four parent responses identifies **four possible extraction-related cases**, not four proven extraction failures.

   For a broader reasoning claim, require a fresh, prospectively specified quantitative evaluation. For a causal quantitative-data claim, use a matched ablation of those 56 training pairs. Neither is a publication prerequisite for the present scoped result.

4. **GreekMMLU: a real adverse result that limits the headline without invalidating the generated gains.**

   The three evaluated checkpoints lose **69, 72 and 43 net items**: **−0.4149, −0.4329 and −0.2585 pp**. Holm-adjusted p-values are **0.000354, 0.000115 and 0.00647**.

   “Task/language/protocol trade-off” adequately describes the heterogeneous benchmark outcomes. It does **not identify which factor caused them**: language, task, prompting, scoring and precision differ together. Prefer “official GreekMMLU accuracy declined” over a mechanistic claim of lost Greek knowledge.

   These results concern **three of the fifteen checkpoints**, not all fifteen. The remaining matrix matters especially for selecting the balanced recipe. Its incompleteness does not suspend publication of the completed comparisons.

5. **IFEval: the cap split supports an association, not “half the gain is learned termination.”**

   For parent versus arm 01:

   | Stratum | Gains / losses | Within-stratum Δ | Contribution to overall Δ |
   |---|---:|---:|---:|
   | Neither response capped | 40 / 31 | +1.98 pp | +1.66 pp |
   | At least one capped | 20 / 8 | +13.79 pp | +2.22 pp |

   Thus **12/21 = 57% of the net improvement occurs in the cap-affected stratum**. That does not establish a 57% causal contribution from termination: stratum membership depends on the outputs themselves, and the analysis covers one checkpoint comparison.

   The uncapped **+9/454** is a legitimate positive observation, but **p=0.342**; it does not independently establish improved instruction compliance. Conversely, stopping appropriately can itself satisfy instructions. The page’s opposition between “stopping” and “complying” is unjustified.

6. **What the round produced: useful candidate recipes and a defensible reason to run round 2.**

   It produced repeatable gains on two generated benchmarks, a measured retention concern, and a surviving diagnostic showing that anchoring changes held-out likelihood displacement. That is substantive progress.

   The balanced subset has the **highest observed generated-lane means**, but its selection, length distribution and training exposure remain confounded. Anchoring α=0.25 has no established benchmark advantage; actual IPO remains untested. Round 2 should test transfer and candidate trade-offs against a declared objective, rather than assume a universally superior replacement has already emerged.

**Findings, most severe first**

1. **HIGH — Obsolete conclusions remain active after the corrected result.**  
   [docs/DPO01_CURVES_20260918.html:132](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:132)

   Line 132 says the matched re-run “has not been done”; line 148 leaves mathematics damage open pending re-scoring; line 215 calls official GreekMMLU the **only** correctly loaded comparison; line 226 says the only positive knowledge result disappeared and multilingual scores remain lower.

   Section 11, especially lines 232–235, still interprets the obsolete deficits. Corrected balanced-versus-plain/anchored MGSM differences are **+2.72/+2.16 pp**, and Global-MMLU differences **−1.29/−1.69 pp**, not the old roughly +5/−3 trade-off.

   Section 14’s old **+0.70 pp** anchoring contrast also needs explicit historical labeling or replacement: corrected IFEval is **−0.074 pp**, with a recomputed seed-paired bootstrap interval **[−0.518,+0.370]**.

   Fix the generator and rendered page together. A new correction banner does not resolve contradictory active prose.

2. **HIGH — Section 12 still presents nonexistent IPO evidence.**  
   [docs/DPO01_CURVES_20260918.html:240](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:240)

   Lines 241–244 retain the IPO target, unmet gate and β-gradient explanation despite section 6 correctly saying sigmoid ran. The conclusion is **“the intended IPO test was not executed,”** not “IPO was inconclusive because its gate failed.” Relabel the corresponding tables and interpretations throughout sections 8–10 as well.

3. **HIGH — The headline and disposition convert the cap association into a causal finding.**  
   [docs/DPO01_CURVES_20260918.html:114](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:114)

   “About half … is learned brevity,” its disposition-table equivalent, and line 257’s “learning to stop rather than to comply” exceed the evidence. Replace them with the **57% observed concentration**, scoped to arm 01, and describe termination as a plausible contributor.

4. **MEDIUM — MGSM corroboration is numerically overstated.**  
   [docs/DPO01_CURVES_20260918.html:117](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:117)

   Recomputed gain-set Jaccards are **0.646/0.702/0.717**; loss-set values are **0.594/0.609/0.662**. “0.65–0.72 on both” is false. The β=10 group is lower still, **0.533/0.375**. Also soften the four extraction cases as described above.

5. **MEDIUM — Dataset and range descriptions need correction.**  
   [docs/DPO01_CURVES_20260918.html:67](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:67)

   “Training on 397 Greek pairs” is inaccurate: **343 train, 54 dev**, with **204 training pairs labeled Greek**. At line 257, label the quoted improvement ranges as group means; individual-checkpoint ranges are **+1.48…+5.91 IFEval** and **+4.40…+13.20 MGSM**. Line 108’s claim that the parent artefact exceeds *all* previously reported damage is also false: **7.63 < 8.4** on Global-MMLU and **9.60 < 9.8** on MGSM.

6. **MEDIUM — The Global-MMLU builder is not fully fail-closed.**  
   [cluster/eval_jobs/frozen_results.py:55](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/frozen_results.py:55)

   A refused leaf is skipped; surviving leaves can still produce an aggregate, which line 130 accepts. Missing subject leaves are not comprehensively rejected either. The current **zero-refusal** result remains usable, but the advertised guarantee requires suppressing incomplete aggregates and checking the complete expected leaf population.

7. **MEDIUM — The ledger still overinterprets one repeat.**  
   [docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:14](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:14)

   **51/2,400 changed Global-MMLU items** in one same-weight repeat demonstrates numerical sensitivity. It does not establish that “roughly half” of parent–arm churn is numerical, or that generated lanes have universally zero noise. The opening progress status is also stale.

8. **MEDIUM — Section 14 conflates this anchor with DPO-Positive.**  
   [docs/DPO01_CURVES_20260918.html:262](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html:262)

   This implementation adds chosen NLL to the loss. DPOP uses a reference-relative, one-sided penalty **inside the log-sigmoid**. Describe a related motivation, not the same objective or a guarantee that chosen likelihood stays high. [Pal et al., §4](https://arxiv.org/html/2402.13228v2#S4)

**Permissible headline**

> **Corrected DPO round 1 improves frozen Greek IFEval and MGSM scores, with an official GreekMMLU trade-off.** All 15 evaluated checkpoints outperform the parent on both generated benchmarks; group-mean gains are +1.94–5.48 and +5.00–11.20 pp. The three checkpoints evaluated on official GreekMMLU decline by 0.26–0.43 pp. Broader reasoning improvement and the contribution of shorter outputs remain unresolved.

**Ordered asks**

1. Close the three HIGH findings in the generator and rendered HTML; explicitly archive obsolete analyses.
2. Publish the corrected measurements with the scoped headline. **Do not require another experiment or an explanation of MGSM’s mechanism first.**
3. Log the MEDIUM findings; repair the aggregation behavior before reusing it for another results matrix.
4. Incorporate the already-running official GreekMMLU matrix before selecting a replacement or declaring a winning recipe.
5. For round 2, prioritize fresh quantitative evaluation, matched subset/exposure controls, and cap-sensitivity analysis. Run actual IPO only if that hypothesis remains decision-relevant.

VERDICT: Corrected gains are real and publishable; the page requires three bounded claim corrections | BLOCKERS: 0 | HIGH: 3