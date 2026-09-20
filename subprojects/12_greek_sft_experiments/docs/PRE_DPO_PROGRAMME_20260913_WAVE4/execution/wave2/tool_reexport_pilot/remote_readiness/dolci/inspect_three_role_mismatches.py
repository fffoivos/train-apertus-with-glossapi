#!/usr/bin/env python3
"""Emit the three bounded public-source turns implicated by the failed audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


TARGETS = (
    ("data/train-00013-of-00015.parquet", 136, 718),
    ("data/train-00014-of-00015.parquet", 3, 15),
    ("data/train-00014-of-00015.parquet", 72, 726),
)

parser = argparse.ArgumentParser()
parser.add_argument("--snapshot", required=True, type=Path)
args = parser.parse_args()

rows = []
for relative_path, row_group, row_in_group in TARGETS:
    table = pq.ParquetFile(args.snapshot / relative_path).read_row_group(row_group)
    row = table.slice(row_in_group, 1).to_pylist()[0]
    raw_messages = row.get("messages")
    raw_bytes = json.dumps(raw_messages, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    implicated = []
    summaries = []
    for turn_index, turn in enumerate(raw_messages or []):
        if not isinstance(turn, dict):
            summaries.append({"turn_index": turn_index, "turn_type": type(turn).__name__})
            continue
        content = turn.get("content")
        content_text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        summaries.append(
            {
                "turn_index": turn_index,
                "role": turn.get("role"),
                "content_type": type(content).__name__,
                "content_chars": len(content_text),
                "content_preview": content_text[:240],
                "tool_fields": {
                    key: turn[key]
                    for key in ("functions", "function_calls", "tool_calls", "tool_call_id", "name")
                    if key in turn and turn[key] is not None
                },
            }
        )
        if turn.get("function_calls") and turn.get("role") != "assistant":
            implicated.append({"turn_index": turn_index, "turn": turn})
    rows.append(
        {
            "source_id": row.get("id"),
            "source_locator": {
                "file": relative_path,
                "row_group": row_group,
                "row_in_group": row_in_group,
            },
            "messages_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "turn_count": len(raw_messages or []),
            "implicated_turns": implicated,
            "turn_summaries": summaries,
        }
    )

print(json.dumps({"schema_version": "dolci_three_role_mismatches_v1", "rows": rows}, ensure_ascii=False, indent=2))
