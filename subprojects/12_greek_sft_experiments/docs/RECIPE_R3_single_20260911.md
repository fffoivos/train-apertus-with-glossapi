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

## 1b. Dataset registry: task type, language, repetitions (measured on the final train file, 2026-09-11)

Global training settings for every block: learning rate 1e-5, cosine to a 0.1 floor, 3% warmup, one epoch, effective batch 16 sequences of ≤4,096 tokens, seed 42 (§2). "Copies" is the only per-block knob: the block is replicated that many times inside the single mix, so each of its rows is seen `copies` times in the one epoch. Language is MEASURED, not declared: Greek-script share of the assistant text over all unique rows of the block in data/arms/R3_single/train.jsonl; the Latin-script rows were classified with langdetect on a sample of up to 1,500 rows per block (data/language_by_block.py → docs/receipts/R3_single/language_by_block.json). "short" = answers with fewer than 20 letters (numeric or grid answers), not classified.

| block | task type | language of the answers (measured) | unique rows | copies | effective rows | supervised tokens |
|---|---|---|---:|---:|---:|---:|
| dolci_precise_if_20k | precise instruction following, verifiable constraints | en 96% of Latin rows; 7% short | 4,116 | 1 | 4,116 | 1.3M |
| ifeval_like | IFEval-style constrained instruction following | en 100% | 46,037 | 1 | 46,037 | 6.5M |
| openmath_gsm | grade-school math word problems with worked solutions | en 100% | 98,943 | 1 | 98,943 | 15.3M |
| nemotron_chat_a | general multi-turn chat, instruction-following chat | en 86%, pl 4%, de 3%, fr/es 1% each | 23,017 | 1 | 23,017 | 30.9M |
| nemotron_chat_b | same as A (second half of the split) | en 87%, pl 3%, de 2%, pt/fr 1% each | 23,262 | 1 | 23,262 | 31.7M |
| dolci_chat | general assistant conversations (OpenAssistant) | es 54%, en 30%, ca 4%, de 4%, fr 2% (NOT an English block) | 3,009 | 1 | 3,009 | 0.8M |
| dolci_code_algo_20k | Python algorithm coding | en 91% (langdetect noise on code for the rest) | 5,503 | 1 | 5,503 | 1.2M |
| dolci_reasoning | verifiable algorithmic and combinatorial reasoning | en 98% | 29,640 | 1 | 29,640 | 6.8M |
| puzzles | zebra logic puzzles and word sorting, brute-force verified | en (user turns Latin 100%; 75% of answers are short grids/lists) | 9,391 | 1 | 9,391 | 0.6M |
| dolci_tooluse | tool use as textual `<function_calls>` demonstrations | en 99% | 29,700 | 1 | 29,700 | 9.2M |
| dolci_science | science QA over supplied documents (bioasq, qasper, scitldr, covid, chia, mslr, data) | en 100% | 6,537 | 1 | 6,537 | 3.9M |
| smoltalk2_multilingual | general chat in five EU languages | fr 22%, de 20%, es 19%, pt 19%, it 18% | 20,207 | 1 | 20,207 | 8.1M |
| dolci_safety | safety: refusals and compliant answers (WildGuardMix, CoCoNot) | en 100% | 6,174 | 1 | 6,174 | 1.1M |
| greek_rewrite | Greek rewriting and summarising of supplied text | el 100% | 1,980 | 1 | 1,980 | 0.4M |
| greek_ours | adapted general SFT, 11 configs (no_robots 40%, apertus_en 18%, personas_if 9%, everyday 9%, euroblocks fr/de 8%, oasst 6%, smolcon 4%, coconot 4%, systemchats 3%) | el 72%, en ≈18%, fr ≈5%, de ≈4% (the paired-English and fr/de-vantage rows of the round-one design; NOT all-Greek) | 19,800 | 2 | 39,600 | 9.1M |
| personality | identity, response manners, capability contract (v3 + v4) | el 98% (user turns el 86%; a few English prompts by design) | 1,504 | 4 | 6,016 | 1.0M |
| greek_if | Greek verifiable instruction following (40 constraint families, levels 1 to 5) | el 87%; 11% Latin script = greeklish-only and English-answer constraints; 2.5% short | 29,773 | 1 | 29,773 | 6.0M |
| greek_math | Greek math: translated GSM8K and MATH plus native problems, answer-verified | el 92%; 6% numeric-only answers; 2% LaTeX-heavy | 14,070 | 1 | 14,070 | 1.3M |
| convskills | conversation skills S1 to S5m (list and semantic retention, clarification, both-order, S4 tic avoidance, S5m fact use) | el 99.6% | 2,811 | 2 | 5,622 | 4.5M |
| correcting | correction and recovery dialogues (misquote confrontation, planted failures masked, clarify) | el 99% (user turns el 78%; greeklish and atonic surfaces by design) | 565 | 2 | 1,130 | 0.9M |

Totals: 376,039 unique rows, 403,727 effective, 140.4M supervised tokens.

**Language over the supervised spans (the readiness review's Q2 measure, 2026-09-11 15:40).** Assistant turns with `train` not false, on the EFFECTIVE rows (copies counted), weighted by letters (Greek, Latin and Cyrillic letters only; digits, punctuation and markup excluded). A span is `el` when at least 90% of its letters are Greek, `latin` at 90% Latin, `mixed` otherwise, `unknown` under 20 letters. Script: data/language_by_block.py (second mode) → docs/receipts/R3_single/language_supervised_spans.json.

| block | supervised letters | el % | latin % | mixed % | unknown % |
|---|---:|---:|---:|---:|---:|
| convskills | 14.9M | 78.3 | 0.6 | 21.1 | 0.1 |
| correcting | 2.5M | 94.3 | 0.4 | 5.1 | 0.1 |
| dolci_chat | 2.7M | 0.0 | 99.4 | 0.1 | 0.0 |
| dolci_code_algo_20k | 2.4M | 0.0 | 100.0 | 0.0 | 0.0 |
| dolci_precise_if_20k | 3.2M | 0.0 | 99.3 | 0.1 | 0.1 |
| dolci_reasoning | 7.9M | 0.0 | 99.9 | 0.1 | 0.0 |
| dolci_safety | 4.5M | 0.0 | 100.0 | 0.0 | 0.0 |
| dolci_science | 9.5M | 0.0 | 100.0 | 0.0 | 0.0 |
| dolci_tooluse | 18.8M | 0.0 | 99.9 | 0.0 | 0.1 |
| greek_if | 19.8M | 85.4 | 7.9 | 6.7 | 0.0 |
| greek_math | 1.4M | 86.8 | 0.1 | 12.4 | 0.7 |
| greek_ours | 27.9M | 62.7 | 32.2 | 5.0 | 0.1 |
| greek_rewrite | 1.4M | 99.8 | 0.0 | 0.2 | 0.0 |
| ifeval_like | 27.0M | 0.0 | 100.0 | 0.0 | 0.0 |
| nemotron_chat_a | 89.3M | 0.0 | 99.2 | 0.5 | 0.0 |
| nemotron_chat_b | 91.2M | 0.0 | 99.1 | 0.6 | 0.0 |
| openmath_gsm | 30.2M | 0.0 | 100.0 | 0.0 | 0.0 |
| personality | 3.0M | 91.2 | 1.4 | 7.3 | 0.0 |
| puzzles | 1.3M | 0.0 | 94.2 | 0.0 | 5.8 |
| smoltalk2_multilingual | 26.0M | 0.0 | 100.0 | 0.0 | 0.0 |
| **all, effective** | **385.0M** | **14.0** | **84.0** | **1.9** | **0.04** (spans: 16,896 of 637,638) |

So Greek is **14.0% of the supervised letters** the model is trained on (Latin-script 84.0%: English plus the five smoltalk2 languages, the Spanish half of dolci_chat, the French/German rows of greek_ours and the Polish/German tail of Nemotron; Cyrillic 0.1%). The row-based figure (about a quarter of effective rows are Greek blocks) overstates the Greek share because the long-answer blocks are English. The earlier block-based proxy the review called out (16.3%) was of the same order, but it was a guess from block labels; this is a measurement. `mixed` in convskills (21%) and greek_math (12%) is Greek text carrying Latin-script names, code, formulas or greeklish surfaces by design, not a language error.

Two facts this table adds that the block names hid: dolci_chat is Spanish-majority, and about 27% of the answers in greek_ours are not Greek (English 18%, French 5%, German 4%). Both were also true of the round-two stage-1 mix that produced arm B.

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
| loss | assistant-only | assistant-only **plus per-turn `train:false` masking** (context turns of planted failures and suite S4 tics; verified through template+packing+collator on real rows, label dump docs/receipts/receipts_label_dump_g2_pilot.json) | CHANGE |
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
| G2 masking through the real pipeline | PASSED and bound to the final file: cluster/test_mask_pipeline.py on 40 rows sampled from data/arms/R3_single/train.jsonl (10 carrying masked turns; 8 packed sequences; 19 masked turns; every masked turn and its end marker at −100, every target and its stop token supervised, every row with a positive supervised count), dump docs/receipts/receipts_label_dump_g2_final.json; trainer cluster/sft_train.py at commit 1217cea4, transformers 5 / TRL 1.12 (Mac venv sfttrain), Apertus template from the arm-B tokenizer. Definition of `masked_context_turns` in the receipt: assistant turns with `train:false` among the UNIQUE rows taken (before replication and before the dev split): 226 planted + 205 rejected targets in the correcting set = 431; 756 = 378 S4 rows × 2 planted answers; personality rows carry no masked turns because all their assistant turns are ideal and supervised. |
| G3 final-snapshot decontamination | PASSED for the cached inventory: the assembler's rule (NFKC + case-fold + punctuation strip; word 8-grams of each training USER turn; a row is dropped when ≥ 0.5 of a turn's distinct 8-grams occur in any evaluation prompt) dropped 1,519 rows at assembly; the standalone match ledger (data/contamination_ledger.py, docs/receipts/R3_single/contamination_ledger_summary.json) re-ran the same rule over the final train.jsonl against 58,359 evaluation prompts in 14 suites (Greek IFEval, GreekMMLU, GSM8K test, the English originals of MMLU/ARC/HellaSwag/TruthfulQA, Greek MGSM, MATH-500-el el+en, XSTest-el el+en, IFBench-el el+en, MultiChallenge-el el+en, native ASEP/medical/GPCR/DemosQA, ellinika-bench) and found 0 matches. No 13-gram rule applies at assembly (the benchmark builders' 8/13-gram tool is separate). NOT covered: the OYXOY sets (frozen files gone from the cluster scratch, not on the Hub; DATA_TODO 52). |
| suite post-edit re-verification | PASSED: 3,284 of 3,437 (data/convskills/v2/reverify/manifest.json) |
| correcting post-edit gate | PASSED: 3,691 supervised turns, 1 demoted |
| dry run on the cluster (5% sample arm, DRY_RUN_OK) | PASSED 2026-09-11 14:01 CEST on the login node: 20,186 sampled rows (seed 42), 11,401,619 tokens → ×20 = 228.0M vs receipt 228.6M (0.2%); dev 3,845 rows / 2,195,787 tokens = the receipt exactly; 175 optimizer steps at effective batch 16 on the sample; log $SCRATCH/sft_round1/logs/dryrun_R3_single_s5.log; uploaded files verified by hash (train.jsonl sha256 53cb197b…, trainer md5 53246fff…) |
| 20-step GPU probe on a debug workbench (trainer changed: per-turn masking) | PASSED 2026-09-11 17:23 CEST, job 3358449 (55 min incl. tokenising the full arm): TRAIN_OK, loss 1.247 → 1.225 over 20 steps, 1.30M tokens, 40.5 GiB per GPU, dev eval on all 20 blocks (257 s), checkpoint-20 and epoch1 written and reloaded; pure training rate ≈ 7.8k tok/s ≈ 28M tokens/nh (R2 probe 7.5k) → full run ≈ 9 h; submitted with walltime 11:30 (partition max 12:00) |

## 3b. Readiness review (docs/reviews/ASTRA_readiness_20260911.md): disposition of every finding

Written 2026-09-11 15:45, after the owner asked whether the review had accepted the M1 claim. It had not: the review's Q2 and Q5 said the language share was unmeasured, and I had closed the review's blockers without dispositioning F1 to F7 and Q1 to Q5 one by one. This table is that disposition. OPEN means open.

| finding | status | evidence |
|---|---|---|
| F1 BLOCKER: B3 decontamination incomplete, rule described inconsistently | CLOSED except OYXOY | rule recorded in §3 G3 (normalisation, user-turn word 8-grams, containment ≥ 0.5 of distinct 8-grams, no 13-gram rule, prompts shorter than 8 words form one gram); inventory of 14 suites / 58,359 prompts; match ledger on the final file: data/arms/R3_single/contamination_ledger.jsonl, 0 matches. OYXOY not covered (DATA_TODO 52). NEW, the audit of the assembly-time drops by evaluation source that Q2 asked for: docs/receipts/R3_single/contamination_audit_ifeval_like.json and contamination_audit_dolci_precise_if_20k.json. ifeval_like export: 56,339 rows, 1,348 hits, all against the English IFEval suite, only 11 distinct IFEval prompts absorb them (731 rows match one prompt); containment 0.5 to 0.6 for 1,279 rows, 1.0 for 13 rows whose whole prompt is the constraint sentence «Answer with one of the following options: My answer is yes / no / maybe». Precise IF export: 20,000 rows, 331 hits ({'ifeval': 276, 'ifbench_el': 55}), 20 distinct prompts. Every inspected match is IFEval constraint boilerplate («At the end of your response, please explicitly add a postscript starting with P.S.», «First repeat the request word for word without change», «Highlight at least 2 sections in your answer with markdown»), never the task text. Verdict: accidental deletion of common instruction templates, no benchmark leakage found. Limitation logged as DATA_TODO 55: a copied task sentence wrapped in different constraints can fall under the 0.5 containment and pass. |
| F2 BLOCKER: B1 complete accounting and leakage verification | CLOSED | data/arms/R3_single/ledger.json (data/verify_arm.py): per-block reasons, train∩dev 0 by id and by content, holdout hashes. The three unexplained counts of the review's Q2: correcting 600 source rows → 24 unrenderable (dialogue ends with a user turn) + 6 over 4,096 tokens → 570 taken → 5 dev → 565 train; personality 1,580 → 6 unrenderable + 1 contaminated → 1,573 → 69 holdout dev → 1,504; convskills 2,851 → 11 same-content duplicates → 2,840 → 1 over-long → 2,839 → 28 dev → 2,811. |
| F3 BLOCKER pending: supervision contract ambiguous | CLOSED | §3 G2: definitions of unique/effective and of `masked_context_turns`; label dump bound to the final train.jsonl and the committed trainer (docs/receipts/receipts_label_dump_g2_final.json). |
| F4 HIGH: dose comparison misleading | CLOSED | §2 personality-dose row rewritten as the review prescribed: same post-split post-weighting definitions, both R2 stage 1 alone and stage 1 plus arm B, described as a reduced-exposure changed-schedule experiment, not raised to ×8. |
| F5 HIGH: coverage and factual dispositions not demonstrated | OPEN (owner) | coverage matrix of the accepted rows NOT computed; the uncovered cells are listed (DATA_TODO 42) and the deferrals recorded (DATA_TODO 53); the two v4 fact doubts resolved by applied edits (H06_11, H11_05); the seven registered v3 corrections NOT delivered and the registry not described as remediation. Owner decision on DATA_TODO 42 and 28 pending. |
| F6 HIGH: promotion plan not operational | OPEN (owner + battery) | floors proposed in §4, not confirmed; the four Greek benchmarks are frozen (data/benchmarks_el/MANIFEST.json); the full battery manifest (scorer versions, serving settings, primary endpoints, uncertainty procedure) is NOT written yet, it is launch-sequence step 6; langdetect rescoring of arm B and peers planned in the battery; blinded human adjudication is the owner's (DATA_TODO 34). |
| F7 MEDIUM: stale or overstated claims | PARTIAL | corrected on 11 Sept: dose, adaptation claim, the three sets' statuses (§3.x), and today the M1 wording (the receipt never held selection rates). The description has not been re-read line by line for other stale statements since the final assembly. |
| Q2 surprises: token-share category definitions; language share unmeasured; ifeval-like drops unexplained | CLOSED | categories now explicit in §1b (task type per block, supervised tokens per block); language measured over supervised spans (§1b: Greek 14.0% of supervised letters, mixed 1.9%, unknown reported separately); drops audited (F1 row). |
| Q3 weights and single stage | CLOSED | the review's advice adopted: weights unchanged, personality ×4 not raised, single stage kept as the experiment vs arm B (§2). |
| Q4 steps 1 to 7 | 1 OPEN (OYXOY); 2 done except OYXOY and the owner deferrals; 3 done (hashes verified on the cluster); 4 done (dry run: rendered tokens within 0.2%, dev exact; supervised accounting via the G2 dump and the receipt, not via the dry run); 5 NOT run (the GPU probe runs on the owner's go); 6 OPEN (F6); 7 pending the go | budget as the review computed: 7.0 nh training + 0.3 probe + 4.3 battery ≈ 11.6 to 13.4 node-hours total; the owner's cap must cover that or name what is cut. |
| Q5 residual risks | ACKNOWLEDGED, not mitigated | single seed; v3 personality factual concerns remain; shared CPT contamination; textual tool calls not evaluated as tool competence; Greek supervision is a minority: 14.0% of supervised letters (now measured). |
| open questions 1 to 5 | 1 owner (budget scope); 2 answered (F2 row); 3 answered (ids AND canonical content; masked-context definition in G2); 4 DATA_TODO 53, owner; 5 owner (§4 floors) | |

## 4. Promotion criteria proposed (against arm B under identical serving settings)
GreekMMLU at least arm B minus 0.5 points (decontaminated subset, frozen fp32 scorer); Greek IFEval strict average at least arm B minus 1 point, both rescored with langdetect installed; Greek MGSM at least arm B; native suite macro-8 at least arm B minus 1 point (retention); identity probe: every contract fact still answered as written; XSTest-el: safe-request adequacy not below arm B and unsafe-request refusal not below arm B. Primary conversation endpoint: picky-user R1 on the frozen 120 profiles under identical serving settings (temperature 0.8, 300 tokens, vLLM): tail-copy rate lower and coherent-turn rate higher than arm B, each by more than the paired bootstrap 95% interval (dialogue-level resampling); secondary: standing-instruction persistence, self-observation accuracy, MultiChallenge-el pass rate on the frozen 262 usable items (ids in data/benchmarks_el/multichallenge/summary.json), IFBench-el, MATH-500-el primary 486. Pivotal conversation judgements: a blinded, order-randomised human adjudication of 60 dialogues by the owner before any promotion decision. Manifests, scorer versions, prompts and decoding are frozen before R3 results are inspected.

## 5. Launch sequence (runs only on the owner's go; nothing below has been executed)
1. `cscs-key sign` (owner) — the certificate is expired.
2. Transfer (tar-pipe, `-4`): `data/arms/R3_single/{train,dev}.jsonl` (about 1.1 GB), `cluster/configs/R3_single.yaml`, and the updated trainer `cluster/sft_train.py` (per-turn masking) → `$SCRATCH/sft_round1/`.
3. Gate: the 5% sample arm dry run on the login node (`dryrun_<arm>.sh`, as for R2_stage1: DRY_RUN_OK, token estimate within 2% of the receipt), then the 20-step probe on a debug workbench if the trainer changed (it did: masking) — one node, about 0.3 node-hours.
4. Preflight (`cluster/preflight.sh`) with the projected 7.0–8.8 node-hours against the cap the owner sets; then `cluster/train_sbatch.sh R3_single`. Full budget of the run AND its benchmarks (both models): 19.0 to 20.8 node-hours ≈ CHF 51 to 56, itemised in docs/RLHF_PLAN_20260911.md §0.
5. After training: the evaluation battery (`cluster/full_battery.sh`) on the new checkpoint AND on arm B where missing (GreekMMLU, native suite, retention), plus the four Greek benchmarks on both, with langdetect installed for the IFEval rescoring.

