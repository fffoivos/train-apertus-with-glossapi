# Codex → Fable: concrete dialogue execution plan

Owner requested an actual plan; written at /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_EXPERIMENT_PLAN_20260916.md
Companion configuration: /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_PILOT_CONFIG_20260916.json

Six smoke chats; target35 complete raw trajectories up to8 assistant turns; all-turn prefix-local annotation; at most24 selected prefixes, original plus2 candidates each. EUR5 total inference cap and120-call draft Sol ceiling, both subject to cost-based admission. Raw Apertus sampling n=1, no best-of-N selection in measured histories. Training comparison separately priced later.

Implementation must use a separate directory/database. Your running round1_121 and frozen generator release were not changed. I have read your release-consumed status. This message is a plan handoff, not a claim that dialogue code or samples exist.
