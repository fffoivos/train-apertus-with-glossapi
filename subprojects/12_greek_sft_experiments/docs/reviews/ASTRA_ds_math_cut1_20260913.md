# Astra review: astra_ds_math_cut1

Date 2026-09-13 10:36 · model gpt-6-astra (asserted from rollout rollout-2026-09-13T10-28-09-01a099aa-9766-7562-8060-c0f483973492.jsonl) · effort xhigh · 8.6 min · prompt 93,595 chars · limit deltas {('codex', '10080'): -78.0} · brief `docs/reviews/briefs/astra_ds_math_cut1.md` · sample 60 rows of `data/math/cut1/edited/rows_edited.jsonl` seed 3

**1. Verdict**

**Change before future use; preserve the completed cut as an auditable historical artifact.** The sample supports concerns about verification, problem wording, difficulty selection, and an overly uniform answer format. It does **not** establish that short solutions caused the regression. The reported MATH-500 results are 40/500 for R3, 64/500 for stage 1, and 38/500 for arm B: deterioration relative to stage 1, but a small improvement over arm B. Neither comparison isolates `math_cut1`. Replace the current generation and filtering recipe with reference-grounded worked solutions, explicit difficulty coverage, and separate checks for mathematical validity, translation fidelity, and answer formatting. Salvage the partial rebuild after review; do not merge it because it contains boxes and longer solutions. Apply the BLOCKER/HIGH findings below to queued successors. For the already trained dataset, record them without deleting artifacts or taking retrospective training action.

Scope: I inspected the **60 pasted records**. Tool access failed, so I could not inspect the full corpus, partial rebuild, evaluator, or live public-source documentation. Training results are owner-reported. Public links below are source pointers whose current contents and reuse terms I could not verify.

**2. Findings ranked by severity**

The sample counts are:

| Property | Count |
|---|---:|
| Translated GSM8K / translated MATH / native | 17 / 17 / 26 |
| `verified: "reference"` | 34/60 |
| `verified: "second_solve"` | 17/60 |
| `verified: "none"` | **9/60 — 15.0%** |
| Native rows marked `none` | **9/26 — 34.6%** |
| Targets ending with `Απάντηση:` / containing `\boxed` | 60/60 / 0/60 |
| Single user–assistant exchange | 60/60 |
| MATH Levels 1 / 2 / 3 / 4 / 5 | 1 / 3 / 6 / 7 / 0 |

I found **no unambiguous arithmetic miscalculation** in the displayed calculations. That does not mean all 60 are valid training examples: answer correctness, sound premises, valid explanations, and instruction compliance are different checks.

**BLOCKER — The supplied records do not substantiate the claimed verification contract.**

Nine native rows carry `verified: "none"`:

`gm_nat_181_2`, `gm_nat_278_0`, `gm_nat_202_0`, `gm_nat_867_2`, `gm_nat_800_1`, `gm_nat_147_0`, `gm_nat_876_4`, `gm_nat_910_1`, `gm_nat_680_0`.

Their calculations look correct, but their metadata does not support the claim that native rows were retained only after second-solver agreement. Conversely, `second_solve` does not establish correctness: examples below passed that gate despite defects.

The corpus identity also needs reconciliation:

**5,823 + 3,284 + 5,108 = 14,215**, matching the sample heading, but differing from the stated trained count by **145 rows, or 1.02%**. This could be legitimate downstream exclusion; its effect is currently unknown.

**Fix:** Before extending the pipeline, produce the exact training manifest and the 145-row exclusion ledger. Record verification methods separately—reference-answer equivalence, prompt fidelity, mathematical explanation, requested output, and post-polish invariance. Include source revisions, original problem IDs and splits, and checker receipts. These provenance fields are absent from the pasted translated records; they may exist in a sidecar, which must be joined.

For native generation, use mathematically specified templates with independently computed answers, or source-backed/human-established references. Do not substitute Luna agreement for those references or reinstate the weaker-model filter.

**HIGH — Correct-looking answers conceal defects in premises, explanations, and requested units.**

These are specific failures or ambiguities, counted separately:

| Evidence | Diagnosis and sample frequency | Concrete fix |
|---|---|---|
| `gm_nat_618_4`: user requests **«Η απάντηση να δοθεί σε λεπτά του ευρώ.»**; target ends **«Απάντηση: 3,62 €»** | **1/60 explicit requested-unit mismatch.** The unrounded result is €3.61728 = 361.728 cents. The target also assumes payment rounding. | Specify “rounded to the nearest cent” in the prompt if intended, and answer **«362 λεπτά του ευρώ»**. Otherwise preserve the exact value in cents. |
| `gm_nat_301_3`: **«Υπολογίζουμε πρώτα ένα μέρος του όγκου του ενυδρείου.»**, followed by `1,2 · 0,5 = 0,6 m²` | **1/60 incorrect mathematical explanation:** this computes area, not part of a volume. The final 360 litres is correct. | Replace with **«Υπολογίζουμε το εμβαδόν της βάσης του ενυδρείου.»** Check dimensional explanations as well as arithmetic. |
| `gm_nat_1162_4`: unchanged price per kWh is used to scale the entire electricity bill by `7/5` | One of **2/60 problems with material premise defects**. The result requires a wholly consumption-proportional bill. A fixed €10 component would give May’s bill €150 rather than €154, while satisfying the stated conditions. | State that the bill contains only consumption charges, with no fixed component; or provide the fixed component and solve accordingly. |
| `gm_gsm_4518`: **«περιοχή ανατολικά της πεδιάδας Β»** becomes **«περιοχή της πεδιάδας Β»** | The second premise defect. The English source already conflates the region east of a plain with the plain itself. Reference `350` does not resolve that inconsistency. | Rewrite consistently in terms of the two plains’ areas, document a source repair, and re-establish the answer. Do not label this an unchanged translation. |
| `gm_gsm_2209`: **«3 φορές περισσότερο χρόνο»** translates “3 times as long” | **1/17 GSM8K translations, 5.9%,** introduces avoidable multiplier ambiguity. | Use **«τριπλάσιο χρόνο»**, preserving the intended answer of 90 minutes. |

The first three examples above are all marked `second_solve`. They demonstrate why agreement on a final value cannot certify the whole training target.

**Fix at pipeline level:** repair these queued examples and audit their corresponding generation patterns. Keep separate failure counts; do not collapse them into an invented “wrong-answer rate.”

**HIGH — The filtering policy selects for solver ease and leaves a documented difficulty gap.**

The brief reports:

- Level 5 was never sampled.
- Blind solving removed 18% of Levels 1–4.
- Luna disagreement removed 892 native candidates.

The sample confirms no Level 5 among its 17 MATH rows. It cannot establish which rejected problems were valid, or how strongly filtering changed difficulty within each level.

**Fix:** retain source problems when an attempted target fails. Retry using the authoritative solution, repair, or place them in an explicit unresolved queue. Report attempted, repaired, retained, rejected, and unresolved counts by level and subject. Recover the 892 native candidates for reference-based adjudication; do not assume either solver was right.

Adding Level 5 restores missing coverage. It cannot by itself explain or repair the reported Level-1 decline.

**HIGH — A longer, boxed rebuild is an untested intervention.**

All 60 targets use `Απάντηση:` and none uses `\boxed`. That is strong evidence of format uniformity. The owner-reported 343/500 unboxed evaluation responses are consistent with learning that format.

However, many sample targets already contain sound worked solutions. `gm_math_675` examines both admissible operation assignments; `gm_math_819` enumerates distinct absolute-distance possibilities. Calling these merely “quick answers” understates their content.

**Fix:** before bulk regeneration, separate:

1. Answer-extraction failures.
2. Insufficient mathematical explanation.
3. Difficulty and subject selection.
4. Training-mixture effects.

Rescore existing predictions using both the official evaluator and audited mathematical answer extraction. Then compare short versus reference-grounded solutions on identical problems, with formatting controlled. Neither an 85-word median nor a box is a correctness criterion.

**MEDIUM — The Greek polish scores miss an obvious defect.**

`gm_gsm_2692` contains **«Τρέvor»** twice in the user message, while the assistant uses **«Τρέβορ»**. It nevertheless has `greekness: 5`.

That is **1/60 rows**, and **1/56 rows receiving the maximum Greekness score**, with a clear mixed-script name defect. The existing polish therefore provides incomplete evidence of linguistic cleanliness.

**Fix:** use Unicode script checks on prose tokens, allowing mathematical variables and unit symbols. Review both prompts and targets. Preserve expressions and recheck answers after polishing.

Also normalize mathematical markup: `gm_math_3718` places `\overline` outside math delimiters in its target. This is a visible markup issue; I could not test its rendering.

**MEDIUM — Metadata exaggerates coverage and should not drive difficulty quotas unchanged.**

`gm_nat_610_1` is tagged **«τριγωνομετρία»**, but requires only `286 − 2·96 = 94`. That is **1/26 native rows with a clear topic misclassification**.

Other examples show why grade labels are insufficient difficulty measures:

- `gm_nat_1071_2`, Γ΄ Λυκείου: solve `1200/x + 5 = 8`.
- `gm_nat_722_3`, Α΄ Λυκείου: integer arithmetic with a distractor.
- `gm_nat_957_0`, Β΄ Λυκείου: proportional scaling and unit conversion.

These problems can be useful; their labels do not demonstrate advanced reasoning coverage.

**Fix:** distinguish intended school audience from mathematical topic, required operations, case analysis, and reasoning depth. Audit actual tasks before using labels to claim a balanced curriculum.

**3. What is good and should not be changed**

- **Most displayed mathematics is sound.** Preserve clean examples rather than regenerating everything.
- **Concise solutions can be complete.** `gm_math_2369` correctly explains four independent binary choices; `gm_math_1776` correctly subtracts the two empty-group assignments.
- **Source originals and reference answers are retained** for all 34 translated examples. This is useful audit material.
- **Greek decimal notation and practical units** are generally handled well.
- **Multipart questions and irrelevant information** provide useful variation. Keep these, while adding less obvious distractors and checking problem validity.
- **Edit provenance** in rows such as `gm_math_2383` and `gm_math_675` is worth preserving. Extend it to all mathematical and linguistic repairs.
- Preserve relevant domain checks, such as the admissible spectator count in `gm_nat_1071_2`.

**4. Answers to the specific questions**

**Keep, change, or remove?**

Keep the completed artifact and its evaluation history. **Change its future replacement.** Do not continue the current blind-solve/disagreement-filter recipe.

Removal from future training becomes justified if a controlled comparison shows that the repaired Greek math block still underperforms the declared alternative, such as English math replay. The current aggregate results do not establish that causal conclusion.

**Is “targets shaped like OpenMathInstruct” the right fix?**

It is a reasonable **hypothesis**, provided “shaped like” means coherent, sufficient worked solutions grounded in trusted mathematics.

Obtain the exact English OpenMathInstruct version and examples used in stage 1. A dataset name does not specify reasoning quality, length, formatting, or sampling.

For instance, `gm_math_3896` could explain its answer completely with:

> Οι δέκα πρώτοι θετικοί περιττοί είναι \(1,3,\ldots,19\). Το άθροισμά τους είναι  
> \[
> S=\frac{10(1+19)}{2}=100.
> \]
> Άρα \(\boxed{100}\).

This adds the missing justification without padding. Use boxes for default mathematical answers where appropriate, while respecting explicit user requests for other formats.

**What should happen to the partial rebuild?**

Treat it as a recoverable candidate pool:

1. **Join every solution to an immutable source problem.** The 2,994 Level-5 solutions versus 2,100 translations may reflect multiple variants; counts alone do not establish orphaned rows.
2. Distinguish reference-solution translations from independently generated solutions. Record reference access accurately.
3. Check source split, benchmark overlap, mathematical expressions, answer equivalence, output instructions, and post-polish invariance.
4. Audit explanations and omitted assumptions, particularly for Level 5.
5. Release a small reviewed pilot before completing bulk generation.

Suggested quality gate: no critical defects in **300 fresh randomly sampled targets**, plus targeted audits of difficult subjects and fragile transformations. This is an acceptance sample, not proof that every remaining row is correct.

**Which public datasets should be adapted?**

The priorities below are recommendations; their current cards were not accessible in this session.

| Priority | Candidate | Recommended use |
|---|---|---|
| First | [GSM8K](https://github.com/openai/grade-school-math) and [MATH](https://arxiv.org/abs/2103.03874) training sources | Build the reference-backed core. Translate established worked solutions; cover all MATH levels. Reserve source-disjoint development problems before adaptation. |
| First pilot | The exact English OpenMathInstruct block used in stage 1; then [OpenMathInstruct-2](https://huggingface.co/datasets/nvidia/OpenMathInstruct-2) | Test translation of an already useful training component. Require source lineage and distinguish original reference answers from answers attached to synthetic problems. |
| Supplement | [NuminaMath-CoT](https://huggingface.co/datasets/AI-MO/NuminaMath-CoT) | Expand harder mathematics selectively. Verify source provenance. Separate numeric-answer problems from proofs that cannot be certified by final-answer comparison. |
| Supplement | [MetaMathQA](https://huggingface.co/datasets/meta-math/MetaMathQA) | Add controlled problem variation after establishing the core. Each transformed question needs a valid corresponding answer; an original problem’s gold answer cannot automatically certify an augmentation. |
| Native Greek | [Greek digital textbooks](https://ebooks.edu.gr/ebooks/) and the [IEP question bank](https://trapeza.iep.edu.gr/) | Acquire authentic terminology and school/exam structures. Verify answer/solution provenance, reuse terms, and diagram dependencies. Do not assume every public question has an authoritative published solution. |

Across these sources, deduplicate and partition by **original problem lineage**, including translations and paraphrases. Check against the exact Greek benchmark versions and their upstream IDs. I have not detected contamination in this sample; I also cannot certify its absence.

**How should targets be verified using reference answers only?**

Use reference answers as the authority for **final-answer validation**, with deterministic checking:

- Exact integer and rational comparison.
- Greek decimal/thousands normalization.
- Symbolic equivalence under stated domains.
- Correct handling of sets, intervals, multipart answers, units, and requested precision.
- Explicit `unresolved` outcomes for unsupported cases.

Never replace these with a weaker model’s vote.

But **reference-answer-only verification cannot certify an entire worked solution**. `gm_nat_301_3` illustrates the limitation: the answer is right, while an explanation is wrong. `gm_gsm_4518` shows that a gold answer can coexist with an inconsistent problem.

Maintain honest labels: `answer_verified` is distinct from `solution_reviewed` and `translation_checked`. For reference-guided generation, acknowledging that the generator saw the reference is essential; matching it is then a limited check, not independent confirmation.

Every filter must publish its effect on difficulty. Repairs and pending cases must remain visible.

**Which new sets should be invented?**

Build small, verifiable sets around the observed gaps:

- **Greek quantitative-language contrasts:** «τριπλάσιο» versus «κατά τρία μεγαλύτερο»; percentages of the original versus remaining quantity; before/after changes; inclusive counts.
- **Units and answer contracts:** cents versus euros, exact versus rounded values, ordered multipart answers, and final-answer-only requests.
- **Math correction dialogues:** valid challenges, false corrections, changed assumptions, and updates that require recomputing dependent results.
- **Well-posedness contrasts:** paired questions with and without a necessary assumption, including fixed versus variable charges.
- **Harder reference-backed reasoning:** domain restrictions, extraneous roots, counting cases, and geometry with sufficient diagram information.

Use executable templates with established mathematical constraints where possible. Keep families together when making train/development splits. These additions address specific math behaviors; they are not demonstrated fixes for flat GreekMMLU or general IFBench performance.

**What acceptance checks and A/B read-out would prove improvement?**

First, audit the evaluator on existing outputs. Report official score, independently checked mathematical accuracy, extraction failures, truncation, and instruction compliance separately. Audit Greek punctuation and equivalent fraction handling.

Then run a controlled comparison from the **same checkpoint**, holding the other training datasets fixed:

| Arm | Greek math treatment |
|---|---|
| A | No `math_cut1`; explicitly declare the budget replacement, such as English math replay |
| B | Repaired common problems with current short-target style |
| C | Identical to B, adding the default boxed final-answer format |
| D | Identical problems with reference-grounded worked solutions and the same format as C |
| E, subsequent | Winning target treatment plus restored difficulty coverage and new problem families |

B→C tests formatting. C→D tests the worked-solution treatment. D→E tests the curriculum change.

Longer targets prevent simultaneously holding problem presentations and supervised token count constant. Declare the primary comparison as equal training budget, report exposures and actual tokenizer counts, and run a matched-problem-exposure sensitivity comparison for C versus D.

Use source-disjoint development data for iteration. Freeze final benchmark translations, prompts, decoding, token limits, and scorers. Report paired item wins/losses, confidence intervals, and preferably multiple training seeds.

Promotion should require:

- Better **mathematical accuracy**, beyond improved extraction or longer answers.
- Recovery toward the refreshed stage-1 MATH baseline—historically 12.8%—without hiding Level-1 losses behind Level-5 gains.
- No material regression on MGSM or the existing non-math checks.
- Public accounting of unresolved examples and difficulty shifts.

If C improves only official extraction while D adds no semantic gain, the demonstrated repair is formatting. If D improves semantic accuracy over C, the worked-solution hypothesis gains support. If all Greek variants lose to A, exclude that block from the next default recipe.

**How to reach Krikri’s approximately 0.68 on MGSM-el?**

First establish protocol comparability. Pin the Greek translation, item IDs, prompts, demonstrations, generation budget, scorer, and checkpoint versions.

If this is the standard **250-item-sized evaluation**, the reported scores correspond to:

- R3: **122 correct**.
- Arm B: **131 correct**.
- Krikri: **169 correct**.

Matching 0.676 therefore requires **47 additional correct answers over R3**, or 38 over arm B. The summary “did not move” should not obscure the observed R3–B difference of −3.6 percentage points, although its uncertainty requires paired predictions.

Use disjoint development examples to distinguish language interpretation, operation selection, arithmetic, omitted conditions, and output extraction. Compare English and Greek versions of the same held-out problems to identify the language-specific component.

Prioritize strong GSM-style worked solutions, quantitative-language contrasts, and appropriate replay weighting. **More Level-5 MATH is not an evidenced route to a 47-answer MGSM gain.** No dataset size or formatting change can currently be promised to reach 0.68.

**5. Open questions for the owner**

1. Which exact 145 rows separate the 14,215-row pool from the 14,070 trained rows, and why?
2. Why are nine sampled native records marked `verified: "none"`? Does a separate verification receipt exist?
3. Can the evaluation manifest and per-item predictions establish how unboxed answers were scored and whether all reported checkpoints used identical protocols?
4. Which exact English OpenMathInstruct block trained stage 1, and what supervised-token weight did it receive relative to Greek math?
5. How do the three partial-rebuild components join by source problem ID? Which solutions saw reference solutions, and which passed guarded polish?
6. Are the 892 native disagreements and rejected translated problems preserved with their attempts and difficulty metadata for reference-based recovery?