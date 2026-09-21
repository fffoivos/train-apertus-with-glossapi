CK3 is complete.

Entry command:

`bash pod/run_stage.sh <measurement|candidates>`

Implemented:

- Hardened provisioning adapter and pod setup.
- Strict pre-download filesystem, disk, driver, wheel, and GPU-memory checks.
- Exact model SHA and config-derived context-length verification.
- Fail-fast vLLM readiness checks and SSH tunnel.
- Independent budget-deadline watchdog.
- Guaranteed ledger stop, pod deletion confirmation, and one-line receipt.
- Secret-safe handling without tracing or logging.
- Fake-pod coverage for all requested success and failure paths.

Reviewer handoff: [impl_CK3_1.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK3_1.md)

Validation:

`Ran 43 tests in 7.418s`

`OK`

No network, pod, provider, Apertus, or Sol calls were made.