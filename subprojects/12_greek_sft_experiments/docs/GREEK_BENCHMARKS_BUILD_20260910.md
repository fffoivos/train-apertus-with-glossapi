# Greek benchmark build: MultiChallenge-el, IFBench-el, XSTest-el, MATH-500-el (2026-09-10)

Owner instruction (10 Sep): "make the benchmarks; have astra review them after you make them". Design constraints come from the two reviews (docs/NEXT_BENCHMARKS_RESEARCH_20260909.md §6, docs/BENCHMARKS_WORTH_RUNNING_20260910.md §7). Code and data: data/benchmarks_el/ (bench_lib.py shared; one directory per benchmark with source/, translate.py, judge or score script, cross-check verdicts, *_final.jsonl); provenance in data/benchmarks_el/MANIFEST.json; cost ledger data/benchmarks_el/cost_ledger.log.

## 1. Sources, pinned
| Benchmark | Upstream | Pinned | Items | Licence |
|---|---|---|---|---|
| MultiChallenge | github.com/ekwinox117/multi-challenge (Scale AI), arXiv:2501.17399 | commit 5ccefcca6a39 (2025-02-05) | 273 conversations (inference memory 113, instruction retention 69, self-coherence 50, versioned editing 41); 3–19 turns, median 946 words, 336,253 words total; last turn is always the user's | no licence file in the repository: research use only, the Greek version is not redistributable without permission |
| IFBench | github.com/allenai/IFBench + HF allenai/IFBench_test, arXiv:2507.02833 | commit 1c40f0c10d9b; HF revision 2e8a48de45ff | 300 prompts (the paper's 294 is a rounded figure; 44 prompts carry two constraints, 344 uses of 58 ids) | code Apache-2.0, data ODC-BY-1.0 |
| XSTest | github.com/paul-rottger/xstest, arXiv:2308.01263 | commit d7bb5bd738c1 (2025-02-24) | 450 prompts (250 safe, 200 unsafe; 18 types × 25) | CC-BY-4.0 |
| MATH-500 | HF HuggingFaceH4/MATH-500 (Lightman et al. subset of MATH test), arXiv:2305.20050 | HF revision 6e4ed1a2a79a | 500 problems (levels 1–5: 43/90/105/128/134; 7 subjects) | MIT |

## 2. Protocols kept from upstream
- MultiChallenge: fixed-history continuation; the judge sees only the response and the target question, "Be VERY STRICT", verdict YES/NO; pass = verdict == PASS_CRITERIA (always YES). Our judge (multichallenge/judge.py) reproduces the prompt verbatim with a pluggable backend (Claude via `claude -p` for arms trained on Sol data; Sol only for cross-judge audits) and a rubric-language switch (English default, Greek available).
- IFBench: per-prompt verifiable constraints, strict/loose × prompt/instruction accuracy; the 29 IFBench-train constraints are excluded from every SFT mix.
- XSTest: refusal taxonomy full compliance / partial refusal / full refusal; safe and unsafe scored separately; our addition: an adequacy label (a non-refusal that does not answer is not compliance).
- MATH-500: boxed-answer extraction + equivalence. Scorer validated on the 500 reference answers before use: self-equivalence 500/500, single-digit perturbation rejected 489/489, decimal-comma variants accepted (the shared SFT checker mathlib.equiv accepted 14 perturbed symbolic answers through its multi-number heuristics; the benchmark uses equiv500 = upstream strip_string normalisation + numeric + sympy, and mathlib.equiv now skips the heuristics for symbolic answers).

## 3. Translation pipeline (all four)
Sol (gpt-5.6-sol, effort medium, 24 workers) with the shared rules (faithful meaning and difficulty, all numbers/units/codes/LaTeX untouched, consistent entity forms, register preserved, natural Greek) plus per-benchmark rules; in-call self-check fields (entities, terms, issue, transfer class); programmatic checks (MATH-500: every math span and number identical, with a splice-back repair for lost backslashes; MultiChallenge: turn count and length ratio); cross-check by Claude Opus subagents (different vendor) on the critical subsets: all 450 XSTest items, all MATH-500 items flagged by any check plus a 59-item random audit, all MultiChallenge target questions plus a 59-conversation audit, all IFBench prompts and kwargs; Sol repairs what the cross-check flags; frozen *_final.jsonl with hashes in MANIFEST.json.

## 4. Results (filled in as stages complete)
### 4.1 MATH-500-el
500/500 translated; programmatic checks after repair: 499/500 (34 rows spliced, 4 re-translated, 1 flagged for the cross-check); 10 rows with translator-noted issues (English wordplay or invented words as objects of the problem); cross-check: pending.
### 4.2 XSTest-el
450/450 translated; transfer classes: faithful 409, substitute 41 (homonyms 12, figurative 14, safe_targets 4, definitions 3, safe_contexts 2, unsafe contrasts 6), native 0; naturalness 5: 416, 4: 32, 3: 2; cross-check: pending.
### 4.3 MultiChallenge-el
Pilot of 10: length ratio 1.09 (Greek/English words), 1/10 flagged non-transferable (avoidance of a specific English word); full run: in progress; cost: the Codex weekly reading did not move during the pilot (the reading is only refreshed by the probe, so the ledger records the probe before/after the full run).
### 4.4 IFBench-el
Transfer analysis (ifbench/TRANSFER_ANALYSIS.md): overlap with our 44 families = seen 2 ids / seen-in-novel-composition 22 / unseen 31 / unresolved 3 → prompts seen 10 / novel-composition 125 / unseen 153 / unresolved 12 (28 mixed); transfer = faithful 9 ids / adapt 47 / replace 2 / exclude 0; deliberate re-tunings (palindrome N 10→3, vowel cap ≤3→≤4, repeats small_n ≥5, sentence_alphabet 26→24, reverse_newline recount). Verifier port: in progress; prompt translation: pending the Greek descriptions.

## 5. Decontamination and exposure
Content overlap (decontam.py): 8-gram overlap of every item (English and Greek) against the local SFT sets (IF final 30,073, math cut1 14,215, conversation suite 858, personality) with the Tülu 3 rule (>50% of an item's 8-grams in one row, or any 13-gram): pending. Not checked locally: the CPT corpus (cluster job, DATA_TODO 32) and Apertus pretraining. Selection exposure: none (never run on any of our checkpoints). MATH-500 lineage: MATH test split; our SFT math translates MATH train levels 1–4 only (source identity disjoint; content check above covers accidental duplicates).

## 6. Owner audit and astra reviews
Reader pages with a random 59-item sample per benchmark for the owner's native audit (pending); astra reviews after the build (pending).
