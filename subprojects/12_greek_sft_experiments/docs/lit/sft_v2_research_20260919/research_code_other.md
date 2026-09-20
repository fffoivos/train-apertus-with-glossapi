# Source-grounded research: code + non-maths capabilities for the 600M-supervised-token SFT plan

Target model: Apertus-8B + Greek CPT, **non-thinking**, hard **4,096-token** context, Apertus chat template with its own tool-call format.
Plan (shares of 600M *supervised/assistant* tokens): maths 30% (180M) · code 25% (**150M**) · precise IF 15% (90M) · general chat 12% (72M) · documents/grounded/rewrite/tables 8% (48M) · science+general reasoning 5% (30M) · tool use 3% (18M) · safety/uncertainty 2% (12M).

**Evidence marking.** `VERIFIED (url)` = read from the primary source in this session. `RECALLED` = from model knowledge, not re-checked — treat as a hypothesis to confirm. `ESTIMATE` = arithmetic I did on verified inputs, with the assumption stated.

**Token conversion used throughout.** I have character counts (from the HF datasets-server `/statistics` endpoint), not tokens. I use **3.4 chars/token** for English+code, so **4,096 tokens ≈ 13,900 characters**. This ratio is RECALLED/approximate for the Apertus tokenizer; every derived token figure below is an ESTIMATE and should be re-measured with the actual tokenizer before budgeting. Greek text tokenizes far worse (RECALLED ~2–2.5 chars/token), but none of the datasets below are Greek.

---

## 0. Executive summary of the load-bearing findings

1. **`nvidia/OpenCodeInstruct` is the right backbone for the 150M code budget.** 5M rows, CC-BY-4.0, Python-only, teachers Qwen2.5-32B-Instruct + Qwen2.5-Coder-32B-Instruct (both Apache-2.0 → no teacher-output restriction). **100.00% of responses are under 6,800 chars (≈2,000 tokens)** — it fits 4k trivially. Per-row unit-test pass rate is a first-class field. Available supervised volume ≈ **1.4B tokens**, i.e. ~9× the 150M target, so you can filter very aggressively.
2. **`nvidia/OpenCodeReasoning-2` is mostly unusable as-is.** `r1_generation` is a DeepSeek-R1 `<think>` trace: median 23,890 chars; **only 30.3% fit under 13,900 chars (≈4k tokens), and only 14.8% under 7,000 chars**. Your model is non-thinking, so you do not want the trace at all. The salvageable field is `solution` (code only, 99.9% under 7,000 chars) — but that is bare code with no prose.
3. **`nvidia/Nemotron-Post-Training-Dataset-v1` `code` and `tool_calling` splits are 100% `reasoning=on`** (verified on the sampled prefix) — all DeepSeek-R1 long traces. Only the `chat` split has a usable half (`reasoning=off`, 376,021 rows).
4. **Two prompt-rehydration traps.** Nemotron v1 `code` rows have `user` content literally `"-"` and Nemotron v1 `chat` rows sampled had **empty user content** (they must be re-joined from `lmsys/lmsys-chat-1m`). OpenCodeReasoning-2 `question` is `"-"` for 100% of rows and must be re-joined from TACO/APPS/CodeContests/open-r1-codeforces.
5. **Model-identity leakage in Nemotron v1 chat.** A sampled assistant turn reads *"I am a large-scale language model independently developed by the Tongyi Lab under Alibaba Group. My name is Qwen."* You must run an identity filter (Ai2 does exactly this — "heuristic model-identity filtering", OLMo 3 report).
6. **Licence red flags for an Apache-2.0 release:** `HuggingFaceTB/smoltalk2` declares **no licence at all**; `teknium/OpenHermes-2.5` declares **no licence** (and contains GPT-4-era outputs); `Salesforce/APIGen-MT-5k` is **CC-BY-NC-4.0** (non-commercial — exclude); `Multilingual-Multimodal-NLP/McEval-Instruct` (= opc `mceval_instruct`) is **CC-BY-SA-4.0** (share-alike); `Salesforce/xlam-function-calling-60k` is **gated** behind an access agreement.
7. **The strongest mixture evidence you asked for exists and cuts against a 55% maths+code share.** Ai2's OLMo 3 Table 28 SFT mixing ablation: adding code to the base mix moved HumanEval 23.2→26.8 but dropped **IFEval 61.7→57.3** and GSM8K 30.1→28.2; adding maths moved MATH 6.6→14.2 and GSM8K 30.1→39.7 but dropped **IFEval 61.7→54.0** and **HumanEval 23.2→18.3**; adding IF data moved IFEval 61.7→74.1 but collapsed **HumanEval 23.2→14.6**. These capabilities trade against each other hard at this scale.
8. **Calibration for "we have never measured code ability".** Measured by Ai2's own harness (OLMo 3 report, Table 26): **Apertus-8B-Instruct scores HumanEval+ 34.4, MBPP+ 42.1, LiveCodeBench-v3 7.8**. Olmo-3-7B-Instruct: 77.2 / 60.2 / 29.5. Qwen3-8B (no-think): 79.8 / 64.4 / 53.2. You are starting from a very low base and the headroom is large.

---

## 1. The named code datasets

### 1.1 `nvidia/OpenCodeInstruct`

VERIFIED (https://huggingface.co/datasets/nvidia/OpenCodeInstruct, https://datasets-server.huggingface.co/size?dataset=nvidia/OpenCodeInstruct, https://arxiv.org/abs/2504.04030)

| property | value |
|---|---|
| rows | **5,000,000** (card `dataset_info`); datasets-server reports a *partial* index of 1,400,000 rows / 1.78 GB parquet |
| configs/splits | single config `train`, single split `train`, 9 columns |
| licence | **CC-BY-4.0**, "ready for commercial/non-commercial use" |
| language | Python only (VERIFIED, paper §: "5 million diverse samples" in Python; card `language: en`) |
| fields | `id`, `input`, `output`, `domain` (generic/algorithmic), `generation_algorithm` (self-instruct/evol-instruct), `llm_judgement` (JSON string), `unit_tests` (JSON list of asserts), `tests_execution_status` (JSON list of pass/fail), `average_test_score` |

**Teachers** (VERIFIED, arXiv:2504.04030 full text):
- instructions: **Qwen2.5-32B-Instruct** (OSS-Instruct-style, seeded from Python functions)
- solutions: **Qwen2.5-Coder-32B-Instruct**
- unit tests: **Qwen2.5-Coder-32B-Instruct**, 10 assertion-style tests per (question, solution) pair
- judge: **Qwen2.5-Coder-32B-Instruct**, three criteria on a 1–5 scale — *requirement_conformance*, *logical_correctness*, *edge_case_consideration* — averaged.
Both teachers are Apache-2.0 models (RECALLED for the exact licence file, but Qwen2.5 series is Apache-2.0) → **no teacher-output restriction blocking an Apache-2.0 release**. This is the cleanest licence story of any code source in the plan.

**Verification / pass rates** — VERIFIED from `/statistics` on the indexed 1,400,000-row prefix (note: a *prefix*, not a random sample):
```
average_test_score  1.0 : 549,389  (39.24%)
                    0.9 : 172,537  (12.32%)
                    0.8 : 110,744  ( 7.91%)
                    0.7 :  71,674
                    0.6 :  50,829
                    0.5 :  38,132
                    0.4 :  33,710
                    0.3 :  28,749
                    0.2 :  28,070
                    0.1 :  30,795
                    0.0 : 285,371  (20.38%)
```
→ **39.2% pass all 10 tests; 51.6% score ≥ 0.9; 20.4% fail everything.** Strongly bimodal, exactly as the paper says.
Domain split: algorithmic 655,799 / generic 744,201. Algorithm: self-instruct 1,089,553 / evol-instruct 310,447.
The paper's own recommendation is notable: it reports that **LLM-judgement filtering beat pure unit-test filtering**, and that ~**77.4%** of the top-judge-scored samples also pass the generated unit tests. So the strongest filter is *judge-max AND pass-rate 1.0*.

**Length distribution** (VERIFIED, `/statistics` on the 1.4M prefix, characters):
`output`: min 74, **median 792**, mean 936, max 6,660. `input`: median 693, max 7,622.
→ **99.59% of outputs ≤ 3,400 chars (≈1,000 tok); 100.00% ≤ 6,800 chars (≈2,000 tok)**. Prompt+response comfortably inside 4,096 tokens for essentially every row.

**Available supervised volume** (ESTIMATE): 5,000,000 × 936 chars / 3.4 ≈ **1.38B assistant tokens**. Filtering to `average_test_score == 1.0` leaves ≈1.96M rows ≈ **540M tokens** — still 3.6× the 150M target.

**Contamination** (VERIFIED, arXiv:2504.04030): n-gram decontamination was run against **HumanEval, HumanEval+, MBPP, MBPP+ only**. **LiveCodeBench and BigCodeBench were NOT decontaminated against** (they are used as *evaluation* benchmarks in the paper but the decontamination sentence names only the HumanEval/MBPP family). If you intend to report LiveCodeBench or BigCodeBench, run your own decontamination.

**Reference results** (VERIFIED, arXiv:2504.04030): OCI-Llama-3.1-8B = HumanEval 78.7 / HumanEval+ 73.2 / MBPP 77.5 / MBPP+ 66.4 / LiveCodeBench 24.1 / BigCodeBench 37.1. OCI-Qwen2.5-Coder-7B = 87.8 / 84.1 / 86.8 / 74.9 / 39.7 / 43.6. The paper states **500k samples already surpassed the original Llama-3 and Qwen2.5-Coder instruct models** — directly relevant, since your 150M-token budget is ≈ 500k–550k OCI rows.

### 1.2 `nvidia/OpenCodeReasoning-2`

VERIFIED (https://huggingface.co/datasets/nvidia/OpenCodeReasoning-2, https://datasets-server.huggingface.co/size?dataset=nvidia/OpenCodeReasoning-2)

| property | value |
|---|---|
| rows | **python 1,398,166 + cpp 1,174,475 = 2,572,641**, over **34,799 unique questions** |
| configs/splits | one config `train`, two splits `python` and `cpp` |
| licence | **CC-BY-4.0** (NVIDIA). Per-row `license` field was **`apache-2.0` for 100%** of the indexed 120k python prefix |
| languages | **Python and C++ only** |
| fields | `question` (**blank — literally `"-"` for 100% of rows**), `r1_generation`, `qwq_critique`, `solution`, `judgement`, `pass_rate`, `source`, `license`, `dataset`, `split`, `difficulty`, `index`, `id`, `question_id` |
| teachers | **DeepSeek-R1** (solutions) and **QwQ** (critiques) — VERIFIED from the card |

**Are these long `<think>` traces that exceed 4k?** Yes, decisively. VERIFIED from `/statistics` histograms on the indexed 120,000-row python prefix (characters):

| field | median | mean | ≤7,000 ch (~2k tok) | ≤13,900 ch (**~4k tok**) | ≤20,000 ch |
|---|---|---|---|---|---|
| `r1_generation` | 23,890 | 27,230 | **14.8%** | **30.3%** | 42.8% |
| `qwq_critique` | 11,799 | 14,399 | 28.8% | 55.9% | 75.9% |
| `solution` (code only) | 670 | 972 | **99.9%** | 100.0% | 100.0% |

→ **~70% of R1 generations do not fit the 4,096-token context at all**, before counting the (re-hydrated) question. And since the target model is non-thinking, the `<think>` block is undesirable regardless.

**Verification:** `judgement` (QwQ right/wrong) = right 105,283 / wrong 14,717 on the 120k prefix (**87.7% "right"**). `pass_rate` = **1.0 for 70,509 / 120,000 = 58.8%**; the card says `-1` means not enough tests to validate.

**Contamination — a real flag.** The card says CodeContests and open-r1/codeforces *test* splits were excluded, but the per-row `split` field on the indexed python prefix reads **`train` 104,449 / `test` 15,551 (12.96%)** — i.e. TACO/APPS **test**-split questions are present. Sources are AtCoder/CodeForces/LeetCode/CodeChef etc., which is the same pool LiveCodeBench draws from. RECALLED: LiveCodeBench is date-windowed over recent contest problems from LeetCode/AtCoder/CodeForces. Treat OCR-2 as **LiveCodeBench-contaminated until you decontaminate yourself**, and drop `split == "test"` rows unconditionally.

**Companion paper**: arXiv:2507.09075, *"OpenCodeReasoning-II: A Simple Test Time Scaling Approach via Self-Critique"* — VERIFIED it exists; 2.5M question-solution-critique triples over ~35K questions; two-stage SFT (generation, then joint generation+critique); they also extended LiveCodeBench to C++.

**Verdict for your plan:** use OCR-2 only as a *(question, `solution`)* source after re-hydrating questions, or skip it. Do not use `r1_generation`.

### 1.3 `OpenCoder-LLM/opc-sft-stage2`

VERIFIED (https://huggingface.co/datasets/OpenCoder-LLM/opc-sft-stage2, https://datasets-server.huggingface.co/size?dataset=OpenCoder-LLM/opc-sft-stage2, /statistics per config)

Top-level licence on the card: **MIT**. Total **436,347 rows**, 537 MB parquet. Paper: arXiv:2411.04905.

| config | rows | instruction chars (median/mean/max) | output chars (median/mean/max) | verification | upstream licence |
|---|---|---|---|---|---|
| `educational_instruct` | **118,278** | 128 / 163 / 1,684 | 305 / **362** / 7,395 | **(instruction, code, testcase) triples validated through a Python compiler**; extra fields `code`, `entry_point`, `testcase` (mean 3.3 test cases) | derived from `OpenCoder-LLM/opc-annealing-corpus` |
| `evol_instruct` | **111,183** | 397 / 653 / 27,712 | 1,461 / **1,552** / 7,646 | **none** (Evol-Instruct generation only) | = `ise-uiuc/Magicoder-Evol-Instruct-110K`, **Apache-2.0** |
| `mceval_instruct` | **35,943** | 1,044 / 1,074 / 5,422 | 2,441 / **2,607** / 127,906 | **none** | = `Multilingual-Multimodal-NLP/McEval-Instruct`, **CC-BY-SA-4.0** ⚠ |
| `package_instruct` | **170,943** | 1,535 / 1,526 / 8,216 | 1,980 / **1,950** / 7,088 | **none** (seeded from pydoc interface docs) | OpenCoder-authored |

**Programming-language coverage:** `educational_instruct` and `package_instruct` are Python; `mceval_instruct` is the **multilingual** one (McEval covers ~40 programming languages — RECALLED); `evol_instruct` is Magicoder-Evol-Instruct, predominantly Python with some other languages (RECALLED). This is the only one of the three named code sources with meaningful **non-Python** coverage.

**4k fit:** maxima are 7,646 / 7,088 chars (≈2,250 tok) except one 127,906-char `mceval` outlier. Essentially **all rows fit 4,096 tokens**; cap `mceval_instruct` output at ~10,000 chars to drop the tail.

**Supervised volume available** (ESTIMATE, rows × mean output chars / 3.4):
educational 12.6M · evol 50.8M · mceval 27.6M · package 98.0M → **≈189M assistant tokens total**. On its own this is just above the 150M code target, but it is largely unverified data.

**Licence chain caution.** The `mceval_instruct` upstream is **CC-BY-SA-4.0** (VERIFIED via HF API). Share-alike on a *dataset* does not automatically make model weights a derivative work, but it is a genuine open question and the conservative move for an Apache-2.0 release is to **drop `mceval_instruct`** (cost: 27.6M tokens and all your non-Python coverage) or to accept the risk explicitly and document it. `evol_instruct`'s upstream Magicoder-Evol-Instruct-110K is declared Apache-2.0, but RECALLED: the Evol-Instruct lineage (WizardCoder/CodeAlpaca) traces back to **OpenAI model outputs**, which the declared Apache-2.0 tag does not cure. Ai2 nevertheless ships `theblackcat102/evol-codealpaca-v1` (Apache-2.0, VERIFIED) inside the ODC-BY Dolci mixture, so there is precedent, but it is precedent, not a clean title.

**Contamination:** RECALLED — the OpenCoder paper (arXiv:2411.04905) describes decontamination of its SFT data against HumanEval/MBPP. I did **not** verify this in this session. Assume **no** LiveCodeBench/BigCodeBench decontamination.

### 1.4 Code summary table for the 150M target

| source | usable rows after the obvious filter | est. supervised tokens | licence for Apache-2.0 release | verification |
|---|---|---|---|---|
| OpenCodeInstruct, `average_test_score==1.0` | ~1.96M | ~540M | **clean** (CC-BY-4.0, Qwen2.5 teachers) | unit tests + LLM judge |
| OpenCodeInstruct, `==1.0` AND all judge scores 5 | unknown (paper: 77.4% of top-judged pass) | ~200–400M | clean | strongest |
| opc `educational_instruct` | 118,278 | ~12.6M | clean (MIT) | compiler-validated + test cases |
| opc `package_instruct` | 170,943 | ~98M | clean (MIT) | none |
| opc `evol_instruct` | 111,183 | ~51M | Apache-2.0 declared, OpenAI-lineage risk | none |
| opc `mceval_instruct` | 35,943 | ~28M | **CC-BY-SA-4.0** ⚠ | none |
| OCR-2 `solution` only, `pass_rate==1.0`, `split!=test` | ~1.3M (py+cpp) | ~370M (bare code) | clean (CC-BY-4.0) | executed pass rate |
| Nemotron v1 `code` | 1,896,395, **all `reasoning=on`** | n/a at 4k | clean (CC-BY-4.0) | n/a |

---

## 2. Mixture inventories: smoltalk2, Dolci, Nemotron

### 2.1 `HuggingFaceTB/smoltalk2` — complete SFT-split inventory

VERIFIED (https://datasets-server.huggingface.co/size?dataset=HuggingFaceTB/smoltalk2 — the 25 split row-counts sum **exactly** to the config total 3,383,242, so this list is complete) and the per-subset token/turn columns are VERIFIED from the dataset card's own stats table (https://huggingface.co/datasets/HuggingFaceTB/smoltalk2).

Config totals: `Mid` 4,779,894 · `SFT` **3,383,242** · `Preference` 446,886.

**`think` subsets — 10, total 1,481,833 rows.** All undesirable for a non-thinking model unless you strip traces.

| split | rows | avg resp. tok | multi-turn | multilingual | tool | rewrite/sum/table |
|---|---|---|---|---|---|---|
| `OpenThoughts3_1.2M_think` | 1,133,524 | 14,543.6 | no (2) | no | no | no |
| `smoltalk_multilingual8_Qwen3_32B_think` | 244,736 | 2,148.7 | no (2) | **yes, 8 langs** | no | no |
| `multi_turn_reasoning_if_think` | 28,217 | 1,312.5 | **yes (6)** | no | no | no |
| `smoltalk_systemchats_Qwen3_32B_think` | 27,436 | 1,059.7 | no (2) | no | no | no |
| `aya_dataset_Qwen3_32B_think` | 15,222 | 1,198.4 | no (2) | **yes** | no | no |
| `table_gpt_Qwen3_32B_think` | 13,201 | (card table truncated) | no (2) | no | no | **table** |
| `smolagents_toolcalling_traces_think` | 9,079 | 681.9 | **yes (5.34)** | no | **yes** | no |
| `LongAlign_64k_Qwen3_32B_yarn_131k_think` | 7,526 | 2,135.7 | no (2) | no | no | long-doc |
| `smoltalk_everyday_convs_reasoning_Qwen3_32B_think` | 2,057 | 1,402.6 | **yes (4)** | no | no | no |
| `s1k_1.1_think` | 835 | 9,745.5 | no (2) | no | no | no |

**`no_think` subsets — 15, total 1,901,409 rows.** These are the ones relevant to you.

| split | rows | avg resp. tok | avg ctx tok | turns | multilingual | tool | rewrite/sum/table |
|---|---|---|---|---|---|---|---|
| `OpenThoughts3_1.2M_no_think_no_think` | 435,193 | 657.7 | 288.0 | 2 | no | no | no |
| `smoltalk_smollm3_smol_magpie_ultra_no_think` | 406,843 | 522.1 | 1,072.5 | **6** | no | no | no |
| `OpenHermes_2.5_no_think` | 384,900 | 214.7 | 269.4 | 2 | no | no | no |
| `smoltalk_multilingual_8languages_lang_5_no_think` | 254,047 | 550.1 | 179.4 | 2 | **yes (fr/es/it/pt/de/ar/ru/zh)** | no | no |
| `smoltalk_smollm3_smol_summarize_no_think` | 96,061 | **182.9** | 442.2 | 2 | no | no | **summarise** |
| `Mixture_of_Thoughts_science_no_think` | 86,110 | 373.0 | 135.6 | 2 | no | no | no (science) |
| `xlam_traces_no_think` | 59,962 | 455.8 | 431.4 | 2 | no | **yes** | no |
| `smoltalk_smollm3_smol_rewrite_no_think` | 53,262 | 229.3 | 235.1 | 2 | no | no | **rewrite** |
| `smoltalk_smollm3_systemchats_30k_no_think` | 33,997 | 284.7 | 439.8 | **6.27** | no | no | no |
| `smoltalk_smollm3_explore_instruct_rewriting_no_think` | 30,391 | 110.9 | 119.4 | 2 | no | no | **rewrite** |
| `tulu_3_sft_personas_instruction_following_no_think` | 29,970 | 397.7 | 136.7 | 2 | no | no | no (precise IF) |
| `table_gpt_no_think` | 13,203 | 155.6 | 787.8 | 2 | no | no | **table** |
| `hermes_function_calling_v1_no_think` | 8,961 | 468.4 | 1,163.9 | **5.35** | no | **yes** | no |
| `LongAlign_64k_context_lang_annotated_lang_6_no_think` | 6,249 | 274.6 | **15,126.2** | 2 | lang-annotated | no | long-doc |
| `smoltalk_smollm3_everyday_conversations_no_think` | 2,260 | 111.0 | 239.2 | **7.75** | no | no | no |

Notes: the card's SmolLM3 weight column shows they **downsampled** `smol-magpie-ultra` ×0.5, `OpenHermes-2.5` ×0.5, `OpenThoughts3_no_think` ×0.4, `smoltalk-multilingual8_think` ×0.3 and `OpenThoughts3_think` ×0.02 — i.e. HF deliberately capped the biggest sources.
`LongAlign_*` averages 15,126 context tokens — **will not fit your 4k window**; exclude or truncate.

**Licences: `HuggingFaceTB/smoltalk2` declares NO licence.** VERIFIED via https://huggingface.co/api/datasets/HuggingFaceTB/smoltalk2 — the tag list contains no `license:*` entry and `cardData.license` is `None`. You must inherit per-subset from the parents, and those are mixed:
- OpenThoughts3-1.2M: **Apache-2.0** (VERIFIED) — but RECALLED: OT3 responses are QwQ-32B distillations, fine for Apache-2.0.
- `teknium/OpenHermes-2.5`: **no licence declared** (VERIFIED) and RECALLED to contain GPT-4/GPT-3.5 outputs → **red flag**.
- `LipengCS/Table-GPT`: **MIT** (VERIFIED).
- `CohereLabs/aya_dataset`: **Apache-2.0** (VERIFIED).
- `NousResearch/hermes-function-calling-v1`: **Apache-2.0** (VERIFIED).
- `allenai/tulu-3-sft-personas-instruction-following`: ODC-BY (RECALLED; the Tulu 3 persona family is ODC-BY per the Dolci card).
- `open-r1/Mixture-of-Thoughts`: **no licence declared** (VERIFIED).
- SmolTalk-native subsets (magpie-ultra, smol-rewrite, smol-summarize, explore-instruct-rewriting, systemchats, everyday-conversations): RECALLED Apache-2.0 via `HuggingFaceTB/smoltalk`; **not verified**, and their responses are Qwen/Llama distillations.
- `xlam_traces_no_think`: derived from `Salesforce/xlam-function-calling-60k`, which is **gated** — see §4.

### 2.2 `allenai/Dolci-Instruct-SFT`

VERIFIED (https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT, https://datasets-server.huggingface.co/statistics?dataset=allenai/Dolci-Instruct-SFT&config=default&split=train)

**Licence: ODC-BY**, one licence for the whole mixture. 2,152,112 rows, 7.0 GB. Fields: `id`, `messages[{role, content, function_calls, functions}]`, `source_dataset`, `domain`. Mean 2.99 messages/row (max 183). Used to train `allenai/Olmo-3-7B-Instruct-SFT`. 69 declared languages including **`ell` (Greek)**.

**`domain` distribution (VERIFIED, exact, full split — not a sample):**
```
Coding          328,614      Reasoning     310,572
Chat            309,538      Math          269,937
Other           254,863      Tool Use      227,579
Precise IF      136,833      Safety        110,295
Science         103,825      Multilingual   99,987
Hardcoded Data       69
```

**`source_dataset` distribution (VERIFIED, exact) with upstream licences:**

| source | rows | upstream licence | overlaps |
|---|---|---|---|
| Verifiable Reasoning | 310,572 | new (Ai2) | — |
| Wildchat | 302,406 | ODC-BY-1.0; **responses upgraded to GPT-4.1** ⚠ | Tulu 3 uses WildChat too |
| Dolci Instruct Tool Use | 227,579 | Ai2, own card declares **no licence** | — |
| Dolci Instruct Python Algorithms | 186,345 | new (Ai2) | — |
| Logic Puzzles | 159,882 | new (Ai2) | — |
| Tulu 3 Persona MATH | 149,958 | ODC-BY-1.0 | **Tulu 3** |
| Dolci Instruct Precise IF | 136,833 | new (Ai2) | Tulu 3 Persona IF lineage |
| Evol CodeAlpaca | 107,270 | Apache-2.0 (VERIFIED) | **Tulu 3** |
| Dolci Instruct OpenThoughts3+ Science | 99,268 | Apache-2.0 upstream | **smoltalk2** (OT3) |
| Aya | 99,987 | Apache-2.0 (VERIFIED) | **smoltalk2** (`aya_dataset_*_think`) |
| FLAN | 89,981 | via `ai2-adapt-dev/flan_v2_converted` | **Tulu 3** |
| OpenMathInstruct 2 | 50,000 | NVIDIA CC-BY-4.0 (RECALLED) | — |
| WildJailbreak | 49,965 | ODC-BY-1.0 | **Tulu 3** |
| Tulu 3 Persona GSM | 49,980 | ODC-BY-1.0 | **Tulu 3** |
| WildGuardMix | 49,373 | Apache-2.0 | **Tulu 3** |
| Tulu 3 Persona Python | 34,999 | ODC-BY-1.0 | **Tulu 3** |
| Tulu 3 Persona Algebra | 19,999 | ODC-BY-1.0 | **Tulu 3** |
| CoCoNot | 10,957 | ODC-BY-1.0 (own card declares none) | **Tulu 3** |
| OpenAssistant | 7,132 | Apache-2.0 | **Tulu 3** |
| TableGPT | 5,000 | MIT (VERIFIED) | **Tulu 3**, **smoltalk2** |
| SciRiff | 4,557 | ODC-BY (VERIFIED) | **Tulu 3** |
| Hardcoded Data | 69 | Ai2 | — |

The Dolci card explicitly notes the OpenThoughts3 component was "**reasoning traces removed for instruct**" — so Dolci-Instruct-SFT is already a *non-thinking* mixture. That makes it the single best-matched named source for your model type.

**`allenai/Dolci-Instruct-SFT-Tool-Use`** (227,579 rows, VERIFIED via HF API; **card declares no licence** — inherit ODC-BY from the parent collection). OLMo 3 report Table 27 (VERIFIED, arXiv:2512.13961) gives its structure:

| component | env. interactions | trajectories | unique functions | % multi-turn | % multi-step |
|---|---|---|---|---|---|
| Science QA | real (MCP) | 22.6K | 8 | — | 42.3% |
| Web Search QA | real (MCP) | 6.6K | 3 | — | 76.1% |
| SimFC | simulated | 200K | 42.6K | 42.3% | 23.8% |

### 2.3 `nvidia/Nemotron-Post-Training-Dataset` v1 and v2

**v1** — VERIFIED (https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v1, https://datasets-server.huggingface.co/size?dataset=nvidia/Nemotron-Post-Training-Dataset-v1). Public, not gated. **CC-BY-4.0.** 25,659,642 rows, 203 GB. Fields: `uuid, license, generator, version, category, reasoning, messages[{role,content,tool_calls}], metadata`.

| split | rows | generator | `reasoning` | msgs/row |
|---|---|---|---|---|
| `chat` | 746,622 | **100% Qwen3-235B-A22B** | **off 376,021 / on 370,601** | exactly 2 |
| `code` | 1,896,395 | 100% DeepSeek-R1-0528 (on indexed prefix) | **100% `on`** | exactly 2 |
| `math` | 2,044,407 | (not sampled) | RECALLED mostly `on` | — |
| `stem` | 20,662,167 | (not sampled) | — | — |
| `tool_calling` | 310,051 | **100% Qwen3-235B-A22B** (prefix) | **100% `on`** | mean 9.62, median 10, max 74 |

Overall generator counts from the card: DeepSeek-R1-0528 24,602,969 + Qwen3-235B-A22B 1,056,673. Both teacher models are permissively licensed (DeepSeek-R1 MIT, Qwen3 Apache-2.0 — RECALLED) → **no barrier to an Apache-2.0 release**, despite the *target* model being a Llama derivative.

**Two traps VERIFIED by inspecting rows:**
- `code`: `user` content is the single character `"-"`; the question must be re-hydrated exactly as for OpenCodeReasoning-2. Assistant content begins `<think>` and the sampled row was **31,711 characters**.
- `chat`: the sampled rows had **zero-length user content** — the card warns that lmsys-chat-1m-sourced prompts must be downloaded from `lmsys/lmsys-chat-1m`.
- `chat` identity leakage, quoted verbatim from a sampled row: *"No, I am a large-scale language model independently developed by the Tongyi Lab under Alibaba Group. My name is Qwen."* **Filter on model-identity strings before use.**

**v2** — VERIFIED metadata (https://huggingface.co/api/datasets/nvidia/Nemotron-Post-Training-Dataset-v2) but **`gated: "auto"`**, so datasets-server refuses unauthenticated access; you need a logged-in token (auto-approved). **CC-BY-4.0**, arXiv:2508.14444. Languages en/de/it/fr/es/ja. Splits: `stem` 355,000 · `chat` 627,720 · `math` 239,467 · `code` 175,000 · `multilingual_ja` 975,202 · `multilingual_de` 1,015,314 · `multilingual_it` 1,016,503 · `multilingual_es` 935,704 · `multilingual_fr` 1,001,504. Note **v2 has no `tool_calls` field** in its `messages` schema (v1 does). Card licence note (VERIFIED via page fetch): "predominantly CC-BY-4.0, with a small subset of prompts from Wildchat having an ODC-BY license and a small subset of prompts from StackOverflow with CC-BY-SA license", and "models trained on this data may be subject to Qwen and DeepSeek license agreements". **No Greek.**

---

## 3. Mixture-effect evidence at 7–8B

### 3.1 The single most relevant ablation — OLMo 3 / Dolci, Table 28

VERIFIED (arXiv:2512.13961, §5.2.2, "Results of our instruct SFT mixing ablations on top of OLMo 2"). `CHE` = HumanEval, `AE` = AlpacaEval.

| mix | Avg | MMLU | BBH | GPQA | MATH | GSM8K | **CHE** | AE | **IFEval** |
|---|---|---|---|---|---|---|---|---|---|
| Base mix | 29.0 | 50.0 | 29.5 | 25.2 | 6.6 | 30.1 | **23.2** | 5.8 | **61.7** |
| + Aya | 29.1 | 51.9 | 28.2 | 28.1 | 6.9 | 31.4 | 21.3 | 4.9 | 60.3 |
| **+ Code** | 28.7 | 51.1 | 28.8 | 25.0 | 6.9 | **28.2** | **26.8** | 5.8 | **57.3** |
| + Flan | 30.3 | 51.9 | **35.0** | 26.8 | 6.6 | 34.7 | 21.3 | 5.8 | 60.3 |
| **+ IF** | 30.7 | 51.4 | 24.7 | 25.5 | 7.9 | 42.2 | **14.6** | 5.5 | **74.1** |
| **+ Math** | 29.3 | 49.9 | 23.9 | 29.2 | **14.2** | **39.7** | **18.3** | 5.4 | **54.0** |
| **+ Safety** | **27.0** | 51.7 | 28.3 | 24.8 | 6.5 | 28.2 | **14.0** | 6.8 | 56.0 |
| + Science | 29.4 | 53.4 | 25.3 | 28.1 | 8.3 | 34.9 | 20.7 | 6.8 | 57.3 |
| + Wildchat | 30.9 | 51.9 | 30.7 | 23.7 | 6.9 | 32.2 | 23.2 | **19.2** | 59.7 |

Reading this against your plan:
- **Does a big maths+code share hurt IF/chat? Yes, measurably.** +Math costs 7.7 IFEval points; +Code costs 4.4. Your plan puts 55% of supervised tokens into maths+code and 15% into precise IF — those two blocks pull in opposite directions on IFEval.
- **Does code help maths? No — here it hurt.** +Code moved GSM8K 30.1→28.2 and left MATH flat. And **+Math actively hurt code** (HumanEval 23.2→18.3). This is the opposite of the common "code helps reasoning" folklore, at least in the SFT stage at this scale.
- **Does IF data hurt code? Severely.** +IF dropped HumanEval 23.2→14.6 (−37% relative).
- **Safety data.** +Safety had the **lowest average of any arm (27.0)** and the worst HumanEval (14.0). But this is *adding safety to a base mix*, not removing it.
- **Removing safety** goes the other way: Tülu 3 (arXiv:2411.15124, Table 10) — VERIFIED via full-text fetch, numbers as summarised: removing safety data dropped the average 60.1→58.0 and Safety 93.1→74.7; removing WildChat dropped the average to 58.9 and AlpacaEval 2 from 12.4→7.5. Tülu 3's framing is that "safety is not orthogonal". Combined reading: **keep a small safety block (your 2% is well-judged) but do not scale it**.

**Caveat, stated plainly:** these are *example-count* ablations on an OLMo 2 base mix with a ~100K-example base, not token-share ablations at 600M tokens on a Greek-CPT Apertus. Direction is informative; magnitudes are not transferable.

### 3.2 Base/mid-training corroboration (OLMo 3, Tables 8–9, VERIFIED)

Same trade-off appears at mid-training: adding meta-reasoning + program-verifiable reasoning to a web-only 5B microanneal moved GSM8K 18.4→26.8, Minerva 6.3→13.6, MBPP 6.2→12.6, HumanEval 7.9→19.5 — while **GenQA 53.7→52.9 and MMLU 55.2→53.7 dropped**. The report's own conclusion: *"there are real tradeoffs when skewing toward certain of these domains… there is clear potential to further improve math and code performance by increasing weight of these domains in the mix — however, this comes at a significant cost to our MCQA and GenQA performance."*

### 3.3 Apertus's own SFT mixture (arXiv:2509.14233, §4.1.3, Table 12) — VERIFIED

Total **4,184,087 examples** (the prose says "approximately 3.8 million"; the table totals 4,184,087), *by examples not tokens*, published at `swiss-ai/apertus-sft-mixture`, arrived at through **eight iterations of mixture refinement**.

| category | examples | share | contents |
|---|---|---|---|
| Multilingual | 1,432,107 | **34.22%** | SmolTalk2 8-lang 1,273,789 · EuroBlocks 157,318 · s1k_42_langs 1,000 |
| Regional | 943,427 | **22.54%** | WikiQA 883,513 · Romansh 46,170 · Swiss-German 6,179 · African 7,339 · Swiss Charter 226 |
| Domain-Specific | 544,975 | **13.02%** | The-Tome (financial/web) |
| Math & Reasoning | 485,526 | **11.60%** | Llama-Nemotron Math 200,000 · Tulu3 Personas Math 125,522 · NuminaMath tool-extracted 63,248 · OpenMath GSM8K 49,948 · Llama-Nemotron Chat/Safety 46,808 |
| Foundation | 400,364 | **9.56%** | WildChat 298,556 · Personas 29,356 · SciRiff 29,809 · TableGPT 24,803 · CoCoNot 10,793 · OASST1 7,047 |
| **Code & Functions** | **377,688** | **9.02%** | Llama-Nemotron Code 200,000 · **Glaive Function Calling 112,688** · **XLam 60,000** · **APIGen 5,000** |

**Critical observation for your plan:** Apertus's "code" block is *half function-calling* — only 200,000 of 377,688 examples are actual code generation, i.e. **~4.8% of the mixture by examples**. Your plan's 25% *by supervised tokens* is a step-change of roughly 5–10× in relative code emphasis. That is the intended change, but it is large, and §3.1 says the bill is paid in IFEval/chat.

Apertus also reports (§4.1.2, Table 10) an SFT filtering ablation on the 10T checkpoint: original Tülu3 avg 0.442 → decontaminated 0.443 → **+ license filtering 0.417 (−5.8%)**, with MMLU-CoT collapsing 0.513→0.253. Licence filtering is not free.

### 3.4 SmolLM3 (https://huggingface.co/blog/smollm3) — VERIFIED

SFT total **1.8B tokens: 1.0B non-reasoning + 0.8B reasoning**, from 12 non-reasoning + 10 reasoning datasets; proportions chosen by "extensive ablations examining the optimal ratio of reasoning to non-reasoning tokens". Trained **4 epochs (~8B tokens)** with best-fit-decreasing packing and **losses masked on user turns and tool-call outputs**. Note SmolLM3 reports its mix **in tokens**, and the smoltalk2 card's `Weight` column shows per-source capping — this is direct precedent for your token-based budgeting.

### 3.5 Epochs and per-source caps

- **Tülu 3**: 2 epochs (RECALLED — the full-text fetch did not surface the epoch count in the main text; Appendix A holds it). Downsampling of large sources / upsampling of small ones is explicit in their Table 7 (VERIFIED via fetch).
- **OLMo 3 DPO**: "We train all models for one epoch following previous work" (VERIFIED). SFT epoch count not surfaced.
- **SmolLM3 SFT**: 4 epochs over a 1.8B-token mix (VERIFIED).
- **AceReason ~5 epochs**: RECALLED, not verified in this session. Do not cite.
- **arXiv:2609.01244 — VERIFIED REAL.** *"Post-Training Science for Supervised Fine-Tuning"*, Charles O'Neill, Mudith Jayasekara, Harry Partridge, submitted **1 September 2026** (https://arxiv.org/abs/2609.01244). It is a **hyperparameter** study (Qwen3 and Llama families, dense + MoE up to 235B, four customer SFT datasets), **not** a data-mixture study. Its directly usable findings:
  - *"Past about two epochs the validation loss overfits, the judged task score does not improve, and **instruction-following degrades**."* — and *"fresh examples outperform repeated data passes at equivalent computational budgets"*. **This is the single best citation for your per-source epoch cap: ≤2 epochs, and prefer new rows over repeats.**
  - Full-FT optimum LR ≈ **3e-5**; LoRA optimum ≈ **1e-3** (flat from 0.6B to 32B, ~33× the full-FT optimum); LoRA rank 64 / α 32 optimal, rank 32 near-free.
  - LoRA recovers ~98% of full-FT gain training 3.1–12.6% of parameters; gap narrows with scale.
  - Global batch size is a memory decision, not a speed one (1-epoch wall-clock within ~10% across batch sizes).
  - Validation loss ranks downstream quality **within** a fixed model+dataset+recipe (Spearman −0.38 to −0.88) but **does not transfer across model families**.
- **Sampling by tokens vs examples:** I found no controlled ablation. What exists is *practice*: SmolLM3 and your plan budget in tokens; Tülu 3, Dolci and Apertus budget in examples. The evidence that this matters is indirect but strong — smoltalk2's own stats table shows `OpenThoughts3_think` is 33.5% of *examples* but **86.74% of tokens**, which is why HF weighted it ×0.02. **Budgeting by examples on a mix with heterogeneous response lengths silently hands the loss to whichever source is longest.** Token budgeting is the right call; just cap per-source token share explicitly.

---

## 4. Tool-use data (3% = 18M supervised tokens)

| dataset | size | licence (VERIFIED unless noted) | multi-turn | notes |
|---|---|---|---|---|
| `Salesforce/xlam-function-calling-60k` | 60,000 | **cc-by-4.0** declared, **`gated: auto`** — card body unreadable without a token | no (single-turn) | RECALLED: single-turn, parallel + multiple calls; the *de facto* baseline. Used by Apertus (60,000 examples) |
| `HuggingFaceTB/smoltalk2` `xlam_traces_no_think` | **59,962** | none declared (inherit xLAM) | 2 msgs | already converted to `messages` + `chat_template_kwargs`; **avg 455.8 response tokens** |
| `NousResearch/hermes-function-calling-v1` | ~9k in smoltalk2 | **apache-2.0** | **yes, 5.35 msgs** | smoltalk2 `hermes_function_calling_v1_no_think` = **8,961** rows, avg ctx 1,163.9 tok, avg resp 468.4 tok |
| `HuggingFaceTB/smoltalk2` `smolagents_toolcalling_traces_think` | 9,079 | none declared | **yes, 5.34 msgs** | **think traces**, avg ctx 6,934 tok — mostly **exceeds 4k**; generated with DeepSeek-V3-0324 |
| `allenai/Dolci-Instruct-SFT-Tool-Use` | **227,579** | none on its own card; parent Dolci is **ODC-BY** | **42.3% multi-turn (SimFC)**, 23.8–76.1% multi-step | 42.6K unique functions; real MCP trajectories (Science QA 22.6K, Web Search 6.6K) + 200K simulated |
| `Dolci-Instruct-SFT` `domain == "Tool Use"` | **227,579** | **ODC-BY** | as above | already inside the main mixture with `function_calls`/`functions` fields on each message |
| `nvidia/Nemotron-Post-Training-Dataset-v1` `tool_calling` | **310,051** | CC-BY-4.0 | **yes, mean 9.62 msgs** | **100% `reasoning=on`** on the indexed prefix — traces must be stripped |
| `Team-ACE/ToolACE` | RECALLED ~11.3k | **apache-2.0** | yes | not size-verified this session |
| `Salesforce/APIGen-MT-5k` | 5,000 | **cc-by-nc-4.0** ⚠ | yes | **NON-COMMERCIAL — exclude from an Apache-2.0 release.** Note Apertus used "APIGen 5,000" |
| Glaive Function Calling | RECALLED ~113k | RECALLED Apache-2.0 | yes | Apertus used 112,688; not verified this session |

**Coverage of the hard cases (no-call / missing-argument / tool-error / multi-turn result use):** I could not verify this per-dataset from primary sources in this session. What is VERIFIED:
- Dolci Tool Use is the only named set with **real environment interactions** (MCP servers) and published multi-step rates — so it is the most likely to contain genuine tool-error and result-consumption turns.
- Nemotron v1 `tool_calling` at a median of 10 messages/row necessarily contains multi-turn result consumption.
- xLAM and smoltalk2's `xlam_traces` are single-turn → **no** tool-error or result-use coverage. RECALLED: xLAM does include "no relevant function" / irrelevance cases, but this is unverified.
- **Gap:** none of these is guaranteed to cover *missing-argument clarification*. You will likely have to synthesise that (a few thousand rows is enough at 3%).

**Conversion to the Apertus tool-call format.** VERIFIED that the formats differ structurally: Nemotron v1 uses `messages[].tool_calls[{id, type, function:{name, arguments}}]` (OpenAI-shaped, `arguments` is a JSON **string**); Dolci uses per-message `functions` and `function_calls` as **plain strings**; smoltalk2 hoists tool definitions into a separate `chat_template_kwargs` column. The Apertus chat template has its own format (per the task brief). So the conversion is a three-way normalisation:
1. Parse each source into a canonical `{tools: [json-schema], turns: [{role, content, calls:[{name, args:obj}], results:[...]}]}`.
2. Re-serialise through the Apertus template's tool syntax — including the *system/tool-definition* placement, which differs per source.
3. **Re-tokenise and re-check the 4k budget after conversion**, because tool schemas are verbose: smoltalk2's `hermes_function_calling_v1_no_think` already averages 1,164 context tokens and `smolagents_toolcalling_traces_think` averages 6,934.
4. Mask the loss on tool-result turns (SmolLM3 does exactly this — VERIFIED).
5. Round-trip test: re-parse your rendered strings with the template's own parser and assert the call objects are identical. Arguments-as-JSON-string vs arguments-as-object is the classic silent corruption here.

---

## 5. Grounded / document tasks at 4k (8% = 48M supervised tokens)

Everything below is already short enough for 4,096 tokens except where flagged.

| task | dataset | rows | avg resp / ctx tok | licence |
|---|---|---|---|---|
| faithful summarisation | smoltalk2 `smoltalk_smollm3_smol_summarize_no_think` | **96,061** | 182.9 / 442.2 | none declared (inherit SmolTalk) |
| rewriting | smoltalk2 `smoltalk_smollm3_smol_rewrite_no_think` | **53,262** | 229.3 / 235.1 | none declared |
| rewriting (instruction-conditioned) | smoltalk2 `smoltalk_smollm3_explore_instruct_rewriting_no_think` | **30,391** | 110.9 / 119.4 | none declared |
| table QA / table ops | smoltalk2 `table_gpt_no_think` | **13,203** | 155.6 / **787.8** | MIT (via `LipengCS/Table-GPT`) |
| table QA (think variant) | smoltalk2 `table_gpt_Qwen3_32B_think` | 13,201 | — | MIT upstream |
| table QA | Dolci `TableGPT` | **5,000** | — | **ODC-BY** (MIT upstream) |
| scientific instruction / extraction | Dolci `SciRiff` | **4,557** | — | **ODC-BY** |
| **unanswerable / non-compliance** | Dolci `CoCoNot` | **10,957** | — | **ODC-BY** |
| classic task variety (extraction, QA, NLI) | Dolci `FLAN` (`ai2-adapt-dev/flan_v2_converted`) | **89,981** | — | **ODC-BY** as shipped |
| long-document grounding | smoltalk2 `LongAlign_64k_context_lang_annotated_lang_6_no_think` | 6,249 | 274.6 / **15,126** ⚠ | none declared |
| long-document grounding | smoltalk2 `LongAlign_64k_Qwen3_32B_yarn_131k_think` | 7,526 | 2,135.7 / **16,220** ⚠ | none declared |
| multi-turn system-grounded | smoltalk2 `smoltalk_smollm3_systemchats_30k_no_think` | 33,997 | 284.7 / 439.8 | none declared |

**Volume reality check** (ESTIMATE, rows × avg response tokens, from the verified smoltalk2 stats table): summarise 17.6M + rewrite 12.2M + explore-rewriting 3.4M + table_gpt 2.1M = **≈35M supervised tokens** from smoltalk2's document family at **1 epoch**. Dolci's table/science/FLAN/CoCoNot components add maybe 25–40M more (response lengths not measured). **48M is achievable but only just, and only at ~1 epoch** — do not plan on 2 epochs here.

**Gaps and additions:**
- **Unanswerable-question handling** is thin: CoCoNot (10,957) is the only purpose-built set in the named sources. `rajpurkar/squad_v2` (**142,192 rows, CC-BY-SA-4.0** — VERIFIED) is the obvious SQuAD2-style top-up, but **CC-BY-SA is a share-alike flag** for an Apache-2.0 release; it is also extractive-span data that needs reformatting into chat. RECALLED alternatives: `google/boolq` (**CC-BY-SA-3.0**, 12,697 rows, VERIFIED licence) — same share-alike issue.
- **FaithEval-like** faithfulness training data: I found no open *training* set in the named sources. FaithEval is an evaluation benchmark (RECALLED). The practical substitute is CoCoNot + a synthesised counterfactual-context set built from your own Greek documents.
- **Greek-language grounded data is absent from every source here.** Dolci declares `ell` among its 69 languages (via Aya), but there is no Greek document/table/summarisation subset anywhere in the named plan. If Greek grounded QA matters, it must be built.

---

## 6. Code evaluation for a non-thinking 8B, and calibration

### 6.1 What to run (cheap, in this order)

1. **HumanEval+ / MBPP+ via EvalPlus** — RECALLED: `evalplus` package, pass@1 greedy; HumanEval+ = 164 problems with ~80× more tests, MBPP+ = 378 problems. VERIFIED from the EvalPlus leaderboard page: *"Models are ranked according to pass@1 using greedy decoding."* Cheapest possible signal; ~542 generations total. **Run this first — you have never measured code ability, and this is a one-hour job.**
2. **MultiPL-E** — RECALLED: HumanEval/MBPP translated to ~18–22 languages. This is the only way to detect that an OpenCodeInstruct-heavy (Python-only) mix has made the model *worse* outside Python. Given that OpenCodeInstruct is 100% Python and `mceval_instruct` is your only multi-language source, **MultiPL-E is not optional for this plan**.
3. **BigCodeBench-Instruct** — RECALLED: ~1,140 tasks, library-heavy, "Instruct" is the natural-language-prompt variant; Complete/Instruct split, pass@1. Much harder; expect single-to-low-double digits at this scale.
4. **LiveCodeBench (easy subset)** — RECALLED: date-windowed contest problems; the OLMo 3 harness uses **v3 with pass@1 at n=10, temp 0.6, top-p 0.95** (VERIFIED, OLMo 3 Table 16). Note: **OLMo 3's harness allows up to 32,768 generated tokens**; your model is capped at 4,096, so you will under-score relative to published numbers unless you note the cap. Flag this in any comparison you publish.

### 6.2 Published scores for comparable models

**A — Ai2's harness, one consistent setup** (VERIFIED, arXiv:2512.13961 Table 26; pass@1, n=10, temp 0.6, top-p 0.95, zero-shot, thinking stripped):

| model | HumanEval+ | MBPP+ | LiveCodeBench v3 | IFEval | IFBench | MATH | AlpacaEval2 LC | BFCL |
|---|---|---|---|---|---|---|---|---|
| **Apertus-8B-Instruct** | **34.4** | **42.1** | **7.8** | 71.4 | 22.1 | 21.9 | 8.1 | n/a |
| OLMo-2-7B-Instruct | 25.8 | 40.7 | 7.2 | 72.2 | 26.7 | 30.1 | 18.3 | n/a |
| Granite-3.3-8B-Instruct | 64.0 | 54.0 | 11.5 | 77.5 | 22.3 | 67.3 | 28.6 | n/a |
| Qwen2.5-7B-Instruct | 74.9 | 62.6 | 34.5 | 73.4 | 28.4 | 71.0 | 23.0 | 55.8 |
| **Olmo-3-7B-Instruct** | **77.2** | **60.2** | **29.5** | 85.6 | 32.3 | 87.3 | 40.9 | 49.8 |
| Qwen3-8B | 79.8 | 64.4 | 53.2 | 86.3 | 29.3 | 82.3 | 49.8 | 60.2 |
| Olmo-3-7B-Instruct **SFT only** | 69.8 | 56.5 | 20.0 | 81.7 | 27.4 | 65.1 | 21.8 | 48.9 |
| Apertus-70B-Instruct (32B table) | 42.9 | 45.8 | 9.7 | 70.4 | 26.0 | 36.2 | 19.9 | n/a |

**Apertus-8B-Instruct at HumanEval+ 34.4 / MBPP+ 42.1 / LCB 7.8 is your true starting point** — and the 70B is barely better (42.9 / 45.8 / 9.7), which says the weakness is in the *post-training data*, not the parameter count. That is precisely the gap a 150M-token code block is meant to close.

**B — the Apertus paper's own harness** (VERIFIED, arXiv:2509.14233 Table 18; HumanEval **pass@10**, MBPP **pass@1**):

| model | HumanEval p@10 | MBPP p@1 | GSM8K | MATH |
|---|---|---|---|---|
| **Apertus-8B-Instruct** | **67.0** | **36.2** | 62.9 | 18.2 |
| Apertus-70B-Instruct | 73.0 | 47.0 | 77.6 | 30.8 |
| Llama-3.1-8B-Instruct | 86.7 | 60.6 | 84.5 | 36.3 |
| SmolLM3-3B | 89.7 | 52.8 | 83.6 | 51.8 |
| Qwen3-8B | 95.6 | 66.8 | 89.5 | 66.8 |
| OLMo-2-1124-7B-Instruct | 65.2 | 32.0 | 83.5 | 31.1 |
| EuroLLM-9B-Instruct | 65.3 | 41.0 | 62.9 | 19.2 |

And IFEval / Multi-IFEval (Table 19): **Apertus-8B-Instruct 71.7 / 68.9**; Llama-3.1-8B-Instruct 78.6 / 71.3; SmolLM3-3B 72.3 / 70.1; OLMo-2-7B-Instruct 71.0 / 60.6.

**C — reference ceiling for an OpenCodeInstruct-trained 8B** (VERIFIED, arXiv:2504.04030): OCI-Llama-3.1-8B = HumanEval+ **73.2**, MBPP+ **66.4**, LiveCodeBench **24.1**, BigCodeBench **37.1**, trained on the full 5M. That is what a *Llama-3.1-8B base* reaches on this data alone; a Greek-CPT Apertus-8B with 25% of its budget on code should be benchmarked against a fraction of that, not against it.

**Suggested targets after this SFT run** (my judgement, not sourced): HumanEval+ **55–70**, MBPP+ **50–60**, LiveCodeBench-v3 **12–20** (capped at 4k output), with **IFEval held at ≥ 71.7** (no regression vs Apertus-8B-Instruct). Track IFEval as the *canary*, because §3.1 says that is what a big code+maths block costs you.

---

## 7. Concrete recommendation

### 7.1 Code — 150M supervised tokens

**Shortlist and filters, in priority order:**

| # | source | filter | est. rows | est. tokens | why |
|---|---|---|---|---|---|
| 1 | `nvidia/OpenCodeInstruct` | `average_test_score == 1.0` **AND** all three `llm_judgement` scores == 5 **AND** `len(output) ≤ 6,800 chars` **AND** de-dup on normalised `input` | ~400k sampled from ~1.5M eligible | **~110M** | only fully verified, licence-clean, 4k-native source; paper shows 500k rows beats the stock instruct models |
| 2 | `OpenCoder-LLM/opc-sft-stage2` `educational_instruct` | all rows (compiler-validated + test cases), `len(output) ≤ 6,800` | 118,278 | **~12.6M** | independent style (educational prose + code), MIT, verified |
| 3 | `OpenCoder-LLM/opc-sft-stage2` `package_instruct` | sample; `len(output) ≤ 6,800`; cap at 15% of the code block | ~50k | **~15M** | library/API usage — the BigCodeBench-shaped skill OpenCodeInstruct lacks |
| 4 | `OpenCodeReasoning-2` | `split != "test"` **AND** `pass_rate == 1.0` **AND** `judgement == "right"`; re-hydrate `question`; use **`solution` only**, wrapped with a short synthesised explanation | ~30k | **~10M** | competitive-programming distribution; keep small |
| — | `mceval_instruct` | **HOLD** — CC-BY-SA-4.0 | — | — | if legal clears share-alike, add ~28M and gain multi-language coverage |
| — | `evol_instruct` | **HOLD** — OpenAI-output lineage | — | — | Ai2 ships the sibling under ODC-BY; decide explicitly |
| — | Nemotron v1 `code` | **EXCLUDE** | — | — | 100% `reasoning=on`, needs question re-hydration, 31k-char responses |

Sum of the clean four: **~148M supervised tokens at 1 epoch.** The target is met **without any repetition and without touching either licence-flagged subset.** That is the headline result: you do not need to compromise on licence to hit 25%.

**Language quota.** If `mceval_instruct` stays out, the code block is **~97% Python**. Decide consciously: either accept a Python specialist and say so, or clear McEval, or synthesise a small non-Python slice. Either way, **run MultiPL-E** to measure what you actually built.

### 7.2 Other capabilities

| capability | target | shortlist + filters | achievable | risk |
|---|---|---|---|---|
| **General chat 12% (72M)** | | Nemotron v1 `chat` **`reasoning == "off"`** (376,021 rows) after re-joining lmsys prompts and **filtering model-identity strings**; + Dolci `domain == "Chat"` (WildChat, 309,538, ODC-BY); + smoltalk2 `smol_magpie_ultra_no_think` (406,843 × 522 tok ≈ 212M available, cap it) | **easily ≥72M** | ⚠ WildChat responses are **GPT-4.1**-generated; smoltalk2 has **no licence**; Nemotron chat has empty prompts + Qwen identity leakage |
| **Precise IF 15% (90M)** | | Dolci `Precise IF` 136,833 (ODC-BY) + `tulu_3_sft_personas_instruction_following_no_think` 29,970 × 398 tok ≈ 11.9M | **tight.** Dolci Precise IF response lengths unmeasured; if ~400 tok/row it yields ~55M. **Plan to measure before committing to 90M** | may need synthesis or 2 epochs |
| **Documents 8% (48M)** | | §5 table: smoltalk2 summarise/rewrite/explore-rewrite/table ≈ 35M + Dolci FLAN/TableGPT/SciRiff/CoCoNot | **~48M at exactly 1 epoch** | no headroom; smoltalk2 licence |
| **Science + reasoning 5% (30M)** | | Dolci `Science` 103,825 (incl. OpenThoughts3+Science 99,268, traces already removed) + `Reasoning` 310,572 + smoltalk2 `Mixture_of_Thoughts_science_no_think` 86,110 × 373 tok ≈ 32M | **comfortable** | `Mixture-of-Thoughts` declares **no licence** |
| **Tool use 3% (18M)** | | Dolci Tool Use 227,579 (ODC-BY, real MCP + multi-turn) as the spine; + smoltalk2 `xlam_traces_no_think` 59,962 × 456 ≈ 27M and `hermes_function_calling_v1_no_think` 8,961 × 468 ≈ 4.2M | **comfortable** | **exclude APIGen-MT-5k (CC-BY-NC)**; xLAM is gated; all need template conversion + 4k re-check |
| **Safety 2% (12M)** | | Dolci `Safety` 110,295 = CoCoNot 10,957 + WildGuardMix 49,373 + WildJailbreak 49,965, all ODC-BY/Apache | **comfortable** | keep at 2% — OLMo 3 Table 28 shows +Safety had the *worst* average of any arm |

### 7.3 Licence red flags, ranked

1. **`Salesforce/APIGen-MT-5k` — CC-BY-NC-4.0.** Hard exclude for an Apache-2.0 release. (Note: Apertus's own mix includes "APIGen 5,000".)
2. **`HuggingFaceTB/smoltalk2` — no licence declared at all.** You must license each subset from its parent, and two parents (`OpenHermes-2.5`, `Mixture-of-Thoughts`) also declare nothing. Either get a written position or route around them.
3. **`teknium/OpenHermes-2.5` — no licence + GPT-4-era outputs.** Exclude.
4. **`mceval_instruct` (McEval-Instruct) — CC-BY-SA-4.0.** Share-alike. Decide explicitly; excluding it costs your non-Python coverage.
5. **`evol_instruct` / Evol-CodeAlpaca — declared Apache-2.0, OpenAI-output lineage.** Ai2 ships it under ODC-BY; decide explicitly.
6. **WildChat inside Dolci — responses regenerated with GPT-4.1.** The mixture is ODC-BY, but OpenAI's terms are a separate question from the data licence. This is 302,406 rows of your best chat data.
7. **`Salesforce/xlam-function-calling-60k` — gated.** Metadata says CC-BY-4.0 but the card body (which may add terms) is unreadable without accepting the gate. **Read the full card after accepting before you ship.**
8. **Clean and unencumbered:** OpenCodeInstruct, OpenCodeReasoning-2, Nemotron v1/v2 (all CC-BY-4.0, permissive teachers); opc-sft-stage2 MIT; Dolci ODC-BY; Aya, hermes-function-calling, ToolACE, OpenThoughts3 Apache-2.0; TableGPT MIT.

Note the precedent from Apertus's own paper: **licence filtering cost 5.8% average performance** (0.443 → 0.417) in their ablation. If this model is to be released under Apache-2.0 alongside the compliance story of the Apertus line, that cost is the price of admission and should be budgeted for, not discovered later.

### 7.4 Lineage-based dedup order

Dedup **before** token budgeting, and always keep the *left* item:

1. **OpenThoughts3** appears three times: smoltalk2 `OpenThoughts3_1.2M_think` / `_no_think_no_think`, and Dolci `Dolci Instruct OpenThoughts3+ Science` (99,268, traces removed). → **Keep Dolci's** (non-thinking, ODC-BY, already science-scoped); drop both smoltalk2 copies.
2. **Table-GPT** appears three times: Dolci `TableGPT` (5,000), smoltalk2 `table_gpt_no_think` (13,203), `table_gpt_Qwen3_32B_think` (13,201). → **Keep `table_gpt_no_think`** (biggest non-thinking, MIT); drop the other two.
3. **Aya** appears twice: Dolci `Aya` (99,987), smoltalk2 `aya_dataset_Qwen3_32B_think` (15,222). → **Keep Dolci's**.
4. **Tulu 3 Personas IF** appears twice: Dolci `Dolci Instruct Precise IF` (136,833, Ai2's regenerated version) and smoltalk2 `tulu_3_sft_personas_instruction_following_no_think` (29,970). Also the prompt source for smoltalk2's `multi_turn_reasoning_if_think`. → **Keep Dolci's; add smoltalk2's only after prompt-level dedup.**
5. **WildChat** appears in Dolci (302,406, GPT-4.1 responses), in Tulu 3 (100K), and in Apertus's own prior mix (298,556). → **Keep Dolci's**, and remember your base model may already have seen the Apertus copy in its own SFT.
6. **xLAM** appears as raw `Salesforce/xlam-function-calling-60k`, smoltalk2 `xlam_traces_no_think` (59,962), and Apertus's own mix (60,000). → **Keep smoltalk2's converted version** (saves the first conversion hop) after resolving the licence.
7. **Tulu 3 safety trio** (CoCoNot / WildGuardMix / WildJailbreak) appears in Tulu 3, Dolci, and partially in Apertus's mix. → **Keep Dolci's.**
8. **OpenCodeReasoning-2 questions ⊂ Nemotron v1 `code` prompts** (the Nemotron card points at the OCR-2 README for re-hydration). → Pick one; the recommendation is OCR-2 `solution`-only, so **drop Nemotron `code` entirely**.
9. **TACO / APPS / CodeContests / codeforces** underlie OCR-2, Nemotron `code`, and RECALLED parts of OpenThoughts3's code portion. → Dedup at the *question_id* level across all three.
10. **Finally**: exact + near-duplicate (MinHash) dedup on normalised prompts across the whole 600M-token mix, then a **decontamination pass** against HumanEval(+), MBPP(+), BigCodeBench, LiveCodeBench, IFEval, IFBench, GSM8K, MATH and your Greek evals. Remember that **only OpenCodeInstruct's HumanEval/MBPP decontamination is documented**, and OCR-2 demonstrably carries TACO/APPS *test*-split rows.

### 7.5 Per-source caps and epochs

- **≤ 2 epochs on any source** — the only directly citable evidence is arXiv:2609.01244: past ~2 epochs validation loss overfits, judged task score stops improving, and **instruction-following degrades**; fresh examples beat repeats at equal compute. SmolLM3 ran 4 epochs over a 1.8B-token mix (VERIFIED) — at your 600M target you have enough fresh data to stay at 1–2.
- **Cap any single source at ~15% of the total supervised tokens.** smoltalk2's own weights are the precedent (×0.02 on OpenThoughts3-think, ×0.3–0.5 on the other large sources). With a 150M code block at 25%, OpenCodeInstruct alone at 110M is already 18% — consider trimming it to ~90M and raising `package_instruct`/OCR-2 to keep the style distribution wider.
- **Cap by tokens, not examples**, and print the realised token share per source after packing. The smoltalk2 stats table is the cautionary example: 33.5% of examples = 86.7% of tokens.
- **Mask the loss on user turns and on tool-result turns** (SmolLM3, VERIFIED).
- **Hard-drop any row whose rendered prompt+response exceeds 4,096 tokens** rather than truncating — a truncated assistant turn teaches the model to stop mid-answer.
- **Watch IFEval as the canary** at every checkpoint. Baseline to hold: Apertus-8B-Instruct **71.7** (Apertus harness) / **71.4** (Ai2 harness).

---

## 8. What I could not verify

- **`Salesforce/xlam-function-calling-60k` card body** — gated; only the `cc-by-4.0` metadata tag was readable. Any extra terms in the card are unknown.
- **`nvidia/Nemotron-Post-Training-Dataset-v2` split-level `reasoning` and `generator` distributions** — gated (`auto`), so datasets-server refused. Split sizes and the licence note came from the card page and HF API.
- **Response-token distributions for Dolci-Instruct-SFT per `source_dataset`** — the `/statistics` endpoint reports `messages` only as a list-length stat, so I have message counts but **not** response lengths. **This is the biggest remaining gap**: your precise-IF (90M), chat (72M) and document (48M) budgets all depend on Dolci token yields I could not measure. Measure these locally before finalising the mix.
- **Tülu 3's exact SFT epoch count and LR** — in Appendix A, not surfaced by the fetch. "2 epochs" is RECALLED.
- **AceReason's ~5 epochs** — RECALLED only; do not cite.
- **opc-sft-stage2 decontamination** — RECALLED from the OpenCoder paper; not re-read.
- **Exact share of Nemotron v1 `chat` rows with empty user content** — observed in the sampled first rows and warned about on the card, but not quantified.
- **EvalPlus leaderboard numbers** — the page is JavaScript-rendered and returned no table. All 8B calibration figures above come instead from the OLMo 3 and Apertus papers, which is arguably better since each table is internally consistent.
- **No-call / missing-argument / tool-error coverage per tool-use dataset** — not verifiable from cards; requires local inspection.
