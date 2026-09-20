# Maths judge calibration and rejudge report (17 September 2026)

Rubric `data/rlhf/maths_judge/rubric_maths_v1.txt` at maths-v1.2, runner `maths_judge.py`. References are two independent blind solves plus a comparison; the reference solvers never see a candidate reply. Eligibility is computed deterministically from the judged fields (`eligible()`), so the judge's own flag cannot create a positive; the model's original values are kept as `verdict_model` and `eligible_positive_model`. Archived: rubric v1 text (`rubric_maths_v1.0_archived.txt`, sha16 6e438e50ca065dd6) and runner (`maths_judge_v1_backup.py`), bound together.

## A. Calibration: the 20 generated maths prompts of round 2, 8 saved replies each

- References: {'verified': 16, 'ambiguous': 4}
- Replies judged: 160; outcomes {'incorrect': 88, 'correct': 37, 'partial': 35}; reasoning {'invalid': 127, 'valid': 32, 'not_provided': 1}
- Ambiguity handling: {'not_applicable': 128, 'no': 31, 'yes': 1}
- Eligible positive replies: 27; prompts with at least one positive: 8 of 20; prompts that can form a pair: 8
- Deterministic rule versus the judge's own flag: 0 disagreements (the judge was self-consistent; the rule now enforces it structurally)

## B. Pre-existing maths: the remaining 41 keepable items carrying maths content (forum and seeded), 4 to 8 saved replies each

- References: {'ambiguous': 25, 'verified': 16}
- Replies judged: 176; outcomes {'partial': 83, 'incorrect': 82, 'correct': 11}; reasoning {'invalid': 157, 'valid': 10, 'not_provided': 9}
- Ambiguity handling: {'no': 87, 'yes': 21, 'not_applicable': 68}
- Eligible positive replies: 0; prompts with at least one positive: 0 of 41; prompts that can form a pair: 0
- Deterministic rule versus the judge's own flag: 0 disagreements (the judge was self-consistent; the rule now enforces it structurally)

## Required cases (maths plan A4)

- `g2:R2B1_006`, the reply whose shares are right but whose chain of exact equalities uses a finite decimal for one third: outcome correct, reasoning invalid, discouraged, not an eligible positive; the clean worked solutions rank above it.
- `g2:R2B12_005`, average 14.9 with an ambiguous "points needed to reach 15": reference ambiguous, no positive, the confidently phrased non-answers are not reinforced.
- `g2:R2B11_009` candidate 1, raised by the R-RL2 reviewer as a possible wrongly excluded positive: under v1.2 it is still not eligible. It computes the 60–240 g range correctly, but the question is ambiguous (the guide does not fix which dose goes with which timing) and the reply does not name that ambiguity (`handled_ambiguity = no`), so it cannot be a positive on an ambiguous reference.
- The maths-in-dialogue case belongs to the dialogue workstream (RGD005, six turns held for this judge).

## Rule changes made during this work

- **v1.1**: under v1 any reference not marked verified forced every reply to be ineligible, so 25 of 41 pre-existing items were held purely because both solvers called the question underspecified, which is normal for real forum questions, while the rubric already said a reply naming the ambiguity can be correct. From v1.1 solver disagreement stays a hard hold, but an ambiguous-but-agreed question keeps its reference and its alternative readings.
- **v1.2** (after R-RL2): the rubric no longer contradicts itself (the blanket ambiguous hold is gone), and eligibility is computed from the fields rather than taken from the judge: a positive needs a usable reference, correct outcome, complete answer to what the user asked, reasoning that is not invalid, and a valid explanation whenever one was requested; on an ambiguous reference it also needs `handled_ambiguity = yes`. `task_completion` is now explicitly measured against the user's request, not against extra material in the reference. Regression tests: `test_maths_judge.py` (8 cases).

## What this says about the data

- The 41 pre-existing maths items produce no eligible pair. On the 16 items with verified references the replies are mostly incorrect with invalid reasoning; on the ambiguous ones 21 replies did name the ambiguity but were still wrong or incomplete. This is a measurement of the model, not a judging artefact, and it is unchanged across three rubric versions.
- Forum mathematics (mathematica and engineering boards) is therefore a poor source of maths preference pairs for this model at this stage. Round-3 maths pairs should be expected from the generated maths prompts, whose measured rate on round 2 is 8 prompts with a usable pair out of 20.

## maths-v2: the judge does the mathematics itself (owner decision, 17 September 2026)

The owner's request was a different maths judging prompt, not a separate reference stage; the judge does the calculation. `rubric_maths_v2.txt` makes the judge write `own_solution` and `question_status` before assessing any candidate; eligibility stays deterministic (`eligible_v2`); one call per batch of four at medium effort. No reference is built or passed.

Calibration on the same 20 round-2 prompts and 160 replies, against v1.2 (two blind high-effort solves, comparison, high-effort judge):

| | v1.2 with references | v2 without |
|---|---|---|
| Eligible positive replies | 27 | 31 (26 shared) |
| Prompts that can form a pair | 8 | 9 |
| `g2:R2B1_006` false-equality reply | discouraged, not eligible | discouraged, not eligible |
| `g2:R2B12_005` ambiguous averages | no positive | no positive |
| Sol calls for these 20 prompts | 60 reference + 40 judging | 40 judging |

Divergences, inspected:
- `g2:R2B12_008` (v2 adds 4 positives): the user asks for a full solution and mentions not remembering how fractions are added. The v1.2 reference turned "explain fraction addition" into a requirement, so correct replies that compute 48 + 40 and subtract from 120 were marked partial. v2 marks them complete. This follows the rubric's rule that completion is measured against what the user asked, not against material a reference adds.
- `g2:R2B11_002` (v2 adds 1 positive): bus 18 €, ferry 32 € with 25 % off the ferry, cost of the round trip. The reference solvers flagged ambiguity; v2 took the natural reading (42 € each way, 84 €) and accepted the one reply that shows it correctly.
- `g2:R2B13_012` (v2 drops 1 positive): judge variance on a single reply.

Conclusion: removing the reference stage does not lose the required cases and does not introduce evidence of leniency; round 3 uses maths-v2.
