# Astra review: gate2_full_v5

Date 2026-09-15 10:11 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T10-06-15-01a0a3e3-45b1-73b2-b9e5-d739e72fe545.jsonl) · effort xhigh · 5.2 min · prompt 114,714 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v5.md`

## 1. Verdict

**HOLD — one HIGH assembly-integrity defect remains.** The assembler loads its approval list, then imports a module that rewrites that approval file, and finally fingerprints the rewritten file. It can therefore select rows using approvals that its receipt no longer represents. This is a verified code defect; the supplied evidence does **not** demonstrate that stale rows entered this particular manifest. The totals reconcile, the masking workaround addresses the disclosed defect for this pass, and all five Greek and five published MATH sample solutions check out. Fix the HIGH finding before further queued assembly, then regenerate and bind the resulting artifacts. Completed R3 receives notes only. This review uses the inlined evidence and manual checks; I did not execute the pipeline or inspect cluster files.

## 2. Findings ranked by severity

### V5-H1 — HIGH: Assembly can use approvals that its own finalizer subsequently revokes

**Evidence: §E and §C.**

The execution order is:

1. Load `label_disagreements.json` into `AGREED`, `BAD`, and `ld_note`.
2. Filter English GSM rows using that snapshot.
3. Execute:
   ```python
   from finalize_label_check import strict_num as _snum
   ```
4. That module has top-level execution: it detects stale records and **rewrites `label_disagreements.json`**.
5. Filter Greek rows using the **old in-memory `AGREED`**.
6. Hash the **new on-disk approval file** into the receipt.

**Concrete failure path, not an observed sample failure:** a reference changes after the previous finalization. During assembly, the import correctly marks its solve record stale in the rewritten file, but `keep_translated()` still accepts its previously approved ID. The receipt then hashes evidence that did not govern that selection.

The canonical-reference map also reads **all raw solve records**, rather than constructing references exclusively from the validated approved records.

**Concrete fix:**

- Move `strict_num` into a side-effect-free utility module; put finalizer execution behind a main guard.
- Run finalization explicitly **before** assembly.
- Load one immutable approval artifact containing the approved record identities and canonical references.
- Build the canonical map only from those approved records; reject conflicting references for the same problem.
- Record the approval hash at load time and assert it remains unchanged through receipt creation.
- Verify the failure case above: changing a reference must prevent admission of the affected family.

**Current impact count:** unknown. The reported `stale_records: []` does not establish an occurrence of this bug, but it does not repair the execution path.

### V5-M1 — MEDIUM: The claimed solve-time problem/reference binding is incomplete

**Evidence: §C.**

The solver saves `id`, `answer`, `ref`, `src`, and `level`. It saves **no problem-text fingerprint**. The finalizer computes a fingerprint from current inputs, but has no solve-time problem fingerprint against which to compare it.

For stable source IDs, changing a question while retaining its reference will therefore evade `stale_records`. For example, changing the supplied `c2_math_1171` question from `tan x = 2` to `tan x = 3` while retaining reference `-3` would leave the reference-only stale check satisfied. This is a constructed counterexample, not an allegation that this row changed.

There is a second discrepancy: the solver derives Level-5 references from `boxed(solution_en)`, while the finalizer loads the raw Level-5 record without the same derivation. Where `ref` is absent, the finalizer obtains an empty reference and its nonempty-reference condition disables stale detection.

**Concrete fix:** use one shared manifest constructor. Save a problem/reference fingerprint with every solve record and compare it during finalization. Treat missing current references as unresolved. For existing records, establish identity from preserved solve-time inputs or re-solve records whose identity cannot be established.

### V5-M2 — MEDIUM: “Strict numeric equality” still accepts unequal numbers

**Evidence: §C and §E.**

Both comparison paths use:

```python
abs(a - b) < 1e-6
```

Thus `0` and `0.0000005` pass the numeric fallback despite being unequal. Converting through `float` also loses exactness for sufficiently large integers.

The four disclosed rescues—`gsm_124`, `gsm_2836`, `gsm_3375`, and `gsm_4112`—do not exhibit this problem: their numerical components match their references.

**Concrete fix:** compare normalized finite numbers using exact decimal or rational arithmetic. Supply full-comparator checks establishing:

- `1,5` equals `1.5`;
- `1,5` does **not** equal `15`;
- `0` does **not** equal `0.0000005`.

The supplied `strict_num` maps `1,5` correctly. However, `equiv500` runs first and its implementation is absent, so the complete comma-handling claim remains unverified.

### V5-M3 — MEDIUM: Launch binding permits an empty receipt identity; exclusion provenance remains incomplete

**Evidence: §F and §B.**

The launch predicate explicitly accepts an empty receipt hash:

```sh
[ -z "$RS" -o "$RS" = "$LS" ]
```

That is weaker than the claimed requirement that cluster code and config match receipt identities. The current receipt contains both identities; **no actual mismatch is shown**.

Separately:

- `exclude_rows_r4.json` is optional: absence silently produces an empty exclusion set.
- Neither the exclusion list nor its reasons file appears among receipt identities.
- The raw `independent_solve.jsonl`, read to construct canonical references, is also absent.
- Aggregate exclusion counts do not identify which rows were removed.

**Concrete fix:** require exactly one valid receipt digest for each required launch artifact and require all three hashes to agree. Make the reviewed exclusion list mandatory and fingerprint it and its reasons. Emit explicit zero-survivor checks for the named exclusions, including copies and English problem-family equivalents.

### V5-M4 — MEDIUM: Two sampled source questions do not support a unique target as written

**Evidence and countable sample rates:**

| Row | Defect | Observed sample rate |
|---|---|---:|
| `math_en_gsm:353716#1` | “Her family ate 2/3 pieces.” The solution silently changes this to two thirds **of the 12 pieces**. That intended reading gives 4; the literal numerical reading leaves \(12-2/3=11⅓\). | **1/5 GSM rows: 20%** under-specified |
| `mc_openbookqa_5631`, first demonstration | “If something is in an ecosystem, it could be…” permits both **A. invisible** and **C. lacking life**. The supervised target is C. | **1/7 displayed MC answers: 14.3%**; **1/3 format rows affected** |

These are question defects, not demonstrated arithmetic mistakes. These small supplied samples do not estimate population prevalence.

**Concrete fix:** clarify the GSM wording and revalidate its family against the amended problem. Remove or rewrite the ambiguous MC question in the source pool, then rebuild every target or demonstration occurrence. Removing only the displayed conversation would miss other uses of the same question.

### V5-L1 — LOW: The satellite-phone instructions do not adequately match the stated English interface

**Evidence:** `convskills_v2:S3c_00357#1`.

The user explicitly says the menu is English, but the navigation path uses only Greek labels:

> «Μενού» → «Ρυθμίσεις» → «Τηλέφωνο/Ρυθμίσεις τηλεφώνου» → «Γλώσσα»

The English equivalents are supplied for the settings to avoid, but not for the main navigation path. This affects **1/5 sampled conversation rows**.

**Concrete fix:** provide paired English/Greek labels and retain the model-dependent qualification. The later request to remove the exact word «επαναφορά» is satisfied; «επαναφέρεις» is a different word, so I do not count that as a failure.

### V5-L2 — LOW: Some descriptions still describe superseded training behavior

**Evidence:**

- §A says “correcting v1 → v2”; the actual pass contains **no correcting block**.
- §D describes final-letter-only supervision; the assembled format block supervises demonstrations too.
- §I’s heading about labels before packing can still imply that the validator’s labels reach training, despite the explicitly acknowledged raw-message path.

**Concrete fix:** distinguish source-format metadata from final-manifest behavior and update the recipe summary. Preserve the historical defect notes.

## 3. What is good and should not be changed

**The arithmetic and assembly accounting now reconcile.**

- R3: **403,727 rows; 151,912,798 supervised tokens**.
- R4: **379,724 rows; 146,408,349 supervised tokens**.
- New-block effective rows plus the retained base reproduce the R4 total.
- Dev accounting reconciles: **2,667 + 146 + 18 + 71 − 560 = 2,342**.
- The suite has **18 dev rows before overlap filtering and zero afterward**, as disclosed.

**The following sample checks passed:**

| Sample | Verified result |
|---|---|
| Greek maths, 5 rows | **0/5 mathematical failures found.** `gm_nat_1060_1#1`: 6; `gm_nat_979_1#1`: 850 and 1,000; `c2_math_1171`: −3; `c2_math5_760`: 4/11; `gm_nat_916_4`: 10. |
| Published MATH, 5 rows | **0/5 false derivations found.** `math_train_4192#1`: \(3-i\); `848#1`: 19,440; `1000#1`: 8; `5123#1`: 6; `6065`: 11. |
| Conversation memory targets | **4/4 correct:** `S1_00330`, `S1_00390`, `S1_00317#1`, `S1_00061`. The verbatim retrievals, message count, and ordered summary match their contexts. |

Also preserve:

- Dropping correcting v2 and masked-context suite rows for this pass.
- Explicitly supervising format demonstrations and asserting that no `train:false` remains.
- Canonical-reference and boxed-answer checks in place of last-number extraction.
- Explicit mathematics dev-family exclusion and overlap checks across all user turns.
- Honest separation of blind label agreement, derivation review, and exempt sources.

The reported **1,009/12,028 disagreements (8.39%)** are disagreement counts, not a verified source-label error rate.

## 4. Answers to the gate questions

| Question | Answer |
|---|---|
| **Is V4-H1 closed?** | The row-label and boxed-answer comparisons are implemented. Approval/reference provenance still has V5-H1, and full comma behavior is not demonstrated. `en_gsm_no_canonical_ref` is omitted rather than explicitly recorded as zero. |
| **Is V4-H2 closed?** | The receipt reports 2 Greek and 3 English reviewer exclusions, consistent with targeted filtering. The excluded IDs/reasons and deference-screen results are not inlined, so removal of the specific family is not independently established. I found **0/5** deference instances in the Greek sample. |
| **Is V4-H3 closed?** | Two published MATH exclusions are counted, but their identities are not shown in the exclusion artifact. The current five published solutions pass. Broader derivation correctness remains unverified, as disclosed; author provenance does not establish it. |
| **Is V4-M1 closed?** | **Yes, for internal accounting:** both tables’ row and supervised-token sums match their totals. |
| **Is V4-M2 closed?** | **Partially.** Reference-change detection and code/config hashes exist, with the limitations in V5-H1 and V5-M1/M3. |
| **Is V4-M3 closed?** | **Yes, as disclosure/accounting.** Suite dev coverage is zero after filtering; dev loss cannot validate that block’s behavior. |
| **Does the masking workaround address this pass?** | **Yes at the manifest level**, based on the code and inspection supplied. It does not fix the trainer. The separate trainer repair still requires the planned real-run verification. |
| **Does the dry run establish window compliance?** | **Yes, under the stated validator contract:** it renders every row and rejects overlength rows. The exact **220,143,431** tokens differ from the receipt’s approximate **224,966,439**; that difference alone is not a truncation failure. |
| **Does the pilot justify an accuracy-improvement claim?** | **No.** The worked-versus-terse primary result was −1.4 pp and did not qualify. The evidence supports improved loop/truncation behavior relative to terse targets. This from-scratch pass remains a new experiment requiring its own results. |

## 5. Open questions for the owner

1. Can you provide the named exclusion entries and zero-survivor results for `c2_gsm_2544`, its English family, `math_train_4407`, and `math_train_2954`, plus the deference-screen scope and counts?
2. What preserved solve-time evidence binds stable problem IDs to the exact questions solved? How many Level-5 records lack an explicit `ref`?
3. After fixing V5-H1, do the approval hash loaded by assembly, receipt hash, and launch-bound artifacts agree, with no evidence file rewritten during assembly?
4. Where is the owner’s explicit re-plan recorded following the pilot’s frozen stop rule, and what claim is the retained Greek maths block intended to test?
5. What are the concrete completion artifacts for the scheduled published-MATH derivation QA and trainer-mask verification?