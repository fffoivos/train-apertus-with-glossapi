# Astra review: gate1_pilots_v2

Date 2026-09-14 18:42 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T18-35-47-01a0a08f-67f9-7c42-b5bb-3e64f8abc6a7.jsonl) · effort xhigh · 7.0 min · prompt 46,813 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate1_pilots_v2.md`

1) **Verdict.** **HOLD remains for R3b because the readout implementation does not fully enforce the frozen completeness rule.** The supplied receipts close the dry-run, budget, validation-coverage, replay and arm-pairing concerns at the documentary level. Both prompt ambiguities are repaired. §J actually contains **nine** complete rows; I found **0/9 incorrect final answers**, plus one formatting defect. The remaining blocker requires a focused readout patch and fixtures, not dataset regeneration. This review used the inlined text and static code inspection; I did not rerun the scripts or independently recompute the exported hashes.

2) **Findings, ranked by severity.**

**BLOCKER — §G can advance an arm with an incomplete or invalid guardrail readout.**

Three reachable paths remain:

- **Missing M0 English scores:** candidate eligibility checks `S[a]` and `E[a]`, but never requires `E[M0]`. With a qualifying Greek primary contrast and otherwise passing guardrails, deleting M0’s English score file can still produce **“advancing arm: M1.”** This violates §F’s missing-readout prohibition.
- **Empty or partial loop-response files:** `loops()` checks file existence, then counts lines without checking IDs or coverage. An existing empty `bench_M1/math500_el.jsonl` returns **0 loops**. A complete 500-item score file can therefore coexist with an incomplete loop readout that passes the gate. The exact-ID check in `score()` does not protect this separate file.
- **Nonfinite guardrail scores:** `num()` accepts nonfinite floats. If a metric parses as NaN, comparisons such as `pp(gi, g0['ifeval']) < -2` are false, allowing an invalid measurement to escape both the missing-value and breach checks.

These are **static counterexamples, not observed pilot outcomes**. The **2/2 supplied fixture cases** produce their intended outcomes, but neither exercises these paths.

**Concrete fix:** require the necessary baseline and candidate readouts before deciding eligibility; validate loop-response files against the same 500 unique frozen IDs and bind them to the scored responses; reject nonfinite/out-of-range guardrail values and normalize units explicitly. Add fixtures for missing M0 English scores, empty/partial/duplicate-ID response files, invalid scalar metrics, a valid advancement, and a negative primary with a strong secondary. All incomplete-readout fixtures must yield no advancement.

**MEDIUM — Intermediate verdicts contradict the final action hierarchy.**

In supplied **fixture A**, the secondary contrast table says **“positive but inconclusive -> dose check”**, while the final decision correctly says the secondary is not evaluated for action. Separately, a negative secondary returns **“stop Phase C”** from `outcome()`, although the final selection can correctly retain a qualified M1.

**Concrete fix:** make contrast tables descriptive—gain and uncertainty only—and emit action recommendations exclusively after guardrail and hierarchy evaluation. A negative secondary should reject M2’s additional contribution while preserving the qualified primary recommendation.

**MEDIUM — Several promised reporting outputs are absent or inconsistent.**

- §F promises **paired guardrail intervals**. §G prints fixed, approximate **unpaired standard errors**, without measured intervals.
- The adjudication coverage f-string contains escaped braces, so it prints the dictionary-comprehension expression literally instead of its values.
- §K promises the exposed item’s paired status, but the shown script contains no implementation of that annotation.
- The claim that differences between stage 1 and another checkpoint establish “run-to-run noise” is unsupported. Those differences can reflect changed model behavior. Additionally, fixture A shows **27 loops**, versus the hardcoded stage-1 reference’s **23**, despite being described as using stage-1 prediction files.

**Concrete fix:** align the reporting specification and implementation; print actual adjudication coverage; implement the exposed-item annotation; describe the five-item band as a frozen screening tolerance without claiming an empirical noise estimate. Reconcile the 23/27 loop counts. These are logged reporting issues, not additional reasons to rebuild data.

**LOW — One supplied prompt has apparent escape corruption.**

In `c2_math5_746`, the prompt contains `$	riangle ABC$`: a tab followed by `riangle`, where `\triangle` is expected. That is **1/9 complete inline rows (11.1%)** with this formatting defect. Its mathematical target, **11**, is correct. This selected sample does not establish a dataset-wide rate.

**Concrete fix:** inspect the stored export for this exact character sequence. If confirmed, repair the serialization/source string and refresh the affected validation/hash records. The inline evidence alone cannot establish whether the corruption occurred in storage or while preparing this pack.

3) **What is good and should not be changed.**

- Preserve the attested paired comparison: M0/M1 matching prompts and IDs, M1 retained in M2, and identical replay/English blocks. Correcting the replay description does not justify changing that recipe.
- Preserve the primary-first hierarchy, the ≥3 pp requirement plus positive bootstrap lower bound, and deterministic `equiv500` as the primary scorer. Response-bound adjudication is appropriately secondary.
- Preserve the explicit distinction between screening tolerances and established retention.
- Preserve both repaired prompt domains: `"από τα 26 γράμματα του λατινικού αλφαβήτου"` in `math5_269` and `"θετικό πολλαπλάσιο του 15"` in `math5_946`.
- Preserve the distinction between pairing/availability exclusions and mathematical failures.

The complete targets in §J check out:

| Row ID | Verified final result |
|---|---:|
| `c2_math_2469` | \((1-\sqrt{65})/4\) |
| `c2_math_1762` | \(220\) |
| `c1b_math_672` | \(6\) |
| `c2_math5_442` | \(1\) |
| `c2_math5_1123` | \(3\) |
| `c2_math5_1152` | \(8/9\) |
| `c2_math5_946` | \(255\) |
| `c2_math5_1181` | \(8/21\) |
| `c2_math5_746` | \(11\) |

In particular, `c2_math5_442` supplies a working existence construction, and `c2_math5_946` establishes minimality rather than merely exhibiting 255. This is **0/9 detected final-answer failures**, not a population accuracy estimate.

4) **Answers to the closure questions in the brief.**

| HOLD item | Assessment |
|---|---|
| **§A: trainer dry-runs** | **Closed on supplied logs.** All three report success. With effective batch 16, \(\lceil7332/16\rceil=459\), \(\lceil7653/16\rceil=479\), and \(\lceil7875/16\rceil=493\), matching the plans. Use these trainer step counts rather than §E’s approximate estimates. |
| **§B: budget preflight** | **Closed on supplied receipt.** CHF 193.44 is below CHF 230 by **CHF 36.56**. Runtime expenditure remains projected. |
| **§C: validity coverage** | **Closed as a coverage finding.** All **12/12 displayed ledger entries** report high effort, validity present and valid, and no problems—including edited rows `c2_gsm_43` and `c2_gsm_48`. Both the polish counts and severity counts sum to **10,306**. The full-coverage claim is receipt-supported; validator correctness across all rows is not independently verified. `"none"` means no severity issue, not no validation. |
| **§D: replay contradiction** | **Closed.** The withdrawn figure is replaced by a consistent receipt convention: 16.33M replay tokens and arm-specific shares of approximately 57.2%, 53.9% and 52.1%. |
| **§E: byte attestation** | **Closed at receipt level.** The supplied checker reports zero mismatches across **14,038 pairs**, matching 13,898 training plus 140 dev Greek rows, alongside shared-block checks. I cannot independently recompute the manifests from this pack. |
| **§F: frozen decision rule** | **Closed as a decision specification**, subject to the logged reporting corrections. Its implementation remains open under §G. |
| **§G: readout and fixtures** | **Not closed.** Both supplied cases behave as intended, but the blocker above permits advancement through other incomplete-readout paths. |
| **§H: two Level-5 ambiguities** | **Closed for prompt meaning, 2/2.** The supplied English sources support the ambiguity diagnosis. The repaired `math5_269` implies \(26^3=17,576\); its target is not shown here. The repaired `math5_946` and its shown target agree on 255. |
| **§I: drops and GSM slots** | **Closed for the stated interpretation and arithmetic.** `no_cut1_pair` accounts for **743 availability exclusions**, not 743 demonstrated quality failures. GSM slots reconcile: \(7390×3+14×2+13=22,211\). Repeated-line drops total **17**. |
| **§J: clipped excerpts** | **Closed for visibility.** Nine complete rows are supplied, with the answer checks and formatting note above. |
| **§K: inherited exposure** | Keep the frozen primary analysis and completed-parent disposition. The promised item-level annotation remains to be implemented; this does not justify retroactive dataset action. |

5) **Open questions for the owner.**

- Were the raw responses altered in fixture A? If they were copied unchanged from stage 1, what explains **27 loops versus the reference’s 23**?
- Which exact MATH-500 item is the inherited exposure in §K, and where will its per-arm correctness status appear?
- Are the **8,930 paired problems**, **10,306 translated exports**, and arm-assembly counts measured at the same stage? If so, explain the five-row difference: \(10,306-8,930=1,376\), while M2 adds \(1,358+13=1,371\) Greek training-plus-dev rows. This is an unresolved accounting question, not evidence that five rows are defective.