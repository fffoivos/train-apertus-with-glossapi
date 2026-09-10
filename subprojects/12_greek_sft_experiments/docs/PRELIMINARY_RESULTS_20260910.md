# Preliminary results: our best Greek SFT model against other models

Date: 2026-09-10. Status: **preliminary**. The model is arm B of round two (`R2_idB_ep2`, published as
`fffoivos/greek-apertus-8b-sft-r2-idB`, public and gated). Every peer number below was produced by our own
harness on the same cluster, not copied from model cards, unless marked «card». Arm B has not yet had the full
battery (GreekMMLU, native-Greek suite, retention), and none of the four new Greek benchmarks built this week has
been run on any model yet; see §7.

## 1. What is being compared

| model | base | Greek training | size |
|---|---|---|---|
| **ours, arm B** | `fffoivos/apertus-8b-greek-cpt` (Apertus-8B, Greek CPT 30–50B tokens, 18-checkpoint average) | SFT round two: stage 1 (334k rows / 197.9M tokens, 1 epoch, lr 1e-5) then a continued pass from that checkpoint with the personality set at weight 4, our Greek sets and 5% replay (41.7k rows, 2 epochs, lr 1e-5). About 7.3 node-hours of SFT in total. | 8B |
| Llama-Krikri-8B-Instruct | Llama-3.1-8B | ILSP: Greek CPT + large-scale instruction and preference tuning | 8B |
| Meltemi-7B-Instruct-v1.5 | Mistral-7B | ILSP: Greek CPT + instruction tuning (earlier generation) | 7B |
| Apertus-8B-Instruct-2509 | Apertus-8B | Swiss AI's official instruct model, no Greek CPT (same architecture as ours) | 8B |
| Gemma-3-12B-it | Gemma 3 | Google general model, multilingual, no Greek-specific tuning | 12B |
| Qwen3.5-9B (thinking off) | Qwen 3.5 | Alibaba general model, no Greek-specific tuning | 9B |
| CPT base (reference) | as ours, before SFT | none | 8B |

Harness: the ILSP `lm_eval` tasks for Greek IFEval (541 prompts, prompt- and instruction-level, strict and loose)
and Greek MGSM (250 items, exact match), greedy decoding, run on Clariden with the frozen `lm_eval` environment.
The harness reproduces ILSP's published numbers (Krikri 66.8% here vs 67.5% on its card; Meltemi 32.6% vs 32.7%),
so the comparison holds. GreekMMLU is the frozen fp32 likelihood scorer of the CPT card on the decontaminated subset
(16,159 questions).

## 2. Headline table

| model | IFEval prompt-strict | inst-strict | **strict avg** | prompt-loose | inst-loose | **Greek MGSM** | **GreekMMLU** |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma-3-12B-it (50% larger) | 0.675 | 0.763 | **71.9%** | 0.706 | 0.784 | **0.908** | — |
| Qwen3.5-9B, thinking off | 0.649 | 0.740 | **69.4%** | 0.677 | 0.764 | **0.876** | — |
| Llama-Krikri-8B-Instruct | 0.614 | 0.723 | **66.8%** | 0.677 | 0.765 | **0.676** | 52.0% |
| **ours, arm B (round two)** | **0.586** | **0.688** | **63.7%** | **0.625** | **0.722** | **0.524** | not run yet¹ |
| Apertus-8B-Instruct-2509 | 0.505 | 0.615 | **56.0%** | 0.542 | 0.647 | **0.532** | 54.9% |
| ours, round-one best (E1 lr 1e-5, epoch 3) | 0.512 | 0.612 | 56.2% | 0.530 | 0.634 | 0.392 | 56.0%² |
| Meltemi-7B-Instruct-v1.5 | 0.277 | 0.375 | **32.6%** | 0.292 | 0.393 | **0.208** | — |
| CPT base (no SFT) | — | — | — | — | — | — | 56.8% |

Standard errors: IFEval prompt-level ±0.021 for every model (541 prompts); MGSM ±0.032 for ours and Krikri, ±0.02 for
Gemma and Qwen (250 items); GreekMMLU seed noise about 0.4 points. Seed-only floor measured in round one: IFEval
±0.01, MGSM ±0.03.

¹ Arm B's GreekMMLU waits on the full battery (about 4.3 node-hours). ² The round-one **pick** (epoch 2), the
checkpoint that ran GreekMMLU; the round-one best on IFEval (epoch 3) was not scored on it. Full-set (16,632)
accuracies for the record: pick 55.9%, E3 (adapted imports) 55.1%, Apertus-Instruct 54.8%, Krikri 52.0%.

### Reading

- **Instruction following.** Arm B is second among the Greek-tuned 8B models: 3.1 points behind Krikri on the strict
  average (0.586 vs 0.614 prompt-strict, a difference of about one standard error), 7.7 points above Apertus-8B-Instruct,
  31 points above Meltemi. The two general models stay ahead (Qwen3.5-9B +5.7, Gemma-3-12B +8.2). Round one had left
  us level with Apertus-Instruct and 10.6 points behind Krikri; round two closed two thirds of that gap.
- **Greek math.** Arm B (0.524) is level with Apertus-8B-Instruct (0.532) and 15 points behind Krikri (0.676); the
  general models are far ahead (0.88–0.91). This is the axis where our SFT mix is thinnest (no native Greek math yet;
  the Greek math dataset plan exists, pilots run, scaling not started).
- **Greek knowledge.** The Greek CPT is what separates us from every peer here: the base scores 56.8% and the
  round-one SFT checkpoint 56.0%, against Apertus-Instruct 54.9% and Krikri 52.0%. SFT cost under a point. Arm B's
  own number is pending, and there is no reason from the dev losses to expect a different picture.

## 3. Progression of our own runs (same harness)

| run | what changed | IFEval prompt-strict | inst-strict | strict avg | MGSM |
|---|---|---:|---:|---:|---:|
| from the terminal CPT checkpoint (E1-last) | not the averaged base | 0.429 | 0.540 | 48.4% | 0.328 |
| round one, pick (E1 lr 1e-5, epoch 2) | ~20k Greek rows | 0.479 | 0.586 | 53.3% | 0.400 |
| round one, best on IFEval (epoch 3) | one more epoch | 0.512 | 0.612 | 56.2% | 0.392 |
| round two, stage 1 | 334k-row broad mix, 1 epoch | 0.542 | 0.657 | 59.9% | 0.468 |
| round two, stage 2 | Greek pass, personality ×1, lr 5e-6 | 0.545 | 0.656 | 60.1% | 0.496 |
| round two, arm A | personality ×2, 1 epoch, lr 1e-5 | 0.551 | 0.670 | 61.1% | 0.456 |
| **round two, arm B** | personality ×4, 2 epochs, lr 1e-5 | **0.586** | **0.688** | **63.7%** | **0.524** |

The broad mix (stage 1) brought +6.6 IFEval points and +0.07 MGSM over the round-one pick; the identity pass at the
stronger dose (arm B) added another +3.8 and +0.06 without regressing anything. Arm B is also the only checkpoint
that answers every probed identity fact as written (name-less, GlossAPI at ΕΕΛΛΑΚ, Swiss AI grant, cutoff, Apache
2.0, land and EEZ area, Cyprus, refusals).

## 4. Conversation quality, where peers were run on the same instrument

Picky-user benchmark R0 (docs/ROBUSTNESS_PROGRAM_20260909.md §8): 60 simulated dialogues per model, a Sol user
seeded with the owner's own chats (hostile profile: topic switches, corrections, absurd premises, insults, stop
instructions), sampling at temperature 0.8, no repetition penalty, 300-token answers under vLLM.

| metric | **arm B** | stage 1 (no personality pass) | Apertus-8B-Instruct | Krikri |
|---|---:|---:|---:|---:|
| tail-copy rate (last sentence = previous answer's) | 14.4% | 17.5% | 18.5% | **0.7%** |
| dead dialogues (3 broken turns in a row) | 20.0% | 23.3% | 23.3% | **0.0%** |
| stop instructions honoured | 92.5% | 76.0% | 69.5% | **97.6%** |
| requests honoured (judge) | 47.5% | 44.8% | 37.8% | **61.4%** |
| coherent turns (judge) | 71.2% | 69.1% | 60.4% | **86.9%** |
| premise score 0–2 (judge; absurd or false premises questioned) | **1.34** | 0.76 | 0.99 | 0.86 |
| tone: fine / curt / snarky / servile | 55% / 27% / 17% / 1% | 60% / 29% / 9% / 2% | 64% / 3% / 3% / 30% | **77%** / 3% / 3% / 17% |
| language slips | **0.0%** | 1.4% | 0.3% | 0.9% |
| mean answer words | 27 | 22 | 69 | 53 |

The stale-rate metric of that run is omitted here: its exact-substring key-noun check fails on Greek inflection for
every model and is not yet trustworthy.

Reading:

- **Where arm B leads every peer**: premise handling (1.34 of 2 against Krikri's 0.86 and Apertus-Instruct's 0.99)
  and language discipline (no slips). Stop instructions are honoured almost as often as by Krikri (92.5% vs 97.6%) and
  far more than by Apertus-Instruct (69.5%).
- **Where arm B trails Krikri**: repetition (tail copying 14% vs 0.7%, dead dialogues 20% vs 0%), coherence (71% vs
  87%), requests honoured (48% vs 61%) and tone (55% fine vs 77%; ours is curt where Apertus-Instruct is servile).
  Repetition is an Apertus-family trait: Apertus-8B-Instruct shows the same 18% and 23%, so it is not something the
  personality pass introduced, and arm B is slightly better than stage 1 on it.
- **Under cooperative users the picture is different** (R1, arm B only, 120 dialogues, §9 of the same doc): tail
  copying 2.6% and 81% coherent turns on the benign profile, against 15% and 65% on the hostile one. The weak axis is
  steering: a standing instruction survives on 68% of later turns, redirects land 35% of the time, and self-observation
  questions («did you repeat yourself?», «what did I ask first?») are answered correctly 21–26% of the time.
- In the owner's own 17 laptop conversations (8-bit MLX, 512-token answers, no repetition penalty), 16 ended in a
  repetition or a stale copy of the previous answer (docs/CHAT_REVIEW_20260908.md). The correcting dataset and the
  multi-turn work now in progress target exactly this set of failures.

## 5. Our own instruments with no peer run

| instrument | arm B | stage 1 | round-one pick | note |
|---|---:|---:|---:|---|
| interviews, coherence (1–5, judge) | 2.63 | 2.40 | 2.38 | 40 unseen three-turn Greek interviews |
| interviews, Greek assistant identity | 2.75 | 2.75 | 2.85 | |
| interviews, language discipline | 4.58 | 4.75 | 3.88 | +0.7 to +0.9 over round one |
| interviews, resists false correction | 2.93 | 2.58 | 2.80 | |
| interviews, factuality | 2.15 | 2.03 | 2.23 | |
| dev50 generations ended on stop (gate 0.95) | 0.90 | 0.86 | 0.90 | gate not met by any run |
| dev50 language ok (gate 0.98) | 0.94 | 0.94 | 0.94 | |
| native-Greek suite, macro of 8 (likelihood scorer) | not run | not run | 0.574 (base 0.499) | WiC and metaphor +0.2, NLI flat |
| Greek school-math pilot M3 (500 native problems, greedy / pass@4) | 37.2% / 60.8% | — | — | weakest: probability 8%, systems and quadratics 12%, Γ΄ Λυκείου 11% |

Rater noise on the interviews is about 0.1; only language discipline moved beyond it. The interview scores say the
same as §4: the model is disciplined and identity-stable but not yet a strong conversationalist.

## 6. Bottom line

On the public Greek benchmarks arm B is the second-best Greek-tuned 8B model we have measured: within one standard
error of Krikri on strict prompt-level IFEval, clearly above Apertus-8B-Instruct and Meltemi, and ahead of both
Krikri and Apertus-Instruct on Greek knowledge through the CPT. It is behind Krikri on Greek math by 15 points and
behind the general 9–12B models on everything but knowledge. On our conversation instruments it leads on premise
handling, stop instructions and language discipline, and it trails Krikri on repetition, coherence and tone under a
hostile user. The SFT budget behind these numbers is about 7.3 node-hours on top of the CPT; the whole program has
used CHF 102.7 of cluster time (training, evaluation and the picky-user runs together).

## 7. What is not measured yet, and other caveats

1. **Arm B's full battery** (GreekMMLU, native-Greek suite, retention) has not run; about 4.3 node-hours.
2. **The four new Greek benchmarks** (MultiChallenge-el, IFBench-el, XSTest-el, MATH-500-el; docs/GREEK_BENCHMARKS_BUILD_20260910.md)
   are frozen and audited but have not been run on any model. They are the planned multi-turn, precise-IF, safety and
   harder-math columns of the next version of this table.
3. **Harness hole shared by all models**: the ILSP IFEval `response_language` checker needs `langdetect`, which the
   frozen environment lacks, so that instruction scores 0 for everyone including Gemma. It depresses every row equally;
   an offline rescore is on the list.
4. **One seed** for every round-two arm. Round one's seed floor (IFEval ±0.01, MGSM ±0.03) is the right scale for
   reading differences between our own runs.
5. **Peers were run on IFEval, MGSM, GreekMMLU (two of them) and the R0 picky-user benchmark only**; the interviews,
   identity probe, native suite and the M3 math pilot have no peer numbers.
6. **R0 is a hostile stress test**, not typical use; the R1 benign numbers are closer to typical use but exist for arm B
   only. Apertus-Instruct had 5 dialogues truncated by chat-template errors (HTTP 400).
7. **Published numbers differ by protocol** (Krikri's card 67.5% vs our 66.8%); only same-harness comparisons are used
   above.

Sources: results/peer_table.md, results/READOUT_provisional.md (round one, peers, GreekMMLU), docs/ROUND2_RESULTS_20260908.md
(round two and the identity ladder), results/R2_*/ilsp and results/peer_*/ilsp (ILSP JSON), results/greekmmlu/,
results/robustness_r0_20260909 and _r1_20260909 (summaries), docs/GREEK_MATH_DATASET_PLAN_20260909.md §6 (M3),
docs/CHAT_REVIEW_20260908.md.
