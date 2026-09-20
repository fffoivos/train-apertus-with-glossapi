# Final reviewed candidate package: 32 maths rows

## Package decision

This directory contains a review-only package of **32 complete user/assistant records** assembled from the frozen maths pilot inputs and the three completed review streams. It contains **24 new or rebuilt candidates** (16 fresh Level-5 adaptations plus eight repaired targets) and **eight retained controls**. No production dataset, frozen input, queue, accepted output, or score was changed.

All 32 candidates have exactly one nonempty user turn followed by one nonempty assistant turn. Their source, adaptation, selected solution, review, repair, and correction bindings are embedded in `candidate_rows.jsonl` with hashes. The candidate ID remains the pilot ID. In particular, `repair_math5_*` and `repair_gsm_*` labels from the adjudication packet are preserved only as frozen packet metadata; the package does not claim that a partial label proves an exact historical training-row mapping.

## Selected content

| Group | Rows | Binding |
|---|---|---|
| Fresh, root-reviewed | `2429`, `2507`, `4821`, `6029`, `5324`, `7113` | Greek adaptation + `solve_high` |
| Fresh with accepted source clarification | `1950`, `6930` | Clarified Greek task + unchanged `solve_high` |
| Fresh, agent-reviewed | `1334`, `1379`, `4646`, `2676`, `3093`, `3125`, `5977` | Reviewed Greek task + clean `verify` solution |
| Fresh control-character override | `3775` | Reviewed Greek task + clean `solve_high`; the earlier `verify` selection is rejected for one decoded U+000C |
| Rebuilt target | `repair_math5_139`, `77`, `537`, `repair_gsm_1253` | `solve_high` |
| Rebuilt target | `repair_math5_1014`, `630`, `436` | `solve_xhigh` |
| Rebuilt target with conflict resolution | `repair_gm_math_2231` | Existing accepted exact-match overlay |
| Retained controls | all eight `control_*` rows | Frozen `prior_candidate_solution` |

For `1334`, the candidate applies the reviewed natural Greek prompt polish “Ποιο είναι, σε τετραγωνικές μονάδες, το εμβαδόν…”. For `1379`, the proposed `f(x)`→`f` notation change is recorded as optional and is **not applied**: the generated wording follows the English source and does not create a demonstrated semantic adaptation failure. For `1950`, the task now explicitly states independent uniform arrivals. For `6930`, it asks for one possible sum and a proof, because `(1,2,5)` and `(2,5,5)` give equivalent zero equations but sums 8 and 12.

The `gm_math_2231` pilot high solution and the earlier accepted overlay are both mathematically valid elementary proofs. The package selects the existing overlay to prevent competing replacements. It is already bound to the exact prior messages and explicitly mentions negative and zero-containing blocks. The unused pilot-high artifact and its hash remain recorded in the row’s conflict history.

## Control-character and message validation

All **88 accepted output envelopes** were parsed and recursively scanned after JSON decoding for C0 characters, excluding TAB/LF/CR, and for DEL. Three findings occur in two envelopes:

- two U+000C characters in `solve_high__repair_math5_1014`, which the reused-row review had already rejected;
- one U+000C character in `verify__fresh_math5_line_3775`, found during final assembly.

Neither envelope is selected. Row `3775` now uses its clean high solution, whose parameter-case proof is equivalent and complete. The final 32 selected message pairs contain **zero** disallowed C0/DEL characters. `control_character_scan.json` contains all 88 file hashes and exact decoded JSON paths.

## Exact token and length inventory

The pinned local CPT tokenizer was available, so tokenization is complete rather than pending. The package was rendered through the canonical training code with:

- tokenizer `fffoivos/apertus-8b-greek-cpt`, revision `18-avg-uniform5-tokens30B-50B`, resolved locally to `c7f806e268083c64ce831bc46483bf98e5ddcee1`;
- the locally cached `swiss-ai/Apertus-8B-Instruct-2509` template;
- the canonical `cluster/sft_train.py::prepare_tokenizer` and `tokenize_messages` path, including its control-token and assistant-mask checks.

Measured totals are **13,681 rendered tokens**, including **8,741 supervised assistant tokens**. Per-row rendered lengths range from **123 to 1,003 tokens**, so all 32 are below the 4,096-token gate. The 24 new/rebuilt candidates account for 12,192 rendered and 8,149 supervised tokens; the eight retained controls account for 1,489 rendered and 592 supervised tokens. Character and whitespace-word counts, per-row token counts, tokenizer/config hashes, vocabulary size 148,992, and control-token IDs are in `token_inventory.json`.

## Measured generation run

The receipts record **92 Sol calls**: 88 accepted calls and four failed first adaptation attempts with no provider-reported usage. The four failures were retried once and accepted; the runner reports no quota stop and no final job failure. Across the 88 calls with usage, the provider receipts report:

- 1,098,460 input tokens, of which 571,392 are marked cached;
- 75,074 output tokens;
- 28,089 reasoning-output tokens.

The sum of individual call durations is 1,849.87 seconds. Because calls ran concurrently, the observed wall interval was 416.553 seconds. Across all 92 attempts, latency had median 17.36 s, nearest-rank p95 49.13 s, mean 20.107 s, and maximum 77.54 s. `usage_metrics.json` provides per-stage/effort/state totals and every receipt binding. These are measured pilot-run values, not a forecast.

## Eight high/xhigh pairs

The paired comparison reads the full proofs and keeps its scope to the eight deliberately selected rows:

| Row | Descriptive result |
|---|---|
| `1379` | Equivalent complete injectivity proofs; both distinguish all three intersection points. |
| `3775` | Equivalent complete parameter/domain analyses; both reject the forbidden double root. |
| `4646` | Equivalent complete Vieta proofs; xhigh repeats a no-extraneous-root point already justified by high. |
| `6930` | Same valid factorization and same failure to detect the source’s nonunique sum. |
| `repair_math5_1014` | Both mathematical ideas reach 2%, but xhigh is required for a clean candidate because high contains decoded controls. |
| `repair_math5_139` | Both complete; high is slightly more direct because it uses one auxiliary variable rather than two. |
| `repair_math5_436` | Both counts are complete; xhigh makes orientation symbols and physical direction easier to audit. |
| `repair_math5_630` | Both establish the tangent formula globally; xhigh uses a shorter AM-GM optimization, while high uses differentiation. |

`paired_high_xhigh.jsonl` binds both envelopes and their individual usage/latency receipts. This eight-row descriptive comparison supports no significance claim, population estimate, or general conclusion about reasoning effort.

## Files and promotion boundary

- `candidate_rows.jsonl`: 32 complete candidate records with full bindings and histories.
- `control_character_scan.json`: decoded scan of all 88 accepted outputs and the final 32 records.
- `token_inventory.json`: exact canonical tokenizer measurements.
- `usage_metrics.json`: 92-call receipt aggregation.
- `paired_high_xhigh.jsonl`: eight full-proof comparisons with receipt metrics.
- `validation.json`: deterministic package checks.
- `manifest.json`: input and output hashes.

The package is ready for root review. It is not a production overwrite or a promotion authorization.
