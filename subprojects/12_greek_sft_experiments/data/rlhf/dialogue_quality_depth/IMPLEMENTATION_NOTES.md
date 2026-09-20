# Phase 0 implementation notes

This directory implements the offline software path only. No provider, Apertus, Sol, pod, network, CSCS, training or plan §12 execution was started by implementation.

## Prompt visibility

- Opening writer: sees source `content`, opening `instruction_spec`, language, task, difficulty, interaction, attitude and register for several independent seeds. It never sees `reference`, `checks`, fixture parameters, evaluator labels, future turns or candidates.
- User simulator: sees only the frozen `user_policy.txt`, one or more independent visible conversation prefixes, and each user's public goal, interaction plan, language, attitude and register. It never sees the fixture, reference answer, checks, annotations, rankings, later turns or candidate replies.
- Turn annotator: sees one prefix ending at the response under review, visible task state, private reference/checks where applicable, and the local executable verifier result. It never sees a later message from that trajectory; batching prohibits two prefixes from the same trajectory in one call.
- Candidate ranker: sees the frozen rubric v2.4 verbatim, the selected prefix, three randomly lettered texts and pilot tie/acceptability rules. Candidate provenance is absent. Mapping back to candidate IDs happens after the response.

## Sol call accounting

Every attempt is atomically inserted in `runtime/registry.sqlite` and appended as `call_reserved` to `runtime/ledger.jsonl` before a request. Completion/failure/ambiguity is a second immutable record. Failed attempts count. Default reservations are exactly: smoke 6, openings 10, user continuation 38, annotation 40, adjudication 10, candidate review 8, repairs 8; total 120. A forecast may replace phase reservations only if all values are nonnegative and the total remains at most 120. Openings batch up to 8 seeds, continuation batches up to 8 independent prefixes per depth wave, annotation batches at most 8 short or 4 long packets and 24,000 estimated tokens, and ranking batches up to 4 independent selected prefixes. Human adjudication ingestion itself makes no Sol call.

Target preflight, raw rollout and candidate requests use the same append-before-request ledger. Sampling is fixed at temperature 0.8, top-p 0.95, maximum 1500 new tokens, `n=1`, no added system prompt. Ambiguous timeouts are terminal and never silently retried; an observed completion recovered from the ledger is final.

## Known gaps

- Standard-library code cannot verify Fable's external tokenizer/chat-template serialization or actual training loss mask. The adapter contract and reference label helper must be tested in that pipeline.
- The watchdog computes and exposes a conservative deadline, but provider termination is deliberately not implemented because no authorized provider control API is specified. Fable must run an independent teardown watchdog and confirm termination.
- Exact verifier hooks cover declared numeric and preservation checks; proof quality, natural-language constraint meaning and factual-source interpretation still require annotation/review.
- Token estimates used only for safe batching and admission are conservative UTF-8 estimates, not checkpoint tokenizer counts. Actual server usage is retained when available.
- SQLite plus append-only JSONL gives process-safe reservation accounting, but a machine loss between the SQLite commit and JSONL fsync can require manual reconciliation; the database reservation remains counted and blocks silent retry.
- Sparse language cells, simulator bias, observed-horizon censoring, local-preference causality, provider billing semantics and downstream trained-model effects remain unmeasured.

Only the Phase 0 statement “offline tests pass” may be made after the test command succeeds. No checklist box in plan §12 is claimed complete.

