# R-DPO9 — closing review, 19 September 2026

**Ran:** all 31 regression tests (**31 passed, zero skipped**); public-API defeat attempts; adversarial official-result validation; independent recomputation of the four official results’ 66,528 rows and Holm correction; checks against the five named JSON artifacts; construction of 38 real lm-eval lane manifests; shell syntax and retirement guards; read-only Clariden checks of staged hashes, checkpoint layouts, training dates, tokenizer rendering, and effective model configurations. CPU configuration/rotary checks only; no model inference or jobs launched. Temporary test fixtures were removed.

**HOLD both jobs: a newly verified RoPE configuration mismatch invalidates the frozen plan’s repair/reuse premise; the public comparison guard and official acceptance/shutdown checks also remain bypassable.**

## Part 1 — the record

### Claim table

“Supported” below means supported at the stated scope, not certification of the whole pipeline.

| Published claim | Assessment | Finding |
|---|---|---|
| Held-out displacement and its monotonic control by α (§§3–4, 14; ledger CLEAN) | **Supported** | The within-run policy/reference contrasts and same-day dose comparison remain meaningful. The newly found evaluation-loader defect does not invalidate this training-time measurement. |
| α0.25 versus α0: +0.70 pp, unresolved (§§6, 14) | **Supported, conditional** | Reproduced **+0.7024 pp**, paired interval **[−0.7394, +1.8484]**. Matching seed/date prevents the identified date imbalance. This remains a contrast under the recorded evaluation configuration, not demonstrated equivalence or a deployment recommendation. |
| Date confounds the original 2×2 (§7) | **Supported but incomplete** | The date finding stands. Model geometry also differs between parent and checkpoints; freezing the date alone cannot isolate training. |
| Date-matched scorecard isolates training (§8; ledger rows 53–54) | **Wrong** | The displayed arithmetic is correct: MGSM **−7.60/−6.13 pp**. But the parent and checkpoints resolve to different RoPE settings. These are observed deficits under different effective model configurations. |
| Date-matched IFEval has no identifiable checkpoint contrast at all (§8) | **Overstated withdrawal** | Its observed contrasts exist, just as the MGSM contrasts do. Neither currently identifies a weights-only effect because of the additional geometry mismatch. Apply that qualification consistently. |
| Between-seed SD and repeat gap are contaminated (§9 banner) | **Supported** | Evaluation dates contaminate the existing summaries. Freezing evaluation dates will not turn groups with different training-prompt dates into pure seed replications. |
| Repeat runs differ “only” through ZeRO floating-point reduction order (§9 body) | **Wrong/overstated** | It contradicts the banner’s evaluation-date qualification; the exclusive attribution to reduction order is also not established by divergent losses alone. |
| BAL improves observed MGSM relative to standard arms (§11) | **Supported, conditional** | Same evaluation date: **+6.00 pp versus plain; +4.53 versus anchored**. Restricting both training and evaluation dates to the 19th gives **+5.60/+4.13 pp**. This survives as an arm-to-arm observation under the shared evaluation geometry; length, selection and exposure remain confounded. |
| BAL’s worse multilingual result is only a cross-date inference (§11; ledger row 57) | **Understated** | Direct BAL-versus-late-standard comparisons already match evaluation dates: **−2.51 pp versus plain; −2.85 versus anchored**. Restricting training dates too gives **−2.69/−3.02 pp**. The absolute loss against the parent remains confounded. |
| Same-day standard-arm Global-MMLU losses are CLEAN (ledger row 56) | **Wrong** | Date matching does not remove the newly verified RoPE mismatch. The corrected six-language aggregation itself is correct. |
| Movement checkpoints span two training dates (ledger row 58) | **Wrong** | The named axis—arms **01, 05, 07 and 08**—trained on **18 September**, confirmed from cluster-local timestamps. Evaluation dates differ. The n=1 and nominal-exposure limitations still stand. |
| GreekMMLU-250 counts, shared flips and 235 unchanged items (§10) | **Supported as recorded observations** | They do not establish a capability ceiling or a preference-specific cause. The parent/arm custom-protocol contrast also needs the new geometry qualification. |
| Custom full run completed eight models and gains +0.28…+0.52 pp held out | **Supported numerically; interpretation overstated** | Eight models are present. “VALID but wrong ruler” is incomplete: its loader also changes effective checkpoint geometry relative to the parent. |
| Official GreekMMLU: −0.41/−0.43/−0.26 pp, all significant after Holm | **Supported for these checkpoints** | Independently reproduced gains/losses **131/200, 114/186, 98/141**. Adjusted p-values: **0.000354, 0.000115, 0.006472**. |
| “Preference training moved official GreekMMLU down” (§10) | **Overstated in its headline formulation** | The subsequent one-checkpoint caveat helps. Prefer: **“The three evaluated trained checkpoints scored 0.26–0.43 pp below the parent under official-label GreekMMLU.”** Recipe reproducibility and preference-specific causation remain unestablished. |
| Custom-versus-official sign disagreement is a protocol comparison (§10) | **Incomplete** | The observations differ in **protocol and effective checkpoint geometry/runtime**. The offered fluency explanation is explicitly labelled untested, appropriately; it must also acknowledge this concrete alternative. |
| IPO trained but failed its preregistered eligibility gate (§12) | **Supported** | Failure to achieve the dev-separation target is not failure to perform training. Its falsification test remains inconclusive. |
| No general replacement has been demonstrated; the round produced useful findings (§§8, 13–14) | **Supported with narrower wording** | Preserve displacement control, conditional BAL contrasts and the measured official results. “No improvement large enough to justify shipping” still presumes deployment tolerances that have not been specified. |

### H1 — HIGH: material contradictory claims remain in the active page

The amendments did not remove the earlier conclusions everywhere. In the [page generator](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/G4F6P1--DPO01/curves_page.py:641):

- **§8 still says the mixed-date scorecard “isolate[s] training.”**
- **§8 still argues that IPO matching the other arms means the column is not measuring what their training did.** That is the inference §10 correctly retracts.
- **§13 still says “Nothing here has been checked by a second party against the artifacts.”** This directly contradicts §6 and the completed reviews.
- **§10’s final custom-protocol caveat says every GreekMMLU figure on the page is internally comparable and none is comparable to published GreekMMLU**, although the section now includes official results.
- **§13 still treats the mathematics and multilingual regressions as solid training conclusions.** The newly found geometry mismatch prevents that interpretation.

These are current statements, not merely historical quotations. The record is not yet clear.

### MEDIUM/LOW record corrections

- **MEDIUM:** Correct the ledger’s over-withdrawal of direct BAL multilingual comparisons and its false movement-axis training-date statement. Add the geometry error described under B1 below.
- **MEDIUM:** The §9 banner must say that the planned evaluation freeze cannot repair training-date variation. Its body must stop reinstating the exclusive nondeterminism explanation.
- **LOW:** “Every arm gains exactly +2.00” is false across the eight-model custom table: `arm05s44_ep3` and `armBAL_ep3` gain **+1.60** on the slice. The seven-arm held-out range is **+0.28…+0.52**, and the clean-full range is **+0.32…+0.58**.
- **LOW:** “Holm-adjusted p ≤ 0.006” should be **≤0.0065**, or report the actual values.
- **LOW:** BAL selects **274 from 343 training pairs**, not from all 397 including dev. A proposed random-subset control must preserve that split.
- **LOW:** Replace residual “can move” language with “changed across these evaluated models”; reconcile the ledger’s old “open/not re-reviewed” rows with its later dispositions.

The three bannered documents clearly identify their bodies as historical records. Preserving those bodies is reasonable; their banners should also identify the new geometry issue. They do not excuse contradictory assertions in the current page.

## Part 2 — launch gate

### B1 — BLOCKER: checkpoint RoPE changes under the frozen evaluator

This is a **sixth error missing from the ledger**.

I loaded the configurations in the actual evaluation environments, without loading model weights:

| Environment | Parent / `parent_ckptcfg` | DPO checkpoint |
|---|---:|---:|
| Frozen/lm-eval: Transformers **4.57.0** | Effective `rope_theta = 500000` | Effective `rope_theta = 12000000` |
| Official GreekMMLU: Transformers **5.16.1** | Effective RoPE theta **500000** | Effective RoPE theta **500000** |

The checkpoints serialize their intended setting inside newer `rope_parameters`. The 4.57 Apertus loader retains that extra field but constructs its rotary embedding from the legacy fields and defaults instead.

This is not merely a JSON difference. Small CPU `ApertusRotaryEmbedding` objects produced different inverse-frequency arrays:

- Parent / `parent_ckptcfg`: digest prefix **`23fb193e7a154bcc`**.
- DPO checkpoint: **`f0db7489bf7b981c`**.

I reproduced this with the frozen launcher’s Python and shared-library paths. Applying its parent-generation-config overlay **still leaves the checkpoint at 12000000**: [staging changes only EOS/PAD/BOS/cache fields](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/dpo01_frozen_rescore.sh:114).

Consequences:

1. Parent/arm lm-eval comparisons change effective model geometry as well as weights, including likelihood-scored Global-MMLU.
2. The completed custom GreekMMLU launchers use the same 4.57 environment and direct model-loading path. Their parent/arm interpretation needs this qualification too.
3. The proposed frozen job preserves the defect. Its manifests record four generation-related config fields, not effective model geometry.
4. Previously scored 19-September checkpoint results cannot simply be reused as evaluations with repaired geometry.
5. **The official negative deltas are not invalidated by this particular defect:** its 5.16.1 loader resolves the intended RoPE parameters consistently.

I have established the configuration/computation mismatch, **not how much of any score difference it explains**. That requires controlled scoring.

### B2 — BLOCKER: the sealed public API still accepts uncontrolled comparisons

The new object prevents the previously tested manifest-copy and separate-outcome edits. However, sealing preserves whatever the builders accept.

Using only public imports and genuine saved outputs:

| Defeat attempt | Result |
|---|---|
| Honest parent versus `arm05_ep3`, with their real generation configs | **Refused**, correctly |
| Same files, but pass the parent’s config through the public builder’s `gen_config=` argument | **Accepted as weights-only**, **+0.184843 pp**, `unverified=[]` |
| Widen exported `POLICIES["weights"]` to include `gen_config` | **Accepted** |
| Build a result from the parent’s raw output using a genuine arm weights receipt | **Accepted as a different model**, despite identical underlying evaluated output |

Relevant surfaces: [builder](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/manifest.py:67), [exported mutable policy table](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/rlhf/evals/compare.py:12).

No private capability, source edit or seal forgery was needed. Moreover, the existing “controlled comparisons pass” test accepts a real parent/checkpoint comparison affected by B1.

**Required:** immutable policy definitions; evaluator-produced, result-bound identities for weights, effective model configuration, tokenizer and generation settings. An unchecked caller assertion cannot become verified provenance merely by being sealed.

### H2 — HIGH: official validation remains weaker than its claimed contract

The [validator](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/eval_jobs/validate_official_result.py:11) correctly checks exact IDs/counts, several settings, boolean correctness and ordinary accuracy consistency.

But these mutations of a genuine result were **accepted**:

- Replace `model_config_sha256` with 64 zeros.
- Set reported accuracy to **NaN**.
- Replace every gold answer with the prediction, mark every answer correct, and report **100% accuracy**.
- Add an extra nonofficial protocol to a row.

Thus the claimed model/config binding is absent, the gold frame is not checked against pinned content, and the numerical check fails open on NaN.

**Required:** bind validation to an expected evaluation receipt, including weights and effective configuration; verify gold answers against the pinned dataset projection; require finite bounded accuracy and valid non-boolean integer indices; enforce the intended protocol schema.

### H3 — HIGH: failed shutdown verification is still interpreted as success

At [driver line 35](/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/greekmmlu_official.sh:35):

```bash
st=$(sshc "squeue ..." | head -1)
[ -z "$st" ] && DOWN=1
```

A failed SSH/scheduler query produces empty output. I reproduced the branch with `sshc` returning **255**: it sets **`DOWN=1`**.

The dirty-node early exit also still uses the old unverified closure path.

**Required:** distinguish a successful empty scheduler response from a failed query; retain an unknown/failure state on communication errors; apply checked cleanup to every exit after allocation acquisition. A failed query must never establish release.

### R-DPO8b fixes that did pass

| Fix | Verification |
|---|---|
| Receipt ID self-consistency | **Fixed.** The six inspected receipts recompute consistently; relabelled IDs are rejected. Parent and `parent_ckptcfg` share the same weights ID. Receipt-to-result binding remains B2. |
| Corrected frozen list | **24 entries: 10 full + 14 generated-only**, matching the narrowed written R1/R2 plan. Four movement checkpoints are present. B1 now requires revising that plan. |
| Retaining `parent_ckptcfg` | **Its missing Global-MMLU baseline is a valid reason.** Its already-existing 19-September IFEval/MGSM cells are redundant. It does not, however, match the checkpoints’ effective RoPE configuration. |
| R3 single-shard staging | **The corrected condition matches all twelve real inputs:** each has one `model.safetensors`, no index, and the required config/tokenizer files. I did not execute staging. |
| Tokenizer freeze/canary | **Passed in memory:** one replacement; both tested conversations, with/without generation prompt, preserve rendering apart from the date. |
| Manifest-based frozen validation | **Improved and functioning at the parsing layer:** 38 real lanes parsed, including 36 Global-MMLU leaves totaling 2,400 items. It does not cure missing configuration identity. |
| Legacy retirement | All four launchers returned **64** before reaching operational code. |

**MEDIUM — reuse still trusts marker/file existence.** Frozen results are skipped on `.validated` existence; R3 skips any nonempty local result JSON. Neither branch revalidates current inputs and output identity. No such frozen markers or twelve-R3 result files existed during this review, so this is a resume defect rather than an existing false completion.

### Staged-file identity

Under `/iopsstor/scratch/cscs/fffoivos/sft_round1/`:

| Artifact | Result |
|---|---|
| Frozen launcher | Exact repository match: SHA-256 `0e6921059e5b402bcef9a92967bd8f1499d4bd87976feccb770f148055377c8f` |
| Frozen model list | Exact match: `99617f1fab722cb4c2809a648f7501690e8330b32da744dcae497f977d743849` |
| `cluster/eval_jobs/weights_receipt.py` | Exact match to repository **`rlhf/evals/weights.py`**: `ae6ed026dd515ecbb5ffe6b2967596238ffa92b2d9b1684ba9f58621aee1b0d4` |
| Eight runtime Python files under `rlhf/` | All identical |
| Two repository test files | Not staged |

The official orchestrators and validator operate locally. The currently staged official scorer under `$R/eval_jobs/` differs from the local copy; the driver uploads the local scorer before starting. These are therefore **not all identical deployed trees**, although the specifically staged frozen execution files match.

### Is the plan worth its cost?

**Frozen, as written: no.** Four node-hours would remove evaluation-date variation while retaining an unrecognized model-geometry change. It would not support the intended weights-only or deployment conclusions.

A corrected evaluation programme **can be worth doing**, and could change the round’s conclusions. We cannot currently know how much of the apparent mathematics/multilingual damage comes from evaluating checkpoints with the wrong RoPE configuration.

The first missing control that matters is **unchanged parent weights passed through the checkpoint export/loading configuration**, alongside a checkpoint evaluated with verified intended geometry. `parent_ckptcfg` is not that export control: it changes only generation-related fields. Qualify the corrected loading path, then reprice the matrix; do not preserve the 19-September reuse assumption automatically.

Within the present list, **`parent_ckptcfg` IFEval/MGSM buys no new comparison**; its Global-MMLU run does. The old `arm01_ep3_parentcfg` and `arm05_ep3_parentcfg` cells will also need reconsideration because their geometry is affected. If the programme intends to answer §14’s question about actually removing displacement, **α1.0 remains absent from the replicated benchmark test**; R1/R2 does not answer it.

**Official rest: scientifically worth approximately 2.5 node-hours after its safeguards are fixed.** The twelve models add the missing replicas and BAL coverage under the appropriate protocol. None is redundant for that stated coverage. They can establish whether the three observed losses extend across the evaluated runs and how BAL behaves. They cannot repair training-date differences or establish a length mechanism; report date strata and checkpoint dispersion accordingly.

## Explicit launch decisions

- **Frozen re-score: NO.** B1 requires changing the evaluation contract and reuse/model list; B2 and H1 also remain open.
- **Official GreekMMLU rest: NO.** Its existing numerical finding survives B1, but B2, H2 and H3 leave the launch gate uncleared; H1 also requires correcting the published record.

## Ordered asks

1. **Add the RoPE error to the ledger and correct its affected CLEAN calls.** Preserve measured scores; withdraw unsupported training-effect interpretations.
2. **Repair and verify effective model geometry before repricing frozen scoring.** Bind the resolved configuration to results and revisit every reused checkpoint cell.
3. **Close the public API bypasses**, with regressions for false builder config, substituted genuine receipts and mutable policy definitions.
4. **Make official validation receipt-bound and strict**, including pinned gold answers, finite numbers and protocol/schema checks.
5. **Make shutdown verification fail closed**, including failed SSH queries and the dirty-node path.
6. **Remove the contradictory active-page claims**, retain the properly bounded positive findings, and resolve the listed MEDIUM/LOW record and reuse issues.
7. **Stage and hash the corrected execution artifacts**, then validate the revised concrete launch plans against these findings.

VERDICT: HOLD — geometry, comparison-integrity, record, and official-job safeguards remain unresolved | BLOCKERS: 2 | HIGH: 3 | LAUNCH frozen: no | LAUNCH official: no

