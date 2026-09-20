#!/usr/bin/env python3
"""Locate role/tag mismatches in the frozen Dolci selection without emitting content."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq


parser = argparse.ArgumentParser()
parser.add_argument("--inventory", required=True, type=Path)
parser.add_argument("--snapshot", required=True, type=Path)
args = parser.parse_args()

inventory = json.loads(args.inventory.read_text())
selected_by_group: dict[tuple[str, int], list[tuple[int, dict]]] = defaultdict(list)
for ordinal, selected in enumerate(inventory["selected"]):
    locator = selected["source_locator"]
    selected_by_group[(locator["file"], locator["row_group"])].append((ordinal, selected))

role_field_counts: Counter[tuple[str, str]] = Counter()
issues = []
rows_read = 0
for (relative_path, row_group), selections in selected_by_group.items():
    table = pq.ParquetFile(args.snapshot / relative_path).read_row_group(row_group)
    for ordinal, selected in selections:
        locator = selected["source_locator"]
        row = table.slice(locator["row_in_group"], 1).to_pylist()[0]
        rows_read += 1
        for turn_index, turn in enumerate(row.get("messages") or []):
            if not isinstance(turn, dict):
                continue
            role = str(turn.get("role"))
            for field in ("functions", "function_calls", "tool_calls", "tool_call_id", "name"):
                if field in turn and turn[field] is not None:
                    role_field_counts[(role, field)] += 1
            if turn.get("function_calls") and role != "assistant":
                value = turn["function_calls"]
                issues.append(
                    {
                        "ordinal": ordinal,
                        "source_id_type": type(row.get("id")).__name__,
                        "source_id": row.get("id"),
                        "source_locator": locator,
                        "turn_index": turn_index,
                        "role": role,
                        "field": "function_calls",
                        "value_type": type(value).__name__,
                        "value_length": len(value) if hasattr(value, "__len__") else None,
                        "export_rule_renders_tag": False,
                        "audit_rule_attempts_tag_parse": True,
                    }
                )

result = {
    "schema_version": "dolci_function_call_role_diagnostic_v1",
    "selected_rows_read": rows_read,
    "role_field_counts": [
        {"role": role, "field": field, "count": count}
        for (role, field), count in sorted(role_field_counts.items())
    ],
    "mismatch_count": len(issues),
    "first_failure_in_frozen_order": min(issues, key=lambda row: (row["ordinal"], row["turn_index"])) if issues else None,
    "mismatches": sorted(issues, key=lambda row: (row["ordinal"], row["turn_index"])),
    "content_emitted": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
