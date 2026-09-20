Implemented the complete offline Phase 0 pilot.

- Code: all required modules, fakeable clients, manifest allocation, ledgers, CLI, and [tests](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/test_dqd.py).
- Prompts/docs: [user_policy.txt](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/user_policy.txt), [turn_quality.txt](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/turn_quality.txt), [RUNBOOK.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/RUNBOOK.md), [ADAPTER_CONTRACT.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/ADAPTER_CONTRACT.md), and [IMPLEMENTATION_NOTES.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/IMPLEMENTATION_NOTES.md).
- Offline runtime initialized with 41 unique family reservations, manifest, SQLite registry, empty stage JSONLs, cost ledger, and receipt. Recorded model calls: 0.

Test result:

```text
Ran 22 tests in 0.071s
OK
```

Known gaps: live inference phases were intentionally not run; external provider termination remains Fable’s watchdog responsibility; the actual tokenizer/chat-template loss mask must still be validated in Fable’s training pipeline.