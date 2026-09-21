"""Prefix-local turn annotation, batching, calibration and adjudication."""
from __future__ import annotations

import collections
import json
import pathlib
import random
import re
from typing import Any

from budget import CallLedger
from clients import SolClient
from common import append_jsonl, estimate_tokens, read_json, read_jsonl, sha256_json, sha256_text, utcnow
from schemas import Annotation, DIMENSIONS, SEVERITIES

HERE = pathlib.Path(__file__).resolve().parent
PROMPT = HERE.joinpath("turn_quality.txt").read_text(encoding="utf-8")

RESULT_SCHEMA = {"type": "object", "properties": {
    "annotations": {"type": "array", "items": {"type": "object", "properties": {
        "annotation_id": {"type": "string"},
        "dimensions": {"type": "object", "properties": {d: {"type": "string", "enum": sorted(SEVERITIES)} for d in DIMENSIONS},
                       "required": list(DIMENSIONS), "additionalProperties": False},
        "local_quality": {"type": "string", "enum": sorted(SEVERITIES)},
        "issue_tags": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "new_error": {"type": "boolean"}, "propagated_error": {"type": "boolean"},
        "recovery_opportunity": {"type": "boolean"}, "recovery_success": {"type": "boolean"},
    }, "required": ["annotation_id", "dimensions", "local_quality", "issue_tags", "evidence", "confidence",
                    "new_error", "propagated_error", "recovery_opportunity", "recovery_success"],
       "additionalProperties": False}}
}, "required": ["annotations"], "additionalProperties": False}


def latest_trajectories(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    result = {}
    for row in read_jsonl(path):
        result[row["trajectory_id"]] = row
    return result


def _contains_value(text: str, value: Any) -> bool:
    if isinstance(value, (str, int, float)):
        return str(value).casefold() in text.casefold()
    return False


def verifier_result(seed: dict[str, Any], response: str) -> dict[str, Any] | None:
    """Execute the catalogue's exact/preservation hooks without executing model code."""
    fixture = seed["fixture"]
    checks = fixture.get("checks", [])
    family = seed["family"]
    if not (seed["task"] in {"math", "instruction"} or checks):
        return None
    outcomes: list[dict[str, Any]] = []
    for check in checks:
        kind = check.get("type")
        if kind == "exact_number":
            value = check["value"]
            numbers = re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", response)
            passed = str(value) in numbers
            outcomes.append({"type": kind, "expected": value, "passed": passed})
        elif kind == "preserve_values":
            missing = [value for value in check.get("values", []) if not _contains_value(response, value)]
            outcomes.append({"type": kind, "missing": missing, "passed": not missing})
        else:
            outcomes.append({"type": str(kind), "passed": None, "note": "no executable hook"})
    if not outcomes and family.startswith("m_"):
        reference = fixture.get("reference", {})
        scalar = next((v for k, v in reference.items() if k in {"answer", "answer_cents", "x", "maximum"}
                       and isinstance(v, (str, int, float))), None)
        if scalar is not None:
            outcomes.append({"type": "reference_scalar", "expected": scalar,
                             "passed": _contains_value(response, scalar)})
    return {"executed": bool(outcomes), "checks": outcomes,
            "all_passed": bool(outcomes) and all(x.get("passed") is True for x in outcomes)}


def build_packets(state: str | pathlib.Path, stage: str) -> list[dict[str, Any]]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    seeds = {s["trajectory_id"]: s for s in manifest["seeds"] if s["stage"] == stage}
    trajectories = latest_trajectories(state / stage / "trajectories.jsonl")
    ledger = CallLedger(state, manifest["config"])
    packets = []
    for tid in sorted(trajectories):
        trajectory = trajectories[tid]
        seed = seeds[tid]
        messages = trajectory["messages"]
        assistant_indices = [i for i, m in enumerate(messages) if m["role"] == "assistant"]
        for turn, index in enumerate(assistant_indices, 1):
            prefix = messages[:index + 1]  # Deliberately excludes every later turn.
            response = messages[index]["content"]
            input_text = json.dumps(messages[:index], ensure_ascii=False)
            call = ledger.get(f"target:rollout:{stage}:{tid}:t{turn}")
            result = json.loads(call["result"]) if call and call.get("result") else {}
            usage = result.get("usage") or {}
            output_tokens = int(usage.get("completion_tokens") or estimate_tokens(response))
            input_tokens = int(usage.get("prompt_tokens") or estimate_tokens(input_text))
            cumulative_context = input_tokens + output_tokens
            packet = {
                "annotation_id": f"{tid}:a{turn}", "trajectory_id": tid, "turn_index": turn,
                "prefix": prefix, "prefix_sha256": sha256_json(messages[:index]),
                "response_sha256": sha256_text(response), "language": seed["language"], "task": seed["task"],
                "input_tokens": input_tokens, "output_tokens": output_tokens,
                "cumulative_tokens": cumulative_context,
                "visible_task_state": {"interaction": seed["interaction"]},
                "private_reference": seed["fixture"].get("reference"),
                "private_checks": seed["fixture"].get("checks", []),
                "verifier_result": verifier_result(seed, response),
            }
            packet["estimated_input_tokens"] = estimate_tokens(packet)
            packets.append(packet)
    return packets


def batch_packets(packets: list[dict[str, Any]], max_tokens: int = 24000) -> list[list[dict[str, Any]]]:
    """At most 8 short/4 long, 24k estimated tokens, and one prefix per trajectory."""
    remaining = list(packets)
    batches: list[list[dict[str, Any]]] = []
    while remaining:
        batch: list[dict[str, Any]] = []
        used: set[str] = set()
        total = 0
        i = 0
        while i < len(remaining):
            packet = remaining[i]
            estimate = int(packet.get("estimated_input_tokens") or estimate_tokens(packet))
            long = estimate > 3000
            limit = 4 if long or any(int(p.get("estimated_input_tokens", 0)) > 3000 for p in batch) else 8
            if packet["trajectory_id"] in used or len(batch) >= limit or total + estimate > max_tokens:
                i += 1
                continue
            batch.append(packet)
            used.add(packet["trajectory_id"])
            total += estimate
            remaining.pop(i)
        if not batch:
            oversized = remaining[0]
            if int(oversized.get("estimated_input_tokens", 0)) > max_tokens:
                raise ValueError(f"annotation packet exceeds {max_tokens} tokens: {oversized['annotation_id']}")
            raise RuntimeError("could not construct annotation batch")
        batches.append(batch)
    return batches


def annotation_prompt(batch: list[dict[str, Any]]) -> str:
    return PROMPT + "\n\nPACKETS:\n" + json.dumps(batch, ensure_ascii=False, sort_keys=True)


def annotate(state: str | pathlib.Path, stage: str, sol: SolClient) -> dict[str, int]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    existing = {r["annotation_id"] for r in read_jsonl(state / stage / "annotations.jsonl")}
    packets = [p for p in build_packets(state, stage) if p["annotation_id"] not in existing]
    batches = batch_packets(packets)
    ledger = CallLedger(state, manifest["config"])
    phase = "smoke" if stage == "smoke" else "annotation"
    written = 0
    for batch in batches:
        ids = [p["annotation_id"] for p in batch]
        prompt = annotation_prompt(batch)
        call_id = f"sol:annotation:{stage}:{sha256_json(ids)[:16]}"
        cached = ledger.reserve(call_id, "sol", phase, {"annotation_ids": ids, "prompt_sha256": sha256_text(prompt),
                                                         "estimated_input_tokens": sum(p["estimated_input_tokens"] for p in batch)})
        if cached is None:
            try:
                result = sol.call(prompt, RESULT_SCHEMA, model="gpt-5.6-sol", effort="high", timeout=900)
                ledger.finish(call_id, result=result)
            except Exception as exc:
                ledger.finish(call_id, error=str(exc)[:1000])
                raise
        else:
            result = cached
        by_id = {r["annotation_id"]: r for r in result.get("annotations", [])}
        if set(by_id) != set(ids):
            raise ValueError("annotation response IDs mismatch")
        packet_by_id = {p["annotation_id"]: p for p in batch}
        for aid in ids:
            p = packet_by_id[aid]
            r = by_id[aid]
            row = Annotation(annotation_id=aid, trajectory_id=p["trajectory_id"], turn_index=p["turn_index"],
                             prefix_sha256=p["prefix_sha256"], response_sha256=p["response_sha256"],
                             language=p["language"], task=p["task"], input_tokens=p["input_tokens"],
                             output_tokens=p["output_tokens"], cumulative_tokens=p["cumulative_tokens"],
                             dimensions=r["dimensions"], local_quality=r["local_quality"], issue_tags=r["issue_tags"],
                             evidence=r["evidence"], confidence=r["confidence"], new_error=r["new_error"],
                             propagated_error=r["propagated_error"], recovery_opportunity=r["recovery_opportunity"],
                             recovery_success=r["recovery_success"], verifier_result=p["verifier_result"]).to_dict()
            row.update({"source_call_id": call_id, "created_utc": utcnow()})
            append_jsonl(state / stage / "annotations.jsonl", row)
            written += 1
    return {"packets": len(packets), "batches": len(batches), "written": written, "existing": len(existing)}


def effective_annotations(state: str | pathlib.Path, stage: str) -> list[dict[str, Any]]:
    state = pathlib.Path(state)
    annotations = read_jsonl(state / stage / "annotations.jsonl")
    decisions = {r["annotation_id"]: r for r in read_jsonl(state / stage / "adjudications.jsonl")}
    out = []
    for row in annotations:
        value = dict(row)
        if row["annotation_id"] in decisions:
            value["raw_local_quality"] = value["local_quality"]
            decision = decisions[row["annotation_id"]]
            value["local_quality"] = decision["decision"]
            if "recovery_opportunity" in decision:
                value["recovery_opportunity"] = bool(decision["recovery_opportunity"])
            if "recovery_success" in decision:
                value["recovery_success"] = bool(decision["recovery_success"])
            value["adjudicated"] = True
        else:
            value["adjudicated"] = False
        out.append(value)
    return out


def mandatory_boundary_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return first-serious and recovery boundary rows from effective labels."""
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        grouped[row["trajectory_id"]].append(row)
    mandatory: dict[str, dict[str, Any]] = {}
    for trajectory_rows in grouped.values():
        ordered = sorted(trajectory_rows, key=lambda r: r["turn_index"])
        first = next((r for r in ordered if r["local_quality"] == "serious"), None)
        if first:
            mandatory[first["annotation_id"]] = first
        for row in ordered:
            if row["recovery_opportunity"]:
                mandatory[row["annotation_id"]] = row
    return mandatory


def calibration_sample(state: str | pathlib.Path, stage: str, n: int = 24, seed: int = 9162602) -> list[dict[str, Any]]:
    state = pathlib.Path(state)
    rows = effective_annotations(state, stage)
    # All serious boundaries and recovery opportunities are mandatory.
    mandatory = mandatory_boundary_rows(rows)
    rng = random.Random(seed)
    remainder = [r for r in rows if r["annotation_id"] not in mandatory]
    # Round-robin across severity/language/depth bins.
    bins: dict[tuple[Any, ...], list[dict[str, Any]]] = collections.defaultdict(list)
    for row in remainder:
        bins[(row["local_quality"], row["language"], 1 if row["turn_index"] <= 2 else 2 if row["turn_index"] <= 5 else 3)].append(row)
    for values in bins.values():
        rng.shuffle(values)
    required_sample_size = min(max(24, n), len(rows))
    selected = list(mandatory.values())
    while len(selected) < required_sample_size and any(bins.values()):
        for key in sorted(bins, key=str):
            if bins[key] and len(selected) < required_sample_size:
                selected.append(bins[key].pop())
    path = state / stage / "calibration.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in selected), encoding="utf-8")
    receipt = {"created_utc": utcnow(), "requested_n": n, "required_sample_size": required_sample_size,
               "sampled_ids": [r["annotation_id"] for r in selected],
               "mandatory_boundary_ids": sorted(mandatory),
               "effective_boundary_ids": sorted(mandatory),
               "required_review_ids": sorted({r["annotation_id"] for r in selected} | set(mandatory)),
               "calibration_sha256": sha256_text(path.read_text(encoding="utf-8"))}
    from common import atomic_json
    atomic_json(state / stage / "calibration_receipt.json", receipt)
    return selected


def adjudicate(state: str | pathlib.Path, stage: str, decisions_path: str | pathlib.Path) -> dict[str, int]:
    state = pathlib.Path(state)
    known = {r["annotation_id"]: r for r in read_jsonl(state / stage / "annotations.jsonl")}
    existing = {r["annotation_id"] for r in read_jsonl(state / stage / "adjudications.jsonl")}
    written = 0
    changed = 0
    for row in read_jsonl(decisions_path):
        aid = row.get("annotation_id")
        if aid not in known:
            raise ValueError(f"unknown annotation {aid}")
        if aid in existing:
            continue
        if row.get("decision") not in SEVERITIES or not str(row.get("evidence", "")).strip() or not str(row.get("reviewer", "")).strip():
            raise ValueError(f"invalid adjudication for {aid}")
        value = {"annotation_id": aid, "trajectory_id": known[aid]["trajectory_id"],
                 "turn_index": known[aid]["turn_index"], "decision": row["decision"],
                 "evidence": row["evidence"], "reviewer": row["reviewer"], "created_utc": utcnow()}
        for optional in ("recovery_opportunity", "recovery_success"):
            if optional in row:
                if not isinstance(row[optional], bool):
                    raise ValueError(f"{optional} must be boolean")
                value[optional] = row[optional]
        append_jsonl(state / stage / "adjudications.jsonl", value)
        written += 1
        changed += row["decision"] != known[aid]["local_quality"]
    all_decisions = read_jsonl(state / stage / "adjudications.jsonl")
    reviewed = len(all_decisions)
    changed_total = sum(r["decision"] != known[r["annotation_id"]]["local_quality"] for r in all_decisions)
    gate = reviewed > 0 and changed_total / reviewed > .2
    summary = {"reviewed": reviewed, "substantive_severity_changes": changed_total,
               "change_share": changed_total / reviewed if reviewed else 0,
               "rubric_revision_required": gate, "created_utc": utcnow()}
    from common import atomic_json
    atomic_json(state / stage / "calibration_review.json", summary)
    return {"written": written, "changed": changed, "reviewed_total": reviewed, "revision_gate": int(gate)}
