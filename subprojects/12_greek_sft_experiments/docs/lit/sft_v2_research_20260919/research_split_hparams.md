# Reserved-split design and SFT exposure: source-grounded research

Date: 2026-09-19. Every claim is tagged **VERIFIED** (I read the primary text this session; URL given),
**COMPUTED** (arithmetic I did from verified numbers, shown), **ESTIMATE** (my assumption, stated),
or **NOT VERIFIED** (asked for, not confirmed — do not cite).

Papers were read as full HTML text (`arxiv.org/html/<id>`), not abstracts.

---

## 0. Headline answers

1. **Band for RL prompts.** The convergent, verified recommendation is roughly **solve rate 20%–60/65%**,
   with the hard floor being "not 0" and the hard ceiling "not 1". Qwen2.5-Math keeps **2–5 correct of 8
   (25%–62.5%)**; OLMo 3 Think drops **pass rate > 62.5%** (5/8); Skywork-OR1 drops **0/N and N/N**.
2. **Fraction of maths data in band for an 8B.** **~35%** (Big-Math under Llama-3.1-8B, 64 rollouts,
   20–80% band) and **~46%** (Skywork-OR1 under R1-Distill-Qwen-7B, 16 rollouts, excluding only 0/N and N/N).
   Your observed **20%** is well below both — this is the central finding of Part A.
3. **Disjoint vs reused.** The evidence is **split and the effect is small**. Tülu 3: unused prompts
   *slightly* beat reused, but **the best mix combines both**. OLMo 3 and DeepSeekMath **reuse SFT prompts**
   for the preference/RL stage. So: reserving is defensible and cheap, but it is **not** the lever that
   decides success — difficulty is.
4. **Is one pass at lr 1e-5 under-training maths?** On **token exposure, almost certainly yes**; on
   **update count, no**. Your ~3,450 updates match OLMo 3 7B Instruct's ~3,400, but your batch is **16×
   smaller**, so you see **~15× fewer supervised tokens**. Details in Part B §B6.

---

# PART A — split design

## A1. How published recipes relate SFT prompts to preference/RL prompts

### Tülu 3 (arXiv 2411.15124v5) — VERIFIED
URL: https://arxiv.org/html/2411.15124v5

**The reused-vs-unused ablation (§5.3), quoted verbatim:**

> "**Unused Prompts Lead to Higher Performance vs. Reusing Prompts From SFT Mix.** We then compare including
> new prompts and re-using prompts from the SFT stage on their effect on downstream DPO performance. To do so,
> we sampled 100k prompts from the SFT dataset mix that were used during training (as shown in Table 7) and
> compare it against prompts from the same open datasets (e.g., OpenAssistant, SciRIFF, Aya, Persona, WildChat,
> etc.) we subsampled from but left unused during SFT. Figure 10 shows that the unused dataset has a **slightly
> higher performance** as opposed to reusing prompts. This suggests that the presence of new prompts can help
> improve downstream DPO performance. Though, **as seen in our best mix, combining unused and reused prompts
> seems to lead to the best result.**"

**Important caveat:** the magnitude lives in **Figure 10**, which is a figure, not a table — the numeric
deltas are **not in the text**. I did not recover per-benchmark numbers. Treat "slightly higher" as the
paper's own characterisation. **Do not quote a number for this ablation.**

Note the design: the unused prompts were drawn **from the same open datasets** they subsampled from — i.e.
this is **same-distribution-new-instances**, not a different distribution. That is exactly the reservation
design you are proposing.

A related verified finding in the same section: scaling *unique* prompts helps, but scaling by **duplicating**
prompts does not — the 383k mix with duplicates performed about the same as a 64k mix, with slight
degradation on DROP/GSM8k/AlpacaEval as duplication rose.

**RLVR prompt set (§6.1, Table 22) — VERIFIED:**
- GSM8K training set (8-shot CoT prompt, final-number extraction)
- MATH training set (3-shot CoT prompt, "flex" MATH eval logic)
- IFEval-style: instructions sampled from the Tülu 2 SFT mix **combined with constraints** from the Zhou et al.
  taxonomy, one verification function per constraint template
- Table 22 totals: **IF verifiable 14,973**; **Total 29,946** prompts. Text: "a mixture of roughly 30,000
  prompts with ground truth labels." Algorithm: **PPO**, reward α = 10.

Note the IFEval construction **reuses SFT-mix instructions** and makes them new items by bolting on constraints
— a cheap way to manufacture held-out-but-on-distribution prompts.

### OLMo 3 / Dolci (arXiv 2512.13961v2) — VERIFIED
URL: https://arxiv.org/html/2512.13961v2

- **Dolci Think DPO prompt source:** "Our prompt pool is **derived from the Dolci Instruct SFT dataset**
  supplemented with the DaringAnteater and UltraFeedback subsets from the OLMo 2 7B preference dataset."
  → **reuse**, directly contrary to a strict-disjointness rule.
- Filtering applied to **chosen** responses only; "We leave rejected responses unfiltered with the intuition
  that an incorrect rejected response may elicit a useful contrast." All prompts decontaminated against evals.
- **DPO training: one epoch**, sweeping learning rate and dataset size.
- **Dolci-Think-RL offline difficulty filtering — VERIFIED, quoted:**
  > "we generate **eight rollouts** for each prompt **from the initial checkpoint of the model we train** (e.g.,
  > if starting from the DPO-trained model, we generate from the DPO checkpoint). We then **remove all samples
  > that the model easily solves (that is, those with a pass rate greater than 62.5%)**. We sample with a
  > **temperature of 1.0 and top-p of 1.0, matching how we sample during RL training.**"
- This is a **one-sided** filter (removes too-easy only). For the 32B they instead used **active sampling**,
  "which fills RL batches only on samples with a **non-zero GRPO group gradient**" — i.e. the two-sided filter
  applied online rather than offline.
- **Olmo 3 Instruct RL** (the non-thinking analogue, closest to your model): they "modify the pool of prompts
  from Dolci Think RL by 1) utilizing **less challenging datasets** in the math and code domains, and
  2) **skipping the offline difficulty filtering**, as our instruct model focuses more on general instruction
  following rather than complex reasoning." → **For a non-thinking instruct model they deliberately went easier.**
- Key finding stated: "DPO yields gains where SFT on the same data cannot" and "DPO and SFT both benefit from
  RL, but **DPO remains a better starting point**."

Two sampling details worth copying: rollouts come from **the exact checkpoint RL will start from**, and the
sampling parameters **match RL-time sampling**. Both are free and both matter for the band being meaningful.

### SmolLM3 — VERIFIED
URL: https://huggingface.co/blog/smollm3
- SFT dataset **1.8B tokens** (1B non-reasoning, 0.8B reasoning), 12 non-reasoning + 10 reasoning datasets.
- "We trained for **4 epochs (~8B tokens)** using **BFD (best-fit decreasing) packing** with the **loss masked
  on user turns** and the results from tool calls."
- Mid-training: 35B-token dataset, **4 epochs (~140B tokens)**.
- Alignment: **APO** (Anchored Preference Optimization), off-policy — "Generations from **Qwen3-32B** selected
  as chosen and responses from **Qwen3-0.6B** as rejected", plus the **Tülu 3 preference dataset** for
  non-reasoning mode. → SmolLM3's preference data is **off-policy and largely not its own SFT prompts**.

### DeepSeekMath / GRPO (arXiv 2402.03300) — VERIFIED
URL: https://arxiv.org/html/2402.03300
> "The training data of RL are chain-of-thought-format questions related to GSM8K and MATH **from the SFT data**,
> which consists of **around 144K questions**. We exclude other SFT questions to investigate the impact of RL on
> benchmarks that lack data throughout the RL phase."

GRPO hyperparameters: policy lr **1e-6**, KL coefficient **0.04**, **64 outputs sampled per question**,
max length 1024, training batch size 1024, single policy update per exploration stage.

**This is the strongest single counterexample to a strict-disjointness rule**: the canonical GRPO result
(GSM8K 82.9→88.2, MATH 46.8→51.7) was obtained on **prompts the model had already been SFT'd on**, with
**no difficulty filtering mentioned**.

### Qwen2.5-Math (arXiv 2409.12122) — VERIFIED — the canonical band
URL: https://arxiv.org/html/2409.12122
> "**Query Selection.** The queries for reinforcement learning training are selected **from the reward model's
> training set**. We leverage supervised fine-tuning models with varying sizes to **resample 8 responses** for
> each query... we **only retain queries for which 2 to 5 out of the 8 responses are correct**. Queries with
> fewer than 2 correct answers are excluded as they indicate that the current Math model **lacks the fundamental
> capability to learn from them**. Likewise, queries with more than 5 correct responses are omitted since the
> model already demonstrates competence... In the end, we **retain 66K queries** for training."

→ Band **25% ≤ solve rate ≤ 62.5%**, measured at **k=8**. Final RL set **66K prompts**.
Also verified: the RM is used for **rejection sampling** to build SFT data (iterative; top-k correct paths;
weighted majority voting where no gold answer exists), then GRPO after SFT.

### DAPO (arXiv 2503.14476v2) — VERIFIED
URL: https://arxiv.org/html/2503.14476
- **DAPO-Math-17K**: "After selection and transformation, we obtained the DAPO-Math-17K dataset, which consists
  of **17K prompts, each paired with an integer as the answer**." Answers were **rewritten to be integers**
  (e.g. an answer of form `a + b√c` becomes `a + b + c`) so parsing is robust.
- **Dynamic Sampling** is one of DAPO's four named techniques, "which improves training efficiency and
  stability" — oversample and drop groups whose accuracy is 0 or 1, keeping the batch full of mixed-outcome
  prompts. (The technique and rationale are VERIFIED; I did not print the exact equation.)
- Result: **50 points on AIME 2024** with Qwen2.5-32B, beating DeepSeek-R1-Zero-Qwen-32B (47).

**The 17K figure is the single most useful sizing anchor for you**: a state-of-the-art maths RL result at 32B
used **17,000 prompts**, not hundreds of thousands.

### Skywork-OR1 (arXiv 2505.22312v2) — VERIFIED — the best band-fraction data
URL: https://arxiv.org/html/2505.22312
> "**6.2 Model-Aware Difficulty Estimation.** Due to the zero-advantage in GRPO when all sampled responses are
> either entirely correct or entirely incorrect within a group, we conduct an initial **offline difficulty
> estimation** for each problem **relative to the models being trained**. Specifically, for each problem, we
> perform **N=16 rollouts for math** problems and **N=8 for coding** questions using a **temperature of 1.0**
> and a maximum token length of 32K... we **exclude problems with 0/N (all incorrect) or N/N (all correct)**."

Retention table (VERIFIED):

| Model | 0/N correct (math/code) | N/N correct (math/code) | **Remaining (math/code)** |
|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-**7B** | 21.4% / 28% | 32.4% / 24% | **46.2% / 48%** |
| DeepSeek-R1-Distill-Qwen-**32B** | 20.7% / 17.1% | 42.0% / 45.4% | **37.3% / 37.6%** |

Also VERIFIED: **online** filtering on top of offline — "at the beginning of each stage, we also discard
training prompts for which the actor model achieved correctness of 1 in the previous stage", plus rejection
sampling of zero-advantage groups. And: "Rigorous filtering and quality control of training data significantly
accelerate learning."

Note the direction: the **stronger** 32B model retains **fewer** prompts (37% vs 46%) — because more problems
become trivially solved. Difficulty filtering must be **re-run per checkpoint**, not computed once.

### Big-Math (arXiv 2502.17387v1) — VERIFIED — the cheap proxy you asked about
URL: https://arxiv.org/html/2502.17387v1  *(note: only v1 renders as HTML; v2/v3 return 404)*

- **>250,000** problems with verifiable answers; plus **47,000** reformulated (**Big-Math-Reformulated**:
  multiple-choice converted to open-ended).
- Three desiderata: uniquely verifiable solutions; open-ended (not guessable); closed-form answers.
- **Solve-rate metadata — VERIFIED:** "For each problem in the dataset we generate **64 rollouts**" from
  **Llama-3.1-8B**, "and calculate the success rate per problem." (Separately, for a *correctness* heuristic
  during filtering they used 64 solutions from Llama-3.1-8B, ~30M rollouts, and 5–8 from Llama-3.1-405B.)
- **Difficulty bands — VERIFIED, quoted:** "we group problems into difficulty quintiles, with the hardest
  quintile being problems that have a **success rate less than 20%** and the easiest quintile with a
  **success rate over 80%**. We find that, from easiest to hardest, the quintiles have **71,926 (28.64%),
  30,533 (12.16%), 25,763 (10.26%), 31,249 (12.44%), and 91,647 problems (36.50%)**."
- **COMPUTED:** total = 71,926+30,533+25,763+31,249+91,647 = **251,118**.
- **COMPUTED — the answer to "what fraction is in band for an 8B":** the middle three bands (solve rate
  20%–80%) = 12.16 + 10.26 + 12.44 = **34.86%**, i.e. **87,545 problems**.
- **36.50% are below 20% solve rate** under Llama-3.1-8B, and "nearly all of Omni-MATH and HARP are
  unsolveable by Llama-3.1-8B."
- Their explicit warning, quoted: "**RLVR would be unlikely to work effectively on Omni-Math and HARP as the
  model's responses would produce no training signal.**"
- Guidance, quoted: "those training less capable, or smaller, models may want to **remove the most difficult
  problems**... for those training a larger, or math-specific, model will find many of the easy questions
  redundant." Retaining the hardest two quintiles still leaves **>120,000 problems**.

**This is your cheap proxy.** Big-Math ships per-problem Llama-3.1-8B solve rates, so you can pre-stratify a
reserve *before* spending any sampling compute on your own model.

### AceReason-Nemotron 1.1 (arXiv 2506.13284) — VERIFIED (see also §B5)
URL: https://arxiv.org/html/2506.13284
- RL: GRPO, strictly on-policy, **G = 8 or 16 rollouts** per question, **global batch of 128 prompts**, single
  policy gradient update, token-level policy gradient loss; stage-wise math-only then code-only.
- **"Stronger SFT models continue to produce consistently better results after large-scale RL, although the
  performance gap narrows during RL training."** (§4.5.1) — directly relevant to your "is SFT strong enough" question.
- §4.5.7 heading: "**RL improves upon the SFT model in terms of pass@K even when K is large**" — this is a
  **direct contradiction of Yue et al.** See §A3 for how I reconcile them.
- §4.5.8: "RL improves over strong SFT model by **solving hard problems**."

### NOT VERIFIED in this pass
I did **not** confirm, and you should not cite from this report: **AceMath**, **Polaris**, **PRIME**,
**Kimi 1.5 curriculum**, **Llama 3 rejection-sampling round counts**, and the dedicated "online difficulty
filtering" papers. The online-filtering *concept* is nonetheless well covered by three verified sources
(DAPO dynamic sampling, Skywork online filtering, OLMo 3 active sampling).

---

## A2. Disjoint, overlapping, or same-distribution-new-instances?

**Verdict: same-distribution-new-instances, with overlap explicitly allowed. Do not enforce strict disjointness.**

Evidence **for** reserving:
- Tülu 3: unused > reused, "slightly" (§A1; magnitude unrecovered, figure-only).
- Mechanism: a prompt seen in SFT has an **inflated solve rate** because the model memorised its target. It
  therefore lands in the "too easy" bucket and gets filtered out anyway — you pay sampling cost to discover
  that. Reserving avoids that waste. This mechanism is **consistent with** Skywork's finding that stronger
  models retain fewer prompts, but I did not find a paper that isolates "SFT-seen → inflated solve rate"
  as a measured effect. Mark it **reasoned, not verified**.

Evidence **against** strict disjointness:
- **DeepSeekMath**: 144K RL prompts taken **from the SFT data**; headline GRPO gains. VERIFIED.
- **OLMo 3**: Dolci Think DPO prompt pool **derived from the Dolci Instruct SFT dataset**. VERIFIED.
- **Tülu 3's own best mix combines unused and reused.** VERIFIED.
- **Qwen2.5-Math**: RL queries come from the **reward model's training set** — a different pool, but the
  selection criterion is the pass-rate band, not novelty. VERIFIED.

**Practical reading.** Novelty is a second-order effect; **difficulty is first-order**. The reason to reserve
is not that reuse is harmful — it is that:
1. a reserve gives you a **clean, uncontaminated** difficulty measurement and an honest eval;
2. it is **free** to do at corpus-construction time and **expensive** to retrofit;
3. held-out-same-distribution prompts stay **on-distribution and learnable**, which is what you want — a
   genuinely out-of-distribution reserve would make the barren-prompt problem *worse*.

So: reserve, but allow the RL mix to include some SFT-seen prompts if the band filter admits them.

---

## A3. Choosing prompts that yield mixed outcomes (given your bimodal finding)

### Your data, placed against the literature
You observed: 115 maths prompts × up to 32 samples → **23 prompts (20%) ever produced an acceptable reply**;
**80% were barren at pass@32**; more samples did not rescue them.

Benchmarks for how bad that is:
- Big-Math / Llama-3.1-8B @ 64 rollouts: **36.50%** below 20% solve rate (that band *includes* the 0% ones,
  so the true all-zero fraction is **lower** than 36.5%). **VERIFIED.**
- Skywork / R1-Distill-Qwen-7B @ 16 rollouts: **21.4%** of maths problems are 0/N. **VERIFIED.**

**Your 80% barren rate is roughly 2–4× worse than published 7–8B numbers.** That is the diagnostic. It means
one or more of: (a) the SFT model is materially weaker at maths than Llama-3.1-8B (consistent with MATH-500
13%); (b) the prompt pool is far too hard for it; (c) the Greek adaptation costs accuracy; (d) the acceptance
criterion is stricter than "final answer matches". **All four are worth separating before spending RL compute** —
(d) in particular is cheap to check and easy to get wrong.

### The four mechanisms recipes actually use
1. **Offline difficulty estimation before RL, from the exact starting checkpoint.** Qwen2.5-Math (8 rollouts,
   keep 2–5), Skywork (16 math / 8 code, drop 0/N and N/N), OLMo 3 (8 rollouts, drop >62.5%). All VERIFIED.
   Note k is **small** — 8 or 16, not 32. Sampling budget goes into *breadth of prompts*, not depth per prompt.
2. **Online / dynamic filtering during training.** DAPO Dynamic Sampling; Skywork per-stage discard of
   now-solved prompts; OLMo 3 active sampling on non-zero GRPO group gradient. All VERIFIED. This is what
   handles the fact that the band **moves as the policy improves**.
3. **Cheap published proxy.** Big-Math's per-problem **Llama-3.1-8B solve rates over 64 rollouts** let you
   stratify before spending your own compute. VERIFIED.
4. **Curriculum / staging.** Skywork multi-stage (8K → 32K context); AceReason stage-wise math-then-code.
   VERIFIED. (Kimi 1.5's curriculum: **NOT VERIFIED**.)

### Your bimodality is the expected shape, not an anomaly
Big-Math Figure 3's distribution is explicitly **U-shaped**: the two extreme bands hold 28.64% + 36.50% =
**65.14%** of all problems, the three middle bands only 34.86% (**COMPUTED** from verified counts). A bimodal
yield is what the literature predicts. The error was sampling 32 deep on an unfiltered pool rather than
sampling 8 wide on a pre-stratified one.

**COMPUTED, same budget reallocated:** 115 prompts × 32 samples = 3,680 rollouts. At k=8 that is
**460 prompts** screened. At the Skywork 7B retention rate (46.2%) that would yield **~212 in-band prompts**
instead of 23 — a **~9× improvement in usable prompts for identical sampling cost**.

### SFT strength as a precondition — and the honest disagreement
- **Yue et al. 2025, "Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the
  Base Model?" (arXiv 2504.13837v5)** — VERIFIED, URL https://arxiv.org/html/2504.13837:
  > "while RLVR-trained models outperform their base models at smaller values of k (e.g., k=1), **base models
  > achieve higher pass@k score when k is large**. Moreover, we observe that the **reasoning capability boundary
  > of LLMs often narrows as RLVR training progresses**. Further coverage and perplexity analysis shows that the
  > reasoning paths generated by RLVR models are **already included in the base models' sampling distribution**,
  > suggesting that their reasoning abilities **originate from and are bounded by the base model**."
  They also find six popular RLVR algorithms perform similarly and remain far from optimal, and that
  **distillation *can* introduce genuinely new reasoning patterns** where RLVR does not.
- **AceReason-Nemotron 1.1 (2506.13284) §4.5.7 explicitly claims the opposite**: "RL improves upon the SFT
  model in terms of pass@K even when K is large." VERIFIED as a claim.

**How to use the disagreement rather than pick a side.** Both camps agree on the operational point that matters
to you: **RLVR redistributes probability mass toward paths the starting policy can already reach.** Whether the
ceiling is strictly the base model's (Yue) or can be nudged (AceReason), a prompt with **pass@k = 0 at your RL
sampling budget contributes exactly zero gradient signal under GRPO/RLVR** — that is not a contested claim, it
is the definition of a zero-advantage group, and it is the stated motivation for filtering in Skywork, Qwen2.5-Math
and DAPO alike.

**Therefore the gate on your SFT stage:** on the reserved maths prompts, sampled from the checkpoint RL will
start from, with RL-time sampling parameters, you need the **fraction of prompts with 1 ≤ correct ≤ 7 out of 8**
to be **substantial** — the published comparables are **~46%** (Skywork 7B) and **~35%** (Big-Math band, 8B).
A defensible internal bar is **≥30%**, with **≥25%** as the minimum at which RL is worth the compute.
**At your current 20%-at-k=32, maths preference/RL is not yet worth running** — strengthen SFT or soften the
prompt pool first. (The ≥30%/≥25% thresholds are **my recommendation calibrated to the verified comparables**,
not a published bar.)

---

## A4. Recommended reservation protocol

### (a) Split by ROOT problem — non-negotiable
The split unit is the **root problem**, not the rendered item. One root groups: augmented/paraphrased variants,
translations (English *and* the later Greek adaptation), multi-solution groups (all k solutions to one problem),
tool-integrated vs CoT renderings, and reformulated variants.

Grounding: Big-Math's **Big-Math-Reformulated** derives 47,000 open-ended items *from existing* multiple-choice
problems (VERIFIED); OpenMathInstruct-2 is **607.3K questions → 13.97M question–solution pairs** (VERIFIED,
Table 5) — a ~23:1 solution-to-question ratio. Splitting on the pair rather than the question would put
near-identical items on both sides. Implementation: a `root_id` assigned at ingestion, plus a normalised-text
hash (strip whitespace/LaTeX-spacing/numbering) as a backstop, and near-duplicate detection across the boundary.

Your existing memory rule *"repaired label ≠ contamination"* applies in spirit: what makes a leak is **the same
root problem**, not incidental string equality between two independently-authored short answers.

### (b) Stratify by source × topic × difficulty × answer type
Stratify so the reserve mirrors the SFT distribution — you want it **on-distribution**. Axes:
- **source** (dataset of origin)
- **topic** (Big-Math used **gpt-4o-mini** to classify into maths domains per Gao et al.; VERIFIED. Their
  finding: differential equations, discrete maths and abstract algebra are hardest; prealgebra easiest by a
  wide margin; most domains have wide internal spread.)
- **difficulty** — use the **Big-Math Llama-3.1-8B 64-rollout solve rate** where available, as a free prior;
  re-measure against your own checkpoint later
- **answer type** (integer / rational / symbolic / interval / tuple / proof-free closed form) — this drives
  verifier coverage, and mismatches here silently become false negatives

### (c) Size of the reserve — verified consumption at 8B-ish scale

| Recipe | Stage | Prompts | Status |
|---|---|---|---|
| Tülu 3 8B | RLVR (PPO) | **29,946** total (14,973 IF-verifiable) | VERIFIED |
| DAPO (32B) | GRPO | **17,000** (DAPO-Math-17K) | VERIFIED |
| Qwen2.5-Math | GRPO | **66,000** (post-band-filter) | VERIFIED |
| DeepSeekMath 7B | GRPO | **~144,000** (from SFT data, unfiltered) | VERIFIED |
| Big-Math | available pool | 251,118; hardest two bands >120,000 | VERIFIED/COMPUTED |

**Recommendation.** Reserve **post-filter** targets, then inflate for expected attrition.

Target **~20,000–30,000 in-band maths prompts** at RL time (between DAPO's 17K and Tülu 3's 30K).
**COMPUTED inflation:** at a 35% in-band retention rate you must reserve **~60,000–85,000** maths roots;
at your currently-observed 20%, **~100,000–150,000**. Reserve at the **pessimistic** end — unused reserve is
nearly free, an undersized one is not recoverable without re-splitting.

Per capability, as a starting allocation:
- **Maths:** 60k–85k roots (largest; highest attrition)
- **Code:** 25k–40k roots (Skywork retained 48% at 7B — attrition is milder than maths)
- **IF:** 15k–25k roots — cheapest to manufacture. Tülu 3's recipe (instructions × constraint taxonomy with
  one verifier per template, 14,973 items) is directly reusable and **combinatorially expandable**.
- **Other (general chat, safety, QA):** 10k–20k, mainly to keep the RL mix from over-optimising. OLMo 3's
  verified finding: "**Mixing RL data from varied domains can prevent over-optimization**" and "Mixing data
  yields lower train reward, but **not** lower downstream performance."

### (d) Verifiability requirements
- **Maths:** a single closed-form, uniquely verifiable final answer (Big-Math's three desiderata, VERIFIED).
  Prefer **integer answers** — DAPO explicitly **rewrote** answers into integer form so parsing is robust
  (VERIFIED). Exclude multiple-choice (guessable) or reformulate it as Big-Math did. Exclude proofs.
  Budget for a symbolic-equivalence checker, not string match.
- **Code:** unit tests, executed in a sandbox. Skywork's §7 separates "Math Verifiers" from "Code Sandboxes";
  they ran **N=8** rollouts for code difficulty estimation. VERIFIED.
- **IF:** programmatic checkers, one per constraint template (Tülu 3). VERIFIED. **Caution:** Tülu 3 has an
  appendix "B.4 **RLVR IFEval overoptimization**" and their unseen-eval analysis states "**Models generally
  overfit to IFEval**" (VERIFIED). Hold out constraint *templates*, not just instances — otherwise you measure
  template memorisation. Tülu 3 built **IFEval-OOD** for exactly this reason.

### (e) Never-train TEST split vs RL-train split — three-way, not two-way

| Split | Purpose | Rule |
|---|---|---|
| **SFT-train** | supervised fine-tuning | may be sampled from freely |
| **RL-pool** (reserved) | difficulty screening → DPO/GRPO prompts | never in SFT; rollouts allowed; consumed by RL |
| **TEST** (never-train) | honest eval, incl. pass@k tracking | **never** trained on at any stage; **no** rollout-derived data enters training |

Size TEST at **~1,000–2,000 roots per capability**, stratified identically to the reserve. It must be frozen
before any sampling, decontaminated against public evals (Tülu 3 found e.g. NuminaMath-TIR 18.2% and
DaringAnteater 30.7% overlap with MATH — VERIFIED, Table 37), and used to report **pass@1 and pass@8 side by
side** so you can detect the Yue et al. failure mode (pass@1 up, pass@k down) if it occurs.

Given your standing rule *"don't shade acceptance green"*: the in-band fraction and pass@8 on TEST should be
reported as raw numbers with the failing value named, and the party measuring the gate should not be the party
that built the SFT mix.

### (f) What makes an item cheap to adapt to Greek later
Score every reserved item on these at reservation time and keep the score as metadata:
- **Short problem text** — translation cost and translation-error risk both scale with length.
- **Language-independent answer** — integers/symbols survive translation unchanged; the verifier needs **no**
  Greek adaptation. This is the single highest-value property.
- **No English-specific wordplay**, puns, letter-counting, alphabetical ordering, idioms, or culture-bound
  units/names. These are unsalvageable and should be excluded from the reserve outright, not translated.
- **Code with tests independent of prompt language** — function signatures, I/O and assertions in code;
  the natural-language statement translated, the tests untouched.
- **IF constraints that survive translation** — "reply in exactly 3 bullet points", "no commas", "end with X"
  port cleanly; "use exactly 5 words starting with S" does not. Tag each constraint template
  `language_portable: true/false`.
- **No English-orthography dependence** in the answer (spelling, capitalisation).
- **Numerals/units normalised** — Greek decimal comma vs point will silently break exact-match verifiers.
  Decide the convention **now** and encode it in the checker.

Your memory rule on **Greek language-polish before "done"** applies to the adapted reserve as well, and your
**fidelity rule** (verify before use) argues for a small human-checked Greek pilot of ~200 items before
adapting the full reserve.

---

# PART B — hyperparameter / exposure assumptions

## B1. Tülu 3 SFT — VERIFIED (Table 11 + §4.3)
URL: https://arxiv.org/html/2411.15124v5

| Setting | 8B | 70B |
|---|---|---|
| Learning rate | **5 × 10⁻⁶** | 2 × 10⁻⁶ |
| Schedule | **Linear** | Linear |
| Batch size (effective) | **128** | 128 |
| Max token length | **4,096** | 4,096 |
| Warm-up ratio | **0.03** | 0.03 |
| Epochs | **2** | 2 |

Prompt pool: **Table 7 total 939,344** (selected from 23,327,961 candidates); 425,145 used elsewhere in the
pipeline. Compute: 8B on 32 GPUs for 6 hours; 70B on 64 GPUs for 50 hours. lr found "after a hyperparameter search".

Your plan's warmup 0.03 and max-len 4,096 match Tülu 3 exactly. Your **lr 1e-5 is 2× theirs**, your
**batch is ~4× smaller in sequences** (16 vs 128), and you use **cosine-to-10%** where they use **linear**.

## B2. Tülu 3's loss-aggregation finding (§4.3.2 "Batch Aggregation") — VERIFIED, and important
Quoted:
> "We found this issue was largely due to a (recently widely-reported) issue with loss aggregation inside
> Transformers: **Averaging the loss across padding tokens without taking into account gradient accumulation or
> distributed training setups.**"

With two samples of n₁, n₂ non-padding tokens, a single forward pass gives `L = (l_{n1} + l_{n2})/(n1 + n2)`
(**every token weighted equally**), whereas gradient accumulation gives `L = (l_{n1}/n1 + l_{n2}/n2)/2`
(**every example weighted equally**). Quoted: "changing gradient accumulation can have large effects on
performance due to effectively changing sample weightings... A similar issue occurs in distributed training
due to cross-device averaging."

> "To fix this issue, we opted generally to use a **sum loss** instead of averaging ('mean loss') when training.
> This removes the issue by simply removing the denominator... and **requires an adjustment to learning rates**.
> This effectively weights all tokens equally... Ultimately, we found that **using a sum loss with a learning
> rate of 5.00E-06 worked best**. Surprisingly, we additionally found that **training for longer did not yield
> further improvements, and so used 2 epochs**."

Validated by finetuning Llama 3.0 on the Tülu 2 mix across learning rates, epochs and loss types (Figures 5, 6).
They cite Muennighoff et al. (2024), the unsloth blog, and muellerzr's write-up.

**The HF blog you cited** (https://huggingface.co/blog/gradient_accumulation) — I did **not** fetch it this
session. **NOT VERIFIED as a URL**, but the *phenomenon* it describes is verified in full from Tülu 3 §4.3.2
above, and Tülu 3 footnote 10 cites the two equivalent write-ups (unsloth.ai/blog/gradient and
muellerzr.github.io/blog/gradient_accumulation_part2.html).

**Action for you.** Because you train **packed 4,096-token sequences with assistant-only loss** under **ZeRO-3**,
you sit squarely in this trap: packing means wildly varying supervised-token counts per sequence, and ZeRO-3
means cross-device averaging. **Confirm empirically whether your trainer normalises by supervised tokens per
micro-batch or per global batch.** If per-micro-batch, your effective per-token weighting depends on your
gradient-accumulation factor, and your lr is not comparable to anyone's. This is a correctness check to run
**before** the 600M/1.5B scale-ups, and it is a plausible partial explanation for weak maths: maths targets are
long, and example-weighted normalisation systematically **down-weights long targets** relative to short ones.

## B3. Apertus SFT (arXiv 2509.14233, §4.2) — VERIFIED, quoted in full
URL: https://arxiv.org/html/2509.14233
> "**4.2 Supervised Finetuning.** We begin post-training with a supervised finetuning phase using the above
> mixture (Section 4.1.3). We use a **global batch size of 512 and 1,024**, and learning rates of **5 × 10⁻⁶**
> and **2 × 10⁻⁶**, respectively, with a **linear decay schedule**. All models are trained with a **maximum
> sequence length of 4,096 tokens**, and the **AdEMAMix optimizer** (Pagliardini et al., 2025) with **β₃ = 0.99,
> α = 8.0**, and both t_β₃ and t_α set to the total number of training steps. Default values are used for
> **β₁ = 0.9 and β₂ = 0.999**."

(512/5e-6 is the 8B; 1,024/2e-6 the 70B.) The section states **no epoch count** and **no token total** — those
are genuinely absent from the report.

**Divergences between your plan and Apertus's own SFT, all material:**

| | Apertus 8B SFT | Your plan |
|---|---|---|
| Optimizer | **AdEMAMix** (β₃=0.99, α=8.0) | AdamW |
| β₂ | **0.999** | **0.99** |
| Learning rate | **5e-6** | **1e-5** (2×) |
| Schedule | **Linear decay** | Cosine to 10% |
| Global batch | **512** sequences | **16** sequences (**32× smaller**) |
| Max seq len | 4,096 | 4,096 ✓ |

The batch-size gap is the striking one. Note also the direction of your lr change: you run a **32× smaller
batch** than Apertus at a **2× larger learning rate**. Conventional scaling (linear or sqrt) points the
opposite way. That combination is not obviously wrong — §B7's paper shows small batches tolerate a wide lr
range — but it is **undisclosed drift from the base model's own recipe** and, per your *"disclose recipe
changes"* rule, belongs in a parameter table before the next launch.

## B4. OpenMathInstruct-2 (arXiv 2410.01560v2) — VERIFIED
URL: https://arxiv.org/html/2410.01560

**Final models:** "All the models are trained with a **batch size of 512**, using the **AdamW** optimizer with a
**constant learning rate of 2e-5** and a **weight decay of 1e-2**." 8B trained on **1M, 2M and 5M** fair-downsampled
subsets; 70B only on the 5M subset at **lr 1e-5**. "The models are trained for **2 epochs**, and we save
**6 equally spaced checkpoints** during the training runs, which are **averaged** to create the final model."

**Ablations** used a different setting: "the model is trained for **4 epochs**, with a **batch size of 256**,
using AdamW with a **constant learning rate of 5e-6** and a weight decay of 1e-2", averaged over **4 runs**.

**Checkpoint averaging (Appendix A.4):** "We have found **consistent gains** in our setup with checkpoint
averaging. Figure 9 shows a gain of **more than 2%** for one of our ablation runs when the final checkpoint is
created using the average of the **last 4 checkpoints**."

**Dataset (Table 5):** **607.3K questions → 13.97M question–solution pairs**; ~592K synthetically-generated
questions contributing ~11M new pairs. (Confirms your "14M examples".)

Two directly portable wins: **constant LR** (not cosine) and **checkpoint averaging** (>2%, essentially free).

## B5. AceReason-Nemotron 1.1 (arXiv 2506.13284) — VERIFIED, quoted
URL: https://arxiv.org/html/2506.13284
> "We observe **consistent performance gains from the first to the fifth epoch**, with improvements
> **plateauing between the fifth and sixth epochs**, regardless of the specific SFT blend used. This suggests
> that **a certain degree of 'overfitting' actually enhances test accuracy with long CoT generation**, likely
> due to **exposure bias in autoregressive models**."

Also: scaling both unique prompts and responses-per-prompt helps, but "**scaling the number of prompts yields
more significant gains**."

**Caveat you must apply.** This 5-epoch finding is explicitly conditioned on **long-CoT generation** and
justified by exposure bias over long sequences. **Your model is non-thinking.** Do **not** transfer "5 epochs"
directly. The nearer analogues for a non-thinking chat model are Tülu 3 (**2**), OLMo 3 Instruct (**2**),
OpenMathInstruct-2 (**2**), SmolLM3 (**4**), and the Baseten study (**ceiling ≈ 2**, §B8). The defensible
range for you is **2–3 epochs**, with **prompt count preferred over extra passes**.

## B6. OLMo 3 SFT, SmolLM3, and the central exposure comparison

**OLMo 3 SFT (Table 47 + A.6.1) — VERIFIED:**
> "our batch size is now measured in **tokens** instead of instances, and we train with **document packing**
> instead of padding. We train all of our **7B SFT models with a batch size of 1M tokens** and 32B SFT models
> with a batch size of 4M tokens, **for two epochs**, with packing, and a **32,768 sequence length**."

| | 7B Thinking SFT | 32B Thinking SFT | **7B Instruct SFT** |
|---|---|---|---|
| Total tokens | 45.4B | 45.2B | **3.4B** |
| Learning rate | 5.0e-5 | 1.0e-4 souped with 5.0e-5 | **8.0e-5** |
| Num. GPUs | 64 | 256 | 8–64 |
| Max seq length | 32K | 32K | 32K |

Also VERIFIED: "We train all models for **two epochs to avoid overfitting**", a learning-rate sweep for
checkpoint selection, qualitative "vibe-test" questions, and a final **linear merge (model soup) of two
checkpoints trained with different learning rates** via mergekit.

**SmolLM3 (3B) — VERIFIED:** SFT dataset **1.8B tokens**, **4 epochs ≈ 8B tokens**, BFD packing, loss masked
on user turns.

### The comparison that answers your key question

**Olmo 3 7B Instruct is the closest published analogue to your run** — non-thinking, ~8B, packed, 2 epochs.

| Run | Tokens/update | Total supervised tokens | Epochs | Updates | LR |
|---|---|---|---|---|---|
| **Yours** | **65,536** | **147M supervised** (226M total) | **1** | **~3,450** | 1e-5 cosine→10% |
| OLMo 3 7B Instruct | **1,048,576** | **3.4B** | 2 | **~3,400** | 8e-5 |
| OLMo 3 7B Think | 1,048,576 | 45.4B | 2 | ~45,400 | 5e-5 |
| SmolLM3 3B | n/s | ~8B | 4 | n/s | n/s |
| Tülu 3 8B | ≤524,288 slots (128×4,096) | 939,344 prompts | 2 | **~14,700** | 5e-6 (sum loss) |
| OpenMathInstruct-2 8B | 512 examples | 5M examples | 2 | **~19,500** | 2e-5 constant |

**COMPUTED:** 226M / 65,536 = **3,448 updates** (matches your ~3,500). OLMo 3 7B Instruct: 3.4B / 1M =
**3,400 updates**. Tülu 3: 939,344 × 2 / 128 = **14,677**. OpenMathInstruct-2 8B on the 5M subset:
5M × 2 / 512 = **19,531**.

**The finding: your update count is normal; your token exposure is the outlier.** You match OLMo 3 Instruct's
step count almost exactly, but at **1/16th the batch**, so you see **3.4B / 226M ≈ 15× fewer tokens**. Against
Tülu 3 and OpenMathInstruct-2 you are short on **both** axes (~4× and ~6× fewer updates respectively).

### Maths specifically
Yours: **~17M maths supervised tokens × 1 pass**.

**ESTIMATE (assumption stated):** OpenMathInstruct-2's 8B run used **5M examples × 2 epochs = 10M example-passes**.
At an assumed **~350 tokens per solution** (typical for OMI-2 CoT solutions; **I did not verify a token count —
the paper reports examples, not tokens**), that is **~3.5B maths tokens**, i.e. **~200× your 17M**. Even at a
conservative 150 tokens/solution it is **~1.5B**, ~90×. The order of magnitude is robust to the assumption;
the exact multiplier is not. **Flag this as an estimate in any writeup.**

**Answer to your question: yes — one pass over ~17M maths tokens is very likely under-training maths**, and
MATH-500 at 13% is consistent with that. But note the diagnosis is **token volume**, not learning rate: at
1e-5 you already run a *higher* lr than Tülu 3 (5e-6), Apertus (5e-6) and OpenMathInstruct-2's ablation setting
(5e-6). **Raising lr further is the wrong lever; raising maths tokens and batch size is the right one.**

Your scaling plan is well-aimed: **COMPUTED**, at 1.5B supervised tokens with 30% maths you reach **450M maths
tokens**, ~26× your current exposure and within an order of magnitude of the OMI-2 8B run. At the 150M rung you
would have only **45M** — barely 2.6× current, so **do not expect the 150M rung to fix maths**; treat it as a
pipeline rehearsal, not a capability test.

**Two concrete recommendations from this section:**
1. **Raise tokens-per-update.** 65,536 tokens/update is small for an 8B full-parameter run — 8× below Tülu 3,
   16× below OLMo 3. Moving toward **256k–1M tokens/update** brings you into the published band and reduces
   gradient noise on long maths targets.
2. **Add checkpoint averaging.** Verified >2% on MATH validation in OpenMathInstruct-2, and OLMo 3 souped two
   different-lr checkpoints. Save 6 equally spaced checkpoints and average the last 4. Essentially free.

## B7. Is the small-batch / β₂ claim correctly attributed to arXiv 2507.07101? — **YES, VERIFIED**
URL: https://arxiv.org/html/2507.07101
Title: **"Small Batch Size Training for Language Models: When Vanilla SGD Works, and Why Gradient Accumulation
Is Wasteful."**

Abstract, quoted: "rather than holding the decay rate of the second moment fixed across batch sizes, we propose
to **hold its half-life fixed in terms of tokens**. We find that small batch sizes (1) train stably, (2) are
consistently **more robust to hyperparameter choices**, (3) achieve **equal or better per-FLOP performance than
larger batch sizes**, and (4) notably enable stable language model training with vanilla SGD... We further
**recommend against gradient accumulation** unless training on multiple devices with multiple model replicas."

→ **"Properly tuned small batches are competitive" is correctly attributed.** VERIFIED.

**The β₂ formula.** The paper defines half-life implicitly via **β^(t₁/₂ / (B·T)) = 1/2**, where B·T is tokens
per batch. Holding t₁/₂ fixed while changing batch size gives −ln β₂ ∝ B, hence:

> **β₂_new = β₂_old^(B_new / B_old)**   — **COMPUTED**; algebraically equivalent to the paper's rule.

The paper does **not print this closed form**; it states the half-life rule and gives a worked value.
**I verified the equivalence numerically against their own number:** at batch 512 with the nanoGPT default
β₂ = 0.95, the formula gives 0.95^(1/512) = **0.9998998**, and the paper states that for batch size 1 they
"rescale β₂ to preserve the token half-life, **resulting in β₂ = 0.9999**." **Exact match.**

→ **Your stated formula is correct**, but cite it as "equivalent to the token-half-life rule of arXiv 2507.07101",
not as a formula printed in the paper.

Two further verified findings worth heeding: the optimal learning rate **does not follow square-root scaling**
("a square root rule would indicate... scaled by a factor of 32, whereas we find that a factor of only about 3
empirically works better"), and **β₁ = 0.9 performs well across batch sizes**.

**Caveat on transfer:** this paper's experiments are **pretraining** (30M-parameter model, 600M tokens of
FineWeb-Edu, batch sizes 1–4096). Transfer to 8B full-parameter SFT is **plausible but not demonstrated**.
Its "recommend against gradient accumulation" carries an explicit exception — "unless training on multiple
devices with multiple model replicas" — which is exactly your 4× GH200 ZeRO-3 setup, so that recommendation
does **not** straightforwardly apply to you.

**Applied to your run:** your β₂ = 0.99 at 65,536 tokens/update. If you raise the batch to 262,144
(4×), the half-life rule gives **COMPUTED** β₂_new = 0.99⁴ = **0.9606**; at 1M tokens/update (16×),
0.99¹⁶ = **0.8515**. Both are far from the AdamW default 0.999 and from Apertus's 0.999. Worth a deliberate
decision rather than an inherited constant — and worth noting that the rule says larger batches want
*smaller* β₂, which is the opposite of common practice.

## B8. Does arXiv 2609.01244 exist? — **YES, VERIFIED**
URL: https://arxiv.org/abs/2609.01244 (HTTP 200)

- **Title:** "**Post-Training Science for Supervised Fine-Tuning**"
- **Authors:** Charles O'Neill, Mudith Jayasekara, Harry Partridge (+2). **Affiliation: Baseten.**
- **Date:** 2026-09-01 (v1, cs.LG). Eighteen days old as of today.

**Scope (matters for how much weight to give it):** a one-lever-at-a-time sweep over **Qwen3 (0.6B–32B)** and
**Llama (3.2-1B, 3.2-3B, 3.1-8B)**, plus MoEs to 235B, on **four anonymised real-world customer SFT datasets**,
for **both LoRA and full fine-tuning**. It is **not** a maths-reasoning paper and **not** an open-recipe
frontier model; several headline findings are LoRA-specific. Selections are made on **validation NLL**.

**Verified findings relevant to you:**
- **Optimal-LR law** (Eq 2.1): `LR = C · M_tuner · (2000 / hidden_size)^(p+q_tuner)`, fitted per family.
  The **LoRA exponent p+q is statistically indistinguishable from zero** in both families → optimal LoRA lr is
  **flat at 1e-3** across 0.6B–32B. The **FullFT optimum sits near 1e-5**. The per-cell discrete-best
  LoRA/FullFT ratio is **≈33×**.
- **Transfer:** a law fit on one family predicts the other's optima to within **0.004 nats**; leave-one-dataset-out
  prediction error is **median 0.0, 90th-percentile ≈0.5 in log₁₀ lr**.
- **Epochs (§7):** "validation loss **overfits past about two epochs** while judged quality does not improve and
  **instruction-following erodes**", and "adding examples lowers loss but **does not move the optimal epoch
  ceiling beyond approximately two**."
- **Data volume (§7.1, §5.2):** "**fresh examples over more passes**"; on Qwen3-4B/8B/14B, "tripling fresh
  examples lowers one-epoch LoRA validation loss in **every experiment**".
- **Optimiser (§6):** **Muon** at a learning rate **~3× below AdamW's** reaches marginally lower validation NLL
  and a flatter minimum on all four datasets, with judged task quality even and **more instruction-following
  retained on IFEval**.

**Two points of direct support for your plan.** First, its **FullFT optimum near 1e-5** is an independent
data point that **your lr 1e-5 is in the right zone** — reassuring, given it sits 2× above Tülu 3 and Apertus.
Second, "**fresh examples over more passes**" is exactly your 150M → 600M → 1.5B strategy, and argues against
fixing maths by adding epochs.

**Caveat:** its epoch ceiling (~2) is measured on **customer instruction-following tasks judged by task-specific
evals**, and its strongest data-volume evidence is **LoRA**. It does **not** contradict AceReason's 5-epoch
long-CoT result so much as describe a different regime — which reinforces §B5's advice to stay at **2–3 epochs**
for a non-thinking model.

---

## C. Consolidated recommendations

**Split design**
1. Split on **root problem**, with translations and multi-solution groups bound to the root.
2. Reserve **60k–85k maths roots**, 25k–40k code, 15k–25k IF, 10k–20k other; target **20k–30k in-band maths
   prompts** at RL time.
3. Hold out a **separate never-train TEST split** (1k–2k roots/capability) and report **pass@1 and pass@8**
   on it side by side.
4. Do **not** enforce strict disjointness at RL time — Tülu 3's best mix combines unused and reused prompts.
5. Screen difficulty with **k=8 rollouts from the exact RL starting checkpoint**, at **RL-time sampling
   parameters**, keeping roughly **1–7 correct of 8**. Re-run per checkpoint; add online filtering during RL.
6. Pre-stratify using **Big-Math's published Llama-3.1-8B 64-rollout solve rates** before spending your own compute.
7. Tag every reserved item for **Greek portability**; exclude English-specific wordplay outright.
8. For IF, hold out **constraint templates**, not just instances (Tülu 3 overfit IFEval).

**Gate before maths DPO/GRPO**
9. Require **≥30%** of reserved maths prompts in-band (≥25% minimum) at pass@8. **At today's 20%-at-k=32,
   do not start.** Reallocating your existing 3,680-rollout budget from 115×32 to 460×8 would, at published
   retention rates, yield **~212 in-band prompts instead of 23**.

**Hyperparameters / exposure**
10. **Audit loss normalisation first** (Tülu 3 §4.3.2) — packed sequences + assistant-only loss + ZeRO-3 is
    precisely the configuration where per-example vs per-token weighting silently diverges, and it
    systematically down-weights long maths targets.
11. **Raise tokens-per-update** from 65,536 toward **256k–1M**; you are 8–16× below comparable runs.
12. **Keep lr ~1e-5** (supported by Baseten's FullFT optimum); do not raise it. If you change batch size,
    rescale **β₂** by the half-life rule (β₂_new = β₂_old^(B_new/B_old)) as a deliberate, disclosed choice.
13. **2–3 epochs**, not 1 and not 5 — AceReason's 5 is long-CoT-specific.
14. **Add checkpoint averaging** (last 4 of 6 equally spaced): >2% on MATH validation, free.
15. **Disclose the drift from Apertus's own SFT recipe** (AdEMAMix→AdamW, β₂ 0.999→0.99, 5e-6→1e-5,
    linear→cosine, batch 512→16) in a parameter table before the next launch.

---

## D. Source index

| Source | URL | Status |
|---|---|---|
| Tülu 3 | https://arxiv.org/html/2411.15124v5 | VERIFIED |
| OLMo 3 | https://arxiv.org/html/2512.13961v2 | VERIFIED |
| SmolLM3 | https://huggingface.co/blog/smollm3 | VERIFIED |
| Apertus v1 | https://arxiv.org/html/2509.14233 | VERIFIED |
| OpenMathInstruct-2 | https://arxiv.org/html/2410.01560 | VERIFIED |
| OpenThoughts3 / Data Recipes | https://arxiv.org/html/2506.04178 | partially read (dataset scale only) |
| AceReason-Nemotron 1.1 | https://arxiv.org/html/2506.13284 | VERIFIED |
| DeepSeekMath (GRPO) | https://arxiv.org/html/2402.03300 | VERIFIED |
| Qwen2.5-Math | https://arxiv.org/html/2409.12122 | VERIFIED |
| DAPO | https://arxiv.org/html/2503.14476 | VERIFIED |
| Skywork-OR1 | https://arxiv.org/html/2505.22312 | VERIFIED |
| Big-Math | https://arxiv.org/html/2502.17387v1 | VERIFIED (v2/v3 HTML 404) |
| Yue et al., RLVR pass@k | https://arxiv.org/html/2504.13837 | VERIFIED |
| Small-batch / β₂ half-life | https://arxiv.org/html/2507.07101 | VERIFIED |
| Post-Training Science for SFT (Baseten) | https://arxiv.org/abs/2609.01244 | VERIFIED — exists |
| HF gradient-accumulation blog | https://huggingface.co/blog/gradient_accumulation | NOT fetched; phenomenon verified via Tülu 3 §4.3.2 |
| AceMath, Polaris, PRIME, Kimi 1.5, Llama 3 rejection sampling | — | **NOT VERIFIED — do not cite** |
