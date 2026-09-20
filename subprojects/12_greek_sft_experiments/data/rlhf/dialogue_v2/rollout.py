"""Raw trajectory collection for D1/D2 (plan §8): one unselected Apertus reply per turn, adaptive user, role views.

Every model call is reserved in the call registry before it is sent and replayed from it on resumption, so a rerun
never repeats a completed (charged) call and never blindly retries a failed, reserved or ambiguous one. Conversations
run concurrently (one thread each) so the GPU waits only on the slowest conversation, not on per-wave batching.
"""
from __future__ import annotations

import concurrent.futures as futures
import json
import pathlib
import time
import traceback
from typing import Any

import views
import worlds
from clients import AmbiguousTimeout, ContextLimitError, SolClient, TargetClient, result_from_dict, result_to_dict
from common import append_jsonl, is_c60, read_jsonl, runtime_dir_for, run_tag_for, sha256_json, sha256_text, utcnow
from contracts import (C60_PROTOCOL_VERSION, C60_USER_POLICY_VERSION, DEV_TAGS, GENERATOR_VERSION, MAX_ASSISTANT_TURNS, MODEL_ID, MODEL_REVISION, MODEL_SHA256,
                       PROTOCOL_VERSION, RESOLVER_SCHEMA, SAMPLING, SAMPLING_CONFIG_VERSION, USER_ACTIONS_SCHEMA,
                       USER_DECISION_SCHEMA, USER_POLICY_VERSION, WORLD_RESOLVER_VERSION)
from glossary import Glossary
from ledger import CallAlreadyAttempted, CallLedger
from user_state import allowed_moves, apply_decision, init_state, validate_decision

# Structural problems make a user turn unusable; the rest are policy deviations recorded on the row for review.
HARD_PROBLEMS = ("done must", "final_assessment must", "finish/abandon must", "a non-terminal move needs")
USER_EFFORT = "medium"   # owner, 17 Sept: all pipeline Sol calls at medium
ACTIONS_EFFORT = "medium"
RESOLVER_EFFORT = "medium"


class ConversationEnded(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class Context:
    def __init__(self, target: TargetClient, sol: SolClient, glossary: Glossary, endpoint: str,
                 model: str = MODEL_ID, checkpoint_sha256: str = MODEL_SHA256, dry_run: bool = False,
                 runtime_override: pathlib.Path | None = None, horizon: int = MAX_ASSISTANT_TURNS):
        if horizon != MAX_ASSISTANT_TURNS and not dry_run:
            raise ValueError(f"the collection horizon is fixed at {MAX_ASSISTANT_TURNS} assistant turns")
        if dry_run and runtime_override is None:
            raise ValueError("dry runs must write outside the data runtime directories")
        self.horizon = horizon
        self.target, self.sol, self.glossary = target, sol, glossary
        self.endpoint, self.model, self.checkpoint_sha256 = endpoint, model, checkpoint_sha256
        self.dry_run = dry_run
        self.runtime_override = runtime_override

    def runtime(self, case_id: str) -> pathlib.Path:
        if self.runtime_override is not None:
            return self.runtime_override / run_tag_for(case_id)
        return runtime_dir_for(case_id)


def _row_meta(ctx: Context, seed: dict[str, Any]) -> dict[str, Any]:
    return {"case_id": seed["case_id"], "run": seed["run"], "category": seed["category"],
            "language": seed["language"], "source_family": seed["source_family"], "split": seed["split"],
            "protocol_version": C60_PROTOCOL_VERSION if is_c60(seed["case_id"]) else PROTOCOL_VERSION,
            "generator_version": GENERATOR_VERSION,
            "user_policy_version": C60_USER_POLICY_VERSION if is_c60(seed["case_id"]) else USER_POLICY_VERSION,
            "glossary_sha16": ctx.glossary.sha16,
            "dry_run": ctx.dry_run, **DEV_TAGS}


def _append_once(path: pathlib.Path, key: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    for existing in read_jsonl(path):
        if all(existing.get(k) == v for k, v in key.items()):
            return existing
    append_jsonl(path, row)
    return row


def _sol(ctx: Context, ledger: CallLedger, call_id: str, phase: str, prompt: str, schema: dict[str, Any],
         effort: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Replay a completed call; never retry an ambiguous or reserved one; retry a failed one once (review R1-2/3)."""
    request = {"prompt_sha256": sha256_text(prompt), "schema_sha256": sha256_json(schema), "effort": effort,
               "model": "gpt-5.6-sol", "glossary_sha16": ctx.glossary.sha16, "prompt_chars": len(prompt), **extra}
    last_error = ""
    for attempt, attempt_id in enumerate((call_id, call_id + ":retry1")):
        row = ledger.get(attempt_id)
        if row:
            if row["status"] == "complete":
                return json.loads(row["result"])
            if row["status"] in {"ambiguous", "reserved"}:
                raise ConversationEnded("ambiguous_timeout", f"{attempt_id} status {row['status']}: {row.get('error') or ''}")
            last_error = row.get("error") or ""
            continue
        cached = ledger.reserve(attempt_id, "sol", phase, {**request, **({"retry_of": call_id} if attempt else {})})
        if cached is not None:
            return cached
        started = time.monotonic()
        try:
            result = ctx.sol.call(prompt, schema, model="gpt-5.6-sol", effort=effort, timeout=900)
        except TimeoutError as exc:
            ledger.finish(attempt_id, error=str(exc)[:1000], ambiguous=True, wall_seconds=time.monotonic() - started)
            raise ConversationEnded("ambiguous_timeout", f"{attempt_id}: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            ledger.finish(attempt_id, error=str(exc)[:1000], wall_seconds=time.monotonic() - started)
            last_error = str(exc)
            continue
        ledger.finish(attempt_id, result=result, wall_seconds=time.monotonic() - started)
        prompts_dir = ledger.runtime / "prompts_sent"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        (prompts_dir / (attempt_id.replace(":", "_") + ".txt")).write_text(prompt, encoding="utf-8")
        return result
    raise ConversationEnded("infrastructure_failure", f"{call_id}: failed twice (one retry): {last_error[:500]}")


def _previous_failure(ledger: CallLedger, call_id: str) -> ConversationEnded | None:
    row = ledger.get(call_id)
    if not row or row["status"] == "complete":
        return None
    error = row.get("error") or ""
    if row["status"] == "failed" and "context" in error.lower():
        return ConversationEnded("context_cutoff", error)
    if row["status"] in {"ambiguous", "reserved"}:
        return ConversationEnded("ambiguous_timeout", f"{call_id} status {row['status']}: {error}")
    return ConversationEnded("infrastructure_failure", f"{call_id}: {error}")


def _assistant(ctx: Context, ledger: CallLedger, seed: dict[str, Any], turn: int,
               messages: list[dict[str, str]]) -> dict[str, Any]:
    case_id = seed["case_id"]
    call_id = f"target:{case_id}:t{turn}"
    prior = _previous_failure(ledger, call_id)
    if prior:
        raise prior
    request_messages = views.public_messages(messages)
    leaks = views.find_leaks(json.dumps(request_messages, ensure_ascii=False), views.apertus_private_strings(seed))
    request = {"kind": "raw_rollout", "case_id": case_id, "turn": turn, "prefix_sha256": sha256_json(request_messages),
               "model": ctx.model, "model_revision": MODEL_REVISION, "checkpoint_sha256": ctx.checkpoint_sha256,
               "sampling": SAMPLING, "sampling_config_version": SAMPLING_CONFIG_VERSION, "no_system_prompt": True}
    cached = ledger.reserve(call_id, "target", "raw_rollout", request)
    if cached is not None:
        result = result_from_dict(cached)
    else:
        try:
            result = ctx.target.complete(request_messages, model=ctx.model, **SAMPLING)
        except ContextLimitError as exc:
            ledger.finish(call_id, error=f"context limit: {exc}"[:1000])
            raise ConversationEnded("context_cutoff", str(exc)) from exc
        except AmbiguousTimeout as exc:
            ledger.finish(call_id, error=str(exc)[:1000], ambiguous=True)
            raise ConversationEnded("ambiguous_timeout", str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            ledger.finish(call_id, error=str(exc)[:1000])
            raise ConversationEnded("infrastructure_failure", str(exc)) from exc
        ledger.finish(call_id, result=result_to_dict(result), wall_seconds=result.wall_seconds)
    receipt = {**_row_meta(ctx, seed), "row_id": f"{case_id}:a{turn}", "assistant_turn": turn, "call_id": call_id,
               "prefix_sha256": request["prefix_sha256"], "text_sha256": sha256_text(result.text),
               "finish_reason": result.finish_reason, "truncated": result.finish_reason == "length",
               "served_model": result.model, "usage": result.usage, "wall_seconds": result.wall_seconds,
               "model_revision": MODEL_REVISION, "checkpoint_sha256": ctx.checkpoint_sha256, "sampling": SAMPLING,
               "sampling_config_version": SAMPLING_CONFIG_VERSION, "apertus_prompt_private_string_matches": leaks,
               "created_utc": utcnow()}
    _append_once(ledger.runtime / "assistant_turns.jsonl", {"row_id": receipt["row_id"]}, receipt)
    return {"text": result.text, "finish_reason": result.finish_reason}


def _troubleshooting_step(ctx: Context, ledger: CallLedger, seed: dict[str, Any], state: dict[str, Any],
                          world_state: dict[str, Any], turn: int, messages: list[dict[str, str]]):
    case_id = seed["case_id"]
    aview = views.actions_view(seed, state, messages)
    aprompt = views.actions_prompt(ctx.glossary, seed, aview)
    leaks = views.find_leaks(aprompt, views.already_known(views.evaluator_only_strings(seed) + views.unrevealed_observation_strings(seed, state), state, messages))
    if leaks:
        raise RuntimeError(f"{case_id}: user actions view leaks hidden world strings: {leaks[:2]}")
    actions = _sol(ctx, ledger, f"sol:actions:{case_id}:t{turn}", "user_actions", aprompt, USER_ACTIONS_SCHEMA,
                   ACTIONS_EFFORT, {"case_id": case_id, "turn": turn})
    acts = actions.get("actions", [])[:5]
    resolutions: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    new_world = dict(world_state)
    records = []
    if acts:
        rview = views.resolver_view(seed, state, acts, messages[-1]["content"])
        rprompt = views.resolver_prompt(ctx.glossary, rview)
        resolved = _sol(ctx, ledger, f"sol:resolver:{case_id}:t{turn}", "world_resolver", rprompt, RESOLVER_SCHEMA,
                        RESOLVER_EFFORT, {"case_id": case_id, "turn": turn, "world_resolver_version": WORLD_RESOLVER_VERSION})
        resolutions = resolved.get("resolutions", [])
        by_action: dict[int, list[dict[str, Any]]] = {}
        for res in resolutions:
            by_action.setdefault(int(res.get("action_index", -1)), []).append(res)
        for index, act in enumerate(acts):
            matched = by_action.get(index) or [{"action_index": index, "check_id": "", "status": "unresolved",
                                                "reason": "resolver returned no resolution for this action"}]
            for res in matched:
                cid = res.get("check_id") or ""
                if res.get("status") == "supported" and cid in seed["world"]["checks"]:
                    text, new_world, record = worlds.apply_check(seed["world"], new_world, cid)
                    observations.append({"action": act["action"], "check_id": cid, "status": "supported",
                                         "observation": text, "simulated": True})
                    records.append(record)
                else:
                    # The resolver saw the hidden world: its reason and check id stay in the event's `resolutions`
                    # (evaluator view) and never enter the user-visible observation (review finding R1-1).
                    status = "unresolved" if res.get("status") != "supported" else "unresolved_unknown_check_id"
                    observations.append({"action": act["action"], "check_id": None, "status": status,
                                         "observation": worlds.UNRESOLVED_OBSERVATION, "simulated": True})
    event = {**_row_meta(ctx, seed), "row_id": f"{case_id}:w{turn}", "after_assistant_turn": turn,
             "actions": acts, "skipped_suggestions": actions.get("skipped_suggestions", []),
             "resolutions": resolutions, "observations": observations, "world_state_before": world_state,
             "world_state_after": new_world, "check_records": records,
             "world_resolver_version": WORLD_RESOLVER_VERSION, "created_utc": utcnow()}
    _append_once(ledger.runtime / "world_events.jsonl", {"row_id": event["row_id"]}, event)
    return observations, new_world


def _user_step(ctx: Context, ledger: CallLedger, seed: dict[str, Any], state: dict[str, Any], turn: int,
               messages: list[dict[str, str]], mode: str, new_observations: list[dict[str, Any]] | None):
    case_id = seed["case_id"]
    moves, reasons = allowed_moves(state, mode, seed)
    view = views.user_view(seed, state, messages, mode, new_observations)
    prompt = views.user_prompt(ctx.glossary, seed, view)
    forbidden = views.evaluator_only_strings(seed)
    if seed.get("world"):
        revealed_now = {o["observation"] for o in (new_observations or [])}
        forbidden += [s for s in views.unrevealed_observation_strings(seed, state) if s not in revealed_now]
        forbidden = views.already_known(forbidden, state, messages)
    leaks = views.find_leaks(prompt, forbidden)
    if leaks or views.transfer_answer_leak(seed, prompt):
        raise RuntimeError(f"{case_id}: user view contains evaluator-only material: {leaks[:2]}")
    base_id = f"sol:user:{case_id}:t{turn}" if mode == "next_turn" else f"sol:final:{case_id}"
    decision = _sol(ctx, ledger, base_id, "user_simulation", prompt, USER_DECISION_SCHEMA, USER_EFFORT,
                    {"case_id": case_id, "turn": turn, "mode": mode, "user_policy_version": USER_POLICY_VERSION})
    problems = validate_decision(decision, state, moves, mode, seed)
    call_ids = [base_id]
    repaired = False
    if problems:
        repair_prompt = (prompt + "\n\nYOUR PREVIOUS ANSWER BROKE THESE RULES; answer again following them:\n- "
                         + "\n- ".join(problems) + "\n\nPREVIOUS ANSWER:\n" + json.dumps(decision, ensure_ascii=False))
        repair_id = base_id + ":repair1"
        repaired_decision = _sol(ctx, ledger, repair_id, "user_simulation_repair", repair_prompt, USER_DECISION_SCHEMA,
                                 USER_EFFORT, {"case_id": case_id, "turn": turn, "mode": mode, "repair_of": base_id})
        call_ids.append(repair_id)
        repaired = True
        repaired_problems = validate_decision(repaired_decision, state, moves, mode, seed)
        decision, problems = repaired_decision, repaired_problems
    hard = [p for p in problems if p.startswith(HARD_PROBLEMS)]
    if hard:
        raise ConversationEnded("infrastructure_failure", f"user simulator output unusable after repair: {hard}")
    assistant_texts = [m["content"] for m in messages if m["role"] == "assistant"]
    new_state, transition = apply_decision(state, decision, assistant_texts, turn)
    if new_observations:
        new_state["observations_obtained"] = state["observations_obtained"] + [
            {"after_assistant_turn": turn, **o} for o in new_observations]
    row = {**_row_meta(ctx, seed), "row_id": f"{case_id}:u{turn}" if mode == "next_turn" else f"{case_id}:final",
           "user_turn_index": turn if mode == "next_turn" else None, "follows_assistant_turn": turn, "mode": mode,
           "message": (decision.get("message") or "").strip() if mode == "next_turn" and (not decision["done"] or is_c60(case_id)) else "",
           "move": decision["move"], "done": decision["done"], "new_information": decision["new_information"],
           "trigger": decision["trigger"], "changes_task": decision["changes_task"],
           "assistance_level": decision["assistance_level"], "perceived_latest_reply": decision["perceived_latest_reply"],
           "revealed_private_preference_ids": decision["revealed_private_preference_ids"],
           "task_progress": decision["task_progress"], "knowledge_updates": decision["knowledge_updates"],
           "misconception_status": decision["misconception_status"], "transfer_attempt": decision["transfer_attempt"],
           "private_note": decision["private_note"], "allowed_moves": moves, "allowed_moves_reasons": reasons,
           "policy_violations_after_repair": problems, "repair_used": repaired, "call_ids": call_ids,
           "state_transition": transition, "observations_given": new_observations or [],
           "created_utc": utcnow()}
    _append_once(ledger.runtime / "user_turns.jsonl", {"row_id": row["row_id"]}, row)
    snap = {**_row_meta(ctx, seed), "row_id": f"{case_id}:s{turn}:{mode}", "after_user_decision_for_turn": turn,
            "state": new_state, "created_utc": utcnow()}
    _append_once(ledger.runtime / "user_state_snapshots.jsonl", {"row_id": snap["row_id"]}, snap)
    return decision, new_state


def _snapshot(ctx: Context, ledger: CallLedger, seed: dict[str, Any], messages: list[dict[str, str]],
              ending: str | None, detail: str = "", world_state: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {**_row_meta(ctx, seed), "messages": messages,
           "assistant_turns": sum(m["role"] == "assistant" for m in messages), "ending_reason": ending,
           "ending_detail": detail[:2000], "world_state": world_state, "model": ctx.model,
           "model_revision": MODEL_REVISION, "checkpoint_sha256": ctx.checkpoint_sha256,
           "sampling_config_version": SAMPLING_CONFIG_VERSION, "updated_utc": utcnow()}
    append_jsonl(ledger.runtime / "trajectories.jsonl", row)
    return row


def run_conversation(ctx: Context, seed: dict[str, Any]) -> dict[str, Any]:
    case_id = seed["case_id"]
    ledger = CallLedger(ctx.runtime(case_id), run_tag_for(case_id))
    opening = {"role": "user", "content": seed["opening"]}
    messages = [opening]
    _append_once(ledger.runtime / "user_turns.jsonl", {"row_id": f"{case_id}:u0"},
                 {**_row_meta(ctx, seed), "row_id": f"{case_id}:u0", "user_turn_index": 0, "mode": "opening",
                  "message": seed["opening"], "move": "opening", "created_utc": utcnow()})
    state = init_state(seed)
    world_state = worlds.initial_state(seed["world"]) if seed.get("world") else None
    ending, detail = None, ""
    try:
        for turn in range(1, ctx.horizon + 1):
            reply = _assistant(ctx, ledger, seed, turn, messages)
            messages = [*messages, {"role": "assistant", "content": reply["text"]}]
            if reply["finish_reason"] == "length":
                raise ConversationEnded("truncated_output", f"assistant turn {turn} hit max_tokens {SAMPLING['max_tokens']}")
            if turn == ctx.horizon and is_c60(case_id):
                # amendment: no final-assessment request only because the cap was reached; the cap is the label
                ending, detail = "turn_cap", f"turn limit {ctx.horizon} reached"
                break
            mode = "final_assessment" if turn == ctx.horizon else "next_turn"
            observations = None
            if seed.get("world") and mode == "next_turn":
                observations, world_state = _troubleshooting_step(ctx, ledger, seed, state, world_state, turn, messages)
            decision, state = _user_step(ctx, ledger, seed, state, turn, messages, mode, observations)
            if mode == "final_assessment":
                ending = {"finish": "natural_completion", "abandon": "abandonment"}.get(decision["move"], "horizon")
                detail = f"turn limit {ctx.horizon}; final user assessment: {decision['move']}"
                break
            if decision["done"]:
                if is_c60(case_id) and decision["move"] == "abandon":
                    # silent departure (no message) is a valid ending, distinct from an explicit abandonment message
                    ending = "abandonment" if (decision.get("message") or "").strip() else "silent_departure"
                else:
                    ending = "natural_completion" if decision["move"] == "finish" else "abandonment"
                detail = decision.get("private_note", "")
                break
            messages = [*messages, {"role": "user", "content": decision["message"].strip()}]
            _snapshot(ctx, ledger, seed, messages, None, world_state=world_state)
    except ConversationEnded as end:
        ending, detail = end.reason, end.detail
    except CallAlreadyAttempted as exc:
        row = ledger.get(exc.call_id) if exc.call_id else None
        ending = "ambiguous_timeout" if not row or row["status"] in {"ambiguous", "reserved"} else "infrastructure_failure"
        detail = str(exc)
    except Exception as exc:  # noqa: BLE001
        ending, detail = "infrastructure_failure", f"{exc}\n{traceback.format_exc()[-1500:]}"
    return _snapshot(ctx, ledger, seed, messages, ending, detail, world_state)


def collect(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str], max_workers: int = 10) -> dict[str, Any]:
    results: dict[str, Any] = {}
    with futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        jobs = {pool.submit(run_conversation, ctx, seeds[cid]): cid for cid in case_ids}
        for job in futures.as_completed(jobs):
            cid = jobs[job]
            row = job.result()
            results[cid] = {"assistant_turns": row["assistant_turns"], "ending_reason": row["ending_reason"]}
    return results


def latest_trajectories(runtime: pathlib.Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(runtime / "trajectories.jsonl"):
        out[row["case_id"]] = row
    return out
