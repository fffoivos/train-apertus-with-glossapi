# Cross-lingual transfer for Greek SFT on an Apertus-8B Greek-CPT base

Source-grounded research report. Date: 2026-09-19.
Every claim is tagged **VERIFIED (URL)** = read from the primary source in this session, or
**RECALLED** = from model memory, not re-verified. Numbers are quoted, never inferred.

---

## 0. Headline findings (read this if nothing else)

1. **The maths gap is almost certainly a BASE-MODEL gap, not an SFT-data gap.** In the Apertus
   tech report's own table, with one common harness:
   Apertus-8B-Instruct **Hendrycks MATH 18.2 / GSM8K 62.9 / MGSM 48.5** vs
   Llama-3.1-8B-Instruct **MATH 36.3 / GSM8K 84.5 / MGSM 67.7**.
   That ~2x MATH gap is the *same* gap you observe between your model (English MATH-500 13–16)
   and Krikri (Greek MATH-500 32–38). Apertus-8B-Instruct reached 18.2 *with* 485,526 maths SFT
   examples. You are already at the family ceiling. **VERIFIED**
   (https://arxiv.org/pdf/2509.14233, Table 18)

2. **But one lever is genuinely untested**: Apertus used ~485K maths rows; OpenMathInstruct-2 is
   14M rows and lifts Llama-3.1-8B-Base to **MATH 67.8** (vs 51.9 for Llama-3.1-8B-Instruct in
   NVIDIA's harness). Nobody has run maths SFT at that scale on an Apertus base. Your plan is
   worth running — but as a *test of the base*, with a pre-registered kill criterion.
   **VERIFIED** (https://arxiv.org/pdf/2410.01560)

3. **Krikri's SFT was ~43–44% Greek, not a "small Greek share".** Exact, from the model card:
   Stage 1 856,946 pairs = **371,379 Greek + 485,567 English**; Stage 2 638,408 = **279,948 Greek
   + 358,460 English**; DPO 92,394 = **47,132 Greek + 45,262 English**. **VERIFIED**
   (https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct)

4. **A likely measurement artifact you must rule out first.** Apertus's SFT explicitly *stripped*
   `\boxed{}` from maths responses ("Mathematical datasets undergo post-processing to remove
   `\boxed{}` formatting from assistant responses if present, enabling more natural response
   generation"). Krikri's Stage 2 explicitly *added* responses "including reasoning steps"/a
   "thinking" section. If your MATH-500 answer extractor keys on `\boxed{}`, it systematically
   under-scores the Apertus lineage and over-scores Krikri. **VERIFIED**
   (https://arxiv.org/pdf/2509.14233 §4.1.3; https://arxiv.org/pdf/2505.13772)

5. **The real risk of English-heavy SFT is not lost maths skill — it is losing Greek output.**
   English-centric instruction tuning collapsed non-Latin-script monolingual line-level pass rate
   from **98.5 (Llama-2-70B base) → 6.0 (Llama-2-70B-Instruct)** and **94.7 → 12.1** for
   Llama-3-70B. Greek is non-Latin script. **VERIFIED**
   (https://aclanthology.org/2024.emnlp-main.380.pdf, Table 6)

6. **Language fidelity and maths accuracy trade off against each other, measurably.** QAlign:
   adding En→X data raised MGSM question–response language consistency 9.7 → 52.3 avg, but
   *dropped* MGSM accuracy 49.6 → 41.0. **VERIFIED** (https://arxiv.org/pdf/2405.01345, Table II)

---

## 1. Cross-lingual transfer of SFT-taught skills

### 1.1 Shaham et al. 2024, "Multilingual Instruction Tuning With Just a Pinch of Multilinguality"

**VERIFIED** (https://arxiv.org/abs/2401.01854 ; https://aclanthology.org/2024.findings-acl.136/ ;
full text via https://ar5iv.labs.arxiv.org/html/2401.01854)

- Base model: **PaLM 2-S** tuned; **PaLM 2-L** as LLM judge.
- Tuning set: **1,000 LIMA + 3,640 OpenAssistant ≈ 4,640 English examples**, machine-translated
  (Google Translate API) into 12 languages.
- 12 languages: Arabic, Chinese, Czech, English, Estonian, Finnish, Hebrew, Hindi, Italian,
  Russian, Spanish, Swahili. (Note: **Greek is not among them**; Hebrew and Arabic are the
  non-Latin mid-resource proxies.)
- Headline: replacing **1% of the English set — ~40 examples spread over 11 languages** —
  "substantially improve[s] multilingual instruction-following, both in seen and unseen languages".
- Models tuned on multilingual mixtures matched or beat monolingually-tuned models "despite
  training on 10x fewer examples in those languages".
- Diversifying to even **2–4 languages** significantly improved cross-lingual generalisation.
- Evaluation: side-by-side LLM-judge win/tie/loss, "discounted-tie weighted average". Human
  agreement with judge: 79.5% (En), 77% (Es), 76.5% (Ru), 75% (He).

**Caveats that matter for you (important — do not over-apply this paper):**
- **The task is open-ended instruction following, not maths.** There is no MGSM/MATH result here.
- **PaLM-2 is pretrained on "hundreds of languages"** — the paper's own framing distinguishes it
  from English-centric models like LLaMA. The "pinch" works because the *pretrained* model already
  has the language; SFT only has to *elicit* it. Your CPT'd model is in the same favourable
  position for Greek. This is the single reason the "1% is enough" result is likely to hold for
  your **chat/IF** capability.
- Authors' stated limitation: data was Google-Translate MT, "not originally sourced by native
  speakers".

### 1.2 Kew, Schottmann, Sennrich 2024, "Turning English-centric LLMs Into Polyglots"

**VERIFIED** (https://arxiv.org/abs/2312.12683 ; https://aclanthology.org/2024.findings-emnlp.766/ ;
full text via https://ar5iv.labs.arxiv.org/html/2312.12683)

- Models: **Llama-2-7B (primary), Llama-2-70B, Falcon-7B, Llama-3-8B**.
- Data: **3,200 unique English instances** as the monolingual baseline; non-English added at
  **200 examples per language** (es, ru, de, zh, fr).
- Five tasks: AlpacaEval single-turn dialogue, MultiSim simplification, XQuAD, X-CSQA, XNLI.
- **Core finding: 2–3 languages in instruction tuning is "both necessary and sufficient" for
  effective cross-lingual generalisation.** Bilingual gives a significant jump; trilingual
  plateaus; 4+ adds nothing.
- **The limiting factor is how much the target language was seen in PRETRAINING.**
- Multilingual tuning helps most for **generative tasks that assume input/output language
  agreement (chat)**; it matters little for structured classification.
- **Greek is explicitly classified LOW-RESOURCE here** (with Hindi and Icelandic), relative to
  Llama-2 pretraining. Low-resource languages "showed poor performance regardless of tuning
  approach" and outputs were "mostly nonsensical" despite passing language ID.
- They measured input/output language agreement with **OpenLID**.

**Read-across:** this paper's negative result for Greek is a result about *Llama-2's pretraining*,
not about Greek. Your 80B-token Greek CPT is precisely the intervention that moves Greek out of
that bucket. The paper's own causal claim ("the limiting factor is pretraining exposure") is
therefore an argument that a small Greek SFT share should now be *enough* for language fidelity —
provided you verify Greek fluency directly rather than assuming it.

### 1.3 Chen et al. 2024, "Monolingual or Multilingual Instruction Tuning: Which Makes a Better Alpaca"

**VERIFIED** (https://arxiv.org/abs/2309.08958 ; https://aclanthology.org/2024.findings-eacl.90/)

- Alpaca + machine translations; LoRA and full-parameter tuning.
- "Under a controlled computation budget, multilingual tuning is **on par or better than** tuning
  a model for each language."
- "Multilingual tuning **with downsampled data** can be as powerful and more robust."
- *Not re-verified in this session:* per-language numeric tables. Treat the direction as verified,
  the magnitudes as **RECALLED**.

### 1.4 MathOctopus / MGSM8KInstruct (Chen et al. 2023)

**VERIFIED** (https://arxiv.org/abs/2310.20246 ; full text via
https://ar5iv.labs.arxiv.org/html/2310.20246)

- **MGSM8KInstruct ≈ 73,600 samples**, 10 languages: En, Bn, Zh, Fr, De, Ja, Ru, Es, Sw, Th.
- Two regimes: **parallel-training** (question and answer both in the native language) vs
  **cross-training** (English question, answer in one native language).
- GSM8K (English!) results — note the multilingual data *raised monolingual English* too:
  - 7B: LLaMA-2 baseline **42.4** → MathOctopus-P **49.3** → MathOctopus-C **50.8**
  - 13B: LLaMA-2 baseline **51.0** → MathOctopus-P **55.5** → MathOctopus-C **56.6**
- MathOctopus-13B scores **47.6 on MGSM**, above ChatGPT's 46.3 (as reported by the authors).
- Paper's conclusion: "crafting multilingual corpora can be regarded as a vital strategy for
  enhancing model performance in a specific language, especially in mathematical reasoning."
- *Not extracted cleanly:* the full per-language MGSM breakdown (Thai/Swahili/Bengali rows). The
  aggregate numbers above are verified; per-language cells are **RECALLED / unverified**.

**Read-across:** this is the strongest pro-"translate your maths data" evidence, and it cuts
against a pure-English plan. But it is a LLaMA-2 result at 7–13B where the English maths baseline
was weak (42.4); the gains may be partly "more maths data of any kind".

### 1.5 Zhu et al. 2024, Question Translation Training / QAlign — the most directly useful paper

**VERIFIED** (https://arxiv.org/abs/2401.07817 ; extended version
https://arxiv.org/pdf/2405.01345 — numbers below are from the extended version's Tables II and IV)

Setup: **QAlign** = stage-I finetuning on X→English *question translation*; **RAlign** = ordinary
response alignment on English question–response maths pairs (MetaMathQA). So "RAlign alone" is
essentially *your current plan*: English-only maths SFT.

MGSM, 10 languages:

| Family | System | Non-En | En | Avg |
|---|---|---:|---:|---:|
| LLaMA-2 | RAlign (7B) — English-only SFT | 35.4 | 65.5 | 38.4 |
| LLaMA-2 | QAlign→RAlign (7B) | **47.6** | 68.0 | **49.6** |
| LLaMA-2 | RAlign (13B) | 41.2 | 68.4 | 43.9 |
| LLaMA-2 | QAlign→RAlign (13B) | **55.7** | 69.2 | **57.1** |
| LLaMA-2 | RAlign (70B) | 47.7 | 78.4 | 50.8 |
| LLaMA-2 | QAlign→RAlign (70B) | **61.5** | 76.0 | **63.0** |
| LLaMA-3 | RAlign (8B) | 47.3 | 74.4 | 50.0 |
| LLaMA-3 | QAlign→RAlign (8B) | **58.4** | 72.0 | **59.8** |
| Mistral | RAlign (7B) | 35.2 | 70.4 | 38.7 |
| Mistral | QAlign→RAlign (7B) | **48.2** | 70.8 | **50.4** |

Two things to take from this:

**(a) English-only maths SFT already transfers a lot.** LLaMA-3-8B with English-only maths SFT
gets **47.3 non-English MGSM**. That is real cross-lingual transfer with zero target-language
maths data. Your Greek MGSM 44–52 is consistent with this regime.

**(b) The catch — the model answers in English.** Table II, 7B, MGSM:

| System | Bn | Th | Sw | Ja | Zh | De | Fr | Ru | Es | En | **Avg** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Question–response language consistency** | | | | | | | | | | | |
| QAlign→RAlign w/o En-X training | 0.0 | 0.0 | 2.9 | 0.0 | 0.0 | 0.5 | 0.1 | 0.1 | 0.0 | 93.8 | **9.7** |
| QAlign→RAlign w/ En-X training | 26.8 | 42.7 | 49.3 | 63.1 | 26.8 | 63.2 | 36.9 | 82.4 | 37.9 | 93.4 | **52.3** |
| **Reasoning accuracy** | | | | | | | | | | | |
| QAlign→RAlign w/o En-X translation | 32.4 | 39.6 | 40.4 | 44.0 | 48.4 | 54.8 | 56.8 | 52.4 | 59.6 | 68.0 | **49.6** |
| QAlign→RAlign w/ En-X translation | 21.2 | 21.6 | 24.8 | 28.0 | 41.6 | 50.8 | 55.2 | 45.6 | 54.4 | 66.4 | **41.0** |

Authors' own words: "Future research needs to address this trade-off and find a better balance
between language consistency and reasoning accuracy. In the following experiments... **for the
sake of reasoning accuracy, we do not include translation data** in stage II training."

**This is the central tension for your plan.** Pure English maths SFT → 9.7% of MGSM answers in
the question's language. Forcing target-language output → −8.6 points of MGSM accuracy. You cannot
have both for free at 7B.

### 1.6 LangBridge (Yoon et al. 2024)

**VERIFIED that it exists and targets this problem** (https://arxiv.org/pdf/2401.10695).
Zero-shot approach: bridge a multilingual encoder (mT5) into a reasoning LM so multilingual
reasoning is obtained "without multilingual supervision"; evaluated on MGSM with 11 languages
against MetaMath. Specific per-language gains **not extracted in this session — RECALLED**.
Architectural change, high engineering cost; **not recommended for your timeline**.

### 1.7 MindMerger, xCoT, mCoT

**RECALLED, not verified in this session.** All three are in the same family: align a multilingual
encoder/representation or distil cross-lingual CoT so English reasoning is reused for non-English
questions. Directionally they agree with QAlign (English is the reasoning "pivot"). **Do not cite
numbers from these without checking the primary sources.**

### 1.8 PolyMath (Qwen, NeurIPS 2025 D&B)

**VERIFIED** (https://arxiv.org/abs/2504.18428 ; full text extracted)

- 18 languages, 4 difficulty levels, 9,000 samples.
- Three headline challenges: (1) reasoning performance varies widely across languages;
  (2) **input–output language consistency (LC) is low and correlates with performance**;
  (3) thinking length differs greatly by language.
- For reasoning LLMs "LC and ACC exhibit a **strong negative correlation, suggesting that lower
  language consistency is associated with better reasoning performance**"; when inconsistent,
  responses are "predominantly in English or Chinese... because their slow thinking abilities are
  mainly developed in English and Chinese".
- **Language control experiment (Table 7, DW-ACC):**

| Model | no control | + force query-language | + force **English** | + force preferred |
|---|---:|---:|---:|---:|
| Qwen-QwQ-32B | 45.9 | 43.4 | **47.9** | 46.2 |
| Deepseek-R1-671B | 47.0 | 46.3 | **47.6** | 46.8 |
| Claude-3.7-sonnet-thinking | 33.5 | 32.5 | **34.9** | 34.7 |

  "Forcing English as the response language yields the best overall performance and minimizes
  language disparities... Forcing the response language to match the query leads to the poorest
  performance." Cross-language std for QwQ drops 5.4 → 3.0 under forced English.

  Caveat: these are **reasoning/thinking models**; yours is non-thinking.

### 1.9 MMATH (2505.19126) — the closest thing to a recipe for your Greek maths rows

**VERIFIED** (https://arxiv.org/html/2505.19126v1 ; full text extracted)

- 374 problems (AIME 2024/2025, CNMO, 311 filtered MATH-500) × 10 languages
  (en, zh, ar, es, fr, ja, ko, pt, th, vi). Metrics: accuracy + **Language Consistency Ratio (LCR)**.
- Finding 1: "reasoning in English shows consistently better performance when asked in
  low-resource languages."
- Finding 2: "smaller models frequently fail to retain [output-language] control" — i.e. the
  prompt-level fix does not work at 7–8B. (Distill-Qwen-7B + ATP: 58.44 → **56.13**, a *drop*.)
- **Finding 3 — the actionable one.** Fine-tuning Qwen2.5-32B-Instruct on just **3,000 examples**:

| Training strategy (3K examples) | MMATH avg |
|---|---:|
| **EN-SFT** (question, thinking, answer all English) | 62.38 |
| **Native-Think** (all native, 300/language) | 61.46 |
| **EN-Think** (reason in English, answer in target language) | **66.72** |
| *(reference)* DeepSeek-R1-Distill-Qwen-32B | 67.01 |

  "EN-SFT yields the **lowest** answering LCR, suggesting that **English-only training contributes
  to off-target responses**." Answering LCR for the EN-Think variant reaches **97.61**, far above
  QwQ-32B's 58.94.

**This is the strongest published evidence for exactly your situation**: a small (3K) capability-
matched, target-language-answering slice on top of English reasoning recovers *both* accuracy and
output-language fidelity.

### 1.10 Mid-resource / non-Latin-script specifics

- **Greek**: only as a *low-resource* label in Kew et al. (relative to Llama-2). **VERIFIED.**
- **Hebrew, Arabic** are in Shaham et al.'s 12 languages; **Thai, Japanese, Korean, Chinese,
  Bengali** recur throughout MathOctopus/QAlign/MMATH/PolyMath. Non-Latin script is consistently
  where language confusion is worst (Marchisio Table 4 is *specifically* "average WPR on non-Latin
  script languages"; Table 6's base→instruct collapse is measured on ar/hi/ja/ko/vi/zh).
  **VERIFIED** (https://aclanthology.org/2024.emnlp-main.380.pdf)
- **Bulgarian** appears in Kew et al.'s medium-resource tier. **VERIFIED.**
- I found **no study that isolates Modern Greek** for SFT transfer. Treat Greek as behaving like
  the Hebrew/Bulgarian/Korean band: non-Latin script, mid-resource, ~1% of web corpora
  (FineWeb-2: Modern Greek **44,202,550 documents = 0.97%**, rank 21 of 40. **VERIFIED**,
  https://arxiv.org/pdf/2509.14233, Table G.6).

### 1.11 Reference multilingual models (Aya, EuroLLM, Salamandra, Teuken)

All maths numbers below are from **one common harness**, the Apertus report Table 18 —
which makes them directly comparable to each other. **VERIFIED** (https://arxiv.org/pdf/2509.14233)

| Model | GSM8K | MGSM | Hendrycks MATH | MathQA |
|---|---:|---:|---:|---:|
| **Apertus-8B-Instruct** | 62.9 | 48.5 | **18.2** | 32.1 |
| Apertus-70B-Instruct | 77.6 | 64.3 | 30.8 | 33.9 |
| EuroLLM-9B-Instruct | 62.9 | 36.1 | 19.2 | 32.7 |
| EuroLLM-22B-Instruct-Preview | 75.5 | 50.7 | 38.0 | 35.4 |
| salamandra-7b-instruct | 22.7 | 9.6 | **5.2** | 28.6 |
| Teuken-7B-instruct-v0.6 | 38.1 | 19.2 | **11.4** | 27.1 |
| Minerva-7B-instruct-v1.0 (Italian) | 13.6 | 2.8 | 3.5 | 24.7 |
| OLMo-2-1124-7B-Instruct | 83.5 | 36.9 | 31.1 | 26.0 |
| SmolLM3-3B | 83.6 | 45.2 | 51.8 | 27.7 |
| **Llama-3.1-8B-Instruct** | **84.5** | **67.7** | **36.3** | 24.4 |
| gemma-3-12b-it | 89.9 | 68.9 | 68.4 | 39.3 |

**The European multilingual 7–9B cohort (Apertus, EuroLLM-9B, Salamandra, Teuken) all sit at
MATH 5–19.** Llama-3.1-8B sits at 36.3. SmolLM3-3B — a *3B* model — hits 51.8. This is a
pretraining-recipe cluster, not a coincidence, and not something SFT data volume has closed for
anyone in that cohort.

Aya-Expanse 8B/32B: 23 languages **including Greek**; techniques are data arbitrage, multilingual
preference training, model merging; up to 76.6% win-rate on translated Arena-Hard-Auto.
**VERIFIED** existence/claims (https://arxiv.org/abs/2412.04261). Per-language maths numbers
**not verified**. Krikri's paper reports Aya Expanse 8B at **IFEval EL 50.4 / MT-Bench EL 7.68 /
ArenaHard EL 23.8**. **VERIFIED** (https://arxiv.org/pdf/2505.13772, Tables 6 and 8).

---

## 2. How the Greek peers actually did it

### 2.1 Llama-Krikri-8B (ILSP, arXiv 2505.13772)

**Pretraining / CPT** — **VERIFIED** (https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct,
corroborated by https://arxiv.org/pdf/2505.13772). 91B tokens, upsampled to 110.2B:

| Sub-corpus | Tokens | Share |
|---|---:|---:|
| Greek | 56.7B | 62.3% |
| English | 21.0B | 23.1% |
| Parallel (el–en) | 5.5B | 6.0% |
| **Math / Code** | **7.8B** | **8.6%** |

> **Note this against your own CPT (79% Greek / 20% replay / 1% other).** Krikri deliberately
> carried an **8.6% explicit maths+code slice through CPT** (sources named in the paper: Stack
> Overflow, the Python-Edu subset, AutoMathText). If your 20% replay did not contain a comparable
> maths fraction, that is a concrete, identifiable divergence from the peer's recipe — and unlike
> the base-model gap, it is one you could fix in a future CPT.

**Post-training** — **VERIFIED** (exact counts from the model card):

| Stage | Total | Greek | English | Greek share |
|---|---:|---:|---:|---:|
| SFT Stage 1 | 856,946 | 371,379 | 485,567 | **43.3%** |
| SFT Stage 2 | 638,408 | 279,948 | 358,460 | **43.9%** |
| DPO (length-normalised) | 92,394 | 47,132 | 45,262 | **51.0%** |

Composition (paper, §3): Stage 1 = filtered original English data, reward-model-filtered synthetic
MAGPIE data, **translated/post-edited data**, regenerated responses, multi-language translation
data, synthetic QA, synthetic multi-turn dialogues, upsampled manual safety data. Stage 2 = same
families at "progressively higher data quality", MAGPIE data with *higher* reward scores, and
**regenerated responses including a "thinking" section**. English sources named: **Tulu 3**,
**SmolTalk**, **MAGPIE-Ultra-v1.0**; preference source **UltraFeedback**.
**VERIFIED** (https://arxiv.org/pdf/2505.13772)

MAGPIE usage: Greek instruction data synthesised "directly in Greek using the MAGPIE technique";
separately, during annealing, Gemma-2-27B-IT was prompted to generate Q&A triplets with reasoning
from curated documents, producing **189M tokens**. **VERIFIED** (same source).

Preference stage: **DPO with an added length-normalisation term**, explicitly "to mitigate the
empirical phenomenon of DPO disproportionally preferring longer sequences". Preference data
included "preferences derived via contrasting regenerated vs. translated references **which aim to
mitigate issues introduced by unwanted translation artifacts**" (citing Dang et al. 2024a,b) and
manually created Greek-specific safety preferences. **VERIFIED**.

> **Translationese is a first-class concern in Krikri's own design.** They built a preference
> signal specifically to punish translation artifacts. If you later machine-adapt slices to Greek,
> budget for the same countermeasure.

**Reported scores** — **VERIFIED** (https://arxiv.org/pdf/2505.13772 Tables 6–8;
https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct):

| | IFEval EL | IFEval EN | MT-Bench EL | MT-Bench EN | ArenaHard EL | ArenaHard EN |
|---|---:|---:|---:|---:|---:|---:|
| Llama-Krikri-8B-Instruct | **67.5** | **82.4** | **7.96** | 7.21 | 31.8 | 35.1 |
| Llama-3.1-8B-Instruct | 45.8 | 75.1 | 6.46 | 7.25 | 4.0 | 19.7 |
| Aya Expanse 8B | 50.4 | 62.2 | 7.68 | 6.92 | 23.8 | – |
| Meltemi-7B-v1.5 | 32.7 | 41.2 | 6.25 | 5.46 | – | – |
| Gemma-2-27B-IT | 63.2 | 75.6 | 8.23 | 8.00 | 32.2 | 49.6 |

Open LLM Leaderboard (English), Table 7:

| Task | Llama-3.1-8B-Instruct | **Krikri-8B-Instruct** |
|---|---:|---:|
| IFEval | 49.22 | **60.79** |
| BBH | 29.38 | 29.31 |
| **MATH (Lvl 5)** | **15.56** | **11.78** |
| GPQA | 8.72 | 7.05 |
| MUSR | 8.61 | 10.46 |
| MMLU-PRO | 31.09 | 25.70 |
| Average | 23.76 | 24.18 |

> **Three things follow, and they matter a great deal.**
>
> 1. **Krikri's own paper reports English MATH of 11.78** — *below* its own Llama-3.1-8B baseline
>    of 15.56. The paper does **not** report GSM8K, MGSM, or MATH-500 anywhere, and the model card
>    reports **no maths benchmark at all**. So your "Krikri Greek MATH-500 32–38" is *your*
>    measurement, not a published one, and it is in tension with the only maths number ILSP
>    themselves published.
> 2. **Krikri lost ground to its own base on every reasoning/knowledge benchmark** (MATH
>    15.56→11.78, MMLU-Pro 31.09→25.70, GPQA 8.72→7.05) and gained only on IFEval. That is direct,
>    in-family evidence that **Greek-heavy CPT erodes maths and reasoning** — at 62.3% Greek, with
>    23.1% English replay *and* a dedicated 8.6% maths/code slice. Your mix is more aggressive
>    (79% Greek / 20% replay).
> 3. Krikri's headline wins are all **instruction-following and chat** (IFEval, MT-Bench,
>    Arena-Hard). That is exactly what the transfer literature predicts a large native-language
>    SFT share buys you — and it is *not* maths.

### 2.2 Meltemi-7B (ILSP, predecessor)

**VERIFIED** existence and CPT composition via ILSP/HF pages and search corroboration
(https://www.ilsp.gr/en/news/meltemi-en/ ; https://huggingface.co/ilsp/Meltemi-7B-Instruct-v1):
Mistral-7B + continual pretraining; ~40B tokens total, of which **28.5B Greek, 10.5B English, and
a ~600M-token Greek–English parallel set**. Instruction tuning followed HuggingFace alignment
recipes (SFT + DPO). v1.5 supersedes v1. Krikri's paper scores Meltemi-7B-v1.5 at **IFEval EL 32.7
/ EN 41.2, MT-Bench EL 6.25 / EN 5.46** — **VERIFIED** (https://arxiv.org/pdf/2505.13772, Table 6).
Precise Meltemi SFT row counts and Greek share: **not verified / RECALLED**.

### 2.3 Krikri v1.5 and other 2026 Greek models

**I could not verify the existence of a "Krikri v1.5".** The HF model card for
Llama-Krikri-8B-Instruct documents no v1.5, and searches surfaced only Krikri-8B
(Base/Instruct), the EMNLP 2025 Findings version of the paper
(https://aclanthology.org/2025.findings-emnlp.268.pdf), and Meltemi-7B-v1.5 (a *Meltemi* version
number, which is probably the source of the confusion). **Treat "Krikri v1.5" as unconfirmed.**
Related Greek-language work found but not examined: **GreekBarBench**
(https://arxiv.org/pdf/2505.17267), a free-text Greek legal reasoning benchmark.

---

## 3. Apertus: how it did multilingual SFT, and where the family ceiling is

**All VERIFIED from https://arxiv.org/pdf/2509.14233 (§4.1.3, Table 12, Table 18, Table 21).**

### 3.1 SFT mixture — ~4.18M examples, 149 languages in post-training overall

| Category | Datasets | Examples | Ratio |
|---|---|---:|---:|
| Foundation | OLMo2 WildChat 298,556; Personas 29,356; SciRiff 29,809; TableGPT 24,803; CoCoNot 10,793; OASST1 7,047 | 400,364 | 9.56% |
| **Math & Reasoning** | **Llama-Nemotron Math 200,000; Tulu3 Personas Math (filtered) 125,522; NuminaMath (tool-extracted) 63,248; OLMo2 OpenMath GSM8K 49,948; Llama-Nemotron Chat/Safety 46,808** | **485,526** | **11.60%** |
| Code & Functions | Llama-Nemotron Code 200,000; Glaive 112,688; XLam 60,000; APIGen 5,000 | 377,688 | 9.02% |
| Multilingual | SmolTalk2 (8 languages) 1,273,789; EuroBlocks 157,318; **s1k 42-langs (filtered) 1,000** | 1,432,107 | 34.22% |
| Regional | WikiQA 883,513; Romansh 46,170; Swiss-German 6,179; African langs 7,339; Swiss Charter 226 | 943,427 | 22.54% |
| Domain-specific | The-Tome | 544,975 | 13.02% |
| **Total** | | **4,184,087** | 100% |

**Was maths English-only? Effectively yes.** Every dataset in the Math & Reasoning row
(Llama-Nemotron Math, Tulu3 Personas Math, NuminaMath, OpenMath GSM8K) is an English source.
Multilinguality lives in a *separate* bucket (SmolTalk2's 8 languages, EuroBlocks).
**Greek is not named anywhere in the SFT mixture.**

**The one deliberate cross-lingual-transfer device — and it is exactly the MMATH recipe:**

> "we include 1,000 examples from the s1k 42 langs dataset... **specifically selecting unique
> samples with non-English prompts/responses but English reasoning chains to encourage
> cross-lingual transfer.**"

So Apertus's own team, with a 4.18M-example budget, allocated **1,000 examples** to
"non-English prompt → English reasoning" — and this is the same construction MMATH found best
(EN-Think 66.72 vs EN-SFT 62.38 vs Native-Think 61.46).

Other relevant process facts:
- **`\boxed{}` was stripped**: "Mathematical datasets undergo post-processing to remove `\boxed{}`
  formatting from assistant responses if present, enabling more natural response generation.
  Verifiable results are instead represented as a verifiable response."
- Alignment: **QRPO** (Quantile Reward Policy Optimization), not DPO; AdEMAMix optimizer;
  380,537 non-controversial + 72,698 controversial prompts.
- The mixture was "developed through **eight iterations** of empirical evaluation". Published at
  https://huggingface.co/datasets/swiss-ai/apertus-sft-mixture

**SFT-mixture ablation (13 benchmarks, Table 10/11 region):** Tulu3 original avg 0.442 vs
decontaminated 0.443 vs decontaminated+licence-filtered 0.417; licence filtering cost 4.3% on the
multilingual suite (avg 0.489), with **MGSM native-CoT showing the largest drop**, and MGSM direct
moving 0.187 → 0.212 / 0.176. Multilingual sub-table: Tulu3 original Global-MMLU 0.528, MGSM 0.187,
MGSM(2nd col) 0.332, INCLUDE V1 0.509, CulturalBench 0.709, Switzerland QA 0.592.

### 3.2 Apertus-8B-Instruct ceiling — the decisive table

Table 18, maths and code, one harness:

| Model | Avg | HumanEval p@10 | MBPP p@1 | **GSM8K** | **MGSM** | **Hendrycks MATH** | MathQA |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Apertus-8B-Instruct** | 44.2 | 67.0 | 36.2 | **62.9** | **48.5** | **18.2** | 32.1 |
| Apertus-70B-Instruct | 54.4 | 73.0 | 47.0 | 77.6 | 64.3 | 30.8 | 33.9 |
| **Llama-3.1-8B-Instruct** | 60.0 | 86.7 | 60.6 | **84.5** | **67.7** | **36.3** | 24.4 |
| Llama-3.3-70B-Instruct | 74.3 | 95.8 | 75.6 | 94.8 | 86.0 | 60.3 | 33.5 |
| Qwen2.5-72B-Instruct | 74.6 | 95.4 | 74.6 | 88.6 | 76.2 | 67.8 | 44.8 |

Table 21 (held-out): Apertus-8B-Instruct **GSM8K-Platinum 61.6**, AGIeval 38.7, GPQA-Main 27.0;
Llama-3.1-8B-Instruct GSM8K-Platinum **78.8**, AGIeval 38.1, GPQA-Main 28.3.

Table 19-region (IFEval): Apertus-8B-Instruct **IFEval 71.7 / Multi-IFEval 68.9**;
Llama-3.1-8B-Instruct 78.6 / 71.3.

Knowledge: Apertus-8B-Instruct MMLU 60.9, Global-MMLU 55.7.

**Interpretation.** Apertus-8B-Instruct is *competitive* on knowledge, IFEval and code-adjacent
tasks, and **specifically weak on maths**: MATH 18.2 vs 36.3, GSM8K 62.9 vs 84.5. It got there
*with* 485K maths SFT rows. Your model — same base family, plus 80B Greek tokens, four SFT rounds
— reports English MATH-500 13–16 and Greek MGSM 44–52. **You are within a few points of the
reference point in both directions.** The SFT pipeline is not obviously broken; the base is weak
at maths.

### 3.3 Does Greek-heavy CPT plausibly erode maths?

**Yes, and the best evidence is the peer itself.** Krikri: English MATH 15.56 → **11.78**,
MMLU-Pro 31.09 → **25.70**, GPQA 8.72 → **7.05** after Greek CPT (62.3% Greek, with 23.1% English
and 8.6% maths/code). **VERIFIED** (https://arxiv.org/pdf/2505.13772, Table 7).

General CPT-forgetting/replay literature: the widely-repeated guidance is that **replay in the
10–30% band preserves source capability during language adaptation**, and more recent work argues
for higher. I surfaced several 2025–2026 papers on this (e.g. "Mitigating Catastrophic Forgetting
in Target Language Adaptation of LLMs via Source-Shielded Updates", arXiv 2512.04844; "Forgetting
in Language Models: Capacity, Optimization, and Self-Generated Replay", arXiv 2605.26097) but
**did not read them; all magnitudes here are RECALLED / unverified.** Do not put these numbers in
a report without reading the sources.

What *is* verified and directly actionable: **Krikri put 7.8B tokens (8.6%) of explicit maths+code
into CPT and still lost 3.8 points of English MATH.** Your 20% replay's maths fraction is the
number to look up in your own dataset receipts.

---

## 4. Minimum target-language share to keep the model answering in Greek

### 4.1 Marchisio et al. 2024, "Understanding and Mitigating Language Confusion in LLMs"

**VERIFIED** (https://aclanthology.org/2024.emnlp-main.380.pdf ; arXiv 2406.20052)

- Language Confusion Benchmark (LCB), **15 typologically diverse languages**, two settings:
  **monolingual** (prompt in l, expect response in l) and **cross-lingual** (English prompt,
  instruction to answer in l).
- Metrics: **LPR** (line-level pass rate — % of responses where *every* line is in the desired
  language), **WPR** (word-level pass rate), **LCPR** (harmonic mean of LPR and WPR).
- Monolingual LPR: Command and GPT models **98.6–99.3**; **Llama 2, Llama 3 and Mistral 48.3–73.0**.
- Cross-lingual LPR: best models "in the low 90s"; **Llama 2 and 3 "in the 30s" due to a tendency
  to respond in English.**

**The key table for you — Table 6, base vs instruction-tuned, monolingual LPR, non-Latin subset:**

| Model | avg | ar | hi | ja | ko | vi | zh |
|---|---:|---:|---:|---:|---:|---:|---:|
| Llama 2 70B (base) | **98.5** | 99.6 | 100.0 | 100.0 | 100.0 | 98.0 | 93.2 |
| Llama 2 70B-Instruct | **6.0** | 0.3 | 1.0 | 7.0 | 0.0 | 17.0 | 10.5 |
| Llama 3 70B (base) | **94.7** | 96.7 | 97.9 | 87.9 | 98.8 | 97.0 | 90.0 |
| Llama 3 70B-Instruct | **12.1** | 21.7 | 23.0 | 10.0 | 0.0 | 10.0 | 8.0 |
| Command R base | 85.9 | 94.9 | 81.0 | 93.9 | 94.2 | 83.0 | 68.1 |
| **Command R** (multilingual post-training) | **99.6** | 100.0 | 100.0 | 100.0 | 100.0 | 99.0 | 98.5 |
| Command R+ base | 78.4 | 92.8 | 67.0 | 90.5 | 93.5 | 65.7 | 60.9 |
| **Command R+** | **99.2** | 99.7 | 100.0 | 99.0 | 100.0 | 99.0 | 97.5 |

Authors: "instruction-tuned Command R models exhibit **less** language confusion than their base
versions, [while] instruction-tuned Llama models are **much more** confused, indicating
English-centric instruction tuning, which is confirmed by our mitigation experiments."

**This is the single strongest warning against your plan as literally stated.** A base model that
can produce a non-Latin-script language at ~95–99% LPR can be driven to **6–12% LPR by
English-centric SFT**. Cohere's multilingually post-trained models go the other way, to 99%+.

**No dose–response curve.** The paper does *not* report "x% target-language data → y% LPR". It is
a binary contrast (English-centric vs multilingual post-training). Anyone quoting a specific
minimum percentage from this paper is over-reading it.

Other verified findings usable as cheap mitigations:
- **Temperature matters a lot.** Command R monolingual WPR: **T=0.0 → 97.2**, T=0.3 → 96.3,
  T=0.7 → 94.2, **T=1.0 → 86.5** (ja 74.5, zh 74.7). Varying nucleus p has a much smaller effect
  (97.3–97.6 across p=0.1–0.5).
- **Beam search** helps WPR moderately but **consistently hurts cross-lingual LPR**: 74.1 (greedy)
  → 68.4 (beam 10), worst for non-Indo-European languages (73.9 → 65.6).
- **Instruction placement**: integrated instructions ("Write an essay in Korean [...]") cause more
  confusion — Command R 69% LPR vs ~85% for isolated instructions at start or end.
- **Few-shot prompting** "greatly reduces Command R Base's language confusion and almost completely
  eliminates the problem in the monolingual setting" (one-shot: 80.6% LPR in the cited experiment).
- Mechanism: confusion occurs where the next-token distribution is flat — at confusion points,
  avg nucleus size 3.56 and entropy 1.228, vs 1.61 / 0.356 elsewhere.

### 4.2 Should the Greek share be capability-matched or generic chat?

The literature answers this **differently for different capabilities**, and the split is the most
important structural fact in this report:

| Capability | Evidence | Does a tiny generic Greek share suffice? |
|---|---|---|
| General instruction following / chat | Shaham (40 examples / 1%); Kew (2–3 languages, 200 ex/lang) | **Yes** — and the CPT'd base makes this easier still |
| Classification-style tasks | Kew: multilingual tuning "of less importance" | **Yes** |
| Open-ended generation w/ I-O language agreement | Kew: "most beneficial" here | Needs *some*, but not much |
| **Maths answering in the target language** | QAlign Table II (9.7% LC without En-X data); MMATH ("EN-SFT yields the lowest answering LCR") | **No — this one breaks specifically** |

So: **generic Greek chat data will hold general Greek fluency; it will NOT stop the model from
answering Greek maths questions in English.** That failure is capability-local, and both papers
that measured it measured it *inside* the maths domain. Your ~15k Greek maths worked solutions are
therefore not optional garnish — they are the specific instrument that protects the maths slice,
and MMATH's result says **3,000 examples was enough at 32B**.

---

## 5. For maths: reason in English, or reason in Greek?

### 5.1 The original MGSM result (Shi et al. 2022) — **VERIFIED** (https://arxiv.org/pdf/2210.03057, Table 3)

Accuracy (%) on MGSM, NATIVE-EXEMPLARS, 6-shot, greedy:

| System | AVG | HRL | URL | EN | DE | FR | ES | RU | ZH | JA | TH | TE | BN | SW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-3 DIRECT | 11.7 | 15.1 | 5.7 | 16.0 | 14.8 | 16.8 | 17.2 | 12.4 | 18.0 | 11.2 | 8.8 | 0.8 | 4.4 | 8.8 |
| GPT-3 **NATIVE-CoT** | 26.4 | 34.7 | 7.2 | 53.6 | 36.0 | 37.6 | 40.4 | 28.4 | 40.0 | 26.0 | 10.8 | 0.4 | 6.4 | 11.2 |
| GPT-3 **EN-CoT** | **31.6** | 39.4 | 13.9 | 53.6 | 44.0 | 46.0 | 44.8 | 28.4 | 40.8 | 32.4 | 19.6 | 5.6 | 9.6 | 20.8 |
| GPT-3 **TRANSLATE-EN** | **45.6** | 47.5 | 40.7 | 53.6 | 46.4 | 46.4 | 51.6 | 48.8 | 47.2 | 44.8 | 41.2 | 42.8 | 41.2 | 37.6 |
| PaLM-540B DIRECT | 18.6 | 19.3 | 16.8 | 22.0 | 18.8 | 19.6 | 20.0 | 22.0 | 19.2 | 16.0 | 16.8 | 17.6 | 17.2 | 15.6 |
| PaLM-540B **NATIVE-CoT** | 48.1 | 47.9 | 44.9 | 62.4 | 49.2 | 46.4 | 56.8 | 48.4 | 46.8 | 40.0 | 52.8 | 45.6 | 46.0 | 35.2 |
| PaLM-540B **EN-CoT** | **51.3** | 52.3 | 46.8 | 62.4 | 53.6 | 51.2 | 58.0 | 55.6 | 46.0 | 49.6 | 49.6 | 46.8 | 46.4 | 44.4 |
| PaLM-540B **TRANSLATE-EN** | **55.0** | 56.3 | 51.2 | 62.4 | 57.2 | 55.2 | 60.0 | 59.6 | 55.6 | 50.0 | 50.8 | 49.6 | 53.2 | 51.2 |

Authors: "reasoning in English (EN-CoT) **consistently achieves competitive or better performance**
than reasoning in the native language of the question."

Also worth knowing (Figure 1 discussion): "**there is no strong correlation between the performance
and the language frequency in the training corpora**: the average accuracy among the four
underrepresented languages was only 3% lower than among the six high-resource languages (44.9% vs
47.9%)". This is an argument that Greek's mid-resource status is *not* the binding constraint on
Greek maths — the model's underlying maths ability is.

### 5.2 Converging modern evidence

| Source | Finding | Numbers |
|---|---|---|
| MGSM (2022) | EN-CoT ≥ native-CoT | GPT-3 31.6 vs 26.4; PaLM 51.3 vs 48.1 |
| QAlign (2024) | Forcing native output costs accuracy | MGSM avg 49.6 → 41.0 |
| PolyMath (2025) | Forcing English output is best for reasoning LLMs | QwQ 45.9 → 47.9 (En) vs 43.4 (query-lang) |
| MMATH (2025) | **EN-Think + target-language answer is best of all** | 66.72 vs EN-SFT 62.38 vs Native-Think 61.46; answering LCR 97.61 |
| Apertus (2025) | Shipped 1,000 examples of exactly this construction | "non-English prompts/responses but English reasoning chains" |

**The answer is: reason in English, answer in the target language.** Five independent sources agree.

### 5.3 The complication you cannot ignore: you are a NON-THINKING model

Every result above separates a *thinking/CoT* segment from an *answer* segment. MMATH's EN-Think
and Apertus's s1k-42-langs both rely on that separation: English goes in the hidden/reasoning part,
Greek in the visible answer.

**Your model has no hidden reasoning channel.** For a non-thinking chat model the worked solution
*is* the visible response. So "English reasoning + Greek answer" would render as a visibly
bilingual reply — poor UX, and almost certainly not what a Greek user wants.

This is a genuine design fork and the literature does not resolve it for you. Three options:

1. **All-Greek worked solutions** (what your 15k Greek maths rows presumably are). Best UX, maximal
   language consistency. Costs accuracy — QAlign quantifies this at roughly **−8.6 MGSM points**
   at 7B, and MMATH's Native-Think trails EN-Think by **5.3 points**.
2. **English reasoning, Greek final answer + Greek restatement.** Closest to the winning recipe;
   bilingual output; needs a deliberate format decision.
3. **Greek reasoning but English-derived structure** — i.e. generate the solution in English, then
   translate the *whole* solution to Greek, so the Greek surface carries English-derived reasoning
   structure. This is what MathOctopus's parallel-training does. It is the only option that gets
   Greek-surface output *and* leans on English maths, and it is the one your "later adapt slices to
   Greek" plan naturally produces.

**Recommendation: option 3 for the bulk, option 1 for a held-out native slice** — and measure the
accuracy cost explicitly rather than assuming it.

---

## 6. Risks

### 6.1 English-heavy SFT degrading the Greek fluency/register gained in CPT — **HIGH, VERIFIED**

Marchisio Table 6 is the evidence: English-centric SFT drove non-Latin-script monolingual LPR from
98.5 → 6.0 (Llama-2-70B) and 94.7 → 12.1 (Llama-3-70B). Greek is non-Latin script. Your CPT
investment in Greek register lives in the base; English-heavy SFT is exactly the operation shown
to bury it. **Mitigation is proven to work** (Command R/R+ go base 78–86 → 99+ with multilingual
post-training), and both Shaham and Kew say the required dose for *general* fluency is small.

**Concrete instruction: make LPR/WPR a first-class, per-arm training metric, not a post-hoc check.**
Use OpenLID (as Kew et al. and QAlign both did) at the line level. An accuracy-only dashboard will
not see this failure until a user does.

### 6.2 Under-trained extended-tokenizer Greek tokens — **MEDIUM, largely UNVERIFIED**

I could **not** find a primary source isolating "vocabulary-extension tokens degrade when
subsequent SFT is mostly English". The vocabulary-extension literature I surfaced
(e.g. arXiv 2608.03494 on embedding-initialisation strategies; HYPEROFA arXiv 2504.21018) is about
*initialisation before CPT*, not about SFT-stage drift. **Treat this risk as reasoned, not
evidenced.**

The reasoning: your 80B-token Greek CPT is what trained the new Greek tokens; an SFT phase that is
>90% English provides near-zero gradient to those embeddings and their unembedding rows, while
updating everything around them. The failure would show up as *degraded Greek generation quality*
rather than as a benchmark drop — which makes it a fluency/perplexity check, not an accuracy check.

**Cheap diagnostics (both worth doing, neither expensive):**
- Track per-token-bucket mean gradient norm / embedding-drift for extended-vocabulary rows vs
  original rows across SFT. If the extended rows barely move while neighbours do, you have your
  answer directly.
- Measure Greek perplexity on a held-out native Greek set at each SFT checkpoint, alongside the
  benchmark suite. A rising Greek PPL with flat benchmarks is the signature.

### 6.3 Translationese from later machine adaptation — **MEDIUM, VERIFIED as a real concern**

Krikri built a countermeasure into its preference stage: "preferences derived via contrasting
regenerated vs. translated references **which aim to mitigate issues introduced by unwanted
translation artifacts**", citing Dang et al. 2024a,b. **VERIFIED**
(https://arxiv.org/pdf/2505.13772). Shaham et al. flag the same limitation in their own data
("translated using the Google Translate API, and not originally sourced by native speakers").
Krikri also "carefully post-edited" its translated Greek benchmarks.

This aligns with your existing memory rule *language_polish_before_done* (guarded Greek
language-correction pass on every adapted artefact) and *natural_greek_sft_repo*'s
authored-over-translated finding. The literature supports the rule you already have.

### 6.4 The measurement risk — **HIGH, and cheapest to eliminate**

Covered in §0.4. Apertus SFT strips `\boxed{}`; Krikri Stage-2 adds explicit reasoning/"thinking"
sections. A `\boxed{}`-keyed extractor would produce exactly the 13–16 vs 32–38 pattern you see
*even if the models were equally capable*. Also note Krikri's published English MATH (11.78) is
*worse* than Llama-3.1-8B-Instruct's (15.56) — so the claim "Krikri is strong at maths" is not
supported by ILSP's own numbers, and your 32–38 measurement deserves adversarial scrutiny before
it drives a training plan. **This directly engages your `benchmark_claims_need_paired_items` rule:
pair the per-item predictions and confirm the scoring protocol before reading the sign.**

---

## 7. Concrete recommendation

### 7.1 Do this before spending a single GPU-hour on a new SFT run

**R0 — Audit the maths scorer (hours, no GPU).** Take ~50 items where Krikri scores and your model
does not, on both Greek and English MATH-500. Inspect the raw generations. Check specifically
whether your model produced a correct answer that the extractor missed because it was not in
`\boxed{}`. Re-score both models with a format-agnostic extractor. **If this closes even a third of
the gap, everything downstream changes.**

**R1 — Establish the four-point ladder in ONE harness (1 GPU-day).** Measure English MATH-500 for:

| # | Model | Published reference to sanity-check against |
|---|---|---|
| (a) | **swiss-ai/Apertus-8B-Instruct** (untouched) | Hendrycks MATH **18.2** (arXiv 2509.14233 T18) |
| (b) | **Your Greek-CPT base**, few-shot | — (this isolates CPT erosion) |
| (c) | **Your current SFT model** | you report 13–16 |
| (d) | **Llama-3.1-8B-Instruct** | Hendrycks MATH **36.3** (same table) |
| (e) | **ilsp/Llama-Krikri-8B-Instruct** | MATH Lvl5 **11.78** (arXiv 2505.13772 T7) |

**Read the result like this:**
- **(c) ≈ (a) ≈ 18 and (d) ≈ 36** → **the base is the bottleneck.** Scaling English maths SFT will
  move you a few points at most. This is the outcome the evidence predicts.
- **(c) < (b)** → your SFT is *destroying* maths ability the base has. A data/recipe bug; fix
  before scaling.
- **(b) << published Apertus-8B base** → the Greek CPT eroded maths. Fix in the *next* CPT with an
  explicit maths slice (Krikri used 8.6%); no SFT mixture will recover it.
- **(e) ≈ 12 in your harness but you separately measure Greek MATH-500 32–38 for Krikri** → your
  two harnesses disagree; resolve before proceeding.

### 7.2 Greek share and composition — for the run you actually launch

**First, restate your own plan in comparable units.** ~37M Greek supervised tokens against "hundreds
of millions" of English is **roughly 7–11% Greek by token**, not the "small share" it sounds like.
Against Krikri's **43–44% by row**, it is about 4–6x smaller. Against Shaham's threshold (1%) it is
7–11x *larger*. You are not in the danger zone the transfer literature warns about — for chat.

**Recommended composition:**

| Slice | Recommendation | Grounding |
|---|---|---|
| **Overall Greek share** | **10–15% of supervised tokens.** Do not go below 10%. | Shaham 1% suffices for IF on a multilingual base; Marchisio shows the non-Latin-script collapse risk; Krikri's 43% is the safe-but-expensive end. 10–15% is the defensible middle. |
| **Greek maths** | **Keep all ~15k rows, and make Greek ≥5% of the MATHS slice specifically.** | MMATH: 3,000 capability-matched examples sufficed at 32B and fixed answering LCR to 97.61. QAlign: without in-domain target-language data, language consistency is **9.7%**. |
| **Greek IF (~30k rows)** | Keep all. This is your highest-confidence slice — IFEval is where Krikri's Greek SFT actually paid (EL 67.5 vs 45.8). | Kew: multilingual tuning "most beneficial for generative tasks that assume input/output language agreement". |
| **Greek chat/rewrite/personality** | Keep. Cheap insurance for register. | Shaham; Kew. |
| **English maths** | **Scale hard — this is the experiment.** Apertus used 485K rows; OpenMathInstruct-2 has 14M. | The only untested lever (§0.2). |
| **Cross-lingual bridge rows** | **Add a small el→en question-translation slice** (QAlign stage-I analogue) and/or Greek-prompt→English-reasoning rows. | QAlign: +11–12 MGSM points non-English from question alignment alone. Apertus shipped 1,000 such rows deliberately. |

**Format decision for the Greek maths rows (§5.3):** produce them by solving in English and
translating the complete worked solution to Greek (MathOctopus parallel-training style), so the
Greek surface carries English-derived reasoning structure — then run your existing guarded Greek
language-correction pass over them. Hold back a small natively-authored Greek slice as a
translationese control.

### 7.3 The transfer experiment — 0% / 5% / 15% Greek arms

Three SFT arms, identical English backbone, identical steps, Greek share varied:

| Arm | Greek share |
|---|---|
| A | **0%** (English-only) — the null; also the arm that tests §6.1 |
| B | **5%** |
| C | **15%** |

**Evaluate every arm on a paired EN/EL grid — and report language metrics as primary, not secondary:**

| Axis | Metric |
|---|---|
| Maths accuracy | MATH-500 **EN and EL** (same 500 items, translated) — paired per-item |
| Maths transfer | MGSM **EN and EL** |
| **Off-target rate** | **LPR / WPR via OpenLID**, per language, on Greek maths *and* Greek chat prompts, reported separately |
| Greek IF | Greek IFEval |
| Greek register | Held-out native Greek perplexity; extended-token embedding drift (§6.2) |
| Decoding sensitivity | Repeat LPR at T=0.0 and your serving T (Marchisio: Command R WPR 97.2 → 86.5 from T=0 to T=1) |

**What each outcome means:**
- **A collapses on Greek LPR but B and C hold** → the Greek share is doing language-fidelity work,
  not capability work. Ship the cheapest share that holds LPR. This is the *expected* result.
- **A, B and C have equal Greek MATH-500** → transfer is complete; Greek maths data buys only
  output language. Reallocate the Greek budget to IF and chat.
- **C > B > A on Greek MATH-500** → genuine capability-level transfer failure; Greek maths data is
  load-bearing and you should invest in translating more of it.
- **Greek LPR is fine in chat but poor in maths specifically** → exactly the QAlign/MMATH failure
  mode; the fix is capability-matched Greek maths rows, not more generic Greek chat.

**Sequencing note (cost control):** run **R0 and R1 first**. If R1 shows (c) ≈ (a) ≈ 18 and
(d) ≈ 36, then the ceiling is the base — and the 0/5/15 experiment becomes a question about
*Greek output fidelity* rather than about *Greek maths accuracy*, which is a much cheaper question
(it can be answered on far fewer tokens, since LPR saturates quickly).

### 7.4 Expectation setting

On the verified evidence, **an English-heavy SFT scale-up should not be expected to reach Krikri's
reported Greek maths numbers**, because the entire European multilingual 7–9B cohort
(Apertus 18.2, EuroLLM-9B 19.2, Teuken 11.4, Salamandra 5.2) sits in a band that no post-training
recipe in that cohort has escaped, while Llama-3.1-8B — Krikri's base — starts at 36.3.

That is not a reason to cancel the plan. It is a reason to **frame it as a base-model diagnostic
with a maths-data-scale arm**, set the kill criterion in advance (e.g. "if English MATH-500 does
not exceed 20 after 10x the maths tokens, the base is the limit"), and route the *expected* win to
where the Greek-CPT + Greek-SFT combination demonstrably pays — **Greek instruction-following,
chat quality and register**, which is precisely where Krikri's own published gains are
(IFEval EL 67.5, MT-Bench EL 7.96, ArenaHard EL 31.8) and where you already beat it on GreekMMLU (69).

---

## Appendix A — Source ledger

| # | Source | URL | Status |
|---|---|---|---|
| 1 | Shaham et al. 2024, Pinch of Multilinguality | https://arxiv.org/abs/2401.01854 ; https://aclanthology.org/2024.findings-acl.136/ | VERIFIED (full text) |
| 2 | Kew et al. 2024, Turning English-centric LLMs into Polyglots | https://arxiv.org/abs/2312.12683 ; https://aclanthology.org/2024.findings-emnlp.766/ | VERIFIED (full text) |
| 3 | Chen et al. 2024, Monolingual or Multilingual Instruction Tuning | https://arxiv.org/abs/2309.08958 ; https://aclanthology.org/2024.findings-eacl.90/ | VERIFIED (abstract/claims); tables RECALLED |
| 4 | Chen et al. 2023, MathOctopus / MGSM8KInstruct | https://arxiv.org/abs/2310.20246 | VERIFIED (aggregates); per-language cells NOT verified |
| 5 | Zhu et al. 2024, Question Translation Training / QAlign | https://arxiv.org/abs/2401.07817 ; https://arxiv.org/pdf/2405.01345 | VERIFIED (Tables II, IV) |
| 6 | Shi et al. 2022, MGSM | https://arxiv.org/pdf/2210.03057 | VERIFIED (Table 3) |
| 7 | PolyMath (NeurIPS 2025 D&B) | https://arxiv.org/abs/2504.18428 | VERIFIED (Tables 6, 7, §4.1–4.2) |
| 8 | MMATH | https://arxiv.org/html/2505.19126v1 | VERIFIED (Tables 5, 6, §3.3.3) |
| 9 | Marchisio et al. 2024, Language Confusion | https://aclanthology.org/2024.emnlp-main.380.pdf ; https://arxiv.org/abs/2406.20052 | VERIFIED (Tables 3–10) |
| 10 | Llama-Krikri-8B paper | https://arxiv.org/pdf/2505.13772 ; https://aclanthology.org/2025.findings-emnlp.268.pdf | VERIFIED (Tables 4–8, §3) |
| 11 | Llama-Krikri-8B-Instruct model card | https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct | VERIFIED (exact SFT/DPO Greek–English counts) |
| 12 | Apertus tech report | https://arxiv.org/pdf/2509.14233 | VERIFIED (§4.1.3, Tables 12, 18, 20, 21, 26, G.6) |
| 13 | Apertus SFT mixture | https://huggingface.co/datasets/swiss-ai/apertus-sft-mixture | Referenced by #12, not independently opened |
| 14 | OpenMathInstruct-2 | https://arxiv.org/pdf/2410.01560 | VERIFIED (headline 51.9 → 67.8) |
| 15 | Aya Expanse | https://arxiv.org/abs/2412.04261 | VERIFIED (scope/claims); per-language maths NOT verified |
| 16 | Meltemi | https://www.ilsp.gr/en/news/meltemi-en/ ; https://huggingface.co/ilsp/Meltemi-7B-Instruct-v1 | PARTIALLY VERIFIED (CPT composition); SFT share RECALLED |
| 17 | LangBridge | https://arxiv.org/pdf/2401.10695 | VERIFIED (existence/scope); numbers NOT extracted |
| 18 | MindMerger, xCoT, mCoT | — | **RECALLED — do not cite numbers** |
| 19 | CPT forgetting / replay-percentage literature | arXiv 2512.04844, 2605.26097 (surfaced, not read) | **UNVERIFIED — magnitudes RECALLED** |
| 20 | Vocabulary-extension / undertrained-token literature | arXiv 2608.03494, 2504.21018 (surfaced, not read) | **UNVERIFIED — §6.2 is reasoned, not evidenced** |
| 21 | "Krikri v1.5" | — | **COULD NOT VERIFY IT EXISTS** (likely confusion with Meltemi-7B-v1.5) |

## Appendix B — Things I could not verify, stated plainly

1. **"Krikri v1.5"** — no evidence found. Only Krikri-8B Base/Instruct and Meltemi-7B-**v1.5**.
2. **Krikri's Greek MATH-500 of 32–38 and MGSM-el of 68** — not published by ILSP anywhere I could
   find. The only maths number in their paper is English **MATH Lvl 5 = 11.78**, *below* their own
   Llama-3.1-8B baseline. Your figures are your own measurements and are unreplicated.
3. **MathOctopus per-language MGSM cells** for Thai/Swahili/Bengali/Russian — aggregates verified,
   individual cells not.
4. **Any dose–response curve for target-language share vs off-target rate.** It does not exist in
   the papers cited. Every "minimum share" figure in §7.2 is my synthesis across capability-specific
   evidence, not a published threshold.
5. **Greek-specific SFT transfer studies.** None found. All Greek read-across here is by analogy to
   Hebrew/Arabic/Korean/Bulgarian.
6. **Whether your 20% CPT replay contained maths.** Not a literature question — check your own
   dataset receipts. Krikri's comparable figure is 8.6% maths+code, and Krikri *still* lost 3.8
   points of English MATH.
