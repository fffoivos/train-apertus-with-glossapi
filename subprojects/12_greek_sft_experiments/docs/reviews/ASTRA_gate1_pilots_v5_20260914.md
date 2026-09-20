# Astra review: gate1_pilots_v5

Date 2026-09-14 20:26 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T20-23-28-01a0a0f1-fe17-7351-9918-14ed8a8e736c.jsonl) · effort xhigh · 3.1 min · prompt 76,719 chars · limit deltas {('codex', '10080'): 67.0} · brief `docs/reviews/briefs/astra_gate1_pilots_v5.md`

1. **Verdict**

**LIFT the R3e HOLD for `1-G4F6P0--00/--01/--02`.** Static inspection confirms that both previously HIGH IFEval defects are closed: an unkeyed global result cannot supply arm scores, and present item lists must match the frozen inventories exactly. The claim that *every* item is closed is too strong: escape-audit assurance remains partial, and secondary adjudication has another validation gap. These are MEDIUM/LOW findings under your disposition. This clears the review checkpoint; it does **not** establish that an actual pilot qualifies. I inspected the inlined code and rows, but did not execute the scripts or independently recompute artifact hashes.

2. **Findings, ranked by severity**

**MEDIUM — F3 remains partially open: the escape auditor suppresses events without a reviewable, narrowly defined exception.**

Evidence: the auditor ignores **every `repaired_NB` event on every `c1b_` row**, across both user and assistant fields. The supplied M0 audit reports **66 such suppressed events**, with no affected row ids or spans. That is an event count, not a count of corrupted rows. The leading-LF self-test checks `repair()` directly; it does not test whether the auditor subsequently suppresses that event. Moreover, the imported `repair_escapes.repair` implementation is not inlined.

Consequently, the reported zero residuals establish zero *unsuppressed detections under these rules*, not independently verified absence of corruption. Re-running current rules on earliest backups also does not establish what happened during every intermediate or manual repair.

**Fix:** replace the prefix-wide exception with reviewed row/field/span exceptions bound to row hashes. Include the 66-event ledger, the repair implementation, and an auditor-level test proving that legitimate terse mathematics is exempted while a corrupted command remains flagged.

**MEDIUM — Secondary adjudication can count an unvalidated, pre-existing `adjudicated` flag.**

Evidence: the final secondary accuracy counts:

```python
r['equiv500'] or r.get('adjudicated')
```

Incoming score rows are never cleared of that field.

A concrete counterexample follows from Case A: its M1 score is **84/500**, and `test/number_theory/239.json` is reported incorrect. Add `"adjudicated": true` to that score row and provide an empty adjudication file. The code would report **85/500 = 17.0%** secondary accuracy despite **`accepted_positive = 0`**. Response hashes remain valid because the response text is unchanged. This is a constructed code-path counterexample, not an observed dataset failure.

Primary accuracy and advancement remain unaffected, which limits severity to MEDIUM.

**Fix:** calculate secondary accuracy from a fresh local set of accepted adjudication ids. Ignore incoming derived adjudication fields and add this counterexample as a fixture.

**LOW — Some structurally invalid inputs crash instead of producing the promised exit-2 refusal.**

Evidence: an IFEval result containing `"prompt_strict_items": [null]` reaches `e.get(...)` on `None`, causing an uncaught exception. The supplied refusal fixtures do not cover this shape. It fails closed, so this does not demonstrate improper advancement.

**Fix:** validate container and entry types before accessing fields, then issue a specific `refuse(...)`. Add a malformed-entry fixture.

**LOW — A visible Greek name error survives in both versions of one prompt.**

Evidence: `c1b_gsm_3505` and `c2_gsm_3505` begin **“Η Μαντὠ θέλει…”**, while later text correctly uses **“Μαντώ”**. This occurs in **2/7 displayed row bodies (28.6%)**, representing **1/4 distinct problems (25%)**. These selected examples do not support a population-rate estimate.

**Fix:** correct the shared prompt to “Μαντώ” in queued exports and refresh the relevant hashes. Apply only a note to any completed artifact. NFC normalization alone would not correct the wrong diacritic.

3. **What is good and should not be changed**

- Preserve the frozen decision hierarchy: M2 cannot bypass a failed primary contrast, and a failed secondary leaves qualified M1 advancing.
- Preserve response-file and per-response hash validation, exact MATH-500 inventories, recomputed primary accuracy/truncations, and the distinction between primary scoring and secondary adjudication.
- Preserve the stated uncertainty: the guardrails are screening tolerances, not demonstrated non-inferiority. English MATH-500 and dev50 remain reported under the frozen rule.
- The displayed mathematical answers are correct: `gsm_310` → **2160**, `gsm_3230` → **8**, `gsm_3505` → **10**, and `math5_746` → **11**. I found **0 mathematical-answer failures in seven displayed bodies covering four problems**. Preserve the intended terse M0 versus explanatory M1 treatment.

4. **Answers to the specific questions**

**Q1 — Do Y, Z and Z2 close the two HIGH defects?**

**Yes, for the stated contracts.** The code prevents unkeyed-global reuse, rejects the one-item inventory, and rejects a present-but-empty list. Aggregate-only inputs remain deliberately valid: omitting the item field still bypasses item-level completeness checks. Thus this is not universal denominator verification.

F1’s finite cached-accuracy check is also closed on inspection. F5’s requested id-membership and real-boolean checks are present, and V now asserts the full coverage dictionary and advancing arm; the separate secondary-accuracy issue above remains.

I count **32/32 reported fixture passes**: **16 expected refusals, seven advancements, and nine no-advancement outcomes**. These are reported synthetic test results, not independently rerun tests or dataset quality rates. F4’s requested reason and exit-status assertions are implemented.

**Q2 — Does the escape evidence establish complete closure?**

**Partially.** The leading-LF test is correctly constructed, and the inventory lists **32 backups**. The audit reports zero residual rows across four exports totalling **24,379 row appearances**, with 66 exempted M0 events. I cannot verify those hashes, the exempted spans, or the historical “zero ambiguous repairs” claim from the supplied material. F3 therefore remains a logged MEDIUM item.

**Q3 — Are final bodies and terminal dispositions supplied?**

**Yes, with a completeness qualification.** There are **seven bodies for four distinct requested problems**. I count **42 distinct ids** in the disposition table:

- **26 exported**, represented by **31 export occurrences** because five ids appear in both M0 and M1.
- **16 excluded**: **15** for missing translation records after rejected retries, and **one**, `math5_802`, under an assembly rule.

Every listed id has a terminal disposition. Without the historical event-id inventories, I cannot verify that the table includes *every* id touched by *every* pass. The exact assembly reason for `math5_802` is also referenced rather than supplied.

5. **Open questions for the owner**

- The updated chain reportedly writes the global IFEval file, but the reader prefers an existing arm-local file. Does the chain remove stale arm-local results or reject conflicts? Please supply that integration code or receipt.
- Can you supply the repair implementation, the 66 exempted events, and historical event-id inventories reconciled against the 42-id disposition table?
- What exact assembly condition excluded `math5_802`: pairing, length, or polish?