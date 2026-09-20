# Maths SFT data research — source-grounded report

Date: 2026-09-19. Target model: Apertus-8B + Greek CPT, **non-thinking**, hard 4,096-token
context (prompt + reply), RoPE trained only to 4,096.

**Evidence marking.** Every claim is tagged `[V]` VERIFIED with the URL shown, `[D]` DERIVED
(arithmetic I did from verified numbers — the inputs are verified, the arithmetic is mine),
or `[R]` RECALLED / unverified. Nothing here is invented; where I could not verify, I say so.

**Tokenizer caveat that applies everywhere.** The HF datasets-server `/statistics` endpoint
reports string lengths in **characters**, not tokens. All token figures below are `[D]`
conversions at **3.6 characters/token**, a mid-range figure for English maths prose with LaTeX
under a Llama-3-class BPE. I did **not** have a tokenizer available in this environment
(`transformers`, `tiktoken`, `pyarrow` all absent — verified by import failure), and I do not
know the Apertus tokenizer's fertility on English LaTeX. **Re-measure with the real Apertus
tokenizer before committing to a budget.** A ±15% error in chars/token moves every
"how many examples fit in 180M tokens" number below by ±15%.

---

## Q1. The three named datasets

### 1A. `nvidia/OpenMathInstruct-2`

**Rows and splits** `[V]` https://datasets-server.huggingface.co/size?dataset=nvidia/OpenMathInstruct-2

| split | rows | parquet bytes |
|---|---:|---:|
| `train` | **13,972,791** | 7,576,089,560 |
| `train_1M` | 1,000,000 | 639,053,029 |
| `train_2M` | 2,000,000 | 1,302,734,324 |
| `train_5M` | 5,000,000 | 3,110,146,543 |

Total across all four splits 21,972,791 rows / 12.63 GB — the 1M/2M/5M splits are
*fair-downsampled subsets of `train`*, not additional data `[V]` dataset card.

**Distinct problems vs solutions per problem** `[V]` paper Table 5 (ar5iv 2410.01560):

| Seed | Approach | # unique questions | # unique question–solution pairs |
|---|---|---:|---:|
| GSM8K | Solution augmentation | 7.4K | 0.46M |
| GSM8K | Question-solution augmentation | 73.6K | 2.11M |
| MATH | Solution augmentation | 7.4K | 2.46M |
| MATH | Question-solution augmentation | 519.1K | 8.94M |
| **Total** | | **607.3K** | **13.97M** |

Mean 23.0 solutions per unique question `[D]` (13.97M / 607.3K), but wildly uneven: the 14.8K
seed MATH+GSM8K problems carry 2.92M pairs (≈197 each `[D]`) while the 592.7K synthesized
problems carry 11.05M (≈18.6 each `[D]`). Abstract: "14M question-solution pairs (≈ 600K unique
questions)" `[V]` https://arxiv.org/abs/2410.01560.

**Fields** `[V]` `/info`: `problem`, `generated_solution`, `expected_answer`, `problem_source`
(4 string columns).

**Source mix.** `train_1M` (`/statistics`, `partial=false`, exact over 1,000,000 rows) `[V]`:
`augmented_math` 831,985 (83.2%), `augmented_gsm8k` 138,547 (13.9%), `gsm8k` 14,764 (1.48%),
`math` 14,704 (1.47%). **GSM8K lineage is only 15.3% of the fair-downsampled data** `[D]` —
directly relevant to your MGSM gap. (The same query on the full `train` split returns
`partial=true`, scanning only 4,803,150 of 13,972,791 rows, so those frequencies are a prefix
and are **not** representative — do not use them.)

**Verification — and what is NOT verified** `[V]` dataset card + paper §3:
- Solutions for *original* GSM8K/MATH train problems: kept only if the final answer matches the
  dataset's ground truth.
- Solutions for *augmented* (synthesized) problems: there is no ground truth. `expected_answer`
  is the **majority-voting answer over 32 sampled generations at temperature 0.7**. The card
  states this in bold. So for ~592K of the 607K unique problems the "correct answer" is a
  405B model's self-consistency vote, not a verified fact.
- **Intermediate reasoning is never verified.** The paper measures this: LLM-as-judge and
  Nemotron-4-340B-Reward each flag 6–12% of 405B-Instruct solutions as containing incorrect
  steps, and manual inspection of 20 such cases found ≈60% genuinely incorrect `[V]` paper
  §2.2.3 + Table 3.
- The team deliberately chose the *loosest* majority threshold: Table 9 `[V]`, min-votes
  0 → 381K data → **50.1**; 8 → 339K → 49.2; 16 → 254K → 44.4; 24 → 160K → 42.0. Filtering
  hurt.

**Teacher model** `[V]`: **Llama-3.1-405B-Instruct**, single teacher, nucleus sampling
(T=1.0/top-p=0.95 for the ablations; T=0.7, 32 samples/question for the synthesized questions).

**Solution style**: short chain-of-thought in the team's own "OpenMath CoT" format (prose +
display LaTeX, answer in `\boxed{}`). **Not** `<think>` traces. Sample verified from
`/first-rows?...&split=train_1M` `[V]`.

**Length and 4,096-token fit** — `train_1M`, exact, characters `[V]`:

| column | min | median | mean | max |
|---|---:|---:|---:|---:|
| `problem` | 13 | 198 | 238.3 | 13,633 |
| `generated_solution` | 190 | 897 | 1,075.8 | 5,743 |
| `expected_answer` | 0 | 3 | 6.4 | 628 |

`[D]` at 3.6 chars/token: solution median ≈ **249 tok**, mean ≈ **299 tok**, **max ≈ 1,595 tok**;
problem mean ≈ 66 tok. **Effectively 100% of `train_1M` rows fit in 4,096 tokens** — the longest
possible prompt+reply is ≈ 3,800 + 1,595 tok only if you pair the single longest problem with
the longest solution, and the paper reports only **564 questions (≈0.1%) exceed 1,024 Llama
tokens** across the whole dataset, with a recommendation to drop them (no performance loss, "in
fact a minor bump") `[V]` card "Note" section. **Per-example total ≈ 365 tokens** `[D]`
(238 + 1,076 chars ÷ 3.6). This is the single most important number for your budget.

**Licence** `[V]` card YAML: **`cc-by-4.0`**. Teacher outputs: Llama-3.1-405B-Instruct, and the
paper's stated motivation is "we leverage open-weight models instead of proprietary
closed-source LLMs allowing us to release the dataset under a permissive license" `[V]` §5.
The Llama 3.1 Community License's derivative-naming clause (models trained on Llama outputs
should carry "Llama" in the name) is a real-world obligation NVIDIA appears to have taken a
position on by releasing CC-BY-4.0; `[R]` I did not verify any legal opinion on this, and you
should check it yourself if the Apertus SFT model is released publicly.

**Decontamination — yes, and it covers MATH-500** `[V]` paper §3.1:
- Method: lm-sys/Yang et al. 2023 pipeline — Sentence-Transformer
  (`multi-qa-MiniLM-L6-cos-v1`) top-k=5 nearest test items, then **Llama-3.1-405B-Instruct as a
  zero-shot paraphrase judge**, run in both orders to cancel positional bias (10 LLM calls per
  synthesized question). Any flagged pair ⇒ question dropped.
- Benchmarks decontaminated against: **test sets of GSM8K, MATH, AMC 2023, AIME 2024**.
- **MATH-500 is a 500-problem subset of the 5,000-problem MATH test set, so it is covered by
  the MATH-test decontamination** `[D]` — the paper never names MATH-500 explicitly, so treat
  "MATH-500 specifically was decontaminated" as an inference, not a quoted claim.
- Effect: 569K → 519K synthesized questions (≈50K removed) `[V]` §3.1 and Appendix.
- **Not decontaminated: Omni-MATH** — released after training; post-hoc check found **≈1.4% of
  its test questions are in the training data** `[V]` Table 4 footnote 7.
- **MGSM: no statement at all.** `[R→not verified]` MGSM is a human translation of 250 GSM8K
  *test* problems; GSM8K test *was* decontaminated, so MGSM's source problems should be
  covered `[D]`, but nobody checked translated forms. Flag as residual risk.
- Residual by design: Table 11 shows near-miss pairs (e.g. MATH test "remainder when 5^30 is
  divided by 7" vs OMI-2 "remainder when 5^2005 is divided by 27") that are *kept*. This is
  intentional — they are different problems — but it means MATH-test-style problems are densely
  covered, which inflates MATH-500 relative to true generalization.

**Known quality problems** (all `[V]`): majority-vote answers for 97% of unique problems;
unverified intermediate reasoning with a measured 6–12% incorrect-step rate; 564 over-long
questions; the 70B model gained much less than the 8B one, which the authors attribute to the
data blend/format being "more suited for weaker models" (§4) — that is actually *encouraging*
for a weak Apertus base.

### 1B. `AI-MO/NuminaMath-1.5`

**Rows** `[V]` `/size`: **896,215** rows, one config `default`, one split `train`, 9 columns,
531 MB parquet.

**Distinct problems vs solutions per problem**: the card's source-breakdown table sums to
**896,215 problems**, exactly equal to the row count `[V]` card + `/size` ⇒ **one solution per
problem, 896,215 distinct problems** `[D]`. This is the mirror image of OMI-2: maximum question
diversity, zero solution multiplicity.

**Fields** `[V]` `/first-rows`: `problem`, `solution`, `answer`, `problem_type`, `question_type`,
`problem_is_valid`, `solution_is_valid`, `source`, `synthetic`.

**Source breakdown** `[V]` card:

| source | problems | proof | mcq | word |
|---|---:|---:|---:|---:|
| cn_k12 | 268,819 | 3,966 | 115,800 | 149,010 |
| olympiads | 197,084 | 62,970 | 13,529 | 117,845 |
| synthetic_math | 148,712 | 41 | 1,057 | 147,612 |
| orca_math | 151,934 | 1 | 17 | 151,916 |
| aops_forum | 67,841 | 24,532 | 5,924 | 33,486 |
| cn_contest | 29,944 | 8,663 | 5,602 | 15,649 |
| metamath | 11,014 | – | 82 | 10,932 |
| inequalities | 7,314 | 5,780 | 49 | 1,478 |
| amc_aime | 5,872 | 208 | 4,374 | 963 |
| number_theory | 4,043 | 2,591 | 15 | 1,239 |
| olympiads_ref | 3,638 | 2,246 | – | 1,392 |
| **Total** | **896,215** | **110,998** | **146,449** | **631,522** |

`/statistics` (`partial=false`) confirms: `question_type` = math-word-problem 631,522 /
MCQ 146,449 / proof 110,998 / other 2,030 / NaN 5,216 `[V]`.
`problem_type`: Algebra 422,915, Geometry 183,796, Number Theory 91,383, Combinatorics 73,643,
Inequalities 41,741, Logic and Puzzles 37,911, Calculus 26,965, Other 12,645 `[V]`.
`synthetic`: False 584,555 / True 311,660 `[V]`.

**Verification — mostly NOT verified** `[V]`: solutions are **scraped human reference
solutions** (exam PDFs, forums), not model generations, and are **not** checked against the
answer. The card adds metadata, not verification. The quality flags are themselves the warning:
- `problem_is_valid`: Yes 859,356 / Incomplete 30,377 / More than one problem 1,105 /
  Not a problem 158 / NaN 5,219 `[V]`
- `solution_is_valid`: Yes 844,988 / Incomplete 32,522 / Problem not solved 13,446 /
  Not matched with problem 32 / NaN 5,227 `[V]`
- `answer` is the literal string `proof` for proof problems and `notfound` where the answer
  could not be extracted `[V]` card.

**Teacher model**: none for solutions (human-written). An LLM was used for *metadata*
(`find_problem_type`) and, in v1.0, for parsing `[V]` card; the specific model is not named
`[not verified]`.

**Solution style**: short human prose proofs/derivations, **not** `<think>`. The first-rows
sample shows OCR-flavoured artefacts: leading `\n`, "Problem 1." prefixes, display-maths blocks,
and one sample where the text is visibly corrupted (`$a b\left(a^{2}+a b+b^{2}\right)=-c0$`,
`$a b-a b$`) — i.e. **mangled inequality signs from PDF extraction** `[V]` observed directly in
`/first-rows`.

**Length / 4,096 fit** `[V]` `/statistics` (`partial=false`), characters:
`problem` median 216 / mean 262.3 / max 45,303; `solution` median 807 / mean 965.0 / max 26,844;
`answer` median 5 / mean 9.1.
`[D]` solution median ≈ 224 tok, mean ≈ 268 tok, max ≈ 7,456 tok. The median row fits
comfortably; the tail does not. **I could not obtain percentiles** (the endpoint returns only
min/median/mean/max for string columns), so "what share fits 4,096" is **not verified** — but
given mean 965 and max 26,844 chars, a filter at ≤10,000 chars problem+solution (≈2,800 tok)
will retain the large majority `[D, approximate]`.

**Licence** `[V]` card YAML: **Apache-2.0**. No teacher-output restriction (human solutions).

**Decontamination: NONE STATED** `[V]` — I read the full card; it contains no decontamination
section, no mention of MATH-500, GSM8K test or MGSM. This is a material risk: `synthetic_math`
(148,712) and `metamath` (11,014) are MATH-train-derived rewrites, `orca_math` (151,934) is
GSM8K-style, and `amc_aime` (5,872) overlaps AMC/AIME evaluation sets. **Assume NuminaMath-1.5
is not decontaminated against your evals and run your own n-gram/embedding decontamination.**

**Known quality problems** (all `[V]`): 110,998 proofs and 146,449 MCQs are unusable for
verifiable-answer training; ~76k rows carry an explicit invalidity flag; PDF-extraction
corruption; the card itself says v1.5 removed `synthetic_amc` because "in our ablation study,
this hurt a bit the performance", and that v1.0's `olympiads` subset had "a lot of parsing
issues, due to the use of generic regular expressions and LLMs".

### 1C. `open-r1/OpenR1-Math-220k`

**Rows and configs** `[V]` `/size`:

| config | rows | parquet bytes | in-memory bytes |
|---|---:|---:|---:|
| `default` | **93,733** | 2,149,897,914 | 5,079,805,007 |
| `extended` | 131,396 | 2,063,936,457 | 4,770,393,404 |
| `all` | 225,129 | 4,221,672,067 | 10,161,169,949 |

Each config has a single `train` split. Card: "220k math problems with two to four reasoning
traces generated by DeepSeek R1 for problems from NuminaMath 1.5" `[V]`.

**Distinct problems vs traces per problem** `[V]` `/statistics` on `default`
(`partial=false`): **93,733 distinct problems**; `generations` list length min 1 / median 2 /
**mean 2.067** / max 6; `correctness_math_verify` mean 2.067; `correctness_count`
min 1 / median 2 / mean 1.779 / max 6. So ≈**2.07 traces per problem, of which ≈1.78 are
correct** `[V]`. `messages` is always length 2 (one user + one assistant) — i.e. one selected
trace rendered as chat `[V]`.

**Fields** (14) `[V]`: `problem`, `solution` (the *original NuminaMath human* solution, not
R1's), `answer`, `problem_type`, `question_type`, `source`, `uuid`, `is_reasoning_complete`
(bool list), `generations` (string list — the R1 traces), `correctness_math_verify` (bool list),
`correctness_llama` (bool list), `finish_reasons` (string list), `correctness_count` (int),
`messages` (chat list).

**Verification** `[V]` card: **Math-Verify** (rule-based, github.com/huggingface/Math-Verify)
for most samples, **Llama-3.3-70B-Instruct as judge for 12%** of samples; "each problem contains
at least one reasoning trace with a correct answer". The open-r1 update-3 blog reports the
filtering variants' surviving counts: "llama verification (124k), math_verify_answer (88.7k),
math_verify_reparsed (101k)" `[V]` https://huggingface.co/blog/open-r1/update-3. Note the
answer itself is inherited from NuminaMath-1.5 and is **not** independently verified.

**Teacher model** `[V]`: **DeepSeek-R1** (full 671B), via SGLang, prompt prefix
"Please reason step by step, and put your final answer within \boxed{}.", 16k token generation
limit, 25 solutions/hour/H100 on 512 H100s.

**Solution style: LONG `<think>` reasoning traces.** Verified directly from `/first-rows`: the
generation opens `<think>\nOkay, so I need to find the speed of the ship…` and runs a full
self-talk trace before the final boxed answer `[V]`. `messages[1].content` is the same trace
including the `<think>` block `[V]`.

**Length — this is the disqualifying number.** The card states the generation cap was 16k
tokens and that "only 75% of problems could be solved in under 8k tokens, and most of the
remaining problems required the full 16k tokens" `[V]`.
`[D]` independent cross-check from bytes: `default` in-memory size 4,964,543,659 B over 93,733
rows = **52,969 B/row**. Subtracting the verified non-trace content (`problem` mean 276.2 +
`solution` mean 945.5 + `answer` 11.7 + `uuid` 35.8 + labels ≈ 1,300 chars) and noting each row
stores ≈2.067 traces in `generations` **plus one more copy inside `messages`** (≈3.067 copies),
gives ≈ (52,969 − 1,300 − 276) / 3.067 ≈ **16,760 characters per trace ≈ 4,655 tokens**.
`/first-rows` truncates long cells so I could not measure the distribution directly (the API
returned degenerate 1-character entries for truncated rows) — **the 16,760-char figure is
derived arithmetic, not a measured percentile.** Both the card's statement and my derivation
point the same way.
**Share that fits your 4,096-token window (prompt + reply): a small minority, certainly under
25%** `[D]` — the card's own 8k figure already excludes 25%, and 4k is half of that.

**Licence** `[V]` card: **Apache-2.0**. Teacher = DeepSeek-R1, whose own licence is MIT
`[R, not verified here]` and which imposes no output restriction `[R]`.

**Decontamination: NONE STATED on the card** `[V]` — I read the full card. The `open-r1`
repository ships `scripts/decontaminate.py` (8-gram + dedup, "Following s1: Simple test-time
scaling") which "decontaminates against the benchmark datasets" `[V]`
https://raw.githubusercontent.com/huggingface/open-r1/main/README.md §"Data decontamination" —
but that is a tool users run, not something applied to the published 220k. Since every problem
comes from NuminaMath-1.5, **all of NuminaMath's contamination risk is inherited.**

**Known quality problems** `[V]`: the `extended` split (which adds `cn_k12`) **performs worse
after SFT** than `default` — "likely because the questions from `cn_k12` are less difficult";
12% of correctness labels come from an LLM judge rather than a rule; `is_reasoning_complete`
exists precisely because some traces are truncated at the 16k cap (`finish_reasons` list).

---

## Q2. The OpenMathInstruct-2 ablations (Toshniwal et al. 2024, arXiv 2410.01560)

All numbers `[V]` from ar5iv HTML of the paper unless marked. Ablation setup: Llama-3.1-8B-Base
as student, 1K held-out MATH-train validation split, remaining 6.5K MATH-train problems as the
SFT pool, 4 epochs, batch 256, AdamW, constant LR 5e-6, **results averaged over 4 runs** with
±std reported.

### (a) Question diversity vs solutions per question — the headline for your hypothesis

> "To investigate the impact of question diversity on SFT performance, we construct finetuning
> datasets with **256K question-solution pairs** with the number of unique questions varying
> from {1K, 2K, 4K, 6.5K}. Figure 6 shows a clear trend that the SFT performance improves with
> an increase in the number of unique questions, with a drop of **more than 10 points** when the
> number of unique questions is limited to 1K." `[V]` §2.2.4

Bullet form in §1: "Controlling for SFT data size, we find that question diversity has a huge
positive impact on SFT performance. Increasing the number of unique questions from 1K to 6.5K
leads to **10.5% improvement** on MATH validation set." `[V]`

Abstract conclusion (d): "**question diversity is crucial for achieving data scaling gains**"
`[V]`.

**Read this carefully against your hypothesis.** At a *fixed token budget*, going from 256
solutions/question (256K ÷ 1K) to 39 solutions/question (256K ÷ 6.5K) bought +10.5 points. The
paper does **not** say k>1 is useless — the whole dataset averages 23 solutions/question — it
says that **when you can spend a token on a new problem instead of a repeat solution, spend it
on the new problem.** Figure 6's exact per-point values are in an image, not in the text; only
the 1K→6.5K delta (10.5) is stated `[V]`, the intermediate 2K/4K values are **not verified**.

### (b) Solution format / verbosity — Table 1 `[V]`

| Format | MATH validation accuracy | Mean solution length (tokens) |
|---|---|---:|
| Llama CoT | 40.6 ± 0.6 | 331.3 |
| **OpenMath CoT** | **44.5 ± 0.8** | **237.0** |

"+3.9% while being 40% shorter" `[V]` §1. Abstract (a): "solution format matters, with
**excessively verbose solutions proving detrimental** to SFT performance" `[V]`.
Matched at 260K pairs via the "Matching Coverage" operation so size is controlled `[V]` §2.2.1.
Note the mean solution is **237 tokens** — this is a measured, tokenizer-based figure from the
authors and it corroborates my `[D]` 299-token estimate from the character statistics.

### (c) Teacher strength vs on-policy (student-generated) data — Table 2 `[V]`

| Teacher | MATH validation accuracy | Mean solution length (tokens) |
|---|---|---:|
| Llama3.1-8B-Base (the student itself) | 30.1 ± 0.6 | 205.7 |
| **Llama3.1-405B-Instruct** | **37.9 ± 0.6** | 180.2 |

**+7.8 points for the strong teacher, at matched coverage** (same unique questions, same
solutions-per-question) `[V]` §1, §2.2.2. Their explanation: "weaker models generate more noisy
solutions that use incorrect reasoning yet end up with the right answer and, ultimately, part of
the SFT dataset" `[V]`. Abstract (b) `[V]`.

**Direct implication for you:** self-generated (on-policy) Greek solutions from your own 8B are
the *weak-teacher* condition, and this ablation says that is worth ~8 MATH points less than
distilling a strong teacher — which is consistent with your 9k-Greek-worked-solutions pilot
moving nothing.

### (d) Robustness to wrong-answer / low-quality solutions

*Removing* low-quality solutions — Table 3 `[V]` (128K fair-downsampled base):

| Filtering strategy | Data size | MATH validation accuracy |
|---|---:|---|
| Unfiltered | 128K | 43.6 ± 1.7 |
| LLM-as-a-Judge: Prompt 1 | 113K | 43.6 ± 0.1 |
| LLM-as-a-Judge: Prompt 2 | 116K | 43.0 ± 0.8 |
| Nemotron-4-340B-Reward: Helpfulness ≥ 3 | 118K | 43.8 ± 0.4 |
| Nemotron-4-340B-Reward: Correctness ≥ 3 | 120K | 43.1 ± 0.4 |

"The proportion of data filtered ranges from 6% to 12% … Yet **none of the filtering strategies
give any meaningful gain** over the baseline Unfiltered model." `[V]`
Table 6 repeats this for the 8B-Base teacher (29.8 unfiltered vs 28.1–30.5 filtered) `[V]`.

*Adding* bad solutions (Figure 5, numbers in image; the text states the finding) `[V]` §2.2.3:
two corruptions — **Wrong-answer Solutions** (teacher generations that missed ground truth) and
**Incorrect Pairing** (correct solutions shuffled onto unrelated questions) — injected at
{10%, 20%, 40%, 80%} across data sizes {64K, 128K, 256K, 512K, 1024K}:

> "the model performance suffers **little to no performance degradation with as much as 20%
> incorrect solutions at data scales ≥ 256K**. Among the two strategies, we see that the model
> is especially robust to 'Incorrect Pairing' with strong performance even with 40% incorrect
> solutions." … "models are indeed robust to the presence of up-to 20% of low-quality solutions
> during SFT and **extensive data filtering at this stage has limited gains**."

Note the size condition: robustness holds **at ≥256K examples**. At your current ~57K-example
scale `[D]` you are in the regime where the paper did *not* claim robustness.

Corroborating Table 9 (majority-vote threshold on synthesized questions) `[V]`:
min-votes 0 / 381K / **50.1**; 8 / 339K / 49.2; 16 / 254K / 44.4; 24 / 160K / 42.0. Keeping
everything, including problems whose "answer" only got a plurality, beat every stricter filter.

### (e) Data scaling for Llama-3.1-8B-Base — 1M / 2M / 5M / 14M

The paper states: "With even the 1M fair-downsampled version … the final model easily
outperforms Llama3.1-8B-Instruct and NuminaMath-7B-CoT. We observe a consistent gain with an
increase in data size, and even at **14M dataset size, we see no signs of saturation**." `[V]`
§4. The per-point values live only in the scaling figure, so I downloaded
`scaling_plot.jpg` from the dataset repo and read it directly:

| SFT data size | MATH test accuracy |
|---|---:|
| 0 (Llama3.1-8B-Base) | ≈ 20.3 |
| **1M** | **≈ 61.2** |
| **2M** | **≈ 64.5** |
| **5M** | **≈ 66.6** |
| **14M** (OpenMath2-Llama3.1-8B) | **67.8** |

`[V]` for the 14M endpoint (67.8, stated in text, card and Table 4) and for the y-axis anchors
(Llama3.1-8B-Instruct reference line at 51.9, "+15.9"); **`[D/read-from-figure]` for the 1M, 2M,
5M and base values** — these are my readings of plotted marker positions against gridlines at
`https://huggingface.co/datasets/nvidia/OpenMathInstruct-2/resolve/main/scaling_plot.jpg`,
accurate to roughly ±0.5 points, not quoted numerals.

GSM8K is **not** plotted against data size; only the final 14M model's GSM8K is reported
(91.7) `[V]` Table 4. **No GSM8K-vs-data-size curve exists in this paper** — flagging because
your question asked for it.

**The shape is the finding.** Base→1M is +40.9 points; 1M→14M is only +6.6 `[D]`. 86% of the
total gain is bought by the first million examples. The curve is concave from 1M onward even
though the authors correctly note it has not flattened.

**Final model table (Table 4)** `[V]`, for calibration:

| Model | GSM8K | MATH | AMC 2023 | AIME 2024 | Omni-MATH |
|---|---:|---:|---:|---:|---:|
| Llama3.1-8B-Instruct | 84.2 | 51.8 | 9/40 | 2/30 | 12.7 |
| NuminaMath-7B-CoT | 75.4 | 55.2 | 11/40 | 0/30 | – |
| **OpenMath2-Llama3.1-8B** | **91.7** | **67.8** | 16/40 | 3/30 | 22.0 |
| + maj@256 | 94.1 | 76.1 | 23/40 | 3/30 | 24.6 |
| Qwen2.5-Math-7B-Instruct | 95.2 | 83.6 | 25/40 | 5/30 | 32.3 |
| OpenMath2-Llama3.1-70B | 94.9 | 71.9 | 20/40 | 4/30 | 23.1 |

(The card's version of this table lists Llama3.1-8B-Instruct at GSM8K 84.5 / MATH 51.9; the
paper's Table 4 says 84.2 / 51.8. Minor discrepancy, both `[V]`, immaterial.)

Training recipe for the released models `[V]` §4: batch 512, AdamW, **constant LR 2e-5**, weight
decay 1e-2, **2 epochs**, 6 equally-spaced checkpoints averaged. (70B: LR 1e-5, 5M subset only.)

---

## Q3. Other evidence on size vs diversity vs solutions-per-problem at 7–8B

### Yuan et al. 2023, "Scaling Relationship on Learning Mathematical Reasoning with LLMs" (arXiv 2308.01825)

Abstract `[V]` https://arxiv.org/abs/2308.01825:
> "We apply supervised fine-tuning (SFT) with different amounts of supervised data and
> empirically find a **log-linear relation between data amount and model performance**, and we
> find **better models improve less with enlarged supervised datasets**. … We propose to apply
> **Rejection sampling Fine-Tuning (RFT)**. … We find with augmented samples containing **more
> distinct reasoning paths, RFT improves mathematical reasoning performance more** for LLMs. We
> also find **RFT brings more improvement for less performant LLMs**. Furthermore, we combine
> rejection samples from multiple models which push LLaMA-7B to an accuracy of **49.3%** on
> GSM8K which outperforms the supervised fine-tuning (SFT) accuracy of **35.9%** significantly."

Base model: **LLaMA-7B/13B/33B/65B and LLaMA-2** on **GSM8K** (7.5K train questions — a fixed
question set). The per-model RFT k=100 / RFT-U13B table is in the paper body, not the abstract;
I did **not** verify those individual cells `[not verified]`. MetaMath's card independently
lists "RFT-7B 50.3" on GSM8K `[V]` meta-math/MetaMathQA README.

**This is the strongest published support for your "more distinct solutions per problem"
hypothesis — but note the regime.** GSM8K's question set is *fixed at 7.5K*; you cannot add
questions, so the only axis left is distinct reasoning paths, and it works. It also explicitly
says the benefit is larger for *weaker* models — which is you. It does **not** say k beats new
questions when new questions are available; OMI-2 §2.2.4 tests exactly that and says the
opposite.

### MetaMath / MetaMathQA (arXiv 2309.12284)

Abstract `[V]`: bootstraps questions "by rewriting the question from multiple perspectives
without extra knowledge"; **MetaMath-7B: 66.4% GSM8K / 19.4% MATH**, "exceeding the
state-of-the-art models of the same size by 11.5% and 8.7%"; MetaMath-70B: 82.3% GSM8K. Base:
**LLaMA-2**.
Card table `[V]` (slightly different from the abstract, both from the authors): MetaMath-7B
66.5 / 19.8; MetaMath-13B 72.3 / 22.4; **MetaMath-Mistral-7B 77.7 / 28.2** — i.e. **+11 GSM8K
points from swapping the base model alone, same data**. Relevant to you: base quality dominates.

Composition, measured exactly `[V]` `/statistics` on `meta-math/MetaMathQA` (`partial=false`),
`type` frequencies over 395,000 rows:
GSM_Rephrased 80,000 · GSM_AnsAug 80,000 · MATH_AnsAug 75,000 · MATH_Rephrased 50,000 ·
GSM_FOBAR 40,000 · GSM_SV 40,000 · MATH_SV 15,000 · MATH_FOBAR 15,000.
⇒ **240,000 GSM8K-derived + 155,000 MATH-derived** `[D]`, all from the **7,473 GSM8K + 7,500
MATH train questions** ⇒ ≈26 samples per seed question `[D]`. Card: "All MetaMathQA data are
augmented from the training sets of GSM8K and MATH. **None of the augmented data is from the
testing set.**" `[V]`
Lengths `[V]`: `query` median 198 chars, `response` **median 426 / mean 498 / max 5,367 chars**
⇒ `[D]` response median ≈ 118 tok, mean ≈ 138 tok, max ≈ 1,491 tok. **The shortest solutions of
any candidate; 100% fit 4,096.**
Teacher: **GPT-3.5** `[V]` per the DART-Math comparison table. Licence **MIT** `[V]`.

### MathScale / MathScaleQA (arXiv 2403.02884)

Abstract `[V]`: extracts topics/knowledge points from seed questions, builds a **concept graph**,
generates new questions; **MathScaleQA = 2 million** QA pairs; teacher **GPT-3.5**; fine-tunes
LLaMA-2 and Mistral; MathScale-7B "surpassing its best peers of equivalent size by 42.9% in
micro average accuracy and 43.7% in macro average accuracy" on their own MwpBench.
DART-Math's comparison table `[V]` gives MathScaleQA at 2021k samples → **MATH 35.2 / GSM8K
74.8 / College 21.8** on Mistral-7B, and marks it **✗ not open-source**. I found no public HF
repo (`MathScale/MathScaleQA-2M` returns an error from the datasets-server `[V]`).
**⇒ Not usable. Listed only as evidence that 2M GPT-3.5-generated pairs reach only MATH 35.2 —
teacher strength caps the ceiling.**

### Skywork-Math (arXiv 2407.08348)

Abstract `[V]`:
> "We argue that the **data scaling law for math reasoning capabilities in modern LLMs is far
> from being saturated** … supervised fine-tuned (SFT) on **common 7B LLMs** using our proposed
> **2.5M-instance Skywork-MathQA dataset**. Skywork-Math 7B has achieved impressive accuracies
> of **51.2% on the competition-level MATH benchmark and 83.9% on the GSM8K benchmark using only
> SFT data**, outperforming an early version of GPT-4 on MATH. The superior performance …
> contributes to our novel **two-stage** data synthesis and model SFT pipelines, which include
> **three different augmentation methods and a diverse seed problem set**, ensuring both the
> quantity and quality … across varying difficulty levels."

The per-base-model breakdown (LLaMA2-7B / DeepSeekMath-7B / Mistral-7B) and the 0.5M→2.5M
scaling table are in the body, **not verified**. The abstract's own framing — "diverse seed
problem set" + "varying difficulty levels" + 2.5M — is the same recipe as OMI-2.

### DART-Math (arXiv 2407.13690) — difficulty-aware rejection sampling

`[V]` https://huggingface.co/datasets/hkust-nlp/dart-math-hard (full card read):
- **`dart-math-hard` 585,392 rows; `dart-math-uniform` 590,705 rows** `[V]` `/size`.
- **Queries come only from MATH + GSM8K training splits** ⇒ ≈**15K distinct problems**, so ≈39
  responses per problem `[D]`. The card is explicit: "based solely on MATH & GSM8K prompt set".
- Teacher: **DeepSeekMath-7B-RL** (an open 7B model, not GPT-4).
- Verification: rejection sampling against ground-truth answers (only correct responses kept).
- **The core finding:** vanilla rejection tuning is "severely biased towards easy queries, with
  frequent failures to generate any correct response for the most challenging queries".
  *Uniform* samples until each query has k_u correct responses; *Prop2Diff* makes the count
  **proportional to difficulty**, deliberately over-weighting hard problems.
- Results on **Mistral-7B** `[V]` card table (MATH / GSM8K / College):
  MetaMathQA 395k → 29.8 / 76.5 / 19.3 · MMIQC 2294k → 37.4 / 75.4 / 28.5 ·
  MathScaleQA 2021k → 35.2 / 74.8 / 21.8 · **DART-Math-Uniform 591k → 43.5 / 82.6 / 26.9** ·
  **DART-Math-Hard 585k → 45.5 / 81.1 / 29.4** · (Xwin-Math-V1.1 1440k, GPT-4, Llama2-7B →
  45.5 / 84.9 / 27.6; KPMath-Plus 1576k, GPT-4 → 46.8 / 82.1, both closed).
- Lengths `[V]` `/statistics` (`partial=false`): `query` median 195 chars; `response`
  **median 995 / mean 1,302 / max 13,968 chars** ⇒ `[D]` median ≈ 276 tok, mean ≈ 362 tok,
  max ≈ 3,880 tok. Fits 4,096 with a tail filter.
- Licence **MIT** `[V]`.

**This is the cleanest published test of "more solutions per problem, allocated by difficulty".
It works: 585k responses over 15k problems beats 2M GPT-3.5 pairs over many more problems
(45.5 vs 35.2 MATH).** But the teacher and the base differ across those rows, so it is not a
controlled k-vs-diversity experiment the way OMI-2 §2.2.4 is.

### MAmmoTH2 / WebInstruct (arXiv 2405.03548)

Abstract `[V]`: harvests **10 million** naturally-occurring instruction pairs from a pre-training
web corpus (recall → extract → refine with open LLMs). "**MAmmoTH2-7B's (Mistral) performance
increases from 11% to 36.7% on MATH and from 36% to 68.4% on GSM8K without training on any
in-domain data.**" The 8B/8x7B and TheoremQA cells are in the body, **not verified**.
`TIGER-Lab/WebInstructFull` = **13,479,418 rows** `[V]` `/size`;
`TIGER-Lab/WebInstruct-verified` = 228,736 train + 1,000 test + 231,833 train_legacy, **Apache-2.0**
`[V]`.
Relevance: proves *out-of-domain, naturally-occurring* maths text transfers — but 36.7 MATH is
well below OMI-2's 67.8.

### ScaleQuest (arXiv 2410.18693)

Abstract `[V]`: two-stage question-tuning (QFT + QPO) unlocks **7B-scale models** to generate
questions **from scratch, no seed data, no proprietary model**; "we produce a dataset of **1
million problem-solution pairs**"; "models trained on our data **outperform existing open-source
datasets** in both in-domain and out-of-domain evaluations"; "**continued performance
improvement as the volume of training data increases**". The per-model MATH/GSM8K table is in
the body, **not verified**.
`dyyyyyyyy/ScaleQuest-Math` = **1,003,467 rows**, **Apache-2.0** `[V]`; fields `query`,
`response`; `/statistics` (`partial=false`) `query` median 166 / mean 195 chars, `response`
**median 1,101 / mean 1,214 / max 7,096 chars** `[V]` ⇒ `[D]` response median ≈ 306 tok, mean
≈ 337 tok, max ≈ 1,971 tok — **100% fits 4,096**. Questions are generated per-row, so
≈1M distinct problems with 1 solution each `[D, inferred from row count = pair count]`.

### AceMath (arXiv 2412.15084)

Abstract `[V]`: "a supervised fine-tuning (SFT) process that **first achieves competitive
performance across general domains, followed by targeted fine-tuning for the math domain**".
Base: **Qwen2.5-Math**. Data card `[V]`
https://huggingface.co/datasets/nvidia/AceMath-Instruct-Training-Data:
general_sft_stage1 **2,261,687**; general_sft_stage2 **1,634,573**; **math_sft 1,661,094**
(confirmed by `/size` `[V]`). Teacher: **math prompts answered by Qwen2.5-Math-72B-Instruct**,
other prompts by **GPT-4o-mini**; "Built with Qwen". Card: "fine-tuning the Qwen2.5-Math-Base
models using **only the math-specific SFT data also delivers competitive math reasoning
performance**" — i.e. the staging is helpful but not load-bearing `[V]`.
"AceMath-7B-Instruct largely outperforms Qwen2.5-Math-7B-Instruct (Average pass@1: **67.2 vs.
62.9**)" `[V]` card. Per-benchmark GSM8K/MATH-500 cells **not verified** (they are in an image on
the card).
**Licence `cc-by-nc-4.0` — non-commercial.** `[V]`

### LIMO (arXiv 2502.03387) and s1 (arXiv 2501.19393) — why they do NOT apply to you

LIMO abstract `[V]`: "LIMO achieves **63.3% accuracy on AIME24 and 95.6% on MATH500**, surpassing
previous fine-tuned models (6.5% on AIME24, 59.2% on MATH500) while using only **1% of the
training data**". Dataset `GAIR/LIMO` = **817 rows**, Apache-2.0 `[V]` `/size` + API.
Base model: **Qwen2.5-32B-Instruct** `[V]`
https://raw.githubusercontent.com/GAIR-NLP/LIMO/main/README.md.
The paper's own stated precondition is **"the completeness of the model's pre-trained knowledge
base"** `[V]` — i.e. the claim is that the reasoning ability is already latent in pre-training
and 817 examples merely elicit its *format*.

s1 `[V]` https://arxiv.org/abs/2501.19393: **s1K = 1,000 questions** with reasoning traces
selected for difficulty/diversity/quality; base **Qwen2.5-32B-Instruct**; "exceeds o1-preview on
competition math questions by up to 27%"; budget forcing (appending "Wait") lifts AIME24
**50% → 57%**. `simplescaling/s1K` and `s1K-1.1` = **1,000 rows** each `[V]`; s1K-1.1 **MIT**.

**Why these do not transfer to Apertus-8B-Greek-CPT** `[D]`, with the load-bearing facts `[V]`:
1. Both use a **32B instruct model that was already heavily maths-post-trained** (Qwen2.5 family;
   OMI-2 Table 4 shows Qwen2.5-Math-7B-Instruct at MATH **83.6** *before* anyone adds 1K
   examples). Your base is at MATH 13%.
2. LIMO's own condition — a "complete pre-trained knowledge base" — is precisely what an 8B
   model with Greek CPT and no maths-heavy pre-training does not have.
3. Both are **long-CoT elicitation** (s1 literally scales *thinking length* at test time, LIMO's
   traces are long). You have a **non-thinking 4,096-token model**; you cannot spend test-time
   tokens.
4. The directly-relevant negative result: **"Small Models Struggle to Learn from Strong
   Reasoners"** (arXiv 2502.12143) `[V]`:
   > "we uncover … the **Small Model Learnability Gap**: small models (≤3B parameters) do not
   > consistently benefit from long chain-of-thought (CoT) reasoning or distillation from larger
   > models. Instead, **they perform better when fine-tuned on shorter, simpler reasoning chains
   > that better align with their intrinsic learning capacity.** … we propose **Mix
   > Distillation** … combining long and short CoT examples."
   Their threshold is ≤3B, not 8B — **so this is suggestive for an 8B model, not proof** `[D]`.
   But it points the same way as OMI-2's verbosity ablation (Table 1: shorter format, +3.9).

---

## Q4. Short-CoT alternatives and additions that fit 4,096 tokens

All row counts `[V]` from `datasets-server /size`; all licences `[V]` from
`https://huggingface.co/api/datasets/{id}` `cardData.license`; all length statistics `[V]` from
`/statistics` with `partial=false`, in **characters**; token columns are `[D]` at 3.6 chars/tok.

| Dataset | Rows | Distinct problems | Style | Verification | Teacher | Sol. median → `[D]` tok | Licence |
|---|---:|---:|---|---|---|---|---|
| `nvidia/OpenMathInstruct-2` | 13,972,791 | **607.3K** | short CoT, `\boxed{}` | answer-match (seeds) / **majority-of-32** (augmented); reasoning unverified | Llama-3.1-405B-Instruct | 897 ch → ~249 | **cc-by-4.0** |
| `AI-MO/NuminaMath-1.5` | 896,215 | **896,215** | human prose | **none**; validity *flags* only | human (scraped) | 807 ch → ~224 | **apache-2.0** |
| `AI-MO/NuminaMath-CoT` | 859,494 (+100 test) | 859,494 | human/LLM CoT | none | mixed | 996 ch → ~277 | **apache-2.0** |
| `meta-math/MetaMathQA` | 395,000 | **~15K** (GSM8K+MATH train) | very short CoT | answer-consistent augmentation | GPT-3.5 | **426 ch → ~118** | **mit** |
| `hkust-nlp/dart-math-hard` | 585,392 | **~15K** | short CoT | **rejection sampling vs ground truth** | DeepSeekMath-7B-RL | 995 ch → ~276 | **mit** |
| `hkust-nlp/dart-math-uniform` | 590,705 | ~15K | short CoT | same | DeepSeekMath-7B-RL | *(not measured)* | **mit** |
| `dyyyyyyyy/ScaleQuest-Math` | 1,003,467 | **~1,003,467** | short CoT | reward/solvability filtering `[R]` | 7B open models | 1,101 ch → ~306 | **apache-2.0** |
| `microsoft/orca-math-word-problems-200k` | 200,035 | 200,035 | short worked answers | **none stated** | **GPT-4-Turbo** (Azure) | *(not measured)* | **mit** |
| `TIGER-Lab/MathInstruct` | 262,039 | – | **mixed CoT + PoT (code)** | – | GPT-4/GPT-3.5 | – | **mit** |
| `nvidia/OpenMathInstruct-1` | 5,752,065 train + 1,127,629 val | ~15K (GSM8K+MATH train) | **code-interpreter** (text+Python) | answer-match + execution | Mixtral-8x7B | – | **`other` / nvidia-license** |
| `TIGER-Lab/WebInstruct-verified` | 228,736 train (+1,000 test, +231,833 legacy) | – | web-harvested QA | "verified" subset | open LLM refinement | – | **apache-2.0** |
| `nvidia/AceMath-Instruct-Training-Data` (`math_sft`) | 1,661,094 | – | short CoT | – | Qwen2.5-Math-72B-Instruct | – | **cc-by-nc-4.0 (NC!)** |
| `allenai/tulu-3-sft-personas-math` | 149,960 | 149,960 | worked solutions | none | **GPT-4o + Claude 3.5 Sonnet** | – | **ODC-BY** + 3rd-party ToS |
| `allenai/tulu-3-sft-personas-math-grade` | 49,980 | 49,980 | grade-school | none | same | – | **ODC-BY** + ToS |
| `allenai/tulu-3-sft-personas-algebra` | 20,000 | 20,000 | algebra | none | same | – | **ODC-BY** + ToS |
| `allenai/Dolci-Instruct-SFT` | 2,152,112 | – | non-thinking instruct mix | – | – | – | **odc-by** |
| `MegaScience/MegaScience` | 1,253,230 | – | science+maths step-by-step | reference answers | – | – | **cc-by-nc-sa-4.0 (NC!)** |
| `nvidia/Llama-Nemotron-Post-Training-Dataset` `SFT/math` | 276,536 | – | **`<think>`, reasoning=on for 100%** | – | Qwen-2.5-32B-Instruct, DeepSeek-R1 | **15,006 ch → ~4,168** | **cc-by-4.0** |
| `HuggingFaceTB/smoltalk2` `SFT/OpenThoughts3_1.2M_no_think_no_think` | 435,193 | – | reasoning-distilled, think stripped | – | – | – | **none declared** |
| MathScaleQA (2,021k) | — | — | — | — | GPT-3.5+Human | — | **NOT RELEASED** |

Notes that matter:

- **`Llama-Nemotron` has no usable "off" maths subset.** I checked directly: `/statistics` on
  `config=SFT, split=math` returns `reasoning: {"on": 276536}` and
  `system_prompt: {"detailed thinking on": 276536}` — **100% of the 276,536 maths rows are
  reasoning-ON**, with `output` **median 15,006 / mean 17,477 / max 74,587 characters** `[V]`
  ⇒ `[D]` median ≈ **4,168 tokens**. Unusable at 4,096. (Reasoning-off rows exist in the `chat`
  and other splits, not in `math`.)
- **`smoltalk2` has no maths-specific config at all.** I listed every config/split `[V]`: the
  nearest is `OpenThoughts3_1.2M_no_think_no_think` (435,193) and
  `Mixture_of_Thoughts_science_no_think` (86,110). Both are reasoning-model distillations with
  the think block removed, not native short CoT. The dataset declares **no licence** in its
  cardData `[V]` — blocking for redistribution.
- **`Dolci`**: `allenai/Dolci-SFT-7B` does not exist; the real repos are `Dolci-Instruct-SFT`
  (2,152,112, odc-by — the *non*-thinking mix), `Dolci-Think-SFT-7B/32B`, `Dolci-RL-Zero-Math-7B`
  etc. `[V]` HF API author search. I did **not** enumerate the maths sub-share of
  `Dolci-Instruct-SFT` `[not verified]`.
- **OpenMathInstruct-1 is the wrong style and the wrong licence**: solutions "use a mix of text
  reasoning and code blocks executed by Python interpreter" `[V]` card, and the licence is
  `other` / `nvidia-license`, not CC-BY. Skip it.
- **Tulu-3 personas licence trap**: the data is ODC-BY, but the card states outputs "were
  generated using GPT-4o and Claude 3.5 Sonnet" and are "subject to OpenAI's terms of use" /
  "Anthropic's terms of service and usage policy" `[V]`. If you publish the Apertus SFT model,
  this inherits a distillation-terms question that CC-BY-4.0 OMI-2 does not.

---

## Q5. RL / verifiable-answer prompt reservoirs, with lineage

| Dataset | Rows | Answer type | Per-problem difficulty metadata | Licence | Lineage (⇒ overlap risk) |
|---|---:|---|---|---|---|
| `SynthLabsAI/Big-Math-RL-Verified` | **>250,000** + 47,000 reformulated `[V, paper]` | verifiable, open-ended, closed-form | **Llama-8B solve rates** `[R — card is GATED]` | HF API says **apache-2.0**; the paper page says **CC BY 4.0** — **conflict, unresolved** | curated from existing open datasets incl. Numina/MATH/GSM8K ⇒ **overlaps the SFT mix** |
| `zwhe99/DeepMath-103K` | **103,022** `[V]` | `final_answer` string | **`difficulty` float64** + `topic` | **mit** `[V]` | built from **MMIQC, WebInstructSub, NuminaMath-CoT** `[V]` ⇒ overlaps NuminaMath |
| `BytedTsinghua-SIA/DAPO-Math-17k` | 1,791,700 rows = **17,917 distinct × 100 copies** `[D]`, cross-checked against `haizhongzheng/DAPO-Math-17K-cleaned` = **17,917** `[V]` | integer | none | **apache-2.0** `[V]` | AoPS-derived `[R]` |
| `agentica-org/DeepScaleR-Preview-Dataset` | **40,315** `[V]` | `answer` extracted from solution | none | **mit** `[V]` | AIME 1984–2023, AMC pre-2023, **Omni-MATH, STILL** `[V]` |
| `Skywork/Skywork-OR1-RL-Data` (`math`) | **105,055** `[V]` | `reward_model.ground_truth` | **`model_difficulty` per problem for DeepSeek-R1-Distill-Qwen-1.5B / 7B / 32B, integer 0–16** `[V]` | **NONE DECLARED** `[V]` ⇒ blocking | **NuminaMath-1.5 + DeepScaleR + STILL-3 + Omni-Math + AIME** `[V]` ⇒ overlaps everything |
| `POLARIS-Project/Polaris-Dataset-53K` | **53,291** `[V]` | `answer` | **`difficulty` = pass rate by DeepSeek-R1-Distill-Qwen-7B** `[V]` | **apache-2.0** `[V]` | **filtered from DeepScaleR + AReaL-boba** `[V]` ⇒ ⊃ DeepScaleR |
| ORZ-Math 57k | ~57,000 `[R]` | verifiable | none `[R]` | `[not verified]` | `[R]` | `Open-Reasoner-Zero/orz_math_57k_collected` **does not resolve** through the datasets-server `[V, error]`; it lives in the GitHub repo. **Nothing here is verified.** |
| NuminaMath-1.5 answer-typed subset | **631,522** `math-word-problem` (excl. 110,998 proof + 146,449 MCQ) `[V]` | numeric/expression, `answer` field | `problem_type` (8 domains) | **apache-2.0** `[V]` | the parent of OpenR1, DeepMath, Skywork-OR1, Big-Math |
| `openai/gsm8k` | train **7,473** / test 1,319 (×2 configs `main`,`socratic`) `[V]` | integer | none | mit `[R]` | – |
| MATH train (`EleutherAI/hendrycks_math`) | 7,500 `[R]`; repo licence **mit** `[V]` | boxed expression | Level 1–5 | mit `[V]` | – |

**The lineage trap, stated plainly.** DeepScaleR ⊂ Polaris; DeepScaleR + NuminaMath-1.5 ⊂
Skywork-OR1; NuminaMath-CoT ⊂ DeepMath-103K; NuminaMath-1.5 = the entire source of
OpenR1-Math-220k; Big-Math is curated from "openly available datasets" that include MATH/GSM8K
`[V, all from the respective cards]`. **A "held-out" RL reservoir defined by *dataset name* will
overlap your SFT mix.** Define it by **problem-text deduplication** (normalise LaTeX/whitespace,
then 8-gram or embedding match) against the exact SFT rows you ship, and record the removal
counts. The `open-r1` repo's `scripts/decontaminate.py` (8-gram, "following s1") is a ready
implementation `[V]`.

**Recommended reservoir**, given you will translate a slice to Greek and sample your own model:
`zwhe99/DeepMath-103K` (MIT, has a `difficulty` float **and** three R1 solutions you can discard,
explicitly decontaminated by the authors) as the primary, plus
`POLARIS-Project/Polaris-Dataset-53K` (Apache-2.0, pass-rate difficulty from a 7B model — the
closest proxy to *your* model's solve rate) as the hard tier. **Avoid Skywork-OR1 (no licence)
until that is resolved, and treat Big-Math as blocked until someone with access reads the gated
card.**

---

## Q6. Recommendation

### 6.1 The budget arithmetic — read this first

OMI-2 `train_1M`, exact `[V]`: problem mean 238.3 chars, solution mean 1,075.8 chars.
`[D]` at 3.6 chars/tok → **299 assistant tokens + 66 prompt tokens ≈ 365 total tokens per
example**. (Independent corroboration: the paper measures its own OpenMath CoT format at a mean
of **237.0 tokens** `[V]` Table 1, on the MATH-only ablation pool, which skews shorter than the
GSM8K-inclusive full set. So 237–299 is the credible band for assistant tokens.)

| Quantity | Value |
|---|---|
| Your proposed maths budget | **180M tokens** (30% of 600M) |
| ⇒ examples, if "supervised tokens" = assistant tokens only | 180M ÷ 299 ≈ **600K examples** `[D]` |
| ⇒ examples, if it means total sequence tokens | 180M ÷ 365 ≈ **495K examples** `[D]` |
| Your **current** maths data | ~17M supervised tokens ≈ **~57K examples-equivalent** `[D]` |
| OMI-2 published curve: 1M examples | MATH ≈ **61.2** (Llama-3.1-8B-Base) |
| OMI-2 published curve: 14M examples | MATH **67.8** |

**Three conclusions fall straight out of this table.**

1. **Your hypothesis is right about size, and the magnitude is larger than you think.** You are
   at ~57K examples. The OMI-2 curve's *first plotted point* is 1M — **17× more**. Your 9k-Greek
   pilot added ~2% to an already-17×-too-small pile; it was never going to move a benchmark.
   Every ablation in §Q2 was run at ≥64K and the robustness claims only hold at ≥256K `[V]`.

2. **The proposed 180M-token budget still lands below the curve's first point.** 495–600K
   examples is **0.5–0.6×** the 1M anchor. You would be interpolating on the steepest part of
   the curve — which is good news for marginal return per token, but it means you should not
   quote 61.2 as your expectation.
   **If you want to reach the published 1M anchor you need ≈365M maths tokens** `[D]`, which is
   **61% of a 600M mix**. Concretely: either raise maths to ~55–60% of 600M, or keep 30% and
   raise the mix to ~1.2B tokens. **This is the single most actionable finding in this
   report — surface it to the owner before the mix ratio is frozen.**

3. **Hold k small.** At a fixed budget, OMI-2 §2.2.4 says spend tokens on distinct questions
   (1K→6.5K unique at fixed 256K pairs = **+10.5 points** `[V]`). With ~600K example slots and
   607.3K unique OMI-2 questions available, **k≈1 is both feasible and what the evidence
   recommends.** Reserve k>1 for the hard tail only, where DART-Math's Prop2Diff result applies
   `[V]`.

### 6.2 Proposed mix (English-first), ~600K examples / ~180M tokens

| # | Source | Filter | Distinct problems | Examples | `[D]` tokens |
|---|---|---|---|---:|---:|
| 1 | **OpenMathInstruct-2** (cc-by-4.0) | see 6.3; **k ≤ 2**, re-balanced toward GSM8K lineage | ~330K | **380K** | ~114M |
| 2 | **NuminaMath-1.5** (apache-2.0) | `question_type=='math-word-problem'` ∧ `answer ∉ {proof, notfound}` ∧ `problem_is_valid=='Yes'` ∧ `solution_is_valid=='Yes'` ∧ `source ∉ {cn_k12, synthetic_math, metamath, orca_math}` | ~110K | **110K** | ~31M |
| 3 | **DART-Math-Hard** (mit) | hard tail only, k ≤ 4 per problem | ~15K | **60K** | ~22M |
| 4 | **ScaleQuest-Math** (apache-2.0) | length filter only — pure question-diversity injection outside MATH/GSM8K lineage | ~50K | **50K** | ~17M |
| | **Total** | | **~505K** | **600K** | **~184M** |

Sizing for row 2 `[D]`: 631,522 word-problems `[V]` minus the excluded sources
(cn_k12 149,010 + synthetic_math 147,612 + orca_math 151,916 + metamath 10,932 word-problems
`[V]`) ≈ **172K** survive on type+source; the validity flags then remove a further ~8%
`[D, approximate from the 76k global invalid count]` ⇒ ~158K available, of which I take 110K.

Why each exclusion in row 2: `cn_k12` because open-r1 measured that adding it **lowered** SFT
performance `[V]`; `synthetic_math` + `metamath` because they are MATH-train rewrites that
duplicate OMI-2's lineage and add contamination risk without adding diversity; `orca_math`
because it duplicates GSM8K-style coverage you are already buying in row 1 (keep it as a
fallback if the MGSM gap does not close).

### 6.3 Concrete filters

1. **Length.** Drop any row with `len(problem) > 3,600 chars` (≈1,000 tok — this reproduces the
   card's own recommendation to drop the 564 questions over 1,024 Llama tokens `[V]`) and any
   row with `len(problem) + len(solution) > 10,800 chars` (≈3,000 tok, leaving ~1,100 tokens of
   headroom inside 4,096 for the chat template, system prompt and generation). On OMI-2
   `train_1M` this removes essentially nothing (solution max is 5,743 chars `[V]`); on
   NuminaMath it removes the 26,844-char tail `[V]`.
   **Re-derive these thresholds with the Apertus tokenizer before running** — see the caveat at
   the top.
2. **Verified-answer only, with one deliberate exception.** Keep OMI-2's `augmented_*` rows even
   though their answers are majority-vote: the paper's Table 9 shows filtering them **hurts**
   (50.1 unfiltered vs 42.0 at min-votes 24) `[V]`, and §2.2.3 shows SFT tolerates ≥20% bad
   solutions at ≥256K scale `[V]`. **Do not re-litigate this with your own judge fleet** — NVIDIA
   already ran that experiment with a 405B judge and a 340B reward model and got nothing
   (Table 3: 43.6 unfiltered vs 43.0–43.8 filtered) `[V]`. For NuminaMath, by contrast, filtering
   **is** required, because nothing there is verified at all.
3. **Per-problem solution cap k.** k=1 for rows 2 and 4; **k ≤ 2** for OMI-2; **k ≤ 4** for the
   DART-Math hard tail. Rationale: §2.2.4 at fixed budget favours diversity `[V]`; Yuan et al.
   and DART-Math show k pays off specifically where the question set is fixed and the problems
   are hard `[V]`.
4. **Difficulty spread.** Use DART-Math's Prop2Diff principle — sample *more* solutions for
   harder problems `[V]` — rather than a uniform k. For OMI-2 you have no difficulty label, but
   you have a usable proxy: **the number of the 32 generations that agreed** is not published
   per row, so instead use `problem_source` (`augmented_math` ≫ `augmented_gsm8k` in difficulty)
   and MATH `Level` for the seed rows. Keep **Levels 1–2 at ≥25%** of the MATH-lineage slice —
   your model is at 13%, and the OMI-2 paper's own Figure 2 is a per-difficulty-level breakdown
   precisely because the gains are not uniform across levels `[V, figure content not read]`.
5. **Topic spread — protect arithmetic and algebra.** Your MGSM (44–52 vs Krikri's 68) is a
   *bigger* relative gap than your MATH-500. But OMI-2 fair-downsampled is only **15.3%
   GSM8K-lineage** `[V]`. **Re-weight row 1 to ~35% `gsm8k` + `augmented_gsm8k`** (≈133K of
   380K) rather than accepting the native 15.3%. NuminaMath's `problem_type` gives you an
   explicit dial for the rest: Algebra 422,915 / Geometry 183,796 / Number Theory 91,383 /
   Combinatorics 73,643 / Calculus 26,965 `[V]` — cap Geometry (it is the worst fit for a
   text-only 4k model; many olympiad geometry problems reference figures) and keep Algebra
   dominant.
6. **Decontaminate everything yourself.** OMI-2 is decontaminated against MATH test (⊃ MATH-500),
   GSM8K test, AMC 2023, AIME 2024 `[V]`. **NuminaMath-1.5, NuminaMath-CoT, DART-Math,
   ScaleQuest and OpenR1 publish no decontamination statement** `[V]`. Run 8-gram + embedding
   decontamination of the *whole assembled mix* against MATH-500, GSM8K test, **and the MGSM
   Greek/English test items**, and publish the removal counts per source. Nobody has checked
   translated forms against MGSM.

### 6.4 Does OpenR1-Math-220k make sense here? **No.**

Four independent reasons, three of them measured:

1. **It does not fit.** Traces average ≈16,760 chars ≈ **4,655 tokens** `[D]`, and the card
   states only 75% of problems were solvable under **8k** tokens `[V]`. Your entire window,
   prompt included, is 4,096. You would be training on truncated traces — teaching the model to
   start reasoning and never finish.
2. **Your model is non-thinking and cannot use test-time length.** The whole value of an R1
   trace is realised by generating a long trace at inference. s1's gain comes from *lengthening*
   thinking at test time (AIME24 50→57 via budget forcing) `[V]`; you have no room for that.
3. **The format evidence points the other way.** OMI-2 Table 1: the *less* verbose format won by
   **+3.9 points while being 40% shorter** `[V]`. Abstract (a): "excessively verbose solutions
   proving detrimental to SFT performance" `[V]`.
4. **The small-model literature agrees.** "Small Models Struggle to Learn from Strong Reasoners"
   `[V]` finds small models "perform better when fine-tuned on shorter, simpler reasoning chains
   that better align with their intrinsic learning capacity" — though its ≤3B threshold means
   this is **suggestive for 8B, not conclusive** `[D]`.

**If you want to keep an OpenR1 option open** (e.g. a later long-context Apertus), the only
defensible use now is: `config=default` only (93,733 problems — the `extended` split is
*measured* to be worse `[V]`), select the single **shortest** generation per problem where
`correctness_math_verify` is true, strip the `<think>…</think>` block, and keep only rows whose
stripped answer is under ~2,800 tokens. That is a **summarisation of an R1 trace, not an R1
trace**, its yield is unknown to me `[not verified — I could not measure the post-strip length
distribution, because `/first-rows` truncates the `generations` cells]`, and it is strictly
dominated by simply taking more OMI-2. **Recommendation: drop OpenR1 from this round entirely
and reallocate its share to rows 1 and 4.**

### 6.5 Expected gain, honestly bracketed

Published anchors, all `[V]`:
- Llama-3.1-8B-**Base**: MATH ≈20.3 → **61.2 at 1M** → 64.5 at 2M → 66.6 at 5M → **67.8 at 14M**
  (1M/2M/5M read from the scaling figure `[D]`).
- Llama-3.1-8B-**Instruct** (no OMI-2): MATH 51.8–51.9, GSM8K 84.2–84.5.
- NuminaMath-7B-CoT (860K human CoT): MATH 55.2, GSM8K 75.4.
- DART-Math-Hard on Mistral-7B (585K, ~15K problems): MATH 45.5, GSM8K 81.1.
- MetaMathQA on Mistral-7B (395K, ~15K problems): MATH 28.2, GSM8K 77.7.
- MathScaleQA on Mistral-7B (2,021K, GPT-3.5 teacher): MATH 35.2, GSM8K 74.8.

**Four discounts stand between you and 61.2, and I cannot quantify any of them from published
work:**
1. **Base-model gap.** Llama-3.1-8B-Base starts at MATH ≈20.3; you are at 13% *after four SFT
   rounds*. Every number above is on a Llama/Mistral/Qwen base with English-heavy,
   maths-heavy pre-training.
2. **Budget gap.** 495–600K examples is 0.5–0.6× the 1M anchor, on the steepest part of the
   curve.
3. **Language-transfer discount.** English→Greek transfer for maths reasoning is **the central
   untested assumption of this plan**, and I found **no published measurement** of it for an 8B
   model `[not verified — I looked and did not find one]`. Note your own English MATH-500 is
   13–16% vs Greek 13%, i.e. your model is currently *not* much better in English either, which
   is mildly encouraging for transfer (the bottleneck looks like maths, not Greek) but is a
   single data point.
4. **Continued-SFT vs from-base.** All the anchors fine-tune a *base* model in one go. You are
   adding a fifth round on an already-instruction-tuned checkpoint.

**My honest bracket:** a substantial English MATH-500 gain is well-supported — the mechanism
(17× more data, 40× more distinct problems, a 405B teacher instead of your own model) is
exactly what moved Llama-3.1-8B-Base by +40 points. **Greek MATH-500 landing in the 25–40%
band and Greek MGSM in the 55–70% band would be consistent with the published curves after the
discounts above**, which would put you at or near Llama-Krikri-8B-Instruct (32–38% / 68%).
**That band is my judgement, not a published result — mark it as such to the owner.** The one
thing the evidence does support unconditionally: **the current 17M-token maths slice is an order
of magnitude too small for any of these ablations to even apply**, and the diversity axis
(57K → ~500K distinct problems) is where the leverage is.

### 6.6 Open items I could not verify

- **Exact 1M/2M/5M values** — read from `scaling_plot.jpg`, ±0.5 points, not quoted numerals.
- **No GSM8K-vs-data-size curve exists** in the OMI-2 paper; only the 14M endpoint (91.7).
- **Figure 6** (diversity ablation) per-point values: only the 1K→6.5K delta (10.5) is in text.
- **Big-Math-RL-Verified is gated** — I could not read its card, so the per-problem Llama-8B
  solve rates and the apache-2.0 / CC-BY-4.0 licence conflict are both unresolved.
- **ORZ-Math 57k** — repo does not resolve through the datasets-server; nothing verified.
- **NuminaMath / DART-Math / ScaleQuest length percentiles** — the statistics endpoint returns
  only min/median/mean/max for string columns, so "% fitting 4,096" is estimated, not measured.
- **OpenR1 post-`<think>`-strip length distribution** — `/first-rows` truncates the cells.
- **Skywork-Math, ScaleQuest, AceMath, MAmmoTH2 body tables** — abstracts verified, per-model
  cells not.
- **All token counts** depend on the 3.6 chars/token assumption. No tokenizer was available.
