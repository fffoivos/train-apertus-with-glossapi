Fixed the CK5 pod setup failure and wrote [impl_CK5_2.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK5_2.md).

Cause: the unconditional uv bootstrap failed before either CUDA-specific vLLM command ran.

Fixes:

- Hardened uv bootstrapping in `pod/dqd_pod_setup.sh`.
- Preserved the CUDA-12 install command unchanged.
- Verified CUDA-13 uses plain `vllm==0.29.0` without leaked flags.
- Added bootstrap, fallback, and both-driver-path tests in `test_pod_runner.py`.

Test result: `Ran 62 tests in 24.313s` — `OK`

Next command:

```bash
bash pod/run_stage.sh resample
```