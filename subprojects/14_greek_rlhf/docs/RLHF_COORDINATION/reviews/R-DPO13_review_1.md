# R-DPO13 review — what I ran

Read-only local and Clariden audit; no jobs launched and no files changed.

I checked the saved/training/evaluation RoPE resolution, exact runtime environments, all 15 arm weight identities, tokenizer and generation configuration, parent repeat equality, 540 Global-MMLU comparability checks, 791 generated benchmark items, all 3,191 benchmark documents for textual contamination, MGSM item churn and length effects, and the official GreekMMLU receipts.

## One-line verdict

The repaired IFEval/MGSM gains are real under the frozen evaluation and are not explained by another RoPE or parent-baseline artefact. They are protocol-specific behavioral gains—not evidence of universal reasoning improvement—and three publication claims require correction.

## Point-by-point findings

| # | Finding | Support | Disposition |
|---|---|---|---|
| 1 | Repair reproduces the geometry used during training | Strong | Supported |
| 2 | Parent comparison is fair on generated lanes | Strong | Supported |
| 3 | Evaluated arms resolve to distinct intended weights | Strong, with provenance defects | Medium |
| 4 | No benchmark copying detected, but “no mathematics” is false | Strong | High |
| 5 | Stopping is equivalent; IFEval is partly length/cap mediated | Strong | Medium |
| 6 | MGSM churn is systematic, not extraction or truncation | Moderate–strong | Supported, mechanism unresolved |
| 7 | Official GreekMMLU regression is genuine | Strong | High |
| 8 | “IPO” arms did not train with IPO | Conclusive | High |

### 1. Did the repair give the arms a better model than they trained with?

No. The repair restores the geometry that Transformers 5.16.1 used during training.

Deciding evidence:

- Training used Transformers 5.16.1 in the recorded `sft5` environment.
- The parent’s legacy configuration specifies `rope_theta=500000` and Llama-3 scaling with factor 8.
- Arm checkpoints store the same values under `rope_parameters`.
- In the original training environment, the parent and an arm checkpoint produce the identical rotary `inv_freq` digest:

  `4ae228093081627907bb1abceaa696354a9d187a0202a20492a1105c1ade70e3`

- Every repaired frozen evaluation receipt records that same digest and effective theta 500,000.
- The deliberately misloaded control instead records digest `082aa1f8…` and theta 12,000,000.
- Apart from RoPE representation, the material raw-config differences were generation metadata: parent EOS `[2,68]` versus checkpoint `[68,2,68]`, Transformers version, and `use_cache`.

The compatibility conversion in [dpo01_frozen_rescore.sh](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_frozen_rescore.sh:152>) is therefore legitimate. It is not an evaluation upgrade beyond the trained model.

For the parent, both its native configuration and the repaired checkpoint-style representation resolve to the same geometry. The warning that `original_max_position_embeddings=8192` exceeds `max_position_embeddings=4096` is shared and not differential.

Strength: strong/conclusive for the configurations and environments examined.

### 2. Was the parent disadvantaged?

No evidence of disadvantage on IFEval or MGSM.

All parent and arm runs used:

- Tokenizer digest `acf4d5c6…`
- Chat-template digest `15622710…`
- Frozen prompt date `2026-09-19`
- BF16, batch size 16, deterministic generation
- Effective EOS set `{2,68}`, pad 3, BOS 1, `do_sample=false`, `num_beams=1`
- Identical prompt hashes and benchmark inputs

The raw EOS lists `[2,68]` and `[68,2,68]` are behaviorally equivalent: order and duplication do not change token-set stopping.

The same-weight parent comparison is stronger than score equality:

| Lane | Items | Prompt differences | Raw-response differences | Filtered-response differences | Metric differences |
|---|---:|---:|---:|---:|---:|
| MGSM | 250 | 0 | 0 | 0 | 0 |
| IFEval | 541 | 0 | 0 | 0 | 0 |

This substantiates the equality entry at [frozen_results.json](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/frozen_results.json:880>).

Global-MMLU-Lite is different: identical weights produced 51/2,400 predicted-correctness flips, balanced 25 gains against 26 losses, and a net score movement of −0.0417 pp. That is small relative to the reported +1.10/+1.49 pp standard-arm means, but Global results do have a measurable numerical-noise floor.

The parent’s `n=1` is not problematic for deterministic inference. It does not eliminate benchmark sampling uncertainty.

Strength: strong for generated lanes; moderate for small Global-MMLU differences.

### 3. Are the arms actually the intended arms?

Yes at the weight-content level.

- The 15 evaluated arm paths resolve to 15 distinct weight-content IDs.
- No trained arms share weights.
- Standard and anchored runs resolve to checkpoint 129; length-balanced runs resolve to checkpoint 105, matching their planned update counts.
- Saved trainer, train-data and dev-data hashes match the intended inputs.
- The deployed trainer hash recorded in the checkpoints matches the audited training script.

Two provenance defects remain:

1. Seven of 15 `run_receipt.json` files contain valid first JSON objects followed by trailing concatenated data. The deployed trainer let multiple ranks write the same receipt; the current code now guards this at [dpo_train.py](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/dpo_train.py:144>).

2. Arm 05’s current config hash does not match its receipt solely because the saved `run_name` still says arm 03. Its training log and receipt nevertheless agree on α=0.25, β=0.1, learning rate 2e-6, seed 42, and the intended data.

Neither defect identifies weight substitution, but both weaken standalone reproducibility.

Strength: strong for weight identity; medium auditability issue.

### 4. Contamination

I found no exact or near-verbatim benchmark contamination.

Across all 397 preference pairs and:

- 250 MGSM items,
- 541 IFEval items,
- 2,400 Global-MMLU-Lite documents,

there were zero normalized full-containment matches and zero shared contiguous sequences at 8, 13, or 20 tokens. This strongly excludes copied or lightly edited benchmark items, but cannot exclude abstract semantic overlap.

However, the premise that the data contain “no mathematics” is false.

The manifest explicitly records 66 `embedded_maths` examples—56 train and 10 development—at [manifest.json](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dpo01/manifest.json:74>). Dedicated mathematics tasks were removed, but embedded numerical reasoning was retained by the export logic. Examples include schedules, prices, wages, vouchers, quantities and explicit calculations.

The accurate description is:

> Dedicated mathematics tasks were excluded; 66 preference pairs retained embedded numerical or quantitative content.

The current “maths excluded” summary in [DPO01_TRAINING_PAIRS_20260918.md](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/DPO01_TRAINING_PAIRS_20260918.md:12>) is materially misleading.

Severity: High, because “math-free preference tuning improved mathematics” is not supportable.

### 5. Stopping and truncation

Stopping is equivalent. MGSM truncation does not explain the gain.

- MGSM permits 1,024 generated tokens and extracts the final numeric answer.
- Parent and all ten standard/anchored arms had zero responses at the output cap.
- Only two nonstandard runs had one capped response each, on the same item; both were wrong.
- No prompt approached the model’s context limit.
- Parent and arm 01 had the same mean MGSM response length: 121.1 tokens.
- On arm 01’s gained items, arm responses were on average 17.9 tokens longer than the parent’s. The MGSM gain is not a brevity/extraction shortcut.

IFEval does show a material length mechanism:

| IFEval measure | Parent | Arm 01 |
|---|---:|---:|
| Mean output tokens | 330.0 | 214.1 |
| Median | 147 | 118 |
| At/near 1,280-token cap | 81/541 | 26/541 |

Arm 01’s gains/losses split as follows:

- Neither response capped: 40 gains, 31 losses; net +9/454 = +1.98 pp.
- At least one response capped: 20 gains, 8 losses; net +12/87 = +13.79 pp.

Thus the +3.88 pp arm-01 IFEval gain is partly a learned concise-termination effect, consistent with chosen responses being shorter in 233/397 pairs. It is a legitimate improvement under this protocol, but not wholly improved instruction reasoning: approximately two points remain on the uncapped subset.

Severity: Medium.

### 6. Does MGSM churn look credible?

It looks like a systematic change in answer behavior, not a scoring or truncation artefact.

For arm 01:

- 48 gains, 31 losses
- Net +17/250 = +6.8 pp
- Only 4/48 gains had the gold number already present anywhere in the parent response
- Zero relevant output-cap events
- The individual paired sign test is suggestive, not conventionally decisive: `p≈0.071`

The changes replicate substantially across seeds:

| Group | Common gains across every seed | Common losses across every seed | Gain-set Jaccard | Loss-set Jaccard |
|---|---:|---:|---:|---:|
| Plain, 5 seeds | 30 | 14 | 0.646 | 0.594 |
| Anchored, 5 seeds | 35 | 15 | 0.702 | 0.609 |
| Balanced, 3 seeds | 40 | 18 | 0.717 | 0.662 |

Item-bootstrap 95% intervals for group-mean MGSM deltas were:

- Plain: +8.48 pp, `[+2.24,+14.72]`
- Anchored: +9.04 pp, `[+2.64,+15.36]`
- Length-balanced: +11.20 pp, `[+4.93,+17.47]`

Manual examples include both genuine arithmetic corrections and newly introduced arithmetic errors. That is consistent with changed solution behavior rather than answer-extraction leakage.

The mechanism is still unresolved. The retained quantitative pairs, preference-induced style/termination changes, and general representation movement are plausible explanations, but none is established causally.

Permissible: “MGSM exact match increased under the frozen protocol.”

Not permissible: “the models acquired substantially stronger general mathematical reasoning.”

Strength: moderate–strong for a real benchmark effect; weak for the proposed mechanism.

### 7. GreekMMLU contradiction

The regression is real, statistically stronger than the small absolute percentages suggest, and it prevents an “everything improved” conclusion.

Under the official GreekMMLU protocol—16,632 Greek items, no chat template, FP32 label likelihood:

| Arm | Δ accuracy | Gained | Lost | Paired p |
|---|---:|---:|---:|---:|
| Arm 01 | −0.4149 pp | 131 | 200 | 0.000177 |
| Arm 05 | −0.4329 pp | 114 | 186 | 0.000038 |
| β=10 mislabeled “IPO” seed 42 | −0.2585 pp | 98 | 141 | 0.00647 |

See [greekmmlu_official_paired.json](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/greekmmlu_official_paired.json:7>).

This does not invalidate IFEval or MGSM because the protocols measure different behaviors:

- GreekMMLU: Greek-only, no chat template, direct label likelihood.
- Global-MMLU-Lite: six non-Greek languages, chat-formatted BF16 evaluation.
- IFEval/MGSM: generated-text tasks with instruction framing.
- The DPO data are multilingual; 163/397 outputs are non-Greek.

The contradiction is therefore evidence of a task/language/protocol tradeoff, not proof that the repaired runs are corrupt. It decisively refutes broad claims of general or Greek-language capability improvement.

Severity: High.

### 8. Additional artefact: the “IPO” arms are not IPO

This is conclusive.

The configuration requests `loss_type: ipo` at [G4F6P1_DPO01_IPO42.yaml](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/configs/G4F6P1_DPO01_IPO42.yaml:20>), but the deployed trainer hardcodes:

`loss_type="sigmoid"`

at [dpo_train.py](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/dpo_train.py:114>).

Those two runs are anchored sigmoid DPO with β=10 and α=0.25. Their scores are real for their weights, but the “IPO β=10” experimental identity is false.

Severity: High.

## Other findings

### Medium — Global-MMLU guard and serialization defect

[frozen_results.py](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/frozen_results.py:108>) reads Global-MMLU-Lite directly instead of passing it through the advertised `compare()` gate, and group Global statistics are not serialized into `frozen_results.json`.

I independently ran all 15×36 expected comparisons: 540 passed and zero were refused. Therefore this is not a current numerical artefact, but the published artifact does not itself prove that fact.

### Low — “Between-seed SD” is not purely seed variance

Some seeds trained on different chat-template dates because training crossed midnight. Evaluation dates are frozen, but the training-date difference cannot be repaired retrospectively. Report these as across-run dispersion, not a clean estimate of seed-only variance.

## What can legitimately be published

A defensible headline is:

> After correcting a RoPE-loading incompatibility that materially understated all Transformers-5 checkpoints, all 15 DPO checkpoints outscored the parent on frozen Greek IFEval and MGSM generation. Mean gains were +1.94 to +5.48 pp on IFEval and +5.00 to +11.20 pp on MGSM. These are protocol-specific gains: official GreekMMLU declined by 0.26–0.43 pp, IFEval benefited partly from shorter outputs, and the β=10 runs used sigmoid DPO rather than IPO.

Do not claim:

- that the preference data contained no mathematics;
- that IPO was evaluated;
- that every benchmark or capability improved;
- that the result proves general mathematical-reasoning improvement;
- that each individual arm has independently significant improvement;
- that the models are unambiguously superior deployment replacements.

The earlier “serious mathematics regression” was an evaluation artefact. The repaired positive MGSM measurements are real observations, but their scientific interpretation remains narrower than the score table suggests.

## Ordered asks

1. Relabel the “IPO β=10” row as anchored sigmoid DPO β=10, or remove it from the objective comparison.
2. Correct all “maths excluded/no mathematics” wording to disclose the 66 embedded quantitative pairs.
3. Put the official GreekMMLU regression in the headline result, not only in limitations.
4. Describe the IFEval gain as partly output-length/termination mediated.
5. Repair the Global result builder so every lane passes the comparability gate and group statistics are serialized.
6. Preserve an audit appendix documenting the seven malformed receipts and arm 05’s stale `run_name`.
7. If a general reasoning claim is wanted, run a preregistered held-out quantitative benchmark and complete the official GreekMMLU matrix across all arms. The present results do not support that claim.

VERDICT: Repaired generated-lane gains are real, but protocol-specific and not a general capability improvement | BLOCKERS: 0 | HIGH: 3 | RESULT: real

