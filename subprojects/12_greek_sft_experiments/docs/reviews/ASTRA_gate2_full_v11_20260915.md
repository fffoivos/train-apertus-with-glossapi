# Astra review: gate2_full_v11

Date 2026-09-15 16:41 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T16-36-20-01a0a548-6567-73f3-ac0e-275914c5e648.jsonl) · effort xhigh · 5.2 min · prompt 256,292 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_gate2_full_v11.md`

## 1. Verdict

**HOLD for 1-G4F6P1.** The v10 comma counterexamples are fixed by the supplied v11 code, and the training-path audits support closing the previous label-transfer finding. However, approval still has a false-positive route through case-insensitive “categorical” comparison of mathematical symbols. A supervised heatstroke response also needs a safety correction before reuse. Other sample defects are listed below as MEDIUM/LOW. **Evidence scope:** I recalculated the supplied totals and inspected the supplied code, rows, and logs; I did not execute the Python comparator, independently scan the complete manifests, recompute file hashes, or rerun the cluster audits. These findings concern the queued pass; completed pilots and baseline runs receive notes only.

## 2. Findings ranked by severity

### V11-H1 — HIGH: arbitrary mathematical symbols are compared case-insensitively

**Evidence:** `equiv500.categorical` lowercases its input and returns any short alphabetic string as a category:

```python
t = ... .lower()
return CATEGORICAL.get(t, t) if re.fullmatch(...) else None
```

Consequently, this call follows the categorical branch:

```python
agree("x", "X")  # (True, "categorical")
```

That result follows directly from the supplied code; **I did not execute it**. Mathematical `x` and `X` can denote different quantities. Neither is a recognized categorical answer such as “ellipse” or “even.”

**Count and impact:** One concrete false-positive counterexample. The artifact reports **2 categorical approvals**, but does not disclose those pairs. I cannot establish that either current approval is wrong. This is a comparator defect, not an observed dataset error rate.

**Fix:** In the **approval library**, restrict categorical matching to an explicit vocabulary and its declared translations. Preserve case for arbitrary mathematical symbols. Add regressions for `x` versus `X`, while retaining legitimate category translations. Re-decide the 12,028 records, disclose changed pairs, and bind the resulting approval and assembly artifacts. Do not silently change the frozen benchmark grader.

### V11-H2 — HIGH: the heatstroke spot sets an unsafe explicit emergency threshold

**Evidence:** In `convskills_v2:S2_00202#1`, the first supervised response includes:

> «Νιώθετε έντονη ζάλη, σύγχυση, πονοκέφαλο ή τάση λιποθυμίας; … ζητήστε βοήθεια. Σε απώλεια αισθήσεων, καλέστε το 112.»

The spot is explicitly about recognizing heatstroke. It mentions **confusion**, but reserves its explicit emergency-call instruction for **loss of consciousness**. It does not literally prohibit an earlier call; the defect is the escalation threshold it teaches by omission.

**Count:** **1/5 conversation rows**, specifically **1/35 supervised conversation turns**, contains this safety concern.

**Verification distinction:** The wording and its supervision are verified from the packet. The medical safety assessment was **not rechecked against an official source in this session**, because browser access was blocked.

**Fix:** Quarantine this response and every conversation reusing it until a qualified clinical review supplies a target that distinguishes heat exhaustion from suspected heatstroke, calls for emergency assistance promptly, and includes immediate cooling. Do not wait for unconsciousness in the revised escalation instruction.

### V11-M1 — MEDIUM: the theatre problem asks for an exact expenditure from a lower bound

**Evidence:** `math_en_gsm:2036578` says:

> “at least once a week”

The target replaces this with:

> “once a week for 6 weeks”

Six visits cost \(6\times3\times5=\$90\), but seven visits cost $105 and also satisfy the premise. **$90 is the minimum, not a uniquely determined total.**

**Count:** **1/5 sampled English GSM rows (20%)** is under-specified. The other four sampled calculations check out.

**Fix:** Exclude the problem family by text, including all solution rows, copies, and any Greek twin. Alternatively, revise the question to ask for the minimum and repeat the applicable fingerprint and reference-approval steps. The sample does not establish the family’s total manifest multiplicity.

### V11-M2 — MEDIUM: three MC questions do not establish a unique answer

| Evidence | Defect | Concrete fix |
|---|---|---|
| `format_mc:mc_openbookqa_5297`, final question: “Which … would be considered a predator?” | Gold **A, grizzly bear**, is not unique: **C, salmon**, and **D, lobster**, also include predatory animals. | Replace the question/distractors or provide a specific food-chain scenario. |
| `format_mc:mc_openbookqa_677`, final question: “The best thing for absorbing” the sun’s warmth | Gold **A, brass sheet**, conflates heat conduction with solar absorption. Material names alone do not specify surface finish, colour, area, or the comparison conditions. | Ask about conduction under comparable conditions, or specify the surfaces and intended absorption comparison. |
| §D `mc_openbookqa_4823`, demonstration: “Which causes more matter vibration?” | Gold **A, megaphone**, versus **D, yelling**, lacks an operating state, sound level, and comparison conditions. A device name alone does not determine vibration magnitude. Stable source ID: `openbookqa:ac161c4db47d`. | Rewrite with defined conditions, or ban the stem from both target and demonstration pools. |

**Counts:**

- §H: **2/15 supervised MC question-answer turns**, affecting **2/5 sequences**.
- §D: **1/11 additional question-answer turns**, affecting **1/3 sequences**.
- Combined: **3/26 questions (11.5%)** have the identified uniqueness/specification defects.

These are selected-sample counts, not estimates of the full pool’s defect rate. They also do not mean every chosen letter is necessarily false.

**Fix beyond individual rows:** Screen question validity across the OpenBookQA pool before further reuse. Correct letter formatting cannot compensate for an ambiguous question, and supervising demonstrations spreads those defects across additional sequences.

### V11-M3 — MEDIUM: sponsorship advice changes “printing” into purchasing complete outfits

**Evidence:** The final turn of `convskills_v2:S2_00202#1` asks whether to fund:

> «την εκτύπωση 25 εμφανίσεων»

The response discusses:

> «7,20 € ανά εμφάνιση, μαζί με εκτύπωση και φόρους»

and treats that as an outfit price that may be marginal. The requested expenditure was **printing on 25 outfits**, not necessarily buying the outfits.

**Count:** **1/5 conversation rows**, one supervised turn. This is the same row as H2, not an additional affected row.

**Fix:** Preserve the printing-only scope. State that €180 permits €7.20 per printed outfit, obtain printing and transport quotations, and compare the school’s needs and permitted sponsorship arrangements without inventing garment-purchase requirements.

### V11-L1 — LOW: the previously flagged activation omission survives in another conversation

**Evidence:** `convskills_v2:S2_00202#1` contains the ThessCard question about whether mobile loading **activates the new balance automatically**. Its answer again explains mandatory boarding validation:

> «Άλλο η φόρτιση … και άλλο η υποχρεωτική επικύρωσή της»

It does not resolve when or how the remotely purchased balance becomes available.

**Count:** **1/5 conversation rows** contains the same issue class previously reported for `S2_00809`.

**Fix:** Search by the reused question/answer content, not only conversation ID. Repair the activation explanation after checking the relevant loading method, or remove that turn’s containing rows. The exclusion of `S2_00809` alone did not close the content-level issue.

### V11-L2 — LOW: the “40-row cohort” contains 39 distinct IDs

**Evidence:** `systemchats:systemchats_29f64948` appears twice in the cohort list. The audit converts requested IDs to a set and reports:

> `39 rows found of 39`  
> `matched_rows 39/39`

**Count:** **40 entries, 39 distinct IDs, one duplicate entry.**

**Assessment:** This does **not** invalidate the clean 39-row audit or demonstrate a missing distinct requested row. It does invalidate the repeated description of that run as auditing 40 distinct rows.

**Fix:** Describe it as 39 unique rows, with any exposure-category overlap disclosed. If 40 unique rows were required, deduplicate before sampling, replenish the cohort, and rerun.

### V11-L3 — LOW: the comparator’s module documentation still describes decimal-comma acceptance

**Evidence:** The supplied `labelcheck_lib.py` module docstring says:

> “a decimal comma only as ‘d,dd’”

The v11 implementation, version string, and tests instead deliberately reject decimal commas.

**Fix:** Update this remaining docstring. The solver docstring correction does not correct the comparator’s own documentation.

## 3. What is good and should not be changed

- **The specific v10 comma fix is sound by code inspection.** Classification precedes spacing removal. The three reported list/thousands collisions remain distinct, while `(1,2)` and `(1, 2)` retain equivalent separator forms.
- **Exact rational comparison and conservative rejection are appropriate.** The 25 disclosed gains versus v7 are mathematically equivalent pairs, including `3009/17 = 177`. The ten disclosed losses are conservative normalization exclusions, not demonstrated bad labels.
- **The approval-binding design is substantially stronger:** shared manifest construction, solve/comparator/manifest identities, approval revalidation before selection, and an unchanged-approval-file check during assembly.
- **The launch-path label evidence is useful.** Supplied logs report zero deficit, extra supervision, or wrong label values for both the four-row audit and the 39-distinct-row cohort. The clean-path negative control now reaches the intended failure branch.
- **Receipt arithmetic reconciles:** block rows sum to **379,642**; nominal supervised counts sum to **146,342,251**; retained base plus new blocks is **283,657 + 95,985 = 379,642**.
- **Sample maths quality is mostly good:** all five Greek maths rows and all five published English MATH solutions check out on the supplied information. `math_train_2687` contains diagram source in the **question** that supplies the necessary geometry; it is not the unsolicited assistant-side code dump previously excluded.
- **The conversation tests themselves work:** the three sampled verbatim recalls reproduce the requested questions; the literal banned word «θηλυκές» is absent from `S3_00031`’s revised answer; `S2_00202` maintains and then releases the requested closing phrase.
- Preserve natural Greek decimal notation in Greek training content. The English approval policy does not justify rewriting Greek `2,5 €` as though it were an erroneous answer list.

## 4. Answers to the brief’s specific issues

| Issue | Assessment |
|---|---|
| **Is V10-H1 closed?** | **Yes for its three counterexamples**, by supplied-code inspection. V11-H1 above is a separate remaining route. |
| **Were the v10 content exclusions implemented?** | The exclusions, reasons, pool bans, and assembler guards support implementation. I did not independently scan the final JSONL for survivors. The activation omission visibly survives under another conversation ID. |
| **Does §C substantiate re-finalization?** | The supplied log reports **135 tests passed**, 12,028 live records, zero stale/missing/unfingerprinted records, and **11,034 + 994 = 12,028** decisions. The previous-finalization delta is zero; the v7 delta reconciles as **11,019 − 10 + 25 = 11,034**. These are inspected artifact claims, not rerun results. |
| **Is F1 closed?** | **The sampled training-path label-transfer finding is supported as closed.** Four-row and 39-row audits are clean; raw-path deficit is **26/15,692 = 0.166%**. The historical 34% claim must remain withdrawn. |
| **Does that prove production GPU readiness?** | **No.** The audit uses a stand-in model and checks batches. It does not establish a successful production model forward/backward/optimizer step with the launch attention implementation. That limitation is correctly disclosed. |
| **Are masks and demonstrations accurately represented?** | Yes: the selected path supports masks, while this pass deliberately excludes masked rows and supervises MC demonstrations after removing their flags. Keep that distinction explicit. |
| **Are the token totals interchangeable?** | No. **224,873,467** is the assembly estimate; **220,083,288** is the reported rendered training count, a difference of **4,790,179**. The full collator-supervised total is not supplied. |
| **Does the pilot justify an accuracy-improvement claim?** | No. The primary worked-versus-terse result is **−1.4 pp** and fails promotion. Reduced looping/truncation supports a behavioural rationale. The from-scratch pass remains a new experiment whose effects combine data and supervision changes. |

The **994/12,028 = 8.26% disagreement rate is not a measured label-error rate**: solver mistakes and conservative comparison failures also contribute.

## 5. Open questions for the owner

1. What are the **two categorical approval pairs**, and do either involve symbols rather than recognized categories?
2. Will the heatstroke spot receive qualified clinical review, including a search for every conversation that reuses it?
3. Can the rebuilt artifact provide zero-survivor evidence for the newly identified problem families and ambiguous MC stems?
4. Is **zero final `convskills_v2` dev rows** intentional? The receipt shows 17 initially assigned, but none in the final dev breakdown.
5. What production step-0 success and stop conditions are recorded for the first pretokenized GPU run?
6. Can future audit receipts record the actual process exit status alongside the verdict line and use a correctly described unique-ID cohort?

**Disposition:** HOLD on **V11-H1 and V11-H2** for the queued pass. Log MEDIUM/LOW findings under the stated policy. Do not retrospectively rebuild completed experiments.

Automatic approval review rejected opening Firefox because it could expose private browser state. Permission for public-source-only verification was requested and remains pending; external medical and scientific source checks are therefore not represented here as completed.