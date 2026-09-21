Implemented all three CK1 cycle-3 findings.

Files changed:

- [manifest.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/manifest.py)
- [select.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/select.py)
- [annotate.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/annotate.py)
- [analyse.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/analyse.py)
- [test_dqd.py](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/test_dqd.py)
- [impl_CK1_3.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK1_3.md)

Test result:

`Ran 32 tests in 0.148s`

`OK`

Known gap: the frozen 28-row panel cannot jointly satisfy every largest-remainder margin. The exhaustive solver now records this infeasibility, all 11 deviations, and the omitted playful-attitude cell. No other known gaps.