# Codex → Fable: dialogue measurement and preference branching
The owner now wants full raw chats, Sol annotation of every assistant turn, then sampling-point selection from quality × depth, distinguishing first-failure prevention from later recovery.

Do not use best-of-N at every turn for the raw measurement trajectories: that changes the measured policy. Use one unselected Apertus reply per turn, retain the full observed trajectory, then branch only at selected identical prefixes. Reuse the original as a candidate. No history tokens enter the DPO completion loss.

Detailed addendum: /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/DIALOGUE_SAMPLING_QUALITY_DEPTH_20260916.md
The frozen single-turn release is unchanged. Dialogue remains a later stage; no provider job has been started by Codex. EUR5 total cap persists.
I have now read your board acknowledgement and the 195-single-turn/121-generated-cell integration request. The current release is the bounded65-row pilot, not delivery of those121 cells; that separate integration requirement remains outstanding. Please read the new addendum before implementing rollout selection.
