# Krikri v1.5 matched-evaluation readiness

## Decision state

**Ready for root review; not launched.** The revision-pinned v1.5 checkpoint is cached, the corrected adapter bundle is read-only on Clariden, all allocation-free checks pass, the exact `sbatch --test-only` command passes, and its predicted job ID does not exist in the queue. The intended next action is one `debug` attempt capped at 1 hour 25 minutes after root reviews these final receipts. No GPU is held.

The immutable code/data payload is `edf6f76fa34cf4a362b258a250259ce7d03029a7f2a739a2c9631caa1777b9dc` at:

`/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_peer_eval/bundle_edf6f76fa34cf4a3`

The directory is `dr-xr-xr-x`; the manifest is read-only. The proposed attempt root does not exist:

`/iopsstor/scratch/cscs/fffoivos/sft_round1/evals/wave2_krikri_v15/attempt_001`

## Bound model and runtime

- Model: `ilsp/Llama-Krikri-8B-Instruct-v1.5` at revision `326e2c0ea90d771c19fcf06225fe87dc922b51b2`.
- Checkpoint identity: all four safetensor files are size- and SHA-256-bound; the canonical preflight rehashed them successfully.
- Control identity: `config.json`, `generation_config.json`, `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `chat_template.jinja`, and `model.safetensors.index.json` are size- and SHA-256-bound. The initial candidate only enforced weights and the template at execution time; the final adapter closes that gap and the canonical receipt verifies all seven added bindings.
- vLLM runtime: `vllm 0.28.0`, `transformers 5.16.1`, `torch 2.13.0+cu130`, entered through the pinned uenv plus `/iopsstor/scratch/cscs/fffoivos/venvs/vllm`.
- ILSP/lm-eval runtime: `lm_eval 0.4.11`, `transformers 4.57.0`, `datasets 4.0.0`, `accelerate 1.13.0`, `torch 2.9.1` in `pytorch/v2.9.1:v2`.
- ILSP data caches: `ilsp/ifeval_greek` revision `3ed53c2a790ce48020bf54aee70e1ea6c6b689b7` (`train`, 541 rows) and `ilsp/mgsm_greek` revision `27b0f7bf1732f9ff2cfc3e26d43293ba9d49ecd3` (`test`, 250 rows). Task implementation files are individually bound in the science manifest.

No new license agreement was accepted during intake. The cached public model reports the Llama 3.1 license; both ILSP evaluation datasets report CC BY-NC-SA 4.0 metadata. These facts constrain later redistribution but do not prevent this private measurement.

## Frozen first-batch contract

The batch uses the model's native chat template, no extra system prompt, greedy decoding (`temperature=0`, `top_p=1`), 2,048 requested output tokens for MATH-500, 1,024 for other fixed tasks, and a 4,096-token model limit.

| Cell | Items |
|---|---:|
| MATH-500 Greek / English | 500 / 500 |
| IFBench Greek / English | 300 / 300 |
| XSTest Greek / English | 450 / 450 |
| MultiChallenge Greek / English diagnostic subset | 213 / 213 |
| ILSP IFEval Greek | 541 |
| ILSP MGSM Greek | 250 |
| Total generations | 3,717 |

The adapter first generates 8 rows in each of the eight fixed cells. It requires 8 rows, 8 unique IDs, and zero request errors in every cell. It then resumes the same files, so those 64 smoke rows are not called again. Final gates require the exact declared row and unique-ID count with zero request errors. ILSP collection requires exactly the two declared task keys, one sample file per task, and exactly 541 and 250 unique document IDs; a different task/config or any count drift fails the attempt.

XSTest and MultiChallenge judging is deferred. MT-Bench and Belebele were not added because their local matched contracts were not validated. GreekMMLU is also outside this first batch: the separate 200-item official-label versus historical full-answer-text protocol diagnostic remains separately priced work and does not alter this adapter.

## Context gate and MultiChallenge boundary

Every actual fixed-suite input was rendered through the v1.5 native template and tokenized allocation-free. All retained inputs plus their requested outputs fit 4,096 tokens. Maximum retained input lengths were:

| Cell | Maximum input tokens | Input + requested output |
|---|---:|---:|
| MATH-500 Greek / English | 845 / 803 | 2,893 / 2,851 |
| IFBench Greek / English | 383 / 400 | 1,407 / 1,424 |
| XSTest Greek / English | 65 / 54 | 1,089 / 1,078 |
| MultiChallenge Greek / English | 3,045 / 2,609 | 4,069 / 3,633 |

MultiChallenge has 273 physical source rows, of which 11 are already source-excluded, leaving 262 eligible IDs. Forty-nine eligible IDs exceed the context budget in at least one v1.5 language cell: 49 Greek and 27 English overlength cell occurrences, with 49 unique IDs in the union. The adapter excludes that same union from both languages and retains 213 items. It does not truncate.

This is a **213/262 diagnostic subset**, not a full MultiChallenge result. It cannot be compared with the historical original-Krikri 262-item aggregate. The full eligible ID ledger and exclusion list are preserved in `multichallenge_full262_id_ledger.json`. Before a peer difference is reported, every included model must pass the same native-template token gate and every model must be scored on the exact same IDs. If the shared set changes, historical row-level results must be recomputed on that intersection. A later longer-context matched run over all 262 items for all models is the preferred supplementary result.

## Scheduler and budget

Exact allocation-free scheduler test:

```text
sbatch --test-only --export=ALL,PEER_BUNDLE=/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_peer_eval/bundle_edf6f76fa34cf4a3,PEER_OUTPUT=/iopsstor/scratch/cscs/fffoivos/sft_round1/evals/wave2_krikri_v15/attempt_001/result.json /iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_peer_eval/bundle_edf6f76fa34cf4a3/peer_eval_debug.sbatch
```

It predicted one `debug` node (`nid006245`, 288 processors) and returned success. A subsequent queue lookup returned `Invalid job id specified`, confirming that test-only ID `3390940` did not create a job.

The script requests 1 node, 4 GPUs, 288 CPUs, 640 GB, and 1:25:00 in `debug`, or 1.4167 node-hours. It assigns fixed-suite vLLM to GPU 0 and ILSP lm-eval to GPU 1 after the fixed smoke passes; GPUs 2–3 are reserve. The projected charge is CHF 3.81. The first measurement envelope remains 4 node-hours (CHF 10.76); there is no fallback to `normal` for this short attempt.

The current ledger is 60.602 node-hours / CHF 163.02 used against CHF 230, leaving CHF 66.98 or about 24.8996 node-hours. This corrects the earlier conservative CHF 164.54 figure by -CHF 1.52. A fresh `squeue --me` snapshot at 2026-09-13 13:42:31Z returned no active jobs.

## Canonical boundary

The canonical repository is pinned at `origin/main` revision `22c4561050cba36f34b8480e1373788e139aaf3c`; `preflight_evaluator.py` is bound at SHA-256 `bc24ae97314f7f48893aafc2bd6c5aa451b5f42c07fcef2270f2f4d1f54f6ee9`.

The current canonical campaign contract has no standalone external-checkpoint evaluation mode. Campaign v3 requires at least one segment and gate and training-specific science fields; evaluation probes require a compiled campaign milestone. Creating dummy training state would misstate provenance. The bounded adapter therefore keeps scientific selection in this experiment, uses the canonical evaluator preflight, and uses the exact raw scheduler test. `CANONICAL_GAP_ISSUE_DRAFT.md` records the reusable feature request locally; it has not been posted.

## Final preflight receipts

| Receipt | Result |
|---|---|
| `receipts/adapter_preflight_edf6f76f.json` | pass; all 3,352 fixed inputs tokenized before exclusion, retained counts exact, no unexpected overlength |
| `receipts/canonical_bindings_edf6f76f.json` | pass; 43 live file bindings plus environment-root integrity |
| `receipts/canonical_vllm_imports_edf6f76f.json` | pass; exact vLLM interpreter and versions |
| `receipts/canonical_lmeval_imports_edf6f76f.json` | pass; exact ILSP evaluator interpreter and versions |
| `receipts/scheduler_test_edf6f76f.json` | pass; scheduler prediction only, no allocation |

The next action is root review of these final artifacts, followed by the single bounded debug attempt under the standing measurement authorization. If it cannot finish inside 1:25:00, stop and re-plan inside the 4-node-hour envelope rather than changing partition or scope.
