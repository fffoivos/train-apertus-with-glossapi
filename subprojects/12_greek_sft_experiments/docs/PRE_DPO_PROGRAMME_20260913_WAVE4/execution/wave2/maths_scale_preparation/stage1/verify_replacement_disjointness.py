#!/usr/bin/env python3
"""Verify four phase-B replacement families against every frozen/exposed family set."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


splits_path = PARENT / "proposed_family_splits.jsonl"
inventory_path = PARENT / "math7500_family_inventory.jsonl"
delta_path = ROOT / "phaseB_selection_delta.jsonl"
splits = load_jsonl(splits_path)
inventory = load_jsonl(inventory_path)
deltas = load_jsonl(delta_path)
replacements = {x["new"]["family_id"] for x in deltas}

sets = {
    "all_original_frozen_split_options": {x["family_id"] for x in splits},
    "frozen_train_stage2": {x["family_id"] for x in splits if x["lane"] == "train_stage2"},
    "frozen_development": {x["family_id"] for x in splits if x["lane"] == "development"},
    "frozen_final_confirmation": {x["family_id"] for x in splits if x["lane"] == "final_confirmation"},
    "maths_generation_pilot": {x["family_id"] for x in inventory if x["pilot"]},
    "current_gradient_train": {x["family_id"] for x in inventory if x["current_assembly"]["appeared_in_gradient_train"]},
    "current_development": {x["family_id"] for x in inventory if x["current_assembly"]["appeared_in_development"]},
    "current_assembly_exclusions": {x["family_id"] for x in inventory if x["current_assembly"]["assembly_excluded_rows"]},
}
intersections = {name: sorted(replacements & values) for name, values in sets.items()}
checks = {
    "four_unique_replacements": len(deltas) == len(replacements) == 4,
    "same_subject_and_level": all(x["old"]["subject"] == x["new"]["subject"] and x["old"]["level"] == x["new"]["level"] for x in deltas),
    "disjoint_from_every_enumerated_set": all(not values for values in intersections.values()),
    "math500_gate_pass": all(not next(x for x in inventory if x["family_id"] == rid)["math500_gate"]["reject"] for rid in replacements),
    "not_cut2_historical_candidate": all(not next(x for x in inventory if x["family_id"] == rid)["cut2"]["candidate_ids"] for rid in replacements),
}
receipt = {
    "verified_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "ok": all(checks.values()),
    "scope": "four train-only phase-B same-cell replacements",
    "source_hashes": {
        "proposed_family_splits.jsonl": sha(splits_path),
        "math7500_family_inventory.jsonl": sha(inventory_path),
        "phaseB_selection_delta.jsonl": sha(delta_path),
    },
    "replacement_family_ids": sorted(replacements),
    "enumerated_set_counts": {name: len(values) for name, values in sets.items()},
    "intersections": intersections,
    "checks": checks,
    "boundary": "Exact normalized MATH-family lineage only; this does not prove checkpoint-unseen status outside enumerated sources.",
}
(ROOT / "replacement_disjointness_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
raise SystemExit(0 if receipt["ok"] else 1)
