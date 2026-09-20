Implemented all four reviewer findings.

Files updated:

- [pod/dqd_provision.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/pod/dqd_provision.py)
- [pod/dqd_pod_setup.sh](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/pod/dqd_pod_setup.sh)
- [pod/run_stage.sh](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/pod/run_stage.sh)
- [test_pod_runner.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/test_pod_runner.py)
- [messages/impl_CK3_2.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK3_2.md)

Test result:

```text
Ran 48 tests in 14.970s

OK
```

Known gap: live Prime provisioning, model download, and vLLM serving were not tested because CK3 requires offline work only. No files outside the working directory were modified.