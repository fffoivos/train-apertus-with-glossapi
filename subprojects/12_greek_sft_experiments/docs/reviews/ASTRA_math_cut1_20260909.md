# Astra review: math_cut1

Date 2026-09-09 18:24 · model gpt-6-astra (asserted from rollout rollout-2026-09-09T18-16-00-01a086bd-7bd3-7471-a210-d81d03dfbb7b.jsonl) · effort xhigh · 8.9 min · prompt 69,007 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_math_cut1.md` · sample 60 rows of `data/math/review_samples/pilot_sample.jsonl` seed 1

**1. Verdict**

**Cut1 should not enter training through the current acceptance checks unchanged.** In the 60 supplied rows—14 GSM8K translations, 16 MATH translations and 30 native problems—I found no incorrect *intended numerical result*, but that does not establish target validity: there are **five checker-label or answer-completeness anomalies**, four problems needing explicit assumptions, and four inputs containing raw diagram code. The most consequential defect is verification that accepts incomplete multipart answers while rejecting equivalent symbolic answers. Repair admission checks and affected rows for cut1/cut2; preserve completed pilots as audit evidence. The reported 95.5% fidelity and 97.8% agreement are pipeline statistics, not demonstrated correctness rates.

**2. Findings ranked by severity**

I manually checked the supplied problems, calculations, answer fields and labels. I could not execute the checker, inspect cut1, retrieve the evaluation set or access research sources live: execution and browser access were unavailable. Counts below describe this sample only; findings overlap and should not be added into one “bad-row rate.”

**BLOCKER — B1. The answer checker does not enforce complete, typed answer equivalence.**

Five rows expose distinct problems:

| Row | Evidence | Assessment |
|---|---|---|
| `math_184` | `final_used: "π κυβικές ίντσες"`, `ref: "\\pi"`, `correct: false` | False rejection. Each piece has volume π cubic inches. |
| `nat_25_4` | `"37/135"` versus `"37 : 135"`, `agree: false` | False rejection of equivalent representations of the requested ratio. |
| `nat_41_1` | Primary final gives `(α) 34 m, (β) 656 €`; `final2` gives only `"656 €"`; `agree: true` | Missing part (α) accepted. |
| `nat_41_3` | Primary final gives `(α) 50 m², (β) 510 €`; `final2` gives only `"510 €"`; `agree: true` | Missing part (α) accepted. |
| `nat_97_2` | Primary final gives only `"0,5 m/min"`; second final includes 5 minutes and 0.5 m/min; `agree: true` | Incomplete **primary training final** accepted. |

That is **5/60 flag/contract anomalies (8.3%)**, comprising two false rejections and three accepted incomplete comparisons. **Three of the nine explicitly multipart native rows (33.3%)** exhibit the completeness problem. The missing answers appear in the solution bodies, so these are not failures to calculate them.

**Concrete fix:**

- Define answers by requested component: labels, values, units, and answer type. Require every component.
- Compare exact integers and rational numbers exactly; handle symbolic expressions such as π symbolically.
- Interpret `37 : 135` as a ratio when the requested type is a ratio. Distinguish ratios, clock times, decimal commas and coordinate separators.
- Convert compatible units rather than discarding them. `3 dm` and `3 m` must fail equivalence.
- Apply numerical tolerance only when approximation is warranted. A blanket 0.1% tolerance can conceal incorrect exact answers.
- Make these five rows regression cases, alongside deliberately wrong units, missing components and swapped component assignments.

For `nat_97_2`, the primary final must become:

> «Απάντηση: (α) 5 λεπτά, (β) 0,5 m/min»

The observed evidence establishes a contract failure; without code, I cannot determine whether its implementation uses suffix matching, numeric subsequences or another mechanism.

**HIGH — H1. Four problems need assumptions stated before they become authoritative training targets.**

These are **four wording/modeling concerns**, not four demonstrated arithmetic mistakes.

| Row | Evidence and consequence | Concrete fix |
|---|---|---|
| `nat_11_3` | «δεξαμενή με ορθογώνια βάση» specifies the base, but not a constant cross-section. The solution assumes volume = base area × height. | Specify a tank shaped as a rectangular prism, with sufficient capacity. Then 60 dm³ / 20 dm² = 3 dm follows. |
| `nat_97_2` | One conveyor belt has speed 0.9 m/min in the first zone and requires 0.5 m/min in the second. A single continuous, inextensible belt cannot maintain different steady speeds along its sections. | Specify two independently driven conveyors and negligible transfer time. |
| `gsm_221` | «στα οποία περιλαμβάνονταν 5 … και 6 …» does not explicitly make those 11 books the exhaustive remainder. The answer 46 assumes they are. | Say the remaining books **were** five Western novels and six biographies. |
| `math_131` | Buying 40 and 24 pencils implies a greatest-common-divisor constraint only if both purchases contain whole packages exclusively. | Add «Αγόρασαν μόνο ολόκληρες συσκευασίες, χωρίς μεμονωμένα μολύβια.» |

The two translated ambiguities are **inherited from the English**, not introduced by the translator. Nevertheless, reference agreement cannot certify that their Greek training prompts determine the answer.

**HIGH — H2. Grade-based verification routing is poorly aligned with actual risk.**

All **30/30 native sample rows have second solves**. Therefore this sample provides **no direct measurement of the proposed unverified production branch**.

Applied to these rows, the cut policy would leave **20/30 native rows unchecked by a second solver**. Meanwhile, at least **6/10 Lykeio rows** require only earlier arithmetic or elementary linear reasoning:

- `nat_25_1`: price ratio and one linear equation.
- `nat_60_1`: perimeter, distance and time.
- `nat_79_4`: remaining fraction of a budget.
- `nat_5_4`: reverse VAT and discount.
- `nat_97_2`: distance/time divisions.
- `nat_59_3`: multiplication, subtraction and exact division.

Conversely, non-Lykeio rows include formal systems (`nat_40_1`), geometric modeling (`nat_11_3`), multipart quantities and mixed-unit calculations.

**Concrete fix:** run inexpensive deterministic checks on **every** row, then route additional verification by features: multipart output, units, diagrams, domains, probability assumptions, ambiguity, and unsupported answer types. Independently solve rows that cannot be checked adequately, across grades, and audit a random sample of apparent passes.

A second Sol solve can help, but it is not an independent correctness certificate. Neither is Sol–Luna agreement: errors and assumptions can be shared.

**HIGH — H3. Raw Asymptote requires an explicit input-format gate.**

**4/16 MATH rows (25%; 4/60 overall)** contain `[asy]` code:

- `math_72`
- `math_146`
- `math_227`
- `math_6`

For **three**—`math_146`, `math_227`, `math_6`—the drawing/code supplies essential information. `math_72` is numerically solvable from the prose alone.

The code contains usable information; these are not automatically unsolvable. The problem is that the brief does not establish whether the deployed model receives rendered images, executable diagram support, or intentionally code-based geometry questions.

**Concrete fix:** quarantine these inputs until their representation matches deployment. For a Greek text-math target:

- Express `math_227` explicitly as the addition `abc + dca = 1000`, with distinct digits and nonzero leading digits.
- Give equivalent textual/grid descriptions for `math_146` and `math_6`.
- Remove the unnecessary diagram from `math_72`, adjusting vertex-specific explanation if necessary.

Re-solve the converted prompt. Do not simply strip `[asy]` blocks.

**HIGH — H4. The reported contamination check is insufficient for benchmark clearance.**

I cannot verify contamination counts without the MGSM reference set and source manifests. The reported character-5-gram threshold does not establish semantic separation after names, places, wording and numbers are changed.

There is also an observable internal split risk: **`nat_21_0` and `nat_21_1` are a closely matched template pair**—ticket-category systems followed by a speed-increase/time-saving quadratic. Different numbers and destinations do not make them independent evaluation families.

**Concrete fix:**

- Preserve canonical source IDs, dataset revisions and original split membership.
- Check overlap with the underlying English benchmark questions as well as the Greek text.
- Partition generated siblings and close templates together before development/test assignment.
- Supplement lexical matching with semantic retrieval and review of the closest matches.
- Recheck the final edited artifacts.

This is a required clearance control, **not an allegation that a sampled row is contaminated**.

**MEDIUM — M1. Grade labels and forced contexts need calibration.**

The six Lykeio examples above show why grade cannot stand in for difficulty. At the other end:

- `nat_40_1`, labeled Α΄ Γυμνασίου, uses formal two-variable elimination.
- `nat_85_4`, labeled Δ΄ Δημοτικού under “systems and quadratics,” instead uses accessible arithmetic comparison. **Do not reject it merely because the topic label sounds advanced.**
- `nat_90_2` uses explicit ΕΚΠ terminology, although its listing-of-multiples method is accessible.
- `nat_40_1` assigns four eggs to each *serving* of spinach pie. Changing «μερίδες» to whole pies would make the quantities more plausible.

These are prerequisite and realism judgments, not verified claims about the current official Greek syllabus.

**Fix:** define prerequisite skills and permitted solution methods per grade; allow explicitly tagged revision problems in later grades.

**MEDIUM — M2. Correct outcomes sometimes conceal weak explanations or invalid unit notation.**

Concrete examples:

- `math_131`: `40 = 5 · 8` and `24 = 3 · 8` establish that 8 is common, but do not explain **greatest**. Add coprimality of 5 and 3, or a short Euclidean calculation.
- `nat_25_4`: the solution calculates the purchase-price parameter `x = 1,50`, then never uses it. The purchase-price ratio is unnecessary because the total acquisition cost is already known. Thus this row has **another irrelevant datum** beyond the advertised sign width.
- `nat_41_3`: «χρέωση για κάθε τετραγωνικό μέτρο» is followed by `100 : 50 = 2 €`; the rate should be **2 €/m²**.
- `nat_96_3`: `1 ώρα · 60 = 60 λεπτά` and `255 λεπτά : 60 = 4 ώρες και 15 λεπτά` are invalid literal quantity equations. Use `1 ώρα = 60 λεπτά` and `255 λεπτά = 4 ώρες και 15 λεπτά`.

**Fix:** check intermediate equations, dimensions and whether explanatory work contributes to the answer. An answer-guarded language editor cannot certify these properties.

**LOW — L1. Greek editing and the line-granularity rule need refinement.**

Specific edits:

- `math_273`: «Ο τελευταίος μη μηδενικός υπόλοιπος» → **«Το τελευταίο μη μηδενικό υπόλοιπο»**.
- `math_72`: «Η γωνία A δεν μπορεί να είναι η κορυφή» → **«Η Α δεν μπορεί να είναι η γωνία της κορυφής»**.
- `gsm_48`: «τεμάχια παραγωγής» is awkward; ask for the total number of corn cobs and potatoes.
- `gsm_23`: kindergarten children are included among children of the primary school. Specify a shared kindergarten/primary-school complex.

The literal “one operation per line” rule is contradicted by **at least 8/60 rows** with explicit multiple numerical operations: `gsm_96`, `math_109`, `gsm_182`, `math_6`, `nat_49_3`, `gsm_255`, `gsm_66`, `gsm_188`. This is a conservative count, excluding algebraic transformations.

**Fix:** require **one meaningful reasoning step per line**, permitting short expressions. Mechanically splitting every sum would make examples such as `nat_95_0` and `math_146` unnecessarily long.

**3. What is good and should not be changed**

- **The arithmetic is substantially sound.** Manual recomputation supports the intended numerical results, including the ticket systems, speed quadratics, ratio/profit problem and diagram-derived answers.
- **All 60 primary solutions end with «Απάντηση: …».** Preserve this interface while enforcing completeness.
- Greek decimal commas, thousands dots, euro placement, and terms such as **ΜΚΔ, ΕΚΠ, διακρίνουσα, ημ** are useful localization choices.
- There are genuine explanations: independence in `math_163`, exclusion of a negative speed in `nat_21_0`/`nat_21_1`, and the obtuse-triangle argument in `math_72`.
- The arithmetic method in `nat_85_4` is a good scaffold toward systems. Preserve method diversity.
- Keeping inches in `math_184` and feet in `gsm_255` preserves the original mathematics. These **2/30 translated rows** are incompletely localized, but retaining those units is not a correctness failure.
- Preserve original English text, change descriptions, second solves and disagreement records. In particular, **repair the rejection of `math_184` and `nat_25_4`; do not discard their correct mathematics.**

**4. Answers to the specific questions**

**Q1 — Translation and localization**

I found **0/30 translation-induced changes to the numerical relationships or intended answer**. That is a manual sample finding, not a population fidelity estimate.

There are **two inherited assumption gaps** (`gsm_221`, `math_131`), **two concrete Greek wording/local-context edits** (`gsm_48`, `gsm_23`), and **two retained imperial-unit cases** (`math_184`, `gsm_255`). These categories overlap conceptually and should not be treated as a single error rate.

Currency replacement preserves the supplied numerical arithmetic. Fictionalized Greek places and events should be treated as story settings, not claims that the named events exist.

**Q2 — Quality as an 8B training target**

Generally suitable after filtering: most solutions expose an operation sequence rather than only supplying a result. The weaknesses are uneven conceptual justification, redundant narration, and occasional notation errors—not wholesale absence of reasoning.

Prioritize short explanations of **why** the operation applies: which quantity a percentage refers to, why a denominator is chosen, why a root is rejected, and why a divisor is greatest. Keep routine arithmetic compact.

**Q3 — Native realism, grades and multipart answers**

There are **9/30 explicit (α)/(β) problems**. One primary final omits a requested component, while two secondary finals do so.

“One clear final answer” should mean **one complete final record**, potentially containing several labeled values. It should not mean “extract the final scalar.”

The grade labels are too coarse for difficulty routing. Use prerequisites and measured model performance; retain easier revision material without calling it intrinsically Lykeio-level difficulty.

**Q4 — Verification and likely error concentrations**

Likely concentrations are **inferred**, not measured here: missing subanswers, unit/time interpretation, unstated geometric assumptions, probability sample spaces, rounding, integer feasibility, and algebraic domain restrictions. These occur across grades.

The cheapest useful addition is **generation from structured parameters plus independently implemented recomputation**:

- exact rational arithmetic for money, fractions and ratios;
- substitution into all original equations for systems;
- positive/integer/domain checks;
- dimensional conversion;
- enumeration for small probability spaces;
- labeled completeness checks for multipart answers.

Recomputing a generator’s proposed equation checks its arithmetic, **not whether the equation models the Greek question**. Retain semantic audits and independent solves for that gap.

**Q5 — Literature and recipe changes**

The references below are primary-source pointers from background knowledge; I could not freshly inspect them here. The proposed allocation is my recommendation, not a literature-established optimum.

| Research direction | Implication for this dataset |
|---|---|
| [GSM8K: Training Verifiers](https://arxiv.org/abs/2110.14168) and [MGSM](https://arxiv.org/abs/2210.03057) | Keep substantial coverage of ordinary multistep word problems. Test whether Greek language access, mathematical reasoning, or both improve through paired English/Greek development items. |
| [MATH](https://arxiv.org/abs/2103.03874) | Use competition problems selectively. Source difficulty levels are not Greek school grades: compare elementary `math_298` labeled Level 3 with vector algebra in Level 1 `math_235`. |
| [GSM-Symbolic](https://arxiv.org/abs/2410.05229) and [GSM-Plus](https://arxiv.org/abs/2402.19255) | Add controlled changes to quantities, wording and requested unknowns. Include structural changes requiring a different operation, with recomputed references. |
| [GSM-IC: Irrelevant Context](https://arxiv.org/abs/2302.00093) | The **10 native rows** explicitly tagged with irrelevant information are a useful start, but their distractions are generally easy to separate. Add plausible competing quantities and paired relevant/irrelevant versions. |
| [Process supervision / PRM](https://arxiv.org/abs/2305.20050) | Add first-error identification and correction. Correct final answers alone do not certify valid intermediate steps. I cannot confidently identify the intended **MathCheck** paper/version without its citation. |
| [MathDial](https://github.com/eth-nlped/mathdial) | Add a small tutoring component: respond to a student attempt, diagnose a misconception, give a proportionate hint, then solve when requested. This sample contains **0/60 multi-turn tutoring examples**. |

A concrete **cut2 starting ablation, by training tokens**, would be:

- **50%** ordinary Greek multistep arithmetic, fractions, ratios, money and units.
- **20%** controlled perturbations and context-robustness pairs.
- **15%** scaffolded probability, systems/quadratics and trigonometry.
- **10%** error identification and repair.
- **5%** multi-turn tutoring.

Cap competition-style MATH at roughly **10% of total tokens**, within the applicable categories. That cap is an experimental starting point, not an established optimum.

The reported **37% greedy versus 61% pass@4** suggests useful solutions may already be reachable for additional problems. It does not establish 61% deployable accuracy: pass@4 requires recognizing a successful candidate. Test verification/selection separately.

The main competition-translation risk is spending training capacity on symbolic formats, hidden diagrams and assumed prerequisites that transfer poorly to Greek MGSM. Conversely, translated elementary MATH rows can be perfectly relevant. Select by skills and evidence of transfer, not source name alone.

**Q6 — Anything that must not be trained on**

Exclude from accepted cut1 targets until repaired:

- incomplete primary answers, concretely `nat_97_2`;
- wording whose answer depends on unresolved assumptions, as in H1;
- diagram-dependent inputs whose usable representation is absent;
- solutions with invalid intermediate equations left uncorrected;
- any confirmed evaluation overlap;
- intentional erroneous solutions presented as correct assistant targets.

Error-spotting data may contain wrong work **inside the task being critiqued**; the supervised assistant response must identify and repair it.

**5. Open questions for the owner**

1. What exactly is “Greek MGSM”—repository, revision, translator, source question IDs and evaluation prompt? The original MGSM release I know did not include Greek; identify the derivative used here.
2. Are 0.524 and 0.676 measured with identical questions, prompts, decoding and scoring? Provide item-level results.
3. What does the checker actually compare: final fields, entire solutions, numeric subsequences, or only the last quantity? How does it explain the five cases above?
4. Which fields become assistant training text? Are rejected pilot rows included only for review, or can they reach cut1?
5. Does the correction pass edit problems as well as solutions? Are full answer checks and semantic checks rerun afterward?
6. What curriculum/prerequisite map governs generation, and how are five-row cell siblings partitioned across training and evaluation?
7. What are cut1’s source proportions and token allocation? How was pass@4 calculated, and was candidate selection evaluated?
8. Which MathCheck reference/version should this review assess?