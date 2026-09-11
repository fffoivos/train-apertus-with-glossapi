# Recipe disclosure: round three, single-stage run from the base (draft 2026-09-11, numbers filled from the R3_single receipt)

Owner rule: every parameter tabled against the previous run, every change flagged, before any launch. Previous run = R2_stage1 (the broad mix, 1 epoch) followed by arm B (the Greek pass with personality ×4, 2 epochs, lr 1e-5). This run folds the Greek pass into one mix and trains once from the base, as decided after the identity ladder and endorsed by the completeness review as an experimental change to be compared against arm B.

## 1. Data (from data/arms/R3_single/receipt.json)

| block | unique train rows | copies | effective rows | rendered tokens | supervised tokens | change vs R2_stage1 |
|---|---:|---:|---:|---:|---:|---|
| (filled from the receipt) | | | | | | |

Totals: (filled). Dev: the stage-1 dev fraction per block plus the same 69 personality rows held out in round two. Train/dev intersection asserted 0. Decontamination: 8-gram/13-gram containment of user turns against the evaluation cache (Greek IFEval, Greek MMLU, GSM8K, the English originals of MMLU/ARC/HellaSwag/TruthfulQA, Greek MGSM, MATH-500-el, XSTest-el, IFBench-el, MultiChallenge-el, native ASEP/medical/GPCR/DemosQA); NOT yet covered: the OYXOY sets (NLI, WiC, WSD, metaphor), which need their frozen copy from the cluster (certificate).

## 2. Training parameters (cluster/configs/R3_single.yaml vs R2_stage1.yaml)

| parameter | R2_stage1 | R3_single | flag |
|---|---|---|---|
| base | fffoivos/apertus-8b-greek-cpt @ 18-avg-uniform5-tokens30B-50B | same | — |
| epochs | 1 | 1 | — |
| learning rate | 1e-5 | 1e-5 | — |
| schedule | cosine_with_min_lr, min_lr_rate 0.1, warmup 3% | same | — |
| weight decay / betas / grad clip | 0.0 / β2 0.99 / 1.0 | same | — |
| packing | BFD, max_length 4,096, padding-free | same | — |
| effective batch | 1 × 4 devices × 4 accumulation = 16 sequences | same | — |
| loss | assistant-only | assistant-only **plus per-turn `train:false` masking** (context turns of planted failures and suite S4 tics; verified through template+packing+collator on real rows, label dump docs/receipts_label_dump_g2_pilot.json) | CHANGE |
| data | 15 blocks, 334,383 rows, 197.9M tokens | 20 blocks: the same 15 + personality v3+v4 ×4 + Greek IF + Greek math + suite v2 ×2 + correcting ×2 (rows/tokens from the receipt) | CHANGE |
| personality dose | none in stage 1 (×4 in the later arm B pass, 2 epochs) | ×4 inside the single mix, 1 epoch | CHANGE (the ladder's dose, but spread over one epoch of the whole mix; the review calls this a provisional carry-over) |
| seed | 42 | 42 | — |
| saves | every 750 steps, keep 2 | same | — |
| expected_train_tokens | 197,862,767 | (receipt) | CHANGE |

Projected cost at the measured stage-1 rate (32.5M tokens per node-hour): (filled) node-hours for training; the evaluation battery is about 4.3 node-hours on top (owner decides whether the budget includes it).

## 3. Launch gates (completeness review)

| gate | status |
|---|---|
| G1 receipt: unique rows, exclusions, copies, rendered and supervised tokens, hashes, provenance; personality holdout excluded before weighting; train∩dev = ∅ | (filled from the receipt) |
| G2 masking through the real pipeline | PASSED (cluster/test_mask_pipeline.py on 40 real rows; 20 decoded examples attached) |
| G3 final-snapshot decontamination | (receipt contamination counts); OYXOY pending the cluster copy |
| suite post-edit re-verification | PASSED: 3,284 of 3,437 (data/convskills/v2/reverify/manifest.json) |
| correcting post-edit gate | PASSED: 3,691 supervised turns, 1 demoted |
| dry run on the cluster (5% sample arm, DRY_RUN_OK) | pending the certificate |

## 4. Promotion criteria proposed (against arm B under identical serving settings)
GreekMMLU within 0.5 points of arm B; Greek IFEval strict average not more than 1 point below arm B; Greek MGSM not below arm B; improvement on the conversation instruments (picky-user R1 tail copy, coherence, standing-instruction persistence, self-observation) and on MultiChallenge-el; the four new benchmarks reported for both models.
