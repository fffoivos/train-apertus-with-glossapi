# First DPO pilot: existing preferences, no maths task training
Date: 2026-09-18
Owner decision: run the data we already have; stop spending calls improving a pipeline before testing its output.
Executor: Opus. This is an execution specification, not a claim that the trainer or run already exists.
Experiment label: G4F6P1--DPO01. Parent: G4F6P1. G/F/P SFT dataset versions remain unchanged; DPO01 identifies preference training.


> Latest recommendation: see [DPO_EXPERIMENT_COMPARISON_20260918.md](DPO_EXPERIMENT_COMPARISON_20260918.md), following the owner's request to spend compute on recipe experiments. That proposed comparison replaces the single-run recommendation below; shared integrity requirements remain applicable. No jobs have been launched.

## Status clarification — 18 September, after owner asked about added assumptions

The owner agreed to use existing preferences, exclude mathematics from preference training, avoid another data-improvement campaign, evaluate the resulting model, and register limitations. The remaining recipe is the author's PROPOSAL, not a record of decisions already agreed with the owner.

In particular, full-parameter training; one epoch; batch 8; the 10% grouped holdout; dropping the earlier chosen-response SFT/RPO term; the smaller evaluation subsets; choosing IFEval as primary; the heuristic regression thresholds; zero NEW EVALUATION JUDGE calls; and the five-node-hour ceiling were supplied by the author. Beta 0.1 and LR 5e-7 were carried forward from the older recipe. Keeping existing development-only dialogue records excluded follows their recorded status, but the resulting single-turn scope must be explicit.

The phrase “supersedes” below specifies what the proposed recipe changes IF adopted; it must not be read as owner approval of every change. In particular, deciding not to repair training data does not inherently require removing judged evaluation. Opus must not describe these choices as previously owner-approved. This clarification does not launch or add an experiment.

Runtime forecast (not a measured DPO qualification): approximately 0.5–1.5 allocated node-hours for worker setup/reference/smoke/train/save, plus 1.5–3 node-hours for the proposed reduced automatic evaluation with matching parent caches reused: 2–4.5 node-hours total. Five is a proposed allowance including contingency, not a guaranteed finish or an approved new spending cap. Queue time and off-node trainer development are additional wall time. A broader evaluation or incompatible baseline caches can exceed this range. At the ledger rate CHF2.69/nh, the range is CHF5.38–12.11; tariff applicability and available allocation must be verified before launch.

## 1. Decision and scope

Run ONE full-parameter, one-epoch DPO experiment against the unchanged SFT parent. Use existing eligible non-maths preference pairs with their existing judgements and text. No new prompt generation, reply sampling for training, reference solving, semantic re-review, judge calibration, relabelling, balancing campaign, or hyperparameter sweep. New Sol/Astra/Opus MODEL-API calls for data generation or judging: ZERO. Ordinary executor work is distinct from launching annotation jobs. Model inference on CSCS for reference log probabilities and evaluation is required and budgeted.

Maths remains an evaluation/retention task. For this pilot, “no maths DPO” means exclude the dedicated maths task/route: purpose=math, task=math, specialist maths-route pairs, and records explicitly classified as standalone maths. Incidental quantities or arithmetic in ordinary assistance remain under the existing general rubric; report their existing embedded-maths labels. Do not invent another classifier or silently describe the result as completely maths-free.

This plan supersedes the 16 September plan's 20,000-pair target, batch 64, auxiliary chosen SFT loss, extra generation/judging, and full evaluation chain for THIS pilot. No minimum pair count or target-distribution quota delays this run. No second model is automatically authorized by an ambiguous or negative result.

Project root (P):
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments

Cluster root (R, verify it still exists):
/iopsstor/scratch/cscs/fffoivos/sft_round1

Read CURRENT_VERSIONS.md and this document together: this document supplies the latest owner scope; recorded artifacts establish what actually exists. All relative paths below are relative to P locally and the staged project root on the worker.

## 2. Evidence and current implementation gap

Inspected on 18 September:
- data/rlhf/registry/registry.sqlite: 209 pair_credit records with eligible=1; eligible records have no maths-content flag.
- data/rlhf/round3/round3_pairs.jsonl and round3_summary.json: 238 eligible, of which 23 purpose=math; 215 remain before reconciliation.
- Hence 424 is an expected input inventory, NOT a certified training count.
- data/rlhf/dialogue_v2/collection60/runtime/branch_pairs.jsonl: eight saved pairs, marked development, development_demo, training_eligible=false, experiment_credit=0. Preserve those flags. Keep these OUT of this training run; no silent promotion. One is maths learning; two have no earlier assistant turn.
- Old generator-0.1 data and the superseded dialogue pilot remain excluded by their existing status.
- No DPOTrainer/DPOConfig implementation was found in cluster/ or data/rlhf/. cluster/dpo_train.py is an implementation task.
- cluster/train_sbatch.sh invokes sft_train.py: it is NOT a DPO launcher.
- The worktree has existing uncommitted edits. Preserve them, and hash the actual files used, not just the Git commit.

## 3. Freeze the parent and environment

Parent policy and frozen reference MUST be the identical G4F6P1 checkpoint:
- HF id: fffoivos/greek-apertus-8b-sft-r4-full
- Recorded revision: 3a557e0842b146ccb6d24427e20b08c52fb368d5
- Recorded checkpoint digest: 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763
- Existing local-cluster aliases: runs/R4_full/epoch1 and eval_copies/R4_full_ep1. These are storage aliases, not new experiment names.

Verify the existing digest receipt's definition (single weights file versus manifest hash); do not compare unlike hash types. Freeze tokenizer, chat template, control-token IDs and EOS treatment from that exact parent. No new vocabulary, template import, system prompt, or resizing.

Reuse the validated Clariden training environment and sharding approach. Existing pointers: cluster/sft_train.py, cluster/configs/zero3.yaml, pytorch/v2.9.1:v2, /iopsstor/scratch/cscs/fffoivos/venvs/sft5. Inspect actual installed torch/transformers/trl/accelerate/deepspeed versions and signatures. Do not assume the old plan's “TRL 1.12” string is an installed or compatible version; pin what passes the smoke test. Official format/API reference: https://huggingface.co/docs/trl/dpo_trainer (consulted 18 September; installed API is decisive).

## 4. Export existing pairs; do not change semantic judgements

Opus implements a small exporter under data/rlhf/dpo01/ using these inputs:
1. Open registry.sqlite read-only. Join pair_credit -> judgements -> prompts/aliases. Read chosen/rejected by the judgement's ORIGINAL source file and alias, using pool/round1_all_samples.jsonl or pool/round2_all_samples.jsonl as recorded. Do not combine rows by a coincidentally matching short id across pools.
2. Keep only keepable, eligible, current general-rubric records. Preserve archived/held exclusions.
3. Read round3_pairs.jsonl entries with status=eligible and a non-null general-route pair. Join round3_all.jsonl and round3_samples.jsonl using prompt id, sampled prompt version, and chosen_k/rejected_k.
4. Apply the maths-task exclusion in section 1. Preserve all other existing rankings and reply text; do not recalculate pair eligibility under a new quality rubric.
5. One pair per distinct logical prompt/prefix. Reconcile aliases and normalized role/content hashes across both inputs. Preserve actual training text byte-for-byte: normalization is for duplicate detection only. If duplicate versions disagree, use the currently active sampled prompt version; otherwise newest active judgement timestamp; otherwise deterministic round3 precedence. Record discarded aliases and conflicts.
6. Structural exclusions only: missing provenance or samples, identical chosen/rejected text, empty completions, mismatched prompt versions, held/superseded status, known benchmark overlap from existing manifests, or an example that cannot fit intact in 4,096 tokens. Do not silently truncate. Report finish_reason=length; preserve existing semantic eligibility rather than launching new judgement calls.
7. Use existing source/seed-family links to prevent train/dev leakage. A group is a connected component of logical aliases, same underlying forum thread/source problem, and known seed siblings. Do not group an entire forum or broad task category as one family. Unknown semantic siblings remain a documented limitation.

Export conversational preference records:
prompt = exact list of context messages ending in the latest user turn;
chosen = one assistant message with the chosen text;
rejected = one assistant message with the rejected text.
Keep provenance/IDs/labels in a sidecar. The trainer must not expose judge rationales, references, hidden scenario state, or metadata to the model.

Freeze groups before training. Deterministic split:
group_key = stable source/seed component id, falling back to canonical prompt hash.
dev if int(sha256("20260918|"+group_key),16) % 10 == 0; otherwise train.
All members of a group have the same split. Approximately 10% dev, not a promised exact count. If fewer than 10 dev groups result, move the lowest-hash train groups until dev has 10. Do not tune the split after seeing model outputs.
Use every remaining train pair once; no oversampling, quota balancing, or extra pairs from the same sampled quartet.

Write:
data/rlhf/dpo01/{train.jsonl,dev.jsonl,provenance.jsonl,exclusions.jsonl,manifest.json}
Manifest includes exact group/row/token counts, purpose × input language, known output language separately, lengths, chosen/rejected length ratios, embedded-maths counts, hashes, source snapshots and split algorithm. Expected roughly 380 training pairs if all 424 survive, but actual counts control the run.

## 5. Fixed training recipe

| Setting | This pilot |
|---|---|
| Objective | Standard sigmoid DPO; NO auxiliary SFT/RPO term |
| Policy / reference | G4F6P1 / frozen identical G4F6P1 |
| beta | 0.1 |
| Label smoothing | 0 |
| Learning rate | 5e-7 |
| Epochs | 1; no automatic extension |
| Effective global batch | 8 PAIRS |
| Layout | 4 GPUs × 1 pair/GPU × accumulation 2 |
| Optimizer | AdamW; beta1=.9, beta2=.99, eps=1e-8, weight decay=0 |
| Gradient clipping | 1.0 |
| Schedule | 3% warmup, cosine to zero; resolve warmup=max(1,ceil(.03 × actual updates)) |
| Seed | 42 |
| Precision | FP32 persistent/master updates and optimizer states; BF16 autocast; FP32 log-prob sums/loss |
| Maximum length | 4,096 tokens per prompt+completion, intact |
| Packing | Off |
| Gradient checkpointing | On; use_cache=False during training |
| Dropout | Disabled for policy/reference likelihood evaluation |
| Reference | Precompute frozen-reference completion log probabilities once, then unload reference |
| Checkpoints | Midpoint and final; final is the preselected evaluation candidate |
| Logging | Every optimizer update; no external telemetry/API reporting |

Copy the existing ZeRO-3 configuration into a run-specific file and set gradient_accumulation_steps=2 there AND in trainer configuration. Do not accidentally inherit 4 from cluster/configs/zero3.yaml. Do not switch to LoRA/quantized training as an unrecorded memory workaround.

For N_train≈382, target ceil(N_train/8)=48 optimizer updates, ~2 warmup updates. A world-size-padding sampler can duplicate a few records: prefer a sampler that uses each row once and handles the final partial batch; at minimum record actual exposures, unique rows, padding/repeats and measured updates. Do not secretly add epochs to reach an old 100-step checkpoint interval.

Let c/r be summed log probabilities of CHOSEN/REJECTED target completion tokens, including one canonical end-of-turn terminator, excluding all prompt/history and padding tokens:
loss = -mean(logsigmoid(0.1 * ((c_policy-c_reference) - (r_policy-r_reference)))).
No length normalization inside this loss. Record per-token likelihoods separately for diagnosis. Set auxiliary SFT/RPO off using the installed API's supported setting; do not leave an inherited default enabled.

Why this recipe: one simple preference update that we can interpret; batch 64 would give only ~6 updates. These are proposed conservative pilot settings, not demonstrated optimal settings for Greek Apertus. A null result with this short, low-LR run does not establish that DPO cannot work.

## 6. Small implementation checks, with no judge calls

Implement cluster/dpo_train.py and its run-specific config; reuse tokenizer/control-ID and FP32 safeguards from sft_train.py. Add only tests needed to avoid an invalid training run:
- A two-pair fixture, including a multi-turn prefix, shows that only the latest assistant completion is scored. Earlier assistant turns are context, not training targets.
- Chosen/rejected share the same prompt IDs; padding/EOS masks are correct. Cached reference values are bound to exact input IDs, masks, reference and template hashes.
- At initialization, matching policy/reference gives near-zero log-ratios and DPO loss near log(2); report numeric discrepancies rather than assume a tolerance blindly.
- Compare a bounded fixture's cached versus direct reference values under identical precision.
- Confirm finite gradients and a nonzero FP32 parameter update after one optimizer step; the reference does not change.
- Save/reload the smoke output and verify token IDs/template and stable logits on the fixture.
- Reinitialize from the original parent for production. Smoke steps do not contaminate the production initialization.

Reference caching implementation: inspect the installed TRL version before enabling any precompute option; some versions restrict built-in caching with ZeRO-3. The scientific requirement is fixed reference likelihoods, not a particular flag. Prefer an offline worker reference pass and a narrow adapter consuming the stored, hash-bound values; verify on the bounded direct-reference fixture that the trainer actually reads those values. If the installed trainer cannot consume them safely without a substantial rewrite, use a frozen reference supported by that trainer and qualify its memory/runtime within the same ceiling. Record which implementation was used. Never silently fall back to reference-free DPO or recompute the reference from the updated policy.

Run local CPU fixture checks without loading the 8B model. Run model loading, tokenization/export processing, reference computation and GPU checks on the designated CSCS worker, not the Mac. A failed infrastructure check may be repaired within the same fixed experiment and budget; changing data judgements or scientific settings is a new decision.

Dry-run command contract to implement (these entrypoints DO NOT exist yet):
python cluster/dpo_train.py --config cluster/configs/G4F6P1_DPO01.yaml --dry-run
Production command INSIDE an audited allocation:
accelerate launch --config_file cluster/configs/zero3_dpo01.yaml cluster/dpo_train.py --config cluster/configs/G4F6P1_DPO01.yaml --out-dir runs/G4F6P1--DPO01
Use a run-specific immutable launcher; do not call the SFT launcher unchanged.

## 7. Evaluation: paired, automatic first, no new LLM judges

Primary comparison is unchanged G4F6P1 versus final G4F6P1--DPO01. No checkpoint shopping. Midpoint is recovery/diagnostic only. Historical Krikri 1.5 and Apertus-Instruct results can be shown only for identical benchmark versions, item IDs and protocols; no new competitor inference or judging in this pilot.

Before training, write evaluation_manifest.json with exact input IDs, dataset/scorer/code hashes, task configs, few-shot exemplars, decoding, chat template, model identities, outputs and expected counts. Reuse baseline per-item outputs only when those bindings match. Re-score saved baseline text with the frozen scorer if necessary; that costs no model call. Where they do not match, run BOTH models under the same frozen protocol within the budget.

Required first-pass evaluation:
| Measurement | Scope / scoring |
|---|---|
| Preference dev | All withheld groups: DPO loss, preference margin, raw chosen/rejected summed and per-token log probabilities vs parent; no judge |
| Greek IFEval | Full 541 items, existing chat protocol; prompt-level strict primary, instruction-level strict and loose secondary |
| Greek MGSM | Full 250 items, existing exact-match scorer; same shot count/template as the verified baseline |
| Greek IFBench | Full 300 items; report existing strict/core/family and overlap splits separately; known words-checker uncertainty remains labelled |
| MATH-500 | Full 500 Greek AND 500 English; same boxed-answer prompt, token cap and equivalence scorer as parent |
| Greek knowledge | 250 fixed GreekMMLU items from the existing clean subset, stratified by available subject/category, largest remainder allocation with hash-order tie breaks; preserve existing official scoring and exemplars |
| Multilingual retention | 100 Global-MMLU items PER language for EL/EN/FR/DE/ES/IT/PT, from existing cached benchmark; choose shared source-question IDs where available, balanced across available subjects and frozen before training; existing chat/few-shot protocol |

GreekMMLU and Global-MMLU subsets are explicitly PILOT DIAGNOSTICS, not full-benchmark scores. The seven-language sample is a modest retention screen, not proof of multilingual generation quality. If no already-supported cached task exists for a language, record it as unmeasured instead of quietly substituting another test.

Do not run the old whole evaluation chain blindly:
- cluster/eval_checkpoint.sh invokes voice_score.py and interviews/score.py even when SKIP_INTERVIEWS is set: that is not a zero-judge path.
- cluster/full_battery.sh spends ~4.3 historical node-hours and covers a different battery.
- data/benchmarks_el/run_review_programmatic.sh calls an external reviewer despite its name.
- data/benchmarks_el/ifbench/score.py reads Greek kwargs unconditionally: do not feed it English responses and publish that as English IFBench accuracy.

Reuse the lower-level programmatic paths:
- evals/ilsp/run.sh and evals/ilsp/tasks; preserve the confirmed baseline's language-check correction from evals/ilsp/rescore_ifeval_langdetect.py, applied equally to both models.
- data/benchmarks_el/generate.py (explicit --sets, never its default including judged tasks).
- data/benchmarks_el/math500/score_math500.py.
- data/benchmarks_el/ifbench/score.py for GREEK responses.
- cluster/eval_jobs/greekmmlu_official.py / greekmmlu.sh and retention_chat.sh as protocol references. Build a scoped worker wrapper selecting manifest IDs; do not change scorers, task names, exemplars or few-shot counts to make the subset easier. Resolve actual installed multilingual task names into the manifest; do not guess them.

Existing worker commands for the served evaluation stage, after Opus binds MODEL, ENDPOINT, OUT and the worker Python environment:
python data/benchmarks_el/generate.py "$ENDPOINT" "$MODEL" "$OUT" --sets math500 --langs el,en --workers 16
python data/benchmarks_el/generate.py "$ENDPOINT" "$MODEL" "$OUT" --sets ifbench --langs el --workers 16
python data/benchmarks_el/math500/score_math500.py "$OUT/math500_el.jsonl" "$OUT/math500_el_score.json"
python data/benchmarks_el/math500/score_math500.py "$OUT/math500_en.jsonl" "$OUT/math500_en_score.json"
python data/benchmarks_el/ifbench/score.py "$OUT/ifbench_el.jsonl" "$OUT/ifbench_el_score.jsonl"
The generator already specifies temperature=0, top_p=1, max_tokens=2048 for maths and 1024 for IFBench, no extra system prompt. Preserve those and the 4,096 context. Existing output files are resumable by id; use distinct model/run directories and verify all expected unique IDs before accepting completion.

After serving stops, reuse GPUs for likelihood-based evals. Run independent eval lanes on separate GPUs only where memory has been qualified; do not overlap them with full-parameter training or the four-GPU native scorer. Do not reserve GPU nodes while implementing code or waiting for a human/LLM review.

No extra automatic dialogues, MT-Bench judge, XSTest judge, Multichallenge judge, stylistic reviewer or human-calibration campaign in the core run. The development dialogue pairs can be scored for completion likelihood without generation, separately, including the non-maths subset; this is a descriptive fit diagnostic with a tiny, previously inspected sample, not evidence of improved conversations.

## 8. Interpretation fixed before seeing results

For each automatically scored task report n, baseline, DPO, paired delta in percentage points, 95% paired item-bootstrap interval (10,000 resamples, seed 42), and improved/regressed/unchanged item counts. Group resampling by underlying source question where rows repeat. Intervals describe uncertainty over this evaluation sample, not seed-to-seed training variation; no multiplicity-adjusted confirmatory claim.

Primary endpoint: Greek IFEval prompt-level strict delta. Positive evidence: interval entirely above zero. Interval crossing zero: inconclusive, even if point estimate rises. Secondary IFBench improvements do not silently replace a failed primary endpoint.

Retention warning thresholds (pragmatic, NOT validated non-inferiority margins): drop of >=3 percentage points on any FULL maths/IF task, >=5 points on 250-item GreekMMLU, or >=10 points on a 100-item language screen. Also flag statistically clear negative paired deltas, missing outputs, repetition/empty-output increases and material truncation increases. A flag means keep the parent as default and inspect the saved outputs; it does not automatically trigger regeneration or another run. Absence of a flag is not proof of preservation.

Also log output length quantiles, exact repeated-tail/empty-output rates, finish reasons, and any existing deterministic language metrics. Do not treat these proxies as measured helpfulness, factuality or safety. Preference reward accuracy is not task accuracy; fixed-pair log-ratio statistics are not an on-policy KL estimate.

Possible conclusions:
1. “IF improves with no detected retention loss on the measured panel”: promising narrow result; broader behaviour still unmeasured.
2. “No clear improvement”: valid pilot result, possibly low statistical power or too small an update; no automatic bigger run.
3. “Regression/numerical failure”: retain parent, explain evidence and resource use.
No conclusion here supports “better dialogue”, “safer overall”, or “beats Krikri across the board” without the missing measurements.

## 9. Compute budget and launch sequence

This handoff spends no compute. Opus executes within the current authorized cap; this document does not raise it.
Local recorded ledger on 18 September (NOT a live balance): cap CHF240, used CHF223.39, rate CHF2.69/node-hour; apparent remaining CHF16.61. This is the experiment cap, distinct from the grant's previously reported overall CHF2,095.08 remaining.

Proposed complete-pilot ceiling: FIVE allocated node-hours, including smoke, reference compute, training, baseline misses, evaluation, startup and failures. At the recorded rate that is CHF13.45, leaving CHF3.16 against this stale ledger. Reserve within five hours:
- 1.5 nh: worker preflight, reference cache, model smoke, one training run, save/reload.
- 3.0 nh: required paired automatic evaluation, prioritizing existing baseline reuse.
- 0.5 nh: contingency.
These are planning ceilings, not measured runtime forecasts.

Before submitting: refresh account usage, concurrent/pending commitments, current tariff and grant deadline; reconcile execution_state.json without overwriting others' allocations. Confirm the one-node profile/time limit and reserve the complete pilot envelope, not just training. If five hours does not fit current authority or qualification predicts it cannot complete, report the exact shortfall; do not raise the cap or silently cut evaluation. Keep code/export preparation moving.

Prefer the approved short-job/debug workflow for checks that fit the LIVE partition limits. Follow current CSCS/canonical allocation receipts; this plan does not resurrect obsolete hand-written orchestration. Training uses one node/four GPUs. Reuse allocations where practical, then release immediately. No recurring monitoring automation; owner previously stopped it.

Run order:
1. Freeze sources, export/split, manifest; implement and fixture-check trainer and scoped eval wrapper without GPU reservation.
2. Bind baseline caches and eval IDs; compute full job ceiling and verify live capacity/budget.
3. On worker, tokenize intact pairs, frozen reference, smoke checks; freeze actual count/update plan.
4. Reinitialize policy from parent, run exactly one epoch, save final, validate reload.
5. Evaluate final and any unmatched parent baselines under the frozen manifest.
6. Write paired report, actual spend and known/unmeasured limitations. Release resources. Stop.

## 10. Deliverables and handoff back

Opus returns:
- data/rlhf/dpo01/manifest.json and provenance/exclusion/split counts.
- Exact config, trainer and environment hashes; reference-cache receipt.
- run_receipt.json: parent/final identities, steps/exposures, losses, FP32 updates, job IDs, measured time/memory, cost, zero external generation/judging calls.
- evaluation_manifest.json, complete per-item outputs, paired metrics and unmeasured cells.
- results/G4F6P1--DPO01/REPORT.md with one verdict and links.
- Update the companion DPO01_LIMITATIONS_AND_FUTURE_WORK_20260918.md with measured evidence, without erasing the original blind spots.
- No upload/publication or default-model replacement implied by completing the pilot.

Do not turn the limitations register into preconditions for running the pilot. Only data integrity, correct objective/masking/model identity, executable evaluation and budget are run requirements. The point is to measure this version before improving the next one.
