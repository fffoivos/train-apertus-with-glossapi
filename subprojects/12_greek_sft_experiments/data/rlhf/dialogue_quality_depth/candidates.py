"""Original plus two fresh candidates under an exact shared prefix."""
from __future__ import annotations

import pathlib
from typing import Any

from budget import CallLedger
from clients import TargetClient
from common import append_jsonl, read_json, read_jsonl, sha256_text, utcnow
from rollout import SAMPLING, ensure_runtime_config, target_result_dict, target_result_from_dict
from schemas import Candidate, prefix_sha256


def generate_candidates(state: str | pathlib.Path, stage: str, target: TargetClient, endpoint: str,
                        model: str, checkpoint_sha256: str) -> dict[str, int]:
    if stage != "measurement":
        raise ValueError("candidate generation is measurement-only")
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    ledger = CallLedger(state, manifest["config"])
    ensure_runtime_config(state, target, endpoint, model, checkpoint_sha256, ledger)
    selections = [r for r in read_jsonl(state / stage / "selection.jsonl")
                  if r.get("inclusion_receipt", {}).get("origin") != "resample"]
    path = state / stage / "candidates.jsonl"
    existing = {r["candidate_id"] for r in read_jsonl(path)}
    written = 0
    for selection in selections:
        actual_hash = prefix_sha256(selection["prefix_messages"])
        if actual_hash != selection["prefix_sha256"]:
            raise ValueError("selection prefix changed")
        original_id = selection["selection_id"] + ":c0"
        if original_id not in existing:
            raw_call = ledger.get(f"target:rollout:{stage}:{selection['trajectory_id']}:t{selection['depth']}")
            raw_result = __import__("json").loads(raw_call["result"]) if raw_call and raw_call.get("result") else {}
            row = Candidate(original_id, selection["selection_id"], "original", selection["original_response"],
                            sha256_text(selection["original_response"]), actual_hash,
                            str(raw_result.get("finish_reason", "observed")), str(raw_result.get("model", model)),
                            raw_result.get("usage", {})).to_dict()
            row.update({"wall_seconds": raw_result.get("wall_seconds"),
                        "source_call_id": f"target:rollout:{stage}:{selection['trajectory_id']}:t{selection['depth']}",
                        "created_utc": utcnow()})
            append_jsonl(path, row); written += 1
        for k in (1, 2):
            candidate_id = selection["selection_id"] + f":c{k}"
            if candidate_id in existing:
                continue
            call_id = f"target:candidate:{stage}:{candidate_id}"
            request = {"kind": "candidate", "candidate_id": candidate_id, "prefix_sha256": actual_hash,
                       "checkpoint_sha256": checkpoint_sha256, "sampling": SAMPLING}
            cached = ledger.reserve(call_id, "target", "candidate_sampling", request)
            if cached is None:
                try:
                    result = target.complete(selection["prefix_messages"], model=model, **SAMPLING)
                    ledger.finish(call_id, result=target_result_dict(result))
                except Exception as exc:
                    ledger.finish(call_id, error=str(exc)[:1000], ambiguous=isinstance(exc, TimeoutError))
                    raise
            else:
                result = target_result_from_dict(cached)
            row = Candidate(candidate_id, selection["selection_id"], "new", result.text, sha256_text(result.text),
                            actual_hash, result.finish_reason, result.model, result.usage).to_dict()
            row.update({"wall_seconds": result.wall_seconds, "source_call_id": call_id, "created_utc": utcnow()})
            append_jsonl(path, row); written += 1
    return {"selections": len(selections), "written": written, "existing": len(existing)}
