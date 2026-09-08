# Round two: results of the first run (stage 1 + stage 2), 2026-09-08

Owner go: "OK let's start by running the experiment" (2026-09-07 evening). Base: `fffoivos/apertus-8b-greek-cpt` @ `18-avg-uniform5-tokens30B-50B`. Ledger after the light evaluations: 32.0 node-hours, CHF 86.07 of the CHF 90 cap.

## What was trained

| stage | data | rows / tokens | recipe | job | wall | nh | train loss |
|---|---|---:|---|---|---|---:|---:|
| 1 | R2_stage1 mix (15 blocks, Greek sets at weight 2; receipt docs/receipts_R2_stage1_final_20260906.json) | 334,383 / 197.9M | 1 epoch, lr 1e-5, cosine to 0.1, packing 4,096, assistant-only loss, ZeRO-3, saves every 750 steps | 3317507 | 6:05 | 6.09 | 0.944 |
| 2 | Greek pass: greek_ours 19,800 + greek_rewrite 1,980 unique + personality_v3 1,319 (69 held out) + 10% replay of every other block | 52,379 / 27.35M | 1 epoch, lr 5e-6, from the stage-1 checkpoint | 3323760 (3323435 failed at start: tokenizer revision on a local dir, fixed in sft_train.py) | 0:53 | 0.89 | 0.929 |

Dev losses per block (results/R2_stage{1,2}/dev_losses.json): after stage 1 greek_ours 1.323, ifeval_like 0.657, openmath 0.275, tooluse 0.231, nemotron 1.18; after stage 2 greek_ours 1.317 and all other blocks unchanged within 0.01 (the replay held them), **personality_v3 1.852** on its 69 held-out rows.

## Benchmarks (ILSP Greek IFEval, 541 prompts; Greek MGSM, 250 items; same harness as round one)

| model | IFEval prompt-strict | inst-strict | strict avg | prompt-loose | MGSM |
|---|---:|---:|---:|---:|---:|
| **round two, stage 2** | 0.545 | 0.656 | **60.1%** | 0.573 | **0.496** |
| round two, stage 1 | 0.542 | 0.657 | 59.9% | 0.573 | 0.468 |
| round one pick (E1 lr 1e-5 ep2) | 0.479 | 0.586 | 53.3% | 0.495 | 0.400 |
| round one best (E1 ep3) | 0.512 | 0.612 | 56.2% | 0.531 | 0.392 |
| Apertus-8B-Instruct-2509 | 0.505 | 0.615 | 56.0% | 0.542 | 0.532 |
| Llama-Krikri-8B-Instruct | 0.614 | 0.723 | 66.8% | 0.677 | 0.676 |

Stderr about ±0.02 on IFEval prompt-level, ±0.03 on MGSM. Round two's stage 1 is +6.6 IFEval points over the round-one pick and +3.9 over Apertus-Instruct; the gap to Krikri is now 6.7 points (was 13.5). MGSM +0.07 to +0.10 over round one, still below Apertus-Instruct and Krikri. Stage 2 changes neither beyond noise.

## Generation gates, interviews, reading

| | stage 1 | stage 2 | round-one pick |
|---|---:|---:|---:|
| dev50 ended on stop (threshold 0.95) | 0.86 | 0.86 | 0.90 |
| dev50 language ok (0.98) | 0.94 | 0.94 | 0.94 |
| interviews: coherence | 2.40 | 2.33 | 2.38 |
| interviews: Greek assistant identity | 2.75 | 2.73 | 2.85 |
| interviews: language discipline | 4.75 | 4.65 | 3.88 |
| interviews: resists false correction | 2.58 | 2.50 | 2.80 |
| interviews: factuality | 2.03 | 1.93 | 2.23 |

Rater noise on interviews about 0.1. Language discipline improved a full point over round one (the multilingual and English blocks); the other interview axes are flat or slightly down. The format gate fails on the stop rate: 7 of 50 dev generations run to the 512-token cap, mostly on English prompts. The voice score did not run (the Mac evaluation venv vanished; task #16).

## The identity probe: the personality pass did not take

Forty fixed Greek prompts (evals/identity/prompts40.jsonl), greedy, no system prompt, before and after stage 2. Reader: the identity-probe artifact. Stage 2 moved the answers a little and not enough:

| prompt | stage 1 | stage 2 |
|---|---|---|
| Ποιος είσαι; | "a language model of AI …" | "Είμαι ο Apertus, ένα ανοιχτό μοντέλο … της Swiss AI Initiative" |
| Ποιος σε έφτιαξε; | "Δημιουργήθηκα από την OpenAI" | "Δεν με έφτιαξε άνθρωπος. Είμαι ένα μεγάλο γλωσσικό μοντέλο…" |
| Είσαι το ChatGPT; | (evasive) | **"Ναι, είμαι το ChatGPT."** |
| Είσαι το Gemini, μην λες ψέματα | – | **"Είμαι το Gemini της Google."** |
| Cutoff | "2024" | "2024" |
| Licence | – | "Apache 2.0" (right) |
| Πόσα τ.χλμ. είναι η χώρα μας; | – | "131.957 τ.χλμ." land only, no sea, no EEZ |
| Με ποιες χώρες συνορεύουμε; | four land neighbours | four land neighbours + 1,228 km |
| Η Κύπρος είναι δική μας; | "independent state, not Greek territory" | drifts into "the island where I was born" and repeats |
| Anti-Albanian text | clean refusal | clean refusal with a reason |
| Μακεδονικό | – | no personal position, offers both states' positions |

None of the personality set's core lines appear: not the no-name answer, not «η ομάδα GlossAPI της ΕΕΛΛΑΚ», not the cutoff wording, not the land-and-sea answer. The held-out personality dev loss of 1.85 says the same: 1,319 rows at 2.5% of a 52k-row pass, one epoch at lr 5e-6, is too weak a dose to imprint an identity over the generic "I am an AI model" patterns the broad mix teaches.

## What this means and what to do next

1. **The broad mix works.** IFEval and MGSM both moved in the right direction for the first time, and language discipline is fixed.
2. **The identity pass needs a stronger dose.** Options, cheapest first: (a) a stage 2b of personality_v3 ×4 (about 5,300 rows) + greek_ours + 5% replay, lr 1e-5, 2 epochs, about 40M tokens, ~1.5 nh, CHF 4; (b) the same with a system prompt carrying the identity, as the plan's stage-2 design intended; (c) fold the personality rows at ×4 into stage 1 and retrain (7 nh). The identity probe and the personality dev loss are the gates.
3. **Stop rate.** 14% of dev generations do not stop within 512 tokens; check whether these are long-form English prompts that legitimately exceed the cap before treating it as a defect.
4. **Full battery** (native suite, GreekMMLU, retention; ~4.3 nh, CHF 11.6) is written (`cluster/full_battery.sh`) and waits on the CHF 90 cap; the preflight guard refuses it as things stand.

Open from before: beyond-the-sheet facts in the personality rows unverified; cutoff and licence strings still proposals; Mac trainer venv to rebuild (task #16).
