#!/usr/bin/env python3
"""Deterministic verifier for pilot12_candidate.jsonl.

The verifier derives claim truth from evidence values and computes required
outcomes. It does not accept the stored truth_category as oracle evidence.
"""
from __future__ import annotations

import ast
import collections
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pilot12_candidate.jsonl"


def safe_eval(expr: str, facts: dict):
    tree = ast.parse(expr, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in facts:
                raise AssertionError(f"unknown fact in expression: {node.id}")
            return facts[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = visit(node.left), visit(node.right)
            if left is None or right is None:
                return None
            return {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
            }[type(node.op)]()
        raise AssertionError(f"unsupported expression: {expr}")

    return visit(tree)


def derived_facts(row: dict) -> dict:
    evidence = row["evidence"][0]
    facts = dict(evidence["facts"])
    for key, expr in row["oracle"].get("derived_facts", {}).items():
        if expr == "requested_items - initial_items":
            facts[key] = [x for x in facts["requested_items"] if x not in facts["initial_items"]]
        else:
            facts[key] = safe_eval(expr, facts)
    return facts


def atom_value(atom: dict, facts: dict):
    actual = facts.get(atom["field"])
    if actual is None:
        return None
    if "asserted_contains" in atom:
        return atom["asserted_contains"] in actual
    asserted = atom["asserted"]
    return actual == asserted


def truth_from_evidence(row: dict, facts: dict) -> str:
    values = [atom_value(atom, facts) for atom in row["evidence"][0]["claim_atoms"]]
    if any(value is None for value in values):
        return "unresolved"
    if all(values):
        return "true"
    if not any(values):
        return "false"
    return "partial"


def has_value(text: str, value) -> bool:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, (int, float)):
        return re.search(rf"(?<!\d){re.escape(str(value))}(?!\d)", text) is not None
    return str(value).casefold() in text.casefold()


def verify_outcome(row: dict, facts: dict) -> None:
    target = next(m for m in row["messages"] if m["id"] == row["decisions"][0]["turn_id"])
    text = target["content"]
    for check in row["oracle"]["outcome_checks"]:
        kind = check["kind"]
        if kind == "contains_computed":
            value = safe_eval(check["expr"], facts)
            assert value is not None and has_value(text, value), (row["row_id"], kind, value)
        elif kind == "contains_fact":
            value = facts[check["field"]]
            assert value is not None and has_value(text, value), (row["row_id"], kind, value)
        elif kind == "contains_all_facts":
            for value in facts[check["field"]]:
                assert has_value(text, value), (row["row_id"], kind, value)
        elif kind == "forbids_phrase":
            assert check["phrase"].casefold() not in text.casefold(), (row["row_id"], kind)
        elif kind == "asks_for":
            assert ("?" in text or ";" in text) and check["phrase"].casefold() in text.casefold(), (row["row_id"], kind)
        elif kind == "exact_content":
            message = next(m for m in row["messages"] if m["id"] == check["turn_id"])
            assert message["content"] == check["value"], (row["row_id"], kind, check["turn_id"])
        else:
            raise AssertionError(f"unknown outcome check: {kind}")


def verify_structure(row: dict) -> None:
    messages = row["messages"]
    ids = [m["id"] for m in messages]
    assert len(ids) == len(set(ids)), (row["row_id"], "duplicate message id")
    assert messages and messages[0]["role"] == "user" and messages[-1]["role"] == "assistant"
    assert all(m["role"] in {"user", "assistant"} and m["content"].strip() for m in messages)
    assert all(a["role"] != b["role"] for a, b in zip(messages, messages[1:])), row["row_id"]
    assert all(m.get("train", True) is True for m in messages if m["role"] == "user")
    assert any(m["role"] == "assistant" and m.get("train", True) for m in messages)
    by_id = {m["id"]: m for m in messages}
    decision = row["decisions"][0]
    assert by_id[decision["user_claim_turn_id"]]["role"] == "user"
    assert by_id[decision["turn_id"]]["role"] == "assistant"
    assert by_id[decision["turn_id"]].get("train", True)
    evidence_ids = {e["evidence_id"] for e in row["evidence"]}
    assert set(decision["evidence_ids"]) <= evidence_ids
    for transition in row["state_transitions"]:
        if not transition["valid"] and by_id[transition["after"]]["role"] == "assistant":
            assert by_id[transition["after"]].get("train", True) is False


def verify_special_evidence(row: dict, facts: dict) -> None:
    if "prior_user_messages" in facts:
        claim_id = row["decisions"][0]["user_claim_turn_id"]
        prior = 0
        for message in row["messages"]:
            if message["id"] == claim_id:
                break
            prior += message["role"] == "user"
        assert prior == facts["prior_user_messages"], (row["row_id"], prior)
    if "requested_items" in facts:
        assert set(facts["initial_items"]) <= set(facts["requested_items"])
        assert facts["omitted_items"] == [x for x in facts["requested_items"] if x not in facts["initial_items"]]


def main() -> int:
    rows = [json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
    assert len(rows) == 12
    assert len({r["row_id"] for r in rows}) == 12
    counts = collections.Counter()
    masked = supervised = 0
    for row in rows:
        verify_structure(row)
        facts = derived_facts(row)
        computed_truth = truth_from_evidence(row, facts)
        stored_truth = row["decisions"][0]["truth_category"]
        assert computed_truth == stored_truth, (row["row_id"], computed_truth, stored_truth)
        assert row["scenario_spec"]["truth_class"] == computed_truth
        verify_special_evidence(row, facts)
        verify_outcome(row, facts)
        counts[computed_truth] += 1
        masked += sum(m["role"] == "assistant" and not m.get("train", True) for m in row["messages"])
        supervised += sum(m["role"] == "assistant" and m.get("train", True) for m in row["messages"])
    assert counts == {"true": 3, "false": 3, "partial": 3, "unresolved": 3}, counts
    result = {"status": "PASS", "rows": len(rows), "truth_counts": dict(sorted(counts.items())), "supervised_assistant_turns": supervised, "masked_assistant_turns": masked}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
