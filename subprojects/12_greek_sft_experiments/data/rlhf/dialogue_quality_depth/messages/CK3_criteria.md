# Checkpoint CK3 acceptance — pod runner
Spec: plan §2 (checkpoint verification, frozen settings), §5 (smoke lessons), §11 (budget, watchdog independent of the rollout worker,
teardown confirmed), and messages/CK3_brief.md.
Blocking: (1) preflight exactly as in the brief with abort codes; (2) sha256 check before serving; --max-model-len read from config.json;
served model name = Hub id; fail-fast serve loop; (3) EXIT trap does ledger gpu-stop + DELETE + confirmation on every exit path, and an
independent watchdog process enforces the budget deadline; (4) no secret printed, echoed, logged or copied (grep scripts and tests);
(5) offline tests with fake shims cover preflight failures, sha mismatch, serve death, happy path, and trap on failure, and pass;
(6) prime_provision.py untouched; nothing outside data/rlhf/dialogue_quality_depth/ modified.
Reviewer: read the scripts; do not run anything that touches the network.
