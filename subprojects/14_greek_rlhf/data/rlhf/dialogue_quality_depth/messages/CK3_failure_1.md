# Execution failure 1 — `bash pod/run_stage.sh measurement` (2026-09-16T17:43:55Z)

Provisioning picked the cheapest offer (A100_80GB on runpod, US-MO-1, $1.607/h, stock=Low) and POST /pods/ returned
HTTP 503 "Insufficient Capacity: runpod doesn't have NVIDIA A100-SXM4-80GB available right now". The runner exited with exit=1,
no pod created, no spend (receipt: ledger_stop=not_started teardown=not_needed pod_id=none). Full log:
runtime/pod/measurement_20260916T174355Z.log.

Required: on a 503 / Insufficient Capacity (or any provisioning HTTP error), exclude that offer (cloudId + dataCenter) and try the next
ranked offer within the allowed GPUs and price cap, up to all available offers, with a short wait between attempts; log each attempt;
only give up when no offer is left. Prefer offers with stock != Low when prices are within 20 % of each other. Keep everything else.
Tests: fake availability with two offers where the first POST fails 503 and the second succeeds; and where all fail.
