# GreekMMLU protocol reconciliation: concrete mismatch found

13 September 2026. This is a code and saved-output audit; no new model score was run.

Our saved Krikri result is 8,650/16,632 = **52.0082%**. Reaggregating its 31 saved subject groups gives **53.6175%**. Neither reproduces the paper’s **66.47%**. The remaining gap cannot be assigned to one cause without matched measurements.

| Dimension | Frozen project evaluator | Current official implementation |
|---|---|---|
| Prompt | Generic request to choose an answer, followed by question/options | Subject-specific Greek request with question/options |
| Scored continuation | Entire answer text, prefixed with a space | Greek option label Α, Β, Γ or Δ |
| Choice score | Average answer-token log probability | Harness multiple-choice log likelihood over label continuations; acc |
| Aggregate | Full item-weighted headline and 31 subject groups | Size-weighted task-group accuracy, with 45 subject/education configs |
| Template | No chat template in custom scorer | Published helper shows no apply-chat-template flag; verify the exact comparison invocation |

The official files are pinned at commit `cd944748e860fda3e9dc21212c2f2710615ecdc5`; `receipt.json` contains exact URLs and hashes. Relevant evidence: [official task utilities](https://github.com/mersinkonomi/GreekMMLU/blob/cd944748e860fda3e9dc21212c2f2710615ecdc5/lm-evaluation-harness/lm_eval/tasks/greekmmlu/utils.py), [task configuration](https://github.com/mersinkonomi/GreekMMLU/blob/cd944748e860fda3e9dc21212c2f2710615ecdc5/lm-evaluation-harness/lm_eval/tasks/greekmmlu/_default_greekmmlu_template_yaml), [paper](https://aclanthology.org/2026.findings-acl.448.pdf). Current code is not proof that every historical publication run used exactly that commit.

The local metric name `official_zero_shot_accuracy_from_average_answer_token_logprob` does not establish official-protocol equivalence. Preserve those historical results as a **custom full-answer continuation diagnostic**. Do not compare them directly with the published leaderboard or overwrite the historical evaluator/results.

Next: freeze 200 identical items, stratified before viewing results, and evaluate original Krikri and G3F2P1 under both the frozen custom and official-label protocols. Record exact dataset revision and intersected row IDs, prompt bytes, label tokenization, normalization, template, truncation, precision and aggregation. Separate the effect of prompt from continuation choice if the main difference is large. This is a diagnostic subset, not a new full benchmark score. Keep it within the existing shared four-node-hour measurement allowance; price before allocation.

Knowledge training should include genuine recall, evidence use and explained MC choices. A format/protocol discrepancy is not evidence that more MC examples alone will fix knowledge.
