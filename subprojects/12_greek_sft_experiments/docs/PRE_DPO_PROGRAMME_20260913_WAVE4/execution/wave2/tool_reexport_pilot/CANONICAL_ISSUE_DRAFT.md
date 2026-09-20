# Preserve upstream `source_dataset` in lossless core exports

The applied `data/export_core.py` repair preserves typed source IDs, immutable revisions and row locators, but `_export_row` still writes only the export block label in `source`. For Dolci Tool Use, the upstream `source_dataset` value (`Dolci Instruct Tool Use`) is not retained. A block label such as `dolci_tooluse` is useful routing metadata, but it is not a substitute for the upstream dataset-family field.

The bounded Tool Use pilot works around this in its experiment-owned adapter by adding `source_dataset` after calling the unchanged `_export_row` helper. The canonical fix should add an optional upstream-source field without changing existing `source` semantics, and `emit` should pass the exact native value when present. It must never infer a missing value.

Acceptance test:

1. A row with `source="dolci_tooluse"`, upstream `source_dataset="Dolci Instruct Tool Use"`, source ID `0`, revision and parquet locator round-trips all five identities exactly.
2. A row without `source_dataset` remains without that field.
3. The actual `assemble_mix_r2.py::to_messages` behavior remains unchanged because provenance fields are outside messages.
4. Existing long-schema/call and occupied-output tests continue to pass.

No canonical or production file was changed by this pilot.
