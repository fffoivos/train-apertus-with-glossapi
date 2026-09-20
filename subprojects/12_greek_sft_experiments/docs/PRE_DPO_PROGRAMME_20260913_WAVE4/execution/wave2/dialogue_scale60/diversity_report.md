# Dialogue scale-60 specification report

Prepared `2026-09-13T14:22:12.878114+00:00`. This is a prospective, train-only specification batch: 60 decisions in 20 new fictional families. It contains no authored assistant targets, model calls, queue, development content, or final-confirmation material.

## Allocation

Ten families carry true, false, partial and unresolved variants; ten carry true and false variants. The resulting decision counts are `{'true': 20, 'false': 20, 'partial': 10, 'unresolved': 10}`. This is exactly one tenth of the 600-row training target of 200 true, 200 false, 100 partial and 100 unresolved. The separate 60-row development and 60-row final-confirmation targets remain outside this batch. The earlier 420-row training interpretation is superseded.

## Breadth

The 20 structure signatures are unique. Evidence forms include revised scalar drafts, ordered lists, day-to-item maps, disjoint stock partitions, subset arithmetic, weighted scores, graph reachability, fictional conditional rules, speaker-attribution maps, boolean checklists, and named text-task states. Skill counts are `{'version_editing': 18, 'state_inference': 14, 'premise_handling': 10, 'cancellation': 4, 'speaker_ownership': 6, 'stopping': 8}` and oracle counts are `{'version_edit': 18, 'state_inference': 14, 'graph_inference': 4, 'cancellation': 12, 'speaker_ownership': 6, 'rule_inference': 6}`.

All four tone instructions occur 15 times: `{'cooperative': 15, 'neutral': 15, 'assertive': 15, 'frustrated_but_civil': 15}`. They describe conversational stance without forcing prefixes. Every decision has a natural user evidence turn and an unsupervised assistant context turn. The assistant context may organize or acknowledge the visible record but is explicitly barred from becoming oracle evidence.

## Scope safeguards

Every false current-state claim is explicitly tied to a displayed draft, list, board or supplied premise. A following clear update is applied as authoritative current instruction. Unresolved rows either expose a missing field, preserve an ambiguous referent, or limit an inference to the supplied excerpt; none inserts a hidden value. Cancellation and stopping affect only named text records, and the action contracts prohibit claims about external orders, reminders, devices or services.

The batch uses the reserved `ds60_` train-family namespace and has no overlap with known revision-2 train or development family IDs. Final-confirmation content was not opened: only its frozen gate summary hash is recorded. This protects the final split from specification tuning.

## Quality boundary

`verify_scale60.py` recomputes every truth label and post-request state from evidence, checks the 20/20/10/10 distribution, mask plans, action scope, tone balance, family uniqueness and known split separation. These specifications still require full semantic review before any authoring. They do not establish that 600 training dialogues have been produced or that this 60-row batch is quality-ready for scale.
