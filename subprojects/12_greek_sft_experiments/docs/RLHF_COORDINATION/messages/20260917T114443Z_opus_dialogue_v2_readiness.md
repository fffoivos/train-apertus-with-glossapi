# Opus (dialogue v2, Workstream B): Stage C readiness — offline gates PASS [shared]

Protocol dialogue-v2-dev-0.1, generator 0.3-dev. Owned paths as in the Stage A message; registry rows added to CURRENT_VERSIONS.md (dialogue v2 pipeline, adaptive user + move-selection rule, world resolver, evaluator view, seeds, sampling config).

Built (B1–B3): adaptive user policy v2.0 with a deterministic move-selection rule (no restatement after a restatement; helping ability; patience tolerance low 1 / medium 2 / high 4 failed replies), user-state transitions, ending reasons; role views built from whitelisted fields (Apertus = public messages only; user; troubleshooting user-actions; world resolver; learner; evaluator); deterministic worlds for RGD003/RGD004 (Sol only maps actions to check ids; unknown actions are unresolved, never success); learner updates accepted only with a verbatim quote of the teaching; prefix-local turn evaluations and hindsight conversation reviews separating target from simulator errors; sampling points (prevention, supported recovery, healthy continuation); branch sampling and escalating ranking with rubric v2.4 plus verification; review page generator; pod runner copy with GET /pods gate, pinned model revision, sha check, EXIT trap, watchdog, GET-confirmed deletion, failed-provisioning pods charged.

Evidence: data/rlhf/dialogue_v2/runtime/readiness.json and readiness_report.md. 21 offline tests covering plan §7 gates 1–10 plus the pod runner: all pass. Dry run with real Sol user/world/learner calls against hand-written stand-in replies (not data): 20 decisions, 0 repairs, 0 policy deviations; resolver mapped all actions to supported checks; learner quotes verbatim; private preferences revealed as new preferences. Independent reviewer (Fable, read-only): cycle 1 HOLD (blocking: an unresolved action's resolver reason could reach the user simulator; major: Sol failure relabelled on rerun and no recovery for a failed Sol call) → fixed with regression tests → cycle 2 PASS.
Gate 10: no DPO trainer exists; exports state completion-only loss and mark trainer integration unverified.

Fixed interpretations and decisions recorded:
- Sampling-config change: max_tokens 1,500 → 1,024 for every D1/D2 reply and branch candidate (dv2-sampling-v1).
- Branch candidates: all 8 per selected D1 point are sampled in one GPU session (avoids a third paid session); judging escalates in blinded fours (second four only if the first gives no verified acceptable reply); results reported as found within 4 and within 8 for a matched-count comparison; "no verified acceptable reply within 8", never incapacity.
- Conversations run concurrently (one thread each) instead of synchronised depth waves: the GPU waits only on the slowest conversation.
- A failed (not ambiguous) Sol call is retried once under a recorded :retry1 id; ambiguous or reserved calls are never retried.
- DVI001 opening word range repaired 450–550 → 220–280 (context fit; ME021 family is 240–300), disclosed in the seed with the pre-repair hash.
- Glossary: every call records the sha16 it read (now ab7c697aca9f08ed, v1.0.2 frozen).
- RGD005 is maths content (explanation and learning): the evaluator accepts any mathematically sound explanation; maths-content turns are held for the specialist maths judge.

D1/D2 counts: 0/0. Sol calls so far: 1 opening call + 24 dry-run calls (+6 latency-probe calls, scratch). EUR spent: 0. First-experiment quotas unchanged.
Next: forecast (separate message), then the D1+D2 collection session.
