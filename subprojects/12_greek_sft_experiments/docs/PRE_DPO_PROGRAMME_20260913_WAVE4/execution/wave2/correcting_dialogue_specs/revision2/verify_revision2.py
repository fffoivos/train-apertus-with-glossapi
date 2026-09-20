#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / "pilot48_input_specs.jsonl").read_text().splitlines() if line.strip()]
manifest = json.loads((HERE / "family_split_manifest.json").read_text())
assert len(rows) == 48
assert Counter(r["truth_category"] for r in rows) == Counter({"true":12,"false":12,"partial":12,"unresolved":12})
assert Counter(r["split"] for r in rows) == Counter({"train":32,"dev":8,"final_confirmation":8})
family_splits = defaultdict(set)
for row in rows: family_splits[row["family_id"]].add(row["split"])
assert all(len(v) == 1 for v in family_splits.values())
assert family_splits["cf05_cafe_order"] == {"dev"}
assert family_splits["cf10_reminder_cancel"] == {"train"}
assert {r["oracle"]["kind"] for r in rows if r["split"] == "train"} == {"version_edit", "state_inference", "cancellation"}

plan = manifest["split_plan"]
assert plan["train"]["decisions"] == {"true":200,"false":200,"partial":100,"unresolved":100,"total":600}
assert plan["dev"]["decisions"]["total"] == 60
assert plan["final_confirmation"]["decisions"]["total"] == 60
assert sum(v["decisions"]["total"] for v in plan.values()) == manifest["program_total"]["decisions"] == 720
assert sum(v["families"] for v in plan.values()) == manifest["program_total"]["families"] == 240
assert manifest["authoring_boundary"].startswith("Specifications alone are not quality-ready for scale.")

result = {"status":"PASS","pilot_decisions":48,"pilot_splits":{"train":32,"dev":8,"final_confirmation":8},"train_oracle_kinds":["cancellation","state_inference","version_edit"],"training_target":600,"holdouts":120,"program_total":720,"family_leakage":False}
(HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
