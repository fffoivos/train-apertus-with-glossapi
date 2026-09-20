#!/usr/bin/env python3
"""Verify the clean active v4 envelope and its immutable-v3 lineage."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


rows = [json.loads(line) for line in (HERE / "candidates.jsonl").read_text().splitlines() if line.strip()]
assert len(rows) == 20 and len({r["row_id"] for r in rows}) == 20
for row in rows:
    assert not ({"root_revision", "source_review_v3", "v3_candidate_sha256", "v3_checker_results", "candidate_row_sha256"} & row.keys())
    assert row["current"]["version"] == 4
    assert row["current"]["candidate_row_sha256"] == sha(canonical(row["candidate_row"]))
    envelope = dict(row); stored = envelope.pop("envelope_sha256")
    assert stored == sha(canonical(envelope))
    assert row["current"]["decision"] == "accepted"
    assert row["current"]["all_checkable_pass"]

by_id = {r["row_id"]: r for r in rows}
assert by_id["mixa_2028_03200"]["current"]["changed_from_v3_candidate"] is False
assert by_id["mixa_2028_03200"]["current"]["source_review"]["adjudication"].endswith("No factual repair is warranted.")
assert by_id["mixa_2026_11688"]["candidate_row"]["assistant"].count("ψ") >= 6
assert "Αν με ρωτάτε" in by_id["mixa_2026_11688"]["candidate_row"]["assistant"]
assert "Αν με ρωτάς" in by_id["mixa_2026_11688"]["candidate_row"]["assistant"]
assert by_id["mixa_2026_06199"]["candidate_row"]["assistant"].count("*") >= 4
assert "θερμ" in by_id["mixa_2026_06199"]["candidate_row"]["assistant"].lower()

result = {
    "status": "PASS",
    "rows": 20,
    "accepted": 20,
    "held": 0,
    "changed_rows": [r["row_id"] for r in rows if r["current"]["changed_from_v3_candidate"]],
    "active_hashes_verified": 20,
    "envelope_hashes_verified": 20,
    "stale_active_v3_fields": 0,
    "checker_pass": 20,
    "production_promoted": 0,
    "model_subprocess_calls": 0,
}
(HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
