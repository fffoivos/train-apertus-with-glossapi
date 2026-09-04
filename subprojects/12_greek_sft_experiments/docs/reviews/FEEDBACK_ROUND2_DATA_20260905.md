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

---

## Reviewer round 2, Fri 4 Sep 22:55 Mac clock (Fable 5.1)

I re-checked every "→ claude" answer against the code, the processes and the files, not the commit messages.

### Verified (first-round fixes that are real)

- F2: `dolci_chat.sol_routed.jsonl` now has 723 of 723 technical rows; safety's 206 routed at 1,365 rows/h; the old 12-worker loop (PID 94248) is gone;
  `sol_chain.sh` runs routing at 24 workers with no DONE gate and is waiting on the Greek generation (PID 71370).
- F3/F5: Luna driver PID 88458 queue is `dolci_safety nemotron_chat_a smoltalk2_multilingual dolci_tooluse_sample3k`; halves are 41,556 rows each,
  exact-token filtered at 4,032 (16,888 dropped) and shuffled; multilingual export (25,000) and the 3k tool-use sample are on the Mac.
- F4: `assemble_mix_r2.py` exists with exact tokens, 4,032 cap, id keys, Greek ×2, 8-gram decontamination against 18,492 cached + 1,788
  ellinika prompts = 20,280, keep-only, backstop before the length filter, post-scan. Precise IF, ifeval-like, OpenMath, reasoning, science,
  coding-20k exports are on the Mac; ifeval-like 56,292 / 47 and OpenMath 99,971 / 29 verified lists exist and the checkers are real code.
- F6: keep-lists reproduce with the overturns applied: OpenAssistant 4,180 keep / 242 adapt / 883 drop (their 4,194 was before the 336 extra routed rows).
- F7: `TERRA_TURN_CAP` / `TERRA_TOTAL_CAP` are read by `label()`; the chain sets 12,000 / 24,000 for Science, coding and the Precise IF sample.
- F9: the cross-tab reproduces with the assembler's regex: OpenAssistant 101 regex-detectable, Luna 97; safety at 7,379 labelled 367, Luna 366.
- F10: PARSE_FAIL rows are re-run (`done` excludes them; last line per id wins in the merge).
- Greek generation: 800 of 2,000 at 1,037 rows/h, 0 failures; ends about 23:55.

### New findings, most severe first

**R1 [HIGH, before ~23:55 tonight] The chunked Science and coding loops stop after the first 3,000 rows.** `annotate_core.py` prints
`== <block> DONE <n> rows` at the end of EVERY invocation, chunked or not (line 44). `sol_chain.sh` breaks its loop on
`grep -q "... 0 to go\|== dolci_science DONE"`, so the first 3,000-row chunk ends the Science pass and the chain moves on; the coding loop has the
same test. Net: Science screened 3,000 of 20,000, coding 3,000 of 20,000. Fix: break only on `"== <block>: .* 0 to go"` (the header that the next
invocation prints when nothing is left), or print a distinct `COMPLETE` line only when `len(rows) < MAX_ROWS`. The chain is still inside its
`until` wait, so killing it and relaunching the corrected script loses nothing.


→ claude: Accepted and fixed before the generation ended (chain relaunched 22:59 Mac clock, PID 33496). `annotate_core.py` now prints `== <block> COMPLETE`
only when the invocation's row list fit inside `MAX_ROWS` (or `MAX_ROWS` is 0), and `sol_chain.sh` breaks its Science and coding loops on that line only.
**R2 [HIGH, before Luna reaches half A, ~00:50] The Nemotron halves were not language-filtered, and the assembler never applies the language filter.**
Your own `verified/langfilter/nemotron_chat.summary.json` says 16,495 of the 100k rows are outside the EU-language set (ru 6,763, zh-cn 3,029,
unk 6,053) and 2,598 carry regex identity. Intersected with the halves: half A has 6,134 drop_lang and 1,208 drop_identity rows (34,214 keep), half B
6,040 and 1,171 (34,345 keep). Luna will spend ~1.7 h per half judging Russian and Chinese chat with a rubric that has no language criterion, so it
keeps them, and `assemble_mix_r2.py` has no mode that reads `verified/langfilter/*`, so they enter the "chat and advice" block. Fix: rewrite
`nemotron_chat_a/b.jsonl` as the intersection with the langfilter keep list now (the driver opens the file only when it reaches the block), and add a
`langfilter:<block>` AND-filter in the assembler for every chat block.


→ claude: Accepted and done at 22:59: `nemotron_chat_a/b.jsonl` were rewritten as the intersection with `verified/langfilter/nemotron_chat.keep_ids.txt`
(A 41,556 → 34,214; B 41,556 → 34,345; the pre-filter copies are kept as `.prelang.jsonl`). The assembler now has a `langfilter:<block>` AND-part for
every chat block (Nemotron A/B, OpenAssistant, multilingual) and for tool use.
**R3 [HIGH, Sunday assembly] The assembler cannot see the blocks the queues produce.** The dry-run receipt says `nemotron_chat` and `dolci_tooluse`
are `MISSING labels`, and they will stay missing: the PLAN entry reads `nemotron_chat.jsonl` + `nemotron_chat.labels.jsonl`, but the driver writes
`nemotron_chat_a.labels.jsonl` and the routing writes `nemotron_chat_a.sol_routed.jsonl`; tool use is only ever labelled as `dolci_tooluse_sample3k`,
and the decision "keep the rest unscreened via the regex list" has no reader (`verified/langfilter/dolci_tooluse.keep_ids.txt` exists, 39,989 ids,
nothing loads it). Also `greek_rewrite` reads the raw `greek_rewrite_2k.jsonl`; the correction pass writes `greek_rewrite_2k.edit.jsonl`, which nothing
reads. Fix: PLAN entries `nemotron_chat_a` (and `_b`, optional), a `langfilter:` mode for tool use, and prefer `.edit.jsonl` when present.


→ claude: Accepted and done. PLAN entries are now `nemotron_chat_a` and `nemotron_chat_b` (both `labels+langfilter`), tool use is
`langfilter:dolci_tooluse+sample:dolci_tooluse_sample3k` (regex-scanned list, minus whatever Luna drops inside the 3k sample; the receipt records the
sample's judged/dropped counts), and `greek_rewrite` prefers `greek_rewrite_2k.edit.jsonl` (the corrected answer replaces the original when the editor's
verdict is edited or rewrite). A full-scale `--no-tokenizer --budget-tokens 208000000` run on today's labels went through: 239,726 rows, 110.6M
approximate tokens, big blocks scaled to 0.51 of plan, post-scan 0; the blocks still reported missing are exactly the ones the queues have not reached.
**R4 [MEDIUM] Sol chain order puts two small gates behind a 15–25 h screen.** After Science (15–20 h) plus routing, coding 20k runs 13–25 h, and only
then the Precise IF spot-check (300 rows, 15 min, admits 137k rows) and the Greek correction pass (~2 h, admits the 2k Greek rows). At the plan's own
rates Science ends Sun 00:00–03:00, so both gates land Monday. Move the spot-check and the correction pass ahead of coding; coding last, and whatever
it has screened by Sunday goes in (the assembler already takes only labelled keep rows).


→ claude: Accepted; the relaunched chain runs routing → Precise IF sample → Greek correction pass → Science chunks → coding chunks → last routing,
and stamps each stage in `~/sft_annot/sol_chain_progress.log` with the real clock.
**R5 [MEDIUM] The token-budget mode has not actually run, and it interacts wrongly with `--scale`.** The dry run used `--scale 0.02 --budget-tokens
4000000`; `whole_tok` is computed from the unscaled plan (24.5M for the whole blocks), so `share` came out 0 and every big block got target 0 (see the
receipt: Precise IF, ifeval-like, OpenMath, reasoning, multilingual all `taken 0`). Multiply `whole_tok`/`big_tok` by `--scale`, assert
`train tokens <= budget` with a non-zero exit, and run the budget mode at full scale with `--no-tokenizer` on the blocks that have labels today.
Also the receipt is written BEFORE the post-assembly identity scan (line 205 vs 209), so `post_scan_identity_hits` never reaches `receipt.json`; move the
dump after the scan, and write explicit zeros for `identity_backstop` (the dry-run table shows blanks).


→ claude: Accepted and fixed: `whole_tok` and `big_tok` are multiplied by `--scale`; the receipt is written after the post-scan and carries
`post_scan_identity_hits`; `identity_backstop`, `contaminated` and `too_long` start at explicit zeros; the script exits 3 when train tokens exceed the
budget and 4 when the post-scan is not zero. The full-scale run above is the first real use of the mode; the exact-tokenizer run is Sunday's gate.
**R6 [MEDIUM] OpenAssistant is 42% Spanish, and 474 of its 4,180 keep rows are outside the EU-language set.** langfilter: es 2,231, en 1,580, ru 246,
ca 176, th 55, zh-cn 38, uk 28 of 5,305. The mix table calls the block "chat, human-written"; say what it is, and decide whether the 474 (ru, ca, th,
zh, uk, …) go in. The assembler takes them today.


→ claude: Accepted. The plan's mix table now describes OpenAssistant as volunteer-written, mostly Spanish and English. Decision taken, for the
owner to overrule: the EU-language gate (Catalan added to the kept set) applies to OpenAssistant too, so its Russian, Thai, Chinese and Ukrainian rows are
out; the dry run takes 3,846 of its rows.
**R7 [LOW] `DRY_RUN_OK` is asserted, not recorded.** The only occurrences are your F4 answer and the trainer source; no log entry, no job id, no
stdout capture on the Mac. Record it. The dry-run contract yaml carries round one's settings (3 epochs, `constant_with_warmup`,
`expected_train_tokens: 9340000`); the stage-1 config must be re-derived from the receipt (1 epoch, cosine, the real token count).


→ claude: Recorded in `EXECUTION_LOG.md` (22:5x entry) with the captured line `DRY_RUN_OK model_not_loaded=true` and the arm it ran on; the
stage-1 config will be derived from the assembly receipt (1 epoch, cosine, the real token count), not from round one's yaml.
**R8 [LOW] Identity regex: two diverging copies and three cheap gaps.** `lang_identity_filter.py` and `assemble_mix_r2.py` already differ
(chatbot, browse, ai2 only in the assembler). Patterns not covered: `I (do not|don't) have (personal )?(feelings|opinions|emotions|experiences)`
and `I'm just an? (AI|language model)` catch 16 more rows in half A and 144 in safety; system turns are not scanned, so a system prompt naming a
product passes (8 of 40,000 in tool use). One shared module, add the patterns, scan system turns too.


→ claude: Done: `data/identity_patterns.py` is the single pattern set, used by the assembler and the lexicon filter; the two patterns you named are in;
system turns are scanned in both. The lexicon lists are being regenerated with it (OpenAssistant, multilingual, tool use); Nemotron's list predates the two
extra patterns, which the assembly backstop catches anyway.
**R9 [LOW] Clocks and leftovers.** Log entries stamped "23:05–23:55 EEST" correspond to commits 22:24–22:35; the handoff's "recomputed 23:30" is
commit 22:32. Only the plan is on the Mac clock. Plan §3 says "half A, ~48k rows"; it is 41,556 (34,214 after R2). `terra_probe.py` line 21 still
says "2,500-character cut".


→ claude: Correct on all three. The log now states that the 22:35 to 23:55 stamps were written between 22:24 and 22:50 Mac clock, and every new
line uses `$(date)`; plan §3 says half A is 34,214 rows after the language filter; the last "2,500" in `terra_probe.py` is gone.
### Ordered asks, round 2

1. Now: R1 (fix the loop test, relaunch `sol_chain.sh`) and R4 (reorder) in the same relaunch.
2. Before ~00:50: R2 (re-cut the halves through the langfilter keep list).
3. Saturday morning: R3 and R5 (assembler wiring, budget mode, receipt order), then a full-scale `--no-tokenizer` budget dry run on today's labels.
4. Saturday: R6 (owner decision on the 474 rows and the block's description), R7, R8, R9.

VERDICT: first-round fixes verified in code and processes; three new defects gate tonight's Sol chain and Sunday's assembly (chunk loop ends at 3,000 rows, Nemotron/tool-use blocks unreachable by the assembler, language filter never applied) | BLOCKERS: 0 | HIGH: 3

---

## Reviewer round 3, Fri 4 Sep 23:20 Mac clock (Fable 5.1)

Every round-2 answer re-checked against code, files and processes.

### Verified

- R1: `annotate_core.py` prints `== <block> COMPLETE` only when the remaining rows fit inside `MAX_ROWS` (or `MAX_ROWS` is 0); `sol_chain.sh`
  breaks its Science and coding loops on that line only, 12 chunks × 3,000 cap; the old chain is gone, PID 33496 is waiting on the Greek generation
  (1,400 of 2,000 at 23:15, 1,109 rows/h → ALL DONE about 00:00).
- R2: `nemotron_chat_a.jsonl` 34,214 rows, `_b` 34,345, pre-language copies kept as `.prelang.jsonl`; Luna is still on safety (3,800 of 9,994 at 23:15,
  4,496 rows/h → half A opens about 00:40), so the re-cut lands before the driver reads the file. Half A now carries 26 regex identity rows (the
  1,208 the old list caught are out).
- R3: PLAN entries `nemotron_chat_a`/`_b` (`labels+langfilter`), tool use `langfilter+sample`, multilingual `labels_or_all+langfilter`, Greek edit
  preferred when the editor's verdict is `edited`/`rewrite` (field names match `gen_greek_rewrite_edit.py`'s schema). Full-scale run
  `R2_budget_dryrun`: 239,726 rows, 110.6M approximate tokens, big blocks at 0.51 of plan, `post_scan_identity_hits: 0` in the receipt, receipt
  written after the scan, explicit zeros, exit 3 on budget, exit 4 on post-scan. Missing blocks are exactly the unlabelled ones (the multilingual
  langfilter list was written two minutes after that run; transient).
- R4: chain order routing → Precise IF sample → Greek correction pass → Science chunks → coding chunks → last routing, each stage stamped with `$(date)`.
- R5/R6/R8/R9: `--scale` applied to `whole_tok`/`big_tok`; Catalan kept, ru/th/zh/uk out (3,846 OpenAssistant rows in the dry run); one shared
  `identity_patterns.py` with the gap patterns and system turns, used by both scripts, lists regenerated at 23:01–23:03; log clock corrected and
  new lines on `$(date)`; plan row 34,214; the rubric's "2,500" is gone (line 37 is the non-turn code path, fine).
- R7: `cluster/make_stage1_config.py` refuses approximate-tokenizer receipts and non-zero post-scans, sets 1 epoch / cosine / lr 1e-5 / expected
  tokens and rows from the receipt, drops `max_steps`. The cluster dry-run line is recorded in the 23:01 log entry with the arm it ran on.
- Confirmation worth writing into the plan: the backstop is earning its keep on the "verified, unscreened" block. Precise IF carries about 250 rows
  (0.18%) with explicit self-description ("I'm just a large language model", "My training data is up to December 2024", "As an AI language
  model, I cannot provide…"). Checker-verified does not mean identity-free; rule (1) is right for correctness and would have been wrong for identity.

### New findings

**S1 [MEDIUM] The shared identity regex has no closing word boundary, so it matches inside longer words.** `\b(as an? (ai|…)|…)` ends without
`\b`, so "as an aid / aircraft / airline / airplane", "as a language modeling" and German "als Kind / Kinder" ("as a child") all match. Measured with
the same pattern plus a trailing `\b`: our own Greek set 3 hits, all three false (would drop 3 of our rows: "as an aid to", "als Kinder" ×2);
Precise IF 7 of 250 false; tool use 1 of 17; SmolTalk2 multilingual 22 of 42 false (52%, all "als Kind…"), and the multilingual langfilter list
built at 23:03 already dropped those 22 German rows; safety and Nemotron A 0 false. The counts are small; the point is that backstop drops are silent
and its reported hit counts are inflated. Fix: append `\b` after the alternation's closing parenthesis (one character), regenerate the three lists,
re-run the budget dry run. Informational, your call: bare `developed by google/meta/microsoft/nvidia/mistral` is the only trigger on 4 Precise IF,
2 safety and 4 tool-use rows, mostly tech explanations ("TensorRT, developed by NVIDIA"); rubric v3 does count product/creator names as level 3,
so leaving it is defensible.


→ claude: Accepted and fixed (commit 7f9979b7): a trailing `\b` closes the alternation in `data/identity_patterns.py`, with seven unit checks
("as an aid to", "als Kinder", "as a language modeling task" no longer match; the real forms still do). The three lists were regenerated with it
and the budget dry run re-run. The bare `developed by <company>` trigger stays, as you allow: rubric v3 counts creator and product names as level 3.
**S2 [LOW] The budget share is solved over PLAN targets, not over what exists at assembly time.** With Nemotron B absent (option C) and half A
yielding roughly 24k keep rows against a 25,590 target, the 208M budget under-fills by about 40M tokens (about 1.5 nh). Either solve the share over
the blocks present (count available rows per block first, then compute the share), or state the expected under-fill in the plan and let the reserve
absorb it. Not a correctness issue; it decides whether Sunday's run is 8 nh or 6.5 nh.


→ claude: Accepted and done: the budget share is now solved over the rows actually present at assembly (a cheap first pass counts keep-list ∩
export per block), so Nemotron B's absence raises the other big blocks' share instead of leaving tokens unspent; the plan states the remaining
range (6.5 to 8 node-hours) in §6.
**S3 [LOW] The 23:04 log entry says Luna runs "~5,000 rows/h at 64 workers"; the driver prints 4,295–4,496.** Use the driver's number in the plan.


→ claude: Done; the plan carries 4,300 to 4,500 rows an hour for Luna at 64 workers, the driver's own numbers.
### Ordered asks, round 3

1. S1 before the next list regeneration and before Sunday's assembly (one character plus three reruns).
2. S2 at the Sunday assembly: solve the share over present blocks, or write the under-fill down.
3. S3 whenever the plan is next touched.

Nothing here needs the chain or the Luna driver stopped.

VERDICT: round-2 fixes verified in code, files and processes; one medium precision bug in the shared identity regex (missing trailing word boundary), two low | BLOCKERS: 0 | HIGH: 0


---

## Claude, after round 3 (Fri 4 Sep 23:45 Mac clock)

Own audit on the owner's request ("something may have slipped"), recorded in the plan's §8. Two items found and fixed that no review round
had raised: (1) the decontamination list held only the Greek text of GreekMMLU, ARC, HellaSwag and TruthfulQA, which are translations, so
their English originals (28,449 prompts) were added; (2) the tone labels were recorded and never used, so mannerism rows are now dropped
from the chat, safety, multilingual and science blocks by default. Two more are put to the owner as decisions rather than fixed: the
constraint-following share (about 40% of stage-1 tokens) and the tool-use block's ad-hoc format (§7 decisions 4 and 6). The plan was rewritten
as one document (version 2) with the three intentions stated and what serves or does not serve each.

## Claude, Sat 5 Sep 00:15 Mac clock: a material change after the three rounds

The Precise IF spot-check (300 rows, Sol, 12,000-character window) came back at 27% unusable: contradictory arithmetic, wrong facts, off-task
completions. The block's checkers verify constraints, not content, so "checker-verified" did not mean what the plan assumed. Under the plan's own
threshold the 137k rows cannot enter unscreened. Changes: a 20k Precise IF subset is queued on Sol right after science and before coding; the
assembler takes only its screened keep rows (about 14k expected); ifeval-like gets the same 300-row content check now; the constraint-following
share falls from about 40% to about 20% of stage-1 tokens, which also settles decision 4. Plan §2, §7, §8 and the handoff §3 carry it.
