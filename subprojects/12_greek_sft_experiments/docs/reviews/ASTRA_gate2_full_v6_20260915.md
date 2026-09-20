# Astra review: gate2_full_v6

Date 2026-09-15 11:14 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T11-10-30-01a0a41e-15cd-7710-b213-1e9ed70ab01e.jsonl) · effort xhigh · 3.9 min · prompt 139,979 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v6.md`

## 1. Verdict

**HOLD for 1-G4F6P1.** The supplied code fixes the original V5-H1 import side effect and improves exclusions, receipt binding, and handling of unsupported masks. However, three HIGH findings remain: approval decisions are not validated against the solve records consumed during assembly; the comparator still admits demonstrably unequal answers; and one sampled published MATH solution teaches false reasoning. These are findings from the supplied code and rows. Local execution was unavailable, so I have **not** independently reproduced hashes, scanned the full manifest, or verified cluster state. The supplied receipt arithmetic reconciles. Completed pilots require notes, not regeneration.

## 2. Findings ranked by severity

### V6-H1 — HIGH: An approved ID does not establish approval of the solve record currently read

**Evidence:** In §E, the assembler loads `AGREED`, then separately reads `independent_solve.jsonl`. Construction of `_canon` checks membership in `AGREED`, but does not check the record’s current:

- `pfp` against the problem text;
- reference against the manifest;
- answer against the reference.

Nor does it verify `_ld['problem_reference_fingerprint']` against a freshly constructed manifest. The finalizer performs relevant checks, but the assembler does not establish that its inputs are the inputs that produced that finalization.

Consequently, changing a solve record after finalization leaves its ID approved. Its changed reference can become canonical during assembly. Recording both files’ current hashes in the receipt documents that combination; it does not establish its consistency.

**Observed incidence:** No stale selected record is demonstrated in the supplied sample. This is a concrete missing validation step, not a measured corpus corruption rate.

**Fix:** Make the approval artifact identify its raw solve file, problem/reference manifest, and comparator version. Verify those identities before selection. Also validate approved records against the current manifest and comparator using side-effect-free functions. Abort on mismatches; do not regenerate approvals implicitly during assembly.

**V5 disposition:** The original import-time rewrite is fixed. This remaining dependency check is distinct.

### V6-H2 — HIGH: Comparator false positives survive the “exact numbers” change

The following results follow directly from the supplied code; they are **static counterexamples, not executed tests**.

| Reference | Candidate | Result implied by current code | Defect |
|---|---|---|---|
| `0` | `+0.0000000005` | Agree | `strict_num` rejects the leading `+`; `equiv500` accepts the difference under its float tolerance. |
| `12345678901234567890` | `+12345678901234567891` | Agree | The leading `+` bypasses Decimal comparison; float conversion loses the distinguishing precision. |
| `\text{ellipse}` | `\text{hyperbola}` | Agree | `strip_string` removes both complete `\text{...}` expressions, producing two empty strings; equality returns before categorical comparison. |

The categorical example is especially clear: contradictory answers become equivalent.

The four reported numeric rescues do not audit these cases. The audit records agreements that `equiv500` would reject; these false positives are **accepted by `equiv500` itself**. An empty `exact_numeric_tightened` list therefore does not establish comparator correctness.

**Observed incidence:** These examples are not supplied solve rows. The number of affected decisions among 12,028 records remains unknown.

**Fix:** Add these regression cases. Recognize numeric syntax—including leading signs and scientific notation—before permitting fallback, and compare recognized numbers exactly. Preserve categorical text and forbid equality caused by normalization to empty strings. Recheck all existing solve records and English GSM solution joins; review changed decisions without rerunning the solver unnecessarily.

### V6-H3 — HIGH: A published MATH target contains false reasoning

**Row:** `math_en_math:math_train_5181#1`

The target says:

> “the number of prime factors … equals $(e_1+1)(e_2+1)\cdots$”

That is the count of **positive divisors**, not prime factors. It then claims every other eligible base is prime or a product of two primes. **8 = 2³** contradicts that claim.

**Count:** **1/5 sampled published English MATH rows (20%)** contains a clearly false worked argument. The final answer, **496**, is correct. This is a sample rate, not an estimate for all published solutions.

**Fix:** Quarantine `math_train_5181` and every copy until its proof is corrected. A valid short argument is:

- For each base greater than one, choose \(n=15\).
- Prime-power bases at most 15 yield at most 46 divisors, attained by \(8^{15}\).
- Bases with two distinct prime factors are 6, 10, 12, 14, and 15.
- All except 12 yield 256 divisors; \(12^{15}=2^{30}3^{15}\) yields \(31\times16=496\).

Check any proven translated twin. Preserve the correct answer and the rest of the block; published provenance alone does not certify reasoning.

### V6-M1 — MEDIUM: Backfilled fingerprints provide weaker historical evidence than the manifest claims

**Evidence:** **12,028/12,028 records—100%—were backfilled**, with zero fingerprints present beforehand.

The source mtimes preceding the solve file’s creation support the reconstruction. They do not independently prove that those exact bytes were supplied to the solver: modification times can survive copies or restoration, and the supplied hashes were collected retrospectively.

The fingerprint portion of the reported “zero stale” result is therefore true by construction immediately after backfill. The reference comparison remains a useful separate check.

**Fix:** Describe this as a **legacy provenance exception supported by file-time evidence**. Hash and preserve the untouched backup, retain the original solver version, and compare request logs where available. Require solve-time fingerprints for new records. This finding alone does not justify 12,028 new solves.

### V6-M2 — MEDIUM: Two sampled questions still permit competing readings

**English GSM row:** `math_en_gsm:1935535`

“3 times more” supports the intended gift of 36 and total of 48, but also the literal “three times additional” reading: gift 48, total 60.

**Count:** **1/5 sampled English GSM questions (20%)** has this ambiguity. The arithmetic under the intended reading is correct.

**Format builder row:** `mc_openbookqa_2469`

> “Which of these items is required for a deer to live”  
> A. sun  
> B. iron

Iron is a necessary nutrient; sunlight is the intended indirect ecological dependency. The question supplies no distinction that makes A uniquely defensible.

**Count:** **1/3 displayed format rows**, or **1/6 displayed MC question–answer pairs**, contains this ambiguity. These are builder samples; I have not independently located their launch-manifest instances.

**Fix:** Clarify the GSM wording before solving again, or exclude its problem family. Remove the deer question from the MC pool before demonstration sampling, as was done for the ecosystem question.

### V6-M3 — MEDIUM: The annual-cost example assumes consecutive usage

**Row:** `convskills_v2:S1_00723#1`

The user describes weekend use, approximately 60 days annually. The answer budgets:

> “δύο μήνες πακέτων των 25 ευρώ”

Sixty scattered usage days do not establish that two monthly packages cover the year. With the answer’s assumptions, annual cost is **€60 + €25 × active subscription months**: €110 for two months, but €360 for twelve.

**Count:** **1/5 sampled conversation rows (20%)** contains this concrete mismatch between the user’s schedule and an assistant’s calculation. The final message-count answer, `4`, is correct.

**Fix:** Calculate from package validity and the months containing visits. Preserve the conditional reliability advice and the correct recall target.

### V6-M4 — MEDIUM: Validator inspection does not fully establish training labels or the exact window limit

**Evidence:** §I displays **two rows** processed by `tokenize_messages`; neither is an actual training-collator output.

Rejecting every masked row addresses the dangerous `train:false` mismatch. However, the validator also repairs unmasked byte-token gaps within assistant spans. The supplied evidence does not show those repairs reaching the raw-message TRL training path.

Separately, the assembler’s window check uses the receipt’s **content-only tokenizer count plus eight tokens per turn**. Its total exceeds the dry-run rendered total by **4,823,724 tokens**:

- Assembly estimate: 224,968,087
- Dry-run rendered count: 220,144,363

That aggregate difference demonstrates different counting methods. It proves neither that an individual row overflows nor that every row fits.

**Fix:** Capture labels from the actual training dataset/collator, including an assistant turn ending in an emoji. Report the maximum rendered row length and explicit counts of truncated, dropped, or otherwise altered rows for the bound manifest.

### V6-L1 — LOW: Documentation still describes incompatible populations

**Evidence:**

- The assembler docstring still lists `correcting_v2 ×2`.
- §H promises five blocks, including correcting, but supplies **20 rows across four blocks**; correcting is absent.
- The format builder receipt says demonstrations are unsupervised, while the assembly receipt correctly states they are supervised.

**Fix:** Update the assembler description and sample heading. Label builder-stage and training-stage supervision separately wherever either receipt is presented.

## 3. What is good and should not be changed

- **Keep the side-effect-free library and main-guarded finalizer.** They remove the original V5-H1 mechanism.
- **Keep positive approval filtering**, mandatory exclusion reasons, problem-family exclusions, and final zero-survivor assertions.
- **Keep correcting v2 and masked conversation rows out** until the training path supports their intended labels.
- **Keep the S5m exclusion.** The reported 74/100 flawed audit supports that decision; I did not independently repeat that audit.
- **Keep partition-first MC splitting and overlap checks across every user turn.**
- **Keep explicit supervision of admitted MC demonstration letters.** That accurately describes this pass.
- All **five sampled Greek maths solutions** have correct calculations and conclusions.
- All **four explicit conversation recall/count targets** match their displayed histories.
- The supplied counts reconcile:
  - Training: 283,657 retained base rows + 96,065 new rows = **379,722**.
  - Dev: 2,667 + 146 + 18 + 70 − 560 = **2,341**.
- No sampled final numerical answer is demonstrably wrong under its intended interpretation. Preserve that distinction from false reasoning and ambiguous prompts.

## 4. Answers to the brief’s readiness questions

| Issue | Assessment |
|---|---|
| **Is original V5-H1 fixed?** | **Yes in the supplied code:** the assembler no longer imports the executing finalizer, and it checks approval-file stability. V6-H1 addresses the remaining relationship between approvals and their inputs. |
| **Is V5-M1 fixed?** | **For new solves:** shared manifest construction and solve-time fingerprints are present. Historical identity remains retrospectively supported, not independently established. |
| **Is V5-M2 fixed?** | **Partially.** Decimal comparison fixes recognized numeric strings; fallback and categorical false positives remain. |
| **Is V5-M3 fixed?** | The supplied predicate requires a nonempty matching identity, and the receipt includes exclusions and solve artifacts. I have not verified actual local/cluster equality. |
| **Are the previously identified exclusions addressed?** | The code and receipt support the requested removals, including GSM solution families and the banned MC pool item. No previously excluded row appears in the supplied sample. |
| **Does F1 establish safe supervision?** | It establishes the intended mitigation in source: no masked messages may survive. It does **not** constitute inspection of the actual training labels. |
| **Does the dry-run establish launch readiness?** | It reports the expected 379,722 rows and 3,363 planned optimizer steps. It does not resolve the HIGH findings or replace training-path inspection. |
| **Does the pilot justify the new maths block?** | It supports a behaviour-repair rationale relative to terse targets, **not a demonstrated accuracy gain**. A fresh run from the CPT base is a different experiment and should be described as an explicit re-plan. |
| **Can this pass launch?** | **Not under this review.** Resolve the three HIGH findings, regenerate affected artifacts and bindings, and review that resulting manifest. |

## 5. Open questions for the owner

1. After correcting the comparator and approval checks, **which actual IDs change disposition**, and how many effective training rows do they represent?
2. Are original solver requests or source snapshots available to strengthen the retrospective fingerprint evidence?
3. Can the owner provide a hash-bound inspection of the **actual training collator**, plus explicit rendered-length and truncation counts?
4. Which recorded decision replaces the pilot’s frozen stop rule with this fresh-base experiment, and what outcome would support its maths rationale?
5. Is English MATH retention intentionally outside the promotion guardrails despite its decline in the pilot? Also, specify the MATH improvement threshold used in criterion (4).