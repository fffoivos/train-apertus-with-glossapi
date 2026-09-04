# Review brief: round-two data screen and plan (subproject 12)

You are reviewing the data-preparation plan and the annotation screen for the Greek SFT of Apertus-8B-Greek-CPT, not a training run.
Read first: `docs/ROUND2_DATA_PLAN_20260905.md` (the plan: mix, timeline to Sunday 6 September, CSCS budget, decisions) and
`docs/ANNOTATION_HANDOFF_20260905.md` (what runs, where the files are, how every number is reproduced, the prompts verbatim, known defects,
the questions to judge). Background: `SFT_ROUND2_PLAN.md` (§1a, §2a, §2b), `EXECUTION_LOG.md` (today's entries from 18:05), the round-one
evidence that vantage transfers but language does not (E2 / E3 / E3′ in `results/READOUT_provisional.md`).

Code to read: `data/terra_probe.py` (rubric and judge call), `data/annotate_core.py` (driver), `data/route_technical.py` (category routing),
`data/zebra_check.py` and `data/puzzle_keep_list.py` (exact checker), `data/gt_score.py`, `data/build_keep_lists.py`, `data/export_core.py`,
`data/gen_greek_rewrite.py`. Data on this machine: `~/sft_annot/` (exports, labels, verified lists, calibration runs). Read-only.

Hard constraints: data preparation done by late Sunday 6 September; CSCS cap CHF 90 with CHF 28.96 left; the owner's rules in plan §1.

Judge these, with numbers where you can recompute them:
1. The routing rule (checker > Sol by source and category > Luna) against the measured judge performance; anything routed to Luna that should not be.
2. Consistency of "verified answers, or a recent generator" across the mix table; whether the dropped sources are really worse than the kept.
3. The Sunday timeline at the measured rates; the first thing to cut if it slips.
4. The budget arithmetic and the choice of a half mix for one epoch under the current cap.
5. The known defects; whether any threatens the mix.
6. Whether the ground-truth method inflates the judges' scores.

Deliverable: findings most severe first, each with a location and a concrete fix, then what is verified good, then ordered asks.
Report failing numbers raw. Last line: `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n>`.
