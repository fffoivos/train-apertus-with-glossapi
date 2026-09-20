# Controlled-training cost gate

No training or evaluation job is authorized by this artifact.

The competition-coverage comparison requires two fresh continuations. The existing `R3_passB` run cannot serve as its control because it starts from R3, not from the common pinned G2F1P0 checkpoint required for both arms.

The latest file-backed accounting snapshot records CHF 164.0810556 used and CHF 65.9189444 remaining under the CHF 230 SFT cap, equivalent to 24.5052 node-hours at CHF 2.69 per node-hour. Refresh this value and the scheduler state immediately before submission.

## Decision

Proceed to exact manifest preparation only. The complete two-arm screen, including its targeted checks, must price at **no more than 4 node-hours / CHF 10.76** before it can be considered for launch.

At that ceiling, retaining:

- 10.4652 node-hours for a selected main run plus finish, based on observed R3 and short-pass training time with a 20% multiplier;
- 3.9786 node-hours for a selected-candidate battery, based on unique historical evaluation windows with a 20% multiplier; and
- 4 node-hours of shared retry/setup reserve

leaves 2.0614 node-hours / CHF 5.55. A six-node-hour screen leaves only 0.0614 node-hours / CHF 0.17 and is therefore operationally unsafe even though it is arithmetically below the cap.

These are telemetry anchors, not a launch estimate. Exact tokenized arm manifests and an exact evaluation manifest must replace the historical proxies. The final battery may not be narrowed silently: Greek quality, maths, instruction following, dialogue, termination and foreign-language retention remain separate reported endpoints.

## Launch gate

Before either arm is submitted, verify all of the following in one canonical-runner receipt:

1. identical pinned G2F1P0 parent;
2. identical learning rate, schedule, seed, updates, batch geometry and non-maths replay;
3. matched rendered exposure and reported supervised tokens and unique problem counts;
4. only the elementary-versus-competition allocation differs;
5. complete targeted evaluation priced inside the same four-node-hour experiment ceiling;
6. fresh queue and accounting evidence; and
7. explicit owner authorization.

If exact pricing exceeds four node-hours, stop. Reprice the whole path to the final candidate rather than dropping evaluation cells or reserve without an explicit decision.
