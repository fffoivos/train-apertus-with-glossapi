#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PILOT = ROOT.parent / "balanced_dialogue_pilot/revision2"
MISSING = object()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version(initial: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    state = copy.deepcopy(initial)
    for event in events:
        op, field, value = event["op"], event["field"], event["value"]
        if op == "set":
            state[field] = value
        elif op == "add_unique":
            state.setdefault(field, [])
            if value not in state[field]:
                state[field].append(value)
        elif op == "move_to_end":
            state[field] = [x for x in state[field] if x != value] + [value]
        elif op == "move_to_start":
            state[field] = [value] + [x for x in state[field] if x != value]
        else:
            raise AssertionError(event)
    return state


def derive(kind: str, evidence: dict[str, Any]) -> dict[str, Any]:
    if kind == "version_edit":
        return version(evidence["initial"], evidence.get("events", []))
    if kind == "cancellation":
        return copy.deepcopy(evidence["entries"])
    if kind == "speaker_ownership":
        state = {item["proposition"]: item["speaker"] for item in evidence["statements"]}
        state.update(evidence.get("missing", {}))
        return state
    if kind == "rule_inference":
        state = copy.deepcopy(evidence.get("known", {}))
        for rule in evidence["rules"]:
            if all(evidence["entity"].get(key) == value for key, value in rule["when"].items()):
                state[rule["field"]] = rule["value"]
        state.update(evidence.get("missing", {}))
        return state
    if kind == "graph_inference":
        state = copy.deepcopy(evidence["facts"])
        edges = [tuple(edge) for edge in evidence["edges"]]
        for query in evidence["queries"]:
            start, goal = query["from"], query["to"]
            state[query["direct_field"]] = (start, goal) in edges or (goal, start) in edges
            seen, todo = {start}, [start]
            while todo:
                node = todo.pop()
                for left, right in edges:
                    nxt = right if left == node else left if right == node else None
                    if nxt is not None and nxt not in seen:
                        seen.add(nxt)
                        todo.append(nxt)
            state[query["reachable_field"]] = goal in seen
        return state
    assert kind == "state_inference"
    state = copy.deepcopy(evidence["facts"])
    state.update(evidence.get("constants", {}))
    for formula in evidence["formulas"]:
        if formula["op"] == "subtract_many":
            state[formula["field"]] = state[formula["args"][0]] - sum(state[arg] for arg in formula["args"][1:])
        elif formula["op"] == "greater_than":
            state[formula["field"]] = state[formula["args"][0]] > state[formula["args"][1]]
        elif formula["op"] == "weighted_sum":
            state[formula["field"]] = sum(state[name] * weight for name, weight in formula["terms"])
        else:
            raise AssertionError(formula)
    return state


def classify(state: dict[str, Any], claims: list[dict[str, Any]]) -> str:
    values: list[bool | None] = []
    for claim in claims:
        actual = state.get(claim["field"], MISSING)
        if actual is MISSING or actual is None:
            values.append(None)
        elif claim.get("op", "equals") == "last_equals":
            values.append(bool(actual) and actual[-1] == claim["asserted"])
        else:
            values.append(actual == claim["asserted"])
    if any(value is None for value in values):
        return "unresolved"
    if all(values):
        return "true"
    if not any(values):
        return "false"
    return "partial"


def apply(state: dict[str, Any], request: dict[str, Any] | None) -> dict[str, Any]:
    result = copy.deepcopy(state)
    if not request or request.get("ambiguous") or request["kind"] == "respond_only":
        return result
    if request["kind"] == "version_ops":
        return version(result, request["ops"])
    if request["kind"] == "cancel":
        result[request["target"]] = "cancelled"
        return result
    if request["kind"] == "stop":
        result[request["target"]] = "stopped"
        return result
    raise AssertionError(request)


def main() -> None:
    rows = read_jsonl(ROOT / "specs.jsonl")
    families = read_jsonl(ROOT / "family_manifest.jsonl")
    receipts = read_jsonl(ROOT / "oracle_receipts.jsonl")
    assert len(rows) == len(receipts) == 60 and len(families) == 20
    assert len({row["row_id"] for row in rows}) == 60
    assert len({row["family_id"] for row in rows}) == 20
    assert len({family["structure_signature"] for family in families}) == 20
    assert Counter(family["decision_count"] for family in families) == Counter({4: 10, 2: 10})
    label_counts = Counter(row["scenario_spec"]["truth_category"] for row in rows)
    assert label_counts == Counter({"true": 20, "false": 20, "partial": 10, "unresolved": 10})
    tone_counts = Counter(row["scenario_spec"]["tone"] for row in rows)
    assert tone_counts == Counter({"cooperative": 15, "neutral": 15, "assertive": 15, "frustrated_but_civil": 15})

    receipt_by_id = {receipt["row_id"]: receipt for receipt in receipts}
    inference_prefixes = ("Άρα ", "Με βάση ", "Από αυτή ", "Στο ", "Στην ", "Στις ", "Με τον ", "Με τους ")
    oracle_kinds = Counter()
    action_changes = 0
    for row in rows:
        assert row["split"] == row["protected"]["split"] == row["scenario_spec"]["split"] == "train"
        assert row["operation"] == "prospective_authoring"
        assert row["lineage"]["public_benchmark_derived"] is False
        assert row["lineage"]["authored_target_exists"] is False
        spec, protected, plan = row["scenario_spec"], row["protected"], row["message_plan"]
        assert spec["expected"]["generation_status"] == "prospective_not_authored"
        assert spec["decision_surface_contract"]["frozen_core_el"] == spec["user_decision_semantic_content_el"]
        assert spec["visible_evidence_contract"]["required_user_context_core_el"]
        assert spec["visible_evidence_contract"]["required_assistant_context_core_el"]
        assert spec["visible_evidence_contract"]["source_role"] == "user"
        assert spec["visible_evidence_contract"]["assistant_context_is_independent_evidence"] is False
        assert spec["context_blueprint"]["assistant_context_train"] is False
        assert spec["context_blueprint"]["assistant_must_not_introduce_evidence"] is True
        assert plan["context_assistant_train"] is False and plan["decision_user_train"] is False
        assert plan["target_assistant_train"] is True and plan["exactly_one_supervised_assistant_turn"] is True
        assert protected["oracle"] == spec["oracle"]
        assert protected["action_contract"] == spec["action_contract"]
        kind = spec["oracle"]["kind"]
        oracle_kinds[kind] += 1
        before = derive(kind, spec["evidence"])
        result = classify(before, spec["claim_atoms"])
        after = apply(before, spec["current_request"])
        assert before == spec["oracle"]["state_before"], row["row_id"]
        assert result == spec["truth_category"] == spec["oracle"]["derived_truth"], row["row_id"]
        assert after == spec["oracle"]["state_after"], row["row_id"]
        receipt = receipt_by_id[row["row_id"]]
        assert receipt["computed_state_before"] == before and receipt["computed_truth"] == result and receipt["computed_state_after"] == after
        action = spec["action_contract"]
        assert action["external_tool_result_supplied"] is False and action["may_claim_external_action_success"] is False
        if kind in {"version_edit", "cancellation"}:
            assert action["mode"] == "text_record_edit" and action["text_record_state_name"]
        else:
            assert action["mode"] == "reasoning_only" and action["text_record_state_name"] is None
        request = spec["current_request"]
        if request and not request.get("ambiguous") and request["kind"] in {"version_ops", "cancel", "stop"}:
            action_changes += 1
            assert after != before
        if spec["truth_category"] in {"false", "partial"} and kind in {"state_inference", "speaker_ownership", "graph_inference", "rule_inference"}:
            assert spec["user_decision_semantic_content_el"].startswith(inference_prefixes), row["row_id"]
        if spec["truth_category"] == "unresolved":
            assert after == before
            assert "ask_one_targeted_clarification" in spec["expected"]["response_moves"]
        assert spec["decision_surface_contract"]["tone_must_not_add_facts_values_references_or_operations"] is True
        assert spec["decision_surface_contract"]["tone_must_not_change_declarative_core_into_question"] is True

    existing_train = {row["family_id"] for row in read_jsonl(PILOT / "inputs/train.jsonl")}
    existing_dev = {row["family_id"] for row in read_jsonl(PILOT / "inputs/dev.jsonl")}
    new_families = {row["family_id"] for row in rows}
    assert all(family.startswith("ds60_") for family in new_families)
    assert not new_families & existing_train and not new_families & existing_dev
    gate = json.loads((PILOT / "sealed/final_confirmation/gate_summary.json").read_text())
    assert gate["content_exposed_in_report"] is False and gate["authoring_launched"] is False
    lineage = json.loads((ROOT / "lineage_receipt.json").read_text())
    assert lineage["final_confirmation"]["content_materialized"] is False
    assert lineage["scale_target"]["train"] == {"true":200,"false":200,"partial":100,"unresolved":100,"total":600}
    assert lineage["this_batch"] == {"true":20,"false":20,"partial":10,"unresolved":10,"total":60}
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for name, digest in manifest["artifact_sha256"].items():
        assert sha(ROOT / name) == digest, name
    assert manifest["authored_targets"] == manifest["model_calls"] == 0
    assert manifest["queue_created"] is False and not list(ROOT.glob("*queue*"))

    result = {
        "status": "PASS_SCALE60_SPECIFICATIONS",
        "families": 20,
        "four_label_families": 10,
        "true_false_families": 10,
        "decisions": 60,
        "truth_counts": dict(label_counts),
        "tone_counts": dict(tone_counts),
        "oracle_kinds": dict(oracle_kinds),
        "oracle_recomputations": 60,
        "clear_text_state_actions_recomputed": action_changes,
        "unique_structure_signatures": 20,
        "known_train_family_intersection": [],
        "known_dev_family_intersection": [],
        "final_content_materialized": False,
        "authored_targets": 0,
        "model_calls": 0,
        "queue_created": False,
        "target_boundary": "60 prospective training specifications out of a 600-training-decision target; 60 development and 60 final-confirmation decisions remain separate.",
    }
    (ROOT / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
