# Measurement corrections before the next SFT comparison

The saved MATH-500 comparison contains substantive scorer errors. All original predictions and score ledgers remain preserved. The replacement scorer is still a reviewed candidate, so its totals are not final benchmark results.

The most consequential finding is in Apertus English: independent full-response review verified 111 correct final answers that the old extractor missed. The extraction candidate changes that cell from 9/500 to 120/500. This is a measurement correction, not an improvement in the model. It removes the basis for treating the old 1.8% result as Apertus's demonstrated mathematical ability under this evaluation.

Across all 152 decisions changed by the first candidate, independent review accepted 133 recovered final answers and 15 removals of false passes. Three categorical answers must be restored: an option letter with different wrapping, an ordinary Greek inflection of “even”, and a correct option label accompanied by its correct category name. One ambiguous numeric separator is resolved by arithmetic in the full response; it must have an explicit adjudication record rather than selecting whichever interpretation matches the reference.

Correct final-answer accuracy and valid reasoning remain separate measures. The reviewer found at least five Apertus English responses with a correct final value despite a clearly defective derivation. They count as correct under the usual final-answer metric, while their proof-quality assessment must remain negative. Apply the same rule to our checkpoints and every competitor.

The safe scorer revision now removes general-purpose evaluation of generated expressions and exposes ambiguous or unsupported forms. It still needs narrower grammar and extraction review: a large review count must not become either silent false negatives or an unbounded manual-grading project. Inspect the actual reference forms, handle common equivalent representations consistently, distinguish unextractable answers from mathematical errors, and publish automatic and adjudicated counts separately.

Before ranking models, freeze one scorer, pin its dependencies and regression cases, apply it to the same saved item IDs for every model, and retain the historical metric under a distinct version. No additional GPU inference is required for this repair.

Evidence: `peer_readiness/scorer_v2/independent_review.md`, `independent_dispositions.jsonl`, `V3_REPORT.md`, and their hash-bound receipts. These are diagnostic artifacts pending the final scorer freeze.
