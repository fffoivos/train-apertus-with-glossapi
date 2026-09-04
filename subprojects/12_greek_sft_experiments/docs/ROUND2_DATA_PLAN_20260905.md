# Round two, data preparation: the plan to Sunday 6 September 2026

Written Friday 4 September, 21:50 on the Mac clock (EEST; the review found the first version's times 2 hours ahead, all times below are now Mac clock), after several reorientations during the day. Revised 22:50 after the independent review (`docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`). This document supersedes the mix and
routing sections of `SFT_ROUND2_PLAN.md` where they differ; it is the one to review. Companion: `ANNOTATION_HANDOFF_20260905.md`.

**Feedback on both documents goes in `docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`** (full path
`/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`).
I watch that file and answer under each finding in place, marked `→ claude:`. A reviewer brief sits next to it.

## 1. Objectives and hard limits

- Goal of stage 1: a broad-ability SFT set for the Greek-CPT Apertus-8B that keeps the Greek vantage, ready to train.
- Time limit: **data preparation finished by late Sunday 6 September, Mac clock (EEST)** (mix assembled, decontaminated, tokenized, receipts written, trainer dry-run green).
- CSCS budget: cap CHF 90, spent CHF 61.04 (22.7 node-hours at CHF 2.69 per node-hour), **CHF 28.96 left, about 10.8 node-hours**.
  Nothing in this plan spends node-hours before Monday; the login node is used for CPU work only, politely (nice 19, few processes, time caps).
- Standing rules from the owner today: (1) trust a source once it is shown high quality and verified, and do not drop its rows on a judge's word;
  (2) an old generator is acceptable only when a program verified the answers, otherwise the source has to be recent;
  (3) decide in advance which sources and categories need more intelligence and give those to Sol as the only judge, rather than re-checking Luna;
  (4) 24 Sol workers is the floor, never lowered or split; (5) no priority tier, more workers instead; (6) do not overdo monitoring.

## 2. The mix we will actually keep

| block | source | written by | checked how | rows in stage 1 |
|---|---|---|---|---|
| constraint following | Dolci Precise IF | 2025 models | constraint checkers (source); no structured constraints in the release, so a Sol spot-check of 300 on Saturday | 137k (136,820 exported) |
| constraint following | argilla ifeval-like, filtered | Qwen2.5-72B, 2024 | our re-run of the IFEval checkers on all 56,339 rows: 56,292 pass, 47 fail (0.08%) | 56k (owner decision: Qwen licence) |
| math | OpenMathInstruct-2, GSM8K-style | Llama-3.1-405B, 2024 | our re-run of the final-answer match on all 100,000 rows: 99,971 match, 29 mismatch | 100k |
| chat and advice | Nemotron IF-Chat v3, chat split | GLM-5, 2026 | reward model best-of-N; Luna screen; Sol on technical rows | 100k screened (150k exported) |
| chat, human-written | OpenAssistant (Dolci Chat), screened | volunteers, 2023 | Luna + Sol on technical rows + Sol second opinion | about 4.2k keep rows; adapt rows are NOT in stage 1 (no line-cut exists; review F1) |
| coding | Dolci "Python Algorithms" | 2025 | Sol spot-check: 20 of 300 wrong (6.7%), so the block is screened by Sol; 20k screened by Sunday, the rest later | 20k screened now (60k exported) |
| reasoning | Dolci "Verifiable Reasoning" | 2025 | Sol spot-check: 3 of 300 wrong (1%), taken as clean | 30k |
| reasoning | Dolci logic puzzles and word sorts | generator | exact brute-force checker | 11,163 confirmed |
| tool use | Dolci Tool Use | 2025 | Luna identity screen | 30k |
| science | Dolci OpenThoughts3+ Science | 2025 | Sol screen (20k exported) | 15k |
| other European languages | SmolTalk2 multilingual-8, Nemotron non-English European rows | Qwen3-32B 2025, GLM-5 2026 | Luna (multilingual only if time allows; else lexicon identity scan) | 25k + 10k |
| safety | Dolci WildGuardMix and CoCoNot, screened | 2024 | Luna; 21% identity so far, so mostly adapt or drop | 10k |
| Greek, rewriting and summarising | written by Sol from scratch, in Greek | gpt-5.6, 2026 | Sol correction pass, screen, owner blind read | 2k (the 10% start) |
| Greek | our round-one adapted set | Sol, 2026 | ours | 20k, seen twice |
| **total** | | | | **about 580k rows, about 0.39B tokens at the measured per-block token means (review F4)** |

Dropped under rule (2): Magpie Ultra, OpenHermes, Tulu WildChat, EuroBlocks fr/de, Dolci persona math, Evol-CodeAlpaca, Tulu persona Python, TableGPT.
Dropped by measurement: Tulu FLAN and Dolci FLAN (Sol finds 193 of 1,323 wrong, 14.6%, on 2015-era labels).

Wrong-rate threshold (review F8): measured wrong rate at most 2% → in unscreened; 2% to 10% → program check or a full Sol screen before use
(Dolci Python Algorithms at 6.7% is therefore Sol-screened, 20k by Sunday, the rest later); above 10% → out (FLAN). Safety (2024, unverifiable)
is a stated exception to rule (2): kept small (10k) because refusals are low-risk and Luna screens identity; regenerated in our voice in stage 2.
Identity backstop (review F1): at assembly a full-text regex (English, five EU languages, Greek) runs over every assistant turn of every row,
after the judges; hits are dropped and counted per block; the written train file is re-scanned and must show 0 hits.
Licence question (review F8): the Qwen question in §6 also covers OpenMathInstruct-2, whose answers are Llama-3.1-405B output under the Llama 3.1
licence naming clause; one decision for both.

## 3. Timeline to Sunday, Mac clock (EEST), with the measured rates

Rates: Luna 4,160 to 4,350 rows an hour at 64 workers (safety); Sol 1,100 rows an hour generating Greek at high effort, 1,000 to 1,400 on
chat and reasoning at medium, 825 on puzzles; checker exact and free. Revised after the review: Nemotron is exact-length-filtered, shuffled
and split into halves A and B (option C needs A only); multilingual goes to Luna before tool use, tool use gets a 3,000-row Luna sample plus
the regex scan; Sol alternates routing with science chunks so the 24 workers are never split.

| when (Mac clock) | Luna (64 workers) | Sol (24 workers) | me (CPU on the login node, polite) |
|---|---|---|---|
| Fri 23:00 | safety, about 9,500 left, 2.3 h | Greek rewriting to 2,000 rows (00:00); OpenAssistant technical rows routed | multilingual export landed; Nemotron halves prepared |
| Sat 01:30 | Nemotron half A, ~48k rows after the length filter, about 11.5 h | routing pass, then Science in 3,000-row chunks alternating with routing, 15 to 20 h | exports done; Precise IF sample 300 queued on Sol |
| Sat 13:00 | multilingual 25k, 6 h | Science continues | assembly script final; blind read pages for the owner (Greek set https://claude.ai/code/artifact/dc57edac-97cc-472e-810e-e336f03d63f2 ; judge keep rows https://claude.ai/code/artifact/fbd19acd-5e48-4de4-b19d-df3e9eba5594) |
| Sat 19:00 | tool-use 3k sample, 45 min; then Nemotron half B if time allows | coding 20k in chunks, 13 h | keep-lists merged as blocks finish |
| Sun 08:00 | Nemotron B continues or is cut | Precise IF spot-check, Greek correction pass, last routing pass | full assembly under the 208M-token budget, decontamination, trainer dry run on the cluster (gate) |
| Sun 14:00 to 22:00 | | | receipts, plan and handoff updated, training config written |
| Mon | | | training launch once the cap decision is in |

Cut order if it slips: Nemotron half B, then tool use beyond the sample (regex scan only), then multilingual to the multilingual regex scan.
Nothing on the critical path waits for the owner except the decisions in section 6.

## 4. Budget for stage 1 under the current cap

Throughput measured in round one: 26M tokens per node-hour; 600 tokens per row after the 4,096-token filter.

| option | rows | epochs | node-hours | CHF | fits CHF 28.96 |
|---|---|---|---|---|---|
| A: the full mix | 620k | 2 | 28.6 | 77 | no |
| B: the full mix | 620k | 1 | 14.3 | 38 | no |
| C: stratified half | 310k | 1 | 7.2 | 19 | yes, with light evals (1 nh) and margin |
| D: tier S from the old plan | 250k | 2 | 11.5 | 31 | no |

So without a cap raise, stage 1 is option C: a stratified half of the mix for one epoch, light evaluations on the final checkpoint,
GreekMMLU deferred (2.8 nh alone). With a cap of CHF 250 to 300 (plan §7), option A plus the full evaluation suite (about 6 nh) costs
about CHF 93 and leaves room for stage 2 and a preference round. The training recipe is round one's pick: lr 1e-5, cosine, 4,096 tokens,
fp32 master weights, TRL trainer on one node.

## 5. What the annotations are for, and what waiting for them buys

The screen puts one sticker on every row of an unverified source: identity, wrong answer, foreign framing, tone, skill, and a verdict
keep, adapt or drop. Nothing is edited during the screen.

Goals, in order of weight:
1. Remove every row where the assistant speaks about itself as an AI, a product, or a foreign national. This is the one non-negotiable,
   because identity transfers across languages and stage 3 must own it outright. OpenAssistant: 366 of 5,305; safety: 556 of 2,667 so far.
2. Remove wrong answers from sources that nobody verified. Measured so far: FLAN 14.6%, OpenAssistant about 11% after Sol, puzzles 20.9% exact.
3. Find the rows whose answer imposes a foreign country's institutions, prices or units on a user who did not ask. Small: about 1% in OpenAssistant.
   These are dropped, or adapted from a capped budget if the owner wants adaptation at all.
4. Record tone (chatbot mannerisms, unasked commands) for the stage-2 style decision. Not a drop reason.
5. A census of skills per source, to check that the Greek set covers every category we train on.

What waiting for the full screen buys, compared with training on Sunday's partial labels: complete identity removal instead of partial;
per-source wrong-answer rates that decide inclusion instead of reputation (FLAN went out on its rate tonight); the skill census for the
Greek coverage check; and the exact keep-lists that make a screened-versus-unscreened control arm possible later. The cost of waiting is
zero node-hours; the screen runs on the Codex subscription and ends inside the Sunday window.

## 6. Owner decisions needed

1. **CSCS cap**: keep CHF 90 (stage 1 = option C, half mix, one epoch) or raise to CHF 250 to 300 (option A plus full evaluations).
2. **Qwen-generated ifeval-like rows** (56k): keep under the Qwen 2.5 licence with attribution, or drop and rely on Precise IF alone.
3. Confirm FLAN out and the Greek rewriting set in.

## 7. Judges: who does what, with what prompt

- Checker (exact, no model): `data/zebra_check.py` for Dolci puzzles and word sorts; the IFEval checkers for ifeval-like; final-answer match for OpenMath.
- Sol, `gpt-5.6-sol`, medium effort, default tier, 24 workers, sole judge for: FLAN (measurement only), Science, the spot-check samples, and every
  row Luna labels as code, math or reasoning inside the Luna blocks (`data/route_technical.py`). Prompt: rubric v3, verbatim in the handoff.
- Sol, high effort, 24 workers, generator for the Greek rewriting set (`data/gen_greek_rewrite.py`, prompt verbatim in the handoff), then the
  round-one correction pass.
- Luna, `gpt-5.6-luna`, medium effort, default tier, 64 workers, for OpenAssistant (done), safety, Nemotron chat, tool use, multilingual:
  identity, framing, tone and skill labels on conversational rows. Same rubric v3.

Luna's measured weaknesses and the mitigation are in the handoff, section 4.
