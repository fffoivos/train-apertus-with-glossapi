#!/usr/bin/env python3
"""Bind staged paths and a fresh live receipt; submission remains opt-in."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--template", required=True)
ap.add_argument("--canonical-root", required=True)
ap.add_argument("--live-receipt", required=True)
ap.add_argument("--approved-by", required=True)
ap.add_argument("--approved-at", required=True)
ap.add_argument("--allow-preparation-submission", action="store_true")
ap.add_argument("--output", required=True)
args = ap.parse_args()
root = Path(args.canonical_root).resolve()
sys.path.insert(0, str(root / "src"))
from apertus_cscs_campaign.receipts import file_binding, digest  # noqa: E402
from apertus_cscs_readiness.data_stage import approval_scope, validate_contract  # noqa: E402

value = json.load(open(args.template, encoding="utf-8"))
value["code_root"] = str(root)
value["live_cluster_receipt"] = file_binding(Path(args.live_receipt))
value["approval"] = {
    "approved_by": args.approved_by,
    "approved_at": args.approved_at,
    "scope_sha256": "",
    "allow_preparation_submission": args.allow_preparation_submission,
}
value["approval"]["scope_sha256"] = digest(approval_scope(value))
validate_contract(value)
path = Path(args.output)
path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
print(hashlib.sha256(path.read_bytes()).hexdigest())
