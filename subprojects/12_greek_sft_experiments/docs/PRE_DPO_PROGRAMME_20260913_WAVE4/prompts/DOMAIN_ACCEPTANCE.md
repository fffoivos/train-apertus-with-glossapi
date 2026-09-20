# Acceptance checks after generation and correction

13 September 2026. These are execution checks, not a second personality prompt. They apply to new candidates before promotion and after any editor pass.

## Mathematics and serialization

- Parse the strict output schema, then inspect decoded strings. Valid JSON can still contain invalid training text. Reject C0 control characters other than ordinary tab/newline/carriage return, and reject DEL. Do not blindly strip or decode escapes to repair them.
- Preserve LaTeX backslashes through one JSON serialization roundtrip. Keep the original response and the decoded object. Escaped `\\angle` in JSON must become literal `\angle` in text, not BEL followed by `ngle`.
- Check relevant equations, symbols, quantities, units, answer parts and domains against the source and accepted adaptation. A control-character scan alone does not prove valid LaTeX; tabs/newlines can also be symptoms of damaged commands. Inspect rendering and compare notation spans.
- Reject/quarantine ambiguous problem-to-solution joins. Bind each solution to its actual input problem hash, source revision, prompt hash, model, effort and attempt. Duplicate IDs with different texts need a declared version decision; last-record order is not provenance.
- Check the derivation and final answer separately. Reference agreement alone is insufficient. A correct challenge to a bad reference remains eligible after verification. Keep source defects, candidate defects and reviewer disagreements separate.
- Apply the actual tokenizer/chat template and training-window gate to the complete rendered candidate. Report overlength rows; do not clip proofs or tool payloads to make them fit.

## Dialogue, instruction following and tools

- Derive truth/state from evidence available at each turn, then check the actual generated text. Stored labels and state tables cannot validate themselves. Substring checks provide only partial assurance; include adversarial mutations and a full semantic read.
- Check all supervised assistant turns, including earlier acknowledgements and exact-output requests. Protect context-only mistakes with the actual training mask.
- Distinguish historical misquotation from new user information. Accept an authorised current state update without rewriting history.
- Run constraints after Greek correction. Keep valid original language when no defect is evidenced. If the task and constraints conflict, return for semantic repair instead of padding, inventing facts or undoing a correct repair.
- For tools, compare full native schemas, calls, results and IDs to pinned upstream rows. Validate arguments and call/result association, then verify what survives the real assembler. Export roundtrip does not establish trainer support for structured tools.

## Benchmark boundary

Preserve historical scores. Empty-response rejection can be restored to the upstream protocol with a regression check. Greek word/POS ambiguities, tokenization and punctuation rules require explicit versioned measurement decisions and matched rescoring; they do not justify silently changing the leaderboard or designing training data against a defective checker.
