# Annotation handoff for independent review, 2026-09-05

Everything a reviewer needs to check the data screen for round two: what runs, where the files are, how each number was
produced, what is known to be weak, and what to judge. The plan it serves is `ROUND2_DATA_PLAN_20260905.md`.

## 1. What the screen is

A sorting pass over the training rows, done by a model (or a program) before we build the training file. Each row, with all
its turns and tool calls, goes to a judge with a fixed rubric and a fixed answer form (nine fields). The judge returns one label per
row; the label is stored next to the row id; nothing is edited or deleted during the pass. At assembly time the labels decide:
drop identity rows and wrong answers, cut single identity lines, count skills per source, and pick adaptation candidates if we adapt.

The nine fields: `vantage` 0-3, `frame_type`, `skill`, `quality` 1-3, `mannerism`, `imperatives`, `disposition` keep/adapt/drop,
`adapt_note`, `why`. Schema: `data/annotation_schema.json`. Rubric: section 7 below, verbatim.

## 2. Who judges what, and why

| judge | model, effort, tier, workers | blocks | reason |
|---|---|---|---|
| checker | exact program | Dolci logic puzzles, word sorts (done); IFEval checkers on ifeval-like; final-answer match on OpenMath (Saturday) | a program beats any model; the puzzles proved it (Luna caught 5 of 8 wrong ones and falsely dropped 6 correct ones) |
| Sol | gpt-5.6-sol, medium, default, 24 | FLAN (measurement only, now stopped), Science 20k, spot-check samples, and every row Luna labels code/math/reasoning inside the Luna blocks | correctness is the question; the owner's rule is to route such rows to Sol in advance as the only judge, not to re-check Luna |
| Sol | gpt-5.6-sol, high, default, 24 | generator of the Greek rewriting set, 2,000 rows | writing needs the strongest model; correction pass and screen follow |
| Luna | gpt-5.6-luna, medium, default, 64 | OpenAssistant (done), safety, Nemotron chat, tool use, multilingual | identity, framing, tone, skill on conversational rows, where correctness is rarely the issue |

Routing is by dataset first (`SFT_ROUND2_PLAN.md` §2b) and by category second (`data/route_technical.py`: Luna's skill label
in {code, math, reasoning} sends the row to Sol, whose label replaces Luna's).

## 3. Measured performance of the judges

Ground truth v2 (`results/ground_truth/gt_v2_rows.jsonl`, labels `gt_v2_labels.json`): 63 rows, 7 per screened block, full turns,
hand-labelled by me under rubric v3; 2 excluded (Nemotron rows whose prompt is withheld). Scorer: `data/gt_score.py`.

| measure | Luna | notes |
|---|---|---|
| same verdict as the hand label | 55 of 61 | |
| identity rows found | 4 of 4, no false identity | the category that matters most |
| rows to act on (adapt or drop): recall | 6 of 7 | the miss is a level-2 case: a recipe on US ingredients and units |
| rows to act on: precision vs my labels | 6 of 11 | the 5 extra drops are correctness calls; 2 verified right, 1 verified wrong, 2 arguable |

Calibration on 100 Dolci puzzle rows against the exact checker (`~/sft_annot/calib/`):

| judge | rows Luna/Sol called wrong | actually wrong (checker) | false drops | missed wrong |
|---|---|---|---|---|
| Luna, 51 zebra puzzles | 11 | 8 | 6 | 3 |
| Sol, same 51 zebra puzzles | 10 | 8 | 4 | 2 |
| word sorts, 49 rows, all correct per checker | Luna 0, Sol 0 called wrong | 0 | 0 | 0 |

Sol as second opinion on Luna's "wrong answer" drops in OpenAssistant (`~/sft_annot/labels/dolci_chat.sol.jsonl`): 487 rows,
349 confirmed, 138 overturned (28%). Examples of overturns: the counterfeit-bill puzzle (Luna 140, Sol 100, Sol right), a
first-aid answer Luna called dangerous and Sol appropriate. This pass was stopped on the owner's instruction (it only catches Luna's
false drops, not its misses) and replaced by advance routing.

Sol spot-checks of Dolci's new sources (`~/sft_annot/labels/dolci_*_sample.labels.jsonl`, 300 rows each): Python Algorithms 20 wrong (6.7%),
so the block is Sol-screened before use; Verifiable Reasoning 3 wrong (1%), taken as clean. Our own checker runs on the sources that claim
verification (cluster, `verified/`): ifeval-like 56,339 rows through the IFEval checkers, 47 fail (0.08%); OpenMath GSM-style 100,000 rows
through the final-answer match, 29 mismatch (0.03%). Both claims hold; the puzzles were the exception.

## 4. Luna's weaknesses, and what is done about each

1. **Correctness judgements are noisy both ways.** On puzzles: 14% false drops of correct rows, 3 of 8 wrong rows missed. On OpenAssistant:
   28% of its wrong-answer drops overturned by Sol. Mitigation: no unverified correctness-heavy source is judged by Luna. FLAN, Science, the
   coding and reasoning samples go to Sol; puzzles, ifeval-like and OpenMath go to programs; Luna's own code/math/reasoning labels are re-judged
   by Sol with Sol's label replacing Luna's. What is NOT mitigated: Luna's misses on explanation and advice rows inside chat blocks (43% and
   20% of OpenAssistant). We accept those, because the alternative is Sol on everything, about 4 days more, and those rows come from a 2026
   generator (Nemotron) or a human (OpenAssistant) rather than from an old model.
2. **Under-flags mild foreign framing** (level 2). One miss in the ground truth, the cheesecake row. Mitigation: none beyond the lexicon scan;
   level-2 rows are about 1% and the owner's hypothesis is that language-neutral framing may not matter if Greek data covers each category.
   To be tested with a screened-vs-unscreened arm, not fixed in the screen.
3. **Cannot verify numbers or logic.** Mitigation: checkers wherever the task has one.
4. **Strengths worth keeping it for:** identity 4 of 4 with no false positives; consistent tone labels; 3,900 to 5,000 rows an hour.

Sol's own errors are not caught by a third judge. What bounds them: the checker calibration above (Sol on puzzles: 4 false drops among 43
correct rows, 9%, and 2 of 8 wrong rows missed, against Luna's 6 and 3; better, not clean, at 825 rows an hour on this reasoning-heavy
material), the 300-row spot-checks, and the owner's blind reads. Consequence: where a checker exists it stays the authority over Sol too.

## 5. Files and how to reproduce every number

Repository: `subprojects/12_greek_sft_experiments/`, git range for this work `578f927b..HEAD` (Friday 4 September).

| what | where | reproduce |
|---|---|---|
| exported rows (full turns) | Mac `~/sft_annot/core_export/*.jsonl`; cluster `/iopsstor/scratch/cscs/fffoivos/sft_round1/core_export/` | `data/export_core.py` (ONLY=block env re-exports one block) |
| labels | `~/sft_annot/labels/<block>.labels.jsonl` (judge in field `judge`), `<block>.sol_routed.jsonl` (category pass), `dolci_chat.sol.jsonl` (retired second-opinion pass) | `data/annotate_core.py <export> <labels> <workers> blocks…` with TERRA_MODEL set |
| ground truth and scoring | `results/ground_truth/gt_v2_*`, `results/ground_truth/luna_v2/` | `python3 data/gt_score.py results/ground_truth/luna_v2/labels.json results/ground_truth/gt_v2_labels.json results/ground_truth/gt_v2_rows.jsonl` |
| puzzle check | `~/sft_annot/verified/puzzles/{keep,wrong,unchecked}_ids.txt`, shard logs `~/sft_annot/puzzle_check_cluster/` | `python3 data/zebra_check.py <rows.jsonl> [labels.json]`; keep-list `data/puzzle_keep_list.py` |
| judge calibration on puzzles | `~/sft_annot/calib/puzzles` (Luna), `~/sft_annot/calib/puzzles_sol` (Sol) | `data/terra_probe.py ~/sft_annot/calib_puzzles.jsonl <out> 100 16` with TERRA_MODEL |
| merged keep-lists | `~/sft_annot/keep_lists/` | `python3 data/build_keep_lists.py ~/sft_annot/labels ~/sft_annot/verified ~/sft_annot/keep_lists` |
| Greek rewriting set | `~/sft_annot/greek_rewrite_2k.jsonl` | `data/gen_greek_rewrite.py <out> 2000 24` |
| samples of every source, full text | https://claude.ai/code/artifact/941df833-a155-45ab-af26-939f88e4db96 | `cluster/dataset_samples_page.py` |
| run logs | `~/sft_annot/annot_luna.log`, `annot_sol.log`, `annot_sol_science.log`, `gen_greek_rewrite.log`, `route_technical_loop.log` | |
| ledger and log | `EXECUTION_LOG.md`, `execution_state.json` | |

Counts at 23:40 Friday (`build_keep_lists.py`):

| block | labelled | keep | adapt | drop | identity | wrong |
|---|---|---|---|---|---|---|
| OpenAssistant (Luna, Sol on 387 technical rows) | 5,305 | 4,088 | 232 | 985 | 366 | 858 |
| safety (Luna, running) | 2,667 | 1,696 | 274 | 697 | 556 | 413 |
| Tulu FLAN (Sol, stopped) | 1,323 | 1,115 | 15 | 193 | 2 | 193 |
| Dolci Python Algorithms sample (Sol) | 274 | 255 | 0 | 19 | 0 | 19 |
| puzzles and word sorts (checker) | 12,503 | 11,163 | 0 | 1,318 | 0 | 1,318 |

## 6. Known defects and their state

- Export v2's shard picker read six of fifteen Dolci shards twice: OpenAssistant 6,952 rows became 5,305 unique, safety 20,000 became 15,650,
  "other" 7,497 became 6,808. Local files and the OpenAssistant labels are deduplicated; the cluster copies still hold the duplicates.
- Dolci Tool Use stores calls in `function_calls`; early exports had empty assistant turns; fixed, re-exported (40k).
- Nemotron IF-Chat v3 withholds the first user prompt for WildChat-seeded rows (content null, only a sha256): 41% of the chat split.
  The export filters them; 100k clean rows are on the Mac, 150k being exported. Recovery by hashing WildChat-1M is possible, not done.
- The judge prompt truncates each turn at 3,000 characters and the conversation at 9,000; Nemotron rows average 23 KB, so later turns are unseen.
- One judge call that exceeded 10 minutes killed a whole worker pool (category pass, Friday 23:20); calls are now caught and recorded as
  PARSE_FAIL rows that can be re-run.
- FLAN rows can concatenate several source articles (one summary row in the ground truth); a dataset construction bug, FLAN is out anyway.

## 7. The prompts, verbatim

### 7.1 Rubric v3 (both judges, `data/terra_probe.py`)

```
You label ONE training row (a user prompt and an assistant answer) for a Greek assistant project. Judge the ASSISTANT ANSWER.
The row may contain several turns: the USER field is the user turns in order, the ASSISTANT field the assistant turns in order; pair them in order. Text may be cut at 2,500 characters: judge what is shown and do NOT penalise truncation or a missing ending.

vantage (0-3): does the answer presuppose a non-Greek world in a way that matters to a Greek user?
 0 neutral: math, code, tables, format tasks, tool calls, rewriting or summarising given text, general knowledge with no locale.
 1 incidental: a foreign name, place, brand, currency or unit appears but the advice does not depend on it. This includes every case where the USER fixed the foreign setting (asked about a US county, US law, a US trip, gave dollar amounts): answering inside the user's own frame is level 1.
 2 framed: the answer itself introduces a foreign world that would misinform or misfit a Greek user who did not ask for it: procedures of the IRS or NHS, ZIP codes, "your state's law", prices or budgets given as advice in dollars, imperial units in advice, holidays, school systems, foreign institutions presented as the user's own.
 3 asserted: the assistant describes itself as an AI, a language model or an assistant with capability or knowledge limits ("as an AI I cannot…", "I'm an AI, not a doctor", "my knowledge cutoff is…", "I don't have access to real-time data"), names a creator or product (OpenAI, Ai2, ChatGPT, OLMo), or speaks as a member of a foreign nation ("our national anthem"). Any such sentence makes the row level 3 even if the rest is useful.
frame_type: what carries the framing (identity for level 3; "none" for levels 0-1).
skill: the main thing the row teaches.
quality: 1 wrong, harmful or useless in what is shown; 2 acceptable; 3 good. Incomplete because of the 2,500-character cut is NOT quality 1.
mannerism: true only if the answer opens or closes with chatbot phrases ("Great question!", "Certainly!", "I hope this helps", "Let me know if you need anything else") or gushes with exclamation marks.
imperatives: true if the answer gives the user second-person commands they did not ask for.
disposition:
 keep = levels 0-1 with quality 2-3.
 adapt = the skill is valuable and the only problem is the frame: level 2 with quality 2-3, or level 3 where the identity sentence is one line on an otherwise good answer.
 drop = quality 1; level 3 where the identity or refusal boilerplate is the substance of the answer, and every answer whose subject is the assistant itself (how it was trained, who made it, how it compares to ChatGPT); refusals that cite a foreign product's policy; persona chats that ignore the user's request; sexual, fetish, demeaning or vulgar roleplay; fabricated private records about named people.
adapt_note: for adapt only, what to change, at most 20 words. why: at most 15 words.
Return ONLY the JSON object.
```

The row is appended as `SOURCE: <block>` and `CONVERSATION (turns in order; TOOL turns are the tool's own outputs, not fabrications by
the assistant):` followed by `[ROLE]` blocks, each turn cut at 3,000 characters, the whole at 9,000.

### 7.2 Greek rewriting generator (Sol, high effort, `data/gen_greek_rewrite.py`)

The passage genre, topic, register, length and task are drawn per row from fixed lists in the script (20 genres in Greek settings,
40 topics, 15 tasks). The prompt, with the slots filled:

```
Γράφεις δεδομένα εκπαίδευσης για έναν ελληνικό βοηθό τεχνητής νοημοσύνης. Όλοι οι χρήστες είναι Έλληνες και ζουν στην Ελλάδα.

Βήμα 1. Γράψε ένα ρεαλιστικό ελληνικό κείμενο: {genre}, με θέμα «{topic}», ύφος {register}, περίπου {words} λέξεις. Το κείμενο εκτυλίσσεται σε ελληνικό περιβάλλον: ελληνικά ονόματα, τόποι, υπηρεσίες, ευρώ, ελληνικές συνήθειες και ημερομηνίες. Να είναι συγκεκριμένο, με ονόματα, ποσά, ώρες και λεπτομέρειες, όπως ένα πραγματικό κείμενο, όχι ένα γενικόλογο υπόδειγμα.{extra}

Βήμα 2. Ο χρήστης δίνει το κείμενο και ζητά: «{instruction}»

Βήμα 3. Γράψε την απάντηση του βοηθού. Η απάντηση εκτελεί ακριβώς ό,τι ζητήθηκε (αν ζητούνται 3 προτάσεις, είναι 3 προτάσεις), μένει πιστή στο περιεχόμενο του κειμένου, δεν προσθέτει πληροφορίες που δεν υπάρχουν εκτός αν ζητείται ανάπτυξη, και δεν περιέχει εισαγωγές ή επιλόγους του τύπου «Φυσικά!», «Ορίστε», «Ελπίζω να βοήθησα». Ξεκινά κατευθείαν με το ζητούμενο. Ο βοηθός δεν αναφέρεται ποτέ στον εαυτό του.

Επίστρεψε ΜΟΝΟ ένα JSON αντικείμενο με τα πεδία passage, instruction, answer. Το πεδίο instruction είναι η οδηγία του χρήστη όπως θα την έγραφε ένας Έλληνας χρήστης, φυσικά και σύντομα (μπορεί να διαφέρει λίγο στη διατύπωση από την παραπάνω).
```

## 8. What I would like the reviewer to judge

1. Is the routing rule (checker > Sol by source and category > Luna) sound given the measured numbers, and is anything routed to Luna that
   should not be? In particular the explanation and advice rows of Nemotron.
2. Is "verified answers, or a recent generator" applied consistently in the mix table, and are the dropped sources really worse than the kept ones?
3. Does the Sunday timeline hold at the measured rates, and what is the first thing to cut if it slips?
4. Is the budget arithmetic right, and is option C (half mix, one epoch) a sensible stage 1 under the current cap?
5. Are the known defects handled, and is any of them a threat to the mix (the duplicate rows on the cluster, the 9,000-character judge window)?
6. Anything in the ground-truth method that inflates the judges' scores.

## 9. Where to put feedback, and how I pick it up

- **Feedback file:** `docs/reviews/FEEDBACK_ROUND2_DATA_20260905.md` (created empty, with headings). Write there in any form: numbered
  findings, questions, or a verdict line. I watch the file for changes while the session runs and read it at every wake-up, and I answer in
  place under each finding with what I changed or why not, marked `→ claude:`.
- **Reviewer brief for a third party or a model:** `docs/reviews/REVIEW_BRIEF_ROUND2_DATA_20260905.md`, the context file to hand to any reviewer.
  For a cross-vendor model review the harness is `~/.claude/skills/autonomous-run/scripts/codex_review.sh`:
  `IMPLEMENTER_MODEL=claude-fable-5-1 CODEX_EFFORT=xhigh ~/.claude/skills/autonomous-run/scripts/codex_review.sh round2-data 578f927b..HEAD docs/reviews/R2_data_screen.gpt-5.6-sol.md docs/reviews/REVIEW_BRIEF_ROUND2_DATA_20260905.md`
  Its output lands in `docs/reviews/R2_data_screen.gpt-5.6-sol.md`, which I also watch.
- Pending numbers in this document (Sol on the 100 puzzles, the reasoning spot-check) are filled in as soon as the runs end; the git log
  shows when.
