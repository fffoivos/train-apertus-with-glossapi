# R-DPO12 — final launch gate

**CLEAR both launches. 0 BLOCKERS, 0 HIGH.** One MEDIUM limitation remains for future task-code changes; it does not block these jobs.

Read-only review completed. **42/42 tests passed. Nothing launched.** Cluster checks used CPU calculations and in-memory staging; prospective fixtures are not new evaluation results.

**Fix verification**

| Item | Result and evidence |
|---|---|
| **R-DPO11 finding 1: task identity** | **PASS for this launch.** Two fresh processes using the installed serializer produced different callable addresses but identical normalized configurations. Separately serialized real-output fixtures compare across **38/38 lanes**. Changing the category or function name is refused. No additional volatile field surfaced. |
| **Effective-generation fixture** | **PASS.** `mint_receipt` matches the settings independently resolved on Clariden: EOS `{2,68}`, BOS 1, tokenizer PAD 3, greedy decoding, one beam, repetition penalty 1, cache enabled. The historic comparison correctly fails for **geometry**, without a generation-config or date mismatch. |
| **R-DPO11 finding 2: record** | **PASS.** All four cited passages are corrected. Regenerating in memory reproduces the supplied HTML exactly. E6 preserves observations while withdrawing training-effect attribution; E2 is scoped to this lm_eval path. Official GreekMMLU and qualified arm-versus-arm observations remain supported. |
| **Frozen resume** | **PASS for the supplied entries.** Executed the actual embedded check: valid receipt accepted; changed config-source path, wrong geometry, weights or date refused. |
| **Official resume** | **PASS.** Requires both full-result validation and successful loading through the evaluator-receipt builder. None of the remaining twelve completed results is present, so this launch takes the fresh-scoring path. |
| **Terminal-state parsing** | **PASS.** Simulated against the actual `release()`: terminal records accepted; `CANCELLED` + RUNNING, `CANCELLED by 123` + RUNNING, SSH failure and live-job responses refused. |
| **Staged execution inputs** | **PASS.** **49 relevant staged payload files match** local sources. Read-only reproduction of the CPU checks passes **19/19 entries** and all four tokenizer canaries. Eighteen entries have parent geometry; only `parent_exportcfg` differs intentionally. |
| **Successful-run comparison path** | **PASS.** All sixteen arms use the same full-lane runner, tokenizer, effective generation settings and repaired geometry. Prospective fixtures using real parent/plain/anchored outputs pass **38/38 lanes for each tested parent–arm pair**. `parent_ckptgen` versus `parent_exportcfg` passes **38/38 under `policy="geometry"`**. |

`parent` and `parent_ckptgen` have equal effective identities. Assess their per-item equality directly; refusal by `compare()` is intentional.

**New finding**

**MEDIUM — callable normalization is not complete executable identity.**  
`rlhf/evals/manifest.py:48`

Removing the address is correct for these fixed tasks and preserves their serialized function names and partial arguments. However, ordinary Python function reprs contain **neither module identity nor code content**. I reproduced two same-named functions from different modules, with different behavior, that normalize identically.

Thus, “keeps the module” overstates what the serializer supplies. This is nonblocking for the unchanged task implementation these launches use. Before supporting comparisons across task-code revisions, bind a task-source/code digest alongside the normalized configuration.

**Decision per job**

| Job | Launch | Basis |
|---|---|---|
| Frozen re-score — 19 models | **YES** | The identity failure is fixed; geometry, generation, tokenizer and comparison-path checks pass. |
| Official GreekMMLU rest — 12 models | **YES** | Receipt, validation and release paths pass. It need not wait for frozen results. |

**Ordered asks**

1. Owner may execute both requested launch commands; no further review gate remains.
2. After completion, require the evaluator receipts and validated outputs before publishing comparisons; check parent/`parent_ckptgen` equality separately.
3. Add task-code identity before future evaluator changes. This is nonblocking follow-up.

VERDICT: CLEAR both launches; remaining callable-code identity limitation is MEDIUM and nonblocking | BLOCKERS: 0 | HIGH: 0 | LAUNCH frozen: yes | LAUNCH official: yes
