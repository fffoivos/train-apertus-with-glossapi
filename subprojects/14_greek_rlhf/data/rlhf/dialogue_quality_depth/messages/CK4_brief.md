# Checkpoint CK4 — export tie rule (owner's pair rule)

Observed in runtime/measurement: selection SEL018 (ME032, recovery prefix, depth 3) was rejected as `tie` although one candidate is
`reinforce` (c2) and the other two are `neutral` and tied with each other. The owner's pair rule (docs/RLHF_PLAN_20260916.md §24
update): chosen = the top-ranked `reinforce` candidate (an acceptable answer); rejected = the lowest-ranked candidate (`discourage`
preferred, `neutral` acceptable); keep the pair only when the judge's margin between chosen and rejected is clear. A tie BETWEEN the
lower candidates must not block a pair; a tie between the chosen and the next candidate does. `no_acceptable_chosen` stays as is.
Fix export_pairs.py accordingly (and rank.py only if the tie information needed is not recorded), add tests for: reinforce + two tied
neutrals → pair; two tied reinforce at the top → rejected as tie; reinforce vs discourage clear → pair; all neutral → rejected.
Export must remain idempotent: re-running `export measurement` after the fix must rewrite preferences.jsonl and rejected_pairs.jsonl
consistently (record the rule version in the receipt). Write messages/impl_CK4_1.md when done. Offline only.
