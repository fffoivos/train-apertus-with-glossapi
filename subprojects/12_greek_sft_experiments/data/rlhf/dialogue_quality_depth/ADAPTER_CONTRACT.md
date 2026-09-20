# Dialogue preference adapter contract

Each row in `runtime/measurement/preferences.jsonl` has exactly these training fields:

`{id, prefix_messages, prefix_sha256, chosen, rejected, chosen_source, rejected_source, selection_kind, depth, language, task, trajectory_id, receipt}`.

The adapter must serialize `prefix_messages` with the checkpoint's actual chat template, separately append either `chosen` or `rejected` as the assistant completion, and verify the serialized prompt/history is byte-identical for both branches before tokenization. `prefix_sha256` is the SHA-256 of canonical UTF-8 JSON for `prefix_messages`; it must match on both candidates and the exported row.

Loss applies only to the selected completion tokens. Every token produced from `prefix_messages` is assigned the ignore label (`-100` in the reference convention), including all earlier user turns and all earlier assistant turns—even an earlier bad assistant response in a recovery example. Completion labels equal their own token IDs. Padding, if added, is also ignored. The repository helper `export_pairs.completion_only_labels(history_token_ids, completion_token_ids)` expresses this contract.

The two sides may differ only after the shared prefix boundary. Never concatenate a prevention completion with a recovery history, reuse a suffix generated after another answer, edit earlier turns, or train prompt/history tokens. Fable's actual loader must independently test the boundary against its tokenizer and chat template before accepting these rows; these offline tests cannot validate that external training pipeline.

