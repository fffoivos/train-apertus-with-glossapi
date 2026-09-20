# Independent review of v3p1 gains against v2

Review completed at 2026-09-13T17:56:31.357822+03:00 by the Sol agent. I read the full localized problem, benchmark answer, complete reference solution, and full saved model response for every one of the **86** exact new-gain row keys. I also read the **5** exact v2 gains that v3p1 no longer passes. The review therefore covers **91/91 unique row keys**. No judging or model subprocess calls were made, and no generated expression was executed.

## Final-answer dispositions

| Review set | Rows | Pass | Fail | Hold |
|---|---:|---:|---:|---:|
| v3p1 new gains versus v2 | 86 | 86 | 0 | 0 |
| v2 gains no longer passed by v3p1 | 5 | 5 | 0 | 0 |
| **Total** | **91** | **91** | **0** | **0** |

All 86 new decisions are valid gains under a final-answer equivalence metric. This conclusion is scoped to these 86 rows and does not establish aggregate scorer correctness. None required a hold: the extracted candidate in each case has an unambiguous mathematical equivalence to the benchmark answer.

The five reversed v2 gains are all v3p1 false negatives. Each saved response ends with an explicit, correct numeric final answer followed by ordinary sentence punctuation (`3.`, `6.`, `36.`, `225.`, `4.`). V3p1 extracts the punctuation with the number and returns `review` for an unsupported token. Their final-answer dispositions should remain pass. One of these five, algebra/1035 in the Greek response, has circular and factually invented intermediate reasoning; that proof defect does not change the unambiguous final answer 3.

## Derivation quality, kept separate from score

| Full-response assessment | Rows |
|---|---:|
| Sound | 40 |
| Correct mathematics with requested-form or simplification issue | 26 |
| Correct final answer with a local exposition/proof issue | 12 |
| Correct final answer with a material derivation fault or contradiction | 13 |

The **13 material-fault** responses remain passes only because this benchmark score is explicitly a final-answer metric. They include invalid intermediate algebra, unsupported geometry claims, contradictory curve classifications, or circular reasoning. The disposition ledger records each defect rather than treating answer agreement as proof validity. The **26 form/simplification** cases include equivalent answers such as `40/105` for `8/21`, `1/sqrt(3)` for `sqrt(3)/3`, decimal answers where a fraction was requested, and radicals not reduced to simplest form. These are equivalence passes, while their instruction-format shortcomings remain visible.

## Reproducibility and limits

[`dispositions.jsonl`](dispositions.jsonl) binds every decision to the exact response file and line, full response hash, exact problem record and line, localized problem hash, reference-answer hash, and complete reference-solution hash. [`source_manifest.json`](source_manifest.json) binds the 86-row change list, v2 and v3p1 complete audits, the 500-row problem file, all 21 response files, and the output ledger. [`review_material.jsonl`](review_material.jsonl) preserves the exact 91 full problem/reference/response triples reviewed, including the eight rows whose response sources currently live under `/private/tmp`.

This review does not modify either scorer, either complete audit, the earlier independent v2 review, or any response. The eight temporary Krikri response rows are bound to their currently preserved `/private/tmp/krikri_v15_scorer_audit_3390957` files by content hash; those paths are less durable than the project result paths, so their hashes should accompany any later archival move.
