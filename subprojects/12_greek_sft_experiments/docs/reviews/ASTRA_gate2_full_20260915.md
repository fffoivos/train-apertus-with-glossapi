# Astra review: gate2_full

Date 2026-09-15 04:29 · model gpt-6-astra (asserted from rollout rollout-2026-09-15T04-24-00-01a0a2a9-ebd4-7232-9cb6-9b1a55294809.jsonl) · effort xhigh · 5.6 min · prompt 84,850 chars · limit deltas {('codex', '10080'): 6.0} · brief `docs/reviews/briefs/astra_gate2_full.md`

## 1. Verdict

**HOLD for the queued 1-G4F6P1 launch.** The receipt’s arithmetic reconciles, but the supplied evidence does not establish that the intended, checked dataset is what the trainer will consume. The main issues are incomplete label-gate application, an unsafe numeric fallback, inadequate train/dev separation, an overly broad decontamination exception, and missing trainer-level verification of supervision masks. Several sample rows also contain visible truncation or unreliable context recall. The owner’s decision to retain worked solutions is accepted; the negative pilot alone is **not** a reason to block this re-planned pass. This review uses only the inlined material: I inspected code and reconciled arithmetic, but did not execute the pipeline or verify file hashes. Completed pilots receive notes only.

## 2. Findings ranked by severity

Sample rates below describe the supplied selections, **not estimated dataset-wide failure rates**. Receipt counts are reported counts whose arithmetic I checked.

### BLOCKER — 1. The recipe and launch configuration are not sufficiently bound to the assembled data

**Evidence**

- §A’s recipe is missing.
- The assembler’s description specifies English GSM **×1**, while its executable call and receipt specify **×2**.
- Maths contributes **15,967,730 / 148,895,935 = 10.72%** of estimated supervised tokens; the code comment says approximately 12%.
- The receipt reports **229,077,034** tokens; the trainer reports **222,734,797**, a difference of **6,342,237, or 2.77%**. This is plausibly explained by the disclosed approximate versus rendered accounting; it is **not evidence of lost rows**.
- Both expected-token fields are null. Dataset hashes appear in the receipt, but the supplied config/dry-run does not demonstrate verification of those hashes.
- Model revision and template source are named, but their resolved immutable identities are absent.

**Concrete fix**

Supply a frozen recipe for **1-G4F6P1 / legacy R4_full**, specifying actual multipliers, label scope, decontamination exceptions and split policy. Bind the launch to final train/dev hashes, input and assembly-code identities, resolved model/tokenizer/template revisions, and trainer-rendered counts. After the fixes below, regenerate the receipt and dry-run together; require the launcher to reject mismatches.

### HIGH — 2. The label check is a blacklist, not the stated positive confirmation requirement

**Evidence**

- English MATH is loaded into `mt` and passed directly to `add_block`; it never receives `bad_en` or another agreement filter. **All 7,290 input rows bypass that gate**, yielding 7,171 kept rows before the dev split and **14,198 effective training rows**.
- Greek rows survive whenever their stripped ID is absent from `BAD`. That does not establish that the problem was solved and agreed.
- Coverage for the native sample `greek_math_v2:gm_nat_1090_0#1` is not demonstrated by the supplied solver inputs.
- The receipt reports **986/12,028 disagreements, or 8.20%**. This is a disagreement rate, not a verified label-error rate. The pasted disagreement list stops mid-ID, so its membership and count cannot be independently reconciled.
- The check compares a blind answer with a **reference**. It does not verify that each retained `generated_solution` actually follows that reference or that the Greek translation preserves the problem.

**Concrete fix**

Join every in-scope maths row to a **positive agreement record** through a stable problem identity. Fail on unknown IDs, missing records, conflicting references or duplicated/stale solver records. Apply the result across corresponding English/Greek variants. Produce per-block counts for agreed, disagreed, unsolved and unmapped problems, and verify final supervised answers separately.

If published English MATH is intended to be exempt, that needs an explicit recipe rule; the current generic “a maths row is kept only…” statement does not describe the implementation.

### HIGH — 3. The numeric fallback can turn mathematical disagreement into agreement

**Evidence**

`num()` extracts a number from arbitrary surrounding text. From the supplied code:

- Reference `2` and answer `\sqrt{2}` both reduce to `2` in the fallback.
- `10 am` and `10 pm` both reduce to `10`.
- `0,125` becomes `0125`, hence `125`, rather than decimal `0.125`.

These are code-level counterexamples. No rescued-pair listing is supplied, so I cannot count how often they affected the 12,028 problems.

**Concrete fix**

Use a parser that accepts the **entire supported numeric expression**, with explicit locale and permitted-unit handling. Do not extract a number from symbolic expressions or arbitrary trailing text. Recompute agreement and audit every pair rescued by the numeric fallback, then rebuild the affected blocks.

### HIGH — 4. The dev split loses coverage and does not establish problem-level separation

**Evidence**

The counts reconcile:

**2,671 inherited + 536 new − 768 overlap removals = 2,439 final dev rows.**

However, cleanup removes **24.0%** of the candidate dev set:

| New block | Initially assigned dev | Final dev |
|---|---:|---:|
| English GSM | 205 | **0** |
| Conversational skills | 27 | **6** |
| Correcting | 3 | **2** |
| MC format | 83 | **39** |

The first-user-turn check is particularly inadequate for few-shot rows:

- In `mc_arc_challenge_40`, the first user turn concerns moose; the supervised target concerns a moth.
- In `mc_openbookqa_7021`, the first turn concerns an engine; the target concerns Earth’s orbit.

The format builder samples demonstrations from the complete source pool **before** assembly splitting. A dev target and its answer can therefore appear inside a training demonstration without the first-turn check detecting it. `train=false` prevents supervision only if honored; it does not prevent exposure.

Separately, **2,671 inherited dev candidates and 146 explicit Greek dev rows bypass the current `check_row` function**. Earlier screening is not evidence that they pass the current cache and rendering checks.

**Concrete fix**

Split by canonical problem/conversation family before duplication and few-shot construction. Keep translations and solution variants together. Construct MC demonstrations within their assigned partition and audit target/question identities across **all turns**. Apply current validation to every final dev row. Restore intended dev coverage; avoid block-level conclusions from two correcting examples.

### HIGH — 5. The IFEval exception waives a cache, not just instruction templates

**Evidence**

- **28,299 + 855 = 29,154** overlap hits are retained, despite being recorded under `drops`.
- The implementation accepts any otherwise-eligible hit confined to the `ifeval` cache for the two named configurations. It does not identify whether the matching text is an instruction template or substantive benchmark content.
- `mixlib.Decon`, cache inventories and cache hashes are absent. Consequently, “every evaluation cache” cannot be verified.
- Filtering stored entries by `v[0]` also needs inspection: if a gram has multiple benchmark memberships but only one stored attribution, removing its IFEval attribution could erase another benchmark’s protection. **That is a conditional implementation risk, not a demonstrated leak.**

**Concrete fix**

Either implement a defined template allowlist or explicitly document a cache-wide waiver. The disclosed exclusion of English IFEval can justify a deliberate waiver; it does not establish template-only filtering. Preserve all benchmark memberships, freeze the evaluation-cache identities, and report final matches against every non-waived cache. Record retained exceptions separately from actual drops.

### HIGH — 6. `assistant_only_loss=true` does not prove that `train=false` is honored

**Evidence**

The three MC samples correctly mark all **six demonstration assistant turns** unsupervised. Several correcting examples likewise mask an initial assistant turn.

But the dry-run reports only assistant-only loss. That alone does not demonstrate that the trainer excludes selected assistant turns. The receipt’s **16,378 supervised format tokens / 8,189 rows = 2 per row** supports the assembler’s intended accounting, not the trainer’s actual labels.

**Concrete fix**

Provide decoded trainer-label inspections after rendering and packing, including:

- `mc_arc_challenge_40`: five demonstration answers excluded; final `A` included.
- `mc_openbookqa_7021`: initial `D` excluded; final `D` included.
- `correcting_v2:cv1_corr_2_00050#1`: initial assistant turn excluded.

Report exact supervised counts and any truncation under the trainer’s rendering. This requires verification, not an assumption that the masks are broken.

### HIGH — 7. Five sample rows are visibly incomplete

**Evidence**

| Row ID | Visible defect |
|---|---|
| `math_en_math:math_train_815` | Prompt stops at “If the graph of `$y=h(x-3)$`”; the requested task is missing. |
| `convskills_v2:S5m_00623#1` | Assistant ends mid-word: “Η αλλαγή σχεδίων δικαιολογείτ”. |
| `convskills_v2:S2_00665#1` | Assistant ends mid-word: “να ρυθμίσετε νόμιμ”. |
| `correcting_v2:cv1_corr_2_00183#1` | Two assistant turns end at “ως Κυ” and “Η εικο”. |
| `correcting_v2:cv1_corr_2_00050#1` | One answer ends “Θα δημιουργ”; another cuts off inside Python code. |

That is **5/25 §H rows (20%)** with visible incompleteness. **4/10 conversation/correction rows (40%)** contain at least one cut-off supervised assistant turn.

What is verified is truncation **in the supplied excerpts**. Whether it exists in the training JSONL or only in the sample exporter remains unresolved.

**Concrete fix**

Check the full hash-bound rows first. If only the exporter clipped them, provide intact samples. If stored rows are damaged, restore or regenerate the affected content and screen the queued blocks for similar failures. A 4,096-token upper-bound check does not detect already-truncated source text.

### HIGH — 8. The two S5m samples resolve uncertain context with unjustified certainty

**Evidence**

- `convskills_v2:S5m_00623#1` ends with “αφού βρίσκεσαι στο Ηράκλειο”, despite intervening travel context involving departure from the Netherlands to Paros.
- `convskills_v2:S5m_00019#1` returns to Chania and €120 despite later Thessaloniki/€360 trip context, and supplies **“Σάββατο 12 Σεπτεμβρίου”** without a date anchor in the supplied conversation.

Different trip budgets can coexist; the defect is treating an ambiguous referent as settled. Both supplied S5m examples exhibit this pattern: **2/2 S5m samples, or 2/5 conversational samples**. One supplies an unsupported exact date.

**Concrete fix**

Audit the queued S5m slice for persistent facts versus temporary trip constraints. Make the final target clarify the applicable location/budget or state its assumption explicitly. Anchor relative dates in supplied context. Preserve the long-context recall objective while removing contradictions from generated histories.

### MEDIUM — 9. Two local wording defects deserve correction or notes

- `greek_math_v2:c2_gsm_2181` asks how many throws are possible **“προτού τον στείλουν”**. Starting at 50 points, one throw leaves him below the threshold; the second triggers referral. The answer correctly calculates **two to reach the threshold**, but does not resolve the wording. This is **1/5 Greek maths samples with a boundary ambiguity**, not a demonstrated arithmetic error. Rewrite the question to specify reaching the threshold or remaining below it, with a matching answer.
- `mc_openbookqa_7021` identifies the Sun through option D, but its stem misleadingly attributes seasons to orbiting alone. Log or repair the causal wording while preserving the MC protocol.

## 3. What is good and should not be changed

- **The receipt arithmetic is internally consistent.** Per-config totals sum to 381,688 rows, 229,077,034 estimated tokens and 148,895,935 estimated supervised tokens. Base accounting also reconciles:  
  `403,727 − 119,765 + 6 − 311 = 283,657`; adding 98,031 effective new rows gives 381,688.
- **Greek ×2 accounting is correct.** Its 146 dev rows are supplied separately; `14,508 × 2 = 29,016` is not a forgotten dev subtraction.
- All **5/5 English GSM** examples have correct arithmetic. The four unambiguous Greek examples and four complete English MATH examples also have consistent solutions.
- Preserve the MC demonstration masks and correcting-block masks. `S3_00284` follows the bullet-format request; `S3_00057#1` removes the prohibited word while preserving the response.
- Do **not** flag `astra_pilot48_10_true` or `astra_scale60_14_parcel_checklist_true` as fabricated external tool actions: their supplied context explicitly defines textual state.
- Preserve the blind-solve screen and its disclosed limitations. Its useful role is filtering disagreement; agreement is not proof of correctness, especially where Sol also generated targets.
- Retain the owner-authorized worked-solution strategy. The pilot supports better generation behavior relative to terse targets.

## 4. Answers to the brief’s specific questions

| Question | Assessment |
|---|---|
| **Is the receipt exact?** | Its arithmetic reconciles. Its token accounting is explicitly approximate, and its hashes are not verified against the trainer’s inputs here. |
| **Is the label check correctly applied?** | No: English MATH bypasses it, unknown IDs are not rejected, and the numeric fallback is unsafe. |
| **Is decontamination verified?** | No: the exception is broader than its description, and the implementation/cache evidence is incomplete. No actual benchmark-leak rate can be counted from these samples. |
| **Is the dev split adequate?** | Not yet: it loses all English GSM coverage, permits untested few-shot exposure paths, and skips current checks for inherited/explicit dev rows. |
| **Is the config structurally plausible?** | Yes: `1 × 4 × 4 = 16` effective batch, and `ceil(54,434 / 16) = 3,403` steps. This does not establish data, template or mask binding. |
| **Can the run be informative after fixes?** | Yes, as a test of the **complete new recipe**. Simultaneous block changes prevent attributing gains specifically to worked maths or correcting v2. |

**Pilot interpretation:** “No drift” is too strong. Against the reference, English MATH changes by **−1.2 pp** for worked solutions and **−3.8 pp** for worked + Level 5. Loops are **37/500 and 45/500**, versus **27/500** in the reference, although substantially below terse targets’ **82/500**. Truncations return close to reference levels. This supports behavioral improvement relative to terse targets; it does not establish accuracy gains or guarantee retention in a from-scratch pass. Freeze the new pass’s baseline, evaluation protocol and acceptance criteria accordingly.

## 5. Open questions for the owner

1. Are the five incomplete excerpts clipped by the exporter, or present that way in training JSONL?
2. What is the intended label-check scope for published English MATH and native Greek problems, and where is their positive coverage manifest?
3. Is the intended IFEval exception template-specific or cache-wide, and which frozen evaluation battery governs that choice?
4. Can the missing recipe, complete label-check output and hash-verifying trainer dry-run be supplied, including actual supervision-mask checks?
5. What predeclared behavior, English-retention and MC-protocol criteria determine success for this owner-authorized full-recipe pass?