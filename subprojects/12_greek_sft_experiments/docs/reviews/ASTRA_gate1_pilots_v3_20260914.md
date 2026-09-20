# Astra review: gate1_pilots_v3

Date 2026-09-14 20:01 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T19-54-52-01a0a0d7-cd0e-7583-94f4-9e6d12605735.jsonl) · effort xhigh · 6.7 min · prompt 64,213 chars · limit deltas {('codex', '10080'): 1.0} · brief `docs/reviews/briefs/astra_gate1_pilots_v3.md`

(1) **Verdict.** **Keep HOLD at R3c, with targeted fixes; the recipe need not change.** The missing-file handling and primary-before-secondary hierarchy are substantially improved, and the supplied assembly counts reconcile. However, the readout still accepts evidence that can produce an incorrect advancement decision, while the escape audit excludes the characters responsible for the original defect. I verified these issues by inspecting the inlined code and reconciling counts; I did not execute the scripts, inspect exports, or verify artifact hashes. The 11 passing outcomes are owner-reported fixtures, not pilot results. No repaired Greek row text is supplied, so I cannot independently measure the remaining dataset defect rate. Completed datasets should receive notes only.

(2) **Findings, ranked by severity.**

**F1 — BLOCKER: The truncation guardrail trusts a cached integer instead of the responses.**

Evidence: §A `load_scores()` recomputes truncations only when `sc['truncated']` is not an integer. It accepts negative integers, values above 500, and stale counts. Python also treats booleans as integers here.

A concrete counterexample, derived from the code: retain Case A’s qualifying scores, mark all **500 M1 responses** as `finish_reason='length'`, and set its score-file `truncated` to `0`. Against Case A’s M0 count of 60, M1 passes the truncation guardrail despite **500/500** length-finished responses. This is a constructed counterexample, not an observed dataset rate. None of the **11 fixtures** exercises a truncation breach.

The advertised structural validation is also incomplete: `equiv500_acc` is neither range-checked nor checked against the rows, and the boolean membership check accepts numeric `0` and `1`.

**Fix:** Derive truncation counts from validated response metadata every time; refuse disagreement with cached counts. Recompute accuracy from strictly validated score rows. Add fixtures for inconsistent counts, invalid ranges, and the exact `M0 + 5` boundary.

**F2 — HIGH: Matching filenames and IDs do not bind scores to the responses that produced them; guardrail evidence can also contradict itself.**

Evidence:

- §A checks MATH response IDs and string types, but no response hash binds each deterministic score to its response. Replacing response contents while preserving IDs leaves the primary score unchanged.
- IFEval/MGSM decisions use aggregate values, while paired intervals use separately loaded items. There is no agreement check.
- Guardrail item dictionaries silently overwrite duplicate IDs and use unrestricted `bool(...)` conversion. Two equally incomplete item sets can receive a “paired” interval.
- MGSM result and sample files are selected independently by lexicographic order, without checking that they belong to the same evaluation.

A second constructed counterexample: M1 can report IFEval aggregate `0.61` against M0’s `0.60`, while its supplied items contain **0/541 successes** against M0’s **541/541**. The code will print a paired decline of 100 pp but still pass the IFEval guardrail.

Case A already illustrates the separation at a smaller scale: MGSM displays **49.0 versus 48.0**, while its item-derived difference is **+0.8 pp**.

**Fix:** Bind scores to response hashes and an evaluation manifest. When guardrail items exist, validate their expected IDs, uniqueness, binary values, run identity, and agreement with the aggregate within an explicit rounding tolerance. Entirely absent item files may retain the documented unpaired fallback. Inconsistent evidence should refuse the readout.

I found an acceptance vulnerability; I have not established that any actual pilot artifacts are stale.

**F3 — HIGH: Escape-repair closure is unsupported, and the supplied repair function has identifiable gaps.**

Evidence:

- The final audit excludes **TAB and LF**. Those exemptions include the original `c2_math5_746` pattern, TAB + `riangle`, and LF + `eq` from `\neq`.
- For Greek text represented diagnostically as `$x [LF]eq 0$`, with source `$x \neq 0$`, the repair function leaves LF unchanged because its preceding character is a space. It records no unresolved event. The reported export audit also permits that LF.
- Ambiguity is not always source-resolved. **BS + `eta`** can represent `\beta` under pattern A or `\eta` under pattern B. With neither command in the source, the implementation defaults to `\beta`; it does not mark the ambiguity unresolved.
- For `cut1/edited/rows_edited.jsonl`, `process()` returns unresolved IDs in `un`, but the caller discards them. The supplied census reports **two unresolved events** there; their export disposition is absent.

The census contains **128 unresolved events**, not necessarily 128 distinct affected rows. All seven entries report `changed: 0`. The later `repaired_rows: 69` does not identify escape-specific repairs or connect them to before/after text. Neither figure establishes an escape failure or repair rate.

**Fix:** Detect suspicious TAB/LF patterns in mathematical contexts, including commands preceded by spaces. Send ambiguous repairs to regeneration unless source context resolves them uniquely. Track unresolved Cut-1 IDs through to regeneration or exclusion. Supply a final audit bound to export hashes, with before/after examples for `c2_math5_746` and representative LF/ambiguous-command cases. Preserve legitimate formatting through contextual checks.

**F4 — MEDIUM: One fixture is misconstructed, and important boundary behavior remains untested.**

Evidence: §B defines:

```python
def truncate_lines(p, n):
    open(p, 'w').write(''.join(open(p).readlines()[:n]))
```

The first `open(p, 'w')` truncates the file before the argument reads it. **Case D creates an empty file, not 499 rows**, duplicating Case C’s condition. Thus **1/11 advertised fixtures (9.1%)** does not test what its label claims. This is a fixture defect rate, not a dataset defect rate.

There is also a boundary error in §A: multiplying fractions by 100 before comparing can make `0.58` versus `0.60` evaluate slightly below −2 pp in binary floating-point arithmetic, incorrectly breaching the frozen tolerance.

**Fix:** Read the response lines first, assert the original count, write 499, and assert the resulting count before invoking the readout. Add isolated loop/truncation breaches, exact tolerance boundaries, and a primary gain meeting the floor but failing the bootstrap bound. Use numerically stable threshold comparisons with a narrowly defined numerical tolerance.

**F5 — MEDIUM: Adjudication coverage does not measure validated adjudication coverage.**

Evidence: §A counts `adjudicated` whenever a scored ID appears in the adjudication file, including already-resolved rows and entries whose response hash or reference fails validation. Duplicate adjudication IDs are silently overwritten.

The acceptance check does validate hashes for newly accepted positive adjudications, which is useful. But the coverage count can overstate valid unresolved-row adjudication. None of the **11 fixtures** specifically exercises this path; Case A shows zero unresolved rows and no adjudication output.

**Fix:** Report separate counts for unresolved rows, unique attempts on unresolved rows, valid response/reference-bound adjudications, rejected or stale entries, and accepted positives. Add fixtures covering negative adjudications, hash mismatches, reference mismatches, and duplicate IDs.

**F6 — MEDIUM: The dry-runs do not demonstrate that the repaired manifests were the exact trainer inputs.**

All three dry-run row counts match their receipts, but token totals differ:

| Arm | Receipt tokens | Dry-run tokens | Difference |
|---|---:|---:|---:|
| M0 | 28,546,834 | 29,960,812 | +1,413,978 |
| M1 | 30,320,475 | 31,278,117 | +957,642 |
| M2 | 31,340,918 | 32,199,143 | +858,225 |

The dry-runs contain no input SHA and set `expected_full_train_tokens` to `null`. Different token-counting or rendering conventions could explain this; the differences do **not** establish stale inputs. However, row-count agreement and “Preflight: OK” cannot establish byte identity.

**Fix:** Include trainer-side input hashes matching the attestation, document the token-counting differences, and identify the operative dose figures. The reported packed-sequence counts support **459 / 479 / 493** planned updates, rather than the checker’s earlier approximations.

(3) **What is good and should remain unchanged.**

- The hierarchy now correctly prevents M2 from rescuing a failed primary contrast and preserves M1 when the secondary fails.
- Requiring both languages’ full frozen MATH ID sets closes the illustrated missing-English and incomplete-response paths.
- Deterministic `equiv500` remains primary; model adjudication remains secondary.
- Paired MATH contrasts, fixed bootstrap settings, and the distinction between screening tolerances and demonstrated non-inferiority are appropriate.
- Computing reference and candidate loops with the same function removes the hard-coded inconsistency.
- The supplied assembly evidence supports preserving paired prompts, shared replay/English blocks, and M1’s inclusion in M2. The reported attestation has **0 mismatches across 14,042 checked pairs**; I have not independently rerun it.
- Prompt-validation invalidation and solution hash re-keying are appropriate mechanisms to retain.

(4) **Answers to the brief’s specific questions.**

**Can HOLD lift?** No. F1–F3 require narrow closure evidence. The hierarchy issue is closed by code inspection; reporting and escape-repair closure remain partial. No recipe redesign is warranted.

**27 versus 23 loops:** The current script consistently applies one rule, and Case A reports **27/500, or 5.4%**, for the reference and its copied responses. That demonstrates implementation consistency. It does not establish why the historical count changed by four: the old function and the four differing IDs are absent.

**Exposed item:** `test/number_theory/239.json` is explicitly annotated, and the primary exclusion sensitivity uses 499 items. This addresses the requested primary annotation. The “incorrect” statuses in Case A are fabricated-fixture statuses, not results from the three actual continuations. If M2 qualifies, reporting secondary exclusion sensitivity would also be useful.

**The five missing rows:** The two-stage filtering explanation is arithmetically coherent:

- Previous snapshot: `1,376 − 5 = 1,371 = 1,358 train + 13 dev`.
- Current snapshot: `1,403 − 4 = 1,399 = 1,385 train + 14 dev`.
- Current translated exports: `8,934 + 1,403 = 10,337`.

Section C’s opening **10,306 / 8,930 / 1,376** figures belong to the previous snapshot and should be labelled accordingly. The current four removed IDs are not supplied, so I verified the accounting, not their contamination matches.

(5) **Open questions for the owner.**

1. What are the final exported texts and repair/validation records for `c2_math5_746`, `gsm_310`, `gsm_3230`, and `gsm_3505`? What happened to the Cut-1 unresolved IDs?
2. Can you supply a corrected fixture report covering F1–F5, together with the exact readout/scorer versions used?
3. What explains each receipt-to-trainer token difference, and do trainer-side SHA values match the three repaired manifests?
4. Does frozen §4 prescribe an actionable English MATH safeguard or dev50 format threshold? The script displays both but enforces neither numerically.
5. Which four IDs explain the historical loop-count difference, and which four Level-5 IDs were removed during the current rendered-row contamination check?