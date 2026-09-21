"""Depth-wave rollout state machine with immutable observed completions."""
from __future__ import annotations

import pathlib
from dataclasses import asdict
from typing import Any

from budget import CallLedger
from clients import AmbiguousTimeout, ContextLimitError, SolClient, TargetClient, TargetResult
from common import append_jsonl, atomic_json, estimate_tokens, read_json, read_jsonl, sha256_json, sha256_text, utcnow
from schemas import TERMINAL_CODES, Trajectory
from manifest import seeds_for_stage, validate_generator_isolation

POLICY_PATH = pathlib.Path(__file__).with_name("user_policy.txt")
USER_SCHEMA = {"type": "object", "properties": {
    "done": {"type": "boolean"}, "message": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["done", "message", "reason"], "additionalProperties": False}
USER_BATCH_SCHEMA = {"type": "object", "properties": {
    "users": {"type": "array", "items": {"type": "object", "properties": {
        "trajectory_id": {"type": "string"}, "done": {"type": "boolean"},
        "message": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["trajectory_id", "done", "message", "reason"], "additionalProperties": False}}
    }, "required": ["users"], "additionalProperties": False}
SAMPLING = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 1500, "n": 1}


def target_result_dict(result: TargetResult) -> dict[str, Any]:
    return asdict(result)


def target_result_from_dict(data: dict[str, Any]) -> TargetResult:
    return TargetResult(**data)


def user_prompt(seed: dict[str, Any], messages: list[dict[str, str]], opening: dict[str, Any]) -> str:
    visible = {
        "language": seed["language"], "attitude": seed["attitude"], "register": seed["register"],
        "user_goal": opening["user_goal"], "interaction_plan": opening["interaction_plan"],
        "visible_prefix": messages,
    }
    return POLICY_PATH.read_text(encoding="utf-8") + "\n\nVISIBLE INPUT:\n" + __import__("json").dumps(visible, ensure_ascii=False, sort_keys=True)


def user_batch_prompt(items: list[tuple[dict[str, Any], list[dict[str, str]], dict[str, Any]]]) -> str:
    import json
    visible = []
    for seed, messages, opening in items:
        visible.append({"trajectory_id": seed["trajectory_id"], "language": seed["language"],
                        "attitude": seed["attitude"], "register": seed["register"],
                        "user_goal": opening["user_goal"], "interaction_plan": opening["interaction_plan"],
                        "visible_prefix": messages})
    return POLICY_PATH.read_text(encoding="utf-8") + "\n\nTreat these as independent conversations.\nVISIBLE INPUTS:\n" + json.dumps(visible, ensure_ascii=False, sort_keys=True)


def _opening_map(state: pathlib.Path, stage: str) -> dict[str, dict[str, Any]]:
    return {r["trajectory_id"]: r for r in read_jsonl(state / stage / "user_events.jsonl") if r.get("turn_index") == 0}


def _latest_trajectories(state: pathlib.Path, stage: str) -> dict[str, dict[str, Any]]:
    out = {}
    for row in read_jsonl(state / stage / "trajectories.jsonl"):
        out[row["trajectory_id"]] = row
    return out


def _snapshot(path: pathlib.Path, seed: dict[str, Any], messages: list[dict[str, str]], terminal: str | None,
              detail: str | None = None) -> dict[str, Any]:
    row = Trajectory(seed["trajectory_id"], seed["stage"], messages,
                     sum(m["role"] == "assistant" for m in messages), terminal, detail,
                     seed["instance_hash"], seed["content_family"], seed["split"]).to_dict()
    row["updated_utc"] = utcnow()
    append_jsonl(path, row)
    return row


def _completed_user_followup(ledger: CallLedger, stage: str, turn: int, trajectory_id: str) -> tuple[dict[str, Any], str] | None:
    """Recover a member result even after a crash part-way through batch apply."""
    prefix = f"sol:user:{stage}:wave{turn}:"
    with ledger.db() as db:
        rows = db.execute("SELECT call_id,request,result FROM calls WHERE provider='sol' AND status='complete' AND call_id LIKE ?",
                          (prefix + "%",)).fetchall()
    import json
    for row in rows:
        request = json.loads(row["request"])
        if trajectory_id not in request.get("trajectory_ids", []):
            continue
        result = json.loads(row["result"])
        match = next((value for value in result.get("users", []) if value.get("trajectory_id") == trajectory_id), None)
        if match is None:
            raise ValueError(f"completed user batch {row['call_id']} lacks {trajectory_id}")
        return match, str(row["call_id"])
    return None


def _apply_followup(state: pathlib.Path, stage: str, path: pathlib.Path, seed: dict[str, Any],
                    messages: list[dict[str, str]], turn: int, follow: dict[str, Any], call_id: str) -> dict[str, Any]:
    tid = seed["trajectory_id"]
    if follow.get("done"):
        return _snapshot(path, seed, messages, "completed", str(follow.get("reason", "")))
    content = str(follow.get("message", "")).strip()
    if not content:
        return _snapshot(path, seed, messages, "infra_failure", "empty simulated user turn")
    user = {"role": "user", "content": content}
    messages = [*messages, user]
    event_id = f"{tid}:u{turn}"
    prior = next((row for row in read_jsonl(state / stage / "user_events.jsonl") if row.get("event_id") == event_id), None)
    if prior and prior.get("message") != user:
        raise ValueError(f"immutable user event {event_id} disagrees with recovered Sol result")
    if not prior:
        append_jsonl(state / stage / "user_events.jsonl", {
            "event_id": event_id, "trajectory_id": tid, "stage": stage, "kind": "user",
            "turn_index": turn, "message": user, "created_utc": utcnow(), "source_call_id": call_id})
    return _snapshot(path, seed, messages, None)


def ensure_runtime_config(state: pathlib.Path, target: TargetClient, endpoint: str, model: str,
                          checkpoint_sha256: str, ledger: CallLedger) -> dict[str, Any]:
    if len(checkpoint_sha256) != 64 or any(c not in "0123456789abcdef" for c in checkpoint_sha256):
        raise ValueError("lowercase checkpoint SHA-256 required")
    path = state / "runtime_config.json"
    if path.exists():
        old = read_json(path)
        if old["requested_model"] != model or old["checkpoint_sha256"] != checkpoint_sha256:
            raise ValueError("runtime model/checkpoint identity is immutable")
        return old
    call_id = f"target:preflight:{sha256_json([endpoint, model, checkpoint_sha256])[:16]}"
    cached = ledger.reserve(call_id, "target", "preflight", {"endpoint": endpoint, "kind": "models"})
    if cached is None:
        try:
            ids = target.models()
            result = {"served_models": ids}
            ledger.finish(call_id, result=result)
        except Exception as exc:
            ledger.finish(call_id, error=str(exc)[:1000])
            raise
    else:
        ids = cached["served_models"]
    if model not in ids:
        raise ValueError(f"requested model {model!r} absent from /v1/models: {ids}")
    config = {"endpoint": endpoint, "requested_model": model, "served_model_id": model,
              "checkpoint_sha256": checkpoint_sha256, "sampling": SAMPLING,
              "no_system_prompt": True, "recorded_utc": utcnow(), "preflight_call_id": call_id}
    atomic_json(path, config)
    receipt_path = state / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    receipt.setdefault("artifacts", {})["runtime_config.json"] = {
        "sha256": sha256_text(path.read_text(encoding="utf-8")), "created_utc": utcnow(), "frozen": True}
    atomic_json(receipt_path, receipt)
    return config


def sample_assistant(ledger: CallLedger, target: TargetClient, stage: str, trajectory_id: str,
                     turn: int, messages: list[dict[str, str]], model: str,
                     checkpoint_sha256: str) -> TargetResult:
    call_id = f"target:rollout:{stage}:{trajectory_id}:t{turn}"
    request = {"kind": "raw_rollout", "trajectory_id": trajectory_id, "turn_index": turn,
               "prefix_sha256": sha256_json(messages), "checkpoint_sha256": checkpoint_sha256,
               "sampling": SAMPLING}
    cached = ledger.reserve(call_id, "target", "raw_rollout", request)
    if cached is not None:
        return target_result_from_dict(cached)
    try:
        result = target.complete(messages, model=model, **SAMPLING)
        ledger.finish(call_id, result=target_result_dict(result))
        return result
    except AmbiguousTimeout as exc:
        ledger.finish(call_id, error=str(exc)[:1000], ambiguous=True)
        raise
    except Exception as exc:
        ledger.finish(call_id, error=str(exc)[:1000])
        raise


def validate_stage_horizon(stage: str, max_turns: int | None) -> int:
    """Resolve the immutable horizon for a stage before any external action."""
    expected = {"smoke": 3, "measurement": 8}.get(stage)
    if expected is None:
        raise ValueError(f"unknown rollout stage {stage!r}")
    horizon = expected if max_turns is None else max_turns
    if horizon != expected:
        raise ValueError(f"{stage} rollout horizon must be exactly {expected}, got {horizon}")
    return horizon


def rollout(state: str | pathlib.Path, stage: str, target: TargetClient, sol: SolClient, endpoint: str,
            model: str, checkpoint_sha256: str, max_turns: int | None = None,
            concurrency: int = 8, crash_hook=None) -> dict[str, int]:
    horizon = validate_stage_horizon(stage, max_turns)
    del concurrency  # Waves are deterministic; client/server may independently batch internally.
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    validate_generator_isolation(state, stage)
    ledger = CallLedger(state, manifest["config"])
    ensure_runtime_config(state, target, endpoint, model, checkpoint_sha256, ledger)
    seeds = seeds_for_stage(state, stage)
    openings = _opening_map(state, stage)
    missing = [s["trajectory_id"] for s in seeds if s["trajectory_id"] not in openings]
    if missing:
        raise ValueError(f"openings missing for {len(missing)} trajectories")
    latest = _latest_trajectories(state, stage)
    path = state / stage / "trajectories.jsonl"
    for seed in seeds:
        if seed["trajectory_id"] not in latest:
            latest[seed["trajectory_id"]] = _snapshot(path, seed, [openings[seed["trajectory_id"]]["message"]], None)
    terminal_counts: dict[str, int] = {}
    # One assistant response per trajectory per depth wave.
    for turn in range(1, horizon + 1):
        pending_followups: list[tuple[dict[str, Any], list[dict[str, str]], dict[str, Any]]] = []
        for seed in seeds:
            tid = seed["trajectory_id"]
            row = latest[tid]
            if row.get("terminal_code"):
                continue
            messages = list(row["messages"])
            if row["assistant_turns"] == turn and messages[-1]["role"] == "assistant":
                pending_followups.append((seed, messages, openings[tid]))
                continue
            if row["assistant_turns"] >= turn:
                continue
            if messages[-1]["role"] != "user":
                raise RuntimeError(f"active trajectory {tid} has inconsistent pending state")
            try:
                result = sample_assistant(ledger, target, stage, tid, turn, messages, model, checkpoint_sha256)
            except AmbiguousTimeout as exc:
                latest[tid] = _snapshot(path, seed, messages, "ambiguous_timeout", str(exc))
                continue
            except ContextLimitError as exc:
                latest[tid] = _snapshot(path, seed, messages, "context_limit", str(exc))
                continue
            except Exception as exc:
                latest[tid] = _snapshot(path, seed, messages, "infra_failure", str(exc))
                continue
            if crash_hook:
                crash_hook("after_target_completion", tid, turn)
            assistant = {"role": "assistant", "content": result.text}
            messages.append(assistant)
            receipt = {"text_sha256": sha256_text(result.text), "finish_reason": result.finish_reason,
                       "truncated": result.finish_reason == "length", "model": result.model,
                       "usage": result.usage, "wall_seconds": result.wall_seconds,
                       "checkpoint_sha256": checkpoint_sha256, "sampling": SAMPLING}
            append_jsonl(state / "ledger.jsonl", {"record": "observed_completion", "provider": "target",
                                                   "trajectory_id": tid, "turn_index": turn,
                                                   "created_utc": utcnow(), "receipt": receipt})
            if result.finish_reason == "length":
                latest[tid] = _snapshot(path, seed, messages, "truncated_output")
                continue
            if turn >= horizon:
                latest[tid] = _snapshot(path, seed, messages, "horizon")
                continue
            latest[tid] = _snapshot(path, seed, messages, None)
            if crash_hook:
                crash_hook("after_assistant_snapshot", tid, turn)
            pending_followups.append((seed, messages, openings[tid]))
        unrecovered = []
        for seed, messages, opening in pending_followups:
            cached_member = _completed_user_followup(ledger, stage, turn, seed["trajectory_id"])
            if cached_member is None:
                unrecovered.append((seed, messages, opening))
                continue
            follow, member_call_id = cached_member
            latest[seed["trajectory_id"]] = _apply_followup(state, stage, path, seed, messages, turn, follow, member_call_id)
        pending_followups = unrecovered
        # Sol advances several independent trajectories in one call, after all
        # actual target responses for this wave exist.
        for offset in range(0, len(pending_followups), 8):
            batch = pending_followups[offset:offset + 8]
            ids = [item[0]["trajectory_id"] for item in batch]
            prompt = user_batch_prompt(batch)
            phase = "smoke" if stage == "smoke" else "user_continuation"
            call_id = f"sol:user:{stage}:wave{turn}:{sha256_json(ids)[:16]}"
            cached = ledger.reserve(call_id, "sol", phase, {"trajectory_ids": ids, "turn_index": turn,
                                                             "prompt_sha256": sha256_text(prompt),
                                                             "estimated_input_tokens": estimate_tokens(prompt)})
            if cached is None:
                try:
                    result = sol.call(prompt, USER_BATCH_SCHEMA, model="gpt-5.6-sol", effort="high", timeout=900)
                    ledger.finish(call_id, result=result)
                except TimeoutError as exc:
                    ledger.finish(call_id, error=str(exc)[:1000], ambiguous=True)
                    for seed, messages, _ in batch:
                        latest[seed["trajectory_id"]] = _snapshot(path, seed, messages, "ambiguous_timeout", str(exc))
                    continue
                except Exception as exc:
                    ledger.finish(call_id, error=str(exc)[:1000])
                    for seed, messages, _ in batch:
                        latest[seed["trajectory_id"]] = _snapshot(path, seed, messages, "infra_failure", str(exc))
                    continue
                if crash_hook:
                    crash_hook("after_sol_completion", ids[0], turn)
            else:
                result = cached
            by_id = {row["trajectory_id"]: row for row in result.get("users", [])}
            if set(by_id) != set(ids):
                raise ValueError("simulated-user batch IDs mismatch")
            for seed, messages, _ in batch:
                tid = seed["trajectory_id"]
                follow = by_id[tid]
                latest[tid] = _apply_followup(state, stage, path, seed, messages, turn, follow, call_id)
    for row in latest.values():
        code = row.get("terminal_code") or "active"
        terminal_counts[code] = terminal_counts.get(code, 0) + 1
    return terminal_counts
