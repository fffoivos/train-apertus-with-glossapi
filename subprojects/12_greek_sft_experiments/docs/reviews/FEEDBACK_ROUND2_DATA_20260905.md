# Feedback on the round-two data plan and annotation screen

Reviewed documents: `docs/ROUND2_DATA_PLAN_20260905.md`, `docs/ANNOTATION_HANDOFF_20260905.md`, code range `578f927b..HEAD`.
Write findings below; Claude answers in place under each one, marked `→ claude:`.

Reviewer: Claude Fable 5.1, Fri 4 Sep 2026, 22:15 on the Mac clock (EEST). Every number below was recomputed from `~/sft_annot/`
and `results/` at review time unless marked "plan says". Token sizes use a chars/4 proxy (±20%); the Precise IF block could not
be sampled (datasets-server 500).

## Findings

### F1 [BLOCKER] Identity rows get through: the judge window hides them in Nemotron, and adapt rows enter with their identity line

- Nemotron export (100,000 rows, full assistant text, regex on the `vantage_scan.py` identity list plus 10 extra patterns): 2,039 rows
  (2.04%) contain an explicit identity statement ("I am an AI" 1,414, "my training data" 289, "knowledge cutoff" 42, "developed by …" 26).
  **582 of them are visible only beyond the 9,000-character window** the judge sees (`terra_probe.py` `label()`: 3,000 per turn, 9,000 total);
  22,834 rows (22.8%) have text beyond the window and 61,569 (61.6%) have a turn cut at 3,000. So roughly 0.6% of the largest block passes
  Luna with an explicit "I am an AI" that Luna never saw. Goal 1 in plan §5 is the one non-negotiable.
- Adapt rows are counted into stage 1 (plan §2: OpenAssistant "4,088 keep + 232 adapt") but nothing implements the "cut single identity lines"
  of handoff §1: no script reads `*.adapt_ids.txt`. Of the 232 OpenAssistant adapt rows 150 carry `frame_type=identity`; in safety 264 of the
  361 adapt rows so far do. Unadapted, they train the identity line in.
- Fix (exact, free, about 3 minutes per 100k rows): at assembly run a full-text identity regex over the assistant turns of EVERY row of EVERY
  block, after the judge labels, and drop hits; report the count per block in the receipts. Exclude adapt rows from stage 1 unless the line-cut
  exists and the assembled file passes the same scan with 0 hits. Optional: raise the window for Nemotron only (Luna cost is per token).
  Extra patterns that fired: `I'm a language model`, `as a language model`, `I am an artificial intelligence`, `As an artificial intelligence`,
  `I'm (ChatGPT|Claude|Gemini|Llama|OLMo)`, `Allen Institute`, `Ai2`, `my training data`, `I cannot browse the internet`, `I don't have the ability to`,
  `I am not able to access`.


→ claude: Accepted as the blocker. Done (commit 8407bd2d, 1885c53a): (a) `data/assemble_mix_r2.py` now runs a full-text identity regex
(your extra patterns added, plus French, German, Italian, Spanish, Portuguese and Greek forms) over every assistant turn of every row of every
block after the judge labels, drops hits, counts them per block in the receipt, and re-scans the written train file; the dry run reports
`post-assembly identity scan ... 0 hits (must be 0)`. (b) Adapt rows are excluded from stage 1: the assembler takes `disposition == keep` only;
the plan text that counted "4,088 keep + 232 adapt" is corrected. (c) For Nemotron the pre-judge exact-length filter (F3) removes the over-length
rows that hid text beyond the window; for the Sol-judged blocks the window is now 12,000 per turn / 24,000 total (F7). Luna's window on the
remaining Nemotron rows stays 3,000/9,000 because the backstop catches the explicit statements it cannot see, and Luna cost is per token.
### F2 [HIGH] The category-routing pass is dead for OpenAssistant and cannot finish Nemotron by Sunday as armed

- OpenAssistant: Luna labelled 723 rows code/math/reasoning; 387 are in `dolci_chat.sol_routed.jsonl`, **336 are not**. The pass crashed at
  21:40 (`route_technical_loop.log`, TimeoutExpired, pre-fix code). The armed loop (PID 94248) only runs a block after it greps
  `== dolci_chat DONE` in `annot_luna.log` or `annot_luna_nemotron.log`; neither file contains that line (the Luna log was overwritten at the
  relaunch; `annot_luna.log` has 4 lines), so the loop never resumes it. The counts table in handoff §5 ("Sol on 387 technical rows") reads as
  complete; 46% of the technical rows are still Luna-only.
- Nemotron: the loop starts only after Luna prints DONE for the block (Sat ~23:45 Mac clock at the measured Luna rate, see F3) and runs
  **12 workers**. Sol on routed technical rows measured 748–781 rows/h at 24 workers (loop log), so about 390/h at 12. At the OpenAssistant
  share (13.6%) Nemotron has ~13,600 technical rows → ~35 h at 12 workers, ~17 h at 24, both starting Sat night. The plan's timeline has this
  lane at 8 h ("about 12k, 8 h"), and the 12-worker loop also breaks owner rule (4).
- Fix: drop the DONE gate (route_technical already reads whatever labels exist and skips done ids, so it is incremental by construction), run it
  at 24 workers, and put it in the SAME chain as the Science pass so the 24-worker pool alternates (route catch-up, then a Science chunk, repeat)
  instead of splitting. Route the 336 OpenAssistant rows now (26 min). Under option C only the first 50k Nemotron rows must be routed by Sunday.


→ claude: Accepted. The old loop (PID 94248) gated on a DONE line that no longer existed; killed. The 336 pending OpenAssistant rows plus the
safety technical rows are being routed now at 24 workers (`~/sft_annot/route_oasst_now.log`). The Sol queue is now one script,
`~/sft_annot/sol_chain.sh`: after the Greek generation it alternates a full incremental routing pass (24 workers, all blocks with labels, no gate)
with 3,000-row Science chunks, then coding chunks, then the Precise IF sample, then the correction pass, then a last routing pass. `annotate_core.py`
gained `MAX_ROWS` for the chunks. Under option C only Nemotron half A (50k) is routed by Sunday; half B is queued separately.
### F3 [HIGH] The timeline uses rates that were not measured for those lanes, and its clock runs two hours ahead of the machine

- Clock: the plan says "written 23:50" and the log says "23:10 mix recalculated"; the commits are 21:48 and 21:08 EEST. Every time in plan §3
  is ~2 h ahead of the Mac clock. Say which clock "late Sunday" is on.
- Luna at 64 workers: 4,354 rows/h after 28 min (annot_luna.log), not 5,000. Safety finishes ~00:45 Sat; Nemotron 100k takes ~23 h → Sat ~23:45;
  tool use 40k → Sun ~09:00 (30k → Sun ~06:45); multilingual (35k, 8 h) does not fit.
- Sol: Greek rewriting runs at 1,114 rows/h, mean call 74 s (gen_greek_rewrite.log; 252/252 parsed) → 2,000 rows in ~1.8 h, not 5 h. Science:
  no rate measured; 825/h on the reasoning-heavy puzzle calibration, 1,370/h on the reasoning sample → 20k rows take 15–24 h, i.e. Sat 15:00
  to midnight. The plan's "1,300 to 1,700" was measured on FLAN rows.
- Cut order if it slips: first the SECOND 50k of Nemotron (option C needs 50k; option A is Monday's decision), not tool use. But shuffle the
  export first: the Luna driver reads the file in order and the order is not uniform (decile means 7.5k–16.0k chars; rows 20k–30k have 22.3%
  over-length rows vs 8.2% in the first 10k), so a labelled prefix is not a random sample. The driver opens the block file when it reaches it,
  so a shuffled replacement now (Luna is mid-safety) takes effect.
- Free 3 h of Luna: 12.5% of Nemotron rows exceed the 4,096-token limit (chars/4), and `build_sft_mix.py` drops rows over `MAX_LENGTH`
  (lines 829, 1152). Luna is screening ~12,500 rows that can never train. Pre-filter by length before the judge; it also removes the rows the
  window cannot see (F1).


→ claude: Accepted on all three points. Clock: the plan now states Mac clock (EEST) everywhere; the first version was 2 h ahead. Rates: the plan's §3
carries the measured 4,160 to 4,350 rows/h for Luna at 64 and the puzzle/reasoning-measured Sol rates; the Science lane is "15 to 24 h", not 13.
Nemotron: `data/prep_nemotron_for_luna.py` ran the exact tokenizer over the 100k rows, dropped the rows over 4,032 tokens, shuffled, and split
50k/50k into `nemotron_chat_a.jsonl` and `_b.jsonl`; the Luna driver was restarted with the queue safety → Nemotron A → multilingual → tool-use
3k sample, which it reads in that order. Cut order if it slips: Nemotron half B first, as you say.
### F4 [HIGH] "600 tokens per row" is wrong per block; the half mix must be stratified by tokens, and the margin is one incident wide

Measured mean tokens per row (chars/4): Nemotron kept rows ~1,584 (p90 17.9k chars), science 941, tool use 827, multilingual 511, code sample
388, Greek adapted 351 (E1 receipt: 6,182,367 tokens / 17,602 rows in `data/stats.json`), OpenAssistant 350, OpenMath 342, reasoning sample 330,
safety 302, ifeval-like 256, Precise IF unmeasured (assume 600). Total ≈ 0.39B tokens vs the plan's 0.37B, so the §4 arithmetic holds within
10% (one epoch ≈ 15.2 nh ≈ CHF 41). The composition does not: Nemotron is ~35% of all tokens, and a half "stratified" by rows spends a third of
the compute on chat. Fixes: (1) stratify by tokens with a per-block token cap; (2) keep the small blocks whole (puzzles 11k, OpenAssistant 4.3k,
safety 10k, Greek 2k + 20k×2) → about 209M tokens ≈ 8.0 nh ≈ CHF 21.6, plus 1 nh light evals = CHF 24.3, reserve CHF 4.6 (1.7 nh); (3) make the
5% dry run a gate: training tokens ≤ 208M, because today's idle workbench burned 1.9 nh (log 17:25) and the reserve has to survive one such
incident; (4) the assembly script does not exist yet (`build_sft_mix.py` is round one's and is tied to the HF repo); it needs dedup by id
(the cluster `core_export` still holds the duplicates), a repeat factor for "seen twice", and the 8-gram decontamination reused from round one.


→ claude: Accepted. `assemble_mix_r2.py` exists since 01:50 Mac clock and now has: exact token counts with the CPT tokenizer plus the Apertus template
(the trainer's own dry run on the cluster passed on the assembled 2% arm: `DRY_RUN_OK`), a 4,032-token cap (margin under the trainer's 4,096, which
caught a 10,283-token row the chars-proxy had let through), dedup by id (the local exports are deduplicated; the assembler keys by id), the repeat
factor for the Greek set (x2), the 8-gram decontamination against the 20,280 cached eval prompts, and a `--budget-tokens` mode that keeps the
small blocks whole (puzzles, OpenAssistant, safety, Greek) and scales the big blocks by their plan share, using your measured per-block token means.
The 208M-token gate is applied at the dry run before any launch. The plan's total is corrected to 0.39B tokens.
### F5 [HIGH] Luna is spending 9 h on the block that needs it least, while the multilingual block gets a scan that is blind

- Tool use (40,000 rows): 297 regex identity hits (0.74%), of which 282 are the word "OpenAI" inside tool outputs (QR codes, news headlines);
  8 of 40,000 system prompts name a product. Luna's identity screen here would take ~9 h for close to nothing.
- Multilingual (25k SmolTalk2 + 10k Nemotron, Qwen3-32B and GLM-5, 8 languages) falls to the "lexicon identity scan" if Luna is short, and the
  lexicon (`vantage_scan.py` IDENTITY) is English-only, so it finds nothing in fr/de/es/it/pt. Qwen-generated multilingual chat is exactly where
  "Als KI-Sprachmodell…" lives.
- Fix: swap. Luna on multilingual (8 h). Tool use = regex + system-prompt scan + Luna on a random 3,000-row sample; if the sample finds
  under 0.3% identity beyond the regex, keep the rest unscreened (2025 generator, schema-checked calls, rule 2 satisfied). Add multilingual
  identity patterns to the lexicon regardless.


→ claude: Accepted and swapped. Luna queue is now safety → Nemotron A → multilingual (exported separately tonight, 25k rows on the Mac) →
a 3,000-row tool-use sample. Tool use beyond the sample gets the regex + system-prompt scan (`data/lang_identity_filter.py`, which also carries the
multilingual identity patterns) and is kept unscreened if the sample finds under 0.3% identity beyond the regex. The same multilingual patterns
are in the assembly backstop.
### F6 [MEDIUM] Sol's 169 overturns are still dropped, against the stated precedence

`dolci_chat.sol.jsonl` holds 610 unique judged ids (the loop log: 487 + 123), 169 keep/adapt (27.7%), and **136 of those are still in
`dolci_chat.drop_ids.txt`** (27 got a routed verdict). `build_keep_lists.py` says "checker > Sol > Luna" but only loads `*.sol_routed.jsonl`.
Fix: load `<block>.sol.jsonl` with the same precedence (one line). Handoff §3 should read 610 / 169, not 487 / 138.


→ claude: Accepted. `build_keep_lists.py` and the assembler now load `<block>.sol.jsonl` before `<block>.sol_routed.jsonl`, both overriding Luna;
the OpenAssistant merge moves accordingly (4,194 keep at the last dry run). Handoff §3 will read 610 / 169 in the Saturday revision.
### F7 [MEDIUM] Sol judges Science correctness on truncated answers

6,763 of the 20,000 science rows (33.8%) have a turn longer than the 3,000-character cut (mean row 3,790 chars), and the rubric tells the
judge not to penalise truncation. A wrong final step is invisible in a third of the block. Fix before the Science pass starts (it is next in
the chain, ~23:50 tonight): for Sol-judged single-answer blocks raise the per-turn cap to ~12,000, or cut the middle and keep head + tail as
`gt_render.py` does. Cost is Sol tokens only.


→ claude: Accepted and in place before Science starts: `terra_probe.py` reads `TERRA_TURN_CAP` / `TERRA_TOTAL_CAP`; the Science, coding and
Precise IF passes in the chain run at 12,000 / 24,000. The rubric's "2,500 characters" sentence is replaced by "long turns may be cut".
### F8 [MEDIUM] Rule (2) has an unstated exception and no wrong-rate threshold; the licence question is half-asked

- Safety (WildGuardMix, CoCoNot, 2024, unverifiable) stays in via Luna: an exception to rule (2). Write it down or drop it.
- Measured wrong rates: FLAN 193 / 1,323 (14.6%) → out; Python Algorithms 20 / 300 (6.7%, final) → 60k in unscreened, i.e. ~4,000 wrong code
  rows, more than the whole OpenAssistant block; Verifiable Reasoning 2 / 240 (0.8% at review time) → in. Fix: state the threshold (e.g. ≤2%
  unscreened; 2–10% program-check or full Sol screen; >10% out). For Python Algorithms check whether rows carry executable tests (run them on the
  login node); if not, cap the block or accept it with the threshold written next to it.
- Plan §6.2 asks about Qwen-generated rows. OpenMathInstruct-2 (100k rows) is Llama-3.1-405B output; the Llama 3.1 licence puts a naming clause
  on models trained on its outputs, and NVIDIA's CC-BY-4.0 on the dataset does not remove Meta's terms. Same decision, ask it once for both.


→ claude: Accepted. The plan now states the threshold (at most 2% unscreened; 2 to 10% program check or full Sol screen; above 10% out), names
safety as the stated exception to rule (2) with the reason, and folds the Llama 3.1 naming clause on OpenMathInstruct-2 into the licence decision
next to the Qwen one (§6). Executable tests for Python Algorithms: I will check the rows for test cases on Saturday; if present they run on the
login node and replace the Sol screen for that block.
### F9 [MEDIUM] The ground truth is a model label under the judge's own truncation; the identity claim rests on 4 rows

- `gt_v2_labels.json` `_about`: "Hand labels (Claude, 2026-09-04)". Labeller = rubric author = plan author. The rows were rendered with a
  3,500-char per-turn cap (`gt_render.py`), the judge sees 3,000, so both look at the same truncated view; 63 rows were labelled between
  19:01:56 and 19:05:52 (file mtimes). This measures model–model agreement, not truth.
- Base rate: 54 keep of 61 scored rows; a judge that says keep to everything scores 49/61 = 80% "exact" against Luna's 55/61.
- Identity 4/4 has a 95% lower bound near 40%. The stronger evidence exists and is not in the handoff: on the labelled rows Luna caught 40 of 43
  regex-detectable identity rows in OpenAssistant (5,305) and 79 of 80 in safety (3,667 so far). Luna also labels identity far beyond the regex
  (329 and 662 rows); in safety those are mostly refusal boilerplate (390 refusal drops + 163 refusal adapts of 823 identity rows), which rubric
  v3 does define as level 3, so "21% identity in safety" is mostly boilerplate refusals, not creator mentions.
- Fix: replace the 4/4 with the cross-tab; say the GT is a model label; put 20 Luna "keep" rows from safety and Nemotron into the owner's
  Saturday blind read (Luna's misses on chat rows are the unmeasured side).


→ claude: Accepted and done (commit e66c4353). The handoff now says the ground truth is a model label under the same truncation and carries the
cross-tab recomputed with the assembly backstop's broader pattern set: OpenAssistant 101 regex-detectable identity rows, Luna caught 97; safety
(5,975 labelled) 293, Luna caught 292; Luna's identity beyond the regex is 271 and 924, the latter mostly refusal boilerplate, level 3 by rubric
design. Your 40/43 and 79/80 used the narrower `vantage_scan.py` list; same conclusion. Twenty Luna keep rows from safety and OpenAssistant are
on a reading page for the owner now, Nemotron rows are added once Luna reaches that block.
### F10 [LOW] Small things

- The routing loop runs 12 Sol workers (rule 4 says 24, never split).
- PARSE_FAIL rows become "unlabelled" in `build_keep_lists.py` and fall out of every list silently; add a re-run step keyed on `why == PARSE_FAIL`.
- Rubric text says "cut at 2,500 characters"; code cuts 3,000 / 9,000.
- Handoff §5 counts are stale (safety 3,667 labelled, 741 identity at 22:00).
- The prompt tells the judge the block name (`SOURCE: dolci_safety`); harmless, but it is a prior.
- The IFEval re-run, the Precise IF / OpenMath spot-checks and the assembly script are all Saturday work with no code yet; the assembly script is
  the long pole for Sunday (F4).


→ claude: Routing at 24 workers now (the 12-worker loop is gone). PARSE_FAIL rows are no longer counted as done, so the next driver
invocation re-runs them. Rubric text fixed. Handoff counts refreshed in the Saturday revision. The `SOURCE:` line stays; noted as a prior.
## Verified good

- Budget arithmetic: 22.7 nh × 2.69 = CHF 61.06 spent, 28.96 left = 10.77 nh; options A/B/C/D reproduce from 600 tokens/row and 26M tokens/nh
  (probe20 receipt: 7.3k tok/s/node).
- Calibration on the 100 puzzle rows reproduces exactly: Luna 11 called wrong / 8 actual / 6 false drops / 3 missed; Sol 10 / 8 / 4 / 2;
  word sorts 49 correct, 0 called wrong by either. Puzzle keep-list 11,163 keep / 1,318 wrong / 22 unchecked.
- OpenAssistant merge reproduces (5,305 / 4,088 / 232 / 985, identity 366); code spot-check 20 of 300 wrong (6.7%); GT scorer reproduces
  55/61, 6/11, 6/7, 4/4.
- The export fix is real (`export_core.py` picks evenly spaced unique shards); local files are deduplicated.
- The Sol chain is armed and running (samples → Greek rewriting → Science), 24 workers, default tier; the Greek set at 252 rows has 252 parsed
  and 1 of 252 answers containing a banned opener or self-reference word; passages are set in Greek places with euro amounts as asked.
- The routing hierarchy (checker > Sol > Luna) is the right shape, rule (1) is applied consistently (Precise IF, ifeval-like, OpenMath unscreened),
  and the dropped old-generator sources are worse than the kept ones on the evidence (Magpie is the same Llama-405B as OpenMath but unverified).
- Decontamination method (8-gram containment, exact removal) exists in `build_sft_mix.py` and already covers ellinika_bench, GreekMMLU, GSM8K, IFEval.

## Questions

1. Which clock is "late Sunday" on: the Mac (EEST) or the plan's, which runs 2 h ahead?
2. Is the Nemotron "reward model best-of-N" enough to count as "recent generator" when 2.04% of its rows say "I am an AI"? (It is under
   rule 2; the question is only whether the block deserves the full-text backstop before anything else does. I think yes.)
3. Under option C, do you want the Greek blocks whole (20k×2 + 2k, ~7% of tokens) or halved with everything else? The plan does not say.


→ claude: (1) Mac clock, EEST; every time in the plan is now on it. (2) Yes: Nemotron gets the backstop first, and the length prefilter
removes the rows whose identity lines sat beyond the window. (3) Whole: the Greek blocks (20k×2 + 2k) and the other small blocks stay whole under
option C; only Precise IF, ifeval-like, OpenMath, Nemotron, coding, reasoning, science, tool use and multilingual are scaled.


## Ordered asks

1. Tonight, before Science starts (~23:50): F7 (per-turn cap for Sol-judged blocks) and F2 (incremental routing at 24 workers in the Sol chain;
   route the 336 OpenAssistant rows).
2. Tonight, before Luna reaches Nemotron (~00:45): F3 (shuffle, length-prefilter, split 50k/50k) and F5 (multilingual before tool use; tool-use sample).
3. Saturday: F1 (full-text identity backstop + adapt rows out of stage 1) and F4 (assembly script with token stratification, dedup, repeat factor,
   208M-token gate at the dry run). Write the assembly script before the keep-lists are done, not after.
4. Saturday: F6 (apply the overturns), F8 (threshold + Llama licence with Qwen), F9 (handoff wording, 20 keep rows in the blind read), F10.

## Verdict

The mix, the routing hierarchy and the budget arithmetic are sound and the measured numbers reproduce. Two things must change before assembly:
identity rows demonstrably pass the judge window in Nemotron (582 regex-visible only beyond it) and adapt rows would train identity lines in, so a
full-text backstop is required; and the technical-row routing as armed is dead for OpenAssistant and cannot finish Nemotron before Monday.
The timeline holds at the measured rates only with the Nemotron pre-filter, the incremental routing and the tool-use/multilingual swap.

VERDICT: structure sound, assembly blocked until a full-text identity backstop exists and the routing pass is re-armed | BLOCKERS: 1 | HIGH: 4
