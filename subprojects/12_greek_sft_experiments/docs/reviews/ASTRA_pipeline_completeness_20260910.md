# Astra review: pipeline_completeness

Date 2026-09-10 21:15 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T21-08-29-01a08c81-c2fb-7891-b23d-e4333f3d4a52.jsonl) · effort xhigh · 7.5 min · prompt 46,473 chars · limit deltas {('codex', '10080'): 6.0} · brief `../docs/reviews/briefs/astra_pipeline_completeness.md`

**1. Verdict**

This is a substantial and promising SFT programme, but the document does **not yet establish that the final dataset is complete or ready to train**. Its strongest features are targeted Greek supervision, executable verification where available, several informative training comparisons, and unusually candid evidence of conversational failures. Its largest weaknesses are unclear accounting of weighted training exposure, unproven final assembly invariants, incomplete contamination coverage, and a correcting-set pilot that teaches resistance to false accusations much more often than recovery from genuine mistakes. I would approve the Saturday run **as a controlled SFT experiment once the launch gates below pass**, not as a demonstrated recipe for reaching Krikri or producing a complete Greek assistant. Pending generation counts are normal at this stage and are not themselves a defect. Completed datasets should remain intact; their weaknesses below are notes unless they concern the new assembly or training recipe.

**2. Findings ranked by severity**

*Evidence boundary:* No sample rows, row IDs, source files or executable receipts accompanied the brief. Consequently, I independently inspected **zero dataset rows** and cannot supply a verified row-level failure rate or quote row IDs. Arithmetic below is checked against the supplied document; earlier review rates remain **reported findings**, not findings independently reproduced here. Local files and external sources were unavailable in this session, so peer comparisons later are qualitative background rather than freshly verified recipe audits.

**B1 — BLOCKER: Reconcile unique rows, training copies, held-out rows and token exposure before assembly is accepted.**  
Evidence: §§2, 3.3, 6 and 8.

The listed counts admit a revealing reconciliation:

| Quantity | Calculated from the document |
|---|---:|
| Foreign rows actually listed in §2 | 295,754 |
| All rows listed, adding 22,000 Greek rows | 317,754 |
| Subtract stated dev set; add one extra copy of 19,800 Greek training rows | **334,383** |
| Reported trainer total | **334,383** |

This strongly suggests that §2 mixes counts before splitting with counts after weighting. It is a plausible explanation, **not verification of the assembler**. Section 8 then labels 312,383 rows as foreign—apparently subtracting 22,000 from the already expanded trainer total. That overstates the foreign rows listed by **16,629**. Using the listed unique counts and provisional new counts gives approximately **368,680**, rather than 385,309, rows before weighting and held-out exclusions.

Likewise, the 192.0M per-block token sum versus 197.9M trainer tokens cannot be attributed solely to template overhead without reconciling weighting and dev removal.

There is also a conditional leakage issue: §8 lists all **1,388 personality-v3 rows**, while retaining the **69-row personality holdout**. If interpreted literally, ×4 would expose those held-out rows 276 times. The assembler may already exclude them; the document does not establish that.

**Fix:** Produce one final receipt recording, per block:

- Unique input rows, train/dev exclusions, duplicate exclusions and effective sampled copies.
- Rendered input tokens **and supervised assistant tokens**, after weighting, masking and length handling.
- Source revision, row IDs, content hashes and parent/template identifiers.
- Zero train/dev intersection, with splitting performed before replication and grouping related variants where appropriate.

This is an assembly correction, not a request to regenerate completed sets.

**B2 — BLOCKER: Demonstrate that the final training path preserves masking and verification.**  
Evidence: §§3.6–3.7, 4, 6 and DATA_TODO 29–30.

Per-message `train: false` support and `test_loss_mask.py` are valuable, but the description does not demonstrate the invariant through the actual renderer, packer and collator. An error here would explicitly teach the planted repetitions, wrong self-reports and other behaviours the new data are meant to remove.

The suite’s final manifest and post-correction verification remain open. A Greekness editor can improve language while changing a remembered fact, dropping a qualifier or invalidating a later reference.

**Fix:** Before launch, provide tests using the actual training pipeline showing that:

- Every token belonging to a masked assistant message—including its ending marker—is excluded from loss.
- Intended assistant targets retain loss, including the appropriate stopping token.
- Packed examples have the intended attention isolation.
- Length handling does not orphan a recovery target from its preceding failure or remove an essential standing instruction.
- Every final queued dialogue passes its semantic and deterministic checks **after editing and final rendering**.
- Rejected or edited intermediate turns cannot leave later supervised turns referring to inconsistent history.

Complete S5m fact-update coverage and the cross-lane exposure cap before scaling is accepted. A generic `DRY_RUN_OK` should link to these results; successfully running a training step is insufficient.

**B3 — BLOCKER: Decontaminate the final frozen mixture against the actual evaluation inventory.**  
Evidence: §§4, 7 and 9.

The documented cache includes Greek MGSM but does not list its English source questions; it also does not list the native-Greek suite. An English training example overlapping a Greek test question can evade Greek-text 8-gram matching. This matters particularly for OpenMath and the translated math block.

The four new benchmarks were checked against the local SFT snapshot available during construction. That does not certify the subsequently generated, edited and assembled correcting, conversation and personality additions.

**Fix:** Run a final check after assembly, covering:

- Every evaluation actually used, including the native suite and new benchmarks.
- English originals alongside Greek translations where available.
- Source problem IDs and provenance, especially GSM8K/MATH split membership.
- Exact/near-duplicate text checks, plus targeted inspection of suspected translated or paraphrased matches.

Distinguish actual duplicate problems from legitimate shared mathematical templates. Retain the declared **486-item primary MATH-500-el subset** and report the 14 flagged items separately.

The full CPT-corpus audit is a separate issue: **its absence alone need not block this SFT experiment**. It limits claims about uncontaminated absolute performance and comparisons with peers; matched base-versus-SFT comparisons remain useful.

**H1 — HIGH: The queued correcting set is badly imbalanced between admitting real mistakes and rejecting false accusations.**  
Evidence: §3.7.

The pilot reports:

- **12/1,353 supervised turns = 0.89%** recovering after a true confrontation.
- **132/1,353 = 9.76%** recovering from a misquote.
- An **11:1 ratio** favouring misquote recovery.

These are calculations from reported categories, not inspected examples. Nevertheless, they identify a design problem directly relevant to §7: self-observation is reported correct only **20.2%** of the time, and the owner experienced repetition or stale copying in **16/17 chats**. That owner sample is diagnostic, not a representative population estimate.

At the pilot’s retained-turn rate, 1,500 dialogues would yield approximately **10,148 supervised turns**, rather than the planned 5,000. Shorter scale dialogues may be intentional, but this must be reconciled for weighting.

**Fix before further generation:** Set explicit accepted-target quotas for genuine-error recovery. Within the existing planted-dialogue cap, ensure that planted failures produce useful supervised recoveries, and make genuine-error recoveries at least as numerous as misquote recoveries. This is a pragmatic recommendation, not a literature-established optimum.

Cover genuine factual errors, dropped qualifiers, misunderstood requests, stale plans, repeated answers and incorrect self-reports. The target should identify and repair the specific error, then continue the task. Keep false-accusation cases as contrasts. Publish counts after rejection and editing; attempted cases are not coverage.

**H2 — HIGH: The one-stage recipe and proposed weights are not validated by arm B.**  
Evidence: §§6 and 8.

The observed comparisons are:

| Continuation from stage 1 | IFEval change | MGSM change |
|---|---:|---:|
| Stage 2 | +0.2 percentage points | +2.8 points |
| Arm A | +1.2 points | −1.2 points |
| Arm B | +3.8 points | +5.6 points |

Arm B changes personality exposure, epochs and learning rate relative to other continuations. Therefore, **“the Greek pass gave +3.8” is an observed combined result, not an isolated curriculum effect**. It also does not establish that personality ×4 will have the same effect when mixed throughout training from the base.

The conversation-dose argument has a unit error: §8’s “8.5k rows” combines approximately **3,500 dialogue rows with 5,000 supervised turns**. The proposed correcting file instead contains 1,500 dialogues. Row counts cannot establish behavioural exposure.

**Fix:** Freeze weights only after B1 provides assistant-loss-token shares and supervised-turn counts. Report personality, genuine recovery, standing-instruction and memory-update exposure separately.

The budget also needs an explicit interpretation. The reported stage-1 rate is approximately **32.50M input tokens per node-hour**:

- 230M tokens: approximately **7.08 node-hours**.
- 260M tokens: approximately **8.00 node-hours**, with no margin.
- Adding the stated evaluation battery gives approximately **11.38–12.30 node-hours**.

These are extrapolations; the changed length and masking distribution can affect throughput. Confirm whether eight node-hours means training alone, and benchmark the final mixture before committing the token budget.

**H3 — HIGH: Use the queued data to address grounded usefulness, not just suppression of undesirable style.**  
Evidence: §§3.6–3.8, 7 and 9.

The current model’s reported interview factuality is **2.15/5**. Yet much of the new programme targets constraints, tics, identity and conversational control. Those are necessary, but “no steering closer” and “contribute first” do not teach reliable answers.

Coverage is not demonstrated for:

- Answering from supplied evidence, citing the relevant passage and distinguishing it from prior knowledge.
- Saying that evidence is insufficient without becoming unhelpful.
- Correcting a factual answer after receiving a reliable source.
- Necessary clarification, infeasible requests and conflicting constraints.
- Benign requests that resemble unsafe ones, including Greek-context examples.
- Ordinary noisy Greek: typos, accentless input, informal Greeklish and code-switching. Producing Greeklish under an IF constraint is a different skill.
- Memory updates and corrections, rather than only remembering the initial fact.

**Fix before further generation:** Add a coverage matrix to the queued suites and correcting set, then allocate their existing budget to uncovered cells. Include short supplied-source tasks so that factual correctness is inspectable. Make style rules conditional: legitimate clarification, options and longer answers must remain possible when the task requires them.

For queued v4, verify the seven correction targets against primary sources and include legitimate operations under identity pressure. The existing v3 remains unchanged under the disposition. Explicitly record that adding a correct v4 answer does **not** guarantee erasure of a conflicting v3 target.

**H4 — HIGH: Repair evaluation definitions before they guide the run or promotion decision.**  
Evidence: §§7 and 9.

The missing `langdetect` dependency makes an IFEval component systematically wrong. Its effect on ranking and aggregate scores cannot be assumed harmless just because every model receives zero on that component.

The picky-user judge lacks human calibration. The 63-row annotation reference is model-labelled, and the outstanding benchmark work includes human-labelled judge validation. Agreement with another model is not equivalent to accuracy against human-adjudicated ground truth.

**Fix:**

- Rescore cached IFEval outputs after repairing the dependency; update every relevant baseline.
- Freeze benchmark versions, prompts, decoding, scoring and primary subsets before evaluating the new model.
- Human-adjudicate a stratified sample of the pivotal conversation judgments, especially genuine error versus false correction.
- Obtain arm B’s missing knowledge/retention baseline before using the new model’s results to make a promotion decision.
- Report paired uncertainty where possible. The round-one “seed floor” is not a confidence interval, and a new single-seed run cannot establish seed robustness.

Some baseline inference can run later, before results are unblinded; the scoring definitions and decision rules should be settled now.

**M1 — MEDIUM, completed-data note: The quality screens support useful selection, not the claimed strength of correctness assurance.**  
Evidence: §§2–5.

Concrete limitations include:

- **5/300 = 1.67%** unusable ifeval-like examples is a point estimate. Assuming random independent sampling, its approximately 95% Wilson upper bound is **3.84%**; it does not establish a population unusable rate below 2%.
- OpenMath’s final-answer agreement does not verify every reasoning step.
- Code has no executable tests.
- Nemotron screening leaves **27% of assistant text unseen**.
- Sol and Luna agreement, or a fresh call to the same editor model, can retain correlated errors.
- Prior reviews report **9/57** Greek IF answers with padding, omissions or unsupported additions and **5/57** with unnatural Greek. These rates must not be attributed to the entire final IF set or to v3.

Judges also act as substantial filters: disposition, mannerism, language, identity and disagreement rejection all shape the resulting distribution. For example, **892/6,000 native math attempts** were discarded for disagreement. That may disproportionately remove difficult cases; agreement is not a neutral sampling mechanism.

**Fix/log:** Preserve completed artifacts. Record selection rates by task, difficulty, length and language, and distinguish machine-verified properties from model judgments. For queued material, inspect entire targets and audit critical factual or semantic claims directly.

**M2 — MEDIUM: The adaptation conclusion is stronger than the experiment supports.**  
Evidence: §5.

E3 versus E3′ supports the proposition that adaptation helped **some measured behaviours in this experiment**: prompt-strict IFEval increased 2.7 points and interview scores improved. MGSM decreased 2.4 points. The arms also differ by nine rows, and the document does not establish replicated matched-pair uncertainty.

“Greek vantage matters and language does not” is unjustified. E2 falling within observed seed variation establishes neither equivalence nor language irrelevance. Moreover, **screening away foreign framing is not equivalent to adding Greek-context competence**.

**Fix:** Narrow the claim. Report Greek language and Greek-context coverage separately. Ensure adaptation respects the user’s specified country, institution or scenario; Greek-language answers should not automatically relocate every task to Greece.

**M3 — MEDIUM, legacy/provenance note: Large blocks lack a clear link to the intended deployed capability.**  
Evidence: §§2, 4 and 9.

Nemotron plus tool use account for **100.89M/192.0M = 52.5%** of the listed unweighted token total. These are precisely the blocks with substantial unseen text or an ad-hoc tool representation. This does not prove harm, but makes them major uncertainties rather than peripheral exceptions.

The licence table also lacks pinned versions and leaves inherited source terms and some generator-related obligations unresolved. A source-card licence label is not a complete provenance record.

**Fix/log:** Retain completed blocks, but record exact revisions and the basis for their intended use. For tools, distinguish textual function-call demonstrations from usable native tool interaction. Do not claim tool competence without serializer/parser validation and an actual tool evaluation. Preserve the stated restriction on MultiChallenge distribution while its permission question remains unresolved.

**3. What is good and should not be changed**

- **Keep the averaged CPT base.** The reported terminal-checkpoint results provide a concrete reason for that choice.
- **Keep executable verification and task-specific routing.** The puzzle calibration is a good example of replacing unreliable judging with a stronger check.
- **Keep Greek IF and Greek math as distinct targeted blocks.** They address measured deficits.
- **Keep genuine multi-turn supervision, masked failure context and contrast cases.** Repair their balance and validation rather than abandoning the approach.
- **Keep guarded Greek editing.** Add final semantic verification; do not remove the language-quality pass.
- **Keep evaluation-only benchmarks out of training.** Preserve flagged subsets and documented quarantines.
- **Keep the SFT-only constraint and defer the optional MCQ block.** Nothing here establishes that preference optimisation or MCQ data is required before this run.
- **Keep the evidence of failures visible.** The live chats and behavioural breakdowns are more actionable than a single favourable aggregate score.

**4. Answers to the specific questions**

**Coverage and peer recipes.** The programme is broad by source count, but its strongest demonstrated coverage is formal instruction following, GSM-style mathematics and synthetic conversation. Greek grounded assistance, ordinary document work, reliable uncertainty, genuine correction, and realistic language surfaces are thinner.

As qualitative literature context, Krikri and Meltemi are relevant Greek/bilingual comparators; Tülu/OLMo recipes emphasise deliberate capability mixtures and evaluation; SmolTalk is a useful comparator for varied everyday assistance, rewriting and conversation. Their final model results do not establish a transferable row ratio or behaviour-set dose—especially where later post-training stages contribute. The brief’s “1–2k behaviour-specific rows in 200–400k” should therefore be treated as a hypothesis requiring matched units and evidence, not a sufficiency rule.

**One stage versus a Greek pass.** Under the stated constraint, I would **keep one run from the base**, with the proposed one epoch and broadly unchanged optimizer recipe once the gates pass. There is insufficient clean evidence to insist on another stage, and insufficient evidence to claim the single-stage replacement is equivalent to arm B. Compare the result directly with arm B; describe the curriculum change as an experimental choice. Do not silently add a second full epoch.

**Greek/English balance and personality ×4.** The Greek/English ratio cannot be recovered from the source labels: the foreign mixture includes other languages, and token lengths and masked contexts vary. Measure language on the actual supervised targets.

The old listed mixture contains only **4.7% explicitly Greek tokens before weighting**, or approximately **8.4% after the stated Greek-ours duplication**, before dev/template adjustments. The new blocks materially change that, but the final share is unknown.

Personality ×4 is a defensible provisional carry-over from the ladder, **not an identified optimum**. Do not increase it. Measure whether identity training spills into ordinary answers, and remember that repeating the same facts gives exposure, not additional factual diversity.

**30k Greek IF versus 46k English ifeval-like rows.** Keep Greek IF at **×1 provisionally**. Including Precise IF, Greek supplies approximately **37.3% of the listed IF rows**, which is substantial. I would not automatically raise the weight or shrink English IF. First inspect supervised-token shares, constraint-family diversity and duplicated prompt structures. The statement that IF will occupy a fifth of tokens remains unverified.

**Can 14k Greek math rows close the MGSM gap? Should OpenMath shrink?** They can plausibly help, but the document cannot predict the gain. Reaching 0.676 from 0.524 means solving **38 additional items out of 250**. That is a substantial target.

Greek math represents only **13.5% of the combined Greek-math/OpenMath row count** at ×1. Keep the verified Greek block. Do not shrink OpenMath solely because it is English; consider reducing its sampling weight if the measured budget crowds out Greek weaknesses or conversational targets. Prefer retaining diverse reasoning over redundant elementary problem variants. Evaluate probability, systems and quadratics separately, since the calibration identifies them as weak.

**Are the conversation sets large enough?** Potentially—but the present dose argument is invalid because it mixes dialogues and turns. Keep **×2 provisionally**, then count accepted supervised targets and tokens for each behaviour. Correcting the 11:1 imbalance matters more than merely doubling the entire correcting set. No literature row-count analogy establishes sufficiency for this model.

**What should be measured after training?** Use the corrected arm B as the primary behavioural baseline, the CPT base for retention, and Krikri as the main 8B performance target.

Measure:

- Corrected Greek IFEval, IFBench-el, MGSM and primary MATH-500-el.
- GreekMMLU and the native suite with unchanged scoring.
- Genuine-error recovery **and** resistance to false correction.
- Repetition, dead dialogues, redirects, standing instructions, updated facts and self-observation.
- Safe-request adequacy and unsafe-request handling separately.
- Grounded Greek document tasks, natural language quality and unsolicited identity statements.

Reuse comparable fixed scenarios and conduct blinded adjudication; reactive conversations may otherwise diverge between models. Predeclare meaningful regression tolerances and promotion criteria. Improved IFEval alone should not compensate for worse conversation or lost knowledge.

**What would make us ready?** A final exposure/provenance receipt; clean grouped splits; proven masking and packing; post-edit verification of queued data; final-snapshot decontamination; repaired correcting-set quotas; corrected scoring; and a measured budget with disclosed parameters. These are concrete launch requirements. “All planned rows finished generating” is not an adequate substitute.

**5. Open questions for the owner**

1. Is eight node-hours the training allowance, or the total including the approximately 4.3-node-hour evaluation battery?
2. Does the assembler already explain the exact `317,754 − 3,171 + 19,800 = 334,383` reconciliation, and does it exclude all 69 personality holdouts before weighting?
3. Is the correcting scale run deliberately shorter than the pilot? What accepted quotas will it enforce for genuine mistakes versus false accusations?
4. Is this release intended to support native tool use, or is tool competence outside its claimed scope?
5. What minimum conversational improvement and maximum knowledge regression will determine promotion over arm B?
6. Who will complete the primary-source factual checks and human adjudication needed for the queued targets and pivotal evaluation judgments?