# Astra review: gate2_full_v4

Date 2026-09-15 06:50 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T06-43-50-01a0a329-f22e-7852-ae54-48b86bb03da4.jsonl) · effort xhigh · 6.8 min · prompt 113,306 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v4.md`

## 1. Verdict

**HOLD for queued pass 1-G4F6P1, with targeted fixes.** The data-only workaround addresses the previous masking blocker, and I accept the supplied `DRY_RUN_OK` as an affirmative all-row window check under the validator described. The last-number fallback is removed, but the GSM gate still compares against a row-local label without establishing that it equals the blind-solve-approved reference. Separately, **3/15 supplied maths rows have identifiable target defects**: one unanswerable Greek question receives a numeric answer, and two published MATH solutions contain reasoning errors. This is a static review of the inlined material; sample counts are not population error estimates. Completed R3 and pilot artifacts should receive notes only.

## 2. Findings ranked by severity

### HIGH — V4-H1: GSM’s boxed-answer check is not bound to the agreed reference

**Evidence:** In §E, `keep_en(problem)` admits a problem through membership in the agreement set. Subsequently, `sol_ok()` compares:

```python
_E.equiv500(str(r['expected_answer']), str(ans).replace(',', ''))
```

There is no shown comparison between that row’s `expected_answer` and the reference accepted by the blind solve.

A concrete counterexample using the Rodney problem from `math_en_gsm:2985681`: its correct answer is **15**. Once that problem passes `keep_en`, a candidate carrying `expected_answer="150"` and `generated_solution="...\\boxed{150}"` passes the shown solution check. **This is a constructed code-path counterexample, not an observed corrupt sample row.**

**Counts:** All **5/5 shown GSM solutions are correct and boxed**. The receipt reports one rejected solution among 20,553 agreement-admitted candidates; it does not report row-label-versus-approved-reference mismatches.

**Fix:** Join each candidate to its canonical, approved reference and require both its `expected_answer` and boxed answer to match that reference. Report mismatch counts and IDs. Also replace unconditional comma deletion with validated numeric normalization: `\boxed{1,5}` must not silently become `15`.

**Previous H2 status:** The last-number vulnerability is closed; the stronger claim “boxed answer equals the agreed label” remains unproven.

### HIGH — V4-H2: A Greek target knowingly supplies a numeric answer to an underdetermined question

**Evidence:** `greek_math_v2:c2_gsm_2544#1` asks:

> «Πόσα χιλιοστόγραμμα θα περιέχει κάθε μέρος της δόσης;»

The quantities supplied determine **50 ml**, not milligrams. The assistant correctly identifies the missing information, then says:

> «Η αριθμητική τιμή που ζητείται σύμφωνα με τα δεδομένα και την απάντηση αναφοράς είναι:»

and boxes **50**.

That ending teaches deference to a reference answer after recognizing that the requested quantity cannot be determined.

**Counts:** **1/5 Greek maths samples**, or **1/3 translated Greek samples**, has this defect. The assembler’s ×2 replication implies two effective training rows for this source row. The supplied English source is insufficient to determine whether the unit error originated in translation.

**Fix:** Exclude this family from the queued manifest pending correction. Either repair the question to ask for millilitres and revalidate the exact text, or retain the milligram question with an explicitly indeterminate answer. Locate and inspect its English twins. Inspect the claimed high-effort validity record for this exact Greek target, and screen for the same unit mismatch and reference-answer language elsewhere.

### HIGH — V4-H3: Published MATH targets contain demonstrably false reasoning

**Evidence:**

- **`math_en_math:math_train_4407#1`:** After correctly obtaining  
  \(2(x+2)^2+(y-5)^2=33-c\), the explanation says **“both \(x+2\) and \(y+5\) must be zero.”** It also says the **right-hand side** is always nonnegative; that property belongs to the left-hand side.
- **`math_en_math:math_train_2954#1`:** It states  
  **“\(\angle BOD'=2\angle BAD=60\)”**, although it previously establishes \(\angle BAD=90^\circ\). The relevant inscribed angle needs the primed point. The solution also introduces \(E,F\) without defining their positions and does not explain why the assumed configuration achieves the maximum.

**Counts:** **2/5 published MATH samples have reasoning defects.** Their final answers, **33 and 554**, are correct. Together with V4-H2, this makes **3/15 maths samples with defective targets**, representing six effective rows under ×2 replication.

**Fix:** Repair or exclude these two source rows and their copies from the queued arm. For `4407`, a complete replacement is the completed-square equation, nonnegativity, and the unique point \((-2,5)\) when \(c=33\). For `2954`, supply a self-contained construction and maximum argument, and correct the angle notation. Apply derivation QA to published solutions; their exemption from blind label solving does not validate their explanations.

### MEDIUM — V4-M1: The R3 supervised-token total is arithmetically wrong

**Evidence:** The R3 block values in §A sum to **151,912,798**, not the stated **140,424,598**: a discrepancy of **11,488,200** tokens.

Using the displayed block values, R4’s **146,411,633** is **3.62% lower** than R3, rather than approximately **4.26% higher** under the stated headline total.

The R4 block sums do reconcile to its receipt.

**Fix:** Reconcile the R3 recount and regenerate the comparison from one authoritative total. Label these as the stated counting-function estimates. Because R3’s training ignored its masks, mask-aware counts alone cannot establish R3’s actual supervised exposure.

### MEDIUM — V4-M2: Coverage and identity records do not establish every claimed binding

**Evidence:**

- The finalizer verifies **12,028 IDs**, including duplicate/missing/extra checks, but its manifest hash covers IDs rather than problem/reference contents. Cached solve records are reused by ID and compared against their stored `ref`. A changed problem under the same translated-source ID can therefore retain an old agreement.
- §F demonstrates remote train/dev SHA-256 comparisons. The excerpt does **not demonstrate** comparison of the executed trainer and remote config against their recorded hashes. No actual mismatch is shown.

**Fix:** Bind solve results to problem/reference fingerprints, and compare those against current inputs. Record or demonstrate the runtime code/config hash checks alongside the manifest checks. These are evidence and reproducibility gaps; I have not counted any actual stale record or runtime mismatch.

### MEDIUM — V4-M3: Conversation-suite dev coverage disappears after overlap filtering

**Evidence:** The block receipt records **18** `convskills_v2` dev rows; the final dev breakdown contains **zero**. Thus **18/18 selected suite dev rows were removed**.

The sample also contains an exact shared user question about the colleague with multiple sclerosis in both `S1_00754` and `S2_00860`, demonstrating reuse across conversation rows. This is train–train reuse, not evidence of surviving train–dev leakage.

**Fix:** Report pre/post-filter dev counts per block. Document that final dev loss provides no conversation-suite coverage. For future suite generation, partition shared prompt families before constructing conversations if suite-specific dev loss is required.

## 3. What is good and should not be changed

- **Keep the data-only masking workaround:** dropping correcting v2 and masked suite rows avoids training their unwanted assistant turns. Declaring format demonstrations supervised makes the receipt consistent with the intended training behavior.
- **Keep the final no-`train=false` assertion.** The old flags in §D are upstream data; §E explicitly removes them before assembly.
- **Keep the fatal all-row rendered-length check.** The supplied dry-run checks 379,740 train rows; its exact **220,148,591** tokens can legitimately differ from the assembler’s approximate **224,971,349**.
- **Keep positive agreement filtering, explicit exemptions, partition-first format construction, and all-user-turn overlap filtering.**
- The five GSM examples have correct calculations. The other four Greek maths examples are sound, including **108 m** in `gm_nat_183_1` and **14,400 litres** in `gm_nat_749_0`.
- The two recall/count targets (`S1_00088`, `S1_00754`) and two reformatting targets (`S3_00297`, `S3_00103#1`) satisfy their checkable requests.
- Preserve the disclosed IFEval waiver, negative pilot results, and R3 masking-defect ledger entry.

## 4. Answers to the gate questions

| Question | Assessment |
|---|---|
| **Is previous H1 closed?** | **For this data-only manifest, yes**, supported by the shown filtering and final assertion. The trainer defect remains. §I still inspects validator labels, not a training batch. |
| **Is previous H2 closed?** | **Partially.** A box is now required; comparison to the approved canonical reference still needs V4-H1. |
| **Does the dry-run establish window compliance?** | **Yes, on the supplied account of the fatal validator.** No further HOLD is justified merely because there was no truncation/drop message. |
| **Do the assembly counts reconcile?** | R4 does: **379,740 train**, **2,342 dev**, and **146,411,633 estimated supervised tokens**. GSM’s `20,553 − 1 − 12 = 20,540`, then ×2, also reconciles. R3’s supervised total does not. |
| **Are the previous dev-check and split fixes present?** | Yes in the code: explicit dev rows receive `check_row`; English maths has no random dev split; declared dev problems are excluded; all dev user turns are checked against train. Completeness of the underlying family maps is not independently demonstrated here. |
| **Does the pilot establish a maths accuracy benefit?** | **No.** It failed its frozen primary criterion. The from-scratch pass is a new experiment; record how the owner’s re-plan supersedes §G’s stop-Phase-C conclusion. |
| **Are promotion rules usable?** | Their HOLD/equal logic is clear. They assess the complete mixture. Preserve the operational-tolerance wording and descriptive treatment of format effects. |
| **What clears this HOLD?** | Close V4-H1, correct/exclude the three cited defective maths source rows and their copies, then regenerate the manifest, receipt, expected row count, and bound dry-run. A trainer rewrite is not required for this pass. |

Current-facing documentation also needs cleanup: §A still says **“correcting v1 → v2”**, and retained F1 language describes masked demonstrations. Preserve historical receipts, but clearly distinguish them from the final launch recipe.

## 5. Open questions for the owner

1. What canonical reference is attached to each admitted English GSM solution, and what is the **row-label mismatch count**?
2. What did the exact-text validity review record for `c2_gsm_2544` conclude, and why did this target remain eligible?
3. Was a diagram or construction text omitted from `math_train_2954`, and how are other diagram-dependent published solutions handled?
4. Is zero conversation-suite dev coverage intentional?
5. Where are the eight native-macro components and the explicit post-pilot re-plan recorded?