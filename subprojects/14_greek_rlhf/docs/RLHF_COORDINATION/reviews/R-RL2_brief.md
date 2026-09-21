# Review brief R-RL2 — maths judge calibration

## Stage goal
A specialist maths judgement that matches the owner's T5 definition, catches the known false positives of the general rubric, and can be applied to the
pre-existing maths items and to new maths prompts. Final product of the phase: all new prompts with their replies evaluated on a review page.

## Scope
- Rubric `data/rlhf/maths_judge/rubric_maths_v1.txt` (maths-v1.1) and runner `data/rlhf/maths_judge/maths_judge.py` (v1 kept as `maths_judge_v1_backup.py`).
- Calibration: `calibration/` (20 round-2 maths prompts, 8 saved replies each) — `references.jsonl`, `judged.jsonl` (v1), `judged_v11.jsonl` (v1.1).
- Pre-existing rejudge: `rejudge_preexisting/` (41 remaining keepable items carrying maths content) — same file layout.
- Report: `data/rlhf/maths_judge/calibration_report.md`. Plan: `docs/RLHF_COORDINATION/MATH_JUDGING_EXECUTION_PLAN_20260917.md` (A2-A4, with the A3 ambiguity rule updated today).
- Old judgements for comparison: `data/rlhf/pool/round{1,2}_all_judged.jsonl` (rubric v2.4, general).

## The rule change to scrutinise
Under v1, any reference not marked `verified` forced `eligible_positive = false`. The pre-existing rejudge then held 25 of 41 items purely because both
independent solvers called the question underspecified, which is normal for real forum questions, while the rubric itself says a reply that names the
ambiguity and asks for or states the missing information can be correct. From v1.1: solver disagreement (`unresolved`, or comparison `agree = false`) is a
hard hold; an ambiguous-but-agreed question keeps its reference and alternative readings, and a reply may be an eligible positive only with
`handled_ambiguity = yes` plus correctness under the reading it states.

## Acceptance criteria
Blocking:
1. References are built without any candidate reply in the solver input, and the judge never treats the reference as text to imitate.
2. Correctness is separate from explanation length; a correct final answer with invalid derivation is never an eligible positive; a short correct answer is allowed when no explanation was requested.
3. Ambiguous items: no positive for a confident single answer; a positive requires `handled_ambiguity = yes` and correctness under the stated reading. Unresolved items stay held.
4. The required cases behave as the plan states: `g2:R2B1_006` (false equality chain not selected), `g2:R2B12_005` (ambiguity held, confident non-answer not reinforced).
5. Prior judgements are untouched; new records are separate files and identify rubric and reference by hash.
Major:
6. The report's counts are reproducible from the files, and its conclusion ("no eligible pair among the 41 pre-existing maths items; forum maths is a poor pair source for this model") follows from the evidence rather than from judge strictness. Say so if the evidence does not support it.
7. The v1.1 change does not create false positives: compare v1 and v1.1 outputs on the calibration set.
