# Experiment registry (G/F/P names)

Adopted scheme (astra 13 Sept; owner 14 Sept): **the names identify trained models.** G = Greek data generation, F = foreign data generation, P = number of training stages with dedicated personality supervision in the ancestry; **--NN** = test within a family; **@epochN** = checkpoint. Internal dataset revisions keep internal names (greek_math_v2A/B/C, math_en_v1, suite_v2, correcting_v2, personality_v3_repaired) and never consume a G/F number; which variant a test used is part of its test details. Storage paths and job names keep the legacy labels; reports use the names. A provisional name is bound to its frozen manifest (sha256) at freeze. Machine-readable source: `data/gfp_registry.json`; helper: `data/gfp_names.py`.

## Base symbol (added 14 Sept 15:10)

A different CPT base is a different lineage, so the base is a leading component of the name: **1** = uniform average of the 30–50B CPT checkpoints (every model so far except one), **2** = the terminal 77B checkpoint (only 2-G1F0P0, the round-one base test), **3** reserved for the cooldown-window average. In prose the format is <base>-G…F…P…; the test suffix --NN appears only when tests of one family are distinguished (the three pilots), otherwise the name means the current/best test.

## Data generations introduced on 14 Sept

| Generation | Content |
|---|---|
| G4 | fourth Greek data generation (14 Sept): the G2 core plus the maths-v2 campaign; internal variants greek_math_v2A (cut-1 terse targets with the answer boxed + native), greek_math_v2B (cut-2 worked targets on the same problems + native), greek_math_v2C (v2B + Level 5); the pass adds suite_v2 x2, correcting_v2 x2 and personality_v3_repaired |
| F6 | foreign data generation used by the G4 line: the F1 foundation with the OpenMath block replaced by math_en_v1 (GSM8K <= 3 solutions per problem, 22,211 rows + 7,328 published MATH train solutions, 172 MATH-500 near-duplicates dropped) |

## Experiments

| Name | Legacy label | Parent | Test details | Status |
|---|---|---|---|---|
| G1F0P0--00 | E1_lr1e-5_3ep_const | cpt-average | LR 1e-05, constant_with_warmup, seed 42, 3 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F0P0--01 | E1_lr5e-6_3ep_const | cpt-average | LR 5e-06, constant_with_warmup, seed 42, 3 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F0P0--02 | E1_cos | cpt-average | LR 1e-05, cosine_with_min_lr, seed 43, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F0P0--03 | E1_cos_s44 | cpt-average | LR 1e-05, cosine_with_min_lr, seed 44, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| 2-G1F0P0 | E1last_cos | cpt-terminal | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F3P0 | E2_cos | cpt-average | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F4P0 | E3_cos | cpt-average | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| G1F5P0 | E3prime_cos | cpt-average | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G2F1P0 | R2_stage1 | cpt-average | LR 1e-05, cosine_with_min_lr, seed 42, 1 epoch(s) | bound (adopted registry, 13 Sept) |
| G2F1P1--00 | R2_stage2 | 1-G2F1P0@epoch1 | LR 5e-06, cosine_with_min_lr, seed 42, 1 epoch(s) | bound (adopted registry, 13 Sept) |
| G2F1P1--01 | R2_idA | 1-G2F1P0@epoch1 | LR 1e-05, cosine_with_min_lr, seed 42, 1 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G2F1P1 | R2_idB | 1-G2F1P0@epoch1 | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G3F2P1 | R3_single | cpt-average | LR 1e-05, cosine_with_min_lr, seed 42, 1 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G3F2P2--00 | 1-G3F2P2--00 | 1-G3F2P1@epoch1 | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G3F2P2--01 | 1-G3F2P2--01 | 1-G3F2P1@epoch1 | LR 1e-05, cosine_with_min_lr, seed 42, 2 epoch(s) | bound (adopted registry, 13 Sept) |
| 1-G4F6P0--00 | M0 | 1-G2F1P0@epoch1 | greek_math_v2A (terse + boxed control) + math_en_v1 + 10% replay of every non-maths 1-G2F1P0 config; LR 1e-5 cosine; 1 epoch; seed 42 | provisional_until_manifest_frozen |
| 1-G4F6P0--01 | M1 | 1-G2F1P0@epoch1 | greek_math_v2B (worked, same problem ids) + math_en_v1; otherwise identical to --00 | provisional_until_manifest_frozen |
| 1-G4F6P0--02 | M2 | 1-G2F1P0@epoch1 | greek_math_v2C (worked + Level 5) + math_en_v1; otherwise identical to --00 | provisional_until_manifest_frozen |
| 1-G4F6P1 | R4_pass | <pilot winner>@epoch1@epoch1 | Greek pass on the winning pilot checkpoint: personality_v3_repaired x4 (first personality stage of this line), suite_v2 x2, correcting_v2 x2, maths 15% of supervised tokens, 5% replay; LR 1e-5 cosine; 2 epochs | provisional_until_manifest_frozen |

Tree from 14 Sept: 1-G2F1P0@epoch1 → 1-G4F6P0--00 / --01 / --02 (the three maths pilots, one data generation, three internal maths-block variants); winner@epoch1 → 1-G4F6P1 (the Greek pass). Incumbents: 1-G2F1P1@epoch2, 1-G3F2P2--00@epoch2 (1-G3F2P2--00).
