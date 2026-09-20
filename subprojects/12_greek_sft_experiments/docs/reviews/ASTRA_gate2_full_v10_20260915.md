# Astra review: gate2_full_v10

Date 2026-09-15 15:52 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T15-47-42-01a0a51b-e02b-7f60-ac47-eec729226423.jsonl) · effort xhigh · 5.3 min · prompt 246,071 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v10.md`

## 1. Verdict

**HOLD on V10-H1, one HIGH finding.** The specific v9 `strip_string` fallback and deficit-mode exit-order defects have been repaired, but the comparator still accepts list–number collisions through identity shortcuts that run before structural checks. This prevents approval of the label gate. The supplied training-path audits support closing V9-H2 and F1 for the tested configuration and cohorts. I reviewed all **25 §H rows**, the **9 MC question–answer turns in §D**, and the supplied code and logs; I independently recalculated the totals and reproduced two normalization collisions. I could not execute the repository’s Python, inspect actual files/hashes, or rerun cluster checks. MEDIUM/LOW findings below are notes under your disposition rule; completed pilots require no drastic action.

## 2. Findings ranked by severity

### V10-H1 — HIGH: identity shortcuts still bypass list–number separation

**Evidence:** `agree()` removes whitespace and LaTeX spacing before calling `numeric_value()` or checking list structure. `equiv_exact()` likewise accepts `canon(r) == canon(c)` before rejecting a list/non-list mismatch.

These pairs are therefore accepted:

| Reference | Answer | Acceptance route | Why incorrect under the declared policy |
|---|---|---|---|
| `1, 000` | `1,000` | `exact` | The first is detected as a list; the second parses as 1000. |
| `45, 045` | `45,\!045` | `exact` | A list becomes indistinguishable from explicitly formatted 45045. |
| `(1, 000)` | `\left(1,\!000\right)` | `symbolic`, through `canon` | A two-element tuple becomes indistinguishable from parenthesized 1000. |

I reproduced the first two normalization collisions using the pasted regex in JavaScript. The third follows directly from the supplied Python branches; I did not run the Python comparator.

The existing test `('1, 000', '1000', False)` misses the equivalent thousands-form answer. Existing expected-true tests such as `('17,44', '17, 44', True)` also conflict with treating the first string as a decimal and the second as a list.

**Count:** three concrete counterexamples, **not three observed defective dataset rows**. The supplied material does not establish their prevalence among the 12,028 decisions.

**Concrete fix:**

- Preserve separator meaning before every normalized-identity shortcut.
- Classify explicit tuples/lists and numeric thousands notation before removing spacing.
- Resolve ambiguous bare commas through a declared format/type rule; conservatively reject ambiguous cross-type matches.
- Keep legitimate tuple equivalences such as `(1,2)` versus `(1, 2)`.
- Add these regressions, re-decide all 12,028 records, publish the changed IDs and pairs, and rebuild affected approval/receipt bindings.

Fixing only `_norm()` again will not close this finding.

### V10-M1 — MEDIUM: two sampled maths prompts do not justify the solution’s interpretation

**English GSM: `math_en_gsm:1682197` — 1/5 sampled GSM rows.**

> “I'm three times older than I was six years ago.”

The target chooses \(x=3(x-6)\), giving 9. “Three times older” also permits the additive reading \(x=4(x-6)\), giving 8. This is the same ambiguity family as the previously excluded “3 times more” problem.

**Greek: `greek_math_v2:c2_gsm_1120#1` — 1/5 sampled Greek maths rows.**

The prompt places berries and small animals in summer, then acorns and salmon in autumn:

> «Από τους σολομούς πήρε το μισό από το βάρος που της απέμενε να πάρει.»

The solution calculates the remainder after berries and acorns while omitting the earlier small-animal gain. Under its answer of 200 pounds from small animals, the gain before salmon is \(200+200+400=800\); the remaining amount is 200, so half is **100**, not the solution’s 200.

**Count:** **2/15 sampled maths rows** have an ambiguity or interpretation defect. This is not a counted arithmetic-error rate or a population estimate.

**Concrete fix:** rewrite the age stem as “three times as old.” For the bear, explicitly define the salmon allocation as half of the amount remaining **after subtracting only berries and acorns**, without implying chronological remaining weight. Apply any eventual correction/exclusion by problem family and inspect language twins.

### V10-M2 — MEDIUM: under-specified MC demonstrations remain supervised

**§D: 2/9 question–answer turns are under-specified**, both in `mc_openbookqa_4872`:

- **“What does harming an organism cause?” → C, population decrease.** Harm need not kill the organism or reduce population size. B, change in appearance, can also occur.
- **“A magnet will stick to … a belt buckle” → A.** The buckle’s material is unspecified—the same defect class as the previously banned door-handle question.

That row also contains the opaque demonstration **“The sea is … A mega Museum.”** I flag it for rewriting but do not include it in the two-question ambiguity count.

**§H: 1/16 MC question–answer turns has another defensible option**, in `format_mc:mc_openbookqa_2021`:

> “Which of these **could** add unwanted contamination to the natural environment?”

D, burning liquid petroleum, is defensible. B, hoarding trash, could also contaminate the environment; the stem provides no containment/disposal conditions that exclude it.

**Concrete fix:** revise or remove the source questions from the pool, covering demonstrations and targets. Check resulting occurrences through `target_sid` and `demo_sids`. Merely removing a sampled assembled row leaves other exposures.

These are reviewer-counted ambiguities in the supplied examples, not an estimated error rate for all 8,175 training rows.

### V10-M3 — MEDIUM: an otherwise correct MATH target trains an unsolicited rendering-code dump

**Evidence:** `math_en_math:math_train_1379` correctly answers **1 x-intercept**, then emits a long `[asy] ... [/asy]` program.

**Count:** **1/5 sampled published-MATH rows** contains this output-format problem. I found no mathematical answer error in those five rows.

The prompt does not request Asymptote code, and the explanatory paragraph already establishes the answer.

**Concrete fix:** remove this optional assistant-side rendering block while retaining the explanation. Screen other `[asy]` occurrences separately; do not indiscriminately remove diagrams needed to understand a problem.

### V10-L1 — LOW: the transit answer does not separately resolve top-up activation

**Evidence:** `convskills_v2:S2_00809` asks whether mobile top-up activates automatically and eliminates a subsequent machine interaction. The answer establishes only:

> «Η προσωποποιημένη ThessCard πρέπει να επικυρώνεται στο λεωφορείο…»

Journey validation does not, by itself, establish how a mobile top-up becomes available.

**Count:** this completeness gap occurs in **1/5 sampled conversation rows**. I could not verify the linked FAQ and am **not counting the transport claim as factually false**.

**Concrete fix:** verify the activation procedure and distinguish it from validation on boarding, preserving the persistent 20-word limit.

### V10-L2 — LOW: current documentation still mixes comparator versions

**Evidence:**

- The introduction says **101 tests**; the final §J entry says **123**.
- The delta headed **“previous finalization v8.1 → v9”** shows **11,000 → 11,034**. §J identifies the 34 restored pairs as the **v10.0 → v10.1** correction.
- The solver docstring still describes approval using `equiv500`.

**Concrete fix:** generate the current comparator version, test count and delta baseline from the finalization artifacts. Clearly separate historical entries from the current decision summary.

## 3. What is good and should not be changed

- **The recipe arithmetic reconciles:** the block rows sum to **379,646**, and nominal assistant-content counts sum to **146,341,757**. The three maths blocks contribute **16,023,746**, or **10.95%**, of that count.
- **Approval binding and positive selection are materially stronger:** shared manifest construction, solve/comparator hashes, approved-record revalidation and family exclusions should remain.
- **The audit now checks complete coverage and token-level labels.** Keep both the defective-path control and the clean-path negative control.
- **Keep the explicit supervision decisions:** MC demonstrations are supervised; masked lanes remain excluded for this pass. These audits do not justify restoring masked lanes automatically.
- **Keep partition-first MC splitting and source-question metadata.**
- Several Greek solutions are sound: `c2_math5_310#1` establishes both the lower bound and attainability; `c2_math5_369#1` correctly derives \(12/\sqrt{47}\) and 59; `gm_nat_634_4#1` correctly obtains median €1,090 and revised mean €1,120.
- Conversation constraints generally hold in the sample. `S1_00730` recalls the opening question verbatim; `S3_00122#1` produces one bullet; `S3c_00491` removes the requested exact word. In `S2_00809`, all six responses following the persistent limit contain **8, 20, 19, 15, 17 and 18 visible words** respectively.
- Keep the honest pilot conclusion: worked targets improved generation behaviour relative to terse targets, but did not qualify on the accuracy objective.

## 4. Answers to the specific gate issues

| Issue | Assessment |
|---|---|
| **Is V9-H1 closed?** | **No.** The cited `strip_string` route is removed, but normalized identity still bypasses structural separation. See V10-H1. |
| **Is V9-H2 closed?** | **Yes, at supplied code/log level.** Deficit mode executes first, requires positive training deficit and complete coverage, and rejects the clean run in audit (d). |
| **Does F1 now inspect the training path?** | **Yes.** The script constructs the actual trainer/data pipeline with a stand-in model and inspects every collated batch. It is no longer merely a validator printout. |
| **What do the label audits establish?** | The supplied launch-path logs show zero deficit, extra supervision or wrong labels on the 4-row test and selected 40-row cohort. The raw-path cohort loses **21/16,435 tokens = 0.128%**. Train and eval reuse those rows; they are not independent samples or a full-manifest defect estimate. |
| **Are the v9 exclusions applied?** | The supplied exclusion records and builder code implement the named GSM families, MATH rows and MC bans. Actual zero-survivor counts remain owner-reported because I could not scan the manifest. |
| **Does 11,034/12,028 agreement certify correctness?** | **No.** The **994 disagreements, 8.26%**, are disagreement counts—not established bad-label counts. Agreement does not validate Greek translation fidelity or solution reasoning. Published English MATH and native rows remain outside this check by recipe. |
| **Do the token totals indicate truncation?** | No such conclusion follows. The nominal and rendered totals differ by **4,784,618** tokens. The supplied full-render results report zero over-window rows, with maxima **4,032 train / 4,019 dev**. |
| **Is launch readiness established?** | Data-count and supplied collator checks are substantially improved, but **V10-H1 still prevents LIFT**. Real GPU execution of the changed path remains untested, as explicitly disclosed. |
| **Does the pilot justify an accuracy claim for this pass?** | No. Treat the owner-selected from-scratch pass as a new experiment under its frozen promotion criteria. Neither individual-block attribution nor an accuracy benefit is established by the pilot. |

## 5. Open questions for the owner

1. What explicit rule distinguishes **decimal commas, thousands separators and bare answer lists**? The current tests require incompatible interpretations.
2. After closing V10-H1, which actual approval IDs change relative to **v9’s 11,033** and **v10.1’s 11,034**? Supply the complete pairs, including a zero-change result if applicable.
3. Which exact package versions and tokenizer/template snapshots identify the audited environment and launch environment?
4. What recorded startup check will establish successful GPU forward/backward execution before the run proceeds unattended?

**Disposition: fix V10-H1 before lifting the hold; log V10-M1–M3 and V10-L1–L2.**