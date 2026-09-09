# Astra review: next_benchmarks

Date 2026-09-09 22:19 · model gpt-6-astra (asserted from rollout rollout-2026-09-09T22-07-53-01a08791-c9ca-7b01-a2fa-09a5eb049144.jsonl) · effort xhigh · 11.4 min · prompt 20,504 chars · limit deltas {('codex', '10080'): 5.0} · brief `docs/reviews/briefs/astra_next_benchmarks.md`

## 1. Verdict

**Revise before bulk translation; keep the shortlist provisionally.** MultiChallenge is the strongest match for the next conversation-skills arm, IFBench is valuable only after establishing what is actually unseen relative to your 44 families, and XSTest needs both a faithful Greek subset and a separately reported native extension. MATH-500 remains fourth. The main weaknesses are benchmark comparability after localisation, insufficient judge/verifier validation, and an inadequate translation-quality audit. **This is a review of the supplied proposal, not a verified dataset audit:** no sample rows or row IDs were supplied, and source-access tools were unavailable in this session. I inspected **0 Greek rows and 0 upstream rows**; translation failure rates are therefore **N/A**, and I cannot substantiate the reported failures in “C rows,” verify licences, or certify the appendix’s citations. Counts below are calculations from the proposal, explicitly distinguished from observed defects.

## 2. Findings ranked by severity

### HIGH 1 — IFBench’s proposed OOD interpretation is not yet defensible

**Evidence — proposal §§3–4:** Your training set has 44 families; the proposed evaluation has 58 held-out constraints. Neither the family definitions nor their correspondence is supplied. The stated exact/n-gram/MinHash gate cannot establish whether evaluation constraints are structurally unseen. Furthermore, “replace non-transferable constraints with Greek-native ones” changes the evaluated construct.

**Consequence — inference:** You could report improved OOD instruction following while measuring familiar constraints expressed differently. Alternatively, replacements could make the Greek version substantially easier or harder.

**Concrete fix:**

- Before translation, build a mapping from **every upstream constraint ID** to your training families, with representative training examples and verifier semantics.
- Classify evaluation items as **unseen constraint**, **seen constraints in a novel composition**, **seen constraint/composition**, or **unresolved**.
- Report coverage and scores by these classes, both per instruction and per prompt. A prompt combining seen and unseen constraints needs explicit treatment.
- Publish a **faithfully transferred core** and a **Greek-native extension** separately. Preserve source IDs and document each replacement.
- Do not infer the number of novel families by subtracting 44 from 58; the taxonomies may have different granularity.

Keeping the upstream 29 training constraints out is a permissible experimental choice. It does **not** establish disjointness from your own training set.

### HIGH 2 — MultiChallenge’s evaluation protocol and judge validation are underspecified

**Evidence — proposal §§3–4:** The plan specifies “binary per-turn rubric questions,” “Sol or Opus,” and “both orders,” but provides no pinned evaluator, rubric schema, target-turn definition, or calibration results.

**Consequence — inference:** A seemingly minor implementation choice could produce a different benchmark. Fixed-history continuation and a fully generated multi-turn trajectory measure different things. Likewise, pointwise rubric judging and pairwise arm preference are different metrics.

**Concrete fix:**

- Pin the upstream data and evaluator first. Establish exactly which histories are supplied, which turns the candidate generates, and how scores aggregate.
- Preserve that protocol for the comparable Greek version. Label any additional rollout evaluation separately.
- Use **pointwise rubric compliance** for the main score. Answer-order reversal belongs to an explicitly pairwise comparison; it is not a generic validation procedure for binary judging.
- Give every rubric a stable ID, target turn, required evidence, and explicit pass/fail semantics.
- Calibrate the judge against native-human labels and deliberately constructed pass/fail responses, including fluent responses that violate one requirement.
- Report judge false-pass and false-fail rates. Cross-vendor agreement alone is not validation.

Run a small feasibility pilot **before** prioritising full IFBench/XSTest production. The proposed execution order delays answering whether the next training arm can actually be measured.

### HIGH 3 — The contamination gate needs provenance and cross-language checks

**Evidence — proposal §§2–4:** Training includes translated GSM8K train and MATH train levels 1–4. The proposed gate uses exact matches, long n-grams, and MinHash against SFT/CPT.

**Consequence — inference:** These methods can miss an English evaluation problem reproduced in Greek training, a paraphrased synthetic version, or an answer/solution reproduced without its original question.

**Concrete fix:** Require three separate checks:

1. **Source identity:** original dataset, revision, split, problem ID, and transformation lineage for both training and evaluation.
2. **Content overlap:** English originals, Greek translations, questions, solutions, and synthetic derivatives; use similarity retrieval to nominate candidates for adjudication.
3. **Experimental exposure:** whether benchmark items or outputs entered generation prompts, debugging, rubric development, checkpoint selection, or repeated arm tuning.

For MATH-500, confirm the expected MATH-test lineage against the actual pinned release and training manifest. **Training on MATH train does not itself invalidate MATH test.** Conversely, “train levels 1–4” does not prove absence of test-item duplicates.

Report confirmed overlaps, unresolved candidates, exclusions, and the remaining denominator. Exposure in inaccessible Apertus pretraining remains unknown; checking your CPT corpus cannot resolve it.

### HIGH 4 — XSTest localisation could remove the very trigger being tested

**Evidence — proposal §3:** “Roughly half” supposedly require reauthoring around Greek homonyms. No item inventory, IDs, or classification supports that fraction. Preserving ten prompt-type labels alone does not preserve difficulty or construct validity.

**Consequence — inference:** A natural translation may remove the alarming lexical ambiguity and make the item easy. A literal translation may create unnatural Greek that tests translation comprehension.

**Concrete fix:**

- Classify every source item as **faithfully transferable**, **requires lexical/cultural substitution**, or **requires a new native item**.
- Preserve source-to-Greek mappings and record the intended benign interpretation, alarming trigger, and relevant context.
- Require native review of **every reauthored item**, preferably by two reviewers with adjudication.
- Report a translated shared core and a native extension separately.
- Score safe and unsafe prompts separately: inappropriate refusal on safe prompts; harmful compliance on unsafe prompts.
- Add an adequacy check. A response can avoid refusal while failing to answer.

The counts in the proposal—250 safe and 200 unsafe—also mean this is not automatically a set of one-to-one matched pairs.

### HIGH 5 — A 5% native sample cannot support a strong quality claim

**Evidence — calculation from proposed sizes:** Rounding the proposed 5% sample upward gives:

| Benchmark | Native-reviewed items | If zero defects are found: approximate one-sided 95% upper bound on defect probability* |
|---|---:|---:|
| MultiChallenge, full | 14 | 19.3% |
| IFBench | 15 | 18.1% |
| XSTest | 23 | 12.2% |
| MATH-500 | 25 | 11.3% |

\*Binomial calculation: \(1-0.05^{1/n}\). These are **prospective uncertainty bounds**, not measured failure rates.

“Share of items edited at cross-check” is an editing statistic, not residual translation accuracy. A checker can miss defects or introduce unnecessary changes.

**Concrete fix:**

- Review all critical constraint changes, rubric changes, and lexical substitutions.
- Add a separately sampled, stratified audit of the final frozen dataset.
- Define defect categories: meaning, answer preservation, constraint preservation, rubric consistency, naturalness, and localisation validity.
- Report final-audit errors with numerator, denominator, severity, and uncertainty.
- If the desired claim is “under approximately 5% defects,” zero errors in a random sample of **59** items provides that one-sided binomial bound; risk strata still need coverage.

The MMLU-ProX-inspired stages are sensible. They do not inherit that project’s quality evidence or human-review investment.

### HIGH 6 — “Fully language-neutral” math scoring is an unsafe specification

**Evidence — proposal §3:** MATH-500 is described as “boxed-answer exact match,” using an existing Greek-format equivalence checker, and “fully language-neutral.” No checker or validation cases are supplied.

**Consequence — inference:** Decimal commas, coordinate separators, unordered solution sets, units, equivalent expressions, and textual answers can change apparent correctness.

**Concrete fix:** Validate the checker against the upstream scoring implementation on frozen responses, then add Greek-specific cases. Distinguish:

- Answer extraction.
- Formatting normalisation.
- Mathematical equivalence.

For example, `1,5` cannot be indiscriminately normalised: it might represent a decimal or two separate values. Preserve mathematical symbols and variable identity, but inspect language inside LaTeX text fields.

Also report results by source difficulty level. The proposal has not established that the complete 500-item set exclusively measures the “upper half” of the curriculum.

### MEDIUM 1 — The budget arithmetic is correct; the cost model is not established

**Evidence — calculation:**

- \(600+60+100+120=880\) calls.
- \(880/1000\times2.8\%=2.464\%\).

Thus “about 2.5%” is arithmetically consistent with the stated assumption.

However, the proposal contains approximately **386,000 source words**, with MultiChallenge contributing about **87%**. Counting short XSTest batches and long conversation jobs as equivalent calls is not a demonstrated resource model. Twenty-four workers affect throughput, not the amount of work.

**Concrete fix:** Measure representative pilot jobs and budget translation, self-check, independent checking, repair, retries, rubric translation, judge calibration, and evaluation separately. Record tokens, context lengths, elapsed time, and observed quota consumption by model.

“Minutes per arm” also needs a timed pilot with the intended hardware, output limits, and judge arrangement. It is not verified here.

### MEDIUM 2 — Adoption and literature claims overstate what the supplied evidence establishes

**Evidence — internal checks:**

- “No Greek instrument” is described as verified, while MultiIFEval-el is explicitly **uninspected**. That does not establish an alternative exists, but it prevents a categorical absence claim.
- HumanEval-XL’s stated dimensions are inconsistent: \(164\times12\times23=45,264\), not the appendix’s **22,080**. Reconcile the actual Greek configurations and task counts.
- GreekMMLU’s supplied public/private split sums correctly: **16,857 + 4,948 = 21,805**. That total is not automatically your accessible evaluation count.
- INCLUDE’s **552 test + 35 validation = 587** should not silently become a 587-item headline test.
- The approximately 41% MultiChallenge result lacks a model/version/date in the recommendation. It cannot establish the performance of current frontier models.
- Appendix A.3 combines language-specific translation audits, judge-prompt perturbations, and correlations with human preference. These do not jointly establish that all MT benchmarks fail or that binary judges are inherently reliable.

**Concrete fix:** Replace categorical claims with scoped statements, reconcile dataset manifests, and attach a primary-source evidence table giving the exact claim, study population, denominator, metric units, and relevant passage/table. In particular, resolve whether “0.18–0.32” denotes score fractions, percentage points, or another quantity.

## 3. What is good and should not be changed

- **The capability-first shortlist is sensible.** Conversation skills, instruction generalisation, and benign over-refusal align with the stated training work.
- **Adopting suitable existing Greek datasets is preferable to duplicating them.** Native lyceum mathematics and established Greek evaluations remain useful complements.
- **Keep English retention and Greek evaluation together.** They answer different questions about adaptation.
- **Preserve source IDs, mathematical notation, category-level reporting, and the training/evaluation separation.**
- **Keep independent checking and native review in the pipeline.** Strengthen their coverage and measurement.
- **Keep MATH-500 outside the initial three.** It contributes cross-language math evidence but does not close the conversation-skills gap.

These findings concern the proposal. Completed datasets should receive the requested notes and provenance qualifications.

## 4. Explicit answers to §5’s five questions

### Q1. Is the ranking right for the next conversation-skills arm?

**Provisionally yes: MultiChallenge → IFBench → XSTest; MATH-500 fourth.**

Change the execution order: conduct a **30–40-conversation MultiChallenge pilot first**, while scoping IFBench verifier work. If only one new benchmark is feasible, MultiChallenge is the best match, conditional on usable scoring and sufficient signal.

Promote XSTest above IFBench if the overlap audit leaves too little genuinely unseen constraint coverage.

Before translating another deterministic multi-turn suite, inspect MultiIFEval-el’s actual contents and access conditions. Its name alone neither proves suitability nor justifies dismissing it.

Two gaps remain outside this shortlist:

- XSTest does not comprehensively measure helpfulness under rudeness or absurdity.
- MultiChallenge’s self-coherence should not be assumed to measure accurate self-observation, identity, or resistance to sycophancy.

Those gaps are better served initially by a small, independently held-out native diagnostic tied to your training specification.

### Q2. MultiChallenge: subset, judge, faithful rubrics, and floor effects?

**Use a frozen subset for development comparisons; retain the full set as the eventual target.**

Using the proposal’s category counts, a proportional 150-conversation subset would contain:

| Category | Proposed subset |
|---|---:|
| Instruction retention | 38 |
| Inference memory | 62 |
| Versioned editing | 23 |
| Self-coherence | 27 |
| **Total** | **150** |

These are derived allocations, not verified upstream counts. Freeze selection before inspecting arm performance; include length and difficulty proxies in sampling.

At a 50% pass rate, ordinary binomial uncertainty is roughly **±8 percentage points for 150 items**, versus **±5.9 points for 273**. Small category samples are substantially noisier. Compare arms with paired, conversation-level uncertainty estimates; do not count correlated turns as independent observations.

For judging:

- Choose the frozen judge after human calibration, not by vendor preference.
- Blind candidate identity and training arm.
- Use a second model to audit disagreements and systematic errors.
- Preserve rubric obligations, negation, entity references, revision order, and target-turn scope through translation.
- Avoid rewarding persistence in an incorrect assertion when the intended skill requires accepting a correction.

For floor effects, compare the base model, current instruction-tuned model, and a stronger reference on the pilot. Include known passing and failing responses to diagnose scorer problems. Do not remove difficult items after observing arm results. If scores remain near zero, retain MultiChallenge as a challenge set and use a separately named, easier native diagnostic for development.

If the 150-item subset guides repeated decisions, preserve the remaining 123 conversations for a later confirmation. A subsequent full-set score would include development-exposed items.

### Q3. Which IFBench constraints fail to transfer, and what replaces them?

**I cannot identify the actual constraint IDs without the 58-constraint registry and verifier code.** Providing a supposedly audited list would be fabrication. The required transfer policy is:

| Constraint class to inspect | Greek issue | Treatment |
|---|---|---|
| English alphabet, pangrams, letter distributions | Different alphabet and feasibility | Preserve explicit literal-symbol tasks where appropriate; otherwise create a separately labelled Greek replacement |
| Case-insensitive lexical matching | `σ`/`ς`, accents, Unicode normalisation | Define permitted normalisation; use consistent matching |
| Exact-character or orthographic requirements | Normalisation can erase the tested distinction | Preserve distinctions required by the instruction |
| Capitalisation | Greek orthographic capitals differ from naïve character conversion | Specify and test the expected convention |
| Word/sentence counts | Greek `;`, abbreviations, apostrophes, hyphens, combining marks | Publish tokenisation and segmentation rules |
| English morphology, syllables, rhymes, dictionary ordering | Literal translation may destroy the requirement | Native redesign with feasibility checks; separate reporting |
| JSON, counts, required fields, fixed literals | Often transferable, subject to the wording | Preserve semantics and test the actual verifier |

**Reviewer-authored examples, not dataset rows:** `σ` and `ς` may need equivalence for keyword matching, while remaining distinct for an exact-letter task. Globally removing tonos would collapse distinctions such as `η` and `ή`. Greek sentence handling must account for `;`.

Every affected verifier needs positive, negative, boundary, and Unicode cases. A linguistically correct translation is insufficient if its checker accepts a violating response.

Report overlap using the classification in HIGH 1, with counts by constraint type and prompt. Publish both the faithful-core score and the verified-unseen subset score.

### Q4. Is native Greek over-refusal better than localised XSTest?

**Use both, with separate scores.**

A faithful source-aligned core supports cross-language comparison. A native extension captures Greek lexical ambiguity, idioms, register, and ordinary formulations that English-origin items may miss.

For each localised or native item, record:

- Intended benign or harmful meaning.
- Trigger and disambiguating context.
- Whether the Greek wording is natural.
- Human agreement on the label.
- Source relationship and reason for modification.

Distinguish safety refusal from uncertainty, inability, impossibility, and a correct explanation of a false premise. These distinctions matter especially for your absurd-user training track.

Report full refusal, partial refusal, and adequate compliance on safe items; evaluate unsafe items separately. Avoid a single pooled “safety” score that conceals the trade-off.

### Q5. Which existing Greek datasets need caution?

**None can be certified reliable or unreliable from this session’s source inspection, because source inspection was unavailable.** The adoption conditions should be:

| Candidate group | Required qualification |
|---|---|
| MT-Bench Greek / m-ArenaHard Greek | Pin prompts, baseline responses, judge version, generation settings, and aggregation. Published Krikri scores are comparable only under matching protocols. Identify human versus model post-editing explicitly. |
| MMLU-Pro Greek / Global-MMLU Greek | Treat MT quality as unvalidated until sampled; check answer preservation and difficulty by subject. Useful secondary evidence, not an unquestioned gold standard. |
| GreekMMLU / INCLUDE / Belebele | Prefer where capability coverage fits; report actual accessible test split and scored count. Native authorship or human translation does not establish uncontaminated evaluation. |
| Greek HLE | Verify access, licence, release, modality, and usable subset. A gated repository is not evidence of poor quality. For 8B, run a floor pilot before routine adoption. |
| Native lyceum / geometry | Check problem provenance, solutions, duplicates, and overlap with your training/CPT materials. Preserve their value as native mathematics measures. |
| AttaQ / StrongReject Greek | Validate the Greek scoring pipeline and translated intent. An English classifier or refusal detector is not automatically valid in Greek. |
| HumanEval-XL Greek | Resolve the count discrepancy, programming-language configurations, and executable tests. Existing Greek prompts do not establish equivalence to HumanEval+. |
| Culture and domain sets | Check actual cards and provenance. The reported erroneous culture-benchmark citation is a documentation concern, not proof that its rows are invalid. |

Replace the blanket licence statement with a per-dataset record covering the exact revision, upstream source, licence text, access restrictions, and intended use. Repository metadata alone should not settle all reuse questions.

For “Krikri-style” contamination, obtain the actual training-source manifests and compare item lineage. **Shared source families are not automatically leakage; shared evaluation items or derivatives are.** Published benchmark scores are not contamination certificates.

## 5. Open questions for the owner

1. What are the pinned benchmark revisions, complete IFBench registry, and definitions/examples for your 44 training families?
2. Does the intended MultiChallenge implementation reproduce the upstream generation and scoring protocol exactly?
3. Can you supply English-source IDs and Greek transformation lineage for SFT, CPT, and synthetic/native math additions?
4. What improvement must the next arm demonstrate, and which evaluation subset will remain untouched during selection?
5. How much native-review capacity is available, including a second reviewer for ambiguous safety labels and changed rubrics?
6. Which gated datasets are accessible, what use/distribution is intended, and what pilot evidence supports the quota and evaluation-time estimates?