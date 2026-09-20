#!/usr/bin/env python3
"""Verify exhaustive dispositions and materialize the root-selected pilot rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    queue_path = HERE / "proof_review_queue.v1.jsonl"
    review_path = HERE / "root_proof_review_v1.json"
    rows = [json.loads(line) for line in queue_path.read_text().splitlines() if line]
    review = json.loads(review_path.read_text())
    by_id = {row["id"]: row for row in rows}
    selected_ids = review["selected_ids"]
    nonselected = review["nonselected"]
    assert len(by_id) == len(rows) == 44
    assert len(selected_ids) == len(set(selected_ids)) == 27
    assert set(selected_ids).isdisjoint(nonselected)
    assert set(selected_ids) | set(nonselected) == set(by_id)

    selected = [by_id[row_id] for row_id in selected_ids]
    family_counts = Counter(row["family_sha256"] for row in selected)
    assert max(family_counts.values()) == 1
    assert len(family_counts) == review["family_status"]["selected_sound_families"] == 27

    output_path = HERE / "root_selected_sound.v1.jsonl"
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected)
    )
    receipt = {
        "schema": "openmath_root_proof_review_receipt_v1",
        "status": "root_review_complete_independent_review_pending",
        "inputs": {
            queue_path.name: sha256(queue_path),
            review_path.name: sha256(review_path),
        },
        "reviewed_rows": len(rows),
        "reviewed_families": len({row["family_sha256"] for row in rows}),
        "root_selected_rows": len(selected),
        "root_selected_families": len(family_counts),
        "nonselected_rows": len(nonselected),
        "reason_classes": dict(Counter(reason.split(";", 1)[0] for reason in nonselected.values())),
        "output": {output_path.name: sha256(output_path)},
        "training_eligible": False,
        "remaining_gates": [
            "independent proof review of all root selections and rejected/repair dispositions",
            "repair or hold the eight unselected families without expanding the source",
            "Greek adaptation decision and review for selected competition rows",
            "actual tokenizer length and target-mask checks",
            "equal-supervised-token arm assembly and full decontamination"
        ]
    }
    receipt_path = HERE / "root_proof_review_receipt.v1.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
