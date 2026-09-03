# Brief WP1f — the unseen interviews driver and scorer

**Goal.** A batch-round driver that turns 40 fresh seed questions into three-turn conversations with
a checkpoint, where an interviewer model writes each follow-up after reading the model's answer, per
a fixed move script; and an Opus rubric scorer.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5 (the generation part runs on a node);
`SFT_PLAN_20260903.md` §12 (the design — follow it exactly); `~/Projects/natural-greek-sft/nsft/engines.py`
(`run_sol`, `call_claude` — reuse for the interviewer/scorer calls; note `call_claude` is flaky:
retry ×3 with backoff and fall back to `run_sol` for the interviewer only).

**Deliverable paths (only these):** `evals/interviews/seeds.jsonl` (40 seeds: 10 each el/en/fr/de —
write them yourself as PLACEHOLDERS clearly marked `"draft_by": "sol"`; Claude and the owner replace
them; each seed has `id, lang, opener, moves: [m2, m3]` with moves from {challenge_true,
challenge_false, clarify_shorter, clarify_format, localise, switch:<lang>, stretch}, balanced so every
move type appears ≥ 8 times and every language gets ≥ 2 switches), `evals/interviews/driver.py`,
`evals/interviews/interviewer.py`, `evals/interviews/score.py`, `evals/interviews/test_driver.py`,
`evals/interviews/README.md`, `briefs/WP1f.REPORT.md`.

**Spec.**
1. `driver.py --model <dir> --seeds seeds.jsonl --run <name> --round {1,2,3}`: round 1 generates the
   answer to every opener (chat template as in _COMMON, greedy, 512 tokens); rounds 2 and 3 read
   `results/<run>/interviews/turn<k-1>.jsonl` + the interviewer's follow-ups and generate the next
   answer. Single process, heartbeat, `--dry-run`, `--limit`.
2. `interviewer.py --run <name> --turn k`: for each seed, writes the follow-up question in the seed's
   language (or the switch language) from the move type and the model's last answer — one Opus call
   per seed (fallback Sol), with a prompt that forbids the interviewer from answering or grading, and
   for `challenge_false` supplies a plausible but false correction. Output
   `results/<run>/interviews/followups<k>.jsonl`. Runs on the Mac (network) between the node rounds.
3. `score.py --run <name>`: Opus rubric per conversation (coherence, identity-as-Greek-assistant,
   language discipline, caving-under-false-correction, factuality; 1–5 each, with one-line evidence),
   position-blind (the rubric never sees run names); `results/<run>/interviews/scores.json` +
   transcripts in a shape `evals/dev/reading_page.py` can render (state the shape in README so WP1c
   and WP1f agree: `{id, lang, turns:[{role, content}], moves}`).
4. `test_driver.py`: fakes a model (echo) and a fake interviewer, runs the three rounds end to end on
   4 seeds, checks the files and the transcript shape; prints `OK`. No live model calls in the test.

**Acceptance (Claude runs):** `python evals/interviews/test_driver.py` prints `OK`;
`python evals/interviews/driver.py --dry-run --model x --seeds evals/interviews/seeds.jsonl --run t --round 1` exits 0.
