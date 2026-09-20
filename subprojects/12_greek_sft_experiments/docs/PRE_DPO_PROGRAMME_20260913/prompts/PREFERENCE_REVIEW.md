# Preference pilot review — version 1

Compare the supplied anonymised answers A and B to the same request and identical conversation history. Use the supplied rubric, factual evidence and expected state. Do not infer model identity. The target language and context define the appropriate voice.

First assess each answer's correctness, instruction fulfilment, use of available evidence, state consistency and appropriate response to the user's actual intent. Then assess completeness, clarity and naturalness. Prefer concise answers only when they retain everything needed; prefer longer answers only when the extra material helps. Do not reward confidence, automatic agreement, automatic disagreement, apologies or elaborate formatting as proxies for quality.

A correction dialogue is assessed against the truth of the disputed claim. A first-person acknowledgement may be useful; a clarification may be necessary; uncertainty may be the correct conclusion. Check these functions before judging style. Distinguish appropriate boundaries from refusal of a harmless request.

Return A or B only when the evidence supports a useful preference and the chosen answer is acceptable under the rubric. Use tie for equally acceptable answers, neither for two unacceptable answers, and insufficient_evidence when pivotal correctness cannot be established. Do not turn a less-wrong answer into an approved training target. Do not rewrite either answer in this rating pass.

Return one JSON object with: pair_id; label (A, B, tie, neither, or insufficient_evidence); per_answer_findings (correctness, task, state, completeness, language, evidence); decisive_reason; uncertainty; eligible_for_training (boolean). Ties, neither and insufficient_evidence are not ordinary chosen/rejected pairs. The coordinator validates eligibility and answer-order consistency.
