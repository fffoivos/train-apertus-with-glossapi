# Independent review of MATH-500 scorer candidate v2

Review completed: 2026-09-13T17:29:43+03:00  
Scope: all 152 score decisions that differ between frozen v1 and candidate v2  
Inputs read: complete saved response, benchmark problem in English and Greek, benchmark reference answer, and saved English reference solution for every changed decision  
Execution boundary: the frozen scores were not changed. No model calls were made. The scorer was not imported or executed, and no saved response was passed to `sympy` or `parse_expr`.

## Verdict

Candidate v2 should not be adopted unchanged. Its main extraction repair is sound: all 133 newly accepted rows have a final answer that matches the benchmark reference. It also correctly rejects 15 of the 19 frozen-only passes. Three other frozen-only rows are correct categorical answers that v2 rejects, and one separator-ambiguous token is correct once its arithmetic context is read.

Applying only these 152 adjudications would produce 3,230 passes rather than v2's 3,226 or frozen v1's 3,112: 3,229 can be decided automatically after the three categorical fixes, and one more is a context-adjudicated separator case. This is a diagnostic projection, not a certified replacement result, because unchanged rows were outside this review.

| Changed-decision class | Count | Independent disposition |
|---|---:|---|
| v2-only pass | 133 | All 133 are valid final-answer recoveries |
| v1-only pass, genuinely wrong or unanswered | 15 | Keep v2 rejection |
| v1-only pass, categorical equivalent | 3 | Restore pass with narrow categorical rules |
| v1-only pass, separator ambiguous in isolation | 1 | Abstain automatically; context review resolves it as correct |

The row-level decisions and bindings are in `independent_dispositions.jsonl`. Each row records the response file and hash, benchmark ID, reference and hash, both extracted values, both scorer decisions, the independent disposition, and any observed proof-quality issue.

## Apertus English: 9 to 120

The 111-point increase is entirely an extraction effect. All 111 changed Apertus English responses terminate normally, contain an explicit intended final answer equal to the benchmark reference, and were rejected by v1 because its extracted string retained the answer phrase or appended display metadata. In 110 responses there is one final-answer marker. `test/algebra/1425.json` contains two phrase occurrences but one actual final marker line; its final value is still unambiguous.

This does not show a change in the model or prove that all 111 derivations are valid. It shows that v1 failed to score the stored final answers. Full-response review found clear derivation defects despite correct final values in at least these Apertus English rows:

- audit 37, `test/intermediate_algebra/1849.json`: invalid slope and range reasoning ends at the reference value 501.
- audit 50, `test/intermediate_algebra/894.json`: the response does not derive the claimed value and uses incorrect ellipse-focus formulas, then ends at 2.
- audit 108, `test/prealgebra/1865.json`: it repeatedly treats 135% as 13.5% and mixes percentages with counts, then ends at grade 12.
- audit 125, `test/intermediate_algebra/752.json`: the telescoping logarithm cancellation is written incorrectly, then the correct value 3 is asserted.
- audit 126, `test/precalculus/1252.json`: powers of the cube root of unity are mishandled, then the correct value 1 is asserted.

Those rows are passes under an exact-final-answer MATH-500 metric. They must not be cited as evidence of correct proofs.

## The 19 frozen-only passes

V2 correctly removes 15 false passes created by the old empty-string collapse or by an incomplete response. Examples include circle versus ellipse, west versus east, Angela or Carla versus Evelyn, and the length-terminated response that ends at `$$=` without choosing even, odd, or neither.

Three categorical rows should remain passes:

- audit 129: `E` is the same requested option label as `(E)`, and the response correctly derives hyperbola.
- audit 147: Greek `άρτια` is the grammatically required form of `even` in the Greek prompt.
- audit 150: `C) Plane` gives both the correct option label `(C)` and the matching category name.

Audit 143 should remain a failure. `rotated ellipse` contains the base category `ellipse`, but the displayed graph is axis-aligned. Discarding the false modifier would turn a false final claim into a pass. Categorical normalization should therefore use a closed alias table and anchored option-label grammar, not arbitrary substring or modifier removal.

Audit 130 is the separator case. The isolated Greek-output token `1,250` can denote 1.25 or 1250, so the response language cannot decide its value. The complete response also writes `1,000,000 × 0.00125 = 1,250`; that arithmetic and the response's own grouping convention establish an intended result of 1250. The row is correct after context adjudication. It is evidence for an ambiguity state, not for a language-based separator rule.

## Extraction review

The same-line final-answer repair works for the observed Apertus pattern. In particular, `_rhs` stops at the closing `$`, so appended display metadata does not contaminate the value.

The implementation and report diverge on following-line answers. `extract` does not attach the next nonempty line to an empty marker. The existing test passes accidentally because `$9$` is the final nonempty line and the function falls back to the last line. A response such as `Answer:` followed by `9` and then an explanatory sentence would extract the explanation. This requires a real next-line state and a regression test containing later text.

The precedence rule also needs explicit treatment. V2 always returns the last balanced `\boxed{...}` before examining final-answer markers, even if a later marker states the actual final answer. A defensible extractor should record candidate type and character span, prefer the last explicit answer-bearing construction by position, and return an ambiguity state when competing final constructions disagree. Un-delimited text after a marker also needs a bounded grammar so explanatory prose is not absorbed into the answer.

## Categorical policy

A narrow policy can recover the three correct categorical rows without reviving v1's false positives:

1. Remove only presentation wrappers and terminal punctuation.
2. Parse an anchored option label such as `E`, `(E)`, or `C) Plane`. When both a label and name appear, require them to agree with the problem's actual option list.
3. Use a closed bilingual alias table with ordinary Greek inflections, including `άρτια` for `even`.
4. Keep arbitrary extra modifiers semantically active. `rotated ellipse` must not normalize to `ellipse` for this problem.

This policy requires the problem and option list at comparison time. Reference/prediction strings alone are insufficient to validate a label-plus-name answer safely.

## Numeric separator policy

Do not select decimal or grouping interpretation from the output language. A single comma or dot followed by exactly three digits should yield `ambiguous_separator` unless the token itself or response-local evidence establishes a convention. The scorer should preserve the raw token, detected separator pattern, and decision source.

For benchmark reporting, use a tri-state result:

- `pass` or `fail` when the representation is unambiguous;
- `abstain_ambiguous_separator` when it is not;
- a separate blinded adjudication record when full response context resolves the token.

The aggregate should report automatic pass/fail/abstention counts and a context-adjudicated result. The benchmark reference must not be used merely to choose whichever parsing makes the prediction pass.

## Symbolic and unit handling

The categorical-before-stripping change fixes the demonstrated empty-string bug, and removing only recognized trailing units is directionally correct. Composite units and powers still need explicit positive and negative tests.

The symbolic fallback blocks release. It sends transformed model text to `sympy.parsing.sympy_parser.parse_expr`, which is evaluation-based. Its LaTeX conversion is also mathematically invalid: removing `\frac` and replacing braces with parentheses turns a fraction into adjacent parenthesized expressions rather than division. Until a safe, limited parser is available, use deterministic normalization plus parsers for explicitly supported numeric, rational, radical, and polynomial grammars. Unsupported expressions should abstain rather than execute or guess.

## Release gate

Before scoring the 22 frozen cells again:

1. Implement true following-line extraction and position-aware conflict handling.
2. Add the anchored option-label and Greek-inflection rules, preserving the failure for `rotated ellipse`.
3. Replace language-forced separators with the tri-state ambiguity policy and blinded context adjudication.
4. Remove the evaluation-based symbolic fallback or replace it with a safe, closed grammar.
5. Add regressions for every changed-decision exception above, freeze the scorer digest, and rescore every cell with the same scorer version.

No claim about model ranking should use the candidate v2 totals before these gates are met.
