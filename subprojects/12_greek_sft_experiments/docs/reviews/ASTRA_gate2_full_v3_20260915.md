# Astra review: gate2_full_v3

Date 2026-09-15 06:01 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T05-54-41-01a0a2fc-f395-7f11-aa93-e2f985ecddb1.jsonl) · effort xhigh · 7.2 min · prompt 124,401 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v3.md`

## 1. Verdict

**HOLD for the queued 1-G4F6P1 launch.** The supplied code closes the explicit-dev checking bypass and the identified maths/format split routes. The four trainer inspections also demonstrate the intended **pre-packing** masking. Two HIGH issues remain: the excerpt does not establish label preservation and exact window enforcement through the actual training data path, and the new GSM solution-answer check can accept a wrong answer by extracting its last number. Separately, the R3 supervised-token total is arithmetically inconsistent, and overlap removal eliminates conversation-suite dev coverage. I reviewed the inlined code and **28 complete sample rows**; I did not inspect the underlying files, recompute hashes, or execute the trainer. Completed R3 and pilot runs receive notes only.

## 2. Findings ranked by severity

### HIGH — H1. F1 is partially closed: the inspection stops before the disputed packing path

**Evidence**

The four inspections show the expected supervision:

| Inspected row | Masked assistant turns | Supervised spans |
|---|---:|---:|
| `format_mc:mc_arc_easy_455` | 3 | 1 |
| `greek_math_v2:c2_gsm_4973` | 0 | 1 |
| `convskills_v2:S4_00353#1` | 2 | 3 |
| `correcting_v2:cv1_corr_2_00277` | 4 | 5 |

**No visible masking failure in these 4/4 inspections.** This closes the missing pre-packing inspection.

However, `inspect_labels.py` calls only `T.tokenize_messages`. It does not exercise packing or the training collator. The trainer excerpt stops at `def validate_and_tokenize_data(` and then jumps to configuration settings. Consequently, the supplied code does not show which dataset reaches TRL or how its final batch labels are constructed.

Window enforcement remains similarly under-evidenced: the assembler uses the receipt’s **“content only, +8 per turn”** count. No exact, pre-truncation maximum or over-window count is supplied. Absence of a printed truncation line is not an affirmative zero-truncation assertion.

The receipt and trainer totals differ by **5,705,410 tokens**. Different counting methods can explain this; the difference cannot establish or quantify truncation.

**Concrete fix**

Provide one launch-bound audit through the actual preparation, packing and collator path:

- Assert every row’s **exact rendered length before truncation** is ≤4,096.
- Report input/output row counts, maximum length, over-window rows and any truncation.
- Check these four examples through actual packing/collation, asserting that masked turns remain `-100` and intended supervised tokens survive.
- Include the data, config and trainer hashes and relevant runtime versions in that audit.

This completes the original F1 evidence requirement without requiring another training experiment.

### HIGH — H2. The GSM final-answer check is not fail-closed

**Evidence: `sol_ok` in §E**

For unboxed output, the code takes the **last numeric substring of the last line**:

```python
(re.findall(..., final_line) or [None])[-1]
```

A concrete counterexample, established by code inspection:

```text
expected_answer: "2"
generated_solution: "Final answer: 1/2"
```

The fallback extracts `2`, so the comparator receives `"2"` versus `"2"` and accepts a solution whose stated answer is `1/2`.

The unconditional comma removal also discards potentially meaningful decimal or answer-list punctuation.

**Observed rate:** all **5/5 sampled English GSM solutions** have correct boxed answers; none demonstrates this defect. The receipt reports **1 rejection among 20,553 label-agreed candidate solutions**, but that is this parser’s rejection rate, not a verified solution-error rate.

**Concrete fix**

Parse the complete terminal answer, preserving mathematical syntax. Reject or quarantine ambiguous extraction instead of selecting the last number. Re-screen the 20,553 candidates and record extraction failures separately from mathematical disagreements. Include the fraction counterexample above in validation.

### MEDIUM — M1. F6 remains inconsistent: the R3 total reverses the apparent supervision change

**Evidence: §A**

The displayed R3 block entries sum to:

**151,912,798 supervised tokens**

The stated total is:

**140,424,598 supervised tokens**

The discrepancy is **11,488,200 tokens**. The R4 block sum correctly equals **147,694,355**.

On the displayed block basis, R4 supervision **decreases by 4,218,443 tokens, or 2.78%**. Using the stated R3 total instead implies a **5.18% increase**.

**Concrete fix**

Regenerate the table and totals from the same recount artifact, assert that block sums equal totals, and identify its counting basis. If the block column is authoritative, correct the R3 total to 151,912,798. This is a reporting correction for completed R3.

### MEDIUM — M2. The overlap fix removes useful dev coverage

**Evidence: §B**

The counts reconcile:

```text
2,667 inherited + 146 maths + 21 suite + 3 correcting + 71 format
= 2,908 before overlap removal
2,908 − 565 = 2,343 final dev rows
```

But the final `dev.by_config` contains:

- **0/21 retained `convskills_v2` dev rows** — 100% removed.
- **1/3 retained `correcting_v2` dev rows** — 66.7% removed.

The filter protects exact user-turn separation, but dev loss provides no direct conversation-suite coverage and almost no correcting coverage.

**Concrete fix**

Keep the overlap filter. For a future assembly, partition conversation families or connected groups of shared prompts before assigning train/dev. For this pass, disclose the missing coverage and use the separate behavioural evaluations to assess these lanes.

### MEDIUM — M3. Several sample targets still teach avoidable errors or unwanted behaviour

These are findings in selected examples, not population estimates.

| Evidence | Count in supplied block sample | Concrete fix |
|---|---:|---|
| `correcting_v2:cv1_corr_2_00020#1`: after **«πες μου μονο τι συμφωνησαμε τελικα»**, the response begins **«Δεν έγραψα αυτό»** and states the agreement twice. This violates the requested summary-only scope. | 1/5 correcting rows | Give the agreement once: **«Σύντομη υπενθύμιση στη Μαρία μέσω Viber, χωρίς απειλές, για εξόφληση 680 € έως τις 15 Σεπτεμβρίου.»** |
| `correcting_v2:astra_scale60_19_weekly_menu_false#1`: **«Την άλλαξα σε σούπα.»** claims completion without displaying the revised draft or an edit result. The transcript establishes no persistent artifact change. | 1/5 correcting rows | Show the updated draft: **«Τρίτη φακές, Τετάρτη ομελέτα, Πέμπτη σούπα.»** If persistent editing is intended, require an actual edit result. |
| `correcting_v2:cv1_corr_3_00147#1`: repeatedly teaches unqualified **«W = V × A»** in an AC-appliance discussion. Real AC power also depends on power factor; 230 V × 10 A gives 2,300 VA. The stated appliance wattage does not justify the general rule. | 1/5 correcting rows | Qualify the formula for DC or unity power factor, and distinguish apparent power from real power in the circuit example. |
| `mc_openbookqa_5631`: “A cardinal makes brief contact with a picnic table” does not establish abrasion. Its masked ecosystem demonstration also allows competing readings: something can be invisible or nonliving. | 1/3 format rows has an underdetermined supervised target | Replace the ambiguous target and demonstration with unambiguous questions. Screen the demonstration pool as well as target questions. |

The format finding is an **underspecification judgment**, not proof that the source answer key was transcribed incorrectly.

### MEDIUM — M4. Provenance improvements do not yet verify the exact-text validation claim

**Evidence**

The finalizer reports **12,028 expected and solved IDs, zero missing and zero extra**, and rejects duplicate solve IDs. Those are useful controls.

However:

- The expected manifest hashes **IDs**, not problem/reference content.
- The solver resumes by ID.
- The finalizer compares answers against the `ref` stored in the solve record, without checking that it matches the current source reference.
- No exact-text Greek derivation-validity records or coverage-ledger excerpt are inlined for the **five Greek maths samples**.

Thus stale-content reuse is a possible code path; **no actual stale record is demonstrated**. Likewise, the Greek derivation-validation coverage is asserted but not independently verifiable here.

**Concrete fix**

Bind solve records to problem-text and reference hashes and reject stale joins. Supply the Greek coverage summary and exact-text records for the sampled rows, with the ledger identity recorded in the receipt.

## 3. What is good and should not be changed

- **Maths sample correctness:** I found **0 incorrect results among 15 maths samples**: five Greek, five English GSM and five published MATH. The shown derivations support their answers.
- **Masking intent:** preserve the demonstrated distinction between context-only assistant turns and supervised responses, including the final MC letter and assistant-end token.
- **Explicit dev checks:** both explicit Greek maths dev rows and format dev rows now pass through `check_row`.
- **Split protections:** preserve zero random dev fractions for English maths, English-twin exclusion through `dev_problems_en`, and the all-user-turn overlap filter.
- **Conversation constraints:** `convskills_v2:S2_00521#1` has **0 violations across its nine subsequent answers under the 20-word cap**, counting whitespace-separated words. All three sampled S4 rows avoid their prohibited closing phrase after the user requests its removal.
- **Accounting:** the R4 block rows sum to **381,138**; its supervised-token entries sum correctly; the dev arithmetic reconciles.
- **S5m disposition:** keep the default exclusion. The supplied audit reports **74/100 flawed**, with overlapping categories that should not be added together.
- **Pilot reporting:** preserve the negative accuracy result and its uncertainty. Reduced looping does not establish an accuracy benefit.

## 4. Answers to the brief’s readiness questions

| Fix claim | Third-pass assessment |
|---|---|
| **F1: trainer inspection and packing/window safety** | **Partially closed.** Pre-packing inspections pass; actual packing/collator and exact-window evidence remain insufficient. See H1. |
| **F2: dev rows bypassing checks** | **Closed by the supplied code.** Both explicit dev routes invoke the same checker. |
| **F3: family isolation** | **Identified maths/format routes addressed.** The code removes random English maths splits and checks all user turns. This does not independently verify the contents of `dev_problems_en` or semantic separation across the entire corpus. |
| **F4: solution validity** | **Partial.** The GSM terminal-answer check has a deterministic false-accept path. Greek exact-text derivation coverage remains an unverified assertion here. |
| **F5: completeness and identities** | **Materially improved.** ID completeness, duplicate rejection and additional identities are present. Content freshness remains unbound; the shown remote launch checks verify data hashes, not remote config/trainer hashes. |
| **F6: common counting basis** | **Not fully closed.** The displayed R3 block sum contradicts its total. |
| **F7: promotion criteria** | **Operationally clearer.** Failure of any of (1)–(3) now explicitly means HOLD. The rule still permits substantial MATH accuracy regression if behaviour and other qualifying metrics pass; that should be an explicit owner choice. |
| **F8: data-card note** | **Acknowledged, not verified.** The updated data-card text is not supplied. |

**Does the pilot qualify the Greek maths block?** No accuracy qualification was obtained. A from-scratch bundled pass may answer a different question, but §G explicitly stops this named Phase C pass. Its superseding owner decision should be recorded clearly. The new run also cannot attribute any improvement specifically to the format block without an ablation; descriptive reporting is appropriate.

## 5. Open questions for the owner

1. Can you supply the actual packing/collator and exact-length audit described in H1?
2. Which R3 recount artifact is authoritative: the displayed block values or the stated total?
3. Where are the exact-text Greek derivation ledger, its coverage summary and the five sample-row records?
4. Does the “owner decision 01:30” explicitly supersede §G’s Phase C stop, and where is that decision documented?
5. Which eight benchmarks define the native macro, and is promotion despite substantial Greek or English MATH accuracy loss intentional?