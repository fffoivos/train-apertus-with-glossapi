# RLHF current versions — single source of truth

Updated 2026-09-17 by Fable (version definitions from the owner). Owner rule (17 Sept): be explicit about the latest version of everything, otherwise we iterate for nothing.
- Read this file before starting any RLHF work.
- Every run, document, page and board message names the versions it used, using the names in this file.
- When a component changes, this file changes in the same step. Superseded and defunct items stay listed with what replaced them.
sha16 = first 16 hex characters of the file's sha256 at the time of this update.

## 0. Generator versions (owner's definitions, 17 Sept)

| Version | Definition | State |
|---|---|---|
| 0.1 | Codex's template-fixture generator | **defunct** |
| **0.2** | A method: declare a target distribution over task types; fill part of it with forum prompts (forum gate v3 plus selection), and generate the rest from person-and-story seeds | **current method, prototype run done (round 2)** |
| **0.3** | 0.2 plus multi-turn dialogue data | under development (dialogue pipeline, adaptive user model) |

What 0.2 has today, and what it lacks:
- Has: forum gate v3 and selection; the person-and-story seed script (`data/rlhf/gen02_demo/seed_demo.py`); one prototype run (round 2: 240 forum + 167 seeded prompts).
- Lacks: a declared target distribution (round 2 used hand-set quotas: a forum tilt and separate seed task weights); one shared task-type taxonomy so that forum prompts count against the targets (forum task types and seed task types are different lists today; the seed label spec proposes a mapping); label definitions in the prompts; a reviewer pass; maths reference solutions; a uniqueness registry; the astrovox cap in code.

## 1. Current components

| Component | Current version | Path | sha16 | Status | Notes |
|---|---|---|---|---|---|
| Model under test | R4_full epoch 1 (run identity **G4F6P1**, the name used in the execution plans) | `fffoivos/greek-apertus-8b-sft-r4-full` | sha256 54d445bc…6763 | current | served with vLLM at 4,096 context (checkpoint maximum) |
| Generator 0.2, seed part | person-and-story seed script (prototype) | `data/rlhf/gen02_demo/seed_demo.py` | bf900db1cf813a37 | current prototype, unreviewed | produced round 2's 167 seeded prompts; labels undefined (see seed label spec) |
| Target distribution | target-distribution-v1 (agreed shares; size open) | `data/rlhf/target_distribution_v1.json` | 4c02f11e351e25a0 | current | purposes 35/25/15/10/10/5; languages 70/20/2×5; counted in accepted pairs |
| Registry of existing prompts | registry v2 (17 Sept; R-PG2 fixes) | `data/rlhf/registry/registry.py` → `registry.sqlite`, `registry_report.json`; relabel `relabel_v1.jsonl` | 73817d4ab62ea403, report 35281e61f1cfe8d5, relabel ebccfd4ae37185c1 | current | 613 logical prompts, 17 duplicate groups, E=209 eligible pairs; exact joint targets; maths yield from the specialist calibration. Superseded: `data/rlhf/inventory.py` (first register). |
| Ingestion and next-500 plan | audited requirements, 17 Sept | docs/RLHF_COORDINATION/PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md | fd272873555dd925 | plan only; implementation pending | seed import, cross-run aliases, substantive uniqueness, joint quotas; approximately 500 additional requests, not 500 total pairs |
| Generator 0.2, release (single-turn) | manifest round3-manifest-v2 + generate.py (detail-sized instances, scenario screen, reservations, review, two repairs, regeneration, per-run code snapshot) + independent label verification `verify.py` | `data/rlhf/generator_v02/` | manifest e95dd2b512bcf9b1, generate a6d125f67f1f3124, verify 85645aecfdb0d274 | current | runs R3-validation-50, R3-main, R3-fix, R3-held, R3-fix2; 411 accepted prompts of 453 slots Since 17 Sept the same generator serves both streams by manifest (`--manifest`, default `manifest_round3.json`; the receipt records the manifest used); current sha16 `43d3fc6e9efe4fae` (adds en-dash ranges to the one-word rule in the detail ceiling; previously `ecef7ea616ce5db8`), which also fixes the glossary lookup that dropped the detail paragraph from runs R3-held, R3-fix and R3-fix2 (see `data/rlhf/round3/receipt_notes.md`). |
| Generator 0.2, forum part: gate | v3 | `data/rlhf/prompts/forum_gate_rewrite_el.txt` | ef13fe3ade026929 | current | task_type values undefined |
| Generator 0.2, forum part: selection | round-2 tilt + astrovox cap | `data/rlhf/forum_select.py` | 85c0be0b29673f1f | current code; astrovox ≤3 % (plan §31) agreed, **not yet in code** | |
| Judge rubric | v2.4 | `data/rlhf/prompts/judge_rank4_v2_en.txt` | 8aa32f266afd08b4 | current for non-maths | |
| Maths judging | **judge_rank4_maths_en.txt** (owner, 17 Sept): the same reviewer prompt as v2.4 with the priorities re-ordered — correct results first, every statement valid, then the task asked for; run through the ordinary `judge_batches.py` in fours at medium | `data/rlhf/prompts/judge_rank4_maths_en.txt` | 41e99a8f2dfa9e79 | current | routing: purpose maths only (115 round-3 prompts, incl. the 39 forum maths); the other 335, of which 128 carry embedded maths, stay on v2.4 by owner decision, with the known limitation that v2.4 does not re-do the arithmetic. Calibration on the 20 round-2 maths prompts: 11 pairable, against 9 under the withdrawn pipeline and 14 under plain v2.4; agreement 18 of 20; both required cases hold. **Withdrawn:** the separate maths pipeline (`maths_judge.py`, rubrics v1/v1.2/v2, references, deterministic eligibility, reconcile) — kept on disk as the record, called by nothing |
| Judge runners | — | `data/rlhf/judge_rank4.py`, `data/rlhf/judge_batches.py` | e7e61e790485816d, a4336de3128fbb39 | current | batches of four for 8- and 16-reply prompts |
| Sampler | — | `data/rlhf/sample.py` | 6825c947a0d40d80 | current | T 0.8, top-p 0.95, max 1,500 tokens, per-row n, no system prompt |
| Votes page generator | — | `data/rlhf/vote_page.py` | b03cb0d3c47f9a0b | current | |
| Labels and terms | spec v1.0.3 + glossary v1.0.3 (17 Sept; R-PG1 cycle-1 and cycle-2 fixes, plus the detail clarification found while verifying labels) | `docs/SEED_LABEL_SPEC_20260917.md`, `data/rlhf/prompts/seed_label_definitions_v1.md` | c8cbb4ca1aa84188, ecdc0ec9ef56b184 | frozen | detail measures only the person's own words; pasted material never raises the level. Term manifest `reviews/R-PG1_term_manifest_v1.0.2.md` |
| Generator 0.3, dialogue part: pipeline code | dialogue-quality-depth-v1, checkpoints CK1–CK5 passed | `data/rlhf/dialogue_quality_depth/` (`dqd.py`, `rank.py`, `pod/run_stage.sh`) | cef83a2932e1d926, 94c5b16779365f28, 7b9fdb950b4d2e7f | current code | 62 offline tests; pod runner is Sol-owned |
| Generator 0.3, dialogue part: user simulator | user_policy v1 | `data/rlhf/dialogue_quality_depth/user_policy.txt` | c58372b0c8a2bc79 | **superseded in principle** | owner agreed the adaptive user model (OPUS_FEEDBACK_20260917.md); not implemented |
| Generator 0.3, dialogue part: turn annotator | turn_quality v1 | `data/rlhf/dialogue_quality_depth/turn_quality.txt` | 523b8fb4bcab21cc | current | verifier value matching is English-only (known defect) |
| Generator 0.3, dialogue v2 (development, Opus Workstream B): pipeline code | dialogue-v2-dev-0.1 (generator 0.3-dev); Stage C readiness PASS (21 offline tests; independent reviewer HOLD at cycle 1, PASS at cycle 2) | `data/rlhf/dialogue_v2/` (`dv2.py`, `rollout.py`, `views.py`, `contracts.py`, `pod/run_stage.sh`) | f88664b00e113d92, 8318158e405d4a14, 106d480b6c0446c2, 864d8b4c1ae37196, 0478a1e45d7bf2cc | development, pending owner review | development_demo rows only; not a production generator until R-PG6 |
| Generator 0.3, dialogue v2: adaptive user and move-selection rule | adaptive-user-v2.0 (+ user-actions v1 for troubleshooting); selection rule = `user_state.allowed_moves` (no restate after a restatement, helping ability, patience tolerance low 1 / medium 2 / high 4 failed replies) | `data/rlhf/dialogue_v2/prompts/user_policy_v2.txt`, `prompts/user_actions_v1.txt`, `user_state.py` | e5d45cbb9ee28055, a7eda68fa88c4aff | development, pending owner review | replaces user_policy v1 for dialogue v2 runs only |
| Generator 0.3, dialogue v2: world resolver and worlds | world-resolver-v1; deterministic observation tables (Sol maps actions to check ids only) | `prompts/world_resolver_v1.txt`, `worlds.py`, RGD003/RGD004 worlds in `rgd_seeds.json` | fdb7f942ba75029a, a0a959a9c514ee47 | development | |
| Generator 0.3, dialogue v2: evaluator view | dv2-turn-eval-v1, dv2-conversation-review-v1, dv2-branch-verify-v1; branch ranking = rubric v2.4 verbatim | `prompts/turn_eval_v1.txt`, `prompts/conversation_review_v1.txt`, `prompts/branch_verify_v1.txt` | 4196f90a9fb71ced, 5dd757513a7e94f3, 189363b3ab35e027 | development | maths content held for the specialist maths judge |
| Dialogue collection amendment | owner scope, 17 Sept: minimum 30/15/15 | docs/RLHF_COORDINATION/DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md | 19e35fcb56de4e7f | current requirements; implementation pending | first-error and post-instruction-change sampling; helpfulness not an eligibility filter; four initial candidates per point proposed, bounded top-ups; combined reviews and deterministic checks |
| Dialogue v2 seeds | D1 DVI001–DVI004 (fresh person-and-story openings by Sol; DVI001 word range repaired); D2 RGD001–RGD006 (openings verbatim from the demo spec) | `data/rlhf/dialogue_v2/seeds/dvi_seeds.json`, `data/rlhf/reference_guided_dialogue_demo/seeds/rgd_seeds.json` | db47f922f5f08e6d, d72d9e75de4d9b28 | development | source families dvi:* and rgd:* reserved from formal evaluation |
| Dialogue v2 sampling config | dv2-sampling-v1: T 0.8, top-p 0.95, **max 1,024 tokens** (changed from 1,500), n 1, no system prompt; model revision 3a557e08 pinned | `data/rlhf/dialogue_v2/contracts.py` | 864d8b4c1ae37196 | development | applies to every D1/D2 reply and branch candidate |
| Pair rule | top reinforce vs lowest-ranked, clear margin, tie matters only at the top | `export_pairs.py` (CK4) | — | current | plan §24 update |
| Resampling protocol | escalating 4→32, production default 16 up front | `resample.py` (CK5), plan §30 | — | current | |
| Dialogue data rule | serious error at turn 1 = single-turn error; dialogue material = failures after turn 1 | plan §29 addenda, final recommendation | — | current | OPUS_FEEDBACK adds: keep deeper recovery examples from chats that failed at turn 1 (proposal) |
| RLHF plan (background) | §1–§32 | `docs/RLHF_PLAN_20260916.md` | 41fe914a77bedd18 | current background | its ~20,000-pair recipe is not an approval of the first run size |
| Execution plan (current) | two-stream plan, 17 Sept: terms folded in (§2, §3, §4a); every item tagged [PG] prompt generation / [RLHF] / [shared] (§0); prompt generation first, work order PG1–PG6 (§0.1; PG2 agreed distribution, PG3 inventory and fill); review checkpoints R-PG1–R-PG6 and R-RL1–R-RL5 with Sol xhigh (§10, `data/rlhf/sol_review.py`); prompt ingestion and next-500 plan: PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md | `docs/RLHF_COORDINATION/RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md` | 4201a6ba6074ef3c | current | sub-plans (tagged): MATH_JUDGING_EXECUTION_PLAN_20260917.md (b5e65de8026e2ebc), DIALOGUE_V2_EXECUTION_PLAN_20260917.md (d7b0293b803dd863), REFERENCE_GUIDED_DIALOGUE_DEMO_20260917.md (42a429a3aef70824); evidence OPUS_FEEDBACK_20260917.md |
| CSCS budget | CHF 240 cap; CHF 222.92 used (82.869 node-hours at CHF 2.69) on 17 Sept; CHF 17.08 left | `execution_state.json`, `cluster/ledger.sh` | — | current | the RLHF plan's DPO training (≈ CHF 7–8) plus evaluation chain (≈ CHF 12) exceed what is left; cap decision needed before R-RL4 |
| CSCS access | certificate valid until 18 Sept 13:49 local | `~/.ssh/cscs-key-cert.pub` | — | current | renewed by the owner 17 Sept |
| Sol | gpt-5.6-sol via codex-cli 0.154.0 | `data/math/codex_server.py` | — | current | do not pass `features.code_mode_host=false` on 0.154 |
| Astra | gpt-6-astra | — | — | only to unblock | owner: too expensive for annotation or routine runs |
| DPO trainer | not built | — | — | missing | blocks any training use of the pairs |

## 2. Data sets

| Set | sha16 | Built with | Status |
|---|---|---|---|
| Round 2 single-turn, generator 0.2 prototype run: `data/rlhf/pool/round2_all.jsonl` (407 = forum 240 + seeded 167) | 661443a62e8b375a | samples `round2_all_samples.jsonl` c3b290153c43fcc1; judged `round2_all_judged.jsonl` 440b5958e1caf169 with rubric v2.4 | **current round**; 212 pairable prompts |
| Round 1 single-turn: `data/rlhf/pool/round1_all.jsonl` (195 = forum gate v3 74 + generator 0.1 121) | afb42b543c621768 | judged `round1_all_judged.jsonl` 6d2c3f72f8beb03c with rubric v2.4 | historical; **generated half built on defunct 0.1** (19 JSON-leak rows already excluded) |
| Forum gated pool: `data/rlhf/pool/forum_gated_v3.jsonl` | — | gate v3 | current; 1,928 gated, 1,564 accepted, 314 used |
| Dialogue pilot pairs: `data/rlhf/dialogue_quality_depth/runtime/measurement/preferences.jsonl` (24 pairs) | dea6cb6598f2d302 | dialogue-quality-depth-v1, rubric v2.4 | pilot evidence; **seeds and openings from defunct 0.1 fixtures; user simulator superseded in principle** |

## 3. Defunct and superseded

| Item | Status | Replaced by | Reason |
|---|---|---|---|
| prompt-generator-0.1 (Codex release 16 Sept 14:43 UTC, `data/rlhf/prompt_generator/`, RELEASE.json 5fb26180e076cd1e) | **DEFUNCT (owner, 17 Sept)** | generator 0.2 (method; prototype run = round 2) | template seeds with near-identical rows, framing text in user messages, raw JSON leak in 19 non-Greek rows, undefined labels. Kept on disk as evidence only. Its fixtures still feed the dialogue pilot manifest, which must change before the next dialogue run. |
| Codex's 50-prompt pilot (`~/Documents/Codex/2026-09-13/rea/outputs/rlhf50_20260916/`, stance and depth axes) | superseded | 0.1, itself defunct | design notes remain useful input to the label spec |
| Rubric v1 (`judge_rank4_en.txt`), v2.1, v2.2 snapshots | superseded | v2.4 | v2.3 has no separate snapshot |
| Forum gate v1, v2 snapshots | superseded | gate v3 | |
| Examiner-style interaction plans and user_policy v1 behaviour | superseded in principle | adaptive user model (to be implemented) | |
| Hand-written pod scripts in `cluster/` (`dqd_pod_setup.sh`, `dqd_pod_stage.sh`, `dqd_provision.py`) | superseded | `data/rlhf/dialogue_quality_depth/pod/run_stage.sh` | Sol-owned and reviewed |

## 4. Pages and the versions they show

| Page | Shows | Status |
|---|---|---|
| Greek RLHF Round 2 Votes — https://claude.ai/artifact/SjzYe8cyaBQ8RMwY5xcWJ5 | round 2 = generator 0.2 prototype run (forum gate v3 + seed script), rubric v2.4 | current |
| Greek RLHF Round 1 Votes — https://claude.ai/artifact/XhfvTBtAsE2bdW2gwSUX6e | round 1, generator 0.1 (defunct) + forum gate v3, rubric v2.4 | historical |
| Prompt Generator 0.2 Demo — https://claude.ai/artifact/AKzzoX6TYCKKobhHiCVgYC | generator 0.2 seed part, demo v3 | current prototype |
| Dialogue Prompt Pipeline — https://claude.ai/artifact/GEvCuj73VvdQKwJXKvi1cC | dialogue v1 prompts (0.1 seeds, user_policy v1) | historical record of the pilot |
| Where the Chats Break — https://claude.ai/artifact/Hf3EsYbj1Av91jdCVy12zk | dialogue pilot measurement | historical |
| Greek RLHF Round One (plan page) — https://claude.ai/artifact/GedQWgZyMBz84zPXgsa28R | rubric v1 | **stale** |
| Forum Prompt Pipeline — https://claude.ai/artifact/ViuavqdWWRYhRxnSZDJ6QY | gate prompt as sent in v2 | **stale** (current gate is v3) |
| Forum prompts — https://claude.ai/artifact/UsPiRAYkamAjmqm9eUoRLU | gate v3 pool | current |
| Greek RLHF Pilot Ratings — https://claude.ai/artifact/FJoXHzhEbf9zsNCwoh1bdB | pilot, rubric v2.3 | historical |
| RLHF pilot votes — https://claude.ai/artifact/9DN7qUc7gU11Q55qqm6Vku | pilot | historical |

## 5. Open decisions caused by 0.1 being defunct
1. Round 1's 121 generated prompts and their pairs: drop from any training pool, or keep the ones that passed review.
2. Dialogue pilot's 24 pairs (openings from 0.1 fixtures): pilot evidence only, or usable.
3. Next dialogue run (generator 0.3): openings from generator 0.2 seeds and the adaptive user model.
4. `CODEX_STATUS.json` still advertises 0.1 as release-ready; Codex owns that file and has been notified on the board.

## Round 3 (17 September 2026)

| Item | Value |
|---|---|
| Prompt set | `data/rlhf/round3/round3_all.jsonl`: 411 generated + 39 forum maths selections = 450 prompts |
| Sampling | **done**: workbench 3420778 (node nid007125, debug), 17:42–17:52, elapsed 10 min 35 s, ledger 83.045 nh / CHF 223.39 (about CHF 0.47 for the window); 450 prompts × 32 replies = 14,400, no errors; 32 replies per prompt, T 0.8, top-p 0.95, max 1,500 tokens, no system prompt, checkpoint G4F6P1 (sha verified on the cluster, `reviews/R-RL1_evidence.txt`) |
| Judging | replies 1–8 for all; 9–16 and 17–32 only where no usable positive appeared; generated prompts escalate, forum maths only for a fixed sample of 8 (measured: 0 positives in 41 pre-existing forum maths items) |
| Routing | 247 prompts carry maths content (maths or embedded) and go to the specialist judge; embedded maths also goes to the general rubric |
| Pairs and page | `data/rlhf/round3/pairs.py`, `page.py` |

## What changes between 0.2 and 0.3 (owner, 17 September 2026)

The structure of 0.2 is preserved. Only two things change: **(A)** the term definitions, now written down and pasted into every generation and judging call, and **(B)** a maths reviewer prompt, built as a variant of the existing reviewer prompt that prioritises correct results and valid reasoning over presentation. Medium effort and batching are part of the method, for economy, and are not to be changed.

Everything else built on 17 September beyond that line was withdrawn or is bookkeeping around the same spine: the reference-solving stage (withdrawn), the separate maths schema and eligibility layer (withdrawn), high effort (reverted to medium).

## Effort policy (owner, 17 September 2026)

Every pipeline call to Sol runs at **medium** effort: prompt generation (instances, renderings, in-run review), maths judging, general judging, label verification. This matches `RLHF_PLAN_20260916.md` §, which sized judging at medium. High effort was never specified in any plan; it was a default of mine and cost about 1,750 high calls on 17 September against 82 medium. The reviewer checkpoints (`data/rlhf/sol_review.py`) remain at xhigh because the owner asked for that explicitly on 17 September; say the word and they drop to medium too.

## Call budget rule (17 September 2026, after the round-3 overspend)

Round 2 spent about 530 Sol calls for 407 prompts, nearly all at medium. Round 3 had spent about 1,870 before its replies were judged, three quarters at high, of which roughly 1,100 bought nothing: 921 on a reference-solving stage that no plan contains and that changed 13 of 307 references, and about 170 on rejudging the same maths three times while the eligibility rule kept moving.

Rules from now on, for both sessions:
1. **No new pipeline stage without the owner's word.** A stage that costs a call per prompt is a spending decision, not an implementation detail. If a plan does not name it, ask before building it.
2. **Effort comes from the plan, not from a default.** The plans say medium for judging and generation; xhigh only for the reviewer checkpoints the owner asked for. Any other level needs a reason written down first.
3. **Settle a rule before applying it in bulk.** Calibrate on the small set, fix the rule, then run. Rejudging the same set a third time means the rule was not ready.
4. **Every run receipt records its call count by stage and effort**, so the cost of a round is visible while it runs rather than after it.

## Session split (17 September 2026)

Round-3 execution (`data/rlhf/round3/`, `maths_judge/`, `generator_v02/`, `cluster/`, sampling, judging, pairs, the votes page) is driven by the forked session. This session owns `docs/RLHF_COORDINATION/**` including this file and `reviews/**`. Decisions that cross the split are relayed between sessions rather than acted on twice.

## Target change, 18 September: maths is out of the RLHF target entirely

Owner decision, 18 September: **generate no maths prompts for RLHF — not from seeds, not from forums.**
Maths quality is to be attacked in SFT first.

Evidence behind it:
- DPO01 full-suite wave 1 (parent + three epoch-3 arms, Greek MGSM n=250): every arm is BELOW the parent
  on maths, by 6.4 to 12.0 points, even though maths prompts were already excluded from DPO01 training.
  Preference training on everyday/factual/instruction/safety pairs is degrading arithmetic it never touched.
  arm00_ep3 -12.0pp and arm02_ep3 -11.6pp are flagged by the section 5 rule-2 threshold (>=10pp on MGSM).
- Forum maths was already measured barren: 0 positives in 41 pre-existing forum maths items, which is why
  round 3 capped forum-maths escalation at a fixed sample of 8 rather than escalating it.

Consequences for the next round's target: the 115 round-3 maths prompts (including the 39 forum maths) have
no successor; that share redistributes across everyday / factual / instruction / safety. The maths judging
prompt (judge_rank4_maths_en.txt, sha16 41e99a8f2dfa9e79) stays on disk as the record but is called by nothing.
