# Correcting decisions pilot: first 12 of 120

Prepared 13 September 2026 by the Sol agent. This is semantic authoring only; Greek correction and independent review remain separate.

The candidate file contains 12 short Greek dialogues: three true corrections, three false corrections, three partly true corrections, and three unresolved claims. Cooperative, neutral, and assertive users occur in each truth group. Earlier assistant errors appear only where the teaching scenario needs them and all six such turns are marked `train:false`.

Each decision links the user's claim turn, the target assistant turn, and a local evidence record. Evidence is limited to arithmetic, visible message counts, explicit list membership, and declared schedule or route state. Null state is treated as unresolved. No legal, medical, current-price, or other externally changing claim is used. Model self-description is absent from the evidence and is never treated as an oracle.

The deterministic verifier passed:

```json
{"masked_assistant_turns": 6, "rows": 12, "status": "PASS", "supervised_assistant_turns": 19, "truth_counts": {"false": 3, "partial": 3, "true": 3, "unresolved": 3}}
```

The verifier derives truth from evidence atoms, computes arithmetic and list differences, counts actual user messages, checks exact-output turns, validates state values in the target, checks clarification questions for unresolved cases, and validates speaker ownership and train masks. It does not accept the stored expected truth label as evidence. Substring inclusion checks cannot prove complete semantics, naturalness, or that every claim in a target is correct; those remain work for the independent review.

Artifacts:

- `pilot12_candidate.jsonl`: complete candidate records and dialogues.
- `pilot12_evidence.json`: evidence policy and compact row-evidence table.
- `pilot12_verifier.py`: deterministic verifier.
- `pilot12_verification_report.json`: execution receipt and limitations.

Passing these checks establishes the declared arithmetic, state, list, exact-output, ownership, and masking properties. It is not a Greek-language acceptance decision or an independent semantic review.
