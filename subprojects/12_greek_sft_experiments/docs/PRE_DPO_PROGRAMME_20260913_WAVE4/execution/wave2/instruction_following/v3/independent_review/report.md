# Independent semantic review of the 20 IF v3 candidates

**Completed:** 13 September 2026, 16:10:25 Europe/Athens  
**Scope:** All 20 original and candidate request/response pairs in `v3/candidates.jsonl`, including operative constraints, repair metadata, checker results, and the four recorded root source checks.  
**Execution:** Full manual review by the Sol agent; no additional model subprocess calls or production writes.

## Verdict

Sixteen candidates are suitable to keep as written. One response needs constraint repair, one source-checked factual repair introduced a narrow new wording problem, one sound candidate has stale surrounding metadata, and one unchanged health row should retain a source-verification gate before promotion.

All twenty deterministic checker suites pass. That is necessary but not sufficient: `mixa_2026_11688` passes its surface checks while failing to realize the requested politeness-plural versus friendly-singular distinction, and `mixa_2026_05543` has a sound current candidate but metadata that still describes the superseded unresolved protocol.

## Required repairs

- `mixa_2026_11688`: reauthor the two opinion versions so one actually addresses the reader in politeness plural and the other in friendly singular. The current headings and register difference do not execute that person constraint. Preserve the balanced equality/excellence arguments, no-exclamation rule, and six ψ occurrences.
- `mixa_2028_03200`: the dated scenario and refusal to assert unverified history are good. The answer says the applicant receives an envelope “with the application and instructions for the oral swab”, while the recorded official finding supports an application followed by a mailed cheek-swab kit. Use `θα λάβεις κιτ στοματικού επιχρίσματος με οδηγίες`. This is the only observed case where a v3 factual repair introduced a new narrow defect.
- `mixa_2026_05543`: keep the candidate row. Regenerate `constraint_mapping`, `expected_result`, `changes`, `issues`, and `semantic_read`, which still say the exact-word protocol is unresolved even though `root_revision` and the current request explicitly choose accent/case-insensitive lexical identity.

## Source and evidence boundary

The four root-authored factual revisions were reviewed independently against the source conclusions recorded in `source_review.json`:

- `mixa_2028_08593` correctly defers IP configuration, register maps, Unit ID, scaling, byte order, and configured port to the actual device/manual. It treats TCP 502 as usual rather than universal and does not treat ping as proof of Modbus service health.
- `mixa_2027_09689` separates public/private dental routing from hospital escalation for breathing, swallowing, or major-swelling symptoms. It avoids predicting private appointment speed and preserves exactly three uppercase sentences.
- `mixa_2027_07834` keeps the legal application conditional, cites the relevant directive provisions, preserves the complaint route, and does not guarantee a refund.
- `mixa_2028_03200` needs the kit wording repair described above; the current availability claim itself is supported by the dated source review.

`mixa_2026_06199` remains semantically appropriate for the supplied 39°C outdoor-practice scenario and satisfies its two-highlight constraint. Its named EODY and Civil Protection attributions were not independently checked in this bounded review, so retain a source gate before promotion. This is an evidence-status limitation, not an observed contradiction.

The other rows either summarize user-supplied text, perform fictional or editing tasks, or state ordinary conditional advice. I found no invented user fact in the repaired summaries. In `mixa_2027_01564`, the illness, documents, and date are permissible fictional scene development; the answer avoids committing to a numeric current legal threshold.

## Constraint and semantic findings

- `mixa_2026_06155`: the repair preserves the joke skill by replacing an impossible accent-dependent contrast with an atonic time-flight/return device inside the required wrapper.
- `mixa_2028_05110`: the prompt-level ending repair removes the contradiction and the answer provides complete, useful anti-fraud steps.
- `mixa_2027_09179`: the summary removes unsupported gender and mental-state claims while preserving all supplied facts, three highlights, and three natural ψ occurrences.
- `mixa_2026_08572`: reducing the incompatible 300-word minimum permits one faithful translation and removes four-version padding.
- `mixa_2027_09553`: the new maximum length fits a summary, and the response retains all material EHIC facts in the supplied passage.
- `mixa_2027_10080`: restoring ordinary accents is the correct interpretation of modern monotonic Greek.
- `mixa_2026_04027`: replacing EOPYY with KTEL Larissas removes irrelevant padding while preserving the song route and five format constraints.
- `mixa_2026_07006`: the corrected bank message is source-faithful, valid JSON, and preserves every lexical/orthographic device.
- `mixa_2027_05368`: the access-control comparison is complete and treats the 1,500-euro ceiling as a quote requirement, not a guaranteed current market price.
- `mixa_2026_04931`: the edited ship message asks the agent about the lawful disposal route and receipt rather than inventing them.
- `mixa_2026_08647`: the schedule contains 12 calls and six visits over three field days, assigns both reporters, budgets exactly 90 euros, and reserves later time for synthesis and Friday delivery.
- `mixa_2027_09233`: the lowercase response gives a reasonable approximate lemon-juice pH range and explains dilution dependence.
- `mixa_2027_01564`: the creative scene preserves all characters, 127 absences, the pending decision, title, Greek-order date, and exact ending.

No other repair introduced a semantic, factual, or device-level defect in the inspected rows.

## Artifacts and limits

`adjudications.jsonl` contains one structured independent verdict per candidate, including source fidelity, semantic completeness, unsupported-fact status, constraint preservation, and hashes. `verification.json` records the input and output hashes and exact verdict counts. `build_review.py` validates row coverage and freezes the review file.

The findings apply to these twenty complete pairs. They do not establish a defect rate for the full IF source, checker recall, or production readiness.
