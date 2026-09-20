#!/usr/bin/env python3
"""Build the narrow Greek-correction artifact from the frozen 12-row pilot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pilot12_candidate.jsonl"
OUTPUT = HERE / "pilot12_correction_candidates.jsonl"
EXPECTED_SHA256 = "7cadb839631d7646da8d4e430484e445d2e82acc6200312fa8da5f8cdc053dfe"

SEMANTIC_FLAGS = {
    "corrv2_u_001": [
        {
            "code": "visible_history_misclassified_unresolved",
            "turn_id": "u001_u2",
            "reason": (
                "The serialized prior turns contain no room, so the historical "
                "claim is false in the visible dialogue rather than unresolved."
            ),
        }
    ],
    "corrv2_u_003": [
        {
            "code": "history_and_current_update_conflated",
            "turn_id": "u003_a2",
            "reason": (
                "The user both makes a false historical attribution and supplies "
                "Athens as current information with an explicit instruction to proceed; "
                "the target asks again and leaves the request unanswered."
            ),
        }
    ],
}


def main() -> None:
    raw = SOURCE.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"frozen source hash mismatch: {actual}")

    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if len(rows) != 12:
        raise SystemExit(f"expected 12 rows, found {len(rows)}")

    rendered = []
    for row in rows:
        flags = SEMANTIC_FLAGS.get(row["row_id"], [])
        row["status"] = "needs_semantic_review" if flags else "unchanged"
        row["changes"] = []
        row["semantic_flags"] = flags
        rendered.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    OUTPUT.write_text("\n".join(rendered) + "\n")


if __name__ == "__main__":
    main()
