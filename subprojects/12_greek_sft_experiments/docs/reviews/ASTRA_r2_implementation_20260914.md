# Astra review: r2_implementation (recovered)

Date 2026-09-14 11:54 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T11-47-49-01a09f19-e644-7781-acfb-53c4f52bdf99.jsonl, 6 model records, all gpt-6-astra) · effort xhigh · brief `docs/reviews/briefs/astra_r2_implementation_inlined.md` (13 source files inlined, 98,814 chars). The wrapper's model assertion failed only because it picked the newest rollout (a concurrent Sol call); fixed in review_astra.py (marker-based lookup).

## 1. Verdict

**R2 should not pass the implementation gate yet.** The paired construction and solution-hash binding are substantially improved, but the supplied code contains one definite syntax blocker and several paths that can export incomplete data, ignore adverse review results, or produce a decision inconsistent with §4. The six original defects are therefore not all fixed. This is a static review of the **13 supplied files**: no dataset rows, execution logs, manifests, or receipts were supplied, so **no observed row failure rate or affected row IDs can be established**. Numerical counterexamples below are constructed examples, not dataset measurements. Recommendations concern queued work; they do not request changes to completed datasets.

## 2. Findings, ranked by severity

### B1 — BLOCKER: the correcting-v2 builder cannot parse

**Evidence:** `data/robustness/correcting/v2/build_v2.py:27`.

The inline `#` comments out the second filename, closing parenthesis, and colon. The supplied statement therefore has an unclosed `(` and cannot execute. Neither the revised 32-row input nor the 60-row input is loaded.

**Fix:** Put both paths in a properly closed tuple, with the comment on its own line:

```python
for p in (
    f'{A}/balanced_dialogue_pilot/revision2/scope_revision_train32/candidate_rows.jsonl',
    f'{A}/dialogue_scale60/accepted_train60/candidate_rows.jsonl',
):
```

Compile-check the file and require the expected input IDs from both sources before publishing `rows_v2.jsonl`. Merely changing the pathname has not fixed original defect 4.

### H1 — HIGH: both chains continue after failures and can report completion

**Evidence:**

- `cluster/drivers/cut2_after_solutions.sh:1` enables only `set -u`.
- Lines **5–18** log failures and continue through validation, repair, polish, and assembly. Line **18** prints `CUT2_CHAIN_DONE` regardless of assembly status.
- Waiting for hardcoded PIDs to disappear at line **4**, or for `pgrep` to find nothing at line **13**, does not establish successful completion.
- `cluster/pilot_chain.sh:31–33,45–49` does not enforce successful completion of every evaluation, scoring, adjudication, and summary command.
- At line **31**, the background subshell finishes with an `echo`, masking the evaluation command’s exit status. At line **49**, the summary pipeline can fail upstream while `tee` succeeds, followed by `PILOT_CHAIN_DONE`.

**Consequence:** A failed mandatory stage does not stop either chain. Existing filenames permit stale artifacts to remain available. Cut-2 assembly can also publish a reduced cohort: missing fidelity, solutions, validity, or polish are row exclusions, rather than an incomplete-stage failure (`assemble_cut2.py:54–64`).

The per-row guards prevent some unreviewed exports; they do **not** certify that the intended generation/review stages finished.

**Fix:** Propagate command failures, explicitly check every background PID’s status, and require completion receipts covering the expected candidate IDs. Publish final artifacts atomically only after those checks. Completion markers must mean success, and downstream consumers must require the matching completion receipt.

### H2 — HIGH: the launch path does not enforce the final pairing and length guarantees

**Evidence:**

- There is **no invocation of `check_pilot_arms.py` anywhere in `cluster/pilot_chain.sh:1–50`**.
- Each arm is submitted immediately after its own dry run (`pilot_chain.sh:15–21`). M0 can already be submitted when M1 or M2 fails validation.
- `assemble_continuation.py:40–42` still falls back to approximate `words*1.7` counts.
- Replay rows bypass length checks altogether (`assemble_continuation.py:66–68`).
- `assemble_cut2.py:92` and `mixlib.py:35` count separately tokenized contents plus fixed overhead. This is not demonstrated to equal the trainer’s rendered sequence length.
- The launcher checks only the dry-run exit status (`pilot_chain.sh:18–19`). The trainer implementation was not supplied, so successful exit cannot be verified to mean “zero dropped or truncated rows.”

The checker itself also has weaker guarantees than its descriptions suggest:

- Greek prompts and replay/English IDs are compared as **sets**, losing multiplicity (`check_pilot_arms.py:19–20,26–34`).
- M1 being equal to M2 passes the subset check (`:29`).
- Empty shared blocks can pass.
- Dev overlap is printed, not asserted (`:35–36`).

**Fix:** Validate all three arms before submitting any job. Require the exact trainer rendering/tokenizer, remove the continuation fallback, check replay lengths, and reject any trainer-side truncation or filtering that changes the approved manifests. Invoke the final checker as a mandatory launch prerequisite. Compare canonical problem identities and multiplicities; require M2’s additions to be the intended Level-5 rows.

### H3 — HIGH: shared dev assignment can be discarded downstream

**Evidence:** `data/assemble_continuation.py:80–87`.

The assembler decides whether an upstream split exists by checking whether **any surviving row is dev**:

```python
if flagged:
    ...
else:
    rng.shuffle(taken)
    ...
```

If contamination filtering removes all flagged rows, it silently creates a new random split.

**Constructed counterexample:** A block contains 100 rows, including one upstream dev row. That dev row is filtered out. The remaining 99 rows now receive a newly sampled dev row. If M2 retains a Level-5 dev flag, M2 follows the other branch and can retain that shared problem in training. M0=M1 and M1⊆M2 can still pass.

Additional gaps:

- English twin handling is optional: `--dev-problems` defaults to empty (`:13–14`). No supplied assembly command proves it is passed.
- The train/dev assertion compares raw IDs (`:100`), which cannot detect the same problem appearing under Greek and English IDs.
- `check_pilot_arms.py:35–36` does not enforce the promised shared dev split.

**Fix:** Represent “split supplied upstream” explicitly, independently of whether any dev rows survive. Never resplit an upstream-assigned block. Require the English family mapping for pilots and assert train/dev separation using canonical problem identities across languages and arms.

### H4 — HIGH: decontamination fails open when caches are absent or incomplete

**Evidence:**

- `data/mixlib.py:14–21`: an empty cache glob produces an empty decontamination index without error.
- `data/assemble_continuation.py:22–29`: same behavior.
- `data/math/cut2/assemble_cut2.py:12,35–36`: a missing MATH-500 cache becomes an empty list.
- `data/check_pilot_arms.py:11–14`: missing MATH-500 or confirmation caches are explicitly skipped.

Thus, **zero loaded benchmark rows can produce zero reported hits and a successful check**. Tokenizer availability fails closed in the pass assembler; benchmark-cache availability does not.

The supplied chains also do not establish the claimed dependency “confirmation cache completed before pilot assembly.”

**Fix:** Require named benchmark caches with verified IDs, language coverage, counts, and hashes. Make their successful construction a prerequisite for assembly and checking. Record the cache identities in each manifest receipt and reject missing or mismatched caches.

### H5 — HIGH: the readout can advance an ineligible arm and recommends an action inconsistent with the hierarchy

**Evidence:** `data/pilot_summary.py`.

Four concrete gaps remain:

1. **Truncation breaches never affect eligibility.** Truncations are printed at lines **45–48**, but eligibility at **63–75** checks only IFEval, MGSM, and loops. An arm with any increase in truncations can therefore advance if the other checks pass.
2. **Missing English MATH-500 results do not prevent advancement.** `score()` returns `None` for missing files (`:9`); the table says “missing,” but advancement uses Greek scores and the other guardrails (`:76–87`).
3. **Exactly 500 IDs is not independently enforced.** `EXPECTED` is whatever set occurs in the local benchmark file (`:7,11`). A defective 499-ID reference file would make 499 IDs acceptable.
4. **A negative primary contrast does not suppress the secondary dose recommendation.** Every adjacent contrast receives an independent action at line **84**.

For the fourth issue, consider a **constructed** 500-item result:

- M0: 150 correct.
- M1: 145 correct.
- M2: 150 correct.
- All guardrails pass.

The primary contrast is negative, requiring the §4 stop/replan action. Nevertheless, the script prints **“M2 vs M1: positive but inconclusive -> dose check.”**

Additionally, loops use a hardcoded **+5** allowance (`:74`). The supplied §4 does not establish that number as the frozen panel noise band.

**Fix:** Validate the complete required readout before choosing an arm. Enforce truncation and loop tolerances from the frozen panel specification, require the canonical 500 IDs for both languages, and implement one hierarchical action decision. A negative primary outcome must produce the stop/replan action without recommending a secondary dose check. Validate arm identities/order rather than treating arbitrary CLI order as the experiment hierarchy.

### H6 — HIGH: high-audit fidelity failures are ignored during export

**Evidence:**

- `run_batches.py:118–122` writes `fidelity_audit_passes.jsonl`.
- `assemble_cut2.py:17–23` reads only the sample, all-row screening, and adjudication files.
- **There are zero reads of the audit output in assembly.**
- The driver runs adjudication **before** the pass audit (`cut2_after_solutions.sh:6–7`).

Therefore, a medium-pass row subsequently flagged by the high audit can remain `faithful=True` in assembly and export if its other checks pass.

The audit’s reported rate also lacks a controlled denominator:

- Sampling uses the current file-order list, without deduplicating or freezing IDs (`run_batches.py:119–120`).
- The reported denominator is every persisted audit record, not the current selected sample (`:122`).
- There is no requirement that every sampled row has a successful result.
- The audit uses the first-stage fidelity prompt (`:26–29`), which differs from the accepted mathematical-fidelity adjudication rule (`:47–52`).

**Fix:** Freeze distinct sampled IDs and input hashes; require complete results for that sample. Route audit flags through the accepted mathematical-fidelity adjudication and hold those rows out until resolved. Compute the missed-defect rate on the frozen sample under that same definition, excluding unrelated persisted records from the denominator.

### H7 — HIGH: MATH-200 can successfully finalize with fewer or more than 200 rows

**Evidence:** `data/benchmarks_el/math200_confirm/build.py:33–40,48–62`.

The completeness check at line **39** occurs **before** filtering failed translation checks at line **40**. There is no final equality/count assertion before writing the benchmark and cache.

Two **constructed** cases follow directly:

- 200 distinct translated IDs, one failed span/number check → **199 final rows**, successful exit.
- 200 distinct IDs plus one duplicate persisted record, all checks passing → **201 final rows**, successful exit.

The “frozen IDs” are also recomputed from the current source snapshot and seed on every invocation (`:13,33–38`); no persisted frozen selection is required. The receipt’s `final_by_level_meets_quota` field stores counts rather than enforcing quotas (`:62`).

**Fix:** Persist the selection once with source identities/hashes. After all checks and polish, require exactly that ID set, exactly one record per ID, exactly 200 rows, and the specified level counts. Repair/retry the same failed IDs rather than silently dropping them. Publish benchmark, cache, and receipt together only after validation.

### H8 — HIGH: derivation validity does not cover the edited solution actually exported

**Evidence:**

- `assemble_cut2.py:60–62` verifies validity against the original generated solution hash.
- Lines **63–65** can replace that solution with polished text.
- Subsequent checks cover boxing, length, and repeated lines—not derivation validity.
- `polish_targets.py:26–27` protects LaTeX regions, numbers, boxes, and approximate line count.

Those guards do not protect mathematical statements expressed in Greek prose. For example, a **synthetic** edit from “η λύση είναι μοναδική” to “η λύση δεν είναι μοναδική” can preserve every protected region and number.

This is a reachable gap, **not an observed bad edit**.

**Fix:** Revalidate edited final targets against the problem/reference, keyed to the final text hash. Unchanged and reverted targets can retain their existing validity result. Export metadata should identify the validity record covering the exact exported assistant text.

### M1 — MEDIUM: MATH-500 adjudication filenames and IDs match, but cached decisions are not response-bound

**Evidence:** `adjudicate_unresolved.py:9–18`; `pilot_summary.py:12–17`.

Both scripts correctly use `math500_el_adjudicated.jsonl` and plain benchmark IDs. There is **no fresh-run key-format mismatch**.

However, the reader accepts an existing `equivalent=True` record solely by ID whenever the current score is unresolved. It does not verify that the adjudication evaluated the current response or reference.

**Fix:** Bind adjudications to response, reference, and judging-protocol hashes and verify them when loading. This affects the secondary reported accuracy; primary `equiv500` decisions remain separate.

### M2 — MEDIUM: the Level-5 length-drop counter is mathematically wrong

**Evidence:** `assemble_cut2.py:98`.

`Counter.update()` adds its argument to the existing count. Passing `existing + 1` produces the recurrence:

\[
c_{n+1}=2c_n+1
\]

Consequently, **three actual drops report seven**; ten report 1,023. Filtering itself still removes those rows.

Also, `stage_counts[*:kept]` is incremented before token-length exclusions (`:77,84`), so it does not mean final retained rows.

**Fix:** Use a normal loop with `reasons['level5_too_long'] += 1`. Distinguish pre-length acceptance from final retained counts in the receipt.

### M3 — MEDIUM: required diagnostic reporting remains incomplete

**Evidence:** `pilot_summary.py:45–58,89–91`.

The summary does not report extraction-failure counts, despite §4 explicitly requiring them. Guardrail paired intervals are not calculated or reported; saying “paired uncertainty applies” is not an interval. The format-gate result is also absent from the summary.

**Fix:** Report extracted/unresolved counts, adjudication coverage and outcomes, the format-gate result, and the prescribed guardrail uncertainty. These should be available before interpreting the decision.

### L1 — LOW: missing-tokenizer failure raises the wrong exception

**Evidence:** `mixlib.py:32–34`.

The deferred `ntok()` function references the exception variable `e`, which Python clears after leaving the `except` block. Calling it later raises `NameError` rather than the intended explanatory `SystemExit`.

**Fix:** Capture the exception name in a persistent variable or default argument. This remains fail-closed, so it is a diagnostic defect rather than unsafe export.

## 3. What is good and should not be changed

- **The current M0/M1 `zip` is safe.** Both lists start together, append together at `assemble_cut2.py:84`, and are retained together at `:94–97`. No supplied mutation breaks alignment. Moving the assertion before filtering and writing would improve defensive checking, but there is no demonstrated current pairing bug.
- **Hash-bound cut-2 polish correctly prevents obsolete-text resurrection.** Validation, polish selection, and assembly use the same `pid|sha8(solution)` convention. Missing or failed polish dispositions cannot export a translated cut-2 target.
- **The 400-word flag and 1,000-word runaway exclusion implement the stated change.** The former is diagnostic rather than an exclusion.
- **The pass assembler now checks historical training rows and new blocks**, and preserves assistant `train:false` masks.
- **The primary scorer remains deterministic `equiv500`; Sol adjudication is secondary.** The 4,000-resample, seed-1 paired bootstrap and the requirement that M1 qualify before M2 can advance are implemented correctly for the intended arm order.
- **MATH-200 now reloads persisted translations and blocks explicitly missing/failed polish.** Preserve those improvements while fixing final membership validation.

## 4. Answers to the specific review questions

| Original defect | Re-review result |
|---|---|
| **1. Pair exclusions and shared dev split** | **Partially fixed.** Upstream lockstep exclusion and paired dev flags are correct. Downstream fallback splitting, optional English mapping, incomplete final assertions, and launch enforcement remain defective. |
| **2. Contamination and exact-length checks** | **Partially fixed.** Pass-training inputs receive checks. Cache availability fails open; continuation still permits approximate tokenization and unchecked replay lengths. Exact trainer behavior was not supplied. |
| **3. Stale/missing polish and hidden 600-word cap** | **Fixed as specifically described.** Keys match, dispositions are required, and thresholds changed correctly. Final edited-text validity remains a separate gap. |
| **4. Correcting input and XSTest prompt file** | **Not verified as fixed.** Correcting is syntactically broken. The XSTest `judge.py` source was not included, so its claimed change cannot be verified. |
| **5. Complete readout, guardrails, adjudication** | **Partially fixed.** Present score files must match the loaded reference set; some guardrails are enforced; adjudication wiring matches. Missing files, truncation enforcement, exact-500 validation, and hierarchical actions remain incomplete. |
| **6. MATH-200 resume and polish failures** | **Partially fixed.** Persisted reload and failure detection work in the supplied logic. Final membership, uniqueness, quotas, and persistent freezing are not enforced. |

**Can stages be skipped or unreviewed rows exported?** Yes: chain failures do not stop downstream work; incomplete stages can yield reduced exports; audit-flagged rows are not consumed by the export gate. Missing validity or polish does correctly exclude individual translated rows.

**Is the readout consistent with §4?** Only partly. Its numerical qualification rule and M2 advancement dependency match. Its completeness requirements, truncation eligibility, and primary-negative action do not.

## 5. Open questions for the owner

1. Is the deployed correcting builder identical to the supplied line 27, and where is the missing XSTest judge source?
2. What does `bench_lib.run_jobs` do with persisted `status='failed'` records, duplicate IDs, worker failures, and changed input content?
3. Does trainer `--dry-run` fail on every dropped/truncated row? Please provide its implementation and the commands that assemble the pilots, including `--dev-problems`.
4. Where are the frozen benchmark-ID manifests, panel definition, and noise-band value supporting the hardcoded `+5`?
5. Which completion receipts prevent queued consumers from using first-pass, partial, or stale artifacts while generation is still running?