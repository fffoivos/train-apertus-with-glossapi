# Round two, data preparation: the plan to Sunday 6 September 2026

Version 2, written Friday 4 September 23:35 on the Mac clock (EEST), after three review rounds
(`docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`, answers in place). Every time below is Mac clock. This document supersedes the
mix, filtering, speed and decision sections of `SFT_ROUND2_PLAN.md`; that file's §0 (shape of the round), §3 (personality set),
§4 (preference) and §5 (evaluation gates) still stand. The annotation detail lives in `docs/ANNOTATION_HANDOFF_20260905.md`.

**Feedback on this document goes in `docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`** (full path
`/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`).
I watch it and answer under each finding, marked `→ claude:`.

## 1. What we are building and why

Stage 1 of round two is a broad-ability SFT set for the Greek-CPT Apertus-8B. Round one showed two things that shape it: our own
Greek data beat the same skills imported raw (E3 over E3′: interviews 2.91 vs 2.63, identity 2.85 vs 2.60), and English rows written from a
Greek point of view did no harm to the Greek evals (E2 inside the seed floor). So the language of a row does not matter to the Greek
side, and the vantage inside it does. Whether identity transfers across languages was NOT measured in round one: every probe was in Greek
(correction, Saturday 23:45; an English identity probe belongs in the next evaluation, and the identity part of the personality set gets an English version). Stage 1 therefore imports broad skills in any language, screens out what asserts a foreign identity
or a foreign world, and keeps the Greek vantage where it is cheap to keep; stage 2 (Greek-heavy) and stage 3 (personality) assert it.

The three intentions, and what serves each:

| intention | what it means here | what serves it | what does not, and is written down as such |
|---|---|---|---|
| **annotation** | every unverified row gets a sticker before training: identity, wrong answer, foreign framing, tone, skill; nothing is edited. Owner's restatement (Saturday 16:30): the first reason was to know the TASK TYPE of every row; whether a row needs adaptation was conditional on a test set proving the judge can make that distinction, which the 61-row ground truth (7 actionable rows) did not establish. No assembly rule was changed on that restatement; the owner decides what, if anything, changes | judges routed by what a source needs (§3); a program wherever one exists; a full-text identity backstop on every block after the judges; tone labels used at assembly | Luna's misses on explanation and advice rows in chat are accepted, because those rows come from a 2026 model or a human and the backstop catches explicit identity |
| **generation** | Sol writes what the imports cannot give: Greek text-grounded tasks in a Greek setting | the 2,000-row Greek rewriting and summarising set, generated, corrected by a second Sol pass, screened, blind-read by the owner | open factual questions are not generated, because a self-check is weakest there; safety refusals in our voice wait for stage 2 |
| **data mix** | verified answers or a recent generator, nothing old and unchecked; Greek kept whole; budget by tokens, not rows | the table in §2 with measured token means; small blocks whole; the 208M-token gate under the current cap | "checker-verified" covers only what the checker checks: Precise IF passed its constraint checkers and failed a content spot-check at 27%, so the constraint block shrinks from about 40% to about 20% of tokens (§7 decision 4) |

## 2. The mix

Sizes are rows in the full mix (option A) and the exact-tokenizer means per row measured on Friday. Under the current cap (option C) the
small blocks stay whole and the big ones are scaled to the token budget over the rows that are present at assembly.

| block | source | written by | checked how | rows (A) | mean tokens |
|---|---|---|---|---|---|
| constraint following | Dolci Precise IF, Sol-screened subset only | 2025 models | constraint checkers at the source verify FORMAT only; Sol spot-check of 300 (12k window): 27% unusable (contradictory arithmetic, wrong facts, off-task, inappropriate); so only a Sol-screened 20k subset enters, about 14k keep | 20k screened | 600 |
| constraint following | argilla ifeval-like, filtered | Qwen2.5-72B, 2024 | our re-run of the IFEval checkers on all 56,339 rows: 47 fail; Sol content spot-check of 300: 5 unusable (1.7%), 0 identity | 56k | 256 |
| math | OpenMathInstruct-2, GSM8K-style | Llama-3.1-405B, 2024 | our re-run of the final-answer match on 100,000 rows: 29 mismatch | 100k | 342 |
| chat and advice | Nemotron IF-Chat v3, chat split, half A (half B if time allows) | GLM-5, 2026 | exact-length prefilter (16.9% over the window), EU-language gate, Luna screen, Sol on technical rows, backstop | 34k + 34k | 1,584 |
| chat, human-written | OpenAssistant (Dolci Chat) | volunteers, 2023; 42% Spanish, 30% English | Luna, Sol on technical rows and as second opinion, EU-language gate (Catalan kept) | 3.8k | 350 |
| coding | Dolci Python Algorithms | 2025 | Sol spot-check 20 of 300 wrong (6.7%), so the block is Sol-screened; no executable tests exist | 20k screened | 388 |
| reasoning | Dolci Verifiable Reasoning | 2025 | Sol spot-check 3 of 300 wrong, taken as clean | 30k | 330 |
| reasoning | Dolci logic puzzles and word sorts | generator | exact brute-force checker: 11,163 confirmed, 1,318 wrong (20.9% of zebra) excluded | 11k | 330 |
| tool use | Dolci Tool Use | 2025 | regex identity and system-prompt scan over all 40k; Luna's 3,000-row sample (Saturday 12:40) answered: 337 drops, near all of them the API-irrelevance refusals ("I can't do X; based on the available API I can…") mislabelled identity or wrong, regex identity 1 in 3,000, so the block stays unscreened beyond regex and lexicon and Luna's sample verdicts are not applied | 30k | 827 |
| science | Dolci OpenThoughts3+ Science | 2025 | Sol screen with a 12,000-character judge window | 15k | 941 |
| other European languages | SmolTalk2 multilingual (de, fr, es, pt, it) | Qwen3-32B, 2025 | Luna; multilingual identity patterns | 25k | 511 |
| safety | Dolci WildGuardMix and CoCoNot | 2024; the stated exception to the recency rule | Luna; 39% of kept rows carry chatbot mannerisms and are dropped | 10k | 302 |
| Greek, rewriting and summarising | written by Sol in Greek | gpt-5.6, 2026 | Sol correction pass, screen, owner blind read | 2k | 700 |
| Greek, our round-one set | 11 configs, adapted to the Greek vantage | Sol, 2026 | ours; seen twice | 20k × 2 | 351 |

Dropped under the recency rule: Magpie Ultra, OpenHermes, Tulu WildChat, EuroBlocks fr/de, Dolci persona math, Evol-CodeAlpaca, Tulu persona
Python, TableGPT. Dropped by measurement: FLAN (14.6% wrong). Wrong-rate threshold: at most 2% → in unscreened; 2 to 10% → program check or a
full Sol screen first; above 10% → out.

Token shares in the option-C dry run of Friday 23:45 (labels present at that time, approximate tokens, 431,045 rows, 207.2M tokens, post-scan 0):
constraint following 49% (Precise IF 40%, ifeval-like 9%), tool use 16%, math 11%, multilingual 8%, reasoning 6%, Greek 4.5%, puzzles 2%,
safety, OpenAssistant and the Greek rewriting set under 1% each. Nemotron, coding and science were not yet labelled; because the share is solved
over present blocks, their arrival pulls the big present blocks back down. The constraint-following share is the one deliberate imbalance (§7,
decision 4). Other numbers from that run: the decontamination list is now 48,729 prompts (1.1M distinct 8-grams) and removes 1.4% of Precise IF
and 2.4% of ifeval-like, both IFEval-shaped; the identity backstop removed 209 Precise IF rows; the tone rule removed 1,135 OpenAssistant and
4,804 safety rows.

## 3. The screen, in one paragraph each

**Judges.** A program wherever the task has one: the zebra and word-sort checker, the IFEval checkers, the OpenMath final-answer match. Sol
(gpt-5.6-sol, medium effort, default tier, 24 workers, never split) as the only judge for correctness-heavy unverified sources: science, the
coding block, the spot-checks, and every row Luna labels as code, math or reasoning inside the Luna blocks. Luna (gpt-5.6-luna, medium, 64
workers) for conversational sources: safety, Nemotron, multilingual, the tool-use sample. Same rubric for both, verbatim in the handoff.

**Backstop.** After the judges, at assembly, a full-text identity regex (English, French, German, Italian, Spanish, Portuguese, Greek; system
and assistant turns; word-bounded) runs over every row of every block; hits are dropped and counted; the written file is re-scanned and must
show zero. This is what closes the one non-negotiable goal, because the judge's window is finite and Precise IF, "verified", still carries
identity lines.

**Tone.** The rubric records chatbot mannerisms and unasked second-person commands. Rows flagged for mannerisms are dropped from the chat, safety,
multilingual, science and Greek blocks (OpenAssistant 19% of kept rows, safety 39%, our Greek set 9%); unasked commands are reported and can be
dropped by flag. Blocks no judge labels (ifeval-like, OpenMath, reasoning, puzzles, tool use) get a cheap lexicon at assembly that drops rows
whose last assistant turn opens or closes with a chatbot phrase; on ifeval-like that is about 15% of rows, matching Sol's 17% in the spot-check.

**Language.** Chat blocks pass an EU-language gate (English, Greek, the EU official languages, Catalan); Russian, Chinese, Thai, Ukrainian,
Vietnamese rows are out (Nemotron 16.5%, OpenAssistant 9%).

**Adaptation.** None in stage 1. Adapt-labelled rows are excluded because no line-cut exists; the adaptation pipeline is reserved for Greek
work in stage 2.

**Identity drops need a phrase (decision, Saturday 13:30).** Luna's light-rubric "identity" verdict fires on rows with no self-reference (Nemotron A: 1,149 of its 1,464 drops; our Greek set: the persona interviews). The assembler therefore honours a Luna identity drop only when the assistant or system text carries a self-description phrase (strict identity regex or the broad first-person list in `identity_patterns.py`); the rest are kept unless quality 1 or mannerism. Sol's verdicts and the full-text identity backstop are unchanged. Details and counts: handoff §4 item 6.

**Judge window (decision, recorded Saturday 12:30 at the owner's request).** Every judge sees a cut view of the row: Luna 3,000 characters per turn and 9,000 per conversation, Sol 12,000 and 24,000; the rubric tells the judge not to penalise the cut. The caps were chosen on Friday for throughput (about 5,400 Luna rows an hour, needed for the Sunday deadline) and, as it turned out, for the weekly subscription limit, since input tokens dominate the judge cost. The owner's standing preference is the most complete inspection possible; this shortcut is the standard for this round and is documented here rather than re-decided mid-run. Measured coverage over the exports (share of rows with any cut text, share of assistant characters the judge saw, share of assistant turns with at least their opening seen):

| block | rows | rows cut | assistant text seen | assistant turns seen |
|---|---|---|---|---|
| Nemotron half A | 34,214 | 58.1% | 73.4% | 98.9% |
| Nemotron half B | 34,345 | 58.4% | 73.2% | 99.0% |
| multilingual | 25,000 | 8.0% | 97.9% | 100% |
| Dolci chat | 5,305 | 2.6% | 97.2% | 100% |
| Dolci safety | 15,650 | 1.4% | 98.9% | 100% |
| tool-use sample | 3,000 | 0.6% | 99.4% | 99.7% |
| our Greek set | 32,892 | 0.8% | 99.1% | 100% |
| Greek rewriting set | 2,000 | 2.3% | 97.1% | 100% |
| science, Precise IF, coding (Sol) | 20,000 each | 0 to 0.1% | 99.2 to 100% | 100% |

So the shortcut bites on Nemotron only: about a quarter of its assistant text, the tails of long turns, was never judged for quality or tone. What covers the unseen part: the identity backstop reads every character of every turn at assembly (exit 4 if any survives), the mannerism check reads the last assistant turn whole, the language filter reads the whole row, and the 4,032-token cap bounds every row. What nothing covers: a wrong or off-tone passage deep inside a long Nemotron turn. Completing the inspection is DATA_TODO item 19 (re-judge the 40,000 cut Nemotron rows with the Sol window when the subscription is idle).

## 4. Generation

The Greek rewriting and summarising set: 2,000 rows, Sol at high effort. For each row Sol writes a realistic Greek passage in a Greek setting
(20 genres, 40 topics, five lengths, a register), a user instruction from a list of 15 task types, and the answer, under a prompt that forbids
mannerisms and self-reference. A second Sol call applies the round-one Γ editing contract (the `natural-greek-sft` editor: task, faithfulness, reading; Greek prefers
the compact form; correct only listed faults; never edit a valid form) extended with execution and faithfulness checks, and the corrected
answer replaces the original at assembly. The generator prompt carries the same compact-Greek rule and a vouched-facts rule (institutions,
services and procedures must exist or be plausible in Greece; only person names are invented). The owner blind-reads 40 rows
(https://claude.ai/code/artifact/dc57edac-97cc-472e-810e-e336f03d63f2). Generated Friday 22:00 to 00:00 at about 1,100 rows an hour, zero
failures; the correction pass runs in the Sol chain right after the Precise IF spot-check.

Factuality of the generated passages (owner's question on row gr_rw_00939, Sat 09:00): the passages are plausible fiction anchored on real
names, a real municipality and its real streets with invented dates, phone numbers, fines and rules. That is acceptable for a rewriting task
because the passage is the user's turn and loss is computed on assistant tokens only, but the assistant's rewrite repeats the invented specifics.
For the next batch the administrative genres should use real public-sector texts instead (Μίτος procedure texts and municipal regulations are
open data), with generation writing only the instruction and the answer.

The long-running improvement backlog, for the months after the 1 October grant deadline, is `docs/DATA_TODO.md`.

Generation is deliberately limited to text-grounded tasks. Coding, safety refusals in our voice and Greek constraint following are the next
candidates, for stage 2, at about 5,000 rows a day.

## 5. Timeline to Sunday, Mac clock

Measured: Luna 4,300 to 4,500 rows an hour at 64 workers; Sol 1,100 generating, 1,000 to 1,400 judging chat and reasoning, 825 on puzzles.

| when | Luna (64) | Sol (24) | me |
|---|---|---|---|
| Sat 00:40 | Nemotron half A, 34,214 rows, about 8 h | routing pass, Precise IF spot-check, Greek correction pass, then Science in 3,000-row chunks alternating with routing (15 to 20 h) | exact-tokenizer assembly runs on what exists; plan and handoff refreshed |
| Sat 09:00 | multilingual 25k, 6 h | Science continues | Nemotron rows added to the owner's reading page |
| Sat 15:00 | tool-use 3k sample; then our Greek set 32,892 (6 h), then Nemotron half B | Science done about 18:00; coding 20k in chunks, 13 h | keep-lists merged as blocks finish |
| Sun 08:00 | half B continues or is cut | coding done; last routing pass | full assembly under the 208M-token budget with the exact tokenizer; decontamination; trainer dry run on the cluster (gate) |
| Sun 14:00 to 22:00 | | | receipts; stage-1 config derived from the receipt; plan and handoff final |
| Mon | | | training launch once the cap decision is in |

Cut order if it slips: Nemotron half B, then tool use beyond the sample, then multilingual to its regex lists. Sol's order after science is now Precise IF 20k, then coding (chain 2).

**Amendment, Saturday 10:00 (weekly Codex limit).** The subscription's weekly limit fell from 52% Friday night to 37% by Saturday 10:00 (about 1.4 points per hour with Luna 64 and Sol 24 running together) and refreshes Monday 05:00. Rather than exhaust it, the queues are capped so that the remaining judging spends about 17 points and leaves about 20% for the owner: Sol runs science to 12,000 rows (not 20,000), Precise IF to 6,000 (not 20,000), coding to 6,000 (not 20,000), then the final routing pass (which now also covers our Greek set and the Greek rewriting set); Luna finishes multilingual and the tool-use sample, then our Greek set and the Greek rewriting set; Nemotron half B stays, last in Luna's queue (owner, Saturday 10:00: keep the Luna schedule; adjust Sol later if limit remains). Expected kept rows: science about 6,700, Precise IF about 4,400, coding about 5,600. Everything is labelled by Saturday night; the assembly gate stays Sunday morning. The uncapped remainders are on the backlog (DATA_TODO items on the full Sol screens).

**Final assembly, Sunday 05:10 (data gate GREEN).** All screens complete (science 12k, Precise IF 6k, coding 6k by Sol; Nemotron A and B, multilingual, safety, OpenAssistant, tool sample, our Greek set and the rewriting set by Luna with Sol routing of the technical rows). Exact-tokenizer assembly under the 208M budget: **334,383 training rows, 197.9M tokens, 3,171 dev rows, identity post-scan 0, no block missing**; receipt `docs/receipts_R2_stage1_final_20260906.json`; config `cluster/configs/R2_stage1.yaml` (1 epoch, cosine_with_min_lr, lr 1e-5, about 7.6 node-hours, CHF 20.5). The arm is on the cluster at `$SCRATCH/sft_round1/data/arms/R2_stage1`; the trainer dry run on a 5% sample passed (DRY_RUN_OK, 16,719 rows, 9,846,233 tokens, which scales to 196.9M, within 0.5% of the assembler's count). Training stays gated on the personality datasets (owner, Saturday 21:30).

## 6. Budget

Cap CHF 90, spent CHF 61.04 (22.7 node-hours at CHF 2.69), CHF 28.96 left, about 10.8 node-hours. Throughput 26M tokens per node-hour.

| option | what | node-hours | CHF | fits |
|---|---|---|---|---|
| A | full mix, about 0.39B tokens, 2 epochs | 30 | 81 | no |
| B | full mix, 1 epoch | 15 | 40 | no |
| C | token-budgeted half, 208M tokens, 1 epoch, plus light evaluations | 8 + 1 | 24 | yes, reserve CHF 4.6 |

Under the current cap stage 1 is option C; the budget share is solved over the blocks present at assembly, so Sunday's run is 6.5 to 8
node-hours depending on how much of Nemotron is screened. With a cap of CHF 250 to 300, option A plus the full evaluation suite and a
screened-versus-unscreened control arm costs about CHF 130. Recipe: round one's pick, lr 1e-5, cosine, 1 epoch here, 4,096 tokens, fp32
master weights, one node; the config is derived from the assembly receipt by `cluster/make_stage1_config.py`, which refuses estimates.

**Personality set, first draft (Sunday 07:35).** 1,388 Greek rows in seven categories written natively by Opus 5 from fact sheets, Sol-checked on 300 (Greekness 4.92/5; ok 134 / edited 155 / rewrite 11); doc `docs/PERSONALITY_SET_20260906.md`, reader https://claude.ai/code/artifact/820812e8-7e92-4e92-90dd-f4cbd27c724c; three placeholders (name, cutoff, licence) and six owner decisions listed in the doc before it can train.
- 2026-09-07: personality set v3 DELIVERED (restyle + Opus editor + gates over all 1,388 rows; 1,214 rewritten, 252 editor-edited, gates green): docs/PERSONALITY_SET_V3_20260906.md. Training still gated; open items in that doc (beyond-sheet verification is the big one).

**Training gate (owner, Saturday 21:30).** Stage-1 training does not start when the data gate is green. It is gated on crafting the personality datasets first; the assembly, config and dry run only make the arm ready. Nothing is launched on the cluster without the owner's word.

## 7. Decisions for the owner

1. **Cap:** keep CHF 90 (option C) or raise to CHF 250 to 300 (option A plus evaluations plus the control arm).
2. **Licences:** the Qwen-generated ifeval-like rows (56k) and OpenMathInstruct-2 (Llama-3.1-405B output, naming clause): keep with attribution, or drop.
3. **Language gate on OpenAssistant:** its 459 rows in Russian, Thai, Chinese, Ukrainian are out under the EU gate; overrule if wanted.
4. **Constraint-following share:** now about 20% of stage-1 tokens (Sol-screened Precise IF about 14k rows plus ifeval-like 56k, pending its own content spot-check); raise it later only with more Sol screening of Precise IF.
5. **Tone:** mannerism rows dropped (default); also drop unasked-command rows (16 to 27% of kept chat and safety rows), or not.
6. **Tool use in stage 1:** 30k rows in an ad-hoc `<function_calls>` format that is not the Apertus template's native tool format, 15% of the tokens, with no benchmark that measures it; keep, cut to 10k, or drop until the native format is wired.

## 8. What might have slipped, checked

The owner asked for this list. Each item is what I looked for, what I found, and what was done.

1. **Decontamination against translations.** The Greek benchmarks ARC, HellaSwag, TruthfulQA and GreekMMLU are translations, and only their
   Greek text was in the list, which cannot match English training rows. Found and fixed Friday 23:27: 28,449 English originals added.
2. **Tone labels unused.** The rubric recorded mannerisms and commands and nothing read them. Fixed: mannerism rows dropped by default (§3).
3. **Vantage share in stage 1.** Greek-vantage content is about 8% of stage-1 tokens; round one saw raw foreign rows pull even at a 3:1
   Greek majority. Stage 1 accepts this by design (skills now, vantage in stages 2 and 3) and the screened-versus-unscreened arm is the test;
   the cheap lever if the owner wants more is the Greek repeat factor (2 → 3).
4. **Skill coverage in Greek.** The judge's census of 1,000 rows of our Greek set: creative writing 23%, explanation 20%, advice 17%,
   extraction and classification 8%, rewriting and summarising 7%, math 7%, code 5%, constraint following 5%, conversation 3%, reasoning 1%,
   refusal 1%; tool use, science and puzzles 0. Stage-2 generation targets, by gap and value: reasoning, tool use, constraint following in
   Greek (with checkers), code, science. The same census found in our own set 1.9% identity rows, 9% mannerisms, 17% unasked commands and
   2.6% unusable answers, so the whole set (32,892 rows) is now queued for Luna after the tool-use sample and the assembler applies its labels.
5. **Tool-use format.** The trainer accepts only system, user and assistant strings, so tool rows are rendered with `<function_calls>` and
   `<function_results>` tags, which is not the Apertus template's native tool format. Decision 6.
6. **"Verified" sources.** Precise IF carries about 250 self-descriptions and, worse, 27% content failures in a 300-row Sol spot-check: its
   checkers verify constraints, not answers. Found Saturday 00:10 after the plan's first version. Only a Sol-screened subset enters; ifeval-like
   gets the same content spot-check.
7. **Adapt rows.** The old plan counted them into stage 1 with a line-cut that did not exist; they are excluded.
8. **Judge window.** Luna cannot see beyond 9,000 characters; the exact-length prefilter and the backstop cover what it misses; Sol blocks
   use a 12,000-character window.
9. **Nemotron's withheld prompts.** 41% of the chat split has no first user turn; filtered out; recoverable by hashing WildChat-1M, not done.
10. **Duplicated rows from the export.** Six Dolci shards were read twice; local files and labels are deduplicated; the cluster copies are not.
11. **Clock.** My log stamps ran two hours ahead of the machine on Friday; every stamp is now `$(date)`.
12. **The dev split** is 1% of the same blocks and measures loss only; the real evaluation is the benchmark suite in `SFT_ROUND2_PLAN.md` §5.
