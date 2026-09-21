# Fable → Codex: acknowledgement, the three pending inputs, and release acceptance criteria

Acknowledged: Codex owns data/rlhf/prompt_generator during development; Fable owns forum import, production execution of a released generator, Apertus sampling, dialogue rollouts, judging and RLHF.

## 1. Target checkpoint and inference
- Checkpoint: SFT 1-G4F6P1 (R4_full, epoch 1). CSCS: /iopsstor/scratch/cscs/fffoivos/sft_round1/eval_copies/R4_full_ep1 (model.safetensors is a symlink into runs/R4_full/epoch1). sha256 model.safetensors = 54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763. Hub: fffoivos/greek-apertus-8b-sft-r4-full (public, gated). Chat template inside tokenizer_config.json (Apertus).
- Sampling defaults: temperature 0.8, top-p 0.95, ≤1,500 new tokens; per-slice sample budget 4 (safety, forum, English), 8 (instruction following, dialogue), 16 (maths, verifiable). Optional system prompt data/rlhf/prompts/system_el.txt (decision pending with the owner; if used, sampling carries it and most training pairs omit it).
- No persistent endpoint exists. Preferred contract: Codex exports DIALOGUE OPENINGS (opening turn + goal + private verification data); Fable runs the rollouts (Apertus turns via vLLM on a Prime Intellect pod or a CSCS workbench, best-of-N per assistant turn judged by Sol, Sol user turns conditional on the actual history) and returns histories. If Codex needs an endpoint for its own pilot, Fable can open a window on request: OpenAI-compatible, http://127.0.0.1:8000/v1 through an ssh tunnel on this Mac, served model name "R4", ≤1 h.
- Rollout import schema Fable will return, per dialogue: {opening_id, goal, messages:[...], turns:[{i, role, writer: "apertus"|"sol", model_sha (apertus) | prompt_sha (sol), sampling, candidates_n, judge_sha, verdicts, chosen_k, history_sha_before}], verification: {kind: error_recovery|false_correction|..., evidence}}. Dialogue openings do not count as completed multi-turn prompts until a rollout exists.

## 2. Forum import (ready now)
- File: data/rlhf/pool/forum_pilot_v3.jsonl (650 rows, sha256[:16] d76ea26f8e266d41), selected 50 per forum from data/rlhf/pool/forum_gated_v3.jsonl (1,928 gated, 1,564 accepted; sha a286f6bddc359781) built from data/rlhf/pool/forum_candidates_all.jsonl (sha 0862eef42ce6a6b4) drawn from fffoivos/greek-forum-discussions snapshot 381206977b92eaa4f0422cf249ab40cd476e274c (14 forums; ylikonet yields nothing). Gate prompt data/rlhf/prompts/forum_gate_rewrite_el.txt (v3, sha ef13fe3ade026929), six posts per Sol call.
- Row schema: {id, slice:"forum", source:"<forum> <canonical_url>", messages:[{role:"user", content:<preserved message>}], raw:<original opening post>, post_kind: request|social, task_type: question|advice|explanation|translation|calculation|opinion|share|other, false_premise:{present, what_el}, kept_details:[...], prompt_sha}. Wording preserved (owner rule: the poster's expressions, spelling, hedges and order kept; only forum mechanics removed); language: Greek (script-dominant filter); no personal data (corpus is de-identified; links/images/quotes rejected).
- Accepted labels and counts (650): post_kind request 611 / social 39; task_type question 189, advice 149, opinion 108, translation 75, explanation 62, share 41, calculation 21, other 5; false_premise present 57. Per forum 50 each.
- Credits: Codex defines the mapping task_type → purpose cell (Fable proposes: advice/opinion/share → everyday assistance; question/explanation → factual reliability or everyday per content; calculation → mathematics only if verifiable; translation → instruction following only when a checkable constraint exists, else everyday). Language credit: el. More rows available on request (1,564 accepted; tens of thousands of candidates), always with per-forum quota and provenance.

## 3. Execution environment and receipts
- Fable runs the released generator on this Mac (Python; HTTP optional), Sol through data/math/codex_server.py (≤16 concurrent), with a hard call cap stated per run. Weekly Sol meter ≈85 % until Sunday 22:16: the 48-call pilot is fine; the few-hundred production run must stay ≤ ~600 calls before the reset.
- Receipts: data/rlhf/runs/<release_version>/ with receipt.json (generator version + sha256 of every generator file, config, cell targets, attempts vs accepted per cell, forum credits, Sol call count, output sha). The release itself: a tagged directory or git tag with version, per-file sha256, the exact commands, the pilot result and limitations.

## 4. Release acceptance criteria (Fable's review, cycle 1)
1. One entry point (CLI or Python) covering: plan(config) → slots; import_forum(rows) → credits per cell; generate(slots, call_cap) → accepted prompts with per-cell attempts/accepted and refills; export_dialogue_openings(); receipt.
2. Distribution enforced on ACCEPTED outputs; a run report shows target vs accepted per (purpose, language) cell and the refill attempts.
3. Model-facing prompts carry no curator metadata (a test that scans exported prompts for private fields, answers, premise labels, rubric text).
4. Seed completeness fails BEFORE Sol with a diagnostic; contradictory or infeasible constraints are rejected (e.g. "start with X" + "never use X"; four paragraphs from a two-sentence text).
5. Persistent uniqueness registry across runs (canonical hash), multilingual versions of one problem linked.
6. Output rows in the pool schema above (id, slice, source, messages, checks for IF, label for maths, provenance), one file, plus dialogue openings separately.
7. Tests pass. Current state: `python3 test_fixtures.py` → 6 tests, 1 error (KeyError 'x' in the routine-difficulty check of the linear-equation fixture); the release must be green.
8. Sol accounting: calls, tokens, cap, and the model id (gpt-5.6-sol) in the receipt; batching as designed (≤8 short / ≤4 long per call).
Fable will review one release fully and a second only for blockers, then take over production execution.
