# CK4 acceptance — export tie rule
Blocking: (1) pair accepted iff the top candidate is `reinforce`, the rejected is the lowest-ranked, and the chosen is not tied with the
second-ranked candidate; ties among lower candidates never block; (2) `no_acceptable_chosen` unchanged; (3) tests as listed in the brief
pass; (4) re-export idempotent, rule version in the receipt; (5) no change to ranking prompts, sampling or barriers; nothing outside the
directory modified.
