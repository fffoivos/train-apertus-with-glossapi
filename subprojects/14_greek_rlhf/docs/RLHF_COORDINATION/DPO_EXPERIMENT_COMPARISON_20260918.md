# DPO experiment comparison — revised proposal, 18 September 2026
Owner steering: CSCS experiments are affordable; learn which training recipe works while keeping new generation and annotation calls constrained.
Executor: Opus. Status: concrete proposed design; no jobs launched and no budget cap raised.
This document replaces the ONE-RECIPE recommendation in DPO01_EXECUTION_PLAN_20260918.md. Its data integrity, model identity, masking, FP32 update and provenance requirements remain applicable. This amendment controls experiment count, schedule, checkpoint selection and evaluation staging.

## 1. What changes, and what stays fixed

New recommendation: FOUR matched training runs, covering two learning rates and the presence/absence of the chosen-answer SFT term. Save checkpoints after epochs 1, 2 and 3. The unchanged G4F6P1 is the baseline. This gives 12 checkpoints from four trajectories, not 12 independent runs.

No new training prompts, samples, judgements, maths reference work or data corrections. Use the same frozen existing non-maths pool and existing eligibility flags. Dedicated maths-task training stays excluded. Development-only dialogues stay diagnostic. Use the same family-separated train/dev split for every arm. Do not change source counts or balancing between arms. Number of external generation/judge calls in the screening stage: ZERO.

This is a hyperparameter/recipe screen, not a factorial study of all possible parameters. Initially hold beta, batch, template, optimizer, initialization and data order fixed. Vary learning rate and the chosen-response term; observe exposure via checkpoints.

## 2. Four-run matrix

| Full experiment name | Peak / constant LR after warmup | beta | alpha for chosen NLL | Question |
|---|---:|---:|---:|---|
| G4F6P1--DPO01--00 | 5e-7 | 0.1 | 0 | Does the conservative preference-only recipe move behaviour? |
| G4F6P1--DPO01--01 | 2e-6 | 0.1 | 0 | Does a fourfold larger LR improve learning or create regressions? |
| G4F6P1--DPO01--02 | 5e-7 | 0.1 | 1 | Does the original chosen-answer SFT term help at low LR? |
| G4F6P1--DPO01--03 | 2e-6 | 0.1 | 1 | Does that term help when updates are stronger? |

Use the full name and settings in every result. Do not reintroduce opaque arm letters. The G/F/P SFT dataset identity remains unchanged.

These numbers define a useful initial bracket; they are not certified optima. alpha=1 is deliberately the older plan's proposed anchored setting, now tested rather than silently removed. beta=.1 is held fixed initially, not presumed correct.

Objective for every example:
- DPO term: standard sigmoid loss with SUMMED, completion-only policy/reference log probabilities, beta=.1.
- Chosen NLL: negative MEAN log probability over that example's chosen completion tokens, then mean over examples in the batch.
- Total: mean DPO + alpha * mean per-example chosen NLL.
- All reductions, EOS and masks are explicitly bound. A library's token-weighted batch mean is not silently interchangeable with per-example token means.
- alpha=0 means plain DPO, alpha=1 means this exact positive-likelihood term. It is not SFT replay on the full original SFT mix and does not guarantee capability retention.

Keep full-parameter FP32 persistent/master updates, BF16 forward compute, AdamW (.9,.99), weight decay 0, clip 1, effective batch 8 pairs, four GPUs × microbatch 1 × accumulation 2, no packing, 4,096 intact tokens, frozen identical G4F6P1 reference, seed 42 and the same epoch-specific permutations across arms. Cache exact frozen-reference log probabilities once and share only where input IDs/masks/template/reference match. Reinitialize weights AND optimizer states from the parent for each arm.

## 3. Exposure experiment and scheduler

Train each arm up to THREE epochs; save inference checkpoints after 1, 2 and 3. Log actual unique pairs, exposures and optimizer steps. With ~380 train pairs this is ~48, 96 and 144 steps, subject to correct partial-batch handling.

Use TWO optimizer steps of linear warmup to the target LR, then CONSTANT LR. This is an explicit change from the first plan's cosine schedule. Reason: the one-epoch checkpoint should be exactly the prefix of the two/three-epoch run. With a separately rescaled cosine schedule, a “one vs three epochs” comparison also changes every earlier learning rate.

This does NOT compare one-epoch-cosine against three-epoch-cosine. Report that limitation. Do not restart the scheduler or optimizer between epochs and do not perform a fresh training run for each epoch count.

Structural smoke tests are shared where the path is identical; test the alpha=1 reduction/masking as well as alpha=0. Each arm must show valid FP32 updates and finite logs. Stop an arm on NaNs/Infs, corrupt data/masks, unchanged trainable weights from a demonstrated optimizer failure, or budget exhaustion. Do not claim an infrastructure failure is a bad scientific setting.

Log total/DPO/chosen-NLL losses separately, chosen/rejected per-token and summed likelihood, margins, gradient norm, clipping frequency, update norm and throughput. Compare held-out DPO metrics only at a common beta; if beta changes later, raw loss values are not directly comparable.

## 4. Freeze a development screen before training

Keep the existing ~10% source-family preference holdout for fitting diagnostics. It is small, uses the same judge process and cannot by itself select the most helpful model.

For behavioural screening, partition EXISTING benchmarks before seeing any new model output:
- Greek IFEval: 150 of the 541 items, balanced over available instruction families as far as multi-label items allow.
- Greek MGSM: 50 of 250.
- MATH-500: 50 underlying problem IDs, evaluated in both Greek and English. Share IDs across languages.
- GreekMMLU: 100 from the existing clean subset, stratified by available subjects.
- Global-MMLU retention: 50 underlying question IDs per EL/EN/FR/DE/ES/IT/PT, shared across languages where available and stratified by subjects.
Total: 750 scored request instances per checkpoint, plus the preference holdout. These are reused existing test questions, not newly generated training requests.

Choose the screen by a deterministic seeded/hash ordering with recorded strata and largest-remainder quotas, seed 20260918. Freeze exact IDs, task/scorer versions, few-shot examples, prompts, chat templates and decoding in screen_manifest.json. Remainder items are withheld from THIS hyperparameter selection. They are not globally untouched benchmarks; historical inspection is a known limitation.

Run the baseline once or reuse hash/protocol-matched outputs. Run the same screen on all epoch checkpoints. Independent model inference on separate GPUs can overlap after memory qualification. Record empty/truncated output rates and lengths. Do not use the Greek IFBench checker on English outputs.

No judge calls or new simulations in this screen. These measurements cannot tell us whether a more formal, more verbose or more compliant answer is actually more useful. Do not claim they can.

## 5. Select finalists without testing every checkpoint on everything

Use one shared screen table with all 12 checkpoints plus baseline. Evaluate all checkpoints at matched exposure before interpreting LR or anchor effects; report the 2×2 comparison at each epoch, not only the best result.

Provisional screen rules:
1. Exclude numerical/structural failures.
2. Flag a checkpoint if it drops >=10 percentage points on GreekMMLU, either MATH language, MGSM, or the pooled Global-MMLU screen; also flag any individual language drop >=20 points. These deliberately coarse screening thresholds identify large losses in small samples; they are not non-inferiority guarantees.
3. Among unflagged checkpoints select the highest Greek IFEval prompt-strict score. Ties: higher macro-average retention accuracy across the named retention tasks/languages, then earlier epoch, then lower LR, then plain DPO. Explicit tie-breaks avoid post-hoc preference.
4. Select at most TWO finalists: the highest-ranked plain-DPO checkpoint and the highest-ranked anchored checkpoint, when those families have an unflagged candidate. Keep unchanged G4F6P1 in the comparison. If no candidate survives, retain the parent and report the screen; do not force a winner.
5. A Pareto/tradeoff table must accompany that mechanical shortlist. IFEval is a measurable screening criterion, not the project's entire goal.

For the finalists only, run the full available automatic battery using the existing protocols:
- Full Greek IFEval and MGSM.
- Full Greek IFBench (with known checker limitations disclosed).
- Full EL/EN MATH-500.
- Full clean GreekMMLU if the refreshed allocation estimate allows it; otherwise retain an explicitly named fixed 250-item diagnostic, including the 100 screen IDs and report the 150 non-screen IDs separately.
- Existing multilingual retention suite where already executable and affordable. At minimum use the old plan's 100 IDs per language, containing the 50 screen IDs, reporting non-screen results separately. Do not silently call a subset a full benchmark.

Report full historical-comparison scores AND scores on items withheld from this search. Do not choose another epoch after inspecting confirmation results and then reuse those same results as fresh confirmation.

Preserve the original richer behavioural evaluation goal: obtain fresh model outputs on already existing non-training assistance/dialogue/safety panels only where useful and compute-budgeted; preserve them for blinded inspection. Do not automatically call their LLM judges. If limited judge capacity becomes available, spend it on the parent versus these finalists, not on all 12 checkpoints. No call count or new paid annotation stage is authorized by this sentence. Without that review, “best automatic scores” is the strongest supported conclusion, not “best assistant”.

## 6. Conditional follow-up experiments

Do not automatically launch all follow-ups.

A. beta sensitivity (at most two additional runs, BEFORE final confirmation):
- If the development screen identifies a useful LR/objective region but shows a clear improvement/retention tradeoff or rapid saturation, run beta=.03 and beta=.3 at that selected LR/alpha, same parent, seed, batch, exposure checkpoints and schedule.
- Compare to its already computed beta=.1 trajectory. beta changes gradient scale as well as the reference-relative objective; do not describe larger beta as automatically producing smaller updates.
- This is sensitivity at one selected LR/alpha, not a joint beta/LR optimization.
- Freeze the final shortlist on development evidence before confirmation.

B. Training-seed repeat:
- If one recipe appears promising, repeat that selected LR/alpha/beta and selected exposure with seed 43, otherwise identical. Evaluate the same screen and report both seeds.
- Because the schedule is constant after the fixed warmup, a repeat trained to the selected epoch matches the corresponding trajectory prefix.
- Do not select whichever seed looks better. Two seeds expose gross instability but do not estimate variance precisely.

C. If all four trajectories are essentially unchanged through three epochs:
- Verify numerics/update scale and output identity before blaming the data.
- A single LR=5e-6 extension may be considered from the parent, using the better-supported objective and the same dev screen. It is a new recorded decision; do not silently expand to a grid.
- If training fit improves substantially but held-out outcomes do not, more LR is not the default answer. Label that pattern overfitting or weak transfer as appropriate.

A chosen-only SFT ablation can later isolate whether the preference penalty adds value if the anchored recipe wins. It is not necessary in the first four-run screen and is deliberately deferred.

## 7. Parallelism and forecast

Compute experiments do not require additional teacher calls. The expensive shared work should happen once: export, tokenization, reference cache, baseline generation/scoring, environment qualification and evaluation manifests.

Initially use one four-GH200 node for full-parameter training, sequential runs in a single suitable allocation to amortize startup. A second training node may run the other two trajectories if turnaround matters and the refreshed budget permits it; it reduces wall time, not node-hours. Do not try to fit four independent four-GPU training runs into one node. Evaluation can run one model per GPU where qualified; avoid overlapping inference with memory-saturating training on the same node. Bound queued successors and do not hold idle nodes while waiting for code or annotation.

Rough forecast, not measured DPO throughput:
- Shared setup/reference and four 3-epoch training trajectories: 3–6 node-hours.
- Baseline/candidate screening plus finalist automatic evaluation: 5–8 node-hours with compatible caches reused.
- Core total: 8–14 node-hours, or CHF21.52–37.66 at the recorded CHF2.69/nh.
- A beta pair and/or seed repeat adds approximately 2–5 node-hours depending on shared setup and evaluation breadth. Do not treat that as a fixed allowance for every follow-up.
- Full official GreekMMLU, uncached baselines, the broad native battery, failed infrastructure and extra behavioural generation can exceed this range; price those explicitly instead of claiming they fit automatically.

Inference: the compute is modest because only ~400 pairs are trained. Historical SFT throughput/startup are not direct DPO benchmarks; long un-packed pairs, reference handling and small batches can change throughput. After the first 10 production optimizer steps, update the remaining-time projection using actual lengths, measured step time, loading and checkpoint costs; do not change the scientific recipe based on timing.

The former five-node-hour suggestion no longer covers this comparison. The last observed local experiment ledger (CHF240 cap, CHF223.39 used) also does not cover the upper end. The owner's willingness to fund experiments is not a numeric cap update: Opus must reconcile current granted project funds, current experiment authority and concurrent commitments and record the actual run envelope before allocation. The CHF2,095.08 grant balance previously supplied by the owner is separate and may be stale. No cap is altered by this proposal. No new monitoring automation.

## 7b. Review checkpoints (owner, 18 September)

An independent reviewer (`data/rlhf/sol_review.py <ID>`, gpt-5.6-sol at xhigh, read-only) reviews the work at four points. Briefs and replies live in `docs/RLHF_COORDINATION/reviews/`.

| ID | When | What it must judge | Blocking? |
|---|---|---|---|
| R-DPO1 | Data frozen, before any allocation | The exported pairs: exclusions applied as decided (round 1, maths task), one pair per prompt, group split with no family across the boundary, text byte-identical to the judged samples, provenance complete | Yes for launching training: a data fault invalidates every arm |
| R-DPO2 | Trainer fixtures pass, before production | Objective and masking: completion-only summed log probabilities, only the latest assistant turn as target, frozen reference, the anchored term's reduction, FP32 update, no silent truncation | Yes for launching training |
| R-DPO3 | Screen manifest frozen, before scoring checkpoints | That the 750-item screen is frozen before any model output is seen, strata and IDs recorded, scorers and protocols unchanged, baseline reuse legitimately hash-matched | No: it gates interpretation, not the training already running |
| R-DPO4 | Results written, before any conclusion | That the report's claims follow from the paired evidence, flags are reported as flags, and no checkpoint was selected after seeing confirmation data | No, but a HOLD here blocks publishing a verdict |

Cycle rule (owner, 18 September): at most TWO cycles per checkpoint. A second cycle happens only if the first returned a blocking finding that was actually fixed; the reply records what changed. A third cycle needs a specific reason written down, not a reviewer's preference restated. Reviews do not pause work that is already running and cannot be invalidated by their outcome: training continues while a review of frozen data or a frozen manifest is in flight, and the finding is applied to what comes after.

## 8. Why this is a better first experiment

This design can distinguish:
- weak learning at the original LR from a stronger update that improves or regresses;
- beneficial longer exposure from overfitting across epochs;
- preference-only updates from preference plus chosen-answer likelihood;
- development fitting from generalization on withheld benchmark items.

It still cannot resolve label truth, broad real-user helpfulness, missing mathematical capability, missing production dialogue coverage, all beta/LR interactions, or publication readiness. Keep those in the limitations register. Limited statistical power and selecting among many checkpoints must be disclosed.

Useful primary sources, checked 18 September:
- Hugging Face's Zephyr full-DPO recipe currently lists LR5e-7 and beta=.01, demonstrating that even the familiar literature example is a recipe bundle rather than support for assuming beta=.1 is universally right: https://raw.githubusercontent.com/huggingface/alignment-handbook/main/recipes/zephyr-7b-beta/dpo/config_full.yaml
- TRL DPO implementation/format documentation: https://huggingface.co/docs/trl/dpo_trainer
- Iterative Reasoning Preference Optimization studies an added chosen NLL term in a different reasoning setting; it motivates a comparison, not a prediction of Greek assistant gains: https://arxiv.org/abs/2404.19733

## 9. Executor deliverables

Produce the frozen matrix, split/provenance and screen/confirmation manifests; exact per-arm loss definitions/configs; shared-reference receipt; all epoch-checkpoint identities; one comparison table with actual steps, exposures, timing, spend and metrics; a shortlist with explicit tradeoffs; and a limitations update. Do not hide failed or regressed variants. Keep model publication/default replacement separate from experiment completion.
