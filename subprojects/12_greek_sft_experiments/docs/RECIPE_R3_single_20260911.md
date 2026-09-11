# Recipe disclosure: round three, single-stage run from the base (draft 2026-09-11, numbers filled from the R3_single receipt)

Owner rule: every parameter tabled against the previous run, every change flagged, before any launch. Previous run = R2_stage1 (the broad mix, 1 epoch) followed by arm B (the Greek pass with personality ×4, 2 epochs, lr 1e-5). This run folds the Greek pass into one mix and trains once from the base, as decided after the identity ladder and endorsed by the completeness review as an experimental change to be compared against arm B.

## 1. Data (from data/arms/R3_single/receipt.json)

<!-- receipt-table -->
| block | unique train rows | copies | effective rows | rendered tokens | supervised tokens | dev rows | contaminated (dropped) | duplicates dropped (exact + same content) | masked context turns (unique rows) | change vs R2_stage1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| dolci_precise_if_20k | 4,116 | 1 | 4,116 | 2.3M | 1.3M | 41 | 79 | 0 | 0 | +5% tokens (same rule, deduplicated, re-decontaminated) |
| ifeval_like | 46,037 | 1 | 46,037 | 12.8M | 6.5M | 465 | 1332 | 142 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| openmath_gsm | 98,943 | 1 | 98,943 | 27.4M | 15.3M | 999 | 29 | 0 | 0 | +8% tokens (same rule, deduplicated, re-decontaminated) |
| nemotron_chat_a | 23,017 | 1 | 23,017 | 35.4M | 30.9M | 232 | 15 | 0 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| nemotron_chat_b | 23,262 | 1 | 23,262 | 36.3M | 31.7M | 234 | 15 | 0 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_chat | 3,009 | 1 | 3,009 | 1.1M | 0.8M | 30 | 1 | 0 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_code_algo_20k | 5,503 | 1 | 5,503 | 2.4M | 1.2M | 55 | 0 | 0 | 0 | +8% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_reasoning | 29,640 | 1 | 29,640 | 16.7M | 6.8M | 299 | 0 | 14 | 0 | +8% tokens (same rule, deduplicated, re-decontaminated) |
| puzzles | 9,391 | 1 | 9,391 | 3.6M | 0.6M | 94 | 0 | 1660 | 0 | -14% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_tooluse | 29,700 | 1 | 29,700 | 30.8M | 9.2M | 300 | 22 | 1 | 0 | +9% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_science | 6,537 | 1 | 6,537 | 6.0M | 3.9M | 66 | 0 | 1 | 0 | +6% tokens (same rule, deduplicated, re-decontaminated) |
| smoltalk2_multilingual | 20,207 | 1 | 20,207 | 11.1M | 8.1M | 204 | 0 | 1 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| dolci_safety | 6,174 | 1 | 6,174 | 1.8M | 1.1M | 62 | 0 | 22 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| greek_rewrite | 1,980 | 1 | 1,980 | 1.2M | 0.4M | 20 | 0 | 0 | 0 | -1% tokens (same rule, deduplicated, re-decontaminated) |
| greek_ours | 19,800 | 2 | 39,600 | 15.6M | 9.1M | 200 | 9 | 7924 | 0 | same weighting (×2) as stage 1; tokens differ by dedupe and re-decontamination |
| personality | 1,504 | 4 | 6,016 | 1.5M | 1.0M | 69 | 1 | 0 | 0 | new in the single mix (×4, one epoch; arm B gave ×4 for two epochs after stage 1) |
| greek_if | 29,773 | 1 | 29,773 | 11.1M | 6.0M | 300 | 0 | 0 | 0 | new block |
| greek_math | 14,070 | 1 | 14,070 | 3.2M | 1.3M | 142 | 3 | 0 | 0 | new block |
| convskills | 2,811 | 2 | 5,622 | 6.8M | 4.5M | 28 | 0 | 11 | 756 | new block |
| correcting | 565 | 2 | 1,130 | 1.5M | 0.9M | 5 | 0 | 0 | 431 | new block |

Totals: 376,039 unique train rows → 403,727 effective rows, 228.6M rendered tokens, 140.4M supervised tokens (61%); dev 3,845 rows (2.20M tokens) incl. the 69 personality holdout rows; train∩dev = 0 by id and 0 by content; rows without a supervised count: 0; post-assembly identity scan hits (exempt blocks: personality, convskills, correcting): 0; contamination drops 1,506 rows; duplicates dropped 9,776 (0 exact same-id, 9,776 same content under different ids); masked context turns 1,187 (unique rows). train.jsonl sha256 53cb197b1030ef19bbdc19358cdb9da0daece1170fdd395d0263ceda4fd95bca, dev.jsonl sha256 dcc82e988490bc490a5ce9fcd780ddfcc967cfca9f26f34746f5703e3ec18730. Projected training cost at the measured stage-1 rate (32.5M tokens per node-hour): **7.0 node-hours**; the evaluation battery about 4.3 on top.
<!-- /receipt-table -->
 Dev: the stage-1 dev fraction per block plus the same 69 personality rows held out in round two. Train/dev intersection asserted 0. Decontamination: 8-gram/13-gram containment of user turns against the evaluation cache (Greek IFEval, Greek MMLU, GSM8K, the English originals of MMLU/ARC/HellaSwag/TruthfulQA, Greek MGSM, MATH-500-el, XSTest-el, IFBench-el, MultiChallenge-el, native ASEP/medical/GPCR/DemosQA); NOT yet covered: the OYXOY sets (NLI, WiC, WSD, metaphor), which need their frozen copy from the cluster (certificate).

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
| data | 15 blocks, 334,383 rows, 197.9M tokens | 20 blocks, 403,727 effective rows, 228.6M tokens (140.4M supervised): the same 15 (deduplicated, re-decontaminated) + personality v3+v4 ×4 + Greek IF + Greek math + suite v2 ×2 + correcting ×2 | CHANGE |
| personality dose | none in stage 1; the arm-B pass then presented 1,319 rows ×4 for 2 epochs = 10,552 presentations after stage 1 | 1,504 rows ×4 for 1 epoch = 6,016 presentations inside the single mix (each v3 row seen 4 times instead of 8, plus 192 v4 rows) | CHANGE — a reduced-exposure, changed-schedule experiment, not the ladder's dose; not raised to ×8 on purpose (repetition alone would not recreate the two-stage schedule) |
| seed | 42 | 42 | — |
| saves | every 750 steps, keep 2 | same | — |
| expected_train_tokens | 197,862,767 | 228,577,090 | CHANGE |

Projected cost at the measured stage-1 rate (32.5M tokens per node-hour): 7.0 node-hours for training; the evaluation battery is about 4.3 node-hours on top (owner decides whether the budget includes it).

## 3. Launch gates (completeness review)

| gate | status |
|---|---|
| G1 receipt: unique rows, exclusions, copies, rendered and supervised tokens, hashes, provenance; personality holdout excluded before weighting; train∩dev = ∅ | PASSED: data/arms/R3_single/receipt.json + ledger.json (train∩dev 0 by id and by content; 69 personality dev rows with hashes, none in train; per-block exclusion reasons; per-block hashes and export provenance; the invariants caught 1,077 exact and 9,776 same-content duplicates, 1,660 of them puzzles that round two trained on, and 98 dev rows whose content had a train twin before the fix) |
| G2 masking through the real pipeline | PASSED and bound to the final file: cluster/test_mask_pipeline.py on 40 rows sampled from data/arms/R3_single/train.jsonl (10 carrying masked turns; 8 packed sequences; 19 masked turns; every masked turn and its end marker at −100, every target and its stop token supervised, every row with a positive supervised count), dump docs/receipts_label_dump_g2_final.json; trainer cluster/sft_train.py at commit 1217cea4, transformers 5 / TRL 1.12 (Mac venv sfttrain), Apertus template from the arm-B tokenizer. Definition of `masked_context_turns` in the receipt: assistant turns with `train:false` among the UNIQUE rows taken (before replication and before the dev split): 226 planted + 205 rejected targets in the correcting set = 431; 756 = 378 S4 rows × 2 planted answers; personality rows carry no masked turns because all their assistant turns are ideal and supervised. |
| G3 final-snapshot decontamination | PASSED for the cached inventory: 1,519 contaminated rows dropped at assembly (ifeval_like 1,348 with the new IFBench-el/English originals in the cache); OYXOY NOT covered: the frozen native-suite example files are no longer on the cluster scratch (frozen_examples_v2 is empty; only prediction files remain) and the sets are not on the Hub, so their text cannot be checked before launch; risk judged low (dictionary-derived lexical/NLI judgments vs our chat/IF/math rows), logged as DATA_TODO 52 for a re-derivation from the OYXOY source before the next round |
| suite post-edit re-verification | PASSED: 3,284 of 3,437 (data/convskills/v2/reverify/manifest.json) |
| correcting post-edit gate | PASSED: 3,691 supervised turns, 1 demoted |
| dry run on the cluster (5% sample arm, DRY_RUN_OK) | pending the certificate |

## 4. Promotion criteria proposed (against arm B under identical serving settings)
GreekMMLU at least arm B minus 0.5 points (decontaminated subset, frozen fp32 scorer); Greek IFEval strict average at least arm B minus 1 point, both rescored with langdetect installed; Greek MGSM at least arm B; native suite macro-8 at least arm B minus 1 point (retention); identity probe: every contract fact still answered as written; XSTest-el: safe-request adequacy not below arm B and unsafe-request refusal not below arm B. Primary conversation endpoint: picky-user R1 on the frozen 120 profiles under identical serving settings (temperature 0.8, 300 tokens, vLLM): tail-copy rate lower and coherent-turn rate higher than arm B, each by more than the paired bootstrap 95% interval (dialogue-level resampling); secondary: standing-instruction persistence, self-observation accuracy, MultiChallenge-el pass rate on the frozen 262 usable items (ids in data/benchmarks_el/multichallenge/summary.json), IFBench-el, MATH-500-el primary 486. Pivotal conversation judgements: a blinded, order-randomised human adjudication of 60 dialogues by the owner before any promotion decision. Manifests, scorer versions, prompts and decoding are frozen before R3 results are inspected.

## 5. Launch sequence (runs only on the owner's go; nothing below has been executed)
1. `cscs-key sign` (owner) — the certificate is expired.
2. Transfer (tar-pipe, `-4`): `data/arms/R3_single/{train,dev}.jsonl` (about 1.1 GB), `cluster/configs/R3_single.yaml`, and the updated trainer `cluster/sft_train.py` (per-turn masking) → `$SCRATCH/sft_round1/`.
3. Gate: the 5% sample arm dry run on the login node (`dryrun_<arm>.sh`, as for R2_stage1: DRY_RUN_OK, token estimate within 2% of the receipt), then the 20-step probe on a debug workbench if the trainer changed (it did: masking) — one node, about 0.3 node-hours.
4. Preflight (`cluster/preflight.sh`) with the projected 7.0–8.8 node-hours against the cap the owner sets; then `cluster/train_sbatch.sh R3_single`.
5. After training: the evaluation battery (`cluster/full_battery.sh`) on the new checkpoint AND on arm B where missing (GreekMMLU, native suite, retention), plus the four Greek benchmarks on both, with langdetect installed for the IFEval rescoring.

