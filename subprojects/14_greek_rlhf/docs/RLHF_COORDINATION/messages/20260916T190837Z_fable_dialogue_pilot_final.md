# Dialogue preference pilot recommendation

Exported 11 clear pairs; 13 selected prefixes yielded no pair. Yield by P/R/C: {'C': 3, 'P': 3, 'R': 5}. Contributing trajectories: 9. Pair yield is a feasibility measure, not evidence that prevention or recovery training is superior. A production allocation should retain a good-context control slice and be chosen only after comparing meaningful yield and verified fixes across P/R/C, depth, task and language.

Known gaps: simulator bias; sparse non-Greek language cells; observed-horizon no-error censoring; no trained-model comparison; no causal demonstration that a locally preferred reply prevents later failure.

## Addendum 2 (2026-09-16 22:32 UTC): escalating resampling run on the 15 unpaired late-failure prefixes (plan §30)
480 fresh replies (32 per prefix, one L40S session), judged in escalating batches of four, stop at the first reinforce, 40 Sol calls.
Samples needed: 4 → 5 prefixes, 8 → 3, 12 → 3, 16 → 3, none at 32 → 1 (ME027 P: the "add the 21 booked places" instruction). 13 pairs
exported (one reinforce found without a clear margin). Pairs now 24 = 11 original + 13 resampled (P 10, R 11, C 3); all 10 late-failure
chats contribute at least one pair. Protocol calibration: half the prefixes need more than 4 samples and a quarter need 12–16; the
32 cap was reached once in 15. Recommended production default for dialogue prefixes: sample 16 fresh replies up front, judge in
escalating fours, stop at the first reinforce; escalate to 32 only for prefixes still empty at 16. Total pilot GPU EUR 1.95; Sol 94 calls.
