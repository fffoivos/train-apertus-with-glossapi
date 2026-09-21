"""Prefix-safe Sol generation of opening user turns."""
from __future__ import annotations

import pathlib
from typing import Any

from budget import CallLedger
from clients import SolClient
from common import append_jsonl, canonical, estimate_tokens, read_json, read_jsonl, sha256_json, utcnow
from manifest import seeds_for_stage, validate_generator_isolation

OPENING_SCHEMA = {
    "type": "object", "properties": {
        "openings": {"type": "array", "items": {"type": "object", "properties": {
            "trajectory_id": {"type": "string"}, "message": {"type": "string"},
            "user_goal": {"type": "string"}, "interaction_plan": {"type": "string"},
        }, "required": ["trajectory_id", "message", "user_goal", "interaction_plan"], "additionalProperties": False}}
    }, "required": ["openings"], "additionalProperties": False,
}


def opening_prompt(seeds: list[dict[str, Any]]) -> str:
    public = []
    for seed in seeds:
        fixture = seed["fixture"]
        public.append({
            "trajectory_id": seed["trajectory_id"], "language": seed["language"], "task": seed["task"],
            "difficulty": seed["difficulty"], "interaction": seed["interaction"],
            "attitude": seed["attitude"], "register": seed["register"],
            "source_content": fixture["content"], "opening_instruction": fixture["instruction_spec"],
            **({"smoke_scenario_instruction": seed["scenario_instruction"]} if seed.get("scenario_instruction") else {}),
        })
    return (
        "Write one natural opening user message for each independent seed below. Use the source content and opening "
        "instruction, assigned language/register and interaction plan. Do not answer the task. Return a concise public "
        "user_goal and interaction_plan that can guide later user turns without revealing any reference answer or check.\n\n"
        + canonical(public)
    )


def generate_openings(state: str | pathlib.Path, stage: str, sol: SolClient, limit: int | None = None,
                      batch_size: int = 8) -> dict[str, int]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    validate_generator_isolation(state, stage)
    seeds = seeds_for_stage(state, stage)
    existing = {r["trajectory_id"] for r in read_jsonl(state / stage / "user_events.jsonl") if r.get("turn_index") == 0}
    todo = [s for s in seeds if s["trajectory_id"] not in existing]
    if limit is not None:
        todo = todo[:limit]
    ledger = CallLedger(state, manifest["config"])
    written = 0
    phase = "smoke" if stage == "smoke" else "openings"
    for offset in range(0, len(todo), batch_size):
        batch = todo[offset:offset + batch_size]
        ids = [s["trajectory_id"] for s in batch]
        call_id = f"sol:openings:{stage}:{sha256_json(ids)[:16]}"
        prompt = opening_prompt(batch)
        request = {"kind": "openings", "trajectory_ids": ids, "prompt_sha256": sha256_json(prompt),
                   "estimated_input_tokens": estimate_tokens(prompt)}
        cached = ledger.reserve(call_id, "sol", phase, request)
        if cached is None:
            try:
                result = sol.call(prompt, OPENING_SCHEMA, model="gpt-5.6-sol", effort="high", timeout=900)
                ledger.finish(call_id, result=result)
            except Exception as exc:
                ledger.finish(call_id, error=str(exc)[:1000])
                raise
        else:
            result = cached
        by_id = {row["trajectory_id"]: row for row in result.get("openings", [])}
        if set(by_id) != set(ids):
            raise ValueError("Sol opening batch IDs do not match request")
        for seed in batch:
            row = by_id[seed["trajectory_id"]]
            message = row["message"].strip()
            if not message:
                raise ValueError("empty opening")
            append_jsonl(state / stage / "user_events.jsonl", {
                "event_id": f"{seed['trajectory_id']}:u0", "trajectory_id": seed["trajectory_id"],
                "stage": stage, "kind": "user", "turn_index": 0,
                "message": {"role": "user", "content": message}, "created_utc": utcnow(),
                "user_goal": row["user_goal"], "interaction_plan": row["interaction_plan"],
                "source_call_id": call_id,
            })
            written += 1
    return {"written": written, "existing": len(existing), "requested": len(todo)}
