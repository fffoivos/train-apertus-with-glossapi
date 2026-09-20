# Benchmark translation or audit — version 1

The purpose is to preserve a measurement instrument. Translate or audit only the supplied benchmark item under its fixed protocol. Do not apply the SFT cultural-distribution rule or replace a subject with an easier Greek analogue.

Preserve the actual question, facts, difficulty, ambiguity, mathematical relations, choices and requested output. Use natural target-language wording and conventional names without changing the tested knowledge. Keep the answer key outside the model-facing prompt. Do not repair a suspected source error silently: report it and preserve the historical item until a versioned evaluation decision is made.

For language-dependent constraints, use the supplied target-language checker definition and adaptation policy. Verify that the translated instruction and checker describe the same operation. Record unavoidable changes in difficulty or semantics. If comparability is lost, mark protocol_review; do not claim the original benchmark score remains directly comparable.

In audit mode inspect actual item text and checker evidence; do not infer a checker passed merely because the answer appears compliant. Never tune this item using a particular model's failure or use it as a training example.

Return one JSON object with: item_id; status (candidate, unchanged, or protocol_review); translated_item (null when auditing only); preserved_properties; deviations; suspected_source_errors; checker_findings; evidence; required_review. Model-facing fields must exclude answer keys and review notes.
