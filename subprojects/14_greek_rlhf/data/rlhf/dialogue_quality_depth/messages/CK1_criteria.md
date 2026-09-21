# Checkpoint CK1 — Phase 0 code complete and verifiable offline

Specification: DIALOGUE_EXPERIMENT_PLAN_20260916.md (§2–§4, §7, §9, §11), DIALOGUE_PILOT_CONFIG_20260916.json, the addendum
DIALOGUE_SAMPLING_QUALITY_DEPTH_20260916.md (all under ../../../docs/RLHF_COORDINATION/), and BRIEF_20260916.md in this directory.
The reviewer checks the SOURCE against these; the implementer's claims are not evidence.

Blocking criteria (any failure = HOLD):
1. Information barriers, verified in the prompt-building code paths: the opening writer never receives reference/checks/params; the user
   simulator prompt contains only the visible prefix + public goal/plan/attitude/register; the annotator packet never contains a later turn
   of the same trajectory and no call mixes two prefixes of one trajectory; the ranker never receives candidate provenance (original/new).
2. Raw rollout and candidate sampling are n=1, temperature 0.8, top_p 0.95, max_tokens 1500, no system message, and the stored text is
   byte-identical with a sha256; `finish_reason=length` maps to a distinct terminal code; context-limit, completion, horizon,
   infra failure and ambiguous timeout are distinct terminal codes; an observed completion is never discarded or re-sampled on restart.
3. Sol call accounting: reservation appended before the request, failed attempts counted, the 120 cap and per-phase reservations
   enforced (reallocation only via a recorded forecast keeping the 120 total), cumulative and never overwritten on resume.
4. Seeds: whole source families reserved in the pilot's own registry; the generator's registry is opened read-only; families reserved
   by generator runs or by the smoke stage cannot appear in measurement; deterministic axis allocation with seed 9162602; infeasible joint
   assignments repaired before model calls with actual joint counts exported; measurement horizon 8 recorded as an explicit override.
5. Selection (plan §9): P/R/C eligibility as defined; controls quota = ceil(25 % of target) spread across depth bins; P vs R apportioned
   by eligible distinct trajectories with largest remainders; at most 1 P + 1 R per trajectory, max 2 prefixes per trajectory; never the
   same prefix twice; every redistribution logged; selection refuses to run before the frozen report exists.
6. Export: at most one chosen/rejected pair per prefix; requires an acceptable chosen answer and a substantive preference; ties and
   all-bad sets go to rejected_pairs.jsonl; chosen and rejected share the byte-identical prefix (same sha256); ADAPTER_CONTRACT.md states
   the completion-only mask including earlier bad assistant turns.
7. Budget: EUR 5 total, operational stop EUR 4.00, reserve EUR 1.00, GPU ledger from gpu-start/gpu-stop, conservative deadline computed;
   forecast refuses to admit a size whose full annotation cannot be funded within the remaining Sol reservation; admission sizes 35/28/21/14
   apportioned by largest remainders with omitted cells recorded.
8. Offline tests exist for every item in the brief's "Required tests" list and pass; no test spawns codex, opens a socket or reads ~/.codex.
9. Nothing outside data/rlhf/dialogue_quality_depth/ was modified (the reviewer checks ../prompt_generator/RELEASE.json hashes still
   verify against the files and that ../sample.py, ../judge_rank4.py, ../../math/codex_server.py are untouched: compare mtimes/contents to
   your reading of them).

Major (fix in this checkpoint unless argued otherwise): prompt quality of user_policy.txt, turn_quality.txt and the ranking prompt —
they must give Sol enough of the plan's semantics (serious vs minor definitions, repair opportunity, done signal, acknowledging a visible
mistake as an ordinary user would, no padding to the horizon) to produce usable outputs; RUNBOOK.md commands must match dqd.py exactly;
DQD_OK/DQD_FAIL lines on every command.

Minor: readability, dead code, duplicated logic.
