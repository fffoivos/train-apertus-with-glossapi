# Astra review: benchmarks_worth

Date 2026-09-10 00:29 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T00-23-35-01a0880e-0794-75f0-bd1f-5fd6e6eabeb2.jsonl) · effort xhigh · 6.3 min · prompt 39,007 chars · limit deltas {('codex', '10080'): -62.0, ('codex_bengalfox', '300'): 0.0} · brief `docs/reviews/briefs/astra_benchmarks_worth.md`

## 1. Verdict

**Revise before adoption.** The proposal has a sound core—strict instruction-following scores, paired comparisons, independent judging, and a frozen evaluation protocol—but its held-out definition and promotion rule are not usable as written. Several exclusions confuse frontier saturation with usefulness for this particular 8B model, while Greek multi-turn behavior, robustness, and identity lack explicit acceptance tests. My disposition is **2 BLOCKER, 6 HIGH, and 2 MEDIUM findings** below. I verified internal claims against the supplied text and independently checked the statistical arithmetic. Browser and filesystem tools were unavailable, so I could not verify the cited papers, vendored implementation, or companion review. **No dataset rows or item manifests were supplied: row-level failure rates and row IDs are unavailable.** Counts below concern the proposal, not generated data.

## 2. Findings ranked by severity

### R1 — BLOCKER: The proposed held-out split overlaps development by definition

**Evidence verified from §4:** **3 of the 5 named unseen groups—INCLUDE-el, lyceum math, and IFBench—also explicitly appear in Tier A**, which the split defines as development. MultiChallenge specifies conversations “outside the development subset,” but provides no membership manifest. This establishes a contradictory specification; it does **not** establish a measured item intersection.

Freezing this list before training would preserve the contradiction. Repeatedly inspecting an “unseen” score to choose arms would also turn it into development feedback.

**Concrete fix:** Publish disjoint development and final-evaluation manifests before the next run. For the current proposal, remove INCLUDE-el, lyceum math, and IFBench from development if retaining them as unseen. Define MultiChallenge membership by conversation IDs. Group translations, paraphrases, shared source passages, and problem variants before assigning splits. Specify when final results may be revealed and how the set is retired from unseen status after informing subsequent decisions.

### R2 — BLOCKER: The promotion rule contradicts the statistical protocol and does not protect retention

**Evidence verified from §5:**

- §5.1 requires Holm–Bonferroni correction.
- §5.6 instead promotes on **two wins exceeding an unadjusted 1.96 × SE**.
- “Loses none by that margin” treats failure to detect regression as evidence of acceptable retention.
- Tier A contains retention metrics, so two retention improvements could satisfy promotion without improving the intended SFT behaviors.

An uncertain regression can therefore pass. Two closely related English/Greek benchmark versions could also supply the required wins without demonstrating improvement across two distinct skills.

**Concrete fix:** Replace the rule with a preregistered endpoint hierarchy:

1. Identify the Greek capability endpoints whose improvement justifies promotion.
2. Specify a minimum practically useful gain and the multiplicity correction across planned arm comparisons.
3. Give retention endpoints explicit non-inferiority margins; require their confidence bounds to exclude unacceptable degradation.
4. Give critical safety and identity failures separate acceptance rules.
5. Return **inconclusive**, rather than “no loss,” when precision is insufficient.

Limit checkpoint selection and repeated comparisons explicitly. Reserve the final held-out evaluation for the selected candidate.

### R3 — HIGH: The item-budget recommendations omit the quantities that determine paired power

**Evidence:** §§1, 5 and B.2 repeatedly claim approximately 1,000 items resolve a 3-point difference at 80% power. That is not a general result.

For paired binary outcomes, let \(q\) be the fraction of items on which the two arms disagree and \(\Delta\) their accuracy difference:

\[
SE(\widehat\Delta)\approx\sqrt{\frac{q-\Delta^2}{n}}.
\]

A simple two-sided, 5%-level, 80%-power approximation gives:

\[
n\approx\frac{(1.96+0.84)^2q}{0.03^2}.
\]

| Assumed discordance \(q\) | Approximate items needed |
|---|---:|
| 10% | 872 |
| 25% | 2,180 |
| 50% | 4,360 |

These are illustrative calculations before multiplicity or clustering adjustments.

The blanket rule “below ~400 items, differences under 5 points are noise” is also false. With 300 paired items and 12 improvements versus zero regressions, the gain is 4 points and exact two-sided McNemar \(p\approx0.00049\).

**Concrete fix:** Estimate discordance from a pilot, then calculate detectable effects for the actual paired design. Report improvement/regression counts. Use Wilson intervals for individual proportions, and an appropriate paired-difference interval or exact test for arm differences. Resample conversations, shared passages, or problem families when those are the independent units. Repeated generations must remain nested within items.

### R4 — HIGH: Several exclusion verdicts are contradicted by the appendix’s own 8B evidence

**Evidence verified from the supplied tables:**

- **GSM8K:** Appendix B.3 reports Apertus at **62.9**. Frontier saturation does not establish saturation for this model.
- **BBH:** B.3 reports Apertus at **55.9**, and an IQR of **7.7** across the reported model sample. That contradicts a blanket “spent” argument based on near-perfect frontier performance.
- **GPQA/AIME:** B.3 itself reports Qwen3-8B **non-thinking** scores of **39.3 on GPQA Diamond and 29.1 on AIME’24**. Parameter count alone therefore does not establish a floor.
- **HLE/Arena-Hard v2:** Missing 7–9B entries establish missing evidence, not measured floor performance.
- Apertus’s **24.7 on 198 GPQA Diamond items** is numerically below 25%, but ordinary sampling uncertainty spans chance comfortably.

Meta’s contamination measurements also concern particular training data and models; they do not establish a universal contamination percentage for your arms.

**Concrete fix:** Base inclusion on the actual Apertus baseline and representative SFT checkpoints under the intended protocol. Keep GSM8K/MGSM eligible to contribute math evidence if paired results are informative. BBH may still be omitted for cost or redundancy, but the stated universal saturation rationale should be removed. Defer AIME and GPQA because of the current baseline, precision, and priorities—not a universal “below ~30B” rule.

### R5 — HIGH: The battery’s endpoint roles and Greek target coverage are incomplete

**Evidence verified from §§3–5:**

- Tier A is called “decisions,” yet includes Greek and English **retention**.
- Its **≥500-item** requirement conflicts with HumanEval’s **164 problems** in B.2; adding more unit tests does not create more independent programming problems. B.2 also lists a 378-item MBPP evaluation, without establishing the actual proposed MBPP+ configuration.
- The proposed math pool is **465 + 250 = 715** items. Pooling does not itself validate the constructs, independence, or weighting. A raw aggregate implicitly weights lyceum math approximately **65%** and MGSM **35%**.
- §4 provides no explicit Greek identity endpoint or acceptance criterion, and no operational Greek robustness specification. Proposed multi-turn additions are English.
- No Greek scorer validation records are supplied for the primary `ifeval_greek` metric.

**Concrete fix:** Give every endpoint one role: **selection, retention constraint, diagnostic, or final held-out evaluation**. Use fixed, justified math strata and report each separately. Remove the universal 500-item eligibility rule.

Add a small, sealed Greek behavioral suite covering multi-turn constraint persistence, corrections, instruction hierarchy, misleading embedded instructions, code-switching, and the owner’s exact identity policy. Report critical failures as counts; do not claim a small suite estimates population performance precisely.

Before relying on Greek IFEval, require existing validation evidence—or perform validation—of translated prompts, constraint metadata, Unicode handling, word/character counts, and known passing/failing outputs. This is an **unverified measurement dependency**, not an observed scorer defect.

### R6 — HIGH: The harness description does not establish either EvalPlus coverage or published-score comparability

**Evidence verified from §§3–4 and A.3:**

- The listed tasks are `humaneval_instruct` and `mbpp_instruct`; the recommendation subsequently calls them **HumanEval+/MBPP+**, “all in the vendored suite.” Those names do not establish use of augmented tests.
- The published **IFEval 71.7 is prompt-loose**; the proposed primary metric is strict.
- The published HumanEval result is **pass@10**; that is not interchangeable with pass@1 or evaluation against augmented tests.
- The proposed `minerva_math500` is not automatically the same evaluation as the published “MATH” number.
- A later Apertus 1.5 harness does not automatically reproduce the earlier report.

**Concrete fix:** Treat comparability as unproven until the task implementations, datasets, metrics, and model revision are audited and the reference model is rerun. Verify EvalPlus test assets explicitly. Report strict and loose IFEval from the same outputs, with different labels. Maintain separate historical-reproduction and locally standardized comparison configurations where necessary.

The required pins are detailed under question 5 below.

### R7 — HIGH: SFT-only decontamination cannot establish the proposed unseen sets’ cleanliness

**Evidence verified from §4:** The proposed filter examines the **SFT mix**. No coverage of CPT data, prior development exposure, synthetic-generation inputs, or benchmark derivations is specified.

The proposed INCLUDE/CPT overlap and culture-benchmark provenance remain **unverified risks**. The brief does not contain evidence sufficient to declare either clean or contaminated.

The “8-gram, >50% overlap, >2% suite overlap” policy also lacks operational definitions: normalization, overlap denominator, short-item handling, and whether the conditions are alternatives or conjunctions.

**Concrete fix:** Track three separate properties:

- Exposure in training, including CPT where inspectable.
- Exposure through model selection or prior evaluation.
- Public provenance and possible upstream exposure.

Audit the inspectable corpus lineage using exact and normalized matches, source identifiers, and targeted near-duplicate review. Document denominators and manually inspect candidate matches. Decide between item removal and source-level quarantine based on the findings; a universal 2% threshold is not a contamination guarantee. Describe results as “no detected overlap under these checks,” not “clean.”

### R8 — HIGH: Changing judge family invalidates inherited validation unless the new evaluator is calibrated

**Evidence:** The proposal inherits agreement claims for published evaluators while replacing their judges with Claude, Gemini, or Qwen. Appendix B.4 itself reports Arena-Hard agreement changing from **89.1% to 66.7%** after a judge substitution.

Neither cross-vendor judging nor an English rubric establishes reliable discrimination between close Greek SFT arms. MultiChallenge’s rubric result likewise does not establish performance on Greek outputs or these particular arms.

**Concrete fix:** Retain the no-OpenAI-judge policy as a conservative independence constraint. Then validate the actual judge, rubric, and scoring implementation on blinded Greek comparisons, including near ties and the target failure categories. Report human adjudication, order consistency, ties, and uncertainty alongside κ.

Label re-judged scores as custom evaluator variants. Keep fixed-baseline scores for trend tracking, but compare close finalists directly as well. English rubrics are a reasonable starting choice; the quoted correlation is not sufficient to make them an unconditional rule for Greek.

### R9 — MEDIUM: Seeds, prompt variants, and costs are conflated

**Evidence from §§5–6:**

- “Greedy plus 3 seeds or 3 prompt-format variants” mixes different sources of variation. A seed ordinarily does not diversify greedy decoding; format variants test a different intervention.
- “≥4 samples” is a default without a variance or cost justification.
- A full two-judge, two-order AlpacaEval run requires **805 × 2 × 2 = 3,220 judgments per arm**; three judges require **4,830**.
- “Minutes per task” has no measured token budget, throughput, judge latency, or code-execution evidence.

**Concrete fix:** Start with one frozen canonical run. Keep format robustness as a separate evaluation. Use repeated stochastic generations where a pilot shows meaningful instability, and distinguish decoding repetitions from independent training runs. Calibrate one primary judge, then use a second judge for a predefined audit subset and disputed comparisons. Pilot actual runtime and cost before calling the expanded suite “light.”

### R10 — MEDIUM: Several evidence summaries need narrower wording and traceable provenance

**Text-verifiable problems:**

- The **83% choice-only result is identified as TruthfulQA-v2** in A.2, but generalized to TruthfulQA elsewhere.
- SimpleQA Verified’s **76.9% removal** becomes “removed as noisy”; the supplied evidence does not provide exclusion-reason counts supporting that interpretation.
- “Highest replicated agreement” is stronger than the author-reported correlations shown for WildBench and LiveBench.
- “Pre-registered” is not established merely by describing a held-out evaluation.
- **Four benchmark families** marked “drop” in §2 reappear under logging in §4: BBH, DROP, TruthfulQA, and MT-Bench.
- The **403-model** distribution lacks a reproducible snapshot and analysis reference.

**Concrete fix:** Add a compact evidence ledger containing exact benchmark version, metric, model population, source location, and verified/unverified status. Distinguish percentages from percentage points and dataset attrition from label-error rates. Replace universal claims with the tested scope. Reconcile “drop” versus “log.”

## 3. What is good and should not be changed

- **Per-item paired comparisons** are the correct foundation.
- **Strict IFEval as a primary instruction-following measure** is reasonable, subject to Greek scorer validation. Preserve loose scores for diagnosis and historical comparisons.
- **IFBench is a well-motivated generalization addition**; assign its development or unseen role explicitly.
- **GreekMMLU is a useful knowledge-retention anchor.** Its size improves precision, although it does not establish cleanliness or instruction-following validity.
- Keeping **small development gates and interviews from independently deciding promotion** is sound.
- Freezing templates, extraction, decoding, and evaluation code is essential.
- The distinction between **contamination and measured score inflation** should remain.
- Acknowledging that n-gram checks miss paraphrases is correct. That limitation does not make those checks useless.

## 4. Answers to the specific questions

**1. Are the §2 verdicts supported?**  
Partly. The strongest cases are programmatic instruction following, additional constraint-family generalization, paired evaluation, and caution around judged scores. The weakest are blanket saturation/floor exclusions, benchmark-version generalizations, and treating published judge validation as transferable to replacement judges.

**2. Are the tiers right for arm selection at 8B?**  
No. Use Greek instruction following and validated Greek math as initial capability endpoints. Add explicit Greek multi-turn, robustness, and identity tests. Treat GreekMMLU and most English capability evaluations as retention constraints or diagnostics. Coding evaluations are optional retention checks given the stated targets; they should not automatically expand every light run. Avoid requiring two arbitrary benchmark wins.

**3. Is the protocol proportionate and sufficiently specified?**  
It overspecifies repeated generations and judge panels while underspecifying estimands, discordance, clustering, non-inferiority margins, repeated selection, and evaluator failure handling. A small team should freeze fewer meaningful endpoints, preserve detailed item logs, and spend extra evaluation budget on close decisions.

**4. Is the held-out split and decontamination stance sound?**  
Not yet. The split is internally contradictory, and SFT-only filtering cannot establish CPT cleanliness. Correct the manifests and provenance labels before calling anything unseen. Public, native, and programmatically scored are not synonyms for uncontaminated.

**5. What must be pinned or checked for Apertus comparability?**

| Component | Required evidence |
|---|---|
| Reference model | Exact Instruct checkpoint and tokenizer revisions; adapter/merge state where relevant |
| Harness | Commit, local modifications, task implementation, evaluator dependencies, and resolved profile |
| Dataset | Repository revision, configuration, split, item IDs, translations, and subset membership |
| Prompt construction | Rendered examples, chat template, system prompt, few-shot items/order, option order, and thinking mode |
| Generation | Token limits, stop/EOS behavior, sampling parameters, truncation, serving versions, precision, quantization, and relevant batching settings |
| Scoring | Extraction and equivalence checks; strict/loose and prompt/instruction aggregation; GPQA Main/Diamond; MATH/full/500; code tests and pass@k |
| Execution outcomes | Counts and treatment of timeouts, invalid answers, extraction failures, and truncated generations |
| Reproduction | Reference-model rerun with the exact configuration, plus investigation of material deviations from the publication |

Using the same harness is insufficient. **A reference rerun under your frozen configuration establishes a defensible local comparison even if historical numbers cannot be reproduced.**

## 5. Open questions for the owner

1. Which proposed unseen sets have already influenced CPT choices, SFT mixtures, prompts, checkpoints, or previous arm decisions?
2. Where are the item manifests and source-lineage records for INCLUDE-el, culture bench, lyceum math, and the MultiChallenge split?
3. What validation artifacts exist for Greek IFEval and the proposed Greek math scorers, including any already accepted in the companion review?
4. What exact behavior should the model exhibit for identity, instruction hierarchy, refusals, and Greek language persistence?
5. Which Greek capability gains justify promotion, and what regressions are unacceptable on each retention endpoint?
6. Which exact Apertus checkpoint, publication table, and harness commit define the intended comparison?
7. How many arms and checkpoints are expected, and what measured generation, judging, and human-review budget is available?

These findings concern the **proposal before adoption**. They do not establish defects in generated rows or justify changes to completed datasets.