#!/usr/bin/env python3
"""Fail-closed validation of dialogue pilot payloads, schemas, and split gates."""
from __future__ import annotations

import hashlib
import json
import copy
import importlib.util
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_SHA = "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_jsonl(path): return [json.loads(x) for x in path.read_text().split("\n") if x.strip()]


def strict_schema(schema, path="$"):
    assert isinstance(schema, dict), path
    if schema.get("type") == "object" or "properties" in schema:
        assert schema.get("additionalProperties") is False, path + " is open"
        props = schema.get("properties", {})
        assert set(schema.get("required", [])) == set(props), path + " properties are not all required"
        for key, child in props.items(): strict_schema(child, path + "." + key)
    if "items" in schema: strict_schema(schema["items"], path + "[]")


MISSING = object()
def replay_version(initial, events):
    state=copy.deepcopy(initial)
    for e in events:
        if e["op"]=="set": state[e["field"]]=e["value"]
        elif e["op"]=="add":
            if isinstance(state.get(e["field"]),list):
                if e["value"] not in state[e["field"]]: state[e["field"]].append(e["value"])
            else: state[e["field"]]=state.get(e["field"],0)+e["value"]
        elif e["op"]=="remove":
            if isinstance(state.get(e["field"]),list): state[e["field"]]=[x for x in state[e["field"]] if x!=e["value"]]
            else: state.pop(e["field"],None)
        else: raise AssertionError(e)
    return state

def derive(evidence):
    state=copy.deepcopy(evidence["facts"]); state.update(evidence.get("extra",{}))
    for f in evidence["formulas"]:
        values=[state.get(a) for a in f["args"]]
        if any(v is None for v in values): value=None
        elif f["op"]=="add": value=sum(values)
        elif f["op"]=="subtract": value=values[0]-values[1]
        elif f["op"]=="subtract_many": value=values[0]-sum(values[1:])
        elif f["op"]=="equals": value=values[0]==values[1]
        elif f["op"]=="greater_than": value=values[0]>values[1]
        elif f["op"]=="graph_direct":
            edges=state[f["args"][2]]; value=[values[0],values[1]] in edges or [values[1],values[0]] in edges
        elif f["op"]=="graph_reachable":
            start,goal,edges=values[0],values[1],state[f["args"][2]]; seen,todo={start},[start]
            while todo:
                node=todo.pop()
                for a,b in edges:
                    nxt=b if a==node else a if b==node else None
                    if nxt is not None and nxt not in seen: seen.add(nxt); todo.append(nxt)
            value=goal in seen
        else: raise AssertionError(f)
        state[f["field"]]=value
    return state

def classify(state, atoms):
    outcomes=[]
    for atom in atoms:
        value=state.get(atom["field"],MISSING); op=atom.get("op","equals")
        if value is MISSING or value is None: outcomes.append(None)
        elif op=="equals": outcomes.append(value==atom["asserted"])
        elif op=="contains": outcomes.append(atom["asserted"] in value)
        elif op=="not_contains": outcomes.append(atom["asserted"] not in value)
        else: raise AssertionError(atom)
    if any(v is None for v in outcomes): return "unresolved"
    if all(outcomes): return "true"
    if not any(outcomes): return "false"
    return "partial"

def apply_request(state, request):
    if not request or request.get("ambiguous"): return copy.deepcopy(state)
    if request["kind"]=="version_ops": return replay_version(state,request["ops"])
    if request["kind"]=="cancel":
        out=copy.deepcopy(state); out[request["target"]]="cancelled"; return out
    raise AssertionError(request)


assert sha(HERE / "run_queue.py") == RUNNER_SHA
manifest = json.loads((HERE / "manifest.json").read_text())
assert manifest["runner"]["sha256"] == RUNNER_SHA
for relative, expected in manifest["artifact_sha256"].items():
    assert sha(HERE / relative) == expected, relative
for path in (HERE / "schemas").glob("*.json"): strict_schema(json.loads(path.read_text()))
for path in (HERE / "prompts").glob("*.txt"): assert path.read_text().count("{{INPUT_JSON}}") == 1

inputs = {}
paths = {"train":HERE/"inputs/train.jsonl","dev":HERE/"inputs/dev.jsonl","final_confirmation":HERE/"sealed/final_confirmation/inputs.jsonl"}
for split, path in paths.items():
    rows = read_jsonl(path); inputs[split] = rows
    assert all(r["split"] == split for r in rows)
    assert len({r["row_id"] for r in rows}) == len(rows)
assert {k:len(v) for k,v in inputs.items()} == {"train":32,"dev":8,"final_confirmation":8}

families = defaultdict(set)
for split, rows in inputs.items():
    for row in rows:
        families[row["family_id"]].add(split)
        spec = row["scenario_spec"]
        if spec["oracle"]["kind"]=="version_edit": state=replay_version(spec["evidence"]["initial"],spec["evidence"]["events"])
        elif spec["oracle"]["kind"]=="state_inference": state=derive(spec["evidence"])
        elif spec["oracle"]["kind"]=="cancellation": state=replay_version(spec["evidence"]["initial"],[{"op":"set","field":e["task"],"value":e["status"]} for e in spec["evidence"]["events"]])
        else: raise AssertionError(spec["oracle"]["kind"])
        assert state == spec["oracle"]["state_before"]
        assert classify(state,spec["claim_atoms"]) == spec["oracle"]["derived_truth"] == spec["truth_category"]
        assert apply_request(state,spec["current_request"]) == spec["oracle"]["state_after"]
        assert row["message_plan"]["context_assistant_train"] is False
        assert row["message_plan"]["target_assistant_train"] is True
assert all(len(splits) == 1 for splits in families.values())

quarantine = read_jsonl(HERE / "quarantine/silence_unspecified.jsonl")
assert len(quarantine) == 1
q = quarantine[0]
assert q["split"] == "final_confirmation" and q["quarantine"]
assert q["scenario_spec"]["current_request"]["silence_requested"] is True
assert q["scenario_spec"]["current_request"]["silence_representation"] == "unspecified"

queues = {
    "train":read_jsonl(HERE/"queues/train.jsonl"),"dev":read_jsonl(HERE/"queues/dev.jsonl"),
    "final_confirmation":read_jsonl(HERE/"sealed/final_confirmation/queue.jsonl"),
}
assert {k:len(v) for k,v in queues.items()} == {"train":32,"dev":8,"final_confirmation":7}
for split, jobs in queues.items():
    ids = {r["row_id"] for r in inputs[split] if not r["quarantine"]}
    assert {j["row_id"] for j in jobs} == ids
    assert all(j["model"] == "gpt-5.6-sol" and j["effort"] == "high" for j in jobs)
probe = read_jsonl(HERE / "queues/probe_train4.jsonl")
probe_rows = {r["row_id"]:r for r in inputs["train"]}
assert len(probe) == 4 and all(j in queues["train"] for j in probe)
assert Counter(probe_rows[j["row_id"]]["scenario_spec"]["truth_category"] for j in probe) == Counter({"true":1,"false":1,"partial":1,"unresolved":1})
assert {probe_rows[j["row_id"]]["scenario_spec"]["oracle"]["kind"] for j in probe} == {"version_edit","state_inference","cancellation"}

runner_spec=importlib.util.spec_from_file_location("balanced_shared_runner",HERE/"run_queue.py")
runner=importlib.util.module_from_spec(runner_spec); runner_spec.loader.exec_module(runner)
all_records={r["row_id"]:r for rows in inputs.values() for r in rows}
receipt_paths={"train":HERE/"receipts/train_payload_bindings.jsonl","dev":HERE/"receipts/dev_payload_bindings.jsonl","final_confirmation":HERE/"sealed/final_confirmation/payload_bindings.jsonl"}
binding_count=0
for split,jobs in queues.items():
    receipts={r["job_id"]:r for r in read_jsonl(receipt_paths[split])}
    assert len(receipts)==len(jobs)
    for job in jobs:
        _,fields=runner.binding(job,all_records[job["row_id"]],{})
        for key in ("job_spec_sha256","input_record_sha256","payload_sha256","prompt_sha256"):
            recorded_key="assembled_prompt_sha256" if key=="prompt_sha256" else key
            assert receipts[job["job_id"]][recorded_key]==fields[key],(job["job_id"],key)
        binding_count+=1

calls = json.loads((HERE / "call_and_cost_envelope.json").read_text())
assert calls["primary_authoring_calls"] == sum(map(len,queues.values())) == 47
assert calls["absolute_call_cap"] == 47 + 12 + 12 + 47 == 118
assert calls["retry_split_caps"] == {"train":4,"dev":4,"final_confirmation":4}
assert calls["probe_is_subset_of_primary"] is True
assert manifest["execution"]["launched"] is False

result = {
    "status":"PASS_PRELAUNCH","specifications":48,"dispatchable":47,"quarantined":1,
    "split_counts":{"train":32,"dev":8,"final_confirmation":8},
    "queue_counts":{"train":32,"dev":8,"final_confirmation":7},
    "probe":{"calls":4,"truth_categories":4,"oracle_kinds":3,"train_only":True},
    "strict_schemas":3,"oracle_recomputations":48,"prompt_bindings_verified":binding_count,"family_leakage":False,"absolute_call_cap":118,
    "runner_sha256":RUNNER_SHA,"launched":False,
}
(HERE / "receipts/prelaunch_verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False,indent=2))
