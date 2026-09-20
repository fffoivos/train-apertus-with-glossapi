#!/usr/bin/env python3
"""Allocation-free result gate for the two-model fixed GreekMMLU diagnostic."""
import argparse, hashlib, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--ids", type=Path, required=True)
parser.add_argument("--original", type=Path, required=True)
parser.add_argument("--g3f2p1", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists(): raise FileExistsError(args.output)
expected = [json.loads(line)["example_id"] for line in args.ids.read_text().split("\n") if line.strip()]
if len(expected) != 200 or len(set(expected)) != 200: raise ValueError("ID gate")
summary = {}
for label, path in (("original_krikri", args.original), ("G3F2P1", args.g3f2p1)):
    payload = json.loads(path.read_text())
    rows = payload["rows"]
    ids = [row["example_id"] for row in rows]
    if payload["model_label"] != label or ids != expected or len(set(ids)) != 200:
        raise ValueError(f"identity/order gate: {label}")
    if any(row[key]["input_truncated"] for row in rows for key in ("custom_full_text", "official_label")):
        raise ValueError(f"unexpected input truncation: {label}")
    for row in rows:
        if set(row) < {"custom_full_text", "official_label"}: raise ValueError("protocol missing")
        for key in ("custom_full_text", "official_label"):
            protocol = row[key]
            if len(protocol["choice_scores"]) != row["num_choices"]: raise ValueError("choice-score count")
    summary[label] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "items": 200,
                      "accuracy": payload["accuracy"], "protocol_disagreements": payload["protocol_disagreements"]}
receipt = {"schema_version": "greekmmlu200_dual_protocol_verification_v1", "status": "passed",
           "selection_sha256": hashlib.sha256(args.ids.read_bytes()).hexdigest(), "models": summary,
           "interpretation": "Paired fixed200 diagnostic only; not an official full-suite reproduction."}
args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
