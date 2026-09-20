Fixed the provisioning failure.

Updated:

- [pod/dqd_provision.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/pod/dqd_provision.py)
- [test_pod_runner.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/test_pod_runner.py)
- [messages/impl_CK3_3.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK3_3.md)

Provisioning now retries distinct eligible offers after create-POST HTTP failures and prefers non-low stock within the 20% price window.

```text
Ran 50 tests in 15.792s

OK
```

Next command:

```bash
bash pod/run_stage.sh measurement
```

Known gap: the revised failover has been validated offline but not yet against a live Prime provisioning attempt. No files outside the directory were modified.