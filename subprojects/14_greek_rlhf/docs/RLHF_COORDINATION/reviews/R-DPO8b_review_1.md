# R-DPO8 cycle-2 review — fix verification and pre-launch gate

**HOLD — 24/24 tests pass, but the public guard remains bypassable and both launch paths have unresolved HIGH defects. Neither job may launch.**

## Fix verification

| # | Cycle-1 finding | Status | Verification |
|---:|---|---|---|
| 1 | Caller-bypassable comparison policy | **Wrongly fixed** | Arbitrary `varying`/`allow_unknown` is gone, but mutable/hand-built manifests, `check()`, `Store`, and unbound item maps still permit uncontrolled comparisons. |
| 2 | Per-request generation/runtime identity unbound | **Correctly fixed** | Whole request, nested generation options, resolved dtype, seeds, task hash/config and harness versions are compared. |
| 3 | Weights identity caller-supplied | **Wrongly fixed** | `receipt()` derives sound IDs, but `load_receipt()` trusts any `w:` ID plus non-empty `files`; the ID is not recomputed. |
| 4 | Item/gold identity unbound | **Correctly fixed at builder layer** | `doc_id`, recomputed document hash and target hash are bound. The separate manifest-to-items binding remains part of finding 1. |
| 5 | Re-run cure insufficient | **Wrongly fixed** | The ledger text names the movement checkpoints, but the launch list omits four of them and contradicts the reuse premise. |
| 6 | α interval mislabelled | **Correctly fixed** | Paired bootstrap reproduces `[−0.7394,+1.8484]`; the numerical test and `alpha_interval.json` agree. |
| 7 | Stale published claims | **Correctly fixed** | All three named documents open with correction banners. |
| 8 | Finalizer trusted submitted frames | **Correctly fixed** | Raw frame, 250-slice, dataset revision/config/split/counts and metadata structure are pinned; `--expect` is mandatory. |
| 9 | Legacy tokenizer staging/cleanup unsafe | **Correctly fixed by retirement** | All four legacy scripts immediately return 64. Retirement is adequate because neither re-run uses them. |
| 10 | Legacy launchers could report success after scorer failure | **Correctly fixed by retirement** | The replacement frozen launcher captures `rc`, validates each model and aggregates background failures. |
| 11 | Official driver stale/live-process hazards | **Wrongly fixed** | Run directories, receipts, bounds and timeout failure work, but output validation is count-only and allocation shutdown is not verified. |
| 12 | Displacement row’s “no date” rationale | **Correctly fixed** | The ledger now states that dates exist but do not confound the within-run contrast. |
| 13 | No paired-seed bootstrap | **Correctly fixed** | `paired_seed_bootstrap()` exists and its published interval is numerically pinned. |
| 14 | Hardcoded `chat_template_applied=false` | **Correctly fixed** | The evaluator derives it from the requested protocols. |
| 15 | Statistical input validation | **Correctly fixed** | The exact empty-pair, bootstrap-parameter and Holm-input defects from cycle 1 now reject cleanly. |

The complete baseline suite passed: **24/24 tests**.

## Defeat attempts and outcomes

| Attempt | Outcome |
|---|---|
| Change nested `max_gen_toks` | **Refused** |
| Change result-level generation kwargs | **Refused** |
| Change resolved dtype, task hash, few-shot seed/config or task metadata dtype | **Refused** |
| Change rendered prompts/date | **Refused** |
| Change few-shot provenance recorded in task config without changing requests | **Refused** |
| Change template provenance while keeping identical rendered requests | **Accepted; appropriate**—provenance differs, model input does not |
| Change only tokenizer/pretrained path | **Accepted; appropriate only with genuine content receipts** |
| Both identity values unknown in honest lm-eval manifests | **Refused** |
| Supply old `varying=`/`allow_unknown=` arguments | **Rejected** |
| Edit a real manifest’s controlled fields before `compare()` | **Accepted: +0.1848 pp** |
| Pass fabricated item maps with genuine manifests | **Accepted: fabricated +100 pp** |
| Hand-construct `RunManifest` and self-declare custom-protocol unknowns | **Accepted: fabricated +100 pp** |
| Use the edited manifest through exported `check()` | **Accepted** |
| Persist and aggregate hand-built manifests through `Store.put/group` | **Accepted** |
| Relabel one real receipt as another `w:` ID | **Accepted as a different model** |
| Give one checkpoint two labels with genuine receipts | **Refused correctly** |
| Reorder identical documents | **Accepted correctly** |
| Reassign targets among IDs | **Refused correctly** |

The public operations above are in scope: `RunManifest` is exported and mutable, `compare()` accepts mappings plus independently supplied item maps, and `check()` and `Store` are exported guard surfaces. Editing the library source, monkeypatching internals, bypassing the package entirely through `stats.paired()`, or cryptographic collision attacks are out of scope.

`_pathless()` drops exactly the right two fields for the observed lm-eval task configs: `metadata.pretrained` and `metadata.tokenizer` are locations, while dtype and task semantics stay bound. The problem is not that those paths are omitted; it is that the replacement content identities are not themselves authenticated.

## Pre-launch findings, most severe first

1. **BLOCKER — The guard still accepts uncontrolled public comparisons.** [`manifest.py:31`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/manifest.py:31>), [`compare.py:51`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/compare.py:51>), [`store.py:23`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/store.py:23>). A closed `POLICIES` table is insufficient when manifests and item maps are unauthenticated, mutable and independently swappable.

2. **HIGH — Weights identity remains caller-supplied at the consumer boundary.** [`weights.py:39`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/weights.py:39>). The honest receipts are correct: parent and `R4_full_ep1_ckptcfg` share `w:0399e4272051aa3a1569008e`; sampled arms have distinct IDs. But changing a receipt dictionary’s `weights_id` is accepted without checking its files.

3. **HIGH — The 22-entry frozen list does not implement the ledger.** [`dpo01_frozen_models.txt:3`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_frozen_models.txt:3>), [`DPO01_POISON_LEDGER_20260919.md:75`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:75>).

   - Missing required R1 entries: `arm01_ep1`, `arm01_ep2`, `arm05_ep1`, `arm05_ep2`. All four checkpoints exist.
   - Redundant under the stated 19-September reuse premise: `parent_ckptcfg|own`, `arm01_ep3|parent`, and `arm05_ep3|parent`; those exact cells were already rendered on the 19th.
   - R2 says “every epoch-3 arm,” but omits `arm00`, `arm02`, `arm03`, `arm04`, `arm06` and `arm08`. Either add them or narrow the ledger’s claim to the replicated scorecard/repeat set.

4. **HIGH — R3 staging rejects all twelve real checkpoints before scoring.** [`dpo01_official_gmmlu_rest.sh:16`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/dpo01_official_gmmlu_rest.sh:16>). Line 22 requires a symlinked `model.safetensors.index.json`, but these checkpoints contain a single `model.safetensors` and no index. Every stage therefore returns `BADLINK`.

5. **HIGH — The official driver’s “full-frame validation” is only a count check.** [`greekmmlu_official.sh:32`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:32>). It accepts any 16,632 rows with the requested label; it does not verify unique/exact IDs, strict booleans, `official_label` only, pinned parquet SHA, `chat_template_applied=false`, dtype, model/config identity or accuracy recomputation.

6. **HIGH — Workbench shutdown is attempted but not established.** [`greekmmlu_official.sh:30`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:30>). At MAXWAIT, missing receipts correctly cause non-zero exit and `close` calls `scancel`. However the close pipeline’s status is ignored, no terminal scheduler state is awaited, and the cluster helper itself uses `scancel … || true`. A failed close can leave spend running until WALL.

7. **MEDIUM — Frozen `.validated` is weaker than its name.** [`dpo01_frozen_rescore.sh:146`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_frozen_rescore.sh:146>). It checks file/line counts and date substrings but does not parse every sample, emit manifests or verify request digests before marking the model reusable.

8. **MEDIUM — The ledger still retains the corrected factual error.** [`DPO01_POISON_LEDGER_20260919.md:116`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:116>) still says the job was cancelled with four completed models. The job completed all eight; line 61 and `greekmmlu_full_partial.json` are correct.

9. **LOW — The official driver documents a default WALL but has none.** [`greekmmlu_official.sh:4`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:4>), [`greekmmlu_official.sh:13`](</Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:13>). The actual R3 wrapper supplies `WALL=02:00:00`, so this does not affect this launch.

## Cleared pre-launch points

- The real tokenizer JSON contains exactly one byte-for-byte match for `strftime_now('%Y-%m-%d')`. The replacement and canary quoting are sound. The single-quoted heredoc is interpreted by the inner `bash -c`, and lm-eval loads `tokenizer=$TOK` and invokes that tokenizer’s `apply_chat_template()`.
- A dynamic template rendered on 2026-09-19 and the literal frozen template produce identical prompt bytes. Old and intended environments are both lm-eval `0.4.11` and Transformers `4.57.0`. The changed tokenizer path should not itself be an identity difference.
- `config=parent` stages arm weights as symlinks while creating regular config files before writing; no model/config symlink is written through.
- Frozen cleanup is scoped to `.frozen_${JOB}_*`, and background failures are counted.
- Current 8-hour walltime is ample: roughly 180 minutes for the present list at four-way concurrency; adding the four missing full runs still remains comfortably below it.
- The scorer-exit quoting is correct: local `\\\$?` becomes an escaped `$?` for the remote shell, which passes a literal `$?` to the inner `bash`; that inner shell expands it after `srun`. A failing scorer writes a non-zero receipt.
- The four-model official geometry has prior live evidence: four official models finished in one 50:27 workbench, so `WALL=120`, `MAXWAIT=100` is adequate when cleanup works.
- R3’s twelve model labels are otherwise correct: four standard-seed replicas per main arm, three BAL runs and IPO43; the already-completed parent, arm01, arm05 and IPO42 are properly excluded.
- The finalizer’s eight-model output is genuine. Independent recomputation matched:

| Model | Raw correct / 16,632 | Clean correct / 16,159 | Slice accuracy |
|---|---:|---:|---:|
| parent | 9,020 | 8,776 | 0.576 |
| arm01_ep3 | 9,097 | 8,854 | 0.596 |
| arm05_ep3 | 9,084 | 8,842 | 0.596 |
| armIPO42_ep3 | 9,110 | 8,869 | 0.596 |

- All four retired scripts were executed only to their first guard and returned exactly `64`.
- The two frozen job files are not yet present under the Clariden scratch launch tree. When the defects are fixed, stage the exact reviewed SHA-256 files before submission.
- Canonical issue [#157](https://github.com/fffoivos/apertus-cscs-efficiency/issues/157) already covers concurrent evaluator-step qualification. No issue or repository was modified during this read-only review.

## Ordered asks

1. **Do not launch either job.**
2. Replace the mutable manifest/items interface with one validated result object or receipt: make builder provenance non-forgeable, bind the item map to it, revalidate on `Store.put/load`, and prevent exported `check()` from accepting hand-built claims.
3. Make `load_receipt()` recompute/verify the canonical files and ID rather than trusting fields in a dictionary or JSON file.
4. Correct the frozen model list: add the four missing R1 movement checkpoints, remove already-19th cells if reuse remains the policy, and either implement or narrow R2’s “every epoch-3 arm” wording. Update `EXPECT`.
5. Fix R3 staging against the real single-shard layout, preferably by verifying a content receipt or resolved `model.safetensors` target instead of assuming an index file.
6. Make official-result validation exact and receipt-bound; make workbench closure checked and wait for a terminal scheduler state.
7. Parse and manifest frozen outputs before writing `.validated`; correct the stale four-model ledger row; stage exact reviewed artifacts on Clariden; then repeat this pre-launch review.

VERDICT: HOLD — neither re-run job may launch until the public guard and five HIGH launch defects are fixed | BLOCKERS: 1 | HIGH: 5

