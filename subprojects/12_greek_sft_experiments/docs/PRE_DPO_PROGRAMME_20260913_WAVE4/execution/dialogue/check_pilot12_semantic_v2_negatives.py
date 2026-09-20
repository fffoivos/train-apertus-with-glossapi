#!/usr/bin/env python3
"""Exercise the original pilot verifier against deliberate semantic-v2 defects."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot12_verifier", HERE / "pilot12_verifier.py")
verifier = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verifier)


def verify_row(row: dict) -> None:
    verifier.verify_structure(row)
    facts = verifier.derived_facts(row)
    computed = verifier.truth_from_evidence(row, facts)
    assert computed == row["decisions"][0]["truth_category"]
    assert row["scenario_spec"]["truth_class"] == computed
    verifier.verify_special_evidence(row, facts)
    verifier.verify_outcome(row, facts)


def caught(row: dict) -> bool:
    try:
        verify_row(row)
    except AssertionError:
        return True
    return False


def main() -> None:
    rows = {
        row["row_id"]: row
        for row in (json.loads(line) for line in (HERE / "pilot12_semantic_v2.jsonl").read_text().splitlines() if line.strip())
    }

    wrong_category = copy.deepcopy(rows["corrv2_u_001"])
    wrong_category["decisions"][0]["truth_category"] = "false"

    unsupported_refusal = copy.deepcopy(rows["corrv2_u_003"])
    next(message for message in unsupported_refusal["messages"] if message["id"] == "u003_a2")["content"] = "Δεν μπορώ να βοηθήσω."

    unsupported_acceptance = copy.deepcopy(rows["corrv2_u_003"])
    next(message for message in unsupported_acceptance["messages"] if message["id"] == "u003_a2")["content"] = (
        "Η αναχώρηση έχει οριστεί από την Αθήνα με προορισμό το Ναύπλιο. Θέλεις να συνεχίσουμε;"
    )

    result = {
        "wrong_category_caught": caught(wrong_category),
        "unsupported_refusal_caught": caught(unsupported_refusal),
        "unsupported_acceptance_with_incidental_question_caught": caught(unsupported_acceptance),
    }
    assert result["wrong_category_caught"] is True
    assert result["unsupported_refusal_caught"] is True
    assert result["unsupported_acceptance_with_incidental_question_caught"] is False
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
