# What I ran

Read-only audit only; no jobs or inference launched.

- Reviewed the GreekMMLU scorer and calibration code.
- Recomputed published calibration, five-fold out-of-fold calibration, choice-count-stratified variants, common-parent calibration, probability-marginal variants, paired differences, and confidence intervals from the saved 16,632-item score vectors.
- Audited the Clariden `frozen/` and `cap3500/` receipts, manifests, run logs, and per-item IFEval JSONL files for all three models.
- Re-tokenized the saved IFEval outputs with the frozen tokenizer and compared prompts, responses, and all four stored metrics item by item.

**One-line verdict:** Q4’s label-shift mechanism is plausible, but “knowledge cost is zero” is not established; Q2’s rerun is genuine and rules out score sensitivity to raising the cap from 1,280 to 3,500, not output-length effects in general.

## Q4 findings

### BLOCKER — “Greek knowledge was never lost” does not follow

The official-label deficit remains a real performance deficit under GreekMMLU as posed: the arms are worse at selecting Α/Β/Γ/Δ. Applying a model-specific decision-rule correction defines a different evaluator; it does not retroactively make the raw capability loss unreal.

Neither alternative establishes a latent “true knowledge” quantity:

- The calibrated result shows that model-specific position-score centering removes the observed deficit.
- The full-text result shows that another scorer does not detect the same deficit.
- Failure to reject a difference—including Holm-adjusted `p=1.0`—is not evidence of exact equality. The paired 95% intervals for the full-text deltas are approximately:

| Arm | Delta | Paired 95% CI |
|---|---:|---:|
| arm01 | −0.036 pp | [−0.300, +0.228] |
| arm05 | +0.024 pp | [−0.242, +0.290] |
| armBAL | −0.090 pp | [−0.292, +0.112] |

No equivalence margin was predeclared. Those data support “no detectable deficit under this alternative scorer,” not “zero knowledge cost.”

### HIGH — the calibration is defensible batch calibration, but the causal reading is too strong

Canonical contextual calibration estimates bias from content-free inputs such as `N/A`; the present code instead estimates four model-specific offsets from the evaluation inputs themselves. [Zhao et al.](https://arxiv.org/abs/2102.09690) define the former. Using the unlabeled test batch is nevertheless a recognized transductive approach—Batch Calibration explicitly permits computing a correction after seeing all test inputs—so same-set estimation is not automatically invalid or gold leakage. [Zhou et al.](https://arxiv.org/html/2309.17249)

The five-fold check shows that in-sample fitting is not driving the result:

| Calibration variant | arm01 | arm05 | armBAL |
|---|---:|---:|---:|
| Published model-specific centering | +0.036 pp | +0.060 pp | +0.006 pp |
| Five-fold out-of-fold centering | +0.030 pp | +0.036 pp | 0.000 pp |
| Out-of-fold, stratified by 2/3/4 choices | +0.012 pp | +0.042 pp | +0.048 pp |

So a held-out split does not materially change this estimator’s answer.

But three qualifications matter:

1. [label_calibration.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/label_calibration.py:10) calls the procedure contextual calibration and describes two estimators, while the implementation reports only subtraction of each position’s mean log-score. It should be named model-specific batch log-score centering.

2. The dataset mixes 3,152 two-choice, 3,478 three-choice, and 10,002 four-choice questions. The published offsets therefore estimate A/B, C, and D from different item populations. Stratification happens not to change the conclusion, but it belongs in the primary analysis.

3. The result is estimator-dependent. A literal probability-marginal implementation of the documented “divide by the marginal” formula, cross-fitted within choice-count strata, leaves deficits of −0.234, −0.216, and −0.126 pp. Applying one common parent-derived correction likewise leaves −0.162, −0.247, and −0.150 pp. Model-specific centering is doing material comparative work.

Calibration is not guaranteed to improve accuracy, because it never uses gold labels. But “the arms improve more because they have more bias” is not independent validation either: each arm receives the transformation that removes its own mean positional shift. The observation is consistent with that mechanism, not proof of it.

A content-free estimate could change the result; it cannot be recovered from the stored score vectors and would require new inference, which I did not launch. It is also not automatically superior: the Batch Calibration paper documents failure cases for content-free dummy inputs.

### HIGH — the content scorer is not a clean or independent intervention

The claim that it changes “only the scoring form” is false in code:

- `official_label` uses `official_prompt(row)`.
- `custom_full_text` uses the different `old_prompt(row)`.
- One ranks bare letters; the other ranks space-prefixed answer strings by mean token log-probability.

See [greekmmlu_official.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/greekmmlu_official.py:46) and its protocol branch at [line 124](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/greekmmlu_official.py:124).

Thus the runs match on items, weights, environment, and dataset hash, but differ in prompt wording, subject framing, answer cue, continuation representation, and ranking statistic. Their absolute parent accuracies—54.28% versus 69.41%—also make clear that they are substantially different instruments.

The run is computationally separate from calibration, but not logically independent evidence for “knowledge unchanged.” Both arguments assume that performance after removing the label interface is a valid proxy for latent knowledge.

## Q2 findings

### Run authenticity: strong

Zero prompt-level flips across three models is credible, not evidence of output reuse.

The receipts match across caps on weights, frozen tokenizer and chat template, date, geometry, model configuration, and greedy generation settings; only the cap differs. The 3,500-token logs record fresh generation of all 791 IFEval+MGSM requests.

Per-item comparison found:

| Model | Byte-identical | Extended | Every old response a prefix of new |
|---|---:|---:|---:|
| parent | 458 | 83 | yes |
| arm01 | 514 | 27 | yes |
| armBAL | 514 | 27 | yes |

That is precisely the expected fingerprint of deterministic decoding: naturally terminated outputs reproduce byte-for-byte, while cap-affected outputs continue from the exact former prefix. Sample-file hashes also differ, and the parent’s mean output independently reproduces 329.99 → 661.32 tokens.

Prompt hashes and rendered prompt text match itemwise; the longest prompt is 509 tokens.

### HIGH — “the cap is irrelevant” is broader than the experiment

The primary IFEval result is solid:

- Parent: 326/541 at both caps.
- arm01: 347/541 at both caps, hence +3.88 pp at both caps.
- armBAL: 357/541 at both caps, hence +5.73 pp at both caps.
- Zero prompt-level strict pass/fail flips for every model.

However:

- Of the 83 extended parent outputs, 78 still re-tokenize to 3,500 tokens.
- For each arm, 25 of the 27 extended outputs still reach 3,500.
- Therefore the experiment usually raises the truncation point; it does not observe natural completion.
- “Not one item changed outcome” is true only for the headline prompt-level outcomes. Parent item 95 and arm01 item 161 changed instruction-level strict and loose results, while remaining prompt-level failures.

The result supports: “The 1,280 cutoff is not what produces the measured prompt-level gap within the feasible extension to 3,500.” It does not support an unrestricted “the cap is irrelevant.”

Yes, failure can be correlated with length without being caused by length. Nontermination, repetition, verbosity, or failure to plan around constraints can simultaneously produce long responses and IFEval failures. The 57% concentration is then an association with that behavioral phenotype. The controlled cap change shows that merely supplying another 2,220 tokens does not repair it.

## Permissible wording

### Q4

> Official bare-label GreekMMLU falls by 0.32–0.43 pp after preference training. The deficit is protocol-sensitive and is consistent with a model-specific label-position score shift: it disappears under model-specific batch log-score centering, including five-fold out-of-fold estimation, and is not detected by a separate custom full-text scorer. These analyses do not establish zero Greek-knowledge loss; the custom scorer also changes the prompt, and the raw official-label degradation remains a real multiple-choice performance cost.

### Q2

> With prompts, weights, tokenizer, geometry, and greedy decoding fixed, increasing IFEval’s output allowance from 1,280 to 3,500 tokens caused zero prompt-level strict pass/fail flips for the parent, arm01, or armBAL; the +3.88 and +5.73 pp gaps were unchanged. This rules out sensitivity of the headline score to the 1,280-token cutoff within the tested range. Most extended responses still reached 3,500, so unrestricted-length behavior remains unresolved, and cap-affected status may mark a correlated nontermination or compliance failure.

## Ordered asks

1. **BLOCKER:** Remove “Greek knowledge did not go down,” “label-position artefact,” and “knowledge cost is zero” from [the headline and section 10](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:673). Replace them with the qualified wording above.

2. **HIGH:** Rename the current method “model-specific batch log-score centering”; publish the out-of-fold and choice-count-stratified robustness rows; disclose the common-parent and probability-marginal sensitivity. Fix the unimplemented “two estimators” documentation.

3. **HIGH:** Stop calling full-text scoring a change of only answer representation or an independent confirmation. For a clean test, hold the official prompt byte-identical and change only the candidate continuation; stronger still, predefine a choice-permutation experiment.

4. **HIGH:** Replace “the output cap is irrelevant,” “not one item changed outcome,” and “not the cause of failing” at [the Q2 headline](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:672). Specify prompt-level strict outcome, the tested 1,280→3,500 range, the two instruction-level changes, and that most extended outputs still hit 3,500.

VERDICT: Q4 overclaims zero knowledge loss; Q2 is valid only as a 1,280-to-3,500 prompt-level robustness result | BLOCKERS: 1 | HIGH: 3 | Q4: unsound | Q2: qualified

