# Fable 5.1 status — updated 2026-09-16T14:59:58Z

Owner: Fable 5.1 (forum generation/import, production execution of the released generator, Apertus sampling and dialogue rollouts, judging, RLHF training and schedule). Acknowledged the board and the ownership split.

Current work: forum import ready (650 gated prompts, provenance-bound; see message 20260916T141830Z_fable_ack_and_contract.md); judge rubric v2.4 (data/rlhf/prompts/judge_rank4_v2_en.txt, preference-based, absolute verdicts + issue tags, owner-calibrated); sampler (data/rlhf/sample.py), judge runner (data/rlhf/judge_rank4.py), cluster sampling driver (cluster/rlhf_sample.sh), Prime Intellect pod route (Opus agent, ≈$1 per 3,000 samples); pilot results in docs/RLHF_PLAN_20260916.md §22–§26.
Touched paths (mine): data/rlhf/* except data/rlhf/prompt_generator; data/rlhf/pool, data/rlhf/pilot, data/rlhf/prompts; cluster/rlhf_sample.sh; docs/RLHF_PLAN_20260916.md.
Next checkpoint: consume the first generator release → assemble a few-hundred-prompt set (forum credits first, generated prompts fill the remaining cells) → sample 4–8 replies per prompt on a Prime Intellect pod → judge with Sol → voting page for the owner. ETA: the day the release lands; sampling ≈1 h, judging ≈1 h for 300 prompts.
Blockers: none; dialogue slots deferred per the owner. Sol weekly meter ≈85 % until Sunday 20 Sept 22:16; a 300-prompt judging pass (≈300–600 calls) is affordable, a 10,000-prompt run is not before the reset.
Release being consumed: prompt-generator-0.1 (RELEASE.json created 2026-09-16T14:43:25Z; hashes verified PASS; 34 tests pass locally). Production run `round1_121` planned from round1_121.json (121 single-turn slots = the cells the forum leaves open; dialogue 0; max_calls 80, effort high, concurrency 3) and launched at 14:48Z; forum credits (74) already built outside the registry (data/rlhf/pool/round1_forum.jsonl) — will be imported through /forum-import in the next run so the registry sees them.

Round-1 set (updated 2026-09-16T14:59:58Z): run round1_121 finished single_turn_ready (121 accepted / 58 calls); joined to data/rlhf/pool/round1_generated.jsonl; round-1 = forum 74 + generated 121 = 195 prompts, 1,140 samples planned (data/rlhf/pool/round1_all.jsonl, receipt round1_all_receipt.json). Sampling in progress on a Prime Intellect pod; judging (rubric v2.4) and the owner's voting page follow. Dialogue plan received; deferred per the owner until the single-turn round is out.

Sampling done (2026-09-16T15:24:38Z): 1,140 samples for the 195 round-1 prompts (forum 296 rows, generated 844 rows; A100_40GB pod 29 min ≈ $1.1; all rows served by R4, sha 54d445bc… verified on the pod). Sol judging with rubric v2.4 (8aa32f266afd08b4) running: forum 75 calls, generated 211 batches of four + rejudge share. Dialogue pilot implementation in progress by Sol (codex exec, high) under data/rlhf/dialogue_quality_depth/ from BRIEF_20260916.md.

Round 1 judged (2026-09-16T15:32:40Z): 0 errors; 79/195 prompts yield a reinforce+discourage pair; votes page https://claude.ai/artifact/XhfvTBtAsE2bdW2gwSUX6e. Dialogue pilot Phase 0 code by Sol under data/rlhf/dialogue_quality_depth/ (22 tests OK), checkpoint CK1 review loop running (sol_loop.py, implementer session 01a0aabf…, independent reviewer).

Dialogue CK1 PASS (2026-09-16T16:09:28Z): reviewer accepted at cycle 4 (10→3→1→0 findings; 34 offline tests). Runtime re-initialised with the passed code; smoke stage (6 chats, 3 turns) starting on a pod.

Dialogue pilot (2026-09-16T17:19:13Z): smoke complete (6 chats, 15 turns, all annotated and root-adjudicated, report frozen). CK2 PASS: forecast rate basis fixed, Sol reservations reallocated within 120; admitted measurement size 28 (GPU est. EUR 2.98; spent EUR 0.87 of 5). CK3 in progress: Sol takes over the pod runner (pod/run_stage.sh); measurement collection follows.

CK3 PASS (2026-09-16T17:43:55Z): pod runner owned by Sol (pod/run_stage.sh, preflight, sha check, config-derived context, fail-fast serve, EXIT trap + watchdog; reviewer accepted at cycle 2). Measurement stage (28 chats, 8 turns) launched on a pod. Round 2 single-turn set in preparation: 240 forum (tilted to question/advice/opinion) + 168 generated with person-and-story seeds (data/rlhf/gen02_demo).

Round 2 sampled (2026-09-16T18:09:29Z): 407 prompts (data/rlhf/pool/round2_all.jsonl; forum 240 tilted to question/advice/opinion + 167 person-and-story generated), 1,908 replies (round2_all_samples.jsonl, pod 18 min ≈ $0.6, first attempt). Sol judging with rubric v2.4 running (≈525 batch calls). Dialogue measurement stage attempt 3 in progress on its own pod (Sol's runner; two earlier attempts failed pre-rollout: runpod 503, token read; both fixed under review).

Round 2 judged (2026-09-16T18:20:24Z): 517 batch calls, 0 errors; pairable prompts (reinforce vs any lower) 212/407 = 52% (forum 109/240, everyday 34/60, IF 27/50, safety 15/20, maths-el 13/18, factual 13/17); generated person-and-story prompts 103/167 pairable (bare 34/47, terse 27/41). Weakest: forum share/calculation (5% reinforce), everyday planning (6%), strict-format IF (7%). Dialogue plan handed to astra (gpt-6-astra, codex 0.154, session 01a0ab6f…) for end-to-end execution per the owner.

Dialogue measurement collected (2026-09-16T18:28:09Z, attempt 3, Sol's runner): 28 trajectories, 111 assistant turns; endings completed 21 / context_limit 4 / horizon 2 / truncated_output 1; pod torn down and confirmed. Astra (root by delegation) now annotating, adjudicating, reporting, selecting, sampling candidates, ranking and exporting pairs; it posts its own milestones on this board.

Dialogue pilot COMPLETE (2026-09-16T19:08:00Z): 28 chats / 111 turns annotated + root-adjudicated (1 change of 94), report frozen, 24 prefixes selected (C6/P9/R9), 72 candidates sampled, 24 rankings, 10 pairs exported (14 rejected: 8 ties, 6 no acceptable chosen). GPU EUR 1.58 total, 54 Sol calls of 120. Deliverables under data/rlhf/dialogue_quality_depth/runtime/measurement/; recommendation posted as a board message.

Escalating resampling (2026-09-16T22:33:07Z, plan §30, CK5 PASS): 15 late-failure prefixes × 32 fresh replies; reinforce found in 14/15 (needed 4:5, 8:3, 12:3, 16:3); 13 pairs added → 24 dialogue pairs (P10 R11 C3). GPU EUR 1.95 total, Sol 94 calls. Tie rule fixed (CK4). Owner rule recorded: only failures after turn 1 count as dialogue failures.

VERSIONS (2026-09-17T09:42:47Z): prompt-generator-0.1 is DEFUNCT per the owner. Current single-turn generator: 0.2-proto (data/rlhf/gen02_demo/seed_demo.py, sha16 bf900db1cf813a37). Every current version, data set and page: docs/RLHF_COORDINATION/CURRENT_VERSIONS.md (single source of truth). Earlier lines in this file that call 0.1 the consumed release are historical.

VERSION DEFINITIONS (2026-09-17T10:08:54Z, owner): generator 0.2 = target distribution over task types, filled by forum prompts + person-and-story seeds (round 2 = prototype run); generator 0.3 = 0.2 + multi-turn dialogue data (under development); 0.1 defunct. See CURRENT_VERSIONS.md.

DIALOGUE V2 (2026-09-17T10:42:32Z): Opus executor dispatched on Workstream B with DIALOGUE_V2_EXECUTION_BRIEF_OPUS_20260917.md; stops at the owner review. Prompt generation (PG1–PG6) remains with the orchestrator.
