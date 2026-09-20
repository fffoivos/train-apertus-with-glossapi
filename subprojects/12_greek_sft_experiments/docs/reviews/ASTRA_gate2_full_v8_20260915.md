# Astra review: gate2_full_v8

Date 2026-09-15 14:16 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T14-09-29-01a0a4c1-f4c9-74f2-bf92-3964a6bd0e65.jsonl) · effort xhigh · 7.2 min · prompt 237,130 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v8.md`

## 1. Verdict

**HOLD on V8-H1 and V8-H2.** The revision substantially improves approval binding and label auditing, but the comparator still admits false numerical agreements, and the audit silently reduces a requested 40-row cohort to 39 rows before declaring complete coverage. These need correction before launch. The supplied logs do support zero label differences on the **39 rows actually audited**, and the corrected raw-path deficit is **20/14,062 = 0.142%**, not 34%. Several sample defects remain, listed below as MEDIUM/LOW. **Verification boundary:** I reviewed the supplied code, rows and logs, recalculated totals, and reproduced normalization behavior in an independent JavaScript transliteration. Tool restrictions prevented reopening local artifacts, running the Python/TRL implementations, checking file hashes, or verifying external citations. I therefore do not certify those executions or identities independently.

## 2. Findings ranked by severity

### V8-H1 — HIGH: numerical approval still has false-positive routes

The exact `Fraction` arithmetic fixes the Decimal-context problem. **The remaining problem is deciding what the strings mean before comparison.**

#### A. Unsupported numerical wrappers still reach float tolerance

These two negative cases follow directly from the supplied functions:

| Reference | Candidate | Why the code accepts |
|---|---|---|
| `0\text{ cm}^2` | `0.0000000005\text{ cm}^2` | Neither parses in `numeric_value`; `equiv500` strips the squared-unit wrapper and accepts the difference under its tolerance. |
| `12345678901234567890\text{ cm}^2` | `12345678901234567891\text{ cm}^2` | Same fallback; conversion to floats loses the one-unit difference. |

`_strip_wrappers` does not handle the trailing `^2`, whereas `E.strip_string` explicitly does. The “either side is number-like” guard therefore never activates.

#### B. Normalization destroys lists and meaningful text

| Reference | Candidate | Incorrect interpretation |
|---|---|---|
| `-1, 1` | `-1.1` | Two listed answers become one decimal. |
| `17, 44` | `17.44` | Same problem. |
| `45, 135, 225, 315` | `45135225315` | Four listed answers become one thousands-grouped integer. |
| `5\text{ or 6}` | `5` | The wrapper remover deletes an alternative answer as though it were a unit. |

The self-tests themselves identify comma-separated forms as lists. Nevertheless, whitespace disappears before numeric classification. The wrapper regex also accepts **arbitrary text**, not an explicit set of units.

**Observed dataset evidence:** `math_2341` already demonstrates the list/integer misclassification, although that particular pair is rejected conservatively. It does not establish that the parser can only err conservatively.

**Count boundary:** these are **six constructed counterexamples derived from the code**, not six observed erroneous approvals. I cannot report their prevalence among the 12,028 solve records.

**Concrete fix:**

- Recognize lists before removing whitespace; do not equate list separators with decimal/thousands separators.
- Restrict removable suffixes to explicitly supported units and formatting.
- Remove numerical float tolerance from the **label-approval fallback**, including numbers exposed by later normalization.
- Add these negative cases, re-decide all records, inspect the decision delta, and rebuild the approval artifact and receipt.

### V8-H2 — HIGH: the audit can pass with requested rows missing

Both §I2(b) and §I2(c) say:

> `IDS MODE: 39 rows found of 40`

They subsequently report `39/39` coverage and success. The code constructs `rows` from whatever it finds, then measures coverage against that reduced list.

**Evidence and counts:**

- **1/40 requested rows missing: 2.5% incomplete selection**, in both runs.
- The missing ID is not printed.
- The supplied logs genuinely account for the 39 selected rows; this finding does **not** invalidate their token comparisons.
- `--expect-deficit` also permits exit 0 for complete coverage with extra supervision or wrong label values, because its success branch checks coverage alone.

The missing row may have been intentionally excluded during rebuilding. That is a plausible explanation, not evidence supplied by the audit.

**Concrete fix:**

1. Fail before trainer construction unless every requested ID exists.
2. Print missing IDs and bind the requested cohort and audited train file by hash.
3. If a row was intentionally removed, document it and explicitly revise the cohort or choose a replacement from the same exposure category.
4. Make `--expect-deficit` require a positive deficit **and zero extra supervision/wrong label values**.
5. Rerun both paths and retain actual process exit statuses.

Also label the exposure artifact as historical: its **379,698 rows** differ from the launch manifest’s **379,716**.

### V8-M1 — MEDIUM: the MC sample still contains defective supervised questions

In §H’s five MC conversations, I count **15 supervised answer turns**.

- **`format_mc:mc_openbookqa_5561`**, demonstration about full moons: “How many full moons are there each month” → **D, “less than two.”** Calendar months can contain two full moons. The universal question has no consistently correct offered answer.
- **`format_mc:mc_openbookqa_6242`**, demonstration about magnets: “a door handle” → **A**. The material is unspecified; a door handle is not necessarily magnetically attracted.

That is **one false universal and one under-specified question: 2/15 answer turns, affecting 2/5 sampled conversations**. This selected sample does not estimate the block-wide defect rate.

Additional builder evidence in §D:

- **`mc_openbookqa_5487`**, demonstration SID **`openbookqa:9a33d472688a`**: every animal “intakes air.” Aquatic respiration makes that universal formulation false.
- The same row’s SID **`openbookqa:ebad3b1a88d8`** assumes a larger lake necessarily means more catfish; lake size alone does not establish that.

**Fix:** ban or repair these stems throughout the pool, covering targets and demonstrations. Screen universal claims and questions whose answer requires an unstated material, population or environmental assumption.

### V8-M2 — MEDIUM: two English GSM rows have prompt/reasoning defects

- **`math_en_gsm:219895#1`**: the solution adds the five small apples and ten unripe apples without establishing that the groups are disjoint. If their overlap is \(k\), the number of perfect apples is \(15+k\), giving **15–20**, not uniquely 15.
- **`math_en_gsm:1660951#1`**: the solution says **“0.4 bags of pitch”**, although pitch is measured in barrels. The final answer, **6 barrels**, is correct; the intermediate unit is wrong.

**Count:** **2/5 sampled English GSM rows** have an issue: one under-specified prompt and one unit error. This is not a 40% wrong-final-answer rate.

**Fix:** exclude the apple problem family or explicitly supply the disjointness assumption in a revised problem. Change “bags of pitch” to “barrels of pitch” in the second solution and inspect sibling solutions.

### V8-M3 — MEDIUM: conversation targets contain a unit-convention error and unsupported certainty

- **`convskills_v2:S2_00313#1`** states:

  > «Με τη δυαδική μετατροπή, 10.000 KB αντιστοιχούν περίπου σε 9,77 MiB.»

  The units need qualification:

  - 10,000 decimal KB = 10,000,000 bytes = **9.536743 MiB**.
  - 10,000 **KiB** = **9.765625 MiB**.

  The latter is applicable only if the platform uses “KB” to mean KiB.

- **`convskills_v2:S1_00739`** asserts database refresh intervals from weekly to quarterly without supporting evidence, then uses:

  > «Πραγματική συνδεσιμότητα αποδεικνύεται…»

  for an accepted installation order. An accepted order is evidence of availability, not proof that installation will succeed. I classify the refresh interval as **unsupported here**, not independently disproved.

**Count:** one unit-convention defect and one unsupported-certainty response, affecting **2/5 sampled conversations**.

**Fix:** distinguish KB from KiB explicitly. For FTTH, cite the particular database’s update policy, describe an accepted order as a stronger indication, and reserve confirmation for successful installation/service testing.

### V8-M4 — MEDIUM: stable question IDs do not survive assembly

The builder adds `meta.target_sid` and `meta.demo_sids`. However, `add_block` constructs each manifest row using only:

```python
dict(config=name, id=..., messages=m)
```

It discards `meta`. Thus stable identities are available in the bound builder artifact but absent from the assembled format rows; launch IDs still contain rebuild-dependent counters.

**Scope:** the **8,189 train and 71 dev format rows**, according to the supplied assembly path.

**Fix:** preserve the source metadata in the manifest and use stable SIDs in exclusion/audit reports. The pool-level stem bans should remain.

### V8-L1 — LOW: residual terminology and documentation defects

- **`math_en_math:math_train_6975#1`** calls the step to \(\sin 5x=\cos 5x\) “sum-to-product”; it uses **angle-addition identities**. The answer \(9^\circ\) is correct.
- **`greek_math_v2:c2_math5_1493#1`** retains `50^{\mathrm{th}}` and `40^{\mathrm{th}}` in Greek prose. Use **«50ός όρος»** and **«40ός όρος»**.
- “Changes, all data” and several comments saying the training path cannot honor masks are stale beside the new pretokenized implementation.

**Fix:** correct terminology and distinguish historical raw-path behavior from the current implementation and the deliberate decision to keep masked rows excluded.

## 3. What is good and should not be changed

- **Receipt arithmetic reconciles.** The block sums give **379,716 rows** and **146,365,719 nominal supervised tokens**. Dev accounting gives \(2667+146+18+71-560=2342\).
- **Exact rational arithmetic is the right improvement.** Preserve it while fixing parsing and fallback behavior. The **24 displayed additions** to the v7 approval set are exact numerical equivalences.
- **Approval binding is substantially stronger.** The composite comparator hash covers both files, and approved records are revalidated before selection.
- **The rewritten audit materially improves evidence.** It iterates all selected batches and compares labels token by token. Preserve this structure.
- **The 34% correction is explicit and necessary.** Keep both the historical entry and its clearly linked correction.
- **All five sampled Greek math final answers and all five sampled published-MATH final answers check out.** Examples include inverse **91**, sequence term **318**, minimum **−1**, and sum **1/1624**.
- **Conversation skill behavior is visible.** Both sampled recall conversations answer the recall task correctly; the three constraint conversations preserve their requested no-question/bullet behavior, including the explicit release in `S2_00457`.
- Keep partition-first MC splitting, all-user-turn overlap checks, family-level exclusions, and the distinction between nominal and rendered tokens.
- Keep completed pilots and earlier rounds unchanged; attach correction notes rather than retrospectively altering their artifacts.

## 4. Answers to the specific issues in the brief

| Issue | Assessment |
|---|---|
| **Is V7-H1 closed?** | **Partly.** Exact arithmetic and the original formatting examples are addressed. V8-H1 identifies remaining false-positive routes. |
| **Is V7-H2 closed?** | **Partly.** The one-batch denominator error is corrected. Requested-cohort coverage still fails open under V8-H2. |
| **Is the 34% deficit supported?** | **No; it is correctly retracted.** The supplied complete-cohort logs support **20/14,062 = 0.142% on the 39 selected rows**. |
| **Does F1 now distinguish validator and training labels?** | **Yes.** The pretokenized route hands validator masks to TRL. Supplied audits show equality on the four-row test and 39-row exposure test, for train and evaluation. This remains a sampled collator result, not production-attention validation. |
| **Were the problematic cost paragraphs handled?** | The reasons enumerate **19 relevant conversation IDs**. Sixteen appear among active reviewer exclusions; the three S4 IDs are consistent with earlier masked-lane removal. The code includes survivor assertions. I did not independently scan the underlying files. |
| **Was `math_train_4864` handled?** | It is explicitly excluded. The retained twin `c2_math_3417` is not reproduced in full here, so its claimed repair remains owner-reported. |
| **Were the two OpenBookQA stems and stable IDs addressed?** | Pool-level bans cover targets and demonstrations. Stable IDs were added to builder rows but are discarded during assembly. Further sampled stems remain defective. |
| **Is comparator identity now sufficient to close V7-M5?** | The stated two-file omission is fixed in code. I did not recompute the composite hash. Dependency/environment identity is not established by that hash alone. |
| **Did only the data change?** | **No.** Data and supervision behavior changed. Attribution to the whole pass is appropriate; attribution to a particular block is unsupported without an ablation. |
| **Does the pilot justify an accuracy-improvement claim?** | **No.** The primary comparison was **−1.4 pp**, and no arm qualified. The from-scratch pass is a separate owner-directed experiment, not a pilot-qualified advance. |
| **Are lengths and launch bindings adequate?** | The supplied length report covers **379,716 train + 2,342 dev rows**, with zero over-window rows. The shown three-way hash checks are useful. Neither establishes successful GPU training; that remains explicitly untested. |
| **Can Gate 2 be lifted now?** | **No.** Close V8-H1 and V8-H2, regenerate affected approvals/bindings, and produce the corrected audit evidence. MEDIUM/LOW findings remain logged under the stated disposition. |

The current raw-path reconstruction also does **not** measure the exact historical token loss of rounds 1–3. Their environment and full training populations would need separate evidence. Keep that limitation in completed-run notes.

## 5. Open questions for the owner

1. Which requested audit ID was missing, and was it removed by the latest assembly?
2. What were the actual loader batch sizes and visible device counts? Six prepared train examples produced two batches despite the printed per-device batch size of one.
3. What persisted runtime checks and stop conditions implement “watched from step 0”? `TRAIN_OK` and plausible loss alone do not prove attention-boundary correctness.
4. Where is the explicit experimental override recorded for including the Greek math block after the pilot’s frozen stop rule?
5. After the comparator repair, how many actual approvals change because of list parsing, meaningful suffixes, and numerical fallback? That delta is needed to measure the dataset impact of V8-H1.