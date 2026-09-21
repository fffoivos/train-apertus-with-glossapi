# CK4 cycle 2 implementation response

1. **Top-ranked candidate must itself be `reinforce` — fixed.** The finding is correct. In `export_pairs.py::_pair_ids()`, `chosen_id` is now exactly `ranking_candidate_ids[0]`; if that candidate's verdict is not `reinforce`, export returns `no_acceptable_chosen` without searching lower ranks. The tie gate now explicitly compares `order[0]` with `order[1]`, and the rejected candidate remains `order[-1]`. Empty and undersized ranking guards remain fail-closed. I bumped `PAIR_RULE_VERSION` from `owner-pair-rule-2026-09-16-evening-v1` to `owner-pair-rule-2026-09-16-evening-v2`.

   In `test_dqd.py::test_export_rejects_top_neutral_even_when_second_is_reinforce()`, the exact `[neutral, reinforce, discourage]` regression now proves the prefix is rejected as `no_acceptable_chosen`. The earlier lower-tie, top-tie, clear-margin, all-neutral, non-clear-margin, and byte-identical rerun tests remain green.

   I regenerated the real measurement export twice. Both runs reported:

   ```text
   DQD_OK export accepted=11 rejected=13
   ```

   `SEL018` remains the intended `c2` over `c1` pair, now receipted under v2. The second regeneration retained these hashes:

   ```text
   a3a5d573dff64ed0d57d4a333644b92e60f390238253125f6e32443a1e39cf7a  runtime/measurement/preferences.jsonl
   35adb3c31ad7acaf51264d93a8edeb83e6a5f209871798d05b4f5a6d4d6f58ec  runtime/measurement/rejected_pairs.jsonl
   5b3bebe0af10ee9d9ae7eeb77a739e7b96a37e67f1d1ec6f69a1ceb8bd2f3737  runtime/measurement/pair_export_receipt.json
   95325330e3c3c1a7e2ac7b73ebbd9399adcee092f52e4235ccc3986c0c2bb423  runtime/receipt.json
   ```

Full offline suite:

```text
$ python3 -m unittest discover -p 'test_*.py'
.......................................................
----------------------------------------------------------------------
Ran 55 tests in 17.434s

OK
```

No finding was disputed. No network, Sol, model, or GPU call was made, and no file outside this directory was modified.
