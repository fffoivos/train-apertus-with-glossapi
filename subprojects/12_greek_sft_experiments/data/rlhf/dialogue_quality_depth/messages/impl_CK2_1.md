# CK2 implementation response

## What I built

1. GPU rate basis and explicit Sol-wave idle accounting

   Changed `forecast.py` in `gpu_rate_model`, `estimate_for_size`, and `forecast`.

   - Completed GPU sessions are joined to immutable `observed_completion` records by their billed start/stop interval.
   - Only sessions containing at least one observed target completion form the billed completion-rate basis. Their complete billed seconds and EUR, including their own setup time, are recorded in `smoke.gpu_rate_model.included_sessions`.
   - Zero-completion sessions are recorded in `excluded_sessions` with reason `zero_observed_target_completions`. Their EUR remains included in `smoke.gpu_spent_eur` and is deducted before the EUR 4.00 operational-stop test.
   - Completed `sol:user:smoke:wave*` reservation/completion timestamps provide measured continuation latency per smoke depth wave. This latency is removed from the productive per-completion basis and added back explicitly for each future depth wave, scaled by continuation batches per wave.
   - Forecast options record productive time/cost, Sol-idle time/cost, seven continuation waves, batch scaling, and estimated billed wall time. A stated 15% conservative margin applies to both productive and explicit idle time/cost.

   On the real smoke ledger, the included basis is pod `8c034ef994094a2d859277b0c6bbedc4` (15 completions, EUR 0.1478038141). Pods `4d4fe67f108b4a528d8f494fa7a93466` and `330f8c4ae4864a3cac7a3d1abd8169f8` are excluded from the rate because they produced zero completions, but their spend remains in the cumulative EUR 0.8651012122. The corrected size-28 estimate is EUR 2.9818426697 against EUR 3.1348987878 remaining to the operational stop.

2. Recorded Sol reservation reallocation and admission

   Added `forecast.py::reallocate_sol_reservations` and integrated it into `forecast`.

   - Each size first reserves the complete eight-turn annotation requirement, then user continuation, openings, and candidate review. Adjudication and repairs each retain a non-zero cap of 1.
   - Existing attempts are included before testing the 120-call total. Failed or incomplete attempts remain counted through the SQLite ledger's attempt counts.
   - Every option records its minimum phase caps, future requirements, used calls, overall cap, fundability, and proposed final caps.
   - Unused headroom is assigned to annotation contingency; no calls are left unallocated and the effective caps sum to exactly 120.
   - Admission selects the largest predeclared size passing both the remaining-GPU and reallocated-Sol tests.

   The corrected frozen runtime forecast admits 28 trajectories. Its effective caps are: smoke 6, annotation 74, user continuation 28, openings 4, candidate review 6, adjudication 1, repairs 1; total 120. The minimum size-28 requirement is 102 calls including the six already used. Size 35 is rejected because its minimum Sol caps total 124 and its GPU estimate exceeds the remaining operational allowance.

   `budget.py::CallLedger._sol_limits` already loaded and validated `forecast.json::sol_reservations`; no production change was needed there. The new test exercises this path, including phase exhaustion and the hard total cap.

3. Frozen runtime correction and audit trail

   `forecast.py::forecast` permits only the specific legacy `smoke_only_revised_plan_required` artifact with no admission, no CK2 rate model, no Sol reallocation, and no measurement artifacts to be superseded. It appends the complete prior forecast and hash to `runtime/forecast_revisions.jsonl`, then freezes the corrected forecast and receipt. Any admitted or already-CK2 forecast remains immutable.

   Updated `runtime/forecast.json` and `runtime/receipt.json`. The new receipt hash matches and is frozen. The prior forecast hash is `b4ebca09f03e1b88e0ce9e2e182a04b80cedd77491e47c6a1cd9a38de5a5149a` and is retained in the revision log and new forecast metadata.

## Testing

Added offline regressions in `test_dqd.py`:

- `test_forecast_rate_uses_only_sessions_with_observed_completions`: a zero-completion session remains spent but is excluded from the rate; a successful session supplies the rate; measured Sol latency becomes explicit idle; the 15% margin is recorded.
- `test_sol_reallocation_funds_in_priority_and_never_raises_cap`: size 28 is reallocatable within 120, annotation is fully funded, adjudication/repairs stay non-zero, and the size-35 requirement is rejected.
- `test_call_ledger_honours_forecast_reallocation_and_total_cap`: the forecast replaces config phase caps, phase exhaustion is enforced, and a seventh attempt beyond a six-call synthetic total is refused.
- Updated the existing frozen-forecast test to attach its synthetic completion to a billed GPU session.

Command:

`python3 -m unittest discover -p 'test_*.py'`

Result:

`Ran 37 tests in 0.175s`

`OK`

## What I could not do and why

- I did not make provider, Apertus, Sol, pod, network, or training calls; CK2 is offline-only. The forecast uses the already-recorded smoke evidence.
- I did not force the brief's shorthand “smoke 3” into the accounting. The immutable registry contains six Sol attempts: one opening call, two continuation-wave calls, and three annotation calls. The plan requires every attempt to count, so the forecast conservatively records six used calls. The three figure matches annotation calls specifically, not total Sol usage.
