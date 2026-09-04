# Round one — provisional readout (autonomous run, 2026-09-04 05:20)

**Status:** the phase-A grid (two learning rates × three epochs) is trained and measured on the light evals. The
provisional pick is **lr 1e-5, 2 epochs**. The replicate (seed 43) and the E1-last arm are training on it now. The
blind reading (owner) and the native-suite / GreekMMLU guards are still open, so nothing here is final.

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
