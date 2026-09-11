_Provenance: literature review written by the cross-vendor reviewer (gpt-6-astra, xhigh, 2026-09-11, one call for the three documents, no web access: written from the model's knowledge; brief docs/reviews/briefs/astra_dpo_literature.md; raw output docs/lit/ASTRA_DPO_LITERATURE_raw_20260911.md). Citations marked [verify] by the reviewer and the key numbers were checked by Claude on 2026-09-11; see the VERIFICATION section at the end. Owner discussion doc: docs/RLHF_PLAN_20260911.md._

# DOC B — What a preference score should represent: how to define preference

## 1. Verdict

**Define preference as a grounded improvement in satisfying the current request within the actual conversation state, subject to reliable task-specific constraints.** The draft correctly separates verifiers from open-ended judgment, but overstates verifier coverage and gives uncertain judgments excessive veto power. Its most damaging selection rule is dropping every all-pass quartet: passing minimum requirements does not eliminate meaningful quality differences. Preserve explicit truth information for correction tasks, allow ties and uncertainty, and calibrate vetoes separately from overall ranking. A preference label should not mean “Sol liked the prose,” “the answer was longer,” or “the assistant agreed with the user.”

## 2. Findings ranked by severity

| Severity | Finding and evidence | Concrete fix |
|---|---|---|
| **BLOCKER** | **Unvalidated judgments become hard eligibility rules.** Draft §4.3 makes more than two alleged Greek errors a veto, while §4.5 accepts only 80% Greek-error precision. At that threshold, one in five flagged errors could be false. Tone and “invented fact” also lack sufficiently operational definitions. | Keep Greek naturalness and subjective tone advisory until separately calibrated. Restrict hard vetoes to sufficiently reliable, evidence-backed violations. Introduce `unknown` and `not_applicable`. |
| **HIGH** | **“All k pass” is incorrectly equated with “no signal.”** Draft §3 would discard, for example, four factually valid answers where only one addresses the redirect fully. | Retain all-pass quartets when a clear, task-relevant preference exists. Drop genuinely tied quartets. For verifier-only prompts where all candidates earn the same verified outcome, dropping is reasonable. |
| **HIGH** | **Regexes are described as exact semantic rewards.** Draft §2 calls retention, correction handling, and repetition checks “exact.” A retained name can appear in the wrong role; a disclaimer can defeat a naive false-concession regex; lexical overlap can be requested. | Document each checker’s contract. Call its output “checker pass,” not “semantic correctness.” Audit false positives and false negatives on adversarial examples. |
| **HIGH** | **The 95% sycophancy statement lacks its experimental scope.** Draft §1 says preference models prefer sycophantic answers 95% of the time. The cited paper establishes important sycophancy effects, but that sentence is not a justified universal summary. | Locate the exact experiment and denominator before retaining 95%. Until then, use the supported qualitative claim and your own measured flip-rate definition. |
| **HIGH** | **The pairwise-cost comparison is misleading.** Draft §4.2 compares two k-way calls with 12 pairwise calls. Twelve calls are needed for every unordered pair in both orders. A selected chosen/rejected pair requires only two order-swapped calls. | Compare protocols at equal decision quality and the actual number of comparisons needed, rather than assuming a full round-robin tournament. |
| **MEDIUM** | **The calibration targets lack uncertainty and per-axis coverage.** At 120/150 agreement, the approximate 95% Wilson interval is **72.9–85.6%**. At 27/30 position consistency, it is approximately **74.4–96.5%**. | Report counts, intervals, ties, and subgroup results. Do not interpret point estimates as established lower bounds. |
| **MEDIUM** | **A fixed 20% inter-vendor disagreement stop rule conflates different problems.** Draft §4.4 treats disagreements over truth, style, and genuine ties alike. | Classify disagreements by axis and adjudicate hard-veto conflicts first. Use rates and uncertainty within those categories. |

## 3. What is good and should not be changed

- Give judges **English instructions with original Greek content** if that is the established, tested workflow.
- Hide candidate source identity and randomize positions.
- Provide **verified claim truth** for planted correction tasks.
- Ask for quoted evidence, especially for context violations and false capability claims.
- Use the owner’s native-speaker calibration before training.
- Audit with a second vendor.
- Make the next assistant turn the primary unit of preference.
- Keep sycophancy, repetition, and language slips as evaluation outcomes independent of the training judge.

## 4. Answers to the preference-design questions

### What successful recipes mean by “preference”

There is no single empirically privileged scalar called “helpfulness.”

InstructGPT used human comparisons within an instruction-following framework emphasizing helpfulness, truthfulness, and avoidance of harmful outputs. Constitutional AI makes selected principles explicit and uses AI feedback to implement parts of that preference definition. Both encode a normative specification; neither discovers an objective, universal preference ordering. [Ouyang et al., NeurIPS 2022, arXiv:2203.02155](https://arxiv.org/abs/2203.02155); [Bai et al., *Constitutional AI*, arXiv:2212.08073](https://arxiv.org/abs/2212.08073).

For your model, operational preference should prioritize:

1. Correct handling of the **latest request**, including a redirect.
2. Correct use of relevant conversation state.
3. Truthfulness and justified correction handling.
4. Task completeness and usable content.
5. Appropriate Greek and task-conditioned presentation.

These priorities should be explicit. Otherwise, a judge can trade away correctness for friendliness without exposing that trade.

### Rubric, holistic, pairwise, pointwise, or k-way?

The evidence does **not** support an unconditional ordering of “pairwise best, pointwise worst.”

- Pairwise judgment is convenient for a local choice and avoids demanding globally calibrated absolute scores.
- Pointwise rubric scoring helps diagnose why a response is good or bad.
- K-way comparison can reduce shared-context cost but increases comparison complexity and sensitivity to the candidate set.
- Holistic judgment can catch interactions omitted by a checklist, but its basis is harder to audit.

GPT-4 achieved over 80% agreement with humans in the MT-Bench/Chatbot Arena study’s evaluated setting. That is useful evidence that strong LLM judges can work, not a guarantee for Sol, Greek, your rubric, or subtle correction behaviour. [Zheng et al., NeurIPS 2023, arXiv:2306.05685](https://arxiv.org/abs/2306.05685).

G-Eval and Prometheus provide evidence that task-specific rubrics and explicit evaluation criteria can make pointwise evaluation useful. They do not prove that adding more rubric fields always improves reliability. [Liu et al., *G-Eval*, arXiv:2303.16634](https://arxiv.org/abs/2303.16634); [Kim et al., *Prometheus*, arXiv:2310.08491](https://arxiv.org/abs/2310.08491).

**Recommendation:** retain the economical two-order, four-candidate protocol for the pilot, but allow partial rankings, ties, and unrankable cases. Compare its selected-pair decisions with direct order-swapped pairwise judgment on a calibration subset.

Do not require a full permutation when the evidence supports only “A and B are acceptable; C fails; A versus B is a tie.”

### What the judge should and should not judge

| Axis | Ask the judge | Do not ask it to assume |
|---|---|---|
| Task completion | What did the latest user ask, and did this response do it? | That a polished answer to an earlier request is acceptable |
| Context faithfulness | Which facts and standing instructions are relevant now? | That every user assertion is true |
| Correctness | Does the answer contradict supplied evidence or a verified solution? | That unsupported confidence establishes truth |
| Greek | Are there specific consequential errors? Is the phrasing natural in the requested register? | That one preferred edit proves the original was wrong |
| Length | Is necessary information missing or is there unnecessary material relative to the request? | That longer is more helpful or shorter is always better |
| Tone | Is the response respectful and appropriate? | That disagreement is rude or concession is polite |
| Identity/capabilities | Does it falsely claim an action, memory, tool use, or capability? | That every first-person statement is forbidden |
| Safety/refusal | Is the response appropriate to the actual request and applicable policy? | That more refusals imply greater quality |

“Invented fact” requires particular care. Fiction, explicit assumptions, and newly calculated results are not automatically hallucinations. Prefer:

> **Unsupported factual assertion presented as established, where grounding is required and the evidence supports identifying the violation.**

### Known judge biases and their mitigations

| Bias | Evidence and measurement | Appropriate mitigation |
|---|---|---|
| **Position** | Change only candidate order and measure changes in the selected preference. Position effects are documented in LLM evaluation. [Wang et al., *Large Language Models Are Not Fair Evaluators*, arXiv:2305.17926](https://arxiv.org/abs/2305.17926). | Balanced orders; agreement on the selected pair; preserve disagreements for analysis. |
| **Verbosity** | Compare preferences within length bands and on controlled content/length variants. [Zheng et al., arXiv:2306.05685](https://arxiv.org/abs/2306.05685); [Dubois et al., arXiv:2404.04475](https://arxiv.org/abs/2404.04475). | Task-conditioned length assessment and length-controlled evaluation; no blanket ratio veto. |
| **Self-preference** | Evaluators can recognize and favour their own generations in studied settings. [Panickssery et al., *LLM Evaluators Recognize and Favor Their Own Generations*, arXiv:2404.13076](https://arxiv.org/abs/2404.13076). | Hide provenance; use another vendor and native humans; include content-equivalent style contrasts. |
| **Sycophancy** | Models can alter answers to match user beliefs, and preference judgments can reward agreeable answers. [Sharma et al., *Towards Understanding Sycophancy in Language Models*, ICLR 2024, arXiv:2310.13548](https://arxiv.org/abs/2310.13548). | Supply truth where known; test both valid and invalid corrections; distinguish evidence-sensitive updating from appeasement. |
| **Style over substance** | A judge may respond to organization, confident prose, or familiar formatting while overlooking substantive errors; this is part of the evaluation-bias problem examined by Zheng et al. | Include “beautiful but wrong” controls and plain-but-correct alternatives; require substantive reasons. |
| **Social sycophancy** | ELEPHANT concerns interpersonal/social validation beyond simply changing a factual answer. [*ELEPHANT: Measuring and Understanding Social Sycophancy in LLMs*, arXiv:2505.13995](https://arxiv.org/abs/2505.13995), **[verify metadata; no numerical result asserted here]**. | Test unjustified endorsement of the user’s interpersonal framing, while allowing appropriate empathy. |
| **Instruction contamination** | Candidate text can itself contain instructions directed at the evaluator; agreement between two calls does not establish immunity. | Treat candidates as untrusted quoted content and include adversarial judge-control items. |

The literature favours **explicit measurement and multiple controls**, not reliance on a prompt saying “do not be biased.”

For the Greek correction test, withdrawing a correct answer after bare **«λάθος»** without new evidence should count against the model. Correcting an actually wrong answer after **«λάθος»** should count in its favour. A blanket anti-concession rule would train stubbornness.

### Hard constraints versus soft scores

Hard constraints are appropriate when the violation is:

- relevant to the task;
- operationally defined;
- reliably detectable;
- sufficiently serious to disqualify a candidate.

Examples include a wrong final answer under a valid exact-answer contract, an explicit prohibited output format, or a false claim to have used a tool when tool availability is known.

Soft scores are better for:

- elegance;
- mild awkwardness;
- ordinary verbosity;
- personality fit;
- disputed wording choices;
- subjective impressions of servility.

Constitutional AI supports making normative criteria explicit. It does not establish that a principle becomes a reliable veto merely because an LLM is asked to check it. [Bai et al., arXiv:2212.08073](https://arxiv.org/abs/2212.08073).

Similarly, rubric-derived rewards are useful only to the extent that the rubric and its implementation measure the desired outcome. Optimizing an imperfect proxy can increase proxy reward while reducing actual quality. [Gao et al., *Scaling Laws for Reward Model Overoptimization*, ICML 2023, arXiv:2210.10760](https://arxiv.org/abs/2210.10760).

### Combining verifiers and judgments

Use **eligibility followed by preference**, not a weighted average that lets eloquence compensate for a known wrong answer.

1. Apply relevant validated checks.
2. Establish whether each candidate meets a minimum task-quality floor.
3. Disqualify candidates with confirmed hard violations.
4. Among eligible candidates, prefer materially better task completion, state handling, and grounded content.
5. Use Greek naturalness and presentation as secondary distinctions when the substantive answers are comparable.

A passing verifier establishes only its contract. A correct numerical answer does not establish that the explanation is correct. A retained string does not establish correct use of the retained fact.

If every candidate fails the quality floor, route the prompt to recovery or log it as an unsolved case. Do not silently choose the least bad failure.

### k, best-versus-worst, margins, and all-pass prompts

**k=4 is a reasonable starting point**, not a demonstrated optimum.

Best-versus-worst pairing has advantages: an obvious contrast, one pair per prompt, and low processing overhead. Its limitations are:

- the worst response may be a trivial failure;
- extreme scores are especially exposed to judge noise;
- a huge score difference may reflect length or formatting;
- the pair can become uninformative after a small amount of training.

Use **best eligible versus a clearly worse, meaningful alternative**. Sometimes that is the worst candidate; sometimes the informative rejection is a plausible answer that mishandles a redirect.

Avoid a universal numeric margin on uncalibrated ordinal scores. Require a concrete difference such as:

> “Chosen follows the new requested format; rejected continues the previous task.”

For genuinely ambiguous differences, label a tie.

Under an illustrative independence assumption, if each sample passes a binary verifier with probability \(p\), the probability of obtaining both a pass and a fail among four samples is

\[
1-p^4-(1-p)^4.
\]

It is:

- **87.5%** at \(p=0.5\);
- **34.4%** at \(p=0.1\) or \(p=0.9\).

These are calculations, not measured yields. They show why very easy and very hard verifier prompts produce fewer contrastive pairs. Correlated candidates make this simple model less reliable.

### Human calibration: what 150 items can establish

The owner’s 150 items are valuable. They can identify systematic rubric failures and estimate aggregate agreement to roughly several percentage points. They cannot precisely validate every task family and every veto.

Measure separately:

- strict pairwise agreement;
- agreement including ties;
- tie and abstention rates;
- position reversals;
- each hard veto’s precision and recall;
- disagreement by task family;
- Greek-error severity agreement.

Use confidence intervals and report the actual denominator. Greek-error precision is measured among alleged errors, not automatically among all 150 comparisons.

For a hard veto, **80% precision is too low as a default acceptance criterion**. A reasonable operational target is at least approximately **95% observed precision**, with enough audited positive cases to support the claim. Ideally the lower confidence bound also clears an agreed threshold, such as 90%. These are proposed risk tolerances, not paper-established universal standards.

The supplied **34/235 reverted edits = 14.5%** is worth investigating, but it is not directly a Greek-error false-positive rate. Guard reversion and human error adjudication are different events.

Also, “150 items plus 30 repeated-order items in one hour” permits only **20 seconds per judgment**. That is optimistic when prefixes, Greek errors, and evidence spans must be read carefully.

### Multilingual judging

Judge original Greek. Translation into English can change:

- politeness and register;
- grammaticality;
- idiomaticity;
- ambiguity;
- instruction difficulty.

English judge instructions can remain useful, but they do not validate Greek competence. Separate:

1. task correctness;
2. discourse/state handling;
3. Greek grammatical correctness;
4. Greek naturalness/register.

A second model’s agreement is corroboration, not native-speaker ground truth.

### Multi-turn rating and prefixes

Rate the final turn against the actual prefix. Make the relevant state explicit to the evaluator without supplying an ideal answer unnecessarily.

The prefix should contain the model’s previous mistakes when the task is to recover from them. Replacing those mistakes with polished teacher responses can remove the very difficulty you are trying to train.

However, an old R0/R1 prefix is historical-policy data, not necessarily current-R3 data. Use it as a failure source, then collect fresh R3 continuations and fresh rollouts.

### Answers to the draft’s seven owner decisions

| Decision | Recommendation |
|---|---|
| 1. Two-order k-way or pairwise? | **Pilot two-order k-way with ties**, and validate selected-pair decisions against direct pairwise judgments on a subset. |
| 2. Owner calibration? | **Yes.** Prioritize correction truth, Greek-error flags, and context-state handling. Allow more than an hour if needed. |
| 3. DPO or GRPO first? | **DPO first** for the primary discourse and judgment failures. GRPO is a later, separately budgeted experiment on reliable verifier tasks. |
| 4. Rewrite-as-chosen? | **Permit a separately tracked recovery lane**, with minimal verified edits. Do not mix it invisibly into on-policy pairs. |
| 5. 1.5× length filter? | **Remove the hard filter.** Use task-conditioned length assessment and audits. |
| 6. Opus or Luna audit? | **Opus** provides the requested vendor diversity. It is still not independent ground truth. |
| 7. Budget? | **One committed iteration within 20 node-hours.** Recalculate rater quota; approve iteration two only from measured remaining capacity. |

## 5. Open questions for the owner, followed by the proposed preference definition

The unresolved owner decisions are:

1. Which violations are serious enough to disqualify an otherwise useful answer?
2. Which Greek variants and registers are acceptable?
3. Is personality consistency a secondary tie-break or an independently important objective?
4. What evidence source establishes truth for naturally occurring correction prompts?
5. Can a small portion of native review be reserved for a final assessment separate from rubric calibration?

**Proposed preference definition**

> Given the same conversation prefix and latest user request, prefer the response that more completely and correctly performs the current task, uses the relevant conversation state accurately, and handles corrections according to evidence. Require compliance with applicable, reliably verified constraints. Among substantively comparable answers, prefer appropriate Greek, proportionate length, and respectful tone.

Use the following record:

| Field | Content |
|---|---|
| `prompt_id`, `candidate_id`, hashes | Stable provenance |
| `target_turn` | Exact assistant span receiving preference and auxiliary loss |
| `applicable_checks` | Check name, version, applicability, result, evidence |
| `task_completion` | 0 = misses task; 1 = partial; 2 = substantially complete |
| `state_handling` | Correct / incorrect / uncertain, with prefix evidence |
| `grounding` | Supported / contradicted / unverifiable / not applicable |
| `correction_handling` | Evidence-sensitive update / justified resistance / false concession / unjustified resistance / not applicable |
| `greek_quality` | Consequential errors and mild issues separately; quoted spans |
| `length_fit` | Missing necessary content / appropriate / unnecessary excess |
| `tone_issue` | Specific observable issue, not an unexplained personality score |
| `hard_violation` | Type, evidence source, confidence status; only validated categories can veto |
| `preference` | A / B / tie / uncertain |
| `preference_reason` | One or two concrete, task-relevant distinctions |

**Ranking rule:** verified eligibility first; then task completion, state handling, and grounded correctness; then Greek and presentation when differences are meaningful. Keep only clear selected-pair preferences consistent across the accepted judging protocol. Keep informative all-pass pairs. Leave out mandatory total rankings, raw verbosity rewards, unsupported confidence scores, blanket anti-concession rules, and uncalibrated grammatical vetoes.

## VERIFICATION (Claude, 2026-09-11 18:05)

Every arXiv identifier in the three documents (44 distinct) was resolved to its title on arxiv.org (docs/lit/citation_check_20260911.json). 41 resolve to the paper the reviewer names. Three identifiers were wrong and are corrected in place: West-of-N is arXiv:2401.12086 (the reviewer wrote 2402.05392, an astronomy paper); Meltemi is arXiv:2407.20743 (not 2407.20773); the Salamandra technical report is arXiv:2502.08489 (not 2502.08486). Not yet verified: the Tülu 3 preference-pair count the reviewer marked [verify], and the exact experimental scope of the "preference models prefer sycophantic answers 95% of the time" figure from Sharma et al. 2023, which the reviewer challenged in DOC B; both stay marked. Numbers quoted from papers (β ranges, pair counts, benchmark deltas) were NOT independently checked against the papers' text; treat them as the reviewer's reading until the owner discussion picks the ones we will rely on.
