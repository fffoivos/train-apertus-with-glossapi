# Recipe: 1-G4F6P1 (R4_full) versus 1-G3F2P1 (R3_single), 15 Sept 2026

## Training parameters

| parameter | R3_single | R4_full | change |
|---|---|---|---|
| attn_implementation | kernels-community/vllm-flash-attn3 | kernels-community/vllm-flash-attn3 |  |
| dataloader_num_workers | 4 | 4 |  |
| expected_train_rows | 403727 | 384010 | **changed** |
| expected_train_tokens | 228577090 | null | **changed** |
| extend_control_tokens | false | false |  |
| gradient_accumulation_steps | 4 | 4 |  |
| learning_rate | 1.0e-5 | 1.0e-5 |  |
| lr_scheduler_type | cosine_with_min_lr | cosine_with_min_lr |  |
| max_grad_norm | 1.0 | 1.0 |  |
| max_length | 4096 | 4096 |  |
| min_lr_rate | 0.1 | 0.1 |  |
| model_name_or_path | fffoivos/apertus-8b-greek-cpt | fffoivos/apertus-8b-greek-cpt |  |
| num_train_epochs | 1 | 1 |  |
| optim | adamw_torch_fused | adamw_torch_fused |  |
| per_device_eval_batch_size | 1 | 1 |  |
| per_device_train_batch_size | 1 | 1 |  |
| planned_world_size | 4 | 4 |  |
| pretokenized_masks | — | true | **changed** |
| require_apertus_control_ids | true | true |  |
| revision | 18-avg-uniform5-tokens30B-50B | 18-avg-uniform5-tokens30B-50B |  |
| save_steps | 750 | 750 |  |
| save_total_limit | 2 | 2 |  |
| seed | 42 | 42 |  |
| template_source | swiss-ai/Apertus-8B-Instruct-2509 | swiss-ai/Apertus-8B-Instruct-2509 |  |
| tokenizer_name_or_path | fffoivos/apertus-8b-greek-cpt | fffoivos/apertus-8b-greek-cpt |  |
| warmup_ratio | 0.03 | 0.03 |  |
| weight_decay | 0.0 | 0.0 |  |

Parent: the CPT base 1 (30–50B average) in both. One epoch, cosine 1e-5 → 1e-6, batch 16 × 4,096, seed 42 in both; the DATA and the SUPERVISION BEHAVIOUR changed (pretokenized_masks: true hands the validator labels to TRL; rounds 1-3 lost supervision after partial-character tokens), so gains are attributed to the pass as a whole, not to individual blocks; token totals are nominal assistant-content counts, not collator-supervised counts.

## Blocks (rows in the epoch; supervised tokens)

| block | R3_single rows | R3 supervised | R4_full rows | R4 supervised | share of supervised | change |
|---|---:|---:|---:|---:|---:|---|
| convskills | 5622 | 7198732 | — | — | — | removed |
| convskills_v2 | — | — | 3364 | 3860796 | 2.6% | **new** |
| correcting | 1130 | 1331892 | — | — | — | removed |
| dolci_chat | 3009 | 822747 | 3009 | 822747 | 0.6% |  |
| dolci_code_algo_20k | 5503 | 1150842 | 5498 | 1149912 | 0.8% | rows changed |
| dolci_precise_if_20k | 4116 | 1260250 | 4050 | 1251009 | 0.9% | rows changed |
| dolci_reasoning | 29640 | 6811400 | 29635 | 6810605 | 4.6% | rows changed |
| dolci_safety | 6174 | 1069805 | 6174 | 1069805 | 0.7% |  |
| dolci_science | 6537 | 3895068 | 6534 | 3893074 | 2.6% | rows changed |
| dolci_tooluse | 29700 | 9158985 | 29532 | 9082507 | 6.2% | rows changed |
| format_mc | — | — | 8157 | 52074 | 0.0% | **new** |
| greek_if | 29773 | 9775168 | 29773 | 9775168 | 6.6% |  |
| greek_math | 14070 | 1576830 | — | — | — | removed |
| greek_math_v2 | — | — | 30554 | 8380240 | 5.7% | **new** |
| greek_ours | 39600 | 12511146 | 39584 | 12474098 | 8.5% | rows changed |
| greek_rewrite | 1980 | 701720 | 1980 | 701720 | 0.5% |  |
| ifeval_like | 46037 | 6465346 | 46037 | 6465346 | 4.4% |  |
| math_en_gsm | — | — | 43954 | 5611212 | 3.8% | **new** |
| math_en_math | — | — | 14324 | 3117572 | 2.1% | **new** |
| nemotron_chat_a | 23017 | 30877076 | 22998 | 30842713 | 20.9% | rows changed |
| nemotron_chat_b | 23262 | 31708196 | 23234 | 31671553 | 21.5% | rows changed |
| openmath_gsm | 98943 | 15345687 | — | — | — | removed |
| personality | 6016 | 1494372 | 6016 | 1492404 | 1.0% |  |
| personality_v3 | — | — | 5 | 788 | 0.0% | **new** |
| puzzles | 9391 | 639325 | 9391 | 639325 | 0.4% |  |
| smoltalk2_multilingual | 20207 | 8118211 | 20207 | 8118211 | 5.5% |  |

Totals: R3_single 403727 rows, 151912798 supervised tokens (same basis as the table); R4_full 384010 rows, 226155190 tokens, 147282879 supervised tokens; dev 2362 rows.
Drops: {"dolci_tooluse(dev):control_chars": 3, "dolci_tooluse(dev):contaminated": 1, "dolci_tooluse:contaminated": 15, "nemotron_chat_a:control_chars": 10, "dolci_precise_if_20k:contaminated": 65, "dolci_tooluse:control_chars": 150, "dolci_reasoning:control_chars": 5, "nemotron_chat_b:control_chars": 19, "greek_ours:over_window": 10, "nemotron_chat_b:over_window": 3, "nemotron_chat_b:contaminated": 6, "nemotron_chat_a:over_window": 6, "greek_ours:contaminated": 2, "dolci_tooluse:over_window": 3, "dolci_precise_if_20k:control_chars": 1, "dolci_code_algo_20k:control_chars": 4, "greek_ours:control_chars": 4, "nemotron_chat_a:contaminated": 3, "dolci_science:control_chars": 3, "dolci_code_algo_20k:contaminated": 1, "personality_v3:contaminated": 1, "math_en_gsm:reference_not_confirmed": 27, "math_en_gsm:solution_answer_ne_label": 0, "math_en_gsm:contaminated": 12, "math_en_math:contaminated": 119, "math_en_math:reviewer_excluded": 9, "greek_math_v2:reference_not_confirmed": 10, "greek_math_v2:contaminated": 4, "convskills_v2:S5m_lane_dropped": 537, "convskills_v2:masked_turns_not_trainable": 378, "convskills_v2:reviewer_excluded": 81, "convskills_v2:over_window": 152, "convskills_v2:duplicate_id": 4, "correcting_v2:block_dropped_masks_not_honoured": 337}. Waived (disclosed): {"dolci_precise_if_20k(dev):ifeval_en_cache_waived": 13, "ifeval_like(dev):ifeval_en_cache_waived": 275, "ifeval_like:ifeval_en_cache_waived": 28299, "dolci_precise_if_20k:ifeval_en_cache_waived": 855}. Label check (blind solve, positive join): {"problems": 12028, "solved": 12028, "agreed": 11034, "disagree": 994, "unsolved": 0, "numeric_fallback_rescues": 29}; per-block label counts: {"en_gsm_agreed": 20526, "en_gsm_disagreed_KEPT": 1463, "en_gsm_reviewer_excluded": 27, "en_gsm_conflicting_reference_problems": 0, "en_gsm_no_canonical_ref": 1463, "en_gsm_label_ne_reference": 1, "en_gsm_solution_answer_ne_label_KEPT": 1465, "en_math_published_exempt": 7290, "greek_agreed": 9533, "greek_disagreed_KEPT": 794, "greek_reviewer_excluded": 10, "greek_native_exempt": 5108}. Personality overlays: {"added": 6, "applied": 29, "occurrences_replaced": 116}. Dev rows removed for overlap: 559.
Bindings: train sha256 97d338ba2c126a4cc6cff273fb1e3f219c6808a01d78e17c60b0257c9aa8f8b5, dev sha256 b8a480f0377c475f759da94f231e86ec04ca81d540b4d7fcf65a504e364dc0f7; evaluation caches, code and input identities in receipt['identities'].

Changes (data and supervision): OpenMath GSM8K ×13.5 → GSM8K ≤3 solutions per problem (blind-solve filtered) + published MATH ×2; terse cut-1 Greek maths → cut-2 worked solutions + Level 5 + native ×2 (filtered); correcting v1 removed and v2 NOT added (decision for this pass: no masked rows; the pretokenized path honours masks, the raw-message path of rounds 1-3 did not); conversation suite v2 final; personality overlays applied; format block (English MC, few-shot as dialogue) added; every row re-decontaminated (8-gram + 13-gram, every cache) and re-checked for control characters and the 4,096 window. Disclosed exemption: for ifeval_like and dolci_precise_if_20k a hit on the English IFEval cache alone is kept (instruction-template overlap by construction; IFEval-en is not in the battery; counts in the receipt as ifeval_template_overlap_kept); hits on any other cache drop the row.
