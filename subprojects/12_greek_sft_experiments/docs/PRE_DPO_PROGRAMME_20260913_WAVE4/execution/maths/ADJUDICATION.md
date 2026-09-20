# Independent adjudication of 19 targeted maths records

## Scope and evidence boundary

This is an independent, record-level adjudication of the 16 rows in `adjudication_packet.jsonl` plus the three rows in `adjudication_supplement.jsonl`. It is a targeted defect packet, not a prevalence sample, and no rate should be extrapolated to the wider dataset. I read each complete Greek problem, candidate solution, reference, provenance fields, and first-review finding. The first review was treated as a claim to test rather than ground truth.

Input identities:

- `adjudication_packet.jsonl`: SHA-256 `388510113165955094bb985819ce0aad3815083dbe5127010055d3f1b87a583f` (16 rows)
- `adjudication_supplement.jsonl`: SHA-256 `19b6d84d83a6dca7c5fd790d25397c73b2ee9c01be7f8bdc68d8d8048d4b0b43` (3 rows)

No source row, official score, or repository file was changed. The companion `adjudication.jsonl` contains one structured decision per row. This was a Sol agent review with no additional model subprocesses and no web access.

## Adjudication summary

Nine candidates have a substantive proof, fidelity, or task-semantic defect despite several correct final numbers: `math5_139`, `math5_77`, `math5_400`, `math5_537`, `math5_1014`, `math5_630`, `math5_765`, `gsm_1253`, and `math5_436`.

`math5_900` correctly challenges a bad source/reference: strict positivity prevents the alleged equality case, so there is no minimum and only an infimum. `math5_269` is conditional and remains unresolved because the localized source does not specify whether the alphabet has 24 or 26 letters.

Four GSM rows are acceptable under ordinary, charitable classroom conventions, while retaining a low-severity source-precision note: four weeks per month (`gsm_4032`), exactly 14 hats (`gsm_4250`), length divided by spacing (`gsm_3826`), and disjoint occupied/broken seats (`gsm_3149`). These conventions should not be promoted to automatic fatal candidate defects.

The first review produced clear false positives or overstatements on `math5_357`, `gsm_2440`, `math5_1103`, and parts of `gsm_1334` and `gsm_1253`. Greek coordinated ellipsis in `math5_357` is grammatical. Retained imperial units are allowed when they preserve the arithmetic. In a dollar-denominated context, `λεπτά` is less idiomatic than `σεντ` but remains numerically unambiguous; this is stylistic terminology, not a wrong unit magnitude.

## Row decisions

| Row | Candidate result | Independent decision | Required boundary |
|---|---|---|---|
| `math5_139` | Final 7 correct | Major proof error: supplementary angles are asserted equal; point order is omitted | Repair proof only |
| `math5_900` | Correctly says no minimum; infimum boxed | Source/reference defect; first review overstates boxed-infimum issue | Keep positivity and challenge reference |
| `gsm_4032` | 200 conditionally correct | Accept explicit four-week classroom convention; source mildly underspecified | Clarify source only if desired |
| `math5_77` | Final 28 correct | Major false cycle equivalence; candidate double-backslash markup; source U+000C corruption | Repair invariant-subset proof and markup |
| `math5_400` | `sin²t` correct only inside interval | Source invalid at both endpoints; candidate omits domain restrictions | State undefined endpoints; do not force source true |
| `math5_269` | 17576 correct for 26 letters | Source/adaptation ambiguity: Greek 24 versus English 26 | Resolve alphabet before unique answer |
| `math5_537` | Final 906 correct | `cos x=0 ⇒ x=150` is false; source has four U+0007 corruptions | Remove false case; repair markup |
| `gsm_4250` | €700 under intended reading | Accept exact-14 classroom convention; literal wording only entails at least 14 | Optional source precision |
| `math5_1014` | Final 2% correct | Major count/denominator error: four blue pieces over two squares | Repair derivation only |
| `math5_630` | Final maximum correct | Proof covers only one point order; candidate and source math markup corrupted | Use domain-wide coordinate proof; resolve markup provenance |
| `math5_765` | Final 401 correct | Silent dollar-to-euro substitution is a fidelity defect; source U+001B and version ambiguity | Make units consistent after provenance resolution |
| `gsm_1253` | 9 minutes | Incorrect for explicit Greek “bring back”; round trip is 18 | Include return leg; preserve imperial arithmetic |
| `gsm_3826` | 286 | Accept intended spacing convention; endpoints remain mildly unspecified | No candidate repair |
| `gsm_1334` | €5 mathematically correct | Bare boxed 5 is a minor presentation issue; imperial-units flag is false positive | Optionally add € only |
| `gsm_2440` | 270 correct | No candidate defect; miles are an allowed preservation choice | No repair |
| `math5_357` | 2 correct | Reviewer false positive: coordinated Greek ellipsis licenses plural agreement | No repair |
| `math5_1103` | 99 correct | `λεπτά` is stylistically less specific than `σεντ`, but dollars make the unit unambiguous | Optional terminology polish only |
| `gsm_3149` | 250 | Accept ordinary disjointness convention; literal overlap would permit 250–300 | Optional source precision |
| `math5_436` | Final 630 correct | Candidate and reference reverse the face-to-face transition; count remains 9 by symmetry | Reverse TH/HT reasoning only |

## Candidate defects with correct final answers

- **`math5_139`:** Coordinate reconstruction gives `P=2±√2`. The two configurations have `∠BAC≈76.057°` and `13.943°`; the `<45°` premise selects `P=2+√2`, so `AP/BP=3+2√2` and the final 7 is sound. The candidate's equality `∠DPB=∠DPO` is still false. Both angles must instead be related through supplements.
- **`math5_77`:** A selected set of pairs covering the same adults is a union of cycles, not necessarily one cycle. The final criterion survives because a union totaling less than 5 necessarily contains a cycle of length less than 5, and such a cycle itself violates the condition.
- **`math5_537`:** There is no root of `cos x=0` in `(100°,200°)`. The candidate duplicates 150 from the `cos 3x=0` branch, so deduplication happens to preserve the correct final set and sum.
- **`math5_1014`:** The rearrangement contains four blue `0.01k²` pieces in total and has total area `2k²`; the candidate says two pieces and normalizes them as though the total were `k²`.
- **`math5_630`:** The claimed tangent formula is globally correct, but the signed-length/angle-difference proof does not establish it for `0<x≤2`. Coordinates give it directly for all `x>0`.
- **`math5_436`:** With `H` meaning that the upper side bears the face and the stack read top-to-bottom, the forbidden contact is `TH`. The candidate and reference say `HT`. Both restrictions admit nine monotone strings, so the count 630 survives.

## Source defects, ambiguity, and provenance limits

- **Actual source/reference failure:** `math5_900` asks for an unattained minimum; `math5_400` includes two undefined endpoints.
- **Semantically unresolved source:** `math5_269` omits which alphabet; `gsm_1253` makes a return trip explicit in Greek while its reference counts only the outward trip.
- **Confirmed source corruption:** `math5_77` has one U+000C, `math5_537` has four U+0007 characters, `math5_630` has two U+0007 characters, and `math5_765` has one U+001B. `math5_630` also has one U+0009 and six U+001B characters in the candidate. These counts came from decoded-string code-point inspection.
- **Unresolved historical pairing:** `math5_630` and `math5_765` have multiple corrupted stored problem variants without evidence identifying the historical source paired to the chosen solution. This provenance uncertainty is separate from the mathematical adjudication.
- **Low-severity classroom underspecification:** `gsm_4032`, `gsm_4250`, `gsm_3826`, and `gsm_3149` should be clarified at source level if formal uniqueness is required, but their candidates are acceptable under their evident teaching convention.

## Adaptation versus correction

Preserving yards, feet, inches, or miles is allowed when those units carry the arithmetic. Accordingly, the adaptation flags on `gsm_1253`, `gsm_1334`, and `gsm_2440` are not defects. A cosmetic metric conversion could introduce rounding or change the task.

The currency cases differ. `math5_765` changes dollars in the displayed problem to euros in the solution, so it fails exact premise fidelity even though both currencies have 100 subunits and the answer remains 401. `math5_1103` keeps dollar signs and values throughout; its use of `λεπτά` is understandable from context and is at most a terminology polish. These are adaptation judgments, not reasons to rewrite a problem so that a reference becomes true.

## Exact local checks executed

The following deterministic Python calculations were executed with the system `python3`; no symbolic service or model was called:

```text
math5_77:
  9! + C(10,5)/2 × (4!)² = 435456
  10! = 3628800
  435456/3628800 = 3/25

math5_537, roots in 100<x<200:
  cos(3x)=0 -> 150
  cos(4x)=0 -> 112.5, 157.5
  cos(5x)=0 -> 126, 162, 198
  cos(x)=0 -> none
  unique sum = 906

math5_1014:
  (4 × 0.01) / 2 = 1/50 = 2%

math5_630:
  tan = sqrt(3)x/(x²-3x+8)
  x = 2sqrt(2) -> 0.6519178866886671
  sqrt(3)/(4sqrt(2)-3) -> 0.6519178866886670

math5_900 admissible approach:
  x1=x2=x3=sqrt((1-97ε²)/3), x4...x100=ε
  ε=0.01   -> objective 3.543062960838135
  ε=0.001  -> objective 2.6948243041273066
  ε=0.0001 -> objective 2.6077736913173077
  infimum 3sqrt(3)/2 = 2.598076211353316

gsm_1253:
  outbound = 6×200×3/400 = 9 minutes
  round trip = 18 minutes

gsm_3826: (900-42)/6×2 = 286
gsm_1334: required=60 inches, long rope=72 inches, short-rope cost=6.25
gsm_2440: 30+(15/10)×60+30+(20/10)×60 = 270

math5_1103:
  39.96-9 = 30.96
  0.75×39.96 = 29.9700
  difference = 99.0000 cents

gsm_3149:
  occupied=200, broken=50, disjoint availability=250
  arbitrary-overlap availability range=250..300

math5_436:
  exhaustive enumeration of 2^8 H/T strings found 9 strings without TH
  70×9 = 630
```

A separate decoded-string scan enumerated every character below U+0020 other than line breaks in `problem_el` and `candidate_solution`. It produced the exact corruption counts listed above. A coordinate calculation for `math5_139` tested both `P=2±√2` configurations against the angle premise and the doubled-angle condition.

## Repair priority

The safest high-value repairs are local proof corrections on `math5_139`, `math5_77`, `math5_537`, `math5_1014`, `math5_630`, and `math5_436`, plus correction of the explicit return-trip error in `gsm_1253`. Source control characters can be repaired mechanically only after respecting the unresolved variant provenance for `math5_630` and `math5_765`. `math5_900`, `math5_400`, and `math5_269` require source-level decisions and must not be “fixed” inside a candidate solution merely to force agreement with a reference.
