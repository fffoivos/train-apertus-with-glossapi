#!/usr/bin/env python3
"""Post-run structural/oracle verifier; semantic and Greek reading remain separate gates."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path): return [json.loads(x) for x in path.read_text().split("\n") if x.strip()]


parser = argparse.ArgumentParser()
parser.add_argument("--inputs", type=Path, required=True)
parser.add_argument("--accepted-dir", type=Path, required=True)
parser.add_argument("--split", choices=["train","dev","final_confirmation"], required=True)
parser.add_argument("--summary-out", type=Path, required=True)
args = parser.parse_args()

records = {r["row_id"]:r for r in read_jsonl(args.inputs)}
envelopes = [json.loads(path.read_text()) for path in sorted(args.accepted_dir.glob("author_*.json"))]
failures = []
for envelope in envelopes:
    rid, result = envelope["row_id"], envelope["result"]
    if rid not in records: failures.append("unknown_row:"+rid); continue
    record, spec = records[rid], records[rid]["scenario_spec"]
    if record["split"] != args.split: failures.append("split:"+rid)
    if result["row_id"] != rid: failures.append("identity:"+rid)
    if result["status"] != "candidate": continue
    messages = result["messages"]; ids = [m["id"] for m in messages]
    plan = record["message_plan"]
    allowed = {plan[k] for k in ("optional_context_user_id","optional_context_assistant_id","decision_user_id","target_assistant_id")}
    if len(ids) != len(set(ids)) or not set(ids) <= allowed: failures.append("message_ids:"+rid)
    target = [m for m in messages if m["id"] == plan["target_assistant_id"]]
    decision_user = [m for m in messages if m["id"] == plan["decision_user_id"]]
    if len(target)!=1 or target[0]["role"]!="assistant" or target[0]["train"] is not True: failures.append("target:"+rid)
    if len(decision_user)!=1 or decision_user[0]["role"]!="user" or decision_user[0]["train"] is not False: failures.append("decision_user:"+rid)
    if sum(m["role"]=="assistant" and m["train"] for m in messages) != 1: failures.append("assistant_mask:"+rid)
    if any(m["role"]=="user" and m["train"] for m in messages): failures.append("user_mask:"+rid)
    if any(m["id"]==plan["optional_context_assistant_id"] and m["train"] for m in messages): failures.append("context_mask:"+rid)
    if messages[-1]["id"] != plan["target_assistant_id"]: failures.append("target_not_last:"+rid)
    exact = spec["expected"]["exact_response"]
    if exact is not None and (not target or target[0]["content"] != exact): failures.append("exact_response:"+rid)
    if len(result["decisions"]) != 1 or result["decisions"][0]["truth_category"] != spec["oracle"]["derived_truth"]: failures.append("truth:"+rid)
    expected_changed = {k for k in set(spec["oracle"]["state_before"])|set(spec["oracle"]["state_after"]) if spec["oracle"]["state_before"].get(k)!=spec["oracle"]["state_after"].get(k)}
    actual_changed = {t["field"] for t in result["state_transitions"]}
    if actual_changed != expected_changed: failures.append("transition_fields:"+rid)
    for transition in result["state_transitions"]:
        field=transition["field"]
        try: before=json.loads(transition["before_json"]); after=json.loads(transition["after_json"])
        except Exception: failures.append("transition_json:"+rid); continue
        if before != spec["oracle"]["state_before"].get(field) or after != spec["oracle"]["state_after"].get(field): failures.append("transition_value:"+rid+":"+field)

summary={"split":args.split,"accepted_artifacts_seen":len(envelopes),"candidate_outputs":sum(e["result"]["status"]=="candidate" for e in envelopes),"blocked_outputs":sum(e["result"]["status"]=="blocked" for e in envelopes),"structural_oracle_status":"PASS" if not failures else "FAIL","failure_count":len(failures),"failures":[] if args.split=="final_confirmation" else failures,"content_exposed":False if args.split=="final_confirmation" else True,"semantic_read_required":True,"greek_read_required":True}
args.summary_out.parent.mkdir(parents=True,exist_ok=True)
args.summary_out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(summary,ensure_ascii=False,indent=2))
