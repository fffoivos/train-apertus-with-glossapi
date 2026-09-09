# Next Greek benchmarks for the instruction-tuned model, beyond MGSM and IFEval (2026-09-09)

Owner ask (9 Sep): research which 1–3 benchmarks to translate into Greek next for instruction-tuned models, beyond GSM (MGSM) and IF (IFEval), and have astra review the proposal. Research by a web-search agent (appendix A, with URLs); ranking and design below are mine; the astra review and its disposition are in docs/reviews/ASTRA_next_benchmarks_20260909.md.

## 1. What we measure today and what already exists in Greek

Our battery (cluster/eval_checkpoint.sh, full_battery.sh): `ifeval_greek` (ILSP, 541, manual translation), `mgsm_greek` (ILSP, 250, manual), GreekMMLU (native, 21,805), the English retention suite, our own ellinika-bench (449 items, 4 pillars, judge + auto) and the dev50/reading40 gates.

**Do not translate, adopt** (already Greek, mostly ILSP/Athena RC, CC-BY-NC-SA unless noted):
- Chat quality: `ilsp/mt-bench-greek` (80 × 2 turns, post-edited, GPT-4o judge), `ilsp/m-ArenaHard_greek` (1,000, post-edited, pairwise judge). Krikri reports 7.96 and 31.8% on these, so adopting them makes our numbers comparable to the published Greek table.
- Knowledge/reasoning: `ilsp/MMLU-Pro_greek` (12,000, MT), `ilsp/greek-hle` (2,500, gated, MIT), Belebele `ell_Grek` (900, human), INCLUDE Greek (587 native exam items), Global-MMLU `el` (MT, not in the human-edited Lite set).
- Math beyond MGSM: `ilsp/greek_lyceum_mathematics` (465 native high-school items from the Ministry item bank), `ilsp/greek-geometry-3k` (3,002).
- Safety (harm side): `ilsp/attaq_greek` (1,402), `ilsp/Jailbreak-StrongReject-el` (309, MIT).
- Code: HumanEval-XL Greek natural-language prompts (164 × 12 languages).
- Native domain sets already surveyed in subproject 09: medical MCQA, ΑΣΕΠ MCQA, civics QA, culture bench, DemosQA, GreekBarBench.
- EuroEval lists Greek IFEval and an unofficial MultiIFEval-el (gated repos, not inspected).

**Holes with no Greek instrument** (verified absent by the agent): multi-turn conversation skills beyond 2 turns, generalisation of instruction following to held-out constraint types, over-refusal (the benign side of safety), harder competition-style math for cross-lingual comparability, persona/identity and sycophancy.

## 2. Selection criteria

1. The benchmark must measure something we are training now and cannot see: the conversation-skills suite (standing instructions, in-dialogue memory, versioned editing, self-observation), instruction following outside the trained families, robustness that is not just refusal, math above grade school.
2. Scoring must survive translation: rule verifiers need Greek engineering (final sigma, tonos, capitalisation), exact-match math is language-neutral, LLM judges are the least robust (round-trip judge prompts shift win rates by 0.18–0.32) so binary per-turn rubrics beat 1–10 holistic scores.
3. Translation method: machine translation alone does not hold up (HellaSwag-type items fail wholesale; Winogrande-type items leak answers through grammatical gender, which Greek has). Use the MMLU-ProX pattern: strong-model translation → self-check → cross-check by a different model → native review of a sample, and report a translation-quality figure next to the model score.
4. Contamination: nothing we translate for evaluation may overlap our SFT sources (our math set translates GSM8K train and MATH train levels 1–4; our IF set is own-authored with 44 constraint families).

## 3. Recommendation: three to translate, one cheap extra

| Rank | Benchmark | What it gives us | Size / translation volume | Scoring after translation | Main risk |
|---|---|---|---|---|---|
| 1 | **MultiChallenge** (Scale AI, 273 conversations, 4 categories) | the exact skills of the S1–S5m lanes: instruction retention (69), inference memory (113), versioned editing (41), self-coherence under pressure (50) | ~336k words, the largest item; a 150-conversation stratified subset is acceptable for arm comparisons | LLM judge with binary per-turn rubric questions; rubrics translated; judge = Sol or Opus, blinded, both orders | frontier models score ~41%, an 8B model may floor; report per category and use it for relative arm comparisons; some embedded English editing tasks need localisation |
| 2 | **IFBench** (Ai2, 294 prompts, 58 held-out constraints) | tells "follows instructions" from "memorised the trained families"; directly tests the OOD-constraint concern raised for our IF set | ~15k words | code verifiers re-engineered for Greek (ς/σ, tonos under capitalisation, Greek alphabet for letter constraints); replace non-transferable constraints with Greek-native ones as M-IFEval did | the 29 training constraints shipped with it must stay out of our SFT mix; our 44 families must be checked against the 58 held-out ones and any overlap reported |
| 3 | **XSTest** (250 safe + 200 unsafe) | the missing benign side of robustness: does the model refuse harmless-but-alarming prompts? Pairs with `attaq_greek` for the harm side; our personality review already found inappropriate refusals in C rows | ~5k words, but roughly half must be re-authored around Greek homonyms rather than translated | judge over full compliance / partial refusal / full refusal, Greek judge prompt | localisation quality; keep the 10 prompt-type schema so the numbers stay interpretable |
| + | **MATH-500** | the upper half of "grade school → high school" for cross-lingual comparison; complements the native lyceum set | ~30k words, LaTeX untouched, Arabic numerals kept | boxed-answer exact match with our existing Greek-format equivalence checker; fully language-neutral | terminology must follow the Greek school curriculum; α/β/π collide with Greek prose; check overlap with our translated MATH train rows first |

Why this order: MultiChallenge is the only instrument for what the suite trains, and without it the suite arm cannot be judged except by our own regexes. IFBench is cheap and answers a question our reviewers keep raising. XSTest is the cheapest and closes the one-sided safety picture. MATH-500 is almost free but the native lyceum set should be adopted first.

Not recommended now: MT-Bench-101 (judge-heaviest, anaphora items become trivial in Greek), WildBench/LiveBench/τ-bench (long, rolling or tool-dependent), SimpleQA (Anglo-centric trivia), BFCL (we do not train tool use), GPQA Diamond (near chance for 8B).

## 4. Build plan and cost (if approved)

- Translation with Sol (24 workers, batches), cross-check by Luna or Opus, 5% native sample reviewed by the owner; per-benchmark translation-quality figure (share of items edited at cross-check, sample verdicts).
- Verifiers: IFBench Greek checkers built on our constraints.py conventions; MultiChallenge and XSTest judges built on the robustness judge pattern (binary fields, evidence spans, both answer orders).
- Decontamination gate as in subproject 09 (exact + long n-gram + MinHash against the SFT mix and the CPT corpus).
- Codex cost estimate at the observed 2.8% per 1,000 Sol calls: MultiChallenge full ≈ 600 calls (translation + check), IFBench ≈ 60, XSTest ≈ 100, MATH-500 ≈ 120 → about 2.5% of a weekly window. Cluster cost: evaluation only (minutes per arm).
- Order: IFBench and XSTest first (days), MultiChallenge subset next, full MultiChallenge and MATH-500 after the Codex reset on 15 Sep.

## 5. Open questions for the astra review

1. Is the ranking right for an 8B Greek SFT model whose next arm is the conversation-skills suite?
2. MultiChallenge in Greek: subset vs full, judge choice, how to keep the binary rubrics faithful, floor effects.
3. IFBench: which of the 58 constraints do not transfer to Greek and what should replace them; how to report overlap with our 44 trained families.
4. XSTest: localisation protocol for the homonym-driven prompts; is a Greek over-refusal set better built natively than localised?
5. Anything in the adopt list that should be treated as unreliable (MT quality, licence, contamination with Krikri-style training data)?

## Appendix A. Research report (web-search agent, 2026-09-09; URLs are the agent's citations, sizes checked via the Hugging Face API where possible)

### A.1 What already exists in Greek
ILSP / Athena RC's Greek Evaluation Suite (49 datasets under `ilsp/`, built for Meltemi arXiv:2407.20743 and Llama-Krikri arXiv:2505.13772):
- Chat/IF: `ilsp/mt-bench-greek` 80 × 2 turns, manually post-edited MT, GPT-4o judge (Krikri-8B-Instruct 7.96 EL vs 7.21 EN); `ilsp/m-ArenaHard_greek` 1,000 (500/500), Cohere m-ArenaHard → Google Translate v3 → post-edited with Claude Sonnet 3.5 v2, GPT-4o judge vs GPT-4o-mini baseline (Krikri 31.8%); `ilsp/ifeval_greek` 541, manual (Krikri 67.5% strict-avg EL vs 82.4% EN); `ilsp/vibeeval_greek` 269 (multimodal). No Greek AlpacaEval, no public Greek arena Space.
- Knowledge/reasoning: GreekMMLU (dascim, native, 21,805 MCQ, 45 subjects, 16,857 public / 4,948 private, arXiv:2602.05150, MIT); `ilsp/mmlu_greek` 31.7k MT; `ilsp/MMLU-Pro_greek` 12,000 test; `ilsp/arc_greek` 7,776; `ilsp/hellaswag_greek` 59,832; `ilsp/truthful_qa_greek` 817; `ilsp/winogrande_greek` 41,665 (all MT, CC-BY-NC-SA); `ilsp/greek-hle` 2,500 (MIT, gated, updated 2026-08-21).
- Math: `ilsp/mgsm_greek` 250 test + 8 few-shot, manually translated; `ilsp/greek_lyceum_mathematics` 465 native items (Ministry item bank); `ilsp/greek-geometry-3k` 3,002.
- Multilingual suites with Greek: Belebele `ell_Grek` (900, professional human translation, arXiv:2308.16884); Global-MMLU `el` (~14,042, MT; Greek not in the 15-language human-post-edited Lite set, arXiv:2412.03304); INCLUDE 552 test + 35 val native Greek exam items (`CohereLabs/include-base-44`); HumanEval-XL Greek NL prompts (23 NL × 12 PL, 22,080, arXiv:2402.16694); FLORES-200/FLORES+ (997 dev / 1,012 devtest); XNLI `el`; EU20 suite (ARC/HellaSwag/MMLU/TruthfulQA/GSM8K MT'd to 20 EU languages, arXiv:2410.08928).
- Without Greek: MMLU-ProX (29 languages, no `el`, arXiv:2503.10497); Multi-IF (en, fr, ru, hi, it, pt, es, zh, arXiv:2410.15553); M-IFEval (fr, ja, es, arXiv:2502.04688); MGSM original 10 (es, fr, de, ru, zh, ja, th, sw, bn, te); XCOPA/XStoryCloze/XWinograd/PAWS-X; Okapi (30 languages); OpenAI MMMLU (14 languages).
- EuroEval Greek (`dataset_configs/greek.py`): official greek-sa, ScaLA-el, ElNER, MultiWikiQA-el, greek-wikipedia summarisation, Winogrande-el, IFEval-el, RAGTruth-el, GreekMMLU, CulturaQA; unofficial GlobalMMLU-el, MultiIFEval-el, INCLUDE-el, EU-MMLU-el; the `EuroEval/*` HF repos are gated (401 unauthenticated). OpenEuroLLM covers Greek, no bespoke Greek eval suite published yet.
- Domain: GreekBarBench (`AUEB-NLP/greek-bar-bench`, 288 public test items, span-judge r=0.856 with experts, arXiv:2505.17267); `ilsp/medical_mcqa_greek` 2,034; `ilsp/mcqa_greek_asep` 1,200; `ilsp/greek-protipa-exams`; Plutus-ben (arXiv:2502.18772).
- Safety: `ilsp/attaq_greek` 1,402 (post-edited MT of IBM AttaQ); `ilsp/Jailbreak-StrongReject-el` 309 (MIT). No Greek over-refusal (XSTest/OR-Bench-style) benchmark exists; the Krikri paper states no systematic LLM-risk evaluation was performed.
- Culture/QA: `ilsp/greek_culture_bench` 1,951 public + 569 private (its card cites arXiv 2503.00995, a Polish paper; citation looks erroneous, unverified); `ilsp/greek_civics_qa` 407; DemosQA 600 (arXiv:2602.16811).
- No Greek multi-turn benchmark beyond MT-Bench-el's 2 turns; no Greek persona/identity or sycophancy benchmark.

### A.2 Standard post-training menu and translatability
| Benchmark | Items | Scoring | Translate? |
|---|---|---|---|
| IFEval (2311.07911) | 541, 25 instruction types | rule verifiers, strict/loose × prompt/instruction | verifiers are language-specific; exists in Greek |
| Multi-IF (2410.15553) | 4,501 conversations × 3 turns, 8 languages | per-turn verifiers | medium; no Greek |
| IFBench (2507.02833, NeurIPS 2025) | 294 prompts, 58 held-out constraints (+29 train) | code verifiers | easy text, hard verifiers |
| MT-Bench (2306.05685) | 80 × 2 turns | GPT-4 judge 1–10 | exists in Greek |
| MT-Bench-101 (2402.14762) | 1,388 dialogues / 4,208 turns, 13 tasks | GPT-4 judge, min score per dialogue | medium-hard, judge-dependent |
| Arena-Hard-Auto v0.1/v2.0 | 500 / 500+250 creative | pairwise judge + style control | exists in Greek (m-ArenaHard) |
| AlpacaEval 2 LC (2404.04475) | 805 | GPT-4-Turbo judge, length-controlled | judge-dependent |
| WildBench (2406.04770) | 1,024 real tasks | judge + checklists | hard, long |
| LiveBench (2406.19314) | 18 tasks, monthly refresh | objective ground truth | rolling |
| MMLU-Pro (2406.01574) | 12,032, 10 options | exact match + CoT | exists in Greek |
| GPQA Diamond (2311.12022) | 198 | exact match | easy, culture-neutral, near chance for 8B |
| BBH (2210.09261) / BBEH (2502.19187) | 6,511 / 4,720 | exact match | several tasks English-orthography-bound |
| MuSR (2310.16049) | 756, ~1,000-word items | MCQ exact match | expensive |
| MATH-500 / AIME | 500 / 30 per year | boxed exact match | easiest: LaTeX untouched |
| HumanEval+ / MBPP+ | 164 / 378–399 | code execution | Greek prompts exist via HumanEval-XL |
| LiveCodeBench | v6 = 1,055 | code execution | low value in Greek |
| BFCL v3/v4 | ~4,751 v3 (secondary source; v4 unverified) | AST match + execution | function names stay English |
| τ-bench / τ²-bench (2406.12045, 2506.07982) | 165 / ~278 | pass^k, state check | needs a Greek user simulator |
| SimpleQA (2411.04368) | 4,326 | LLM grader | Anglo-centric trivia |
| TruthfulQA (2109.07958) | 817 | MC1/MC2 + judge | exists in Greek; misconceptions culture-bound |
| XSTest (2308.01263) | 250 safe + 200 unsafe | refusal classifier / judge | easy text, needs lexical re-design |
| HarmBench / WildGuardTest (2406.18495) | 510 / 5,299 | fine-tuned classifiers | classifier English-only |
| MultiChallenge (2501.17399) | 273 conversations, ~5 turns, 1,231.7 words avg | LLM judge, binary rubric per target turn | medium-hard |
| LongMemEval (2410.10813) / LoCoMo (2402.17753) | 500 / ~1,540 | judge + F1 | very expensive |
| MTRAG (2501.03468) | 110 conversations / 842 turns | reference metrics + judge | RAG-specific |

### A.3 Methodology lessons from translated benchmarks
- MGSM used paid professional native translators with cross-checking and kept answers in Arabic numerals across all languages, so answer extraction stays language-agnostic (arXiv:2210.03057).
- MT'd eval sets degrade unevenly: an audit of Okapi vs EU20 found HellaSwag xCOMET-XXL ~0.42–0.65 vs ARC 0.97–0.98, with 600–744/1,000 HellaSwag items carrying accuracy errors, 87.6% major (arXiv:2604.01957); an Icelandic study rated MT'd ARC-is 20% OK / 37% incomprehensible vs 55% / 7% for professional localisation and found no valid item in MT'd HellaSwag-is, recommending against MT'd benchmarks (arXiv:2603.16406).
- Cultural specificity: 28% of MMLU questions need culturally sensitive knowledge, 84.9% of geography-dependent items target North America or Europe; rank volatility is higher on culturally sensitive subsets (arXiv:2412.03304); professional annotators edited 38.5% of gold samples; Google Translate beat GPT-3.5-turbo on ChrF++.
- Translation errors shift absolute scores ~6–11 pp but mostly preserve rankings (arXiv:2605.24904); Spanish MMLU lost 6–13% GPT-4 accuracy with post-editing recovering 41% of failures (Plaza et al. 2024); only 13.2% of 2,000+ surveyed non-English benchmarks are human-translated (arXiv:2504.15521).
- IF constraints do not translate mechanically: Multi-IF used Llama-3.1-405B + professional post-editing (~15% revised) and excludes inapplicable constraint categories per language; M-IFEval replaces English-orthography constraints with language-native ones (e.g. "do not use Katakana").
- LLM-judge scoring is the least translation-robust: round-trip-translated judge prompts shift win rates by 0.18–0.32 (arXiv:2504.11829); translated benchmarks correlate poorly with human preference (INCLUDE ρ = −0.26, MT-AIME24 ρ = −0.09, arXiv:2604.12911). MMLU-ProX used a 4-stage pipeline (Claude Sonnet 3.7 translation → self-reflection → improvement → cross-check by o3/GPT-4.1) plus 30+ experts and >400 labour-hours.
- Translation difficulty ranking by gain from a better pipeline: Winogrande +3.42% > ARC-C +2.35% > HellaSwag +1.63% > MMLU +0.94%; Winogrande is worst because target-language grammatical gender leaks the answer (arXiv:2602.22207), directly relevant to Greek. The current taxonomy (Original → MT → MT+revision → human translation → full localisation) recommends translation only for culture-agnostic content (arXiv:2510.24450).

### A.4 The agent's ranked shortlist
1. MultiChallenge (273 conversations; instruction retention 69, inference memory 113, versioned editing 41, self-coherence 50; ~336k words; binary per-turn rubric judge; frontier ~41.4%).
2. IFBench (294 prompts / 58 held-out constraints; ~15k words; Greek verifier engineering; keep the 29 training constraints out of the SFT mix).
3. XSTest (450 prompts; ~5k words; localisation of the homonym-driven half; judge over compliance/partial/full refusal).
4. MT-Bench-101 adaptability + interactivity subset (~7 tasks, ~130k words; judge-heaviest; anaphora items may become trivial in Greek).
5. MATH-500 (~30k words; boxed exact match; adopt `ilsp/greek_lyceum_mathematics` first, translate for cross-lingual comparability).
Cross-cutting: for 1, 3, 4 raw MT will not hold; use the MMLU-ProX pattern and report a translation-quality figure with the model scores.
