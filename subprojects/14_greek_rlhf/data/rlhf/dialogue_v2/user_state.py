"""User state schema and deterministic transition logic for the adaptive user (plan §4, spec §4.7-§4.8).

Sol proposes the user's decision from its private view; this module decides which moves are allowed before the
call (strategy change after a failed restatement, helping ability, patience) and applies/validates the result.
"""
from __future__ import annotations

import copy
from typing import Any

from contracts import FAILURE_RESPONSE_MOVES, HELPING_ABILITY, INSTRUCTION_CHANGE_MOVES, MOVES, PATIENCE_TOLERANCE, TERMINAL_MOVES

ASSISTANCE_ORDER = {"none": 0, "restatement": 1, "pointed_defect": 2, "partial_scaffold_or_example": 3,
                    "supplied_solution": 4}


def init_state(seed: dict[str, Any]) -> dict[str, Any]:
    us = seed["user_state"]
    state = {
        "goal": us["goal"], "known_facts": list(us.get("known_facts", [])), "expertise": us["expertise"],
        "misconception": us.get("misconception", ""),
        "disclosed_preferences": list(us.get("disclosed_preferences", [])),
        "private_preferences": copy.deepcopy(us.get("private_preferences", [])),
        "revealed_preferences": [],
        "patience": us["patience"], "tolerance": PATIENCE_TOLERANCE[us["patience"]],
        "helping_ability": us["helping_ability"], "helping_ability_note": us.get("helping_ability_note", ""),
        "attitude_now": seed["labels"]["attitude"],
        "consecutive_failed_replies": 0, "repeated_defect_count": 0, "strategies_tried": [], "moves_so_far": [],
        "task_progress": "not_started", "observations_obtained": [],
    }
    if seed.get("learner"):
        state["learner"] = {"knowledge_items": copy.deepcopy(seed["learner"]["knowledge_items"]),
                            "misconception": copy.deepcopy(seed["learner"]["misconception"]),
                            "transfer_attempts": []}
    return state


def scheduled_change_applies(state: dict[str, Any], seed: dict[str, Any] | None) -> bool:
    """Amendment (correction group): the user decision that follows assistant reply 2, when reply 1 already failed.
    If reply 2 fails too, the next request must change strategy with an actionable instruction."""
    return bool(seed and seed.get("case_id", "").startswith("C60") and seed.get("category") == "existing_type"
                and len(state["moves_so_far"]) == 1 and state["consecutive_failed_replies"] >= 1)


def allowed_moves(state: dict[str, Any], mode: str = "next_turn", seed: dict[str, Any] | None = None) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    if mode == "final_assessment":
        return ["finish", "abandon", "accept_partial"], ["turn limit reached: only a final assessment is recorded"]
    allowed = set(HELPING_ABILITY[state["helping_ability"]])
    if state["helping_ability"] != "can_give_example":
        reasons.append(f"helping ability {state['helping_ability']}: {state['helping_ability_note']}")
    last = state["moves_so_far"][-1] if state["moves_so_far"] else None
    if last == "restate":
        allowed.discard("restate")
        reasons.append("your previous message was a restatement: do not restate again; change strategy if the reply failed")
    failures = state["consecutive_failed_replies"]
    tolerance = state["tolerance"]
    if failures == 0:
        allowed.discard("abandon")
        reasons.append("no failed reply yet: abandoning is not a plausible reaction now")
    if failures >= tolerance + 1:
        allowed &= {"accept_partial", "abandon", "finish"}
        reasons.append(f"patience {state['patience']} exhausted after {failures} failed replies in a row: accept, finish or abandon")
    elif failures >= tolerance:
        allowed &= {"express_frustration", "accept_partial", "abandon", "finish", "simplify", "clarify", "continue"}
        reasons.append(f"patience {state['patience']} nearly exhausted after {failures} failed replies in a row: "
                       "one last simple attempt (frustration or a narrower request), accept, finish or abandon")
    if scheduled_change_applies(state, seed):
        change = INSTRUCTION_CHANGE_MOVES & set(HELPING_ABILITY[state["helping_ability"]])
        allowed |= change
        reasons.append("the first reply already failed: if the latest reply also fails, your message MUST change strategy "
                       f"with an actionable instruction ({', '.join(sorted(change))}): a short example, one smaller part, a "
                       "simpler or narrower request, a clarification or missing context. A complaint or a restatement is not "
                       "enough. If the latest reply succeeded, react normally.")
    return [m for m in MOVES if m in allowed], reasons


def validate_decision(decision: dict[str, Any], state: dict[str, Any], allowed: list[str], mode: str,
                      seed: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    move = decision.get("move")
    perceived = decision.get("perceived_latest_reply", {})
    if move not in allowed:
        problems.append(f"move {move!r} is not in ALLOWED_MOVES {allowed}")
    if bool(decision.get("done")) != (move in TERMINAL_MOVES):
        problems.append("done must be true exactly for finish or abandon")
    message = (decision.get("message") or "").strip()
    c60 = seed.get("case_id", "").startswith("C60")
    if mode == "final_assessment":
        if message:
            problems.append("final_assessment must have an empty message")
    elif move in TERMINAL_MOVES and message and not c60:     # c60: an explicit abandonment may carry a message (never sent)
        problems.append("finish/abandon must have an empty message")
    elif move not in TERMINAL_MOVES and not message:
        problems.append("a non-terminal move needs a message")
    if move == "continue" and perceived.get("defect_present"):
        problems.append("continue is the healthy path: it cannot follow a defect you noticed (use a failure response or accept_partial)")
    if scheduled_change_applies(state, seed) and perceived.get("defect_present") and move not in INSTRUCTION_CHANGE_MOVES:
        problems.append("strategy change required: the first two replies failed, so choose one of "
                        f"{sorted(INSTRUCTION_CHANGE_MOVES)} with an actionable instruction in the message")
    if move in {"point_to_defect", "restate", "express_frustration"} and not perceived.get("defect_present"):
        problems.append(f"{move} requires a noticed defect in the latest reply")
    if move == "abandon" and not (perceived.get("defect_present") or state["consecutive_failed_replies"] > 0):
        problems.append("abandon requires an unresolved failure")
    level = decision.get("assistance_level")
    if move in {"continue", "finish", "abandon", "accept_partial"} and level != "none":
        problems.append(f"{move} carries assistance_level none")
    if move == "restate" and level != "restatement":
        problems.append("restate carries assistance_level restatement")
    if move == "point_to_defect" and ASSISTANCE_ORDER.get(level, 0) < 2:
        problems.append("point_to_defect carries at least pointed_defect")
    if move in {"give_example", "decompose"} and ASSISTANCE_ORDER.get(level, 0) < 3:
        problems.append(f"{move} carries at least partial_scaffold_or_example")
    private_ids = {p["id"] for p in state["private_preferences"]}
    unknown = [i for i in decision.get("revealed_private_preference_ids", []) if i not in private_ids]
    if unknown:
        problems.append(f"revealed ids {unknown} are not unrevealed private preferences")
    if decision.get("revealed_private_preference_ids") and not decision.get("changes_task"):
        problems.append("revealing a private preference changes the task (changes_task=true)")
    if seed.get("learner"):
        items = {k["item_id"] for k in state["learner"]["knowledge_items"]}
        for update in decision.get("knowledge_updates", []):
            if update.get("item_id") not in items:
                problems.append(f"unknown knowledge item {update.get('item_id')}")
    else:
        if decision.get("knowledge_updates") or decision.get("transfer_attempt", {}).get("attempted"):
            problems.append("knowledge updates and transfer attempts are for learning scenarios only")
    return problems


def apply_decision(state: dict[str, Any], decision: dict[str, Any], assistant_texts: list[str],
                   turn: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (new_state, transition record). Knowledge updates need an exact quote from visible teaching."""
    new = copy.deepcopy(state)
    perceived = decision["perceived_latest_reply"]
    if perceived["defect_present"]:
        new["consecutive_failed_replies"] += 1
        new["repeated_defect_count"] = state["repeated_defect_count"] + 1 if perceived["same_defect_as_before"] else 1
    else:
        new["consecutive_failed_replies"] = 0
        new["repeated_defect_count"] = 0
    new["moves_so_far"].append(decision["move"])
    if decision["move"] in FAILURE_RESPONSE_MOVES:
        new["strategies_tried"].append({"turn": turn, "move": decision["move"]})
    if decision["move"] == "express_frustration":
        new["attitude_now"] = "frustrated"
    revealed = set(decision.get("revealed_private_preference_ids", []))
    for pref in list(new["private_preferences"]):
        if pref["id"] in revealed:
            new["private_preferences"].remove(pref)
            new["revealed_preferences"].append({**pref, "revealed_at_user_turn": turn})
            new["disclosed_preferences"].append(pref["text"])
    new["task_progress"] = decision.get("task_progress", state["task_progress"])
    accepted, rejected = [], []
    if "learner" in new:
        visible = "\n".join(assistant_texts)
        by_id = {k["item_id"]: k for k in new["learner"]["knowledge_items"]}
        for update in decision.get("knowledge_updates", []):
            quote = (update.get("evidence_quote") or "").strip()
            if quote and quote in visible and update["item_id"] in by_id:
                by_id[update["item_id"]]["status"] = update["new_status"]
                by_id[update["item_id"]].setdefault("history", []).append({"turn": turn, "status": update["new_status"], "evidence_quote": quote})
                accepted.append(update)
            else:
                rejected.append({**update, "reason": "evidence_quote not found verbatim in visible assistant replies"})
        if decision.get("misconception_status") in {"held", "weakened", "revised"}:
            if decision["misconception_status"] != "held" and not accepted:
                rejected.append({"misconception_status": decision["misconception_status"],
                                 "reason": "misconception change without any justified knowledge update"})
            else:
                new["learner"]["misconception"]["status"] = decision["misconception_status"]
        attempt = decision.get("transfer_attempt") or {}
        if attempt.get("attempted"):
            new["learner"]["transfer_attempts"].append({"turn": turn, "text": attempt.get("attempt_text", "")})
    record = {"turn": turn, "move": decision["move"], "consecutive_failed_replies": new["consecutive_failed_replies"],
              "repeated_defect_count": new["repeated_defect_count"], "revealed": sorted(revealed),
              "knowledge_updates_accepted": accepted, "knowledge_updates_rejected": rejected}
    return new, record
