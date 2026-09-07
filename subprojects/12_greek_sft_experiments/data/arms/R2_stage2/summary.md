# R2_stage2 (Greek pass)

replay fraction 0.1, seed 2026. train 52379 rows, dev 3240 rows (stage-1 dev + 69 personality rows held out).

| block | rows |
|---|---|
| greek_ours | 19800 |
| openmath_gsm | 9054 |
| ifeval_like | 4615 |
| dolci_tooluse | 2717 |
| dolci_reasoning | 2717 |
| nemotron_chat_b | 2326 |
| nemotron_chat_a | 2302 |
| smoltalk2_multilingual | 2021 |
| greek_rewrite | 1980 |
| personality_v3 | 1319 |
| puzzles | 1103 |
| dolci_safety | 619 |
| dolci_science | 612 |
| dolci_code_algo_20k | 503 |
| dolci_precise_if_20k | 390 |
| dolci_chat | 301 |

Sources: greek_ours and greek_rewrite = every unique row of the stage-1 arm (weight-2 duplicates collapsed); replay = a seeded 10% of each other stage-1 block; personality_v3 = data/personality/v3/full_20260906/edited.jsonl. Aya Greek left out (owner decision open, plan §7.4).
