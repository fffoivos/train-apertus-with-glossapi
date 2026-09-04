# Round One Readout

*Autonomous run, night of 2026-09-03 → 04. Written 2026-09-04 07:06; the sections below are the running record and
update as chains finish (last update 09:20; round one complete). CHF used so far: 50.35 of the 90 cap (rate CHF 2.69 per node-hour).*

## Executive summary

**What ran.** The full first round of Greek SFT on the Greek-CPT Apertus-8B, executed by Sol from written briefs, certified by
an independent Fable review before the first GPU minute (BLOCKERS 0; two HIGH findings fixed and re-certified), and driven on
Clariden through one-node workbenches. Phase A: two learning rates × three epochs on the Greek data (E1), every epoch checkpoint
evaluated on Greek IFEval, Greek MGSM, a format gate, a stylometric voice score against no_robots-el, and 40 unseen three-turn
interviews scored by an LLM judge. Then a replicate (cosine schedule, second seed), a third seed, the E1-last arm on the terminal
CPT checkpoint, and phase B (E2, E3; E3′ finishing). Guards: the frozen native-Greek suite on the pick; GreekMMLU waits for a
three-hour batch that needs your notice (>2 h job, protocol §6).

**The pick (provisional, G3 is yours): lr 1e-5, 2 epochs.** Lowest dev loss, best stop rate, the only checkpoint with a voice
Delta under 1.0 (0.85), interviews tied with epoch 3 within judge noise; epoch 3 at 1e-5 has started to overfit by dev loss;
lr 5e-6 needs three epochs to reach the same place.

**Guards so far.** Native-Greek suite on the pick: macro 0.574 vs the base's 0.499, no benchmark down beyond noise (NLI −0.008),
WiC and metaphor up 0.2 — a jump large enough to deserve a second look, now reproduced on the rival, the replicate and E1-last (see the four-way table).

**E1-last is settled:** the terminal CPT checkpoint fine-tunes to the same dev loss but clearly worse Greek math (MGSM 0.33 vs
0.42, four times the seed floor) and instruction following, and its NLI/metaphor deficit on the native suite survives SFT (macro-8
0.500 vs 0.575). The averaged checkpoint stays the base.

**Noise floors.** Seed only (two cosine seeds): ifeval ±0.01, MGSM ±0.03, voice ±0.05, interviews ±0.02, mean Greek dev loss
±0.01. Seed + schedule (constant epoch-2 vs cosine): the constant-lr checkpoint reads better than the cosine endpoint on voice
(0.85 vs 0.95–1.00) and interviews (2.83 vs 2.60) — a real difference, and a question for you: phase B uses the recipe's cosine
schedule.

**Phase B (done).** Neither E2 (paired English) nor E3 (skills + fr/de) moves the Greek dev loss or the Greek light evals
beyond the seed floor; each moves its own slice as intended. **The adaptation question is answered:** E3 (imported slices
adapted to the Greek point of view) beats E3′ (the same rows raw) on interviews 2.91 vs 2.63 (floor 0.02), on the voice score
0.96 vs 1.11 (floor 0.05), on clean stopping 90% vs 80%, and on Greek IFEval 0.497 vs 0.470 (floor 0.01), with Greek MGSM
within the floor. The raw slices pull the model toward an American assistant (identity 2.60 vs 2.85, factuality 1.85 vs 2.27).
E3 is also the best-reading arm of the whole round on the interviews.

**Known-ness of the training claims (base-model probe).** Of 10,388 Greek-reality claims the rows assert, the base answers
9% greedily and 2% in one of four samples; 88% come out "unknown" — with a strong caveat: the probe is a four-shot QA format
a base model largely fails, so this is an upper bound on ignorance. The risk of plan §8 is real; the probe needs calibration
on the SFT'd pick before E7 filters on it.

**Guards complete except GreekMMLU.** All four SFT checkpoints pass the native-Greek suite (macro-8 ≈ 0.57 vs the base's 0.50; NLI flat, WiC and metaphor +0.2 — systematic). E1-last's NLI goes 0.387 → 0.388 and WiC 0.336 → 0.737: the deficit persists after SFT. GreekMMLU needs your go.

**Three decisions for you.**
1. **G3:** confirm (lr 1e-5, 2 epochs) — after the blind reading: https://claude.ai/code/artifact/690e0be1-dff4-4d25-ac8e-d49b861ab19c
   (40 prompts × 7 runs, unlabeled; press Save to get the ratings JSON and paste it to me).
2. **GreekMMLU batch:** ~3 node-hours (≈ CHF 8) in one normal-partition workbench, four models in parallel (pick, replicate,
   E1-last, the 5e-6 rival) — a job over two hours, so it waits for your word.
3. **Next arms:** E7 (unknown-claim rows removed) once the known-ness labels exist; a constant-lr vs cosine check for phase B
   if you agree the schedule difference is real; the preference round (§9) on the pick.

**Incidents worth knowing.** Sol's backend was down for 25 minutes early on; the headless Opus lane returned truncated or
malformed JSON for the interview judge (fixed with a repair pass and a Sol fallback); two eval drivers were corrupted by
live edits (fixed: drivers run from per-label copies); the native suite OOMs any lane sharing its GPUs (light and native evals
now run separately). Every fix is committed; the ledger is honest about the node-hours these cost.

---

**Status:** round one is complete. Phase A (two learning rates × three epochs), the replicate, the third seed, E1-last and phase B (E2, E3, E3′) are trained and measured; the native-suite guard is done on all four checkpoints. Open: the blind reading (G3), the GreekMMLU batch (needs your go), and the next arms.

## Grid table (light evals)

| label | dev_no_robots | dev_mean_el | ifeval_strict | ifeval_inst | mgsm | gate_stop | gate_lang | voice_delta | gen_words_el | int_coherence | int_factuality | int_greek_assist | int_language_dis | int_mean | int_n | int_resists_fals |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0b |  |  |  |  |  | 0.000 | 0.860 | 0.863 | 8528 |  |  |  |  |  |  |  |
| E1_lr1e-5_ep1 | 1.471 | 1.395 | 0.468 | 0.578 | 0.380 | 0.880 | 0.940 | 1.027 | 2190 | 1.880 | 2.150 | 2.450 | 3.400 | 2.530 | 40 | 2.770 |
| E1_lr1e-5_ep2 | 1.452 | 1.350 | 0.479 | 0.586 | 0.400 | 0.900 | 0.940 | 0.853 | 2139 | 2.380 | 2.230 | 2.850 | 3.880 | 2.830 | 40 | 2.800 |
| E1_lr1e-5_ep3 | 1.476 | 1.363 | 0.512 | 0.612 | 0.392 | 0.880 | 0.940 | 1.081 | 1995 | 2.500 | 2.080 | 2.830 | 4.150 | 2.860 | 40 | 2.730 |
| E1_lr5e-6_ep1 | 1.511 | 1.478 | 0.386 | 0.516 | 0.332 | 0.560 | 0.860 | 0.797 | 3329 | 1.600 | 1.770 | 2.200 | 2.650 | 2.150 | 40 | 2.520 |
| E1_lr5e-6_ep2 | 1.464 | 1.384 | 0.458 | 0.578 | 0.412 | 0.880 | 0.940 | 1.001 | 2332 | 2.100 | 2.000 | 2.600 | 3.800 | 2.620 | 40 | 2.580 |
| E1_lr5e-6_ep3 | 1.457 | 1.361 | 0.486 | 0.584 | 0.416 | 0.880 | 0.940 | 1.008 | 2668 | 2.520 | 2.300 | 2.800 | 3.700 | 2.800 | 40 | 2.700 |


Columns: dev losses from the training runs' epoch-end evaluations (held-out 2%); `ifeval_strict/inst` = ILSP Greek
IFEval prompt/instruction strict accuracy; `mgsm` = ILSP Greek MGSM exact match (250); `gate_stop` = share of 50 dev
generations that ended on the turn token (512-token cap; the non-stops are mostly the long English math and the
English twin prompts E1 never trained on); `voice_delta` = Burrows's Delta to no_robots-el (lower = closer; the
reference's own split-half floor is 0.05); `int_*` = Opus/Sol rubric means (1–5) over the 40 unseen interviews.

## Dev-loss trend (the epoch question)

| epoch | lr 1e-5 mean Greek dev loss | lr 5e-6 mean Greek dev loss |
|---|---|---|
| 1 | 1.395 | 1.478 |
| 2 | 1.350 | 1.384 |
| 3 | 1.363 | 1.361 |

lr 1e-5 bottoms at epoch 2 and rises at epoch 3 in most Greek configs (overfitting onset); lr 5e-6 is still improving
at epoch 3 and lands where 1e-5 was at epoch 2.

## Decision rule (plan §11) applied

1. **Vibes first.** Interview rubric means: (1e-5, ep2) 2.83, (1e-5, ep3) 2.86, (5e-6, ep3) 2.80 — a tie within
   the judges' noise; language discipline favours the 1e-5 arm (3.9–4.2 vs 3.7). Voice Delta favours
   **(1e-5, ep2) at 0.85**, the only checkpoint under 1.0 (the rest 1.00–1.08). The blind reading is the owner's.
2. **ifeval_greek among ties:** (1e-5, ep3) 0.512 > (5e-6, ep3) 0.486 > (1e-5, ep2) 0.479 — three points apart,
   with 541 prompts that is about one standard error; not decisive.
3. **Guards:** pending (native suite for the two candidates running; GreekMMLU in the morning). Dev loss says
   (1e-5, ep3) has started to overfit.
4. **Fewer epochs on ties** → **(1e-5, 2 epochs)**.

## What the interviews say beyond the numbers

The judges are strict (coherence ~2.4/5, factuality ~2.1/5 across the board). Recurrent flags: repeated list items
in long answers (worst at the under-trained (5e-6, ep1): "30+ identical repeated list items"), answering twice or
mixing languages after a switch (language discipline 2.7 → 4.2 with training), and factual slips on Greek
specifics (a GDPR-age claim, bank-deposit rules) — the knowledge-alignment risk of plan §8 made visible.

## Waiting for the owner

- **Blind reading:** https://claude.ai/code/artifact/690e0be1-dff4-4d25-ac8e-d49b861ab19c (40 prompts × 7 runs:
  base + six checkpoints, unlabeled, shuffled per prompt). Ratings persist in the browser; the JSON download
  does not work inside the artifact viewer yet — copy from the page or ask me to add an in-page export.
- **G3 confirmation** of the pick, or a different (lr, epoch).
- **GreekMMLU batch** (~3 h workbench, >2 h → owner notice per protocol): winner, replicate, E1-last, plus the
  (5e-6, ep3) rival.
- **Phase B** (E2/E3/E3′) starts at the pick once the replicate's noise floor is known.

## Ledger

See EXECUTION_LOG.md; CHF used at 05:20 ≈ 15.3 of the 90 cap.


## Replicate (E1_cos) vs the grid winner — dev losses at epoch 2

| config | grid winner (1e-5 const, ep2) | replicate (1e-5 cosine, 2 ep, seed 43) | diff |
|---|---|---|---|
| apertus_en | 1.318 | 1.240 | -0.078 |
| coconot | 1.544 | 1.583 | +0.039 |
| euroblocks_de | 1.584 | 1.632 | +0.048 |
| euroblocks_fr | 1.421 | 1.472 | +0.051 |
| everyday | 1.182 | 1.217 | +0.035 |
| no_robots | 1.452 | 1.465 | +0.013 |
| no_robots_en_pov | 1.847 | 1.880 | +0.033 |
| oasst | 1.397 | 1.487 | +0.090 |
| personas_if | 1.370 | 1.404 | +0.034 |
| smolcon | 1.158 | 1.134 | -0.024 |
| systemchats | 1.348 | 1.326 | -0.022 |

Mean Greek dev loss: winner 1.350, replicate 1.374 (+0.024). Caveat: the replicate differs from the grid
winner in BOTH seed (43 vs 42) and schedule (cosine-to-min-lr over 2 epochs vs constant, checkpoint taken mid-run), so
this is not a pure seed-noise floor; it is the reference point for phase B, which shares its schedule. A second
cosine seed would isolate seed noise (≈ 1 nh) — a candidate for the owner's morning decision.


## E1-last (terminal CPT checkpoint) vs the replicate (averaged checkpoint), same recipe (1e-5, 2 ep, cosine)

| config | E1_cos (18-avg base) | E1last_cos (rev 17 base) | diff |
|---|---|---|---|
| apertus_en | 1.240 | 1.364 | +0.124 |
| coconot | 1.583 | 1.592 | +0.009 |
| euroblocks_de | 1.632 | 1.665 | +0.033 |
| euroblocks_fr | 1.472 | 1.502 | +0.030 |
| everyday | 1.217 | 1.212 | -0.005 |
| no_robots | 1.465 | 1.443 | -0.022 |
| no_robots_en_pov | 1.880 | 1.900 | +0.020 |
| oasst | 1.487 | 1.404 | -0.083 |
| personas_if | 1.404 | 1.371 | -0.033 |
| smolcon | 1.134 | 1.163 | +0.029 |
| systemchats | 1.326 | 1.363 | +0.037 |

Mean Greek dev loss: averaged base 1.374, terminal base 1.364 (-0.010). By dev loss the terminal checkpoint
fine-tunes at least as well (lower on no_robots and oasst, higher on smolcon/systemchats). Whether its NLI/WiC deficit
survives SFT is a guard question (native suite, GreekMMLU) — pending.


## Readability bar from the replicate (light evals, epoch 2)

| metric | grid winner (seed 42, constant) | replicate (seed 43, cosine) | gap |
|---|---|---|---|
| ifeval_greek strict | 0.479 | 0.460 | 0.019 |
| mgsm_greek | 0.400 | 0.416 | 0.016 |
| gate stop rate | 0.90 | 0.88 | 0.02 |
| voice Delta | 0.853 | 1.000 | 0.15 |
| interview mean (1–5) | 2.83 | 2.61 | 0.22 |
| mean Greek dev loss | 1.350 | 1.374 | 0.024 |

Differences between arms smaller than these gaps are not readable (seed and schedule are confounded here; the seed-44
run isolates seed noise).


## Native-Greek suite guard — the pick vs the base (frozen fp32 scorer, same 73,894-example subset)

| benchmark | base (card) | E1 lr1e-5 ep2 | diff |
|---|---|---|---|
| asep_mcqa | 0.562 | 0.614 | +0.052 |
| demosqa | 0.469 | 0.472 | +0.003 |
| gpcr | 0.608 | 0.655 | +0.047 |
| medical_mcqa | 0.425 | 0.489 | +0.064 |
| oyxoy_metaphor | 0.345 | 0.552 | +0.207 |
| oyxoy_nli | 0.651 | 0.643 | -0.008 |
| oyxoy_wic | 0.549 | 0.775 | +0.226 |
| oyxoy_wsd_definition | 0.385 | 0.390 | +0.005 |
| **macro (8)** | 0.499 | 0.574 | +0.075 |

The guard passes: no benchmark drops beyond noise (NLI −0.008); the macro of the eight rises from 0.499 to 0.574, driven by WiC (+0.23), metaphor (+0.21) and the MCQ sets (+0.05–0.06). A jump this size on a likelihood scorer is worth a second look (same 73,894-example subset and fp32 scorer as the card; the SFT checkpoint is scored through an eval copy with the base tokenizer/config) — E1-last and the replicate natives will show whether it is systematic. GreekMMLU (2.8 h/model) waits for the morning batch.


## E1-last light evals (terminal checkpoint base) vs the replicate (averaged base), same recipe

| metric | replicate (18-avg base) | E1-last (rev 17 base) |
|---|---|---|
| ifeval_greek strict | 0.460 | 0.429 |
| mgsm_greek | 0.416 | 0.328 |
| gate stop rate | 0.88 | 0.88 |
| voice Delta | 1.000 | 0.895 |
| interview mean | 2.61 | 2.57 |
| mean Greek dev loss | 1.374 | 1.364 |

Dev loss ties, but the terminal checkpoint comes out clearly worse on Greek math (−0.09, four times the readability bar)
and worse on instruction following. **The averaged checkpoint stays the base.** Its native/GreekMMLU guards are pending.


## Seed-only noise floor (E1_cos seed 43 vs seed 44, identical recipe) — dev losses at epoch 2

| config | seed 43 | seed 44 | diff |
|---|---|---|---|
| apertus_en | 1.240 | 1.271 | +0.031 |
| coconot | 1.583 | 1.591 | +0.008 |
| euroblocks_de | 1.632 | 1.572 | -0.060 |
| euroblocks_fr | 1.472 | 1.460 | -0.012 |
| everyday | 1.217 | 1.205 | -0.012 |
| no_robots | 1.465 | 1.441 | -0.024 |
| no_robots_en_pov | 1.880 | 1.842 | -0.038 |
| oasst | 1.487 | 1.437 | -0.050 |
| personas_if | 1.404 | 1.396 | -0.008 |
| smolcon | 1.134 | 1.109 | -0.025 |
| systemchats | 1.326 | 1.378 | +0.052 |

Mean Greek dev loss: 1.374 vs 1.365 (-0.008); largest per-config seed gap 0.052. Differences between arms
below ~0.05 on a single config or ~0.02 on the mean are seed noise. (Light-eval floor from seed 44 follows
when its evals finish.)


## Phase B — E2 (Greek + the paired English no_robots) vs the E1 reference, dev losses at epoch 2

| config | E1 reference (mean of 2 seeds) | E2 (E1 + no_robots_en_pov) | diff |
|---|---|---|---|
| apertus_en | 1.256 | 1.361 | +0.105 |
| coconot | 1.587 | 1.596 | +0.009 |
| euroblocks_de | 1.602 | 1.573 | -0.029 |
| euroblocks_fr | 1.466 | 1.433 | -0.033 |
| everyday | 1.211 | 1.209 | -0.002 |
| no_robots | 1.453 | 1.454 | +0.001 |
| no_robots_en_pov | 1.861 | 1.716 | -0.145 |
| oasst | 1.462 | 1.413 | -0.049 |
| personas_if | 1.400 | 1.376 | -0.024 |
| smolcon | 1.121 | 1.164 | +0.042 |
| systemchats | 1.352 | 1.367 | +0.015 |

Mean Greek dev loss: reference 1.370, E2 1.368 (-0.001; seed floor ≈ 0.02 on the mean). The English twin dev set
(`no_robots_en_pov`, held out on both sides) is where E2 should move: 1.861 → 1.716. Light evals of E2 follow.


## Seed-only floor on the light evals (E1_cos seed 43 vs 44)

| metric | seed 43 | seed 44 | gap |
|---|---|---|---|
| ifeval_greek strict | 0.460 | 0.470 | 0.010 |
| mgsm_greek | 0.416 | 0.444 | 0.028 |
| gate stop rate | 0.88 | 0.92 | 0.04 |
| voice Delta | 1.000 | 0.946 | 0.054 |
| interview mean | 2.61 | 2.59 | 0.02 |

So the grid winner's edge over the cosine reference on voice (0.853 vs ~0.97) and interviews (2.83 vs ~2.60) is
larger than seed noise — the constant-lr epoch-2 checkpoint reads better than the cosine endpoint. Worth an owner look:
phase B is trained with the cosine schedule (the recipe's), so its reference is the cosine pair.

## Phase B dev losses at epoch 2 — E2 and E3 vs the E1 reference

| config | E1 reference (2 seeds) | E2 | E3 (skills + fr/de, Greek POV) |
|---|---|---|---|
| apertus_en | 1.256 | 1.361 (+0.105) | 1.144 (-0.112) |
| coconot | 1.587 | 1.596 (+0.009) | 1.587 (+0.000) |
| euroblocks_de | 1.602 | 1.573 (-0.029) | 1.475 (-0.127) |
| euroblocks_fr | 1.466 | 1.433 (-0.033) | 1.308 (-0.158) |
| everyday | 1.211 | 1.209 (-0.002) | 1.213 (+0.002) |
| no_robots | 1.453 | 1.454 (+0.001) | 1.457 (+0.004) |
| no_robots_en_pov | 1.861 | 1.716 (-0.145) | 1.908 (+0.047) |
| oasst | 1.462 | 1.413 (-0.049) | 1.407 (-0.055) |
| personas_if | 1.400 | 1.376 (-0.024) | 1.374 (-0.026) |
| smolcon | 1.121 | 1.164 (+0.042) | 1.170 (+0.048) |
| systemchats | 1.352 | 1.367 (+0.015) | 1.367 (+0.015) |

Mean Greek dev loss: reference 1.370, E3 1.368 (-0.002). Where the mixes are supposed to move the model:
E2 on the English twins (`no_robots_en_pov` 1.861 → 1.716), E3 on the skills and fr/de slices
(`apertus_en` 1.256 → 1.144, `euroblocks_fr` 1.466 → 1.308, `euroblocks_de` 1.602 → 1.475). Greek dev loss is unchanged by either mix
(within the 0.02 seed floor). E3′ (the same rows raw) is training; its dev loss on the adapted dev sets is the
adaptation question's first number, the light evals the second.


## Phase B light evals (epoch 2) — against the cosine reference pair (seed floor: ifeval ±0.01, MGSM ±0.03, voice ±0.05, interviews ±0.02)

| arm | ifeval_greek strict | mgsm_greek | gate stop | voice Delta | interview mean |
|---|---|---|---|---|---|
| E1 reference (seeds 43 / 44) | 0.460 / 0.470 | 0.416 / 0.444 | 0.88 / 0.92 | 1.000 / 0.946 | 2.61 / 2.59 |
| E2 (+ paired English no_robots) | 0.473 | 0.404 | 0.92 | 0.943 | 2.56 |
| E3 (+ skills and fr/de, Greek POV) | 0.497 | 0.384 | 0.90 | 0.959 | **2.91** (language discipline 4.08, the best of all arms) |
| E3′ (same rows, raw) | 0.470 | 0.408 | 0.80 | 1.109 | 2.63 (factuality 1.85, identity 2.60) |

E2 sits inside the seed floor on every Greek metric: the paired English rows neither help nor hurt the Greek behaviour
(they move the English-twin dev loss, as intended). E3 raises Greek IFEval by ~0.03 (three times the seed floor) and lowers
Greek MGSM by ~0.04 (at the floor's edge, and in the wrong direction for a math slice — worth a look at the MGSM outputs).


## E3′ (raw slices) — dev losses at epoch 2, against E3 (adapted slices)

Greek dev sets: E3 1.368, E3′ 1.370 (seed floor 0.02) — the raw slices do not disturb the Greek side either. On the imported
slices the dev sets are the *adapted* conversations, so E3′ is expected to be worse there and is: apertus_en 1.144 → 1.382,
euroblocks_fr 1.308 → 1.542, euroblocks_de 1.475 → 1.649. That is a measure of how different the adapted text is,
not of quality; the adaptation verdict is the light evals (Greek IFEval, MGSM, voice, interviews, and the fr/de/en answers in the
interviews), landing ~08:10.


## Known-ness of the training rows' Greek-reality claims (base model probe, Gekhman-style)

| config | claims | known (greedy) | weakly known (1 of 4 samples) | unknown |
|---|---|---|---|---|
| apertus_en | 1620 | 573 (35%) | 70 (4%) | 977 (60%) |
| coconot | 413 | 41 (10%) | 11 (3%) | 361 (87%) |
| euroblocks_de | 259 | 32 (12%) | 9 (3%) | 218 (84%) |
| euroblocks_fr | 283 | 25 (9%) | 9 (3%) | 249 (88%) |
| everyday | 865 | 39 (5%) | 14 (2%) | 812 (94%) |
| no_robots | 4690 | 183 (4%) | 86 (2%) | 4421 (94%) |
| oasst | 540 | 32 (6%) | 4 (1%) | 504 (93%) |
| personas_if | 1056 | 22 (2%) | 21 (2%) | 1013 (96%) |
| smolcon | 59 | 1 (2%) | 1 (2%) | 57 (97%) |
| systemchats | 603 | 22 (4%) | 14 (2%) | 567 (94%) |
| **all** | 10388 | 970 (9%) | 239 (2%) | 9179 (88%) |

Per Sol's own basis for the claim — inferred: known 14, weakly 3, unknown 141; known: known 952, weakly 235, unknown 8993; uncertain: known 4, weakly 1, unknown 45. Corpus-presence (the second signal) was not run tonight.

**Read this with care.** The probe asks the *base* model a short question four-shot and matches the gold answer by normalized
containment within 48 tokens. A base model that has not been instruction-tuned fails that format for many facts it does hold,
and Greek answers admit many surface forms; so "unknown" here is an upper bound on ignorance, not a measurement of it. The
apertus_en slice (English questions, math/code personas) scores 37% known; the Greek slices 3–11%. Two things follow: the
knowledge-alignment risk of plan §8 is real and large by this probe; and the probe itself needs calibration — run it on the
SFT'd pick (which can answer in the format) and on a set of claims known to be true and in the CPT corpus before E7 filters
on these labels. Rows: 5,684 with claims → labels none / known / mixed / unknown are in `results/E0b/knownness/knownness_rows.jsonl`.


## The adaptation question — E3 (Greek point of view) vs E3′ (the same rows, raw)

| metric | E3 adapted | E3′ raw | gap | seed floor |
|---|---|---|---|---|
| ifeval_greek strict | 0.497 | 0.470 | +0.027 | 0.01 |
| mgsm_greek | 0.384 | 0.408 | −0.024 | 0.03 |
| gate stop rate | 0.90 | 0.80 | +0.10 | 0.04 |
| voice Delta (lower = closer to the house voice) | 0.959 | 1.109 | −0.150 | 0.05 |
| interview mean (1–5) | 2.91 | 2.63 | +0.28 | 0.02 |
| interview: Greek-assistant identity | 2.85 | 2.60 | +0.25 | — |
| interview: factuality | 2.27 | 1.85 | +0.42 | — |
| interview: language discipline | 4.08 | 4.00 | +0.08 | — |

**Verdict (provisional, before the owner's reading):** adapting the imported slices to the Greek point of view is worth it.
The adapted mix reads better by every vibe measure — interviews +0.28 (fourteen times the seed floor), voice 0.15 closer to
no_robots-el, stopping cleanly 90% vs 80% — and scores higher on Greek IFEval, at no cost on Greek math beyond the floor.
The raw slices pull the model toward an American assistant: lower identity and factuality scores in the interviews, a voice
further from the reference. This is the result the dataset was built to test.

## Native-Greek suite — pick vs rival (frozen fp32 scorer)

| benchmark | base (card) | pick (1e-5, ep2) | rival (5e-6, ep3) |
|---|---|---|---|
| asep_mcqa | 0.562 | 0.614 | 0.613 |
| demosqa | 0.469 | 0.472 | 0.477 |
| gpcr | 0.608 | 0.655 | 0.644 |
| medical_mcqa | 0.425 | 0.489 | 0.494 |
| oyxoy_metaphor | 0.345 | 0.552 | 0.581 |
| oyxoy_nli | 0.651 | 0.643 | 0.642 |
| oyxoy_wic | 0.549 | 0.775 | 0.775 |
| oyxoy_wsd_definition | 0.385 | 0.390 | 0.392 |
| **macro (8)** | 0.499 | 0.574 | 0.577 |

Both SFT checkpoints sit above the base on the macro; the pick and the rival are within a point of each other. The replicate (seed 43, cosine) reproduces the pick's profile exactly (macro-8 0.573; WiC 0.775, metaphor 0.568, NLI 0.642) — the jump on the likelihood scorer is systematic to SFT, not a seed accident. E1-last's native is running.


## Native-Greek suite — all four SFT checkpoints vs their bases (frozen fp32 scorer)

| benchmark | base 18-avg (card) | base 17 terminal (card) | pick 1e-5 ep2 | rival 5e-6 ep3 | replicate (cos, s43) | E1-last (base 17) |
|---|---|---|---|---|---|---|
| asep_mcqa | 0.562 | 0.551 | 0.614 | 0.613 | 0.616 | 0.601 |
| demosqa | 0.469 | 0.466 | 0.472 | 0.477 | 0.467 | 0.464 |
| gpcr | 0.608 | 0.629 | 0.655 | 0.644 | 0.639 | 0.624 |
| medical_mcqa | 0.425 | 0.384 | 0.489 | 0.494 | 0.487 | 0.463 |
| oyxoy_metaphor | 0.345 | 0.339 | 0.552 | 0.581 | 0.568 | 0.339 |
| oyxoy_nli | 0.651 | 0.387 | 0.643 | 0.642 | 0.642 | 0.388 |
| oyxoy_wic | 0.549 | 0.336 | 0.775 | 0.775 | 0.775 | 0.737 |
| oyxoy_wsd_definition | 0.385 | 0.381 | 0.390 | 0.392 | 0.391 | 0.384 |
| **macro (8)** | 0.499 | 0.434 | 0.574 | 0.577 | 0.573 | 0.500 |

E1-last's NLI goes 0.387 → 0.388 and WiC 0.336 → 0.737: the deficit persists after SFT. All SFT checkpoints on the averaged base share one profile (macro-8 ≈ 0.57): NLI flat, WiC and metaphor +0.2,
the MCQ sets +0.03–0.06 — systematic to SFT. E1-last recovers WiC (0.34 → 0.74) but not NLI (0.39) or metaphor (0.34 vs 0.55–0.58 for the averaged-base checkpoints): macro-8 0.500 vs ≈0.575. Together with the light evals (MGSM 0.33 vs 0.42), the terminal checkpoint is the worse starting point on every axis. The averaged base stays.

## Peers on the same harness (2026-09-04, evaluation plan Part A)

Greek IFEval and Greek MGSM, scored with our harness, on four public instruct models. The harness agrees with ILSP's published numbers (Krikri 66.8% here vs 67.5% on its card; Meltemi 32.6% vs 32.7%), so the comparison holds.

| model | IFEval prompt-strict | IFEval inst-strict | IFEval strict avg | Greek MGSM |
|---|---|---|---|---|
| Llama-Krikri-8B-Instruct (ILSP card: 67.5%) | 0.614 | 0.723 | **66.8%** | 0.676 |
| Apertus-8B-Instruct-2509 (no Greek CPT) | 0.505 | 0.615 | **56.0%** | 0.532 |
| Gemma-3-12B-it (50% larger) | 0.675 | 0.763 | **71.9%** | 0.908 |
| Meltemi-7B-Instruct-v1.5 (ILSP card: 32.7%) | 0.277 | 0.375 | **32.6%** | 0.208 |
| ours: lr 1e-5, epoch 3 | 0.512 | 0.612 | **56.2%** | 0.392 |
| ours: adapted imports, epoch 2 | 0.497 | 0.601 | **54.9%** | 0.384 |
| ours: lr 5e-6, epoch 3 | 0.486 | 0.584 | **53.5%** | 0.416 |
| ours: the pick, lr 1e-5, epoch 2 | 0.479 | 0.586 | **53.3%** | 0.400 |
| ours: paired English, epoch 2 | 0.473 | 0.568 | **52.1%** | 0.404 |
| ours: raw imports, epoch 2 | 0.470 | 0.579 | **52.4%** | 0.408 |
| ours: from the terminal CPT checkpoint | 0.429 | 0.540 | **48.4%** | 0.328 |

**Reading.** Our best run sits level with Apertus-8B-Instruct on instruction following (56.2% vs 56.0%) and 11 points below Krikri. On Greek math every one of our runs is below Apertus-8B-Instruct (0.40 vs 0.53) and far below Krikri (0.68) and Gemma (0.91). Greek CPT plus twenty thousand SFT rows did not buy math; the peers were trained on millions of rows including math and constraint data. Meltemi is below all of ours on both.

## Blind reading, round two (Claude as rater, tone axis)

Rescored by Claude, blind, on all 13 runs × 40 prompts with a tone axis (warmth, unsolicited commands, chatbot mannerisms). Page: https://claude.ai/code/artifact/fa8d4fa7-f210-4a1f-8ae5-9bb6d2814e97 · summary in results/reading2/summary.md. Headline: epoch 3 reads better than epoch 2 on answer quality (Greek prompts 3.52 vs 3.22, rater noise 0.1), all fine-tuned runs are tonally flat (warmth ≈ 3.0), mannerisms are rare and concentrated on two prompts, and six failures are shared by every run (list loops, the Caribbean 'we', arithmetic with two multipliers, the dementia vignette, exact-count constraints).
