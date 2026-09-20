Review target: GATE 1 of docs/R4_EXEC_PLAN_20260914.md (data/manifest freeze + launch readiness) for the three pilot continuations M0/M1/M2.
You reviewed the plan itself this morning (docs/reviews/ASTRA_r4_exec_plan_20260914.md); its findings are dispositioned in the plan's §8. Do not re-review the plan; review the ARTIFACTS against it.
Judge: (1) do the arm receipts prove the contrast the plan claims (same retained problem ids in M0/M1, byte-identical prompts, only the Greek maths block differs, English block and replay identical)? (2) are the cut-2 verification gates applied as specified (fidelity on every problem, derivation validity at high on every solution, repair-at-high, post-polish recheck) and are the drop counts reported honestly? (3) decontamination: MATH-500 exclusions propagated; inherited exposure disclosed; (4) launch readiness: configs vs the recipe table in plan §4, token/update counts, budget (preflight), the frozen decision rule and readout script; (5) anything that would make the pilot readout uninterpretable.
Disposition: BLOCKER/HIGH block the launch until fixed; MEDIUM/LOW logged. Report failing counts you can verify from the receipts below.

=== CUT-2 RECEIPT (data/math/cut2/final/receipt.json) ===
{
 "inputs": {
  "source_problems": 11495,
  "fidelity_results": 11495,
  "solutions": 11483,
  "validity_results": 11696,
  "polish_results": 11698,
  "cut1_rows": 14215,
  "native": 5108
 },
 "stage_counts": {
  "translated_gsm8k:source": 6000,
  "translated_gsm8k:kept": 5735,
  "translated_math:source": 3999,
  "translated_math:kept": 3195,
  "translated_math5:source": 1496,
  "translated_math5:kept": 1376,
  "translated_gsm8k:retained_final": 5735,
  "translated_math:retained_final": 3195,
  "translated_math5:retained_final": 1376
 },
 "dropped": {
  "translated_gsm8k:unfaithful_both_stages": 75,
  "translated_gsm8k:invalid_derivation": 81,
  "translated_gsm8k:no_cut1_pair": 96,
  "translated_gsm8k:length_short": 2,
  "translated_gsm8k:repeated_lines": 9,
  "translated_gsm8k:unpolished": 2,
  "translated_math:no_cut1_pair": 647,
  "translated_math:unfaithful_both_stages": 14,
  "translated_math:invalid_derivation": 23,
  "translated_math:math500_13gram": 87,
  "translated_math:no_solution": 9,
  "translated_math:length_short": 10,
  "translated_math:boxed_not_equivalent": 9,
  "translated_math:repeated_lines": 5,
  "translated_math5:invalid_derivation": 20,
  "translated_math5:unfaithful_both_stages": 47,
  "translated_math5:math500_13gram": 47,
  "translated_math5:no_solution": 3,
  "translated_math5:repeated_lines": 3
 },
 "flags": {
  "first_stage_flagged": 727,
  "audit_flagged": 5,
  "adjudicated": 727,
  "overturned_by_high": 585,
  "polished_edited": 3197,
  "polish_reverted": 17,
  "translated_overlays_user_changed_skipped": 1,
  "M0_overlays_applied": 1,
  "translated_math5:decimal_point_outside_latex": 2,
  "translated_math5:over_400_words": 2,
  "native_overlays_applied": 3,
  "native_overlays_unmatched": 0
 },
 "files": {
  "rows_M0": {
   "rows": 8930,
   "sha256": "92ce1bbdda36ada08a2557713bb688b39117ecf01f9f68c5acae9c9307b01858"
  },
  "rows_M1": {
   "rows": 8930,
   "sha256": "10ddebaf63f4b38395c92da96e34e38f049b2c5cd1281e61b9531e80288b30fa"
  },
  "rows_M2_extra": {
   "rows": 1376,
   "sha256": "a1d2da541e1711fc30d561aaa2527adec21a859cd71a594f9cb6c807557dc57e"
  },
  "rows_native": {
   "rows": 5108,
   "sha256": "e7314def02b72e619d55aa0b57a260745f23c0097cbf845e9da12817e4964f83"
  },
  "arm_M0": {
   "rows": 14038,
   "sha256": "bc9bdceeff25a1267ea09c8f947537ca84e1f3f1fa7a3229339e2c814aff677f"
  },
  "arm_M1": {
   "rows": 14038,
   "sha256": "fcb9c876f3f44aa72c52e4a5f81148bc23ff0053a9c1865d5e3edea5d8fa35de"
  },
  "arm_M2": {
   "rows": 15414,
   "sha256": "9e89580fd0de114ccc991ddb3a5f1086eb73082bc15a2a72237ea7b86f289637"
  }
 },
 "paired_ids_M0_M1": 8930,
 "dev_rows": {
  "paired": 89,
  "level5": 13,
  "native": 51,
  "english_twins_excluded": 102
 },
 "tokenizer": "apertus-tokenizer",
 "words": {
  "M0": 40.433818589025755,
  "M1": 105.81153415453528,
  "M2_extra": 157.79360465116278,
  "native": 47.653876272513706
 }
}

=== ENGLISH BLOCK RECEIPT (data/math/en/build_receipt.json) ===
{"gsm_rows_in": 100000, "gsm_problems": 7417, "gsm_kept": 22211, "k": 3, "gsm_identical_solutions_collapsed": 7, "math_in": 7500, "math_kept": 7328, "math_dropped": 172, "drop_reasons": {"13gram_math500": 171, "exact_math500": 1}, "levels": {"Level 5": 2235, "Level 3": 1558, "Level 4": 1655, "Level 1": 556, "Level 2": 1322, "Level ?": 2}}

=== INHERITED EXPOSURE (MATH-500 vs parent training data) ===
{"R2_stage1": {"train_file": "data/arms/R2_stage1/train.jsonl", "rows_scanned": 334383, "hit_rows": 1, "distinct_eval_items_hit": 1, "by_config": [{"config": "dolci_code_algo_20k", "kind": "13gram", "rows": 1}]}, "R3_single": {"train_file": "data/arms/R3_single/train.jsonl", "rows_scanned": 403727, "hit_rows": 17, "distinct_eval_items_hit": 12, "by_config": [{"config": "dolci_code_algo_20k", "kind": "13gram", "rows": 1}, {"config": "greek_math", "kind": "13gram", "rows": 16}]}}

=== ARM RECEIPTS ===
--- M0: {"arm": "M0", "seed": 42, "parent": "data/arms/R2_stage1/train.jsonl", "replay_frac": 0.1, "tokenizer": "apertus-tokenizer (content only, +8 per turn; the trainer dry-run gives the exact rendered count)", "blocks": [{"block": "math_en_gsm", "file": "data/math/en/gsm8k_dedup3.jsonl", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4516285, "tokens_effective": 4516285, "supervised_tokens_unique": 2808807, "supervised_tokens_effective": 2808807, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "file": "data/math/en/math_train_published.jsonl", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 35, "train_unique_rows": 7174, "train_rows_effective": 14348, "tokens_unique": 2209386, "tokens_effective": 4418772, "supervised_tokens_unique": 1562883, "supervised_tokens_effective": 3125766, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "file": "data/math/cut2/final/arm_M0.jsonl", "renderer": "ua", "copies": 1, "available": 14038, "taken": 14038, "dev_rows": 140, "train_unique_rows": 13898, "train_rows_effective": 13898, "tokens_unique": 3282117, "tokens_effective": 3282117, "supervised_tokens_unique": 1607762, "supervised_tokens_effective": 1607762, "content_sha256": "3924cd51b9cb3a566fb12e3c43d92d29a03701e08253b1cbc9517e82aa2a11bc"}], "decontamination_caches": {"english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl": {"rows": 28449, "sha256": "1fb6d83577ea62df8009a4bfd2d5e2f9cdd4c2ed39103f25867c8f46f8d24246"}, "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl": {"rows": 16632, "sha256": "52395e626d8ecd4ffe6219acd41df252987eb4a83da59cd01627b0be00b35411"}, "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl": {"rows": 1319, "sha256": "12d2145d474994b29bd487cfd2cd3a01a725e30cca4f0850da5df2a07f4b2d77"}, "ifbench_el.jsonl": {"rows": 586, "sha256": "607ae20febafc841db52accba26fcc6f05a81e3279174ec82a04c3023dad283f"}, "ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl": {"rows": 541, "sha256": "e0c1fda7f338da3d98bb178ec4a382935d0f4fced2c33816564e98759d567c21"}, "math200_confirm.jsonl": {"rows": 400, "sha256": "000148d2dc47429d8e1b923710d594228aa502e5c019f095b091c890cee4ea9f"}, "math500_el.jsonl": {"rows": 1000, "sha256": "e29827dc3b18f
    replay taken per parent config: {"dolci_chat": 301, "dolci_code_algo_20k": 503, "dolci_precise_if_20k": 307, "dolci_reasoning": 2717, "dolci_safety": 619, "dolci_science": 612, "dolci_tooluse": 2712, "greek_ours": 3957, "greek_rewrite": 198, "ifeval_like": 1792, "nemotron_chat_a": 2300, "nemotron_chat_b": 2325, "openmath_gsm": 0, "puzzles": 1103, "smoltalk2_multilingual": 2021}
--- M1: {"arm": "M1", "seed": 42, "parent": "data/arms/R2_stage1/train.jsonl", "replay_frac": 0.1, "tokenizer": "apertus-tokenizer (content only, +8 per turn; the trainer dry-run gives the exact rendered count)", "blocks": [{"block": "math_en_gsm", "file": "data/math/en/gsm8k_dedup3.jsonl", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4516285, "tokens_effective": 4516285, "supervised_tokens_unique": 2808807, "supervised_tokens_effective": 2808807, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "file": "data/math/en/math_train_published.jsonl", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 35, "train_unique_rows": 7174, "train_rows_effective": 14348, "tokens_unique": 2209386, "tokens_effective": 4418772, "supervised_tokens_unique": 1562883, "supervised_tokens_effective": 3125766, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "file": "data/math/cut2/final/arm_M1.jsonl", "renderer": "ua", "copies": 1, "available": 14038, "taken": 14038, "dev_rows": 140, "train_unique_rows": 13898, "train_rows_effective": 13898, "tokens_unique": 5055646, "tokens_effective": 5055646, "supervised_tokens_unique": 3381291, "supervised_tokens_effective": 3381291, "content_sha256": "ba49410e8dcdba12afb93c263e1c53453cbf9650ffe09e27f6d1bbf8d827eb1d"}], "decontamination_caches": {"english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl": {"rows": 28449, "sha256": "1fb6d83577ea62df8009a4bfd2d5e2f9cdd4c2ed39103f25867c8f46f8d24246"}, "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl": {"rows": 16632, "sha256": "52395e626d8ecd4ffe6219acd41df252987eb4a83da59cd01627b0be00b35411"}, "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl": {"rows": 1319, "sha256": "12d2145d474994b29bd487cfd2cd3a01a725e30cca4f0850da5df2a07f4b2d77"}, "ifbench_el.jsonl": {"rows": 586, "sha256": "607ae20febafc841db52accba26fcc6f05a81e3279174ec82a04c3023dad283f"}, "ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl": {"rows": 541, "sha256": "e0c1fda7f338da3d98bb178ec4a382935d0f4fced2c33816564e98759d567c21"}, "math200_confirm.jsonl": {"rows": 400, "sha256": "000148d2dc47429d8e1b923710d594228aa502e5c019f095b091c890cee4ea9f"}, "math500_el.jsonl": {"rows": 1000, "sha256": "e29827dc3b18f
    replay taken per parent config: {"dolci_chat": 301, "dolci_code_algo_20k": 503, "dolci_precise_if_20k": 307, "dolci_reasoning": 2717, "dolci_safety": 619, "dolci_science": 612, "dolci_tooluse": 2712, "greek_ours": 3957, "greek_rewrite": 198, "ifeval_like": 1792, "nemotron_chat_a": 2300, "nemotron_chat_b": 2325, "openmath_gsm": 0, "puzzles": 1103, "smoltalk2_multilingual": 2021}
--- M2: {"arm": "M2", "seed": 42, "parent": "data/arms/R2_stage1/train.jsonl", "replay_frac": 0.1, "tokenizer": "apertus-tokenizer (content only, +8 per turn; the trainer dry-run gives the exact rendered count)", "blocks": [{"block": "math_en_gsm", "file": "data/math/en/gsm8k_dedup3.jsonl", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4516285, "tokens_effective": 4516285, "supervised_tokens_unique": 2808807, "supervised_tokens_effective": 2808807, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "file": "data/math/en/math_train_published.jsonl", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 35, "train_unique_rows": 7174, "train_rows_effective": 14348, "tokens_unique": 2209386, "tokens_effective": 4418772, "supervised_tokens_unique": 1562883, "supervised_tokens_effective": 3125766, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "file": "data/math/cut2/final/arm_M2.jsonl", "renderer": "ua", "copies": 1, "available": 15414, "contaminated": 5, "taken": 15409, "dev_rows": 153, "train_unique_rows": 15256, "train_rows_effective": 15256, "tokens_unique": 6058272, "tokens_effective": 6058272, "supervised_tokens_unique": 4177164, "supervised_tokens_effective": 4177164, "content_sha256": "ee6c84cc93f8d3956f517f09e5cb5bb4d8469871918c5690b2e2e658ee675856"}], "decontamination_caches": {"english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl": {"rows": 28449, "sha256": "1fb6d83577ea62df8009a4bfd2d5e2f9cdd4c2ed39103f25867c8f46f8d24246"}, "greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl": {"rows": 16632, "sha256": "52395e626d8ecd4ffe6219acd41df252987eb4a83da59cd01627b0be00b35411"}, "gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl": {"rows": 1319, "sha256": "12d2145d474994b29bd487cfd2cd3a01a725e30cca4f0850da5df2a07f4b2d77"}, "ifbench_el.jsonl": {"rows": 586, "sha256": "607ae20febafc841db52accba26fcc6f05a81e3279174ec82a04c3023dad283f"}, "ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl": {"rows": 541, "sha256": "e0c1fda7f338da3d98bb178ec4a382935d0f4fced2c33816564e98759d567c21"}, "math200_confirm.jsonl": {"rows": 400, "sha256": "000148d2dc47429d8e1b923710d594228aa502e5c019f095b091c890cee4ea9f"}, "math500_el.jsonl": {"rows": 1000, "sha2
    replay taken per parent config: {"dolci_chat": 301, "dolci_code_algo_20k": 503, "dolci_precise_if_20k": 307, "dolci_reasoning": 2717, "dolci_safety": 619, "dolci_science": 612, "dolci_tooluse": 2712, "greek_ours": 3957, "greek_rewrite": 198, "ifeval_like": 1792, "nemotron_chat_a": 2300, "nemotron_chat_b": 2325, "openmath_gsm": 0, "puzzles": 1103, "smoltalk2_multilingual": 2021}

=== results/pilots/check_arms.log (tail) ===
caches: english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl:28449:1fb6d835, greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl:16632:52395e62, gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl:1319:12d2145d, ifbench_el.jsonl:586:607ae20f, ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl:541:e0c1fda7, math200_confirm.jsonl:400:000148d2, math500_el.jsonl:1000:e29827dc, mgsm_el.jsonl:250:b96a9dd2, multichallenge_el.jsonl:3308:72468f1e, native_asep_mcqa.jsonl:2346:f8230d12, native_demosqa.jsonl:600:3d769837, native_gpcr.jsonl:208:ae256518, native_medical_mcqa.jsonl:432:ae4f9346, xstest_el.jsonl:900:b3a910ef
M0: 71717 train rows, 28.5M tokens (18.4M supervised), ≈436 updates, greek train 13898 / dev 140, blocks {'greek_math': 13898, 'math_en_math': 14348, 'math_en_gsm': 22004, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
M1: 71717 train rows, 30.3M tokens (20.1M supervised), ≈463 updates, greek train 13898 / dev 140, blocks {'greek_math': 13898, 'math_en_math': 14348, 'math_en_gsm': 22004, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
M2: 73075 train rows, 31.3M tokens (20.9M supervised), ≈478 updates, greek train 15256 / dev 153, blocks {'math_en_gsm': 22004, 'greek_math': 15256, 'math_en_math': 14348, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
OK: M0 and M1 carry the same 13898 Greek maths prompts (multiset)
OK: M0/M1 Greek ids are exactly paired
OK: M2 = M1 + 1358 Level-5 rows
OK: replay identical multisets across arms (21467 rows)
OK: math_en_gsm identical multisets across arms (22004 rows)
OK: math_en_math identical multisets across arms (14348 rows)
OK: Greek dev sets paired (140 problems)
OK: no English training row shares a problem with the 102 dev problems
RESULT PASS


=== results/pilots/dryrun_M0.log: MISSING at brief time ===

=== results/pilots/dryrun_M1.log: MISSING at brief time ===

=== results/pilots/dryrun_M2.log: MISSING at brief time ===

=== data/math/cut2/out/run.log (tail) ===
 the venv): waits for fidelity_all (pid 91791) and Level-4 HIGH (pid 91792); then stragglers at high (32) -> fidelity ADJUDICATION at high (64) -> validate (64) -> repair_high (32) -> validate -> polish (48) -> assemble; second pass after Level-5
[09-14 12:02] CHAIN v6 queued: waits for fidelity_all (pid 91791) and Level-4 HIGH (pid 91792); then stragglers(high,32) -> audit(64) -> adjudicate(64) -> polish(64) -> validate(64) -> repair(32) -> polish -> validate -> assemble(strict); second pass after Level-5; fail-closed
[09-14 12:25] level5 solutions HIGH exit 0: 2026-09-14 12:25 cut2 level5 solutions HIGH: n=1487 codex None -> 31.0 (delta None)
[09-14 13:16] fidelity_all + Level-4 HIGH ended: 11192 fidelity rows, 1289 L4 rows
[09-14 13:19] solutions_resume exit 0: 2026-09-14 13:19 cut2 solutions: n=107 codex 38.0 -> 38.0 (delta 0.0)
[09-14 13:21] fidelity_audit exit 0: audit of medium passes: frozen sample 300, flagged at high 5 (missed-defect rate under the strict rule 1.7%; adjudication under the mathemat
[09-14 13:28] fidelity_adjudicate exit 0: 2026-09-14 13:28 cut2 fidelity adjudication HIGH: n=724 codex 38.0 -> 38.0 (delta 0.0)
[09-14 15:30] polish exit 0: Counter({'unchanged': 8173, 'edited': 3289, 'reverted': 17, 'failed': 4})
[09-14 17:32] validate exit 0: 2026-09-14 17:32 cut2 validate: n=11479 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:36] repair_high exit 0: 2026-09-14 17:36 cut2 repair HIGH: n=215 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:39] polish_r exit 0: Counter({'unchanged': 125, 'edited': 90})
[09-14 17:42] validate_r exit 0: 2026-09-14 17:42 cut2 validate: n=215 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:42] assemble pass 1 (Level 5 may still be pending): {'rows_M0': 8805, 'rows_M1': 8805, 'rows_M2_extra': 1266, 'rows_native': 5108, 'arm_M0': 13913, 'arm_M1': 13913, 'arm_M2': 15179}
[09-14 17:42] Level-5 HIGH complete: 1493 rows
[09-14 17:42] polish2 exit 0: Counter()
[09-14 17:42] validate2 exit 0: 2026-09-14 17:42 cut2 validate: n=0 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:42] repair_high2 exit 0: 2026-09-14 17:42 cut2 repair HIGH: n=0 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:42] polish3 exit 0: Counter()
[09-14 17:42] validate3 exit 0: 2026-09-14 17:42 cut2 validate: n=0 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:42] assemble_final exit 2: EXPORT REFUSED: incomplete stages {"translated_gsm8k:no_cut1_pair": 96, "translated_gsm8k:unpolished": 3, "translated_math:no_cut1_pair": 62
[09-14 17:42] CUT2_CHAIN_FAILED at assemble_final
[09-14 17:42] FINISH: retry failed polish -> validate new texts -> strict assembly
[09-14 17:44] polish4 exit 0: Counter({'failed': 2, 'edited': 1, 'unchanged': 1})
[09-14 17:44] validate4 exit 0: 2026-09-14 17:44 cut2 validate: n=2 codex 38.0 -> 38.0 (delta 0.0)
[09-14 17:44] assemble_final exit 2: EXPORT REFUSED: incomplete stages {"translated_math5:fidelity_unchecked": 3}
[09-14 17:44] CUT2_CHAIN_FAILED at assemble_final
[09-14 17:46] CUT2_CHAIN_DONE (strict assembly succeeded after the fidelity resume)


=== CONFIG (cluster/configs/M1.yaml; M0/M2 identical except names/paths) ===
run_name: M1_lr1e-5_1ep_cos
arm: M1
model_name_or_path: /iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1
tokenizer_name_or_path: fffoivos/apertus-8b-greek-cpt
revision: 18-avg-uniform5-tokens30B-50B
template_source: swiss-ai/Apertus-8B-Instruct-2509
train_file: data/arms/M1/train.jsonl
eval_file: data/arms/M1/dev.jsonl
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

save_steps: 200
save_total_limit: 2

=== DECISION RULE + READOUT: plan §4 tables; data/pilot_summary.py (paired one-sided 90% bootstrap, guardrails IFEval/MGSM −2 pp, loops M0+5) ===


=== ARM SIZES (final manifests, exact tokenizer) ===
1-G4F6P0--00 (M0): 71,717 rows, 28.5M tokens (18.4M supervised), ≈436 updates; --01 (M1): 71,717 rows, 30.3M (20.1M), ≈463; --02 (M2): 73,075 rows, 31.3M (20.9M), ≈478. Replay (10% of every non-maths stage-1 config) = 21,467 rows ≈ 19M tokens ≈ 65% of each arm's tokens (both fractions reported per plan §4). English maths = 22,004 GSM8K + 14,348 MATH rows in every arm.

=== 60-ROW SAMPLE: worked targets (M1) with the paired terse+boxed target (M0) for the same problem; then 20 Level-5 targets (M2 extra) ===

--- c2_gsm_2139 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Η εταιρεία Facebook αποφάσισε να δώσει επίδομα παραγωγικότητας σε όλες τις εργαζόμενές της που είναι μητέρες. Το συνολικό ποσό του επιδόματος αντιστοιχεί στο 25% των ετήσιων κερδών της Facebook, τα οποία το 2020 ήταν 5.000.000 €. Είναι γνωστό ότι η Facebook απασχολεί 3.300 εργαζομένους. Το ένα τρίτο είναι άνδρες, ενώ από τις γυναίκες οι 1.200 δεν είναι μητέρες. Πόσο ήταν το επίδομα που έλαβε καθεμία από τις εργαζόμενες μητέρες, αν όλες έλαβαν το ίδιο ποσό;
M1 (worked): Το συνολικό ποσό που θα μοιραστεί στις εργαζόμενες μητέρες ισούται με το 25% των ετήσιων κερδών της Facebook. Επομένως:

\[
\frac{25}{100}\cdot 5.000.000=1.250.000\text{ €}.
\]

Από τους 3.300 εργαζομένους, το ένα τρίτο είναι άνδρες. Άρα ο αριθμός των ανδρών είναι:

\[
3.300\cdot\frac{1}{3}=1.100.
\]

Επομένως, οι γυναίκες που εργάζονται στην εταιρεία είναι:

\[
3.300-1.100=2.200.
\]

Γνωρίζουμε ότι από τις 2.200 εργαζόμενες γυναίκες οι 1.200 δεν είναι μητέρες. Συνεπώς, ο αριθμός των εργαζόμενων μητέρων είναι:

\[
2.200-1.200=1.000.
\]

Το συνολικό επίδομα των 1.250.000 € μοιράστηκε εξίσου στις 1.000 μητέρες. Άρα καθεμία έλαβε:

\[
\frac{1.250.000}{1.000}=1.250\text{ €}.
\]

Επομένως, το επίδομα που έλαβε καθεμία από τις εργαζόμενες μητέρες ήταν 1.250 €.

\[
\boxed{1250}
\]
M0 (terse+boxed): Συνολικό ποσό επιδόματος:
25% · 5.000.000 = 1.250.000 €
Άνδρες εργαζόμενοι:
3.300 : 3 = 1.100 άτομα
Γυναίκες εργαζόμενες:
3.300 − 1.100 = 2.200 άτομα
Εργαζόμενες μητέρες:
2.200 − 1.200 = 1.000 άτομα
Επίδομα ανά εργαζόμενη μητέρα:
1.250.000 : 1.000 = 1.250 €
Απάντηση: 1.250 €
\boxed{1250}

--- c2_gsm_1043 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Η Γιάννα πονάει στην κοιλιά. Ο αδελφός της, ο Μιχάλης, λέει ότι αυτό συμβαίνει επειδή η Γιάννα έφαγε 5 περισσότερα κομμάτια σοκολάτας από το τριπλάσιο του αριθμού των κομματιών που έφαγε εκείνος. Αν ο Μιχάλης έφαγε 20 κομμάτια σοκολάτας, πόσα έφαγε η Γιάννα;
M1 (worked): Ο Μιχάλης έφαγε 20 κομμάτια σοκολάτας.

Αρχικά, υπολογίζουμε το τριπλάσιο του αριθμού των κομματιών που έφαγε ο Μιχάλης:

\[
20 \cdot 3 = 60
\]

Άρα, το τριπλάσιο των κομματιών που έφαγε ο Μιχάλης είναι 60 κομμάτια σοκολάτας.

Η Γιάννα έφαγε 5 περισσότερα κομμάτια από αυτόν τον αριθμό. Επομένως, προσθέτουμε 5 στα 60:

\[
60 + 5 = 65
\]

Συνεπώς, η Γιάννα έφαγε συνολικά 65 κομμάτια σοκολάτας.

\[
\boxed{65}
\]
M0 (terse+boxed): Ο Μιχάλης έφαγε 20 κομμάτια σοκολάτας.
Το τριπλάσιο είναι:
20 · 3 = 60 κομμάτια
Η Γιάννα έφαγε 5 κομμάτια περισσότερα.
60 + 5 = 65 κομμάτια
Απάντηση: 65 κομμάτια σοκολάτας
\boxed{65}

--- c2_gsm_4373 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ο Νίκος έφτιαξε 12 τούρτες για τα γενέθλια της αδελφής του. Ο Δημήτρης έφτιαξε επίσης 4 τούρτες, αλλά έφαγε 1 περιμένοντας να αρχίσει το πάρτι. Πόσες τούρτες έμειναν;
M1 (worked): Αρχικά υπολογίζουμε πόσες τούρτες έφτιαξαν συνολικά ο Νίκος και ο Δημήτρης.

Ο Νίκος έφτιαξε 12 τούρτες και ο Δημήτρης έφτιαξε άλλες 4. Επομένως, πριν φάει κάποιος κάποια τούρτα, υπήρχαν:

\[
12+4=16
\]

Άρα, οι δύο τους έφτιαξαν συνολικά 16 τούρτες.

Στη συνέχεια, ο Δημήτρης έφαγε 1 τούρτα όσο περίμενε να αρχίσει το πάρτι. Για να βρούμε πόσες τούρτες έμειναν, αφαιρούμε τη 1 τούρτα από τις 16 συνολικές τούρτες:

\[
16-1=15
\]

Επομένως, αφού ο Δημήτρης έφαγε την τούρτα, για το πάρτι έμειναν 15 τούρτες.

Η τελική απάντηση είναι:

\[
\boxed{15}
\]
M0 (terse+boxed): Συνολικά έφτιαξαν:
12 + 4 = 16 τούρτες
Ο Δημήτρης έφαγε 1 τούρτα:
16 − 1 = 15 τούρτες
Απάντηση: 15 τούρτες
\boxed{15}

--- c2_gsm_2046 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ένας υπάλληλος μπορεί να επεξεργάζεται 25 έντυπα την ώρα. Αν πρέπει να επεξεργαστούν 2.400 έντυπα μέσα σε μία εργάσιμη ημέρα 8 ωρών, πόσους υπαλλήλους πρέπει να προσλάβεις για εκείνη την ημέρα;
M1 (worked): Ένας υπάλληλος επεξεργάζεται 25 έντυπα κάθε ώρα και η εργάσιμη ημέρα διαρκεί 8 ώρες.

Άρα, μέσα σε μία εργάσιμη ημέρα, ένας υπάλληλος μπορεί να επεξεργαστεί:

\[
25 \times 8 = 200
\]

Δηλαδή, κάθε υπάλληλος επεξεργάζεται συνολικά 200 έντυπα την ημέρα.

Πρέπει να επεξεργαστούν συνολικά 2.400 έντυπα. Για να βρούμε πόσοι υπάλληλοι χρειάζονται, διαιρούμε το συνολικό πλήθος των εντύπων με το πλήθος των εντύπων που επεξεργάζεται ένας υπάλληλος σε μία ημέρα:

\[
\frac{2.400}{200} = 12
\]

Επομένως, για να επεξεργαστούν και τα 2.400 έντυπα μέσα στην εργάσιμη ημέρα των 8 ωρών, πρέπει να προσληφθούν συνολικά 12 υπάλληλοι για εκείνη την ημέρα.

\[
\boxed{12}
\]
M0 (terse+boxed): Κάθε υπάλληλος επεξεργάζεται σε 8 ώρες:
25 · 8 = 200 έντυπα
Ο αριθμός των υπαλλήλων είναι:
2.400 : 200 = 12 υπάλληλοι
Απάντηση: 12 υπάλληλοι
\boxed{12}

--- c2_math_2966 [translated_math, level Level 3, validity none, polished unchanged]
PROBLEM: Η περίμετρος ενός ορθογωνίου είναι 24 ίντσες. Πόσες τετραγωνικές ίντσες είναι το μέγιστο δυνατό εμβαδόν αυτού του ορθογωνίου;
M1 (worked): Έστω ότι η μία πλευρά του ορθογωνίου έχει μήκος $x$ ίντσες. Εφόσον η περίμετρος είναι $24$ ίντσες, το άθροισμα του μήκους και του πλάτους είναι

$$2(\text{μήκος}+\text{πλάτος})=24,$$

άρα

$$\text{μήκος}+\text{πλάτος}=12.$$

Επομένως, η άλλη πλευρά έχει μήκος $12-x$ ίντσες. Πράγματι, η περίμετρος είναι

$$x+x+(12-x)+(12-x)=24.$$

Το εμβαδόν του ορθογωνίου είναι

$$E=x(12-x)=12x-x^2.$$

Για να βρούμε τη μέγιστη τιμή του, συμπληρώνουμε το τετράγωνο:

$$E=-(x^2-12x)=-(x^2-12x+36)+36,$$

οπότε

$$E=-(x-6)^2+36.$$

Επειδή

$$(x-6)^2\ge 0,$$

έχουμε

$$-(x-6)^2\le 0,$$

και συνεπώς

$$E\le 36.$$

Η ισότητα ισχύει όταν $x=6$, οπότε και η άλλη πλευρά είναι $12-6=6$ ίντσες. Άρα το ορθογώνιο μέγιστου εμβαδού είναι τετράγωνο πλευράς $6$ ιντσών και το μέγιστο δυνατό εμβαδόν είναι

$$\boxed{36}$$
M0 (terse+boxed): Έστω α το μήκος και β το πλάτος.
2 · (α + β) = 24
α + β = 12
Για σταθερό άθροισμα, το γινόμενο μεγιστοποιείται όταν οι αριθμοί είναι ίσοι.
α = β = 6
Ε = 6 · 6
Ε = 36 τετραγωνικές ίντσες
Απάντηση: 36 τετραγωνικές ίντσες
\boxed{36}

--- c2_math_2098 [translated_math, level Level 1, validity none, polished unchanged]
PROBLEM: Να υπολογίσεις το $|7-24i|$.
M1 (worked): Για έναν μιγαδικό αριθμό της μορφής $z=a+bi$, το μέτρο του υπολογίζεται από τον τύπο

$$|z|=\sqrt{a^2+b^2}.$$

Στον μιγαδικό αριθμό $7-24i$ έχουμε πραγματικό μέρος $a=7$ και συντελεστή του φανταστικού μέρους $b=-24$. Επομένως,

$$|7-24i|=\sqrt{7^2+(-24)^2}.$$

Υπολογίζουμε ξεχωριστά τα τετράγωνα:

$$7^2=49$$

και

$$(-24)^2=576.$$

Άρα,

$$|7-24i|=\sqrt{49+576}=\sqrt{625}.$$

Επειδή $25^2=625$ και το μέτρο ενός μιγαδικού αριθμού είναι πάντα μη αρνητικό, προκύπτει ότι

$$|7-24i|=25.$$

Επομένως, η τελική απάντηση είναι

$$\boxed{25}$$
M0 (terse+boxed): |7 - 24i| = √(7² + (-24)²)
|7 - 24i| = √(49 + 576)
|7 - 24i| = √625
|7 - 24i| = 25
Απάντηση: 25
\boxed{25}

--- c2_math_2469 [translated_math, level Level 4, validity none, polished edited]
PROBLEM: Να βρεις τη μικρότερη λύση της εξίσωσης
\[\frac{2x}{x-2}+\frac{2x^2-24}{x}=11.\]
M1 (worked): Αρχικά εξετάζουμε τους περιορισμούς της εξίσωσης. Οι παρονομαστές δεν πρέπει να μηδενίζονται, άρα
\[
x\neq 0 \quad \text{και} \quad x\neq 2.
\]

Πολλαπλασιάζουμε και τα δύο μέλη με τον κοινό παρονομαστή $x(x-2)$:
\[
x(x-2)\left(\frac{2x}{x-2}+\frac{2x^2-24}{x}\right)=11x(x-2).
\]

Απλοποιώντας κάθε όρο, παίρνουμε
\[
2x^2+(2x^2-24)(x-2)=11x(x-2).
\]

Αναπτύσσουμε τα γινόμενα:
\[
(2x^2-24)(x-2)=2x^3-4x^2-24x+48
\]
και
\[
11x(x-2)=11x^2-22x.
\]

Επομένως,
\[
2x^2+2x^3-4x^2-24x+48=11x^2-22x.
\]

Συγκεντρώνουμε όλους τους όρους στο αριστερό μέλος:
\[
2x^3-2x^2-24x+48-11x^2+22x=0,
\]
άρα
\[
2x^3-13x^2-2x+48=0.
\]

Αναζητούμε ρητές ρίζες. Για $x=6$ έχουμε
\[
2(6)^3-13(6)^2-2(6)+48
=432-468-12+48=0,
\]
οπότε το $x-6$ είναι παράγοντας του πολυωνύμου. Η παραγοντοποίηση είναι
\[
2x^3-13x^2-2x+48=(x-6)(2x^2-x-8).
\]

Άρα
\[
(x-6)(2x^2-x-8)=0,
\]
οπότε είτε
\[
x=6
\]
είτε
\[
2x^2-x-8=0.
\]

Για τη δεύτερη εξίσωση, η διακρίνουσα είναι
\[
\Delta=(-1)^2-4\cdot2\cdot(-8)=1+64=65.
\]

Επομένως,
\[
x=\frac{-(-1)\pm\sqrt{65}}{2\cdot2}
=\frac{1\pm\sqrt{65}}{4}.
\]

Καμία από τις τρεις λύσεις δεν παραβιάζ
M0 (terse+boxed): Πρέπει να ισχύει x ≠ 0 και x ≠ 2.
2x/(x − 2) + (2x² − 24)/x = 11
2x² + (2x² − 24)(x − 2) = 11x(x − 2)
2x³ − 13x² − 2x + 48 = 0
(x − 6)(2x² − x − 8) = 0
x = 6
2x² − x − 8 = 0
x = (1 ± √65)/4
Η μικρότερη επιτρεπτή λύση είναι (1 − √65)/4.
Απάντηση: (1 − √65)/4
\boxed{\frac{1-\sqrt{65}}{4}}

--- c2_math_631 [translated_math, level Level 3, validity none, polished unchanged]
PROBLEM: Έστω ότι $p$ και $q$ είναι οι δύο διαφορετικές λύσεις της εξίσωσης
$$(x-3)(x+3)=21x-63.$$
Αν $p>q$, ποια είναι η τιμή της παράστασης $p-q$;
M1 (worked): Παραγοντοποιούμε πρώτα το δεξί μέλος της εξίσωσης:

\[
21x-63=21(x-3).
\]

Επομένως, η αρχική εξίσωση γράφεται:

\[
(x-3)(x+3)=21(x-3).
\]

Μεταφέρουμε όλα τα μέλη στο αριστερό μέρος:

\[
(x-3)(x+3)-21(x-3)=0.
\]

Παρατηρούμε ότι ο παράγοντας \((x-3)\) είναι κοινός. Τον βγάζουμε κοινό παράγοντα:

\[
(x-3)\big[(x+3)-21\big]=0.
\]

Απλοποιούμε την παράσταση μέσα στην αγκύλη:

\[
(x+3)-21=x-18.
\]

Άρα:

\[
(x-3)(x-18)=0.
\]

Για να είναι το γινόμενο ίσο με μηδέν, πρέπει ένας από τους δύο παράγοντες να είναι μηδέν:

\[
x-3=0 \Rightarrow x=3
\]

ή

\[
x-18=0 \Rightarrow x=18.
\]

Οι δύο διαφορετικές λύσεις είναι επομένως \(3\) και \(18\). Εφόσον \(p>q\), έχουμε \(p=18\) και \(q=3\). Συνεπώς:

\[
p-q=18-3=\boxed{15}.
\]
M0 (terse+boxed): (x-3)(x+3)=21x-63
x²-9=21x-63
x²-21x+54=0
(x-18)(x-3)=0
p=18
q=3
p-q=18-3
p-q=15
Απάντηση: 15
\boxed{15}

--- c2_gsm_3582 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Πριν από δύο ημέρες, η θερμοκρασία το πρωί ανέβαινε κατά 1,5 βαθμό κάθε 2 ώρες. Αν η θερμοκρασία ήταν 50 βαθμοί στις 3 π.μ., ποια ήταν η θερμοκρασία στις 11 π.μ.;
M1 (worked): Από τις 3 π.μ. έως τις 11 π.μ. περνούν συνολικά:

\[
11-3=8 \text{ ώρες}
\]

Η θερμοκρασία ανεβαίνει κατά \(1{,}5\) βαθμό κάθε 2 ώρες. Επομένως, υπολογίζουμε τη θερμοκρασία ανά δίωρο.

Στις 5 π.μ. η θερμοκρασία ήταν:

\[
50+1{,}5=51{,}5 \text{ βαθμοί}
\]

Στις 7 π.μ. ήταν:

\[
51{,}5+1{,}5=53 \text{ βαθμοί}
\]

Στις 9 π.μ. ήταν:

\[
53+1{,}5=54{,}5 \text{ βαθμοί}
\]

Τέλος, στις 11 π.μ. η θερμοκρασία ήταν:

\[
54{,}5+1{,}5=56 \text{ βαθμοί}
\]

Άρα, η θερμοκρασία στις 11 π.μ. ήταν \(56\) βαθμοί.

\[
\boxed{56}
\]
M0 (terse+boxed): Από τις 3 π.μ. έως τις 11 π.μ. περνούν:
11 − 3 = 8 ώρες
Τα διαστήματα των 2 ωρών είναι:
8 : 2 = 4
Η συνολική αύξηση είναι:
4 · 1,5 = 6 βαθμοί
Η θερμοκρασία στις 11 π.μ. ήταν:
50 + 6 = 56 βαθμοί
Απάντηση: 56 βαθμοί
\boxed{56}

--- c2_gsm_1594 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ο Γιάννης πουλάει 20 ξυλόγλυπτα με πυρογραφία προς 15 € το καθένα. Το ξύλο κόστισε 100 €. Πόσο κέρδος βγάζει;
M1 (worked): Ο Γιάννης πουλάει συνολικά 20 ξυλόγλυπτα και εισπράττει 15 € από το καθένα.

Αρχικά υπολογίζουμε τα συνολικά έσοδα από τις πωλήσεις:

\[
20 \cdot 15\,€ = 300\,€
\]

Επομένως, από την πώληση όλων των ξυλόγλυπτων εισπράττει συνολικά 300 €.

Για να βρούμε το κέρδος, πρέπει να αφαιρέσουμε από τα συνολικά έσοδα το κόστος του ξύλου, το οποίο ήταν 100 €:

\[
300\,€ - 100\,€ = 200\,€
\]

Άρα, αφού αφαιρεθεί το κόστος του ξύλου από τα χρήματα που εισέπραξε, ο Γιάννης βγάζει κέρδος 200 €.

\[
\boxed{200}
\]
M0 (terse+boxed): 20 · 15 = 300 €
300 − 100 = 200 €
Απάντηση: 200 €
\boxed{200}

--- c2_math_2841 [translated_math, level Level 4, validity none, polished edited]
PROBLEM: Όταν ο διψήφιος ακέραιος $MM$, του οποίου τα ψηφία είναι ίδια, πολλαπλασιάζεται με τον μονοψήφιο ακέραιο $M$, το αποτέλεσμα είναι ο τριψήφιος ακέραιος $NPM$. Ποια είναι η μεγαλύτερη δυνατή τιμή του $NPM$;
M1 (worked): Ο διψήφιος αριθμός με τα ίδια ψηφία είναι
\[
MM=10M+M=11M.
\]
Εφόσον το γινόμενο είναι ο αριθμός $NPM$, το τελευταίο ψηφίο του γινομένου πρέπει να είναι $M$. Άρα το τελευταίο ψηφίο του $M\cdot M=M^2$ πρέπει επίσης να είναι $M$. Επομένως
\[
M^2\equiv M\pmod{10}.
\]
Ισοδύναμα,
\[
M^2-M\equiv0\pmod{10}
\]
και
\[
M(M-1)\equiv0\pmod{10}.
\]
Εξετάζοντας τα ψηφία $1,2,\ldots,9$, βρίσκουμε ότι μόνο τα $M=1$, $M=5$ και $M=6$ έχουν την απαιτούμενη ιδιότητα:
\[
1^2=1,
\]
\[
5^2=25,
\]
\[
6^2=36.
\]
Πράγματι, σε κάθε περίπτωση το τελευταίο ψηφίο του $M^2$ είναι $M$.

Υπολογίζουμε τώρα τα αντίστοιχα γινόμενα:
\[
11\cdot1=11,
\]
το οποίο δεν είναι τριψήφιο,
\[
55\cdot5=275,
\]
και
\[
66\cdot6=396.
\]
Από τα δυνατά τριψήφια αποτελέσματα, το μεγαλύτερο είναι το $396$. Επίσης έχει πράγματι τη μορφή $NPM$, αφού για $M=6$ έχουμε $N=3$ και $P=9$.

Άρα η μεγαλύτερη δυνατή τιμή του $NPM$ είναι
\[
\boxed{396}
\]
M0 (terse+boxed): Για M ≤ 3, το γινόμενο δεν είναι τριψήφιο.
44 · 4 = 176
55 · 5 = 275
66 · 6 = 396
77 · 7 = 539
88 · 8 = 704
99 · 9 = 891
Μόνο τα 275 και 396 τελειώνουν στο ψηφίο M.
Η μεγαλύτερη έγκυρη τιμή είναι το 396.
Απάντηση: 396
\boxed{396}

--- c2_gsm_494 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Η Γεωργία χρειάζεται 3 αβοκάντο για να φτιάξει μία δόση γουακαμόλε με τη συνταγή της γιαγιάς της. Αν είχε ήδη 5 αβοκάντο και η αδελφή της αγοράσει άλλα 4, πόσες δόσεις γουακαμόλε μπορεί να φτιάξει η Γεωργία;
M1 (worked): Αρχικά, βρίσκουμε πόσα αβοκάντο έχει συνολικά η Γεωργία. Είχε ήδη 5 αβοκάντο και η αδελφή της αγόρασε άλλα 4, επομένως προσθέτουμε:

\[
5+4=9
\]

Άρα, η Γεωργία έχει συνολικά 9 αβοκάντο.

Για να φτιάξει μία δόση γουακαμόλε, χρειάζεται 3 αβοκάντο. Επομένως, για να υπολογίσουμε πόσες δόσεις μπορεί να φτιάξει με τα 9 αβοκάντο, διαιρούμε το συνολικό πλήθος των αβοκάντο με τα αβοκάντο που απαιτούνται για κάθε δόση:

\[
9\div 3=3
\]

Άρα, τα 9 αβοκάντο αρκούν ακριβώς για 3 δόσεις γουακαμόλε, χωρίς να περισσέψει κανένα αβοκάντο.

Η Γεωργία μπορεί να φτιάξει συνολικά:

\[
\boxed{3}
\]
M0 (terse+boxed): Τα αβοκάντο που έχει συνολικά είναι:
5 + 4 = 9 αβοκάντο
Οι δόσεις που μπορεί να φτιάξει είναι:
9 ÷ 3 = 3 δόσεις
Απάντηση: 3 δόσεις
\boxed{3}

--- c2_math_781 [translated_math, level Level 3, validity none, polished unchanged]
PROBLEM: Να βρεις τον μέγιστο κοινό διαιρέτη των $10.293$ και $29.384$.
M1 (worked): Χρησιμοποιούμε τον αλγόριθμο του Ευκλείδη. Σε κάθε βήμα αντικαθιστούμε τον μεγαλύτερο αριθμό με το υπόλοιπο της διαίρεσής του με τον μικρότερο:

\begin{align*}
\operatorname{ΜΚΔ}(10.293,29.384)
&=\operatorname{ΜΚΔ}(29.384-2\cdot10.293,10.293)\\
&=\operatorname{ΜΚΔ}(8.798,10.293)\\
&=\operatorname{ΜΚΔ}(8.798,10.293-8.798)\\
&=\operatorname{ΜΚΔ}(8.798,1.495)\\
&=\operatorname{ΜΚΔ}(8.798-5\cdot1.495,1.495)\\
&=\operatorname{ΜΚΔ}(1.323,1.495)\\
&=\operatorname{ΜΚΔ}(1.323,1.495-1.323)\\
&=\operatorname{ΜΚΔ}(1.323,172)\\
&=\operatorname{ΜΚΔ}(1.323-7\cdot172,172)\\
&=\operatorname{ΜΚΔ}(119,172)\\
&=\operatorname{ΜΚΔ}(119,172-119)\\
&=\operatorname{ΜΚΔ}(119,53)\\
&=\operatorname{ΜΚΔ}(119-2\cdot53,53)\\
&=\operatorname{ΜΚΔ}(13,53).
\end{align*}

Τέλος, διαιρούμε το $53$ με το $13$:

\[
53=4\cdot13+1.
\]

Άρα

\[
\operatorname{ΜΚΔ}(13,53)=\operatorname{ΜΚΔ}(13,1)=1.
\]

Επομένως, ο μέγιστος κοινός διαιρέτης των $10.293$ και $29.384$ είναι

\[
\boxed{1}
\]
M0 (terse+boxed): Εφαρμόζουμε τον αλγόριθμο του Ευκλείδη.
29.384 = 2 · 10.293 + 8.798
10.293 = 1 · 8.798 + 1.495
8.798 = 5 · 1.495 + 1.323
1.495 = 1 · 1.323 + 172
1.323 = 7 · 172 + 119
172 = 1 · 119 + 53
119 = 2 · 53 + 13
53 = 4 · 13 + 1
13 = 13 · 1 + 0
Ο τελευταίος μη μηδενικός υπόλοιπος είναι το 1.
Απάντηση: 1
\boxed{1}

--- c2_math_1662 [translated_math, level Level 3, validity none, polished unchanged]
PROBLEM: Έστω ότι $3\triangle_4=\triangle2_{11}$, όπου το $\triangle$ παριστάνει ένα ψηφίο από το 0 έως το 9. Ποια είναι η τιμή του ψηφίου που λείπει;
M1 (worked): Μετατρέπουμε τους δύο αριθμούς στο δεκαδικό σύστημα, χρησιμοποιώντας την αξία θέσης κάθε ψηφίου.

Ο αριθμός $3\triangle_4$ είναι γραμμένος στη βάση $4$, άρα:
\[
3\triangle_4=3\cdot4^1+\triangle\cdot4^0=3\cdot4+\triangle\cdot1=12+\triangle.
\]

Αντίστοιχα, ο αριθμός $\triangle2_{11}$ είναι γραμμένος στη βάση $11$, επομένως:
\[
\triangle2_{11}=\triangle\cdot11^1+2\cdot11^0=11\cdot\triangle+2.
\]

Αφού οι δύο αριθμοί είναι ίσοι, εξισώνουμε τις δεκαδικές τους τιμές:
\begin{align*}
12+\triangle&=11\cdot\triangle+2\\
12-2&=11\cdot\triangle-\triangle\\
10&=10\cdot\triangle\\
\triangle&=\frac{10}{10}\\
\triangle&=1.
\end{align*}

Το $1$ είναι πράγματι επιτρεπτό ψηφίο και στις δύο βάσεις. Επομένως, η τιμή του ψηφίου που λείπει είναι
\[
\boxed{1}
\]
M0 (terse+boxed): Η ισότητα είναι 3△₄ = △2₁₁.
3△₄ = 3·4 + △
△2₁₁ = 11·△ + 2
12 + △ = 11·△ + 2
10 = 10·△
△ = 1
Απάντηση: 1
\boxed{1}

--- c2_gsm_54 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Στο φυτώριο «Ο Πράσινος Κήπος» υπάρχουν 1.491 κόκκινα τριαντάφυλλα, 3.025 κίτρινα γαρίφαλα και 1.768 λευκά τριαντάφυλλα. Πόσα λουλούδια υπάρχουν συνολικά στο φυτώριο;
M1 (worked): Για να βρούμε πόσα λουλούδια υπάρχουν συνολικά στο φυτώριο, προσθέτουμε τα λουλούδια και των τριών κατηγοριών.

Αρχικά, προσθέτουμε τα 1.491 κόκκινα τριαντάφυλλα και τα 3.025 κίτρινα γαρίφαλα:

\[
1.491+3.025=4.516
\]

Άρα, τα κόκκινα τριαντάφυλλα και τα κίτρινα γαρίφαλα είναι συνολικά 4.516.

Στη συνέχεια, προσθέτουμε σε αυτό το αποτέλεσμα τα 1.768 λευκά τριαντάφυλλα:

\[
4.516+1.768=6.284
\]

Επομένως, αν αθροίσουμε τα 1.491 κόκκινα τριαντάφυλλα, τα 3.025 κίτρινα γαρίφαλα και τα 1.768 λευκά τριαντάφυλλα, βρίσκουμε:

\[
1.491+3.025+1.768=6.284
\]

Συνεπώς, στο φυτώριο «Ο Πράσινος Κήπος» υπάρχουν συνολικά 6.284 λουλούδια.

\[
\boxed{6284}
\]
M0 (terse+boxed): 1.491 + 3.025 = 4.516 λουλούδια
4.516 + 1.768 = 6.284 λουλούδια
Απάντηση: 6.284 λουλούδια
\boxed{6284}

--- c2_math_1979 [translated_math, level Level 2, validity none, polished edited]
PROBLEM: Πενήντα μπαλάκια επιτραπέζιας αντισφαίρισης είναι αριθμημένα με τους αριθμούς $1, 2, 3, \ldots, 49, 50$. Επιλέγεται τυχαία ένα μπαλάκι. Ποια είναι η πιθανότητα ο αριθμός του επιλεγμένου μπαλακίου να είναι πολλαπλάσιο του 5 ή του 7 ή και των δύο; Να γράψετε την απάντησή σας ως κοινό κλάσμα.
M1 (worked): Τα 50 μπαλάκια έχουν την ίδια πιθανότητα να επιλεγούν, οπότε υπολογίζουμε πόσοι αριθμοί από το 1 έως το 50 είναι πολλαπλάσια του 5 ή του 7.

Τα πολλαπλάσια του 5 είναι
\[
5,10,15,20,25,30,35,40,45,50,
\]
άρα είναι
\[
\frac{50}{5}=10.
\]

Τα πολλαπλάσια του 7 είναι
\[
7,14,21,28,35,42,49,
\]
άρα είναι
\[
\left\lfloor\frac{50}{7}\right\rfloor=7.
\]

Ο αριθμός 35 έχει μετρηθεί και στις δύο ομάδες, επειδή είναι το μοναδικό πολλαπλάσιο και του 5 και του 7 στο συγκεκριμένο διάστημα. Επομένως, για να μην τον υπολογίσουμε δύο φορές, τον αφαιρούμε μία φορά:
\[
10+7-1=16.
\]

Άρα υπάρχουν 16 ευνοϊκά αποτελέσματα ανάμεσα στα 50 δυνατά αποτελέσματα. Η ζητούμενη πιθανότητα είναι
\[
\frac{16}{50}.
\]

Απλοποιούμε το κλάσμα διαιρώντας αριθμητή και παρονομαστή με 2:
\[
\frac{16}{50}=\frac{8}{25}.
\]

Επομένως, η πιθανότητα είναι
\[
\boxed{\frac{8}{25}}
\]
M0 (terse+boxed): Το πλήθος των πολλαπλασίων του 5 είναι 50 ÷ 5 = 10.
Το πλήθος των πολλαπλασίων του 7 είναι ⌊50 ÷ 7⌋ = 7.
Τα κοινά πολλαπλάσια είναι πολλαπλάσια του 35.
Το πλήθος των πολλαπλασίων του 35 είναι ⌊50 ÷ 35⌋ = 1.
Το πλήθος των ευνοϊκών περιπτώσεων είναι 10 + 7 − 1.
10 + 7 − 1 = 16
Η πιθανότητα είναι 16 / 50.
16 / 50 = 8 / 25
Απάντηση: 8/25
\boxed{\frac{8}{25}}

--- c2_gsm_4566 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ένα εισιτήριο του μετρό κοστίζει 3 €. Σε ένα λεπτό, το μετρό πουλά κατά μέσο όρο 5 τέτοια εισιτήρια. Πόσα θα είναι τα έσοδα από τα εισιτήρια σε 6 λεπτά;
M1 (worked): Σε κάθε λεπτό, το μετρό πουλά κατά μέσο όρο 5 εισιτήρια και κάθε εισιτήριο κοστίζει 3 €.

Επομένως, τα έσοδα από τα εισιτήρια μέσα σε ένα λεπτό είναι:

\[
5 \cdot 3 = 15\text{ €}.
\]

Άρα, σε ένα λεπτό το μετρό έχει κατά μέσο όρο έσοδα 15 € από την πώληση των εισιτηρίων.

Για να υπολογίσουμε τα συνολικά έσοδα σε 6 λεπτά, πολλαπλασιάζουμε τα έσοδα του ενός λεπτού επί 6:

\[
15 \cdot 6 = 90\text{ €}.
\]

Επομένως, σε 6 λεπτά το μετρό θα πουλήσει εισιτήρια συνολικής αξίας 90 € και τα έσοδά του από αυτά θα είναι:

\[
\boxed{90}
\]
M0 (terse+boxed): Τα εισιτήρια που πωλούνται σε 6 λεπτά είναι:
5 · 6 = 30 εισιτήρια
Τα συνολικά έσοδα είναι:
30 · 3 = 90 €
Απάντηση: 90 €
\boxed{90}

--- c2_gsm_3903 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ο Γιάννης πηγαίνει με το ποδήλατο από το σπίτι του στο κατάστημα. Έπειτα, συνεχίζει με την ίδια ταχύτητα και διανύει 50 μίλια μέχρι το σπίτι του φίλου του, του Πέτρου. Ο Γιάννης χρειάζεται διπλάσιο χρόνο για να πάει από το σπίτι του στο κατάστημα από όσο χρειάζεται για να πάει από το κατάστημα στον φίλο του. Αν τώρα ο Πέτρος και ο Γιάννης επιστρέψουν μαζί με τα ποδήλατά τους στο κατάστημα, πόσα μίλια έχουν διανύσει συνολικά σήμερα;
M1 (worked): Αφού ο Γιάννης κινείται σε όλη τη διαδρομή με την ίδια ταχύτητα, ο χρόνος είναι ανάλογος της απόστασης.

Η διαδρομή από το κατάστημα μέχρι το σπίτι του Πέτρου είναι 50 μίλια. Ο χρόνος από το σπίτι του Γιάννη μέχρι το κατάστημα είναι διπλάσιος, άρα και η αντίστοιχη απόσταση είναι διπλάσια:

\[
2\cdot 50=100 \text{ μίλια}.
\]

Επομένως, μέχρι να φτάσει στον Πέτρο, ο Γιάννης έχει διανύσει:

\[
100+50=150 \text{ μίλια}.
\]

Στη συνέχεια, ο Γιάννης και ο Πέτρος επιστρέφουν μαζί από το σπίτι του Πέτρου στο κατάστημα. Η απόσταση είναι 50 μίλια για τον καθένα, οπότε συνολικά διανύουν:

\[
50+50=100 \text{ μίλια}.
\]

Άρα η συνολική απόσταση που έχουν διανύσει σήμερα είναι:

\[
100+50+100=250 \text{ μίλια}.
\]

Τελική απάντηση: \(\boxed{250}\)
M0 (terse+boxed): Η διαδρομή από το κατάστημα στον Πέτρο είναι 50 μίλια.
2 · 50 = 100 μίλια από το σπίτι του Γιάννη στο κατάστημα
100 + 50 = 150 μίλια διανύει ο Γιάννης μέχρι τον Πέτρο
50 + 50 = 100 μίλια διανύουν μαζί στην επιστροφή
150 + 100 = 250 μίλια
Απάντηση: 250 μίλια
\boxed{250}

--- c2_gsm_1748 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Η Κατερίνα βρίσκεται στο σούπερ μάρκετ. Έχει συνολικά 60 € για να ξοδέψει. Θα αγοράσει 2 συσκευασίες χούμους, που κοστίζουν 5 € η καθεμία. Επίσης, θα αγοράσει κοτόπουλο αξίας 20 €, μπέικον αξίας 10 € και λαχανικά αξίας 10 €. Θέλει να αγοράσει μήλα που κοστίζουν 2 € το ένα. Με τα χρήματα που θα της απομείνουν, πόσα μήλα μπορεί να αγοράσει;
M1 (worked): Αρχικά, υπολογίζουμε το συνολικό κόστος για τις 2 συσκευασίες χούμους. Κάθε συσκευασία κοστίζει 5 €, επομένως:

\[
2 \cdot 5\,€ = 10\,€
\]

Άρα, η Κατερίνα θα πληρώσει 10 € για το χούμους.

Στη συνέχεια, υπολογίζουμε το συνολικό κόστος για το κοτόπουλο, το μπέικον και τα λαχανικά:

\[
20\,€ + 10\,€ + 10\,€ = 40\,€
\]

Επομένως, αυτά τα τρία είδη κοστίζουν συνολικά 40 €.

Τώρα αφαιρούμε από τα 60 € το κόστος του χούμους και το κόστος των υπόλοιπων ειδών:

\[
60\,€ - 10\,€ - 40\,€ = 10\,€
\]

Άρα, της απομένουν 10 € για μήλα. Αφού κάθε μήλο κοστίζει 2 €, ο αριθμός των μήλων που μπορεί να αγοράσει είναι:

\[
10\,€ \div 2\,€ = 5
\]

Επομένως, η Κατερίνα μπορεί να αγοράσει συνολικά \(\boxed{5}\) μήλα.
M0 (terse+boxed): Κόστος για το χούμους:
2 · 5 € = 10 €

Συνολικό κόστος των άλλων αγορών:
10 € + 20 € + 10 € + 10 € = 50 €

Χρήματα που απομένουν:
60 € − 50 € = 10 €

Αριθμός μήλων:
10 € : 2 € = 5

Απάντηση: 5 μήλα
\boxed{5}

--- c2_gsm_5419 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ο Μάρκος κέρδισε 5 ευρώ λιγότερα από τον Ευάγγελο. Μαζί κέρδισαν 37 ευρώ. Πόσα ευρώ κέρδισε ο Μάρκος; Χρησιμοποίησε το γράμμα E για να συμβολίσεις πόσα ευρώ κέρδισε ο Ευάγγελος.
M1 (worked): Θέτουμε

\[
E=\text{τα ευρώ που κέρδισε ο Ευάγγελος}.
\]

Ο Μάρκος κέρδισε 5 ευρώ λιγότερα από τον Ευάγγελο, επομένως τα χρήματα που κέρδισε ο Μάρκος είναι

\[
E-5.
\]

Αφού μαζί κέρδισαν 37 ευρώ, προσθέτουμε τα κέρδη τους και σχηματίζουμε την εξίσωση

\[
E+(E-5)=37.
\]

Απαλείφουμε την παρένθεση και συνδυάζουμε τους όμοιους όρους:

\[
E+E-5=37
\]

\[
2E-5=37.
\]

Προσθέτουμε 5 και στα δύο μέλη της εξίσωσης:

\[
2E-5+5=37+5
\]

\[
2E=42.
\]

Διαιρούμε και τα δύο μέλη με 2:

\[
E=\frac{42}{2}=21.
\]

Άρα ο Ευάγγελος κέρδισε 21 ευρώ. Ο Μάρκος κέρδισε 5 ευρώ λιγότερα, οπότε

\[
21-5=16.
\]

Επομένως, ο Μάρκος κέρδισε

\[
\boxed{16}
\]
M0 (terse+boxed): Ο Ευάγγελος κέρδισε E ευρώ.
Ο Μάρκος κέρδισε E − 5 ευρώ.
E + E − 5 = 37
2 · E − 5 = 37
2 · E = 42
E = 21
21 − 5 = 16 €
Απάντηση: 16 €
\boxed{16}

--- c2_gsm_584 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Κάθε παράθυρο έχει 4 υαλοπίνακες. Ένα σπίτι έχει 6 διπλά παράθυρα στο ισόγειο και 8 μονά παράθυρα στον επάνω όροφο. Πόσοι υαλοπίνακες υπάρχουν σε ολόκληρο το σπίτι;
M1 (worked): Κάθε διπλό παράθυρο αποτελείται από 2 παράθυρα. Επομένως, τα 6 διπλά παράθυρα στο ισόγειο αντιστοιχούν σε:

\[
6 \times 2 = 12
\]

Άρα, στο ισόγειο υπάρχουν συνολικά 12 παράθυρα.

Στον επάνω όροφο υπάρχουν 8 μονά παράθυρα. Για να βρούμε πόσα παράθυρα υπάρχουν σε ολόκληρο το σπίτι, προσθέτουμε τα παράθυρα των δύο ορόφων:

\[
12 + 8 = 20
\]

Επομένως, σε ολόκληρο το σπίτι υπάρχουν 20 παράθυρα.

Γνωρίζουμε ότι κάθε παράθυρο έχει 4 υαλοπίνακες. Άρα, για να υπολογίσουμε το συνολικό πλήθος των υαλοπινάκων, πολλαπλασιάζουμε τα 20 παράθυρα με τους 4 υαλοπίνακες που έχει το καθένα:

\[
20 \times 4 = 80
\]

Συνεπώς, σε ολόκληρο το σπίτι υπάρχουν συνολικά \(\boxed{80}\) υαλοπίνακες.
M0 (terse+boxed): Τα διπλά παράθυρα αντιστοιχούν σε μονά παράθυρα:
6 · 2 = 12
Τα συνολικά παράθυρα είναι:
12 + 8 = 20
Οι συνολικοί υαλοπίνακες είναι:
20 · 4 = 80
Απάντηση: 80 υαλοπίνακες
\boxed{80}

--- c2_gsm_397 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Η κόρη της Λαμπρινής είναι 10 χρόνια μικρότερη από την κόρη της Κατερίνας. Ο γιος της Λαμπρινής έχει τη διπλάσια ηλικία από την κόρη της Κατερίνας. Αν η κόρη της Κατερίνας είναι 12 ετών, πόσα χρόνια μεγαλύτερος είναι ο γιος της Λαμπρινής από την κόρη της Λαμπρινής;
M1 (worked): Η κόρη της Κατερίνας είναι 12 ετών.

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
M0 (terse+boxed): 12 − 10 = 2 έτη
2 · 12 = 24 έτη
24 − 2 = 22 έτη
Απάντηση: 22 έτη
\boxed{22}

--- c2_gsm_351 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ο Αντώνης χρειάζεται για το σοκολατένιο κέικ του τα μισά φλιτζάνια αλεύρι από όσα είναι τα αυγά που χρειάζεται. Αν χρησιμοποιεί 60 αυγά στη συνταγή του, υπολόγισε πόσα φλιτζάνια αλεύρι και πόσα αυγά χρησιμοποιεί συνολικά.
M1 (worked): Ο Αντώνης χρησιμοποιεί 60 αυγά. Ο αριθμός των φλιτζανιών αλευριού είναι ο μισός από τον αριθμό των αυγών, επομένως διαιρούμε το 60 με το 2:

\[
60 \div 2 = 30
\]

Άρα, για το σοκολατένιο κέικ χρησιμοποιεί 30 φλιτζάνια αλεύρι.

Για να υπολογίσουμε πόσα φλιτζάνια αλεύρι και πόσα αυγά χρησιμοποιεί συνολικά, προσθέτουμε τις δύο ποσότητες:

\[
30 + 60 = 90
\]

Επομένως, ο Αντώνης χρησιμοποιεί συνολικά 90 φλιτζάνια αλεύρι και αυγά στη συνταγή του.

\[
\boxed{90}
\]
M0 (terse+boxed): Χρησιμοποιεί 60 αυγά.
60 : 2 = 30
Χρειάζεται 30 φλιτζάνια αλεύρι.
30 + 60 = 90
Απάντηση: 90
\boxed{90}

--- c2_math_3939 [translated_math, level Level 4, validity none, polished unchanged]
PROBLEM: Έστω ότι οι $f$ και $g$ είναι συναρτήσεις για τις οποίες ισχύει $f^{-1}(g(x))=5x+3$. Να βρεις το $g^{-1}(f(-7))$.
M1 (worked): Γνωρίζουμε ότι
\[
f^{-1}(u)=v \iff u=f(v).
\]

Επομένως, από τη σχέση
\[
f^{-1}(g(x))=5x+3
\]
προκύπτει ισοδύναμα ότι
\[
g(x)=f(5x+3).
\]

Επειδή
\[
g(s)=t \iff s=g^{-1}(t),
\]
εφαρμόζουμε τη συνάρτηση $g^{-1}$ και στα δύο μέλη της εξίσωσης $g(x)=f(5x+3)$:
\[
g^{-1}(g(x))=g^{-1}(f(5x+3)).
\]

Άρα
\[
x=g^{-1}(f(5x+3)).
\]

Θέλουμε να υπολογίσουμε το $g^{-1}(f(-7))$. Βρίσκουμε την τιμή του $x$ για την οποία
\[
5x+3=-7.
\]
Λύνουμε την εξίσωση:
\[
5x+3=-7
\]
\[
5x=-7-3
\]
\[
5x=-10
\]
\[
x=-2.
\]

Επομένως,
\[
g^{-1}(f(-7))=g^{-1}(f(5(-2)+3)).
\]
Πράγματι,
\[
5(-2)+3=-10+3=-7.
\]

Από τη σχέση $g^{-1}(f(5x+3))=x$, για $x=-2$, παίρνουμε
\[
g^{-1}(f(5(-2)+3))=-2.
\]

Συνεπώς,
\[
\boxed{-2}
\]
M0 (terse+boxed): Θέτουμε το 5x + 3 ίσο με -7.

5x + 3 = -7

5x = -10

x = -2

Άρα:

f⁻¹(g(-2)) = -7

Εφαρμόζουμε τη συνάρτηση f.

g(-2) = f(-7)

Εφαρμόζουμε την αντίστροφη συνάρτηση g⁻¹.

g⁻¹(f(-7)) = -2

Απάντηση: -2
\boxed{-2}

--- c2_gsm_25 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Η τάξη του Βασίλη έθετε κάθε εβδομάδα έναν στόχο για τον αριθμό των κονσερβών τροφίμων που θα συγκέντρωνε. Την πρώτη ημέρα συγκεντρώθηκαν 20 κονσέρβες. Στη συνέχεια, ο αριθμός των κονσερβών αυξανόταν κατά 5 κάθε ημέρα. Αν συγκέντρωναν κονσέρβες 5 ημέρες την εβδομάδα για να πετύχουν τον στόχο τους, πόσες κονσέρβες τροφίμων ήταν ο εβδομαδιαίος στόχος τους;
M1 (worked): Την πρώτη ημέρα η τάξη συγκέντρωσε 20 κονσέρβες. Κάθε επόμενη ημέρα συγκέντρωνε 5 περισσότερες από την προηγούμενη.

Τη δεύτερη ημέρα συγκέντρωσε:
\[
20+5=25
\]
κονσέρβες.

Την τρίτη ημέρα συγκέντρωσε:
\[
25+5=30
\]
κονσέρβες.

Την τέταρτη ημέρα συγκέντρωσε:
\[
30+5=35
\]
κονσέρβες.

Την πέμπτη ημέρα συγκέντρωσε:
\[
35+5=40
\]
κονσέρβες.

Για να βρούμε τον εβδομαδιαίο στόχο, προσθέτουμε τις κονσέρβες που συγκεντρώθηκαν κατά τις 5 ημέρες:
\[
20+25+30+35+40=150
\]

Επομένως, ο εβδομαδιαίος στόχος της τάξης του Βασίλη ήταν να συγκεντρώσει συνολικά \(150\) κονσέρβες τροφίμων.

\[
\boxed{150}
\]
M0 (terse+boxed): 1η ημέρα: 20 κονσέρβες.
2η ημέρα: 20 + 5 = 25 κονσέρβες.
3η ημέρα: 25 + 5 = 30 κονσέρβες.
4η ημέρα: 30 + 5 = 35 κονσέρβες.
5η ημέρα: 35 + 5 = 40 κονσέρβες.
20 + 25 = 45 κονσέρβες.
45 + 30 = 75 κονσέρβες.
75 + 35 = 110 κονσέρβες.
110 + 40 = 150 κονσέρβες.
Απάντηση: 150 κονσέρβες
\boxed{150}

--- c2_math_672 [translated_math, level Level 2, validity none, polished unchanged]
PROBLEM: Επιλέγονται τυχαία δύο διαφορετικοί αριθμοί από το σύνολο $S = \{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11\}$. Η πιθανότητα το άθροισμά τους να είναι 12 θα ήταν μεγαλύτερη, αν είχε προηγουμένως αφαιρεθεί από το σύνολο $S$ ο αριθμός $n$. Ποια είναι η τιμή του $n$;
M1 (worked): Αρχικά επιλέγουμε δύο διαφορετικούς αριθμούς από τους 11 αριθμούς του συνόλου. Το πλήθος όλων των δυνατών ζευγών είναι
\[
\binom{11}{2}=\frac{11\cdot 10}{2}=55.
\]

Τα ζεύγη διαφορετικών αριθμών με άθροισμα 12 είναι
\[
(1,11),\ (2,10),\ (3,9),\ (4,8),\ (5,7).
\]
Άρα υπάρχουν 5 ευνοϊκά ζεύγη και η αρχική πιθανότητα είναι
\[
P=\frac{5}{55}=\frac{1}{11}.
\]

Κάθε αριθμός του συνόλου ανήκει σε ένα από αυτά τα ζεύγη, εκτός από το 6. Πράγματι, ο συμπληρωματικός του αριθμός είναι πάλι το 6, αφού
\[
6+6=12,
\]
αλλά οι δύο επιλεγμένοι αριθμοί πρέπει να είναι διαφορετικοί. Επομένως, αν αφαιρεθεί το 6, δεν χάνεται κανένα ευνοϊκό ζεύγος, ενώ τα συνολικά ζεύγη γίνονται
\[
\binom{10}{2}=45.
\]
Έτσι η νέα πιθανότητα είναι
\[
\frac{5}{45}=\frac{1}{9}>\frac{1}{11}.
\]
Αν αφαιρεθεί οποιοσδήποτε άλλος αριθμός, χάνεται ένα ευνοϊκό ζεύγος και η πιθανότητα γίνεται \(\frac{4}{45}<\frac{1}{11}\). Συνεπώς,
\[
\boxed{6}
\]
M0 (terse+boxed): Τα δυνατά ζεύγη είναι \(\binom{11}{2}=55\).
Τα ζεύγη με άθροισμα \(12\) είναι \((1,11),(2,10),(3,9),(4,8),(5,7)\).
Άρα τα ευνοϊκά ζεύγη είναι \(5\).
\(P=\frac{5}{55}\)
\(P=\frac{1}{11}\)
Ο μόνος αριθμός που δεν ανήκει σε ευνοϊκό ζεύγος είναι το \(6\).
Αν αφαιρεθεί το \(6\), τα δυνατά ζεύγη γίνονται \(\binom{10}{2}=45\).
Τα ευνοϊκά ζεύγη παραμένουν \(5\).
\(P'=\frac{5}{45}\)
\(P'=\frac{1}{9}\)
\(\f

--- c2_gsm_3744 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ένα αεριωθούμενο αεροπλάνο διανύει 580 μίλια σε 2 ώρες. Με αυτόν τον ρυθμό, πόσο μακριά θα μπορούσε να πετάξει σε 10 ώρες;
M1 (worked): Γνωρίζουμε ότι το αεριωθούμενο αεροπλάνο διανύει 580 μίλια σε 2 ώρες. Αρχικά, υπολογίζουμε πόσα μίλια διανύει σε 1 ώρα, διαιρώντας τη συνολική απόσταση με τον συνολικό χρόνο:

\[
\frac{580\ \text{μίλια}}{2\ \text{ώρες}}=290\ \text{μίλια ανά ώρα}.
\]

Επομένως, με αυτόν τον ρυθμό, το αεροπλάνο διανύει 290 μίλια σε κάθε ώρα.

Στη συνέχεια, για να βρούμε πόσο μακριά θα μπορούσε να πετάξει σε 10 ώρες, πολλαπλασιάζουμε την απόσταση που διανύει σε 1 ώρα επί 10:

\[
290\ \text{μίλια ανά ώρα}\times 10\ \text{ώρες}=2.900\ \text{μίλια}.
\]

Άρα, αν το αεριωθούμενο αεροπλάνο διατηρήσει τον ίδιο ρυθμό σε όλη τη διάρκεια της πτήσης, σε 10 ώρες θα μπορούσε να διανύσει συνολικά 2.900 μίλια.

\[
\boxed{2900}
\]
M0 (terse+boxed): Η απόσταση ανά ώρα είναι:
580 : 2 = 290 μίλια
Η απόσταση σε 10 ώρες είναι:
290 · 10 = 2.900 μίλια
Απάντηση: 2.900 μίλια
\boxed{2900}

--- c2_math_1512 [translated_math, level Level 1, validity none, polished unchanged]
PROBLEM: Δίνεται ότι $\triangle+q=59$ και $(\triangle+q)+q=106$. Ποια είναι η τιμή του $\triangle$;
M1 (worked): Έχουμε τις δύο εξισώσεις:

\[
\triangle+q=59
\]

και

\[
(\triangle+q)+q=106.
\]

Από την πρώτη εξίσωση γνωρίζουμε ότι το άθροισμα \(\triangle+q\) είναι ίσο με \(59\). Επομένως, στη δεύτερη εξίσωση μπορούμε να αντικαταστήσουμε την παράσταση \(\triangle+q\) με \(59\):

\[
59+q=106.
\]

Για να βρούμε το \(q\), αφαιρούμε \(59\) και από τις δύο πλευρές:

\[
q=106-59=47.
\]

Άρα:

\[
q=47.
\]

Τώρα αντικαθιστούμε την τιμή \(q=47\) στην πρώτη εξίσωση:

\[
\triangle+q=59
\]

\[
\triangle+47=59.
\]

Για να υπολογίσουμε το \(\triangle\), αφαιρούμε \(47\) και από τις δύο πλευρές:

\[
\triangle=59-47=12.
\]

Επομένως, η τιμή του \(\triangle\) είναι

\[
\boxed{12}
\]
M0 (terse+boxed): Ισχύει:
△ + q = 59
△ + 2q = 106
Αφαιρούμε την πρώτη εξίσωση από τη δεύτερη.
q = 106 − 59
q = 47
△ = 59 − 47
△ = 12
Απάντηση: 12
\boxed{12}

--- c2_gsm_485 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Η Μαρία ξόδεψε το 60% των χρημάτων της για φαγητό και το 25% από όσα απέμειναν για τον λογαριασμό του κινητού της. Αφού ξόδεψε 20 € για ψυχαγωγία, της έμειναν 40 €. Πόσα χρήματα είχε αρχικά η Μαρία;
M1 (worked): Μετά την πληρωμή του λογαριασμού του κινητού, η Μαρία ξόδεψε 20 € για ψυχαγωγία και της έμειναν 40 €. Επομένως, αμέσως μετά την πληρωμή του κινητού είχε:

\[
20+40=60\text{ €}
\]

Για το κινητό ξόδεψε το \(25\%\) των χρημάτων που είχαν απομείνει μετά το φαγητό. Άρα τα 60 € αντιστοιχούν στο:

\[
100\%-25\%=75\%
\]

Επομένως, το \(1\%\) των χρημάτων που είχε μετά το φαγητό ήταν:

\[
60:75=0{,}80\text{ €}
\]

Άρα, μετά την αγορά του φαγητού είχε:

\[
0{,}80\cdot100=80\text{ €}
\]

Για φαγητό είχε ξοδέψει το \(60\%\) των αρχικών χρημάτων της, οπότε τα 80 € που απέμειναν αντιστοιχούν στο:

\[
100\%-60\%=40\%
\]

Επομένως, το \(1\%\) των αρχικών χρημάτων της ήταν:

\[
80:40=2\text{ €}
\]

Άρα τα αρχικά χρήματα της Μαρίας ήταν:

\[
2\cdot100=200\text{ €}
\]

Τελικά, η Μαρία είχε αρχικά \(\boxed{200}\) ευρώ.
M0 (terse+boxed): Μετά το φαγητό απέμεινε το 40% των χρημάτων.
100% − 60% = 40%
Μετά τον λογαριασμό απέμεινε το 75% αυτού του ποσού.
100% − 25% = 75%
Το ποσό πριν από την ψυχαγωγία ήταν:
40 € + 20 € = 60 €
Το ποσό αυτό είναι το 30% των αρχικών χρημάτων.
40% · 75% = 30%
Τα αρχικά χρήματα ήταν:
60 € ÷ 30% = 200 €
Απάντηση: 200 €
\boxed{200}

--- c2_math_3582 [translated_math, level Level 3, validity none, polished unchanged]
PROBLEM: Για κάποιον θετικό ακέραιο $k$, όταν το 60 διαιρείται με το $k^2$, το υπόλοιπο είναι 6. Ποιο είναι το υπόλοιπο όταν το 100 διαιρείται με το $k$;
M1 (worked): Αφού το υπόλοιπο της διαίρεσης του 60 με το $k^2$ είναι 6, υπάρχει θετικός ακέραιος $a$ τέτοιος ώστε

\[
60=ak^2+6.
\]

Αφαιρούμε το 6 και από τα δύο μέλη:

\[
ak^2=60-6=54.
\]

Άρα το $k^2$ πρέπει να είναι τέλειο τετράγωνο που διαιρεί το 54. Αναλύουμε το 54 σε γινόμενο πρώτων παραγόντων:

\[
54=2\cdot 27=2\cdot 3^3=2\cdot 3^2\cdot 3.
\]

Το μοναδικό τετράγωνο μεγαλύτερο από το υπόλοιπο 6 που διαιρεί το 54 είναι

\[
k^2=3^2=9.
\]

Επειδή ο $k$ είναι θετικός ακέραιος, παίρνουμε

\[
k=3.
\]

Τώρα διαιρούμε το 100 με το 3. Εφόσον

\[
100=3\cdot 33+1=99+1,
\]

το υπόλοιπο της διαίρεσης είναι

\[
\boxed{1}
\]
M0 (terse+boxed): Το υπόλοιπο 6 είναι μικρότερο από τον διαιρέτη.
k² > 6
Η διαφορά του υπολοίπου από το 60 διαιρείται με το k².
60 − 6 = 54
Άρα το k² είναι τετραγωνικός διαιρέτης του 54 μεγαλύτερος από 6.
k² = 9
k = 3
Διαιρούμε το 100 με το 3.
100 = 33 · 3 + 1
Απάντηση: 1
\boxed{1}

--- c2_gsm_3781 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ο Κόστας μάζεψε από τα μανγκόδεντρά του συνολικά 60 κιλά μάνγκο. Πούλησε 20 κιλά στη λαϊκή αγορά και από την ποσότητα που απέμεινε πούλησε τη μισή στους κατοίκους της γειτονιάς του. Αν κάθε κιλό περιέχει 8 μάνγκο, πόσα μάνγκο έχει ακόμη;
M1 (worked): Αρχικά ο Κώστας είχε συνολικά 60 κιλά μάνγκο. Αφού πούλησε 20 κιλά στη λαϊκή αγορά, του απέμειναν:

\[
60-20=40 \text{ κιλά}
\]

Στη συνέχεια πούλησε στους κατοίκους της γειτονιάς του τη μισή από αυτήν την ποσότητα. Επομένως, η ποσότητα που πούλησε στη γειτονιά ήταν:

\[
\frac{1}{2}\cdot 40=20 \text{ κιλά}
\]

Άρα, μετά και τη δεύτερη πώληση, του έμειναν:

\[
40-20=20 \text{ κιλά}
\]

Κάθε κιλό περιέχει 8 μάνγκο. Για να υπολογίσουμε πόσα μάνγκο περιέχονται στα 20 κιλά που απέμειναν, πολλαπλασιάζουμε:

\[
20\cdot 8=160 \text{ μάνγκο}
\]

Επομένως, ο Κώστας έχει ακόμη συνολικά \(\boxed{160}\) μάνγκο.
M0 (terse+boxed): Μετά τη λαϊκή αγορά απομένουν:
60 − 20 = 40 κιλά
Στη γειτονιά πουλά:
40 : 2 = 20 κιλά
Του απομένουν:
40 − 20 = 20 κιλά
Τα μάνγκο που έχει ακόμη είναι:
20 · 8 = 160 μάνγκο
Απάντηση: 160 μάνγκο
\boxed{160}

--- c2_math_1762 [translated_math, level Level 4, validity none, polished unchanged]
PROBLEM: Έστω $\mathbf{a}$ και $\mathbf{b}$ δύο διανύσματα και έστω $\mathbf{m}$ το μέσο τους. Αν $\mathbf{m}=\begin{pmatrix}3\\7\end{pmatrix}$ και $\mathbf{a}\cdot\mathbf{b}=6$, να βρεις την τιμή του $\|\mathbf{a}\|^2+\|\mathbf{b}\|^2$.
M1 (worked): Αφού το διάνυσμα $\mathbf{m}$ είναι το μέσο των διανυσμάτων $\mathbf{a}$ και $\mathbf{b}$, ισχύει
\[
\mathbf{m}=\frac{\mathbf{a}+\mathbf{b}}{2}.
\]

Πολλαπλασιάζοντας και τα δύο μέλη με $2$, παίρνουμε
\[
\mathbf{a}+\mathbf{b}=2\mathbf{m}.
\]

Εφόσον
\[
\mathbf{m}=\begin{pmatrix}3\\7\end{pmatrix},
\]
έχουμε
\[
\mathbf{a}+\mathbf{b}=2\begin{pmatrix}3\\7\end{pmatrix}
=\begin{pmatrix}6\\14\end{pmatrix}.
\]

Επομένως, το τετράγωνο του μέτρου του αθροίσματος είναι
\[
\|\mathbf{a}+\mathbf{b}\|^2
=\left\|\begin{pmatrix}6\\14\end{pmatrix}\right\|^2
=6^2+14^2
=36+196
=232.
\]

Από την άλλη πλευρά,
\[
\begin{aligned}
\|\mathbf{a}+\mathbf{b}\|^2
&=(\mathbf{a}+\mathbf{b})\cdot(\mathbf{a}+\mathbf{b})\\
&=\mathbf{a}\cdot\mathbf{a}+\mathbf{a}\cdot\mathbf{b}
+\mathbf{b}\cdot\mathbf{a}+\mathbf{b}\cdot\mathbf{b}\\
&=\|\mathbf{a}\|^2+2\mathbf{a}\cdot\mathbf{b}+\|\mathbf{b}\|^2.
\end{aligned}
\]

Άρα
\[
\|\mathbf{a}\|^2+\|\mathbf{b}\|^2
=\|\mathbf{a}+\mathbf{b}\|^2-2\mathbf{a}\cdot\mathbf{b}.
\]

Χρησιμοποιώντας ότι $\|\mathbf{a}+\mathbf{b}\|^2=232$ και $\mathbf{a}\cdot\mathbf{b}=6$, βρίσκουμε
\[
\|\math
M0 (terse+boxed): Το μέσο των διανυσμάτων είναι το μισό του αθροίσματός τους.
𝐚+𝐛=2·𝐦
𝐚+𝐛=2·(3,7)
𝐚+𝐛=(6,14)
6²=36
14²=196
‖𝐚+𝐛‖²=36+196
‖𝐚+𝐛‖²=232
Ισχύει ‖𝐚+𝐛‖²=‖𝐚‖²+‖𝐛‖²+2·𝐚·𝐛.
2·6=12
‖𝐚‖²+‖𝐛‖²=232−12
‖𝐚‖²+‖𝐛‖²=220
Απάντηση: 220
\boxed{220}

--- c2_math_2985 [translated_math, level Level 2, validity none, polished unchanged]
PROBLEM: Πόσες τετραγωνικές μονάδες είναι το εμβαδόν του παραλληλογράμμου με κορυφές τα σημεία $(0,0)$, $(6,0)$, $(2,8)$ και $(8,8)$;
M1 (worked): Τα σημεία $(0,0)$ και $(6,0)$ βρίσκονται πάνω στην ευθεία $y=0$. Επομένως, μπορούμε να θεωρήσουμε ως βάση του παραλληλογράμμου το ευθύγραμμο τμήμα που τα ενώνει.

Το μήκος της βάσης είναι η διαφορά των τετμημένων των δύο σημείων:
\[
β=6-0=6
\]
άρα η βάση έχει μήκος $6$ μονάδες.

Η απέναντι πλευρά ενώνει τα σημεία $(2,8)$ και $(8,8)$, τα οποία βρίσκονται πάνω στην ευθεία $y=8$. Η βάση βρίσκεται στην ευθεία $y=0$, οπότε το ύψος του παραλληλογράμμου είναι η κατακόρυφη απόσταση ανάμεσα στις δύο παράλληλες ευθείες:
\[
υ=8-0=8
\]
άρα το ύψος είναι $8$ μονάδες.

Το εμβαδόν ενός παραλληλογράμμου δίνεται από τον τύπο
\[
E=β\cdot υ.
\]
Αντικαθιστούμε τις τιμές της βάσης και του ύψους:
\[
E=6\cdot 8=48.
\]

Επομένως, το εμβαδόν του παραλληλογράμμου είναι $48$ τετραγωνικές μονάδες, δηλαδή
\[
\boxed{48}
\]
M0 (terse+boxed): Η κάτω βάση έχει μήκος 6 - 0.
6 - 0 = 6
Η πάνω βάση είναι παράλληλη και βρίσκεται σε ύψος 8.
Ε = βάση · ύψος
Ε = 6 · 8
Ε = 48
Απάντηση: 48 τετραγωνικές μονάδες
\boxed{48}

--- c2_gsm_4027 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ένας σκύλος τρέχει μέσα σε ένα χωράφι και μαζί του αρχίζει να τρέχει μια ομάδα από 4 γάτες. Μαζί με κάθε γάτα αρχίζουν να τρέχουν 2 κουνέλια και μαζί με κάθε κουνέλι 3 λαγοί. Πόσα ζώα τρέχουν στο χωράφι;
M1 (worked): Αρχικά στο χωράφι τρέχει **1 σκύλος**. Μαζί του αρχίζουν να τρέχουν **4 γάτες**.

Για κάθε γάτα αρχίζουν να τρέχουν 2 κουνέλια. Επομένως, ο συνολικός αριθμός των κουνελιών είναι:

\[
4 \text{ γάτες} \cdot 2 \text{ κουνέλια ανά γάτα}=8 \text{ κουνέλια}.
\]

Στη συνέχεια, μαζί με κάθε κουνέλι αρχίζουν να τρέχουν 3 λαγοί. Αφού υπάρχουν 8 κουνέλια, ο συνολικός αριθμός των λαγών είναι:

\[
8 \text{ κουνέλια} \cdot 3 \text{ λαγοί ανά κουνέλι}=24 \text{ λαγοί}.
\]

Τέλος, προσθέτουμε όλα τα ζώα που τρέχουν στο χωράφι:

\[
1 \text{ σκύλος}+4 \text{ γάτες}+8 \text{ κουνέλια}+24 \text{ λαγοί}=37 \text{ ζώα}.
\]

Άρα, στο χωράφι τρέχουν συνολικά:

\[
\boxed{37}
\]
M0 (terse+boxed): Τρέχει 1 σκύλος.
Τρέχουν 4 γάτες.
4 · 2 = 8 κουνέλια.
8 · 3 = 24 λαγοί.
1 + 4 = 5 ζώα.
5 + 8 = 13 ζώα.
13 + 24 = 37 ζώα.
Απάντηση: 37 ζώα
\boxed{37}

--- c2_gsm_5926 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Ο Γιάννης έγραψε μια έκθεση 150 λέξεων. Η Μαγδαληνή έγραψε μια έκθεση με διπλάσιο μήκος και ο Τιμόθεος έγραψε μια έκθεση που είχε 30 λέξεις περισσότερες από την έκθεση της Μαγδαληνής. Αν κάθε σελίδα χωράει 260 λέξεις, πόσες σελίδες καταλαμβάνουν συνολικά οι εκθέσεις του Γιάννη, της Μαγδαληνής και του Τιμόθεου;
M1 (worked): Η έκθεση του Γιάννη έχει 150 λέξεις.

Η Μαγδαληνή έγραψε έκθεση διπλάσιου μήκους από την έκθεση του Γιάννη. Επομένως, ο αριθμός των λέξεων της έκθεσής της είναι:

\[
150 \times 2 = 300 \text{ λέξεις}
\]

Ο Τιμόθεος έγραψε 30 λέξεις περισσότερες από όσες έγραψε η Μαγδαληνή. Άρα, η έκθεσή του έχει:

\[
300 + 30 = 330 \text{ λέξεις}
\]

Συνολικά, οι τρεις εκθέσεις περιέχουν:

\[
150 + 300 + 330 = 780 \text{ λέξεις}
\]

Αφού κάθε σελίδα χωράει 260 λέξεις, διαιρούμε το συνολικό πλήθος των λέξεων με τις λέξεις που χωράει κάθε σελίδα:

\[
780 \div 260 = 3
\]

Επομένως, οι εκθέσεις του Γιάννη, της Μαγδαληνής και του Τιμόθεου καταλαμβάνουν συνολικά:

\[
\boxed{3}
\]
M0 (terse+boxed): 150 · 2 = 300 λέξεις
300 + 30 = 330 λέξεις
150 + 300 + 330 = 780 λέξεις
780 : 260 = 3 σελίδες
Απάντηση: 3 σελίδες
\boxed{3}

--- c2_gsm_3959 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Μια εταιρεία έχει 1.000 εργαζομένους. Θα πραγματοποιηθούν τρεις γύροι απολύσεων. Σε κάθε γύρο θα απολύεται το 10% των εργαζομένων που απομένουν. Πόσοι εργαζόμενοι θα απολυθούν συνολικά;
M1 (worked): Στον πρώτο γύρο απολύεται το 10% των 1.000 εργαζομένων:

\[
1.000 \cdot 10\% = 1.000 \cdot 0,10 = 100
\]

Άρα απολύονται 100 εργαζόμενοι και απομένουν:

\[
1.000-100=900
\]

Στον δεύτερο γύρο απολύεται το 10% των 900 εργαζομένων που απομένουν:

\[
900 \cdot 10\% = 900 \cdot 0,10 = 90
\]

Επομένως, μετά τον δεύτερο γύρο απομένουν:

\[
900-90=810
\]

Στον τρίτο γύρο απολύεται το 10% των 810 εργαζομένων που απομένουν:

\[
810 \cdot 10\% = 810 \cdot 0,10 = 81
\]

Για να βρούμε πόσοι εργαζόμενοι απολύθηκαν συνολικά, προσθέτουμε τις απολύσεις των τριών γύρων:

\[
100+90+81=271
\]

Άρα ο συνολικός αριθμός των εργαζομένων που θα απολυθούν είναι:

\[
\boxed{271}
\]
M0 (terse+boxed): Απολύσεις στον πρώτο γύρο:
1.000 · 10/100 = 100 εργαζόμενοι
Εργαζόμενοι μετά τον πρώτο γύρο:
1.000 − 100 = 900 εργαζόμενοι
Απολύσεις στον δεύτερο γύρο:
900 · 10/100 = 90 εργαζόμενοι
Εργαζόμενοι μετά τον δεύτερο γύρο:
900 − 90 = 810 εργαζόμενοι
Απολύσεις στον τρίτο γύρο:
810 · 10/100 = 81 εργαζόμενοι
Συνολικές απολύσεις:
100 + 90 + 81 = 271 εργαζόμενοι
Απάντηση: 271 εργαζόμενοι
\boxed{271}

--- c2_gsm_3731 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ο κτηνοτρόφος Γιώργος έχει τρεις αγελάδες γαλακτοπαραγωγής: τη Βάσω, την Κανέλα και τη Μαργαρίτα. Η Βάσω, η μικρότερη αγελάδα, του δίνει δύο κουβάδες γάλα κάθε μέρα. Η Κανέλα, η μεγαλύτερη αγελάδα, παράγει τρεις φορές αυτή την ποσότητα. Η Μαργαρίτα παράγει έναν κουβά περισσότερο από τη Βάσω. Πόσους κουβάδες γάλα παίρνει συνολικά ο κτηνοτρόφος Γιώργος από τις τρεις αγελάδες κάθε εβδομάδα;
M1 (worked): Η Βάσω παράγει κάθε μέρα:

\[
2 \text{ κουβάδες}
\]

Η Κανέλα παράγει τρεις φορές την ποσότητα της Βάσως. Επομένως, η ημερήσια παραγωγή της είναι:

\[
3 \cdot 2 = 6 \text{ κουβάδες}
\]

Η Μαργαρίτα παράγει έναν κουβά περισσότερο από τη Βάσω. Άρα παράγει καθημερινά:

\[
2+1=3 \text{ κουβάδες}
\]

Συνεπώς, οι τρεις αγελάδες παράγουν συνολικά κάθε μέρα:

\[
2+6+3=11 \text{ κουβάδες}
\]

Μία εβδομάδα έχει \(7\) ημέρες. Επομένως, για να βρούμε πόσους κουβάδες γάλα παίρνει συνολικά ο κτηνοτρόφος Γιώργος κάθε εβδομάδα, πολλαπλασιάζουμε την ημερήσια παραγωγή με το \(7\):

\[
11 \cdot 7=77 \text{ κουβάδες}
\]

Άρα ο κτηνοτρόφος Γιώργος παίρνει συνολικά \(77\) κουβάδες γάλα από τις τρεις αγελάδες κάθε εβδομάδα.

\[
\boxed{77}
\]
M0 (terse+boxed): 2 · 3 = 6 κουβάδες από την Κανέλα κάθε μέρα
2 + 1 = 3 κουβάδες από τη Μαργαρίτα κάθε μέρα
2 + 6 + 3 = 11 κουβάδες κάθε μέρα
11 · 7 = 77 κουβάδες κάθε εβδομάδα
Απάντηση: 77 κουβάδες
\boxed{77}

--- c2_math_2213 [translated_math, level Level 2, validity none, polished unchanged]
PROBLEM: Στην τάξη μου στα Μαθηματικά υπάρχουν 30 μαθητές. Από αυτούς, 12 έχουν συμπαθητικό μπαμπά, 15 έχουν συμπαθητική μαμά και 9 έχουν και συμπαθητικό μπαμπά και συμπαθητική μαμά. Πόσοι μαθητές έχουν μαμά και μπαμπά που δεν είναι συμπαθητικοί;
M1 (worked): Θεωρούμε δύο σύνολα: τους μαθητές που έχουν συμπαθητικό μπαμπά και τους μαθητές που έχουν συμπαθητική μαμά.

Αρχικά, 9 μαθητές ανήκουν και στα δύο σύνολα, αφού έχουν και συμπαθητικό μπαμπά και συμπαθητική μαμά.

Από τους 12 μαθητές που έχουν συμπαθητικό μπαμπά, οι 9 έχουν επίσης συμπαθητική μαμά. Άρα οι μαθητές που έχουν μόνο συμπαθητικό μπαμπά είναι:
\[
12-9=3.
\]

Αντίστοιχα, από τους 15 μαθητές που έχουν συμπαθητική μαμά, οι 9 έχουν επίσης συμπαθητικό μπαμπά. Επομένως, οι μαθητές που έχουν μόνο συμπαθητική μαμά είναι:
\[
15-9=6.
\]

Έτσι, οι μαθητές που έχουν τουλάχιστον έναν συμπαθητικό γονέα είναι συνολικά:
\[
3+9+6=18.
\]

Η τάξη έχει 30 μαθητές, οπότε όσοι δεν έχουν κανέναν συμπαθητικό γονέα, δηλαδή έχουν και μαμά και μπαμπά που δεν είναι συμπαθητικοί, είναι:
\[
30-18=12.
\]

Άρα η τελική απάντηση είναι:
\[
\boxed{12}
\]
M0 (terse+boxed): Προσθέτουμε όσους έχουν συμπαθητικό μπαμπά ή μαμά.
12 + 15 = 27
Αφαιρούμε όσους μετρήθηκαν δύο φορές.
27 − 9 = 18
Αφαιρούμε αυτούς τους μαθητές από το σύνολο.
30 − 18 = 12
Απάντηση: 12 μαθητές
\boxed{12}

--- c2_gsm_4970 [translated_gsm8k, level gsm, validity none, polished edited]
PROBLEM: Για να παραγάγει μία σοκολάτα, μια εταιρεία χρειάζεται 1,5 γραμμάρια ζάχαρης. Κάθε λεπτό η εταιρεία παράγει 36 σοκολάτες. Πόσα γραμμάρια ζάχαρης θα χρησιμοποιήσει η εταιρεία σε δύο λεπτά;
M1 (worked): Σε ένα λεπτό η εταιρεία παράγει 36 σοκολάτες. Για κάθε σοκολάτα χρειάζεται 1,5 γραμμάριο ζάχαρης. Επομένως, η ποσότητα ζάχαρης που χρησιμοποιείται σε ένα λεπτό είναι:

\[
36 \cdot 1{,}5 = 54
\]

Άρα, σε ένα λεπτό η εταιρεία χρησιμοποιεί 54 γραμμάρια ζάχαρης.

Σε δύο λεπτά θα χρησιμοποιήσει τη διπλάσια ποσότητα ζάχαρης. Επομένως:

\[
54 \cdot 2 = 108
\]

Άρα, για να παραγάγει τις σοκολάτες σε δύο λεπτά, η εταιρεία θα χρησιμοποιήσει συνολικά:

\[
\boxed{108}
\]
M0 (terse+boxed): Σε δύο λεπτά παράγονται:
36 · 2 = 72 σοκολάτες
Η ζάχαρη που χρησιμοποιείται είναι:
72 · 1,5 = 108 γραμμάρια
Απάντηση: 108 γραμμάρια
\boxed{108}

--- c2_gsm_322 [translated_gsm8k, level gsm, validity none, polished unchanged]
PROBLEM: Ο Μάνος πρέπει να αγοράσει καινούρια πιάτα για το σπίτι του. Θέλει να πλένει τα πιάτα μόνο μία φορά την εβδομάδα. Τρεις ημέρες την εβδομάδα τρώνε μόνο ο ίδιος και ο γιος του και χρησιμοποιούν από 1 πιάτο ο καθένας. Τις υπόλοιπες ημέρες τρώνε μαζί τους και οι γονείς του και τότε όλοι χρησιμοποιούν από 2 πιάτα την ημέρα. Πόσα πιάτα πρέπει να αγοράσει;
M1 (worked): Τρεις ημέρες την εβδομάδα τρώνε μόνο ο Μάνος και ο γιος του. Επομένως, τα άτομα που τρώνε αυτές τις ημέρες είναι:

\[
1+1=2 \text{ άτομα}
\]

Αφού ο καθένας χρησιμοποιεί 1 πιάτο, σε καθεμία από αυτές τις ημέρες χρησιμοποιούν 2 πιάτα. Άρα, στις 3 ημέρες χρησιμοποιούν συνολικά:

\[
3\cdot 2=6 \text{ πιάτα}
\]

Η εβδομάδα έχει 7 ημέρες, οπότε οι ημέρες κατά τις οποίες τρώνε μαζί τους και οι γονείς του είναι:

\[
7-3=4 \text{ ημέρες}
\]

Τότε τρώνε συνολικά ο Μάνος, ο γιος του και οι δύο γονείς του:

\[
2+2=4 \text{ άτομα}
\]

Καθένας χρησιμοποιεί 2 πιάτα, άρα κάθε τέτοια ημέρα χρειάζονται:

\[
4\cdot 2=8 \text{ πιάτα}
\]

Για τις 4 αυτές ημέρες χρειάζονται:

\[
8\cdot 4=32 \text{ πιάτα}
\]

Συνεπώς, για ολόκληρη την εβδομάδα ο Μάνος πρέπει να αγοράσει:

\[
32+6=38 \text{ πιάτα}
\]

\[
\boxed{38}
\]
M0 (terse+boxed): Τρεις ημέρες τρώνε 2 άτομα.
3 · 2 · 1 = 6
Τις υπόλοιπες ημέρες τρώνε 4 άτομα.
7 − 3 = 4
4 · 4 · 2 = 32
6 + 32 = 38
Απάντηση: 38 πιάτα
\boxed{38}

--- c2_math5_872 [Level 5, validity none, polished unchanged]
PROBLEM: Ποιο είναι το γινόμενο όλων των συντεταγμένων όλων των σημείων τομής των δύο κύκλων που ορίζονται από τις εξισώσεις $x^2-2x +y^2-10y+25=0$ και $x^2-8x+y^2-10y+37=0$;
TARGET: Ολοκληρώνουμε τα τετράγωνα στις δύο εξισώσεις.

Για τον πρώτο κύκλο:
\[
x^2-2x+y^2-10y+25=0.
\]
Προσθέτουμε \(\left(\frac{-2}{2}\right)^2=1\) και χρησιμοποιούμε ότι
\[
y^2-10y+25=(y-5)^2.
\]
Έτσι,
\[
(x^2-2x+1)+(y^2-10y+25)=1,
\]
άρα
\[
(x-1)^2+(y-5)^2=1^2.
\]
Επομένως, ο πρώτος κύκλος έχει κέντρο \((1,5)\) και ακτίνα \(1\).

Για τον δεύτερο κύκλο:
\[
x^2-8x+y^2-10y+37=0.
\]
Ολοκληρώνοντας τα τετράγωνα, παίρνουμε
\[
(x^2-8x+16)+(y^2-10y+25)=-37+16+25=4,
\]
οπότε
\[
(x-4)^2+(y-5)^2=2^2.
\]
Άρα ο δεύτερος κύκλος έχει κέντρο \((4,5)\) και ακτίνα \(2\).

Η απόσταση των κέντρων είναι
\[
\sqrt{(4-1)^2+(5-5)^2}=\sqrt{9}=3.
\]
Το άθροισμα των ακτίνων είναι επίσης
\[
1+2=3.
\]
Επομένως, οι κύκλοι εφάπτονται εξωτερικά και έχουν μόνο ένα κοινό σημείο. Το σημείο αυτό βρίσκεται στην ευθεία των κέντρων και είναι το
\[
(1+1,5)=(2,5).
\]
Πράγματι, απέχει \(1\) από το \((1,5)\) και \(2\) από το \((4,5)\).

Το γινόμενο όλων των συντεταγμένων του μοναδικού σημείου τομής είναι
\[
2\cdot 5=\boxed{10}.
\]

--- c2_math5_1272 [Level 5, validity none, polished edited]
PROBLEM: Για το σύνολο $\{1, 2, 3, \ldots, n\}$ ορίζεται για καθένα από τα μη κενά υποσύνολά του ένα μοναδικό εναλλασσόμενο άθροισμα ως εξής. Διατάσσουμε τους αριθμούς του υποσυνόλου σε φθίνουσα σειρά και στη συνέχεια, αρχίζοντας από τον μεγαλύτερο, προσθέτουμε και αφαιρούμε εναλλάξ τους διαδοχικούς αριθμούς. Για παράδειγμα, το εναλλασσόμενο άθροισμα για το $\{1, 2, 3, 6,9\}$ είναι $9-6+3-2+1=5$, ενώ για το $\{5\}$ είναι απλώς $5$. Να βρείτε το άθροισμα όλων αυτών των εναλλασσόμενων αθροισμάτων για $n=7$
TARGET: Θεωρούμε οποιοδήποτε υποσύνολο
\[
S\subseteq\{1,2,3,4,5,6\}.
\]
Το ζευγαρώνουμε με το υποσύνολο
\[
S\cup\{7\}.
\]

Αν τα στοιχεία του $S$ σε φθίνουσα σειρά είναι
\[
a_1>a_2>\cdots>a_k,
\]
τότε το εναλλασσόμενο άθροισμά του είναι
\[
A(S)=a_1-a_2+a_3-\cdots+(-1)^{k+1}a_k.
\]

Στο $S\cup\{7\}$, το $7$ είναι το μεγαλύτερο στοιχείο, οπότε γράφεται πρώτο. Επομένως,
\[
A(S\cup\{7\})=7-a_1+a_2-a_3+\cdots+(-1)^k a_k.
\]

Προσθέτοντας τα δύο αθροίσματα, κάθε στοιχείο του $S$ εμφανίζεται μία φορά με θετικό και μία φορά με αρνητικό πρόσημο:
\[
\begin{aligned}
A(S)+A(S\cup\{7\})
&=(a_1-a_2+a_3-\cdots)
 +(7-a_1+a_2-a_3+\cdots)\\
&=7.
\end{aligned}
\]
Άρα κάθε τέτοιο ζεύγος υποσυνόλων έχει συνολικό εναλλασσόμενο άθροισμα $7$.

Το σύνολο $\{1,2,3,4,5,6\}$ έχει
\[
2^6=64
\]
υποσύνολα, αφού για καθένα από τα $6$ στοιχεία υπάρχουν $2$ επιλογές: είτε ανήκει είτε δεν ανήκει στο $S$. Επομένως σχηματίζονται $64$ ζεύγη. Για $S=\varnothing$, το ζεύγος συνεισφέρει μόνο το υποσύνολο $\{7\}$, του οποίου το άθροισμα είναι $7$.

Συνεπώς, το ζητούμενο άθροισμα όλων των μη κενών υποσυνόλων είναι
\[
64\cdot 7=448.
\]

\[
\boxed{448}
\]

--- c2_math5_1387 [Level 5, validity none, polished unchanged]
PROBLEM: Δεδομένου ότι οι γραφικές παραστάσεις των $y=h(x)$ και $y=j(x)$ τέμνονται στα σημεία $(2,2),$ $(4,6),$ $(6,12),$ και $(8,12),$ υπάρχει ένα σημείο στο οποίο οι γραφικές παραστάσεις των $y=h(2x)$ και $y=2j(x)$ πρέπει να τέμνονται. Ποιο είναι το άθροισμα των συντεταγμένων αυτού του σημείου;
TARGET: Από τα σημεία τομής των γραφικών παραστάσεων των $y=h(x)$ και $y=j(x)$ γνωρίζουμε ότι οι δύο συναρτήσεις έχουν ίσες τιμές για τις αντίστοιχες τετμημένες. Επομένως,

$$
\begin{array}{c@{\qquad}c}
h(2)=j(2)=2, & h(4)=j(4)=6, \\
h(6)=j(6)=12, & h(8)=j(8)=12.
\end{array}
$$

Έστω ότι οι γραφικές παραστάσεις των $y=h(2x)$ και $y=2j(x)$ τέμνονται στο σημείο $(a,b)$. Τότε, στο $x=a$, οι δύο συναρτήσεις πρέπει να έχουν την ίδια τιμή $b$. Άρα

$$h(2a)=2j(a)=b.$$

Αναζητούμε στις γνωστές τιμές ένα $a$ για το οποίο γνωρίζουμε τόσο το $j(a)$ όσο και το $h(2a)$. Επιλέγουμε $a=4$, διότι τότε

$$2a=2\cdot4=8.$$

Από τα δεδομένα έχουμε

$$j(4)=6$$

και συνεπώς

$$2j(4)=2\cdot6=12.$$

Επίσης, από το σημείο τομής $(8,12)$ γνωρίζουμε ότι

$$h(8)=12.$$

Επομένως,

$$h(2\cdot4)=h(8)=12=2j(4).$$

Άρα οι γραφικές παραστάσεις των $y=h(2x)$ και $y=2j(x)$ τέμνονται στο σημείο

$$(4,12).$$

Το άθροισμα των συντεταγμένων του σημείου είναι

$$4+12=16.$$

Συνεπώς, η τελική απάντηση είναι

$$\boxed{16}$$

--- c2_math5_234 [Level 5, validity none, polished unchanged]
PROBLEM: Η Περιφερειακή Λίγκα Μπάσκετ των Μικρών Δώδεκα έχει δύο ομίλους, με έξι ομάδες σε κάθε όμιλο. Κάθε ομάδα παίζει δύο φορές με καθεμία από τις άλλες ομάδες του ομίλου της και μία φορά με κάθε ομάδα του άλλου ομίλου. Πόσοι αγώνες της λίγκας έχουν προγραμματιστεί;
TARGET: Κάθε όμιλος έχει $6$ ομάδες. Επομένως, για μία συγκεκριμένη ομάδα, οι άλλες ομάδες του ίδιου ομίλου είναι

\[
6-1=5.
\]

Η ομάδα παίζει δύο φορές με καθεμία από αυτές, άρα οι αγώνες της μέσα στον όμιλό της είναι

\[
5\times 2=10.
\]

Στον άλλο όμιλο υπάρχουν $6$ ομάδες και η συγκεκριμένη ομάδα παίζει μία φορά με καθεμία από αυτές. Επομένως, οι αγώνες της εναντίον ομάδων του άλλου ομίλου είναι

\[
6\times 1=6.
\]

Άρα κάθε ομάδα παίζει συνολικά

\[
10+6=16
\]

αγώνες στη λίγκα.

Οι δύο όμιλοι έχουν συνολικά

\[
2\times 6=12
\]

ομάδες. Αν πολλαπλασιάσουμε τις $12$ ομάδες με τους $16$ αγώνες κάθε ομάδας, παίρνουμε

\[
12\times 16=192.
\]

Όμως έτσι κάθε αγώνας έχει μετρηθεί δύο φορές, μία για καθεμία από τις δύο ομάδες που συμμετέχουν. Γι’ αυτό διαιρούμε με το $2$:

\[
\frac{12\times 16}{2}=\frac{192}{2}=96.
\]

Επομένως, έχουν προγραμματιστεί συνολικά

\[
\boxed{96}
\]

--- c2_math5_419 [Level 5, validity none, polished unchanged]
PROBLEM: Δίνεται ότι $x<1$ και ότι 
\[(\log_{10} x)^2 - \log_{10}(x^2) = 48,\]
να υπολογίσετε την τιμή της παράστασης
\[(\log_{10}x)^3 - \log_{10}(x^3).\]
TARGET: Εφόσον ορίζεται ο όρος $\log_{10}x$, πρέπει $x>0$. Θέτουμε
\[
y=\log_{10}x.
\]

Χρησιμοποιούμε την ιδιότητα
\[
\log_{10}(x^2)=2\log_{10}x=2y.
\]

Άρα η δοσμένη εξίσωση γίνεται
\[
y^2-2y=48.
\]

Μεταφέρουμε το $48$ στο αριστερό μέλος:
\[
y^2-2y-48=0.
\]

Αναζητούμε δύο αριθμούς με γινόμενο $-48$ και άθροισμα $-2$. Οι αριθμοί αυτοί είναι οι $-8$ και $6$, οπότε
\[
y^2-8y+6y-48=0,
\]
\[
y(y-8)+6(y-8)=0,
\]
\[
(y-8)(y+6)=0.
\]

Επομένως
\[
y-8=0 \quad \text{ή} \quad y+6=0,
\]
δηλαδή
\[
y=8 \quad \text{ή} \quad y=-6.
\]

Επειδή $0<x<1$, ισχύει $\log_{10}x<0$. Άρα απορρίπτουμε τη θετική τιμή $y=8$ και παίρνουμε
\[
\log_{10}x=y=-6.
\]

Τώρα χρησιμοποιούμε την ιδιότητα
\[
\log_{10}(x^3)=3\log_{10}x.
\]

Επομένως
\[
\begin{aligned}
(\log_{10}x)^3-\log_{10}(x^3)
&=(\log_{10}x)^3-3\log_{10}x\\
&=(-6)^3-3(-6)\\
&=-216+18\\
&=\boxed{-198}.
\end{aligned}
\]

--- c2_math5_1462 [Level 5, validity none, polished edited]
PROBLEM: Η Λουκία γεννήθηκε την Τετάρτη 1 Δεκεμβρίου 2004. Εκείνη η Τετάρτη ήταν η πρώτη ημέρα της ζωής της. Οι γονείς της διοργάνωσαν ένα πάρτι για εκείνη τη $1000$ή ημέρα της ζωής της. Ποια ημέρα της εβδομάδας έγινε το πάρτι;
TARGET: Μία εβδομάδα έχει $7$ ημέρες. Αφού η $1$η ημέρα της ζωής της Λουκίας ήταν Τετάρτη, Τετάρτη ήταν επίσης κάθε ημέρα ο αριθμός της οποίας είναι κατά $1$ μεγαλύτερος από ένα πολλαπλάσιο του $7$:

\[
1,\ 8,\ 15,\ 22,\ldots
\]

Διαιρούμε το $1000$ με το $7$:

\[
1000=7\cdot142+6.
\]

Άρα το υπόλοιπο είναι $6$. Ο επόμενος αριθμός που είναι κατά $1$ μεγαλύτερος από πολλαπλάσιο του $7$ είναι το $1002$, επειδή

\[
1002=7\cdot143+1.
\]

Επομένως, η $1002$η ημέρα της ζωής της ήταν Τετάρτη. Η $1000$ή ημέρα ήταν δύο ημέρες νωρίτερα:

\[
\text{Τετάρτη}\longrightarrow\text{Τρίτη}\longrightarrow\text{Δευτέρα}.
\]

Συνεπώς, το πάρτι έγινε τη Δευτέρα, δηλαδή

\[
\boxed{\text{Monday}}
\]

--- c2_math5_651 [Level 5, validity none, polished edited]
PROBLEM: Το παραλληλόγραμμο $ABCD$ με $A(2,5)$, $B(4,9)$, $C(6,5)$ και $D(4,1)$ συμμετρίζεται ως προς τον άξονα $x$ και προκύπτει το $A'B'C'D'$. Στη συνέχεια, το $A'B'C'D'$ συμμετρίζεται ως προς την ευθεία $y=x+1$ και προκύπτει το $A''B''C''D''$. Αυτό γίνεται έτσι ώστε το $D'$ να είναι η εικόνα του $D$ και το $D''$ να είναι η εικόνα του $D'$. Ποιο είναι το διατεταγμένο ζεύγος συντεταγμένων του $D''$ στο επίπεδο συντεταγμένων;
TARGET: Αρχικά εξετάζουμε μόνο την κορυφή $D$, αφού ζητούνται οι συντεταγμένες της τελικής εικόνας της.

Η κορυφή είναι
\[
D=(4,1).
\]

Κατά τη συμμετρία ως προς τον άξονα $x$, η τετμημένη παραμένει ίδια, ενώ η τεταγμένη αλλάζει πρόσημο. Δηλαδή εφαρμόζουμε τον μετασχηματισμό
\[
(x,y)\longmapsto(x,-y).
\]

Επομένως,
\[
D=(4,1)\longmapsto D'=(4,-1).
\]

Στη συνέχεια βρίσκουμε το συμμετρικό του $D'$ ως προς την ευθεία
\[
y=x+1.
\]

Για να μετατρέψουμε την ευθεία αυτή στην $y=x$, μεταφέρουμε την ευθεία και το σημείο κατά μία μονάδα προς τα κάτω. Έτσι,
\[
y=x+1\longmapsto y=x
\]
και
\[
D'=(4,-1)\longmapsto(4,-1-1)=(4,-2).
\]

Η συμμετρία ως προς την ευθεία $y=x$ ανταλλάσσει την τετμημένη με την τεταγμένη:
\[
(x,y)\longmapsto(y,x).
\]

Άρα,
\[
(4,-2)\longmapsto(-2,4).
\]

Τέλος, αναιρούμε την αρχική μεταφορά προς τα κάτω, μεταφέροντας το νέο σημείο κατά μία μονάδα προς τα πάνω:
\[
(-2,4)\longmapsto(-2,4+1)=(-2,5).
\]

Επομένως, το διατεταγμένο ζεύγος συντεταγμένων του $D''$ είναι
\[
\boxed{(-2,5)}.
\]

--- c2_math5_269 [Level 5, validity none, polished unchanged]
PROBLEM: Ο Γιάννης θέλει να βρει όλες τις λέξεις τεσσάρων γραμμάτων που αρχίζουν και τελειώνουν με το ίδιο γράμμα. Πόσοι συνδυασμοί γραμμάτων ικανοποιούν αυτή την ιδιότητα;
TARGET: Για το πρώτο γράμμα υπάρχουν $26$ επιλογές.

Για το δεύτερο γράμμα υπάρχουν επίσης $26$ επιλογές και, ανεξάρτητα, για το τρίτο γράμμα υπάρχουν άλλες $26$ επιλογές.

Το τέταρτο γράμμα δεν επιλέγεται ελεύθερα, επειδή πρέπει να είναι ίδιο με το πρώτο. Επομένως, για κάθε επιλογή του πρώτου γράμματος, το τελευταίο καθορίζεται πλήρως.

Άρα, σύμφωνα με την αρχή του πολλαπλασιασμού, το πλήθος των συνδυασμών είναι

\[
26\cdot 26\cdot 26=26^3.
\]

Υπολογίζουμε:

\[
26^2=26\cdot 26=676
\]

και

\[
26^3=676\cdot 26=676\cdot(20+6)=13.520+4.056=17.576.
\]

Επομένως, οι συνδυασμοί γραμμάτων που αρχίζουν και τελειώνουν με το ίδιο γράμμα είναι

\[
\boxed{17576}
\]

--- c2_math5_746 [Level 5, validity none, polished edited]
PROBLEM: Στο παρακάτω διάγραμμα, τα σημεία $A$, $B$, $C$ και $P$ είναι τοποθετημένα έτσι ώστε $PA=2$, $PB=3$, $PC=4$ και $BC=5$. Ποιο είναι το μέγιστο δυνατό εμβαδόν του $	riangle ABC$; [asy]
defaultpen(linewidth(0.8)); size(150);
pair B = (0,0), C = (5,0), A = (2,3), P = (2.2,2);
draw(A--B--C--cycle^^B--P^^C--P^^A--P);
label("$A$",A,N); label("$B$",B,S); label("$C$",C,S); label("$P$",P,S);
[/asy]
TARGET: Αφού $PB=3$, $PC=4$ και $BC=5$, παρατηρούμε ότι
\[
PB^2+PC^2=3^2+4^2=9+16=25=5^2=BC^2.
\]
Επομένως, από το αντίστροφο του Πυθαγόρειου θεωρήματος, το τρίγωνο $PBC$ είναι ορθογώνιο στο $P$.

Άρα το εμβαδόν του είναι
\[
[\triangle PBC]=\frac12\cdot PB\cdot PC
=\frac12\cdot3\cdot4=6.
\]

Έστω $H$ το ίχνος της καθέτου από το $P$ προς την ευθεία $BC$. Χρησιμοποιώντας τώρα ως βάση την $BC=5$, έχουμε
\[
[\triangle PBC]=\frac12\cdot BC\cdot PH.
\]
Άρα
\[
6=\frac12\cdot5\cdot PH
\]
και επομένως
\[
12=5PH \quad\Longrightarrow\quad PH=\frac{12}{5}.
\]

Έστω $h$ η απόσταση του $A$ από την ευθεία $BC$. Τότε
\[
[\triangle ABC]=\frac12\cdot BC\cdot h
=\frac12\cdot5\cdot h.
\]
Επομένως, για να μεγιστοποιηθεί το εμβαδόν, πρέπει να μεγιστοποιηθεί το ύψος $h$.

Το σημείο $A$ απέχει σταθερή απόσταση $AP=2$ από το $P$, άρα κινείται σε κύκλο με κέντρο $P$ και ακτίνα $2$. Η μεγαλύτερη δυνατή απόσταση του $A$ από την $BC$ προκύπτει όταν το $A$ βρίσκεται πάνω στην κάθετη προς την $BC$ που περνά από το $P$, στην πλευρά του $P$ που απομακρύνεται από την $BC$. Τότε
\[
h=PH+PA=\frac{12}{5}+2
=\frac{12}{5}+\frac{10}{5}
=\frac{22}{5}.
\]

Άρα το μέγιστο δυνατό εμβαδόν είναι
\[
[\triangle ABC]_{\max}
=\frac12\cdot5\cdot\frac{22}{5}
=\frac{22}{2}
=\boxed{11}.
\]

--- c2_math5_1109 [Level 5, validity none, polished edited]
PROBLEM: Να υπολογίσετε την τιμή της παράστασης $\cfrac{\left\lceil\cfrac{17}{7}-\left\lceil\cfrac{27}{17}\right\rceil\right\rceil}{\left\lceil\cfrac{27}{7}+\left\lceil\cfrac{7\cdot17}{27}\right\rceil\right\rceil}$.
TARGET: Υπολογίζουμε πρώτα τις παραστάσεις που βρίσκονται μέσα στις εσωτερικές συναρτήσεις οροφής. Η συνάρτηση οροφής $\lceil x\rceil$ δίνει τον μικρότερο ακέραιο που είναι μεγαλύτερος από ή ίσος με το $x$.

Αρχικά,
\[
1<\frac{27}{17}<2,
\]
επομένως
\[
\left\lceil\frac{27}{17}\right\rceil=2.
\]

Επίσης,
\[
\frac{7\cdot17}{27}=\frac{119}{27}.
\]
Επειδή
\[
4=\frac{108}{27}<\frac{119}{27}<\frac{135}{27}=5,
\]
έχουμε
\[
\left\lceil\frac{7\cdot17}{27}\right\rceil=5.
\]

Αντικαθιστούμε αυτές τις τιμές στην αρχική παράσταση:
\[
\frac{\left\lceil\frac{17}{7}-\left\lceil\frac{27}{17}\right\rceil\right\rceil}{\left\lceil\frac{27}{7}+\left\lceil\frac{7\cdot17}{27}\right\rceil\right\rceil}
=
\frac{\left\lceil\frac{17}{7}-2\right\rceil}{\left\lceil\frac{27}{7}+5\right\rceil}.
\]

Για τον αριθμητή:
\[
\frac{17}{7}-2=\frac{17}{7}-\frac{14}{7}=\frac{3}{7},
\]
άρα
\[
\left\lceil\frac{3}{7}\right\rceil=1,
\]
αφού $0<\frac{3}{7}<1$.

Για τον παρονομαστή:
\[
\frac{27}{7}+5=\frac{27}{7}+\frac{35}{7}=\frac{62}{7}.
\]
Επειδή
\[
8=\frac{56}{7}<\frac{62}{7}<\frac{63}{7}=9,
\]
προκύπτει
\[
\left\lceil\frac{62}{7}\right\rceil=9.
\]

Επομένως, η τιμή της παράστασης είναι
\[
\boxed{\frac{1}{9}}
\]

--- c2_math5_966 [Level 5, validity none, polished unchanged]
PROBLEM: Το λουρί του Άρη είναι δεμένο σε έναν πάσσαλο στο κέντρο της αυλής του, η οποία έχει σχήμα κανονικού εξαγώνου. Το λουρί του έχει ακριβώς το μήκος που χρειάζεται ώστε να φτάνει στο μέσο κάθε πλευράς της αυλής του. Αν το κλάσμα του εμβαδού της αυλής του Άρη στο οποίο μπορεί να φτάσει ενώ είναι δεμένος με το λουρί του εκφράζεται στην απλούστερη ριζική μορφή ως $\frac{\sqrt{a}}{b}\pi$, ποια είναι η τιμή του γινομένου $ab$;
TARGET: Το μήκος του λουριού είναι ίσο με την απόσταση από το κέντρο του κανονικού εξαγώνου μέχρι το μέσο μιας πλευράς. Επομένως, αν συμβολίσουμε το μήκος του λουριού με $r$, τότε $r$ είναι το απόστημα του εξαγώνου.

Η περιοχή στην οποία μπορεί να φτάσει ο Άρης είναι ο εγγεγραμμένος κύκλος ακτίνας $r$. Άρα το εμβαδόν της είναι
\[
E_{\text{κύκλου}}=\pi r^2.
\]

Χωρίζουμε τώρα το κανονικό εξάγωνο σε $6$ ίσα ισόπλευρα τρίγωνα, ενώνοντας το κέντρο του με τις κορυφές του.

Σε ένα από αυτά τα τρίγωνα, το ύψος είναι $r$. Το ύψος χωρίζει το ισόπλευρο τρίγωνο σε δύο ορθογώνια τρίγωνα $30^\circ$-$60^\circ$-$90^\circ$. Αν η πλευρά του ισόπλευρου τριγώνου είναι $s$, τότε
\[
r=\frac{\sqrt{3}}{2}s.
\]

Λύνουμε ως προς $s$:
\[
s=\frac{2r}{\sqrt{3}}.
\]

Το εμβαδόν ενός από τα έξι τρίγωνα είναι
\[
E_{\text{τριγώνου}}
=\frac{1}{2}\cdot s\cdot r
=\frac{1}{2}\cdot\frac{2r}{\sqrt{3}}\cdot r
=\frac{r^2}{\sqrt{3}}.
\]

Επομένως, το εμβαδόν ολόκληρου του εξαγώνου είναι
\[
E_{\text{εξαγώνου}}
=6\cdot\frac{r^2}{\sqrt{3}}
=\frac{6r^2}{\sqrt{3}}.
\]

Άρα το ζητούμενο κλάσμα του εμβαδού είναι
\[
\frac{E_{\text{κύκλου}}}{E_{\text{εξαγώνου}}}
=\frac{\pi r^2}{\frac{6r^2}{\sqrt{3}}}
=\pi r^2\cdot\frac{\sqrt{3}}{6r^2}
=\frac{\sqrt{3}}{6}\pi.
\]

Συνεπώς, $a=3$ και $b=6$. Επομένως,
\[
ab=3\cdot6=\boxed{18}.
\]

--- c2_math5_1181 [Level 5, validity none, polished unchanged]
PROBLEM: Έστω ότι $\theta$ είναι η γωνία μεταξύ της ευθείας
\[\frac{x + 1}{2} = \frac{y}{3} = \frac{z - 3}{6}\]
και του επιπέδου $-10x - 2y + 11z = 3.$ Να βρείτε το $\sin \theta.$

[asy]
import three;

size(150);
currentprojection = perspective(6,3,2);

triple I = (1,0,0), J = (0,1,0), K = (0,0,1), O = (0,0,0);

draw(surface((2*I + 2*J)--(2*I - 2*J)--(-2*I - 2*J)--(-2*I + 2*J)--cycle),paleyellow,nolight);
draw((2*I + 2*J)--(2*I - 2*J)--(-2*I - 2*J)--(-2*I + 2*J)--cycle);
draw((0,0,0)--(-0.5,1.5,1));
draw
TARGET: Από τη συμμετρική μορφή της ευθείας
\[
\frac{x+1}{2}=\frac{y}{3}=\frac{z-3}{6},
\]
θέτουμε την κοινή τιμή ίση με \(t\). Τότε
\[
x+1=2t,\qquad y=3t,\qquad z-3=6t,
\]
άρα
\[
x=-1+2t,\qquad y=3t,\qquad z=3+6t.
\]
Επομένως, ένα διάνυσμα διεύθυνσης της ευθείας είναι
\[
\mathbf d=\begin{pmatrix}2\\3\\6\end{pmatrix}.
\]

Το επίπεδο έχει εξίσωση
\[
-10x-2y+11z=3,
\]
οπότε ένα κάθετο διάνυσμά του είναι
\[
\mathbf n=\begin{pmatrix}-10\\-2\\11\end{pmatrix}.
\]

Αν \(\theta\) είναι η γωνία μεταξύ της ευθείας και του επιπέδου, τότε η γωνία μεταξύ των διανυσμάτων \(\mathbf d\) και \(\mathbf n\) είναι \(90^\circ-\theta\). Άρα
\[
\sin\theta=\cos(90^\circ-\theta)
=\frac{|\mathbf d\cdot\mathbf n|}{\|\mathbf d\|\,\|\mathbf n\|}.
\]

Υπολογίζουμε πρώτα το εσωτερικό γινόμενο:
\[
\mathbf d\cdot\mathbf n
=2(-10)+3(-2)+6(11)
=-20-6+66
=40.
\]

Τα μέτρα των δύο διανυσμάτων είναι
\[
\|\mathbf d\|=\sqrt{2^2+3^2+6^2}
=\sqrt{4+9+36}
=\sqrt{49}
=7
\]
και
\[
\|\mathbf n\|=\sqrt{(-10)^2+(-2)^2+11^2}
=\sqrt{100+4+121}
=\sqrt{225}
=15.
\]

Επομένως,
\[
\sin\theta
=\frac{|40|}{7\cdot15}
=\frac{40}{105}
=\boxed{\frac{8}{21}}.
\]

--- c2_math5_1355 [Level 5, validity none, polished unchanged]
PROBLEM: Ποιος είναι ο μέγιστος αριθμός σημείων τομής που μπορούν να προκύψουν όταν σχεδιαστούν $2$ διαφορετικοί κύκλοι και $2$ διαφορετικές ευθείες στο ίδιο φύλλο χαρτιού;
TARGET: Δύο γεωμετρικά σχήματα τέμνονται όταν έχουν ένα ή περισσότερα κοινά σημεία. Για να βρούμε τον μέγιστο αριθμό σημείων τομής, τοποθετούμε τους κύκλους και τις ευθείες έτσι ώστε κάθε επιτρεπτή τομή να δίνει διαφορετικά σημεία.

Οι δύο διαφορετικοί κύκλοι μπορούν να τέμνονται το πολύ σε $2$ σημεία. Άρα:

\[
N_{\text{κύκλος–κύκλος}}=2.
\]

Μια ευθεία μπορεί να τέμνει έναν κύκλο το πολύ σε $2$ σημεία. Επομένως, αφού έχουμε $2$ ευθείες και $2$ κύκλους, προκύπτουν συνολικά:

\[
N_{\text{ευθεία–κύκλος}}
=2\text{ ευθείες}\cdot 2\text{ κύκλοι}\cdot 2\text{ σημεία}
=8.
\]

Τέλος, οι δύο διαφορετικές ευθείες μπορούν να επιλεγούν ώστε να μην είναι παράλληλες. Τότε τέμνονται σε ακριβώς $1$ σημείο:

\[
N_{\text{ευθεία–ευθεία}}=1.
\]

Επιλέγουμε τη διάταξη έτσι ώστε κανένα από αυτά τα σημεία να μη συμπίπτει με κάποιο άλλο. Συνεπώς, ο συνολικός μέγιστος αριθμός σημείων τομής είναι:

\[
N_{\max}=2+8+1=11.
\]

Άρα ο μέγιστος αριθμός σημείων τομής είναι

\[
\boxed{11}
\]

--- c2_math5_442 [Level 5, validity none, polished unchanged]
PROBLEM: Έστω $a,$ $b,$ $c$ διακεκριμένοι μιγαδικοί αριθμοί τέτοιοι ώστε
\[\frac{a}{1 - b} = \frac{b}{1 - c} = \frac{c}{1 - a} = k.\]
Να βρείτε το άθροισμα όλων των δυνατών τιμών του $k.$
TARGET: Από την ισότητα των τριών κλασμάτων παίρνουμε
\[
a=k(1-b),\qquad b=k(1-c),\qquad c=k(1-a).
\]
Αντικαθιστούμε διαδοχικά τις δύο τελευταίες σχέσεις στην πρώτη:
\begin{align*}
a&=k(1-b)\\
&=k\bigl(1-k(1-c)\bigr)\\
&=k\bigl(1-k(1-k(1-a))\bigr).
\end{align*}
Αναπτύσσοντας το δεξί μέλος, έχουμε
\begin{align*}
a&=k\bigl(1-k+k^2(1-a)\bigr)\\
&=k-k^2+k^3-ak^3.
\end{align*}
Επομένως,
\[
ak^3+a-k^3+k^2-k=0.
\]
Η παράσταση παραγοντοποιείται ως
\[
(k^2-k+1)(ak+a-k)=0.
\]
Άρα εξετάζουμε δύο περιπτώσεις.

Αν
\[
ak+a-k=0,
\]
τότε
\[
a(k+1)=k.
\]
Η τιμή $k=-1$ δεν ικανοποιεί την εξίσωση, οπότε
\[
a=\frac{k}{k+1}.
\]
Με τον ίδιο ακριβώς τρόπο, εφαρμόζοντας τις κυκλικές σχέσεις για τα $b$ και $c$, προκύπτει
\[
b=\frac{k}{k+1},\qquad c=\frac{k}{k+1}.
\]
Τότε όμως $a=b=c$, αντίθετα με την υπόθεση ότι οι τρεις μιγαδικοί είναι διακεκριμένοι. Επομένως αυτή η περίπτωση απορρίπτεται.

Άρα αναγκαστικά
\[
k^2-k+1=0.
\]
Οι δύο ρίζες είναι
\[
k_1=\frac{1+i\sqrt3}{2},\qquad k_2=\frac{1-i\sqrt3}{2}.
\]
Οι τιμές αυτές είναι πράγματι δυνατές: για καθεμία μπορούμε να επιλέξουμε
\[
a=2,
\qquad b=2k-1,
\qquad c=-k,
\]
οπότε οι $a,b,c$ είναι διακεκριμένοι, κανένας παρονομαστής δεν μηδενίζεται και οι τρεις λόγοι ισούνται με $k$.

Τέλος, από τους τύπους του Vieta, το άθροισμα των ριζών της $k^2-k+1=0$ είναι
\[
k_1+k_2=

--- c2_math5_669 [Level 5, validity none, polished unchanged]
PROBLEM: Να βρείτε το άθροισμα των τετραγώνων των λύσεων της εξίσωσης $x^2-13x+4=0$.
TARGET: Έστω $r_1$ και $r_2$ οι λύσεις της εξίσωσης

\[
x^2-13x+4=0.
\]

Από τους τύπους του Viète, για μια εξίσωση της μορφής $x^2-Sx+P=0$, το άθροισμα των λύσεων είναι $S$ και το γινόμενό τους είναι $P$. Επομένως,

\[
r_1+r_2=13
\]

και

\[
r_1r_2=4.
\]

Ζητάμε το άθροισμα $r_1^2+r_2^2$. Υψώνουμε στο τετράγωνο το άθροισμα των λύσεων:

\[
(r_1+r_2)^2=13^2.
\]

Αναπτύσσοντας το τετράγωνο του αθροίσματος, παίρνουμε

\[
r_1^2+2r_1r_2+r_2^2=169.
\]

Αφαιρούμε τώρα τον όρο $2r_1r_2$ και από τα δύο μέλη:

\[
r_1^2+r_2^2=169-2r_1r_2.
\]

Επειδή $r_1r_2=4$, αντικαθιστούμε:

\[
r_1^2+r_2^2=169-2\cdot4
\]

\[
=169-8
\]

\[
=161.
\]

Άρα το άθροισμα των τετραγώνων των λύσεων είναι

\[
\boxed{161}
\]

--- c2_math5_643 [Level 5, validity none, polished unchanged]
PROBLEM: Το τετράγωνο του $a$ και η τετραγωνική ρίζα του $b$ είναι αντιστρόφως ανάλογα. Αν $a=2$ όταν $b=81$, τότε να βρείτε το $b$ όταν $ab=48$.
TARGET: Αφού το $a^2$ και το $\sqrt{b}$ είναι αντιστρόφως ανάλογα, το γινόμενό τους είναι σταθερό. Επομένως,

\[
a^2\sqrt{b}=k,
\]

όπου $k$ είναι η σταθερά αναλογίας.

Για $a=2$ και $b=81$, έχουμε

\[
k=2^2\sqrt{81}.
\]

Υπολογίζουμε:

\[
2^2=4
\]

και

\[
\sqrt{81}=9.
\]

Άρα

\[
k=4\cdot 9=36.
\]

Επομένως, για οποιεσδήποτε αντίστοιχες τιμές των $a$ και $b$ ισχύει

\[
a^2\sqrt{b}=36.
\]

Υψώνουμε και τα δύο μέλη στο τετράγωνο:

\[
\left(a^2\sqrt{b}\right)^2=36^2.
\]

Άρα

\[
a^4\cdot b=1.296.
\]

Γνωρίζουμε επίσης ότι

\[
ab=48.
\]

Διαιρούμε την εξίσωση $a^4b=1.296$ με την εξίσωση $ab=48$:

\[
\frac{a^4b}{ab}=\frac{1.296}{48}.
\]

Απλοποιώντας, παίρνουμε

\[
a^3=27.
\]

Επομένως,

\[
a=\sqrt[3]{27}=3.
\]

Τέλος, από τη σχέση $ab=48$ έχουμε

\[
3b=48
\]

και, διαιρώντας με $3$,

\[
b=\frac{48}{3}=\boxed{16}.
\]

--- c2_math5_1340 [Level 5, validity none, polished edited]
PROBLEM: Ρίχνουμε ένα συνηθισμένο εξάεδρο ζάρι και έστω $P$ το γινόμενο των πέντε αριθμών που είναι ορατοί. Ποιος είναι ο μεγαλύτερος αριθμός που διαιρεί με βεβαιότητα το $P$;
TARGET: Το γινόμενο όλων των αριθμών του ζαριού είναι
\[
1\cdot2\cdot3\cdot4\cdot5\cdot6=6!=720.
\]

Αναλύουμε το $720$ σε πρώτους παράγοντες:
\[
720=2^4\cdot3^2\cdot5.
\]

Σε κάθε ρίψη μόνο η κάτω έδρα δεν είναι ορατή. Επομένως το $P$ προκύπτει αφαιρώντας από το γινόμενο έναν από τους αριθμούς $1,2,3,4,5,6$.

Εξετάζουμε τον μικρότερο αριθμό εμφανίσεων κάθε πρώτου παράγοντα:

- Για τον παράγοντα $2$, η μικρότερη δύναμη προκύπτει όταν δεν φαίνεται το $4=2^2$:
\[
\frac{720}{4}=180=2^2\cdot3^2\cdot5.
\]
Άρα κάθε $P$ περιέχει τουλάχιστον τον παράγοντα $2^2$.

- Για τον παράγοντα $3$, η μικρότερη δύναμη προκύπτει όταν δεν φαίνεται το $3$ ή το $6$:
\[
\frac{720}{3}=240=2^4\cdot3\cdot5,
\qquad
\frac{720}{6}=120=2^3\cdot3\cdot5.
\]
Άρα κάθε $P$ περιέχει τουλάχιστον έναν παράγοντα $3$.

- Για τον παράγοντα $5$, αν δεν φαίνεται το $5$, τότε
\[
\frac{720}{5}=144=2^4\cdot3^2,
\]
οπότε το $P$ δεν είναι πάντοτε διαιρετό με $5$.

Συνεπώς ο μεγαλύτερος κοινός διαιρέτης όλων των δυνατών τιμών του $P$ είναι
\[
2^2\cdot3=4\cdot3=12.
\]

Άρα ο μεγαλύτερος αριθμός που διαιρεί με βεβαιότητα το $P$ είναι
\[
\boxed{12}
\]

--- c2_math5_1123 [Level 5, validity none, polished edited]
PROBLEM: Έστω ότι οι $x,$ $y,$ και $z$ είναι θετικοί πραγματικοί αριθμοί. Να βρείτε την ελάχιστη τιμή της παράστασης
\[\frac{4z}{2x + y} + \frac{4x}{y + 2z} + \frac{y}{x + z}.\]
TARGET: Θέτουμε
\[
a=2x,\qquad b=y,\qquad c=2z.
\]
Επειδή οι $x,y,z$ είναι θετικοί πραγματικοί αριθμοί, ισχύει και $a,b,c>0$. Επίσης,
\[
x=\frac a2,\qquad y=b,\qquad z=\frac c2.
\]
Άρα η δοσμένη παράσταση γίνεται
\begin{align*}
\frac{4z}{2x+y}+\frac{4x}{y+2z}+\frac{y}{x+z}
&=\frac{4\cdot\frac c2}{a+b}+\frac{4\cdot\frac a2}{b+c}+\frac{b}{\frac a2+\frac c2}\\
&=\frac{2c}{a+b}+\frac{2a}{b+c}+\frac{2b}{a+c}\\
&=2\left(\frac{a}{b+c}+\frac{b}{a+c}+\frac{c}{a+b}\right).
\end{align*}

Θέτουμε
\[
S=\frac{a}{b+c}+\frac{b}{a+c}+\frac{c}{a+b}.
\]
Τότε
\begin{align*}
S+3
&=\left(\frac{a}{b+c}+1\right)+\left(\frac{b}{a+c}+1\right)+\left(\frac{c}{a+b}+1\right)\\
&=\frac{a+b+c}{b+c}+\frac{a+b+c}{a+c}+\frac{a+b+c}{a+b}\\
&=(a+b+c)\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right).
\end{align*}

Όμως
\[
a+b+c=\frac12\big[(b+c)+(a+c)+(a+b)\big],
\]
οπότε
\[
S+3=\frac12\big[(b+c)+(a+c)+(a+b)\big]
\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right).
\]

Από την ανισότητα Cauchy–Schwarz,
\[
\big[(b+c)+(a+c)+(a+b)\big]
\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right)
\ge (1+1+1)^2=9.
\]
Επομένως,
\[
S+3\ge\frac92
\quad\Longrightarrow\quad
S\ge\frac92-3=\frac32.
\]
Άρα η αρχική παράσταση ικανοποιεί
\[
2S\ge 2\cdot\frac32=3.
\]

Η ισότητα στην Cauchy–Schwarz ισχύει όταν
\[
b+c=a+c=a+b,
\]
δηλαδή όταν $a=b=c$. Με βάση

--- c2_math5_1152 [Level 5, validity none, polished unchanged]
PROBLEM: Οι κύκλοι $A,B$ και $C$ εφάπτονται εξωτερικά μεταξύ τους και εσωτερικά στον κύκλο $D$. Οι κύκλοι $B$ και $C$ είναι ίσοι. Ο κύκλος $A$ έχει ακτίνα 1 και διέρχεται από το κέντρο του $D$. Ποια είναι η ακτίνα του κύκλου $B$;

[asy]unitsize(1cm);
pair A,B,C,D;
A=(-1,0);
B=(0.66,0.88);
C=(0.66,-0.88);
D=(0,0);
draw(Circle(A,1),linewidth(0.7));
draw(Circle(B,0.88),linewidth(0.7));
draw(Circle(C,0.88),linewidth(0.7));
draw(Circle(D,2),linewidth(0.7));
label("$A$",A,A);
label("$B$",B,B);
label("$C$",C,C)
TARGET: Έστω $E,H$ και $F$ τα κέντρα των κύκλων $A,B$ και $D$ αντίστοιχα, και $G$ το σημείο επαφής των ίσων κύκλων $B$ και $C$. Θέτουμε
\[
FG=x \quad\text{και}\quad GH=y.
\]
Επειδή το $H$ είναι το κέντρο του κύκλου $B$, το $GH=y$ είναι η ακτίνα του κύκλου $B$.

Ο κύκλος $A$ έχει ακτίνα 1 και διέρχεται από το κέντρο $F$ του κύκλου $D$, άρα
\[
EF=1.
\]
Επιπλέον, οι κύκλοι $A$ και $D$ εφάπτονται εσωτερικά. Επομένως, η ακτίνα του $D$ είναι
\[
1+EF=1+1=2.
\]

Οι ίσοι κύκλοι $B$ και $C$ είναι συμμετρικοί ως προς την ευθεία $EFG$, οπότε $HG\perp EF$. Άρα τα τρίγωνα $EGH$ και $FGH$ είναι ορθογώνια στο $G$.

Οι κύκλοι $A$ και $B$ εφάπτονται εξωτερικά, επομένως
\[
EH=1+y.
\]
Επίσης,
\[
EG=EF+FG=1+x.
\]
Εφαρμόζοντας το Πυθαγόρειο θεώρημα στο τρίγωνο $EGH$, παίρνουμε
\[
(1+y)^2=(1+x)^2+y^2.
\]
Αναπτύσσοντας:
\[
1+2y+y^2=1+2x+x^2+y^2,
\]
άρα
\[
2y=2x+x^2
\]
και συνεπώς
\[
y=x+\frac{x^2}{2}.
\]

Ο κύκλος $B$ εφάπτεται εσωτερικά στον κύκλο $D$, του οποίου η ακτίνα είναι 2, άρα
\[
FH=2-y.
\]
Στο ορθογώνιο τρίγωνο $FGH$ έχουμε
\[
(2-y)^2=x^2+y^2.
\]
Αναπτύσσοντας:
\[
4-4y+y^2=x^2+y^2,
\]
οπότε
\[
4-4y=x^2
\]
και
\[
y=1-\frac{x^2}{4}.
\]

Εξισώνουμε τις δύο εκφράσεις του $y$:
\[
x+\frac{x^2}{2}=1-\frac{x^2}{4}.
\]
Πολλαπλασιάζοντας με 4:
\[
4x+2x^2=4-x^2,
\]
άρα
\[
3x^2+4x-4=0.
\]
Παραγοντοποιούμε:
\[
(3x

--- c2_math5_946 [Level 5, validity none, polished unchanged]
PROBLEM: Έστω $f(n)$ μια συνάρτηση η οποία, για έναν ακέραιο $n$, δίνει έναν ακέραιο $k$, όπου $k$ είναι ο μικρότερος δυνατός ακέραιος τέτοιος ώστε το $k!$ να διαιρείται με το $n$. Δεδομένου ότι το $n$ είναι πολλαπλάσιο του 15, ποια είναι η μικρότερη τιμή του $n$ για την οποία $f(n) > 15$;
TARGET: Θέτουμε
\[
n=15r,
\]
όπου ο \(r\) είναι θετικός ακέραιος. Ζητάμε τη μικρότερη τιμή του \(n\) για την οποία \(n\nmid 15!\), αφού τότε ο μικρότερος \(k\) με \(n\mid k!\) θα είναι μεγαλύτερος από \(15\).

Για κάθε \(r\leq 14\), ο αριθμός \(r\) διαιρεί το \(14!\). Επομένως,
\[
15!=15\cdot14!
\]
διαιρείται με το
\[
15r=n.
\]
Άρα, για \(r\leq14\), ισχύει \(f(n)\leq15\). Συνεπώς πρέπει
\[
r>14.
\]

Εξετάζουμε διαδοχικά τις επόμενες τιμές του \(r\).

Για \(r=15\), έχουμε
\[
n=15\cdot15=225.
\]
Όμως μέσα στο \(15!\) υπάρχουν οι διαφορετικοί παράγοντες \(15\), \(5\) και \(3\), και
\[
15\cdot5\cdot3=225.
\]
Επομένως,
\[
225\mid15!,
\]
άρα \(f(225)\leq15\). Συνεπώς πρέπει \(r>15\).

Για \(r=16\), έχουμε
\[
n=15\cdot16=240.
\]
Μέσα στο \(15!\) υπάρχουν οι διαφορετικοί παράγοντες \(15\), \(8\) και \(2\), και
\[
15\cdot8\cdot2=240.
\]
Άρα
\[
240\mid15!,
\]
οπότε \(f(240)\leq15\). Συνεπώς πρέπει \(r>16\).

Για \(r=17\), παίρνουμε
\[
n=15\cdot17=255.
\]
Επειδή
\[
255=3\cdot5\cdot17
\]
και ο \(17\) είναι πρώτος, κανένα \(k!\) με \(k<17\) δεν περιέχει τον πρώτο παράγοντα \(17\). Άρα
\[
255\nmid k!\quad\text{για κάθε }k<17.
\]
Αντίθετα,
\[
17!=1\cdot2\cdots3\cdots5\cdots17
\]
περιέχει τους παράγοντες \(3\), \(5\) και \(17\), επομένως
\[
255\mid17!.
\]
Άρα
\[
f(255)=17>15.
\]

Επομένως, η μικρότερη ζ
