# Astra: execute the whole dialogue plan, end to end, from the current state

Owner's instruction (2026-09-16 evening): "have astra execute the whole plan". You own execution of
../../../docs/RLHF_COORDINATION/DIALOGUE_EXPERIMENT_PLAN_20260916.md (read it fully, with DIALOGUE_PILOT_CONFIG_20260916.json and
DIALOGUE_SAMPLING_QUALITY_DEPTH_20260916.md) through Phase 6 and the deliverables list, using the code in THIS directory (dqd.py CLI,
RUNBOOK.md, pod/run_stage.sh). You act as root reviewer by the owner's delegation (adjudication included). Nobody will answer questions:
decide, record the decision, continue. Work in this directory; write only here (runtime/, messages/, pod/ fixes) and one message file
under ../../../docs/RLHF_COORDINATION/messages/<utc>_astra_<topic>.md per milestone.

## Current state (verify it yourself with `python3 dqd.py --state runtime status` and the files)
- Phase 0 code passed three reviewed checkpoints (messages/review_CK1_4.md, review_CK2_1.md, review_CK3_5.md); 34+ offline tests
  (`python3 -m unittest discover -p 'test_*.py'`).
- Smoke done: 6 chats, 15 turns annotated, adjudicated (runtime/smoke/SMOKE_DECISIONS.jsonl), report frozen, forecast frozen:
  admitted size 28, Sol reallocation recorded (runtime/forecast.json). Spend so far about EUR 0.90 of the EUR 5 cap (see the ledger).
- Measurement openings written (28). A measurement pod run MAY BE IN PROGRESS: `bash pod/run_stage.sh measurement` was started at
  18:04Z; its log is the newest runtime/pod/measurement_*.log and the driver log is ../../../logs/dqd_pod_measurement_driver.log
  (each run ends with a DQP_STAGE_RECEIPT line). Two earlier attempts failed before any rollout (runpod 503 → fixed with offer
  fallback; Hub token read without trailing newline → fixed). Do NOT start a second pod while runtime/pod/prime_state.json exists or
  that process is alive (check `pgrep -f "pod/run_stage.sh"`); wait for its receipt. If it failed, read the log, fix the cause in pod/
  or the code, keep tests green, and rerun `bash pod/run_stage.sh measurement`.

## What to do (plan phases, in order; gates are in RUNBOOK.md)
1. Measurement collection complete for all 28 admitted trajectories with honest terminal codes (plan §6 gate).
2. `python3 dqd.py --state runtime annotate measurement`, then `calibration measurement --n 24`, then adjudicate as root: review the
   stratified sample AND every boundary turn; verify maths/factual claims yourself; write a decisions JSONL (annotation_id, decision in
   good/minor/serious/unjudgeable, evidence, reviewer="astra (root by delegation)", optional recovery_opportunity/recovery_success)
   and run `adjudicate measurement --decisions FILE`; if more than 20 % substantive changes, follow the plan (revise/reannotate the
   class). Rerun calibration until the boundary set is stable, then `report measurement` (frozen).
3. `select measurement` (P/R/C rules, receipts), then `bash pod/run_stage.sh candidates` (2 fresh replies per selected prefix), then
   `rank measurement`, `export measurement` (preferences.jsonl, rejected_pairs.jsonl, receipt).
4. Write runtime/measurement/final_recommendation.md per plan §10 (pair yield by P/R/C, depth, task, language; severity and verified
   fix rate; cost per usable pair; gaps: no-error cases, simulator bias, sparse languages, unmeasured items) and the cost ledger summary.
5. Post a milestone message on the board after 1, 2, 3 and 4, and a final one with all deliverable paths.

## Hard constraints
- Budgets: Prime Intellect EUR 5 total for this dialogue programme (EUR 4.00 operational stop; the ledger already holds ~EUR 0.90);
  Sol 120 calls total for the pilot as recorded in runtime/forecast.json; the code enforces both; never raise them. Your own reasoning is
  not counted against the 120.
- Secrets: ~/.config/prime/key, ~/.cache/huggingface/token, ~/.ssh/prime_intellect_key are read by the scripts and passed as env/stdin
  to the one command that needs them. Never print, echo, log, or copy them.
- Pods: only through pod/run_stage.sh (it provisions, serves, runs, and ALWAYS tears down with confirmation). Never leave a pod up.
  Kill processes only by PID. No CSCS/Clariden. Do not modify /Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts/prime_provision.py
  or anything under ../prompt_generator/. The Sol client ../../math/codex_server.py works on codex 0.154 (verified).
- Sampling settings, prompts (user_policy.txt, turn_quality.txt) and information barriers are frozen; if you must change one, version it,
  record why, and rerun only what depends on it.
- Report faithfully: failed gates are failed; no checklist box is ticked without its artefact.
When everything is done, end with a summary: deliverable paths, counts (trajectories, turns, annotations, adjudication changes, selected
prefixes by P/R/C, candidates, exported pairs, rejected pairs), spend (EUR, Sol calls), and what remains unmeasured.
