# R-DPO8 review — what I ran

- Ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v rlhf.tests.test_evals`: **11/11 passed** once given a writable temporary directory. The initial sandbox run had one environment-only `TemporaryDirectory` error.
- Built adversarial manifests and real-shaped lm-eval samples to exercise `compare()`, `prompt_digest`, unknown values, generation settings, document identity, and `weights_id`.
- Used read-only `ssh clariden` inspection of samples, tokenizer configuration, trainer-state timestamps, staged symlinks, served outputs, and installed TRL source. **No cluster job was launched.**
- Independently recomputed official GreekMMLU accuracies, deltas, exact McNemar tests, Holm correction, and paired/unpaired bootstrap intervals.
- Ran `bash -n` and isolated failure-path traces for the four evaluation launchers and workbench driver.

**Verdict:** HOLD. The official GreekMMLU result is clean and most E1 taint calls are right, but the ledger’s proposed cure is insufficient, the new comparison guard is bypassable, and every newly reviewed launcher still has a fail-open path.

## Part A — poison ledger

| Ledger row or claim | Status | Deciding evidence |
|---|---|---|
| E1 root cause: the parent template injects the current date | **Confirmed** | The parent `tokenizer_config.json` contains `strftime_now('%Y-%m-%d')` in the default system message. Actual IFEval samples contain the resulting `Current date:` line. |
| 18/19 September lm-eval split | **Confirmed** | Direct enumeration found **28 runs dated 2026-09-18 and 26 dated 2026-09-19**, matching `run_dates.json`. A Global-MMLU-Lite likelihood sample also contains `Current date: 2026-09-18`; likelihood prompts are not exempt. |
| Training prompts also receive the date | **Confirmed, ledger wording incomplete** | `cluster/dpo_train.py:67-70` applies the tokenizer template during length processing, while installed TRL’s `dpo_trainer.py:322` and `data_utils.py:228,247` apply it when preparing conversational DPO examples. Trainer-state mtimes confirm that standard seeds 42–43 trained on the 18th and 44–46 on the 19th. But `BALs43` trained on the 19th, so the ledger’s broad “seeds 42–43 versus 44–46” description is not valid across every family. |
| §3–4 representation displacement is CLEAN | **Status confirmed; rationale incomplete** | All five dose arms were trained on the 18th, and each policy/reference pair is evaluated on the same rendered prompt. Thus E1 does not confound the within-run displacement or same-date dose ordering. But `DPO01_POISON_LEDGER_20260919.md:43` says there is “no date”; that is false. Training and held-out prompts carry the date, so it can affect the absolute learned displacement even though it does not explain the reported contrast. |
| “α contrast is clean as a seed-paired contrast” | **Wrong as published** | The seeds really are paired one-to-one by both seed and date: 42/43 on the 18th and 44/45/46 on the 19th in both arms. The +0.70 pp point estimate is therefore E1-clean. But the published interval `[−0.52,+1.77]` is explicitly an **unpaired** two-arm bootstrap in `cluster/eval_jobs/evidence_bundle.py:70-90`. A paired bootstrap of the five differences gives approximately `[−0.74,+1.85]`. The conclusion remains inconclusive, but the ledger mislabels the evidence. |
| Seed SD, repeat gaps and cross-date checkpoint/config comparisons are POISONED | **Confirmed** | Those summaries mix evaluation dates and, for seed dispersion, training dates. A frozen rescore removes evaluation-date variation but cannot remove the date embedded during training. |
| Date-matched scorecard and MGSM survival claims | **Confirmed, conditionally clean** | The seed-44–46 standard-arm comparisons are both trained and evaluated on the 19th. Those restricted contrasts survive E1. |
| “BAL reduces MGSM” | **Incomplete** | BAL42 trained on the 18th, while BALs43/BALs44 trained on the 19th. The two 19th-trained BAL replicas still support the qualitative comparison against 19th standard arms, but an all-three-seed BAL summary is not a pure date-controlled seed estimate. |
| Global-MMLU-Lite deltas | **Ledger split confirmed** | Runs scored against the 18 September parent prompt are clean as same-date contrasts; 19 September runs compared with the 18 September parent are poisoned. The benchmark is likelihood-based, but its prompt still includes the date. |
| Balanced-arm multilingual ranking | **Confirmed POISONED where dates cross** | It inherits the same parent/run prompt-date mismatch; no special immunity was found. |
| Arm07/08 movement and “no recovery” | **Confirmed POISONED** | Epochs cross the date boundary. The proposed 17-model R1 omits arm07 epochs 4–5 and arm08 epochs 1–3, so it does not repair this result. |
| Served lane: 35/8/2 and associated claims | **Confirmed POISONED and not retrospectively repairable** | Parent serve logs are from 18 September; inspected arm serves are from early 19 September. Saved rows contain only `id`, response, finish reason and usage—neither messages nor rendered prompts. `data/benchmarks_el/generate.py:58` drops the inputs. |
| GreekMMLU-250/custom-full results | **Confirmed superseded or wrong-protocol, not E1-contaminated** | The official/custom prompt path does not use the chat template, so no dynamic date is inserted. Their problem is protocol/frame identity, not E1. |
| Official GreekMMLU result is CLEAN | **Confirmed** | All four files have 16,632 items, identical parquet SHA-256, and `chat_template_applied=false`. The official-label path in `greekmmlu_official.py:124-129` constructs the raw official prompt rather than calling the chat template. Cluster stages resolve to each arm’s `runs/.../checkpoint-129/model.safetensors`, not the parent. Tokenizer hashes match the parent. |
| “IPO did not train” withdrawn | **Confirmed withdrawn** | IPO42’s trainer state is 129/129 steps, epoch 3. The older statement remains stale in other published documents. |
| R1–R4 are necessary and sufficient | **Wrong/incomplete** | R1 cannot undo training-time dates, excludes five movement checkpoints, and only repairs the included lm-eval cells. R2 need not repeat Global-MMLU under a generation config because generation settings do not govern loglikelihood. R4 provides only one arm/checkpoint-config direction, not a full deployment-config interaction. |

### Independent official GreekMMLU recomputation

| Arm | Accuracy delta vs parent | Discordant pairs, gained/lost | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|
| arm01 epoch 3 | −0.414863 pp | 131 / 200 | 0.0001768261 | 0.0003536522 |
| arm05 epoch 3 | −0.432900 pp | 114 / 186 | 0.00003829115 | 0.0001148734 |
| IPO42 epoch 3 | −0.258538 pp | 98 / 141 | 0.006471864 | 0.006471864 |

Parent accuracy is `0.6941438191438192`. These reproduce the published result and remain significant after Holm correction.

### Published material missing from the ledger’s correction surface

The ledger does not fully enumerate stale published assertions:

- `docs/RLHF_COORDINATION/OVERNIGHT_20260918.md:100-111` still says IPO did not train and publishes obsolete GreekMMLU gaps.
- `docs/RLHF_COORDINATION/reviews/R-DPO6_response.md:30,40-58` repeats the no-training claim, treats repeat gaps as same-seed evidence, and documents the unpaired α bootstrap.
- `docs/RLHF_COORDINATION/reviews/R-DPO7a_response.md:29-39,73` retains E1-poisoned aggregate Global-MMLU conclusions and the unpaired interval.
- `docs/DPO01_CURVES_20260918.html:249` still says nothing was independently checked, contradicting the later verification material.

These need explicit correction banners or withdrawal, not merely a corrected future scorecard.

### Rerun assessment

R1’s literal tokenizer substitution is sound only if:

1. the staged tokenizer is the tokenizer lm-eval actually loads;
2. both the rendered prompt bytes and tokenizer/config digest are recorded; and
3. no script overrides it with `tokenizer=$PARENT`.

`dpo01_gencfg_control.sh:60` currently does override with the parent tokenizer, so merely editing the staged model configuration would not freeze that run.

For vLLM, the robust equivalent is an explicit frozen `--chat-template`, or a proven staged tokenizer configuration, followed by recording the input messages, rendered prompt or prompt-token IDs, template digest, and complete request-generation configuration. The current serving path does none of that.

Necessary changes to the rerun plan:

- Expand R1 from 17 to **22 models** if the movement claim is retained: add arm07 epochs 4–5 and arm08 epochs 1–3. Otherwise withdraw that claim.
- Do not claim R1 produces a pure “seed SD”; it produces dispersion among checkpoints trained under different dated prompts.
- R2 should cover generated benchmarks affected by generation settings, not Global-MMLU likelihood.
- R3’s remaining 13 official GreekMMLU models is appropriate; the four completed official runs do not need rerunning.
- R4 needs both configuration directions if a deployment-config interaction is to be estimated.
- The α point contrast and §3–4 displacement do not require E1 reruns for their current restricted interpretations.

## Part B — `rlhf/evals`

### Defeat attempts

| Attempt | Outcome | Materiality |
|---|---|---|
| Change an actual generation row’s `max_gen_toks` and stop sequence while leaving result-level `generation_kwargs` unchanged | **Accepted** | **Material hole.** `_prompt_strings()` ignores the nested generation-options dictionary in real `generate_until` rows. |
| Change recorded `generation_kwargs` | **Refused** | Correct. |
| Change dtype, task hash, few-shot metadata/seeds or other ignored result metadata | **Accepted** | Some are materially outcome-affecting; the manifest does not bind them. |
| Different few-shot selection producing different rendered prompts | **Refused** | Prompt digest catches it. |
| Different few-shot provenance with byte-identical rendered prompts | **Accepted** | Not model-input-material, but provenance remains unrecorded. |
| Different chat-template application producing different text | **Refused** | Prompt digest catches it. |
| Different template provenance producing coincidentally identical text | **Accepted** | Usually outcome-equivalent, but provenance is not bound. |
| Both manifests have `gen_config=None` | **Refused by default** | Correct unknown-not-equal behavior, unless the caller places the key in `varying` or `allow_unknown`. |
| Call `compare(..., varying=IDENTITY_KEYS)` | **Accepted** | **Complete guard bypass.** Every identity difference and unknown can be declared varying. |
| Reuse one `weights_id` for different checkpoints | **Accepted** | **Material hole.** |
| Give one checkpoint two labels | **Refused as different weights** | False negative caused by label identity rather than artifact identity. |
| Reorder otherwise identical documents | **Accepted** | Harmless and desirable. |
| Reassign doc hashes/targets among IDs without changing the sorted hash multiset | **Accepted** | Material dataset/gold-binding hole. |
| Cryptographic `doc_hash` collision | Theoretically accepted | Not the practical threat; absent, forged or unbound hashes are. |

### Prompt and dataset identity

In a real `generate_until` sample, the rendered prompt is `gen_args_0.arg_0`, while `arg_1` is a nested dictionary containing stop conditions, sampling parameters and `max_gen_toks`. `manifest.py:36-48` hashes only string values, so it omits that dictionary.

In a real Global-MMLU loglikelihood row, the prompt and continuation are both strings. Both are currently included. They should be: changing the candidate continuation set changes the likelihood task even if the shared context is identical.

`item_digest` should not be a sorted multiset of bare `doc_hash` values. It should digest canonical records binding at least:

`doc_id + document hash + target/gold hash`

Those hashes should be recomputed or supplied by a trusted dataset receipt, not accepted unchecked from arbitrary result rows.

### Weights identity

`weights_id` at `rlhf/evals/manifest.py:50,88` is an assertion, not an identity. Replace it with a content-derived checkpoint receipt: a canonical digest over resolved shard filenames, byte sizes and full SHA-256 hashes, including the shard index where present. Symlinked stage paths should resolve to the same identity as their target checkpoint.

### Statistics

- `mcnemar_exact` matches independent exact binomial calculations at both small and large discordant counts, including `(602,530)`, `(606,521)`, `(9000,7632)` and `(1100,100)`.
- `holm` matches an independent `p.adjust(..., method="holm")`.
- `paired` correctly enforces identical item sets and strict booleans.
- `seed_bootstrap` correctly implements the documented **independent-arm** bootstrap, but it is not suitable for the claimed seed-paired α interval.
- Validation is incomplete: empty paired maps divide by zero, and bootstrap/Holm do not cleanly reject empty inputs, invalid replicate counts, invalid confidence levels or non-finite/out-of-range p-values.

## Part C — unre-reviewed fixes

### `finalize_greekmmlu_full.py`

What is sound:

- Strict booleans are enforced at `cluster/eval_jobs/finalize_greekmmlu_full.py:89-92`.
- Required manifest fields and clean-descriptor bytes/hash are checked at `:25-57`.
- Output is written only after validation at `:184-190`.
- Current real data are mutually consistent: all four models have the same 16,632 IDs and ID-frame digest `832743e9170dddf47c52d3582bf758ebfce0ae163c0badd94d2a214842d79b6a`, with the expected source, revision, config, split and fingerprint.

What remains unsafe:

- `check_metadata()` at `:59-74` searches serialized bindings for source/revision strings instead of structurally comparing all pinned fields.
- The first submitted model defines the authoritative frame at `:138-145`. If every model contains the same wrong frame, all pass.
- The held-out IDs at `:123-159` are discovered opportunistically from a parent prediction file; their exact count, digest, dataset binding and relationship to the raw frame are not pinned.

The raw frame and held-out slice must each be frozen in the manifest by an authoritative sorted-ID digest or explicit ID file.

### GreekMMLU launchers

Unique per-job stage names are an improvement, but final wildcard cleanup is unsafe:

- `dpo01_greekmmlu_full.sh:82,172`
- `dpo01_greekmmlu.sh:73,163`

`rm -rf "$OUT"/.stage_*` can remove another concurrent job’s live stage. Cleanup must name only stages owned by the current invocation.

Tokenizer validation is still fail-open:

- `dpo01_greekmmlu_full.sh:91-121`
- `dpo01_greekmmlu.sh:82-112`

One-sided absence of `special_tokens_map.json` or `tokenizer_config.json` passes. The comparison also discards `auto_map` and `transformers_version`, not just `tokenizer_class`. `auto_map` can select implementation code and must not be silently normalized away. `dpo01_armcfg_cell.sh:27-30` copies the parent tokenizer without first proving that it matches the arm tokenizer.

Exit-status tracing found real false-success paths:

- `dpo01_greekmmlu_full.sh:144-154` and `dpo01_greekmmlu.sh:135-145`: a failed model command returns success if a headline file exists.
- `dpo01_gencfg_control.sh:53-64`: a failed `uenv run` is followed by a successful `echo`, producing final status 0.
- `dpo01_armcfg_cell.sh:54-66`: a failed score is followed by `echo` and `CELL_DONE`, again producing status 0.

The runner’s status must be captured and required to equal zero independently of any legacy headline or finalizer behavior.

### Official workbench driver

`cluster/greekmmlu_official.sh:4-20` is unsafe for full runs:

- The comments say a full run needs about 2.8 hours, but defaults remain `WALL=02:00:00` and `MAXWAIT=110`.
- Reaching `MAXWAIT` closes the workbench without checking or cancelling/waiting for live scoring processes.
- Existing result files with matching labels can satisfy the poll immediately, causing the driver to copy stale results and close a workbench while a new scorer is still running.
- The script documents up to four models but does not enforce the bound.

Each invocation needs a run identifier or start-time receipt, per-process state, freshness checks, a walltime exceeding the maximum wait, and explicit cancel/wait behavior before closing the workbench.

## Findings, most severe first

1. **BLOCKER — Comparison policy is caller-bypassable.** `rlhf/evals/compare.py:29-53` permits `varying=IDENTITY_KEYS` and arbitrary `allow_unknown`, defeating the promised refusal guard. Public comparisons should accept a closed, named policy or an approved singleton varying key; unsafe overrides must not be available to report-producing code.

2. **HIGH — Actual generation requests and runtime identity are not bound.** `rlhf/evals/manifest.py:36-48,87-95` omits nested per-row generation options and many materially relevant result fields.

3. **HIGH — Checkpoint identity is caller-supplied.** `rlhf/evals/manifest.py:50,88` permits two checkpoints to share an ID and one checkpoint to acquire multiple IDs.

4. **HIGH — Dataset and gold identity are not bound to item IDs.** `rlhf/evals/manifest.py:65-91` hashes a sorted multiset of document hashes without binding them to IDs or targets.

5. **HIGH — The ledger’s rerun cure is insufficient.** `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:35-37,45,54,67` claims R1 cures E1 everywhere, although training-time dates remain and five movement checkpoints are absent.

6. **HIGH — The α interval is falsely described as paired.** `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:44`; `cluster/eval_jobs/evidence_bundle.py:70-90`; `rlhf/evals/stats.py:58-68`.

7. **HIGH — Stale published claims are outside the ledger’s correction list.** `docs/RLHF_COORDINATION/OVERNIGHT_20260918.md:100-111`; `docs/RLHF_COORDINATION/reviews/R-DPO6_response.md:30,40-58`; `docs/RLHF_COORDINATION/reviews/R-DPO7a_response.md:29-39,73`.

8. **HIGH — The finalizer trusts the first model to define the raw and held-out frames.** `cluster/eval_jobs/finalize_greekmmlu_full.py:59-74,123-159`.

9. **HIGH — Tokenizer staging remains fail-open and cleanup can cross job boundaries.** `cluster/eval_jobs/dpo01_greekmmlu_full.sh:91-121,172`; `cluster/eval_jobs/dpo01_greekmmlu.sh:82-112,163`; `cluster/eval_jobs/dpo01_armcfg_cell.sh:27-30`.

10. **HIGH — Evaluation launchers can report success after scoring failure.** `cluster/eval_jobs/dpo01_greekmmlu_full.sh:144-154`; `cluster/eval_jobs/dpo01_greekmmlu.sh:135-145`; `cluster/eval_jobs/dpo01_gencfg_control.sh:53-64`; `cluster/eval_jobs/dpo01_armcfg_cell.sh:54-66`.

11. **HIGH — The official driver can close around live scoring or accept stale outputs.** `cluster/greekmmlu_official.sh:4-20`.

12. **MEDIUM — The displacement row’s status is right but its “no date” rationale is false.** `docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md:43`; `cluster/dpo_train.py:67-70`.

13. **MEDIUM — The API lacks a paired-seed bootstrap despite publishing a paired interpretation.** `rlhf/evals/stats.py:58-68`; `rlhf/tests/test_evals.py:93-95`. The current test named for the published interval does not assert the numerical interval.

14. **LOW — Official evaluator metadata hardcodes `chat_template_applied=false` even for supported chat protocols.** `cluster/eval_jobs/greekmmlu_official.py:181-184`. The reviewed official-label files are nevertheless genuinely template-free.

15. **LOW — Statistical input validation is incomplete.** `rlhf/evals/stats.py`: empty pairs, invalid bootstrap parameters and invalid p-values need explicit rejection.

## Ordered asks

1. Do not authorize reruns or republication until findings 1–11 are fixed.
2. Close the comparison API: validated manifest schema, content-derived checkpoint identity, canonical item/gold identity, full request/runtime capture, and no unrestricted `varying`/`allow_unknown`.
3. Correct the ledger: label the α interval unpaired or recompute it paired; distinguish evaluation-date freezing from training-date contamination; add the five missing movement checkpoints or withdraw the movement claim.
4. Add correction banners to every stale published document listed above.
5. Pin the full GreekMMLU raw frame and held-out slice independently of submitted model outputs.
6. Make all launchers fail closed on tokenizer presence/equality, scoring status, finalizer status and per-job cleanup.
7. Repair the workbench driver with fresh-output receipts, live-process accounting, sufficient walltime and explicit shutdown semantics.
8. Only then construct a dry-run manifest/receipt for the narrowed rerun set and review it before spending cluster capacity.

VERDICT: HOLD — ledger and guard are not safe enough to authorize re-runs or republication | BLOCKERS: 1 | HIGH: 10

