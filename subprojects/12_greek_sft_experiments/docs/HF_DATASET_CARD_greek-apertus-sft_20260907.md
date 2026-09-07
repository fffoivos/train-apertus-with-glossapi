---
language:
  - el
  - en
  - fr
  - de
  - es
  - it
  - pt
license: other
license_name: mixed-per-block
license_link: https://huggingface.co/datasets/fffoivos/greek-apertus-sft/blob/main/README.md
pretty_name: Greek Apertus SFT datasets
task_categories:
  - text-generation
tags:
  - greek
  - sft
  - instruction-tuning
  - apertus
  - glossapi
size_categories:
  - 100K<n<1M
configs:
  - config_name: round2_stage1
    data_files:
      - split: train
        path: round2_stage1/train.jsonl
      - split: validation
        path: round2_stage1/dev.jsonl
  - config_name: personality_v3
    data_files:
      - split: train
        path: personality_v3/train.jsonl
  - config_name: round1_E1
    data_files:
      - split: train
        path: round1_arms/E1_train.jsonl
      - split: validation
        path: round1_arms/E1_dev.jsonl
  - config_name: round1_E2
    data_files:
      - split: train
        path: round1_arms/E2_train.jsonl
      - split: validation
        path: round1_arms/E2_dev.jsonl
  - config_name: round1_E3
    data_files:
      - split: train
        path: round1_arms/E3_train.jsonl
      - split: validation
        path: round1_arms/E3_dev.jsonl
  - config_name: round1_E3prime
    data_files:
      - split: train
        path: round1_arms/E3prime_train.jsonl
      - split: validation
        path: round1_arms/E3prime_dev.jsonl
---

# Greek Apertus SFT datasets

The supervised fine-tuning data of the **Greek Apertus** project: the GlossAPI team of EELLAK (Open Technologies Alliance) continues the pre-training of `swiss-ai/Apertus-8B-2509` on Greek text and then trains it on instructions, with a grant from the Swiss AI Initiative. This repository holds every training arm we assembled, exactly as it went (or goes) to the trainer: one `messages` list per row, chat format, no system turn.

Access is gated: request it and the maintainer approves colleagues and collaborators.

## Configs

| config | split | rows | tokens (Greek-CPT tokenizer) | what it is |
|---|---|---:|---:|---|
| `round2_stage1` | train | 334,383 | 197.9M | Round-two stage-1 mix (September 2026): broad skills in any language, screened for foreign identity and foreign vantage, plus our Greek sets at weight 2 |
| `round2_stage1` | validation | 3,171 | 1.9M | held-out dev slice of the same mix |
| `personality_v3` | train | 1,388 | — | the Greek personality set: Greece-centric facts from the Greek vantage, who-am-I, identity under pressure, limits, refusals in our voice, sensitive Greek topics, register (see below) |
| `round1_E1` | train / validation | 17,602 / 658 | 6.2M | Round-one arm E1: Greek-only, eleven adapted configs |
| `round1_E2` | train / validation | 26,910 / 658 | 9.4M | E1 plus paired English rows |
| `round1_E3` | train / validation | 22,919 / 658 | 9.0M | E1 plus skills and fr/de rows adapted to the Greek vantage |
| `round1_E3prime` | train / validation | 22,910 / 658 | 10.5M | the same rows as E3, unadapted (the control) |

Row schema: `{"messages": [{"role": "user"|"assistant", "content": ...}, ...]}`; round-two rows also carry `config` (the source block) and `id`; round-one rows carry `row_id`, `config`, `category`; personality rows carry `id` and `category`.

## round2_stage1: composition

Assembled with an exact tokenizer count under a 208M-token budget (receipt in `receipts/`). Every block was judged row by row (task type, mannerisms, foreign-identity or foreign-vantage assertions) by an LLM judge before assembly; contaminated rows (overlap with our evaluation sets) and over-long rows were removed.

| block | source | rows taken | tokens | weight |
|---|---|---:|---:|---:|
| dolci_precise_if_20k | `allenai/Dolci-Instruct-SFT`, Precise IF (judge-screened) | 3,934 | 2.17M | 1 |
| ifeval_like | `argilla/ifeval-like-data` | 46,619 | 12.95M | 1 |
| openmath_gsm | `nvidia/OpenMathInstruct-2`, GSM8K-style | 91,458 | 25.31M | 1 |
| nemotron_chat_a / _b | NVIDIA Nemotron post-training chat split, halves A and B | 23,250 + 23,497 | 72.47M | 1 |
| dolci_chat | OpenAssistant conversations via Dolci | 3,039 | 1.12M | 1 |
| dolci_code_algo_20k | Dolci Python algorithms (judge-screened) | 5,084 | 2.24M | 1 |
| dolci_reasoning | Dolci verifiable reasoning | 27,445 | 15.46M | 1 |
| puzzles | Dolci logic puzzles and word sorts (brute-force verified) | 11,139 | 4.16M | 1 |
| dolci_tooluse | Dolci tool use | 27,445 | 28.42M | 1 |
| dolci_science | Dolci OpenThoughts3+ science (judge-screened) | 6,176 | 5.66M | 1 |
| smoltalk2_multilingual | `HuggingFaceTB/smoltalk2`, de/fr/es/pt/it | 20,412 | 11.26M | 1 |
| dolci_safety | Dolci WildGuardMix + CoCoNot | 6,256 | 1.78M | 1 |
| greek_rewrite | our Greek rewriting and summarising set | 2,000 | 1.20M | 1 |
| greek_ours | our round-one Greek set (translated and adapted to the Greek vantage) | 20,000 | 7.80M | 2 |

## personality_v3

1,388 Greek rows written natively (Opus 5) from a verified fact sheet and an identity sheet, restyled under an answer style guide (level of detail by question type), corrected by a separate editor pass, and gated (no unresolved placeholders; size and borders of Greece always with the sea and the EEZ; identity wording).

| category | rows | content |
|---|---:|---|
| A | 660 | Greece-centric facts answered from the Greek vantage ("we", "here" = Greece) |
| B | 180 | who am I: an open project of the GlossAPI team of EELLAK on Apertus 8B, no name of its own |
| C | 100 | identity under pressure (claims of being another model, jailbreak framings) |
| D | 120 | limits (knowledge cutoff, no browsing, no images, no memory) |
| E | 120 | refusals in our voice |
| F | 88 | sensitive Greek topics, sober and factual |
| G | 120 | register (formal, informal, greeklish, no accents) |

The knowledge-cutoff wording and the licence named inside these rows are the project's current proposals.

## Licences

The blocks keep the licences of their sources; check the source card before redistribution. Our own rows (`greek_rewrite`, `greek_ours`, `personality_v3`, and the round-one Greek adaptations) are released under the licence of the sources they derive from where they are derived, and otherwise under the project licence to be announced with the model. In particular, the round-one Greek rows adapted from `HuggingFaceH4/no_robots` inherit its non-commercial terms.

## Provenance

Project repository: GlossAPI / EELLAK, `train-apertus-with-glossapi`, subproject 12. Receipts with per-block counts, contamination and screening numbers are in `receipts/`.
