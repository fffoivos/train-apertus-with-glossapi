# CK3 cycle 3 implementation response

## Cause

The entry command reached provisioning correctly, but the imported shared helper's `cmd_provision()` selects only the single cheapest offer returned by `rank_pick()`. The selected runpod A100 80 GB offer had `stock=Low`; its `POST /pods/` returned HTTP 503 `Insufficient Capacity`. That `ApiError` escaped the local adapter, so no remaining eligible availability offer was attempted. The receipt confirms the failure was pre-allocation: no pod ID, no ledger start, and no spend.

## Fix

In `pod/dqd_provision.py`:

- `_offer_identity()` defines retry exclusion by the required `(cloudId, dataCenter)` pair.
- `_ranked_offers()` enumerates availability while reusing the unchanged shared helper's per-offer policy checks (allowed GPU, secure cloud, one GPU, price cap, and no-spot policy). It deduplicates capacity identities. A `Low`-stock offer receives a 20% ranking penalty, so a non-`Low` offer is preferred when its price is within 20%.
- `_provision_with_fallback()` logs every attempt, pins the shared helper to one ranked offer at a time, catches create-POST HTTP errors, excludes that offer, waits five seconds, and tries the next offer until one succeeds or all eligible identities are exhausted. It restores the helper functions after every attempt. If a failed attempt leaves a pod-state file, it stops instead of risking a second billing pod; otherwise the existing helper's polling, immediate state persistence, self-kill, and teardown behavior is unchanged.
- `main()` now routes the `provision` action through `_provision_with_fallback()`; teardown is unchanged. The external `prime_provision.py` was not modified.

In `test_pod_runner.py`:

- `test_provision_retries_next_offer_after_http_error_and_prefers_stock()` supplies a fake availability response where a non-`Low` offer costs 10% more than the cheapest `Low` offer, makes its first POST fail with HTTP 503, and verifies that the second distinct offer succeeds.
- `test_provision_exhausts_all_distinct_offers_after_http_errors()` makes every POST fail, includes a duplicate `(cloudId, dataCenter)`, and verifies every distinct offer is attempted exactly once before failure.
- The prior hostile inherited GPU-count regression remains green.

Validation:

```text
$ python3 -m unittest discover -p 'test_*.py'
..................................................
----------------------------------------------------------------------
Ran 50 tests in 15.792s

OK
```

## Next orchestrator command

Run the same sole entry command again:

```bash
bash pod/run_stage.sh measurement
```

No separate cleanup is needed for the failed attempt in `CK3_failure_1.md`: it created no pod and persisted no pod state.
