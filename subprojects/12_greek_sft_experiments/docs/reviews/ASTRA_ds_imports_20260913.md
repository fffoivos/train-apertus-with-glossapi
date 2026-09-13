# Astra review: astra_ds_imports

Date 2026-09-13 10:39 · model gpt-6-astra (asserted from rollout rollout-2026-09-13T10-28-12-01a099aa-a301-79c0-8f9e-3060dfad4e29.jsonl) · effort xhigh · 11.0 min · prompt 140,750 chars · limit deltas {('codex', '10080'): 13.0} · brief `docs/reviews/briefs/astra_ds_imports.md` · sample 80 rows of `data/arms/R3_single/train.jsonl` seed 3

**1. Verdict**

**Change the next import mix; preserve completed R3 as an experimental record.** The sample supports concrete repairs to tool schemas, output contracts, premise handling and unsupported capability claims. It does **not** establish that any individual block earns its present allocation. The reported gains concentrate in Greek IFEval: R3 improves by 4.1 percentage points over arm B, while Greek MGSM declines by 3.6 points, GreekMMLU remains at 56% versus the base’s 57%, and unseen-constraint performance remains at 9.3%. Nemotron’s reported **44.6% of supervised tokens is insufficiently justified**; a substantial reduction deserves a controlled trial. Keep a smaller, validated retention mixture and spend the recovered budget on grounded Greek knowledge and difficult conversational behavior. I manually reviewed the supplied excerpt; execution and browsing tools were unavailable, so I could not inspect the original train file, reproduce evaluation results, or live-verify external sources. Public-source recommendations below are consequently provisional.

**2. Findings ranked by severity**

The sample contains **80 record starts, but only 77 complete records with identifiable configurations and IDs**. Three records are cut off: the painted-horse conversation, the juggling conversation and the movie/tool conversation. Of the 77 complete records, **66 belong to the imported blocks**; 11 are `personality`, `greek_if` or `greek_math`. Those 11 provide context but cannot establish defects in the imports.

All rates below describe this excerpt—not estimated corpus-wide failure rates.

**BLOCKER — The exported tool examples contain unusable function definitions. Establish whether this is an export defect or a training defect before further queued use.**

Among **five complete, identified `dolci_tooluse` rows, two contain truncated, unparsable function-definition payloads: 2/5, or 40%.**

- `olmo-toolu-sft-mix-T2-S2-f2-bfclv3-decontaminated_S2_909985`: the declaration of `agents_get_profile` ends inside its parameter definition. The assistant subsequently supplies `nrds_id` and `advertiser_id` despite lacking their usable declaration.
- `olmo-toolu-sft-mix-T2-S2-f2-bfclv3-decontaminated_T2_274958`: the review-function definition ends mid-description. The assistant passes an Amazon product identifier into a function described as retrieving Shein reviews, using `goods_id` without a usable supporting schema. It then repeats the product/review calls after receiving their results.
- The incomplete movie record has another broken schema and calls `watchmode.new_titles` without a visible declaration. Its ID is absent; **it is excluded from the 2/5 count**.

**Fix:** Compare these exports with the immutable raw rows. If clipping occurred only during export, repair the exporter and close that part of the finding without changing training data. Otherwise, quarantine affected rows and validate the entire queued block: schema parsing, function existence, argument types, identifier provenance, dependencies and result-to-call association.

Textual function calls are not inherently invalid. They become useful tool training only when their protocol matches deployment and their execution semantics are validated. All five complete examples encode results as `user` messages. If deployment uses actual tool roles and call IDs, convert and test the complete interaction—not merely the surrounding tags. Synthetic results may be fixtures; they are not evidence of successful real API execution.

**HIGH — Correct reasoning is being paired with incorrect output behavior.**

**Four of five `dolci_reasoning` rows violate the requested whole-response output contract under a strict machine-readable interpretation: 80%.**

- `minnonsubstring_diff_4_12_538423e82a_javIhj`: requests a single string; receives an explanation and `Answer: bb`.
- `differentiate_diff_3_46_e0b1c52e97_jSjHng`: requests a SymPy expression; receives prose and mathematical notation around the expression.
- `pipelinearrangement_diff_8_16_3c7cec6e84_ydG7qa`: requests a single permutation line; receives a lengthy derivation.
- `skarockgarden_diff_0_95_53d7e28827_JpEawj`: requests three characters with no separators; receives an enumeration and `Answer: 001`.

I do **not** count `stuwell_diff_5_35_797cfc7811_V07xRy` as a strict-format failure because its wording is less explicit.

The mathematical content is valuable: manual checks support all five answers. For example, the flow-shop sequence finishes at 83; the rectangle problem correctly admits both `001` and `100`.

**Fix:** Preserve these problems and their difficulty. Produce exact-format targets when requested, and separate explanatory variants under prompts that explicitly request explanations. Validate the complete assistant target, not an answer extracted from its final line. Include alternate valid solutions in mathematical validation.

**HIGH — One IFEval example has mutually incompatible instructions. Mechanical compliance checks must start with satisfiability.**

`ifeval_like` has **12 complete examples**.

- `65824` requires both no capital letters anywhere and a postscript starting with `P.S.`. Under literal case-sensitive matching, both cannot be satisfied. The target uses `p.s.`. This is **1/12 unsatisfiable prompts, or 8.3%**, not simply a careless assistant response.

Do not inflate this rate with ambiguous validator interpretations. For example, `50917` explicitly defines paragraph separation using `***`; its title alone does not prove a paragraph-count failure.

**Fix:** Repair the contradictory requirement—such as explicitly requiring lowercase `p.s.`—and run a satisfiability check before generation. After the guarded Greek polish pass, rerun all deterministic constraints because polishing can change case, punctuation, counts and delimiters.

**HIGH — Some targets teach the model to supply an answer despite defective or insufficient premises.**

Across **18 `openmath_gsm` examples**, I found no demonstrated arithmetic error *given the interpretation used by each answer*. That is different from having 18 sound question–answer pairs.

- `2786602`: the prompt says the remaining caterpillars “become caterpillars.” The answer silently changes that to butterflies and returns 72. **One clear contradictory-premise repair: 1/18, or 5.6%.**
- `2944737`: the school mean cannot be uniquely calculated without grade sizes. The answer explicitly assumes equal sizes, which is better than hiding the assumption, but concludes with an unconditional 93. **One additional assumption-dependent target: 1/18.** Grade sizes of 10, 20 and 10 would instead give 93.5.
- `2247265`: “600 miles, back and forth” can mean 600 total miles or 600 each way. The target chooses the latter. Those interpretations produce 22 and 52 additional gallons respectively. This is an ambiguity flag, **not a proven wrong answer**.

Related task-fidelity problems appear in **two of eight `greek_ours` examples**:

- `everyday:everyday_3a871516`: asked whether an application serves the user’s area, the assistant says «Άνοιξε την εφαρμογή ταξί…» without knowing the area or naming an application. It avoids the missing information rather than resolving it.
- `no_robots:a1deeeafaf6329bebbca08655509e78ad3da776272dcd4b37eb5d0bb59a18179`: a paragraph rewrite adds a sales pitch, including «γιατί να μη δείτε πόσο βαθιά φτάνει η λαγότρυπα…». That changes the requested transformation.

**Fix:** Repair source defects explicitly and record the changes. For ambiguous problems, create separately labelled, unambiguous variants. Also retain adversarial variants whose correct answer identifies insufficient information or a contradiction. For the taxi example, ask for the city/area. For the rewrite, preserve the supplied facts and remove the added promotion.

This addresses the reported premise-handling weakness directly; merely producing more polished explanations would not.

**HIGH — Imported self-description is insufficiently grounded in the deployment.**

Of **five complete, identified Nemotron conversations, two contain deployment-dependent capability claims**:

- `26840`: “No database of past chats,” followed by the claim that the conversation gets “shredded.” The row supplies no deployment policy supporting these storage/deletion assurances.
- `184544`: “I cannot generate images directly.” That may be correct for a bare text model and wrong for a tool-enabled assistant.

These are **2/5 contextualization flags**, not proof that both statements are false in the intended product.

**Fix:** Remove unconditional storage, deletion and capability claims from queued generic chat targets. Condition them on explicit system-provided capabilities and verified product policy. A request to forget something also needs an appropriate action or limitation statement, rather than unsupported reassurance.

The excerpt does **not** verify the reported 2.1% capitulation rate. In `26840`, “You’re right to pull on that thread” acknowledges a reasonable distinction; it is not evidence of accepting a false correction. A phrase detector must not silently become a sycophancy filter.

**HIGH — Stop extending the present token allocation without a contribution test.**

The **44.6% Nemotron token share and 14% Greek share are owner-reported figures**, not independently reproduced here. “Latin-script 84%” must not be relabelled “English 84%”: it includes other languages and potentially Greeklish.

All **five identified Nemotron conversations use Markdown somewhere**. That establishes a stylistic feature of this sample, not five instruction violations or proof that Nemotron caused Greek Markdown habits.

Nevertheless, almost half the supervised token budget is a substantial allocation without block-level evidence. Retention above the base does not establish that this dose is necessary, especially when retention is also described as flat against the incumbent.

**Fix for queued planning:** Stop allocating additional bulk generation at the present share. Use **20% of supervised tokens as an initial Nemotron cap in a candidate mix**, with a 10% arm if affordable. These are experimental doses, not established optima. First test a reduction with matched non-Nemotron English coverage; separately test reallocating tokens to Greek. Otherwise, a single intervention confounds source, language, length and task changes.

Completed R3 remains unchanged.

**MEDIUM — Several IFEval examples reward superficial completion rather than useful instruction following.**

Concrete examples among the 12 rows:

- `20181` appends `[address] [name]` to public-speaking advice without a useful role for either placeholder.
- `32502` literally inserts `*highlighted section*` twice.
- `33041` responds to a constraint-only request by describing compliance with the constraints.
- `76094` includes a ready-written VPN answer inside the user message. The assistant preserves both supplied paragraphs and adds placeholder sentences. That is one answer-bearing prompt, **not demonstrated benchmark contamination**.

These are distinct problems, so I would not combine them into one objective “failure rate.”

**Fix:** Make placeholders meaningful, remove accidental template echoes, and distinguish transformation tasks from question answering. Downsample repetitive, low-content constraint templates. Expand constraint families and combinations only after checking the identical 9.3% IFBench-el results for possible harness limitations or rounding.

**MEDIUM — Content validation is weaker than format validation, including in apparently benign imports.**

- `ifeval_like:31188` recommends cooking ground-beef patties for 3–4 minutes per side “for medium doneness,” with no measured safety endpoint. Replace this with a verified thermometer-based instruction before reuse; elapsed time alone depends on thickness and heat. The official [FoodSafety.gov temperature chart](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures) is the appropriate verification source, but I could not open it in this session.
- `nemotron_chat_a:39501` presents *Sima* as a local Mallorcan drink and describes Palo using wormwood. Both warrant primary-source checks. **I do not count them as verified factual errors here.**
- `dolci_code_algo_20k`, ID ending `116214`, uses trial division up to approximately √n despite a request to handle large integers efficiently. Without an input bound, performance adequacy is unestablished. Specify the range and test its boundary.
- Outside the imports, `personality:F02_00` says «Η επίσημη θέση μας…». That assigns the assistant an unrequested national position. Use «Η επίσημη ελληνική θέση…» and independently source the legal claims and precise geographical figures.
- Also outside the imports, `greek_if:mixa_2026_05581` changes permission for 20 umbrellas into an instruction to have «ακριβώς 20». Preserve the upper bound: «να μην ξεπερνούν τις 20».

These last two are notes on their respective blocks, not evidence against an import source.

**3. What is good and should not be changed**

- **Preserve the reasoning difficulty.** The five reasoning answers checked are mathematically sound. Repair their output format rather than removing them.
- **Preserve accurate mathematical supervision.** The 18 English examples generally calculate correctly; all four contextual `greek_math` examples also calculate correctly. Target premise defects rather than discarding mathematics wholesale.
- **Preserve contradiction detection.** `greek_ours:apertus_en:apertus_en_685ee677` correctly identifies incompatible scheduling conditions and the impossibility of assigning 12 distinct ratings from five values. This is precisely the behavior missing elsewhere.
- **Preserve benign interpretation of alarming language.** `dolci_safety:wildjailbreak_24847` answers “poison the tree of self-doubt” helpfully instead of refusing on a keyword.
- **Preserve faithful, concise Greek transformations.** `greek_rewrite:gr_rw_01051` retains the event and allergy information within the requested character limit.
- **Preserve actual constraint success.** `greek_ours:personas_if:personas_if_1757a77b` supplies four sentences, one `ΧΕΡΙΑ` and two `ΛΟΙΜΩΞΗ` occurrences.
- **Preserve multilingual competence where required.** The six SmolTalk examples comprise three Spanish, one German, one Italian and one French response, matching their prompts. Spanish itself is not a defect. None of these is evidence about Spanish OASST: **there are zero `dolci_chat` examples in the identifiable sample.**
- **Do not globally remove Markdown, explanations or acknowledgments.** Their appropriateness depends on the request. Removing them indiscriminately would damage legitimate tasks.

**4. Answers to the specific questions**

**Which blocks earn their share, and which should shrink or go?**

No individual block has demonstrated marginal benefit in the supplied evidence. The defensible distinction is between plausible retention coverage and demonstrated necessity at the current dose.

| Block | Complete sampled rows | Recommended disposition for the next mix |
|---|---:|---|
| `dolci_precise_if` | 0 | Retain provisionally as constraint coverage; validate before attributing value. |
| `ifeval_like` | 12 | Repair contradictions; shrink repetitive and low-content templates. |
| `openmath_gsm` | 18 | Keep mathematical coverage; reduce easy/redundant problem families and repair premises. Do not delete wholesale. |
| `nemotron_chat_a+b` | 5 | Substantially reduce in controlled trials; repair unsupported self-description. |
| `dolci_chat` | 0 | Test omission from the candidate mix. Permanent removal depends on Spanish retention; no sample evidence establishes poor quality. |
| `dolci_code_algo` / sampled `_20k` | 3 | Keep a tested code-retention allocation. Establish the config mapping and input bounds. |
| `dolci_reasoning` | 5 | Keep after exact-format repair. Strongest directly inspected argument for preserving challenging content. |
| `puzzles` | 2 | Both sorting answers are correct. Cap repetitive templates after a family census; preserve distinct skills. |
| `dolci_tooluse` | 5 | Admit only validated rows in the deployment protocol. If tool use is outside product scope, test removing this allocation. |
| `dolci_science` | 0 | Keep provisionally for subject coverage; require a stratified audit. |
| `smoltalk2_multilingual` | 6 | Size against explicit language-retention requirements; reduce redundancy with other chat imports. |
| `dolci_safety` | 1 | Keep coverage; expand useful answers to safe but alarming requests. |
| `greek_rewrite` | 1 | Keep; expand with strict factual and editing fidelity. |
| `greek_ours` ×2 | 8 | Repair and sample by capability/source family. Replace unconditional doubling with fresh Greek coverage while preserving the Greek token allocation. |

The brief’s imported counts sum to **347,116 weighted row exposures**, treating `greek_ours` as doubled. That differs from the 403,727-row final file, plausibly because final-R3 additions are included. A manifest should reconcile this rather than treating the final-file sample as a sample exclusively of imports.

**What is missing for GreekMMLU-style knowledge?**

The excerpt contains elementary arithmetic, chat, formatting and narrow algorithms, but **no identifiable example of the proposed Greek subject-balanced multiple-choice knowledge set**. This does not prove that none exists elsewhere in the full file.

Build that set from two complementary sources:

1. **Verified general-domain educational questions:** candidate training splits from [AI2 ARC](https://huggingface.co/datasets/allenai/ai2_arc), [OpenBookQA](https://huggingface.co/datasets/allenai/openbookqa) and [SciQ](https://huggingface.co/datasets/allenai/sciq). These provide source-grounded science coverage; they do not cover the full humanities, social-science and Greek-context requirement.
2. **Native Greek educational material:** [official schoolbooks](https://ebooks.edu.gr/) and [Kallipos academic textbooks](https://repository.kallipos.gr/), subject to item-level rights and provenance checks. Construct questions from identified passages with independently checked answers and plausible distractors.

Greek exam banks are attractive but potentially dangerous for evaluation validity: establish whether GreekMMLU already draws from them before admitting any items. A different wording or translation is not sufficient separation.

Each item should retain:

- Original source and item identifiers, passage/page locator, document hash, date, rights information and subject.
- Canonical answer index, distractor justification and any ambiguity findings.
- Original/adapted/polished versions linked to the same item family.
- A decontamination receipt and split assignment.

Use two explicit response modes: **answer-only** and **answer plus a short explanation**. Match the requested label alphabet and output syntax exactly. Store the canonical index independently of rendered labels. Check option permutations where valid; items containing positional options such as “all of the above” require special handling.

**Required item-level decontamination**

Freeze the actual GreekMMLU version and every evaluation set used for acceptance. Then:

1. Match original source IDs and source question families.
2. Match normalized stems and options, including option-order-independent comparisons.
3. Retrieve paraphrases, translations and numerical/template variants using lexical and cross-language methods.
4. Adjudicate candidate overlaps using source evidence and human review; model similarity scores are flags, not ground truth.
5. Keep all translations and adaptations of an item in one split.
6. Publish removals and repairs by subject, difficulty and source.

Include original GSM8K/MGSM and MATH evaluation families in this audit. Strings such as `decontaminated` in row IDs do not demonstrate decontamination against these particular Greek evaluations. Avoid deleting entire subjects merely because they overlap conceptually with a benchmark.

Also diagnose the flat GreekMMLU result before assuming that more MCQs solve it. On a **fresh held-out set**, compare Greek versus English presentation, closed-book versus supplied evidence, and forced-choice versus generated-answer scoring. Those contrasts help distinguish knowledge, language comprehension, retrieval and formatting limitations.

**Which public resources would I add for Greek-context competence?**

These are primary-source starting points, **not sources whose current cards, licenses or contents I verified during this session**.

| Resource | Intended use |
|---|---|
| [MITOS](https://mitos.gov.gr/) and [gov.gr](https://www.gov.gr/) | New Greek procedural QA: prerequisites, missing information, jurisdiction, deadlines and exceptions. Store dated evidence. |
| [ELSTAT](https://www.statistics.gr/) | Grounded table reading, percentages, denominators, regional comparisons and uncertainty. |
| Greek schoolbooks and Kallipos, above | Native subject knowledge across sciences and humanities. |
| [EUR-Lex](https://eur-lex.europa.eu/) Greek texts | Evidence-bound civic/legal comprehension, clearly tied to the relevant document and date. These are source materials, not ready-made QA targets. |
| [Aya Dataset](https://huggingface.co/datasets/CohereForAI/aya_dataset) | Candidate human-authored instruction examples; inspect actual Greek coverage and source overlap before selecting. |
| [Belebele](https://huggingface.co/datasets/facebook/belebele) | Prefer as a held-out multilingual reading diagnostic; keep it out of training if used for evaluation. |
| [xLAM function-calling data](https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k) | Candidate tool-data alternative if tools matter; apply the same schema and execution gates. Public provenance does not establish correctness. |

`greek_ours` already contains `no_robots` adaptations. Adding that source again without original-ID deduplication would not constitute fresh coverage.

**Which new sets should be invented?**

Prioritize four small, verifiable sets over another large generic chat import:

- **Greek correction and uncertainty dialogues:** paired true/false user corrections, missing premises, contradictory requests and warranted disagreement. Gold answers come from sources or calculation.
- **Greek version editing and conversational memory:** multiple revisions with exact final-state checks, protected text spans, cancelled changes, stop instructions and explicit prevention of obsolete tail copying.
- **Greek practical-context tasks:** administrative processes, education, geography, cultural references and everyday services—with dates, jurisdiction and clarification when necessary.
- **Helpful responses to alarming but safe requests:** measure whether the answer actually helps, not only whether it avoids refusal. Use fresh scenarios rather than translating the held-out XSTest items into training.

The Greek polish pass must preserve numbers, answer keys, uncertainty, source meaning and task constraints. Any substantive repair needs its own logged change.

**Acceptance checks and the A/B read-out**

Before admitting queued data:

- Zero malformed schemas or undefined calls in tool targets; validated dependency and identifier handling.
- Zero known unsatisfiable prompts; all applicable deterministic output checks pass after polish.
- Every knowledge target has inspectable supporting evidence and a resolved answer key.
- Every repair/filter reports its effect on difficulty, subject, language, length and source-family diversity.
- Human audits sample the difficult and long examples as well as the easy ones. Model annotations remain visible; a weaker model must not become the authority over a stronger generator.
- Report actual **loss-bearing assistant tokens** by block and language, including repetitions and packing/truncation effects.

Use the same starting checkpoint, supervised-token budget, optimization schedule and evaluation harness:

| Comparison | What it isolates |
|---|---|
| Original mixture vs mandatory repairs at original weights | Effect of demonstrated data defects. |
| Repaired original weights vs reduced Nemotron, with matched English replacement | Effect of Nemotron allocation. |
| Reduced Nemotron mix vs additional Greek allocation | Effect of language/task reallocation. |
| Greek allocation without vs with grounded knowledge MCQs, token matched | Incremental knowledge-set benefit. |
| Targeted block omissions with replacement tokens | Retention necessity of that block; grouped omissions support only group-level claims. |

Use multiple training seeds where feasible and paired item-level uncertainty estimates. Do not select winners from rounded aggregate scores.

I would preregister these decision rules:

- **Shrinking a block succeeds** if it preserves relevant retention within a declared noninferiority margin and improves the targeted behavior or frees budget for a demonstrated gain.
- **The knowledge addition succeeds** if GreekMMLU improves beyond uncertainty, exceeds the base, and improves a fresh source-disjoint knowledge test. A reasonable initial engineering target is **at least +2 percentage points over 56%**, not a claim that this effect is guaranteed.
- **The conversational addition succeeds** through better exact editing/memory outcomes and fewer incorrect concessions—not fewer occurrences of acknowledgment phrases.
- Preserve Greek IFEval gains, report IFBench-el generalization separately, and explicitly track the **3.6-point MGSM deficit to arm B** and **4.8-point MATH-500-el deficit to stage 1**.
- Retention needs per-task results and confidence intervals. If the evaluation is too small to establish the chosen margin, “not statistically significant” is not a pass.

**5. Open questions for the owner**

1. Which import blocks are completed, queued for further generation, or merely queued for reuse? The proposed generation controls apply only to queued work.
2. Were the three incomplete records and truncated function declarations caused by the sample exporter? What do the raw identified rows contain?
3. What are the exact per-block supervised-token counts, unique source-family counts, loss masks and repetition weights? What denominator produced 44.6%?
4. Which nine tasks establish retention, against which comparator, and are their raw results consistent with “above base” and “flat”?
5. Which exact GreekMMLU release and source families were excluded? Are there item-level receipts covering translations and source-ID overlap?
6. Are the identical 9.3% IFBench-el and 56% GreekMMLU figures rounded results, or do the underlying predictions also coincide? How are answers extracted and scored?
7. What tool protocol, memory policy and image capabilities will the deployed assistant actually have?
8. What proportion of existing removals came from judge labels, and how did those removals change difficulty and subject coverage?