#!/usr/bin/env python3
"""Bind frozen GreekMMLU diagnostic IDs to pinned parquet content without emitting items."""
from __future__ import annotations

import argparse
import hashlib
import json
import collections
from pathlib import Path

import pyarrow.parquet as pq


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--parquet-source-path")
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    selected = [json.loads(line) for line in args.ids.read_text().split("\n") if line.strip()]
    if len(selected) != 200 or len({row["example_id"] for row in selected}) != 200:
        raise RuntimeError("frozen selection must contain exactly 200 unique example IDs")
    if len({int(row["dataset_row_index"]) for row in selected}) != 200:
        raise RuntimeError("frozen selection must contain exactly 200 unique row indices")

    table = pq.read_table(args.parquet)
    if table.num_rows != 16632:
        raise RuntimeError(f"dataset row drift: {table.num_rows}")
    required = {"question", "choices", "answer", "group", "subject", "level"}
    if set(table.column_names) != required:
        raise RuntimeError(f"dataset schema drift: {table.column_names}")
    records = table.to_pylist()

    bindings = []
    strata = set()
    choice_arities = collections.Counter()
    for selection in selected:
        index = int(selection["dataset_row_index"])
        if selection["example_id"] != f"greekmmlu:{index}":
            raise RuntimeError(f"example/index mismatch: {selection['example_id']}")
        record = records[index]
        if record["subject"] != selection["subject"] or record["level"] != selection["level"]:
            raise RuntimeError(f"selection metadata drift: {selection['example_id']}")
        if len(record["choices"]) not in {2, 3, 4} or int(record["answer"]) not in range(len(record["choices"])):
            raise RuntimeError(f"choice/answer schema drift: {selection['example_id']}")
        choice_arities[len(record["choices"])] += 1
        payload = {key: record[key] for key in sorted(required)}
        bindings.append({
            "example_id": selection["example_id"],
            "dataset_row_index": index,
            "subject": record["subject"],
            "level": record["level"],
            "content_sha256": hashlib.sha256(canonical(payload)).hexdigest(),
        })
        strata.add((record["subject"], record["level"]))

    receipt = {
        "schema_version": "greekmmlu_diagnostic200_content_binding_v1",
        "status": "passed",
        "repo_id": "dascim/GreekMMLU",
        "revision": "6a03aa06b68beb932fb75edff3a34e50b3674649",
        "config": "All",
        "split": "test",
        "parquet": {"path": args.parquet_source_path or str(args.parquet.resolve()), "local_temporary_path": str(args.parquet.resolve()) if args.parquet_source_path else None, "bytes": args.parquet.stat().st_size, "sha256": sha256(args.parquet)},
        "selection": {"path": str(args.ids.resolve()), "bytes": args.ids.stat().st_size, "sha256": sha256(args.ids)},
        "dataset_rows": table.num_rows,
        "selected_rows": len(bindings),
        "observed_subject_level_strata": len(strata),
        "selected_choice_arity_counts": {str(key): value for key, value in sorted(choice_arities.items())},
        "content_binding_rule": "SHA256 of UTF-8 canonical JSON over answer, choices, group, level, question, subject; content itself is not emitted",
        "ordered_selection_content_sha256": hashlib.sha256(canonical(bindings)).hexdigest(),
        "rows": bindings,
        "official_config_reconciliation": "pending: observed 61 subject-level strata versus 45 official task configs",
        "measurement_launched": False,
    }
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
