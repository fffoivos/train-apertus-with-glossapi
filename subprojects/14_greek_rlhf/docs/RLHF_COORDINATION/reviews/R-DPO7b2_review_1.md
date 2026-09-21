# R-DPO7b cycle 2 — protocol-fix verification and fresh audit

**Verdict:** **HOLD publication.** The four completed full-run predictions are numerically salvageable, and the checkpoint/config verification claims are true, but the finalizer is still not identity-bound; five HIGH protocol, execution, and integration defects remain.

## Fix verification

| Finding | Status | Verification |
|---|---|---|
| 7b BLOCKER — raw 16,632 vs clean 16,159 | **Correctly fixed** | The finalizer computed both through one path. Independent recomputation matched every integer and confirmed that clean accuracy uses exactly the 16,159 manifest IDs. |
| 7a2 BLOCKER — descriptor manifest | **Correctly fixed for the real manifest** | Schema/status, 247,855-byte ID file, SHA-256 `d97360da…208f`, uniqueness, and 16,159 count all passed. The primary path existed, so fallback was not exercised. |
| 7a2 HIGH — exact population/model set and fail-closed behavior | **Wrongly fixed** | [finalize_greekmmlu_full.py:55](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:55) checks only row count and clean-ID inclusion. It never reads `run_metadata.json`, verifies the exact raw ID population, or requires a frozen eight-label list; my four-label invocation succeeded with “4 models, all validated.” |
| 7b HIGH — shared staging/checkpoint truncation | **Wrongly fixed, current artifacts safe** | [dpo01_armcfg_cell.sh:23](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_armcfg_cell.sh:23) is job-unique, but [dpo01_gencfg_control.sh:16](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:16) still uses the shared `R4_full_ep1_ckptcfg` stage without the claimed symlink refusal. The running GreekMMLU snapshot also predates the unique-stage change. Nevertheless, only one full job ran and all 68 checkpoint configs remain intact. |
| 7b HIGH — tokenizer replacement | **Wrongly fixed, current scores safe** | [dpo01_greekmmlu_full.sh:89](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:89) checks only when both files exist. All 68 checkpoints lack `special_tokens_map.json`, so that check is bypassed; `tokenizer_config.json` differs from the parent in 10 fields and is copied wholesale. Actual `tokenizer.json` is byte-identical across the parent and all 68 checkpoints, so the audited scoring inputs are safe. |
| 7b HIGH — worker failures exit zero | **Wrongly fixed** | Even the repaired local script records `rc` but returns success whenever a headline exists, at [dpo01_greekmmlu_full.sh:124](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:124). Three completed arm workers already failed their legacy finalizer but were logged as `done`. |
| 7b MEDIUM — headline existence accepts invalid results | **Not fixed** | The skip and success tests still accept any matching headline at [dpo01_greekmmlu_full.sh:74](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:74). |
| 7b MEDIUM — asymmetric overlay | **Correctly fixed** | Both directions now assign-or-delete. Retained stages contain the intended four fields, and raw lm-eval files reproduce the published 2×2 values. |
| 7a2 MEDIUM — shared checkpoint-config baseline | **Correctly fixed/verified** | All **68/68** checkpoint bundles are identical: `config.json` 899 bytes, 26 keys, SHA-256 `ad6631b6…45984`; `generation_config.json` SHA-256 `3393b7e9…56ab`; fields are EOS 68, pad 3, BOS 1, `use_cache=false`. No checkpoint config was damaged. |

## New and still-open findings

### [BLOCKER] The finalizer still cannot certify dataset or model identity

[finalize_greekmmlu_full.py:55](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:55), [finalize_greekmmlu_full.py:81](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:81), [run_native_greek_mcq_eval.py:465](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py:465)

The guard still accepts “16,159 clean IDs plus any 473 other unique IDs.” It also does not validate prediction-row `model`/`benchmark`, metadata schema, label, source, revision, config, split, fingerprint, scoring flags, or the resolved checkpoint. Arm metadata points only to an ephemeral `.stage_*` directory that the job deletes.

The real completed files are correct only because I checked them independently:

| Model | Raw | Clean |
|---|---:|---:|
| parent | 9,020/16,632 = **54.2328%** | 8,776/16,159 = **54.3103%** |
| arm01_ep3 | 9,097/16,632 = **54.6958%** | 8,854/16,159 = **54.7930%** |
| arm05_ep3 | 9,084/16,632 = **54.6176%** | 8,842/16,159 = **54.7187%** |
| armIPO42_ep3 | 9,110/16,632 = **54.7739%** | 8,869/16,159 = **54.8858%** |

Their raw IDs are exactly ordered `greekmmlu:0` through `greekmmlu:16631`; all four share ID-set digest `c789d0a1…918e9`, dataset fingerprint `273cd537879dc5ec`, and the pinned `dascim/GreekMMLU@6a03aa…4649` `All/test` binding.

### [HIGH] The live job masks real failures and will report false success

Job-3443296 snapshot lines 93–116; `.../greekmmlu_full/{arm01_ep3,arm05_ep3,armIPO42_ep3}/run.log:53-59`

The running script is SHA-256 `4f7cf250…047e`; the repaired Mac copy is `0cefd354…eac`. The live cluster file is also the old hash.

All three completed arms produced valid 16,632-row predictions, then failed the legacy finalizer with `HF evaluation geometry drift`. Nevertheless, the batch log says each is `done`. Barring an unrelated shell error, the job will print `GREEKMMLU_DONE` and exit zero. Its Slurm status is therefore not a completion receipt.

At the audit cutoff, 12:12 UTC, the second wave was at 10,800/16,632 for all four remaining models.

### [HIGH] The shared-stage fix is incomplete

[dpo01_gencfg_control.sh:16](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:16), [dpo01_gencfg_control.sh:20](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_gencfg_control.sh:20)

The reverse-control stage remains shared and can still recreate a config symlink during another invocation’s remove/copy/write sequence. The present 2×2 results are safe: retained configs are regular files, source configs are intact, and the raw results reproduce:

- Parent checkpoint-config: IFEval `0.6025878`, MGSM `0.424`.
- arm01 parent-config: IFEval `0.5933457`, MGSM `0.392`.
- arm05 parent-config: IFEval `0.6025878`, MGSM `0.384`.

### [HIGH] Tokenizer checking remains fail-open

[dpo01_greekmmlu_full.sh:89](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_greekmmlu_full.sh:89), [run_native_greek_mcq_eval.py:250](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py:250)

Current evidence is favorable:

- All checkpoint and parent `tokenizer.json` files are identical: 18,994,464 bytes, SHA-256 `acf4d5c6…81092`.
- All checkpoints use the same pad token and scoring uses `add_special_tokens=False`.
- Across 66,528 completed rows, recomputing argmax and correctness from stored choice scores found **0 mismatches**, **0 non-finite rows**, and **0 non-positive-token candidates**.

But missing tokenizer files currently pass, and non-class `tokenizer_config` differences are not checked. This is not the requested fail-closed implementation.

### [HIGH] The executed 250 slice is neither the frozen sample nor the declared official protocol

[DPO_EXPERIMENT_COMPARISON_20260918.md:48](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO_EXPERIMENT_COMPARISON_20260918.md:48), [DPO_EXPERIMENT_COMPARISON_20260918.md:77](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO_EXPERIMENT_COMPARISON_20260918.md:77), [build_screen_manifest.py:92](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/build_screen_manifest.py:92), [greekmmlu_official.py:21](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/greekmmlu_official.py:21)

The real frozen screen manifest contains **100 clean, subject-stratified IDs** and declares `official_label`. The executed 250 has:

- **0/100 overlap** with those frozen IDs.
- **243 clean + 7 contaminated** IDs.
- Exact equality to `random.Random(42)` sampling from the ordered raw 16,632 frame.

The runner uses the historical generic prompt and ranks full choice text by average token log-probability. That is `custom_full_text`, not official GreekMMLU, despite metadata calling it `official_zero_shot_accuracy`. The same parent scores **54.23%** here versus the retained **69.4% official-label** result—a 15.17-point protocol difference.

The scoring mechanics are internally correct for the custom protocol, but publication must label this as an adaptive custom-full-text diagnostic. Confirmation should be reported on the items outside the observed 250: raw `n=16,382`, clean `n=15,916`.

### [HIGH] There is no safe join from full results into the 250 artifact

[consolidate.py:55](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/consolidate.py:55), [curves_page.py:20](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:20), [curves_page.py:570](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:570)

Nothing reads `greekmmlu_full`. The artifact has one scalar `greekmmlu` field and groups 15 runs. Replacing that scalar only for the seven full-scored arms would mix 16,632/16,159-item scores with 250-item scores inside the same means and standard deviations.

The full results need separate typed fields and tables: `250_raw`, `250_clean`, `full_raw`, `full_clean`, and `full_minus_250`, each with explicit model coverage.

### [MEDIUM] Manifest fallback is safe for this manifest, but the contract is still optional

[finalize_greekmmlu_full.py:35](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/finalize_greekmmlu_full.py:35)

A wrong basename-neighbor file cannot pass the real manifest because both its SHA-256 and byte count are checked. However, the code only checks those fields *if present*. A same-schema descriptor omitting them can use the fallback without content authentication. It also trusts, rather than asserts, the expected revision and `16,632/16,159` counts.

## Ordered asks

1. Make the finalizer validate a frozen eight-label set, exact raw-ID digest/population, every `run_metadata.json` binding and prediction-row label/benchmark; emit full manifest, ID-file, metadata, prediction, runner, registry, and resolved-checkpoint hashes.
2. After all eight prediction files exist, run that finalizer with the canonical eight labels. Ignore job 3443296’s eventual success status.
3. Make `run_one` require both `rc == 0` and validated outputs; replace headline-only skip logic.
4. Make every stage job-unique, delete only its own stage, and fail on missing tokenizer artifacts; compare normalized tokenizer configuration rather than copying it unchecked.
5. Label the measurement `custom_full_text`; either amend the adaptive protocol record or rerun official-label scoring before making an official GreekMMLU claim.
6. Add a separate full-results integration path. Report the 250 selection set and the `16,382` raw / `15,916` clean confirmation-only sets separately; never mix populations in group means.

VERDICT: HOLD: completed predictions are salvageable, but identity certification, execution status, frozen-protocol alignment, and result integration are not publication-safe | BLOCKERS: 1 | HIGH: 5

