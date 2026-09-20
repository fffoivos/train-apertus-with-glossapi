# MATH-500 safe scorer candidate v3

Status: candidate only, not ready to pin. Frozen historical scores are unchanged.

## Corrections after independent review

Candidate v3 removes output-language inference from numeric parsing. Tokens such as `1,250` and `1.250` have two defensible readings; when either prediction reading can change the decision, the scorer returns `review` with both rational values. Pinned MATH references retain their English-source convention, so source forms such as `58,500` can be compared to the unambiguous prediction `58500` without using the reference to choose a prediction reading.

The extractor now explicitly takes the first nonempty line following an empty final-answer marker. Its match annotation is `re.Match[str]`. The regression `The final answer is:\n\n$9$\nThanks` extracts `$9$`, rather than falling through to `Thanks`.

No general-purpose parser, `eval`, `sympify`, or `parse_expr` receives model text. Candidate v3 tokenizes at most 96 tokens and 256 characters from a small arithmetic grammar, caps the expression tree at 64 nodes and depth 24, restricts powers to integer magnitude 20, and programmatically constructs SymPy objects. Unknown commands, functions, subscripts, punctuation and parser failures return `review`. The regression confirms `\\frac{a}{b}` equals `a/b` and does not equal `a*b`; this avoids the frozen conversion that deletes `\\frac` and concatenates numerator and denominator groups.

## Exact audit of recorded output

The audit covers 22 exact 500-ID cells, 11,000 responses total. It reads the frozen per-row decisions from their score ledgers and never invokes the frozen `equiv500` or `parse_expr` on model text.

- 1,907 responses reached the frozen general-parser branch after its exact, categorical and numeric branches failed.
- None of those 1,907 rows was recorded as a pass. The unsafe parser therefore contributed zero recorded passes in this corpus, although its execution and conversion remain unacceptable for future output.
- Candidate v3 yields 3,293 pass, 5,454 fail and 2,253 review decisions. These are diagnostics, not adjusted scores.
- The 2,253 reviews comprise one ambiguous prediction (`1,250`), 33 conflicting final constructions and 2,219 unsupported or failed bounded-symbolic cases.
- The frozen scorer recorded 20 passes through empty-to-empty normalization. Candidate v3 preserves the five independently validated categorical equivalents and rejects the other 15.
- Explicit-answer and exact runner-suffix extraction recovers 144 recorded false negatives. The independent reviewer validated the 133 changes inherited from v2; the 11 additional v3 extraction changes still require the same bounded review.

The review rate is 20.5%, so this candidate must not be used as a drop-in final benchmark scorer. Its value is to close code-execution and silent-ambiguity paths while exposing the remaining grammar/adjudication workload. The full 3,396-row decision/review ledger, exact response and recorded-score hashes, and per-cell counts are in `complete_audit_v3_candidate.json`.

The independent review of all 152 v2 changes found all 133 gains valid as final-answer recoveries, 15 frozen-only decisions genuinely wrong or unanswered, three narrow categorical equivalents, and one separator ambiguity that full-response arithmetic resolves as 1250. Candidate v3 implements the three categorical rules and keeps the separator automatic result at review; the blinded context disposition stays separate. Correct final values remain distinct from proof validity: the independent report identifies five Apertus answers with defective derivations despite matching finals.

## Review-state stratification

`v3_review_stratification.json` classifies all 2,253 review rows without semantic scoring:

| Surface class | Rows | Bounded disposition |
|---|---:|---|
| likely extractable compact maths | 1,169 | Extend only observed closed reference grammars |
| likely tail answer inside prose | 616 | Add anchored English/Greek terminal rules; audit every new decision |
| likely incomplete after length termination | 334 | Count extraction failure as zero and report separately |
| prose with no closed answer | 77 | Count extraction failure as zero and report separately |
| conflicting final constructions | 33 | Keep review; resolve from full response without reference-guided selection |
| long surface needing bounded tail extraction | 14 | Apply the same capped terminal extractor before failure |
| malformed incomplete surface | 9 | Count extraction failure as zero and report separately |
| ambiguous separator | 1 | Keep automatic abstention and separate blinded context adjudication |

Reference forms among reviews are 1,031 scalar numeric, 301 fraction, 249 algebraic symbolic, 182 tuple/list, 131 matrix/vector, 122 other, 84 interval/set, 82 radical, 65 plus-minus set and 6 categorical text. The highest-yield bounded work is scalar tail extraction, then safe handling of the benchmark's common fraction/radical/polynomial forms. Matrix, interval, tuple and plus-minus answers should use dedicated structural normalizers rather than a broader expression parser.

## Next gate

Review the 11 new extraction gains and 33 extraction conflicts first. Implement the closed common source forms in descending measured yield, then reclassify genuinely unextractable or incomplete final surfaces as deterministic extraction failures, reported separately from mathematical inequivalence. Every extension needs positive equivalence, negative collision and complexity-bound regressions. This avoids hand-judging all malformed outputs and avoids a general-purpose parser. When the remaining review set is limited to true numeric/final-construction ambiguity, freeze one scorer digest and rescore every selected cell into new files; retain frozen v1 scores under its historical metric name.
