#!/usr/bin/env python3
"""Emit only aggregate schema/domain evidence; never emit row text."""
import argparse
import collections
import json
from pathlib import Path
import pyarrow.parquet as pq

ap = argparse.ArgumentParser()
ap.add_argument("--snapshot", required=True)
args = ap.parse_args()
root = Path(args.snapshot).resolve()
files = sorted((root / "data").glob("train-*.parquet"))
domains = collections.Counter()
source_datasets = collections.Counter()
rows = 0
per_file = []
for path in files:
    pf = pq.ParquetFile(path)
    names = pf.schema_arrow.names
    columns = [x for x in ("domain", "source_dataset") if x in names]
    local = collections.Counter()
    for rg in range(pf.num_row_groups):
        t = pf.read_row_group(rg, columns=columns)
        if "domain" in columns:
            vals = t.column("domain").to_pylist()
            local.update(str(x) for x in vals)
            domains.update(str(x) for x in vals)
        if "source_dataset" in columns:
            source_datasets.update(str(x) for x in t.column("source_dataset").to_pylist())
    rows += pf.metadata.num_rows
    per_file.append({"file": path.relative_to(root).as_posix(), "rows": pf.metadata.num_rows,
                     "row_groups": pf.num_row_groups, "domain_counts": dict(local)})
print(json.dumps({
    "files": len(files), "rows": rows,
    "schema_arrow": str(pq.ParquetFile(files[0]).schema_arrow),
    "schema_fields": pq.ParquetFile(files[0]).schema_arrow.names,
    "domain_counts": dict(domains),
    "source_dataset_counts": dict(source_datasets),
    "per_file": per_file,
}, ensure_ascii=False, indent=2))
