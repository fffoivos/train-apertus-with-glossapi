#!/usr/bin/env python3
"""Validate the remote OpenMath pilot and prepare a proof-review queue."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROWS = HERE / "candidate_rows.remote.jsonl"
INVENTORY = HERE / "eligible_family_inventory.remote.jsonl"
REMOTE_RECEIPT = HERE / "openmath.remote.receipt.json"
VALID_LEVELS = {f"Level {i}" for i in range(1, 6)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def main() -> None:
    receipt = json.loads(REMOTE_RECEIPT.read_text())
    assert sha256(ROWS) == receipt["files"]["candidate_rows.jsonl"]
    assert sha256(INVENTORY) == receipt["files"]["eligible_family_inventory.jsonl"]
    assert receipt["status"] == "passed"

    rows = load_jsonl(ROWS)
    inventory = load_jsonl(INVENTORY)
    assert len(rows) == receipt["pilot_rows"] == 45
    assert len({row["family_sha256"] for row in rows}) == receipt["pilot_families"] == 36
    assert len(inventory) == receipt["eligible_families"] == 3996
    assert len({row["family_sha256"] for row in inventory}) == len(inventory)
    assert len({row["id"] for row in rows}) == len(rows)

    review: list[dict] = []
    quarantine: list[dict] = []
    for row in rows:
        assert row["status"] == "unreviewed_source_candidate"
        assert [message["role"] for message in row["messages"]] == ["user", "assistant"]
        assert all(message["content"].strip() for message in row["messages"])
        assert row["expected_answer"] not in (None, "")
        assert row["solution_sha256"] == hashlib.sha256(row["messages"][1]["content"].encode()).hexdigest()
        assert not any(
            (ord(char) < 32 and char not in "\t\n\r") or ord(char) == 127
            for message in row["messages"]
            for char in message["content"]
        )
        if row["level"] not in VALID_LEVELS:
            quarantine.append(
                {
                    "id": row["id"],
                    "family_sha256": row["family_sha256"],
                    "subject": row["subject"],
                    "level": row["level"],
                    "disposition": "quarantine_unknown_difficulty_before_semantic_review"
                }
            )
        else:
            review.append(row)

    assert len(review) == 44
    assert len({row["family_sha256"] for row in review}) == 35
    assert len(quarantine) == 1
    dump_jsonl(HERE / "proof_review_queue.v1.jsonl", review)
    dump_jsonl(HERE / "quarantine.v1.jsonl", quarantine)

    verification = {
        "schema": "openmath_pilot_local_intake_v1",
        "status": "structure_pass_semantic_review_pending",
        "source_files": {
            ROWS.name: sha256(ROWS),
            INVENTORY.name: sha256(INVENTORY),
            REMOTE_RECEIPT.name: sha256(REMOTE_RECEIPT),
        },
        "remote_receipt_status": receipt["status"],
        "eligible_inventory_families": len(inventory),
        "pilot_rows": len(rows),
        "pilot_families": len({row["family_sha256"] for row in rows}),
        "proof_review_rows": len(review),
        "proof_review_families": len({row["family_sha256"] for row in review}),
        "quarantined_rows": len(quarantine),
        "quarantine_reason_counts": dict(Counter(row["disposition"] for row in quarantine)),
        "outputs": {
            "proof_review_queue.v1.jsonl": sha256(HERE / "proof_review_queue.v1.jsonl"),
            "quarantine.v1.jsonl": sha256(HERE / "quarantine.v1.jsonl"),
        },
        "training_eligible": False,
        "remaining_gates": [
            "complete derivation and expected-answer review for every queued solution",
            "select the equal-supervised-token competition allocation",
            "actual reader tokenizer length and target-mask verification",
            "family-disjoint development/final and complete assembly decontamination",
            "matched two-arm manifests and canonical-runner cost receipt"
        ]
    }
    (HERE / "local_intake_verification.v1.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
