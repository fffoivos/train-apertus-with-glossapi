# Astra review: gate1_pilots_v4

Date 2026-09-14 20:17 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T20-11-33-01a0a0e7-12b7-7363-9e34-3a2f3c938385.jsonl) · effort xhigh · 6.5 min · prompt 70,093 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate1_pilots_v4.md`

**(1) Verdict**

**HOLD remains for 1-G4F6P0--00/--01/--02, because F2 still has two HIGH input-validation defects in IFEval.** An unkeyed global result can silently supply all three arms, and an incomplete item set can pass by declaring its own denominator. Both can affect advancement. The MATH response binding, recomputed metrics, hierarchy, and boundary handling are substantially improved. F3’s zero-residual export audit is reported evidence, with verification limits described below. I reviewed the inlined code and checked internal arithmetic; I did not execute the Python or independently recompute hashes. The report contains **25/25 passing fixtures**, but Case A is fabricated and establishes no actual pilot improvement. These findings require readout fixes; they do not establish a need to regenerate datasets. Completed datasets receive notes only.

**(2) Findings ranked by severity**

**HIGH — F2: The global IFEval fallback can assign one unlabelled result to every arm.**

In `ifeval(label)`, both the arm-specific path and the global fallback use:

```python
d = x if 'prompt_strict' in x else x.get(label)
```

Consequently, if all arm-specific files are absent, this single global file is sufficient:

```json
{"prompt_strict": 0.60}
```

It supplies 60% to **all three arm slots**, produces no missing-IFEval entry, and makes every IFEval difference zero. With otherwise qualifying inputs, an arm can advance without its own IFEval measurement. This contradicts the documented fallback contract: a global file keyed by label.

This is a **static counterexample**, not an observed production-file failure. None of the supplied fixtures tests it.

**Fix:** Accept a direct result only from the arm-specific path. Require the global file to contain the requested label explicitly. Add a fixture with no arm-specific IFEval files and one unkeyed global result; it must refuse or remain incomplete, with no advancement.

**HIGH — F2: IFEval completeness trusts the submitted denominator and skips empty item lists.**

Two distinct invalid payloads pass the displayed validation:

```json
{
  "n": 1,
  "prompt_strict": 1.0,
  "prompt_strict_items": [{"key": 0, "prompt_strict": true}]
}
```

This passes because `check_items` receives `int(d.get('n') or N_IFEVAL)`, namely **1 rather than 541**. It can supply a passing 100% guardrail while **540/541 required items are absent**.

Separately:

```json
{"n": 541, "prompt_strict": 1.0, "prompt_strict_items": []}
```

passes because `if it:` skips validation entirely. An explicitly empty item list becomes an unpaired aggregate.

These are two constructed acceptance paths, not measured dataset failures. Fixture R tests disagreement with a populated item list; it covers neither path.

**Fix:** Enforce the frozen 541-item denominator independently of file metadata. Distinguish an **absent optional item field** from a **present invalid or empty field**. Validate keys against the frozen benchmark inventory where available; cardinality alone does not establish item identity. Preserve explicitly permitted aggregate-only reporting. Add refusal fixtures for the two payloads above.

**MEDIUM — F3: Export closure is reported, but the pack does not independently establish the detector’s coverage or final row contents.**

The supplied audit reports **0 residual rows across 24,379 exported row occurrences**: 8,934 + 8,934 + 1,403 + 5,108. That is an owner-reported rate, not an independently verified failure rate. The 66 M0 detections are **events**, so they cannot be converted into an affected-row percentage.

There is also a concrete limitation in the supplied repair function: a text beginning with `[LF]abla f`, with source `\nabla f`, remains unchanged with no event because newline handling requires `i > 0`. The export auditor might catch this separately, but its implementation is not inlined.

The intermediate report still lists unresolved `math_3175`/`gm_math_3175` and forced regeneration of `gsm_310`, `gsm_3230`, `gsm_3505`. Its Level-5 unresolved list contains **27 entries representing 26 unique IDs**, with `math5_661` repeated. These entries do **not** prove current exported corruption: later repairs, replacements, or exclusions can explain them. They do require a terminal disposition to make the closure traceable.

Only `math_3175` has a complete repaired field shown:

> `Να υπολογίσεις το $\cos 72^\circ$.`

For `c2_math5_746` and the three GSM rows, the pack supplies status assertions rather than the final exported row bodies.

**Fix:** Supply the export-auditor implementation, a leading-LF fixture, and a final disposition table linking the named unresolved IDs to repaired/replaced/excluded outputs and their hashes. Include the four requested final row bodies. Log this as a verification limitation; do not infer a measured corruption rate from it.

**MEDIUM — F5: “Valid negative” does not require a valid adjudication boolean.**

After checking response hash and reference, the code treats everything except literal `True` as `valid_negative`:

```python
if u.get('equivalent') is True:
    ...
else:
    cov['valid_negative'] += 1
```

Thus a missing value, `null`, or `"false"` becomes a supposedly valid negative. An unknown ID is also counted under `attempts_on_resolved_rows`, although it may identify no benchmark row.

Fixture V’s four supplied attempts correctly produce one positive, one negative, one stale attempt, and one resolved-row attempt. It contains **zero malformed-value or unknown-ID cases**, so it does not establish the broader “validated categories” claim. This affects secondary reporting, not primary advancement.

**Fix:** Validate benchmark membership and `type(equivalent) is bool`. Refuse malformed entries or report them in explicit invalid categories.

**MEDIUM — F1: Cached NaN accuracy is accepted despite the refusal contract.**

For a cached `equiv500_acc` of NaN:

```python
abs(float(sc['equiv500_acc']) - acc) > 1e-4 + EPS
```

evaluates false. The file is accepted.

The subsequent overwrite with the recomputed accuracy protects the decision, which is why this is not HIGH. Nevertheless, the claim that invalid or contradictory cached accuracy is refused is incomplete.

**Fix:** Validate cached accuracy as a finite fraction before comparison. Add NaN and finite-disagreement fixtures. Existing fixture F tests IFEval NaN, not MATH cached accuracy.

**LOW — F4: Fixture assertions are narrower than some fixture descriptions.**

The report shows **25/25 PASS, zero reported failures**. However, fixture V asserts only that the output contains `'accepted_positive': 1`; it does not assert the remaining coverage categories or the claimed unchanged decision. Refusal cases generally assert only `REFUSED`, not the intended reason.

Also, the fixtures deliberately flip `equiv500` labels without rescoring response semantics. They exercise readout decisions and hash plumbing, not mathematical grading correctness.

**Fix:** Assert V’s complete coverage dictionary and advancing arm, and assert the intended refusal category in negative fixtures. Describe these as synthetic readout fixtures.

**(3) What is good and should remain**

- **MATH response binding:** Exact frozen-ID coverage, boolean score checks, file hashes, and per-response hashes meaningfully address stale score/response pairings.
- **Decision hierarchy:** M2 cannot advance through a failed primary contrast; a failed secondary preserves qualifying M1.
- **Boundary handling:** The displayed implementation includes the exact +5 truncation/loop boundaries, −2 pp guardrail boundary, gain floor, and positive-bootstrap-LB requirement.
- **Scientific interpretation:** Keep English MATH and dev50 reported according to the frozen rule. Keep the explicit statement that screening tolerances do not demonstrate non-inferiority.
- **Exposure accounting:** Retain the annotation and exclusion sensitivity analysis for `test/number_theory/239.json`.
- **Dose accounting:** The trainer figures are internally consistent: `ceil(7331/16)=459`, `ceil(7653/16)=479`, and `ceil(7878/16)=493`. Retain the dose/recipe check before Phase C.

**(4) Answers to the five questions in the brief**

1. **Final texts and cut-1 unresolved events:** Partially answered. The inlined `math_3175` repair removes the displayed ANSI corruption and preserves the source instruction. The final bodies of `c2_math5_746`, `gsm_310`, `gsm_3230`, and `gsm_3505` remain unavailable for row-level review. Their successful repair/export is reported, not independently verified.

2. **Corrected fixtures and versions:** The pack supplies readout v3, scorer v2, fixture code, and a 25/25 passing report. Fixture D now explicitly asserts 499 response rows. This closes the previously identified test-construction issue, but does not cover the acceptance paths above.

3. **Token differences and trainer-side identity:** **All three supplied receipt/cluster SHA-256 pairs match textually.** That supports the asserted file identity; I did not recompute them. The 3–5% counting-convention explanation is plausible but remains undecomposed. Separately, trainer totals show M1 has approximately **4.40% more tokens than M0**, and M2 **2.94% more than M1**. Those are real dose differences in the supplied figures, not receipt-counting discrepancies.

4. **English MATH and dev50 safeguards:** Answered. They are reported, not decision gates, under the supplied frozen rule. I would not change that rule during this re-review.

5. **Historical loop IDs, contamination IDs, and snapshots:** The four historical loop IDs remain unrecoverable; retiring the irreproducible 23 and recomputing consistently is an acceptable accounting correction. The contamination IDs are now explicit: `c2_math5_530`, `c2_math5_664`, `c2_math5_1156`, `c2_math5_1139`. Their removal is reported, while the counts independently reconcile:

   **1,403 − 4 = 1,399 = 1,385 added train rows + 14 added dev rows.**

   Likewise, **10,337 = 8,934 + 1,403**. This verifies internal consistency, not the underlying 13-gram matches.

**(5) Open questions for the owner**

- Can the next pack demonstrate refusal/non-advancement for the unkeyed global fallback, self-declared one-item denominator, and explicitly empty item list, while preserving valid aggregate-only inputs?
- What does the export auditor do with source-supported corrupted commands at the beginning of a field? Please include its implementation and the backup inventory underlying the reported zero ambiguous repairs.
- Can you provide the four missing final row bodies and a terminal disposition table reconciling the intermediate unresolved lists with the hash-labelled exports?

**The two HIGH IFEval fixes are the remaining actionable reasons to retain the HOLD.**