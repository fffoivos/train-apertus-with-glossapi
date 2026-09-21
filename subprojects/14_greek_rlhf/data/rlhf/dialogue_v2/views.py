"""Role views (spec §4.8): Apertus, user, learner, world resolver and evaluator packets are built from whitelisted
fields only. Leak checks compare each model-visible prompt with the private strings it must not contain."""
from __future__ import annotations

import json
from typing import Any

import worlds
from contracts import prompt_text
from glossary import Glossary
from common import word_count
from user_state import allowed_moves


def public_messages(trajectory_messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Apertus view: the public conversation only, exactly role/content, no system prompt."""
    out = []
    for i, message in enumerate(trajectory_messages):
        expected = "user" if i % 2 == 0 else "assistant"
        if set(message) != {"role", "content"} or message["role"] != expected or not message["content"].strip():
            raise ValueError(f"public transcript malformed at {i}")
        out.append({"role": message["role"], "content": message["content"]})
    return out


def _labels_block(glossary: Glossary, seed: dict[str, Any], include_task: bool = True) -> dict[str, str]:
    labels = {k: v for k, v in seed["labels"].items() if k in {"attitude", "register", "interaction", "difficulty", "detail"}}
    if include_task:
        labels["task"] = seed["labels"]["task"]
    return labels


def user_view(seed: dict[str, Any], state: dict[str, Any], messages: list[dict[str, str]], mode: str,
              new_observations: list[dict[str, str]] | None = None) -> dict[str, Any]:
    moves, reasons = allowed_moves(state, mode, seed)
    private_state = {
        "goal": state["goal"], "known_facts": state["known_facts"], "expertise": state["expertise"],
        "misconception": state["misconception"], "disclosed_preferences": state["disclosed_preferences"],
        "private_preferences_not_yet_stated": [{"id": p["id"], "text": p["text"], "reveal_when": p["reveal_when"]}
                                               for p in state["private_preferences"]],
        "patience": state["patience"], "helping_ability": state["helping_ability"],
        "helping_ability_note": state["helping_ability_note"], "attitude_now": state["attitude_now"],
        "consecutive_failed_replies_so_far": state["consecutive_failed_replies"],
        "repeated_defect_count": state["repeated_defect_count"],
        "strategies_tried": state["strategies_tried"], "task_progress": state["task_progress"],
    }
    view: dict[str, Any] = {
        "scenario_category": seed["category"], "language": seed["language"], "labels": seed["labels"],
        "MODE": mode, "ALLOWED_MOVES": moves, "allowed_moves_reasons": reasons,
        "your_private_state": private_state, "visible_conversation": messages,
    }
    if seed["case_id"].startswith("C60") and messages and messages[-1]["role"] == "assistant":
        # amendment check 1: counts are computed by code and handed to the simulator instead of estimated by it
        text = messages[-1]["content"]; lines = text.splitlines()
        view["COMPUTED_FACTS_ABOUT_THE_LATEST_REPLY"] = {
            "words": word_count(text), "characters": len(text), "non_empty_lines": sum(1 for ln in lines if ln.strip()),
            "paragraphs": sum(1 for block in text.split("\n\n") if block.strip()),
            "bullet_lines": sum(1 for ln in lines if ln.lstrip().startswith(("-", "*", "•"))),
            "numbered_lines": sum(1 for ln in lines if ln.lstrip()[:3].rstrip(".)").isdigit()),
            "note": "computed exactly by code; use these numbers, do not recount"}
    if seed["category"] == "writing":
        view["your_illustrative_draft"] = {"text": seed["user_view_extras"]["reference_draft"],
                                           "note": seed["user_view_extras"]["reference_note"]}
    if seed["category"] == "troubleshooting":
        view["OBSERVATIONS_OBTAINED"] = {"earlier": state["observations_obtained"],
                                         "just_now_from_the_steps_you_carried_out": new_observations or []}
    if seed.get("learner"):
        learner = state["learner"]
        view["your_learner_state"] = {
            "knowledge_items": [{"item_id": k["item_id"], "text": k["text"], "status": k["status"]}
                                for k in learner["knowledge_items"]],
            "misconception": learner["misconception"],
            "transfer_question_for_yourself": seed["learner"]["transfer_question"],
            "transfer_note": seed["learner"]["transfer_note"],
            "your_earlier_attempts": learner["transfer_attempts"],
        }
        if seed["learner"].get("practice_text"):
            view["your_learner_state"]["practice_text_you_have_at_hand"] = seed["learner"]["practice_text"]
    return view


def user_prompt(glossary: Glossary, seed: dict[str, Any], view: dict[str, Any]) -> str:
    views = ["user view"] + (["learner view"] if seed.get("learner") else [])
    block = glossary.block(_labels_block(glossary, seed), moves=True,
                           dialogue=[("User state", None), ("Role views", views)])
    policy = "user_policy_v2_1.txt" if seed["case_id"].startswith("C60") else "user_policy_v2.txt"
    return (prompt_text(policy) + "\n\n" + block + "\n\nYOUR VIEW (JSON):\n"
            + json.dumps(view, ensure_ascii=False, indent=1))


def actions_view(seed: dict[str, Any], state: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
    return {"scenario_category": seed["category"], "language": seed["language"],
            "your_private_state": {"goal": state["goal"], "known_facts": state["known_facts"],
                                   "expertise": state["expertise"], "patience": state["patience"],
                                   "helping_ability_note": state["helping_ability_note"]},
            "observations_you_already_obtained": state["observations_obtained"],
            "visible_conversation": messages}


def actions_prompt(glossary: Glossary, seed: dict[str, Any], view: dict[str, Any]) -> str:
    block = glossary.block({"attitude": seed["labels"]["attitude"]}, dialogue=[("Role views", ["user view"])])
    return (prompt_text("user_actions_v1.txt") + "\n\n" + block + "\n\nYOUR VIEW (JSON):\n"
            + json.dumps(view, ensure_ascii=False, indent=1))


def resolver_view(seed: dict[str, Any], state: dict[str, Any], actions: list[dict[str, Any]],
                  latest_assistant: str) -> dict[str, Any]:
    world = seed["world"]
    return {"hidden_world_facts": world["hidden_facts"], "root_cause": world["root_cause"],
            "SUPPORTED_CHECKS": worlds.resolver_catalogue(world),
            "user_known_facts": state["known_facts"],
            "observations_user_already_obtained": state["observations_obtained"],
            "latest_assistant_reply_for_context": latest_assistant,
            "ACTIONS": [{"action_index": i, "action": a["action"]} for i, a in enumerate(actions)]}


def resolver_prompt(glossary: Glossary, view: dict[str, Any]) -> str:
    block = glossary.block(dialogue=[("Role views", ["world resolver"])])
    return (prompt_text("world_resolver_v1.txt") + "\n\n" + block + "\n\nRESOLVER VIEW (JSON):\n"
            + json.dumps(view, ensure_ascii=False, indent=1))


# --------------------------------------------------------------------------------------------------------------
# Leak checks
# --------------------------------------------------------------------------------------------------------------
def evaluator_only_strings(seed: dict[str, Any]) -> list[str]:
    """Strings that exist only in evaluator/world views and must never reach the user/learner or Apertus prompt."""
    out: list[str] = []
    ref = seed.get("evaluator_reference", {})
    for key in ("grading_rule", "root_cause"):
        if isinstance(ref.get(key), str):
            out.append(ref[key])
    # private_targets_not_hard_constraints mirror the user's own private preferences (user view) and are excluded here.
    for key in ("hidden_facts", "subject_knowledge", "valid_resolutions", "forbidden_additions"):
        out.extend(x for x in ref.get(key, []) if isinstance(x, str))
    transfer = ref.get("transfer_check")
    if transfer:
        out.append(transfer["what_to_check"])
    if seed.get("world"):
        out.append(seed["world"]["root_cause"])
        out.extend(seed["world"]["hidden_facts"])
    return sorted(set(out))


def unrevealed_observation_strings(seed: dict[str, Any], state: dict[str, Any]) -> list[str]:
    if not seed.get("world"):
        return []
    revealed = {o["observation"] for o in state.get("observations_obtained", [])}
    out = []
    for check in seed["world"]["checks"].values():
        for variant in check["observations"]:
            if variant["text"] not in revealed:
                out.append(variant["text"])
    return out


def already_known(strings: list[str], state: dict[str, Any], messages: list[dict[str, str]]) -> list[str]:
    """A world string is not hidden from the user when the user already knows it (known facts) or it is already in the
    visible conversation (for example the assistant said the same thing). Generated worlds can repeat such sentences."""
    visible = " ".join(state.get("known_facts", [])) + " " + " ".join(m["content"] for m in messages)
    return [s for s in strings if s not in visible]


def apertus_private_strings(seed: dict[str, Any]) -> list[str]:
    out = list(evaluator_only_strings(seed))
    extras = seed.get("user_view_extras", {})
    if extras.get("reference_draft"):
        out.append(extras["reference_draft"])
    for pref in seed["user_state"].get("private_preferences", []):
        out.append(pref["text"])
    # Learner knowledge items and the misconception are the user's own knowledge; saying them is not a leak.
    return sorted(set(out))


def find_leaks(text: str, forbidden: list[str], min_len: int = 24) -> list[str]:
    return [s for s in forbidden if len(s) >= min_len and s in text]


def transfer_answer_leak(seed: dict[str, Any], view_text: str) -> bool:
    ref = seed.get("evaluator_reference", {}).get("transfer_check")
    if not ref:
        return False
    return ("transfer_check" in view_text or "\"answer\"" in view_text
            or ref["what_to_check"] in view_text)
