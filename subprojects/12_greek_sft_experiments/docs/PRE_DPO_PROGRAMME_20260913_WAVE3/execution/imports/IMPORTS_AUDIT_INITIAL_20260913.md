# Initial bounded audit of imported, personality-v4 and retention data

Date: 13 September 2026  
Reviewer lane: high review (G/F/P naming only)  
Scope: read-only audit of the completed **G3F2P1** assembly by a Sol audit agent. Its stored path retains the legacy internal directory name shown below. No additional model subprocesses or model calls were launched; there were no corpus edits, network fetches, GPU jobs or publication.

## Verdict

Do not reuse the current tool block in a new assembly. Its local exporter truncated function definitions at 1,500 characters, and that truncation is present in the full training records. At least **12,257/29,700 rows (41.27%)** have a schema payload that is exactly 1,500 characters and fails both JSON and Python-literal parsing. The broader parse-failure count is **13,879/29,700 (46.73%)**. This is an all-row, source-code-explained defect, not a clipped review preview.

The other audited blocks are not cleared by their existing checks. OpenMath is definitively the **GSM8K-source slice**, not the MATH slice; its 99,971/100,000 verification checked only the final boxed answer against the supplied expected answer. The deterministic full-row sample still found a contradictory/underdetermined premise in 1/4 OpenMath rows. Nemotron, Dolci chat/reasoning and multilingual retention need all-row structural filters followed by semantic stratified review. Personality v4 is small enough to read in full and must be bound to the actual serving capability contract before any further use.

## Evidence boundary and source identity

The final local assembly is:

- `/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/arms/R3_single/train.jsonl`
- 403,727 effective rows, 228,577,090 rendered tokens; SHA-256 `53cb197b1030ef19bbdc19358cdb9da0daece1170fdd395d0263ceda4fd95bca`.
- The assembly receipt and row ledger report zero train/dev overlap by ID or full message content and zero cross-block exact-content duplicates. The 27,688 within-train repeated contents are deliberate weighted copies elsewhere in the mix; among the blocks audited here, only personality repeats content.

The local receipts bind each assembly export by SHA-256, but the public-dataset exporters do **not pin an upstream revision**. Thus this audit can identify the repository/config/split and verify the exact local export, but it cannot reconstruct an immutable upstream row from repository identity alone. Dolci exports also discard most original metadata after selection. For the tool block, the untruncated upstream schemas are not available in the local final export; they require a clean re-export from a pinned upstream revision.

| final block | actual upstream identity and local assembly source | local population reaching assembly | final train unique / effective | weight | effective supervised tokens (% of 140,424,598) |
|---|---|---:|---:|---:|---:|
| `openmath_gsm` | `nvidia/OpenMathInstruct-2`, config `default`, split `train`, explicitly filtered by `problem_source.lower() == "gsm8k"`; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/openmath_gsm_raw.jsonl` | 100,000 exported; 99,971 boxed-answer matches; 99,942 after contamination; 999 dev | 98,943 / 98,943 | 1 | 15,332,053 (10.92%) |
| `nemotron_chat_a` | `nvidia/Nemotron-SFT-Instruction-Following-Chat-v3`, config `default`, split `chat`; exact-length filtered, seed-2026 shuffled and divided into A/B; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/nemotron_chat_a.jsonl` | 23,326 local eligible; 23,249 taken; 232 dev | 23,017 / 23,017 | 1 | 30,862,329 (21.98%) |
| `nemotron_chat_b` | same upstream and process; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/nemotron_chat_b.jsonl` | 23,566 local eligible; 23,496 taken; 234 dev | 23,262 / 23,262 | 1 | 31,695,432 (22.57%) |
| `dolci_chat` | `allenai/Dolci-Instruct-SFT`, rows with `domain == "Chat"`; local IDs are OASST1; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/dolci_chat.jsonl` | 5,305 raw local rows; 3,053 label/language-eligible; 3,039 taken; 30 dev | 3,009 / 3,009 | 1 | 822,450 (0.59%) |
| `dolci_reasoning` | `allenai/Dolci-Instruct-SFT`, `source_dataset == "Verifiable Reasoning"`; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/dolci_reasoning.jsonl` | 29,986 eligible; 29,939 taken; 299 dev | 29,640 / 29,640 | 1 | 6,795,526 (4.84%) |
| `dolci_tooluse` | `allenai/Dolci-Instruct-SFT`, `domain == "Tool Use"`; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/dolci_tooluse.jsonl` | 40,000 raw local rows; 39,984 language/identity-kept; 39,728 assembly-eligible; capped at 30,000; 300 dev | 29,700 / 29,700 | 1 | 9,156,934 (6.52%) |
| `smoltalk2_multilingual` | `HuggingFaceTB/smoltalk2`, config `SFT`, split `smoltalk_multilingual_8languages_lang_5_no_think`; `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/smoltalk2_multilingual.jsonl` | 25,000 raw local rows; 24,974 language/identity-kept; 20,411 label-intersection/taken; 204 dev | 20,207 / 20,207 | 1 | 8,117,982 (5.78%) |
| `personality` | local concatenation `/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/personality/personality_v3v4_final.jsonl`: 1,388 v3 + 192 v4 (144 H response-manner, 48 I capability-contract) | 1,580 source; 1,574 renderable; 1 contaminated; 69 dev | 1,504 / 6,016 | 4 | 959,288 (0.68%) |

Nemotron A+B therefore contribute **62,557,761/140,424,598 supervised tokens (44.55%)**, reproducing the previously reported 44.6%. Personality's repeated exposure rate is **4,512/6,016 = 75%**; every other audited block has 0 repeated-ID and 0 repeated-message exposures in the final train file. This says nothing about semantic near-duplicates.

The OpenMath source identity is established directly by `data/export_raw.py`: it streams `nvidia/OpenMathInstruct-2/default/train` and retains only rows whose `problem_source` is `gsm8k`. No MATH-source row enters `openmath_gsm`. Existing project documentation attributes these generated solutions to Llama-3.1-405B; that generator attribution was not independently re-fetched in this bounded pass.

## Full-record sample: 24 rows

The exact sample is [sample_24_full_rows.jsonl](./sample_24_full_rows.jsonl), with a readable rendering in [sample_24_rendered.md](./sample_24_rendered.md). Selection is deterministic: lowest SHA-256 rank from the fixed string `imports-audit-v1`, stratum and row ID. Quotas were 4 OpenMath; 2 each from Nemotron A/B; 2 each from Dolci chat/reasoning; 4 tool; 4 multilingual; and 2 each from personality-v4 H/I. Weighted personality copies were collapsed before selection. This is a diagnostic, equal-block sample, not a population-rate estimate.

| stratum | n | findings from the complete records |
|---|---:|---|
| OpenMath GSM | 4 | 3 internally sound elementary solutions. `1435929` asks about an unquantified fourth cake type; the answer acknowledges that it is unknown, assumes/ignores it, then gives an unconditional `38`. **1/4 premise defect.** |
| Nemotron A+B | 4 | Three useful multi-turn/code rows. `74214` calls `enum.Flag` the universal “industry standard” and overstates O(1), single-instruction and fixed-memory properties. **1/4 unsupported technical overclaim.** No deployment-capability row happened to fall in this random stratum. |
| Dolci chat + reasoning | 4 | `minimumtreeweighteddominatingancestor…` computes the correct pair `1 4` but violates the explicit single-line output contract by emitting a full derivation. One Spanish OASST row is explicitly dated 2023; another is speculative and weak. **1/4 certain format defect**, plus stale/weak-content flags. |
| Dolci tool use | 4 | Three schemas terminate inside a property definition: IDs ending `S2_74667`, `S2_876560`, and `S2_235057`. Their calls use arguments hidden by the cut. `S2_966434` has a complete parseable schema and coherent calls/results. **3/4 actual schema corruption.** |
| SmolTalk multilingual | 4 | German row `45130` says `das Louvre` instead of `der Louvre`; Spanish row `1385` receives no concrete editing request yet the target rewrites the supplied service pitch. The other Spanish code repair is useful; the second German row follows its constraints. **2/4 clear language/task defects.** |
| Personality v4 | 4 | Both H rows correctly preserve quantities and resist a false correction. `v4_I02_06` usefully acts on transcribed text without objecting to microphone input. `v4_I01_01` hard-codes inability to see images, so its correctness depends on the release/serving contract. **0/4 unconditional semantic defects; 1/4 deployment-dependent target.** |

The separate targeted follow-up is [targeted_defect_followup_rows.jsonl](./targeted_defect_followup_rows.jsonl), rendered in [targeted_defect_followup_rendered.md](./targeted_defect_followup_rendered.md). All 11 requested IDs were found as complete final records. It confirms:

- `openmath_gsm:2786602` contains the source contradiction “the rest become caterpillars” while the target silently changes them to butterflies.
- `openmath_gsm:2944737` cannot determine a school-wide mean without grade sizes; the target introduces equal sizes and reports 93 unconditionally.
- `openmath_gsm:2247265` chooses 600 miles each way; “600 miles, back and forth” remains ambiguous rather than proven wrong.
- `nemotron_chat_b:26840` asserts no storage/database/profile and that the transcript is “shredded”; `184544` asserts no image generation. Both require serving-policy evidence.
- All four targeted Dolci reasoning rows give explanations despite a whole-response exact-output request.
- Both targeted tool rows contain the same broken schemas in the complete final train file. One calls arguments whose definitions were cut; the other passes an Amazon ID to a Shein-review function with no visible `goods_id` field and repeats calls after receiving their results.

## Tool protocol: all-row result

The all-row structural scanner read all **29,700 unique final training rows**, extracting the complete message strings rather than previews.

| check | count | rate | interpretation |
|---|---:|---:|---|
| schema payload exactly 1,500 chars | 12,281 | 41.35% | direct signature of the exporter's `[:1500]` cap; 24 happen to parse at that boundary |
| exact-1,500 schema and parse failure | 12,257 | 41.27% | certain clipped/unusable visible schema minimum |
| any schema parse failure | 13,879 | 46.73% | includes 1,622 shorter malformed payloads; these need upstream comparison |
| row with a called function name absent from visible schema | 5,409 | 18.21% | audit flag, not a final defect rate; string syntax and arguments can create conservative regex false positives |
| rows with one or more function-call turns | 27,055 | 91.09% | remaining rows may intentionally teach direct answers |
| rows with function-result turns | 25,163 | 84.72% | protocol variants require classification |
| rows with a post-call assistant answer | 25,037 | 84.30% | call-only targets may be intentional; deployment contract decides |

The cause is in `data/export_core.py`: system `functions`, empty-content `function_calls` and `tool_calls` are sliced to 1,500 characters before writing the local export. The assembler later converts those already clipped strings into `<functions>` / `<function_calls>` training text. The repair is a pinned, lossless re-export followed by schema/call/result validation; editing the clipped JSONL cannot recover missing bytes.

## Next audit matrix

| dataset and denominator | all-row programmatic audit required before admission | semantic review after structural gate | bounded next sample |
|---|---|---|---:|
| Tool use, 29,700 final rows (prefer all 40,000 pinned upstream candidates) | Lossless schema parse; declared call name; argument names/types/required fields; call/result count and IDs; dependency provenance; role/protocol conversion; no post-result duplicate calls; final answer grounded in results. Quarantine the current block until re-export. | Review only structurally valid rows for whether the API selection, result use and refusal/handoff behavior teach the intended deployment protocol. | 300 valid rows, stratified by source ID prefix, turn count, number of functions/calls and direct-answer/call-only/final-answer protocol. |
| OpenMath GSM, 98,943 train rows | Preserve current box-vs-expected check; add `problem_source == gsm8k`, numeric/unit consistency, explicit whole-response format, duplicate problem-family and anomaly scans for missing quantities/contradictory predicates. Checker scope must be reported. | Re-solve and audit premises, every substantive step, units and answer completeness; do not infer soundness from the final box. | 300 rows, stratified by operation family, length/step count, unit/currency/percentage/mean/rate keywords and anomaly flags; separate 50 flagged-premise rows. |
| Nemotron A+B, 46,279 train rows | All-row capability/privacy/storage/creator/time claims; language; role alternation; turn count/length; exact/near duplicate and response-opening/closing patterns. Bind A/B to the same upstream revision and preserve prefilter counts. | Inspect coherence across turns, false-correction behavior, unsupported self-description, register and usefulness. | 384 rows: 192 per half, balanced across 3/5/7/9+ turns, length quartiles, capability flags and technical/nontechnical prompts. |
| Dolci reasoning, 29,640 train rows | Parse prompt output contract; verify complete assistant response, not extracted last line; run source oracle where available; family/near-duplicate census. | Check derivations and alternative valid answers for each family. | 300 rows across task families, oversampling every exact-output flag; 50 independent re-solves. |
| Dolci chat, 3,009 train rows | Language, dated/time-sensitive assertions, role completeness, identity/capability claims, exact/near duplicates and source-family preservation. | Native-language task fidelity and factual/helpfulness review. | 180 rows: 60 Spanish, 40 English, 20 each from other retained languages or all available if fewer. |
| SmolTalk multilingual, 20,207 train rows | Re-run language and multilingual identity/capability patterns on complete text; constraint checker where encoded; exact/near duplicate and source-template census. | Native-language grammar, task fidelity, cultural setting and assistant-persona review. | 300 rows: 60 each in de/fr/es/pt/it, split across constraint, code, editing and chat families. |
| Personality v4, 192 source rows; 4× exposure after holdout/filters | Validate message endings, loss-mask/EOS handling, placeholders, arithmetic/state retention, fact/capability claim ledger and release-manifest match. | **Read all 192 rows.** H: manners, false correction, stopping and request fidelity. I: each capability claim against the intended product, with conditional variants where tools vary. | 192/192, with a second reviewer on all 48 category-I rows and all disputed H rows. |

All semantic samples must preserve the full record and use separate targeted follow-up sets. Rates from targeted flags must not be mixed into random-sample denominators.

## Five certain row dispositions for the next revision

These are proposals only; the completed corpus remains unchanged.

1. **Quarantine `openmath_gsm:2786602`** until the problem is explicitly repaired to “the rest become butterflies” and the solution is rechecked. This changes a source premise, so it needs a recorded semantic-repair scope.
2. **Quarantine `openmath_gsm:2944737`** unless grade populations are supplied or the question explicitly asks for the unweighted mean of the three grade averages.
3. **Quarantine tool row ending `S2_909985`** until a lossless pinned re-export restores the complete `agents_get_profile` schema and validates its two arguments.
4. **Quarantine tool row ending `T2_274958`**; after re-export, verify the product/review API relationship, valid review arguments and remove the repeated post-result calls if they are not source-intended.
5. **Patch `dolci_reasoning:minimumtreeweighteddominatingancestor_diff_1_12_71abf88241_Hd0ejp`** by keeping the verified selection but making the complete assistant target exactly `1 4`, as its prompt requires. Preserve the derivation only in a separately prompted explanation variant.

## Delivered evidence

- [structural_metrics.json](./structural_metrics.json): effective/unique/repeated counts and all-row tool metrics.
- [sample_24_full_rows.jsonl](./sample_24_full_rows.jsonl): exact 24 sampled training records.
- [sample_24_rendered.md](./sample_24_rendered.md): complete readable rendering used for semantic inspection.
- [targeted_defect_followup_rows.jsonl](./targeted_defect_followup_rows.jsonl): 11 complete targeted records.
- [targeted_defect_followup_rendered.md](./targeted_defect_followup_rendered.md): readable targeted follow-up.
- [LOSSLESS_TOOL_REEXPORT_HANDOFF.md](./LOSSLESS_TOOL_REEXPORT_HANDOFF.md): bounded pilot and CPU-host full-run contract.
- [export_core_lossless.patch](./export_core_lossless.patch): cleanly applying, revision-pinned lossless exporter patch with isolated validation.
