#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNNER_SHA = "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"
SOURCE_SHA = "d4f8270bd50a506ab3ef37cc0999a4babbdb283f664885694377994c7036936c"
MISSING = object()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def replay(initial: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    state = copy.deepcopy(initial)
    for event in events:
        if event["op"] == "set":
            state[event["field"]] = event["value"]
        elif event["op"] == "add":
            if isinstance(state.get(event["field"]), list):
                if event["value"] not in state[event["field"]]:
                    state[event["field"]].append(event["value"])
            else:
                state[event["field"]] = state.get(event["field"], 0) + event["value"]
        elif event["op"] == "remove":
            if isinstance(state.get(event["field"]), list):
                state[event["field"]] = [x for x in state[event["field"]] if x != event["value"]]
            else:
                state.pop(event["field"], None)
        else:
            raise AssertionError(event)
    return state


def derive(evidence: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(evidence["facts"])
    state.update(evidence.get("extra", {}))
    for formula in evidence["formulas"]:
        values = [state.get(arg) for arg in formula["args"]]
        if any(value is None for value in values):
            value = None
        elif formula["op"] == "subtract_many":
            value = values[0] - sum(values[1:])
        elif formula["op"] == "greater_than":
            value = values[0] > values[1]
        else:
            raise AssertionError(formula)
        state[formula["field"]] = value
    return state


def state_before(spec: dict[str, Any]) -> dict[str, Any]:
    if spec["oracle"]["kind"] == "version_edit":
        return replay(spec["evidence"]["initial"], spec["evidence"]["events"])
    if spec["oracle"]["kind"] == "state_inference":
        return derive(spec["evidence"])
    raise AssertionError(spec["oracle"]["kind"])


def classify(state: dict[str, Any], atoms: list[dict[str, Any]]) -> str:
    results: list[bool | None] = []
    for atom in atoms:
        actual = state.get(atom["field"], MISSING)
        results.append(None if actual is MISSING or actual is None else actual == atom["asserted"])
    if any(result is None for result in results):
        return "unresolved"
    if all(results):
        return "true"
    if not any(results):
        return "false"
    return "partial"


def state_after(state: dict[str, Any], request: dict[str, Any] | None) -> dict[str, Any]:
    if not request or request.get("ambiguous"):
        return copy.deepcopy(state)
    assert request["kind"] == "version_ops"
    return replay(state, request["ops"])


def strict_schema(schema: dict[str, Any], path: str = "$") -> None:
    if schema.get("type") == "object" or "properties" in schema:
        assert schema.get("additionalProperties") is False, path
        assert set(schema.get("required", [])) == set(schema.get("properties", {})), path
        for key, child in schema.get("properties", {}).items():
            strict_schema(child, f"{path}.{key}")
    if "items" in schema:
        strict_schema(schema["items"], path + "[]")


def strip_lineage(row: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(row)
    out.pop("preparation_lineage", None)
    return out


def main() -> None:
    assert sha(PARENT / "inputs/dev.jsonl") == SOURCE_SHA
    assert sha(HERE / "run_queue.py") == RUNNER_SHA
    assert sha(HERE / "prompts/author_dialogue.txt") == "1284d6bb4384913ad3bc49c8e30bfb6575c3b888822d173ae1e58920363f4705"
    assert sha(HERE / "prompts/greek_correction.txt") == "adf624b1eca49c415f33fa9a1f03b874d825fb6dd758c91a12224cc4f3d39929"
    assert sha(HERE / "prompts/semantic_repair.txt") == "d0a0d83e714325427d29fdbe8a76137c7822b0a23962c5ba63940172b716d7cf"
    for path in (HERE / "schemas").glob("*.json"):
        strict_schema(json.loads(path.read_text()))
    for path in (HERE / "prompts").glob("*.txt"):
        assert path.read_text().count("{{INPUT_JSON}}") == 1

    source_rows = read_jsonl(PARENT / "inputs/dev.jsonl")
    rows = read_jsonl(HERE / "inputs.jsonl")
    assert len(source_rows) == len(rows) == 8
    source_by_id = {row["row_id"]: row for row in source_rows}
    by_id = {row["row_id"]: row for row in rows}
    assert len(by_id) == 8 and set(by_id) == set(source_by_id)
    changed_ids = []
    for row_id, row in by_id.items():
        if strip_lineage(row) != source_by_id[row_id]:
            changed_ids.append(row_id)
    assert set(changed_ids) == set(source_by_id)
    coffee_context = "Στο πρόχειρο της παραγγελίας, η τρέχουσα καταχώριση είναι μεσαίος ντεκαφεϊνέ χωρίς ζάχαρη."
    library_context = "Υπάρχουν 3 αντίτυπα: 2 είναι δανεισμένα και το τρίτο δεσμευμένο."
    coffee_cores = {
        "pilot48_05_true": "Στο πρόχειρο της παραγγελίας, η καταχώριση είναι μεσαίος ντεκαφεϊνέ χωρίς ζάχαρη. Πρόσθεσε τώρα λίγο γάλα.",
        "pilot48_05_false": "Στο πρόχειρο της παραγγελίας, η τρέχουσα καταχώριση λέει κανονικός καφές, όχι ντεκαφεϊνέ. Κάν' τον τώρα κανονικό.",
        "pilot48_05_partial": "Στο πρόχειρο της παραγγελίας, η καταχώριση λέει μεγάλος καφές χωρίς ζάχαρη. Πρόσθεσε τώρα ένα νερό.",
        "pilot48_05_unresolved": "Στο πρόχειρο της παραγγελίας, κάν' τον όπως την άλλη φορά.",
    }
    for row_id, row in by_id.items():
        spec = row["scenario_spec"]
        if row_id.startswith("pilot48_05_"):
            assert spec["visible_evidence_contract"]["required_user_context_core_el"] == coffee_context
            assert spec["context_blueprint"]["evidence_summary_el"] == coffee_context
            assert spec["user_decision_semantic_content_el"] == coffee_cores[row_id]
            assert spec["action_contract"] == {"mode": "text_record_edit", "external_tool_result_supplied": False, "may_claim_external_action_success": False, "text_record_state_name": "πρόχειρο παραγγελίας"}
        else:
            assert spec["visible_evidence_contract"]["required_user_context_core_el"] == library_context
            assert spec["context_blueprint"]["evidence_summary_el"] == library_context
    assert by_id["pilot48_09_unresolved"]["scenario_spec"]["user_decision_semantic_content_el"] == "Με βάση μόνο αυτή την καταγραφή, συμπεραίνω ότι ένα αντίτυπο θα επιστραφεί την Παρασκευή."
    before = source_by_id["pilot48_05_false"]
    after = strip_lineage(by_id["pilot48_05_false"])
    assert before["scenario_spec"]["evidence"]["initial"]["coffee"] == "κανονικός"
    assert state_before(after["scenario_spec"])["coffee"] == "ντεκαφεϊνέ"
    assert after["scenario_spec"]["expected"]["response_moves"][0] == "correct_current_record_claim_briefly"
    repair_rows = read_jsonl(HERE / "source_semantic_repairs.jsonl")
    assert len(repair_rows) == 8 and {row["row_id"] for row in repair_rows} == set(by_id)
    assert all(row["model_calls"] == 0 and row["changes"] for row in repair_rows)

    labels = Counter()
    families = Counter()
    for row in rows:
        spec = row["scenario_spec"]
        state = state_before(spec)
        assert state == spec["oracle"]["state_before"], row["row_id"]
        assert classify(state, spec["claim_atoms"]) == spec["truth_category"] == spec["oracle"]["derived_truth"], row["row_id"]
        assert state_after(state, spec["current_request"]) == spec["oracle"]["state_after"], row["row_id"]
        assert spec["visible_evidence_contract"]["source_role"] == "user"
        assert spec["visible_evidence_contract"]["assistant_assertion_is_independent_evidence"] is False
        assert spec["decision_surface_contract"]["frozen_core_el"] == spec["user_decision_semantic_content_el"]
        assert row["protected"]["oracle"] == spec["oracle"]
        plan = row["message_plan"]
        assert plan["context_assistant_train"] is False
        assert plan["decision_user_train"] is False
        assert plan["target_assistant_train"] is True
        assert plan["exactly_one_supervised_assistant_turn"] is True
        labels[spec["truth_category"]] += 1
        families[row["family_id"]] += 1
    assert labels == Counter({"true": 2, "false": 2, "partial": 2, "unresolved": 2})
    assert families == Counter({"cf05_cafe_order": 4, "cf09_library_hold": 4})
    train_families = {row["family_id"] for row in read_jsonl(PARENT / "inputs/train.jsonl")}
    assert not (set(families) & train_families)

    author = read_jsonl(HERE / "queue_author8.jsonl")
    combined = read_jsonl(HERE / "queue_author8_then_greek8.jsonl")
    assert len(author) == 8 and len(combined) == 16
    assert combined[:8] == author
    assert all(job["stage"] == "dialogue_authoring" and not job["depends_on"] for job in author)
    for job in combined[8:]:
        assert job["stage"] == "greek_correction"
        assert job["depends_on"] == ["author__" + job["row_id"]]
        assert {req["field"] for req in job["dependency_requirements"]} == {"status", "checks_needed", "issues"}
    assert all(job["model"] == "gpt-5.6-sol" and job["effort"] == "high" for job in combined)

    conditional = json.loads((HERE / "conditional_calls.json").read_text())
    manifest = json.loads((HERE / "manifest.json").read_text())
    counts = manifest["counts"]
    assert counts == {"primary_authoring": 8, "greek_correction": 8, "semantic_repair_cap": 2, "retry_cap": 2, "absolute_call_cap": 20}
    assert conditional["semantic_repair"]["cap"] == conditional["retry"]["cap"] == 2
    assert manifest["cumulative_budget"]["pilot_calls_consumed_before_package"] == 68
    assert manifest["cumulative_budget"]["projected_cumulative_at_package_cap"] == 88
    assert manifest["cumulative_budget"]["global_pilot_absolute_cap"] == 118
    assert manifest["cumulative_budget"]["headroom_after_package_cap"] == 30
    assert manifest["cumulative_budget"]["no_cap_reset"] is True
    for relative, digest in manifest["artifact_sha256"].items():
        assert sha(HERE / relative) == digest, relative

    gate = json.loads((PARENT / "sealed/final_confirmation/gate_summary.json").read_text())
    assert gate["row_count"] == 8 and gate["dispatchable"] == 7 and gate["quarantined"] == 1
    assert gate["content_exposed_in_report"] is False and gate["authoring_launched"] is False
    assert not (HERE / "run_state").exists()

    result = {
        "status": "PASS_DEVELOPMENT8_PREPARATION",
        "rows": 8,
        "truth_counts": dict(labels),
        "families": dict(families),
        "oracle_recomputations": 8,
        "source_repairs": changed_ids,
        "source_repair_groups": 3,
        "author_jobs": 8,
        "greek_jobs": 8,
        "conditional_semantic_repair_cap": 2,
        "retry_cap": 2,
        "package_call_cap": 20,
        "cumulative_calls_before": 68,
        "cumulative_max_after": 88,
        "global_pilot_cap": 118,
        "max_workers": 8,
        "train_family_intersection": [],
        "final_content_materialized": False,
        "model_calls": 0,
        "launched": False,
    }
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
