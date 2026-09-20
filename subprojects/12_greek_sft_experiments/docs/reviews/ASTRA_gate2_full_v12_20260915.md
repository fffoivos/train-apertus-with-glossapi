# Astra review: gate2_full_v12

Date 2026-09-15 17:31 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T17-27-09-01a0a576-ebb4-7e50-b577-c317544bf078.jsonl) · effort xhigh · 4.6 min · prompt 271,777 chars · limit deltas {('codex', '10080'): 1.0} · brief `docs/reviews/briefs/astra_gate2_full_v12.md`

## 1. Verdict

**HOLD on V12-H1: the approval comparator still has a reproducible-by-inspection false-positive path, accepting opposite arrows as equivalent.** The specific v11 case-folding defect is fixed, and the supplied training-path audits support closing F1 for the tested cohorts. Receipt arithmetic reconciles. In §H, I found **no wrong final answer among 15 maths rows**, but one defective published explanation; **3 clearly under-specified MC items among 20 supervised question–answer pairs**, affecting **3/5 format rows**; and an unsupported personal assertion in **1/5 conversation rows**. These are sample counts, not population estimates. This review uses the supplied code, rows and logs: local execution and browsing were unavailable, so I did not independently recompute file hashes, execute Python, or verify current legal sources. Only the HIGH finding below gates the queued pass; MEDIUM/LOW findings are notes under your stated disposition.

## 2. Findings ranked by severity

### V12-H1 — HIGH: structural normalization equates opposite arrows

**Evidence:** In §C, both `canon()` and `_norm()` contain:

```python
t.replace('\\left', '').replace('\\right', '')
```

These are substring replacements, so:

| Input | Result after replacement |
|---|---|
| `\leftarrow` | `arrow` |
| `\rightarrow` | `arrow` |

Tracing the supplied implementation, this call necessarily reaches structural identity and accepts:

```python
agree(r"\leftarrow", r"\rightarrow")
# (True, "symbolic")
```

The same mechanism affects expressions such as `a\leftarrow b` versus `a\rightarrow b`. These express opposite directions.

**Count and limit:** One constructed false-positive pair established by source inspection; **no affected corpus row identified**. The two disclosed categorical approvals do not cover this path. The artifact reports **131 symbolic approvals**.

**Concrete fix:** Remove only complete `\left` and `\right` sizing commands, with command-boundary checks, in both functions. Add opposite-arrow rejection tests alongside ordinary delimiter tests. Re-decide the existing 12,028 solve records, disclose changed pairs, and rebuild the approval/receipt bindings. **No new blind generation is needed merely to make this correction.**

---

### V12-M1 — MEDIUM: the format sample still rewards answers unsupported by the stated conditions

Three clear cases in §H:

| Row | Supervised item | Defect | Concrete correction |
|---|---|---|---|
| `format_mc:mc_openbookqa_3784` | “Which area would be brightest, if you woke up there?” → **D, frozen areas** | No illumination, time, snow cover or comparison conditions are specified. Frozen does not establish brightest. | Specify comparable daylight and snow-covered terrain, or remove the item. |
| `format_mc:mc_openbookqa_126` | “Additional consistent force on a vehicle moving forward…” → **A, slightly accelerate** | Force direction is missing; opposing or transverse force supports other outcomes. Magnitude does not establish “slightly.” | Specify a net force in the direction of motion and remove the unsupported magnitude qualifier. |
| `format_mc:mc_arc_easy_5199` | Observing a change in river flow pattern → **D, years** | The intended process and timescale are unstated. Changes can occur over days, seasons or years. | Specify a long-term channel-change study or remove the item. |

**Count:** **3/20 supervised MC pairs (15%)**, in **3/5 format rows (60%)**. Two are demonstrations; one is a final target. All are supervised in this pass.

There is another wording defect in the separate §D sample: `mc_arc_challenge_3288`, SID `arc_challenge:f6ab5b4cc2e4`, asks what **“must”** differ between metal pieces. The premises permit identical dimensions. Option A describes something that **could** differ. That is **1/8 additional §D pairs**, counted separately.

**Concrete fix:** Review the source pool for missing conditions, then apply corrections or bans to both target and demonstration occurrences. Preserve stable SIDs when recording affected exposures. Repeated sampling has already shown why checking final targets alone is insufficient.

---

### V12-M2 — MEDIUM: a conversation invents the child’s parents’ divorce

**Evidence:** `convskills_v2:S2_00638`.

The user says classmates ask:

> «αν οι γονεις μου χωρισαν»

The suggested reply asserts:

> «Οι γονείς μου χώρισαν και ακόμη το συνηθίζω.»

The preceding turns do not establish a divorce. The assistant converts somebody else’s question into a sensitive autobiographical fact.

**Count:** **1/5 sampled conversation rows (20%)** contains this defect.

**Concrete fix:** Offer wording that preserves uncertainty:

> «Είναι οικογενειακό θέμα. Θα σου πω όσα νιώθω άνετα να μοιραστώ.»

Alternatively, introduce the divorce-specific wording conditionally. Search for this reused answer across conversation rows, rather than fixing only `S2_00638`.

---

### V12-M3 — MEDIUM: published MATH provenance does not prevent defective explanation text

**Evidence:** `math_en_math:math_train_3060`.

The solution contains:

```latex
s^2 = 2\cdot(4^2) - 2l\cdot(4^2)\cos(120^{\circ})
```

The extra `l` is undefined. It also claims:

> “the altitude and the centroid of an equilateral triangle are the same point”

An altitude is a segment/line, not the centroid. The relevant fact is that the centroid lies on the median and divides it in a 2:1 ratio.

**Count:** **1/5 English MATH explanations (20%)** has these defects. The final answer **384 is correct**; I found no incorrect final answer in the 15 sampled maths rows.

**Concrete fix:** Remove the stray `l` and correct the centroid statement in every replay copy. Retain the valid geometry and final answer. This supports explanation review of published solutions without treating the entire published block as defective.

---

### V12-M4 — MEDIUM: personality overlays replace only one occurrence of a repeated ID

**Evidence:** §E builds:

```python
by_id = {r['id']: i for i, r in enumerate(kept)
         if r['config'].startswith('personality')}
```

Each ID maps to its **last** occurrence. A replacement therefore changes at most one occurrence before duplicate IDs are suffixed.

The receipt records:

- **29** replacements applied;
- **4,512** inherited personality ID collisions suffixed;
- **6,016** personality training rows.

**Verified:** The code does not implement replacement across replay copies.  
**Unresolved:** The packet does not identify the 29 overlay targets and their multiplicities. It therefore does **not** establish how many intended replacements remain unapplied; assuming 87 would be unjustified.

**Concrete fix:** Map each source ID to all matching indices. Report matched and replaced occurrence counts per overlay, and verify the intended target text across all copies.

---

### V12-L1 — LOW: the cohort is unique, but global manifest uniqueness is not enforced

The supplied cohort contains **40 distinct IDs**, addressing the previous cohort defect.

However, the assembler counts collisions by `(config, id)`, and generated suffixes can collide with existing IDs. For example, a same-config input sequence:

```text
x, x, x#r1
```

becomes:

```text
x, x#r1, x#r1
```

There is no final global uniqueness assertion in the pasted assembler.

**Concrete fix:** Reserve generated IDs against all existing IDs and assert uniqueness over the final manifest. **No actual duplicate in the current full manifest is established here.**

---

### V12-L2 — LOW: another ThessCard answer remains operationally incomplete

**Evidence:** `convskills_v2:S2_00514` says:

> «Το προϊόν πρέπει να εγγραφεί στην κάρτα μέσω συμβατού μηχανήματος ή της προβλεπόμενης διαδικασίας»

That does not resolve whether the described mobile operation already writes the product to the card or requires a subsequent loading step. Journey validation and completion of a top-up are separate questions.

**Count:** **1/5 sampled conversation rows** contains this unresolved answer. I cannot establish that its text is identical to the excluded seed.

**Concrete fix:** Identify the application/top-up method, or ask for it; then explain loading completion separately from validation on boarding. Verify the operational instructions against the relevant official service.

---

### V12-L3 — LOW: the claimed docstring correction is incomplete

The pasted `labelcheck_lib.py` opening docstring still says:

> “a decimal comma only as 'd,dd'”

The implementation, version string and tests explicitly reject decimal-comma interpretation.

**Concrete fix:** Correct that opening docstring. Also revise present-tense comments claiming masked turns necessarily would be supervised: the supplied pretokenized implementation honors those flags, although this pass deliberately excludes such rows.

## 3. What is good and should not be changed

- **Keep the explicit categorical vocabulary.** The supplied logic distinguishes `x/X`, `A/a` and `Bob/bob`. Both disclosed categorical approvals—`math5_67` and `math5_1462`—are legitimate wrapper-normalization matches.
- **Keep exact arithmetic and conservative rejection.** Do not restore tolerance or arbitrary removal of trailing text to recover a few rows.
- **Keep approval revalidation and input binding.** They address a materially stronger problem than merely checking whether an ID appears in an approval list.
- **Keep the pretokenized mask path and strict negative control.** The supplied audits show zero deficit, extra supervision and wrong label values for the launch-path cohorts.
- **Keep partition-first MC sampling, preserved SIDs and overlap checks across all user turns.**
- **Keep the MB/MiB distinction in `S3_00097#1`.** Both the calculation and the requested rewrite are correct.
- **Keep the pilot’s negative result and corrected deficit history.** Neither completed experiment should be retrospectively rewritten to support the new pass.

## 4. Answers to the brief’s specific issues

| Issue | Assessment |
|---|---|
| **Is v11-H1 fixed?** | **Yes, narrowly:** arbitrary alphabetic strings no longer compare case-insensitively. V12-H1 is a separate structural-normalization defect. |
| **Are the heatstroke and ThessCard exclusions accounted for?** | The supplied reasons name **21 heatstroke rows and 22 ThessCard rows**, with **two shared IDs**, giving **41 distinct source rows**. The assembler guards the listed exclusions. I did not independently perform the claimed content searches or scan the full manifest for survivors. |
| **Are the theatre and three MC exclusions represented?** | Yes: the theatre family/Greek twin and three banned stems are represented in the supplied exclusions and builder. Full-file absence remains reported rather than independently scanned. |
| **Does F1 now demonstrate the actual training-label path?** | **Yes, within its stated scope.** Launch audit (b) matches **40/40 rows**, with **17,968/17,968 supervised labels** and zero differences. Audit (a) also passes; negative control (d) fails correctly. |
| **What is the measured raw-path deficit?** | **49/17,968 tokens = approximately 0.273%** on this selected cohort. This is neither a population estimate nor the withdrawn 34% figure. |
| **Do the assembly totals reconcile?** | Yes: **283,657 + 41,024 + 14,326 + 28,982 + 3,416 + 8,176 = 379,581** train rows. Dev: **2,667 + 146 + 17 + 71 − 559 = 2,342**. |
| **Are row lengths launch-compatible?** | The supplied full-render report says **0 over-length rows**, with maxima **4,032 train / 4,019 dev**, below 4,096. |
| **Does the pilot justify a maths-accuracy gain?** | **No.** The primary comparison failed. Reduced looping/truncation supports a behavioral rationale, not an established accuracy gain. |
| **Can improvements be attributed to individual blocks?** | **No.** Data composition and supervision behavior both changed. The recipe correctly attributes results to the pass as a whole. |
| **Is production GPU execution verified?** | **No.** The audits establish data preparation and label transfer using the stand-in model; they do not exercise production forward/backward execution with the full model and FlashAttention. Preserve the disclosed watched-start boundary. |
| **Lift Gate 2 now?** | **No: resolve V12-H1, re-decide approvals and refresh bindings first.** The other findings remain notes under your disposition. |

The **994/12,028 disagreements are model/reference disagreements**, not a measured 8.26% source-label error rate.

## 5. Open questions for the owner

1. Can the review artifact expose all **131 symbolic approval pairs**, plus any changes after the command-boundary fix?
2. Which **29 personality IDs** were replaced, and how many occurrences of each exist before and after overlays?
3. Which tokenizer/template and package versions bind the label audits to production, and what constitutes a successful watched GPU start?
4. For `S2_00514`, what current official evidence supports the mandatory-document list, and does the widow’s employment answer adequately explain any consequences for her pension? I have not verified either legal point.
5. Where is the final promotion definition naming the **eight native benchmarks** and explicitly stating the MATH-500 improvement tolerance?