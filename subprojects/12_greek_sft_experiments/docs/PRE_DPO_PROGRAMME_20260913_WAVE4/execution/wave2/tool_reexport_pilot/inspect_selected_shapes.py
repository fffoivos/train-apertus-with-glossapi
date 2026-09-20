#!/usr/bin/env python3
"""Read the first bounded Tool Use rows per source shard; emit no row text."""
import argparse
import ast
import collections
import json
from pathlib import Path
import pyarrow.parquet as pq

ap = argparse.ArgumentParser()
ap.add_argument("--snapshot", required=True)
ap.add_argument("--per-shard", type=int, default=4)
args = ap.parse_args()
root = Path(args.snapshot).resolve()

rows = []
for path in sorted((root / "data").glob("train-*.parquet")):
    rel = path.relative_to(root).as_posix()
    pf = pq.ParquetFile(path)
    kept = 0
    for rg in range(pf.num_row_groups):
        if kept >= args.per_shard:
            break
        table = pf.read_row_group(rg)
        for ri, row in enumerate(table.to_pylist()):
            if row["domain"] != "Tool Use":
                continue
            turn_shapes = []
            for turn in row["messages"]:
                shape = {
                    "role": turn.get("role"),
                    "content_type": type(turn.get("content")).__name__,
                    "content_chars": len(turn.get("content") or ""),
                    "nonnull_native_fields": sorted(k for k, v in turn.items() if v is not None),
                }
                for field in ("functions", "function_calls"):
                    value = turn.get(field)
                    if value is None:
                        continue
                    facts = {
                        "storage_type": type(value).__name__,
                        "chars": len(value),
                    }
                    try:
                        parsed = json.loads(value)
                        facts.update({
                            "json_parseable": True,
                            "json_type": type(parsed).__name__,
                            "items": len(parsed) if isinstance(parsed, list) else None,
                            "item_key_sets": sorted({tuple(sorted(y)) for y in parsed if isinstance(y, dict)}) if isinstance(parsed, list) else [],
                        })
                    except (json.JSONDecodeError, TypeError):
                        facts["json_parseable"] = False
                        try:
                            tree = ast.parse(value, mode="eval")
                            body = tree.body
                            calls = list(body.elts) if isinstance(body, (ast.List, ast.Tuple)) else [body]
                            facts["python_call_parseable"] = all(isinstance(c, ast.Call) for c in calls)
                            facts["python_call_count"] = len(calls)
                            facts["python_positional_counts"] = [len(c.args) for c in calls if isinstance(c, ast.Call)]
                            facts["python_keyword_name_sets"] = [sorted(k.arg or "**" for k in c.keywords) for c in calls if isinstance(c, ast.Call)]
                        except SyntaxError:
                            try:
                                tree = ast.parse(value, mode="exec")
                                calls = [x.value for x in tree.body if isinstance(x, ast.Expr)]
                                facts["python_call_parseable"] = bool(calls) and len(calls) == len(tree.body) and all(isinstance(c, ast.Call) for c in calls)
                                facts["python_call_count"] = len(calls)
                                facts["python_positional_counts"] = [len(c.args) for c in calls if isinstance(c, ast.Call)]
                                facts["python_keyword_name_sets"] = [sorted(k.arg or "**" for k in c.keywords) for c in calls if isinstance(c, ast.Call)]
                            except SyntaxError:
                                facts["python_call_parseable"] = False
                    shape[field] = facts
                turn_shapes.append(shape)
            rows.append({
                "source_locator": {"file": rel, "row_group": rg, "row_in_group": ri},
                "turn_count": len(row["messages"]),
                "turn_shapes": turn_shapes,
            })
            kept += 1
            if kept >= args.per_shard:
                break
print(json.dumps({
    "schema_version": "dolci_tool_selected_shape_probe_v1",
    "sample_rows": len(rows),
    "selection": f"first {args.per_shard} Tool Use rows encountered per source shard",
    "content_redacted": True,
    "rows": rows,
}, ensure_ascii=False, indent=2))
