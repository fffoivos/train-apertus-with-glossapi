# Greek instruction-following dataset: plan and pilot design

Date: 2026-09-08 (evening). Owner's brief: plans and experiments for the Greek instruction-following set; vary subjects and questions; cover every dimension of instruction following the literature names. Status: PLAN + pilot design; the repo inventory (§3) and the pilot numbers (§6) are filled in as they land.

## 1. Why this set, and what it must move

Round two's stage-1 mix is 49% constraint-following data by tokens, all of it English (IFEval-like 46,619 rows, Dolci Precise IF 3,934, Nemotron chat). It moved Greek IFEval from 56.2% to 63.7% strict average. The remaining gap to Krikri (66.8%) and the instruction types where the round-one pick scored 0.00 (`language:response_language`) point at constraints that transfer badly from English: language, script, register and Greek typography. Greek MGSM is the other gap and is not this set's job.

The set is verifiable by construction: every row carries a machine-checkable constraint list, the answer is checked before the row is kept, and the same checker becomes a training-time filter, a preference-pair source (pass vs fail on the same prompt) and a Greek IFEval-style evaluation. No judge in the loop.

## 2. The dimensions of instruction following (what the literature names)

Sources and what each contributes. Every family is a column of the generator; the pilot samples every family.

| family | source | what it covers | Greek-specific additions |
|---|---|---|---|
| **Format** | IFEval (Zhou et al. 2023): `detectable_format:*`, `detectable_content:*` | JSON output, markdown title `<<…>>`, N bullet points, N sections with a marker, N highlighted sections, placeholders `[…]`, postscript `P.S.`, constrained response ("My answer is yes/no/maybe"), multiple responses separated by `******` | Greek quotation marks «…», ano teleia (·) as list separator, Greek section markers («Ενότητα 1»), numbered lists with Greek letters (α΄, β΄, γ΄) |
| **Length** | IFEval `length_constraints:*` | number of words (at least / at most / around), sentences, paragraphs (separated by `***`), the Nth paragraph starting with a word | word counting on Greek tokens (tonos/dialytika do not split words), sentence boundaries on `.`, `;` (Greek question mark), `!`, `·` |
| **Keywords** | IFEval `keywords:*` | include words, exclude words, letter frequency, word frequency (word X at least N times) | inflected forms (the word must appear in a given case/number), a keyword in polytonic form, a letter frequency for Greek letters (e.g. «ω» at least 5 times) |
| **Language and script** | IFEval `language:response_language`; Multi-IF (He et al. 2024) | respond entirely in language X | respond in Greek to a Greeklish or English prompt; Greeklish output only; no Latin characters at all; ALL CAPS in Greek (capitalisation drops accents: «ΕΛΛΑΔΑ»); lowercase only; polytonic only; monotonic only (no polytonic marks); Ancient/katharevousa register markers (final -ν, dative) |
| **Change case** | IFEval `change_case:*` | all uppercase, all lowercase, N capital words | Greek uppercase rules (no accents in caps except dialytika), title case for Greek names |
| **Punctuation** | IFEval `punctuation:no_comma` | no commas | no commas; only Greek question marks (`;`), no Latin `?`; use ano teleia for lists; no exclamation marks |
| **Start / end** | IFEval `startend:*` | end with an exact phrase; wrap the whole response in double quotes | start with «Αγαπητέ/ή», end with a fixed Greek sign-off; wrap in «…» |
| **Combination and repetition** | IFEval `combination:*` | repeat the request first then answer; two responses | repeat the request in Greek then answer; give a formal and an informal version separated by a marker |
| **Content constraints** | InfoBench (Qin et al. 2024) decomposed rubrics; FollowBench "content" | must mention N facts, must not mention X, must answer only the sub-question, must include a date or a number | Greek entities: name the responsible Greek authority, give amounts in euros, dates in Greek order (ημέρα/μήνας/έτος) |
| **Situation and role** | FollowBench "situation"; Tulu 3 Persona-IF (Lambert et al. 2024) | a persona or scenario the answer must respect (a lawyer, a nine-year-old, a job ad) | Greek personas and settings: ΚΕΠ clerk, φροντιστήριο teacher, ναυτικός, ομογενής, μαθητής Γ΄ Λυκείου, δημοτικός υπάλληλος |
| **Style and register** | FollowBench "style"; InfoBench | tone, formality, simplicity, no adjectives, journalistic vs literary | πληθυντικός ευγενείας throughout; second person singular; καθαρεύουσα touches; village register; no loanwords; no Greeklish |
| **Example-driven (format by example)** | FollowBench "example" | follow the pattern of given examples (few-shot format) | same, with Greek examples |
| **Mixed / composite** | FollowBench difficulty levels 1–5 (number of constraints), ComplexBench (Wen et al. 2024) composition types: And, Chain, Selection | several constraints at once; ordered chains ("first … then …"); conditional ("if the topic is X do A else B") | the composition levels are the main knob of the pilot (§5) |
| **Multi-turn** | Multi-IF; our own picky-dialogue harness | constraints that accumulate over turns, corrections of earlier constraints, "now do it again but…" | the escalating dialogues of `evals/dialogues/picky_dialogues.py`, turned into training rows |
| **Negative / refusal within constraints** | CoCoNot (Brahman et al. 2024) | instructions that cannot be satisfied, contradictory constraints, unsafe requests inside a formatted task | refuse in our voice while still honouring the format constraints that can be honoured |
| **Reasoning under constraints** | IFBench / OLMo 3 IF (2025) held-out constraint types | unseen constraint wording, arithmetic on the constraint ("twice as many bullets as sentences") | unseen Greek phrasings of the same constraint, to test generalisation |

Checkability: families 1 to 8 and the composite levels are fully regex-checkable; content and situation constraints are checkable when phrased with a token to find (a name, a number, a phrase); style and example families need a judge and are kept to a minority (≤15% of rows) so the set stays verifiable.

## 3. What the repo already has (inventory)

Inventory taken 2026-09-08 evening (Explore agent over the subproject, `~/sft_annot/core_export` and `~/Projects/natural-greek-sft`).

**Evaluation and checkers.** The Greek IFEval task is vendored at `evals/ilsp/tasks/ifeval_greek/` (25 checker classes rewritten for Greek: accent-insensitive keyword matching, a Greek word counter that drops punctuation-only tokens, sentence split on `.`/`;`/`!`/`?`, section marker «Ενότητα», postscript «Υ.Γ.», constrained answers «Η απάντησή μου είναι ναι/όχι/ίσως»; 11 unit tests). The per-instruction table `results/ifeval_by_instruction.json` (541 prompts, 834 instruction instances) gives the round-one pick's weakest types against Krikri: two_responses 0.17 vs 0.83, nth_paragraph_first_word 0.00 vs 0.67, number_paragraphs 0.30 vs 0.78, number_placeholders 0.44 vs 0.89, no_comma 0.55 vs 0.97, letter_frequency 0.39 vs 0.64. One caveat: `language:response_language` (31 instances, 3.7% of the total) is 0.00 for every model including Gemma and Qwen, because the eval environment lacks `langdetect` and the fallback only recognises Greek; those points are unwinnable by data and recoverable by installing the package. `evals/dialogues/picky_dialogues.py` already maps free Greek constraint phrasings to checks (no accents, no Greek script, ≤N words, exactly N sentences, forbidden stems, adjective heuristic, number-only, English-only, formal plural) and carries four escalating multi-turn dialogues.

**English constraint data in the stage-1 mix.** `~/sft_annot/core_export/ifeval_like_raw.jsonl` (56,339 rows with `instruction_id_list` and `kwargs`, all passing the checkers) and `dolci_precise_if_20k.jsonl` (the Sol-screened window; the full 137k export had 27% content failures in a 300-row spot check). Type counts in ifeval-like are inversely related to our deficits: two_responses 11 rows, nth_paragraph_first_word 24, capital_word_frequency 28, no_comma 157, letter_frequency 1,063, against number_sentences 31,651. The Greek skill census of our own set has constraint following at 5%.

**Generation harness.** The batched, resumable, schema-enforced `codex exec` pattern (`data/gen_greek_rewrite.py`, `nsft/pair.py`: one call per chunk, output cached by id, strict post-validation, 24 workers, `--sandbox read-only --ephemeral`, `features.code_mode_host=false`, `project_doc_max_bytes=0`) and the usage-aware Claude lane (`data/personality/v2/claude_call.py`: pre-call gate at 62% of the 5-hour window, model assertion from `modelUsage`, limit detection in the body). Measured Sol throughput 1,100 rows/h generating at 24 workers.

**Topic and persona lists.** `gen_questions.py` USERS (16 personas) and six question forms; `gen_greek_rewrite.py` 20 genres × 40 topics × 15 tasks (DATA_TODO asks for a topic list ten times longer); the personality set's category G (style and conventions) is the closest existing Greek constraint taxonomy; `facts_greece.json` (110 facts) for grounding.

**What was missing, now built under `data/greek_if/`:** `constraints.py` (44 families, 40 regex-checkable, Greek phrasing banks, compatibility matrix, level sampler, checker; 39/40 checkers pass a good/bad unit pair, the formal/informal register checkers needed case-insensitive matching), `gen_prompts.py` (16 domains × 84 subtopics × 12 forms × 20 personas × levels 1–5, three prompt layouts, 10% repeated-constraint emphasis, persona surface: atonic, greeklish, formal), `gen_requests.py` (Sol writes the user requests per cell, the "authored" arm of E0), `run_pilot.py` (Sol answers in batches of 8, 24 workers, resumable), `score_pilot.py` (checker verdicts, per-family/level/domain/form/persona pass rates, wording invariance, prompt-diversity metrics).

## 4. The generator: subjects × questions × constraints

Three independent axes, sampled jointly so that every cell of the grid is populated and no axis correlates with another.

**Subjects (topics).** A tree, not a flat list, so diversity can be measured at two levels: 16 domains × 6 to 10 subtopics each ≈ 120 leaves. Domains: everyday life (household, shopping, neighbours), Greek public services (ΚΕΠ, ΑΑΔΕ, ΕΦΚΑ, ΕΟΠΥΥ, δήμος, ΔΕΗ), work and CVs, school and university, health (general information only), food and recipes, travel inside Greece, travel abroad, history and culture, language itself (grammar, spelling, meaning), science explanations, technology and phones, money and bills, sport, arts and media, relationships and etiquette.

**Question forms.** Twelve: quick fact, explanation, step-by-step instructions, comparison, opinion with reasons, creative writing (poem, story, ad), rewriting given text, summarising given text, translation, classification or list, planning, correction of a wrong premise. Rewriting, summarising and translation carry a source text drawn from a pool of short Greek passages so the constraint is applied to real material.

**Personas.** Twenty Greek user types with a register each (from `gen_questions.py` USERS plus new ones): a pupil writing without accents, a pensioner using the formal plural, a diaspora Greek in Greeklish, a civil servant, a journalist, a nurse, a farmer, a student abroad, a small-shop owner, a lawyer's assistant, a tourist learning Greek.

**Constraint sampling.** For each row: draw the composition level L ∈ {1,2,3,4,5} with weights 0.30, 0.30, 0.20, 0.12, 0.08 (FollowBench's ladder), then L constraint families without replacement, then one instantiation per family from its Greek phrasing bank (three to six phrasings per instantiation so the wording varies). Reject incompatible pairs (uppercase + lowercase, no commas + "use a comma-separated list") from a compatibility matrix.

**Prompt assembly.** The instruction is written as a Greek user would: the request first, then the constraints in a natural order, sometimes before the request, sometimes after, sometimes split across two sentences, 10% of the time with the constraint repeated for emphasis. No template should be recognisable across rows: the phrasing bank plus persona register produce the surface.

## 5. Pilot experiments (what we measure before scaling)

Each experiment is a small Sol run (batches of 8 prompts, 24 workers, the usual harness), scored by the checker; targets and readouts are fixed before the run.

| # | question | design | readout |
|---|---|---|---|
| E0 | Request variability: template-written vs Sol-authored user requests on the same cells | 300 rows each arm, same (domain, subtopic, form, persona, level 2) cells; templates from `gen_prompts.py` vs the bank from `gen_requests.py` | prompt-diversity metrics (12-token prefix share, mean 5-gram Jaccard, type-token ratio), pass rate, answer length; template arm measured before any Sol call: 19.9% of prompts share a 12-token prefix |
| E1 | Yield per constraint family: which constraints can Sol satisfy on the first try in Greek? | 40 rows per family, level 1 only, subjects and forms uniformly sampled | pass rate per family; families under 60% get a rewrite prompt or a checker fix |
| E2 | Yield by composition level | 60 rows per level 1–5, families uniform | pass rate vs L; the level at which yield drops under 50% sets the mix's ceiling |
| E3 | Subject variability: does the subject change yield or answer shape? | 15 rows per domain at level 2 | pass rate and answer length per domain; near-duplicate rate of prompts within a domain (character 5-gram Jaccard > 0.5) |
| E4 | Question-form variability | 20 rows per form at level 2 | pass rate per form; the forms where the constraint fights the task (a poem with no commas) |
| E5 | Greek-only families vs their English analogues | 40 rows each: no-accents, Greek uppercase, Greeklish out, formal plural, polytonic | pass rate and the failure modes (which we fix in the checker or the prompt) |
| E6 | Wording invariance | the same 60 (subject, constraint) pairs with three different Greek phrasings of each constraint | agreement of pass/fail across phrasings; a checker that disagrees with itself is a bug |
| E7 | Judge agreement on the non-checkable minority | 60 style/situation rows scored by Opus as a separate judge | agreement with a human read of 30; decides whether these families stay |

Diversity readouts on the union: distinct subjects covered, distinct (form, family) cells covered, mean pairwise 5-gram Jaccard across prompts, type-token ratio of the prompts, and the share of prompts that share a 12-token prefix with another prompt (the templated-feel measure).

Cost: about 700 rows for E1 to E6 at Sol's usual rate, one afternoon of the 24 workers; E7 a few dozen Opus calls.

## 6. Results

Filled after the pilot.

## 7. From pilot to the set

Target 10k rows for the first cut, then 30k. Composition: level 1 25%, level 2 30%, level 3 25%, level 4 12%, level 5 8%; Greek-only families at least 30% of rows; every domain at least 3% and no domain above 10%; every form at least 4%; style and situation families at most 15%. Every row keeps its constraint list and the checker verdict in metadata, so the assembler can filter and the DPO stage can build pairs. Multi-turn rows from the picky-dialogue pattern come as a second cut once the single-turn set trains.
