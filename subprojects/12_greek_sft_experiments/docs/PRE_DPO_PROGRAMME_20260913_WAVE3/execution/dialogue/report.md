# Dialogue and correcting audit

Audit window: 2026-09-13 15:20:30–15:27:20 Europe/Athens. I reviewed 24 complete dialogues, comprising 310 messages and 155 assistant turns. Of those assistant turns, 142 are supervised and 13 are masked context. The review was performed by the Sol agent, with no additional model subprocess calls, GPU jobs, SSH work, training, or source mutation.

## Verdict

The correcting taxonomy is now reconciled. The often-cited 3,692 number is the pre-edit total of loss-bearing assistant turns, partitioned by mutually exclusive `kind`. The 114 true, 20 false, 6 partial and 3 unresolved counts are overlapping `after_claim` labels on those same turns. They must not be added to the kind counts. A later language check demoted one target, so the actual final correcting export contains **3,691** supervised turns. Later assembly filters reduce this to **3,487 supervised turns across 570 unique train/dev rows**; the training split contains **3,462 unique supervised turns across 565 rows**, presented twice.

The convskills artifact actually consumed by assembly is `v2/final/rows_final.jsonl`, which is byte-identical to `v2/reverify2/rows_final.jsonl`: 2,851 rows, SHA-256 `d267ce173e49ace38f161eddbfde42558c4c3bf471097c0e8839d7be5e30996f`. The older `v2/reverify/rows_final.jsonl` has 3,284 rows and a different hash. Reviews of that older file remain historical evidence but do not describe the final post-repair population.

Three certain supervised semantic defects in the 24-dialogue panel survive the completed assembly: `corr_3_00270` conflates lease commencement with the actual relocation date; `S5m_00789` assigns an absolute date to “next Saturday” without a serialized clock; and `S5m_00630` assumes a second diner who was never introduced. Each appears twice in the assembled training file. A fourth certain error, `corr_3_00066`’s three-versus-four self-count, was correctly contained as `train:false` context. `corr_3_00152` also has a certain metadata error: an unverified administrator claim is labeled false rather than unresolved, although that label is stripped before training and the refusal text does not depend on disproving the identity claim.

These are row-level findings. The targeted correcting panel was deliberately enriched for correction truth and misquotation, and the convskills panel has only two rows per lane. No corpus-wide defect rate is claimed.

## Exact taxonomy reconciliation

The assembly code increments `trainable_by_kind` once for every kept assistant turn and separately increments `kept_after_claim_*` when that turn follows a labeled claim. Recomputing the cross-tab from all 600 raw dialogues and the final export gives:

| Axis | Pre-edit supervised | Final supervised |
|---|---:|---:|
| Exclusive kind total | 3,692 | 3,691 |
| ideal | 2,755 | 2,755 |
| closing | 575 | 575 |
| recovery | 158 | 158 |
| misquote recovery | 199 | 198 |
| clarify | 5 | 5 |

| Secondary `after_claim` label | Pre-edit | Final |
|---|---:|---:|
| none | 3,549 | 3,549 |
| true | 114 | 113 |
| false | 20 | 20 |
| partial | 6 | 6 |
| unresolved / unverifiable | 3 | 3 |

The final demotion is `corr_3_00072`, an `ignore_change` misquote recovery following a true claim, rejected after editing for an invented administrative process. That single demotion explains both 3,692 → 3,691 and true 114 → 113.

The approximate 3,822 headline arose by treating overlapping axes as exclusive addends: ordinary ideal turns, closings, recoveries, misquote recoveries, and selected truth labels were mixed into one sum. The corrected reporting unit is a supervised assistant turn with one exclusive `kind`, plus zero or one secondary correction-truth label.

The final export and the completed training population are also different denominators. Twenty-four exported rows end on a user message and are rejected as unrenderable; six more exceed the assembly length limit. The remaining 570 unique rows contain 3,487 supervised and 431 masked assistant turns. Five rows, containing 25 supervised turns, go to development. The 565 training rows therefore contain 3,462 unique supervised turns and 427 masked context turns. With the configured two copies, the training exposure is 6,924 supervised-turn presentations. Among the 3,462 unique training targets, the secondary truth counts are true 108, false 20, partial 6, unresolved 3, and none 3,325.

## Speaker ownership and state

The raw correcting schema is easy to misread. Each `turns[i]` object describes the current assistant answer, but its `claim` and `claim_truth` fields describe the next user message generated after that answer. Its `after_claim` field describes the user claim to which the current answer responds. This is why speaker ownership must be joined by turn position rather than inferred from object nesting.

The final correcting export discards `claim`, `claim_truth`, `after_claim`, `probe`, `probe_ref`, and the hidden profile. It retains message roles, content, train flags, kind, assessment and verdict. That is adequate for training but inadequate for an independent correction-truth audit. A sidecar should carry stable user-turn IDs, the exact claim, its evidence, adjudicated truth class, and the target assistant-turn ID.

The `corr_3_00152` targeted case illustrates the problem. “I am a platform administrator” is not shown to be false by the dialogue. It is unresolved. The assistant can still say the claim cannot be verified and does not authorize disclosure. Relabeling it unresolved preserves the correct behavior while making the truth state honest.

## Masks and final assembly

In the 24 inspected dialogues, roles alternate correctly, no message is empty, every record ends on an assistant turn, and every record has a supervised target. The correcting half contains 77 supervised and 9 masked assistant turns; the convskills half contains 65 supervised and 4 masked assistant turns.

The assembly converter retains `train:false` only on assistant messages. The completed training receipt records 756 masked convskills context turns and 431 masked correcting context turns. The trainer builds one assistant-token group per assistant message and sets every token in a `train:false` group to label `-100`. I inspected the actual assembled line for `corr_3_00066`: both the planted repetition and its numerically wrong recovery remain present with `train:false`.

This is strong static and artifact evidence that masks survive serialization. I did not execute the tokenizer-level mask test in this bounded pass, so I do not claim a fresh tensor-level result. The exact tokenizer, packing configuration and output label dump should remain part of promotion evidence.

## The 24-dialogue panel

The correcting half used two deterministic rows per targeted class: false, true, partial, unresolved, misquotation, and ordinary. This is a fixture panel, not a probability sample. The convskills half used two deterministic rows from each final lane. The selection key and all IDs are in `sample_ids.json`.

Useful behavior in the inspected rows should be preserved:

- `corr_3_00008`, `corr_3_00152`, and `corr_3_00287` reject unsupported or false corrections without stock capitulation.
- `corr_3_00169` uses acknowledgements when the objection is genuinely valid or partly valid and narrows the claim rather than accepting everything. These acknowledgements are useful training, not language clutter.
- S1 count and ordered-list targets match the visible message history in both inspected rows.
- S2 keeps bullets or formal address across intervening turns and drops the constraint only when the user revokes it.
- The inspected S3 and S3c transformations maintain the requested list/shortening/word-removal state.
- Both S4 rows keep the planted tic turns masked and omit the prohibited tic in later supervised answers.

The defects and unresolved areas are deliberately separated:

- Confirmed prior finding that survives final assembly: `corr_3_00270` turns the lease start into the actual relocation date and computes a deadline from it.
- Newly identified row in an already documented defect class: `S5m_00789` renders “next Saturday” as 12 September without a reference date. It also carries the user-side template artifact `η/ο`; that is a language/template repair, not semantic repair.
- Newly identified row-specific unsupported assumption: `S5m_00630` budgets a meal for two although the conversation contains only the user.
- Contained defect: `corr_3_00066` says a phrase occurred three times when it occurred four times. The checker masks the recovery; a precise patch can salvage it.
- Needs evidence rather than a defect verdict: current administrative routes, legal deadlines, restaurant availability, transport policies, museum prices, school procedure and similar external claims in several sampled rows. The transcript contains no dated evidence pack sufficient to certify them.

One targeted correcting row, `corr_2_00244`, is present in the final export but absent from the assembled training file after later filtering. The other 23 sampled dialogues appear twice in the assembled training file. This distinction is recorded per sample rather than treating final export and final training population as identical.

## Repairs

Five semantic-repair records are provided in `proposed_semantic_patches.jsonl`. Three contain bounded candidate changes. P001 and P005 are marked `needs_evidence`: no statutory deadline or replacement meal price is promoted as gold. The records preserve the settled scenario and teaching objective, do not perform Greek style rewriting, and do not alter source files. The `η/ο` template artifact is excluded because it belongs to language/template correction.

## Relation to prior reviews

I treated existing reviews as prior evidence. The lease-date conflation in `corr_3_00270`, the missing temporal anchor class, template artifacts, external-evidence gap, and the need to preserve speaker-linked claim metadata were already documented. This audit confirms whether those issues remain in the exact final artifacts and adds only the new row IDs and exact taxonomy cross-tab. It does not relabel those prior findings as new discoveries.

Files produced: `source_manifest.json`, `sample_ids.json`, `findings.jsonl`, `proposed_semantic_patches.jsonl`, and this report. Original datasets, manifests, code and assembled files were not modified.
