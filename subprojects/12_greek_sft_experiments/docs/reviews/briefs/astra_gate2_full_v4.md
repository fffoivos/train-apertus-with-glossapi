Review target: GATE 2 (assembly + launch readiness) for the from-scratch pass 1-G4F6P1 (legacy R4_full). FOURTH pass. Your v3 verdict (docs/reviews/ASTRA_gate2_full_v3_20260915.md): HOLD on H1 (packing/collator path) and H2 (GSM last-number check). H1 led to a confirmed DEFECT: cluster/sft_train.py hands raw messages to TRL SFTTrainer with assistant_only_loss=True (function _dataset, lines 576-577; run(), lines 758-766); TRL renders with the patched template whose generation markers cover every assistant turn, so the per-message train=false flag is honoured only by the trainer's validator (tokenize_messages), never in training. Consequence for this pass (data-only, no trainer change tonight): correcting_v2 is dropped whole (its planted failures would be learned), conversation-suite rows with masked context turns (S4 lane) are dropped, the format block's demonstration answers are declared supervised (they are correct letters; the flags were removed so the receipt states what is trained), and the assembler asserts that no train=false turn remains anywhere in the manifest. Round 3 (1-G3F2P1) was affected by the same defect (correcting v1 x2, S4 rows) - logged in the ledger. The trainer fix (pre-tokenized dataset with assistant_masks) is a separate change to be verified with a short real run before the next pass. H2: the English GSM solution check now requires a boxed answer equal to the agreed label (no last-number fallback; drop count in the receipt). Window: the dry-run's validate_and_tokenize_data renders EVERY row with the real tokenizer and raises on any row over max_length ("truncation is forbidden", lines 395-421), so DRY_RUN_OK is an affirmative pre-truncation window check for all rows. THIRD pass notes retained below. Your verdicts: v1 docs/reviews/ASTRA_gate2_full_20260915.md (HOLD), v2 docs/reviews/ASTRA_gate2_full_v2_20260915.md (HOLD: F1 inspection absent, F2 dev rows bypassing checks, F3 family isolation; F4-F8 logged). Fixes since v2, mapped:
F1: §I now holds the trainer-side inspection produced with the trainer's own tokenize_messages on the launch manifest and config (a format row with 3 masked demonstrations and only the final letter supervised, a suite row with 2 masked turns, a correcting row with the planted turn masked, a maths row fully supervised), plus the trainer code excerpt showing that per-token labels (-100 for masked positions) are built BEFORE packing and that TRL's BFD packing concatenates pre-tokenized examples with their assistant masks (no re-rendering after packing). Window: the assembler enforces <= 4,096 tokens per row (drops recorded as over_window in the receipt); the dry-run printed no truncation or drop line.
F2: explicit dev rows (Greek maths dev families, format dev questions) now go through the same check_row (control characters, contamination, window); their drops are recorded under '<block>(dev)'.
F3: no random maths dev split remains (math_en_gsm and math_en_math have dev_frac 0); the only maths dev rows are the cut-2 dev families, whose English twins are excluded from both English blocks via dev_problems_en (family identity by problem); the overlap filter now removes a dev row if ANY of its user turns appears among train user turns (demonstrations included).
F4: every English GSM8K solution's own final answer must be equivalent to the agreed label (count in the receipt: math_en_gsm:solution_answer_ne_label); every Greek solution carries a high-effort derivation-validity record keyed to its exact text (cut-2 coverage ledger, provenance in docs/DATASET_PROVENANCE_LEDGER.md).
F5: the finalizer now reconstructs the expected problem manifest (12,028) and reports missing/extra records (0/0) with a manifest hash; S5m is dropped by default (receipt records the arguments); --allow-unconfirmed refuses non-_dry arm names; identities now include the inherited dev file, dev_problems_en.json, the source-text maps, the personality patch, the launch config and the trainer code.
F6: the recipe table recounts round 3 with the same tokenizer functions (common basis) when the recount is present (§A states the basis).
F7: criteria refined in §J (any of (1)-(3) failing -> HOLD; native macro defined; tolerances named as such; format effect descriptive).
F8: noted for the data card.
No filesystem access: everything is inlined. Verdict GO / HOLD with concrete fixes.

=== §A RECIPE TABLE (docs/RECIPE_R4_full_20260915.md) ===
# Recipe: 1-G4F6P1 (R4_full) versus 1-G3F2P1 (R3_single), 15 Sept 2026

## Training parameters

| parameter | R3_single | R4_full | change |
|---|---|---|---|
| attn_implementation | kernels-community/vllm-flash-attn3 | kernels-community/vllm-flash-attn3 |  |
| dataloader_num_workers | 4 | 4 |  |
| expected_train_rows | 403727 | 379740 | **changed** |
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
| require_apertus_control_ids | true | true |  |
| revision | 18-avg-uniform5-tokens30B-50B | 18-avg-uniform5-tokens30B-50B |  |
| save_steps | 750 | 750 |  |
| save_total_limit | 2 | 2 |  |
| seed | 42 | 42 |  |
| template_source | swiss-ai/Apertus-8B-Instruct-2509 | swiss-ai/Apertus-8B-Instruct-2509 |  |
| tokenizer_name_or_path | fffoivos/apertus-8b-greek-cpt | fffoivos/apertus-8b-greek-cpt |  |
| warmup_ratio | 0.03 | 0.03 |  |
| weight_decay | 0.0 | 0.0 |  |

Parent: the CPT base 1 (30–50B average) in both. One epoch, cosine 1e-5 → 1e-6, batch 16 × 4,096, seed 42 in both; only the data changed.

## Blocks (rows in the epoch; supervised tokens)

| block | R3_single rows | R3 supervised | R4_full rows | R4 supervised | share of supervised | change |
|---|---:|---:|---:|---:|---:|---|
| convskills | 5622 | 7198732 | — | — | — | removed |
| convskills_v2 | — | — | 3490 | 4073892 | 2.8% | **new** |
| correcting | 1130 | 1331892 | — | — | — | removed |
| dolci_chat | 3009 | 822747 | 3009 | 822747 | 0.6% |  |
| dolci_code_algo_20k | 5503 | 1150842 | 5498 | 1149912 | 0.8% | rows changed |
| dolci_precise_if_20k | 4116 | 1260250 | 4050 | 1251009 | 0.9% | rows changed |
| dolci_reasoning | 29640 | 6811400 | 29635 | 6810605 | 4.7% | rows changed |
| dolci_safety | 6174 | 1069805 | 6174 | 1069805 | 0.7% |  |
| dolci_science | 6537 | 3895068 | 6534 | 3893074 | 2.7% | rows changed |
| dolci_tooluse | 29700 | 9158985 | 29532 | 9082507 | 6.2% | rows changed |
| format_mc | — | — | 8199 | 52450 | 0.0% | **new** |
| greek_if | 29773 | 9775168 | 29773 | 9775168 | 6.7% |  |
| greek_math | 14070 | 1576830 | — | — | — | removed |
| greek_math_v2 | — | — | 28972 | 7722736 | 5.3% | **new** |
| greek_ours | 39600 | 12511146 | 39584 | 12474098 | 8.5% | rows changed |
| greek_rewrite | 1980 | 701720 | 1980 | 701720 | 0.5% |  |
| ifeval_like | 46037 | 6465346 | 46037 | 6465346 | 4.4% |  |
| math_en_gsm | — | — | 41080 | 5175722 | 3.5% | **new** |
| math_en_math | — | — | 14342 | 3124372 | 2.1% | **new** |
| nemotron_chat_a | 23017 | 30877076 | 22998 | 30842713 | 21.1% | rows changed |
| nemotron_chat_b | 23262 | 31708196 | 23234 | 31671553 | 21.6% | rows changed |
| openmath_gsm | 98943 | 15345687 | — | — | — | removed |
| personality | 6016 | 1494372 | 6016 | 1493880 | 1.0% |  |
| personality_v3 | — | — | 5 | 788 | 0.0% | **new** |
| puzzles | 9391 | 639325 | 9391 | 639325 | 0.4% |  |
| smoltalk2_multilingual | 20207 | 8118211 | 20207 | 8118211 | 5.5% |  |

Totals: R3_single 403727 rows, 140424598 supervised tokens (sum of blocks); R4_full 379740 rows, 224971349 tokens, 146411633 supervised tokens; dev 2342 rows.
Drops: {"dolci_tooluse(dev):control_chars": 3, "dolci_tooluse(dev):contaminated": 1, "dolci_tooluse:contaminated": 15, "nemotron_chat_a:control_chars": 10, "dolci_precise_if_20k:contaminated": 65, "dolci_tooluse:control_chars": 150, "dolci_reasoning:control_chars": 5, "nemotron_chat_b:control_chars": 19, "greek_ours:over_window": 10, "nemotron_chat_b:over_window": 3, "nemotron_chat_b:contaminated": 6, "nemotron_chat_a:over_window": 6, "greek_ours:contaminated": 2, "dolci_tooluse:over_window": 3, "dolci_precise_if_20k:control_chars": 1, "dolci_code_algo_20k:control_chars": 4, "greek_ours:control_chars": 4, "nemotron_chat_a:contaminated": 3, "dolci_science:control_chars": 3, "dolci_code_algo_20k:contaminated": 1, "personality_v3:contaminated": 1, "math_en_gsm:reference_not_confirmed": 1463, "math_en_gsm:solution_answer_ne_label": 1, "math_en_gsm:contaminated": 12, "math_en_math:contaminated": 119, "greek_math_v2:reference_not_confirmed": 809, "greek_math_v2:contaminated": 4, "convskills_v2:S5m_lane_dropped": 537, "convskills_v2:masked_turns_not_trainable": 378, "convskills_v2:over_window": 169, "convskills_v2:duplicate_id": 4, "correcting_v2:block_dropped_masks_not_honoured": 337}. Waived (disclosed): {"dolci_precise_if_20k(dev):ifeval_en_cache_waived": 13, "ifeval_like(dev):ifeval_en_cache_waived": 275, "ifeval_like:ifeval_en_cache_waived": 28299, "dolci_precise_if_20k:ifeval_en_cache_waived": 855}. Label check (blind solve, positive join): {"problems": 12028, "solved": 12028, "agreed": 11019, "disagree": 1009, "unsolved": 0, "numeric_fallback_rescues": 4}; per-block label counts: {"en_gsm_agreed": 20553, "en_gsm_dropped": 1463, "en_math_published_exempt": 7290, "greek_agreed": 9528, "greek_disagreed": 809, "greek_native_exempt": 5108}. Personality overlays: {"added": 6, "applied": 29}. Dev rows removed for overlap: 560.
Bindings: train sha256 c9d6f405ccb0c2506019c62f7f1d3e61a98dcc023c8814ddb82feef07ad0cf29, dev sha256 7d6a73f99bd57816b3878d36a3b4e87441fa01f13a848b8b4ac726e3e7c43315; evaluation caches, code and input identities in receipt['identities'].

Changes, all data: OpenMath GSM8K ×13.5 → GSM8K ≤3 solutions per problem (blind-solve filtered) + published MATH ×2; terse cut-1 Greek maths → cut-2 worked solutions + Level 5 + native ×2 (filtered); correcting v1 → v2; conversation suite v2 final; personality overlays applied; format block (English MC, few-shot as dialogue) added; every row re-decontaminated (8-gram + 13-gram, every cache) and re-checked for control characters and the 4,096 window. Disclosed exemption: for ifeval_like and dolci_precise_if_20k a hit on the English IFEval cache alone is kept (instruction-template overlap by construction; IFEval-en is not in the battery; counts in the receipt as ifeval_template_overlap_kept); hits on any other cache drop the row.

=== §B RECEIPT (data/arms/R4_full/receipt.json) ===
{
 "arm": "R4_full",
 "seed": 42,
 "args": {
  "arm": "R4_full",
  "seed": 42,
  "allow_unconfirmed": false,
  "keep_s5m": false,
  "drop_s5m": true
 },
 "tokenizer": "apertus-tokenizer (content only, +8 per turn; the trainer dry-run gives the exact rendered count)",
 "base": "data/arms/R3_single",
 "base_rows": 403727,
 "removed_configs": [
  "convskills",
  "correcting",
  "greek_math",
  "openmath_gsm"
 ],
 "label_check": {
  "problems": 12028,
  "solved": 12028,
  "agreed": 11019,
  "disagree": 1009,
  "unsolved": 0,
  "numeric_fallback_rescues": 4
 },
 "blocks": [
  {
   "block": "math_en_gsm",
   "input_rows": 20552,
   "kept": 20540,
   "dev": 0,
   "copies": 2,
   "train_rows_effective": 41080
  },
  {
   "block": "math_en_math",
   "input_rows": 7290,
   "kept": 7171,
   "dev": 0,
   "copies": 2,
   "train_rows_effective": 14342
  },
  {
   "block": "greek_math_v2",
   "input_rows": 14490,
   "kept": 14486,
   "dev": 146,
   "copies": 2,
   "train_rows_effective": 28972
  },
  {
   "block": "convskills_v2",
   "input_rows": 1936,
   "kept": 1763,
   "dev": 18,
   "copies": 2,
   "train_rows_effective": 3490
  },
  {
   "block": "format_mc",
   "input_rows": 8199,
   "kept": 8199,
   "dev": 71,
   "copies": 1,
   "train_rows_effective": 8199
  }
 ],
 "drops": {
  "dolci_tooluse(dev):control_chars": 3,
  "dolci_tooluse(dev):contaminated": 1,
  "dolci_tooluse:contaminated": 15,
  "nemotron_chat_a:control_chars": 10,
  "dolci_precise_if_20k:contaminated": 65,
  "dolci_tooluse:control_chars": 150,
  "dolci_reasoning:control_chars": 5,
  "nemotron_chat_b:control_chars": 19,
  "greek_ours:over_window": 10,
  "nemotron_chat_b:over_window": 3,
  "nemotron_chat_b:contaminated": 6,
  "nemotron_chat_a:over_window": 6,
  "greek_ours:contaminated": 2,
  "dolci_tooluse:over_window": 3,
  "dolci_precise_if_20k:control_chars": 1,
  "dolci_code_algo_20k:control_chars": 4,
  "greek_ours:control_chars": 4,
  "nemotron_chat_a:contaminated": 3,
  "dolci_science:control_chars": 3,
  "dolci_code_algo_20k:contaminated": 1,
  "personality_v3:contaminated": 1,
  "math_en_gsm:reference_not_confirmed": 1463,
  "math_en_gsm:solution_answer_ne_label": 1,
  "math_en_gsm:contaminated": 12,
  "math_en_math:contaminated": 119,
  "greek_math_v2:reference_not_confirmed": 809,
  "greek_math_v2:contaminated": 4,
  "convskills_v2:S5m_lane_dropped": 537,
  "convskills_v2:masked_turns_not_trainable": 378,
  "convskills_v2:over_window": 169,
  "convskills_v2:duplicate_id": 4,
  "correcting_v2:block_dropped_masks_not_honoured": 337
 },
 "base_removed_rows": 119765,
 "personality_overlays": {
  "added": 6,
  "applied": 29
 },
 "waived": {
  "dolci_precise_if_20k(dev):ifeval_en_cache_waived": 13,
  "ifeval_like(dev):ifeval_en_cache_waived": 275,
  "ifeval_like:ifeval_en_cache_waived": 28299,
  "dolci_precise_if_20k:ifeval_en_cache_waived": 855
 },
 "base_dev_kept": 2667,
 "base_kept_after_checks": 283657,
 "format_mc_demonstrations": "supervised (correct letters); the train=false flags were removed because the training path does not honour them",
 "dev_rows_removed_for_overlap": 560,
 "train": {
  "rows": 379740,
  "tokens": 224971349,
  "supervised_tokens": 146411633,
  "by_config": {
   "convskills_v2": {
    "rows": 3490,
    "tokens": 5933932,
    "supervised": 4073892,
    "share_supervised": 0.0278
   },
   "dolci_chat": {
    "rows": 3009,
    "tokens": 990738,
    "supervised": 822747,
    "share_supervised": 0.0056
   },
   "dolci_code_algo_20k": {
    "rows": 5498,
    "tokens": 2187008,
    "supervised": 1149912,
    "share_supervised": 0.0079
   },
   "dolci_precise_if_20k": {
    "rows": 4050,
    "tokens": 2070024,
    "supervised": 1251009,
    "share_supervised": 0.0085
   },
   "dolci_reasoning": {
    "rows": 29635,
    "tokens": 15397559,
    "supervised": 6810605,
    "share_supervised": 0.0465
   },
   "dolci_safety": {
    "rows": 6174,
    "tokens": 1488016,
    "supervised": 1069805,
    "share_supervised": 0.0073
   },
   "dolci_science": {
    "rows": 6534,
    "tokens": 5715502,
    "supervised": 3893074,
    "share_supervised": 0.0266
   },
   "dolci_tooluse": {
    "rows": 29532,
    "tokens": 32678055,
    "supervised": 9082507,
    "share_supervised": 0.062
   },
   "format_mc": {
    "rows": 8199,
    "tokens": 1816051,
    "supervised": 52450,
    "share_supervised": 0.0004
   },
   "greek_if": {
    "rows": 29773,
    "tokens": 15340030,
    "supervised": 9775168,
    "share_supervised": 0.0668
   },
   "greek_math_v2": {
    "rows": 28972,
    "tokens": 11290162,
    "supervised": 7722736,
    "share_supervised": 0.0527
   },
   "greek_ours": {
    "rows": 39584,
    "tokens": 19267428,
    "supervised": 12474098,
    "share_supervised": 0.0852
   },
   "greek_rewrite": {
    "rows": 1980,
    "tokens": 1735320,
    "supervised": 701720,
    "share_supervised": 0.0048
   },
   "ifeval_like": {
    "rows": 46037,
    "tokens": 10779096,
    "supervised": 6465346,
    "share_supervised": 0.0442
   },
   "math_en_gsm": {
    "rows": 41080,
    "tokens": 8347624,
    "supervised": 5175722,
    "share_supervised": 0.0354
   },
   "math_en_math": {
    "rows": 14342,
    "tokens": 4417196,
    "supervised": 3124372,
    "share_supervised": 0.0213
   },
   "nemotron_chat_a": {
    "rows": 22998,
    "tokens": 34665350,
    "supervised": 30842713,
    "share_supervised": 0.2107
   },
   "nemotron_chat_b": {
    "rows": 23234,
    "tokens": 35554975,
    "supervised": 31671553,
    "share_supervised": 0.2163
   },
   "personality": {
    "rows": 6016,
    "tokens": 1882652,
    "supervised": 1493880,
    "share_supervised": 0.0102
   },
   "personality_v3": {
    "rows": 5,
    "tokens": 1350,
    "supervised": 788,
    "share_supervised": 0.0
   },
   "puzzles": {
    "rows": 9391,
    "tokens": 3162861,
    "supervised": 639325,
    "share_supervised": 0.0044
   },
   "smoltalk2_multilingual": {
    "rows": 20207,
    "tokens": 10250420,
    "supervised": 8118211,
    "share_supervised": 0.0554
   }
  },
  "sha256": "c9d6f405ccb0c2506019c62f7f1d3e61a98dcc023c8814ddb82feef07ad0cf29"
 },
 "dev": {
  "rows": 2342,
  "by_config": {
   "dolci_reasoning": 173,
   "greek_if": 300,
   "smoltalk2_multilingual": 204,
   "puzzles": 80,
   "nemotron_chat_b": 110,
   "greek_ours": 183,
   "dolci_tooluse": 248,
   "ifeval_like": 430,
   "personality": 69,
   "greek_math_v2": 146,
   "nemotron_chat_a": 95,
   "dolci_precise_if_20k": 41,
   "greek_rewrite": 20,
   "dolci_code_algo_20k": 55,
   "dolci_chat": 29,
   "format_mc": 71,
   "dolci_science": 28,
   "dolci_safety": 60
  },
  "sha256": "7d6a73f99bd57816b3878d36a3b4e87441fa01f13a848b8b4ac726e3e7c43315"
 },
 "label_counts": {
  "en_gsm_agreed": 20553,
  "en_gsm_dropped": 1463,
  "en_math_published_exempt": 7290,
  "greek_agreed": 9528,
  "greek_disagreed": 809,
  "greek_native_exempt": 5108
 },
 "identities": {
  "eval_caches": {
   "english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl": {
    "rows": 28449,
    "sha256": "1fb6d83577ea62df8009a4bfd2d5e2f9cdd4c2ed39103f25867c8f46f8d24246"
   },
   "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl": {
    "rows": 16632,
    "sha256": "52395e626d8ecd4ffe6219acd41df252987eb4a83da59cd01627b0be00b35411"
   },
   "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl": {
    "rows": 1319,
    "sha256": "12d2145d474994b29bd487cfd2cd3a01a725e30cca4f0850da5df2a07f4b2d77"
   },
   "ifbench_el.jsonl": {
    "rows": 586,
    "sha256": "607ae20febafc841db52accba26fcc6f05a81e3279174ec82a04c3023dad283f"
   },
   "ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl": {
    "rows": 541,
    "sha256": "e0c1fda7f338da3d98bb178ec4a382935d0f4fced2c33816564e98759d567c21"
   },
   "math200_confirm.jsonl": {
    "rows": 400,
    "sha256": "000148d2dc47429d8e1b923710d594228aa502e5c019f095b091c890cee4ea9f"
   },
   "math500_el.jsonl": {
    "rows": 1000,
    "sha256": "e29827dc3b18f3d7111a00ac1052abc9e7b5b6b16c6256d1f962bcc6d201397f"
   },
   "mgsm_el.jsonl": {
    "rows": 250,
    "sha256": "b96a9dd2dce9f4de655bf8e3b6282e171579145ca84622b705302fe483be848b"
   },
   "multichallenge_el.jsonl": {
    "rows": 3308,
    "sha256": "72468f1e202d692670aa7bad15b68b96f76eb373080c889fad21a98b07938aab"
   },
   "native_asep_mcqa.jsonl": {
    "rows": 2346,
    "sha256": "f8230d120358733971d16499e1f7b4d1c431b6f801d34c1580b9b2beb77e8ffb"
   },
   "native_demosqa.jsonl": {
    "rows": 600,
    "sha256": "3d76983757fa114be1463a406465d4d076f82dd6761869736367737dc5b8f67f"
   },
   "native_gpcr.jsonl": {
    "rows": 208,
    "sha256": "ae256518ef62f101306ee9a5c9a74f4ff2896a48cc8509cebd09ce16d2cea397"
   },
   "native_medical_mcqa.jsonl": {
    "rows": 432,
    "sha256": "ae4f93469beca70f574ae29dfcbfe6021fc73a9416c15bd8d2e6244f42101051"
   },
   "xstest_el.jsonl": {
    "rows": 900,
    "sha256": "b3a910ef5cccade2987752e172346a39a40bc79b4761c2e8273b96ba18ddbc89"
   }
  },
  "caches_used_for_waiver_check": [
   "english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl",
   "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl",
   "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl",
   "ifbench_el.jsonl",
   "math200_confirm.jsonl",
   "math500_el.jsonl",
   "mgsm_el.jsonl",
   "multichallenge_el.jsonl",
   "native_asep_mcqa.jsonl",
   "native_demosqa.jsonl",
   "native_gpcr.jsonl",
   "native_medical_mcqa.jsonl",
   "xstest_el.jsonl"
  ],
  "code": {
   "assemble_full_r4.py": "32ec5a3a45502e52fe8c0732d01b816226f7f72b9af2f25a9537d516108a000f",
   "mixlib.py": "7c1499628bcb2d2887cee1d650c4e6792172d58fe8523c66744000b732ba7895",
   "format_block/build_mc_fewshot.py": "6992743acf461fe3dda20f3b35a6820418562e0e822fb736635f0aab803c829f",
   "math/cut2/independent_solve.py": "df666f375a48fb9e2482990da29ffe49126d6575ae99db7df43d3b3e0bd3015d",
   "math/cut2/finalize_label_check.py": "1653b02ab689a7da42e92db52953d1524da909876bc45f949104a71bb224c1a9"
  },
  "inputs": {
   "arms/R3_single/train.jsonl": "53cb197b1030ef19bbdc19358cdb9da0daece1170fdd395d0263ceda4fd95bca",
   "arms/R3_single/dev.jsonl": "dcc82e988490bc490a5ce9fcd780ddfcc967cfca9f26f34746f5703e3ec18730",
   "math/cut2/final/dev_problems_en.json": "59268201c6d84073bbc6ee12574e7d70bcf92942ff1eb54c44c5b9d8f4aef31f",
   "math/cut2/prep/translations_with_reference.jsonl": "31700cc811006951849793814b13b763b40ea361d73e9ef5d8679b8e5d45ca3a",
   "math/cut2/out/level5_problems_el.jsonl": "733d26f7d23d60c63e9fa665726d44fd6c6e869cb4c42558156add6bad2bfcfc",
   "/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/personality/deployment_and_closure_patch.jsonl": "77f676c35eca1fc6b9e6d950e791e558d91e49973f3ba8f5648e75286f410357",
   "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/configs/R4_full.yaml": "f4f3f685174e404758d51d9acb13683522f3362ad50f33670f366bf33a9b7cc0",
   "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/sft_train.py": "f8de43b1f8b99959741e6c4a9158ad99fd31ffc5b3b1636c1ac07a925df39b4d",
   "math/en/gsm8k_dedup3.jsonl": "355f67695fe21e3bc24e6983ac554cd0369add7507efe882463933a4a5d9fd84",
   "math/en/math_train_published.jsonl": "f78ca1918ad706cc99214d9579cf81e05e6f8607a4b65bedf1155e3f1ee1e75e",
   "math/cut2/final/arm_M2.jsonl": "093525b1af54ab44e7a945488e4a0559e735c3aef9befe36aade5e757474afea",
   "convskills/v2/final/rows_final.jsonl": "d267ce173e49ace38f161eddbfde42558c4c3bf471097c0e8839d7be5e30996f",
   "robustness/correcting/v2/rows_v2.jsonl": "afa8a1904f3c8dc441d76638956bd0568750ff0cacf73cdaab1e105dfb4eebeb",
   "format_block/mc_fewshot_en.jsonl": "aab12bb4068992710483635205060580b6d608f70fa6b9b223bb2a1c6a7d72a2",
   "math/cut2/final/label_disagreements.json": "12b0902dad2b8296bcdd6c5493cfdaee8386d83c5b56171fa92056f401bb415b"
  },
  "model": {
   "name": "fffoivos/apertus-8b-greek-cpt",
   "revision": "18-avg-uniform5-tokens30B-50B",
   "template_source": "swiss-ai/Apertus-8B-Instruct-2509"
  }
 }
}
=== §C LABEL CHECK (independent blind solve, medium effort; positive join) ===
{
 "unsolved": [],
 "extra_records": [],
 "n_problems": 12028,
 "n_solved": 12028,
 "expected_manifest_sha256": "33e27e328398279e38098817574c33f0648c93672457e2c4e64133c986487a8a",
 "agreement": {
  "gsm8k:disagree": 302,
  "gsm8k:agree": 5435,
  "gsm8k_en_only:disagree": 200,
  "gsm8k_en_only:agree": 1491,
  "math:disagree": 507,
  "math:agree": 4093
 },
 "numeric_fallback_rescues": [
  {
   "id": "gsm_124",
   "answer": "10 pm",
   "ref": "10"
  },
  {
   "id": "gsm_2836",
   "answer": "852 BC",
   "ref": "852"
  },
  {
   "id": "gsm_3375",
   "answer": "10 months",
   "ref": "10"
  },
  {
   "id": "gsm_4112",
   "answer": "20 minutes",
   "ref": "20"
  }
 ],
 "rule": "kept only on a positive agreement record: equiv500, or strict numeric equality (audited list); disagreements dropped; native rows and the published English MATH solutions are outside the solve scope by recipe"
}
agreed ids: 11019, disagree ids: 1009 (first 20 disagree: ['gsm_1004', 'gsm_1007', 'gsm_1011', 'gsm_1036', 'gsm_1038', 'gsm_1061', 'gsm_1062', 'gsm_1078', 'gsm_1086', 'gsm_1104', 'gsm_1117', 'gsm_1136', 'gsm_1138', 'gsm_1148', 'gsm_1195', 'gsm_1196', 'gsm_1221', 'gsm_1232', 'gsm_1251', 'gsm_1255'])
per-block label counts from the receipt: {"en_gsm_agreed": 20553, "en_gsm_dropped": 1463, "en_math_published_exempt": 7290, "greek_agreed": 9528, "greek_disagreed": 809, "greek_native_exempt": 5108}
waived (disclosed): {"dolci_precise_if_20k(dev):ifeval_en_cache_waived": 13, "ifeval_like(dev):ifeval_en_cache_waived": 275, "ifeval_like:ifeval_en_cache_waived": 28299, "dolci_precise_if_20k:ifeval_en_cache_waived": 855}
identities: {
 "eval_caches": {
  "english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl": {
   "rows": 28449,
   "sha256": "1fb6d83577ea62df8009a4bfd2d5e2f9cdd4c2ed39103f25867c8f46f8d24246"
  },
  "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl": {
   "rows": 16632,
   "sha256": "52395e626d8ecd4ffe6219acd41df252987eb4a83da59cd01627b0be00b35411"
  },
  "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl": {
   "rows": 1319,
   "sha256": "12d2145d474994b29bd487cfd2cd3a01a725e30cca4f0850da5df2a07f4b2d77"
  },
  "ifbench_el.jsonl": {
   "rows": 586,
   "sha256": "607ae20febafc841db52accba26fcc6f05a81e3279174ec82a04c3023dad283f"
  },
  "ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl": {
   "rows": 541,
   "sha256": "e0c1fda7f338da3d98bb178ec4a382935d0f4fced2c33816564e98759d567c21"
  },
  "math200_confirm.jsonl": {
   "rows": 400,
   "sha256": "000148d2dc47429d8e1b923710d594228aa502e5c019f095b091c890cee4ea9f"
  },
  "math500_el.jsonl": {
   "rows": 1000,
   "sha256": "e29827dc3b18f3d7111a00ac1052abc9e7b5b6b16c6256d1f962bcc6d201397f"
  },
  "mgsm_el.jsonl": {
   "rows": 250,
   "sha256": "b96a9dd2dce9f4de655bf8e3b6282e171579145ca84622b705302fe483be848b"
  },
  "multichallenge_el.jsonl": {
   "rows": 3308,
   "sha256": "72468f1e202d692670aa7bad15b68b96f76eb373080c889fad21a98b07938aab"
  },
  "native_asep_mcqa.jsonl": {
   "rows": 2346,
   "sha256": "f8230d120358733971d16499e1f7b4d1c431b6f801d34c1580b9b2beb77e8ffb"
  },
  "native_demosqa.jsonl": {
   "rows": 600,
   "sha256": "3d76983757fa114be1463a406465d4d076f82dd6761869736367737dc5b8f67f"
  },
  "native_gpcr.jsonl": {
   "rows": 208,
   "sha256": "ae256518ef62f101306ee9a5c9a74f4ff2896a48cc8509cebd09ce16d2cea397"
  },
  "native_medical_mcqa.jsonl": {
   "rows": 432,
   "sha256": "ae4f93469beca70f574ae29dfcbfe6021fc73a9416c15bd8d2e6244f42101051"
  },
  "xstest_el.jsonl": {
   "rows": 900,
   "sha256": "b3a910ef5cccade2987752e172346a39a40bc79b4761c2e8273b96ba18ddbc89"
  }
 },
 "caches_used_for_waiver_check": [
  "english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl",
  "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl",
  "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl",
  "ifbench_el.jsonl",
  "math200_confirm.jsonl",
  "math500_el.jsonl",
  "mgsm_el.jsonl",
  "multichallenge_el.jsonl",
  "native_asep_mcqa.jsonl",
  "native_demosqa.jsonl",
  "native_gpcr.jsonl",
  "native_medical_mcqa.jsonl",
  "xstest_el.jsonl"
 ],
 "code": {
  "assemble_full_r4.py": "32ec5a3a45502e52fe8c0732d01b816226f7f72b9af2f25a9537d516108a000f",
  "mixlib.py": "7c1499628bcb2d2887cee1d650c4e6792172d58fe8523c66744000b732ba7895",
  "format_block/build_mc_fewshot.py": "6992743acf461fe3dda20f3b35a6820418562e0e822fb736635f0aab803c829f",
  "math/cut2/independent_solve.py": "df666f375a48fb9e2482990da29ffe49126d6575ae99db7df43d3b3e0bd3015d",
  "math/cut2/finalize_label_check.py": "1653b02ab689a7da42e92db52953d1524da909876bc45f949104a71bb224c1a9"
 },
 "inputs": {
  "arms/R3_single/train.jsonl": "53cb197b1030ef19bbdc19358cdb9da0daece1170fdd395d0263ceda4fd95bca",
  "arms/R3_single/dev.jsonl": "dcc82e988490bc490a5ce9fcd780ddfcc967cfca9f26f34746f5703e3ec18730",
  "math/cut2/final/dev_problems_en.json": "59268201c6d84073bbc6ee12574e7d70bcf92942ff1eb54c44c5b9d8f4aef31f",
  "math/cut2/prep/translations_with_reference.jsonl": "31700cc811006951849793814b13b763b40ea361d73e9ef5d8679b8e5d45ca3a",
  "math/cut2/out/level5_problems_el.jsonl": "733d26f7d23d60c63e9fa665726d44fd6c6e869cb4c42558156add6bad2bfcfc",
  "/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/personality/deployment_and_closure_patch.jsonl": "77f676c35eca1fc6b9e6d950e791e558d91e49973f3ba8f5648e75286f410357",
  "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/configs/R4_full.yaml": "f4f3f685174e404758d51d9acb13683522f3362ad50f33670f366bf33a9b7cc0",
  "/Users/foivoskarounos-zamparloukos/Projects/
Rule: a maths row is kept only where Sol's blind answer agrees with the source label (equiv500 or tolerant numeric equality); disagreements and unsolved problems are dropped from BOTH the Greek block and the English GSM8K block. The check is against Sol's medium-effort answer, so a wrong Sol answer drops a good row (cost: coverage), and a wrong label with a matching wrong Sol answer is not caught (bound stated in the ledger).
Solver script:
#!/usr/bin/env python3
"""Independent reference check (owner rule, 15 Sept): Sol solves every maths problem BLIND (English text, medium effort, no reference shown); a row keeps its
reference only where Sol's answer is equivalent (equiv500) to the source label; disagreements are dropped from the pass. Scope: every problem in the cut-2
export (GSM8K + MATH Levels 1-5) plus the GSM8K problems used only by the English block. Runs in chunks of 500 and stops if the weekly Codex meter reaches
CEILING (default 82). Writes out/independent_solve.jsonl and final/label_disagreements.json. Usage: WORKERS=48 python3 independent_solve.py [--ceiling 82]"""
import json, os, sys, argparse, collections, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, f'{ROOT}/data/benchmarks_el'); sys.path.insert(0, f'{ROOT}/data/benchmarks_el/math500'); sys.path.insert(0, f'{ROOT}/data/math')
import bench_lib as B, mathlib as M, equiv500 as E
ap = argparse.ArgumentParser(); ap.add_argument('--ceiling', type=float, default=82.0); ap.add_argument('--chunk', type=int, default=500); a = ap.parse_args()
SCH = M.write_schema('independent_solve', {'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer'], 'additionalProperties': False})
src = {json.loads(l)['id']: json.loads(l) for l in open(f'{HERE}/prep/translations_with_reference.jsonl')}
for l in open(f'{HERE}/out/level5_problems_el.jsonl'): r = json.loads(l); src.setdefault(r['id'], dict(r, ref=M.boxed(r['solution_en']) or ''))
items = {}
for f in ('rows_M1', 'rows_M2_extra'):
    for l in open(f'{HERE}/final/{f}.jsonl'):
        pid = re.sub(r'^c2_', '', json.loads(l)['id']); s = src[pid]; items[pid] = dict(id=pid, problem_en=s['problem_en'], ref=str(s.get('ref', '')), src='gsm8k' if pid.startswith('gsm') else 'math', level=str(s.get('level', '')))
gsm_en = {}
for l in open(f'{ROOT}/data/math/en/gsm8k_dedup3.jsonl'):
    r = json.loads(l); gsm_en.setdefault(r['problem'], r)
covered = {v['problem_en'] for v in items.values() if v['src'] == 'gsm8k'}; extra = 0
for prob, r in gsm_en.items():
    if prob not in covered:
        ref = str(r.get('expected_answer') or r.get('answer') or M.gsm_answer(r.get('reference_solution') or r.get('solution') or '') or ''); import hashlib; k = 'gsmen_' + hashlib.sha256(prob.encode('utf-8')).hexdigest()[:12]; items[k] = dict(id=k, problem_en=prob, ref=ref, src='gsm8k_en_only', level='gsm'); extra += 1
print(f'problems: {len(items)} ({extra} GSM8K problems only in the English block)', flush=True)
def solve(x):
    p = (f"Solve the following problem. Reply only with the final answer in 'answer': an exact value in its simplest form (integer, fraction a/b, decimal, or a LaTeX expression when the answer is symbolic); no units, no explanation.\n\nPROBLEM:\n{x['problem_en']}")
    r = B.sol_json(p, SCH, effort='medium'); return None if r is None else dict(id=x['id'], answer=r['answer'], ref=x['ref'], src=x['src'], level=x['level'])
out = f'{HERE}/out/independent_solve.jsonl'; done = {json.loads(l)['id'] for l in open(out)} if os.path.exists(out) else set()
todo = [v for k, v in items.items() if k not in done]
for i in range(0, len(todo), a.chunk):
    used = B.codex_limit()
    if used is not None and used >= a.ceiling: print(f'STOP: codex meter {used} >= ceiling {a.ceiling} with {len(todo) - i} problems left', flush=True); break
    B.run_jobs(todo[i:i + a.chunk], solve, out, stage=f'independent solve chunk {i // a.chunk + 1}')
rows = [json.loads(l) for l in open(out)]; agree = collections.Counter(); dis = []
for r in rows:
    ok = bool(E.equiv500(r['ref'], r['answer'])) if r['ref'] else False; agree[(r['src'], ok)] += 1
    if not ok: dis.append(r['id'])
print('agreement by source:', {f'{k[0]}:{"agree" if k[1] else "disagree"}': v for k, v in sorted(agree.items())}, '| unsolved (no record):', len(items) - len(rows), flush=True)
json.dump(dict(disagree=sorted(dis), unsolved=sorted(set(items) - {r['id'] for r in rows}), n_problems=len(items), n_solved=len(rows)), open(f'{HERE}/final/label_disagreements.json', 'w'), indent=1)
print('written final/label_disagreements.json', flush=True)

Finalizer:
#!/usr/bin/env python3
"""Independent-solve agreement (owner rule 15 Sept) with a STRICT numeric normaliser (astra gate-2 F3): a fallback comparison happens only when both the
answer and the reference are pure numbers after stripping a leading currency sign, a trailing percent sign or a trailing unit WORD; nothing is extracted
from expressions containing letters inside, backslashes, '^', '/', or several numbers. Decimal comma is accepted only as 'd,dd' (one comma, 1-2 decimals);
thousands separators only as 'd,ddd' groups. Writes final/label_disagreements.json with agreed/disagree lists, per-source counts and the audit of every
pair rescued by the fallback. Usage: python3 finalize_label_check.py"""
import json, re, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE))); sys.path.insert(0, f'{ROOT}/data/benchmarks_el/math500'); import equiv500 as E
UNIT = re.compile(r'^\s*[$€£]?\s*(-?[\d.,]+)\s*(%|[A-Za-zα-ωά-ώ]{1,12}\.?)?\s*$')
def strict_num(s):
    m = UNIT.match(str(s))
    if not m: return None
    core = m.group(1)
    if re.fullmatch(r'-?\d{1,3}(,\d{3})+(\.\d+)?', core): core = core.replace(',', '')
    elif re.fullmatch(r'-?\d+,\d{1,2}', core): core = core.replace(',', '.')
    elif ',' in core: return None
    try: return float(core)
    except ValueError: return None
def agree(ref, ans):
    if not ref: return False, None
    if E.equiv500(ref, ans): return True, 'equiv500'
    a, b = strict_num(ans), strict_num(ref)
    if a is not None and b is not None and abs(a - b) < 1e-6: return True, 'numeric'
    return False, None
rows = [json.loads(l) for l in open(f'{HERE}/out/independent_solve.jsonl')]; c = collections.Counter(); dis, agreed, rescued = [], [], []
# completeness: the expected problem manifest (same construction as independent_solve.py) vs the solve records
import hashlib
src = {json.loads(l)['id']: json.loads(l) for l in open(f'{HERE}/prep/translations_with_reference.jsonl')}
for l in open(f'{HERE}/out/level5_problems_el.jsonl'): r = json.loads(l); src.setdefault(r['id'], r)
expected = set()
for f in ('rows_M1', 'rows_M2_extra'):
    for l in open(f'{HERE}/final/{f}.jsonl'): expected.add(re.sub(r'^c2_', '', json.loads(l)['id']))
covered = {src[i]['problem_en'] for i in expected if i in src and i.startswith('gsm')}
for l in open(f'{ROOT}/data/math/en/gsm8k_dedup3.jsonl'):
    r = json.loads(l)
    if r['problem'] not in covered: expected.add('gsmen_' + hashlib.sha256(r['problem'].encode('utf-8')).hexdigest()[:12])
solved_ids = [r['id'] for r in rows]
if len(solved_ids) != len(set(solved_ids)): raise SystemExit('duplicate solve records')
missing = sorted(expected - set(solved_ids)); extra = sorted(set(solved_ids) - expected)
print(f'expected problems {len(expected)}, solve records {len(rows)}, missing {len(missing)}, extra {len(extra)}')
for r in rows:
    ok, how = agree(r['ref'], r['answer']); c[(r['src'], ok)] += 1
    (agreed if ok else dis).append(r['id'])
    if how == 'numeric': rescued.append(dict(id=r['id'], answer=r['answer'], ref=r['ref']))
n_problems = len(rows)
json.dump(dict(agreed=sorted(agreed), disagree=sorted(dis), unsolved=missing, extra_records=extra, n_problems=len(expected), n_solved=len(rows), expected_manifest_sha256=hashlib.sha256('\n'.join(sorted(expected)).encode()).hexdigest(), agreement={f'{k[0]}:{"agree" if k[1] else "disagree"}': v for k, v in sorted(c.items())}, numeric_fallback_rescues=rescued, rule='kept only on a positive agreement record: equiv500, or strict numeric equality (audited list); disagreements dropped; native rows and the published English MATH solutions are outside the solve scope by recipe'), open(f'{HERE}/final/label_disagreements.json', 'w'), indent=1)
print({f'{k[0]}:{"agree" if k[1] else "disagree"}': v for k, v in sorted(c.items())}, '| numeric-fallback rescues:', len(rescued)); [print('   ', x) for x in rescued[:12]]

=== §D FORMAT BLOCK (data/format_block/receipt.json + builder) ===
{
 "rows": 8270,
 "dev_rows": 71,
 "split": "partition-first: 1% of questions are dev; demonstrations are sampled only within the same partition",
 "by_source": {
  "openbookqa": 4953,
  "arc_easy": 2216,
  "arc_challenge": 1101
 },
 "shots": {
  "0": 1636,
  "2": 1643,
  "5": 1630,
  "3": 1686,
  "1": 1675
 },
 "system_header_rows": 2743,
 "dropped": {
  "contaminated": 57
 },
 "sources": "ARC-Challenge train, ARC-Easy train, OpenBookQA train (HF parquet, 15 Sept)",
 "supervised": "final assistant letter only; prior shots train=false"
}
#!/usr/bin/env python3
"""English chat-format multiple-choice block (15 Sept): the leaderboard chat protocol renders k prior questions as user/assistant turns with a letter answer,
then the target question; our mix has none of this pattern, and the incumbent loses 5-10 points in that mode. Sources: ARC-Challenge/Easy and OpenBookQA
TRAIN splits (never the test splits used in retention). One row per question, k in {0,1,2,3,5} prior shots from the same source, prior assistant turns
unsupervised (train=false), the final letter supervised; one third of rows carry the MMLU-style header as a system turn. Decontaminated against every
evaluation cache with the mix's rule. Writes mc_fewshot_en.jsonl + receipt.json."""
import json, os, random, sys, pandas as pd, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, f'{ROOT}/data'); from mixlib import Decon
rng = random.Random(15); LET = 'ABCDE'
def load(name, qcol):
    df = pd.read_parquet(f'{HERE}/src/{name}'); out = []
    for r in df.to_dict('records'):
        texts = list(r['choices']['text']); labels = list(r['choices']['label']); key = r['answerKey']
        if key not in labels or len(texts) < 3 or len(texts) > 5: continue
        idx = labels.index(key); out.append(dict(q=str(r[qcol]).strip(), choices=texts, gold=idx, src=name.split('_train')[0]))
    return out
pool = load('arc_challenge_train.parquet', 'question') + load('arc_easy_train.parquet', 'question') + load('openbookqa_train.parquet', 'question_stem')
HDR = {'arc_challenge': 'The following are multiple choice questions (with answers) about science.', 'arc_easy': 'The following are multiple choice questions (with answers) about science.', 'openbookqa': 'The following are multiple choice questions (with answers) about common knowledge and science.'}
def render(item): return 'Question: ' + item['q'] + '\n' + '\n'.join(f'{LET[i]}. {c}' for i, c in enumerate(item['choices'])) + '\nAnswer:'
DEC = Decon(require_confirm=True); rows = []; dropped = collections.Counter(); by_src = collections.defaultdict(list)
rng.shuffle(pool)
for it in pool: it['dev'] = rng.random() < 0.01   # partition FIRST (astra gate-2 F4): a dev question never appears as a demonstration in a train row
for it in pool: by_src[(it['src'], it['dev'])].append(it)
for it in pool:
    k = rng.choice([0, 1, 2, 3, 5]); cand = [x for x in by_src[(it['src'], it['dev'])] if x is not it]; shots = rng.sample(cand, min(k, len(cand)))
    msgs = []
    if rng.random() < 0.33: msgs.append(dict(role='system', content=HDR[it['src']]))
    for sh in shots: msgs += [dict(role='user', content=render(sh)), dict(role='assistant', content=LET[sh['gold']], train=False)]
    msgs += [dict(role='user', content=render(it)), dict(role='assistant', content=LET[it['gold']])]
    if DEC.contaminated(msgs): dropped['contaminated'] += 1; continue
    rows.append(dict(id=f"mc_{it['src']}_{len(rows)}", messages=msgs, dev=it['dev'], meta=dict(src=it['src'], shots=len(shots))))
rng.shuffle(rows)
with open(f'{HERE}/mc_fewshot_en.jsonl', 'w') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
rec = dict(rows=len(rows), dev_rows=sum(1 for r in rows if r['dev']), split='partition-first: 1% of questions are dev; demonstrations are sampled only within the same partition', by_source=dict(collections.Counter(r['meta']['src'] for r in rows)), shots=dict(collections.Counter(r['meta']['shots'] for r in rows)), system_header_rows=sum(1 for r in rows if r['messages'][0]['role'] == 'system'), dropped=dict(dropped), sources='ARC-Challenge train, ARC-Easy train, OpenBookQA train (HF parquet, 15 Sept)', supervised='final assistant letter only; prior shots train=false')
json.dump(rec, open(f'{HERE}/receipt.json', 'w'), indent=1); print(rec)

Three sample rows:
{"id": "mc_openbookqa_2816", "messages": [{"role": "system", "content": "The following are multiple choice questions (with answers) about common knowledge and science."}, {"role": "user", "content": "Question: If pollution is caused by many things, it is least likely to be caused by\nA. using styrofoam\nB. pedaling forward\nC. driving cars\nD. smoking cigarettes\nAnswer:"}, {"role": "assistant", "content": "B"}], "dev": false, "meta": {"src": "openbookqa", "shots": 0}}
{"id": "mc_arc_easy_3035", "messages": [{"role": "user", "content": "Question: Which energy type is common enough in Nevada to make a significant contribution to the renewable energy needs of the state?\nA. coal\nB. geothermal\nC. natural gas\nD. petroleum\nAnswer:"}, {"role": "assistant", "content": "B", "train": false}, {"role": "user", "content": "Question: Which resource is most likely found in large amounts in forest ecosystems?\nA. iron\nB. wood\nC. plastic\nD. petroleum\nAnswer:"}, {"role": "assistant", "content": "B", "train": false}, {"role": "user", "content": "Question: A class is testing the effect of exercise on heart rate. The heart rate of two students before exercise is compared to their heart rate after running around a track. Which procedure will most likely help the class correctly compare the results of the two students?\nA. test students who are the same height\nB. have the students run on the same day\nC. measure the distance each student runs\nD. have the students run for the same amount of time\nAnswer:"}, {"role": "assistant", "content": "D"}], "dev": false, "meta": {"src": "arc_easy", "shots": 2}}
{"id": "mc_openbookqa_5631", "messages": [{"role": "user", "content": "Question: If something is in an ecosystem, it could be\nA. invisible\nB. vacuum of space\nC. lacking life\nD. alien\nAnswer:"}, {"role": "assistant", "content": "C", "train": false}, {"role": "user", "content": "Question: After seeing her give birth, the zookeepers discovered that Harry the ____ was actually a girl.\nA. hen\nB. hotcake\nC. healfish\nD. hare\nAnswer:"}, {"role": "assistant", "content": "D", "train": false}, {"role": "user", "content": "Question: A cardinal makes brief contact with a picnic table, and between them there is\nA. death\nB. transactions\nC. animosity\nD. abrasion\nAnswer:"}, {"role": "assistant", "content": "D"}], "dev": false, "meta": {"src": "openbookqa", "shots": 2}}

=== §E ASSEMBLER (data/assemble_full_r4.py, verbatim) ===
#!/usr/bin/env python3
"""The from-scratch pass mix for 1-G4F6P1 (15 Sept, owner decision 01:30): round 3's vetted single-pass rows with four block swaps, every row re-checked.
Start from data/arms/R3_single (403,727 rows, all screens applied on 11 Sept). Remove: openmath_gsm (GSM8K x13.5), greek_math (cut-1 terse), correcting (v1),
convskills (replaced by the current v2 final). Add: math_en_gsm (GSM8K <=3 solutions/problem) x2, math_en_math (published MATH train solutions, human-written; outside the blind-solve scope by recipe) x2,
greek_math_v2 (cut-2 worked + Level 5 + native, arm_M2 export) x2, convskills_v2 x2, correcting_v2 x2, format_mc x1. Translated maths rows and English GSM8K rows are kept
only on a POSITIVE agreement record of the blind solve (final/label_disagreements.json 'agreed'); native rows (two independent solves at generation) and the
published MATH solutions are outside the solve scope by recipe and counted as exempt. --allow-unconfirmed is for dry runs only. Personality overlays (accepted
patch) applied to the kept personality rows. Every row (old and new) passes the mix's decontamination (8-gram containment + any 13-gram vs every eval
cache) and the 4,096-token window. Dev = R3's dev minus the removed configs + 1% of each new block + the cut-2 dev rows. Fails closed on any check.
Usage: python3 assemble_full_r4.py --arm R4_full [--allow-unconfirmed]  (apertus-local-chat venv: exact tokenizer)"""
import argparse, json, random, collections, hashlib, os, re, sys, pathlib, ast
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE)); from mixlib import Decon, ntok, row_tokens, sup_tokens, TOKMODE
ap = argparse.ArgumentParser(); ap.add_argument('--arm', default='R4_full'); ap.add_argument('--seed', type=int, default=42); ap.add_argument('--allow-unconfirmed', action='store_true'); ap.add_argument('--keep-s5m', action='store_true', help='keep the S5m lane (dropped by default after the 15 Sept audit: 74/100 flawed)'); a = ap.parse_args(); a.drop_s5m = not a.keep_s5m
if a.allow_unconfirmed and not a.arm.endswith('_dry'): raise SystemExit('--allow-unconfirmed is for dry runs only: the arm name must end with _dry')
if TOKMODE is None: ntok('x')
rng = random.Random(a.seed); OUT = HERE / 'arms' / a.arm; OUT.mkdir(parents=True, exist_ok=True); DEC = Decon(require_confirm=True)
# Disclosed decision (15 Sept 02:30): the English IFEval-like blocks share their instruction-template sentences with the English IFEval prompts by
# construction (the 13-gram rule drops 61% of ifeval_like). IFEval-en is not in our battery and the Greek IFEval prompts share no English 13-grams,
# so for these two blocks a hit on the 'ifeval' cache alone is kept (counted as ifeval_template_overlap_kept); hits on any other cache still drop.
from mixlib import normalize_text as _nt, ngrams as _ng
class _GramsExcluding:
    """The mix's two rules over every evaluation cache EXCEPT the named one (all memberships preserved: grams are re-read from the files)."""
    def __init__(self, exclude_prefix):
        import glob as _g; self.g8 = {}; self.g13 = {}; self.files = []
        for f in sorted(_g.glob(str(HERE / 'cache' / 'evals' / '*.jsonl'))):
            if os.path.basename(f).startswith(exclude_prefix): continue
            self.files.append(os.path.basename(f)); suite = os.path.basename(f).split('.')[0]
            for l in open(f):
                if l.strip():
                    r = json.loads(l); nt = _nt(str(r['text']))
                    for g in _ng(nt): self.g8.setdefault(g, (suite, str(r['eval_id'])))
                    for g in _ng(nt, 13): self.g13.setdefault(g, (suite, str(r['eval_id'])))
    def contaminated(self, messages):
        for m in messages:
            if m['role'] != 'user': continue
            nt = _nt(m['content']); gs = _ng(nt)
            if gs and sum(1 for g in gs if g in self.g8) / len(gs) >= 0.5: return True
            if len(nt.split()) >= 13 and any(g in self.g13 for g in _ng(nt, 13)): return True
        return False
DEC_NOIF = _GramsExcluding('ifeval.')
IFEVAL_TEMPLATE_BLOCKS = {'ifeval_like', 'dolci_precise_if_20k'}
def L(p): return [json.loads(l) for l in open(p) if l.strip()]
def render(r):
    turns = r.get('turns') or r.get('messages') or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]
    out = [dict(role=t['role'], content=t['content'], **({'train': False} if t['role'] == 'assistant' and t.get('train') is False else {})) for t in turns]
    return out if any(m['role'] == 'assistant' and m.get('train', True) and m['content'].strip() for m in out) else None
# independent reference check (owner rule)
LD = HERE / 'math' / 'cut2' / 'final' / 'label_disagreements.json'
if LD.exists(): _ld = json.load(open(LD)); AGREED = set(_ld['agreed']); BAD = set(_ld['disagree']) | set(_ld.get('unsolved', [])); ld_note = dict(problems=_ld['n_problems'], solved=_ld['n_solved'], agreed=len(AGREED), disagree=len(_ld['disagree']), unsolved=len(_ld.get('unsolved', [])), numeric_fallback_rescues=len(_ld.get('numeric_fallback_rescues', [])))
elif a.allow_unconfirmed: AGREED = None; BAD = set(); ld_note = 'ALLOW-UNCONFIRMED DRY RUN'; print('WARNING: dry run without label_disagreements.json')
else: raise SystemExit('label_disagreements.json missing: run the independent solve first')
src_en = {}
for p in (HERE / 'math' / 'cut2' / 'prep' / 'translations_with_reference.jsonl', HERE / 'math' / 'cut2' / 'out' / 'level5_problems_el.jsonl'):
    for r in L(p): src_en.setdefault(r['id'], r.get('problem_en', ''))
AGREED_TEXT = {src_en[i] for i in (AGREED or set()) if i in src_en} | ({src_en[i] for i in src_en} if AGREED is None else set())
AGREED_HASH = {i[len('gsmen_'):] for i in (AGREED or set()) if i.startswith('gsmen_')}
LABEL = collections.Counter()
def keep_translated(row_id):
    pid = re.sub(r'^(c2_|c1b_)', '', row_id)
    if pid.startswith('gm_nat') or pid.startswith('nat'): LABEL['greek_native_exempt'] += 1; return True
    if AGREED is None: return True
    if pid in AGREED: LABEL['greek_agreed'] += 1; return True
    LABEL['greek_disagreed' if pid in BAD else 'greek_unmapped'] += 1; return False
def keep_en(prob):
    if AGREED is None: return True
    if prob in AGREED_TEXT or hashlib.sha256(prob.encode('utf-8')).hexdigest()[:12] in AGREED_HASH: LABEL['en_gsm_agreed'] += 1; return True
    LABEL['en_gsm_dropped'] += 1; return False
REMOVE = {'openmath_gsm', 'greek_math', 'correcting', 'convskills'}
base = L(HERE / 'arms' / 'R3_single' / 'train.jsonl'); base_dev = L(HERE / 'arms' / 'R3_single' / 'dev.jsonl')
rec = dict(arm=a.arm, seed=a.seed, args=vars(a), tokenizer=TOKMODE, base='data/arms/R3_single', base_rows=len(base), removed_configs=sorted(REMOVE), label_check=ld_note, blocks=[], drops=collections.Counter())
kept = [r for r in base if r['config'] not in REMOVE]; rec['base_removed_rows'] = len(base) - len(kept)
# personality overlays (accepted patch, as in the pass assembler)
PATCH = os.path.expanduser('~/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/personality/deployment_and_closure_patch.jsonl'); ov = collections.Counter()
if os.path.exists(PATCH):
    by_id = {r['id']: i for i, r in enumerate(kept) if r['config'].startswith('personality')}
    for o in L(PATCH):
        c = o.get('candidate_row'); c = ast.literal_eval(c) if isinstance(c, str) else c
        if not c or not c.get('messages'): ov['missed'] += 1; continue
        if o['operation'] == 'replace_existing_row' and o['row_id'] in by_id: kept[by_id[o['row_id']]] = dict(kept[by_id[o['row_id']]], messages=c['messages']); ov['applied'] += 1
        elif o['operation'] == 'add_new_coverage_row': kept.append(dict(config='personality_v3', id=c.get('id', o['row_id']), messages=c['messages'])); ov['added'] += 1
        else: ov['missed'] += 1
rec['personality_overlays'] = dict(ov)
def check_row(msgs, cfg):
    if any(re.search(r'[\x00-\x08\x0b-\x1f\x7f]', m['content']) for m in msgs): rec['drops'][f'{cfg}:control_chars'] += 1; return False
    hit = DEC.contaminated(msgs)
    if hit:
        if cfg.replace('(dev)', '') in IFEVAL_TEMPLATE_BLOCKS and hit[0] == 'ifeval' and not DEC_NOIF.contaminated(msgs): rec.setdefault('waived', collections.Counter())[f'{cfg}:ifeval_en_cache_waived'] += 1   # disclosed cache-wide waiver of the English IFEval cache for the two constraint blocks; every other cache still applies
        else: rec['drops'][f'{cfg}:contaminated'] += 1; return False
    if row_tokens(msgs) > 4096: rec['drops'][f'{cfg}:over_window'] += 1; return False
    return True
train = []; dev = [r for r in base_dev if r['config'] not in REMOVE and check_row(r['messages'], r['config'] + '(dev)')]; rec['base_dev_kept'] = len(dev)
for r in kept:   # historical rows get the same checks as new blocks
    if any(m['role'] == 'assistant' and m.get('train') is False for m in r['messages']): rec['drops'][f"{r['config']}:masked_turns_not_trainable"] += 1; continue
    if check_row(r['messages'], r['config']): train.append(r)
rec['base_kept_after_checks'] = len(train)
def add_block(name, rows, copies, dev_frac=0.01, dev_rows=None):
    rr = []
    for r in rows:
        m = render(r)
        if m is None: rec['drops'][f'{name}:no_supervised_turn'] += 1; continue
        if check_row(m, name): rr.append(dict(config=name, id=f"{name}:{r['id']}", messages=m))   # ids are unique per block, never bare
    seen = set(); dup = sum(1 for r in rr if r['id'] in seen or seen.add(r['id'])); rr = [r for r in rr if not (r['id'] in (s2 := set()) or s2.add(r['id']))] if False else [r for i, r in enumerate(rr) if r['id'] not in {x['id'] for x in rr[:i]}] if dup else rr
    if dup: rec['drops'][f'{name}:duplicate_id'] += dup
    rng.shuffle(rr); nd = int(round(len(rr) * dev_frac)) if dev_rows is None else 0; dv, tr = rr[:nd], rr[nd:]; dev.extend(dv)
    if dev_rows:
        for r in dev_rows:
            m = render(r)
            if m is None: rec['drops'][f'{name}(dev):no_supervised_turn'] += 1; continue
            if check_row(m, name + '(dev)'): dev.append(dict(config=name, id=f"{name}:{r['id']}", messages=m))
    for c in range(copies): train.extend(dict(r, id=f"{r['id']}#{c}" if c else r['id']) for r in tr)
    rec['blocks'].append(dict(block=name, input_rows=len(rows), kept=len(rr), dev=nd + (sum(1 for r in dev if r['config'] == name) - nd if dev_rows else 0), copies=copies, train_rows_effective=len(tr) * copies)); print(f'{name}: {len(rows)} in, {len(rr)} kept, x{copies}', flush=True)
devp = set(json.load(open(HERE / 'math' / 'cut2' / 'final' / 'dev_problems_en.json')))
gsm = [r for r in L(HERE / 'math' / 'en' / 'gsm8k_dedup3.jsonl') if r['problem'] not in devp]; n0 = len(gsm); gsm = [r for r in gsm if keep_en(r['problem'])]; rec['drops']['math_en_gsm:reference_not_confirmed'] = n0 - len(gsm)
sys.path.insert(0, str(HERE / 'benchmarks_el' / 'math500')); sys.path.insert(0, str(HERE / 'math')); import equiv500 as _E; from mathlib import boxed as _boxed
def sol_ok(r):   # the generated solution's own final answer must equal the agreed label (astra gate-2 v2 F4)
    ans = _boxed(r['generated_solution'])   # boxed answer required (no last-number fallback, astra gate-2 v3 H2)
    return ans is not None and bool(_E.equiv500(str(r['expected_answer']), str(ans).replace(',', '')))
n1 = len(gsm); gsm = [r for r in gsm if sol_ok(r)]; rec['drops']['math_en_gsm:solution_answer_ne_label'] = n1 - len(gsm)
add_block('math_en_gsm', [dict(id=str(r.get('_row', i)), user=r['problem'], assistant=r['generated_solution']) for i, r in enumerate(gsm)], 2, dev_frac=0)   # x2; no random dev split (several solutions per problem): the maths dev families are held out via dev_problems_en
mt = [r for r in L(HERE / 'math' / 'en' / 'math_train_published.jsonl') if r['problem'] not in devp]; LABEL['en_math_published_exempt'] = len(mt)   # human-written MATH solutions: outside the blind-solve scope by recipe
add_block('math_en_math', [dict(id=str(r['id']), user=r['problem'], assistant=r['generated_solution']) for r in mt], 2, dev_frac=0)   # no random dev split: the maths dev families are held out by problem (dev_problems_en) in both languages
g = L(HERE / 'math' / 'cut2' / 'final' / 'arm_M2.jsonl'); n0 = len(g); g = [r for r in g if keep_translated(r['id'])]; rec['drops']['greek_math_v2:reference_not_confirmed'] = n0 - len(g)
add_block('greek_math_v2', [r for r in g if not r.get('dev')], 2, dev_rows=[r for r in g if r.get('dev')])
# 15 Sept 06:10 (astra gate-2 v3 H1 -> confirmed defect): cluster/sft_train.py passes raw messages to TRL with assistant_only_loss=True, which supervises
# EVERY assistant turn; the per-turn train=false masks are honoured only by the trainer's validator. Until the trainer is fixed and verified, no row with a
# masked assistant turn enters a pass: correcting_v2 is dropped whole (its planted failures would be learned), convskills rows with masked context turns
# (S4 lane) are dropped, and the format block's demonstration answers are declared supervised (they are correct letters).
cs = L(HERE / 'convskills' / 'v2' / 'final' / 'rows_final.jsonl'); n0 = len(cs)
if a.drop_s5m: cs = [r for r in cs if not str(r.get('id', '')).startswith('S5m')]; rec['drops']['convskills_v2:S5m_lane_dropped'] = n0 - len(cs)
n1 = len(cs); cs = [r for r in cs if not any(t.get('role') == 'assistant' and t.get('train') is False for t in (r.get('turns') or []))]; rec['drops']['convskills_v2:masked_turns_not_trainable'] = n1 - len(cs)
add_block('convskills_v2', cs, 2)
rec['drops']['correcting_v2:block_dropped_masks_not_honoured'] = len(L(HERE / 'robustness' / 'correcting' / 'v2' / 'rows_v2.jsonl'))
fm = L(HERE / 'format_block' / 'mc_fewshot_en.jsonl')
for r in fm:   # demonstrations are supervised in the training path: declare it (drop the flag) so the receipt describes what is trained
    for m in r['messages']: m.pop('train', None)
rec['format_mc_demonstrations'] = 'supervised (correct letters); the train=false flags were removed because the training path does not honour them'
add_block('format_mc', [r for r in fm if not r.get('dev')], 1, dev_rows=[r for r in fm if r.get('dev')])
# final checks: dev/train disjoint by id and by first user turn; every train row supervised
tid = {(r['config'], r['id'].split('#')[0]) for r in train}; did = {(r['config'], r['id']) for r in dev}
if tid & did: raise SystemExit(f'dev/train id overlap: {list(tid & did)[:5]}')
fu = lambda r: next((m['content'] for m in r['messages'] if m['role'] == 'user'), ''); lu = lambda r: [m['content'] for m in r['messages'] if m['role'] == 'user'][-1]
tu_all = set(); [tu_all.update(m['content'] for m in r['messages'] if m['role'] == 'user') for r in train]
n_dev0 = len(dev); dev = [r for r in dev if not any(m['content'] in tu_all for m in r['messages'] if m['role'] == 'user')]   # ANY dev user turn found among train user turns removes the dev row   # dev is for eval loss only: a dev row is removed if its first or its target user turn appears ANYWHERE among train user turns (few-shot demonstrations included)
rec['dev_rows_removed_for_overlap'] = n_dev0 - len(dev)
if any(m['content'] in tu_all for r in dev for m in r['messages'] if m['role'] == 'user'): raise SystemExit('dev/train user-turn overlap remains')
if any(not any(m['role'] == 'assistant' and m.get('train', True) for m in r['messages']) for r in train): raise SystemExit('unsupervised train row')
if any(m.get('train') is False for r in train + dev for m in r['messages']): raise SystemExit('a masked assistant turn remains in the manifest (the training path would supervise it)')
rng.shuffle(train); rng.shuffle(dev)
def dump(p, rows):
    h = hashlib.sha256()
    with open(p, 'w') as f:
        for r in rows: s = json.dumps(r, ensure_ascii=False) + '\n'; f.write(s); h.update(s.encode())
    return h.hexdigest()
by_cfg = collections.Counter(r['config'] for r in train); sup = collections.Counter(); tot = collections.Counter()
for r in train: sup[r['config']] += sup_tokens(r['messages']); tot[r['config']] += row_tokens(r['messages'])
rec['train'] = dict(rows=len(train), tokens=sum(tot.values()), supervised_tokens=sum(sup.values()), by_config={k: dict(rows=by_cfg[k], tokens=tot[k], supervised=sup[k], share_supervised=round(sup[k] / max(1, sum(sup.values())), 4)) for k in sorted(by_cfg)}, sha256=dump(OUT / 'train.jsonl', train))
rec['dev'] = dict(rows=len(dev), by_config=dict(collections.Counter(r['config'] for r in dev)), sha256=dump(OUT / 'dev.jsonl', dev)); rec['drops'] = dict(rec['drops']); rec['waived'] = dict(rec.get('waived', {})); rec['label_counts'] = dict(LABEL)
def fsha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
rec['identities'] = dict(eval_caches=DEC.identities, caches_used_for_waiver_check=DEC_NOIF.files, code={n: fsha(HERE / n) for n in ('assemble_full_r4.py', 'mixlib.py', 'format_block/build_mc_fewshot.py', 'math/cut2/independent_solve.py', 'math/cut2/finalize_label_check.py')}, inputs={(str(p.relative_to(HERE)) if str(p).startswith(str(HERE)) else str(p)): fsha(p) for p in (HERE / 'arms' / 'R3_single' / 'train.jsonl', HERE / 'arms' / 'R3_single' / 'dev.jsonl', HERE / 'math' / 'cut2' / 'final' / 'dev_problems_en.json', HERE / 'math' / 'cut2' / 'prep' / 'translations_with_reference.jsonl', HERE / 'math' / 'cut2' / 'out' / 'level5_problems_el.jsonl', pathlib.Path(PATCH) if os.path.exists(PATCH) else HERE / 'nonexistent', HERE.parent / 'cluster' / 'configs' / 'R4_full.yaml', HERE.parent / 'cluster' / 'sft_train.py', HERE / 'math' / 'en' / 'gsm8k_dedup3.jsonl', HERE / 'math' / 'en' / 'math_train_published.jsonl', HERE / 'math' / 'cut2' / 'final' / 'arm_M2.jsonl', HERE / 'convskills' / 'v2' / 'final' / 'rows_final.jsonl', HERE / 'robustness' / 'correcting' / 'v2' / 'rows_v2.jsonl', HERE / 'format_block' / 'mc_fewshot_en.jsonl', LD) if p.exists()}, model=dict(name='fffoivos/apertus-8b-greek-cpt', revision='18-avg-uniform5-tokens30B-50B', template_source='swiss-ai/Apertus-8B-Instruct-2509'))
json.dump(rec, open(OUT / 'receipt.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(dict(rows=rec['train']['rows'], tokens=rec['train']['tokens'], supervised=rec['train']['supervised_tokens'], dev=rec['dev']['rows'], drops=rec['drops'], label_check=ld_note), ensure_ascii=False)); print('maths share of supervised tokens:', round(sum(v['supervised'] for k, v in rec['train']['by_config'].items() if k.startswith(('math_', 'greek_math'))) / rec['train']['supervised_tokens'], 3))

=== §F TRAINER DRY-RUN + CONFIG + LAUNCH BINDING (chain excerpt) ===
[ "$(sshc "cd $R && md5sum data/arms/R4_full/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/R4_full/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch"; exit 1; }

for F in train dev; do RS=$(python3 -c "import json; print(json.load(open('data/arms/R4_full/receipt.json'))['$F']['sha256'])"); CS=$(sshc "cd $R && sha256sum data/arms/R4_full/$F.jsonl | cut -d' ' -f1"); [ "$RS" = "$CS" ] || { say "FAILED: $F.jsonl sha256 on the cluster ($CS) differs from the receipt ($RS)"; exit 1; }; say "$F.jsonl sha256 bound to the receipt: $CS"; done

grep -q "^expected_train_rows: $(wc -l < data/arms/R4_full/train.jsonl | tr -d ' ')$" cluster/configs/R4_full.yaml || { say "FAILED: config expected_train_rows does not match the manifest"; exit 1; }

{"arm": "R4_full", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/R4_full/dev.jsonl", "eval_rows": 2342, "eval_tokens": 1333053, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "fffoivos/apertus-8b-greek-cpt", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 53803, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 3363, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "R4_full_lr1e-5_1ep_cos", "steps_per_epoch": 3363, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/R4_full/train.jsonl", "train_rows": 379740, "train_tokens": 220148591, "warmup_ratio": 0.03, "world_size": 4}
DRY_RUN_OK
Config:
run_name: R4_full_lr1e-5_1ep_cos
arm: R4_full
model_name_or_path: fffoivos/apertus-8b-greek-cpt
tokenizer_name_or_path: fffoivos/apertus-8b-greek-cpt
revision: 18-avg-uniform5-tokens30B-50B
template_source: swiss-ai/Apertus-8B-Instruct-2509
train_file: data/arms/R4_full/train.jsonl
eval_file: data/arms/R4_full/dev.jsonl
expected_train_tokens: null
learning_rate: 1.0e-5
num_train_epochs: 1
lr_scheduler_type: cosine_with_min_lr
warmup_ratio: 0.03
weight_decay: 0.0
adam_beta2: 0.99
max_grad_norm: 1.0
max_length: 4096
per_device_train_batch_size: 1
per_device_eval_batch_size: 1
gradient_accumulation_steps: 4
planned_world_size: 4
seed: 42
bf16: true
attn_implementation: kernels-community/vllm-flash-attn3
require_apertus_control_ids: true
extend_control_tokens: false
optim: adamw_torch_fused
dataloader_num_workers: 4


min_lr_rate: 0.1

expected_train_rows: 379740
save_steps: 750
save_total_limit: 2

Preflight: OK

=== §G PILOT READOUT EXCERPT (why the block is in) ===
# Pilot readout, 14 Sept 2026 (1-G4F6P0--00 / --01 / --02)

Question (plan §4, H9): do Sol-written worked Greek solutions (cut-2) raise MATH-500-el by at least 3 pp over terse cut-1 targets, at a one-epoch continuation from 1-G2F1P0@epoch1 with the same replay and English maths blocks? Secondary: does adding Level 5 help further?

## Result: no arm advances
Readout under the frozen rule (`results/pilots/summary.md`, readout v3.2, scorer v2, all inputs hash-bound):

| arm | MATH-500-el | loops | truncated | MATH-500-en | IFEval-el | MGSM-el | train loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1-G2F1P0@epoch1 (reference) | 12.8 | 27 | 60 | 16.4 | 54.2 | 46.8 | — |
| --00 terse targets | 13.4 | 82 | 132 | 13.8 | 55.3 | 46.0 | 0.756 |
| --01 worked solutions | 12.0 | 37 | 59 | 15.2 | 56.6 | 47.2 | 0.738 |
| --02 worked + Level 5 | 13.0 | 45 | 62 | 12.6 | 56.0 | 44.8 | 0.733 |

- Primary --01 vs --00 on MATH-500-el: −1.4 pp, one-sided 90% LB −3.6, two-sided 90% CI [−4.2, +1.6], 15.8% discordant items. Not qualified (gain < 3 pp, LB ≤ 0).
- Secondary --02 vs --01: +1.0 pp (LB −1.0); not evaluated for action under the hierarchy.
- Versus the stage-1 reference (paired, same 500 items): --00 +0.6, --01 −0.8, --02 +0.2 pp on Greek; −2.6 / −1.2 / −3.8 pp on English. All within noise of zero on Greek; English drifts down with the maths continuation.
- Guardrails pass for both candidates (IFEval-el paired +1.3 / +0.7 pp vs --00; MGSM-el +1.2 / −1.2 pp; loops and truncations far below --00).

## What the pilot did show
1. Terse targets damage generation behaviour: --00 finished 132 of 500 Greek responses by length (reference 60) and 82 looped (reference 27), typically an equation line repeated to the token limit. Worked solutions restore the reference behaviour (--01: 59 / 37; --02: 62 / 45). Terse maths targets should not be used again.
2. Accuracy is flat at 12–13% for every arm. One epoch over ~9k Greek worked solutions (with 57% replay) does not move MATH-500-el for this 8B model; neither does adding 1.4k Level-5 rows. The dose-check branch of the rule existed only for an inconclusive positive; a negative primary stops it.
3. English MATH-500 falls in every arm relative to the reference (largest for --02, −3.8 pp), so the Greek maths continuation is not free.

## Consequence
Under the frozen rule the negative outcome stops Phase C as planned (the 15 Sept pass 1-G4F6P1 with the new maths block) and calls for a write-up and a re-plan of the maths lane. The rest of the R4 candidate (correcting v2, the English maths block, the personality overlays, the Krikri-suite and GreekMMLU protocol work) is unaffected by this result but was scheduled inside the same pass.

## Options for the re-plan (owner decision)
A. Run the 15 Sept pass without a Greek maths block (correcting v2 + the other R4 changes on the incumbent recipe); keep --01's worked solutions as a small behaviour-repair block only if a later screen justifies it. Cheapest (≈7 nh as planned), gives the retention/GreekMMLU/Krikri-suite numbers the checklist needs.
B. Dose test before deciding: continue --01 for one more epoch over the maths blocks only (≈1 nh) and re-read MATH-500-el; the plan reserved this only for the inconclusive branch, so it would be an explicit override.
C. Change the maths lever: English-first (the published MATH/GSM solutions already in F6) with Greek problems only at inference, or larger and more diverse Greek maths data at the pass scale rather than a continuation; needs a new pilot design and Sol budget.
D. Deprioritise the maths objective for this round and spend the remaining CHF 38 on the evaluation programme (Krikri suite, native adapted rerun, MT audit) and the correcting-attribution arm.

Recommendation: A for tomorrow (it keeps the day useful and honours the rule), with B run in parallel only if the owner wants the dose question answered before dropping the lever.

=== §H SAMPLE ROWS FROM THE NEW BLOCKS (5 each: greek_math_v2, math_en_gsm, math_en_math, correcting_v2, convskills_v2) ===
--- math_en_gsm math_en_gsm:2985681 (total 397 chars, unclipped)
[user] Rodney has 35 dollars more than Ian. Ian has half as much money as Jessica has. If Jessica has 100 dollars, how much more money does Jessica have than Rodney?
[assistant] Ian has half as much money as Jessica has.
Since Jessica has $100, Ian has $100 / 2 = 50$.
Rodney has $35 more than Ian.
So Rodney has $50 + 35 = 85$.
Thus, Jessica has $100 - 85 = 15$ dollars more than Rodney.
So the answer is \boxed{15}.
--- math_en_gsm math_en_gsm:2033256 (total 647 chars, unclipped)
[user] Tony decided he wanted to be an astronaut.  He went to college for 4 years to get a degree in science.  He then went on to get 2 more degrees in other fields for the same period of time.  He also got a graduate degree in physics, which took another 2 years.  How many years in total did Tony go to school to be an astronaut?
[assistant] Let's break down the years Tony spent in school:

* 4 years for a degree in science
* 2 more degrees, each taking 4 years, so that's 2 x 4 = 8 years
* A graduate degree in physics, which took 2 years

Adding all these up, Tony spent 4 + 8 + 2 = 12 + 2 = 14 years in school to be an astronaut.

So, the answer is \boxed{14}.
--- greek_math_v2 greek_math_v2:c2_gsm_2544#1 (total 1142 chars, unclipped)
[user] Ένας γιατρός πρέπει να δώσει φάρμακο σε ένα παιδί και γνωρίζει ότι δεν μπορεί να του δώσει την ίδια ποσότητα που θα έδινε σε έναν ενήλικα. Οι οδηγίες αναφέρουν ότι για κάθε κιλό βάρους το παιδί πρέπει να λαμβάνει 5 ml φαρμάκου. Ο γιατρός γνωρίζει ότι το παιδί ζυγίζει 30 κιλά και ότι η συνολική δόση πρέπει να χορηγηθεί σε 3 ίσα μέρη. Πόσα χιλιοστόγραμμα θα περιέχει κάθε μέρος της δόσης;
[assistant] Για κάθε κιλό βάρους, το παιδί πρέπει να λαμβάνει 5 ml φαρμάκου. Αφού το παιδί ζυγίζει 30 κιλά, υπολογίζουμε πρώτα τη συνολική ποσότητα του φαρμάκου:

\[
30\,\text{kg}\times 5\,\frac{\text{ml}}{\text{kg}}=150\,\text{ml}
\]

Άρα, η συνολική δόση που πρέπει να λάβει το παιδί είναι 150 ml.

Η συνολική αυτή ποσότητα πρέπει να χορηγηθεί σε 3 ίσα μέρη. Επομένως, διαιρούμε τα 150 ml με το 3:

\[
150\,\text{ml}\div 3=50\,\text{ml}
\]

Συνεπώς, κάθε μέρος της δόσης περιέχει 50 ml φαρμάκου. Παρατηρούμε ότι τα δεδομένα επιτρέπουν τον υπολογισμό σε χιλιοστόλιτρα (ml), όχι σε χιλιοστόγραμμα (mg), αφού δεν δίνεται η συγκέντρωση ή η πυκνότητα του φαρμάκου. Η αριθμητική τιμή που ζητείται σύμφωνα με τα δεδομένα και την απάντηση αναφοράς είναι:

\[
\boxed{50}
\]
--- math_en_gsm math_en_gsm:1094890#1 (total 438 chars, unclipped)
[user] The result from the 40-item Statistics exam Marion and Ella took already came out. Ella got 4 incorrect answers while Marion got 6 more than half the score of Ella. What is Marion's score?
[assistant] Ella got 4 incorrect answers, which means she got $40-4 = 36$ correct answers.
Half the score of Ella is $36/2 = 18$.
Marion got 6 more than half the score of Ella, which means she got $18 + 6 = 24$ correct answers.
Thus Marion's score is \boxed{24}.
--- greek_math_v2 greek_math_v2:c2_gsm_397#1 (total 946 chars, unclipped)
[user] Η κόρη της Λαμπρινής είναι 10 χρόνια μικρότερη από την κόρη της Κατερίνας. Ο γιος της Λαμπρινής έχει τη διπλάσια ηλικία από την κόρη της Κατερίνας. Αν η κόρη της Κατερίνας είναι 12 ετών, πόσα χρόνια μεγαλύτερος είναι ο γιος της Λαμπρινής από την κόρη της Λαμπρινής;
[assistant] Η κόρη της Κατερίνας είναι 12 ετών.

Η κόρη της Λαμπρινής είναι 10 χρόνια μικρότερη από την κόρη της Κατερίνας. Επομένως, η ηλικία της είναι:

\[
12-10=2
\]

Άρα, η κόρη της Λαμπρινής είναι 2 ετών.

Ο γιος της Λαμπρινής έχει διπλάσια ηλικία από την κόρη της Κατερίνας. Αφού η κόρη της Κατερίνας είναι 12 ετών, η ηλικία του γιου της Λαμπρινής είναι:

\[
12\cdot 2=24
\]

Άρα, ο γιος της Λαμπρινής είναι 24 ετών.

Για να βρούμε πόσα χρόνια μεγαλύτερος είναι ο γιος της Λαμπρινής από την κόρη της Λαμπρινής, αφαιρούμε την ηλικία της κόρης από την ηλικία του γιου:

\[
24-2=22
\]

Επομένως, ο γιος της Λαμπρινής είναι 22 χρόνια μεγαλύτερος από την κόρη της Λαμπρινής.

\[
\boxed{22}
\]
--- greek_math_v2 greek_math_v2:gm_nat_183_1 (total 654 chars, unclipped)
[user] Στη γιορτή κρασιού του Ναυπλίου, ο Κώστας περιφράσσει έναν χώρο χορού σε σχήμα ισοσκελούς τραπεζίου. Οι δύο βάσεις του τραπεζίου έχουν μήκη 18 m και 10 m, ενώ καθεμία από τις ίσες πλευρές έχει μήκος 5 m. Θα μείνει άνοιγμα 2 m για την είσοδο. Στο υπόλοιπο όριο θα τοποθετηθούν τρεις παράλληλες σειρές σχοινιού. Το εισιτήριο της εκδήλωσης κοστίζει 3 €. Πόσα μέτρα σχοινιού χρειάζονται συνολικά;
[assistant] Η τιμή του εισιτηρίου δεν χρειάζεται.

Άθροισμα των βάσεων:
18 + 10 = 28 m

Άθροισμα των ίσων πλευρών:
5 + 5 = 10 m

Περίμετρος του τραπεζίου:
28 + 10 = 38 m

Μήκος μίας σειράς σχοινιού:
38 − 2 = 36 m

Συνολικό μήκος τριών σειρών:
36 · 3 = 108 m

Απάντηση: 108 m
--- math_en_gsm math_en_gsm:2573723#1 (total 424 chars, unclipped)
[user] Lara is baking cookies using four baking trays. She places five rows of cookies on a baking tray where there are six cookies in one row. How many cookies is she baking?
[assistant] On each baking tray, there are 5 rows of cookies, with 6 cookies in each row.
So, the total number of cookies on each tray is 5 * 6 = 30.
Since there are 4 baking trays, the total number of cookies is 4 * 30 = 120.
Thus, Lara is baking \boxed{120} cookies.
--- math_en_gsm math_en_gsm:2353522 (total 311 chars, unclipped)
[user] Jerica is twice Louis' age. Matilda is 7 years older than Jerica. If Louis is 14, how many years old is Matilda?
[assistant] Louis is 14 years old. 
Jerica is twice Louis' age, so Jerica is 14 * 2 = 28 years old.
Matilda is 7 years older than Jerica, so Matilda is 28 + 7 = 35 years old.
So, Matilda is \boxed{35} years old.
--- greek_math_v2 greek_math_v2:c2_gsm_1334 (total 1012 chars, unclipped)
[user] Η Τάνια χρειάζεται να αγοράσει αρκετό σχοινί ώστε να το κόψει σε 10 κομμάτια μήκους έξι ιντσών το καθένα. Βλέπει ένα σχοινί μήκους 6 ποδιών που κοστίζει 5 € και επίσης σχοινιά μήκους 1 ποδιού που κοστίζουν 1,25 € το καθένα. Ποιο είναι το μικρότερο ποσό που πρέπει να ξοδέψει για να προμηθευτεί το σχοινί που χρειάζεται;
[assistant] Η Τάνια χρειάζεται συνολικά

\[
10 \times 6 = 60
\]

ίντσες σχοινιού.

Το σχοινί των 6 ποδιών έχει μήκος

\[
6 \times 12 = 72
\]

ίντσες, αφού κάθε πόδι ισούται με 12 ίντσες. Επομένως, μπορεί να κοπεί σε

\[
72 \div 6 = 12
\]

κομμάτια των 6 ιντσών. Είναι αρκετό, επειδή

\[
12>10.
\]

Αυτό το σχοινί κοστίζει 5 €.

Κάθε σχοινί του 1 ποδιού έχει μήκος 12 ίντσες. Για να έχει 60 ίντσες, θα χρειαστεί

\[
60 \div 12 = 5
\]

τέτοια σχοινιά. Το συνολικό τους κόστος θα είναι

\[
5 \times 1{,}25 = 6{,}25\text{ €}.
\]

Συγκρίνουμε τα δύο ποσά:

\[
5<6{,}25.
\]

Άρα η οικονομικότερη επιλογή είναι να αγοράσει το σχοινί των 6 ποδιών και το μικρότερο ποσό που πρέπει να ξοδέψει είναι

\[
\boxed{5}
\]
--- convskills_v2 convskills_v2:S3_00297 (total 1038 chars, unclipped)
[user] Η κολλητή μου, η Άννα, παντρεύεται τον Πέτρο στην Αίγινα και βαφτίζουν μαζί τη μικρή τους Δανάη. Τα παιδιά μου, έξι και εννέα ετών, θα τους δώσουν ένα χειροποίητο άλμπουμ με οικογενειακές φωτογραφίες. Γράψε μια ευχή που θα μπορούσαν να υπογράψουν και τα δύο στην πρώτη σελίδα.
[assistant] Αγαπημένοι μας Άννα και Πέτρο,

σας ευχόμαστε η κοινή σας ζωή να είναι γεμάτη αγάπη, γέλια και όμορφες οικογενειακές στιγμές! Να είστε πάντα ευτυχισμένοι και να καμαρώνετε τη μικρή σας Δανάη καθώς μεγαλώνει. Στη Δανάη ευχόμαστε να είναι γερή, καλότυχη και να φωτίζει πάντοτε τη ζωή σας, όπως φωτίζετε κι εσείς τη δική της.

Με όλη μας την αγάπη,
[τα ονόματά μας]
[user] Ξαναπές το σε κουκκίδες.
[assistant] • Αγαπημένοι μας Άννα και Πέτρο,

• Σας ευχόμαστε η κοινή σας ζωή να είναι γεμάτη αγάπη, γέλια και όμορφες οικογενειακές στιγμές!

• Να είστε πάντα ευτυχισμένοι και να καμαρώνετε τη μικρή σας Δανάη καθώς μεγαλώνει.

• Στη Δανάη ευχόμαστε να είναι γερή, καλότυχη και να φωτίζει πάντοτε τη ζωή σας, όπως φωτίζετε κι εσείς τη δική της.

• Με όλη μας την αγάπη,
  [τα ονόματά μας]
--- greek_math_v2 greek_math_v2:gm_nat_749_0 (total 456 chars, unclipped)
[user] Ο κύριος Νίκος έχει έναν ελαιώνα στην Καλαμάτα. Για το πότισμα των ελαιόδεντρων χρησιμοποιεί μια ορθογώνια δεξαμενή μήκους 4 m, πλάτους 2,5 m και ύψους 1,8 m. Η δεξαμενή είναι γεμάτη κατά 80%. Πόσα λίτρα νερού περιέχει;
[assistant] Το εμβαδόν της βάσης είναι:
4 · 2,5 = 10 m²

Ο συνολικός όγκος της δεξαμενής είναι:
10 · 1,8 = 18 m³

Ο όγκος του νερού είναι:
18 · 0,8 = 14,4 m³

Μετατρέπουμε τα κυβικά μέτρα σε λίτρα:
14,4 · 1.000 = 14.400 λίτρα

Απάντηση: 14.400 λίτρα
--- convskills_v2 convskills_v2:S1_00088 (total 5305 chars, unclipped)
[user] Εξηγήστε μου σας παρακαλώ γιατί, όταν πήγα να νοικιάσω αυτοκίνητο στη Σόφια, δεν δέχτηκαν το δίπλωμα ως απόδειξη ταυτότητας και μου ζήτησαν ταυτότητα ή διαβατήριο. Αφού και το δίπλωμα έχει φωτογραφία, όνομα και ημερομηνία γέννησης, ποια είναι η διαφορά;
[assistant] Το δίπλωμα οδήγησης αποδεικνύει κυρίως ότι έχετε δικαίωμα να οδηγείτε συγκεκριμένες κατηγορίες οχημάτων. Δεν αποτελεί όμως γενικά ταξιδιωτικό έγγραφο ούτε υποκαθιστά πάντοτε επίσημο δελτίο ταυτότητας ή διαβατήριο.

Γιατί κάνει αυτή τη διάκριση η εταιρεία; Κατά την ενοικίαση πρέπει να ελέγξει χωριστά δύο πράγματα: την άδεια οδήγησής σας και την ταυτότητά σας για τη σύμβαση, την ασφάλιση και ενδεχομένως την εγγύηση. Η φωτογραφία και η ημερομηνία γέννησης δεν αρκούν, επειδή κάθε έγγραφο εκδίδεται για διαφορετικό νομικό σκοπό.

Επομένως, στη Σόφια ήταν εύλογο να ζητήσουν έγκυρη ταυτότητα ή διαβατήριο επιπλέον του διπλώματος. Οι ακριβείς απαιτήσεις μπορεί επίσης να προβλέπονται στους όρους της συγκεκριμένης εταιρείας ενοικίασης.
[user] Μια κάτοικος από το Παλαιοχώρι Χαλκιδικής ζητά από το ΚΕΠ να της κλείσουμε ραντεβού στο αγροτικό ιατρείο, αλλά στο σύστημα δεν εμφανίζεται η δομή ούτε διαθέσιμο ημερολόγιο. Μπορείς να μου εξηγήσεις γιατί συμβαίνει αυτό και ποια υπηρεσία είναι συνήθως αρμόδια για τα ραντεβού;
[assistant] Αυτό συμβαίνει συνήθως επειδή το συγκεκριμένο αγροτικό ιατρείο δεν έχει ενταχθεί ως αυτοτελής δομή στο ηλεκτρονικό σύστημα ραντεβού ή επειδή δεν δημοσιεύει ηλεκτρονικό ημερολόγιο. Ενδέχεται επίσης να εξυπηρετείται από ιατρό που μετακινείται ορισμένες ημέρες από το αρμόδιο Κέντρο Υγείας. Επομένως, η απουσία του από το σύστημα δεν σημαίνει απαραίτητα ότι το ιατρείο δεν λειτουργεί.

Για το ραντεβού σας θα πρέπει συνήθως να επικοινωνήσετε απευθείας με το Κέντρο Υγείας στο οποίο υπάγεται το αγροτικό ιατρείο ή με τη γραμματεία του. Εκεί μπορούν να σας ενημερώσουν για τις ημέρες παρουσίας του ιατρού και για τον τρόπο προγραμματισμού της επίσκεψής σας. Αν δεν γνωρίζετε την αρμόδια μονάδα, μπορείτε να ζητήσετε από τον δήμο ή την αρμόδια Υγειονομική Περιφέρεια τα σωστά στοιχεία επικοινωνίας. Το ΚΕΠ μπορεί να σας βοηθήσει να εντοπίσετε την υπηρεσία, αλλά δεν μπορεί να καταχωρίσει ραντεβού όταν δεν υπάρχει διαθέσιμη δομή και ημερολόγιο στο σύστημα.
[user] Πώς αλλάζω βήμα βήμα τη γλώσσα στο δορυφορικό τηλέφωνο του πλοίου χωρίς να μπερδέψω τους όρους «network», «roaming» και «emergency calls»; Το μενού είναι στα αγγλικά και βρισκόμαστε καθ’ οδόν από Πειραιά προς Λεμεσό.
[assistant] Η ακριβής διαδρομή εξαρτάται από το μοντέλο του τηλεφώνου. Για να μην αλλάξεις κατά λάθος κρίσιμες ρυθμίσεις, ακολούθησε μόνο επιλογές που αφορούν τη συσκευή και τη γλώσσα:

1. Από την αρχική οθόνη άνοιξε το «Menu».
2. Επίλεξε «Settings».
3. Αναζήτησε «Phone» ή «Phone settings».
4. Επίλεξε «Language».
5. Διάλεξε «Greek» και επιβεβαίωσε με «OK» ή «Apply».
6. Αν δεν υπάρχουν Ελληνικά, επίλεξε μια γλώσσα που γνωρίζεις καλά και βγες από το μενού.

Μην ανοίξεις τις επιλογές «Network» ή «Roaming». Η πρώτη καθορίζει σε ποιο δορυφορικό δίκτυο συνδέεται η συσκευή. Η δεύτερη αφορά τη χρήση άλλου διαθέσιμου δικτύου και πιθανές πρόσθετες χρεώσεις. Η επιλογή «Emergency calls» προορίζεται για πραγματικό κίνδυνο και δεν αποτελεί ρύθμιση γλώσσας.

Επειδή βρίσκεσαι εν πλω, μην κάνεις επαναφορά εργοστασιακών ρυθμίσεων και μην αλλάξεις τον πάροχο ή την αυτόματη επιλογή δικτύου. Αν δεν βρίσκεις τη γλώσσα στα πρώτα επίπεδα του μενού, σταμάτησε και ζήτησε το ακριβές μοντέλο από τον υπεύθυνο επικοινωνιών του πλοίου.
[user] Γράψε ένα μικρό ραδιοφωνικό σποτ για τον Αγροτικό Σύλλογο Τυρνάβου που καλεί τους παραγωγούς άνω των 55 ετών σε ενημέρωση για πλασματικά χρόνια ασφάλισης. Η συνάντηση θα γίνει την Κυριακή στις 11 το πρωί στο παλιό δημαρχείο και θα μιλήσει εργατολόγος για στρατό, παιδιά, σπουδές και κενά ασφάλισης.
[assistant] Είσαι παραγωγός άνω των 55 ετών και σκέφτεσαι τη σύνταξή σου; Έλα αυτή την Κυριακή στις 11 το πρωί στο παλιό δημαρχείο. Ο Αγροτικός Σύλλογος Τυρνάβου σε καλεί σε ενημερωτική συνάντηση για τα πλασματικά χρόνια ασφάλισης. Εργατολόγος θα σου εξηγήσει τι μπορείς να αναγνωρίσεις από στρατό, παιδιά, σπουδές και κενά ασφάλισης. Έλα να ρωτήσεις όσα σε απασχολούν και να μάθεις τι ισχύει για τη δική σου περίπτωση. Κυριακή στις 11, στο παλιό δημαρχείο. Σε περιμένουμε.
[user] Στο λιμάνι του Αμβούργου, πόσες ώρες μπορώ να αφήσω αυτοκίνητο στο Parkplatz Überseequartier χωρίς να το μετακινήσω;
[assistant] Μπορείς να αφήσεις το αυτοκίνητο έως **720 ώρες**, δηλαδή 30 ημέρες, χωρίς να το μετακινήσεις. Το γκαράζ λειτουργεί όλο το 24ωρο και η χρέωση υπολογίζεται ανά 24ωρο. Πριν μπεις, κοίτα πάντως και την επιτόπια σήμανση, γιατί οι όροι μπορεί να αλλάξουν. [Επίσημες πληροφορίες της Contipark](https://www.contipark.de/de/parken/hamburg/tiefgarage-ueberseequartier/)
[user] Γράψε μια φανταστική καταχώριση ημερολογίου από τη σκοπιά μιας δεκαεπτάχρονης που περιμένει στην ουρά για ψωμί στην Κυψέλη τον Φεβρουάριο του 1942, ενώ ο πατέρας της προσπαθεί να ανταλλάξει το ρολόι του με τρόφιμα.
[assistant] Φλεβάρης του 1942. Η ουρά δεν προχωρά κι εγώ μετρώ τις ανάσες μου αντί για λεπτά. Ο πατέρας έφυγε με το ρολόι του παππού. Μακάρι να γυρίσει με αλεύρι πριν νυχτώσει.
[user] Ποιο ήταν το 6ο μήνυμά μου, λέξη προς λέξη;
[assistant] Γράψε μια φανταστική καταχώριση ημερολογίου από τη σκοπιά μιας δεκαεπτάχρονης που περιμένει στην ουρά για ψωμί στην Κυψέλη τον Φεβρουάριο του 1942, ενώ ο πατέρας της προσπαθεί να ανταλλάξει το ρολόι του με τρόφιμα.
--- math_en_math math_en_math:math_train_4407#1 (total 958 chars, unclipped)
[user] Suppose that the graph of \[2x^2 + y^2 + 8x - 10y + c = 0\]consists of a single point. (In this case, we call the graph a degenerate ellipse.) Find $c.$
[assistant] We try to rewrite the given equation in the standard form for an ellipse. Completing the square in both variables, we have \[\begin{aligned} 2(x^2+4x) + (y^2-10y) + c &= 0 \\ 2(x^2+4x+4) + (y^2-10y+25) + c &= 33 \\ 2(x+2)^2 + (y-5)^2 &= 33-c. \end{aligned}\]To get this equation in standard form, we would normally try to divide by $33-c,$ and if $33-c>0,$ then we get the standard form of a (non-degenerate) ellipse. But we cannot do so if $33-c=0.$ Indeed, if $33-c=0,$ then only one point $(x,y)$ satisfies the equation, because both $x+2$ and $y+5$ must be zero for the left-hand side to equal zero. (And if $33-c < 0$, then no points satisfy the equation, because the right-hand side is always nonnegative.) Thus, the value of $c$ that makes a degenerate ellipse satisfies $33-c=0,$ so $c=\boxed{33}.$
--- math_en_math math_en_math:math_train_5776#1 (total 279 chars, unclipped)
[user] The area of a circle is $49\pi$ square units. What is the radius of the circle, in units?
[assistant] Since the area of a circle is $\pi \cdot r^2$, where $r$ is the radius, we have the equation $\pi \cdot r^2 = 49\pi$. Solving for $r$, we find that $r=7$, so the radius is $\boxed{7}$ units.
--- math_en_math math_en_math:math_train_4028#1 (total 746 chars, unclipped)
[user] Let $\alpha$ and $\beta$ be conjugate complex numbers such that $\frac{\alpha}{\beta^2}$ is a real number and $|\alpha - \beta| = 2 \sqrt{3}.$  Find $|\alpha|.$
[assistant] Let $\alpha = x + yi$ and $\beta = x - yi.$  Then from $|\alpha - \beta| = 2 \sqrt{3},$ $2|y| = 2 \sqrt{3},$ so $|y| = \sqrt{3}.$

Now, $\frac{\alpha}{\beta^2}$ is real.  Since $\alpha$ and $\beta$ are complex conjugates, $\alpha^2 \beta^2$ is real, so $\frac{\alpha}{\beta^2} \cdot \alpha^2 \beta^2 = \alpha^3$ is real.  But
\[\alpha^3 = (x + yi)^3 = (x^3 - 3xy^2) + (3x^2 y - y^3) i,\]so $3x^2 y - y^3 = 0,$ or $y(3x^2 - y^2) = 0.$  Since $|y| = \sqrt{3},$ $y \neq 0,$ so $3x^2 = y^2 = 3,$ which means $x^2 = 1.$  Therefore,
\[|\alpha| = \sqrt{x^2 + y^2} = \sqrt{1 + 3} = \boxed{2}.\]
--- math_en_math math_en_math:math_train_2954#1 (total 1267 chars, unclipped)
[user] The sides of rectangle $ABCD$ have lengths $10$ and $11$. An equilateral triangle is drawn so that no point of the triangle lies outside $ABCD$. The maximum possible area of such a triangle can be written in the form $p\sqrt{q}-r$, where $p$, $q$, and $r$ are positive integers, and $q$ is not divisible by the square of any prime number. Find $p+q+r$.

[assistant] Since $\angle{BAD}=90$ and $\angle{EAF}=60$, it follows that $\angle{DAF}+\angle{BAE}=90-60=30$. Rotate triangle $ADF$ $60$ degrees clockwise. Note that the image of $AF$ is $AE$. Let the image of $D$ be $D'$. Since angles are preserved under rotation, $\angle{DAF}=\angle{D'AE}$. It follows that $\angle{D'AE}+\angle{BAE}=\angle{D'AB}=30$. Since $\angle{ADF}=\angle{ABE}=90$, it follows that quadrilateral $ABED'$ is cyclic with circumdiameter $AE=s$ and thus circumradius $\frac{s}{2}$. Let $O$ be its circumcenter. By Inscribed Angles, $\angle{BOD'}=2\angle{BAD}=60$. By the definition of circle, $OB=OD'$. It follows that triangle $OBD'$ is equilateral. Therefore, $BD'=r=\frac{s}{2}$. Applying the Law of Cosines to triangle $ABD'$, $\frac{s}{2}=\sqrt{10^2+11^2-(2)(10)(11)(\cos{30})}$. Squaring and multiplying by $\sqrt{3}$ yields $\frac{s^2\sqrt{3}}{4}=221\sqrt{3}-330\implies{p+q+r=221+3+330=\boxed{554}}$
--- math_en_math math_en_math:math_train_1470#1 (total 298 chars, unclipped)
[user] If the sum of the squares of nonnegative real numbers $a,b,$ and $c$ is $39$, and $ab + bc + ca = 21$, then what is the sum of $a,b,$ and $c$?
[assistant] Since $$(a+b+c)^2 = a^2 + b^2 + c^2 + 2ab + 2bc + 2ca = (39) + 2(21) = 81,$$ it follows that $a+b+c = \pm 9$. Since $a,b,c \ge 0$ we find $a+b+c=\boxed{9}$.
--- convskills_v2 convskills_v2:S1_00754 (total 5111 chars, unclipped)
[user] Θα μπορούσατε να μου πείτε αν είναι πρέπον να συλλυπηθώ τηλεφωνικώς την πρώην σύζυγό μου για την απώλεια της αδελφής της, έπειτα από δώδεκα χρόνια χωρίς επικοινωνία;
[assistant] Ναι. Ένα σύντομο και διακριτικό τηλεφώνημα είναι πρέπον αν εκφράσετε μόνο ειλικρινή συλλυπητήρια, χωρίς να ανακινήσετε το παρελθόν ή να προσδοκάτε περαιτέρω επικοινωνία. Αν φοβάστε ότι θα αιφνιδιαστεί, προτιμήστε πρώτα ένα μήνυμα.
[user] Μια νέα συνάδελφος με σκλήρυνση κατά πλάκας θα προσληφθεί στην κλινική μας στη Λάρισα. Για να περιορίζεται η κόπωση, συγκρίνω δύο λύσεις: συνεχόμενο εξάωρο 07:00–13:00 ή σπαστό ωράριο 07:00–11:00 και 17:00–19:00. Ποια επιλογή εξυπηρετεί καλύτερα την εργαζόμενη και τη λειτουργία του τμήματος, με βάση ανάπαυση, μετακινήσεις και παραδόσεις βάρδιας;
[assistant] Κατά κανόνα το συνεχόμενο 07:00–13:00 εξυπηρετεί καλύτερα και την εργαζόμενη και το τμήμα. Απαιτεί μία μόνο μετάβαση και επιστροφή, περιορίζει την επιβάρυνση από δύο προετοιμασίες εργασίας και δημιουργεί μία παράδοση βάρδιας αντί για δύο. Επιπλέον, προσφέρει προβλέψιμη κάλυψη του πρωινού ωραρίου.

Το σπαστό ωράριο παρέχει εξάωρο διάστημα ανάπαυσης, αλλά συνεπάγεται τέσσερις διαδρομές και δεύτερη ενεργοποίηση αργά το απόγευμα. Αυτά μπορεί να επιδεινώσουν την κόπωση και να αυξήσουν τα σημεία όπου χάνονται πληροφορίες κατά τις παραδόσεις.

Η τελική επιλογή πρέπει να συμφωνηθεί με την εργαζόμενη και τον ιατρό εργασίας. Αν η συνεχόμενη εξάωρη παρουσία είναι δύσκολη, μπορούν να προβλεφθούν σταθερά διαλείμματα, δροσερός χώρος ανάπαυσης, καθιστικά καθήκοντα και ευελιξία σε ημέρες έξαρσης. Το σπαστό ωράριο έχει νόημα μόνο αν η ίδια διαπιστώνει ότι η ενδιάμεση ανάπαυση υπερκαλύπτει την κόπωση των πρόσθετων μετακινήσεων.
[user] Πόσα μέτρα μακριά από τη σημερινή ακτογραμμή πρέπει να μετράμε όταν λέμε ότι ένα κτίσμα βρίσκεται μέσα σε ζώνη κινδύνου διάβρωσης;
[assistant] Δεν υπάρχει ένα καθολικό όριο σε μέτρα. Η ζώνη προκύπτει από τον τοπικό ρυθμό υποχώρησης της ακτής, τον χρονικό ορίζοντα, τις καταιγίδες, τη μορφολογία και τις επίσημες χαρτογραφήσεις. Επομένως, μετράμε από θεσμικά ορισμένη γραμμή αναφοράς και εφαρμόζουμε ειδική μελέτη, όχι μια σταθερή απόσταση.
[user] Επιστρέφω στο φροντιστήριο στη Λάρισα με ωράριο 15:00–21:30, όταν η κόρη μου θα είναι πέντε μηνών. Θεωρείτε ρεαλιστικό να θηλάζω πριν φύγω, να κάνω μία άντληση στο διάλειμμα και να ξαναθηλάζω το βράδυ, ή η τόσο μεγάλη απόσταση μεταξύ των γευμάτων κινδυνεύει να μειώσει αισθητά την παραγωγή μου; Θα ήθελα τη γνώμη σας με τα βασικά επιχειρήματα.
[assistant] Ναι, μπορεί να είναι ρεαλιστικό, ιδίως αν στους πέντε μήνες η παραγωγή σας έχει ήδη εδραιωθεί, αλλά μία μόνο άντληση σε απουσία περίπου επτά ωρών δεν επαρκεί εξίσου για όλες τις μητέρες. Η παραγωγή λειτουργεί κυρίως με βάση τη ζήτηση: αν το στήθος μένει συστηματικά γεμάτο για πολλές ώρες, μπορεί σταδιακά να μειωθεί το γάλα ή να εμφανιστούν συμφόρηση και ενόχληση. Θα βοηθούσε να θηλάζετε αμέσως πριν φύγετε, να αντλείτε περίπου στη μέση της βάρδιας και να θηλάζετε μόλις επιστρέφετε, καθώς και ελεύθερα τις υπόλοιπες ώρες. Κάντε δοκιμές πριν επιστρέψετε και παρακολουθήστε την άντληση, το βάρος και τις βρεγμένες πάνες. Αν διαπιστώσετε πτώση, εξετάστε δεύτερη σύντομη άντληση ή συμβουλευτείτε παιδίατρο ή πιστοποιημένη σύμβουλο γαλουχίας. Το NHS σημειώνει ότι αρχικά μπορεί να χρειάζεται άντληση τουλάχιστον ανά τρεις ώρες όταν βρίσκεστε μακριά από το μωρό ([NHS](https://www.nhs.uk/best-start-in-life/baby/feeding-your-baby/breastfeeding/breastfeeding-returning-to-work/)).
[user] Για την εργασια φυσικης πηγαμε στην παραλια του Βολου και ειδαμε αμμο, βοτσαλα, ενα τοιχιο και μια προβλητα. Ποια σημαδια μπορω να βαλω σε λιστα για να ξεχωρισω αν η ακτη διαβρωνεται, αν μαζευει υλικο ή αν απλα αλλαζει με τις εποχες;
[assistant] Μπορείς να καταγράψεις τα εξής σημάδια:

- διάβρωση: η ακτογραμμή υποχωρεί, αποκαλύπτονται ρίζες ή θεμέλια, σχηματίζεται απότομο «σκαλοπάτι» στην άμμο, λιγοστεύουν η άμμος και τα βότσαλα ή εμφανίζονται φθορές στο τοιχίο
- συσσώρευση υλικού: η παραλία πλαταίνει, δημιουργούνται νέες λωρίδες άμμου ή σωροί από βότσαλα και το υλικό μαζεύεται κυρίως στη μία πλευρά της προβλήτας
- εποχική μεταβολή: η ακτή στενεύει τον χειμώνα και ξαναπλαταίνει το καλοκαίρι, χωρίς σταθερή υποχώρηση από χρόνο σε χρόνο
- επίδραση κατασκευών: σύγκρινε τις δύο πλευρές της προβλήτας και του τοιχίου, επειδή συσσώρευση στη μία πλευρά και διάβρωση στην άλλη δείχνουν παρεμπόδιση της μεταφοράς υλικού
- τεκμηρίωση: βγάλε φωτογραφίες από τα ίδια ακριβώς σημεία, μέτρα την απόσταση του νερού από σταθερά σημάδια και σημείωσε ημερομηνία, καιρό, κύματα και παλίρροια

Μία μόνο επίσκεψη δεν αρκεί για ασφαλές συμπέρασμα. Χρειάζονται επαναλαμβανόμενες παρατηρήσεις σε διαφορετικές εποχές και, ιδανικά, μετά από δυνατές κακοκαιρίες.
[user] Πόση ώρα κάνει περίπου το φέρι από το Χονγκ Κονγκ για το Μακάο;
[assistant] Υπολογίστε περίπου 55–60 λεπτά εν πλω από το Χονγκ Κονγκ προς το Μακάο. Για τον συνολικό χρόνο, καλό είναι να προβλέψετε περίπου 90 λεπτά μαζί με την έγκαιρη προσέλευση και τους ελέγχους· πριν φύγετε, ελέγξτε το συγκεκριμένο δρομολόγιο στην [TurboJET](https://www.turbojet.com.hk/en/routing-sailing-schedule/hong-kong-macau/sailing-schedule-fares).
[user] Μέτρα: πόσα μηνύματα σού είχα στείλει πριν από το τωρινό;
[assistant] 6
--- convskills_v2 convskills_v2:S3_00103#1 (total 1279 chars, unclipped)
[user] Γυρίζω από μπάρκο και βρήκα τις μουριές στην οδό Κανάρη στον Πειραιά να ακουμπάνε στο μπαλκόνι μου. Ποια προβλήματα πρέπει να καταγράψω πριν κάνω αναφορά στον δήμο και ποια στοιχεία να έχω μαζί μου;
[assistant] Πριν από την αναφορά, καταγράψτε αν τα κλαδιά τρίβονται στα κάγκελα, στα κουφώματα ή στην πρόσοψη, αν έχουν προκαλέσει ρωγμές, γρατζουνιές, υγρασία ή ζημιά σε τέντες και αν επιτρέπουν πρόσβαση εντόμων ή ζώων στο μπαλκόνι. Σημειώστε επίσης τυχόν ξερά ή σπασμένα κλαδιά, επαφή με καλώδια, περιορισμό ορατότητας, εμπόδια στο πεζοδρόμιο και πεσμένους καρπούς που δημιουργούν ολισθηρότητα.

Έχετε μαζί σας την ακριβή διεύθυνση, τον όροφο, στοιχεία επικοινωνίας, ημερομηνίες παρατήρησης και καθαρές φωτογραφίες γενικού και κοντινού πλάνου. Χρήσιμες είναι οι κατά προσέγγιση αποστάσεις των κλαδιών από το κτίριο, οι ώρες που εμφανίζεται το πρόβλημα, η περιγραφή τυχόν προηγούμενης ζημιάς και οι αριθμοί παλαιότερων αναφορών. Ζητήστε αριθμό πρωτοκόλλου και κρατήστε αντίγραφο. Μην κλαδέψετε μόνος σας δημοτικό δέντρο και ειδοποιήστε άμεσα τις αρμόδιες υπηρεσίες αν υπάρχει κίνδυνος πτώσης ή επαφή με ηλεκτροφόρα καλώδια.
[user] Ξαναπές το σε λίστα με ένα μόνο στοιχείο, το πιο σημαντικό.
[assistant] - Καταγράψτε με καθαρές φωτογραφίες ότι τα κλαδιά ακουμπούν στο μπαλκόνι και τυχόν ζημιές ή άμεσους κινδύνους.
--- convskills_v2 convskills_v2:S2_00860 (total 8723 chars, unclipped)
[user] Από την 1η Νοεμβρίου μετακομίζουμε τέσσερα άτομα της ομάδας backend σε νοικιασμένο σπίτι στην Άνδρο για δοκιμαστική τηλεργασία 14 ημερών. Έχουμε κοινό budget 1.800 ευρώ, δύο αυτοκίνητα, καθημερινό stand-up στις 10:00 και εναλλάξ on-call κάλυψη όλο το εικοσιτετράωρο. Χρειάζομαι πλάνο για μεταφορά, θέσεις εργασίας, ίντερνετ με εφεδρεία, βάρδιες, ψώνια και μία ημέρα επιστροφής στην Αθήνα αν αποτύχει η υποδομή.
[assistant] 1–14 Νοεμβρίου: κλείστε ακτοπλοϊκά για τέσσερις και δύο αυτοκίνητα, με άφιξη μία ημέρα νωρίτερα. Προϋπολογισμός: 500€ μεταφορά, 850€ σπίτι, 300€ ψώνια, 150€ εφεδρεία. Πριν φύγετε, επιβεβαιώστε τέσσερα γραφεία, εργονομικές καρέκλες, πολύπριζα και ήσυχους χώρους. Κύρια σύνδεση: σταθερό ίντερνετ με δοκιμή ταχύτητας. Εφεδρεία: δύο 5G routers διαφορετικών παρόχων και φορτισμένα power banks. Stand-up 10:00, κοινές ώρες 10:00–17:00. Ένας διαφορετικός primary on-call ανά ημέρα, με δεύτερο backup και ρεπό μετά από νυχτερινό συμβάν. Κάντε δύο ομαδικά ψώνια και κοινό ταμείο αποδείξεων. Ορίστε την 3η Νοεμβρίου ως ημέρα επιστροφής στην Αθήνα αν αποτύχουν και οι τρεις συνδέσεις ή υπάρχουν παρατεταμένες διακοπές ρεύματος.
[user] Σκαρφίσου έναν σύντομο διάλογο ανάμεσα σε έναν αφηρημένο υπάλληλο ΚΕΠ και στο tablet της Ψηφιακής Κάρτας, που του θυμίζει ότι ξέχασε να δηλώσει την αποχώρησή του την Παρασκευή πριν φύγει για το τριήμερο.
[assistant] Υπάλληλος: «Γιατί αναβοσβήνετε; Δεν βλέπετε ότι φεύγω για το τριήμερο;»

Τάμπλετ: «Το βλέπω. Εσείς όμως βλέπετε ότι δεν δηλώσατε την αποχώρησή σας;»

Υπάλληλος: «Μα είναι Παρασκευή. Δεν μπορείτε να το ξεχάσετε μέχρι την Τρίτη;»

Τάμπλετ: «Μπορώ να ξεχάσω πολλά. Εσείς όμως πατήστε πρώτα “αποχώρηση” και μετά ξεχάστε με όσο θέλετε.»

Υπάλληλος: «Σωστά. Ευτυχώς που είστε πιο συγκεντρωμένο από εμένα.»

Τάμπλετ: «Καλό τριήμερο. Και τώρα μπορείτε να αποχωρήσετε επισήμως.»
[user] Από εδώ και πέρα να μου μιλάς στον πληθυντικό ευγενείας.
[assistant] Θα σας απευθύνομαι στον πληθυντικό.
[user] Λες να αξίζει να χάσω μία μέρα από το καλοκαιρινό διάβασμα για να πάω πρώτη φορά στο πανηγύρι της Αγίας Μαρίνας στο χωριό του παππού μου, στην Άνδρο; Οι γονείς μου λένε ότι είναι σημαντικό για την οικογένεια, αλλά τον Ιούλιο προετοιμάζομαι ήδη για Πανελλαδικές και θα γυρίσουμε ξημερώματα.
[assistant] Ναι, πιθανότατα αξίζει να διαθέσετε μία ημέρα για μια πρώτη οικογενειακή εμπειρία που ίσως δεν επαναληφθεί εύκολα. Προγραμματίστε ελαφρύτερο διάβασμα εκείνη την ημέρα και ανάπαυση την επομένη· αν όμως ακολουθεί διαγώνισμα ή η επιστροφή θα σας στερήσει κρίσιμο ύπνο, φύγετε νωρίτερα από το πανηγύρι.
[user] Μένω τρεις μήνες σε Airbnb στη Νάξο και η τηλεόραση έχει μόνο τέσσερα ελληνικά κανάλια. Ο ιδιοκτήτης λέει να αγοράσω εγώ μικρή κεραία με 25 ευρώ. Νομίζετε είναι λογικό για προσωρινή διαμονή ή καλύτερα να ζητήσω από αυτόν να ελέγξει την κεραία του σπιτιού; Ποιοι είναι οι λόγοι;
[assistant] Ζητήστε πρώτα από τον ιδιοκτήτη να ελέγξει την κεραία, την καλωδίωση και τον συντονισμό της τηλεόρασης, ιδίως αν η τηλεόραση δηλωνόταν ως παροχή. Η βλάβη μπορεί να αφορά την εγκατάσταση του σπιτιού, η κεραία που θα αγοράσετε ίσως δεν λύσει το πρόβλημα και δεν είναι λογικό να επιβαρυνθείτε για πάγιο εξοπλισμό προσωρινής κατοικίας. Αγοράστε τη μόνο αν συμφωνήσει γραπτώς να σας επιστρέψει τα 25 ευρώ ή αν θέλετε να την κρατήσετε.
[user] Κάθε πόσες ώρες συνιστάται συνήθως αλλαγή θέσης σε κατακεκλιμένο ηλικιωμένο με υψηλό κίνδυνο κατακλίσεων στο σπίτι;
[assistant] Για κατακεκλιμένο ηλικιωμένο υψηλού κινδύνου χρησιμοποιείται συχνά ως πρακτικό σημείο εκκίνησης αλλαγή θέσης ανά 2–4 ώρες, αλλά δεν υπάρχει ένα ασφαλές διάστημα για όλους. Το πρόγραμμα πρέπει να εξατομικευτεί από νοσηλευτή ή γιατρό βάσει του δέρματος, της κινητικότητας, του στρώματος και της γενικής κατάστασης· ορισμένες οδηγίες θέτουν για υψηλό κίνδυνο τουλάχιστον μία αλλαγή ανά 4 ώρες. Χρειάζονται επίσης καθημερινός έλεγχος του δέρματος και κατάλληλο στρώμα αποφόρτισης. [Οδηγίες NHS](https://www.cpft.nhs.uk/download/g04-guidelines-on-the-prevention-and-management-of-pres.pdf?ver=16238)
[user] Για το κυριακάτικο τραπέζι του τμήματος θα φτιάξουμε έναν δίσκο με τυριά από τις Κυκλάδες. Δώσε μου επιλογές χωρισμένες σε ήπια, πικάντικα, φρέσκα και σκληρά, ώστε να υπάρχει κάτι κατάλληλο και για όσους αποφεύγουν τις πολύ έντονες γεύσεις.
[assistant] Ήπια: γραβιέρα Νάξου και νεαρό βολάκι Άνδρου. Πικάντικα: κοπανιστή Μυκόνου ή Τήνου και παλαιωμένη μανούρα Σίφνου. Φρέσκα: ξινομυζήθρα Νάξου και φρέσκια πετρωτή Άνδρου. Σκληρά: αρσενικό Νάξου και Σαν Μιχάλη Σύρου. Για όσους αποφεύγουν τις έντονες γεύσεις, δώστε περισσότερο χώρο στη γραβιέρα και στο νεαρό βολάκι, ενώ σερβίρετε την κοπανιστή χωριστά.
[user] Θα θέλατε να μου δώσετε έναν κατάλογο με τα βασικά χαρακτηριστικά που αξίζει να αναφέρω στην αγγελία για το τριάρι μου στη Λάρισα, όπως θέρμανση, όροφος, ασανσέρ και απόσταση από την κεντρική πλατεία;
[assistant] Στην αγγελία αξίζει να αναφέρετε: ακριβή περιοχή και απόσταση από την κεντρική πλατεία, τετραγωνικά, όροφο, έτος κατασκευής και ανακαίνισης, αριθμό υπνοδωματίων, τύπο και αυτονομία θέρμανσης, κλιματισμό, ενεργειακή κλάση, ασανσέρ, κοινόχρηστα, κουφώματα και μόνωση, προσανατολισμό και φωτεινότητα, μπαλκόνια, αποθήκη, θέση στάθμευσης, επίπλωση και ηλεκτρικές συσκευές, σύνδεση οπτικής ίνας, προσβασιμότητα, πολιτική για κατοικίδια, ζητούμενο μίσθωμα και εγγύηση, καθώς και την πραγματική διαθεσιμότητα του ακινήτου.
[user] Μια νέα συνάδελφος με σκλήρυνση κατά πλάκας θα προσληφθεί στην κλινική μας στη Λάρισα. Για να περιορίζεται η κόπωση, συγκρίνω δύο λύσεις: συνεχόμενο εξάωρο 07:00–13:00 ή σπαστό ωράριο 07:00–11:00 και 17:00–19:00. Ποια επιλογή εξυπηρετεί καλύτερα την εργαζόμενη και τη λειτουργία του τμήματος, με βάση ανάπαυση, μετακινήσεις και παραδόσεις βάρδιας;
[assistant] Το συνεχόμενο 07:00–13:00 είναι συνήθως λειτουργικότερο: περιορίζει τις μετακινήσεις σε μία μετάβαση και μία επιστροφή, δεν δεσμεύει ολόκληρη την ημέρα και απαιτεί λιγότερες παραδόσεις βάρδιας. Το σπαστό παρέχει μεγάλη ενδιάμεση ανάπαυση, αλλά προσθέτει κόπωση από δύο κύκλους μετακίνησης και επανεκκίνησης. Η τελική επιλογή πρέπει να συμφωνηθεί με την εργαζόμενη και, όπου χρειάζεται, με τον ιατρό εργασίας, με δυνατότητα διαλειμμάτων, δροσερό χώρο και επανεκτίμηση μετά από δοκιμαστική περίοδο.
[user] Θα επέστρεφες από Θεσσαλονίκη στην Αθήνα με το τελευταίο τρένο την Κυριακή ή με το νυχτερινό ΚΤΕΛ, αν τη Δευτέρα στις 09:00 είχες υποχρεωτικό σεμινάριο στο πανεπιστήμιο; Θέλω τη γνώμη σου με βάση την αξιοπιστία, την ξεκούραση και τον κίνδυνο καθυστέρησης.
[assistant] Για υποχρεωτικό σεμινάριο τη Δευτέρα στις 09:00, θα επέστρεφα με τρένο νωρίτερα την Κυριακή και όχι με το τελευταίο μέσο. Αν έπρεπε να επιλέξετε αποκλειστικά μεταξύ τελευταίου τρένου και νυχτερινού ΚΤΕΛ, θα προτιμούσα το τρένο μόνο εφόσον το δρομολόγιο επιβεβαιώνεται την ίδια ημέρα και αφήνει αρκετές ώρες ύπνου στην Αθήνα· διαφορετικά, το ΚΤΕΛ αποτελεί εφεδρεία αλλά προσφέρει σαφώς χειρότερη ξεκούραση. Ελέγξτε πριν φύγετε τις [ζωντανές ενημερώσεις της Hellenic Train](https://www.hellenictrain.gr/eksypiretisi-epivaton/katastasi-kykloforias/live-plirofories-dromologion/) και το [επίσημο πρόγραμμα του ΚΤΕΛ Θεσσαλονίκης](https://ktelthes.gr/dromologia-thessaloniki-athina-peiraias/).
[user] Φτιάξε ένα χιουμοριστικό τετράστιχο για να το κολλήσω στο ταξί, όπου μια ATH.ENA Card παραπονιέται ότι όλοι θυμούνται να τη φορτίσουν ηλεκτρονικά μόνο όταν φτάσουν μπροστά στην πύλη του μετρό στο Σύνταγμα.
[assistant] «Όλη τη μέρα μένω αδειανή, κανείς δεν με θυμάται,
μα μόλις δουν την πύλη μπρος, το κινητό πετάγεται.
Στο Σύνταγμα με φορτίζουνε με άγχος και λαχτάρα—
θυμηθείτε με απ’ το σπίτι σας, όχι μπρος στην μπάρα!»
[user] Γιατί η εγγύηση ενός ενοικίου δεν θεωρείται αυτομάτως «τελευταίο μίσθωμα»; Στο συμβόλαιο του διαμερίσματος που νοικιάζω στα Εξάρχεια αναφέρεται εγγύηση 650 ευρώ, αλλά ο ιδιοκτήτης λέει ότι πρέπει να πληρώσω κανονικά και τον τελευταίο μήνα πριν αποχωρήσω.
[assistant] Η εγγύηση εξασφαλίζει χωριστές πιθανές απαιτήσεις του ιδιοκτήτη, όπως ζημιές, ανεξόφλητους λογαριασμούς ή μισθώματα, και κανονικά εκκαθαρίζεται μετά την παράδοση του ακινήτου. Δεν αποτελεί προκαταβολή του τελευταίου μήνα, εκτός αν το μισθωτήριο το προβλέπει ή συμφωνήσετε διαφορετικά. Επομένως πληρώστε κανονικά το τελευταίο μίσθωμα και ζητήστε γραπτώς ημερομηνία αυτοψίας, πρωτόκολλο παράδοσης και επιστροφή των 650 ευρώ μετά τον έλεγχο· αν υπάρχει διαφωνία, χρειάζεται έλεγχος του συγκεκριμένου συμβολαίου από δικηγόρο.
[user] Εντάξει, άσε τον περιορισμό, απάντα κανονικά.
[assistant] Έγινε, απαντώ κανονικά.
[user] Γράψε μου ένα μικρό, ζεστό μήνυμα για την ομαδική συνομιλία της βάρδιας μας στο νοσοκομείο «Αττικόν». Θέλω να ενημερώσω ότι άφησα ψηφιακή εξουσιοδότηση μέσω gov.gr στη συνάδελφο Ελένη Παππά για να παραλάβει εκ μέρους μου τις στολές από την αποθήκη, και να την ευχαριστήσω με λίγο χιούμορ για τη βοήθεια.
[assistant] Καλημέρα, ομάδα! Άφησα ψηφιακή εξουσιοδότηση μέσω gov.gr στην Ελένη Παππά για να παραλάβει τις στολές μου από την αποθήκη. Ελένη, ευχαριστώ που σώζεις και τη βάρδια και τη γκαρνταρόμπα μου!

=== §I TRAINER LABEL INSPECTION (cluster, sft5 env, the trainer's tokenize_messages on the launch manifest) ===
=== format_mc format_mc:mc_openbookqa_4994: 204 tokens, 8 supervised; assistant turns 4, flagged train=false 0; supervised spans 4
   span 0: 'A<|assistant_end|>'
   span 1: 'B<|assistant_end|>'
   span 2: 'B<|assistant_end|>'
   span 3: 'A<|assistant_end|>'
=== greek_math_v2 greek_math_v2:c2_gsm_2544#1: 352 tokens, 205 supervised; assistant turns 1, flagged train=false 0; supervised spans 1
   span 0: 'Για κάθε κιλό βάρους, το παιδί πρέπει να λαμβάνει 5 ml φαρμάκου. Αφού το παιδί ζυγίζει 30 κιλά, υπολογίζουμε πρώτα τη συνολική ποσότητα του φαρμάκου:\n\n\\[\n30\\,\\t'

--- trainer code: labels built per token before packing; packing config ---
def tokenize_messages(tokenizer, messages: list[dict[str, Any]]) -> dict[str, list[int]]:
    """Render a conversation and build labels for the supervised assistant turns.

    Every assistant message is supervised unless it carries ``"train": false``
    (a context-only turn: a planted failure the model must see but never
    imitate). Only role/content reach the template; the patched Apertus
    template yields exactly one contiguous generation span per assistant
    message (content followed by the assistant-end token), which is what lets
    the per-message flag map onto the token mask.
    """
    render_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    train_flags = [bool(m.get("train", True)) for m in messages if m["role"] == "assistant"]
    rendered = tokenizer.apply_chat_template(
        render_messages,
        tokenize=True,
        return_dict=True,
        return_assistant_tokens_mask=True,
    )
    input_ids = list(rendered["input_ids"])
    assistant_mask = list(rendered.get("assistant_masks", []))
    if len(input_ids) != len(assistant_mask) or not any(assistant_mask):
        raise ConfigError("chat template did not produce a non-empty assistant mask")
    # Group the template's generation spans by assistant turn: each turn's group ends with the span that carries
    # the assistant-end token. A turn can render as more than one span when its content ends in a character that
    # the byte-level tokenizer splits (an emoji): the template's offset-based mask leaves the trailing byte tokens
    # unmarked, so the content span and the end-token span are separated by one or two unmasked content tokens.
    # Those gap tokens are content, never structure (the end token follows the content directly in the Apertus
    # template); they are supervised for a target turn and masked with the rest for a context turn.
    end_id = tokenizer.convert_tokens_to_ids(ASSISTANT_END)
    control_ids = set(tokenizer.convert_tokens_to_ids(list(APERTUS_CONTROL_IDS)))
    runs = _mask_runs(assistant_mask)
    groups: list[tuple[int, int]] = []
    group_start: int | None = None
    for start, end in runs:
        if group_start is None:
            group_start = start
        if end_id in input_ids[start:end]:
            groups.append((group_start, end))
            group_start = None
    if group_start is not None or len(groups) != len(train_flags):
        raise ConfigError(
            f"assistant mask yields {len(groups)} turn groups (+{int(group_start is not None)} open) for {len(train_flags)} assistant messages"
        )
    for (start, end), flag in zip(groups, train_flags, strict=True):
        gap = [index for index in range(start, end) if not assistant_mask[index]]
        if len(gap) > 3 or any(input_ids[index] in control_ids for index in gap):
            raise ConfigError(f"unexpected unmasked tokens inside an assistant turn at {gap[:5]}")
        for index in range(start, end):
            assistant_mask[index] = 1 if flag else 0
    if not any(assistant_mask):
        raise ConfigError("row has no supervised assistant tokens after applying train=false flags")
    labels = [token_id if bit else -100 for token_id, bit in zip(input_ids, assistant_mask, strict=True)]
    return {"input_ids": input_ids, "assistant_masks": assistant_mask, "labels": labels}


def validate_and_tokenize_data(

        "fp16": False,
        "max_length": int(config["max_length"]),
        "packing": True,
        "packing_strategy": "bfd",
        "padding_free": False,  # BFD makes this true inside TRL.
        "eval_packing": False,
        "assistant_only_loss": True,
        "completion_only_loss": False,
        "shuffle_dataset": True,
        "eval_strategy": "epoch",

--- inspection script ---
#!/usr/bin/env python3
"""Trainer-side label inspection (astra gate-2 F6): render rows with the trainer's own tokenize_messages and print which assistant turns are supervised.
Run on the cluster in the sft5 env: python cluster/inspect_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sft_train as T
ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--train', required=True); a = ap.parse_args()
config = T.load_config(a.config); tok = T.prepare_tokenizer(config); tok = tok[0] if isinstance(tok, tuple) else tok
want = {'format_mc': lambda r: sum(1 for m in r['messages'] if m['role'] == 'assistant') >= 3, 'correcting_v2': lambda r: any(m.get('train') is False for m in r['messages']), 'convskills_v2': lambda r: any(m.get('train') is False for m in r['messages']), 'greek_math_v2': lambda r: True}
picked = {}
for l in open(a.train):
    r = json.loads(l); c = r['config']
    if c in want and c not in picked and want[c](r): picked[c] = r
    if len(picked) == len(want): break
for c, r in picked.items():
    out = T.tokenize_messages(tok, r['messages']); ids, labels = out['input_ids'], out['labels']
    n_sup = sum(1 for x in labels if x != -100); spans = []; cur = []
    for i, (t, lab) in enumerate(zip(ids, labels)):
        if lab != -100: cur.append(t)
        elif cur: spans.append(tok.decode(cur)); cur = []
    if cur: spans.append(tok.decode(cur))
    flags = [(m.get('train', True)) for m in r['messages'] if m['role'] == 'assistant']
    print(f"=== {c} {r['id']}: {len(ids)} tokens, {n_sup} supervised; assistant turns {len(flags)}, flagged train=false {flags.count(False)}; supervised spans {len(spans)}")
    for k, sp in enumerate(spans): print(f"   span {k}: {sp[:160]!r}")

=== §J S5m AUDIT + PREDECLARED CRITERIA ===
S5m audit summary: {"n": 100, "flawed": 74, "contradicts": 9, "unsupported": 69, "ambiguity": 23}
**Gate-2 outcome (05:00) and fixes.** astra HOLD → fixed before launch: label check turned into a positive agreement join (translated rows and English GSM8K rows kept only on an 'agreed' record; native rows and the published MATH solutions exempt by recipe); strict numeric fallback (four rescues, audited); dev split partition-first for the format block and overlap checked across all user turns; the English-IFEval waiver for the two constraint blocks re-implemented over every other cache with all memberships preserved and disclosed as a cache-wide waiver; trainer-side label inspection of masked turns; receipt bound to cache, code, input and model identities; chain refuses a manifest whose sha256 differs from the receipt. **S5m lane dropped**: a Sol audit of 100 rows found 74 flawed (69 unsupported specifics, 23 ambiguity resolved without basis, 9 contradictions); the other suite lanes stay.

**Predeclared promotion criteria (frozen before launch, refined 05:30 after astra F7).** 1-G4F6P1 becomes the RLHF starting point if, against the incumbent 1-G2F1P1 under identical protocols: (1) no regression beyond the tolerance on IFEval-el, MGSM-el, GreekMMLU official, MT-Bench-el (tolerances, operational not statistical: 2 pp on 500-item sets, 3 pp on MGSM, 0.5 pp on GreekMMLU, 0.2 on MT-Bench); (2) MATH-500-el behaviour not worse than the worked pilots: loops ≤ 45 and truncations ≤ 65 of 500 (round 3 had 69 / 96), non-Greek prose ≤ 10 of 500; (3) chat-mode retention (Global-MMLU, ARC-C, HellaSwag) not below the incumbent by more than 1 pp; (4) at least one of IFEval-el, MATH-500-el, GreekMMLU official, MT-Bench-el, or the native-suite macro average (mean of the eight native benchmarks, +1 pp) improved by more than its tolerance. **Failure of any of (1)–(3) → HOLD and RLHF starts from the incumbent.** (1)–(3) hold and (4) fails → "equal", owner's call. The format block's effect is reported descriptively (no ablation); the pilot's loop/truncation figures (37/59 and 45/62) are the reference for (2), not the stage-1 band.
**06:10: trainer masking defect.** The training path does not honour `train:false` (ledger entry). The pass drops correcting v2 and the S4 lane and declares the format demonstrations supervised; the trainer fix is scheduled after this run. Round 3's numbers carry the defect.
