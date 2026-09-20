#!/usr/bin/env python3
"""Read-only Dolci parquet inventory and deterministic 200-row locator freeze."""
import argparse
import hashlib
import heapq
import json
from pathlib import Path

import pyarrow.parquet as pq


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def row_key(revision, relpath, row_group, row_in_group, source_id):
    material = "\0".join([
        revision, relpath, str(row_group), str(row_in_group),
        f"{type(source_id).__name__}:{canonical(source_id)}",
    ])
    return hashlib.sha256(material.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--target", type=int, default=200)
    args = ap.parse_args()
    if len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
        raise SystemExit("revision must be 40 lowercase hex characters")
    root = Path(args.snapshot).resolve()
    files = sorted((root / "data").glob("train-*.parquet"))
    if not files:
        raise SystemExit("no train parquet files")
    summaries, selected = [], []
    schema_text = None
    schema_fields = None
    match_counts = {}
    for path in files:
        pf = pq.ParquetFile(path)
        rel = path.relative_to(root).as_posix()
        if schema_text is None:
            schema_text = str(pf.schema_arrow)
            schema_fields = pf.schema_arrow.names
        matches = 0
        for rg in range(pf.num_row_groups):
            table = pf.read_row_group(rg, columns=["domain"])
            domains = table.column("domain").to_pylist()
            matches += sum(x == "Tool Use" for x in domains)
        match_counts[path] = matches
        summaries.append({
            "file": rel,
            "resolved_bytes": path.stat().st_size,
            "row_groups": pf.num_row_groups,
            "rows": pf.metadata.num_rows,
            "tool_use_rows": matches,
            "selected": 0,
        })
    active = [p for p in files if match_counts[p]]
    if not active:
        raise SystemExit("no Tool Use rows")
    base, rem = divmod(args.target, len(active))
    quotas = {p: base + (i < rem) for i, p in enumerate(active)}
    summary_by_path = {root / x["file"]: x for x in summaries}
    for path in active:
        pf = pq.ParquetFile(path)
        rel = path.relative_to(root).as_posix()
        id_col = "id" if "id" in pf.schema_arrow.names else ("conversation_id" if "conversation_id" in pf.schema_arrow.names else None)
        columns = ["domain"] + ([id_col] if id_col else [])
        quota = quotas[path]
        heap = []
        for rg in range(pf.num_row_groups):
            table = pf.read_row_group(rg, columns=columns)
            domains = table.column("domain").to_pylist()
            ids = table.column(id_col).to_pylist() if id_col else [None] * len(domains)
            for ri, (domain, source_id) in enumerate(zip(domains, ids)):
                if domain != "Tool Use":
                    continue
                fallback = f"{rel}:rg{rg}:row{ri}"
                actual_id = source_id if source_id is not None and source_id != "" else fallback
                key = row_key(args.revision, rel, rg, ri, actual_id)
                item = (-int(key, 16), key, rg, ri, actual_id)
                if len(heap) < quota:
                    heapq.heappush(heap, item)
                elif item[0] > heap[0][0]:
                    heapq.heapreplace(heap, item)
        if len(heap) != quota:
            raise SystemExit(f"{rel}: selected {len(heap)} but quota is {quota}")
        summary_by_path[path]["selected"] = quota
        picks = sorted(heap, key=lambda x: x[1])
        selected.extend({
            "source_revision": args.revision,
            "source_locator": {"file": rel, "row_group": rg, "row_in_group": ri},
            "source_id": source_id,
            "selection_sha256": key,
            "stratum": rel,
        } for _, key, rg, ri, source_id in picks)
    selected.sort(key=lambda x: (x["stratum"], x["selection_sha256"]))
    payload = {
        "schema_version": "dolci_tool200_source_inventory_v1",
        "source_dataset": "allenai/Dolci-Instruct-SFT",
        "source_revision": args.revision,
        "source_snapshot": str(root),
        "selection_method": "per-shard minimum SHA-256 over revision, locator, and typed source id",
        "target": args.target,
        "files": summaries,
        "schema_fields": schema_fields,
        "schema_arrow": schema_text,
        "selected": selected,
    }
    payload["selected_locator_sha256"] = hashlib.sha256(canonical(selected).encode()).hexdigest()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
