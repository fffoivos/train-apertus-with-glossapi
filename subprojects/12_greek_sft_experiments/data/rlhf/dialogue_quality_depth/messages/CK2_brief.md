# Checkpoint CK2 — smoke evidence in; make the forecast honest about what the smoke measured

Context (orchestrator's run, 2026-09-16): the smoke stage ran end to end (6 chats, 15 Apertus completions, 3 Sol calls, every turn
annotated and adjudicated by root: 1 change of 15). Before the successful pod session there were TWO pod sessions that produced zero
completions because of setup failures outside this code (root-owned /workspace; an invalid --max-model-len). Their spend (EUR 0.32 +
EUR 0.40) is correctly in the ledger. `forecast smoke` then returned `admission_status=smoke_only_revised_plan_required` with size 35 at
EUR 18.9 GPU and every size with `annotation_funded=false`. Two defects to fix in this checkpoint; nothing else.

1. GPU rate basis. The forecast derives the billed-cost-per-completion rate from ALL smoke GPU sessions, including the two with zero
   observed completions, which inflates the rate ~6×. Required: the rate basis is the set of GPU sessions with at least one observed
   completion (their billed seconds and EUR, including their own setup time); sessions with zero completions still count as spent
   against the cap but not in the rate. Record in forecast.json which sessions formed the basis and which were excluded and why. Keep a
   stated conservative margin (say what it is). Model the GPU idle time during Sol continuation waves explicitly: per-wave Sol latency
   measured from the smoke ledger × number of waves, added to the GPU wall estimate, rather than hidden in the per-completion rate.
2. Sol reservation reallocation. Observed batching (annotation 5 packets per call; continuation one call per depth wave for all active
   chats) makes the fixed per-phase reservations (annotation 40, user_continuation 38, openings 10, ...) wrong for every size, while the
   120 total is enough for 28 and 21. Plan §11 allows reallocating between phases "only in the recorded forecast while retaining the
   overall 120-call cap and enough capacity to annotate every admitted turn". Required: `forecast smoke` computes and RECORDS a
   reallocation in forecast.json (annotation for the full admitted horizon funded first, then user continuation, openings, candidate
   review, with adjudication and repairs kept small but non-zero), and budget.py honours the forecast's reallocation instead of the
   config defaults once forecast.json exists. Never exceed 120 total including the calls already made (smoke 3). Then admission picks
   the largest predeclared size (35/28/21/14) fundable on BOTH ledgers: GPU to the EUR 4.00 operational stop (EUR 1.00 reserve
   untouched, prior spend deducted) and Sol within the reallocated 120.
Tests for both (fake ledgers with zero-completion sessions; reallocation arithmetic; cap never exceeded). Offline only. Write
messages/impl_CK2_1.md for the reviewer when done.
