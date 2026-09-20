# Astra review: gate2_full_v2

Date 2026-09-15 05:11 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T05-02-25-01a0a2cd-1a63-76d2-b121-f9e6561f5a50.jsonl) · effort xhigh · 9.0 min · prompt 108,384 chars · limit deltas {('codex', '10080'): 1.0} · brief `docs/reviews/briefs/astra_gate2_full_v2.md`

## 1. Verdict

**HOLD for launch of 1-G4F6P1.** The second pass fixes several substantive problems: the receipt arithmetic reconciles, reference filtering uses positive agreement, the IFEval waiver checks the other caches, and the receipt records the S5m removal. However, **§I contains no trainer-label inspection results**, **217 dev rows bypass the assembler’s current row checks**, and **the English MATH split does not enforce problem-family separation from Greek training rows**. Close findings F1–F3 before launch. I inspected the supplied code and samples and recomputed the counts; I did not authenticate manifest bytes or execute the trainer. The owner’s decision to retain worked solutions is accepted as the experiment’s scope.

## 2. Findings, ranked by severity

### F1 — BLOCKER: The claimed trainer-label inspection is absent

**Evidence:** §I consists only of its heading. Neither `DRY_RUN_OK` nor `assistant_only_loss: true` establishes that per-turn `train=false` masks survive tokenization and packing.

Specific rows requiring inspection include:

- `mc_arc_easy_3035` and `mc_openbookqa_5631`: both demonstration answers must be masked; the final answer must remain supervised.
- `convskills_v2:S4_00354`: the two earlier responses containing the unwanted closing phrase must be masked.
- `correcting_v2:cv1_corr_2_00134#1`: the deliberately repeated, incorrect response must be masked; the recovery response must be supervised.

**Verified failure:** missing validation evidence. **Actual mask-failure rate: unknown.**

The token totals also need a precise interpretation: the receipt reports **227,429,079**, whereas the trainer reports **221,717,421**, a difference of **5,711,658 tokens, or 2.51%**. Different counting methods can explain this; the difference itself does not demonstrate truncation.

**Concrete fix:** Supply inspection output from the trainer version used for launch, bound to the manifest hashes, configuration, and tokenizer/template identity. Include:

1. Decoded supervised spans and mask counts for the rows above.
2. Evidence that packing preserves those masks.
3. Full-manifest counts of sequences exceeding 4,096 **before truncation**, truncated rows, and rows with no supervised tokens.

### F2 — HIGH: Explicit dev rows bypass current assembly checks

**Evidence:** In `add_block`, ordinary rows pass `check_row`. Explicit `dev_rows` take this separate path:

```python
dev.extend(
    dict(config=name, id=f"{name}:{r['id']}", messages=render(r))
    for r in dev_rows if render(r)
)
```

That path performs no current control-character, contamination, or window check.

The final receipt retains:

- **146 Greek maths dev rows**
- **71 format dev rows**

Thus **217/2,163 final dev rows — 10.0% — bypass `check_row` in this assembler**. This is a bypass rate, not a measured contamination rate. The format builder previously checks contamination, but that does not establish all three current checks for both blocks.

**Concrete fix:** Route explicit dev rows through the same applicable checks as other rows, record their drops, and recount after filtering. Reassemble and refresh both manifest hashes and the dry-run evidence.

### F3 — HIGH: Problem-family isolation remains incomplete

**Evidence:** The English MATH input excludes `dev_problems_en`, but then:

```python
add_block('math_en_math', ..., 2)
```

creates **72 additional English MATH dev rows through random row splitting**. Their corresponding Greek problems are not subsequently excluded from Greek training. Exact English/Greek text comparisons cannot detect that crossing.

The final overlap filter also compares only the **first and last dev user turns** against all training user turns. It does not examine intermediate supervised tasks. Multi-turn supervision is visible in rows such as `convskills_v2:S2_00524` and `correcting_v2:cv1_corr_2_00111#1`.

**Verified:** these separation guarantees are absent from the code. **Actual cross-language or intermediate-task leakage count: unknown; no matched leaking pair is supplied.**

The existing filter removed **529/2,692 candidate dev rows, 19.7%**. All **21 conversation dev rows** disappeared, and correcting dev fell from **3 to 1**. That reconciles with the final receipt, but leaves little behavioural coverage in dev.

**Concrete fix:** Assign maths splits once using canonical problem identities shared across languages, solutions, and copies. Include the 72 English MATH dev families in that assignment. Audit every format demonstration and every supervised conversational task using source-family identities or full task/context signatures. Report zero family intersections after assembly.

### F4 — MEDIUM: Reference agreement does not establish generated-target correctness

**Evidence:** `keep_en(prob)` checks whether the **problem** belongs to the agreed set. The assembler then copies `generated_solution` without comparing that solution’s answer against the agreed reference. This affects **20,541 retained English GSM solution records, duplicated into 41,082 training rows**. The translated Greek join similarly establishes source-reference agreement, not translation fidelity or correctness of the written solution.

For example, `math_en_gsm:1962966#1` contains the expected answer 48 under its four-week assumption. If its generated answer were changed to 49 while its problem stayed unchanged, the shown agreement gate would still accept it. **That is a code counterexample, not an observed error in this row.**

I found **no clearly wrong final value among the 15 supplied maths rows**. Existing upstream target checks may exist; they are not supplied.

**Concrete fix:** Record existing per-solution validation, or compare each generated target’s final answer with its agreed reference. Bind that result to the actual problem and solution text. Preserve the recipe’s published-MATH and native-generation exemptions, with their existing provenance.

### F5 — MEDIUM: Completeness and reproducibility claims exceed the recorded safeguards

**Evidence:**

- The finalizer assigns `n_problems = len(rows)` and `unsolved = []`. It does not compare the solve log against the intended problem manifest. Consequently, its output cannot establish completeness by itself.
- S5m exclusion requires `--drop-s5m`; the documented default invocation omits it. The **current receipt does record 537 dropped rows**, so I am not claiming S5m remains in this manifest.
- `--allow-unconfirmed` is described as dry-run-only, but the code allows it to write the production arm directory.
- Receipt identities omit material assembly dependencies, including the inherited dev file, `dev_problems_en.json`, source-text mapping files, and the personality patch. The launcher configuration and trainer code are also absent from the shown identity set.

**Concrete fix:** Check unique solve-record IDs against a hashed expected-problem manifest; derive missing IDs from the difference. Make S5m exclusion an enforced recipe property and mark unconfirmed outputs as unlaunchable. Record all consumed inputs, assembly arguments, trainer/configuration identities, and resolved model/tokenizer revisions.

### F6 — MEDIUM: The R3/R4 supervised-token comparison is not on an established common basis

**Evidence:** `greek_if` retains **29,773 rows**, and the assembler does not edit their messages, yet the recipe reports:

- R3: **6,045,528 supervised tokens**
- R4: **9,775,168 supervised tokens**
- Increase: **61.7%**

Other inherited blocks also show substantial changes. This can reflect a counting-method change, but then the table is not a comparable measure of training exposure.

The R4 block totals themselves **do sum correctly** to 380,996 rows, 227,429,079 estimated tokens, and 147,664,959 estimated supervised tokens.

**Concrete fix:** Recompute both recipes with the same trainer tokenization and masking implementation. Distinguish bookkeeping changes from actual changes to supervised spans.

### F7 — MEDIUM: Promotion rules need complete failure handling and more precise terminology

**Evidence:**

- §J explicitly specifies HOLD when criterion **(1)** fails, but does not explicitly give the disposition when **(2) or (3)** fails alone.
- “Native suite improved by more than noise” lacks a stated aggregate and threshold.
- The fixed margins are operational tolerances; their designation as statistical “noise” is not established by the supplied evidence.
- A bundled R4 run cannot isolate a causal “format-block effect.”

The pilot also does not support an unqualified “no drift, no runaway” summary:

| Measure | Worked `--01` | Worked + Level 5 `--02` | New promotion limit |
|---|---:|---:|---:|
| Loops / 500 | 37 | 45 | ≤32 |
| Truncated / 500 | 59 | 62 | ≤65 |

Both worked arms exceed the newly declared loop limit. English MATH also fell by **1.2 pp** and **3.8 pp** from the reference.

**Concrete fix:** Specify that failure of **any** criterion (1)–(3) means HOLD and incumbent selection. Define the native aggregate and improvement threshold. Describe fixed margins as tolerances unless backed by uncertainty estimates. Report format performance descriptively unless an ablation supports attribution. These are notes on the completed pilot, not a request to rerun it.

### F8 — LOW: A few sampled examples need clearer assumptions or wording

These are sample findings, not population estimates.

| Row | Evidence | Concrete fix |
|---|---|---|
| `math_en_gsm:1962966#1` | **1/5 English GSM samples** assumes four weeks per month without the question specifying it. Answer 48 is correct under that convention. | State the four-week assumption in the problem or explicitly qualify the solution. |
| `correcting_v2:cv1_corr_2_00111#1` | **1/5 correcting samples** gives an underspecified seasons demonstration: “κρατώντας την ίδια κλίση” does not clearly preserve the axis’s direction in the room. A stationary flashlight also needs to remain aimed at the globe. | Specify fixed axis direction and illumination throughout the demonstration. The correction behaviour itself is sound. |
| `mc_openbookqa_5631` | **1/3 format samples** contains weak questions. Brief contact does not establish abrasion; the ecosystem demonstration permits both invisible and nonliving things. | Prefer unambiguous items for this format-training block. This is an ambiguity finding, not proof that its recorded source key is wrong. |

## 3. What is good and should not be changed

- **The receipt arithmetic reconciles.** Base retention plus the six new blocks equals **380,996 rows**; dev additions minus 529 removals equals **2,163**.
- **Positive agreement is a substantive improvement.** Unknown translated/GSM problems are rejected in the confirmed path. The reported **1,009/12,028 disagreements, 8.39%**, are solver/reference disagreements—not an independently established bad-label rate.
- **The IFEval waiver now has the right membership logic.** Rebuilding the union without English IFEval retains detection of grams shared with other caches. The disclosed waiver counts are **28,299/46,037 = 61.5%** for `ifeval_like` and **855/4,050 = 21.1%** for `dolci_precise_if_20k`.
- **The sampled behavioural targets generally work.** I found no failure of the intended correction/attribution task in the five correcting samples, or of the explicit modification/persistence instruction in the five conversation samples. For example, `S2_00976` respects “Από εδώ και πέρα μη μου κάνεις ερωτήσεις πίσω” across six subsequent answers. This does not certify every embedded factual claim.
- **The clipping objection is resolved for the displayed sample.** None of the **25 §H rows** visibly ends mid-response. Stored-manifest integrity and trainer truncation remain separate checks.
- **Keep the worked-solution rationale accurately scoped.** The completed pilot supports substantially better generation behaviour than the terse arm. It does not demonstrate an accuracy improvement.
- **Keep S5m excluded.** The supplied audit reports **74/100 flawed rows**; its overlapping categories should not be summed into another failure rate.

## 4. Answers to the brief’s readiness questions

**Is this manifest and recipe ready to train?**  
**HOLD pending F1–F3.** The other findings are logged at MEDIUM/LOW under the requested disposition.

**Does the positive join fix the previous label-filter problem?**  
Yes, for the confirmed path’s **source-reference eligibility**. It does not establish solve-log completeness or per-generated-solution correctness.

**Is the strict numeric fallback acceptable for this pass?**  
The four listed rescues are auditable, and none shows the previous extraction of a number from a complex expression. Their problem statements are absent, so I cannot verify the semantic appropriateness of stripping `pm` or `BC`. The generic parser also accepts arbitrary suffix words and `%`; it is not a general proof of numerical equivalence.

**Is the IFEval exception now adequately disclosed and scoped?**  
Yes, as a **cache-wide English IFEval waiver for two blocks**, rather than a verified template-only exception. The other-cache union addresses the shared-membership problem. English IFEval should remain outside clean held-out performance claims for this pass.

**Does the launch binding close the manifest-identity issue?**  
The shown SHA-256 comparison correctly checks remote train/dev bytes against the receipt’s hashes. That is stronger evidence than filenames or the short MD5 comparison. The supplied excerpt does not bind the complete trainer/configuration environment or provide §I’s missing results.

**Does the negative pilot require rejecting the owner-authorized pass?**  
No. The owner explicitly chose a new from-scratch pass retaining worked solutions for behaviour. That decision supersedes the earlier scheduling consequence. The report should preserve the negative accuracy result and distinguish reduced failures relative to terse training from meeting the new stage-1 guardrail.

## 5. Open questions for the owner

1. What are the actual §I mask-inspection and pre-truncation results for the final hashed manifests?
2. How many of the **72 English MATH dev problems** have Greek training counterparts? What canonical family mapping establishes separation?
3. Which existing artifacts certify generated-solution answers, Greek translation fidelity, and the native rows’ two-solve checks?
4. Why do unchanged inherited rows acquire substantially different supervised-token counts between R3 and R4?
5. Which cache explicitly covers the **IFEval-el promotion set**, and what native-suite aggregate and improvement threshold will govern promotion?