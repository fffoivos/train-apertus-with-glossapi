# R-DPO10 — launch-gate review

**Ran:** 38 tests (**38 passed, zero skipped**); public-builder defeat attempts; six official-result mutations; mocked shutdown cases; parsing of 38 real lm-eval lanes; CPU checks of all 35 configuration cases in the scoring and training environments; official-environment geometry checks; tokenizer canaries and hashes; staged-file comparisons; generator/HTML consistency checks.

No allocation, inference or scoring job launched. Repository and cluster artifacts remained unchanged. I checked configuration staging in memory rather than rerunning the file-writing `DRYRUN`.

**HOLD both jobs.** The RoPE repair works. The remaining blockers concern result identity, a generation-config axis that does not change effective generation settings, and contradictory active conclusions.

## Fix verification

| Item | Result |
|---|---|
| **B1: faithful RoPE repair** | **PASS for these inputs.** Preserve theta **500000**, `rope_type=llama3`, factor **8**, low/high factors **1/4**, and **`original_max_position_embeddings=8192`**. The model context remains **4096**; these are distinct settings. |
| **Cross-version geometry** | Repaired 4.57 configurations exactly match training 5.16.1: inverse-frequency bytes, `attention_scaling=1`, and complete sine/cosine tables for positions 0–4095. Leaving `rope_parameters` present does not influence this 4.57 implementation. |
| **35-entry gate** | **34 match the parent; only `parent_exportcfg` differs**, as intended. Parent digest begins `4ae228093081`; export control begins `082aa1f8a9e9`. |
| **Is `inv_freq` sufficient?** | **For these verified llama3 configurations, yes with the additional checks above. Generally, no:** attention scaling and sequence-dependent rotary behavior also matter. The helper currently records neither completely. |
| **B2: original lm-eval defeats** | False `gen_config=` arguments are rejected; widening `POLICIES` raises `TypeError`; substituting another run’s complete receipt fails output-hash validation. **Other public builders remain vulnerable**, below. |
| **H1: active record** | **FAIL.** The generated HTML matches its generator, including contradictory current claims. |
| **H2: official validator** | **PASS for all four previous mutations:** false config hash, NaN accuracy, rewritten gold answers and extra row protocol. Boolean and out-of-range predictions also fail. Genuine input passes. |
| **Pinned gold** | Independently regenerated all **16,632** TSV records from the pinned cluster projection; digest exactly matches `9cd8b41b…ea24`. |
| **H3: release verification** | SSH failure and live jobs return failure. Successful empty `squeue` returns success. Aged-out job plus terminal `sacct` state succeeds; active state or failed accounting query fails. Remaining audit defects are MEDIUM below. |
| **Tokenizer and lane validation** | Four canaries pass; all **17 distinct weights directories** share the tokenizer hash. Parsed **541 IFEval**, **250 MGSM**, and **36 Global-MMLU leaves totaling 2,400 items**. |

## Findings, most severe first

### 1. BLOCKER — B2 remains open through the official public builder

[rlhf/evals/manifest.py:203](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/manifest.py:203)

`from_official_greekmmlu(path, label, weights, …)` still takes caller-supplied identity. I supplied the **same genuine `parent.json`** twice, first with the parent’s genuine weights receipt, then with `arm05_ep3`’s genuine receipt.

`compare()` accepted this as a weights comparison:

- **16,632 items**
- **0 gained, 0 lost**
- **0.000000 pp**
- `varying=["weights_id"]`

Weights identity was **not** reported as unverified. This required no source edit, private capability or output modification. `from_native_mcq` retains the same unchecked argument surface at `manifest.py:168`.

The ledger’s assertion that “builders take NO identity arguments” is therefore false. Only the lm-eval builder received that repair.

**`mint_receipt` assessment:** acceptable as an isolated unit-test fixture, but not evidence of historical evaluator provenance. Its padded digest prefixes are synthetic. I also changed only a fixture receipt’s geometry and obtained an accepted parent/arm comparison with `unverified=[]`. That is receipt-level falsification, not evidence that the production writer generates false geometry; it demonstrates that receipt authenticity remains a trust assumption. Synthetic backfills must not silently become production evidence.

### 2. HIGH — the proposed generation-config treatment is ineffective, and receipts describe the wrong settings

[cluster/eval_jobs/run_receipt.py:39](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/run_receipt.py:39); `cluster/eval_jobs/dpo01_frozen_rescore.sh:153`

The receipt reads four fields from **`config.json`**, while scoring also loads **`generation_config.json`** and applies lm-eval overrides.

In the installed scoring environment:

- lm-eval’s `HFLM._model_generate` explicitly passes **`use_cache=True`**.
- Parent generation config uses EOS **`[2, 68]`**.
- Checkpoint generation config uses EOS **`[68, 2, 68]`**.
- Those lists produce identical EOS stopping decisions; I checked every vocabulary ID.

Resolving all **35 entries** through the installed generation-config preparation code produced equivalent settings after deduplicating EOS IDs: cache enabled, EOS `{2,68}`, BOS 1, PAD 3, greedy decoding, one beam and repetition penalty 1.

Consequently, the extra sixteen `parent|gen` entries **do not establish a distinct generation/deployment treatment as written**. Their receipts nevertheless claim a cache/EOS difference derived from inactive model-config fields.

The useful geometry contrast is **`parent_exportcfg` versus `parent_ckptgen`**. The sixteen repaired `own|full` arms are also useful. The remaining generation-config duplication needs removal, explicit justification as replication, or an actually distinct, explicitly specified treatment. Record effective generation settings after all overrides.

### 3. HIGH — H1 remains: the current page reinstates withdrawn conclusions

[results/G4F6P1--DPO01/curves_page.py:650](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:650)

Examples still present in both source and delivered HTML:

| Source line | Current claim |
|---|---|
| `curves_page.py:650` / HTML `:139` | Calls the date-matched scorecard **“the only controlled one”**, despite differing geometry. |
| `curves_page.py:653` / HTML `:142` | **“A serious MGSM regression is real and date-matched.”** The paragraph still presents the result as established damage. |
| `curves_page.py:689` / HTML `:178` | **“A real but much smaller improvement survives”** on custom GreekMMLU. |
| `curves_page.py:698` / HTML `:187` | Says trained checkpoints improve custom GreekMMLU, without the geometry qualification in that conclusion. |
| `curves_page.py:720` and `:732` | Reuses mathematics/multilingual regressions to support an overall negative training interpretation. |

The E6 opening and corrected closing paragraph do not resolve these contradictory active statements. Keep the observed scores; consistently withdraw their interpretation as weights-only effects.

### 4. MEDIUM — E6’s mechanism, coverage and speculation need correction

`docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:19`, `:28`; `curves_page.py:619`, `:620`, `:724`

**The unrepaired arms retain llama3 scaling.** Transformers 4.57 defaults to theta **12,000,000**, **with** llama3 factor 8, original context 8192 and low/high factors 1/4. “No llama3 scaling” is incorrect.

Other qualifications:

- The parent-under-checkpoint-generation-config cell retains correct geometry. E6 does not make **both** off-diagonal cells mis-loaded.
- Coverage counts are conflated. The page’s source artifact contains **54 IFEval/MGSM entries**, **51 Global-MMLU entries**, and **66 custom GreekMMLU entries**, including baselines—not 66 lm-eval arm runs.
- Training/displacement and official GreekMMLU are unaffected by this specific mismatch. The official environment resolves all seventeen distinct inputs consistently.
- The served implementation consumes the correctly resolved `rope_parameters`; its other date/config limitations remain.
- “Nearly the same size in every recipe,” “two lanes … show almost no damage,” and “leading candidate” do not measure the artefact’s contribution. Different benchmarks/protocols cannot establish that it explains most of the deficit.
- `parent_exportcfg` measures the artefact **on parent weights**. It does not establish that its magnitude transfers unchanged to trained arms.

### 5. MEDIUM — resume and storage identity remain incomplete

`cluster/eval_jobs/dpo01_frozen_rescore.sh:196`; `cluster/dpo01_official_gmmlu_rest.sh:16`; `rlhf/evals/store.py:19`

Revalidation improves on marker existence, but frozen resume does not compare the saved receipt’s weights/configuration/geometry against the **currently requested list entry**. Official resume binds configuration hash, not weights content.

`Store._key()` also omits geometry and weights identity. I stored two sealed results differing in geometry: they received the **same key**, leaving **one record**.

No frozen receipts or remaining-twelve official results existed to trigger these resume defects during this review.

### 6. MEDIUM — shutdown failure is still misrecorded on the dirty-node path

`cluster/greekmmlu_official.sh:29`, `:39`

With `release()` returning failure, the dirty-node branch still calls the ledger with **“closed: dirty node.”** It exits 2, so it does stop the outer launcher; this is not the previous false-success return. The closure record is nevertheless false.

The `sacct` fallback also accepts a mixed response containing `CANCELLED` and `RUNNING`. Require an unambiguous terminal allocation record rather than a terminal-state substring.

### 7. MEDIUM — staged directories are not an exact repository mirror

The execution-critical frozen files **match**, with SHA-256 prefixes:

| File | Prefix |
|---|---|
| Frozen launcher | `5e8488d02c18` |
| Model list | `bf5b90493103` |
| `run_receipt.py` | `a482c180d53a` |
| Staged `weights_receipt.py`, mapped to repository `rlhf/evals/weights.py` | `ae6ed026dd51` |
| Eight `rlhf` runtime files | All identical |

However, staged `build_screen_manifest.py`, `consolidate.py` and four retired launchers differ. **None of those four staged launchers contains the retirement guard.**

The staged official scorer also differs; `cluster/greekmmlu_official.sh:35` uploads the local scorer before launch. The validator/gold file run locally, and the two test files are not staged. These differences do not independently block the two named commands, but “the staged trees match” is false.

Additional LOW record leftovers: `curves_page.py:739` and `:742` still use **397** rather than **343 training pairs** for BAL selection/control descriptions. Section 9 still implies evaluation-date freezing repairs seed dispersion completely; it cannot remove training-date variation. The direct date-matched BAL multilingual contrasts, **−2.51/−2.85 pp**, remain understated.

## Explicit launch decisions

| Job | Decision | Conditions for a clear review |
|---|---|---|
| **Frozen re-score, 35 entries** | **NO** | Resolve finding 2’s effective-generation identity and matrix design; correct finding 3’s active record. The RoPE repair itself is cleared for the inspected inputs. |
| **Official GreekMMLU rest, 12 models** | **NO** | Close finding 1’s official result-to-weights binding and correct finding 3’s active record. This job does **not** need to wait for frozen-score results or the generation-axis redesign. |

## Ordered asks

1. Bind official/native result identity to evaluator-produced, output-bound evidence; repeat the demonstrated same-file/different-weights defeat.
2. Record effective generation settings and resolve the redundant generation-config cells before spending on the frozen matrix.
3. Reconcile every active conclusion with E6, including its actual scaling behavior and unmeasured effect size.
4. Address the logged resume, storage, shutdown-record and staging defects; they remain MEDIUM.
5. Restage changed execution files and rerun the focused checks. No GPU scoring is needed to close these review findings.

VERDICT: HOLD both jobs; RoPE repair passes, identity and interpretation gates remain open | BLOCKERS: 1 | HIGH: 2 | LAUNCH frozen: no | LAUNCH official: no
