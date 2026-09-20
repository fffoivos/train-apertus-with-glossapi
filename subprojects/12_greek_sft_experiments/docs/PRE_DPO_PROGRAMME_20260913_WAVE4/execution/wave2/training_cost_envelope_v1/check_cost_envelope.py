#!/usr/bin/env python3
"""Verify the source bindings and arithmetic in receipt.json."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def d(value: object) -> Decimal:
    return Decimal(str(value))


def main() -> None:
    receipt = json.loads(
        (HERE / "receipt.json").read_text(),
        parse_float=Decimal,
        parse_int=Decimal,
    )

    for binding in receipt["source_bindings"]:
        path = ROOT / binding["path"]
        actual = sha256(path)
        assert actual == binding["sha256"], (path, actual, binding["sha256"])

    budget = receipt["budget"]
    tariff = d(budget["tariff_chf_per_node_hour"])
    used = d(budget["used_chf"])
    cap = d(budget["cap_chf"])
    headroom = cap - used
    assert headroom == d(budget["headroom_chf"])
    assert headroom / tariff == d(budget["headroom_node_hours"])

    telemetry = receipt["telemetry_anchor"]
    final_train = (
        d(telemetry["main_training_node_hours"])
        + d(telemetry["finishing_training_node_hours"])
    ) * d(telemetry["runtime_multiplier"])
    final_eval = sum(d(x) for x in telemetry["selected_candidate_eval_components_node_hours"].values()) * d(
        telemetry["runtime_multiplier"]
    )
    assert final_train == d(telemetry["reserved_final_training_node_hours"])
    assert final_eval == d(telemetry["reserved_final_evaluation_node_hours"])

    for scenario in receipt["scenarios"]:
        total = sum(d(x) for x in scenario["components_node_hours"].values())
        assert total == d(scenario["total_node_hours"])
        assert total * tariff == d(scenario["total_chf"])
        assert d(budget["headroom_node_hours"]) - total == d(scenario["remaining_node_hours"])
        assert headroom - total * tariff == d(scenario["remaining_chf"])

    assert receipt["decision"]["maximum_pair_launch_envelope_node_hours"] == 4
    print("PASS: source bindings and all cost-envelope arithmetic verified")


if __name__ == "__main__":
    main()
