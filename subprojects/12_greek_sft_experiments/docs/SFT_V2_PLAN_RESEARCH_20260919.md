# SFT v2: research on the assumptions and consequences of the experiment plan

19 September 2026. Subject: `Greek_Apertus_8B_SFT_Experiment_Plan.md` v1.0 (copy: `docs/lit/sft_v2_research_20260919/PLAN_v1.0_as_received.md`).
Status: research only. Nothing was launched, no evaluation was run, no dataset was downloaded.

Method: five web-research agents (Opus), each writing a source-tagged report (verified with URL / derived / recalled), plus checks against our own receipts. The five reports are in `docs/lit/sft_v2_research_20260919/` (≈41k words); this document is the synthesis. Where I write "report: …" the claim comes from an agent's reading of the source and I did not re-open the source myself. Where I checked something myself it says so.

## 0. The ten things that change the plan

1. **The plan's baseline does not exist.** It assumes a later SFT round repaired 1-G4F6P1's regression. Our records have no SFT round after 1-G4F6P1 (only the DPO01 arms). The MGSM-el gap to the incumbent (44.4 vs 52.4) stands and is not the RoPE artefact (checked today: the SFT checkpoints carry the reference geometry).
2. **Maths was tiny, and 180M tokens is still below the first published scale point.** We trained on ≈17M supervised maths tokens ≈ 57k examples. OpenMathInstruct-2's scaling curve starts at 1M examples; 86% of its gain (Llama-3.1-8B base, MATH ≈20 → 61 → 67.8 at 14M) comes from the first million. 180M tokens ≈ 0.5–0.6M examples. One million examples needs ≈300M supervised tokens.
3. **Distinct problems first, several solutions second.** At a fixed 256k pairs, going from 1k to 6.5k unique questions gave +10.5 MATH points (OpenMathInstruct-2 §2.2.4). Several solutions per problem helps where the question set is fixed and the problems are hard (Yuan 2023, DART-Math). So the owner's multiplicity hypothesis holds for the hard tail; for the bulk the lever is ≈500k distinct problems at k≈1–2.
4. **The base model may be the maths ceiling.** Apertus tech report, one harness: Apertus-8B-Instruct MATH 18.2 / GSM8K 62.9 / MGSM 48.5 vs Llama-3.1-8B-Instruct 36.3 / 84.5 / 67.7, with 485k English maths rows in Apertus's SFT. Our own runs agree: stock Apertus-Instruct 11.0 on MATH-200-el, ours 16.0, Krikri 39.0. We are already above our own family's instruct model; the gap to Krikri equals the gap between the base families. Maths-data scale is the untested lever, so the big maths run should be framed as a diagnostic with a stop criterion fixed in advance.
5. **The real language risk is losing Greek output per capability, not losing maths.** English-centric SFT took correct-language rates for non-Latin scripts from 98 to 6 in one study (Marchisio 2024); English-only maths SFT gave 9.7% question–answer language consistency (QAlign). Generic Greek chat does not repair Greek maths answering; capability-matched Greek rows do (a few thousand sufficed in MMATH). Greek must be at least ≈5% of the maths slice itself, and output language must be a primary metric per arm.
6. **Long reasoning traces do not fit this model.** 4,096 tokens is a hard limit (CPT ran only at 4,096; vLLM refuses more). OpenR1-Math traces average ≈4,650 tokens; OpenCodeReasoning-2 traces fit in ≈30% of rows; Nemotron's maths, code and tool splits are 100% reasoning-on. Drop all three as named. The plan's 8K context is a length-extrapolation experiment, not a setting.
7. **A 55% maths+code share pulls against instruction following.** OLMo 3 SFT ablation (added domains on an OLMo 2 base mix): +code IFEval 61.7→57.3; +maths →54.0 and HumanEval 23.2→18.3; +IF IFEval →74.1 but HumanEval →14.6. Direction is informative, magnitudes are not transferable. The plan's task-allocation comparison (M) is therefore essential, and IFEval-el is the canary at every checkpoint.
8. **For instruction following, variety beats volume, and SFT does not move IFBench.** IFBench paper (measured under RL with verifiers, not SFT): 10→1,000 examples per constraint is flat past ≈50; 1→3 constraints per prompt +10.6 points; a single/multi-turn mix beats either alone. OLMo 3 7B: SFT 81.7 IFEval / 27.4 IFBench → after RL 85.8 / 32.3. So: widen families and compositions rather than rows per family, and build the verifiable prompt reserve for RL now (it needs no LLM calls).
9. **We under-train on volume, not on learning rate.** ≈3,450 updates at 65k tokens is ≈15× fewer tokens than OLMo 3's 7B SFT at a similar update count. Published 8B recipes use 5e-6 (Tulu 3, Apertus) with batches of 128–512 sequences; our 1e-5 is already high. Fresh examples beat repeated passes and instruction following degrades past ≈2 epochs (arXiv 2609.01244; I read it: its full-fine-tuning optimum is ≈3e-5 on four narrow customer tasks, not a licence to raise ours).
10. **The Greek dose is limited by inventory.** We own ≈37M supervised Greek tokens, with doubled copies inside (Greek maths ≈4.2M unique). 15% of 600M = 90M would mean ≈4 passes over Greek maths and ≈2 over Greek IF. With a two-pass cap the honest Greek share at 600M is ≈10%.

## 1. The plan's assumptions, one by one

| # | Assumption in the plan | Finding | Consequence |
|---|---|---|---|
| A1 | A recovered SFT model is the baseline | Not in our records | Baseline = 1-G4F6P1 and the incumbent 1-G2F1P1, both from the same CPT checkpoint |
| A2 | Maths 30% of 600M is a large dose | 0.5–0.6M examples, below the first published scale point | Either maths ≈300M (≈1M examples) in a ≈1B mix, or accept 600M as a point on the steep part of the curve and do not expect the published 61 |
| A3 | OpenMathInstruct-2 + NuminaMath-1.5 + OpenR1 | OpenR1 does not fit; NuminaMath is unverified and undecontaminated and is the parent of most RL sets | §2 mix; decontaminate the assembled mix ourselves (MATH-500, GSM8K test, MGSM in Greek and English) |
| A4 | "Use complete, checked solutions" | NVIDIA's filtering experiments gained nothing (43.6 unfiltered vs 43.0–43.8); SFT tolerated ≥20% wrong solutions at ≥256k pairs; short format beat verbose by 3.9 points at 40% fewer tokens; a 405B teacher beat self-generated by 7.8 | Do not spend judge budget re-verifying OpenMathInstruct-2; verify NuminaMath by its own validity flags; keep solutions short |
| A5 | Code 25% from three named sources | OpenCodeInstruct alone offers ≈9× the need, verified, Python only, all answers under ≈2k tokens; OpenCodeReasoning-2 mostly unusable; our previous mix had 1.15M code tokens (0.8%) and code was never measured | §3 mix; add a code evaluation (HumanEval+/MBPP+) to the battery before the first comparison; decide consciously that the block is ≈97% Python |
| A6 | IF 15% from Greek IF, Tulu personas, smoltalk2, Dolci | Tulu personas is single-turn, IFEval-25 only, responses never code-verified, and duplicated inside Dolci, smoltalk2 and Nemotron | §4 mix; per-family caps; family-level hold-out |
| A7 | Greek 15 percentage points held fixed | Inventory supports ≈10% at 600M under a two-pass cap | Fix the Greek share by inventory and state exposures per block; ≥5% Greek inside the maths slice |
| A8 | Transfer from foreign-language maths and code | Supported in direction (MathOctopus, QAlign, MMATH, Shaham), no dose–response curve exists for any language, none for Greek | Keep the plan's G experiment, but with output-language rate as a primary metric and a small Greek→English question-translation slice (QAlign: +11–12 MGSM points on non-English from question alignment alone) |
| A9 | Validate 8,192 context | CPT geometry is 4,096; serving refuses more | Keep 4,096 for the main line; hard-drop rows that exceed it rather than truncating |
| A10 | LR 5e-6 / 1e-5 / 2e-5 at 65k-token batch | Batch is 4–16× smaller than comparable recipes; β2 0.99 and cosine differ from Apertus's own SFT recipe (AdEMAMix, β2 0.999, 5e-6, linear, batch 512) | Put batch into the first calibration (65k vs 262k tokens, β2 rescaled by the half-life rule as a disclosed choice); add checkpoint averaging (OpenMathInstruct-2: >2 points, free); table the drift from Apertus's recipe before launch |
| A11 | Phase 0 loss-normalisation check | Our trainer (`cluster/sft_train.py`) sets no loss-normalisation option and relies on library defaults; packed sequences with assistant-only loss is the configuration where Tulu 3 found long targets under-weighted | Make it the first gate: one deterministic batch, summed per-token loss vs the trainer's reported loss, across accumulation and across the four GPUs |
| A12 | Eight screening runs | 4×150M + 4×600M = 3.0B supervised tokens ≈ 135 node-hours ≈ CHF 365 at 1-G4F6P1's measured rate (22M supervised tokens per node-hour); one 600M run ≈ 27 h on one node, over a 24 h job; cap is CHF 240 with 225.65 spent | The cap and the run list are the owner's decision; the trainer's resume makes 600M feasible as a chain |
| A13 | Licences handled per source | smoltalk2 declares no licence (it is in our current mix); APIGen-MT is non-commercial; McEval-Instruct is share-alike; WildChat-in-Dolci answers are GPT-4.1; Apertus's own licence filtering cost them 5.8% average | Licence column in the manifest from day one; owner decides the release constraint before assembly |

## 2. Mathematics: contents and sampling

Proposed English-first block (report, with licences): OpenMathInstruct-2 (CC-BY-4.0; 607k unique questions, 14M pairs, Llama-3.1-405B short solutions, decontaminated against MATH test, GSM8K test, AMC 23, AIME 24) as the spine; NuminaMath-1.5 word problems only, validity flags on, excluding cn_k12, synthetic_math, metamath and orca_math (≈158k available); DART-Math-Hard for the hard tail; ScaleQuest for question diversity outside the MATH/GSM8K lineage. Excluded: OpenR1 (length), AceMath and MegaScience (non-commercial), Skywork-OR1 (no licence), Nemotron maths (all reasoning-on).

Sampling rules:
- Unit of sampling is the **root problem**; all solutions, paraphrases and later Greek versions carry the root id.
- k = 1 for NuminaMath and ScaleQuest, k ≤ 2 for OpenMathInstruct-2, k ≤ 4 on the hard tail (more samples for harder problems, DART-Math's principle). This is the clean test of the multiplicity hypothesis: a k = 1 control arm against k = 4 on the same hard roots.
- Re-weight towards grade-school word problems: the native share of GSM8K-lineage rows is 15.3%; MGSM-el is our larger relative gap, so ≈35%.
- Keep MATH levels 1–2 at ≥25% of the MATH-lineage slice; cap geometry (figure references).
- Length: problem ≤ ≈1,000 tokens, problem + solution ≤ ≈3,000 tokens, measured with our tokenizer (the reports used character estimates).
- Greek: all ≈15k Greek problems, ≤2 exposures, ≥5% of the block. Format decision for future Greek maths rows: solve in English, render the whole solution in Greek, then the guarded language pass; hold a native-authored slice as a translationese control.

Two budget options to put to the owner: (a) 600M mix with maths ≈40% (≈0.8M examples); (b) ≈1B mix with maths 30% (≈1M examples). Stop criterion proposal for the diagnostic reading: if English MATH-500 stays under ≈20 after ≈10× the previous maths tokens, the base is the limit and the maths effort moves to the base (maths replay in CPT) rather than to SFT data.

## 3. Code and the other blocks

Code (≈150M, one pass, no repetition; report): OpenCodeInstruct filtered to all tests passed and top judge scores (≈110M, consider trimming to ≈90M so no single source exceeds ≈15% of the mix); OpenCoder educational_instruct (≈12.6M, MIT, compiler-validated); package_instruct sample (≈15M, library usage); OpenCodeReasoning-2 code-only solutions with `split != test` (≈10M, needs question rehydration). On hold for a licence decision: mceval_instruct (share-alike; our only non-Python coverage) and evol_instruct (OpenAI-output lineage). Calibration (Ai2 harness): Apertus-8B-Instruct HumanEval+ 34.4 / MBPP+ 42.1; OLMo-3-7B-Instruct 77.2 / 60.2; Apertus-70B barely above the 8B, which points at post-training data.

Chat, documents, science, tools, safety: achievable from Dolci-Instruct-SFT (ODC-BY, exact per-domain counts in the report) and smoltalk2 no-think subsets, subject to the licence question. Warnings: Nemotron chat has empty user turns and answers that say "developed by Alibaba" — filter, and check the Nemotron chat already in our mix (42% of 1-G4F6P1's supervised tokens) for the same defect; documents (≈48M) is reachable only at exactly one pass; keep safety at ≈2% (adding safety had the worst average in OLMo 3's ablation, removing it hurt in Tulu 3's). Dedup order across overlapping collections is in the code report §7.4. Per-source response-token yields for Dolci could not be read remotely and must be measured locally before the IF, chat and document budgets are fixed.

## 4. Instruction following: size, breadth, quality

Breadth (the main lever):
- Extend our 44 families with the 29 IFBench training constraints, structured outputs (JSON schema, tables, YAML/CSV), conditionals, negation, position and counting families, editing with preservation, system-level standing rules, contradictory or impossible constraints (refuse or flag), and the three-turn rewrite format (task → answer → "rewrite it to comply with X"), which is exactly our 35% redirect/redo failure. Candidate lists with verifiability marks: IF report §3.
- Cap each family at roughly 50–300 rows per stage; spend the surplus on compositions (up to five constraints) and on variable ranges wider than the evaluation ranges. Caveat: these numbers were measured under RL with verifiers, not SFT.
- Mix single-turn and multi-turn rows.

Size (English first, report §5.1, ≈190k rows ≈ 100M tokens by estimate): our Greek IF 30k; `allenai/IF_sft_data_verified` 31.7k (code-verified, up to five constraints); Dolci Precise IF 40k of 137k (verifier-filtered); smoltalk2 multi-turn IF 28k (strip thinking); Nemotron structured outputs 15k; Conifer and VerInstruct for soft constraints 20k; UltraIF for naturally occurring constraints 15k; system-prompt chats 10k; adversarial/impossible 2k. Tulu personas only if a verifier pass keeps it.

Quality: re-run verifiers on every imported row; drop keyword-stuffed and padded answers (our own astra review found this failure on short factual answers); response-quality check on a sample; dedup across the overlapping collections before budgeting.

Work that needs no LLM calls: the whole RL prompt reserve (`allenai/IF_multi_constraints_upto5` 95k and `allenai/RLVR-IFeval` 15k are prompt-only with verifiers); Greek-aware verifiers (final sigma, accent normalisation, accent-less capitals, the Greek question mark in sentence splitting, inflection-aware keyword matching); rows whose answer is a deterministic function of the input (copy, span, format transformation, re-serialisation); minting new constraint–response pairs from responses we already hold that happen to satisfy a range constraint. New constrained responses always need generation; UltraIF suggests an 8B model plus verifiers can be its own generator.

## 5. The reserved split for later Greek adaptation and RLHF

Design (split report §A4, IF report §4.2, maths report §Q5):
- **Three-way by root**: SFT-train / RL-pool (never in SFT; sampled on-policy later) / TEST (never trained on at any stage; 1–2k roots per capability). Frozen before any sampling.
- **Defined by problem text, not by dataset name.** NuminaMath is the parent of OpenR1, DeepMath, Skywork-OR1 and Big-Math; DeepScaleR sits inside Polaris. Normalised-text hash plus 8-gram/embedding match against the exact SFT rows, with removal counts recorded.
- **Sizes**: maths 60–85k roots (published recipes consume 17k–66k in-band prompts; ≈35–46% of problems fall in band for 7–8B models, ours measured ≈20%, so reserve at the pessimistic end); code 25–40k roots with unit tests; IF 15–25k prompts plus ≈15% of constraint families never trained and ≈25% reserved for RL; other 10–20k.
- **Sources for the maths reserve**: a stratified slice of OpenMathInstruct-2 roots held out of SFT (same distribution as training, which is what makes prompts learnable), preferring rows whose answer comes from the original MATH/GSM8K train sets; DeepMath-103K (MIT, difficulty score, decontaminated by its authors); Polaris-53K (Apache-2.0, 7B pass-rate difficulty); GSM8K and MATH train. Big-Math is gated with a licence conflict; Skywork-OR1 has no licence.
- **Difficulty**: screen with 8 samples from the exact starting checkpoint at RL-time sampling settings; keep ≈1–7 correct of 8 (Qwen2.5-Math kept 2–5 of 8; OLMo 3 dropped >62.5%). Breadth over depth: our 115 prompts × 32 samples would have been better spent as 460 × 8. Gate proposed by the report: ≥30% of reserved maths prompts in band before any maths preference/RL work; today's figure is ≈20%.
- **Disjointness is not a hard rule** at RL time (Tulu 3: unused plus reused prompts was best; DeepSeekMath reused SFT prompts); the reserve is for clean difficulty measurement and an honest test set.
- **Cheap Greek adaptation**: tag every reserved item at reservation time — short problem text, language-independent answer (integers and symbols need no verifier changes), no English wordplay or letter-level constraints, code tests independent of the prompt language, decimal-comma convention fixed in the checker now. Only the prompt is translated (OpenMathInstruct-2 problems average ≈66 tokens), so adapting 30k reserve prompts costs roughly a tenth of adapting the same number of SFT rows. Pilot ≈200 human-checked Greek items before the bulk.

## 6. Corrections to the agents' reports

- "Krikri v1.5 does not exist" — it does; we evaluated it (MATH-500-el 38.4).
- "Krikri's 32–38 is unreplicated and may be a `\boxed` artefact" — those are our own measurements with the full-response extractor; the `\boxed` artefact is real for stock Apertus-Instruct on English MATH-500 (1.8%) and that number must not be used.
- arXiv 2609.01244: one report gave the full-fine-tuning optimum as ≈1e-5; the paper says ≈3e-5 (read by me).
- All token counts in the reports are character-based estimates; nothing was tokenised with our tokenizer.
- The OLMo 3 mixture ablation and the IFBench variety ablation are from other bases and, for IFBench, from RL; treat directions as evidence and magnitudes as unknown.

## 7. Decisions for the owner

1. Baseline and whether the plan's "recovered model" refers to something outside this repository.
2. Maths budget: 600M mix at ≈40% maths, or ≈1B mix at 30%; and the stop criterion for the base-ceiling reading.
3. Release constraint (decides smoltalk2, WildChat-in-Dolci, mceval, evol, Tulu personas).
4. Greek share by inventory (≈10% at 600M, ≤2 exposures) versus producing more Greek rows before launch.
5. Context stays at 4,096 for the main line.
6. Batch size joins the first calibration; checkpoint averaging added.
7. Cost cap for the run list (≈CHF 365 for the plan's first eight runs at the measured rate).
8. Reserve sizes and the ≥30% in-band gate before maths preference work.

Zero-cost preparation that does not depend on these decisions: the loss-normalisation check on one batch; the manifest schema with root ids, lineage and licence columns; the text-level dedup/decontamination tooling; token-length measurement of candidate sources with our tokenizer; the IF prompt reserve and Greek-aware verifiers.

## 8. Sampling when a source is not taken whole (added 19 Sept, after the owner's question)

Status: this is my recommendation from the evidence below, not a settled result. No paper tests sub-category sampling for a mix like ours; the direct evidence is from maths only.

Evidence:
- A source's raw row counts are not a distribution worth preserving. In rejection-sampled sets, easy problems collect more correct solutions, so sampling rows proportionally over-represents easy problems. DART-Math (Mistral-7B, same ≈15k problems, ≈590k rows): equal solutions per problem MATH 43.5; more solutions for harder problems 45.5; both far above proportional rejection sampling sets of 2–4× the size (MetaMathQA 395k 29.8, MathScaleQA 2M 35.2). OpenMathInstruct-2 ships its 1M/2M/5M subsets "fair-downsampled" (even over questions, not over pairs) for the same reason.
- Proportional-to-source also does not match our targets: the native GSM8K-lineage share of OpenMathInstruct-2 is 15.3% while MGSM-el is our larger gap.
- smoltalk2's published weights down-weight its largest sources heavily (×0.02 to ×0.5); 33.5% of its examples hold 86.7% of its tokens, so row quotas misstate token shares.

Rule proposed (all blocks):
1. Sample **roots, not rows**: choose problems/conversations first, then take k solutions for each chosen root.
2. **Stratify** each source by its own sub-categories (topic × difficulty × source-of-problem for maths; language × task type × tests-passed for code; constraint family × number of constraints × turns for IF).
3. Across strata use a **tempered share**: weight ∝ (available roots)^0.5, with a floor so no stratum disappears and a cap so none exceeds ≈15% of the mix; then apply the few deliberate overrides and record them (GSM8K-lineage ≈35%; MATH levels 1–2 ≥25%; geometry capped; hard strata get larger k).
4. Within a stratum sample **uniformly at random over roots**; keep the natural length distribution (never "shortest first"), subject to the 4,096 drop rule.
5. Quotas are in **supervised tokens measured with our tokenizer**, not rows.
6. Make selection **deterministic and nested**: rank roots by a hash of (seed, root id) and take the top of each stratum, so the 150M set is a subset of the 600M set, which is a subset of the 1.5B set. The plan's D and S comparisons then differ in amount, not in which problems were drawn. The RL-pool and TEST reserves are cut first with the same strata.
7. Ship a receipt per block: strata, available vs taken roots, k, tokens, overrides.

Open question this rule does not settle: the exponent (0.5 is a convention from multilingual sampling, not a measured optimum for SFT). It can be tested cheaply inside the maths block (proportional vs tempered vs uniform-over-strata at 150M) if the owner wants evidence rather than a convention.
