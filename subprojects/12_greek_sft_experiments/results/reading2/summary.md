# Reading evaluation, round two: summary

Blind scoring by Claude of 13 runs × 40 prompts (prompt 15 excluded: it contains its own answer). Scales: answers/greek/warmth 1–5; the rest are shares (0–1). command and mannerism are BAD when high.

### All 39 prompts

| run | n | answers | greek | stops | constraint_ok | warmth | command | mannerism | language_ok |
|---|---|---|---|---|---|---|---|---|---|
| base model (no SFT) | 39 | 1.13 | 2.26 | 0.00 | 0.00 | 1.72 | 0.05 | 0.03 | 0.97 |
| lr 1e-5, epoch 1 | 39 | 2.95 | 3.85 | 0.85 | 0.55 | 2.95 | 0.03 | 0.05 | 0.97 |
| the pick: lr 1e-5, epoch 2 | 39 | 3.13 | 3.87 | 0.87 | 0.55 | 2.92 | 0.03 | 0.03 | 1.00 |
| lr 1e-5, epoch 3 | 39 | 3.38 | 3.90 | 0.90 | 0.45 | 3.03 | 0.10 | 0.03 | 1.00 |
| lr 5e-6, epoch 1 | 39 | 2.79 | 3.59 | 0.59 | 0.45 | 2.87 | 0.03 | 0.03 | 0.87 |
| lr 5e-6, epoch 2 | 39 | 2.85 | 3.77 | 0.87 | 0.55 | 2.95 | 0.05 | 0.03 | 0.90 |
| lr 5e-6, epoch 3 | 39 | 3.21 | 3.90 | 0.90 | 0.55 | 2.97 | 0.00 | 0.05 | 1.00 |
| seed replicate 43 (cosine), epoch 2 | 39 | 3.10 | 3.95 | 0.92 | 0.36 | 3.03 | 0.03 | 0.05 | 1.00 |
| seed replicate 44 (cosine), epoch 2 | 39 | 3.00 | 3.90 | 0.92 | 0.64 | 2.97 | 0.03 | 0.03 | 0.97 |
| from the terminal CPT checkpoint, epoch 2 | 39 | 3.15 | 3.92 | 0.92 | 0.45 | 2.97 | 0.00 | 0.05 | 1.00 |
| Greek + paired English, epoch 2 | 39 | 3.00 | 3.92 | 0.90 | 0.36 | 3.00 | 0.05 | 0.05 | 1.00 |
| Greek + adapted imports, epoch 2 | 39 | 3.15 | 3.82 | 0.90 | 0.55 | 2.92 | 0.08 | 0.05 | 1.00 |
| Greek + raw imports, epoch 2 | 39 | 2.95 | 3.92 | 0.92 | 0.27 | 2.92 | 0.05 | 0.05 | 1.00 |

### Greek prompts only (30)

| run | n | answers | greek | stops | constraint_ok | warmth | command | mannerism | language_ok |
|---|---|---|---|---|---|---|---|---|---|
| base model (no SFT) | 27 | 1.11 | 2.26 | 0.00 | 0.00 | 1.67 | 0.07 | 0.04 | 0.96 |
| lr 1e-5, epoch 1 | 27 | 3.11 | 3.93 | 0.89 | 0.50 | 2.93 | 0.04 | 0.07 | 1.00 |
| the pick: lr 1e-5, epoch 2 | 27 | 3.22 | 3.89 | 0.89 | 0.50 | 2.89 | 0.04 | 0.04 | 1.00 |
| lr 1e-5, epoch 3 | 27 | 3.52 | 3.93 | 0.89 | 0.40 | 3.04 | 0.11 | 0.04 | 1.00 |
| lr 5e-6, epoch 1 | 27 | 2.93 | 3.74 | 0.70 | 0.50 | 2.81 | 0.04 | 0.04 | 1.00 |
| lr 5e-6, epoch 2 | 27 | 2.96 | 3.89 | 0.85 | 0.60 | 2.93 | 0.04 | 0.04 | 1.00 |
| lr 5e-6, epoch 3 | 27 | 3.48 | 3.96 | 0.89 | 0.60 | 2.96 | 0.00 | 0.07 | 1.00 |
| seed replicate 43 (cosine), epoch 2 | 27 | 3.26 | 4.00 | 0.93 | 0.40 | 3.04 | 0.04 | 0.07 | 1.00 |
| seed replicate 44 (cosine), epoch 2 | 27 | 3.11 | 3.96 | 0.93 | 0.60 | 2.96 | 0.04 | 0.04 | 1.00 |
| from the terminal CPT checkpoint, epoch 2 | 27 | 3.15 | 3.96 | 0.93 | 0.40 | 2.96 | 0.00 | 0.07 | 1.00 |
| Greek + paired English, epoch 2 | 27 | 3.15 | 3.96 | 0.89 | 0.40 | 3.00 | 0.07 | 0.07 | 1.00 |
| Greek + adapted imports, epoch 2 | 27 | 3.19 | 3.89 | 0.89 | 0.50 | 2.89 | 0.11 | 0.07 | 1.00 |
| Greek + raw imports, epoch 2 | 27 | 3.19 | 3.96 | 0.89 | 0.30 | 2.89 | 0.07 | 0.07 | 1.00 |

### English, French, German prompts (9)

| run | n | answers | greek | stops | constraint_ok | warmth | command | mannerism | language_ok |
|---|---|---|---|---|---|---|---|---|---|
| base model (no SFT) | 12 | 1.17 | 2.25 | 0.00 | 0.00 | 1.83 | 0.00 | 0.00 | 1.00 |
| lr 1e-5, epoch 1 | 12 | 2.58 | 3.67 | 0.75 | 1.00 | 3.00 | 0.00 | 0.00 | 0.92 |
| the pick: lr 1e-5, epoch 2 | 12 | 2.92 | 3.83 | 0.83 | 1.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| lr 1e-5, epoch 3 | 12 | 3.08 | 3.83 | 0.92 | 1.00 | 3.00 | 0.08 | 0.00 | 1.00 |
| lr 5e-6, epoch 1 | 12 | 2.50 | 3.25 | 0.33 | 0.00 | 3.00 | 0.00 | 0.00 | 0.58 |
| lr 5e-6, epoch 2 | 12 | 2.58 | 3.50 | 0.92 | 0.00 | 3.00 | 0.08 | 0.00 | 0.67 |
| lr 5e-6, epoch 3 | 12 | 2.58 | 3.75 | 0.92 | 0.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| seed replicate 43 (cosine), epoch 2 | 12 | 2.75 | 3.83 | 0.92 | 0.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| seed replicate 44 (cosine), epoch 2 | 12 | 2.75 | 3.75 | 0.92 | 1.00 | 3.00 | 0.00 | 0.00 | 0.92 |
| from the terminal CPT checkpoint, epoch 2 | 12 | 3.17 | 3.83 | 0.92 | 1.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| Greek + paired English, epoch 2 | 12 | 2.67 | 3.83 | 0.92 | 0.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| Greek + adapted imports, epoch 2 | 12 | 3.08 | 3.67 | 0.92 | 1.00 | 3.00 | 0.00 | 0.00 | 1.00 |
| Greek + raw imports, epoch 2 | 12 | 2.42 | 3.83 | 1.00 | 0.00 | 3.00 | 0.00 | 0.00 | 1.00 |

### Rater noise floor (two seed replicates of the same recipe)

answers 0.1, greek 0.05, language_ok 0.03, constraint_ok 0.28, stops 0.0, warmth 0.06, command 0.0, mannerism 0.02
