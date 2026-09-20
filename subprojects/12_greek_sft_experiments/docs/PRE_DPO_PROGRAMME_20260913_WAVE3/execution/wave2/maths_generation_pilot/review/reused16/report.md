# Independent adjudication of 16 reused maths-pilot rows

Review completed by the Sol agent at **2026-09-13 16:35:17 Europe/Athens**. I fully read **16 frozen rows**: all **8 repair rows** and all **8 reused controls**. For each row I kept the frozen Greek problem, actual prior target, supplied reference, and generated high/xhigh/blind variants distinct. This is a row-level adjudication of this deliberately selected set, not a population-quality estimate. The 16 fresh pairs are outside this review and remain assigned to root.

## Decisions

| Disposition | Count | Meaning in this review |
|---|---:|---|
| `regenerate` | 8 | Replace the defective prior target with the named generated candidate. |
| `keep` | 8 | Retain the actual prior target; generated text is valid but unnecessary. |
| `source-repair` | 0 | No frozen pilot problem needs another repair before use. Three frozen inputs already carry explicit historical control-character repairs. |
| `hold` | 0 | No mathematical uncertainty remains within these 16 frozen inputs. |

The eight repair rows all have a mathematically acceptable replacement. The eight controls remain valid. Agreement between variants was treated only as corroboration; each result was checked from the problem itself.

## Repair rows

| Row | Prior/reference adjudication | Accepted candidate | Mathematical reason |
|---|---|---|---|
| `repair_math5_139` | Prior and reference reach 7 through a false angle identification caused by opposite rays. | `solve_high` | The sine-law proof covers the admissible angle branch and derives (AP/BP=3+2\sqrt2), hence 7. |
| `repair_math5_77` | Prior reaches 28 but falsely equates a (k)-owner collection with one (k)-cycle. | `solve_high` | The replacement uses invariant subsets/unions of cycles, then counts cycle types ((10)) and ((5,5)) to obtain (3/25) and 28. |
| `repair_math5_537` | Prior reaches 906 but falsely says (cos x=0\Rightarrow x=150^\circ). | `solve_high` | Direct enumeration gives no (cos x=0) solution, six solutions from the other factors, and sum (906^\circ). |
| `repair_math5_1014` | Prior has the right 2% but miscounts blue pieces and changes the area denominator. | `solve_xhigh` | Direct area normalization gives (x=0.1L) and blue area (2x^2=0.02L^2). |
| `repair_math5_630` | Prior/reference use a point-order derivation outside its established domain. | `solve_xhigh` | Coordinates give the tangent formula for every (AC=x>0); AM-GM is tight at (x=2\sqrt2). |
| `repair_gsm_1253` | Prior/reference give 9 minutes by counting only the outward trip. | `solve_high` | The explicit Greek “να φέρει πίσω” requires (2\times3600/400=18) minutes. |
| `repair_math5_436` | Prior/reference reverse the physical forbidden transition, although the count stays 630. | `solve_xhigh` | Bottom-to-top, face-to-face is exactly face-up then face-down; the nine valid orientation strings times 70 metal orders give 630. |
| `repair_gm_math_2231` | Prior has the right 24 but relies on an unstated binomial convention for negative starts. | `solve_high` | Elementary factors (8) and (3), plus the witness (1\cdot2\cdot3\cdot4=24), cover all integer blocks and prove maximality. |

The frozen problems for `repair_math5_77`, `repair_math5_537`, and `repair_math5_630` already record their source-level LaTeX control repairs. I found no remaining source defect in those frozen inputs, so their disposition concerns the target solution only.

One generated repair introduced a new presentation defect: `solve_high__repair_math5_1014` contains two decoded **U+000C** characters where `\frac` was intended. Its arithmetic idea is valid, but the text is not acceptable. `solve_xhigh` is clean and is the selected version. No selected candidate contains a disallowed decoded C0/DEL character.

## Controls

All eight prior controls remain the preferred targets:

- `control_gm_gsm_3835`: (3(60+3\cdot80)+20=920).
- `control_gm_gsm_3096`: the ordinary classroom rate reading gives (120/3=40). Exact endpoint timing is not specified, but that mild physical ambiguity does not make the target wrong under the charitable intended reading.
- `control_gm_math_2731`: the three roots are (2,2,2), with product 8.
- `control_gm_math_1054`: the square sum is (385=35\cdot11), so the remainder is 0.
- `control_gm_math_1745`: area gives the lower bound 100 and the standard triangular grid attains it. The concise prior proof is complete.
- `control_gm_math_837`: (10.5/0.25=42) ounces.
- `control_gm_math_3507`: the original slope is (-2/3), so the perpendicular slope is (3/2).
- `control_gm_math_3924`: exclude the ten perfect-square denominator zeros among 100 numerator roots, leaving 90; cancellation cannot restore excluded domain points.

Both generated variants for each control are also mathematically valid and use acceptable Greek. They do not justify replacing an already correct prior target. This observation is limited to the eight controls read here.

## Evidence and limits

The deterministic verifier independently recomputes the pivotal finite counts, branches, sums, ratios, unit conversions, and control answers. It also binds each selected generated envelope to its recorded input and prompt hashes and detects the rejected U+000C output. It does not execute generated code. Geometric construction claims and semantic interpretation were reviewed directly rather than inferred from answer agreement.

Files:

- `adjudications.jsonl`: all 16 row-level decisions and evidence.
- `verification.json`: passing deterministic calculation receipt.
- `verify_reused.py`: verifier source.
- `source_manifest.json`: frozen source and all 36 accepted-envelope hashes examined.

Review performed by the Sol agent; no additional model subprocess calls and no production writes were made.
