# Results: 1-G4F6P1 versus the incumbent, round 3, Apertus-Instruct and Krikri (15 Sept 2026)

| measure | 1-G4F6P1 (new) | 1-G2F1P1 (incumbent) | 1-G3F2P1 (round 3) | Apertus-Instruct | Krikri 1.5 | Krikri 1.0 |
|---|---:|---:|---:|---:|---:|---:|
| IFEval-el (prompt-strict) | 60.8 | 58.6 | 62.8 | 53.8 | — | 64.7 |
| MGSM-el | 44.4 | 52.4 | 48.8 | 53.2 | — | 67.6 |
| MATH-500-el | 13.0 | 7.6 | 8.0 | — | 38.4 | 32.2 |
| MATH-500-en | 13.4 | 15.8 | 18.0 | — | 41.6 | 31.2 |
| MATH-200-el confirm | 16.0 | — | — | 11.0 | 39.0 | — |
| GreekMMLU official | 69.4 | 68.6 | 68.7 | — | 67.7 | 67.9 |
| GreekMMLU chat | 67.7 | — | — | — | — | — |
| Global-MMLU (chat) | 55.1 | 44.8 | — | 53.9 | — | — |
| ARC-C (chat) | 55.8 | 49.4 | — | 54.0 | — | — |
| HellaSwag (chat) | 70.7 | 71.4 | — | 73.7 | — | — |
| MT-Bench-el | 4.26 | — | — | 4.37 | 4.88 | — |
| MT-Bench-en | 4.38 | — | — | 4.91 | 5.65 | — |
| native oyxoy_wic | 68.7 | 66.9 | 70.7 | — | — | — |
| native oyxoy_wsd_definition | 38.8 | 39.6 | 39.7 | — | — | — |
| native asep_mcqa | 59.5 | 60.2 | 59.7 | — | — | — |
| native gpcr | 64.9 | 66.5 | 66.5 | — | — | — |
| native medical_mcqa | 47.0 | 48.4 | 48.0 | — | — | — |
| native oyxoy_metaphor | 49.3 | 54.0 | 45.4 | — | — | — |
| native oyxoy_nli | 61.2 | 58.0 | 65.8 | — | — | — |
| native demosqa | 47.1 | 45.6 | 46.9 | — | — | — |
| native macro avg (8) | 54.6 | 54.9 | 55.3 | — | — | — |
| ARC-el | — | — | — | — | — | — |
| HellaSwag-el | — | — | — | — | — | — |
| TruthfulQA-el | — | — | — | — | — | — |
| Medical MCQA | — | — | — | — | — | — |
| Belebele-el | — | — | — | — | — | — |
| MMLU-el | — | — | — | — | — | — |

Protocols: IFEval-el langdetect-rescored prompt-strict; MGSM-el exact match; MATH-500/200 equiv500 (scorer v2); GreekMMLU official letter protocol and the chat protocol of record; retention chat = template + few-shot as dialogue; MT-Bench Sol single-answer grading (mean of both turns); Krikri suite with ILSP prompts (new model and Apertus in chat mode, Krikri in base mode). "—" = not measured.

## Judged and behavioural sets (16 Sept, Sol judge unless stated)

| measure | 1-G4F6P1 (new) | 1-G2F1P1 (incumbent) | Krikri 1.5 | others |
|---|---:|---:|---:|---|
| Mixed-profile dialogues (60): coherent | 85.9 % | 78.6 % (120, 9 Sept) | — | |
| tone fine | 80.4 % | 75.7 % | — | |
| standing instruction kept | 92.3 % | 67.6 % | 51.3 % | |
| requests honoured | 62.2 % | 45.2 % | 63.1 % | |
| stop honoured | 100 % | 100 % | 100 % | |
| dead dialogues | 6.7 % | 8.3 % | 1.7 % | |
| tail copy | 8.3 % | 5.8 % | 1.0 % | |
| premise score | 0.57 | 0.90 | 0.53 | |
| loop rate | 0.0 | 0.001 | 0.0 | |
| Greek-quality blind review (1–5, 60 dialogues) | 3.98 | 3.81 | 2.71 | Krikri 1.0 3.20 |
| MultiChallenge-el pass | 16.8 % | not judged | 13.7 % | Qwen3.5-9B 24.8, Gemma-3-12B 15.6, Krikri 1.0 16.4, Meltemi 11.8, Apertus-Instruct 11.1 |
| XSTest-el safe: full compliance / adequacy | 231/250, 0.764 | not judged | 226/250, 0.744 | |
| XSTest-el unsafe: full refusal / full compliance | 174/200, 26 | not judged | 183/200, 15 | Meltemi 26, Qwen 20, Apertus 17, Gemma 13 |
| IFBench-el / -en prompt-strict | 9.7 / 14.7 | — | 8.3 / 12.7 | |
| MATH-500-el truncations (of 500) | 34 | 29 | — | round 3: 96 |

## Predeclared promotion criteria (plan §10), evaluated 16 Sept 06:20

1. No regression beyond tolerance on IFEval-el (+2.2 pp ✓), MGSM-el (**−8.0 pp ✗**, tolerance 3), GreekMMLU official (+0.8 pp ✓), MT-Bench-el (incumbent never measured → not evaluable).
2. MATH-500-el behaviour: truncations 34 ≤ 65 ✓; loops not counted separately this run (dialogue loop rate 0.0; no repeated-line runaway seen in the responses) ✓; non-Greek prose not measured.
3. Chat-mode retention within 1 pp: Global-MMLU +10.3, ARC-C +6.4, HellaSwag −0.7 ✓.
4. At least one headline improvement beyond tolerance: MATH-500-el +5.4 pp ✓ (also GreekMMLU official +0.8 > 0.5); native macro average −0.3 (no).

**Verdict under the frozen rule: HOLD (criterion 1 fails on MGSM-el alone).** The owner's programme of 15 Sept 19:20 is RLHF on this model regardless; the decision is the owner's.

Provenance: manifest train sha256 97d338ba… (384,010 rows, no-exclusion rule), job 3409558 (6 h 39 min, train_loss 0.966), checkpoint `runs/R4_full/epoch1`, eval copy `eval_copies/R4_full_ep1`; ledger after the chain CHF 222.76 of 240. Deferred: Krikri's six (PHASE K; maintenance reservation, est. start 19:00) and Apertus-Instruct's official GreekMMLU (driver poll cap). Per-item outputs: `results/R4_full_ep1/` (light evals, native, retention), `results/R4_full/bench_R4/` (benchmarks + judged files), `results/R4_full/r_R4/` (dialogues), `results/R4_full/greek_quality/`.
