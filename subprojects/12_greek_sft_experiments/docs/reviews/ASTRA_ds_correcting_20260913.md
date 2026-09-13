# Astra review: astra_ds_correcting

Date 2026-09-13 10:37 · model gpt-6-astra (asserted from rollout rollout-2026-09-13T10-28-09-01a099aa-975e-77a3-af59-a7920e42f147.jsonl) · effort xhigh · 9.2 min · prompt 196,778 chars · limit deltas {('codex', '10080'): -78.0} · brief `docs/reviews/briefs/astra_ds_correcting.md` · sample 40 rows of `data/robustness/correcting/scale/rows/rows_final.jsonl` seed 3

**1. Verdict**

**Change the design; exclude v1 as-is from queued mixes, and preserve completed datasets and runs for reference.** Correction training is salvageable, but increasing the FALSE proportion alone will not fix this set: the sample contains a supervised false concession, filters that suppress useful corrective behavior, and two records with reversed top-level speaker fields. The reported regression and recovery after removing the set support investigating it as a cause, although I cannot independently verify that ablation’s controls. I recommend a compact, balanced, evidence-checked SFT v2, tested against a matched **no-correcting** control; use DPO only as a subsequent comparison. The existing misquote recoveries contain useful material worth retaining, but transcript quotation resistance is insufficient coverage for false factual corrections.

**2. Findings ranked by severity**

This review covers the pasted sample, not the underlying JSONL, generation logs, or training tensors. Nine of the 40 excerpts are truncated; that is a **display limitation, not evidence of nine corrupt source records**. The remaining 31 records contain 205 assistant replies, including 169 marked `train:true`. Counts below are manual. Because truncation excludes long records, these rates should not be extrapolated to all 600 dialogues.

| Verified observation | Count and denominator |
|---|---:|
| Complete displayed records with reversed top-level `user`/`assistant` fields | **2/31 — 6.5%** |
| Unambiguous supervised concession to a false claim about prior history | **1/169 targets — 0.6%; 1/31 records — 3.2%** |
| Records containing an explicit recall or recap request | **40/40** |
| Requested question responses excluded for `checks:question_only` in three game dialogues | **14 exclusions** |
| Fully visible planted replies marked `train:false` | **15/15** |
| Supervised closings in complete records | **29/169 targets — 17.2%** |

These categories overlap and must not be added into an overall error rate.

**BLOCKER — The serialized record has two conflicting representations of who said what.**

In `corr_3_00088` and `corr_2_00124`, `turns` ends with a user message, but the top-level fields put the preceding assistant question under `user` and the final user answer under `assistant`.

For example, `corr_3_00088` has:

- Top-level `user`: «Θα προτιμούσες να δεις από το παράθυρο κάτι να περπατάει έξω από το σκάφος ή να ακούσεις τη φωνή σου από έναν κλειδωμένο θάλαμο;»
- Top-level `assistant`: «τη φωνη μου απο τον θαλαμο, επομενο και ακομα πιο τρομακτικο»

That second string is explicitly a **user** turn in the conversation.

**Impact:** If training uses the flat fields, these records teach the assistant to impersonate the user. If training exclusively uses `turns`, training contamination from this defect is unproven; the export is still unsafe for downstream reuse.

**Fix:** Make role-indexed `turns` canonical. Derive any flat pair from explicit turn indices, never positional assumptions about the last two messages. Trace these two IDs through the actual packer and inspect their token labels. Repair the export rather than dropping long game dialogues, which would selectively remove difficult examples. This is a blocker for queued reuse until the loader path is established.

**HIGH — A supervised target accepts a fabricated prior request. Other repairs also concede or diagnose too much.**

The clearest case is `corr_2_00257`. The user claims:

> «Εγώ το ζήτησα σε δεκαδικές ώρες, π.χ. 7,5, όχι σε `[h]:mm`»

Neither earlier user message requested decimal hours. The **assistant** had introduced them as an option. Nevertheless, the supervised response says:

> «Δεν το έδωσα σε δεκαδικές ώρες όπως ζήτησες.»

It then gives a reasonable decimal-hours formula. This directly exhibits the reported failure pattern: **correct task content attached to a false admission**. Its metadata nevertheless says `assessment:"ok"` and `verdict:"correct"`.

Two additional cases should be assessed separately from that narrow false-history rate:

- **`corr_3_00105`: unwarranted grammatical concession.** The earlier phrase is «δεν ήσουν γενναίος άνθρωπος». The target treats «γενναίος» as proof it addressed a man. But the adjective agrees with the grammatically masculine noun «άνθρωπος», which can refer to a woman. Accepting the newly specified female addressee is appropriate; declaring the earlier construction necessarily male is not.
- **`corr_3_00088`: incomplete repair.** The planted error falsely attributes the user’s choice to an assistant instruction: «Αφού πριν σου είπα να γίνεις αόρατος». The recovery diagnoses unnecessary repetition, without clearly repairing that ownership error. I classify this as an incomplete repair, **not another unequivocal false concession**.

**Fix:** Check the acknowledgment and final answer separately. A target passes only if both are supported. For `corr_2_00257`, a suitable opening is:

> «Στην προηγούμενη απάντηση χρησιμοποίησα `[h]:mm`· τώρα το προσαρμόζω σε δεκαδικές ώρες.»

For `corr_3_00088`:

> «Εσύ διάλεξες να γίνεσαι αόρατος· εγώ το παρουσίασα λανθασμένα ως δική μου προτροπή.»

Do not globally ban «Σωστά». Require its scope to match the part that is actually correct.

**HIGH — The filters demonstrably remove intended behavior while retaining weaker targets.**

Across three complete dialogues:

| Row | Exclusions for `checks:question_only` |
|---|---:|
| `corr_3_00295` | 3 |
| `corr_3_00088` | 6 |
| `corr_2_00124` | 5 |
| **Total** | **14** |

The users explicitly requested question-based games. One excluded answer in `corr_3_00088` also repairs an actual repetition before asking the next question.

Further examples:

- `corr_3_00295`: the response correctly rejects the fabricated basketball quotation and supplies a new dilemma, but is excluded for `checks:loop`.
- `corr_3_00103`: the useful initial clarification about the purpose of the rent message is excluded as `assessment:question_only`.
- `corr_3_00291`: a recovery accurately describes the visible repetition and correctly checks \(p=2\) and \(E_k=4\), but is excluded for `checks:invented_process`. Describing an observable preceding reply is not inventing an internal process.
- `corr_3_00239`: the first answer is simultaneously `assessment:"wrong"`, `train:true`, and `reject:null`. This proves an unresolved metadata disagreement, **not by itself that the formula is wrong**.

**Fix:** Replace global surface prohibitions with task-conditioned checks. Questions are required in games and often necessary for clarification. Observable self-reports need comparison with the transcript. Style defects should usually trigger an edit, not removal of the entire target.

Before generating further, publish exclusion rates by truth class, task, context length, and difficulty. Otherwise the filter can undo the proposed balancing.

**HIGH — The objective is diluted, and its accounting cannot yet establish the actual correction balance.**

From the **brief’s supplied counts**, rather than an independent full-file count:

- Explicit HOLD targets: **20/3,692 = 0.54%**.
- Closings: **575/3,692 = 15.6%**.
- TRUE-correction acceptances outnumber the reported HOLD targets **5.7:1**, before considering planted-failure recoveries.

However, approximately 200 misquote confrontations also provide resistance supervision. **It would be wrong to claim the set contains only 20 resistance examples.** Their relationship to the other categories needs reconciliation: the five exact counts sum to 3,622; adding roughly 200 misquotes gives roughly 3,822, not 3,692. The categories therefore overlap, omit cases, or use different definitions.

The sample independently shows an especially strong scaffold: **40/40 dialogues ask the assistant to recall or summarize something**. Several mostly teach ordinary adaptation and recall—for example `corr_3_00190`, `corr_3_00014`, and `corr_2_00105`.

**Inference:** The set may teach “recap, acknowledge, continue” more strongly than evidence-sensitive correction handling. Doubling its mix weight doubles exposure to that distribution; it does not create independent correction cases.

**Fix:** Define the sampling unit as a **correction decision**, with an atomic truth label and required response behavior. Report post-filter counts and supervised-token weights. Keep supporting context, but remove closings and unrelated ordinary replies from the correction-specific loss budget. Balance after filtering and polishing.

**HIGH — Successful quotation resistance can still fail the user’s active instruction.**

In `corr_2_00201`, the user requests:

> «grapse to ontws se mia.»

The supervised response contains **two sentences**: a sentence rejecting the quotation, followed by the requested scientific explanation. Both `assessment` and the subsequent synthetic user response approve it.

This is **one definite instruction failure among the ten fully readable misquote-recovery replies**, including one reply inside an otherwise truncated record. All ten reject the fabricated quotation; nine are supervised. Thus the sample supports quotation discrimination, but not uniformly successful overall recovery.

**Fix:** Score recovery conjunctively: truthful stance **and** correct content **and** fulfillment of the current request. If one sentence is required, the explanation can simply be supplied without accepting the accusation; a separate defense of the transcript is unnecessary. Synthetic user approval must never serve as validation.

**HIGH — `claim_truth` and “typed checks” are not auditable from the delivered records.**

None of the **31 complete records** exposes `claim_truth`, supporting evidence, or an independent target audit. That does not prove these never existed internally. It means they cannot be checked against the exported targets.

Two source-sensitive examples show why that matters:

- `corr_3_00104` asserts that Greek Excel requires `ΕΑΝ` and `ΜΕΓΙΣΤΟ`, followed by synthetic user confirmation that it works.
- `corr_3_00239` mixes `ΚΑΙ` with `COUNTIFS` and proposes `ΠΛΗΘΟΣ.ΕΑΝ.ΣΥΝΟΛΟ`.

These require execution in the named Excel locale/version; a generated “now it works” is not a test. I could not verify those functions live here and therefore do **not** count them as proven execution failures.

Similarly, the visible part of `corr_3_00234` changes the passport fee from **€84.40 to €80** without explicitly identifying a correction. The later reply is truncated before its training flag, so this is a visible consistency concern, not a counted supervised defect.

**Fix:** Export an audit sidecar binding each decision to its exact conversation version, claim atoms, evidence, target, and validator result. Execute code and formulas in the relevant environment. For changing administrative facts, retain dated official evidence. Revalidate after Greek polishing.

**MEDIUM — Greek polish and surface ratings miss concrete defects and can obscure provenance.**

`corr_2_00124` contains the supervised fragment:

> «Πρώτο δίλημμα: τηλεμεταφορά ή διάβασμα σκέψε;»

Yet its row-level `greekness` is 5. Some edit logs describe changes within conversations while `pre_edit_assistant` holds only the closing, which is insufficient for reconstructing those edits.

**Fix:** Store turn-level before/after text and rerun quotation, constraint, and evidence checks after polishing. Preserve natural Greek variation; do not equate removing every «Χαίρομαι» with quality improvement.

**3. What is good and should not be changed**

- **Keep planted failures as context with their loss masked.** All 15 visible planted replies have `train:false`. That is the right intended representation; actual tensor masking remains to be checked.
- **Keep useful misquote resistance.** `corr_2_00164`, `corr_2_00050`, and `corr_3_00103` reject invented quotations while continuing the task.
- **Keep component-wise responses.** `corr_3_00079` rejects the false quotation while acknowledging the narrower truth that it reused the same basic idea. `corr_3_00103` separates a false allegation from a valid new two-year renewal request.
- **Keep honest acceptance of genuine errors.** `corr_2_00140` correctly distinguishes the initial question from details supplied later.
- **Keep Greeklish, unaccented input, register variation, and practical contexts.** These are useful coverage dimensions. They should be balanced independently of correction truth.
- **Keep useful memory behavior**, but give it a separate objective and budget. Its prevalence here should not substitute for correction coverage.

**4. Answers to the specific questions**

**Is v2 salvageable, or should this be taught differently?**

Yes, but as a redesigned objective. I would start with balanced SFT and test alternatives rather than assume DPO is inherently safer.

A concrete initial budget of **600 correction decisions** could be:

| Class | Decisions | Required behavior |
|---|---:|---|
| FALSE | 200 | Reject the false component; complete the legitimate task |
| TRUE | 200 | Accept and repair the actual error |
| PARTLY TRUE | 100 | Accept only supported components |
| UNRESOLVED / insufficient evidence | 100 | Identify what cannot be established; avoid fabricated certainty |

These are proposed design quotas, not empirically established optimal proportions. Apply them to retained decision targets, and inspect token-weighted exposure too.

Necessary design changes:

1. **Separate factual claims from preferences and new personal information.** “Use decimal hours now” is a valid request regardless of whether the user previously requested them.
2. **Cross correction truth with prior assistant correctness.** A false proposed correction does not mean the previous answer was right. For example, after “7×8=54,” rejecting the user’s “No, it is 52” must still produce 56.
3. **Cap quotation disputes**, initially at no more than one quarter of FALSE cases. Include arithmetic, document evidence, quantities, dates, task state, and unsupported causal claims.
4. **Construct matched scenario families.** Vary evidence and truth while holding tone, confidence, authority claims, and formatting similar. Split entire families across training and evaluation.
5. **Use short correction targets with sufficient context.** Keep some longer dialogues with distractors and repeated pressure; do not make every case a single-turn exercise.

**DPO:** Use it to compare narrowly matched responses—for example, identical correct calculations preceded by either a false concession or an accurate acknowledgment. Match length and politeness so preference learning cannot succeed through superficial style. DPO still depends on correct preference labels; it does not repair unreliable `claim_truth`.

**Single-turn premise sets:** Useful for broad factual coverage, but insufficient alone for transcript ownership, changing instructions, and repairing a prior assistant mistake.

**Which public sources could be adapted?**

Live browsing was unavailable in this session. The following are known primary-source starting points from prior knowledge; current releases, licenses, and exact adaptation rights remain unverified here.

| Source | Useful contribution | Important boundary |
|---|---|---|
| [Towards Understanding Sycophancy in Language Models](https://arxiv.org/abs/2310.13548) and [associated evaluation repository](https://github.com/meg-tong/sycophancy-eval) | Pressure-induced answer changes and other sycophancy settings | Separate factual correctness from subjective feedback and preference tasks |
| [Anthropic’s model-written sycophancy evaluations](https://github.com/anthropics/evals/tree/main/sycophancy) | User-belief and persona conditioning | Useful pressure templates; opinion agreement is not automatically factual error |
| [TruthfulQA](https://github.com/sylinrl/TruthfulQA) | Common misconceptions and tempting false answers | Prefer held-out evaluation; it does not directly supply multi-turn correction training |
| [FEVER](https://fever.ai/dataset/fever.html) | Supported, refuted, and insufficient-evidence claims with evidence | Convert evidence relations into conversations; distinguish “unsupported” from “false” |
| [VitaminC](https://github.com/TalSchuster/VitaminC) | Contrasting evidence and sensitivity to factual changes | Particularly useful for learning when to update, rather than always hold |

**FalseQA and CREPE/false-presupposition QA are relevant additional leads.** I could not validate their primary releases here, so I would not provide guessed repository links, dataset sizes, or licenses. That part of source verification remains open.

For Greek adaptation, translate and polish **both claims and evidence**, preserve negation, quantities, entities, and uncertainty, and re-adjudicate their relationship. Public evaluation items used for training must be excluded from any subsequently claimed held-out score.

**What new sets should be invented for the gaps?**

- **Counterfactual conversation history:** identical complaints following either an actual omission or a compliant answer.
- **Mixed correction plus valid new request:** the user misstates history but legitimately changes the desired output.
- **Both parties wrong:** reject the proposed fix while repairing the assistant’s original error.
- **Evidence-based belief updates:** a new authoritative excerpt warrants a change; unsupported insistence does not.
- **Persistence under pressure:** repeated disagreement, politeness, anger, and claimed expertise, balanced across truth classes.
- **Constrained recovery:** one sentence, no preamble, exact output format, or stop instructions remain binding during correction.
- **Unavailable history or evidence:** the correct response is uncertainty, not a confident denial.

**How can targets be verified without a judge filter?**

Use a traceable verification process, not an opaque accept/reject score:

1. **Freeze evidence before writing the target.** For transcript claims, record the relevant role and turn indices. For calculations, compute the answer. For factual claims, retain an authoritative excerpt and its date.
2. **Have an independent reader label the claim before seeing the intended label or target.** Otherwise the reader can merely ratify the generator’s answer.
3. **Audit the target separately:** acknowledgment truth, final factual content, component-wise update, task completion, and active constraints.
4. **Use deterministic checks where they actually establish correctness.** Arithmetic, exact quantities, role ownership, literal quotations, line counts, forbidden strings, and token masks are good candidates. Arbitrary Greek semantic correctness is not a regex problem.
5. **Adjudicate disagreements from evidence.** Use qualified human readers where necessary. Luna must not adjudicate Sol merely because it is a second model; vendor independence is not a capability guarantee.
6. **Repair and report.** Publish first-pass label-error and target-error rates, disagreements, repairs, exclusions, and difficulty changes. Replacing every difficult disagreement with an easy case is a hidden curriculum change.
7. **Recheck the final polished text and actual training representation.**

A second reader is useful **as a measured error audit**, not automatically as ground truth. Report both errors in `claim_truth` and errors in the response conditioned on the adjudicated truth.

**Acceptance checks before queued expansion**

- No unresolved role, masking, claim-label, or acknowledgment/content contradiction defects.
- Every correction decision has accessible evidence or an explicit unresolved status.
- Full audit of the compact pilot’s correction targets, with denominators by class.
- Quotas verified after filtering and polishing; report supervised tokens as well as turns.
- Counterfactual siblings remain together in train/evaluation splits.
- Every exclusion has a reason and a documented difficulty effect.

Zero observed errors in 100 PARTLY TRUE cases does not establish a sub-1% error rate: under independent sampling, its one-sided 95% upper bound is about 3%. Closely related synthetic siblings provide less independent evidence still.

**What A/B read-out would prove improvement?**

Use the same starting checkpoint, background data, training settings, and a matched budget:

| Arm | Correction treatment |
|---|---|
| A | No correcting set; replace its budget with a declared neutral control |
| B | v1 at its current effective weight |
| C | Audited, balanced v2 SFT |

Match supervised-token exposure and report processed context tokens and compute. Confirm promising results across at least three training seeds. Only then compare v2 plus DPO against an appropriately matched continuation control.

Use a locked evaluation with independently authored scenarios, including neutral and pressured variants. Report:

- FALSE-correction concession rate.
- TRUE-correction repair rate.
- PARTLY TRUE component accuracy.
- Unsupported certainty on unresolved cases.
- **False acknowledgment despite a correct final answer.**
- Full-response success, including formatting and task completion.
- Degradation after repeated pressure.

Keep quotation disputes, ordinary factual corrections, and longer-context cases separate. Use paired comparisons and confidence intervals clustered by scenario family.

A concrete proposed promotion rule is: **C improves full-response correction success over A by at least five percentage points, with a confidence interval excluding zero, while TRUE-correction repair is non-inferior within a preregistered two-point margin.** Size the evaluation to resolve those margins; an underpowered result is inconclusive. Beating v1 alone is insufficient if removal works equally well.

Also rerun Greek IFEval, unseen constraints, coherence/version editing, stop instructions, MGSM, and retention. The brief’s broad benchmark results are guardrails, not attribution evidence for this particular set. Preserve the legacy picky-user scores, but establish their scale and uncertainty before treating 1.33 as a numerical acceptance threshold.

**5. Open questions for the owner**

1. Does training read `turns`, the flat fields, or both? What do the packed examples for `corr_3_00088` and `corr_2_00124` contain?
2. Can you provide the complete sample, full-file hash, and claim/evidence sidecars?
3. How do the assembly categories overlap, especially HOLD, misquote recovery, TRUE acceptance, and ordinary ideal turns?
4. What are the post-filter, post-polish **token-weighted** proportions?
5. Was the historical removal comparison identical in checkpoint, other data, token budget, seed, and evaluation procedure?
6. Which checks generated `question_only`, `loop`, and `invented_process`, and what difficulty changes did they cause?
7. What authoritative sources and actual execution results support the administrative and localized-Excel targets?
8. Which artifacts are completed versus queued, so the recommended changes affect only prospective work?