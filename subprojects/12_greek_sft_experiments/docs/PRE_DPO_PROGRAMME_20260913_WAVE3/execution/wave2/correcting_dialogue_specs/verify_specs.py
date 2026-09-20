#!/usr/bin/env python3
"""Independently recompute truth and state outcomes for the pilot48 specs."""
from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MISSING = object()


def version(initial, events):
    state = copy.deepcopy(initial)
    for e in events:
        if e["op"] == "set": state[e["field"]] = e["value"]
        elif e["op"] == "add":
            if isinstance(state.get(e["field"]), list):
                if e["value"] not in state[e["field"]]: state[e["field"]].append(e["value"])
            else: state[e["field"]] = state.get(e["field"], 0) + e["value"]
        elif e["op"] == "remove":
            if isinstance(state.get(e["field"]), list): state[e["field"]] = [x for x in state[e["field"]] if x != e["value"]]
            else: state.pop(e["field"], None)
        else: raise AssertionError(e)
    return state


def inference(evidence):
    state = copy.deepcopy(evidence["facts"]); state.update(evidence.get("extra", {}))
    for f in evidence["formulas"]:
        args = f["args"]; values = [state.get(a) for a in args]
        if any(v is None for v in values): value = None
        elif f["op"] == "add": value = sum(values)
        elif f["op"] == "subtract": value = values[0] - values[1]
        elif f["op"] == "subtract_many": value = values[0] - sum(values[1:])
        elif f["op"] == "equals": value = values[0] == values[1]
        elif f["op"] == "greater_than": value = values[0] > values[1]
        elif f["op"] == "graph_direct":
            edges = state[args[2]]; value = [values[0], values[1]] in edges or [values[1], values[0]] in edges
        elif f["op"] == "graph_reachable":
            start, goal, edges = values[0], values[1], state[args[2]]; seen, todo = {start}, [start]
            while todo:
                node = todo.pop()
                for a, b in edges:
                    nxt = b if a == node else a if b == node else None
                    if nxt is not None and nxt not in seen: seen.add(nxt); todo.append(nxt)
            value = goal in seen
        else: raise AssertionError(f)
        state[f["field"]] = value
    return state


def cancellation(initial, events):
    state = copy.deepcopy(initial)
    for e in events: state[e["task"]] = e["status"]
    return state


def classify(state, atoms):
    outcomes = []
    for atom in atoms:
        value = state.get(atom["field"], MISSING)
        if value is MISSING or value is None: outcomes.append(None)
        elif atom.get("op", "equals") == "equals": outcomes.append(value == atom["asserted"])
        elif atom["op"] == "contains": outcomes.append(atom["asserted"] in value)
        elif atom["op"] == "not_contains": outcomes.append(atom["asserted"] not in value)
        else: raise AssertionError(atom)
    if any(x is None for x in outcomes): return "unresolved"
    if all(outcomes): return "true"
    if not any(outcomes): return "false"
    return "partial"


def apply_request(state, request):
    if not request or request.get("ambiguous"): return copy.deepcopy(state)
    if request["kind"] == "version_ops": return version(state, request["ops"])
    if request["kind"] == "cancel":
        out = copy.deepcopy(state); out[request["target"]] = "cancelled"; return out
    return copy.deepcopy(state)


rows = [json.loads(line) for line in (HERE / "pilot48_input_specs.jsonl").read_text().splitlines() if line.strip()]
assert len(rows) == 48 and len({r["spec_id"] for r in rows}) == 48
for row in rows:
    evidence, kind = row["evidence"], row["oracle"]["kind"]
    if kind == "version_edit": state = version(evidence["initial"], evidence["events"])
    elif kind == "state_inference": state = inference(evidence)
    elif kind == "cancellation": state = cancellation(evidence["initial"], evidence["events"])
    else: raise AssertionError(kind)
    assert classify(state, row["claim_atoms"]) == row["truth_category"] == row["oracle"]["derived_truth"], row["spec_id"]
    assert apply_request(state, row["current_request"]) == row["oracle"]["state_after"], row["spec_id"]
    assert state == row["oracle"]["state_before"], row["spec_id"]
    context = row["context_blueprint"]["optional_prior_assistant_turn"]
    assert context["train"] is False and context["must_be_derived_from_evidence"] is True
    if row["current_request"] and row["current_request"].get("current_update_authority"):
        assert row["truth_category"] == "false"
    if row["expected"]["exact_response"] is not None:
        assert row["expected"]["exact_response"] == "Ακυρώθηκε."
    if row["expected"]["generation_status"] == "blocked":
        assert row["current_request"].get("silence_representation") == "unspecified"

assert Counter(r["truth_category"] for r in rows) == Counter({"true":12,"false":12,"partial":12,"unresolved":12})
assert Counter(r["tone"] for r in rows) == Counter({"cooperative":12,"neutral":12,"assertive":12,"frustrated_but_civil":12})
families = defaultdict(set)
for row in rows: families[row["family_id"]].add(row["split"])
assert len(families) == 12 and all(len(splits) == 1 for splits in families.values())

manifest = json.loads((HERE / "family_split_manifest.json").read_text())
target = manifest["scale_target"]
totals = Counter()
for split in target["split_plan"].values():
    for truth in ("true","false","partial","unresolved"): totals[truth] += split["decisions"][truth]
assert dict(totals) == target["truth_counts"]
assert sum(totals.values()) == target["decisions"] == 600
print(json.dumps({"status":"PASS","records":48,"truth_counts":dict(Counter(r["truth_category"] for r in rows)),"families":12,"family_leakage":False,"scale_target":dict(totals)}, ensure_ascii=False, sort_keys=True))
