# Instruction-Following (IF) SFT Data — Source-Grounded Research

Prepared 2026-09-19 for the Apertus-8B Greek SFT plan (non-thinking chat model, 4,096-token context,
IF = 15% of 600M supervised tokens = **90M tokens**).

## Verification convention

- **[V]** = VERIFIED against a primary source (paper text, dataset card, or HF datasets-server API) with URL.
- **[R]** = RECALLED / unverified — treat as a lead to check, not as a fact.
- **[EST]** = a number I derived arithmetically from verified inputs. The formula is always shown.
  Token estimates use English ≈ 4 characters/token and are **not** measured with the Apertus tokenizer.
  Greek text on a mostly-Latin BPE typically costs **more** tokens per character, so Greek-side estimates
  are conservative-low.

All row counts below come from `https://datasets-server.huggingface.co/size?dataset=...` unless stated,
queried 2026-09-19.

---

# 1. Inventory of open IF training datasets

## 1.1 Summary table (all row counts [V])

| Dataset | Rows | Turns | Code-verified responses? | Teacher | Licence | Notes |
|---|---:|---|---|---|---|---|
| `allenai/tulu-3-sft-personas-instruction-following` | **29,980** | single (all msgs=2) | **No** | GPT-4o-2024-08-06 | ODC-BY | IFEval's 25 constraint types only; 1–3 constraints/prompt |
| `allenai/tulu-3-pref-personas-instruction-following` | **19,890** | single | No (constraint-relaxation rewrite) | GPT-4o | ODC-BY | DPO pairs |
| `allenai/RLVR-IFeval` | **14,973** | prompts only (msgs=1) | n/a (prompts+verifier) | — | ODC-BY | **24 distinct constraint types**, ~620–655 each |
| `allenai/tulu-3-IF-augmented-on-policy-8b` | **65,530** | single | partly | Tulu-3-8B on-policy | ODC-BY | 70b variant = 65,551 |
| `allenai/tulu-3-wildchat-if-on-policy-8b` | **10,792** | single | No | on-policy | ODC-BY | WildChat prompts containing constraints |
| `allenai/RLVR-GSM-MATH-IF-Mixed-Constraints` | **29,946** | prompts only | n/a | — | ODC-BY | Tulu 3's final RLVR mix |
| `allenai/IF_multi_constraints_upto5` | **95,373** | prompts only (msgs=1) | n/a | — | ODC-BY [R] | **IFBench/IF-RLVR train prompts**, up to 5 constraints |
| `allenai/IF_multi_constraints_upto5_no_lang` | **95,418** | prompts only | n/a | — | ODC-BY [R] | language-constraint-free variant |
| `allenai/IF_sft_data_verified` | **31,751** | single (msgs=2) | **YES** | qwen72b 13,635 / llama405b 8,721 / tulu70b 7,685 / yi34b 1,156 / llama3-8b 554 | ODC-BY [R] | The IFBench paper's "strict" set |
| `allenai/IFBench_multi-turn` | **3,161** | 3-turn | n/a | — | ODC-BY [R] | `ifbench_constraints` 1,387 + `ifeval_constraints` 1,774 |
| `allenai/IFBench_test` | **300** | single+multi | n/a | — | ODC-BY [R] | **EVAL ONLY — never train on this** |
| `allenai/Dolci-Instruct-SFT` (Precise IF slice) | **136,833** | mixed | YES (per OLMo 3 paper) | QwQ-32B | ODC-BY | "Dolci Tülu 3 Precise IF" |
| `allenai/Dolci-Instruct-RL` (IF slice) | **37,568** | prompts | n/a | — | ODC-BY | from `IF_multi_constraints_upto5_filtered` |
| `allenai/Dolci-RL-Zero-IF-7B` | **13,179** | prompts | n/a | — | ODC-BY | RL-Zero IF |
| `HuggingFaceTB/smoltalk2` `SFT/multi_turn_reasoning_if_think` | **28,217** | **6 messages exactly** | [R] | Qwen3-32B [R] | Apache-2.0 [R] | **multi-turn IF**, thinking traces |
| `HuggingFaceTB/smoltalk2` `SFT/tulu_3_sft_personas_instruction_following_no_think` | **29,970** | single | No | — | Apache-2.0 [R] | **= the Tulu personas set (dedup!)** |
| `HuggingFaceTB/smoltalk` `smol-constraints` (v1) | **36,236** | single | [R] | Llama-3.1-405B-Instruct [R] | Apache-2.0 [R] | **decontaminated against IFEval** [V] |
| `nvidia/Nemotron-SFT-Instruction-Following-Chat-v3` | **407,362** (server) / card says 887K total, IF subset 249K | multi-turn | [R] | GPT-OSS-120B (IF), GLM-5 (chat) | CC-BY-4.0 + ODC-By | 2026 release; **contains Tulu personas IF prompts** |
| `nvidia/Nemotron-Instruction-Following-Chat-v1` | **320,426** | multi-turn | [R] | — | CC-BY-4.0 | superseded by v3 chat split |
| `nvidia/Nemotron-RL-Instruction-Following-Structured-Outputs-v2` | **62,696** | — | n/a | — | CC-BY-4.0 | JSON/schema outputs |
| `nvidia/Nemotron-RL-instruction_following-structured_outputs` | **9,949** | — | n/a | — | CC-BY-4.0 | v1 |
| `nvidia/Nemotron-RL-Instruction-Following-Calendar-v2` | **9,915** | — | n/a | — | CC-BY-4.0 | date/calendar formatting |
| `nvidia/Nemotron-RL-Instruction-Following-Citation-Formatting-v1` | **9,540** | — | n/a | — | CC-BY-4.0 | citation format |
| `nvidia/Nemotron-RL-Instruction-Following-Free-Form-Formatting-v1` | **9,037** | — | n/a | — | CC-BY-4.0 | free-form format |
| `nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1` | **2,011** | multi-turn | n/a | — | CC-BY-4.0 | **multi-turn IF RL** |
| `nvidia/Nemotron-RL-Instruction-Following-Adversarial-v1` | **1,000** | — | n/a | — | CC-BY-4.0 | adversarial IF |
| `nvidia/Nemotron-RL-InverseIFEval-v1` | **1,000** | — | n/a | — | CC-BY-4.0 | **counter-intuitive instructions** |
| `nvidia/Nemotron-RL-CFBench-v1` | **1,121** | — | n/a | — | CC-BY-4.0 | en/ar/hi/zh/ja/ko |
| `nvidia/IFEval-Hi` | **848** | single | n/a | — | CC-BY-4.0 | Hindi IFEval — template for a Greek port |
| `ConiferLM/Conifer` | **13,606** | multi-level | No (GPT-4 refinement) | GPT-4 | Apache-2.0 | complex/multi-level constraints |
| `kkk-an/UltraIF-sft-175k` | **181,147** | single | eval-question filtering | Llama-3.1-8B pipeline | CC-BY-4.0 | decomposed real user prompts |
| `kkk-an/UltraIF-dpo-20k` | (server: 0 rows — not auto-converted) | — | — | — | CC-BY-4.0 | DPO |
| `Post-training-Data-Flywheel/AutoIF-instruct-61k` | **61,492** | single | **YES (executed unit tests)** | Qwen2/LLaMA3 pipeline | Apache-2.0 | AutoIF released data |
| `THU-KEG/VerInstruct` | **27,498** | single | hybrid code + QwQ-32B judge | — | Apache-2.0 | en+zh; hard + **soft** constraints |
| `Junjie-Ye/MulDimIF` | **9,106** | — | — | — | CC-BY-4.0 | en+zh, multi-dimensional |
| `zk-guo/RECAST-30K` | **29,939** | — | — | — | CC-BY-4.0 | many-constraint |
| `gililior/wild-if-eval` | **7,523** | — | — | — | Apache-2.0 | decomposed real WildChat constraints (eval) |
| `YuxinJiang/FollowBench` | **1,852** | — | LLM-judge | — | Apache-2.0 | EVAL |
| `kqsong/InFoBench` | **500** | — | LLM-judge (DRFR) | — | MIT | EVAL |
| `THU-KEG/IFBench` | **444** | — | — | — | Apache-2.0 | **name collision** — NOT the AI2 IFBench |

Licences marked [R] are inherited-from-collection assumptions; **re-check each card before shipping.**

## 1.2 Tulu 3 personas IF — exact profile [V]

From the HF statistics endpoint (`/statistics?dataset=allenai/tulu-3-sft-personas-instruction-following`):

- constraints per row: **1 → 10,089 | 2 → 9,959 | 3 → 9,932**; mean 1.995, max 3.
- `messages` length: min 2, max 2 → **100% single-turn**.
- prompt length: mean 299 chars, median 274, max 2,551.
- Columns: `id, prompt, messages, constraints`. There is **no verification/pass field**.

Construction (Tülu 3 paper, https://arxiv.org/abs/2411.15124) [V]:
> "We use our persona-driven approach to synthetically generate verifiable instructions covering 25 different
> constraint types defined in IFEval... we start by manually writing 1-2 example instructions per constraint...
> resulting in total of 33 verifiable instructions which we used as seed prompts... In total, we collected
> 29,980 verifiable instruction-response pairs which we call If-Persona-Sft."

**Weakness (important):** the instructions are verifiable, but the paper never says the *responses* were run
through the verifiers at SFT time. The dataset card confirms no verification column. Contrast with the DPO
stage, where AI2 explicitly did verify and reported the result:
> "We generate an additional set of more than 66k instances and we then run the chosen completions through
> constraint verifier functions, and only add those instances to the final set which actually fulfilled the
> constraint(s). This leaves us with a cleaned set of about 26k preferences" — i.e. **~60% of GPT-4o chosen
> completions were discarded as constraint-violating.** [V]

That ~40% survival rate is the single best argument for re-running verifiers over any dataset you import.

Also note Tulu 3's own finding on the verified-vs-unverified trade-off [V]:
> "The IF-augmented-verified dataset improves IFEval performance only by 1 point, while also slightly harming
> the average performance... We therefore choose to include IF-augmented (not verified) and Persona IF in the
> final 8B DPO mix."

## 1.3 IFBench / IFTrain / IF-RLVR (Pyatkin et al. 2025) [V]

Paper: **"Generalizing Verifiable Instruction Following"**, arXiv:2507.02833v2,
https://arxiv.org/abs/2507.02833 · code https://github.com/allenai/IFBench

**Contributions:** IFBench = **58 new verifiable test constraints**, 300 prompts, built by attaching
constraints to *held-out (unreleased)* WildChat prompts, human-checked for prompt/constraint compatibility,
across **7 categories: count, ratio, words, sentence, format, custom, copy**. IFTrain = **29 new training
constraints** + verifiers ("more than doubles the current set of train constraint types").

**Training data recipe** [V]:
> "We randomly sample prompts from Tülu-3-SFT and we append at least one and up to n constraints. We prevent
> the combination of contradictory constraints by maintaining a dictionary of constraint conflicts... For most
> of the experiments we create about 60k-100k prompts."

### Findings that matter for your plan

**(a) Number of constraints per prompt.** Table 1 (Qwen2.5 policy), IFBench / IFEval by max constraints n:

| n constraints | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| IFBench | 48.9 | 53.1 | **59.5** | 49.4 | 55.8 | 54.1 |
| IFEval | 71.2 | 79.9 | 77.8 | 79.5 | 79.9 | **85.8** |

> "training on a bigger combination of constraints leads to better performance, compared to training on only up
> to 3 constraints per instance. Interestingly, instructions in IFEval have up to 3 constraints and up to 2
> constraints in IFBench, but training on up to 5 or 6 constraints still leads to better generalization."

**Read carefully:** n=1 is clearly worst on both axes, but the IFBench column is non-monotonic (peak at 3,
dip at 4). The robust claim is "**more than one constraint**", not "monotonically more is better".

**(b) Instances per constraint saturate fast.** Same table, instances/constraint 10/50/100/500/1000 →
IFBench 48.6 / 52.7 / 51.7 / 51.0 / 48.6; IFEval 73.6 / 72.8 / 74.3 / 70.1 / 72.8.
**Going from 50 to 1000 examples per constraint buys nothing and may hurt.** This is the strongest evidence in
the literature that *constraint variety beats example count*.

**(c) Constraint variety.** §4.2: training on IFTrain(29 unseen) + n IFEval constraints, n∈{5,10,15,20,25}.
"A combination of the full IFTrain and IFEval constraints leads to the highest in-domain performance on
IFEval... On the out-of-domain benchmark IFBench, on the other hand, performance is less affected by the number
of IFEval constraints... training on a larger set and larger variety of constraints is beneficial for
generalization."

**(d) Variable ranges.** §4.3: train ranges disjoint from test ranges scores **lower**; a **wider** train range
that includes and extends the test range "performs comparably and often even better than training on the same
range."  → **Sample constraint variables from a wider range than you expect at test time.**

**(e) Category ablation.** §4.4: removing **length** and **keywords** categories harms IFEval most; removing
**change_case** and **detectable_format** barely matters (89.65 IFEval).

**(f) SFT vs DPO vs GRPO — controlled, same prompts, same verifiers** (Table 5) [V]:

| | DPO after SFT | DPO after DPO | GRPO after SFT | GRPO after DPO |
|---|---|---|---|---|
| IFEval strict | 76.89 | 79.67 | 85.77 | **89.65** |
| IFBench strict | 25.2 | 29.3 | 28.6 | **30.6** |

> "GRPO training with IF verifiable rewards consistently outperforms the model trained with DPO on IFEval and
> IFBench. Further, starting with a model that has gone through both SFT and DPO training results in higher
> final IF performance."

**(g) Headline gains** (Table 3 / abstract): Tülu-3-8B **IFEval 82.4 → 92.2**, **IFBench 28.9 → 45.9**.
Qwen2.5-7B base → IFEval 87.8, IFBench 54.7. Cost: **AlpacaEval 2 collapses 34.5 → 21.3** while GSM8K/MMLU/BBH
stay roughly flat (83.2/66.4/68.9).

**(h) RLVR from base + reasoning template generalizes best** (Table 6): from-base IFBench = llama3.1 54.1,
qwen2.5 53.7, olmo2 46.6, vs from-instruct 44.6/45.9/44.6. "IF-RLVR with reasoning leads to improved IF
generalization." **Caveat for you: Apertus is a non-thinking model, so this route is not directly available.**

**(i) Multi-turn** (Table 7, Qwen2.5-7B-Instruct), IFEval/IFBench constraints, single-turn and multi-turn eval:

| trained on | single-turn eval (IFE/IFB) | multi-turn eval (IFE/IFB) |
|---|---|---|
| single turn | 89.1 / 45.9 | 85.2 / 71.7 |
| multi turn | 81.5 / 34.7 | 90.2 / 68.6 |
| **mix** | 86.6 / 54.8 | 89.5 / **72.9** |

> "IF-RLVR-multi mostly leads to an improved performance on the multiturn setup... while harming the singleturn
> performance. **IF-RLVR-mix harms singleturn performance less, and sometimes even helps it, while reaching a
> comparable multiturn performance.**"

**→ Directly actionable: train on a MIX of single- and multi-turn IF, not multi-turn alone.**
Multi-turn setup is 3 turns: (user task t) → (assistant r1) → (user: rewrite r1 to comply with constraint c).
**That is exactly your weak "redirect/redo" case (35%).**

**(j) Reward hacking / response quality** [V]. §5: with GPT-4.1 as judge scoring how well a completion answers
the prompt *with the constraint removed*, "Completions from the base policy are scored higher by the
LLM-as-judge than completions from the IF-RLVR trained model, for both IFEval and IFBench prompts." Mitigation:
add a general RM signal, F = V+1 if V>0 and S>α; V−0.5 if V>0 and S≤α; V otherwise, with
Llama-3.1-Tulu-3-8B-RM and α=7. Result: IFEval 86.1, IFBench 30, **AlpacaEval 2 recovers to 31.6**.

**(k) DPO pair construction is hard** (Table 4) [V]: fraction of prompts where a model got **all** constraints
right — Tulu-3-70B 15%, Qwen-72B 26%, Llama-3.1-405B 21%, Llama3-8B 6%, Yi-34B 10%. And:
> "Out of all the instances that models get completely correct, **54% have only 1 constraint and only 2% have 5
> constraints**. We also find that most LLMs get the same easy instances right and the same hard instances
> wrong, which makes the creation of preference pairs more difficult."

This is why `IF_sft_data_verified` is only 31,751 rows: it is the surviving "strict" set.

## 1.4 OLMo 3 / Dolci (arXiv:2512.13961) [V]

Precise-IF construction [V]:
> "We source precise IF prompts from the overall Tülu 3 mix with additional verifiable constraints added from
> Pyatkin et al. (2025). We also regenerate Persona IF prompts as in Tülu 3, but with personas sourced from
> Meyer and Corneil (2025). We then generate responses for each prompt using **QwQ-32B**, and we **verify
> responses using verifiers associated with each constraint, keeping only the correct responses.**"

→ **Dolci's precise IF IS response-verified; Tulu 3's personas IF is not.** Prefer Dolci.

Mixture sizes: Dolci Instruct SFT total **2,152,112**, with category `Precise IF` = **136,833** [V, statistics
endpoint + card]. Dolci **Think** SFT carries "Dolci Think Persona Precise IF" 223,123→220,530 and "Dolci Think
Precise IF" 135,792→135,722 [V, paper table]. RL IF prompts = "IF-RLVR (Pyatkin et al. 2025) with up to 5
constraints, which are sampled from IFEval and IFBench-Train", appearing as
`allenai/IF_multi_constraints_upto5_filtered_dpo_0625_...` = **37,568** rows in `Dolci-Instruct-RL` [V].

**Stage-by-stage IF results (Table 24)** [V] — the most important table in this report:

| | Think SFT | Think DPO | Think RL | Instruct SFT | Instruct DPO | Instruct RL |
|---|---|---|---|---|---|---|
| **7B** IFEval | 83.9 | 80.6 | **86.0** | 81.7 | 82.0 | **85.8** |
| **7B** IFBench | 30.0 | 28.3 | **41.6** | 27.4 | 29.3 | **32.3** |
| **32B** IFEval | 83.7 | 82.3 | 89.0 (3), 93.8 (3.1) | 87.7 | 87.3 | 88.8 |
| **32B** IFBench | 37 | 34.4 | 47.6 (3), **68.1 (3.1)** | 29.7 | 36.3 | 39.7 |

> "the final RL training stage leading to the biggest improvements in Olmo 3's precise instruction-following
> abilities... for both the development (IFEval) and the unseen (IFBench) evaluations."

**Sobering conclusion for a 90M-token SFT allocation:** at 7B, ~137k verified precise-IF SFT rows +
2.15M-row mixture gives **IFEval 81.7 / IFBench 27.4** (Instruct SFT). DPO adds ~+2/+2. **RL adds +4/+5
(Instruct) or +2/+11.6 (Think).** Your current Greek IFEval prompt-strict of 61–68% is below OLMo 3 7B Instruct
SFT's 81.7, so there is real headroom from SFT alone — but **IFBench-style generalization is an RL story**, and
the non-thinking Instruct track gains much less on IFBench (27.4→32.3) than the thinking track (30.0→41.6).

OLMo 3 also reports the over-optimization trade-off [V]:
> "we observe a trade-off when performing OlmoRL on IFEval alone, wherein higher IFEval scores correlate with
> lower AlpacaEval scores. However, when we perform our final mixed training, we are able to maintain high
> AlpacaEval scores without compromising IFEval performance, as the LM-judge reward..."

## 1.5 smoltalk2 [V]

`https://huggingface.co/datasets/HuggingFaceTB/smoltalk2` — configs `Mid` (4,779,894), `SFT` (3,383,242),
`Preference` (446,886). IF-relevant splits:

- `SFT/multi_turn_reasoning_if_think` — **28,217 rows, every row exactly 6 messages** (3 user + 3 assistant),
  `source = multi-turn-reasoning-if`. **This is the single best off-the-shelf multi-turn IF SFT set.**
  Caveat: it carries thinking traces; Apertus is non-thinking → strip `<think>` content, which changes the
  assistant distribution and must be re-verified.
- `SFT/tulu_3_sft_personas_instruction_following_no_think` — **29,970 rows**, i.e. the Tulu personas set
  re-rendered without thinking. **This is a duplicate of source (a); dedup mandatory.**
- Multilingual (8 languages): `SFT/smoltalk_multilingual8_Qwen3_32B_think` 244,736 and
  `SFT/smoltalk_multilingual_8languages_lang_5_no_think` 254,047. **Greek is not one of SmolLM3's 8 languages**
  [R — verify the language list before assuming].
- `SFT/smoltalk_systemchats_Qwen3_32B_think` 27,436 + `SFT/smoltalk_smollm3_systemchats_30k_no_think` 33,997 —
  **system-prompt-following** data, directly relevant to your weak "standing instruction" case.

smoltalk v1 `smol-constraints` = **36,236 rows** [V]; card: "a 36K-sample dataset that trains models to follow
specific constraints, such as generating responses with a fixed number of sentences or words, or incorporating
specified words in the output. **The dataset has been decontaminated against IFEval to prevent overlap.**" [V]

## 1.6 Other methods (abstracts verified)

- **AutoIF** — "Self-play with Execution Feedback", arXiv:2406.13542 [V]. "transforms the validation of
  instruction-following data quality into code verification, requiring LLMs to generate instructions, the
  corresponding code to check the correctness of the instruction responses, **and unit test samples to verify
  the code's correctness**. Then, execution feedback-based rejection sampling..." Improves SFT, offline DPO and
  online DPO on Qwen2/LLaMA3. **Open data:** `Post-training-Data-Flywheel/AutoIF-instruct-61k` = 61,492 rows,
  Apache-2.0 [V] (community re-release, plus a `-with-funcs` variant with the verifier functions — that variant
  is the valuable one because it ships executable checkers).
- **Conifer** — arXiv:2404.02823 [V]. 13,606 rows, Apache-2.0. GPT-4-curated multi-level complex constraints +
  "progressive learning scheme that emphasizes an easy-to-hard progression, and learning from process feedback."
  7B model "outperforms the state-of-the-art open-source 7B models".
- **UltraIF** — arXiv:2502.04153 [V]. 181,147 SFT rows, CC-BY-4.0. "decomposes real-world user prompts into
  simpler queries, constraints, and corresponding evaluation questions"; trains an *UltraComposer*; aligns
  LLaMA-3.1-8B-**Base** to match its Instruct version on 5 IF benchmarks "using only 8B model as response
  generator and evaluator". **Most relevant precedent for doing this cheaply without a frontier teacher.**
- **VerIF / VerInstruct** — arXiv:2506.09942 [V]. 27,498 rows, en+zh, Apache-2.0. "combines rule-based code
  verification with LLM-based verification from a large reasoning model (e.g., QwQ-32B)", ~22,000 instances with
  verification signals; models "generalize well to unseen constraints" and "general capabilities remain
  unaffected". **This is the template for handling SOFT constraints you cannot regex.**
- **"From Complex to Simple"** (He et al. 2024) — arXiv:2404.15846 [V]. "We found that training LLMs with
  instructions containing **multiple constraints** enhances their understanding of complex instructions,
  especially those with lower complexity levels. **The improvement can even generalize to compositions of
  out-of-domain constraints.**" Independent corroboration of IFBench §4.1.
- **Multi-IF** — arXiv:2410.15553 [V]. 4,501 conversations × 3 turns, 8 languages (English + 7). "All the
  models tested showed a higher rate of failure in executing instructions correctly with each additional turn.
  For example, **o1-preview drops from 0.877 at the first turn to 0.707 at the third turn**... **languages with
  non-Latin scripts (Hindi, Russian, and Chinese) generally exhibit higher error rates**." Greek is not in the
  7 [R]. **Training implication: multi-turn degradation is universal and is the same failure your 68%/35%
  numbers describe.**
- **M-IFEval** — arXiv:2502.04688 [V]. French, Japanese, Spanish, "with both general and **language-specific**
  instructions"; "benchmark performance across languages and instruction types can vary widely". **Precedent
  that a faithful port needs language-specific constraints, not just translation.**
- **MaXIFE** — arXiv:2506.01776 [V]. "**23 different languages with 1667 verifiable instruction tasks**",
  rule-based + model-based. Reportedly 47 instruction types vs IFEval's 25 [R — the 47 figure came from a
  search summary, not the abstract]. **No HF dataset found under that name** [V — empty search result]; check
  the paper's repo. **Worth checking whether Greek is among the 23** — I could not confirm.
- **Nemotron** — `nvidia/Nemotron-SFT-Instruction-Following-Chat-v3`, created **2026-06-04** [V], CC-BY-4.0 +
  ODC-By, "ready for commercial/non-commercial use". Card [V]: chat prompts from lmarena/lmsys/WildChat,
  responses from **GLM-5**, best-of-N by `Qwen3-Nemotron-235B-A22B-GenRM-2603`, conversations extended by user
  simulation with GLM-5; "**For multi-turn robustness, a randomly sampled response at a given turn is used as
  the context for extension instead of using the best judged response. Only the last assistant turn in each
  sample should hence be used for training.**" IF split "generated with the same pipeline as v2 using
  **GPT-OSS-120B (medium effort)**. We further include prompts from tulu-3-sft-personas-instruction-following
  and generate responses using GPT-OSS-120B."
  **Two landmines:** (1) it re-uses Tulu personas IF prompts → dedup; (2) rows sourced from lmsys-chat-1m /
  WildChat-1M have **system + first user message set to `null`** and need `prepare_chat_prompts.py` + an
  HF token to reconstruct [V].
  **Size discrepancy to resolve:** card says Chat 637K / IF 249K / Total 887K, but the datasets-server reports
  **407,362** rows for the auto-converted config. Do not quote a single number until reconciled.
- **Benchmarks worth mining for taxonomy only (not training):** FollowBench (1,852; multi-level, LLM-judged,
  "situation, style, and format constraints" per the IFBench related-work [V]), InFoBench (500, MIT,
  decomposes instructions into atomic constraints judged individually [V]), WildIFEval
  (`gililior/wild-if-eval` 7,523, Apache-2.0 — real WildChat constraints decomposed), MulDimIF (9,106),
  RECAST-30K (29,939), `nvidia/Nemotron-RL-SysBench-v1` and `-CFBench-v1` (1,121).
  **Name collision warning:** `THU-KEG/IFBench` (444 rows) is a *different* benchmark from AI2's IFBench [V].
- **Not located / unverified in this pass [R]:** Suri (long-form multi-constraint), CRAB, SPaR, IHEval,
  LIFBench, ComplexBench training data. I found no authoritative HF training set for these under those exact
  names; the ComplexBench/CFBench/SysBench hits are either eval ports or Nemotron RL repackagings. Treat these
  as open leads.

---

# 2. What actually improves IF in SFT at 7–8B

### 2.1 Constraint variety ≫ example count — the clearest result
IFBench Table 1: **10 / 50 / 100 / 500 / 1000 instances per constraint → IFBench 48.6 / 52.7 / 51.7 / 51.0 /
48.6.** Flat-to-declining past ~50. Meanwhile going 29→54 constraint types measurably helps generalization.
**Implication for your 90M tokens: do not spend them on more rows of the same 44 families. Spend them on more
families, then on composition.**

### 2.2 Multi-constraint composition helps, and generalizes to unseen compositions
IFBench §4.1 (n=1 is worst; 3–6 best) plus He et al. 2024's independent "generalize to compositions of
out-of-domain constraints". Your current 1–5 constraints/prompt is already right; the Tulu personas set you'd
import is capped at **3** and is 34% single-constraint.

### 2.3 Widen constraint variable ranges
IFBench §4.3: train on a **wider** range than test ⇒ equal or better than matched range; **disjoint** range ⇒
worse. Cheap, purely programmatic win.

### 2.4 Hard vs soft constraints
IFBench is deliberately hard-only and admits the limitation [V]: "We exclusively focus on verifiable
constraints, which is limiting, as many constraints used by users in the wild are constraints that do not have
an easily verifiable ground truth. This also means our constraints might sometimes seem unnatural or
contrived." VerIF's answer is hybrid code + LLM verification over hard **and** soft constraints, and it reports
general capabilities unharmed. FollowBench's style/situation constraints are LLM-judged by construction.
**Take: keep a soft-constraint slice (≈20–25%) judged by an LLM, or the model learns contrived formatting and
loses chat quality — exactly the AlpacaEval 34.5→21.3 failure.**

### 2.5 Category ablation: length and keywords are load-bearing
IFBench §4.4: dropping **length** or **keywords** hurts IFEval most; dropping **change_case** or
**detectable_format** barely matters. Note this is about *what to keep*, and it is measured on IFEval, which is
itself format-heavy — do not over-generalize.

### 2.6 Overfitting to the IFEval 25 — the numbers
- Abstract [V]: "most models strongly overfit on a small set of verifiable constraints... leading models such
  as **GPT-4.1 or Claude 3.7 Sonnet score below 50%**" on IFBench; also "**Qwen3-32B or Claude 4 Sonnet score
  below 50%**".
- Tulu 3's earlier IFEval-OOD (52 constraints, 6 categories) found the same [V]: "there is a significant
  difference between performance on IFEval and IFEval-OOD of all the models, even though we created the latter
  to be structured very similar to the original dataset, just with a disjoint set of constraints... those
  models that do well on IFEval are likely overfitting to the specific set of constraints."
- Concretely: Tülu-3-8B **IFEval 82.4 vs IFBench 28.9**; Tulu-DPO 81.1 vs 25.5; OLMo 3 7B Instruct SFT
  **81.7 vs 27.4**. A ~55-point gap is normal.
- **Your Greek IFEval 61–68% is therefore not the metric to optimize.** Krikri-8B's 66.8 tells you nothing
  about generalization. You need a Greek IFBench-style OOD set or you will optimize into the same trap.

### 2.7 Multi-turn persistence
IFBench Table 7: training on a **mix** of single- and multi-turn dominates either alone (Qwen2.5-7B-Instruct
multi-turn IFBench: single-trained 71.7, multi-trained 68.6, **mix 72.9**, while single-turn IFBench is
45.9 / 34.7 / **54.8**). Multi-IF shows the universal per-turn decay (o1-preview 0.877→0.707 over 3 turns).
Their multi-turn format — task, assistant answer, then "rewrite it to comply with c" — **is** your redo case.
Nemotron v3's trick is relevant too: extend context from a *randomly sampled* (not best) prior response, and
train only on the last assistant turn — this teaches recovery from a mediocre own-turn rather than from a
golden one.

### 2.8 Response quality under constraints
See §1.4(j). The mitigation that worked is a **combined reward** (verifiable + general RM with a threshold),
recovering AlpacaEval 21.3 → 31.6 at a cost of IFEval 92.2 → 86.1. In SFT terms the analogue is: **reject
constraint-satisfying responses that are bad answers**, with a quality judge, not just a verifier.

### 2.9 System-prompt vs user-prompt constraints
IFBench frames this as the "instruction hierarchy" (Wallace et al.) and observes models differ in how they
prioritize composed instructions [V], but runs no system-vs-user ablation. smoltalk's `systemchats-30k` /
smoltalk2 systemchats (27,436 + 33,997) are the available training data. **I found no paper quantifying
system-prompt vs user-prompt constraint training at 7–8B** — treat as an open question, and note your
"standing instruction kept 68%" is precisely a system/standing-rule failure.

### 2.10 Does English IF data transfer to other languages?
This is the crux of the "English first" strategy, and the evidence is **encouraging but conditional**:

- **"Multilingual Instruction Tuning With Just a Pinch of Multilinguality"** arXiv:2401.01854 [V]:
  "many languages transfer some instruction-following capabilities to other languages from even monolingual
  tuning... **only 40 multilingual examples integrated in an English tuning set substantially improve
  multilingual instruction-following, both in seen and unseen languages**... models tuned on multilingual
  mixtures exhibit comparable or superior performance in multiple languages... **despite training on 10x fewer
  examples** in those languages... **diversifying the instruction tuning set with even just 2-4 languages
  significantly improves cross-lingual generalization.**"
- **"Zero-shot cross-lingual transfer in instruction tuning"** arXiv:2402.14778 [V]: "cross-lingual transfer
  does happen successfully in IT even if all stages of model training are English-centric, **but only if
  multilinguality is taken into account in hyperparameter tuning and with large enough IT data**. English-trained
  LLMs are capable of generating correct-language, comprehensive and helpful responses in other languages, but
  **suffer from low factuality and may occasionally have fluency errors**."
- **Multi-IF** [V]: non-Latin scripts (Hindi, Russian, Chinese) have higher error rates. Greek is also
  non-Latin.

**Synthesis:** English-dominant IF training should transfer the *skill* to Greek, and a very small Greek slice
disproportionately unlocks it. But (i) format/fluency transfer better than factuality, (ii) non-Latin script
costs you, and (iii) **constraints whose verifier is language-dependent will not transfer at all** — they will
transfer as *wrong behaviour* (see §4.3). The owner's plan (English now, small Greek adaptation later) is
well-supported; just make the Greek slice non-zero and put it on the language-dependent families first.

---

# 3. Proposed constraint taxonomy for scaling

## 3.1 The IFEval 25 [V]
Extracted from `instructions_registry.py` (active, uncommented entries), google-research:
https://raw.githubusercontent.com/google-research/google-research/master/instruction_following_eval/instructions_registry.py
9 categories, 25 instruction IDs:

| # | ID | Category |
|---|---|---|
| 1 | `keywords:existence` | keywords |
| 2 | `keywords:frequency` | keywords |
| 3 | `keywords:forbidden_words` | keywords |
| 4 | `keywords:letter_frequency` | keywords |
| 5 | `language:response_language` | language |
| 6 | `length_constraints:number_sentences` | length |
| 7 | `length_constraints:number_paragraphs` | length |
| 8 | `length_constraints:number_words` | length |
| 9 | `length_constraints:nth_paragraph_first_word` | length |
| 10 | `detectable_content:number_placeholders` | content |
| 11 | `detectable_content:postscript` | content |
| 12 | `detectable_format:number_bullet_lists` | format |
| 13 | `detectable_format:constrained_response` | format |
| 14 | `detectable_format:number_highlighted_sections` | format |
| 15 | `detectable_format:multiple_sections` | format |
| 16 | `detectable_format:json_format` | format |
| 17 | `detectable_format:title` | format |
| 18 | `combination:two_responses` | combination |
| 19 | `combination:repeat_prompt` | combination |
| 20 | `startend:end_checker` | startend |
| 21 | `startend:quotation` | startend |
| 22 | `change_case:capital_word_frequency` | change_case |
| 23 | `change_case:english_capital` | change_case |
| 24 | `change_case:english_lowercase` | change_case |
| 25 | `punctuation:no_comma` | punctuation |

(`multi-turn:constrained_start`, `keywords:key_sentences`, `detectable_content:rephrase_paragraph` and
`detectable_format:rephrase` exist in the file but are **commented out** — useful ideas AI2 abandoned.)

## 3.2 The IFBench 58 test constraints [V] (Appendix A, arXiv:2507.02833v2) — counted: 8+11+5+3+11+11+9 = 58
**count (8):** conjunctions (≥N coordinating conjunctions) · numbers (exactly N numbers) · person_names (≥N
different person names) · pronouns (≥N pronouns) · punctuation (every standard punctuation mark incl.
interrobang) · unique_word_count (≥N unique words) · word_count_range (between min and max words) ·
words_french (every Nth word in French).
**format (11):** emoji at end of every sentence · line_indent (stairs) · list with custom separator · newline
(each word on a new line) · no_bullets_bullets · options (answer with one of...) · parentheses nested ≥5 deep ·
quote_unquote · quotes nested ≥3 deep alternating · sub-bullets · thesis (italics via HTML).
**ratio (5):** trigram overlap %±2 with a reference · sentence_balance · sentence_type (2:1 declarative:
interrogative) · sentence_words (3 sentences, equal char counts, all different words) · stop_words ≤ %.
**sentence (3):** alliteration_increment · increment (each sentence exactly k more words) · keyword in the
N-th sentence.
**words (11):** alphabet (each word starts with next letter) · consonants (consonant cluster in each word) ·
last_first (last word of sentence = first of next) · no_consecutive (no two consecutive words share first
letter) · odd_even_syllables · palindrome (≥10, each ≥5 chars) · paragraph_last_first · prime_lengths ·
repeats (no word more than k times) · start_verb · vowel (only one vowel type).
**custom (11):** character_reverse · csv_city · csv_quotes · csv_special_character · date_format_list
(YYYY-MM-DD) · european_capitals_sort (by latitude) · mcq_count_length · multiples · reverse_newline ·
sentence_alphabet (26 sentences A–Z) · word_reverse.
**plus (9):** count/keywords_multiple (kw1×1, kw2×2, kw3×3, kw4×5) · words/keywords_specific_position (n-th
sentence, m-th word) · words/words_position (2nd and 2nd-to-last word) · copy/repeat_change · copy/repeat_simple ·
copy/repeat_span (word indices) · format/title_case · format/output_template · format/no_whitespace.

## 3.3 The IFTrain 29 training constraints [V] (Appendix B) — counted: 29
word_once · word_count_diff_numb · exclude_word_harder · letter_counting2 · paragraphs (`* * *` divider) ·
paragraphs2 (two line breaks) · first_word_sent · first_word_answer · last_word_sent · last_word_answer ·
bigram_wrapping (`<<I am>>`) · copying_simple · copying_multiple (N times, 6 asterisks) · punctuation_dot ·
punctuation_exclamation · lowercase_counting · letter_counting · counting_composition (3 paragraphs × n_sent ×
n_words) · count_unique · count_increment_word · palindrome · keyword_specific_position · start_end (same word
start and end) · repeat_phrase (N times, one word replaced each time) · no_adjacent_consecutive ·
square_brackets · sentence_hyphens · copy · copy_span_idx (character indices).

## 3.4 Candidate families to add, by heading
Marked **[P]** programmatically verifiable, **[J]** needs an LLM judge, **[P/J]** hybrid.
I do not know your exact 44, so this is a candidate menu; strike what you already have.

**Length** — word/sentence/paragraph/character counts [P]; ranges rather than exact values [P]; *per-section*
length [P]; monotone increment/decrement across sentences [P]; token-budget "answer in under N words, then
stop" [P]; long-form floor (≥N words, the Suri regime) [P].

**Format/structure** — Markdown heading levels [P]; table with exactly N columns [P]; numbered vs bulleted [P];
nesting depth [P]; separators/dividers [P]; no-whitespace, title case, template filling [P]; "no markdown at
all" [P]; code fence with a named language [P].

**Lexical include/exclude** — include word/phrase [P]; exact frequency [P]; forbid word/phrase [P]; forbid a
*category* (e.g. no brand names) [J]; synonym-level avoidance [J]; include N of a given list [P].

**Position** — first/last word of response [P]; first word of the n-th paragraph [P]; keyword at sentence n,
word m [P]; second and second-to-last word [P]; start with a verb [P/J — needs a POS tagger].

**Counting** — letters, words, sentences, unique words, pronouns, conjunctions, digits, emoji [P];
syllables [P/J — needs a syllabifier]; stop-word ratio [P]; trigram overlap with a reference [P].

**Case/punctuation** — all caps / all lower [P]; capitalized-word frequency [P]; ban a punctuation mark [P];
require every punctuation mark [P]; sentence-final punctuation type ratios [P].

**Language/script/register** — respond entirely in language X [P, via langid]; every N-th word in language Y
[P]; script constraint (no Latin characters) [P]; register/formality (formal vs informal address) [J];
transliteration [P].

**Style/persona/audience** — write as persona P [J]; for an audience of 8-year-olds [J]; tone [J];
no first person [P]; second person only [P/J]; ban hedging [P via lexicon / J for real coverage].

**Content** — must cover topics {a,b,c} [J]; must NOT mention X [P for literal, J for semantic]; must include
a counter-argument [J]; must cite N sources [P for count, J for validity].

**Process** — think step by step then answer [P for structure, J for faithfulness]; answer first, then justify
[P]; give exactly N alternatives then pick one [P]; state assumptions before answering [P/J].
**NB: for a non-thinking model these are output-structure constraints, not reasoning constraints.**

**Conditional** — "if the text mentions X, answer in JSON, else in prose" [P, if the branch predicate is
decidable]; "if you don't know, say exactly 'ΔΕΝ ΓΝΩΡΙΖΩ'" [P]. **This family is largely absent from IFEval
and IFBench and is a real-use-case gap.**

**Negation** — "do not use bullet points" [P]; "do not apologize" [P]; "do not restate the question" [P/J];
"answer without using the word 'the'" [P]. Negative constraints are known to be harder; worth a dedicated slice.

**Priority/conflict handling** — two constraints that partially conflict, with an explicit precedence rule [J];
"if constraints conflict, prefer the length limit" [P/J]. Not covered by any IFEval/IFBench family.

**System-level standing rules** — a system prompt that sets a persistent rule, tested several turns later [P if
the rule is verifiable]; "always end with a disclaimer" [P]; system-vs-user conflict where system must win [J].
**This is your 68% failure and IFEval has no family for it.**

**Multi-turn add/modify/revoke** — add a constraint at turn 2 that must persist to turn 4 [P]; revoke a
standing constraint [P]; modify a parameter (N=3 → N=5) [P]; redo the previous answer under a new constraint
[P]. **This is your 35% failure and is exactly the IFBench multi-turn format.**

**Editing with preservation** — "rewrite this keeping every proper noun unchanged" [P]; "shorten by 30% without
losing any numbered fact" [P/J]; "translate but keep code blocks verbatim" [P].

**Structured outputs** — JSON conforming to a given schema [P, jsonschema]; YAML [P]; CSV/TSV with quoting and
a special character [P]; exactly N rows [P]; Markdown table [P]; XML [P]. Nemotron's Structured-Outputs-v2
(62,696) is the ready-made source.

**Tool/function-call formatting** — emit a call matching a given signature [P]; arguments-only, no prose [P];
N parallel calls [P]. `nvidia/...Citation-Formatting` (9,540) and `Calendar-v2` (9,915) are adjacent.

**Refusal of impossible/contradictory constraints** — "write a 5-word essay of 200 words" → the model should
flag the contradiction rather than silently pick one [J]. `nvidia/Nemotron-RL-InverseIFEval-v1` (1,000) and
`-Adversarial-v1` (1,000) target this. **Note IFBench deliberately removed conflicts** ("we manually checked
samples to avoid situations where a model could only fulfill either the question or the constraint") — so this
family is genuinely unaddressed by the AI2 line of work and is a differentiator.

---

# 4. Splitting a verifiable prompt reservoir between SFT and RL/preference

## 4.1 What the prior work actually did

- **Tulu 3** [V]: **reuses prompts across stages.** If-Persona-Sft (29,980) is converted into If-Persona-Pref
  (~20K) by *relaxing a constraint* in the prompt and using the response to the modified prompt as the
  rejected. IF-augmented prompts are "only used for the DPO and RLVR stages". RLVR-IFeval (14,973) draws from
  the Tülu 2 SFT mix. **So: SFT and preference share prompts; the RLVR pool is separate-ish but same taxonomy
  (24–25 IFEval constraint types throughout).** No constraint-level hold-out — which is exactly why Tulu 3
  scores 82.4 IFEval / 28.9 IFBench.
- **IFBench / IF-RLVR** [V]: **constraint-level hold-out is the central design.** "We define a taxonomy of
  constraint templates, which we split into training and test constraints to prevent contamination", and test
  prompts use WildChat prompts "**held out from release**". They additionally hold out **variable ranges**
  (§4.3) and run **leave-one-category-out** (§4.4). The DPO-vs-GRPO comparison (Table 5) is run on *the same
  prompts and constraints and verifiers* — a clean controlled design worth copying.
- **OLMo 3 / Dolci** [V]: SFT precise IF = Tülu-3 mix prompts + Pyatkin constraints, QwQ-32B responses,
  verifier-filtered. RL IF = "prompts from IF-RLVR with up to 5 constraints, sampled from IFEval and
  IFBench-Train". **Same constraint taxonomy, different prompt pools, and the SFT responses are consumed
  (verified-correct only) while the RL pool keeps prompts unanswered.** Evaluation stays honest because
  IFBench's 58 test constraints were never trained on.

## 4.2 Recommended split design

Build **one reservoir** of (task prompt × constraint template × instantiated variables) and partition it on
**three independent axes** before any generation:

1. **Constraint-family hold-out (the important one).** Partition your families into:
   - **TRAIN-SFT** ~60% of families
   - **TRAIN-RL** ~25% of families — *overlapping task prompts allowed, but a different family set*
   - **HELD-OUT-EVAL** ~15% of families, **never trained on in any stage**, your private Greek-IFBench.
   Rationale: this is the only way to measure generalization rather than memorization, and IFBench §4.2 shows
   OOD performance is "less affected by the number of in-domain constraints" — so a modest held-out slice costs
   you little in-domain and buys you the only honest metric you will have.
2. **Variable-range hold-out.** Train on a **wider** range that *includes and extends* the eval range
   (IFBench §4.3: wider ≥ same > disjoint). Do **not** use disjoint ranges — that was the losing arm.
3. **Prompt hold-out.** Task prompts used in the eval set must never appear in training, following IFBench's
   "unseen, i.e. held out from release" discipline.

**Stage assignment.**
- **SFT** gets verified-correct responses on TRAIN-SFT families, 1–5 constraints, single- and multi-turn mixed.
- **Preference/RL** gets *prompts only* on TRAIN-RL families plus a re-use of TRAIN-SFT prompts with **new,
  harder variable instantiations**. Reusing SFT prompts at RL time is what Tulu 3 and OLMo 3 both do and is
  cheap; the thing you must not reuse is the *held-out families*.
- Keep the **rejects** you already generate as DPO rejected — but heed IFBench Table 4: most models fail the
  same hard items, so naive pairs skew easy (54% of all-correct instances have only 1 constraint). Deliberately
  oversample pairs at 3–5 constraints.

**Per-family budget.** Given the 10/50/100/500/1000 result, target **~50–300 examples per constraint family per
stage**, and spend the surplus on *new families* and *new compositions*, not depth.

## 4.3 Language dependence — which constraints break in Greek

This is the axis that decides what can be ported programmatically and what must be re-authored. Flag every
constraint in the reservoir with one of: **LANG-FREE** (port as-is), **LANG-PARAM** (port with a Greek
parameter table), **LANG-REWRITE** (verifier must be rewritten), **DROP**.

**LANG-FREE** — structure and counting over whitespace/punctuation tokens: paragraph counts, sentence counts
(*with the caveat below*), word counts, bullet/heading/nesting formats, JSON/YAML/CSV/XML schemas, table shape,
placeholder counts, template filling, no-whitespace, repeat/copy tasks, trigram overlap, tool-call shape.

**LANG-PARAM** — same verifier, Greek parameter table needed: postscript marker (**P.S. → Υ.Γ.**), constrained
response option sets (*"My answer is yes." → "Η απάντησή μου είναι ναι."*), title/quotation conventions
(Greek uses « » guillemets alongside " "), date formats, `language:response_language` (target `el`).

**LANG-REWRITE — the traps.** These are the ones that will silently produce wrong training labels:
- **Final sigma (ς/σ).** Any letter-frequency, letter-counting, palindrome, alphabet-order, "no two consecutive
  words share a first letter", or first/last-letter constraint must decide whether ς and σ are the same letter.
  They are the same *letter* but different *codepoints*. **Pick one rule, normalize with `unicodedata`, and
  state it in the prompt.** (This is the same class of bug as the OCR final-sigma decision already on file.)
- **Accents/diacritics.** ά/α, έ/ε, ή/η, ί/ι/ϊ/ΐ, ό/ο, ύ/υ/ϋ/ΰ, ώ/ω. Letter counting, palindromes and
  "include the word X" all need an explicit NFD-strip-or-not policy. A verifier that compares raw codepoints
  will mark correct answers wrong.
- **Capitalization.** Greek convention **drops accents in all-caps** (ΑΘΗΝΑ, not ΆΘΗΝΑ) and maps ς→Σ. So
  `change_case:english_capital` ported naively will fail every *correct* Greek all-caps response. `.upper()`
  in Python does strip most accents for Greek but **not** reliably for ΐ/ΰ — test it.
  `capital_word_frequency` is also weaker evidence in Greek since Greek does not capitalize months, days,
  nationalities or adjectives-from-proper-nouns the way English does.
- **Sentence segmentation.** The **Greek question mark is `;` (U+003B, or the legacy U+037E)**, and the *ano
  teleia* `·` (U+0387) functions as a semicolon. Any sentence counter, "N-th sentence", sentence-type ratio, or
  declarative/interrogative constraint using an English splitter will mis-segment Greek badly. **Rewrite the
  splitter before porting any `sentence` family.**
- **Keyword inclusion/exclusion in an inflected language.** "Include the word X" is the single most fragile
  family: Greek nouns/adjectives decline and verbs conjugate, so the natural form in a sentence is often not
  the citation form. An exact-substring verifier either rejects good answers or forces ungrammatical text
  (keyword-stuffing in the literal sense). **Options:** (a) instruct "in exactly this form", (b) verify against
  a generated inflection paradigm, (c) stem/lemma-match. Decide once, globally.
- **Syllable counting, prime word lengths, alliteration, consonant clusters, odd/even syllables** — all need
  Greek-specific implementations (Greek syllabification rules including diphthongs αι/ει/οι/ου and digraphs
  μπ/ντ/γκ). Either rewrite or **DROP**.
- **Alphabet-order constraints** — the Greek alphabet has **24** letters in a different order; `sentence_alphabet`
  becomes a 24-sentence task. LANG-PARAM if you re-author the alphabet, LANG-REWRITE for the verifier.
- **`words_french` (every N-th word in French)** — port as "every N-th word in English" or drop.
- **Stop-word ratio** — needs a Greek stop-word list, not a translated English one.

**DROP for Greek** — anything whose English form is a pun on English orthography (e.g. "only one type of vowel"
interacts differently with Greek vowel inventory; interrobang usage).

**Practical consequence:** roughly the **format/structure/counting-by-word** half of any taxonomy is LANG-FREE
and can be ported by rule. The **letter-, case-, sentence-, and lexical-morphology** half is LANG-REWRITE. Tag
this at reservoir-build time in English so the Greek adaptation later is a filter, not an archaeology project.

---

# 5. Concrete recommendation

## 5.1 Reaching ~90M supervised IF tokens without template monotony

**Token accounting method [EST]:** rows × (uncompressed bytes/row) ÷ 4 chars-per-token. Where only parquet
(compressed) size is known I assume a 2.0× expansion; these are estimates, not measurements. Measure with the
Apertus tokenizer before committing.

Anchor point [V→EST]: Tulu personas IF is 70,397,173 bytes uncompressed over 29,980 rows = 2,348 B/row ⇒
**~590 tokens/row** ⇒ 29,980 rows ≈ **17.7M tokens**. So **90M tokens ≈ 150K–200K rows** at typical IF density
— your existing Greek 30k set is already ~17M of the 90M if densities are comparable (Greek will tokenize
worse, so likely more).

**Proposed mixture (targets, English-first):**

| Slice | Source | Rows | ~Tokens [EST] | Licence | Why |
|---|---|---:|---:|---|---|
| Greek verified IF (yours) | in-house | 30,000 | ~18M | own | the Greek anchor; "pinch of multilinguality" says even a small Greek share unlocks transfer |
| Verified multi-constraint EN | `allenai/IF_sft_data_verified` | 31,751 | ~16M | ODC-BY [R] | **only large code-verified IF SFT set**, up to 5 constraints, 5-model teacher diversity |
| Dolci precise IF (subsample) | `allenai/Dolci-Instruct-SFT` `Precise IF` | 40,000 of 136,833 | ~20M | ODC-BY | verifier-filtered QwQ-32B responses; IFEval + IFTrain constraints |
| Multi-turn IF | smoltalk2 `SFT/multi_turn_reasoning_if_think` | 28,217 | ~20M | Apache-2.0 [R] | **your 68%/35% failure**; strip thinking traces |
| Structured outputs | `nvidia/...Structured-Outputs-v2` | 15,000 of 62,696 | ~8M | CC-BY-4.0 | JSON/schema family you likely lack |
| Soft/complex constraints | Conifer 13,606 + VerInstruct 27,498 (subsample) | 20,000 | ~10M | Apache-2.0 | prevents format-only overfit; keeps chat quality |
| Wild/real constraints | UltraIF-sft-175k (subsample) | 15,000 | ~6M | CC-BY-4.0 | naturally-occurring user constraints, not templates |
| System/standing rules | smoltalk2 systemchats (both) | 10,000 | ~4M | Apache-2.0 [R] | standing-instruction persistence |
| Adversarial/impossible | Nemotron InverseIFEval + Adversarial | 2,000 | ~1M | CC-BY-4.0 | refusal-of-contradictory family |
| **Total** | | **~192K** | **~103M** | | trim to 90M after tokenizer measurement |

Deliberately **not** included as a bulk source: `tulu-3-sft-personas-instruction-following` — it is
unverified-response, single-turn, capped at 3 constraints, confined to the IFEval 25, and **already inside**
Dolci, smoltalk2 and Nemotron v3. Include it only if a verifier pass keeps it.

Alternative if you want one big commercial-friendly source: `nvidia/Nemotron-SFT-Instruction-Following-Chat-v3`
IF split (card: 249K rows) is CC-BY-4.0/ODC-By, multi-turn, 2026-fresh — but resolve the 407K-vs-887K row
discrepancy, strip `reasoning_content`, and handle the nulled lmsys/WildChat prompts first.

## 5.2 Dedup rules between overlapping families

Confirmed overlaps [V]:
1. **Tulu personas IF ⊂ smoltalk2** — `SFT/tulu_3_sft_personas_instruction_following_no_think` = **29,970** vs
   the original **29,980**. Near-identical.
2. **Tulu personas IF prompts ⊂ Nemotron v3** — card states it explicitly ("We further include prompts from
   tulu-3-sft-personas-instruction-following and generate responses using GPT-OSS-120B").
3. **Tulu personas IF ⊂ Dolci** — Dolci "regenerate[s] Persona IF prompts as in Tülu 3, but with personas
   sourced from Meyer and Corneil (2025)", i.e. *same recipe, new personas* — prompts differ but the
   distribution is the same. Dolci Instruct SFT separately lists Tulu 3 Persona MATH/GSM/Python/Algebra.
4. **`IF_multi_constraints_upto5` ⊂ Dolci-Instruct-RL** (as `..._filtered_dpo_0625_...`, 37,568) and is the
   prompt source for `IF_sft_data_verified`.
5. **`RLVR-IFeval` ⊂ `RLVR-GSM-MATH-IF-Mixed-Constraints`** [R — inferred from Tulu 3's "roughly 30,000 prompts"
   mixture description; verify by hashing].

**Rules:**
- Dedup on the **task prompt with the constraint sentence(s) stripped**, not the full prompt — the same
  underlying Tülu-3-SFT instruction reappears with different constraints across all these sets, and full-string
  dedup will miss it entirely.
- Then dedup on **(stripped prompt, constraint-family multiset)** to avoid near-clones.
- Apply MinHash/LSH at ~0.8 Jaccard on the stripped prompt for the WildChat-derived slices (Nemotron chat,
  UltraIF, tulu-3-wildchat-if) which all draw from the same WildChat/lmsys pool.
- **Decontaminate against `allenai/IFBench_test` (300) and against your held-out Greek families** at the
  constraint-template level, not just the string level. smoltalk v1 already decontaminated against IFEval [V];
  nobody has decontaminated against IFBench for you.

## 5.3 Quality filters (in order)

1. **Re-run the verifiers on every imported row.** Precedent: AI2 discarded ~60% of GPT-4o "chosen"
   completions this way [V]. Anything failing its own stated constraint is dropped, not repaired.
2. **Keyword-stuffing / padding detector.** Constraint satisfaction correlates with degenerate text. Cheap
   programmatic signals: type-token ratio below a threshold; the constrained keyword appearing at >2× the
   required count; repeated n-grams; sentences that exist only to hit a word count; list items that are
   single words. This is the SFT-side analogue of IFBench's reward-hacking finding.
3. **Response-quality judge on a constraint-stripped view.** Copy the IFBench protocol exactly [V]: show the
   judge the prompt **with the constraint removed** and the response, score 1–10 on helpfulness/relevance/
   accuracy/depth/creativity, drop the bottom tail. This is the only filter that catches "followed the
   constraint, failed the task". The paper's own judge prompt is in its Appendix C.
4. **Composition balance.** Enforce a target distribution over constraints-per-prompt (target roughly
   1:2:3:4:5 = 10:20:30:25:15) rather than accepting whatever the sources give — Tulu personas is capped at 3
   and 34% single-constraint.
5. **Family balance with a cap.** Cap any single constraint family at ~300 SFT examples (the 50→1000 plateau).
6. **Greek language-correction pass** on any Greek-side artefact before it is called done (existing house rule).

## 5.4 What can be produced WITHOUT any LLM calls — the honest answer

**The hard constraint: attaching a new verifiable constraint to an existing prompt invalidates the existing
response.** A response written for "summarize this article" is almost never a valid response to "summarize this
article in exactly 7 sentences, each starting with a different letter". So **any new (prompt+constraint) pair
needs a new response, and that needs generation.** There is no way around this for the SFT slice.

**Needs NO LLM calls (pure programmatic):**
- **The entire RL/preference prompt reservoir.** Prompts + constraints + verifiers, no responses required.
  This is exactly what `IF_multi_constraints_upto5` (95,373) and `RLVR-IFeval` (14,973) are — prompt-only sets
  (`messages` length = 1 [V]). **You can build an arbitrarily large Greek RL prompt pool for free**, including
  all the wider-variable-range and multi-constraint composition tricks. Given that RL is where the IFBench gains
  come from (§1.4 Table 24), **this is the highest-value zero-cost work available.**
- **Constraint verifiers themselves** — 40 of your 44 families are already programmatic; write the remaining
  Greek-aware ones (sentence splitter with `;`/`·`, ς/σ + accent normalizer, Greek stop-words, inflection-aware
  keyword matcher).
- **Variable-range widening** on existing prompts.
- **Compatibility/conflict matrix extension** and multi-constraint composition over existing families.
- **Verification, filtering, dedup, decontamination, balancing** of everything imported.
- **Constraint-family tagging** (LANG-FREE / LANG-PARAM / LANG-REWRITE) of the whole reservoir.
- **Mining constraints that already exist in data you hold** — WildIFEval's approach: real user prompts already
  contain constraints; extracting and *labelling* them is programmatic even if generating responses is not.
- **A limited class of SFT rows where the response is mechanically derivable:** copy/repeat/span-extraction
  families (`copying_simple`, `copying_multiple`, `copy_span_idx`, `repeat_prompt`, `repeat_span`), format
  transformations of existing verified text (square-bracket wrapping, bigram wrapping, hyphen joining,
  newline-per-word, title case, no-whitespace), and structured re-serializations (JSON↔CSV↔YAML of data you
  already have). These are **genuinely free SFT rows** — the "answer" is a deterministic function of the input.
  IFTrain deliberately includes this class ("to teach the model to copy better from the input"). Budget: these
  could plausibly supply **10–20% of the 90M tokens at zero LLM cost** [EST — unvalidated].
- **Re-using existing verified responses under *newly discovered* constraints they already satisfy.** Run your
  full verifier battery over responses you already have; where a response happens to satisfy a constraint it was
  not written for, you can mint a new (prompt+constraint, response) pair for free. Yield is low for tight
  constraints but non-trivial for range constraints ("between 100 and 300 words"). **This is the cheapest
  remaining trick and nobody in the surveyed literature does it.**

**Needs generation (no way around it):** any new constrained response; multi-turn redo/revoke dialogues;
soft-constraint responses; the Greek adaptation of any English response. Cheapest path per UltraIF [V]: an 8B
model can serve as both response generator and evaluator and still match Llama-3.1-8B-Instruct on 5 IF
benchmarks — **you may not need a frontier teacher for the verifiable slice at all**, because the verifier, not
the teacher, is what guarantees correctness. Rejection-sample from your own model against your own verifiers
(AutoIF's execution-feedback loop) and you have an LLM-budget-free-ish path that uses only local compute.

## 5.5 The one strategic caution

Everything in §1.4 (OLMo 3 Table 24) and §1.3(f) says the same thing: **SFT moves IFEval, RL moves IFBench.**
A 90M-token IF SFT allocation will very likely take Greek IFEval prompt-strict from 61–68% up toward the
low 80s, matching OLMo 3 7B Instruct SFT's 81.7. It will **not**, on this evidence, fix Greek IFBench or
multi-turn persistence by itself — Instruct-track SFT→RL moved IFBench only 27.4→32.3 even with 137K verified
precise-IF rows. Plan the verifiable prompt reservoir (§5.4, free) now so the RL stage is unblocked, and hold
out constraint families from day one so you can tell memorization from generalization.

---

## Open items I could not verify

- Licences marked [R] for the `allenai/IF_*` and smoltalk2 repos (inherited assumptions).
- Whether Greek is among MaXIFE's 23 languages, and the "47 instruction types" figure.
- smoltalk2's 8 multilingual languages (Greek presence unknown); teacher for `multi_turn_reasoning_if_think`.
- The Nemotron v3 row-count discrepancy (card 887K vs server 407,362).
- Suri, CRAB, SPaR, IHEval, LIFBench, ComplexBench training sets — no authoritative HF training set found under
  those exact names in this pass.
- Whether `RLVR-IFeval` is a strict subset of `RLVR-GSM-MATH-IF-Mixed-Constraints`.
- Krikri-8B 66.8 / Apertus-Instruct 56 figures were given to me in the brief; I did not re-verify them.
