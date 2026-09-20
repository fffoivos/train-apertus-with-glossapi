Implemented CK5 completely and wrote the reviewer handoff: [impl_CK5_1.md](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/dialogue_quality_depth/messages/impl_CK5_1.md).

Files written: `resample.py`, `test_resample.py`, `dqd.py`, `rank.py`, `budget.py`, `candidates.py`, `export_pairs.py`, `pod/run_stage.sh`, `test_pod_runner.py`, `runtime/forecast.json`, `runtime/receipt.json`, and the reviewer message.

Test result: `Ran 60 tests in 18.349s` — `OK`

Known gaps: live GPU/Sol stages were intentionally not executed. The supplied target file contains 15 targets, although plan §30 mentions 16; no unsupported target was invented.