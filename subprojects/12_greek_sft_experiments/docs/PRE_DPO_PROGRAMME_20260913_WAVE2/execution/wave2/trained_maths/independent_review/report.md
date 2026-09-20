# Independent adjudication of the trained-maths audit

**Completed:** 13 September 2026, 16:06:06 Europe/Athens  
**Reviewer:** Sol agent, full manual semantic reading  
**Reviewed:** all 13 raw flagged or uncertain rows; both targeted known-failure controls; and 12 deterministic raw-unflagged controls. Because `gm_nat_618_4` belongs to both the flagged set and the targeted controls, this is 27 review slots and 26 distinct rows.  
**Execution boundary:** No additional model subprocess calls, production writes, source edits, network work, training, or CSCS jobs.

## Decision

The raw audit found several real problems, but it also treated a few defensible language choices and concise proofs too strictly. The independent read routes four rows for prompt-level semantic repair, one for a proof repair, one for a final-unit repair, and the previously unflagged `gm_nat_301_3` for a local terminology repair. It keeps the remaining inspected rows, with optional presentation polish on two.

No editor-introduced mathematical or task damage was observed in these 26 rows. One edit changes an acceptable indeclinable foreign-name form to another acceptable declined form and creates a mild style inconsistency, but no semantic defect. This is a result for the named rows only, not a population claim about the editor or corpus.

Every inspected actual training record is byte-identical to its supplied after-correction messages, appears once, and has user then assistant speaker ownership.

## How the independent controls were chosen

The control seed is `trained-maths-independent-controls-v1`. Rows had to have an accepted raw verdict of `no_defect_found` and could not be a known-failure control. Within each stratum, the row with the smallest SHA-256 rank of the literal string `seed\0stratum\0row_id` was selected. Twelve of the fourteen represented strata were then selected by the analogous deterministic stratum rank. This produced twelve rows from twelve distinct strata:

| Stratum | Row |
|---|---|
| native_none/edited | `gm_nat_16_2` |
| gsm/edited | `gm_gsm_3835` |
| math_1/unchanged | `gm_math_2731` |
| gsm/unchanged | `gm_gsm_3096` |
| math_4/edited | `gm_math_3507` |
| math_2/unchanged | `gm_math_1054` |
| math_3/edited | `gm_math_1745` |
| math_4/unchanged | `gm_math_3924` |
| native_second_solve/unchanged | `gm_nat_1080_1` |
| math_3/unchanged | `gm_math_837` |
| native_none/unchanged | `gm_nat_710_2` |
| math_1/edited | `gm_math_3807` |

The root-recovered `accepted/025.json` was already present when this review was frozen; it supplied the raw result for `gm_math_3807`. This audit did not make a replacement model call.

## Adjudication of the 13 raw flags

| Row | Independent judgment | Route |
|---|---|---|
| `gm_math_1372` | Correct. `ν < 10,14` lacks an approximation marker, but integrality means it does not admit a wrong candidate or invalidate 73. | Keep; optionally write `71/7 ≈ 10,14` or skip the decimal. |
| `gm_gsm_4161` | The literal “each camper” could mean 96, but the preceding percentages make the intended “each interested camper” reading plain. The calculation 56 is correct under the ordinary classroom reading. | Keep; optional prompt clarification. |
| `gm_nat_738_1` | The prompt says the visit fee and per-metre fee are “the same amount”, contradicting the table's 90 € and 14 €/m. The solution is correct for the table. | Repair the prompt; keep the solution. |
| `gm_math_2231` | The answer 24 and maximality example are correct. The binomial notation is not defined for every negative starting integer under the ordinary elementary convention. | Add an elementary divisibility line or handle nonpositive blocks; keep 24. |
| `gm_nat_618_4` | All volume, cost, and rounding work is correct. The requested unit is euro cents, so the final form should be `362 λεπτά`, rather than `3,62 €`. | Repair the final unit only. |
| `gm_nat_635_0` | `Το κατάστημα της έκανε έκπτωση` is naturally resolved in context as “the shop gave her a discount”. Writing `τής` would remove the possessive reading, but the current form is not defective Greek. | Keep. |
| `gm_gsm_4211` | The prompt gives 22 €/hour but only a count of three dogs. `3×22` needs a missing duration or a per-dog rate. | Repair the prompt before reuse. |
| `gm_gsm_4140` | Both indeclinable `της Έμμα` and integrated `της Έμμας` are defensible. The editor's answer-only change produces mild stylistic inconsistency, not a grammatical or semantic failure. The arithmetic is correct under the intended simple-yield classroom convention. | Keep; do not rewrite automatically. |
| `gm_gsm_5274` | The arithmetic gives about 30 mL. Omitting “about” in the answer is a precision-of-presentation issue, not wrong arithmetic. | Keep; optional qualifier. |
| `gm_gsm_1514` | The English pronoun is ambiguous, but the available 10-cookie quantity points to Sabrina. The Greek version instead makes the mother the natural giver in the subordinate clause, leaving the amount unknown. | Repair the prompt; keep the calculation and answer 5. |
| `gm_gsm_4519` | “Three times later” is loose, but the elementary task clearly intends a delay three times as large. The editor states that reading more precisely and 165 minutes is correct. | Keep under the charitable classroom reading. |
| `gm_gsm_2098` | `caboose` is separately counted in the source; `το τελευταίο βαγόνι` can simply be one of the already counted passenger or cargo cars. The Greek prompt no longer compels subtraction of two extra vehicles. | Repair the adapted prompt; keep the algebra and answer 44. |
| `gm_math_550` | The work is concise but adequate. It identifies the only five-digit composition and maximizes its order; the neighboring minimum-sum observation makes the five-digit bound apparent. | Keep. Adding “six digits sum to at least 12” is optional exposition. |

### Proof completeness in `gm_math_2231` and `gm_math_550`

The two rows should not receive the same diagnosis. In `gm_math_2231`, the proof invokes `C(ν+3,4)` for every integer without defining generalized binomial coefficients or handling negative starts. The result is right, but the written proof has a real, small domain gap. In `gm_math_550`, the missing sentence about six digits merely states an already apparent elementary bound; the construction and maximum are sufficiently supported for this task. Concision does not make the answer wrong.

## Known-failure controls

`gm_nat_618_4` was correctly caught by the raw audit, though its defect is narrowly an output-unit failure. It should answer `362 λεπτά`; the mathematics does not need regeneration.

`gm_nat_301_3` was not flagged by the raw audit. Its result is 360 litres and every computation is correct. The first line nevertheless says `ένα μέρος του όγκου` immediately before calculating `1,2·0,5=0,6 m²`. That quantity is the base area, not part of a volume. The reader can infer “part of the volume calculation”, but the unit and teaching context make this a minor terminology defect. Replace only the line with `Υπολογίζουμε πρώτα το εμβαδόν της βάσης του ενυδρείου.`

This control therefore detects a false negative in the raw audit without converting a correct solution into a wrong one.

## Unflagged controls

All twelve deterministic controls remain suitable to keep after full reading:

- `gm_nat_16_2`: correct LCM argument; useful language edit.
- `gm_gsm_3835`: correct 300 and 920 seat totals; useful collocation edit.
- `gm_math_2731`: correct principal-root product 8.
- `gm_gsm_3096`: correct 120/3=40 under the ordinary rate reading.
- `gm_math_3507`: correct perpendicular slope 3/2; improved terminology.
- `gm_math_1054`: correct sum 385 and remainder 0.
- `gm_math_1745`: area lower bound 100 and an exact standard subdivision.
- `gm_math_3924`: 100 numerator roots minus 10 excluded perfect squares gives 90.
- `gm_nat_1080_1`: correct cost equation and 1,5 kg result.
- `gm_math_837`: correct inverse-percentage result of 42 ounces.
- `gm_nat_710_2`: correct remaining share of 104,76 €.
- `gm_math_3807`: correct repair of `συγγραμμική` and correct value 2.

No hidden defect was found in these controls. Their agreement with the raw no-defect verdicts is evidence about these named rows, not an estimate of the unflagged pool's accuracy.

## Editor effects

The editor made local improvements in `gm_math_1372`, `gm_gsm_4161`, `gm_math_2231`, `gm_gsm_1514`, `gm_gsm_4519`, `gm_nat_16_2`, `gm_gsm_3835`, `gm_math_3507`, `gm_math_1745`, and `gm_math_3807`. The other inspected rows were unchanged. None of these edits altered a quantity, operation, answer, task, source interpretation, or speaker boundary.

For `gm_gsm_4140`, `Έμμα` is the important exception to avoid overcorrection: the prompt's indeclinable form is defensible, and the editor's declined form in the answer is also defensible. Consistency could be chosen in a later style pass, but this does not justify treating either form as corrupt Greek.

## Files and limits

`adjudications.jsonl` contains one structured decision per distinct row, including the raw verdict, independent category, route, editor effect, and lineage check. `verification.json` freezes the selection, exact counts, source hashes, and the adjudications hash. `build_review.py` deterministically reconstructs the selected set and validates all lineage claims.

The review used the full `problem_en`, `problem_el`, before-correction problem and solution, after-correction solution, editor record, actual training messages, and raw accepted finding for every selected row. It did not use agreement with a reference answer or earlier second solve as sufficient proof. No prevalence, editor-wide success rate, or production-readiness claim follows from this bounded adjudication.
