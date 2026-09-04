# Round two, data preparation: the plan to Sunday 6 September 2026

Written Friday 4 September, 23:50, after several reorientations during the day. This document supersedes the mix and
routing sections of `SFT_ROUND2_PLAN.md` where they differ; it is the one to review. Companion: `ANNOTATION_HANDOFF_20260905.md`.

**Feedback on both documents goes in `docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`** (full path
`/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md`).
I watch that file and answer under each finding in place, marked `→ claude:`. A reviewer brief sits next to it.

## 1. Objectives and hard limits

- Goal of stage 1: a broad-ability SFT set for the Greek-CPT Apertus-8B that keeps the Greek vantage, ready to train.
- Time limit: **data preparation finished by late Sunday 6 September** (mix assembled, decontaminated, tokenized, receipts written).
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
| chat, human-written | OpenAssistant (Dolci Chat), screened | volunteers, 2023 | Luna + Sol on technical rows | 4.3k (4,088 keep + 232 adapt) |
| coding | Dolci "Python Algorithms" | 2025 | Sol spot-check: 20 of 300 wrong (6.7%), so the block is screened by Sol; 20k screened by Sunday, the rest later | 20k screened now (60k exported) |
| reasoning | Dolci "Verifiable Reasoning" | 2025 | Sol spot-check: 3 of 300 wrong (1%), taken as clean | 30k |
| reasoning | Dolci logic puzzles and word sorts | generator | exact brute-force checker | 11,163 confirmed |
| tool use | Dolci Tool Use | 2025 | Luna identity screen | 30k |
| science | Dolci OpenThoughts3+ Science | 2025 | Sol screen (20k exported) | 15k |
| other European languages | SmolTalk2 multilingual-8, Nemotron non-English European rows | Qwen3-32B 2025, GLM-5 2026 | Luna (multilingual only if time allows; else lexicon identity scan) | 25k + 10k |
| safety | Dolci WildGuardMix and CoCoNot, screened | 2024 | Luna; 21% identity so far, so mostly adapt or drop | 10k |
| Greek, rewriting and summarising | written by Sol from scratch, in Greek | gpt-5.6, 2026 | Sol correction pass, screen, owner blind read | 2k (the 10% start) |
| Greek | our round-one adapted set | Sol, 2026 | ours | 20k, seen twice |
| **total** | | | | **about 580k rows, about 0.35B tokens** |

Dropped under rule (2): Magpie Ultra, OpenHermes, Tulu WildChat, EuroBlocks fr/de, Dolci persona math, Evol-CodeAlpaca, Tulu persona Python, TableGPT.
Dropped by measurement: Tulu FLAN and Dolci FLAN (Sol finds 193 of 1,323 wrong, 14.6%, on 2015-era labels).

## 3. Timeline to Sunday, with the judge rates measured tonight

Rates: Luna 4,160 rows an hour at 64 workers (measured on safety, first 1,000 rows); Sol 1,300 to 1,700 at 24 on chat, 825 on puzzles;
checker exact and free. Times are Athens time. Nemotron 100k therefore takes 24 h, not 20: done Sunday about 03:00, tool use 30k by about 10:00.

| when | Luna (64 workers) | Sol (24 workers) | me (CPU, cluster login node, polite) |
|---|---|---|---|
| Fri 23:45 | safety, 13k left, about 3 h | spot-checks, 26 code + 300 reasoning rows, 20 min | exports running: multilingual 25k, Nemotron 150k |
| Sat 03:00 | Nemotron 100k, about 20 h | Greek rewriting set, 2,000 rows, high effort, about 5 h | exports: OpenMath 100k, Python Algorithms 60k, Verifiable Reasoning 30k, Precise IF 137k, ifeval-like 56k |
| Sat 08:00 | | Science 20k, about 13 h | re-run IFEval checkers on ifeval-like; Sol spot-checks on Precise IF 300 and OpenMath 300; owner reads 40 Greek rewriting rows: https://claude.ai/code/artifact/dc57edac-97cc-472e-810e-e336f03d63f2 |
| Sat 21:00 | Nemotron running | Science done; coding 20k under Sol, about 13 h | assemble-mix script, decontamination lists, tokenizer run on a 5% dry run |
| Sun 03:00 | Nemotron done; tool use 30k, about 7 h | technical rows of Nemotron, about 12k, 8 h, in parallel with coding on the same 24 workers only if the account allows, else after | |
| Sun 10:00 | tool use done, or cut to the lexicon scan if late | coding and Nemotron technical rows done | |
| Sun 10:00 to 22:00 | | correction pass on the Greek rewriting rows, 2 h | keep-lists merged, mix assembled, decontaminated against all ILSP sets + IFEval/GSM8K, tokenized, receipts, plan updated |
| Mon | | | training launch, only once the cap decision is in |

Slack: about 6 hours on Luna, about 10 hours on Sol. If Luna runs slower than 5,000 an hour, tool use is cut to the 30k we need,
then multilingual goes to the lexicon identity scan instead of Luna. Nothing on the critical path waits for the owner except the
two decisions in section 6.

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
