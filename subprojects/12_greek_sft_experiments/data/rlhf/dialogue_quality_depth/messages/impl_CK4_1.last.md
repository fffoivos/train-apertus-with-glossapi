CK4 is complete.

Implemented the owner’s tie rule in [export_pairs.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/export_pairs.py), added five export regressions in [test_dqd.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/test_dqd.py), and regenerated the measurement artifacts. SEL018 is now accepted.

Reviewer message: [impl_CK4_1.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK4_1.md)

```text
Ran 54 tests in 18.426s

OK
```

The export was run twice with byte-identical results: 11 accepted pairs and 13 rejected prefixes.

Known gaps: none within CK4. No network, model, Sol, or GPU calls were needed, and no files outside the directory were modified.