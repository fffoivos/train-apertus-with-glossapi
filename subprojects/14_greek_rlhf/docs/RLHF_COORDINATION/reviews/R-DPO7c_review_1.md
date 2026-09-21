**R-DPO7c — conclusions review, 19 September 2026**

Read the four R-DPO7 reviews, R-DPO6 and its response, the generator and rendered HTML, all four named JSON bundles, and the 66 local GreekMMLU prediction files. Recomputed scorecard summaries, the sign tally, and paired GreekMMLU statistics. Through read-only SSH, checked the four completed full-benchmark prediction files, paired IFEval/MGSM samples, recorded prompts, and IPO trainer states. No files changed or evaluations launched.

The prior reviews are qualified audits, not blanket certification. Their unresolved identity and completion findings remain constraints; the counts below concern this review’s findings.

**HOLD: the page over-withdraws GreekMMLU, mistakes an unresolved anchor benefit for no benefit, and contains a newly verified prompt-date confound that prevents interpreting the 2×2 as a configuration interaction.**

**Findings, most severe first**

**1. BLOCKER — The “completed 2×2” changes the prompt date in a crossed pattern. It does not isolate configuration.**

The actual IFEval cells are:

| Weights | Parent configuration: correct / 541; prompt date | Checkpoint configuration: correct / 541; prompt date |
|---|---:|---:|
| Parent | 335; September 18 | 326; September 19 |
| Plain | 321; September 19 | 334; September 18 |
| Anchored | 326; September 19 | 336; September 18 |

The date is text supplied to the model: `Current date: 2026-09-18` versus `Current date: 2026-09-19`. This difference occurs in **541/541 IFEval prompts and 250/250 MGSM prompts** in each affected comparison. Normalizing only that date leaves **zero other prompt differences**; the generation arguments and benchmark documents match.

Consequently, the reported **+1.85/−1.66 pp** and **+1.48/−2.59 pp** contrasts change weights **and prompt text**. The resulting differences-in-differences, **3.51 and 4.07 pp**, cannot be attributed uniquely to configuration–weight interaction. The date contribution has not been measured.

This also qualifies the claimed parent configuration penalties of **−1.66 pp IFEval and −2.40 pp MGSM**. Those comparisons change the date too.

The problem extends beyond these six cells:

- Standard-arm seeds 42–43 use September 18; seeds 44–46 use September 19.
- All balanced and IPO runs use September 19.
- The inspected Global-MMLU-Lite likelihood prompts also contain the changing date. Absence of generation does not remove this prompt difference.

**Permissible wording:** “The recorded evaluation conditions produce opposite IFEval contrasts. A changing system-prompt date prevents identifying a configuration interaction or a training effect under either configuration.”

Freeze the rendered prompt and complete the matched comparisons before restoring the causal wording in [§7](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:575). Retain every measured score.

**2. HIGH — IPO is not an untrained control; its GreekMMLU improvement cannot establish that training did not cause the improvement.**

Both IPO trainer states record **129/129 optimizer steps and epoch 3.0**. The **2.0% and 2.6%** figures describe attainment of a *dev-separation target*, not the fraction of training completed or the magnitude of parameter change. Its configured objective also includes `chosen_nll_alpha: 0.25`.

The page correctly recognizes failed generalization as a possible explanation in §12, then contradicts that distinction by repeatedly calling IPO an arm that “did not train.”

Independent pairing on the **16,382 items outside the previously observed slice** gives:

| Checkpoint | Wrong → right | Right → wrong | Accuracy change | Exact McNemar p |
|---|---:|---:|---:|---:|
| Plain | 602 | 530 | **+0.4395 pp** | **0.03479** |
| Anchored | 594 | 535 | **+0.3602 pp** | **0.08427** |
| IPO42 | 606 | 521 | **+0.5189 pp** | **0.01231** |

These are unadjusted item-level tests for individual checkpoints, not independent training replications. A three-comparison Holm adjustment would leave only IPO below 0.05. Nevertheless, the positive fixed-set score differences are measured facts regardless of significance thresholds.

The clean held-out population gives the same direction: **+0.4587/+0.3833/+0.5529 pp** on **15,916 items**.

Therefore:

- Withdrawing **“+2 pp of Greek knowledge”** is justified.
- Withdrawing the **observed +2 pp on the selected 250-item slice** is unjustified. Those three checkpoints each answer **149 versus 144** correctly.
- Acknowledging the smaller held-out improvement is necessary.
- Declining to claim *established preference-specific knowledge acquisition* is reasonable.
- Declaring it **not attributable to preference learning**, or something **“any perturbation” produces**, is unsupported. No untrained round-trip or arbitrary-perturbation control was measured.

There is a straightforward training-effect interpretation: different objectives can produce a common beneficial change without achieving the IPO dev gate. The evidence does not distinguish that explanation from other changes shared by the training/export pipeline.

IPO has the highest held-out **point estimate**. Its advantage over plain is only **13 items, p=0.428**; over anchored, **26 items, p=0.062**. It ties the other two on the 250 slice. This does not establish IPO superiority.

**Permissible wording:** “Three completed trained checkpoints improve custom-full-text GreekMMLU accuracy by 0.36–0.52 pp on previously unexamined items. The improvement’s mechanism and preference specificity remain unresolved. The original +2 pp remains a slice-specific observation.”

Replace the categorical withdrawal and arbitrary-perturbation explanation in [§10](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:606).

**3. HIGH — “MGSM damage is real while the IFEval gain is not” applies unequal evidentiary standards.**

For the anchored checkpoint, the two reported MGSM deficits are indeed **−16/250 = −6.40 pp**. But their paired counts are:

| Recorded comparison | Gained / lost | Exact McNemar p |
|---|---:|---:|
| Checkpoint configuration column | 37 / 53 | **0.1133** |
| Parent configuration column | 39 / 55 | **0.1214** |

If non-significant paired tests invalidate the GreekMMLU observation, they would invalidate these MGSM observations too. That is the wrong treatment of both: the observed differences remain, while generalization and attribution require qualification.

The two columns reuse the same checkpoint and questions; they are not independent replications. Equal net losses do not demonstrate equal error mechanisms, universal configuration invariance, or damage specifically to mathematical reasoning. The date confound further prevents the claimed isolation of a weight effect.

There **is** useful corroborating negative evidence. Restricting standard arms to September 19 prompts and comparing against the September 19 checkpoint-config parent gives:

- Plain, three seeds: **34.80% versus 42.40%, −7.60 pp**.
- Anchored, three seeds: **36.27% versus 42.40%, −6.13 pp**.

That supports retaining a serious observed MGSM regression. It does not support [§7’s “survives any choice of configuration”](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:580).

**Permissible wording:** “MGSM accuracy is consistently lower in the measured standard-arm runs, including comparisons matched on configuration and prompt date. Its error mechanism and robustness to other serving conditions remain unestablished.”

Also replace “worse on every lane we can measure” with the precisely named measurements. GreekMMLU is positive, and additional benchmark columns contain positive observations.

**4. HIGH — §14 turns an inconclusive alpha comparison into demonstrated equivalence and a causal mechanism conclusion.**

The deciding result is **+0.70 pp, 95% run-bootstrap interval [−0.52, +1.77]**. This does not establish that the anchor “demonstrably does not change” benchmark outcomes.

There is another mismatch: the five-seed comparison tests **α=0 versus α=0.25**, whereas α=0.25 still leaves **−4.77 nats** of held-out chosen displacement. The setting that removes displacement is **α=1.0, +0.49 nats**, outside that replicated contrast.

Thus the experiment does not establish that removing displacement fails to improve benchmarks, or that displacement was not a binding constraint.

**Permissible wording:** “The measured alpha sweep changes held-out displacement monotonically. The replicated α=0.25 comparison does not establish a benchmark advantage; its effect remains unresolved.”

Keep the ranking withdrawn; remove the equivalence and “not binding” conclusions from [§14](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:673).

**5. HIGH — The rendered artifact omits the new evidence, and both versions misstate verification status.**

The supplied [HTML](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_CURVES_20260918.html) does **not** contain the generator’s full-benchmark section. It also omits the generator’s explicit “two checkpoints, one run each” qualification.

Both versions still say that nothing has been independently recomputed. That is false after R-DPO7a’s numerical checks and R-DPO7b2’s examination of **66,528 full-run prediction rows**, quite apart from this review. Independent numerical verification and unresolved pipeline certification must be reported separately.

The full-benchmark section also needs an explicit **4/8 models completed: parent plus three arms** label. Full item coverage is not full model or seed coverage.

**Permissible wording:** “Selected calculations and completed prediction files have been independently checked. Remaining protocol and completion findings are tracked separately. Full GreekMMLU currently covers three trained checkpoints and their parent.”

Regenerate the HTML after the conclusions are corrected; do not republish the current render.

**6. MEDIUM — The balanced-arm trade is supported, but its exposure argument and population description need correction.**

The observed comparison is useful:

- MGSM: **40.80% versus 36.08%, +4.72 pp**.
- Global-MMLU-Lite: **53.61% versus 56.23%/56.70%, −2.62/−3.09 pp**.
- Every balanced MGSM run, **40.0–41.6%**, exceeds every standard-arm run, **32.4–38.4%**.

The MGSM advantage persists against September 19 standard runs: **+6.00 pp versus plain; +4.53 pp versus anchored**. It should not be withdrawn.

However, the subset is **274 of 343 training pairs**, with **54 separate dev pairs**, rather than 274 of 397 training pairs. Steps fall from **129 to 105**, or **18.6%**.

A different subset improving with fewer steps does not logically refute recovery with additional steps on a fixed dataset. Those comparisons change different things. Likewise, “instruction following holds” is a descriptive similarity, not demonstrated equivalence.

**Permissible wording:** “The selected subset shows an observed MGSM/multilingual trade-off. Length, example selection and training exposure remain confounded, with prompt-date comparability additionally requiring correction.”

**7. MEDIUM — The custom-protocol caveat permits internal score comparisons, not conclusions about knowledge acquisition or its absence.**

The **54.23% custom-full-text** parent score and reported **~69.4% official-label** reference make protocol dependence consequential. Consistent custom scoring supports comparisons of those recorded custom scores. It does not establish that either their improvement or lack of improvement transfers to official-label scoring or broader Greek knowledge.

The executed 250-item sample also had **0/100 overlap** with the frozen screen IDs and included **7 contaminated items**. Describe it explicitly as an adaptive diagnostic. The held-out clean analysis is a valuable check and should remain visible.

**Permissible wording:** “These are internally comparable custom-full-text diagnostic scores. Their relationship to official GreekMMLU performance and broader knowledge has not been established.”

**Disposition of all twelve table entries**

| # | Published disposition | Adjudication | Deciding evidence and permissible conclusion |
|---|---|---|---|
| 1 | Alpha 0.25 best — withdrawn | **Supported** | **+0.70 [−0.52,+1.77] pp** does not establish superiority. Preserve the estimated advantage and uncertainty. |
| 2 | Total update governs damage — mechanism withdrawn | **Supported** | **21 dependent checkpoints** and nominal `lr × steps` do not identify a governing mechanism. Retain exploratory associations. |
| 3 | Enough movement recovers parent — not demonstrated | **Supported** | Four endpoints span **3.51 pp**; mean contrasts are **−0.97/+0.69 pp** under the two recorded baselines. Neither recovery nor equivalence is established. |
| 4 | Length mechanism — confounded | **Supported** | **+4.72 pp MGSM**, but **274 versus 343 pairs; 105 versus 129 steps**. Preserve the subset result; do not identify length as its cause. |
| 5 | Envelope damaged, content intact — withdrawn | **Supported** | No error decomposition separates extraction, formatting, truncation and reasoning. |
| 6 | GreekMMLU +2 pp — withdrawn | **Understated** | **149 versus 144/250** remains true; held-out gains are **+0.36–0.52 pp**. Withdraw broad knowledge attribution, not the observations. |
| 7 | IPO falsifies displacement hypothesis — inconclusive | **Supported** | Dev separation **0.0010/0.0013 versus 0.0500** misses the gate. This does not make IPO untrained. |
| 8 | Served signs — 35/8/2, descriptive | **Supported** | Independently reproduced **35 positive, 8 negative, 2 tied** across 45 cells. Retain as a tally of the recorded evaluations, not independent evidence of deployment benefit. |
| 9 | Configuration confound survives as interaction | **Wrong as an identified interaction** | The prompt date crosses the factorial cells. Configuration and date effects are not separated. |
| 10 | IFEval gain reverses by configuration | **Overstated** | **+1.85/+1.48 versus −1.66/−2.59 pp** is correct arithmetic for differing conditions. Pure configuration dependence is unresolved. |
| 11 | MGSM damage survives | **Overstated** | Negative observed scores survive, including same-date comparisons. **−6.40 pp twice** does not establish universal invariance or reasoning damage. |
| 12 | Held-out displacement and anchor control survive | **Supported, descriptively** | The sweep **−11.22, −8.29, −4.77, −2.38, +0.49 nats** is a substantive finding for the measured runs. It does not establish downstream benefit or lack of benefit. |

**What is correct and must not change**

Retain the corrected six-language Global-MMLU-Lite aggregation, all unfavorable runs, the IPO gate, separation of seed variation from item uncertainty, and the balanced arm’s multilingual trade-off.

Retain the small positive GreekMMLU observations. Shared flips and low seed variation describe reproducibility among these models; they neither establish broad precision nor prove that the benchmark cannot register improvement. The **235 unchanged items** are an observation about the tested models, not an intrinsic benchmark ceiling.

“No demonstrated general replacement for the parent” remains a fair release judgment. **“Nothing shippable for any purpose”** requires application-specific tolerances that are absent here. **“Only instrumentation remains”** understates the round: it also produced measured likelihood control, a promising subset trade-off, observed regressions, and a small positive custom GreekMMLU result with unresolved attribution. “No improvement survives on any benchmark” should be removed.

The specific worry is substantiated: several passages replace unsupported positive conclusions with unsupported negative ones. That is an evidentiary error; the data cannot establish the author’s motivation.

**Ordered asks**

1. **Freeze the actual rendered prompts and repair the configuration comparison.** Existing September 19 controls can be retained if matching is verified; evaluate the missing same-date counterparts. Until then, remove claims of isolated configuration interaction and deployment reversal.
2. **Restore the GreekMMLU observations.** Publish gained/lost counts, held-out raw and clean results, uncertainty, and 4/8 model coverage. Remove “did not train” and “any perturbation.”
3. **Apply the same standards to positive and negative outcomes.** Retain observed MGSM regressions; narrow the claims about reasoning, configuration invariance and “every lane.”
4. **Remove the alpha-equivalence conclusion.** Separate measured displacement control from unresolved benchmark benefit.
5. **Correct the balanced-subset denominator, adaptive-protocol description and verification status; regenerate and inspect the HTML.** Preserve the prior reviews’ unresolved release constraints separately from verified numerical results.

VERDICT: HOLD—retain the measured gains and regressions; resolve the prompt-date confound and correct the over-withdrawals before republication | BLOCKERS: 1 | HIGH: 4