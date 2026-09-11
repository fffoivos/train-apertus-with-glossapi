_Provenance: literature review written by the cross-vendor reviewer (gpt-6-astra, xhigh, 2026-09-11, one call for the three documents, no web access: written from the model's knowledge; brief docs/reviews/briefs/astra_dpo_literature.md; raw output docs/lit/ASTRA_DPO_LITERATURE_raw_20260911.md). Citations marked [verify] by the reviewer and the key numbers were checked by Claude on 2026-09-11; see the VERIFICATION section at the end. Owner discussion doc: docs/RLHF_PLAN_20260911.md._

# DOC C — Synthetic preference data

## 1. Verdict

**Build a smaller, failure-focused first dataset from R3’s own responses, with explicit provenance and a separate recovery lane.** The draft’s generation strategy is broadly consistent with successful synthetic-preference work, but the “no humans” category needs correction: several influential reward models rely on human annotations upstream. The proposed 5,000–7,000 retained pairs are a hypothesis, not a measured yield, and the current selection rules could systematically remove useful chat preferences. Native Greek prompts, valid correction examples, decontaminated failure-derived tasks, and cross-vendor/native auditing matter more here than copying a large English preference corpus.

## 2. Findings ranked by severity

| Severity | Finding and evidence | Concrete fix |
|---|---|---|
| **HIGH** | **The planned distribution is not yet tied to post-R3 failures.** Draft §4.6 assigns 6,500/10,500 prompts, **61.9%**, to IF, math, and retention-checker lanes. The largest supplied failures concern redirect handling and self-observation, and those measurements precede the proposed R3 evaluation. | Reallocate after R3 evaluation. Give redirects, correction handling, recaps, and conversation state explicit quotas instead of expecting generic IF to transfer. |
| **HIGH** | **Training on failure transcripts can contaminate evaluation.** Draft §§4.1 and 4.6 draw on R0/R1 transcripts and owner-chat replays while using related dialogue measurements for promotion. | Mark reused transcripts and close derivatives as training/development. Freeze a separate final evaluation split by source dialogue and scenario/template family. |
| **HIGH** | **“LLM raters and no humans” conflates label provenance.** HelpSteer-style data and reward models are not examples of an entirely human-free chain. | Record whether each label is newly human-authored, AI-authored, or produced by a model trained on human preference/attribute labels. |
| **HIGH** | **The same-family generation/judging risk is real but unmeasured here.** Sol wrote much of the SFT data and will judge the policy’s outputs. Vendor identity alone neither proves nor removes bias. | Audit content-equivalent style contrasts, remove source metadata, use Opus on a fixed subset, and use native human adjudication for consequential disagreement. |
| **MEDIUM** | **The retained-pair forecast has no pilot evidence.** 5,000–7,000 from 10,500 prompts means **47.6–66.7% yield**. No family-level pass rates, disagreement rates, or length-filter losses are supplied. | Estimate yield and reasons for rejection from a stratified pilot. Forecast by family rather than using a single overall percentage. |
| **MEDIUM** | **The recovery policy is underspecified.** Draft §3 allows rewrites for loop failures, but does not define minimality, verification, proportion, or objective. | Store recovery data separately. Prefer minimal verified repairs; compare a small recovery-SFT lane with rewrite-positive DPO before merging them. |

## 3. What is good and should not be changed

- Sample the model’s actual response distribution.
- Use existing failure cases to identify prompt families.
- Keep evaluation prompts out of generation.
- Retain the programmatic verifier infrastructure.
- Preserve two-order checks and independent audits.
- Avoid training a Greek reward model before its cost is justified.
- Keep full candidate sets and raw judgments, even when only one pair is used.
- Separate newly generated preference data from completed SFT datasets and their historical labels.

## 4. Literature answers

### What the influential synthetic pipelines actually did

| Recipe | What it contributes | Important qualification |
|---|---|---|
| **UltraFeedback** | Roughly **64k prompts**, typically **four responses per prompt**, generated from a pool of models and scored by GPT-4 on multiple dimensions. [Cui et al., *UltraFeedback*, arXiv:2310.01377](https://arxiv.org/abs/2310.01377). | A substantial synthetic preference source, but scorer details, aggregation, and binarization matter. |
| **Zephyr** | Demonstrates effective instruction and preference distillation into a 7B model using synthetic data. [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944). | Dataset cleaning and preference extraction are part of the recipe, not incidental bookkeeping. |
| **Tülu 3** | Uses a broad prompt mixture and model-specific preference generation as part of a staged open pipeline. [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124). | Exact mixture size, candidate sources, scorer, and stagewise ablations should be checked before replication. |
| **HelpSteer / HelpSteer2** | Attribute-based supervision separates helpfulness, correctness, coherence, complexity, and verbosity. HelpSteer2 uses approximately **10k response pairs** with human annotations. [Wang et al., arXiv:2311.09528](https://arxiv.org/abs/2311.09528); [Wang et al., arXiv:2406.08673](https://arxiv.org/abs/2406.08673). | These are not “no-human-label” datasets. Pair counts and response counts must not be confused. |
| **Nemotron-style reward use** | A reward model can turn attribute supervision into scalable scoring of new synthetic responses. HelpSteer2 is a relevant underlying source. [Wang et al., arXiv:2406.08673](https://arxiv.org/abs/2406.08673). | New labels may be automatic while the scorer inherits human supervision. Reward-model benchmark success is not automatically policy-training success. |
| **ArmoRM** | Uses multi-objective reward modeling and a gating mechanism to combine attribute predictions. [Wang et al., *Interpretable Preferences via Multi-Objective Reward Modeling and Mixture-of-Experts*, arXiv:2406.12845](https://arxiv.org/abs/2406.12845). | A learned attribute mixture is not an objective Greek-quality oracle. |
| **Skywork reward data/models** | Relevant releases include `Skywork/Reward-Preference-80K`. | **[verify release composition and paper metadata]**. I cannot responsibly give a paper-level provenance claim or isolated DPO gain from memory. Do not classify the release as wholly synthetic without checking it. |
| **Magpie** | Synthesizes user instructions by exploiting an aligned model’s chat formatting, reducing dependence on hand-written seed questions. [Xu et al., *Magpie*, arXiv:2406.08464](https://arxiv.org/abs/2406.08464). | It creates an instruction distribution, not verified preference truth; Greek realism and task coverage still require checking. |
| **SPIN** | Uses existing demonstrations as positives and model-generated responses as negatives in iterative self-play fine-tuning. [Chen et al., *Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models*, arXiv:2401.01335](https://arxiv.org/abs/2401.01335). | A counterexample to “both candidates must be on-policy.” It also depends on the quality of the demonstration positives. |
| **Self-rewarding LMs** | Iteratively generates and evaluates responses with the model itself; the reported setup includes several iterations at larger model scale. [Yuan et al., *Self-Rewarding Language Models*, arXiv:2401.10020](https://arxiv.org/abs/2401.10020). | Does not establish that an 8B Greek model can reliably judge its own linguistic or factual errors. |
| **West-of-N** | Selects high- and low-scoring samples to create synthetic preference contrasts, particularly for reward-model improvement. [*West-of-N*, arXiv:2401.12086](https://arxiv.org/abs/2401.12086), **[verify metadata]**. | Best/worst selection amplifies scorer errors as well as useful contrasts. |
| **RLAIF** | Finds that AI feedback can be competitive with human-feedback pipelines in evaluated tasks, and examines choices of AI labeler. [Lee et al., *RLAIF vs. RLHF*, arXiv:2309.00267](https://arxiv.org/abs/2309.00267). | Neither the strongest available model nor a same-size model is guaranteed to be the best rater for every task. Task-specific agreement matters. |

### UltraFeedback cleaning: the transferable lesson

UltraFeedback’s downstream use exposed the importance of checking scoring and binarization rather than trusting aggregate labels. The Zephyr/UltraFeedback history includes revisions to preference construction and cleaned releases; **the exact bug mechanism and affected dataset revision should be verified before citing it quantitatively**. [Cui et al., arXiv:2310.01377](https://arxiv.org/abs/2310.01377); [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

For your pipeline, make these invariants explicit:

- A selected winner must actually correspond to the intended candidate.
- Swapped-order outputs must map back to stable candidate IDs.
- Aggregated scores must match their component fields.
- A hard-veto flag must not disappear during binarization.
- Identical candidates must not become a strict preference.
- Missing/invalid judgments must not default to zero and accidentally become “worst.”
- Dataset revisions must be immutable and recorded.

These checks are more valuable than invoking “UltraFeedback-style” as a quality guarantee.

### Prompt sourcing: failures, difficulty, and coverage

Use three sources:

1. **Fresh R3 failures**, collected on development scenarios.
2. **New instances of explicit target behaviours**, with controlled truth and constraints.
3. **Naturalistic Greek requests**, including benign conversations where excessive defensiveness would be harmful.

A failure transcript is a source of a task, not permission to reuse the same scenario in the final test.

Hard prompts are useful when the model sometimes succeeds. If it never succeeds, ordinary within-policy DPO cannot supply a valid chosen response. Very easy verifier prompts likewise offer little contrast when every candidate receives the same outcome.

Do not optimize only the difficult edge cases. A correction-heavy dataset can teach the model to treat ordinary users as adversaries. Include:

- valid corrections;
- invalid corrections;
- uncertain corrections requiring checking;
- benign requests that require no correction discussion.

Prompts close to SFT data are not automatically invalid. However, near-duplicates can train memorization and overstate progress if related prompts appear in evaluation. Split and deduplicate by source, semantic scenario, and template—not merely by exact string.

### Sampling: temperature, k, and diversity

Use **T=0.8, k=4** as a provisional baseline. Keep the same decoding configuration within the main comparison.

Record:

- temperature, top-p, and any top-k;
- repetition penalties;
- maximum output length;
- stop tokens;
- seeds;
- serving/model/tokenizer revisions.

Do not change repetition penalty while measuring whether DPO fixes repetition; otherwise the causal attribution becomes ambiguous.

**Diversity means different plausible solutions or discourse choices, not just different wording.** Measure duplicate and near-duplicate rates. If all four responses are effectively identical, increasing k may buy little.

For difficult but recoverable prompts, a second batch of four samples is reasonable. Give that lane a cap and record the additional cost.

### Why current-policy responses are usually preferable—and when rewrites help

Current-policy candidates provide errors the model actually makes. They also avoid making source/style differences perfectly predictive of preference. The online/offline alignment literature supports the importance of candidate distribution and negative examples. [Tajwar et al., arXiv:2404.14367](https://arxiv.org/abs/2404.14367).

Teacher rewrites can nevertheless be valuable when the policy does not produce the desired behaviour at all. SPIN and Zephyr are evidence against categorically excluding off-policy positives. [Chen et al., arXiv:2401.01335](https://arxiv.org/abs/2401.01335); [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

The risks of rewrite-positive DPO include:

- learning the teacher’s style rather than the substantive correction;
- very different chosen/rejected support;
- attributing the preference to length or formatting;
- importing new factual mistakes;
- allowing a generator to judge its own repair.

For loop failures, prefer a **minimal repair of the model’s response** over a completely new essay. Verify the repair independently and keep its provenance visible. A small SFT recovery lane may be easier to interpret than mixing these pairs into the main DPO objective.

### Same-family SFT generation and judging

The concern is plausible:

1. Sol writes SFT responses.
2. R3 acquires some Sol-associated style.
3. Sol rewards outputs matching its preferred style.
4. The next model becomes more stylistically homogeneous, without necessarily becoming more useful.

The self-preference literature supports investigating this mechanism; it does not quantify it for Sol, Greek, or your checkpoint. [Panickssery et al., arXiv:2404.13076](https://arxiv.org/abs/2404.13076).

Mitigate it with:

- model-source blinding;
- a fixed Opus audit subset;
- native-speaker judgments;
- correctness/style conflict cases;
- content-equivalent alternatives with different presentation;
- analysis of whether judge preferences track length, headings, disclaimers, or familiar verbal habits.

A different vendor reduces one source of dependence. It does not remove shared training data, common stylistic preferences, or shared factual errors.

### Filtering and confidence

Retain a pair only when:

- the prefix is identical;
- the chosen response meets the task-quality floor;
- the hard-veto decision is supported;
- the preference is substantive and clear;
- accepted judging orders agree;
- candidate identity mapping is correct;
- neither response was truncated in a way that invalidates comparison.

Do not equate self-reported judge confidence with a calibrated probability. Use confidence as an audit-routing feature unless calibration demonstrates otherwise.

Preserve rejected and uncertain quartets. They tell you whether a failure is due to:

- model incapability;
- ambiguous rubric;
- unreliable Greek judgment;
- inconsistent order effects;
- insufficient diversity;
- unsuitable prompt construction.

### Data quantity and the observed curve

The published counts establish that useful preference training spans **tens of thousands to hundreds of thousands of pairs**, not that more is always better. UltraFeedback/Zephyr and Tülu 3 are relevant scale references, but not a controlled learning curve for Greek dialogue behaviour. [Cui et al., arXiv:2310.01377](https://arxiv.org/abs/2310.01377); [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124).

For your project, the important curve is:

> retained **distinct, reliable contrasts** versus improvement on new conversations.

Measure it at the pilot and full first-iteration scale. Repeating easy preferences or generating all six correlated pairs from every quartet can inflate pair count without equivalent information.

### Synthetic-preference failure modes

| Failure | Detection | Prevention |
|---|---|---|
| Rubric hacking | High rubric score with poor independent task outcomes | Hold-out adversarial checks; independent evaluation |
| Length inflation | Length shifts within task families; preferences correlated with length | Task-conditioned judgment and length-controlled audits |
| Formatting bias | Headings/list structure predict preference after controlling for content | Style-controlled comparisons |
| Refusal over-generalization | Increased refusal on benign requests, including XSTest-style cases | Include benign hard prompts and audit refusal reasons |
| False anti-sycophancy | Model refuses valid corrections | Balance valid/invalid/uncertain corrections |
| Language drift | More English framing, code-switching, or translated-sounding Greek | Original Greek evaluation and language-specific monitoring |
| Teacher-style collapse | Reduced variation without better correctness or completion | Source-blind, content-controlled audits |
| Reward overoptimization | Training score rises while independent quality stalls or falls | Early stopping on held-out behaviour, not training reward |

Reward overoptimization is an established general concern; its precise onset depends on the proxy and optimization strength. [Gao et al., arXiv:2210.10760](https://arxiv.org/abs/2210.10760).

### Lower-resource language evidence

Translated preference sets are useful for coverage and can reduce annotation cost. They are weaker evidence for native pragmatics, idiom, register, and correction dynamics.

Okapi is a relevant example of multilingual instruction/RLHF work using multilingual data construction. [*Okapi: Instruction-tuned Large Language Models in Multiple Languages with Reinforcement Learning from Human Feedback*, arXiv:2307.16039](https://arxiv.org/abs/2307.16039), **[verify metadata and exact translated components]**.

Aya and Aya 23 establish the value of deliberate multilingual data and evaluation, but their final model results do not isolate the effect of native versus translated Greek preference data. [Üstün et al., arXiv:2402.07827](https://arxiv.org/abs/2402.07827); [Aryabumi et al., arXiv:2405.15032](https://arxiv.org/abs/2405.15032).

For EuroLLM, Salamandra, Meltemi, and Krikri, do not infer preference-training details merely from the existence of an instruction checkpoint. The exact Greek DPO methods and controlled native-versus-translated preference ablations remain **open in this review**.

For your target behaviours, native Greek generation should dominate. Translation is more defensible for content-preserving tasks than for politeness, social sycophancy, naturalness, or subtle conversational repair.

## 5. Open questions for the owner, followed by a concrete pipeline

The remaining questions are:

1. Which R0/R1 and owner-chat scenarios have already influenced training or prompt design?
2. Which final evaluation scenarios can remain untouched?
3. How many post-R3 failures are recoverable with k=4 or k=8?
4. Does “no humans” mean no new large-scale labels, or literally no upstream human supervision?
5. How much native review is available after calibration?
6. Should rewrite recovery be a separate SFT intervention or a small, explicitly labeled DPO component?

**Proposed first-iteration pipeline**

### Prompt allocation

Start with **6,000 distinct prompts**, subject to adjustment after the R3 baseline:

| Family | Prompts | Main evidence |
|---|---:|---|
| Redirects and correction handling | 1,500 | Typed truth/constraint checks plus judgment |
| Standing instructions and conversation-state retention | 900 | Validated checks; semantic audit |
| Recap and self-observation | 600 | Prefix-grounded answers, typed checks where possible |
| Greek verifiable IF | 900 | Checkers |
| Greek math | 600 | Answer verification; reasoning audit subset |
| Naturalistic Greek open chat and owner-style requests | 1,000 | Judgment |
| English/other EU-language preservation | 500 | Language-appropriate checks and judgment |
| **Total** | **6,000** | |

This gives explicit attention to the reported discourse failures while preserving a verifier component. It is a proposal, not a literature-derived optimum.

Use a **stratified 1,200-prompt pilot** from this training pool first. Keep the native calibration set and final evaluation outside it.

### Sampling and rating

- Generate **four R3 responses per prompt**, T=0.8.
- This produces **24,000 responses**.
- At 300 output tokens each, that is approximately **7.2 million generated tokens**, excluding prefixes and recovery samples.
- Run applicable verifiers first.
- Use two-order rubric comparison on judgment-dependent families, allowing ties.
- On the calibration subset, compare selected-pair decisions with direct order-swapped pairwise judgments.
- Audit a fixed **10% of judged prompts with Opus**, stratified by family and including both hard-veto decisions and accepted pairs.

If all 3,600 prompts in the redirect/correction, recap, open-chat, and preservation lanes receive two primary calls, that is **7,200 Sol calls**, before retries and calibration. At the supplied 18k fixed-input assumption, it entails **129.6 million fixed input tokens**. At the draft’s supplied 0.004% quota-per-call estimate, it would consume **28.8%**, not 2.88%. Actual consumption must be measured.

### Pair construction and recovery

- Keep at most one main pair per prompt.
- Keep all-pass pairs with a meaningful substantive preference.
- Drop true ties and unresolved disagreements.
- Never choose a confirmed hard failure.
- Keep Greek-error flags advisory until their precision supports veto use.
- Remove the universal 1.5× length filter.
- For all-fail prompts, permit one capped resampling round.
- If still unsolved, route to a separately tracked recovery set; do not manufacture an ordinary on-policy pair.

Forecast **roughly 3,000–4,000 main pairs** only as a planning assumption. Replace that forecast with measured family-level yield after the pilot. Record every filtering stage’s count.

### Storage and evaluation

Store all candidates, raw judgments, order mappings, verifier versions, truth provenance, token counts, generation settings, and final pair reasons.

Split by source dialogue and scenario/template lineage. Once a failure case informs training, treat it as development evidence. Use separate final conversations for promotion.

Select checkpoints on development data, then run the reserved final evaluation. Report primary dialogue results with paired, dialogue-level uncertainty and disclose which seeds received which evaluations.

### The three most informative experiments

1. **Judge-protocol calibration before training.**  
   On the same blind items, compare two-order k-way decisions with direct pairwise decisions. Measure human agreement, ties, position reversals, Greek-veto precision, and truth-versus-style conflicts. This determines whether the proposed labels deserve optimization.

2. **A small objective comparison on identical data.**  
   Compare plain DPO, DPO with the explicitly normalized α=0.1 chosen-NLL anchor, and an equal-exposure chosen-only SFT control. Keep β, LR, masks, and prompts fixed where applicable. Measure discourse gains, chosen likelihood, held-out Greek loss, and retention. This tests whether the negative preference signal helps and whether the anchor prevents a real regression.

3. **Conditional refreshed-data iteration.**  
   If iteration one helps and budget remains, compare training on newly sampled policy responses with further training on the old pairs at matched optimizer exposure. Report the extra sampling cost. This directly tests the claimed value of iteration for this model, rather than assuming two iterations are better.

## VERIFICATION (Claude, 2026-09-11 18:05)

Every arXiv identifier in the three documents (44 distinct) was resolved to its title on arxiv.org (docs/lit/citation_check_20260911.json). 41 resolve to the paper the reviewer names. Three identifiers were wrong and are corrected in place: West-of-N is arXiv:2401.12086 (the reviewer wrote 2402.05392, an astronomy paper); Meltemi is arXiv:2407.20743 (not 2407.20773); the Salamandra technical report is arXiv:2502.08489 (not 2502.08486). Not yet verified: the Tülu 3 preference-pair count the reviewer marked [verify], and the exact experimental scope of the "preference models prefer sycophantic answers 95% of the time" figure from Sharma et al. 2023, which the reviewer challenged in DOC B; both stay marked. Numbers quoted from papers (β ranges, pair counts, benchmark deltas) were NOT independently checked against the papers' text; treat them as the reviewer's reading until the owner discussion picks the ones we will rely on.
