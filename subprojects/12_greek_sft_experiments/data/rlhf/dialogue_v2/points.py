"""Sampling points on saved trajectories (plan §6, spec §4.8) and D1 selection (at most two per conversation).

Prevention: prefix ends immediately before the first seriously erroneous assistant reply (turn 1 = single-turn material).
Supported recovery: prefix ends immediately after the first genuinely helpful user intervention following that error.
Healthy continuation: a deeper assistant turn with no earlier serious error where a meaningful next task exists.
Nothing is invented to fill a cell; maths-content points are held for the specialist maths judge.
"""
from __future__ import annotations

from typing import Any

from common import append_jsonl, read_jsonl, run_tag_for, sha256_json, utcnow
from contracts import (CANDIDATES_MAX, DEV_TAGS, HELPING_ABILITY, HELPFUL_MOVES, MAX_POINTS_PER_D1_CONVERSATION,
                       SAMPLING, SERVED_CONTEXT)
from rollout import latest_trajectories


def _assistant_positions(messages: list[dict[str, str]]) -> list[int]:
    return [i for i, m in enumerate(messages) if m["role"] == "assistant"]


def _prompt_tokens(runtime, case_id: str, turn: int) -> int | None:
    for row in read_jsonl(runtime / "assistant_turns.jsonl"):
        if row["case_id"] == case_id and row["assistant_turn"] == turn:
            return int((row.get("usage") or {}).get("prompt_tokens") or 0) or None
    return None


def possible_points(seed: dict[str, Any], runtime) -> dict[str, Any]:
    cid = seed["case_id"]
    trajectory = latest_trajectories(runtime)[cid]
    messages = trajectory["messages"]
    positions = _assistant_positions(messages)
    evals = {r["assistant_turn"]: r for r in read_jsonl(runtime / "turn_evaluations.jsonl") if r["case_id"] == cid}
    users = {r.get("user_turn_index"): r for r in read_jsonl(runtime / "user_turns.jsonl")
             if r["case_id"] == cid and r.get("mode") == "next_turn"}
    review = next((r for r in read_jsonl(runtime / "conversation_reviews.jsonl") if r["case_id"] == cid), None)
    helpful_by_review = {u["user_turn_index"]: u for u in (review or {}).get("user_turns", [])}
    serious = sorted(t for t, e in evals.items() if e["local_quality"] == "serious")
    first_serious = serious[0] if serious else None
    points: list[dict[str, Any]] = []

    def make(kind: str, before_turn: int, prefix_end: int, reason: str, extra: dict[str, Any]) -> dict[str, Any]:
        prefix = messages[:prefix_end]
        tokens = _prompt_tokens(runtime, cid, before_turn)
        fits = tokens is not None and tokens + SAMPLING["max_tokens"] <= SERVED_CONTEXT
        maths = bool(evals.get(before_turn, {}).get("maths_content")) if before_turn in evals else bool(seed.get("maths_content"))
        last_user = users.get(before_turn - 1) if before_turn > 1 else None
        return {"point_id": f"{cid}:{kind}:a{before_turn}", "case_id": cid, "kind": kind,
                "before_assistant_turn": before_turn, "prefix_messages": prefix, "prefix_sha256": sha256_json(prefix),
                "prefix_prompt_tokens": tokens, "fits_context_with_cap": fits,
                "single_turn_material": kind == "prevention" and before_turn == 1,
                "maths_content_hold": maths, "reason": reason,
                "assistance_level_of_last_user_turn": (last_user or {}).get("assistance_level", "none" if before_turn == 1 else None),
                "last_user_move": (last_user or {}).get("move", "opening" if before_turn == 1 else None),
                "original_reply_quality": evals.get(before_turn, {}).get("local_quality"), **extra}

    if first_serious is not None:
        points.append(make("prevention", first_serious, positions[first_serious - 1],
                           f"first serious reply at assistant turn {first_serious}: {evals[first_serious].get('error_summary', '')}", {}))
        for t in range(first_serious, len(positions) + 1):
            user = users.get(t)
            if not user or user.get("done") or user.get("move") not in HELPFUL_MOVES:
                continue
            verdict = helpful_by_review.get(t)
            if verdict is not None and not verdict.get("genuinely_helpful"):
                continue
            if t + 1 > len(positions) and trajectory["ending_reason"] != "context_cutoff":
                continue
            prefix_end = positions[t] if t < len(positions) else len(messages)
            points.append(make("supported_recovery", t + 1, prefix_end,
                               f"user turn {t} ({user['move']}, {user.get('assistance_level')}) after the serious error at turn {first_serious}",
                               {"helpful_user_turn": t, "helpfulness_confirmed_by_review": verdict is not None}))
            break
    for d in range(2, len(positions) + 1):
        if first_serious is not None and first_serious < d:
            break
        previous = evals.get(d - 1)
        if not previous or not previous.get("meaningful_next_task_exists"):
            continue
        user = users.get(d - 1)
        if not user or user.get("move") in {"restate", "express_frustration", "abandon", "finish"}:
            continue
        points.append(make("healthy_continuation", d, positions[d - 1],
                           f"assistant turn {d} with no earlier serious error; user turn {d - 1} = {user.get('move')}", {}))
    return {"case_id": cid, "first_serious_turn": first_serious, "serious_turns": serious, "points": points,
            "review_points": (review or {}).get("possible_sampling_points", [])}


def select_d1(seed: dict[str, Any], runtime, possible: dict[str, Any]) -> list[dict[str, Any]]:
    usable = [p for p in possible["points"] if p["fits_context_with_cap"] and not p["maths_content_hold"]]
    chosen: list[dict[str, Any]] = []
    for kind in ("prevention", "supported_recovery"):
        match = next((p for p in usable if p["kind"] == kind), None)
        if match:
            chosen.append(match)
    healthy = [p for p in usable if p["kind"] == "healthy_continuation"
               and p["prefix_sha256"] not in {c["prefix_sha256"] for c in chosen}]
    if len(chosen) < MAX_POINTS_PER_D1_CONVERSATION and healthy:
        chosen.append(max(healthy, key=lambda p: p["before_assistant_turn"]))
    return chosen[:MAX_POINTS_PER_D1_CONVERSATION]


def possible_points_c60(seed: dict[str, Any], runtime) -> dict[str, Any]:
    """Amendment rule. A: prefix ending immediately before the first seriously erroneous reply. B: prefix ending immediately
    after the first user turn, following that error, that changes the instructions (clarification, example, simplification,
    decomposition, new constraint, changed goal, supplied solution), whether or not it helped. Complaints and restatements
    are not changes. Every change point is recorded with its labels; healthy continuations are recorded but not sampled."""
    from contracts import INSTRUCTION_CHANGE_MOVES
    cid = seed["case_id"]
    trajectory = latest_trajectories(runtime)[cid]
    messages = trajectory["messages"]
    positions = _assistant_positions(messages)
    evals = {r["assistant_turn"]: r for r in read_jsonl(runtime / "turn_evaluations.jsonl") if r["case_id"] == cid}
    users = {r.get("user_turn_index"): r for r in read_jsonl(runtime / "user_turns.jsonl")
             if r["case_id"] == cid and r.get("mode") == "next_turn"}
    review = next((r for r in read_jsonl(runtime / "conversation_reviews.jsonl") if r["case_id"] == cid), {})
    reviewed_users = {u["user_turn_index"]: u for u in review.get("user_turns", [])}
    serious = sorted(t for t, e in evals.items() if e["local_quality"] == "serious")
    first_serious = serious[0] if serious else None
    points, change_points, absent = [], [], {}

    def make(kind, before_turn, prefix_end, reason, extra):
        prefix = messages[:prefix_end]
        tokens = _prompt_tokens(runtime, cid, before_turn)
        fits = tokens is not None and tokens + SAMPLING["max_tokens"] <= SERVED_CONTEXT
        last_user = users.get(before_turn - 1) if before_turn > 1 else None
        return {"point_id": f"{cid}:{kind}:a{before_turn}", "case_id": cid, "kind": kind, "before_assistant_turn": before_turn,
                "prefix_messages": prefix, "prefix_sha256": sha256_json(prefix), "prefix_prompt_tokens": tokens,
                "fits_context_with_cap": fits, "single_turn_material": kind == "A" and before_turn == 1,
                "maths_content_hold": False, "reason": reason,
                "assistance_level_of_last_user_turn": (last_user or {}).get("assistance_level", "none" if before_turn == 1 else None),
                "last_user_move": (last_user or {}).get("move", "opening" if before_turn == 1 else None),
                "original_reply_quality": evals.get(before_turn, {}).get("local_quality"), **extra}

    if first_serious is None:
        absent["A"] = "no seriously erroneous reply" if evals else "not reviewed"
        absent["B"] = "no serious error to follow"
    else:
        points.append(make("A", first_serious, positions[first_serious - 1],
                           f"first serious reply at assistant turn {first_serious}: {evals[first_serious].get('error_summary', '')}", {}))
        for t in range(first_serious, len(positions) + 1):
            user = users.get(t)
            if not user:
                continue
            rv = reviewed_users.get(t, {})
            by_sim = user.get("move") in INSTRUCTION_CHANGE_MOVES or bool(user.get("changes_task"))
            by_review = rv.get("instruction_change")
            is_change = by_review if by_review is not None else by_sim
            record = {"user_turn": t, "move": user.get("move"), "changes_task": user.get("changes_task"),
                      "assistance_level": user.get("assistance_level"), "instruction_change": bool(is_change),
                      "simulator_says_change": by_sim, "review_says_change": by_review,
                      "change_type": rv.get("change_type"), "change_quality": rv.get("change_quality"),
                      "has_message": bool((user.get("message") or "").strip()) and not user.get("done")}
            change_points.append(record)
        b = next((c for c in change_points if c["instruction_change"] and c["has_message"]), None)
        if b is None:
            absent["B"] = ("the conversation ended before any user turn followed the error" if not change_points
                           else "no instruction change after the first serious error (complaints, restatements or silent ending only)")
        else:
            t = b["user_turn"]
            prefix_end = positions[t] if t < len(positions) else len(messages)
            points.append(make("B", t + 1, prefix_end,
                               f"user turn {t} ({b['move']}; {b['change_type'] or 'change'}; {b['change_quality'] or 'unlabelled'}) after the serious error at turn {first_serious}",
                               {"change_user_turn": t, "change_type": b["change_type"], "change_quality": b["change_quality"]}))
    healthy = []
    for d in range(2, len(positions) + 1):
        if first_serious is not None and first_serious < d:
            break
        user = users.get(d - 1)
        if user and user.get("move") not in {"restate", "express_frustration", "abandon", "finish"}:
            healthy.append({"before_assistant_turn": d, "last_user_move": user.get("move")})
    return {"case_id": cid, "first_serious_turn": first_serious, "points": points, "change_points": change_points,
            "absent": absent, "healthy_continuations_recorded": healthy,
            "review_proposed": {"A": review.get("proposed_A"), "B": review.get("proposed_B")}}


def write_points_c60(seeds: dict[str, dict[str, Any]], case_ids: list[str], runtime_for) -> dict[str, Any]:
    from contracts import C60_BRANCH_RULE_VERSION, C60_CANDIDATES
    summary: dict[str, Any] = {}
    for cid in case_ids:
        runtime = runtime_for(cid)
        if cid not in latest_trajectories(runtime):
            continue
        if cid in {r["case_id"] for r in read_jsonl(runtime / "sampling_points.jsonl")}:
            continue
        possible = possible_points_c60(seeds[cid], runtime)
        selected = [p for p in possible["points"] if p["fits_context_with_cap"]]
        not_fitting = [p["point_id"] for p in possible["points"] if not p["fits_context_with_cap"]]
        append_jsonl(runtime / "sampling_points.jsonl", {
            "case_id": cid, "run_tag": run_tag_for(cid), "first_serious_turn": possible["first_serious_turn"],
            "possible_points": possible["points"], "selected_point_ids": [p["point_id"] for p in selected],
            "change_points": possible["change_points"], "absent": possible["absent"], "not_fitting_context": not_fitting,
            "healthy_continuations_recorded": possible["healthy_continuations_recorded"], "review_proposed": possible["review_proposed"],
            "selection_rule": "c60: A and B where they exist and fit the context; healthy continuations recorded, not sampled",
            "branch_rule_version": C60_BRANCH_RULE_VERSION, "created_utc": utcnow(), **DEV_TAGS})
        for point in selected:
            append_jsonl(runtime / "branch_points.jsonl", {**point, "candidates_planned": C60_CANDIDATES, "created_utc": utcnow(), **DEV_TAGS})
        summary[cid] = {"selected": [p["point_id"] for p in selected], "absent": possible["absent"]}
    return summary


def write_points(seeds: dict[str, dict[str, Any]], case_ids: list[str], runtime_for) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for cid in case_ids:
        runtime = runtime_for(cid)
        if cid not in latest_trajectories(runtime):
            continue
        existing = {r["case_id"] for r in read_jsonl(runtime / "sampling_points.jsonl")}
        possible = possible_points(seeds[cid], runtime)
        selected = select_d1(seeds[cid], runtime, possible) if cid.startswith("DVI") else []
        held = [p["point_id"] for p in possible["points"] if p["maths_content_hold"]]
        if cid not in existing:
            append_jsonl(runtime / "sampling_points.jsonl", {
                "case_id": cid, "run_tag": run_tag_for(cid), "first_serious_turn": possible["first_serious_turn"],
                "possible_points": possible["points"], "review_suggested_points": possible["review_points"],
                "selected_point_ids": [p["point_id"] for p in selected], "held_for_maths_judge": held,
                "selection_rule": ("D1: prevention and supported recovery where they exist; otherwise the deepest healthy "
                                   "continuation; at most two; context-fitting; maths held. D2: marked only, no candidates."),
                "created_utc": utcnow(), **DEV_TAGS})
            for point in selected:
                append_jsonl(runtime / "branch_points.jsonl", {**point, "candidates_planned": CANDIDATES_MAX,
                                                                "created_utc": utcnow(), **DEV_TAGS})
        summary[cid] = {"possible": [p["point_id"] for p in possible["points"]],
                        "selected": [p["point_id"] for p in selected], "held_for_maths_judge": held}
    return summary
