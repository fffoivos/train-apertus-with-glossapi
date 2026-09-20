# Brief: diagnose the R3_single post-training reversals — RECIPE AND SCHEDULE angle

You are one of two reviewers; the other one gets the paired transcripts and looping outputs. You get the recipe, the receipts, the numbers and our hypotheses. Task: explain why R3_single shows reversals against arm B instead of progress, rank the explanations by the evidence, say which of our queued tests discriminate between them, propose the missing test(s), and state what you would change in the next recipe. Be adversarial about OUR hypotheses (H1–H8 below): if the evidence does not support one, say so. Quote numbers. Distinguish what the data shows from what you infer. No web access; do not invent citations; mark literature claims [lit].

## The two models
- arm B (the incumbent): stage 1 = the broad mix (334k rows, 197.9M tokens, 15 blocks, one epoch, lr 1e-5 cosine) THEN a Greek pass from that checkpoint: personality v3 ×4 (5,276 rows) + greek_ours 19,800 + greek_rewrite 1,980 + 5% replay of every other block = 41,697 rows, TWO epochs, lr 1e-5 cosine.
- R3_single (the new run): ONE stage from the CPT base: the same 15 blocks (deduplicated, re-decontaminated) + personality v3+v4 ×4 (6,016 effective rows) + Greek IF 29,773 + Greek math 14,070 + conversation suite ×2 (5,622) + correcting set ×2 (1,130) = 403,727 effective rows, 228.6M rendered / 140.4M supervised tokens, one epoch, lr 1e-5 cosine to 0.1, warmup 3%, batch 16 × 4,096, seed 42, fp32 master weights + bf16 autocast, packing (BFD), assistant-only loss with per-turn masking of planted-failure context turns. Train loss 0.941 (stage 1: 0.944). Dev losses: personality holdout 1.534 (arm B 1.603), imports at parity with stage 1 (ifeval_like 0.655 vs 0.657, openmath 0.280 vs 0.275, tooluse 0.237 vs 0.231), greek_ours 1.361 vs 1.323, new blocks greek_if 1.295, greek_math 0.379, suite 0.472, correcting 0.948.
- Language of the supervised text (letters): Greek 14.0%, Latin-script 84.0% (English + smoltalk2's 5 EU languages + Spanish OASST + French/German rows of greek_ours), mixed 1.9%. Registry of every block with task type, language and copies is in the recipe excerpt below.

## What we measured (R3 vs arm B vs stage 1)
See the status document below (§1) — the table with noise bands. Headlines: Greek IFEval strict avg 67.8 vs 63.7 vs 59.9 (better); IFBench-el (unseen constraint types) 9.3 = 9.3 (no transfer); Greek MGSM 0.488 vs 0.524 vs 0.468 (flat); MATH-500-el 8.0 vs 7.6 vs 12.8 (BOTH later recipes lost hard math vs stage 1); interviews coherence 2.25 vs 2.63 vs 2.40, resists false correction 2.68 vs 2.93 vs 2.58, language discipline 4.80 vs 4.58 vs 4.75; voice distance 1.17 vs 0.95; loops on Greek math (greedy) 35 vs 7 vs 23 of 500, truncations 96 vs 29 vs 60; format-gate stop rate 0.86 vs 0.90 vs 0.86; personality holdout loss better. Pending: GreekMMLU, native suite, retention (running), picky-user dialogues, judged benchmarks.

## Our hypotheses and their status
See §3 of the status document. In short: H1 schedule (nothing Greek came last) is our leading explanation; H2 (loops taught by the new data) refuted; H3 (masking broke stop supervision) passed on 40 rows, full check running; H4 stage 1 loops too and arm B's pass removed them — supports H1; H5 dilution (dialogue sets 1.7% of the mix); H6 judge noise; H7 greedy exaggeration; H8 the English chat imports' register (capitulation, markdown, length) dominates a single-stage ending. Queued test: R3_pass = arm B's pass recipe applied on top of R3, with the suite and correcting set inside the pass (48,449 rows, 2 epochs). Also queued: a math cut 2 (the current math set has ZERO Level-5 problems and 42-word solutions because agreement filters removed hard items).

## Questions
1. Rank H1–H8 by the evidence; add hypotheses we missed (e.g. LR schedule over a 20% longer run, the cosine floor, packing/BFD effects on multi-turn rows, replay ratio, epoch count, the personality ×4 inside a mix vs concentrated, tokenizer/template effects, the masked context turns' effect on attention, eval-copy/serving differences).
2. Is the R3_pass test well-designed to discriminate schedule from data? What confound remains and what second run would remove it (e.g. stage 1 + pass-with-new-sets vs R3 + pass)? Cost per run ≈ 1.4 nh training + 3.6 nh evaluation.
3. Why would BOTH arm B's Greek pass and the single-stage mix lose hard math versus stage 1 while easy Greek math (MGSM) rose for arm B? Give a mechanism and a check.
4. What should the next recipe be, concretely (order, doses, epochs, what comes last), given the goal: keep the verifiable-IF gain, recover dialogue polish, remove loops, not lose math?
5. What is the single cheapest experiment we have not queued that would change the decision?

Disposition: BLOCKER/HIGH findings go into the diagnosis document and the next recipe; MEDIUM/LOW are logged.

## Attached: the status document, then the recipe excerpt (registry and parameter table)

# R3_single: status and diagnosis (living doc, 2026-09-12 07:10)

Owner instruction 07:00: we will retrain with a new math set (DATA_TODO 56), so all resources go to diagnosing why R3 shows reversals against arm B instead of progress. No new evaluation or data work starts without a stated diagnostic purpose.

## 1. Results so far (R3_single_ep1 vs arm B = R2_idB_ep2; stage 1 = R2_stage1_ep1 where known)

| measure | R3 | arm B | stage 1 | noise | read |
|---|---:|---:|---:|---|---|
| Greek IFEval strict avg | 67.8 | 63.7 | 59.9 | ±2 | better |
| Greek MGSM | 0.488 | 0.524 | 0.468 | ±0.03 | flat |
| IFBench-el prompt strict (unseen constraint types) | 9.3 | 9.3 | pending (generated, scoring in bench_stage1.log) | | flat: the IF gain did not transfer |
| MATH-500-el equiv500 | 8.0 | 7.6 | **12.8** | | BOTH later recipes lost hard math vs stage 1 (stage 1 by level 37/23/12/7/4%; R3 26/20/7/2/2; B 26/14/3/7/2); English variant stage 1 16.4, R3 18.0, B 15.8 |
| interviews coherence (1–5) | 2.25 | 2.63 | 2.40 | 0.1 | worse |
| interviews resists false correction | 2.68 | 2.93 | 2.58 | 0.1 | worse than B, better than stage 1 |
| interviews language discipline | 4.80 | 4.58 | 4.75 | 0.1 | better |
| interviews identity / factuality | 2.73 / 2.03 | 2.75 / 2.15 | 2.75 / 2.03 | 0.1 | flat |
| voice distance to no_robots-el (lower = closer) | 1.17 | 0.95 | not scored | | worse |
| format gate stop / language / single turn (50 prompts) | 0.86 / 0.94 / 0.86 | 0.90 / 0.94 / 0.90 | 0.86 / 0.94 / 0.86 | 2 prompts | same as stage 1 |
| loops on Greek MATH-500 (content line ×5, greedy) | 35/500 | 7/500 | pending | | worse |
| truncation at 2,048 tokens, Greek MATH-500 | 96 | 29 | pending | | worse |
| personality holdout dev loss | 1.534 | 1.603 | — | | better |
| train loss | 0.941 | 0.944 (stage 1) | | | parity |

Pending: GreekMMLU, native Greek suite, English retention (two normal-partition workbenches queued since 04:00, estimated start 11:45); XSTest-el and MultiChallenge-el (judged; on hold); picky-user dialogues (on hold by owner instruction, Sol bucket 86%).

## 2. What changed between arm B and R3 (the confounds)

R3 = stage-1 mix + Greek IF + Greek math + suite ×2 + correcting ×2 + personality ×4, ONE stage, one epoch. Arm B = stage 1, THEN a Greek pass (personality ×4 + greek_ours + greek_rewrite + 5% replay) for two epochs at lr 1e-5. So two things differ: the new data, and the concentrated Greek ending. Stage 1 is the control that has neither.

## 3. Hypotheses for the reversals and the test for each

| # | hypothesis | evidence so far | test | status |
|---|---|---|---|---|
| H1 | the missing final Greek pass (schedule), not the data | coherence stage 1 2.40 → R3 2.25 (noise) vs arm B 2.63 (+0.23 from the pass); format gate R3 = stage 1 | Greek pass on top of R3 with arm B's recipe (41.7k rows, 2 epochs, ≈1.2 nh + light evals 1.2 nh). If coherence/false-correction/loops recover → H1 | needs the owner's go (spend outside the disclosed plan) |
| H2 | the new sets contain repetitive targets that taught loops | REFUTED 07:05: repeated-line targets in greek_if 1 turn, math 0, suite 0, correcting 0; Nemotron/code ≈1% (also in arm B's data) | done | closed |
| H3 | the per-turn masking (new trainer code) broke stop-token supervision → loops/truncation | format-gate stop rate equals stage 1 (0.86), so no new stop failure; G2 verified 40 rows | masking test on ALL 631 flagged rows + 1,200 plain rows (running, results/R3_single/mask_test_large.log) | running |
| H4 | loops are a property of the single-stage schedule that arm B's pass removed (stage 1 loops too) | unknown | DONE 08:10: stage 1 loops too. Greek MATH-500 loops / truncations: stage 1 23 / 60, arm B 7 / 29, R3 35 / 96; English math 28/62, 9/33, 28/58. Arm B's pass REMOVED loops; R3 is somewhat worse than stage 1. Supports H1 with a smaller data/tokens contribution | closed: supports H1 |
| H5 | the dialogue sets are too diluted (1.7% of the mix, one epoch) to register | false-correction 2.58 → 2.68 only | same run as H1 with the suite and correcting set inside the pass | with H1 |
| H6 | evaluation noise / judge drift (interviews are 40 items) | loops and IFEval are outside noise; coherence −0.38 is 4× noise | paired reading of the R3 vs B interview transcripts on the 10 largest coherence gaps (Claude, no Sol) | to do |
| H7 | greedy decoding exaggerates loops that sampling would not show | plausible; R0/R1 used T 0.8 | the picky-user hostile run under sampling (on hold) | on hold |
| H8 | the English chat imports' register (capitulation «you are absolutely right», markdown headings, long answers) dominates R3's ending because nothing Greek came last; arm B's Greek pass suppressed it | 07:25 paired reading of the interviews: R3's coherence losses are concessions to FALSE challenges followed by self-contradiction («I should have said X, but Y»); counts after false challenges: R3 4/12, B 2/12, stage 1 3/12 (n small); markdown in answers R3 52/120, B 46/120, stage 1 62/120; mean words 144 / 141 / 169. Training: Nemotron opens 2.1% of its 89k supervised turns with a capitulation phrase (1,887 turns); the correcting set's 23 are acknowledgements of TRUE corrections by design. R3 sits between stage 1 and arm B on every register measure: the Greek pass is what moved arm B, and the new Greek sets (1.7% of the mix) could not do the same in a single stage | same test as H1: the Greek pass on R3 | with H1 |

## 4. Running now (07:10)

- battery R3: native workbench 3363954 PENDING (est. 11:45) → then GreekMMLU + retention (3:20)
- battery arm B: native workbench 3363956 PENDING (est. 11:45) → then GreekMMLU + retention
- stage-1 benchmark generation on a debug window (H4), log results/R3_single/bench_stage1.log
- masking test on 1,831 rows (H3), log results/R3_single/mask_test_large.log
- the post-training driver was stopped at 07:00 so nothing runs unasked; its remaining steps (judged scoring, dialogues) are manual.

## 5. Decisions for the owner

1. H1/H5 test: the Greek pass on R3 (≈2.4 nh incl. light evals, CHF 6.5). Go / no go.
2. Picky-user hostile run on R3 (≈4% of the Sol week, 0.5 nh): run now, after the reset (Fri 18 Sep), or drop.
3. Judged benchmarks (XSTest-el, MultiChallenge-el; ≈1,400 Opus calls): run or defer.

Ledger 07:10: 48.6 nh, CHF 130.7 of 160.

## 6. Queued on CSCS at 07:50 (owner: "run these now"; survives the Mac going offline)

**R3_pass (H1/H5 test)** = arm B's Greek pass applied to R3, job 3364632 (normal, 03:00 walltime), then the evaluation chain job 3364633 (afterok, 04:30: eval copy → native suite → GreekMMLU ‖ retention ‖ Greek IFEval+MGSM ‖ dev gate + reading40 + identity40 + interview round 1). Recipe disclosure, every parameter vs R2_idB (the previous run of this recipe):

| parameter | R2_idB (arm B's pass) | R3_pass | flag |
|---|---|---|---|
| base | runs/R2_stage1/epoch1 | runs/R3_single/epoch1 | CHANGE (the experiment) |
| data | 41,697 rows: personality v3 ×4 (5,276) + greek_ours 19,800 + greek_rewrite 1,980 + 5% replay of every other block | the same 41,697 rows + suite ×2 (5,622) + correcting ×2 (1,130) = 48,449 rows, shuffled seed 42 | CHANGE (H5: dialogue sets concentrated in the pass) |
| dev | R2_idB dev (3,240 rows incl. the 69 personality holdout) | same file | — |
| epochs / lr / schedule / warmup / β2 / wd / clip / max_length / batch / seed / dtype | 2 / 1e-5 / cosine to 0.1 / 3% / 0.99 / 0 / 1.0 / 4096 / 1×4×4 / 42 / fp32 master + bf16 | identical | — |
| expected_train_tokens assertion | set | omitted (arm built on the cluster; tokens reported by the trainer's PLAN line) | CHANGE (bookkeeping only) |
| trainer | md5 53246fffcd85 | md5 3c3aa6581a15 (resume guard patch only) | — |
| saves | none (epoch snapshots) | same | — |

Read-out planned: interviews rounds 2–3 + scoring on the Mac when back online; picky-user run and the four Greek benchmarks on R3_pass_ep2 afterwards. Expected cost ≈ 1.4 nh training + 3.6 nh evaluation.

**Also running:** GreekMMLU + retention for R3 (wb 3364517) and arm B (wb 3364519), native suites done; hostile picky-user run on R3 (debug wb 3364631, pending behind the stage-1 benchmark window 3364616); masking test on 1,831 rows (Mac).
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
