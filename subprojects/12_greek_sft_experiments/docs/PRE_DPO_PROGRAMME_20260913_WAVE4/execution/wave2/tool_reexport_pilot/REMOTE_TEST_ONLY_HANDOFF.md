# Remote freeze and scheduler-test handoff

> Historical pre-staging handoff. Remote staging, strict compilation and scheduler tests were subsequently completed. Use `REMOTE_READINESS_REPORT.md` and the `scheduler_test_only_v2.json` receipts for the current state.

## Current boundary

No payload has been staged and no job has been submitted. Both prebind data-stage contracts have `allow_preparation_submission=false` and placeholder live-receipt bindings. The local compiled artifacts validate schema, dependency ordering and resource routing only; they are not remote manifests.

An earlier attempt to copy the Dolci locator inventory to Clariden was rejected by automatic approval review because the transfer payload included source locators and identifiers. It was not retried or bypassed. Root must perform the reviewed staging step before exact remote compilation or scheduler testing.

## Frozen payload identities

- Dolci pilot contract: `d1ed83ff7049ccfa49a7e12d1492f20a2ef512330abc542b2bc5bc80a29b09e7`
- Dolci runner: `ea86109a26829a61f7b7ec4c2ea277c3e9d2e96f7a1586cedd5fbe48a091aa79`
- Dolci locator inventory: `ee76456f63a7921a2311d45ad7a33cfea2f41dff58b539d4670b27584d47924e`
- OpenMath pilot contract: `1cf73a4038a0ca55b8b5a9b2ea69686edb775e9404f4defc06dfbf66f72031ed`
- OpenMath worker: `33505d07b73e596dceefe1a09c0d7f409eeec8608649f18d27b073ff209b95d2`

## Review sequence

1. Stage each experiment payload and its input files at the exact paths in its prebind contract. Verify every staged byte against the frozen identities before creating outputs or downloading a source shard.
2. Freeze or reuse canonical `apertus-cscs-efficiency` commit `01f4b7e21f39f346df61485bd1818f7ed07c7f44` at the declared canonical code root.
3. Refresh a mutation-free Clariden live receipt for each independent run root.
4. Use `bind_data_stage.py` separately on each template. The reviewed binding must point to the staged canonical root and fresh live receipt. Enable preparation submission only in this final reviewed binding.
5. Compile each bound contract with `apertus-data-stage compile` on Clariden. Inspect the complete batch and verify one task, one attempt, 30 minutes, 8 CPUs, 64 GB, array cap 1, and no GPU/GRES argument.
6. Ask `apertus-data-stage submit-batch` without `--apply` for the exact planned command. This canonical no-apply mode prints the command but does not contact the scheduler.
7. Run that exact command with only `--test-only` inserted after `sbatch`. Save stdout, stderr, return code, command, compiled-manifest hash and live-receipt binding as the scheduler-test evidence.
8. Stop for root review. A passing scheduler test is not an instruction to submit either job.

The tasks remain separate. Dolci has a maximum planning charge of CHF 1.345; OpenMath has a separate maximum of CHF 1.345. The combined ceiling is CHF 2.69 only if both are independently launched.
