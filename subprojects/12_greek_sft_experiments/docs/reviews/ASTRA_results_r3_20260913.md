# Astra review: results_r3

Date 2026-09-13 11:30 · model gpt-6-astra (asserted from rollout rollout-2026-09-13T11-23-21-01a099dd-248f-7813-9ca2-131d57dbf6be.jsonl) · effort xhigh · 7.2 min · prompt 34,791 chars · limit deltas {('codex', '10080'): 8.0} · brief `docs/reviews/briefs/astra_results_r3.md`

**1. Verdict.** R3 is a trade-off, not an overall improvement over arm B. Greek IFEval improves substantially, and the mixed-profile dialogue results suggest better request handling, coherence and tone. However, greedy Greek-math loops and truncations worsen sharply, hard-math performance remains below stage 1, and correction-handling conclusions change with the judge and test protocol. **I would retain arm B as the general-use incumbent today.** R3_pass is the strongest candidate for an instruction-following and dialogue-focused replacement; R3_passB is the more conservative candidate on easy math and stop instructions. Neither is ready for unconditional promotion. Against competitors, the strongest result is competitive Greek IFEval; the largest deficits are mathematics and dialogue reliability relative to Krikri. R4 should repair and isolate those deficits before expanding data generation. Completed R3 datasets and runs should receive notes and remain preserved as experimental evidence.

**2. Findings ranked by severity.**

Evidence boundary: I can check the supplied tables, their arithmetic and their internal consistency. No dataset rows, full transcripts, item-level predictions or scoring code are attached. Consequently, **there are no independently verifiable row IDs or sample-row failure rates to report**. Counts below are supplied aggregate counts or explicitly identified calculations from them. The Greek quotations are excerpts reported in the brief, not independently inspected rows.

- **BLOCKER — The evidence does not support an unconditional promotion or a settled causal diagnosis.** Interview follow-ups differ between models; correction rankings differ between interviews and picky-user runs; the pass-dialogue subsection says “Hostile” while its table says “mixed”; and the pass checkpoints lack the reported XSTest/MultiChallenge and retention coverage available for B/R3. These limitations directly affect which checkpoint appears preferable.  
  **Fix before promotion:** freeze a small, identical-input comparison of B, R3 and both passes, with run identities hidden, item IDs, complete outputs, termination metadata and explicit denominators. Resolve the profile-label inconsistency from the run configurations. Reuse existing generations wherever possible. Before R4 bulk generation, distinguish supported defects from hypotheses in the plan.

- **HIGH — Greek hard-math regression is established against stage 1; its attribution to terse targets is not established.** Under greedy **MATH-500-el equiv500**, stage 1 solves **64/500**, R3 **40/500**, and B **38/500**. R3 loses 49 previously correct items and gains 25; **42/49 losses are completed wrong answers**. B loses 46 and gains 20; **45/46 losses are completed wrong answers**, despite not seeing the new math set.  
  **Fix:** replace queued terse math targets with independently checked worked solutions, preserve final-answer conventions, and include explicit Greek/English math retention in the finishing stage. Label this a testable repair, not a confirmed cure. Audit extraction first.

- **HIGH — The correcting set is poorly aligned with the intended skill, but “14:1 correcting set caused capitulation” overstates the evidence.** The supplied counts imply **272 acknowledgement/recovery turns versus 20 false-correction holds: 13.6:1**. TRUE-correction acceptance alone is **114:20 = 5.7:1**. Moreover, the listed categories total approximately **3,822**, exceeding the stated **3,692 supervised turns by 130** if they are exclusive. Overlap may explain this, but it must be documented.  
  **Fix before further generation:** reconcile the turn taxonomy and count *correction opportunities* separately from ordinary turns and closings. Build independently verified true/false/partly-true correction episodes with balanced coverage within that targeted subset. Do not make the whole assistant more argumentative. Keep suite inclusion fixed when testing the correcting set.

- **HIGH — Neither finishing pass repairs the greedy termination regression.** On Greek MATH-500, loops are **7/500 for B**, **35/500 for R3**, **31/500 for R3_pass**, and **40/500 for R3_passB**: **1.4%, 7.0%, 6.2%, 8.0%**. Truncations are **29, 96, 75, 75 of 500**: **5.8%, 19.2%, 15.0%, 15.0%**. The historical pass actually increases the reported loop count relative to R3.  
  **Fix:** make greedy loop/truncation counts explicit promotion gates, complete the missing large masking audit, and test decoding separately from supervision. Keep semantic stop requests, EOS supervision, cross-turn tail copying and within-answer loops as distinct failure classes.

- **HIGH — Several metrics need repair or adjudication before they can drive data allocation.** IFBench’s Greek word-family checkers remain unaudited; XSTest’s absolute safety rates depend strongly on the judge; English MATH extraction demonstrably penalizes Apertus-Instruct; and pooled premise scores use an unspecified broader denominator.  
  **Fix:** apply the inexpensive checks in §4(d) before generating large benchmark-targeted datasets. In particular, do not train to satisfy an unvalidated Greek word checker or a single judge’s disputed refusal labels.

- **MEDIUM — Some narrative conclusions are stronger than their tables.** “Ahead of Apertus-Instruct and Meltemi everywhere” is false: R3_pass has worse staleness (**62.9% vs 50.5%/52.3%**), lower premise scores (**0.42 vs 0.71/0.60**), and worse stop handling than Apertus (**91.7% vs 95.2%**). “No tail copies” for Krikri should be **0.7%**. Rising personality holdout loss is consistent with overfitting but does not establish that mechanism.  
  **Fix:** correct the narrative, define every noise band, and publish a single current table with protocol, sample size, scorer version and missing cells.

**3. What is good and should not be changed.**

- **Keep the historical-pass control.** R3_passB materially improves interpretation. It is valuable even though it does not isolate scheduling alone.
- **Keep the corrected mixed-profile baseline and both judges’ results.** The corrections expose uncertainty that would otherwise produce a misleading success story.
- **Preserve the Greek IF capability.** R3_pass reaches **71.6 strict average**, compared with B’s **63.7**, under the corrected language-detection protocol. Wholesale removal of compliant Greek instruction data would be unjustified.
- **Keep paired failure accounting and bilingual math diagnostics.** The lost/gained-item partition shows why “it is all loops” fails. The Greek/English distinction is also informative.
- **Keep broad replay and retention checks.** R3/B’s native-suite and cached retention results provide useful evidence against a broad collapse. They do not replace targeted math and dialogue checks.
- **Preserve completed artifacts, holdouts and raw outputs.** Fix queued recipes and annotate completed datasets rather than rewriting the evidence underlying this round.

**4. Answers to the brief.**

**(a) Improvement, regression and promotion**

The principal measured comparisons are:

| Protocol | Arm B | R3 | R3_pass | R3_passB |
|---|---:|---:|---:|---:|
| Greek IFEval, strict prompt/instruction average | 63.7 | 67.8 **(+4.1 pp)** | 71.6 **(+7.9 pp)** | 68.5 **(+4.8 pp)** |
| Greek MGSM | 52.4% | 48.8% **(−3.6 pp)** | 48.4% **(−4.0 pp)** | 53.2% **(+0.8 pp)** |
| Greek MATH-500, greedy equiv500 | 7.6% | 8.0% **(+0.4 pp)** | 10.0% **(+2.4 pp)** | 11.2% **(+3.6 pp)** |
| Greek MATH-500, loops | 7/500 | 35/500 | 31/500 | 40/500 |
| Greek MATH-500, truncations at 2,048 tokens | 29/500 | 96/500 | 75/500 | 75/500 |

Parentheses are differences against B.

**Effects supported beyond the stated noise, or by substantial counted failures:**

- The IFEval gains exceed the stated **±2-point** band, especially R3_pass’s **+7.9**. However, the document does not define whether that band describes a score or a paired difference, or its confidence level. Treat the gain as convincing task-specific evidence, not a formally established universal IF improvement.
- The greedy loop/truncation regression is substantial and survives both passes.
- The hard-math decline against **stage 1**, rather than B, has unusually useful paired evidence. From the reported loss/gain counts, approximate item-paired 95% intervals for accuracy changes are **R3: −4.8 pp, approximately [−8.1, −1.5]**; **B: −5.2 pp, approximately [−8.4, −2.0]**. These calculations assume the partitions are correct and benchmark items are independent; they do not establish causality.
- MGSM’s **−3.6/−4.0 pp** for R3/augmented pass warrants concern, but the quoted **±3 pp** band is insufficiently defined to declare a reliable difference. PassB’s **+0.8 pp** is parity, not demonstrated improvement.
- The passes’ MATH gains over B need paired correctness tables before being called reliable recoveries. Both remain below stage 1’s **12.8%**.

**Judge-dependent effects:**

- **MultiChallenge-el, 262 conversations:** Sol gives **R3 16.0%, B 18.7%**; Opus gives **13.4%, 11.8%**. The order reverses. The rounded rates correspond to **42 versus 49 passes** under Sol and **35 versus 31** under Opus. With the stated **±2.5-point** band, neither ranking is a sound selection criterion.
- **Adaptive interviews:** coherence falls from B to R3 under both judges, but by different amounts: **2.85→2.67 with Sol**, approximately **2.62→2.25 with Opus**. False-correction resistance is essentially tied under Sol (**2.83 versus 2.80**) but lower for R3 under Opus (**2.92 versus 2.67**).
- Sol gives R3_pass the highest interview correction score, **3.08**, versus **2.75** for PassB. The picky-user false-claim cells favor PassB instead. These tests do not establish a common correction-handling ranking.
- **XSTest-el:** R3/B are close under Sol: safe adequacy **76.4/77.2**, unsafe refusal **88.0/89.0**. Opus gives unsafe refusal **96.0/96.5**. The between-model difference is small; the absolute safety conclusion changes materially with the judge.

**Protocol-dependent effects:**

Under the reported **mixed profile, Sol user and judge, T=0.8**, R3 improves over B on coherence **85.9% versus 78.6%**, request honouring **59.7% versus 45.2%**, and staleness **67.0% versus 74.2%**. R3_pass improves these further to **89.9%, 68.7%, 62.9%**.

These are promising results, but the comparison uses **60 versus 120 dialogues**, adaptive trajectories and uneven move opportunities. Its effective sample size is not 808 independent turns. For example, the reported dead-dialogue percentages correspond to approximately **4/60 for R3 versus 10/120 for B**, and **2/60 and 3/60** for the passes.

The earlier hostile-only B run is not a valid comparator. The contradictory hostile/mixed headings prevent claiming a separate hostile-profile recovery from the supplied material.

**Promotion:** retain B for general use. Advance R3_pass to targeted validation if the intended product prioritizes ordinary instruction following and conversational responsiveness. Keep PassB as a competing candidate because it restores MGSM to B’s level and reports **100%** stop-request handling. Do not combine the best cells from the two passes into an imaginary single winner.

Native-suite macro **0.516 versus 0.514** and clean GreekMMLU **0.5612 versus 0.5609** are effectively flat. R3’s cached retention scores being at or above the CPT reference supports preservation on that particular suite; it does not establish retention for the unevaluated passes.

**(b) Competition and return on data effort**

Using the **rescored Greek IFEval**, **Greek MGSM**, and **same-runner greedy Greek MATH-500** protocols:

| Peer | IFEval: R3_pass minus peer | MGSM: R3_pass / PassB minus peer | MATH-el: R3_pass / PassB minus peer |
|---|---:|---:|---:|
| Krikri-8B | **+1.8 pp** | **−19.2 / −14.4 pp** | **−22.2 / −21.0 pp** |
| Meltemi-7B | **+37.8 pp** | **+27.6 / +32.4 pp** | **+1.6 / +2.8 pp** |
| Apertus-8B-Instruct | **+12.4 pp** | **−4.8 / 0.0 pp** | **−2.2 / −1.0 pp** |
| Qwen3.5-9B, thinking off | **−1.5 pp** | **−39.2 / −34.4 pp** | **−68.8 / −67.6 pp** |
| Gemma-3-12B | **−4.1 pp** | **−42.4 / −37.6 pp** | Pending |

These are descriptive gaps, not significance claims. In particular, **+1.8 over Krikri and −1.5 behind Qwen on IFEval are within the quoted ±2-point scale**. The large IFEval advantages over Apertus and Meltemi are much more convincing.

For **mixed-profile dialogues**, R3_pass trails Krikri by:

- **5.5 pp** in coherence: **89.9 versus 95.4**.
- **5.2 pp** in requests honoured: **68.7 versus 73.9**.
- **7.6 pp** more tail copying: **8.3 versus 0.7**.
- **3.1 pp** more staleness: **62.9 versus 59.8**.
- **8.3 pp** in stop handling: **91.7 versus 100**.

Krikri is therefore a useful 8B dialogue reference, although its **0.21 premise score** is not a behavior to copy indiscriminately.

Qwen’s **99.5% coherence** coexists with **14.2% requests honoured** and **13.3% stop handling**. That combination deserves transcript inspection; coherence alone cannot establish that it is the better assistant under this protocol.

On **Sol-judged MultiChallenge**, Qwen’s **24.8%** is descriptively **6.1 pp above B** and **8.8 pp above R3**. B, Krikri and R3 are too close and judge-sensitive for a defensible ordering. There are no pass results.

On **Sol-judged XSTest**, B/R3 have the highest listed safe adequacy, **77.2/76.4**, compared with Qwen **71.6**, Krikri **70.8**, Apertus **69.6**, and Meltemi **60.8**. Krikri has higher unsafe refusal, **93.0 versus B’s 89.0 and R3’s 88.0**. This suggests a helpfulness/refusal trade-off, subject to adjudication.

My ranking by expected return per unit of data effort is:

1. **Recover demonstrated math capability and prevent finishing-stage erosion.** Stage 1’s **12.8% Greek MATH** and R3’s **18.0% English MATH** already exist within this lineage. Recovery is a more defensible immediate target than catching Qwen.
2. **Eliminate tail copying and improve redirect/stop handling.** These are narrow, repeatedly measured failures with a strong 8B reference.
3. **Teach discriminative correction handling.** Few carefully verified contrastive episodes may be more useful than thousands of generic acknowledgements. Its exact priority depends on the fixed-probe result.
4. **Broaden IF beyond familiar constraint types.** Preserve IFEval gains, but audit IFBench before targeting its word-family failures.
5. **Expand genuinely harder mathematical coverage, including Level 5.** This is worthwhile but costlier and less certain than retention repair.

Krikri’s **32.2% MATH-el at 8B** shows that parameter count alone does not explain our result. Conversely, Qwen’s **78.8%** does not show that its entire advantage is cheaply closable through SFT. The tables confound base training, architecture and post-training. Call this a **capability gap of unresolved origin**, not a proven 8B capacity ceiling or a promised SFT fix.

**(c) Challenge to the four diagnoses**

| Diagnosis | Evidence assessment and alternative | Single discriminating test |
|---|---|---|
| **Terse Greek math targets caused the reversal** | Strong evidence of style transfer: median **35 words**, **343/500 unboxed**, versus B’s **86 words and 68 unboxed**; reported training solutions average about **42 words**. Insufficient evidence that brevity caused wrong reasoning. Alternatives include restricted difficulty coverage, the blind-solve selection filter, changed exposure and interference from other new data. B’s length-neutral regression proves a separate mechanism exists. | Matched training ablation using the **same math problem IDs and correct answers**, varying terse versus worked targets while fixing other data and finishing treatment. Predeclare exposure controls and report both example counts and supervised tokens. Score bilingual held-out correctness with audited extraction. |
| **The 14:1 correcting set caused false agreement** | Plausible coverage problem, not causal proof. R3_pass adds both suite and correcting data and about **16.2% more pass rows**. Premise-only scores are **1.17 B, 0.80 R3, 0.83 pass, 1.00 PassB**. False-claim cells have only **9–22 turns**, while adaptive Sol interviews favor the augmented pass. | Hold suite, other data and training budget fixed; compare the original correcting subset with verified true/false/partial correction coverage. Evaluate identical factual minimal pairs using answer keys and blind adjudication. |
| **Greedy decoding causes the loops** | It clearly exposes a failure, but comparison with sampled picky-user dialogues changes **task, context, temperature and loop definition** simultaneously. “Line ×5” and “sentence ×3” are not interchangeable. No repeated-line training targets does not exclude other data-induced looping mechanisms. | Generate the **same Greek math items and histories** under greedy and T=0.8, using the same cap and detector, with several sampling seeds. Compare accuracy, loops and truncation jointly. |
| **Tail copying and stops reflect the same termination defect** | Not established. Cross-turn copying, failure to obey “stop,” EOS errors and within-answer recurrence can have different causes. The 50-prompt format gate differs by only **one or two prompts**; that does not clear token masking. The large **1,831-row** masking audit’s outcome is absent. | A fixed scripted dialogue panel separating redirects, stop requests and normal continuation, logging emitted EOS, finish reason and copied spans. First inspect a blind sample of detected copies for legitimate repetition. Complete the masking audit as an implementation check. |

The quoted outputs **«Σωστά, το διορθώνω»**, **«Σωστό:»**, and **«το παστίτσιο δεν έχει μπεσαμέλ»** support a plausible false-agreement failure shape *as reported*. Without their complete histories and row IDs, they cannot establish prevalence or source attribution.

**(d) Evaluation validity: what not to trust and the cheapest fix**

| Number or claim | Current limitation | Cheapest adequate fix |
|---|---|---|
| **IFBench-el overall ranking** | Words-family pass rate is **3.8% Greek versus 20.3% English**, pooled across four models. This may reflect checker/translation defects, genuine difficulty, or both. | Hand-author positive and negative cases for each Greek word checker; audit Unicode, accents, case, token boundaries and translated constraints. Rescore saved outputs. |
| **IFBench zero families imply broken evaluation** | That inference is unsupported. Custom checkers reportedly accept constructed answers. Repeat has only **9 underlying rows**; excluding it shifts scores by **≤0.3 pp**. | Preserve the families provisionally; check the empty-kwargs row and publish unique-item counts separately from pooled model-item counts. |
| **MultiChallenge ordering among B/R3/Krikri** | Small gaps, order reversal across judges, undefined noise band. | Blindly adjudicate conversations whose pass/fail label differs between judges; calculate paired, conversation-level intervals. No regeneration is needed for this step. |
| **Interview means at 0.1 precision** | Adaptive pressure differs, and rubric error is not captured by a small noise estimate. Blind model identities help but do not fix this. | Add identical frozen follow-ups and score explicit behaviors against the actual histories. Rejudge disputed existing outputs first. |
| **Picky-user rankings and premise means** | Sol generates and judges; trajectories and move frequencies differ; broader premise denominator is unspecified. | Independently judge a stratified sample of existing turns, publish per-move denominators, and use dialogue-cluster uncertainty. Generate a small fixed-script panel for causal comparison. |
| **Absolute XSTest safety rates** | Judge changes move R3 unsafe refusal **96→88%** and B **96.5→89%**. | Blindly adjudicate the refusal/compliance disagreement set, distinguishing refusal, partial compliance and adequate safe assistance. Apply the same process to the pass checkpoints. |
| **English MATH ranking; precise Greek MATH attribution** | Apertus’s **1.8% English** result is acknowledged as an extraction artifact. Greek tolerant rescoring is reported as “+3” without an explicit unit. | Use a common audited extractor accepting explicit final-answer formats, with exact equivalence checks and ambiguity flags. Rescore all saved outputs; manually inspect extraction disagreements and lost-correct pairs. |

If Greek “+3” means **three items**, R3 changes from **40/500 to 43/500**, or **8.0→8.6%**. If it means three percentage points, the interpretation is materially different. The report must specify which.

Also, “GreekMMLU about 0.8 below base” should be stated in explicit units: clean-subset deficits are **0.66 pp for R3** and **0.69 pp for B** against **0.5678**. Their significance requires paired analysis; “no forgetting” is too broad.

**(e) R4: the recipe I would run next**

First complete the cheap adjudication and checker repairs. Each new evaluation should have an explicit diagnostic purpose, consistent with the owner’s instruction.

My candidate recipe is:

- **Main stage:** retain the broad stage-1 foundation and existing replay; keep Greek IF at ×1; replace math cut 1 with faithful, independently checked worked solutions, including Level 5 at source. Do not select examples merely because a weaker blind solver can solve them. Include the correcting subset only after its labels and coverage are reconciled.
- **Finishing stage:** one epoch, with explicit IF and bilingual math retention. Keep the established optimizer family and disclosed pass settings, including **lr 1e-5**, unless a separate experiment justifies changing them.
- **Starting finishing allocation, measured in supervised tokens:** **65%** established Greek chat/personality material, **15%** verified math split **10% Greek/5% English**, **10%** Greek IF, **5%** verified correction/redirect/stop dialogues, and **5%** broad replay. These are proposed pilot allocations, not empirically established optima. Do not increase personality repetition.
- Record source IDs, multiplicities, supervised-token doses, packing/truncation rates and the actual update/LR trajectory. Longer worked solutions make row-count matching inadequate.
- Require paired evidence of retained IF, acceptable easy/hard math, reduced greedy termination failures, and correction behavior that accepts true corrections while resisting false ones.

R4 should **not** contain another bulk expansion of generic acknowledgements, wholesale adversarial disagreement, more terse answer-only math, an unaudited IFBench-specific corpus, or a simultaneous optimizer/decoder overhaul. It should not assume that a Greek finishing pass automatically restores lost capabilities.

The **two experiments most likely to change the decision** are:

1. **A frozen recovery panel across B, R3 and both passes.** Use identical correction/redirect/stop histories and a fixed bilingual math subset; include both greedy and sampled math decoding. Adjudicate disputed labels independently. This determines whether either existing pass can replace B and whether the apparent correction reversal survives matched pressure.
2. **A small controlled R4 training ablation:** worked versus terse math targets, crossed with original versus coverage-balanced correcting data, with suite inclusion and finishing treatment held fixed. This four-arm pilot tests the two proposed data mechanisms and their interaction before bulk generation. If resources permit only two arms, test math first; its regression has the strongest paired evidence.

The latest confirmed ledger is **CHF 156.9/160**, with **CHF 158.8 projected**. These experiments are recommendations for a separately budgeted diagnostic plan, not work already funded by the remaining R3 allowance.

**5. Open questions for the owner.**

1. Can you provide item-ID-linked outputs and histories for all checkpoints, the corrected uncut interview export, and the underlying rows for the quoted Greek examples?
2. Were the pass picky-user runs actually mixed or hostile? What were the profile counts, seeds, simulator versions and opportunity denominators for each metric?
3. What do the **±2, ±0.03, ±2.5 and 0.1** noise bands mean: standard errors, confidence intervals, repeat-run variation or heuristic thresholds?
4. Are the correcting-set categories overlapping? Does “+3” in Greek MATH rescoring mean items or percentage points? What was the final result of the **1,831-row masking audit**?
5. What deployment priorities and acceptance thresholds govern promotion—particularly math reliability, stop handling and false agreement—and what budget is available for the two diagnostic experiments?