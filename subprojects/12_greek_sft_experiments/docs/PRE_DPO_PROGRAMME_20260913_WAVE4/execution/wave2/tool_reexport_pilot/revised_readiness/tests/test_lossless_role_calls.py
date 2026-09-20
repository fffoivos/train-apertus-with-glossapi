#!/usr/bin/env python3
"""Pure-function regression controls for non-assistant function_calls handling."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_functions(path: Path, names: set[str], namespace: dict):
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


export = load_functions(
    ROOT / "frozen_science" / "export_core.py",
    {"_json_text", "_tag", "_export_turn"},
    {"json": json, "text_of": lambda value: "" if value is None else str(value), "TOOL_FIELDS": ("functions", "function_calls", "tool_calls", "tool_call_id", "name")},
)
pilot = load_functions(
    ROOT / "pilot_run.py",
    {"tag_payload", "nonassistant_call_quarantine"},
    {"json": json, "re": re},
)


def assert_rendered(raw: str, role: str, expected_reason: str | None):
    source = {"role": role, "content": "request", "function_calls": raw, "functions": None}
    rendered = export["_export_turn"](source)
    assert rendered["function_calls"] == raw
    payload = json.loads(pilot["tag_payload"](rendered["content"], "function_calls"))
    assert payload == {"function_calls": raw}
    assert pilot["nonassistant_call_quarantine"](source) == expected_reason


assert_rendered("null", "user", "nonassistant_function_calls:null_string_sentinel")
assert_rendered(
    'lookup_city(city="Bern")',
    "user",
    "nonassistant_function_calls:role_user",
)
assert_rendered('lookup_city(city="Bern")', "assistant", None)

empty = export["_export_turn"]({"role": "user", "content": "plain", "function_calls": ""})
assert "<function_calls>" not in empty["content"]
assert pilot["nonassistant_call_quarantine"]({"role": "user", "function_calls": ""}) is None

tool = export["_export_turn"](
    {"role": "tool", "content": {"ok": True}, "tool_call_id": "call-1", "name": "lookup_city"}
)
assert tool["tool_call_id"] == "call-1" and tool["name"] == "lookup_city"
assert json.loads(tool["content"]) == {"content": {"ok": True}, "tool_call_id": "call-1", "name": "lookup_city"}

actual = json.loads((ROOT.parent / "remote_readiness" / "dolci" / "three_role_mismatches.json").read_text())
actual_reasons = []
for row in actual["rows"]:
    for implicated in row["implicated_turns"]:
        source = implicated["turn"]
        rendered = export["_export_turn"](source)
        payload = json.loads(pilot["tag_payload"](rendered["content"], "function_calls"))
        assert payload["function_calls"] == source["function_calls"]
        actual_reasons.append(pilot["nonassistant_call_quarantine"](source))
assert actual_reasons.count("nonassistant_function_calls:null_string_sentinel") == 2
assert actual_reasons.count("nonassistant_function_calls:role_user") == 1

print("5 synthetic controls and 3 frozen-source regressions passed")
