# Instruction following and non-maths reasoning — version 1

Produce or repair one example under the supplied operation and target language. The input defines its skill, facts, permitted transformations, literal constraints and checker conventions. Fulfil the substantive request as well as its measurable constraints. A correctly formatted but irrelevant answer fails.

For adaptation, preserve logical structure, quantifier scope, negation, conditional direction, alternatives, exceptions, temporal order and the information available. Rebuild language-dependent mechanics in the target language only when the specified mapping preserves the task's difficulty and checkability. Record that mapping. If the mapping weakens the task or cannot be checked by the supplied checker, report blocked; do not quietly choose an easier constraint.

For IF, use the provided definitions of word/token counts, sentence boundaries, case, Unicode normalization, exact strings and option labels. Do not substitute your own counting convention. Keep the request and target consistent with the same constraints. If the specification is contradictory or unsatisfiable, report it; semantic repair may propose an explicit request change only when that operation is allowed.

For reasoning, show the necessary deductions from the given premises. Do not assume the converse, uniqueness, exclusivity or missing facts. When the task asks whether a conclusion follows, preserve distinctions among entailment, contradiction and insufficient information. Plausibility is not entailment. Keep any deliberate ambiguity or missing premise if it is what the example teaches.

Use natural language within the valid solution space. Do not solve a pronoun restriction by making all prose awkwardly passive, or meet a length constraint by deleting required content. A source for a rewrite task must actually exhibit the property being transformed. Mask erroneous historical context when it is not intended for supervision.

Return one JSON object with: row_id; status (candidate or blocked); messages; preserved_invariants; constraint_mapping; expected_result; explanation; checks_needed; changes; issues. Only report a checker result as executed if actual tool output is supplied. Your expected counts or logical result remain proposals until independently checked.
