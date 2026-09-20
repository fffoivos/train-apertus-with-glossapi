#!/usr/bin/env python3
"""Publish revision 2 without changing the frozen revision-1 artifacts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent
rows = [json.loads(line) for line in (V1 / "pilot48_input_specs.jsonl").read_text().splitlines() if line.strip()]
assert len(rows) == 48

for row in rows:
    if row["family_id"] == "cf05_cafe_order":
        row["split"] = "dev"
    elif row["family_id"] == "cf10_reminder_cancel":
        row["split"] = "train"

with (HERE / "pilot48_input_specs.jsonl").open("w") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

families = {}
for row in rows:
    families.setdefault(row["family_id"], {
        "family_id": row["family_id"], "split": row["split"], "oracle_kind": row["oracle"]["kind"],
        "skill": row["skill"], "setting": row["setting"],
    })
    assert families[row["family_id"]]["split"] == row["split"]

scale_splits = {
    "train": {"families": 200, "four_label_families": 100, "true_false_only_families": 100,
              "decisions": {"true": 200, "false": 200, "partial": 100, "unresolved": 100, "total": 600}},
    "dev": {"families": 20, "four_label_families": 10, "true_false_only_families": 10,
            "decisions": {"true": 20, "false": 20, "partial": 10, "unresolved": 10, "total": 60}},
    "final_confirmation": {"families": 20, "four_label_families": 10, "true_false_only_families": 10,
                           "decisions": {"true": 20, "false": 20, "partial": 10, "unresolved": 10, "total": 60}},
}
manifest = {
    "name": "correcting_dialogue_family_split_v2",
    "published_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "supersedes_for_planning": str(V1 / "family_split_manifest.json"),
    "count_unit": "labelled assistant decision",
    "pilot": {
        "decisions": 48,
        "truth_counts": dict(Counter(r["truth_category"] for r in rows)),
        "families": 12,
        "split_decisions": dict(Counter(r["split"] for r in rows)),
        "train_skill_coverage": sorted({r["skill"] for r in rows if r["split"] == "train"}),
        "split_revision": {"cf05_cafe_order": "train_to_dev", "cf10_reminder_cancel": "dev_to_train"},
    },
    "program_total": {
        "decisions": 720,
        "families": 240,
        "truth_counts": {"true": 240, "false": 240, "partial": 120, "unresolved": 120},
    },
    "training_target": {
        "decisions": 600,
        "truth_counts": {"true": 200, "false": 200, "partial": 100, "unresolved": 100},
        "families": 200,
        "four_label_families": 100,
        "true_false_only_families": 100,
    },
    "holdout_targets": {
        "dev": {"decisions": 60, "families": 20},
        "final_confirmation": {"decisions": 60, "families": 20},
    },
    "split_plan": scale_splits,
    "pilot_families": list(families.values()),
    "remaining_family_slots": {
        "train": {"four_label": 92, "true_false_only": 100},
        "dev": {"four_label": 8, "true_false_only": 10},
        "final_confirmation": {"four_label": 8, "true_false_only": 10},
    },
    "leakage_rules": [
        "family_id belongs to exactly one split",
        "same entities, state graph, evidence table, paraphrase, or numeric template remain in that split",
        "no public benchmark-derived prompts or lightly paraphrased benchmark tasks",
        "final_confirmation families are sealed after specification and cannot guide prompt tuning",
        "decision totals are counted from supervised labelled assistant decisions, never conversations or raw turns",
    ],
    "authoring_boundary": "Specifications alone are not quality-ready for scale. The active goal authorizes later scaling after the stated semantic, Greek, oracle, masking, and leakage gates pass.",
}
(HERE / "family_split_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

receipt = {
    "status": "PASS",
    "pilot_decisions": len(rows),
    "pilot_split_decisions": dict(Counter(r["split"] for r in rows)),
    "program_total_decisions": 720,
    "training_decisions": 600,
    "dev_decisions": 60,
    "final_confirmation_decisions": 60,
    "source_v1_manifest_sha256": hashlib.sha256((V1 / "family_split_manifest.json").read_bytes()).hexdigest(),
    "source_v1_specs_sha256": hashlib.sha256((V1 / "pilot48_input_specs.jsonl").read_bytes()).hexdigest(),
    "manifest_sha256": hashlib.sha256((HERE / "family_split_manifest.json").read_bytes()).hexdigest(),
    "specs_sha256": hashlib.sha256((HERE / "pilot48_input_specs.jsonl").read_bytes()).hexdigest(),
    "model_subprocess_calls": 0,
    "production_writes": 0,
}
(HERE / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
