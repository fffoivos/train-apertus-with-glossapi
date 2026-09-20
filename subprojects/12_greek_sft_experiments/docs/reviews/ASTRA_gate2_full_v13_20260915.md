# Astra review: gate2_full_v13

Date 2026-09-15 18:21 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T18-14-32-01a0a5a2-4cab-71a3-9806-71935496d04f.jsonl) · effort xhigh · 6.5 min · prompt 274,454 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v13.md`

## 1. Verdict

**HOLD GATE 2 for V13-H1: the approval comparator still accepts unequal numbers after deleting meaningful whitespace.** The specific v12 `\leftarrow`/`\rightarrow` defect is fixed in the supplied approval code. The expanded TRL audits support closing the label-transfer finding for the tested cohorts. However, `1 2/3` is converted into `12/3` and can agree with `4`. I also found a recurring ambiguous GSM question, two published MATH answers containing rendering-code dumps, and an under-specified MC demonstration. **Scope:** I inspected the supplied code, rows and logs and independently recalculated totals and normalization examples; I did not execute the Python modules, recompute file hashes or rerun the cluster audits. Sample rates below describe these supplied samples, not estimated corpus-wide rates.

## 2. Findings ranked by severity

### V13-H1 — HIGH: whitespace removal changes mixed numbers into different fractions

**Evidence:** `agree()` accepts `sep_canon(r) == sep_canon(c)` before numeric parsing. `sep_canon()` deletes whitespace. Independently, `_strip_wrappers()` deletes the same whitespace before `SLASH` parses a fraction.

These three constructed counterexamples follow directly from the supplied code:

| Reference | Answer accepted | Actual values | Acceptance path |
|---|---|---|---|
| `1 1/2` | `11/2` | \(3/2 \ne 11/2\) | `exact` |
| `1 2/3` | `4` | \(5/3 \ne 4\) | `numeric`: reference becomes `12/3` |
| `-1 1/2` | `-11/2` | \(-3/2 \ne -11/2\) | `exact` |

**Count:** 3/3 constructed probes expose false agreements. **No affected solve-record ID has been established.** This is a demonstrated comparator defect, not a measured dataset error rate.

**Concrete fix:** classify mixed-number syntax before either whitespace-insensitive identity or numeric parsing. Parse it exactly, or conservatively reject it; do not concatenate its digits. Preserve legitimate spacing inside LaTeX fractions. Add the counterexamples and correct-equivalence controls, re-decide all 12,028 records, publish changed IDs with both answer strings, and rebuild/rebind affected artifacts.

**Disposition:** required before lifting HOLD.

### V13-M1 — MEDIUM: the previously excluded “times older” ambiguity recurs

**Evidence:** `math_en_gsm:392457#1` says:

> “Job is 3 times older than Bea.”

The solution takes Bea’s age as 15 and Job’s as \(3×15=45\), producing Harry’s age **26**. Reading “three times older” additively gives Job \(15+3×15=60\), hence Harry **33.5**. The exclusion ledger already applies this distinction to another age problem.

**Count:** **1/5 English GSM sample rows, 20%,** has this ambiguity. This does not establish a 20% block-wide rate.

**Concrete fix:** exclude this problem family across English solution rows, replay copies and any Greek twin, or repair the wording to “three times as old” and revalidate. Search the remaining pool for this construction instead of discovering it one ID at a time.

### V13-M2 — MEDIUM: rendering-code contamination remains in published MATH targets

**Evidence:**

- `math_en_math:math_train_7385` contains an extensive `[asy] … [/asy]` block inside the projection solution.
- `math_en_math:math_train_6030` begins with an `[asy]` clock-rendering program.

Both mathematical answers are correct: \((-5/2,5/2)\) and \(150^\circ\). The defect is unsolicited rendering source in the assistant target—the same defect class previously used to exclude `math_train_1379`.

**Count:** **2/5 published MATH sample rows, 40%,** contain these dumps. This is a target-cleanliness rate, not a wrong-answer rate.

**Concrete fix:** remove the assistant-side rendering spans from these two self-contained explanations, or exclude all their replay occurrences. Scan the remaining published block for `[asy]`; review diagram-dependent cases separately before removing anything.

### V13-M3 — MEDIUM: an MC demonstration lacks conditions that make its answer unique

**Evidence:** §D builder row `mc_openbookqa_2552`, demonstration ID **`openbookqa:bfc5c7c9583f`**, asks:

> “Which ingredient may cause chemical change?”

Choices are almonds, milk, citrus juice and olive oil; the supervised answer is **C**. No receiving substance or reaction is specified. The other ingredients can also participate in chemical changes. Citrus juice becomes uniquely defensible only with an unstated scenario.

**Count:** **1/7 answer-bearing MC turns across the three §D builder examples** is under-specified. Separately, I found no definite wrong letter in the **15 answer-bearing turns across the five §H format rows**.

**Concrete fix:** remove this source question from both target and demonstration pools, or supply an explicit reaction context and revalidate the choices. Report occurrences by stable source-question ID; the excerpt does not establish its final-manifest multiplicity.

### V13-M4 — MEDIUM: conversation review should operate at the reused-answer level

**Evidence:** the owner reports **2,259/2,851 source rows = 79.2%** contain an assistant turn reused in at least three rows, involving 554 distinct turns and up to 40 copies. The final training block contains **3,364 rows from 1,682 pre-replay training rows**. These are different denominators.

The exclusion history demonstrates that one defective answer can propagate across many conversations. Nevertheless, all **5/5 current conversation final-turn tasks** pass the checks I could perform directly.

**Concrete fix:** maintain a review inventory keyed by assistant-answer content hash, recording source occurrences, surviving train/dev occurrences and effective replay weight. Review reused answers once with their relevant contexts, then apply exclusions to every occurrence. Report unique-answer coverage alongside row counts.

**Disposition:** logged. Reuse alone does not justify a new HIGH or wholesale block removal.

### V13-M5 — MEDIUM: the benchmark comparator retains false-positive routes fixed in approval

**Evidence:** the separately supplied `equiv500()` still:

- collapses `\leftarrow` and `\rightarrow` through substring removal;
- accepts `\text{ellipse}` versus `\text{hyperbola}` after both normalize to empty strings;
- accepts `x` versus `X` through categorical case-folding.

**Count:** three constructed false-positive pairs; no affected evaluation-item count or score change is established.

This does **not** reopen the repaired approval-library arrow finding: approval now uses a different path. It limits what can be concluded from the extended benchmark score.

**Concrete fix:** version and test the scorer for queued evaluations, retain the separately reported upstream metric, and audit actual prediction/reference pairs before claiming numerical impact. Preserve completed pilot reports and attach notes rather than silently changing their results.

### V13-L1 — LOW: the self-test count is overstated

**Evidence:** the visible test list contains **151 cases**, matching the finalizer log. The opening summary and §J claim **152**.

**Concrete fix:** generate the documented count from the actual run. This discrepancy alone does not demonstrate a stale comparator artifact.

## 3. What is good and should not be changed

- **Positive approval joins and input binding:** the assembler revalidates approved solve records against the solve file, manifest and composite comparator identity.
- **All-occurrence overlays:** the supplied implementation replaces every matching inherited occurrence; **29 overlays × 4 occurrences = 116 replacements**, matching the receipt.
- **Global ID protection:** suffix reservation, config prefixes and the final train-plus-dev uniqueness assertion address the reported collision mechanisms.
- **Explicit supervision policy:** retain `pretokenized_masks: true`, the declared supervision of MC demonstrations and the decision excluding masked rows from this pass.
- **Improved audit controls:** complete cohort coverage, token-level comparisons and a clean-path negative control are materially stronger evidence than the earlier one-batch inspection.
- **Useful sample quality:** the Greek mathematical derivations checked out. Conversation recall and transformation tasks also pass: `S1_00386#1` reproduces the fourth user message, `S1_00743` correctly answers **5**, and the requested removals of «επικοινωνία» and «περάσει» succeed.
- **Receipt arithmetic reconciles:** block totals sum to **379,508 training rows** and **146,208,753 nominal assistant-content tokens**. The supplied dev accounting yields **2,354 rows**.

## 4. Answers to the brief’s specific issues

| Issue | Assessment |
|---|---|
| **Can V12-H1 be closed?** | **Yes, narrowly.** Command-boundary removal preserves the supplied arrow distinctions. V13-H1 is a separate remaining normalization defect. |
| **Are the other v12 fixes supported?** | The supplied code/receipt addresses the four stem bans, `math_train_3060`, repeated overlay occurrences and global uniqueness. The content-search exclusions are documented; I have not independently established zero surviving copies from the full manifest. |
| **Does F1 now inspect the actual training path?** | **Yes, for the audited cohorts.** The script constructs the trainer, obtains its dataloaders and compares collated labels. The supplied logs report zero discrepancies for the 4-row and 40-row pretokenized cohorts. |
| **How large is the demonstrated raw-path defect?** | **23/15,943 supervised tokens = 0.144%** in the selected 40-row cohort, with the same total deficit in its eval audit. Neither 34% nor the 16% exposure figure is a supported corpus-wide faulty-label rate. |
| **Is production GPU execution validated?** | **No.** The audits use a 4,911,584-parameter stand-in. They establish label transfer under the tested setup, not a successful 8B FlashAttention training run. Retain the declared watched startup. |
| **Are all rows within the rendered window?** | The supplied full-render logs report **0 over-window rows**, with maxima **4,032 train / 4,019 dev**. The exact rendered training total is **219,937,982**, distinct from the assembler’s **224,648,088** estimate. |
| **Does blind agreement certify the training solutions?** | **No.** It checks source-label agreement with the blind answer. English GSM additionally checks the generated boxed answer; that still does not certify reasoning, ambiguity or Greek translation fidelity. |
| **Does the pilot qualify this maths change?** | **No.** The primary result is −1.4 pp and fails the frozen advancement rule. The authorized from-scratch pass is a separate experiment; its results cannot establish an individual block’s effect because data and supervision both change. |
| **Should convskills be dropped wholesale?** | The current sample supplies no new basis for mandatory removal. Retaining its existing weight is consistent with the approved recipe, with the reused-answer review gap explicitly logged. Do not treat replayed rows as independent coverage. |
| **Can the gate be lifted now?** | **No: resolve V13-H1 and show the resulting decision delta and bindings.** The MEDIUM/LOW findings remain logged under the stated disposition. |

## 5. Open questions for the owner

1. Do any of the 12,028 reference/answer pairs—or retained GSM solution answers—contain mixed-number whitespace? Provide IDs, strings and decisions before and after the fix.
2. How many of the **554 reused assistant turns** have been reviewed, and what are their surviving effective training weights?
3. Which exact scorer version will govern promotion, and how will its extended MATH metric be distinguished from the upstream score?
4. After the next comparator change, can the review packet include one consistent set of test count, decision delta, manifest hashes and launch bindings?