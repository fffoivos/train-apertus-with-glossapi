# Astra review: gate2_full_v9

Date 2026-09-15 15:03 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T14-56-14-01a0a4ec-c0db-7251-92f1-7c57f2f25954.jsonl) · effort xhigh · 6.8 min · prompt 242,076 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v9.md`

## 1. Verdict

**HOLD — V8-H1 and V8-H2 are not fully closed.** The comparator still accepts non-equivalent answers through destructive normalization, and `--expect-deficit` still succeeds when the deficit is zero. These are specific, repairable code defects; they do **not** establish that the current manifest contains incorrect approvals. The supplied 40-row audits now support complete coverage and zero label differences on the pretokenized path. Sample review also found two under-specified GSM problems and three problematic MC questions. I independently checked the supplied code, sample mathematics, word counts and accounting; I did **not** rerun the Python modules, verify on-disk hashes, execute cluster training, or verify external factual claims. Runtime conclusions below are therefore attributed to the supplied logs.

## 2. Findings ranked by severity

### V9-H1 — HIGH: normalization still bypasses the unit whitelist and list protection

**Evidence:** `agree()` calls `equiv_exact()` when neither raw answer parses numerically. That function calls `E.strip_string()`, which still removes **arbitrary** trailing `\text{...}` and `\mbox{...}` content and removes spaces before reconsidering numeric equality.

The following results follow directly from the supplied control flow. These are **synthetic counterexamples, not dataset row IDs**, and were not executed in the installed Python environment:

| Counterexample | Reference | Answer | Result implied by code |
|---|---|---|---|
| V9-C01 | `5\text{ apples}` | `5\text{ or 6}` | `(True, 'symbolic')`: both normalize to `5` |
| V9-C02 | `17, 44\text{ apples}` | `17.44\text{ apples}` | `(True, 'symbolic')`: the list loses its space and becomes decimal `17,44` |
| V9-C03 | `17,\ 44` | `17.44` | `(True, 'numeric')`: the LaTeX space is removed before list detection |

Thus, **three constructed negative cases still reach approval**. This is not an estimated dataset failure rate. I have not identified a current approved record containing these exact pairs.

The new `5\text{ apples}` versus bare `5` regression passes because one side is numeric and triggers early rejection. It does not test the route where **both sides initially fail numeric parsing**.

**Concrete fix:**

- Use one whitelist-respecting normalizer throughout label approval; do not pass approval inputs through the benchmark’s destructive `strip_string()`.
- Preserve list/alternative classification across normalization. Recognize LaTeX spacing without first deleting the evidence of a separator.
- Add these three negative regressions.
- Also test symbolic decimal expressions such as `1.0+1e-100` versus `1.0+0`; the supplied `parse_expr` call does not explicitly enforce rational parsing of decimal literals.
- Re-decide all 12,028 records, publish the changed pairs, then rebuild the approval artifact and dependent manifests/receipts. **Do not presume all 149 symbolic approvals are defective.**

### V9-H2 — HIGH: `--expect-deficit` still accepts a zero-deficit result

**Evidence:** the script checks ordinary success first:

```python
if ok_tr and ok_ev:
    ...
    sys.exit(0)
```

Consequently, complete coverage with zero deficit, zero extra labels and zero wrong values exits successfully **even when `--expect-deficit` is set**. The later `def_tr > 0` condition is never reached.

**Current impact:** this does **not** invalidate audit (c), whose supplied output explicitly reports a positive deficit: **74/14,915 tokens, or 0.496%**. Missing-ID rejection and the extra/wrong-label checks are visibly repaired. The remaining defect is the claimed negative-control contract.

**Concrete fix:** evaluate the requested mode before either success exit:

- Normal mode: complete coverage and zero differences.
- Deficit mode: complete coverage, positive training deficit, zero extra supervision and zero wrong label values.

Verify that deficit mode rejects both a clean run and runs containing missing rows, extra supervision or wrong labels. Then rerun the paired audits.

### V9-M1 — MEDIUM: two of five GSM samples require unstated assumptions

**Count:** **2/5 sampled GSM rows (40%)** have under-specified stems. This is a sample question-quality rate, not a corpus-wide error estimate.

| Row ID | Evidence | Concrete fix |
|---|---|---|
| `math_en_gsm:316680` | “Simon is 5 years away from being 1/2 the age of Alvin.” The target freezes Alvin at 30 and returns 10. Under the future-age reading, \(s+5=(30+5)/2\), giving **12.5**. | Specify “five years younger than half Alvin’s current age,” or exclude the problem family. |
| `math_en_gsm:2274628#1` | Ten customers buying 20 bowls account for 40 rewards. The other ten customers’ purchases are unspecified. If each buys ten bowls, another 20 rewards are due and **10**, rather than 30, remain. | State that the other customers earned no rewards, or exclude the family. |

For exclusions, use the existing **problem-text family mechanism**, covering every solution, repeated copy and Greek twin. Blind agreement with the reference does not resolve either ambiguity.

### V9-M2 — MEDIUM: ambiguous or incorrectly worded questions remain in supervised MC turns

**Count:** across §H and §D, I inspected **27 question–answer turns in eight conversations**. I flag **3/27 turns (11.1%)**, affecting three conversations. Within §H alone, that is **2/17 turns**, affecting **2/5 conversations**.

| Row ID | Problematic turn | Evidence and fix |
|---|---|---|
| `format_mc:mc_openbookqa_7302` | “A person pours water into a cylinder in order to” → **B, observe it** | The stem supplies no purpose establishing observation over touching or tasting. Replace it with an explicit experimental task and suitable choices, or ban the stem. |
| `format_mc:mc_arc_challenge_3348` | “greatest contributor to air pollution in the United States” → **B, automobiles** | No pollutant, measurement basis, year or source is specified. The question cannot establish a unique ranking as written. Supply those conditions or ban it. |
| `mc_openbookqa_6611` (§D builder sample) | Moving toward a mirror → **A, “the head would start to grow”** | Apparent visual size is confused with physical growth. Rewrite the choice to refer explicitly to appearing larger, or ban it. |

Because demonstrations are supervised in this pass, filtering only target questions would be insufficient. Apply any repair or ban at the source-question pool level and rebuild affected conversations.

### V9-M3 — MEDIUM: published MATH answers are correct, but two explanations need repair

**Count:** **0/5 incorrect final numerical answers** found in the English MATH sample; **2/5 explanations** contain an issue, comprising one proof gap and one typographical error.

- **`math_en_math:math_train_5239`:** “\(3nr+r^2\) should be less than 1” is used without establishing the required bound on \(n\). The answer **19 is correct**. A rigorous replacement is:
  - For \(n\le18\), \((n+0.001)^3-n^3\le0.972054001<1\), so no integer \(m>n^3\) fits.
  - For \(n=19\), \((19+0.001)^3-19^3=1.083057001>1\), so \(m=19^3+1\) fits.
- **`math_en_math:math_train_3603#1`:** the interval ends with `2a+19`; it should end with **`20a+19`**. I independently checked the final count **600** using the floor-function breakpoints.

**Concrete fix:** repair these explanations while preserving their correct answers. Published provenance and label agreement should remain distinct from reasoning validation.

### V9-L1 — LOW: current summaries still contain obsolete descriptions

**Evidence includes:**

- §A says correcting v2 is absent because masked turns “are not honoured by the training path.”
- §C’s rule, the comparator docstring and `_same()` comment still describe an `equiv500` approval fallback.
- The audit docstring describes deficit-mode success primarily through coverage.
- The delta heading says “v7 → v8.1” while showing the v9 result, 11,033 approvals.

**Concrete fix:** update current summaries and comments to the final behavior. Preserve dated history and its explicit corrections. Describe masked-row exclusion as the **decision for this pass**.

## 3. What is good and should not be changed

- **The accounting reconciles.** Block rows sum to **379,670**; nominal assistant-content tokens sum to **146,356,319**. Dev accounting gives \(2667+146+17+71-559=2342\). Approval paths sum to **11,033**, plus **995** disagreements.
- **All five Greek mathematics samples have correct worked calculations and answers.** Examples include `c2_math_1550` with \(a=1\), `gm_nat_412_2#1` with four containers costing €59.20, and `c2_math5_1340#1` with guaranteed divisor 12.
- **The sampled conversation instruction handling is sound.** In `S2_00933`, all eight responses after the limit contain at most 20 whitespace-delimited words; the maximum is **19**. `S2_00325#1` maintains «Καλή συνέχεια» and stops after revocation. The recall and targeted-edit examples also preserve the requested content. This does not certify their external factual claims.
- **The approval binding, revalidation, exclusion-family handling and partition-first MC split are valuable safeguards.**
- **Preserving `target_sid` and `demo_sids` is the correct repair.** The supplied assembler retains `meta` in both train and explicit dev rows.
- **Retain the audited pretokenized path and the disclosed supervision decision.** There is no reason from this review to reintroduce masked lanes.
- **Keep the corrected deficit reporting.** The exposure count is not a faulty-label count, and the rejected 34% figure must remain explicitly superseded.

## 4. Answers to the brief’s closure and readiness questions

| Question | Answer |
|---|---|
| **Is V8-H1 closed?** | **No.** Direct numeric comparisons are improved, but normalization still bypasses the whitelist and list protections. |
| **Is V8-H2 closed?** | **Partly.** Missing requested IDs now fail, and deficit-mode extra/wrong-label checks are present. Zero-deficit acceptance remains. |
| **Does F1 now include the training path?** | **Yes, according to the supplied logs.** The real SFTTrainer’s data preparation and collation were inspected, including packing, with complete 40/40 coverage. This is stronger than validator-only inspection. |
| **What does the 40-row audit establish?** | Pretokenized train labels match the validator at **14,915 supervised positions**, with zero deficit, extra labels or wrong values. Evaluation collation of the same cohort also matches. It is not an exhaustive audit of the actual 2,342-row dev set. |
| **What remains untested operationally?** | A production 8B GPU training step with the new path, including forward/backward execution and optimization. The stand-in audit does not establish that result. |
| **Are the v8 sample exclusions and metadata fix evidenced?** | The exclusion declarations, pool bans, family-removal code and metadata-preservation code support them. I did not independently scan the final files for zero survivors. |
| **Are the token totals contradictory?** | **No.** The recipe’s 224,892,131-token estimate and trainer’s 220,096,680 rendered tokens use different methods. The rendered-length report shows zero over-window rows. Neither total is a full-manifest count of actual supervised labels. |
| **Are planned optimizer steps coherent?** | Yes: \(\lceil53,789/16\rceil=3,362\). |
| **Does the pilot justify an accuracy claim for this block?** | **No.** Worked versus terse targets scored −1.4 pp, and no arm qualified. The reported generation-behavior improvement supports a narrower rationale. The from-scratch pass requires its own interpretation and promotion decision. Completed pilots need only accurate notes. |
| **Can Gate 2 be lifted now?** | **No.** Repair H1 and H2, report the approval delta, and refresh dependent evidence before lifting the hold. |

## 5. Open questions for the owner

1. Which current solve pairs, if any, are affected by the remaining normalization routes, and what changes after all 12,028 decisions are replayed?
2. Where is the recorded decision distinguishing this from-scratch experiment from the Phase C stopped by the frozen pilot rule?
3. Which exact TRL, Transformers, tokenizer and template revisions produced the audits, and are those identical to the launch environment?
4. What production-step evidence will close the remaining GPU execution gap?