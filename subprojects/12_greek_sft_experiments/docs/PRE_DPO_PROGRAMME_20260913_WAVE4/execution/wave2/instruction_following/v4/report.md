# Greek instruction-following pilot: v4 review envelope

**Completed:** 13 September 2026, Europe/Athens  
**Current result:** 20 accepted, 0 held  
**Reviewer:** Sol agent  
**Boundary:** This is a candidate-review envelope. No row was promoted to production and no additional model subprocess was called.

V4 keeps the v1–v3 artifacts immutable and gives every row one unambiguous active `current` record. Candidate hashes, checker results, review decision, source review, and change status now live under that record; superseded v3 fields are retained only through explicit lineage hashes rather than appearing as current metadata. The canonical project checker passes all 20 candidates.

Three candidate rows changed from v3:

- `mixa_2026_05543`: the response remains unchanged. The active constraint metadata now states the same accent-and-case normalization rule as the surfaced request, removing the stale “protocol unresolved” description.
- `mixa_2026_06199`: both named official links were checked directly. The response preserves the explicit cancel-or-relocate recommendation and two highlighted spans, while distinguishing early heat-exhaustion action from suspected-heatstroke emergency escalation.
- `mixa_2026_11688`: two short reader-address cues were added: plural politeness in the official version and singular address in the friendly version. The opinion and six occurrences of `ψ` remain intact.

`mixa_2028_03200` is unchanged. The official Orama Elpidas instructions explicitly say that the mailed envelope contains the registration application and gives instructions for the oral swab. The v3 wording “φάκελο με την αίτηση και οδηγίες για το στοματικό επίχρισμα” is therefore supported and is not a factual defect.

The EODY heat page identifies children and people exercising intensely as higher-risk groups, advises cooler hours and reduced exercise during heat, and links to separate heatstroke and heat-exhaustion actions. The Civil Protection page advises avoiding heavy activity in high temperature and prolonged running in the sun. These checks support the retained preventive argument without treating every symptom as the same clinical state.

Files:

- `candidates.jsonl`: the clean 20-row v4 envelope.
- `delta_from_v3.json`: the three actual candidate changes and before/after hashes.
- `source_review.json`: direct official-source adjudications for `03200` and `06199`.
- `checker_results.json`: current checker results keyed by row.
- `receipt.json` and `verification.json`: counts, hashes, and invariant checks.
