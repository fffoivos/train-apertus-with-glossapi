# Independent review: eight fresh Level-5 rows

## Scope and outcome

The review covers exactly `fresh_math5_line_1334`, `1379`, `3775`, `4646`, `2676`, `3093`, `3125`, and `5977`. I read each frozen English source and reference, its Greek adaptation, every high and blind-verification solution, and every available xhigh solution. Xhigh variants exist for `1379`, `3775`, and `4646`; the other five rows have no xhigh artifact.

No row is held and no solution needs mathematical repair. The selected solution for all eight rows is the blind `verify` version because in each case it states the needed domain or geometric qualification at least as clearly as the other valid version(s). Agreement of final answers was used only as a cross-check: every derivation was checked independently.

The row decisions are:

| Row | Decision | Selected solution | Final | Main finding |
|---|---|---|---|---|
| `1334` | Repair Greek adaptation; accept solution | `verify` | 45 square units | The proof correctly distinguishes the double root at `x=3` from a second point. Prompt wording is understandable but translation-like; a minimal natural rewrite is supplied. |
| `1379` | Repair Greek adaptation; accept solution | `verify` | 3 points | Injectivity and all three real cases are complete. Replace “η f(x) είναι μια συνάρτηση” with the mathematically precise “Έστω f μια συνάρτηση”. |
| `3775` | Accept | `verify` | `k=0` | The degenerate linear case, the full discriminant split, and the excluded denominator root at `k=-1/2` are all handled. |
| `4646` | Accept | `verify` | `(-3/10,-10/3)` | Vieta’s product is valid after establishing `x≠0`; an independently reconstructed circle gives zero residual at all four points. |
| `2676` | Accept | `verify` | 10 units | Two base-height expressions for the same triangle give the result; the proof correctly allows altitude feet on the supporting lines. |
| `3093` | Accept | `verify` | 30 units | `r/h=4/9`, so the similar triangle has scale `5/9`; all triangle and segment conditions are satisfied. |
| `3125` | Accept with declared source-typo normalization | `verify` | 3 | The English source is missing “is”. The Greek adaptation repairs that obvious typo transparently; the analytic ellipse derivation is correct. |
| `5977` | Accept | `verify` | 17 units | Under the standard simple-quadrilateral convention, the perpendicular offsets differ by 15 and the other component is 8. The proof states the convention. |

`adjudication.jsonl` contains the complete selected solution result, accepted prompt text, source identity, hashes of every reviewed adaptation/solution artifact, variant comparison, and the row-specific mathematical, domain, reference, and Greek findings. The two proposed Greek prompt repairs are review candidates only; no frozen pilot file was altered.

## Independent mathematical checks

The exact checks confirm:

- `1334`: x-intercepts `-2,3`, y-intercept `18`, area `45`.
- `1379`: `x²=x⁴` factors as `x²(x-1)(x+1)`, giving exactly `-1,0,1`.
- `3775`: discriminant `4+8k`; the `k=-1/2` double root has original denominator zero, while `k=0` gives `x=-1`.
- `4646`: the circle through the three stated points has coefficients `A=89/30`, `B=1/30`, `C=-51/5` in `x²+y²+Ax+By+C=0`; the derived quartic vanishes at `2,-5,1/3,-3/10`, their product is `1`, and the fourth point also has zero circle residual.
- `2676`: both area expressions give `CE=10`.
- `3093`: perimeter `54`, `r/h=4/9`, scale `5/9`, new perimeter `30`.
- `3125`: minor diameter `2`, axis ratio `3/2`, major axis `3`.
- `5977`: `AD²=8²+15²=289`, hence `AD=17`.

The successful calculation command was:

```text
python3 review/fresh8_agent/independent_checks.py
```

Its complete output is frozen in `independent_checks.txt`. The script uses only Python’s standard library and exact rational arithmetic except where the calculations are integral.

## Independent check of root’s two source repairs

Both repairs in `review/fresh8_root/source_repairs.jsonl` are accepted.

For `fresh_math5_line_1950`, “at a random time” does not by itself specify a unique joint distribution. Making the two arrivals independent and uniform on the hour states exactly the model already used by the reference and generated solution. Under that model, the non-meeting area is `2025/3600`, so the meeting probability is `7/16`. The existing high solution remains complete; its phrase “with the usual interpretation” is merely redundant after the prompt repair.

For `fresh_math5_line_6930`, the generated identity is correct:

`sin²x+sin²2x+sin²3x+sin²4x-2 = -2 cos x cos 2x cos 5x`.

The original question nevertheless implies a unique sum that does not follow from its wording. Every zero of `cos x` is already a zero of `cos 5x`, since `x=(2n+1)π/2` implies `5x=(10n+5)π/2`. Thus `(a,b,c)=(1,2,5)` and `(2,5,5)` define equivalent zero equations but yield sums `8` and `12`. Asking for one possible sum and requiring the identity preserves the intended trigonometric task. The existing high solution already proves the `(1,2,5)` factorization and says “we can take”, so it needs no change.

The successful supplemental check was:

```text
python3 review/fresh8_agent/source_repair_checks.py
```

Its output is in `source_repair_checks.txt`; the analytic zero-set argument above, rather than the numerical grid, establishes nonuniqueness.

## Boundaries

This is an eight-row targeted adjudication plus the separately requested two-repair check, not a prevalence estimate. No model subprocess was called. No source, accepted run artifact, queue, score, production dataset, or solution was modified; all new files are confined to `review/fresh8_agent/`.
