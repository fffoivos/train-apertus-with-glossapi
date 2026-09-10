# Astra review: benchmarks_programmatic

Date 2026-09-10 11:09 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T10-59-30-01a08a54-37a4-7203-8ad7-242c48f3cd7e.jsonl) · effort xhigh · 10.5 min · prompt 92,937 chars · limit deltas {('codex', '10080'): 0.0} · brief `../docs/reviews/briefs/astra_benchmarks_programmatic.md` · sample 90 rows of `benchmarks_el/review_sample_programmatic.jsonl` seed 1

**1) Verdict.** **Hold arm decisions pending targeted corrections and scorer qualification.** I reviewed the **40 IFBench rows and 50 MATH rows** supplied; the IFBench sample covers **32 of 58 constraint IDs**. MATH’s translations are generally convincing, but the stated scorer validation does not establish reliable scoring of Greek model answers. IFBench has visible reference-rendering problems, changes to instruction strength, and insufficient evidence for its “novel composition” classification. These are **BUILT** sets, so the release gates below apply before use. I could not inspect the named files, execute either verifier, or access upstream code in this session: row comparisons and counts below are independently checked; implementation behavior and historical cross-check results remain unverified unless explicitly identified otherwise.

**2) Findings ranked by severity**

**BLOCKER — F1. MATH’s validation omits a concrete Greek-answer case and does not validate end-to-end scoring.**

Evidence: `test/intermediate_algebra/860.json` asks whether the conic is an ellipse, using the Greek option **«έλλειψη»**, while its reference answer is `\text{ellipse}`. This is **1/50 sampled rows with an evident need for cross-language categorical equivalence**. It is **not an observed scorer failure**: no scorer was executed. However, the described normalization + numeric + SymPy pipeline contains no stated mechanism for this translation.

The brief’s **500/500 self-comparisons** establish that references recognize themselves. **489/489 rejected digit perturbations** test a narrow negative class; the remaining **11 answers** need an explicit coverage account. Neither result establishes correct extraction or equivalence for model-generated Greek answers.

**Fix before use:**

- Add independently labelled tests requiring `έλλειψη` and `\text{έλλειψη}` to match `\text{ellipse}`, while rejecting `υπερβολή`.
- Validate answer types separately. Sample anchors include the grouped integer in `number_theory/417`, the vector in `precalculus/145`, and the symbolic expression in `precalculus/1133`.
- Test full responses: Greek introductory prose, intermediate calculations, multiple boxes, contradictory answers, missing answers, and malformed expressions.
- Validate decimal commas without confusing them with coordinates, lists, or thousands separators.
- Score a frozen pilot response corpus, blind to arm identity, against human labels before making an arm decision. Report extraction errors, false acceptances, and false rejections separately.
- Pin the exact upstream scorer and report its metric separately from any extended Greek equivalence metric.

**HIGH — F2. Both sampled overlap prompts fail to display the actual reference clearly; one has a potentially impossible target.**

Rows **#214 and #152** display:

> «το κείμενο της παραπάνω ερώτησης»

after introducing “the following reference text.” Their `reference_text` kwargs instead contain their respective task bodies. This is **2/2 sampled overlap rows, or 2/40 IFBench rows**, with quoted metatext in place of the actual reference. It leaves the respondent to resolve whether that quoted phrase is itself the reference.

Neither prompt specifies the overlap denominator: reference trigrams, response trigrams, and their union yield different percentages.

There is also a concrete conditional feasibility problem. **#152’s reference has nine words and seven trigrams.** If overlap is the fraction of reference trigrams reproduced, attainable values begin at 0%, 14.29%, 28.57%, …; **11% ±2% is impossible**. This conclusion is conditional on the denominator, not a verified implementation failure.

**Fix:** Render the literal `reference_text`, define the formula and tokenization convention, and check integer attainability for every overlap item. Store a satisfying response for each retained constraint combination under the actual evaluation token budget. For #214, dropping the consonant constraint does not by itself establish that the remaining item is valid.

**HIGH — F3. Prompt-faithfulness and checker-faithfulness are conflated; substantive retunings need separate reporting.**

In **#142, #139, #189 and #190**, English requires:

> “Each section must begin…”

Greek requires:

> «Τουλάχιστον μία ενότητα ξεκινά…»

That changes a universal requirement to an existential one. All four retain a `faithful` tag for `format:thesis`: **4/4 sampled occurrences, affecting 4/40 rows**.

The upstream checker might already enforce only the weaker condition. That would explain checker-faithfulness, but would not make the Greek prompt faithful to the English instruction. The metadata must distinguish those claims.

Other visible changes include:

- **#236:** ten palindromes → three.
- **#269, #271:** three vowel types → at most four.
- **#214:** a two-constraint task → one constraint.
- **#277:** one required ISO date format → either numeric Greek dates or dates with a written month.
- **#117, #113:** an unquoted *explanation* → subsequent unquoted *text*, accompanied by mechanical quotation restrictions.

**Fix:** Record prompt-semantic fidelity, upstream-checker fidelity, and difficulty retuning separately. Put replacements, dropped constraints, material threshold relaxations, and altered acceptance predicates in a separately reported extension. Preserve a versioned full-set score for diagnostics.

The **26→24 alphabet adaptation can reasonably remain in a localized core** when it preserves the task “traverse the alphabet.” The palindrome reduction and newline reduction require a different justification: they change task size. Reasons for those choices do not establish matched difficulty.

**HIGH — F4. The overlap labels do not yet substantiate the generalisation claim.**

The sample contains:

| Supplied class | Rows |
|---|---:|
| Seen | 1 |
| Seen in novel composition | 20 |
| Unseen | 17 |
| Unresolved | 2 |

Of the **20 “novel composition” rows, 15 contain only one listed instruction ID**: **#85, #45, #32, #17, #142, #43, #10, #277, #61, #119, #26, #36, #0, #139, #62**.

A single ID could encode multiple primitives, or “composition” could mean combining a constraint with a task. Therefore this is not proof of misclassification. It does mean the displayed metadata cannot establish novel combinations of constraint families.

Likewise, the brief’s **58 held-out IDs** cannot be presented as **58 unseen families** when its own mapping assigns 24 IDs to seen-related classes and three to unresolved.

**Fix:** Publish the ID→SFT-family mapping, including evidence from the actual SFT instructions and compound primitives. Define what constitutes a novel composition. Report:

- Prompt counts and instruction-instance counts per class.
- Prompt-level all-constraints success and instruction-level success.
- Family-macro results alongside pooled results.
- Mixed prompts as an explicit cross-cutting flag, with their constituent classes.
- Unresolved cases separately.
- Results for the corrected core and extension separately.

Recompute this metadata after removing constraints, including #214. Scope “unseen” to the **audited SFT corpus**; this cannot establish absence from base-model pretraining.

**HIGH — F5. Final-file checks need stronger semantics and a closed repair ledger.**

In `test/intermediate_algebra/1572.json`, two `\text{if }` leaves become `\text{αν }`, while `checks.math_spans` is `true`. The translation is appropriate, but this demonstrates that the boolean does **not mean literal equality of every math span**.

The sample also contains **eight rows with repair provenance**, including two marked `spliced`: `precalculus/1133` and `algebra/733`. I found no visible renewed splice corruption in these two. The four supplied diagram pairs—`geometry/65`, `geometry/226`, `prealgebra/631`, `precalculus/1303`—show no visible diagram alteration. This is visual comparison of supplied text, not binary-file certification.

The historical claim that **10/11 corruptions were confirmed repaired** leaves the eleventh item’s status unspecified.

**Fix:** Before release, bind the final dataset, assembly code, verifiers, test results, and audit decisions to hashes. Replace ambiguous booleans with explicit outcomes such as “byte-identical” versus “approved prose-only exception.” Close every discovered defect with its row ID, exact patch, and post-patch verification.

The protection checker must be independent of the repair scanner. Reusing the scanner that corrupted text to certify its repair recreates the same blind spot.

**HIGH — F6. Keep the template-sibling flags, but use the 486-item subset for the primary arm comparison.**

`test/intermediate_algebra/1126.json` is flagged: **1/50 sampled rows**. I verified the flag’s presence, not the underlying training-row relationship. The brief reports **14/500** siblings overall.

Those 14 items can contribute up to **2.8 percentage points** to an arm gap on the full 500, which could matter for a close decision.

**Fix:** Prespecify **486 unflagged items as the primary comparison**, with full-500 and flagged-14 results alongside it. Use the union of contamination relationships across all arms. Retain the records and provide links to the relevant SFT rows and the matching rationale. Exact duplicates, translated duplicates, and template siblings should remain distinct categories.

**MEDIUM — F7. Some “Greek linguistic” counters are explicitly operational approximations.**

Rows **#32 and #271** disclose the clitic gate. It excludes legitimate possessive pronouns in constructions such as:

> «Το μικρό μου παιδί γελά.»

Here `μου` precedes a noun and is not sentence-final. The stated rule therefore undercounts grammatical pronouns by construction. Disclosure makes the operational requirement clearer; it does not make it a general Greek pronoun counter.

Similarly, #209’s treatment of `ξ` and `ψ` combines letter adjacency with a phonetic exception. That is a usable custom rule, but its name and claims should reflect the convention.

**Fix:** Describe these as operational counters; publish their banks and normalization rules. Validate against independently labelled examples. Do not turn their scores into claims about grammatical competence.

**MEDIUM — F8. Two local wording/provenance issues should be corrected.**

- **IFBench #0:** «Θα έπρεπε είναι να τα κάψει όλα…» contains a grammatical error. Also, its five keywords are **declinable**, contrary to the brief’s “indeclinable Greek keywords” account. Requiring their exact displayed forms is nevertheless clear and usable.
- **MATH `prealgebra/1128`:** «Δεν μπορείτε να κάνετε “συνδυασμούς”» broadly prohibits combinations, whereas the intended prohibition concerns mixing components from different pairs. The following example largely resolves the meaning.

**Fix:** Remove `είναι` in #0 and correct the keyword-provenance description. In the MATH item, use wording such as «Κάθε ζευγάρι πρέπει να χρησιμοποιείται ολόκληρο» followed by the existing example.

These are **one clear grammar defect in 40 IFBench rows** and **one localized wording defect in 50 MATH rows**, not estimates of total dataset defect rates.

**LOW — F9. Preserve inherited source defects in the audit record.**

IFBench **#139** ends with an unfinished action in English and Greek. MATH `algebra/733` inherits a malformed definition containing a bare `≤` without its bound.

**Fix:** Record these as upstream defects. Any substantive repair should produce a documented adapted item; silently completing only the Greek version would change the comparison.

**3) What is good and should not be changed**

- The MATH sample largely preserves mathematical meaning. I found **no unambiguous answer-changing translation defect among these 50 rows**. That is a bounded review result, not certification of all 500.
- `intermediate_algebra/1572` correctly translates the conditional prose inside `\text{}` while visibly preserving the branches and inequalities.
- The supplied diagram bodies appear preserved. Keep the byte-equality requirement for diagram code.
- IFBench **#61 and #62** now expose the exact request to repeat, matching their Greek kwargs.
- Exact keyword forms, explicit name banks, Greek quotation conventions, and transparent operational definitions improve reproducibility.
- The localized palindrome task is not inherently impossible: **«άκακα», «Σέρρες», «Σάββας»** are palindromes of at least five letters under accent removal and σ/ς folding. This supports feasibility under that convention; it does not justify treating three as equivalent difficulty to ten.
- Keep provenance, sibling flags, and the repair history. Generating descriptions from checker specifications is useful, provided an independent audit checks the specification itself.

**4) Answers to the specific questions**

**IFBench: prompt/checker agreement, Greek rules, overlap and extension**

I cannot certify agreement with unseen code or assess all 58 implementations from 32 represented IDs. The most important rule-specific checks are:

| Rule or primitive | Required check or clarification |
|---|---|
| Pronouns — #32, #271 | Separate grammatical pronouns from the declared operational count; test possessives, articles, clitics and `ό,τι`. |
| Conjunctions — #9 | Accent folding must not turn article `η` into conjunction `ή`. Confirm that `και/κι` represents one conjunction type. These are unexecuted test cases. |
| Stop words — #175 | Publish the actual finite bank. “Articles, prepositions, conjunctions…” does not uniquely determine a percentage. |
| Initial verb — #259 | Test genuine imperatives such as `Δες`, `Πες`, `Εξέτασε`, and noun negatives. The disclosed heuristic is not validation evidence. |
| Vowels — #269, #271 | Specify vowel **letters**, preferably `{α, ε, η, ι, ο, υ, ω}`, and handling of diaeresis and Latin text. |
| Syllables | Preserve distinctions needed for diaeresis and hiatus before counting; state the synizesis convention. No syllable item is supplied here. |
| Emoji | Distinguish codepoints from displayed emoji sequences; test modifiers, flags and ZWJ sequences. No sampled row permits implementation assessment. |
| Names — #26 | Multiple inflections of one name must not inflate the count of different names. |
| Sentence/word primitives | Test both Greek question-mark encodings, abbreviations, decimals, quoted punctuation, HTML, mixed scripts and empty-token cases. |

For incremental constraints such as **#75, #182, #189 and #190**, explicitly test one-line or one-sentence responses. Whether these pass is unknown. If they pass under the original operational contract, adding minimum lengths creates an adaptation requiring separate reporting.

The generalisation claim requires the class reporting in F4. The core/extension boundary should follow F3. The two replacement types are not identified in this sample, so I cannot approve their placement individually.

Also, describe the IF score as **verified constraint satisfaction**. Several underlying tasks require factual accuracy, useful explanations, or coherent writing that the listed constraints do not establish.

**MATH: scorer sufficiency, LaTeX changes and sibling flags**

The scorer evidence is insufficient for arm selection. Reference self-tests and narrow perturbations are useful initial tests, but they do not measure error rates on model responses.

The demonstrated `if`→`αν` change is safe. The other six claimed by-design differences cannot be approved without their exact patches. Permit only individually identified prose leaves; preserve mathematical operators, variables, quantities, ordering and diagram code. A `\text{}` block can contain an identifier or unit, so blanket permission to translate everything inside it is unsafe.

Keep original English rows and answers immutable. “Mathematical content preserved with approved prose exceptions” is supportable; “all LaTeX byte-identical” is not literally true.

The sibling flag is appropriate, with the primary/secondary scoring treatment in F6.

**Process: mandatory checks before freezing**

1. **Protect structure independently:** compare the ordered sequence and multiplicity of protected math and diagram segments. A bag of numbers or a span count cannot detect all swaps and reassociations.
2. **Allowlist exact exceptions:** record each permitted prose replacement inside LaTeX; reject changes outside those locations.
3. **Audit meaning beyond bytes:** check negation, quantifiers, bounds, units, referents and number words. Protected mathematics can survive while surrounding prose changes the problem.
4. **Review the final version:** inspect every repaired row and every exception after the last assembly pass. Regenerate all QC fields.
5. **Validate execution:** use independent positive/negative fixtures for all 58 IF types, satisfying witnesses for retained combinations, and the MATH response corpus described in F1.
6. **Freeze the actual model input:** diagram images versus raw Asymptote, rendering, answer instructions, token limits, and response extraction must be fixed across arms.

**Sample sizes and defensible quality claims**

The current sample supports these descriptive counts:

| Observation | Count |
|---|---:|
| IF overlap reference-rendering ambiguity | 2/40 = 5% |
| IF universal→existential thesis wording change | 4/40 = 10% |
| “Novel composition” rows with one listed ID | 15/20 = 75% |
| Clear IF grammar defect identified | 1/40 = 2.5% |
| MATH localized wording defect identified | 1/50 = 2% |
| Unambiguous answer-changing MATH translation defects found | 0/50 |
| MATH categorical Greek-answer scoring case requiring validation | 1/50 |

**Do not add these rates together:** they measure different properties, and several are metadata or validation findings rather than mistranslations.

From the brief, the historical counts mean:

- IF’s pre-fix task flags: **5/300 = 1.67%**; constraint flags: **12/300 = 4%**. Their union cannot be calculated without row-level overlap. These are not post-fix rates.
- MATH’s splice failures: **11/38 = 28.95% within the inspected repaired subgroup**. This is not a full-set estimate.
- The second MATH cross-check found **3/72 = 4.17%** meaning defects in its inspected version and sample. Selection details and subsequent fixes prevent treating that as the final defect rate.
- A clean 59-row check before later edits does not automatically certify the later artifact.

For a genuinely random final-file audit with **zero detected defects**, the one-sided 95% binomial upper bound is:

\[
p_{\mathrm{upper}}=1-0.05^{1/n}.
\]

Thus **0/59 supports an upper bound of approximately 4.95%**, assuming the auditor reliably detects the defined defect class. It does not support “zero defects,” “99% clean,” or a verifier false-acceptance rate.

For a **1% threshold**, a general binomial plan needs **299 zero-defect observations**. Exploiting these fixed finite populations, exact sampling without replacement needs **189/300 IF items** or **225/500 MATH items** to reject a defect count of at least 1% after zero findings.

The planned **59 per set is a reasonable initial native audit**, with two additions:

- Preserve the random sample for the rate claim; audit repaired rows, exceptions, suspicious cases and missing constraint types separately.
- Add coverage across all 58 IF types and MATH answer types. Randomly auditing 59 prompts does not guarantee that coverage.

Each 59-item result supports a separate 95% statement. For a conservative simultaneous statement covering both sets, use **72 zero-defect random items per set** under the binomial/Bonferroni calculation. All these bounds concern the specified, detectable defects—not errors the auditor systematically misses.

**5) Open questions for the owner**

- What are the exact frozen dataset, verifier and upstream-scorer hashes?
- What is `ratio:overlap`’s formula, and what satisfying witness passes #152?
- What does `faithful` mean, and which primitive compositions justify the 15 single-ID “novel composition” labels?
- What happens when the scorer receives `έλλειψη` for `intermediate_algebra/860`? Which 11 references lacked digit-perturbation tests?
- What are the seven exact LaTeX exception patches, and what happened to the eleventh previously corrupted row?
- Which SFT rows substantiate the 14 sibling flags, and is the exclusion mask shared across arms?
- Will the native audit inspect the final hashed files and independently labelled response/checker behavior, as well as prompt readability?