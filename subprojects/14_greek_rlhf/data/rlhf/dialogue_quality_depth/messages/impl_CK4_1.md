# CK4 implementation response

## What I built

`export_pairs.py` now implements the owner's 2026-09-16 evening pair rule as `owner-pair-rule-2026-09-16-evening-v1`:

- `_pair_ids()` chooses the highest-ranked candidate whose absolute verdict is `reinforce` and the lowest-ranked candidate whose verdict is `neutral` or `discourage`.
- `_tied_with_next()` rejects only a tie containing the chosen candidate and its immediate next-ranked candidate. A tie confined to lower candidates does not block the pair.
- A pair is emitted only when `best_vs_worst == "clear"`; both `slight` and `none` are rejected as `no_substantive_preference`.
- A ranking with no `reinforce` candidate remains rejected as `no_acceptable_chosen`. Chosen-unusable, missing-candidate, prefix-integrity, and completion-mask checks remain in force.
- `rank.py` was not changed because `ties_candidate_ids`, candidate order, verdicts, and `best_vs_worst` already contain all information required by the rule.

Export regeneration is now idempotent and crash-safe:

- `_atomic_jsonl()` replaces `preferences.jsonl` and `rejected_pairs.jsonl` atomically instead of appending or refusing non-empty prior outputs.
- The export derives a SHA-256 over the three source JSONL files. When the rule and source hash are unchanged, it preserves the export timestamp, making reruns byte-identical.
- `pair_rule_version` is recorded in every accepted-pair receipt, every rejected-pair row, `pair_export_receipt.json`, and both artifact entries in `runtime/receipt.json`.

The real measurement export was regenerated. It now contains 11 accepted pairs and 13 rejected prefixes. In particular:

- `SEL018` is accepted as `SEL018:c2` over lowest-ranked `SEL018:c1`; the tie between lower candidates `c0` and `c1` no longer blocks it.
- `SEL022` is also accepted despite a tie confined to its two lower discourage candidates.
- `SEL003`, whose margin is only `slight`, is now rejected as `no_substantive_preference`.

## How I tested it

`test_dqd.py` now executes the four requested cases against the exporter:

1. reinforce plus two tied neutrals produces a pair;
2. two tied reinforce candidates at the top are rejected as `tie`;
3. a clear reinforce-versus-discourage comparison produces a pair;
4. all-neutral candidates are rejected as `no_acceptable_chosen`.

An additional regression proves a `slight` margin is rejected and that two successive exports produce byte-identical preferences, rejected rows, pair receipt, and versioned global receipt data.

Full offline suite:

```text
$ python3 -m unittest discover -p 'test_*.py'
......................................................
----------------------------------------------------------------------
Ran 54 tests in 18.426s

OK
```

Actual export rerun, performed twice:

```text
DQD_OK export accepted=11 rejected=13
```

The second run retained these exact hashes:

```text
88cb3a4c3e9bfbd3024f594a5f8cc07b42fad3359c51827208d07a32ee3c4f96  runtime/measurement/preferences.jsonl
b7b84985f67ce72dc5a8799a4823ea3cc991176a45237e0f7cb325f5deed3aed  runtime/measurement/rejected_pairs.jsonl
d6f1f94b094151f72df94a8a82d6a1ab9958448b8029fea3cd864e7c7c1a97bc  runtime/measurement/pair_export_receipt.json
86abbc72b1da8cd3880f078d03f9643019baa9dce41e8a275c5f1b9ff221e14a  runtime/receipt.json
```

## What I could not do

Nothing required by CK4 remains unperformed. The checkpoint was explicitly offline, and the change only reinterprets already-recorded rankings, so no new model, Sol, network, or GPU call was needed or made.
