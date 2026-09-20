#!/usr/bin/env python3
"""Lossless, deterministic Dolci Tool Use pilot. Local cached inputs only."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


ANNOTATION_KEYS = {"title", "description", "default", "examples", "$schema", "deprecated", "readOnly", "writeOnly"}
SUPPORTED_SCHEMA_KEYS = ANNOTATION_KEYS | {
    "type", "properties", "required", "additionalProperties", "items", "enum", "const",
    "anyOf", "oneOf", "allOf", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "pattern", "minItems", "maxItems", "uniqueItems",
}


def _types(value):
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }


def check_schema(schema, path="$"):
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise ValueError(f"{path}: schema is not an object/boolean")
    unknown = set(schema) - SUPPORTED_SCHEMA_KEYS
    if unknown:
        raise ValueError(f"{path}: unsupported schema keywords {sorted(unknown)}")
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not isinstance(types, list) or not types or any(x not in _types(None) for x in types):
            raise ValueError(f"{path}: invalid type")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ValueError(f"{path}: properties is not an object")
        for key, sub in schema["properties"].items():
            check_schema(sub, f"{path}.properties.{key}")
    if "items" in schema:
        check_schema(schema["items"], f"{path}.items")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], (bool, dict)):
        raise ValueError(f"{path}: unsupported additionalProperties")
    if isinstance(schema.get("additionalProperties"), dict):
        check_schema(schema["additionalProperties"], f"{path}.additionalProperties")
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            if not isinstance(schema[key], list) or not schema[key]:
                raise ValueError(f"{path}: {key} must be a nonempty list")
            for i, sub in enumerate(schema[key]):
                check_schema(sub, f"{path}.{key}[{i}]")


def validate_instance(instance, schema, path="$"):
    if schema is True:
        return
    if schema is False:
        raise ValueError(f"{path}: forbidden by false schema")
    check_schema(schema)
    if "allOf" in schema:
        for sub in schema["allOf"]:
            validate_instance(instance, sub, path)
    for key, exact in (("anyOf", False), ("oneOf", True)):
        if key in schema:
            matches = 0
            for sub in schema[key]:
                try:
                    validate_instance(instance, sub, path)
                    matches += 1
                except ValueError:
                    pass
            if matches == 0 or (exact and matches != 1):
                raise ValueError(f"{path}: {key} failed")
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        actual = _types(instance)
        if not any(actual[x] for x in types):
            raise ValueError(f"{path}: expected {types}")
    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"{path}: enum failed")
    if "const" in schema and instance != schema["const"]:
        raise ValueError(f"{path}: const failed")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [x for x in required if x not in instance]
        if missing:
            raise ValueError(f"{path}: missing required {missing}")
        properties = schema.get("properties", {})
        extra_schema = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                validate_instance(value, properties[key], f"{path}.{key}")
            elif extra_schema is False:
                raise ValueError(f"{path}: unexpected property {key}")
            elif isinstance(extra_schema, dict):
                validate_instance(value, extra_schema, f"{path}.{key}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValueError(f"{path}: minItems failed")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise ValueError(f"{path}: maxItems failed")
        if schema.get("uniqueItems") and len({canonical(x) for x in instance}) != len(instance):
            raise ValueError(f"{path}: uniqueItems failed")
        if "items" in schema:
            for i, value in enumerate(instance):
                validate_instance(value, schema["items"], f"{path}[{i}]")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValueError(f"{path}: minLength failed")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise ValueError(f"{path}: maxLength failed")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise ValueError(f"{path}: pattern failed")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        for key, op in (("minimum", lambda a, b: a >= b), ("maximum", lambda a, b: a <= b),
                        ("exclusiveMinimum", lambda a, b: a > b), ("exclusiveMaximum", lambda a, b: a < b)):
            if key in schema and not op(instance, schema[key]):
                raise ValueError(f"{path}: {key} failed")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def load_ast_functions(path: Path, names: set[str], namespace: dict):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes} != names:
        raise ValueError(f"missing expected functions in {path}")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def literal(node):
    if isinstance(node, ast.Name) and node.id in {"true", "false", "null"}:
        return {"true": True, "false": False, "null": None}[node.id]
    if isinstance(node, ast.List):
        return [literal(x) for x in node.elts]
    if isinstance(node, ast.Tuple):
        return [literal(x) for x in node.elts]
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    return ast.literal_eval(node)


def parse_calls(raw: str):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = None
    if value is not None:
        rows = value if isinstance(value, list) else [value]
        parsed = []
        for x in rows:
            if not isinstance(x, dict):
                raise ValueError("JSON call is not an object")
            fn = x.get("function", x)
            name = fn.get("name")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            if not isinstance(name, str) or not isinstance(args, dict):
                raise ValueError("JSON call lacks name/object arguments")
            parsed.append({"name": name, "arguments": args, "grammar": "json"})
        return parsed
    try:
        body = ast.parse(raw, mode="eval").body
        nodes = list(body.elts) if isinstance(body, (ast.List, ast.Tuple)) else [body]
    except SyntaxError:
        module = ast.parse(raw, mode="exec")
        if not module.body or not all(isinstance(x, ast.Expr) for x in module.body):
            raise ValueError("call string is neither JSON nor call expressions")
        nodes = [x.value for x in module.body]
    parsed = []
    for node in nodes:
        if not isinstance(node, ast.Call) or node.args or any(k.arg is None for k in node.keywords):
            raise ValueError("call expression must use named literal arguments")
        name = dotted_name(node.func)
        if not name:
            raise ValueError("call name is not a dotted identifier")
        parsed.append({"name": name, "arguments": {k.arg: literal(k.value) for k in node.keywords}, "grammar": "python_call"})
    return parsed


def declared_functions(raw: str):
    value = json.loads(raw)
    if not isinstance(value, list):
        raise ValueError("functions JSON is not a list")
    result = {}
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("function schema item is not an object")
        fn = item.get("function", item)
        name = fn.get("name")
        params = fn.get("parameters", {"type": "object"})
        if not isinstance(name, str) or not isinstance(params, dict):
            raise ValueError("function schema lacks name/parameters")
        check_schema(params)
        result[name] = params
    return result


def tag_payload(content: str, name: str):
    match = re.search(rf"<{name}>\n(.*?)\n</{name}>", content, re.S)
    if not match:
        raise ValueError(f"missing rendered {name} tag")
    return match.group(1)


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--expected-contract-sha256", required=True)
    args = ap.parse_args()
    started = time.monotonic()
    contract_path = Path(args.contract).resolve()
    if sha(contract_path) != args.expected_contract_sha256:
        raise ValueError("pilot contract hash mismatch")
    contract = json.loads(contract_path.read_text())
    if contract.get("schema_version") != "dolci_tool200_pilot_v1":
        raise ValueError("pilot contract schema drift")
    base = contract_path.parent
    for key, binding in contract["implementation"].items():
        path = (base / binding["path"]).resolve()
        if sha(path) != binding["sha256"]:
            raise ValueError(f"implementation hash mismatch: {key}")
    inv_path = (base / contract["source"]["inventory_path"]).resolve()
    if sha(inv_path) != contract["source"]["inventory_sha256"]:
        raise ValueError("source inventory hash mismatch")
    inv = json.loads(inv_path.read_text())
    revision = contract["source"]["revision"]
    if inv["source_revision"] != revision or len(inv["selected"]) != contract["target_rows"]:
        raise ValueError("source selection contract mismatch")
    snapshot = Path(contract["source"]["snapshot"])
    for shard in contract["source"]["selected_shards"]:
        path = snapshot / shard["file"]
        if path.stat().st_size != shard["bytes"] or sha(path) != shard["sha256"]:
            raise ValueError(f"source shard binding mismatch: {shard['file']}")
    for key, expected in contract["tokenizer"]["files"].items():
        if sha(Path(contract["tokenizer"]["path"]) / key) != expected:
            raise ValueError(f"tokenizer binding mismatch: {key}")

    export_path = (base / contract["implementation"]["export_core"]["path"]).resolve()
    vantage_path = (base / contract["implementation"]["vantage_scan"]["path"]).resolve()
    consumer_path = (base / contract["implementation"]["consumer"]["path"]).resolve()
    ns = {"json": json, "re": re}
    load_ast_functions(vantage_path, {"text_of", "assistant_text", "user_text"}, ns)
    ns.update({"os": os, "TOOL_FIELDS": ("functions", "function_calls", "tool_calls", "tool_call_id", "name")})
    load_ast_functions(export_path, {"_json_text", "_tag", "_export_turn", "_source_id", "_export_row"}, ns)
    consumer_ns = {"GREEK_EDITS": {}}
    load_ast_functions(consumer_path, {"to_messages"}, consumer_ns)

    selected_by_group = defaultdict(list)
    for ordinal, sel in enumerate(inv["selected"]):
        loc = sel["source_locator"]
        selected_by_group[(loc["file"], loc["row_group"])].append((ordinal, sel))
    upstream = {}
    for (rel, rg), sels in selected_by_group.items():
        table = pq.ParquetFile(snapshot / rel).read_row_group(rg)
        for ordinal, sel in sels:
            row = table.slice(sel["source_locator"]["row_in_group"], 1).to_pylist()[0]
            if row.get("domain") != "Tool Use" or row.get("id") != sel["source_id"]:
                raise ValueError("source locator or id mismatch")
            if row.get("source_dataset") != contract["source"]["required_source_dataset"]:
                raise ValueError("upstream source_dataset mismatch")
            upstream[ordinal] = row
    if len(upstream) != contract["target_rows"]:
        raise ValueError("not all selected rows resolved")

    sft_path = (base / contract["implementation"]["sft_train"]["path"]).resolve()
    spec = importlib.util.spec_from_file_location("frozen_sft_train", sft_path)
    sft = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = sft
    spec.loader.exec_module(sft)
    tokenizer, control_ids = sft.prepare_tokenizer({
        "tokenizer_name_or_path": contract["tokenizer"]["path"],
        "template_source": contract["tokenizer"]["path"],
        "require_apertus_control_ids": True,
        "extend_control_tokens": False,
    })

    attempt = int(os.environ.get("APERTUS_DATA_STAGE_ATTEMPT", "1"))
    run_root = Path(os.environ["APERTUS_DATA_STAGE_RUN_ROOT"])
    artifacts = run_root / "artifacts" / f"tool200-a{attempt}"
    if artifacts.exists():
        raise ValueError(f"attempt artifact directory already exists: {artifacts}")
    artifacts.mkdir(parents=True)
    export_rows, metrics, rendered_rows = [], [], []
    for ordinal in range(contract["target_rows"]):
        src = upstream[ordinal]
        sel = inv["selected"][ordinal]
        msgs = src.get("messages") or []
        turns = [ns["_export_turn"](m) for m in msgs if isinstance(m, dict)]
        user = ns["user_text"](src)
        assistant = ns["assistant_text"](src)
        out = ns["_export_row"]("dolci_tooluse", src["domain"], ns["_source_id"](src, "missing"), user, assistant,
                                turns, revision, sel["source_locator"])
        out["source_dataset"] = src["source_dataset"]
        roundtrip = json.loads(json.dumps(out, ensure_ascii=False))
        exact_native = True
        declared = {}
        schema_chars = 0
        call_count = 0
        grammars = set()
        protocol_errors = []
        for original, exported in zip(msgs, roundtrip["turns"]):
            for field in ("functions", "function_calls", "tool_calls", "tool_call_id", "name"):
                if field in original and exported.get(field) != original.get(field):
                    exact_native = False
            if original.get("functions"):
                schema_chars += len(original["functions"])
                try:
                    declared.update(declared_functions(original["functions"]))
                except Exception as exc:
                    protocol_errors.append(f"schema:{type(exc).__name__}:{exc}")
                if tag_payload(exported["content"], "functions") != original["functions"]:
                    protocol_errors.append("rendered_schema_mismatch")
            if original.get("function_calls"):
                try:
                    calls = parse_calls(original["function_calls"])
                    call_count += len(calls)
                    grammars.update(x["grammar"] for x in calls)
                    for call in calls:
                        if call["name"] not in declared:
                            raise ValueError(f"undeclared call {call['name']}")
                        validate_instance(call["arguments"], declared[call["name"]])
                except Exception as exc:
                    protocol_errors.append(f"call:{type(exc).__name__}:{exc}")
                payload = json.loads(tag_payload(exported["content"], "function_calls"))
                if payload.get("function_calls") != original["function_calls"]:
                    protocol_errors.append("rendered_call_mismatch")
        rendered = consumer_ns["to_messages"](roundtrip, "dolci_tooluse")
        if rendered is None:
            protocol_errors.append("consumer_rejected")
            token_count = 0
            supervised = 0
        else:
            rendered_text = "\n".join(m["content"] for m in rendered)
            for original, exported in zip(msgs, roundtrip["turns"]):
                if original.get("role") in {"tool", "environment"} and exported["content"] not in rendered_text:
                    protocol_errors.append("rendered_result_mismatch")
            encoded = sft.tokenize_messages(tokenizer, rendered)
            token_count = len(encoded["input_ids"])
            supervised = sum(encoded["assistant_masks"])
        structural = exact_native and not protocol_errors
        within = bool(rendered) and token_count <= contract["max_tokens"]
        export_rows.append(roundtrip)
        rendered_rows.append(rendered)
        metrics.append({
            "ordinal": ordinal, "source_id": sel["source_id"], "source_locator": sel["source_locator"],
            "source_dataset": src["source_dataset"], "turn_count": len(turns), "schema_chars": schema_chars,
            "call_count": call_count, "call_grammars": sorted(grammars), "exact_native_roundtrip": exact_native,
            "protocol_errors": protocol_errors, "structural_accept": structural,
            "rendered_tokens": token_count, "assistant_supervised_tokens": supervised,
            "within_token_gate": within, "candidate_accept": structural and within,
            "upstream_id_fields": sorted({k for turn in msgs for k in ("tool_call_id", "name") if k in turn and turn[k] is not None}),
        })

    def write_jsonl(name, rows):
        path = artifacts / name
        path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
        return path

    export_file = write_jsonl("lossless_export.jsonl", export_rows)
    metrics_file = write_jsonl("row_metrics.jsonl", metrics)
    accepted = [row for row, m in zip(export_rows, metrics) if m["candidate_accept"]]
    accepted_file = write_jsonl("accepted_candidate.jsonl", accepted)
    ordered = sorted(range(len(metrics)), key=lambda i: (
        metrics[i]["schema_chars"], metrics[i]["call_count"], metrics[i]["turn_count"],
        metrics[i]["call_grammars"], hashlib.sha256(canonical(metrics[i]["source_locator"])).hexdigest()))
    sample_indices = sorted({ordered[round(i * (len(ordered) - 1) / 39)] for i in range(40)})
    if len(sample_indices) != 40:
        raise ValueError("semantic sample did not contain 40 unique rows")
    semantic_file = write_jsonl("semantic_review_sample40.jsonl", [{
        "source_id": metrics[i]["source_id"], "source_locator": metrics[i]["source_locator"],
        "features": {k: metrics[i][k] for k in ("schema_chars", "call_count", "turn_count", "call_grammars", "rendered_tokens")},
        "messages": rendered_rows[i], "review_status": "pending_human_semantic_review",
    } for i in sample_indices])
    token_inventory = {
        "max_tokens": contract["max_tokens"], "rows": len(metrics),
        "within": sum(m["within_token_gate"] for m in metrics),
        "overlong_excluded": sum(not m["within_token_gate"] for m in metrics),
        "min": min(m["rendered_tokens"] for m in metrics), "max": max(m["rendered_tokens"] for m in metrics),
        "total": sum(m["rendered_tokens"] for m in metrics),
        "assistant_supervised_total": sum(m["assistant_supervised_tokens"] for m in metrics),
        "control_token_ids": control_ids, "vocab_size": len(tokenizer),
    }
    token_file = artifacts / "token_inventory.json"
    atomic_json(token_file, token_inventory)
    structural_ok = sum(m["structural_accept"] for m in metrics)
    status = "passed" if structural_ok == contract["target_rows"] else "failed"
    receipt = {
        "schema_version": "dolci_tool200_pilot_receipt_v1", "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(), "attempt": attempt,
        "source_dataset": contract["source"]["dataset"], "source_revision": revision,
        "selected_locator_sha256": inv["selected_locator_sha256"], "selected_rows": len(metrics),
        "native_roundtrip_pass": sum(m["exact_native_roundtrip"] for m in metrics),
        "structural_accept": structural_ok, "candidate_accept": len(accepted),
        "overlong_excluded": token_inventory["overlong_excluded"],
        "semantic_review_rows": 40, "semantic_review_status": "pending_human_semantic_review",
        "native_protocol": {"schema_fields": inv["schema_fields"], "call_or_result_ids_required": "conditional_on_upstream_presence"},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "bindings": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in
                     (export_file, metrics_file, accepted_file, semantic_file, token_file)},
    }
    receipt_path = run_root / "receipts" / "tool200.json"
    atomic_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        run_root = os.environ.get("APERTUS_DATA_STAGE_RUN_ROOT")
        if run_root:
            atomic_json(Path(run_root) / "receipts" / "tool200.json", {
                "schema_version": "dolci_tool200_pilot_receipt_v1", "status": "failed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
            })
        raise
