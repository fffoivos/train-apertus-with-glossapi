# Astra review: gate2_full_v7

Date 2026-09-15 13:19 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T13-13-19-01a0a48e-88ad-7660-9c9f-7f09298c79cb.jsonl) · effort xhigh · 6.6 min · prompt 197,082 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v7.md`

## 1. Verdict

**HOLD.** V7 substantially improves approval binding and supplies credible evidence that the small collator test now supervises emoji endings correctly. However, the comparator still admits unequal numeric answers through formatting-dependent fallback paths, and the larger training-label audit is not reproducible from the displayed inspection script. A previously excluded annual-cost error also survives in another conversation. This review independently checks the pasted code, sample reasoning and arithmetic; **I did not execute the original Python/TRL code, recompute file hashes, or verify cluster state.** The rates below describe the supplied samples, not the full dataset. Completed experiments receive documentation notes only.

## 2. Findings ranked by severity

### V7-H1 — HIGH: Numeric formatting still bypasses exact comparison

**Evidence:** In `agree`, exact numeric comparison applies only when **both** raw strings match `strict_num`. Otherwise, `equiv500` can strip formatting and compare the resulting numbers with floating-point tolerance.

Two deterministic counterexamples follow from the supplied code:

| Reference | Candidate answer | Result implied by the code |
|---|---|---|
| `0` | `.0000000005` | Incorrect agreement: the candidate misses `NUM`; `strip_string` adds the leading zero; `5×10⁻¹⁰ ≤ 10⁻⁹`. |
| `12345678901234567890` | `12345678901234567891\text{ cm}` | Incorrect agreement: the candidate misses `NUM`; normalization removes the unit wrapper; floating-point conversion loses the integer difference. |

These are **code-derived counterexamples, not executions of the original module**. The number of affected approved records is unknown. The reported zero decision delta does not establish their absence because both finalizations retain these fallback paths.

There is another exactness hazard: `scaleb()` and unary negation are context-sensitive Decimal operations. Long signed or scientific-notation values can round under the default precision, despite an exact `Decimal` constructor.

**Concrete fix:** Normalize explicitly permitted numeric formatting before classification, then compare numeric values exactly. If either side is numeric or number-like, prevent fallback to tolerant numeric equality. Preserve sign and exponent without context-dependent rounding. Add these cases and values exceeding 28 significant digits, re-decide all records and English joins, then regenerate approval bindings and the assembly receipt.

### V7-H2 — HIGH: The expanded label audit does not establish correctness of the new launch path

**Evidence:**

- The four-row inspection is useful: **941 collator labels versus 941 validator labels**, covering three manifest rows and one synthetic conversation.
- The displayed script reads only **`batch = next(iter(dl))`**, but computes `val_total` over **all selected rows**.
- For the 40-row audit, the packet reports **10,307 collator-supervised tokens versus 15,696 validator-supervised tokens**. Under the displayed batch size of one and 4,096-token packing limit, one batch cannot contain 10,307 supervised tokens. Either the script/configuration differed, or that output was aggregated by undisclosed code.
- The verdict itself is weak: `extra_text` accepts a supervised span whenever it contains **any** assistant message. A span containing a user prompt followed by an assistant answer would pass this test.
- Total equality is printed but not required for `OK`; a mismatch does not produce a nonzero exit.

Therefore, **the reported 34.3% deficit is not independently supportable from this script**. This does not negate the demonstrated five-token emoji defect or prove that the new training path is broken.

**Concrete fix:** Inspect every batch from the exact launch trainer/configuration. Compare token IDs and labels against the expected sequences using packing boundaries; assert that every expected assistant token is supervised and every other token is masked. Require complete ID coverage, matching totals and nonzero exit on failure. Repeat the 40-row case under the corrected path across multiple packs, and inspect evaluation batches too.

The current GPU limitation should remain explicit. A bounded production-attention smoke check can precede sustained training; “watched from step 0” alone will not detect silent label errors.

### V7-M1 — MEDIUM: The excluded annual-cost error survives in `S2_00573`

**Evidence:** `convskills_v2:S2_00573` describes scattered weekend use:

> «τα Σαββατοκύριακα … περίπου 60 ημέρες»

The assistant nevertheless prices:

> «για δύο μήνες χρήσης … 23,80 € για 60 ημέρες»

Two 30-day packages do not necessarily cover 60 usage days distributed across a year. The subsequent approximately €250 savings threshold inherits that assumption.

This is the same substantive defect excluded under `S1_00723`. It remains in **1/5 sampled conversation rows (20%)**. The sample proves one surviving occurrence; the block’s ×2 recipe implies repeated training exposure.

The same row also assumes an unstated divorce in its final answer:

> «Ναι, έχουν χωρίσει…»  
> «πληροφορίες για το διαζύγιο»

The user reported classmates asking whether the parents divorced, without confirming it.

**Concrete fix:** Repair or exclude this conversation and search **all assistant turns** for reused versions of the faulty cost comparison. Price the periods needed to cover the actual usage calendar, including equipment and applicable terms. For illustration, twelve €11.90 periods cost €142.80—not €23.80—but the correct count remains schedule-dependent. Make the divorce disclosure conditional and otherwise use neutral wording.

### V7-M2 — MEDIUM: One published MATH solution contains a false domain statement

**Evidence:** `math_en_math:math_train_4864` states:

> “Since \(x\) can be any positive integer…”

But the proposed consecutive positive integers are \(x-1,x,x+1\), requiring **\(x\ge2\)**. At \(x=1\), the first integer is zero.

The answer remains correct. Count: **1/5 published-MATH samples has this reasoning defect; 0/5 has a wrong final answer.**

**Concrete fix:** State \(x\ge2\). Every sum is divisible by three, while both six and nine occur, so the common divisor is exactly three. Apply any correction to both effective copies.

### V7-M3 — MEDIUM: Under-specified MC questions remain, including a supervised demonstration

**Evidence:**

- **`format_mc:mc_openbookqa_4358`**, first demonstration: water disappearing from a pan in one sunny afternoon does not establish that “it was the summertime.” Evaporation is possible in other seasons.
- **`mc_openbookqa_6407`**, target in §D: “while passing Jupiter” does not specify approaching or receding. “Stronger gravity” is not unconditionally determined.

Counts: **1/5 assembled MC sample rows** and **1/3 additional builder sample rows** contain these ambiguities: **2/8 supplied MC conversations**, involving **2/19 question–answer pairs**. This is an ambiguity count, not a demonstrated wrong-key rate.

Because demonstrations are supervised, their factual quality matters equally.

**Concrete fix:** Remove these stems from the pool before demonstration sampling, or rewrite them to establish the intended answer—for example, “as the spacecraft approaches Jupiter.” Record stable source-question IDs for targets and demonstrations so exclusions remain traceable after rebuilding.

### V7-M4 — MEDIUM: “Only the data changed” is now false

**Evidence:** The recipe discloses `pretokenized_masks: true`, but still concludes:

> “only the data changed.”

The new run also changes which tokens receive loss. The packet itself demonstrates a difference on the emoji fixture. Therefore, R4 versus R3 changes **both data and supervision behavior**.

Furthermore, **60,968 rows containing partial-character tokens is an exposure count**, not a measured count of rows with faulty labels. The invalidly documented 40-row calculation cannot establish the historical corpus-wide deficit.

**Concrete fix:** Describe R4 as a combined data-and-supervision change. Keep product-level comparison with the incumbent, but do not attribute gains specifically to the new datasets or format block. Label the recipe’s content-token totals as nominal assistant-content counts, distinct from actual collator-supervised counts. Add notes to completed rounds and pilots; do not rerun or alter them on this finding alone.

### V7-M5 — MEDIUM: Approval identity covers the wrapper, not the complete comparator

**Evidence:** `comparator_sha()` hashes only `labelcheck_lib.py`, while decisions also depend on `equiv500.py`. The latter is recorded in the assembly receipt, but is not bound into the approval artifact’s comparator identity.

Revalidation helps, but a dependency change that preserves existing positive decisions would not trigger the claimed comparator-identity mismatch.

**Concrete fix:** Bind both modules into a composite comparator fingerprint and verify it before selection. Include relevant numeric-context settings or eliminate context dependence. This is a remaining reproducibility weakness; I have not demonstrated a dependency mismatch in this manifest.

### V7-L1 — LOW: Several descriptions remain internally inconsistent

**Evidence:**

- The provenance exception is appropriately disclosed, but its `evidence` text still asserts that timestamps establish what the solver saw. They support consistency, not that stronger conclusion.
- §I still describes raw messages as the launch training path.
- The plan prints `assistant_only_loss: true` although the reported effective SFTConfig sets it false.
- The format receipt retains conflicting descriptions of supervision.

**Concrete fix:** Generate descriptions from effective configuration. Say historical source identity is supported by timestamp evidence but lacks request-level proof. Preserve the legacy exception and backups.

## 3. What is good and should not be changed

- **Approval revalidation is a substantial improvement.** The assembler visibly verifies the solve-file hash, manifest identities, problem fingerprints, references and agreement before selection.
- **All 15 supplied maths final answers check out:** five Greek, five English GSM and five published MATH. The domain error above does not change its final answer. This supports those sampled answers only.
- The Greek solutions correctly explain relative percentage growth, positional digit symmetry and the Euclidean algorithm.
- **Receipt arithmetic reconciles:** 379,698 training rows, 2,342 dev rows and 12,028 label decisions. The reported decision categories sum to 11,019 agreements and 1,009 disagreements.
- **Window evidence is materially better:** the supplied full-render report records zero over-window rows, with maxima of 4,032 train and 4,019 dev tokens. The distinction between the assembly estimate and rendered length is now explicit.
- Keep partition-first MC splitting, checking every user turn for overlap, and the mandatory exclusion reasons.
- Keep correcting v2, masked-context conversation rows and S5m excluded from this candidate. The trainer change does not itself justify restoring them.
- The sampled conversation rows demonstrate useful memory behavior and consistent bullet formatting after the persistent instruction.

## 4. Answers to the brief’s gate questions

| Question | Answer |
|---|---|
| **Is V6-H1 closed?** | The central solve-record/approval binding defect is addressed in the displayed code. Independent hash verification was unavailable; complete comparator dependency binding remains V7-M5. |
| **Is V6-H2 closed?** | The three named regressions are addressed, but the underlying formatting-dependent numeric bypass remains. **Not closed.** |
| **Is V6-H3 closed?** | `math_train_5181` is excluded in code and receipt, with a final survivor check. I cannot independently certify `c2_math5_155`: its complete problem and solution are not supplied here. |
| **Were the v6 content exclusions effective?** | The named exclusions and MC bans are represented in code. However, the annual-cost defect survives under `S2_00573`. |
| **F1: Which path actually trains?** | The latest configuration selects pretokenized masks, with effective `assistant_only_loss=False`. Earlier raw-path descriptions are superseded. The small collator result supports this path; broader verification remains insufficient. |
| **Is the 4,096-token window supported?** | Yes, by the supplied rendered-length report and fail-on-overflow validator. I did not rerun them. |
| **Does the pilot qualify this maths intervention?** | No. Its frozen primary criterion failed. The from-scratch run must be described as a new exploratory recipe, also incorporating a supervision change—not a pilot-qualified accuracy improvement. |
| **Is launch ready?** | **HOLD until V7-H1 and V7-H2 are resolved.** The medium and low findings remain logged under the stated disposition. |

## 5. Open questions for the owner

1. Which exact script, configuration and aggregation produced the 40-row `10,307 / 15,696` result?
2. Does the production **evaluation** dataset receive the same pretokenized assistant masks? The inspection supplies raw evaluation construction and shows no evaluation collator labels.
3. Can you supply the complete `c2_math5_155` row and source problem for independent reasoning verification?
4. Is there a mapping of reused factual answers across conversation lanes, so a correction such as `S1_00723` also reaches `S2_00573`?
5. Will the final experiment record explicitly identify both the failed-pilot override and the supervision change, alongside the frozen promotion criteria?