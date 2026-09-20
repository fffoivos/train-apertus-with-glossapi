# Greek Apertus 8B: SFT experiment plan

**Version 1.0 · 19 September 2026**

## Decision summary

Build a broader capability pool, calibrate the optimizer on that pool, and then separate four questions: **coverage, training exposure, task allocation, and Greek adaptation**. Test identity/style separately. Do not make the next experiment another continuation of a continually changing SFT checkpoint.

The primary target is a strong Greek-capable general assistant at a fixed inference budget, including precise instruction following, mathematics, practical and algorithmic coding, document work, coherent conversation, tool use, and appropriate safety boundaries. This plan targets the SFT foundation; it does not assume SFT alone will dominate every 8B leaderboard.

The supplied receipts describe R4. The owner reports that the subsequent round fixed its regression. Use the **latest recovered SFT model as the evaluation baseline**, not R4's unresolved regression. Start the main training comparisons from the **same chosen Greek CPT checkpoint**, with fresh optimizer state. Obtain the later run's configuration delta before launch.

**Evidence convention:** U1/U2 identify the supplied documents; R1–R19 identify research or official dataset documentation. All proposed percentages, token budgets, run orders, and promotion rules below are experimental design choices, not published optima for Greek Apertus.

## 1. Starting configuration and controls

The documented configuration is as follows. [U1, sections 2–3]

| Setting | Documented value | Initial decision |
|---|---|---|
| Parameters | Full-parameter 8B fine-tuning | Retain |
| Starting checkpoint | Greek Apertus CPT, uniform average of 18 checkpoints | Freeze exact revision and tokenizer |
| Learning rate | 1e-5 | Reference; compare 5e-6 and 2e-5 |
| Optimizer | Fused AdamW, beta2=0.99, weight decay=0 | Retain initially; beta1 and epsilon need the resolved config |
| Schedule | Cosine to 10% of peak, 3% warmup | Retain initially; later compare linear decay with matched endpoints |
| Gradient clipping | Global norm 1.0 | Retain after verifying normalization and logging |
| Precision | bf16 compute, fp32 master weights | Retain; verify optimizer-state precision |
| Context | 4,096, best-fit packing | Validate 8,192 for the expanded pool; 16K is a separate extension |
| Global batch | 16 packed sequences, about 65,536 token slots | Preserve this token batch when changing context |
| Hardware | 4 GH200, ZeRO-3, no offload | Retain unless subsequent setup changed |
| Accumulation | Microbatch 1 × 4 GPUs × 4 accumulation steps | At 8K, use accumulation 2 to preserve 65,536 slots |
| Loss | Assistant-only, precomputed masks | Retain; test labels, packing, and reduction end to end |
| Training exposure | One assembled pass; individual blocks repeated 1–4 times | Replace headline epoch count with tokens and per-root exposure |
| Seed | 42 | Screening seed; confirm finalists with two additional fixed seeds |

The earlier 1e-5 versus 5e-6 decision came from a 17,602-row Greek-only pilot. It is evidence for that setting, not proof that 5e-6 is inferior on a much larger, longer-answer mixture. [U1, section 2]

### Phase 0: implementation and data gate

Before expensive comparisons, verify a small deterministic batch through the actual training stack.

- Decode `input_ids` and labels after packing. Confirm all intended assistant tokens, endings, and mathematical solutions receive supervision; system/user/tool-result tokens do not, unless intentionally specified.
- Wrong assistant answers included as correction context must have zero positive-target loss. Keep intentionally negative examples separate from correct SFT targets.
- Confirm independent packed conversations cannot attend across boundaries; resetting position IDs alone does not establish attention isolation. Preserve attention across turns of the same conversation.
- Compare an equivalent logical batch with and without accumulation. For token-weighted training, normalize summed supervised-token losses across the logical update, including distributed reduction, rather than averaging separately normalized microbatch losses. This class of implementation error is documented by Hugging Face. [R5]
- Log pre-clipping global gradient norm, clipping fraction, supervised-token count, processed-token count, actual learning rate, optimizer updates, and source/task/language contributions.
- Reconcile the recipe's 3% warmup setting with its statement that the learning rate reaches its peak around 6% of the epoch. This could be sparse logging or different clocks; do not call it a bug without inspecting the trace. [U1, sections 2–3]

**Gate:** do not interpret mixture or optimizer results until these tests pass. The historical initial norm near 260 is a reason to inspect scaling, not a reason by itself to increase clipping. [U1, section 2]

## 2. Build the dataset pool

Maintain two versioned pools:

**Old:** the audited descendants of the existing blocks, incorporating the fixes that produced the recovered model. Do not deliberately reintroduce known bad targets.

**Expanded:** the old pool plus the selected sources below, after cross-source deduplication and quality checks. Aim initially for hundreds of thousands of distinct root tasks; use actual measured coverage rather than a headline row target as the launch criterion. A reservoir can be larger than any one experiment consumes.

### Capability allocation

All weights are shares of **supervised tokens**. Greek replaces foreign-language examples within a capability rather than being appended as another task.

| Capability | Balanced | Reasoning-heavy | Assistant-heavy | Greek share inside balanced mixture, in percentage points of total |
|---|---:|---:|---:|---:|
| Mathematics | 30% | 40% | 20% | 3.0 |
| Code | 25% | 30% | 20% | 1.5 |
| Precise instruction following | 15% | 10% | 20% | 3.0 |
| General assistance and conversation | 12% | 7% | 20% | 3.0 |
| Documents, grounded QA, rewriting, tables | 8% | 5% | 10% | 2.5 |
| Science and general reasoning | 5% | 3% | 5% | 1.0 |
| Tool use | 3% | 3% | 3% | 0.5 |
| Safety and uncertainty | 2% | 2% | 2% | 0.5 |
| Total | 100% | 100% | 100% | 15.0 |

The 15 Greek percentage points are an initial dose, not an estimate of the optimum. For the first task-allocation comparison, hold these absolute points fixed across mixtures so that changing math/code allocation does not also change the aggregate Greek dose. Report the resulting within-task Greek fractions.

A Greek-prompt coding example contains code tokens. Count it as a Greek-task example for the allocation, but separately report actual natural-language output and unintended language switches; do not call every code token a Greek-language token.

At 600M supervised tokens, the balanced allocation gives math 180M, code 150M, IF 90M, chat 72M, documents 48M, science 30M, tools 18M, and safety 12M. Greek-task supervision totals 90M within those amounts.

### Source selection

| Capability | Main sources to compile | Inclusion and coverage requirements |
|---|---|---|
| Mathematics | `nvidia/OpenMathInstruct-2`; selected `AI-MO/NuminaMath-1.5`; a controlled `open-r1/OpenR1-Math-220k` subset | Prefer expanded problem coverage; retain arithmetic/algebra as well as harder topics. Use complete, checked solutions and label verification strength. [R9–R11] |
| Coding | `nvidia/OpenCodeInstruct`; selected `nvidia/OpenCodeReasoning-2`; `OpenCoder-LLM/opc-sft-stage2`, especially practical/package tasks | Select passing positive targets, independently strengthen tests on a sample, and include practical coding, debugging, tests, SQL, and JS/TS rather than only contest Python. [R12–R14] |
| IF | Existing verified Greek IF; Tulu 3 Personas IF; Smoltalk2 multi-turn IF; selected Dolci precise IF | Cover output constraints and content correctness, standing instructions, revocation, and accumulated edits. Deduplicate related source families. [R15–R17] |
| Chat | Curated existing Nemotron; selected Dolci and Smoltalk2 SFT components | Classify by actual task. Math inside chat counts toward math. Retain varied answer lengths and natural multi-turn exchanges. [U1; R15–R16] |
| Documents | Smoltalk2 rewrite/summarization/table subsets; existing Greek rewrite; new source-grounded Greek tasks | Preserve the supplied evidence, include unanswerable questions, and reject unsupported additions. Longer-context sources enter only the long-context branch. [R15] |
| Science/reasoning | Selected Dolci science/reasoning; existing brute-force-checked puzzles | Separate factual knowledge, explicit derivation, and answer-only formatting. Avoid importing purported answers without checks. [U2; R16] |
| Tools | Selected Dolci and Smoltalk2 tool examples | Normalize to the deployed Apertus interface. Include no-call, missing-argument, tool-error, and tool-result-use cases. [R15–R16] |
| Safety/uncertainty | Selected Dolci components and audited Greek examples | Balance harmful-request handling with helpful responses to benign requests; measure over-refusal and unsupported certainty. [R16] |

A provisional internal coding balance is 40% algorithmic, 35% practical programming, and 25% debugging/testing/modification. These are selection quotas to test, not a claim that the named sources supply each category in those proportions.

OpenR1 stores multiple solutions and guarantees at least one verified answer per retained problem—not universal correctness of every trajectory. OpenCodeInstruct provides execution-status fields, but generated tests can also be wrong or incomplete. Preserve uncertainty labels rather than equating a dataset brand with verified correctness. [R11–R12]

### Root-level bookkeeping

For every example record: source and revision, upstream source, root problem/conversation ID, solution variant ID, translation parent, teacher and target style, primary task and secondary tags, input/output languages, natural-language versus code spans, lengths, exact loss-mask counts, verification status, license, and train/dev/test assignment.

Link shared conversation prefixes and derived follow-ups. A repeated context is repeated supervision if its assistant tokens receive loss; physical row counts alone will miss this.

Separate four quantities: distinct tasks, alternative targets, target lengths, and repeated exposure. Approximate exposure is `N × K × L × E`, but log actual masked tokens. For token shares implemented through whole-example sampling, account for expected target length; choosing 30% of rows from math does not guarantee 30% of supervised tokens. Prefer compiling explicit per-bucket token quotas and then shuffling the manifest.

Split and decontaminate by root across translations and solution variants. Aggregate collections such as Dolci and Smoltalk overlap their component datasets. Keep evaluation problems out even when translated or paraphrased. [R15–R16]

Preserve source-level licensing. The supplied recipe flags `no_robots` as non-commercial; the final inclusion decision needs the intended release constraints rather than a blanket assumption that every public dataset is interchangeable. [U1, section 1]

## 3. Combine the Greek datasets by function

| Existing Greek block | Proposed treatment |
|---|---|
| `greek_if` | Retain verified native constraints; audit semantic correctness and impossible/ambiguous constraint combinations. |
| `greek_math_v2` | Retain corrected worked solutions; add Greek versions of newly covered methods, without a universal 100–250-word rule. |
| `greek_ours` | Language-audit and reclassify by actual task. Separate translation from changes to factual/local context. |
| `convskills_v2` | Route into multi-turn IF/chat; group shared prefixes and exclude defective assistant targets. Do not restore discarded lanes without a new audit. |
| `greek_rewrite` | Retain transformations of supplied text, then expand with grounded extraction/QA over suitable real source documents. |
| `personality` and overlays | Split identity/capabilities, style/register, factual material, and safety/uncertainty. Test identity/style separately rather than treating the whole block as one behavioural intervention. |
| Missing Greek code/tool coverage | Translate natural-language requests/explanations while preserving code, schemas, tests, and computational semantics; re-run checkers. |

The existing process and its limits are documented in U2. In particular, constraint checking does not prove answer quality, math has recorded solver disagreements, and conversation prefixes can amplify a defective answer. [U2, part one]

Do not meet a Greek percentage by repeating the same small subset indefinitely. Report effective exposures per root and per block. When the intended dose exceeds the available diversity, either acquire verified new Greek examples or declare the experiment to be a repetition test. A language-dose study must not silently change both language and unique-problem coverage.

### Expected transfer

The hypothesis is that foreign-language mathematics and code teach partly transferable procedures, while Greek examples help the model interpret Greek requests and express its answers reliably. Cross-lingual instruction-tuning and MathOctopus studies support meaningful transfer and benefits from multilingual additions, but do not establish a universal Greek activation threshold or dose. [R7–R8]

Choose English, Chinese, or other-language data for checked quality and useful coverage. A teacher's country or name does not establish its output language. Keep high-quality foreign traces intact unless translation passes verification. Greek-specific morphology, register, punctuation constraints, and local factual content are separate needs.

## 4. Experiment catalogue and execution order

All token budgets below refer to supervised tokens. Log processed tokens and compute separately. Unless specified otherwise, use the same frozen CPT checkpoint, fresh optimizer, task manifest, seed, template, and evaluation protocol. Reuse an existing run only when these controls really match.

### H: optimizer calibration on the new pool — required

Run the balanced expanded pool at 150M tokens and the initial 15% Greek dose, with no dedicated identity/style block.

| ID | Peak LR | Processed-token slots/update | beta2 |
|---|---:|---:|---:|
| H0 | 1e-5 | 65,536 | 0.99 |
| H1 | 5e-6 | 65,536 | 0.99 |
| H2 | 2e-5 | 65,536 | 0.99 |

Keep the documented cosine schedule, warmup, clipping, and weight decay. Select by generated task results plus retention, using validation loss as a diagnostic. If H2 wins and remains stable, a 3e-5 extension is optional; do not jump to a much higher published rate without evidence.

Use the winner for the initial data comparisons. Confirm the leading configuration at 600M before treating a 150M ranking as permanent. If the learning-rate ordering changes with scale, retain a two-rate bracket for the remaining medium-scale comparisons.

### D: old versus expanded pool × training amount — required

| ID | Pool | Budget | Purpose |
|---|---|---:|---|
| D0 | Audited old | 150M | Reweighted old-pool baseline |
| D1 | Audited old | 600M | More exposure to existing coverage |
| D2 | Expanded | 150M | New-pool benefit at the small budget |
| D3 | Expanded | 600M | New-pool benefit at the larger budget |

Use the same balanced task proportions and aggregate Greek dose. D2 can be the matching H winner. D0 is not a reproduction of the original R4 proportions.

Freeze a **common Greek capability pool** across all D arms. Where the old material lacks a required bucket, such as Greek tool use or practical coding, add the same validated Greek examples to both pools. Label the control “old sources plus common Greek pool,” not a historical reproduction. This keeps new Greek coverage from being silently confounded with foreign-source expansion.

D0→D1 measures more training on the same reservoir; D0→D2 and D1→D3 measure the expanded data package at matched exposure. New sources also change teacher/style/quality, so call the result a **pool effect**, not a pure proof about unique-problem counts. Confirm a close pool comparison at a second learning rate rather than assuming one pool's optimizer optimum is universal.

To isolate breadth further, compare a small nested subset of the expanded pool repeated more often against a larger subset repeated less often, with matched task/difficulty/length distributions and mathematical/code token budgets.

### M: task allocation — required

At 600M, compare balanced, reasoning-heavy, and assistant-heavy weights using the same expanded reservoir. Hold Greek percentage points, source selection rules within each task, and optimizer settings fixed. Reuse D3 as the balanced arm when all settings match.

Promote a trade-off that improves priority capabilities without unacceptable Greek IF, safety, language-quality, or completion regressions. Do not collapse everything into a single score that hides a large loss in one required capability.

### G: Greek transfer — required before finalization

Construct a matched, translation-eligible task pool. Run G0, G15, and G30 with approximately 0%, 15%, and 30% Greek-task supervision at the same budget and task weights.

For this specific language experiment, keep Greek-only constraint families out of **all three arms**; otherwise their presence changes task coverage as well as language. Their contribution is tested separately below. Use equivalent Greek and foreign versions of the same root tasks wherever feasible; do not append extra Greek problems to one arm.

It is not possible to guarantee identical root exposures, identical token budgets, and identical text lengths when tokenization changes. Predeclare root/exposure matching as primary, keep token totals close, and report the residual; then confirm finalists under the deployment-relevant compute budget. Do not pad responses to create artificial equality.

Evaluate paired English/Greek tasks, native Greek requests, code correctness, output language, and Greek naturalness. G15 in this matched pool is a new control, not automatically interchangeable with an earlier 15%-Greek run using different native tasks.

Interpretations: English and Greek improving together supports transfer; English improving without Greek suggests an interface/transfer bottleneck; Greek IF improving but math staying flat shows that language compliance alone did not improve mathematical solving.

### P: custom Greek package × identity/style — required as a controlled ablation

At the selected Greek dose, compare the following. Preserve total task/language budgets by replacing omitted content rather than simply shortening training.

| ID | Greek capability slots | Identity/style slots |
|---|---|---|
| P00 | Matched independently translated/native control material | Neutral Greek control examples |
| P10 | Your audited custom Greek material | Neutral Greek control examples |
| P01 | Matched independently translated/native control material | Audited identity/style package |
| P11 | Your audited custom Greek material | Audited identity/style package |

The custom package includes native IF, conversation skills, adaptations, math, and rewrite tasks, classified separately. This tests the package as produced; it does not prove that Greek itself causes the difference. Follow a negative package result with leave-one-block-out tests rather than discarding all Greek data.

Define the initial personality dose as **four exposures of the audited identity/style subset**, reflecting the earlier experiment, and measure its actual tokens after separating facts/safety. Do not preserve a 1% percentage blindly as the total run grows tenfold. An additional doubled-dose comparison is optional. Keep the same truthful identity system prompt across arms.

A lower-cost screen can branch P arms from the same capability checkpoint for an equal 50M-token tail, with identical optimizer-reset policy and capability replay. That answers a late-adaptation question. Confirm the winning policy in a full-from-CPT run before using it as the full-recipe conclusion.

### S: scale finalists — required only after gates

Train the winning recipe at 1.5B supervised tokens; extend to 3B only when curves, diversity, and retention justify it. Save checkpoints by token milestones as well as update numbers. A longer run's unannealed midpoint is not equivalent to a completed shorter run.

Track exposure distributions per source, root, translation, and solution. Try fresh tasks, more distinct solutions, and additional repetitions as separate interventions. Validate with two additional seeds on the leading comparison rather than running every early arm with three seeds.

### Optional targeted branches

**B — batch:** after H, compare 32,768 / 65,536 / 262,144 processed-token slots per update, retuning LR locally as needed. Consider the beta2 time-scale protocol in section 5; do not conclude that bigger is better from published example counts.

**R — reasoning targets:** on a fixed 5K–10K problem set and one teacher, compare ordinary complete derivations with explicit non-obvious method choices and checks. Match lengths approximately. Test 1 solution, multiple distinct solutions, and repeated identical solutions in a separate comparison.

**L — longer context:** first test 8K versus 16K on the same eligible examples to validate implementation/retention. Then compare the actual package that includes previously excluded long solutions/documents. Do not attribute the latter's gain to context length alone.

**O — optimizer/schedule:** compare cosine with linear decay at matched peak, warmup and final LR; separately test AdEMAMix against an AdamW control with separately tuned LR and stated moment settings.

**C — ordering:** compare shuffled training with reasoning-emphasized early ordering and later assistant/Greek emphasis, using the same overall task/language token multiset and schedule. This is not an easy-to-hard prerequisite curriculum. Retain broad examples throughout rather than end in a personality-only phase.

**BASE — CPT diagnostic:** apply a fixed capability pilot to original Apertus and the selected Greek-CPT checkpoint, using their correct tokenizer/head configurations. This tests the starting capability package; if tokenizers differ, report the comparison as such. Do not conflate it with the already-completed averaged-versus-terminal checkpoint test.

## 5. Hyperparameters: what the literature supports

### Published recipes differ substantially

| Reference | Relevant reported setup | Implication for this project |
|---|---|---|
| Apertus v1, SFT [R1] | 8B: LR 5e-6, reported global batch 512, 4K context, linear decay; AdEMAMix beta1=.9, beta2=.999, beta3=.99, alpha=8, schedules for alpha/beta3 across training | A direct-family optimizer/schedule comparator exists; it is not the same as the documented AdamW/cosine recipe. |
| Tulu 3, 8B SFT [R2] | LR 5e-6, reported batch 128, 4K, linear decay, 3% warmup, two epochs | Supports a lower-rate and multi-pass control, not a guaranteed optimum. |
| OpenThoughts [R3] | Large-data configuration: LR 8e-5, batch 512, five epochs, packing | Strong reasoning-distillation recipes can use very different settings; do not transplant the LR into a different batch/model/objective. |
| AceReason-Nemotron 1.1 [R4] | Long-reasoning SFT continued improving through roughly five epochs, plateauing around five to six | One pass is not a universal stopping rule. |
| Small Batch Size Training for Language Models [R6] | Properly tuned small batches were competitive, including a Gemma 3 4B MATH fine-tuning experiment; beta2 was adjusted for token half-life | Test both smaller and larger batches; batch and moment memory interact. |
| Post-Training Science for SFT, September 2026 [R18] | In specialized customer-task experiments, later epochs could retain task scores while eroding general IF; loss and task-score trends diverged | Select exposure using capabilities and retention, not loss alone. Scope differs from a broad Greek assistant mixture. |

The reported example/sequence batches are not automatically comparable with your packed 65K-token batch. Padding, packing, answer lengths, and masks change the number of useful targets per update.

### Batch implementation on the documented four GPUs

Assuming microbatch 1 and 8,192-token packed sequences:

| Accumulation steps | Global packed sequences | Token slots/update |
|---:|---:|---:|
| 1 | 4 | 32,768 |
| 2 | 8 | 65,536 |
| 8 | 32 | 262,144 |

Actual non-padding tokens may be lower. At 16K, accumulation 1 gives the old 65,536-slot budget. Changing context while retaining the old accumulation blindly changes batch and number of optimizer steps.

### beta2 is a time-scale, not merely a default

Adam's beta2 controls smoothing of squared gradients. Keeping it fixed while changing tokens per optimizer update changes the amount of training history represented by that smoothing.

A literature-supported heuristic preserves the token half-life using:

`beta2_new = beta2_old ** (B_new / B_old)`

Starting with beta2=.99 at 65,536 slots, this gives approximately .994987 at 32,768 and .960596 at 262,144. This is a testable scaling protocol, not a claim that either value is optimal for Apertus. It approximates comparable supervised-token history only when supervised fractions are similar. [R6]

Either keep beta2=.99 for a pure fixed-hyperparameter batch comparison, or use the stated half-life-preserving protocol and label the comparison accordingly. To understand a promising change, add the corresponding fixed-beta control. Keep beta1 and epsilon fixed while testing this; obtain their actual values from the config.

### Settings to retain and settings to defer

Keep weight decay 0, clipping 1, bf16/fp32-master precision, and full updates for the first comparison. Do not add dropout, LoRA, Muon, or several optimizer changes to the main mixture sweep.

AdEMAMix is a useful optional comparator because it was used for Apertus SFT, but it needs its own LR comparison and schedule specification. A control with AdamW beta2=.999 helps separate the added slow momentum from a beta2 change. Treat copying all published settings as a recipe comparison, not a one-variable optimizer ablation.

The September 2026 optimizer study also reports a Muon comparison, but its narrow tasks and limited downstream probes are insufficient reason to replace your working optimizer before data/coverage experiments. [R18]

Warmup 3% is a reasonable control supported by Tulu 3. If early instability persists after correcting normalization, compare a longer warmup separately. Linear versus cosine is a later controlled ablation; the old constant-rate comparison was confounded by seed. [U1, section 2; R2]

## 6. Evaluation and promotion

Freeze evaluation before source expansion. Use development suites for repeated decisions and independent final tests for finalists.

| Axis | Required measurements |
|---|---|
| Greek/English mathematics | Single-attempt correctness on easy and difficult tasks, paired-language outcomes, extraction success, truncation, looping, token cost; pass@k only as a separate diagnostic |
| Code | Algorithmic tasks plus practical/library tasks; executable unit tests, edge cases, bug repair, and SQL/JS/TS coverage; Greek/English requests sharing code tests |
| IF | Strict checkable constraints, native Greek-only constraints, multi-turn persistence/revocation, content correctness |
| Grounded work | Faithfulness, answerability, extraction accuracy, unsupported additions, long-context performance |
| Conversation/language | Blind native Greek review, useful brevity/detail, language switching, revisions, resistance to incorrect user corrections |
| Identity/safety/tools | Correct identity/capability statements, over-refusal, harmful-request handling, valid tool syntax and arguments, use of tool results |

EvalPlus and BigCodeBench are candidates for the coding suite, representing strengthened code tests and practical coding evaluation respectively. Add your deployment-specific tasks rather than relying on either alone. [R19]

Keep task instructions, correct per-model templates, tool access, generation limits, stop tokens, and extraction consistent. Evaluate base and instruct comparators under suitable formats rather than forcing incompatible formatting.

Use paired comparisons on the same tasks and cluster uncertainty by root, keeping translations together. Repeat finalists across seeds. Small differences on a few hundred questions are not conclusive merely because one run has a higher percentage; do not reuse the original pilot's fixed noise band as a universal bound.

Set minimum acceptable retention before launch. A possible starting policy is a practical improvement on priority math/code/IF measures with no greater than a predeclared small loss on other required axes, followed by a larger confirmation suite when uncertainty overlaps the margin. Choose the actual margins from baseline variability and deployment requirements, not from this document by fiat.

A model with better training loss but worse generated answers or Greek IF does not advance. A model with slightly worse reference loss but better checked solutions can advance when retention also passes.

## 7. What is still needed from the setup

| Requested item | Why it affects decisions |
|---|---|
| Latest recovered-run receipt, model revision, config, and change log versus R4 | Preserves the fixes and establishes the real baseline; not another investigation of an already-fixed regression |
| Resolved trainer and DeepSpeed configs, launch command, code commit, exact tokenizer and embedding/head revisions, beta1/epsilon, optimizer-state precision, attention kernel/checkpointing settings | Settles batch, scheduler clock, optimizer semantics and 8K/16K feasibility |
| Small post-collation tokenized batch with input IDs, labels, attention/sequence boundaries and position IDs | Audits actual masking, accumulation normalization and packing rather than intent |
| Machine-generated per-source/task/language token and root statistics, exposure histogram, and 4K/8K/16K length coverage | Converts proposed weights into achievable doses and shows whether expansion supplies new coverage |
| Per-item evaluation outputs for the recovered model, plus prompts, templates, generation/stop settings, extraction and code test harness | Establishes meaningful effects, error patterns and fair comparisons |
| Total available GPU allocation, observed throughput/peak memory at candidate lengths, inference budgets, desired tool/reasoning interface, and release constraints | Determines how many arms to run, the cost of long trajectories, and which sources can ship |

Already supplied: four GH200s, ZeRO-3, full updates, 4K/65K-token-batch recipe, corrected mask path, LR/beta2/weight-decay/clipping settings. These need not be rediscovered; the missing item is the current resolved state and any later changes.

## 8. Practical launch order

**Start:** implementation/data gate → H0/H1/H2 → D0/D1/D3, reusing the matching H winner as D2 → the two alternative M arms.

This is **eight distinct screening/comparison runs before optional batch tests**, with reuse only when controls match. It is not a mandate to finish all eight if an early gate fails. The initial H runs and D0 use 150M, while D1/D3/M use 600M.

**Then:** Greek transfer → custom-package/personality ablation, using equal-tail screening when necessary → full-run confirmation → 1.5B finalist → 3B only with evidence.

The optional batch, target-style, longer-context, optimizer and ordering experiments should be triggered by the observed bottleneck or available compute. Do not run their full cross-product.

The most useful immediate evidence bundle is the **latest resolved training configuration, one actual packed batch, and per-item outputs from the recovered model**. That would allow the provisional plan to become a launch-ready set of configurations.

## Sources

### Supplied project documents

- **U1.** `SFT_RECIPE_SHAREABLE_20260918(2).html`, “The Greek Apertus: how we did supervised fine-tuning.” R4 receipts, especially sections 1–3 and the evaluation caveats. The later recovery is reported by the owner in the conversation, not recorded in this attachment.
- **U2.** `SFT_DATASET_EXAMPLES_20260918(1).html`, “What is in the training mixture, and how the Greek parts were made.” Sampled rows and source-generation limitations.

### Primary research and official documentation

- **R1.** [Apertus v1 technical report, section 4.2](https://arxiv.org/html/2509.14233v1).
- **R2.** [Tulu 3, SFT hyperparameters and training analysis](https://arxiv.org/html/2411.15124v1).
- **R3.** [OpenThoughts: Data Recipes for Reasoning Models](https://arxiv.org/html/2506.04178v1).
- **R4.** [AceReason-Nemotron 1.1](https://arxiv.org/html/2506.13284v1).
- **R5.** [Hugging Face: Fixing Gradient Accumulation](https://huggingface.co/blog/gradient_accumulation).
- **R6.** [Small Batch Size Training for Language Models](https://arxiv.org/html/2507.07101v1).
- **R7.** [Multilingual Instruction Tuning With Just a Pinch of Multilinguality](https://aclanthology.org/2024.findings-acl.136/).
- **R8.** [Breaking Language Barriers in Multilingual Mathematical Reasoning / MathOctopus](https://aclanthology.org/2024.findings-emnlp.411/).
- **R9.** [OpenMathInstruct-2 dataset card](https://huggingface.co/datasets/nvidia/OpenMathInstruct-2).
- **R10.** [NuminaMath-1.5 dataset card](https://huggingface.co/datasets/AI-MO/NuminaMath-1.5).
- **R11.** [OpenR1-Math-220k dataset card](https://huggingface.co/datasets/open-r1/OpenR1-Math-220k).
- **R12.** [OpenCodeInstruct dataset card](https://huggingface.co/datasets/nvidia/OpenCodeInstruct).
- **R13.** [OpenCodeReasoning-2 dataset card](https://huggingface.co/datasets/nvidia/OpenCodeReasoning-2).
- **R14.** [OpenCoder SFT stage 2 dataset card](https://huggingface.co/datasets/OpenCoder-LLM/opc-sft-stage2).
- **R15.** [Smoltalk2 dataset card](https://huggingface.co/datasets/HuggingFaceTB/smoltalk2).
- **R16.** [Dolci-Instruct-SFT dataset card](https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT).
- **R17.** [Tulu 3 Personas instruction-following dataset card](https://huggingface.co/datasets/allenai/tulu-3-sft-personas-instruction-following).
- **R18.** [Post-Training Science for Supervised Fine-Tuning, September 2026 preprint](https://arxiv.org/html/2609.01244v1).
- **R19.** [EvalPlus project](https://evalplus.github.io/) and [BigCodeBench project](https://bigcode-bench.github.io/).
