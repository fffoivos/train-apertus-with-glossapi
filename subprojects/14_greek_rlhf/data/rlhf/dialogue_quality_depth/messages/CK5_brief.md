# Checkpoint CK5 — escalating resampling stage (owner's protocol, plan §30)

Owner's instruction (2026-09-17): for prefixes with no reinforce-worthy reply, produce more replies, escalating up to 32, and establish
this as the protocol. Implement a new stage in this directory:

`python3 dqd.py --state runtime resample measurement --targets runtime/measurement/resample_targets.json --max-fresh 32
   [--endpoint URL --model NAME --checkpoint-sha256 SHA]`  (GPU part)  and
`python3 dqd.py --state runtime resample-judge measurement` (Sol part), plus `resample-export measurement`.

Semantics:
1. Targets: a JSON list of {trajectory_id, kind (P|R), depth}. The prefix for depth d is the byte-identical message history before
   assistant turn d of that trajectory (same prefix_sha256 convention as candidates.py). Register each target as a selection of kind
   P or R with a receipt (`resample` origin), without touching the frozen report or the existing selection.jsonl rows (append new rows
   with a distinct selection id prefix, e.g. RS###).
2. GPU part: sample up to `--max-fresh` fresh replies per target in ONE pod session (frozen sampling settings, n=1 per request, the
   pod runner `bash pod/run_stage.sh resample` provisions/serves/tears down exactly like `candidates`). Store every completion byte-
   identical with sha256 in runtime/measurement/resample_candidates.jsonl (fields like candidates.jsonl + `batch_index` 0..7 for
   groups of four in sampling order). Resumable and idempotent like candidates.
3. Sol part: judge in ESCALATING batches of four in sampling order: batch 0 (fresh 1–4), then 5–8, … up to 8 batches. Each judge
   call sees the prefix and four candidates (extend rank.py's 3-candidate prompt to four letters A–D, same rubric v2.4 verbatim,
   randomized letters, provenance hidden, verdicts reinforce/neutral/discourage, ties, issues, notes, best_vs_worst). Stop at the first
   batch containing a `reinforce`; record for every target: batches judged, samples needed (4×batches, or `no_reinforce_at_32`),
   the winning candidate id and the lowest-ranked candidate seen across the judged batches (by verdict class then rank).
4. Export: for each target with a reinforce, one pair = {chosen: the first reinforce candidate, rejected: the lowest-ranked candidate
   seen (prefer discourage; neutral acceptable), require clear margin}; append to preferences.jsonl with `origin: resample` and
   `samples_needed`; others go to rejected_pairs.jsonl with reason `no_reinforce_at_32`. Write runtime/measurement/resample_report.json:
   per target and aggregate (histogram of samples needed; share with no reinforce at 32; by kind P/R; cost).
5. Budget: Sol calls for this stage are an owner-authorised extension of the pilot cap: add a recorded `extensions` entry in
   runtime/forecast.json ({"resample": {"authorised_by": "owner 2026-09-17", "max_new_sol_calls": 128}}) and make budget.py honour
   extensions additively (cap = 120 + extensions) with the same reserve-before-request accounting. GPU stays under the EUR 5 cap.
6. Tests (offline, fake clients): prefix hash equals the original selection's for the same depth; batches stop at the first reinforce;
   samples_needed arithmetic; no_reinforce_at_32; export picks the lowest-ranked rejected; extension accounting; idempotent restart.
Write messages/impl_CK5_1.md when done: commands to run in order (openings are not needed; the trajectories exist), and what changed.
