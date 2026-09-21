VERDICT RESPONSE: CK1 cycle 4 finding addressed

1. Agreed.

   Changed `rollout.py::validate_stage_horizon` and `rollout.py::rollout`. The new validator fixes the stage horizons at exactly 3 for smoke and exactly 8 for measurement. `rollout()` invokes it as its first operation, before state reads, generator-isolation checks, ledger construction, runtime-config preflight, or any target/Sol provider call. An omitted `--max-turns` resolves only to the fixed horizon for that stage; an explicit mismatch raises a stage-specific error.

   Changed `dqd.py::MachineArgumentParser.parse_args`. The root parser now validates the rollout stage/horizon combination immediately after syntactic parsing. Thus `rollout measurement --max-turns 3` is a parse failure before `HTTPApertusClient` is constructed or `with_sol` can start the Sol client. The existing `[3, 8]` integer choices remain a first syntax filter, while the post-parse combination check enforces the stage-specific value.

   Added `test_dqd.py::RolloutTests.test_measurement_three_turn_horizon_rejected_before_checks_or_clients`. It proves measurement/3 and smoke/8 are rejected before the generator check and verifies that target `models`, target `complete`, and Sol `call` are never invoked.

   Added `test_dqd.py::CLITests.test_parser_rejects_measurement_three_before_client_construction`. It invokes the CLI with measurement/3, checks the machine-readable parse failure, and proves neither target-client construction nor Sol-client construction occurs.

Validation command:

`python3 -m unittest discover -p 'test_*.py'`

Result:

`Ran 34 tests in 0.187s`

`OK`
