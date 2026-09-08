# R2_idA (Greek pass)

replay fraction 0.05, seed 2026, personality weight 2. train 39059 rows, dev 3240 rows (stage-1 dev + 69 personality rows held out).

| block | rows |
|---|---|
| greek_ours | 19800 |
| openmath_gsm | 4527 |
| personality_v3 | 2638 |
| ifeval_like | 2308 |
| greek_rewrite | 1980 |
| dolci_reasoning | 1359 |
| dolci_tooluse | 1359 |
| nemotron_chat_b | 1163 |
| nemotron_chat_a | 1151 |
| smoltalk2_multilingual | 1010 |
| puzzles | 551 |
| dolci_safety | 310 |
| dolci_science | 306 |
| dolci_code_algo_20k | 252 |
| dolci_precise_if_20k | 195 |
| dolci_chat | 150 |

Sources: greek_ours and greek_rewrite = every unique row of the stage-1 arm (weight-2 duplicates collapsed); replay = a seeded 10% of each other stage-1 block; personality_v3 = data/personality/v3/full_20260906/edited.jsonl. Aya Greek left out (owner decision open, plan §7.4).
