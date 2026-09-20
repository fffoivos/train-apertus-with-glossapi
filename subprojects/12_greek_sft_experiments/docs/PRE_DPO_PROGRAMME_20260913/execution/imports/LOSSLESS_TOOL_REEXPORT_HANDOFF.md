# Lossless tool re-export handoff

The reviewable change is [export_core_lossless.patch](./export_core_lossless.patch). It applies cleanly to the current `data/export_core.py`; [export_core_lossless_candidate.py](./export_core_lossless_candidate.py) is the resulting candidate file for inspection. No project or corpus file was changed.

## What the patch changes

- Removes every 1,500-character cut from system schemas, `function_calls`, `tool_calls` and block-style calls.
- Keeps the current text protocol so the existing assembler can still consume the export.
- Also retains the native `functions`, `function_calls`, `tool_calls`, `tool_call_id` and `name` fields. Non-string content is retained as `native_content`; block-style calls are retained as `block_calls`. Tool/environment results are rendered as a JSON envelope containing their content, name and call ID.
- Renders schemas and every call representation even when the turn also contains ordinary text. If `function_calls`, `tool_calls` and block calls coexist, all three are named inside one `<function_calls>` JSON object rather than one silently replacing another.
- Preserves existing source IDs, including zero, and records the typed `source_id`. If a parquet source has no ID, the fallback includes file, row group and row index rather than a repeated row-group number.
- Records an immutable 40-hex upstream revision and a row locator: parquet file/row-group/row index, or streaming split/source index.
- Preserves valid numeric source ID `0`; fallback is used only when the field is absent, null or empty.
- Prevalidates every selected repository revision before creating or opening output files. It then requires a new or empty destination, preventing an invalid invocation from truncating existing exports.

## Intake requirements

Before a pilot, create a reviewed JSON object mapping every selected dataset repository to a full 40-hex Hugging Face commit. For the tool-only pilot it needs exactly `allenai/Dolci-Instruct-SFT`. All selected repositories are checked before the destination is touched. Record the revision file hash, patch hash, command, `ONLY`, `THIN`, selected parquet files, output hash, row count and timestamp in the run receipt. Resolve and review licence/terms separately; a commit pin establishes identity, not permission.

The current export samples evenly spaced parquet shards and applies seeded thinning. For a repair export, do not overwrite `/Users/foivoskarounos-zamparloukos/sft_annot/core_export/dolci_tooluse.jsonl`. Supply a new or verified-empty versioned destination, then compare IDs and structural receipts before assembly. Missing upstream fields are reported; they are not filled from guesses or from the corrupted local export.

## Native export versus the current consumer

The patched export itself round-trips native schemas, all three call representations, structured results, source IDs and call IDs. The current downstream consumer, `data/assemble_mix_r2.py::to_messages`, explicitly constructs new dictionaries from only `role`, `content` and optional `train`; it therefore strips every native field.

The patch compensates by putting complete JSON equivalents in `<functions>`, `<function_calls>` and the tool-result content. The isolated test executes the actual current `to_messages` function and confirms that a 2,400-character schema, a 1,800-character call argument, mixed ordinary text, block calls, call IDs and result IDs all remain in rendered message content. This establishes rendered-text survival under the current consumer. It does not establish native structured-tool preservation in the final trainer input. If native tool objects are required by the serving/training protocol, the consumer and trainer need a separate structured-message change and acceptance test; until then, the candidate is text-protocol tool supervision.

## Bounded pilot, then full CPU-host run

1. Apply the patch in an isolated checkout on the CPU data host.
2. Pin the Dolci revision and run `ONLY=dolci_tooluse` into a new pilot directory with a small deterministic target, such as 200 rows. Use a pilot-only target override or temporary reviewed fixture; do not change the production target silently.
3. Require 200/200 exact native-field export roundtrips, 200/200 parseable schemas where a schema exists, every called name declared, arguments validated against the visible schema, preserved call/result IDs, and no payload-length boundary spike. Then pass every row through the actual consumer and require byte-complete rendered tags for schemas, calls, results and IDs. Compare each pilot record to its pinned upstream row locator.
4. Run the existing 4,032-token gate on the lossless rendered rows. Long schemas may now push records beyond the training window; report and exclude them rather than clipping them.
5. Semantically inspect 40 pilot rows stratified by schema length, call count, turn count and protocol variant. The 40-row read is separate from structural acceptance.
6. Only after those gates pass, run the full tool export on the appropriate CPU data host, not this Mac. Write to a new versioned path, produce hashes/counts and run the 29,700/40,000 all-row protocol audit before selecting any training subset.

The old 29,700-row block remains quarantined. A successful re-export creates a new candidate pool; it does not mutate or retroactively repair G3F2P1.

## Isolated validation

[validate_lossless_patch.py](./validate_lossless_patch.py) parses and tests the exact candidate helpers, and first checks that the patch applies cleanly. It covers schemas and calls longer than 1,500 characters, mixed text with all call forms, absent optional fields, source ID zero, refusal of an occupied destination, native result/call IDs, exact JSON roundtrip, actual-consumer rendered survival and the immutable-revision gate. The observed results are in [lossless_patch_validation.txt](./lossless_patch_validation.txt); all ten checks passed without network or corpus access.

## Root application update — 13 September 2026

The reviewed code repair has now been applied to the project and verified against the tested candidate. See `../applied_repairs.json` (at the execution root) for file hashes and limitations. Historical corpora and scores were not recomputed. Earlier statements above describe the proposal-stage audit.
