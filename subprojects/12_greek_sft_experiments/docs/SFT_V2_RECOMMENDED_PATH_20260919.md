# SFT v2: recommended path

19 September 2026. Companion to `SFT_V2_PLAN_RESEARCH_20260919.md` (evidence) and the plan v1.0. This document commits to one path. Where my confidence between options is close, the option becomes an experiment arm; where it is not, it is decided here. Costs use 1-G4F6P1's measured rate: 22M supervised tokens per node-hour, ≈CHF 12 per 100M supervised tokens. Nothing here is launched; launch needs the owner's go.

## 1. The target run

**One pass over ≈1.0B supervised tokens, from the CPT base, 4,096 context.** 1B is the smallest mix that gives mathematics one million examples (the first point of the only published 8B scaling curve, where most of the gain already is) while keeping every other capability at or above the plan's absolute amounts. Everything except the Greek blocks is seen once; fresh examples beat repeated passes in every source we read.

| Block | Share | Tokens | Contents |
|---|---:|---:|---|
| Mathematics | 33% | 330M | OpenMathInstruct-2 ≈700k examples over ≈520k distinct problems (the rest of its 607k are the reserve); NuminaMath-1.5 word problems ≈150k (validity flags on; cn_k12, synthetic_math, metamath, orca_math out); ScaleQuest ≈100k; DART-Math-Hard ≈80k; GSM8K and MATH train originals; all ≈15k Greek problems ×2 |
| Code | 15% | 150M | OpenCodeInstruct, all tests passed and top judge scores ≈90–110M; OpenCoder educational ≈13M and package ≈15–25M; OpenCodeReasoning-2 code-only solutions ≈10M (`split != test`, questions rehydrated) |
| Instruction following | 13% | 130M | breadth-first build of research §4: our Greek IF 30k; IF_sft_data_verified; Dolci Precise IF; smoltalk2 multi-turn IF (thinking stripped); structured outputs; soft constraints (Conifer, VerInstruct); UltraIF; system-prompt chats; impossible/contradictory constraints; zero-cost deterministic rows |
| Chat and multi-turn | 21% | 210M | Dolci chat; filtered Nemotron chat (no empty user turns, no foreign identity strings); smoltalk2 no-think chat; our conversation suite v2 and Greek chat |
| Science and reasoning | 7% | 70M | Dolci science and reasoning; puzzles |
| Documents, rewriting, tables | 5% | 50M | smoltalk2 summarise/rewrite/table; Dolci FLAN/TableGPT/SciRiff; Greek rewrite |
| Tool use | 3% | 30M | Dolci tool use, converted to the Apertus format; no-call and error cases kept |
| Safety and uncertainty | 2% | 20M | Dolci safety trio; audited Greek rows |
| Identity and personality | 1% | 10M | personality v3 + overlays, ×4 as in the incumbent |

Greek: every Greek block we own, at most two exposures, ≈65–70M tokens ≈ 7% of the mix, with Greek ≥5% inside the maths block. More Greek waits for LLM budget; experiment G below measures what the share buys.

Decided without an experiment (evidence is one-sided):
- 4,096 context; rows that exceed it are dropped, never truncated. No long reasoning traces (OpenR1, OpenCodeReasoning-2 traces, Nemotron maths/code/tools).
- Short worked solutions; no re-verification of OpenMathInstruct-2 with our judges (NVIDIA's filtering gained nothing; a stronger teacher mattered more than filtering).
- Sampling by root problem, stratified, square-root shares with floors/caps, recorded overrides (grade-school word problems ≈35% of maths; MATH levels 1–2 ≥25%; geometry capped), token quotas, nested deterministic selection (research §8).
- Reserve cut before anything else: three-way by root (SFT / RL pool / never-train test), defined by problem text not dataset name; maths 80k roots, code 30k, IF 20k prompts plus 15% of constraint families never trained and 25% kept for RL, other 15k; every item tagged for Greek portability (research §5).
- Checkpoint averaging over the last checkpoints of each run (OpenMathInstruct-2: more than 2 points, free).
- Licence column in the manifest; sources with no declared licence or non-commercial terms stay out of the main line until the owner rules (smoltalk2 subsets are the main case; equivalents exist in Dolci for most).

## 2. Experiments, in order

Each stage feeds the next. Runs inside a stage are independent and can run in parallel.

**Stage 0 — gates, no training.** Loss-normalisation check on one deterministic batch (summed per-token loss vs the trainer's, across accumulation and GPUs). Pool assembled with root ids, lineage, licence; reserves cut; lengths measured with our tokenizer; text-level decontamination against every benchmark we use, in Greek and English. Code evaluation (HumanEval+/MBPP+) and an output-language rate added to the battery. Parameter table against 1-G4F6P1 and against Apertus's own SFT recipe.

**Stage 1 — optimiser and batch (3 runs × 150M, balanced mix, ≈CHF 54).** My confidence is close between our recipe and the published ones, so all three run:
| arm | batch (tokens/update) | peak LR | note |
|---|---:|---:|---|
| H-ours | 65k | 1e-5 | the recipe of all previous rounds |
| H-tulu | 524k | 5e-6 | Tulu 3 / Apertus scale of batch and LR |
| H-omi | 524k | 2e-5 | OpenMathInstruct-2's LR at its batch scale |
β2 rescaled by the token half-life rule with batch, disclosed. Winner by generated-task results (maths, IF, code) with retention as a constraint. If H-omi wins and is stable, that is the setting for everything after.

**Stage 2 — does maths scale on this base, and does k matter (5 runs, ≈CHF 87).** Maths-only blocks plus 20% general replay so the chat format holds.
- Ladder: 100k / 300k / 1M distinct problems, k=1, nested. Reads the dose–response curve on English and Greek MATH-500 and MGSM.
- The owner's multiplicity hypothesis at a fixed 300k examples: 300k×1 (the ladder's middle point) vs 150k×2 vs 75k×4, same strata.
Decision rules fixed now: if English MATH-500 at 1M is under 20, the base is the ceiling — maths drops to ≈15% in the target run and the maths effort moves to the base (maths replay in CPT). If it climbs through 1M without flattening, the target run's maths block goes up to 2M examples and the mix to ≈1.3B. The k result sets k for the target run (by stratum if the hard strata differ).

**Stage 3 — allocation and Greek dose (5 runs × 300M, ≈CHF 182).** One shared control, so five runs cover two questions.
| arm | allocation | Greek |
|---|---|---:|
| control | §1 shares (maths per stage 2) | 7% |
| M-reasoning | maths + code 60% | 7% |
| M-assistant | maths + code 35%, IF + chat 45% | 7% |
| G0 | §1 shares | 0% |
| G15 | §1 shares | 15% (two exposures of everything Greek, the rest by repeating the best-verified Greek blocks; labelled a repetition arm) |
Primary readings: maths, code, IFEval-el/IFBench-el, dialogue measures, Greek output-language rate per capability, Greek quality review. OLMo 3's ablation says maths/code and IF pull against each other; this stage measures the exchange rate on our model rather than assuming theirs.

**Stage 4 — the target run (≈1.0–1.3B, ≈CHF 121–157).** Settings from stages 1–3, seed 42; two more seeds only for the final comparison against the incumbent and 1-G4F6P1. Promotion criteria frozen before launch, as for 1-G4F6P1.

Total before extra seeds: ≈CHF 445–480, ≈165–180 node-hours; on one node at a time about a week of wall clock, less with parallel jobs.

Optional, only if a stage result asks for it: sampling exponent (proportional vs square-root vs uniform, 3 × 100M inside the maths block); AdEMAMix as in Apertus's recipe; ordering (reasoning early, assistant and Greek late).

## 3. What I expect, and how sure I am

- **Instruction following, chat, code: near-certain gains.** IF data of this breadth took OLMo 3 7B to 81.7 IFEval after SFT; our code block goes from 1M to 150M tokens against a family baseline of HumanEval+ 34. These are the results the run is most likely to deliver.
- **Mathematics: a real bet with a measured answer by stage 2.** For: twenty times the distinct problems, a stronger teacher, the only recipe with a published 8B curve. Against: every model of the Apertus-type European cohort sits under 20 on MATH, including Apertus-Instruct with 485k maths rows. Stage 2 exists so that the 1B run is sized by our own curve rather than by either argument.
- **Greek output under an English-heavy mix: the main risk**, controlled by Greek rows inside each capability and measured in every arm.
- **Not addressed by this path:** IFBench-el and multi-turn persistence improve mainly with RL on verifiable prompts; the reserve makes that the next step after the target run.

## 4. What needs the owner

1. Go for stage 0 (no cost) and the cost envelope for stages 1–4 (≈CHF 480; the cap is CHF 240 with 225.65 spent).
2. Release constraint, which decides smoltalk2, WildChat-in-Dolci, McEval and evol_instruct.
3. The stage-2 decision rules as written, or different thresholds.
