# SFT v2: recommended path, version 2

19 September 2026. Replaces `SFT_V2_RECOMMENDED_PATH_20260919.md` (kept unchanged as the record) after an external review of that document. Evidence: `SFT_V2_PLAN_RESEARCH_20260919.md` and `docs/lit/sft_v2_research_20260919/`. Owner's standing instructions for this campaign (19 Sept): no budget cap, spend is tracked for efficiency; use the data mix that is best for the experiment; aim for parallel execution that finishes in 24–48 hours. Nothing here is launched; launch needs the owner's go.

## 0. Disposition of the review

Adopted (the review was right and version 1 was wrong or loose):

| # | Review point | What changes |
|---|---|---|
| 1 | "One million examples" is not "one million distinct problems"; OpenMathInstruct-2's scale points count question–solution pairs, trained for two epochs at constant 2e-5 with weight decay 0.01 | The ladder is in **distinct roots actually available after deduplication and reserve**, with solutions and tokens stated separately. One pass is a working hypothesis with a repetition control, not a rule. ≈1B is a candidate size that the inventory confirms or corrects |
| 2 | Greek maths: two exposures give 8.4M tokens = 2.5% of a 330M block, not 5% | My error. The Greek maths rule becomes absolute: all ≈15k problems, two exposures (≈2.5%). Whether that is enough is what experiment G-maths measures |
| 3 | Personality: four exposures are ≈1.5M tokens, not 10M | My error. Keep the incumbent's dose (four exposures ≈1.5M). At ≈1B that is 0.15% of the mix, against ≈1% when it last imprinted, so dilution is a named risk tested in P, with a late identity pass as the fallback (that is how the incumbent got its identity) |
| 4 | Allocations must come from a measured inventory | Stage 0 deliverable: per block, unique roots → selected solutions → unique supervised tokens (our tokenizer) → exposures → final tokens. Percentages in §1 are procurement targets until then |
| 5 | "Under 20 means the base is the ceiling" does not follow | Replaced by a plateau rule plus a base comparison (§2, stage 2). The maths share is decided by stage 3, never by one score |
| 6 | The multiplicity comparison changes problems and solutions together | Added the control on the same 75k roots: one solution repeated four times vs four different solutions |
| 7 | Greek package and personality questions had dropped out | Restored as stage 3b, in a form that needs no new Greek data |
| 8 | Report correctness, language compliance, and both jointly; a numeric or code-only answer is not a language failure | Adopted as the metric definition |
| 9 | Bridge arm for the optimiser stage; resolved β2 and full recipe per arm; keep the runner-up | Adopted, with my own choice on β2 below |
| 10 | 4,096 is the validated operating limit, not a proven ceiling; report what the length filter removes | Adopted. One length rule only: the rendered row must fit 4,096 tokens with our tokenizer |
| 11 | Gates: gradient/update equivalence, packing boundaries, labels and end-of-turn supervision, resume equivalence; a development split; every comparison from the same CPT checkpoint; full allocation tables per arm | Adopted |
| 12 | Python-only code stated plainly; tests must have run and be non-empty; NuminaMath "math-word-problem" is not grade-school; the 50–300 per-constraint figure is an RL result; "SFT does not move IFBench" and "near-certain" were overclaims | Adopted; wording fixed in §1 and §3 |
| 13 | Measure throughput on the new mix; screen RL prompts on a stratified sample first | Adopted |

Adopted with a change, or not adopted:

- **β2.** Version 1 rescaled β2 by the half-life rule, which gives 0.99^8 ≈ 0.923 at the large batch. At 300M tokens a 524k-token batch is only ≈900 updates; a 13-update memory for the second moment is a second, aggressive change riding on the batch comparison. Decision: **β2 fixed at 0.99 in every arm**; the rescaled value is the confirmation run only if a large-batch arm wins.
- **Optimiser stage at 300M, not 150M.** At 150M a large-batch arm gets ≈440 updates and ≈13 warmup steps, which handicaps exactly the arms we want to learn about.
- **"Compare our Greek package against independent matched Greek material."** No such material exists and there is no LLM budget to make it. Replaced by two tests that use what we hold: a matched language swap (our Greek maths and adapted rows are translations, so exact English parallels exist for the same roots) and leave-one-block-out.
- **Size.** I keep ≈1B as the expected target: it is what one pass over the pool plausibly yields under these shares, and maths needs far more than the 17M it had. The inventory decides the final number.

## 1. Target run (procurement targets until the stage-0 inventory)

One assembled pass from the CPT base (`fffoivos/apertus-8b-greek-cpt`, revision `18-avg-uniform5-tokens30B-50B`), fresh optimiser, 4,096 context.

| Block | Target share | Contents and conditions |
|---|---:|---|
| Mathematics | ≈33% | Distinct roots first. OpenMathInstruct-2 roots left after the reserve (≈520k of 607k; its grade-school share raised to ≈35% using its own `gsm8k`/`augmented_gsm8k` source labels); NuminaMath-1.5 numeric-answer problems with validity flags on (≈150k; this category is not "grade-school"); ScaleQuest (≈1M synthetic questions from 7B teachers: used for question diversity, amount set by stage 2); DART-Math-Hard adds **solutions, not roots**, and is used only where k > 1; GSM8K and MATH train; all ≈15k Greek problems ×2 (≈2.5% of the block) |
| Code | ≈15% | OpenCodeInstruct rows whose tests ran, were non-empty and all passed, plus top judge scores; OpenCoder educational and package; OpenCodeReasoning-2 code-only solutions (treated as code supervision, `split != test`). **Stated scope: ≈97% Python.** A non-Python slice enters only if the owner clears McEval's share-alike licence |
| Instruction following | ≈13% | Breadth-first (research §4). "Family" = one constraint type. Per-family depth starts from a modest cap and is a tunable, not a rule (the 50–300 figure comes from RL experiments) |
| Chat and multi-turn | ≈21% | Dolci chat; Nemotron chat filtered for empty user turns and foreign identity strings; our conversation suite v2 and Greek chat |
| Science and reasoning / documents / tools / safety | ≈7 / 5 / 3 / 2% | As in version 1 |
| Identity and personality | four exposures (≈1.5M tokens) | Split in the manifest into identity, style, factual, safety |

Greek in total: every Greek block at two exposures ≈ 63M tokens from ≈31M unique (to be re-measured), ≈6% at 1B.

## 2. Campaign

All comparison runs start from the same CPT checkpoint with a fresh optimiser unless a run is explicitly a continuation. "Feeds the next stage" means findings, not weights. Selection uses the development split only; TEST is opened for finalists.

**Stage 0 — inventory and gates (no training beyond minutes).**
1. Inventory table per block (unique roots → solutions → unique tokens → exposures → final tokens), with what the 4,096 rule removes per capability and difficulty band.
2. Four-way split by root, defined by problem text: SFT-train / development / RL pool / never-train TEST. Reserve sizes as in research §5.
3. Decontamination of the assembled pool against every benchmark in use, Greek and English.
4. Trainer gates: (a) loss — summed per-token loss vs the trainer's; (b) **update equivalence** — same logical batch with and without accumulation and across 1 vs N GPUs/nodes gives the same gradient within tolerance; (c) packed sequences cannot attend across conversation boundaries; (d) decoded labels cover assistant tokens and end-of-turn, nothing else; (e) **resume equivalence** — interrupted-and-resumed vs uninterrupted short run: optimiser state, scheduler position, data cursor, token counters, parameters.
5. Multi-node data-parallel launch for the trainer (needed for the wall-clock target, §4), then an independent code review before any production run.
6. Throughput measured on the new mix; battery gains a code evaluation (HumanEval+/MBPP+ plus our own debugging, library-use and modification items with matched Greek requests, run sandboxed without network or credentials) and the three language metrics.
7. Parameter table for every arm: optimiser, β1/β2/ε, weight decay, schedule, warmup, clipping, batch, LR; against 1-G4F6P1 and against Apertus's own SFT recipe.

**Stage 1 — optimiser recipes (4 runs × 300M, balanced mix).**
| arm | tokens/update | peak LR | β2 | other |
|---|---:|---:|---:|---|
| small-batch reference | 65k | 1e-5 | 0.99 | cosine to 10%, warmup 3%, wd 0, clip 1.0 (as all previous rounds) |
| large-batch, lower LR | 524k | 5e-6 | 0.99 | same |
| large-batch, bridge | 524k | 1e-5 | 0.99 | same |
| large-batch, higher LR | 524k | 2e-5 | 0.99 | same |
These are candidate recipes, not reproductions of published ones. Winner by development-set task results with retention as a constraint; the runner-up is kept if close and re-checked in stage 4. Checkpoint averaging is evaluated here: final checkpoint vs one predeclared window (last four of six equally spaced), on development data.

**Stage 2 — mathematics: scale, multiplicity, base (7 runs; maths blocks plus 20% general replay).**
- Ladder: 100k → 300k → all available distinct roots (expected ≈0.7–1.5M depending on ScaleQuest), k = 1, nested.
- Budget question at a fixed 300k examples: 300k×1 vs 150k×2 vs 75k×4 different solutions, all drawn from one common pool of roots that have at least four valid solutions.
- Hypothesis control on the same 75k roots: one solution repeated four times vs four different solutions (tokens matched approximately). This is the direct test of "different solutions help".
- Base comparison: the 300k arm repeated on the original Apertus-8B base with its own tokenizer, reported as a comparison of starting packages.
- Rule: stop adding maths SFT when two successive increases in exposure each buy less than 1.5 points on development MATH (English and Greek) and the plateau survives one targeted control (the better stage-1 runner-up recipe, or two passes). A plateau redirects effort to the starting checkpoint, the teacher targets and the objective; it is not a claim that the model cannot improve.

**Stage 3a — allocation and Greek weight (5 runs × 300M).** Full token tables per arm are produced from the inventory before launch; the cut in each arm is stated capability by capability.
| arm | change from control |
|---|---|
| control | §1 shares, Greek at two exposures |
| reasoning-heavy | maths 40, code 20; taken proportionally from chat, science, documents |
| assistant-heavy | maths 20, code 12; added to IF and chat |
| Greek removed | Greek rows replaced by English rows of the same capability |
| Greek doubled | four exposures of every Greek block — an operational test of weighting this package, including repetition; not a test of "Greek" as such. At 300M the control's Greek exposure differs from the 1B run's, so the final Greek policy is re-checked in stage 4 |

**Stage 3b — language, package, personality (equal-length continuations from the stage-3a control, same optimiser-reset policy, capability replay; ≈50M each).**
- Language swap: the same roots in Greek vs in English (our translated maths and adapted rows against their English originals). Cleanest available test of transfer.
- Leave-one-block-out over the Greek package (IF, maths, adapted chat, conversation suite, rewrite).
- Personality: identity+style on vs off, omitted rows replaced by neutral Greek rows; factual and safety parts stay in both. Also the dilution check: does four exposures still imprint identity at the target run's dilution? If not, the fallback is a short late identity pass.
A promising result here is confirmed inside the stage-4 recipe before it is generalised.

**Stage 4 — confirmation and target.** Re-run the most important close contrast (from stages 1–3) at 600M; then the target run at the inventory's size; two additional seeds for the final comparison against 1-G4F6P1 and the incumbent. The ranking at 300M is not assumed to hold at 1B.

After the target run: RL-pool screening starts on a stratified sample (≈2k prompts × 8 samples) to estimate the learnable fraction before any full screen.

## 3. Expectations and failure conditions

| Area | Expectation | It has failed if |
|---|---|---|
| Instruction following | IFEval-el clearly above 1-G4F6P1's 60.8 and the incumbent's 58.6; IFBench-el and multi-turn may move a little, most of their gain is expected from later RL | IFEval-el does not beat both baselines on paired items |
| Code | First measured baseline; stock Apertus-8B-Instruct is 34 / 42 on HumanEval+ / MBPP+ | Below stock Apertus-Instruct |
| Mathematics | Unknown: the ladder is the measurement | The ladder is flat from 100k roots onward under both recipes |
| Greek output | Correct-and-Greek stays at or above 1-G4F6P1 in every capability | Correctness rises while correct-and-Greek falls in maths or code |
| Identity | Holds at four exposures | Interview probes fail at target dilution → late identity pass |

## 4. Wall clock and tracked cost

At 1-G4F6P1's rate (22M supervised tokens per node-hour; to be re-measured): stage 1 ≈ 1.2B, stage 2 ≈ 0.9B, stage 3 ≈ 1.7B, stage 4 ≈ 2.2B plus 2.0B for seeds ≈ 6–8B supervised tokens ≈ 270–360 node-hours ≈ CHF 730–970.

The stages are sequential, so parallel nodes alone are not enough: on single 4-GPU nodes the chain of longest runs is ≈14 + 14 + 14 + 45 h. With each run data-parallel over 4 nodes (16 GPUs; 524k-token batch = 128 sequences) a 300M run is ≈3.5 h and a 1B run ≈12 h, so training is ≈35 h end to end with runs inside a stage in parallel (up to ≈28 nodes at the widest point). With evaluation and the decisions between stages, **48 hours of cluster time after stage 0 is realistic; 24 is not.** The small-batch reference arm (16 sequences per update) cannot be spread over 16 GPUs and runs on one node for ≈14 h, which fits inside the same window. Stage 0 itself (pool download and assembly, gates, multi-node launch, review) comes first and is mostly engineering and data work, not cluster time.
