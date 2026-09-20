# Factual knowledge and multiple choice — version 1

Write or adapt one training example in the supplied target language and requested format: short answer, multiple choice with explanation, or evidence-based QA. Use the supplied source passages and evidence IDs. Preserve the specified skill and difficulty. Do not draw from evaluation questions or their translated/paraphrased forms.

When adaptation changes a cultural subject, rebuild both the question and answer from evidence about the new subject. Never transfer a foreign institution's law, history or properties to a Greek name. If support for the analogue is missing, report blocked. For a retained foreign subject, keep its facts and use the appropriate Greek perspective without changing what is true. Foreign-language retention examples keep relevant knowledge of that language's own world.

Every factual assertion in the target answer and explanation must be supported by the supplied evidence. Do not manufacture citations, dates, sources or confidence. Use the source's stated date and scope; flag facts whose applicability is unclear. Closed-context QA must be answerable from its passage. An unanswerable variant is allowed only when explicitly requested and its missing evidence is deliberate.

In MC format, use the assigned option order and correct-answer position. Exactly one option must satisfy the question under its stated scope. Distractors must be plausible but demonstrably wrong for this question, mutually distinguishable and comparable in form; avoid ambiguous aliases, length clues and grammatical cues. Record why each distractor is wrong. If the evidence cannot establish uniqueness, block the candidate. Dataset-level position balancing is the coordinator's job; do not claim balance from one row.

Preserve an appropriate direct answer and enough explanation to support it. Do not expand a factual answer into generic advice or replace a requested explanation with just a letter. Keep evidence notes outside the target except where the requested answer format itself calls for citations.

Return one JSON object with: row_id; status (candidate or blocked); question; context (if any); options (if any, with fixed IDs); answer; explanation; supporting_evidence (claim to source-span/ID mapping); distractor_checks; adaptation_record; issues. Mark the record's family ID unchanged so all variants stay in the same split.
