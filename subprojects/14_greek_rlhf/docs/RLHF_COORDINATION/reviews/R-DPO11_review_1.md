# R-DPO11 — launch gate, third pass

**HOLD both launches. No BLOCKER remains; two HIGH findings remain.** The official identity repair passes. The 19-model matrix is appropriate, but `compare()` rejects its Global-MMLU comparisons because task identity includes process-specific memory addresses. The published page also retains withdrawn conclusions.

Read-only verification completed: **40/40 tests passed**, all 19 configurations checked on Clariden without inference, four official weight receipts independently rehashed, and staged files compared. **Nothing launched.**

**Fix verification**

| Item | Verification |
|---|---|
| Official identity binding | **PASS.** Same-file/two-model arguments, substituted receipts, and altered label/path/config/weights-ID fields are refused. All four completed receipts match freshly hashed weight shards. |
| Official launch receipt path | **PASS.** The driver uploads the writers, generates receipts against the scored directory on Clariden, fetches them, and validates results before promotion. |
| Legacy native builder | **PASS.** Removed from the public API; `caller-asserted` results cannot enter comparisons. |
| Effective generation | **PASS for these 19 inputs.** EOS `{2,68}`, BOS 1, PAD 3, greedy decoding, one beam, repetition penalty 1, cache enabled. |
| Matrix and geometry | **PASS.** All 19 entries are `full`. Eighteen share the parent’s inverse frequencies, attention scaling and complete rotary tables through position 4095; only `parent_exportcfg` differs intentionally. Four tokenizer canaries pass. |
| Comparison acceptance | **FAIL.** Prospective fixtures accept IFEval/MGSM, but reject all 36 Global-MMLU leaves. Finding 1 below. |
| Published record | **PARTIAL.** Several corrections landed, but contradictory active conclusions remain. Generated standalone HTML exactly matches the generator. |
| Resume and store | **PARTIAL.** Store geometry/weights/runtime/population keys are added. Frozen resume checks weights, mode and date; configuration binding and official resume remain incomplete. |
| Dirty-node record / accounting | **PARTIAL.** Dirty-node failure is recorded honestly. One mixed-state `sacct` response still passes. |
| Staging / retirement | **PASS for execution files.** All 49 staged files with local counterparts match, including the mapped weights writer. Four retirement guards precede executable work and return 64. Six additional remote helpers remain; the two tests are unstaged. |

**Findings, most severe first**

**1. HIGH — Global-MMLU runtime identity contains process-specific function addresses**

[rlhf/evals/manifest.py:48](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/manifest.py:48), [manifest.py:151](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/manifest.py:151)

`_pathless()` removes model/tokenizer paths, but retains serialized callables such as:

```text
functools.partial(<function process_docs at 0xfff4ec604180>, category='Business')
functools.partial(<function process_docs at 0xfff4d41f4180>, category='Business')
```

These appear in both `process_docs` and `fewshot_config.process_docs`. Their addresses differ between scorer processes, so `runtime.task_config` differs despite identical task behavior.

I confirmed the installed serializer produces different addresses in two fresh CPU processes. Then, using existing outputs **only as in-memory fixtures**, I applied the frozen date, recomputed task hashes, and supplied the live-verified generation/geometry identities:

- Parent versus `arm01_ep3`: **2 lanes accepted; 36 rejected**.
- Parent versus `arm05_ep3`: **2 lanes accepted; 36 rejected**.
- Every rejection reports **`runtime differs in: task_config`**.

Removing only those volatile addresses in memory makes **38/38 lanes pass for both arms**, and **38/38 geometry-control comparisons pass**. No repository code or production receipt was changed.

**Required:** stable callable identity that preserves function/code identity and partial arguments, including category. Keep the runtime guard. Add a regression proving separately serialized equivalent tasks compare, while changed task behavior remains refused. Per-run validation currently cannot detect this cross-run failure.

**2. HIGH — the published page still reinstates withdrawn conclusions**

[results/G4F6P1--DPO01/curves_page.py:648](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:648), [curves_page.py:731](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:731)

Both generator and delivered HTML still say:

| Location | Remaining statement |
|---|---|
| Generator `:648`; HTML `:137` | “What is left is a consistent mathematics regression, a multilingual regression…” |
| Generator `:731`; HTML `:220` | The multilingual direction remains negative, “so the overall reading gets worse, not better.” |
| Generator `:476`; HTML `:112` | The generation-configuration confound is “real, but not cleanly measured.” |
| Generator `:758`; HTML `:247` | Recommends redoing the configuration 2×2 to identify its effect. |

The first two again interpret differently loaded parent/arm scores as training damage. The latter two contradict the verified inert generation axis and revised matrix.

The ledger’s [E2 section at line 40](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:40) also needs precise scope: the **nominal generation-config axis is inert in this lm_eval setup**. “The 2×2 had one real axis … the date” overlooks its weights/geometry differences; this verification does not establish serving-environment equivalence.

**Required:** reconcile these active passages with E6 and the 19-model plan. Retain the observed scores, the official GreekMMLU result, and explicitly qualified arm-versus-arm observations.

**3. MEDIUM — resume binding remains incomplete**

[cluster/eval_jobs/dpo01_frozen_rescore.sh:197](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_frozen_rescore.sh:197), [cluster/dpo01_official_gmmlu_rest.sh:16](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/dpo01_official_gmmlu_rest.sh:16)

Frozen resume binds only the mode prefix: changing `verbatim:<source>` can retain the same resume identity. It does not compare the requested configuration’s effective geometry/generation with the saved receipt.

Official resume still checks result/configuration metadata without requiring or validating its weights receipt.

**Nonblocking for these launches:** no frozen receipts or remaining-twelve official results were present to trigger these paths.

**4. MEDIUM — `CANCELLEDby*` still accepts mixed accounting states**

[cluster/greekmmlu_official.sh:29](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:29)

Mocking the actual `release()` function:

- Empty successful `squeue`: accepted.
- Live job, SSH failure, failed accounting query: refused.
- `CANCELLED` plus `RUNNING`: refused.
- **`CANCELLED by 123` plus `RUNNING`: accepted.**

The wildcard consumes the trailing active state. Parse accounting records individually and require an unambiguous terminal allocation record. This remains **MEDIUM**, not an additional launch gate.

**Decision per job**

| Job | Decision | Precise condition |
|---|---|---|
| Frozen re-score, 19 models | **NO** | Fix finding 1, demonstrate all 38 lanes compare across separate serializations, restage the changed code, and correct finding 2. |
| Official GreekMMLU rest, 12 models | **NO** | Correct finding 2. Its receipt/identity execution path is cleared; it need not wait for the frozen comparison fix or frozen results. |

The **19-model design is sufficient for the stated scope**: correctly loaded, date-frozen parent-versus-arm measurements, plus E6 measured **on parent weights**. It cannot remove training-date differences or establish that the parent’s artefact magnitude transfers to trained arms.

`parent_ckptgen` is a justified equivalence check. Because its effective identity matches `parent`, `compare()` deliberately refuses both weights and generation-policy comparisons; assess matching manifests and per-item outcomes directly.

**Ordered asks**

1. Stabilize callable serialization and add the Global-MMLU comparison regression.
2. Correct the remaining page/ledger statements and regenerate the published HTML.
3. Restage the changed runtime files and verify hashes. No GPU scoring is needed to close these findings.
4. Complete resume binding and terminal-state parsing as nonblocking hardening.

VERDICT: HOLD both; Global-MMLU comparison identity and published conclusions remain incorrect | BLOCKERS: 0 | HIGH: 2 | LAUNCH frozen: no | LAUNCH official: no
