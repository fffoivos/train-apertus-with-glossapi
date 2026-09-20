"""Deterministic simulated worlds for troubleshooting cases (world resolver, spec §4.8).

Sol never writes observations. It only maps a user's intended action to a supported check id or "unresolved"; the
observation text comes from the fixed table below, evaluated against the current simulated state. Nothing here
executes on a real machine; every observation is marked simulated.
"""
from __future__ import annotations

import copy
from typing import Any

UNRESOLVED_OBSERVATION = ("You could not carry out this step as described, or you cannot tell what happened (this "
                          "option or result is not something you can find). If you mention it, say so honestly.")


def _derive_printer(state: dict[str, Any]) -> dict[str, Any]:
    reachable_network = state["printer_network"] == state["laptop_network"] == "Home"
    return {**state, "reachable": bool(state["usb_connected"] or reachable_network),
            "network_reachable": reachable_network}


def _derive_python(state: dict[str, Any]) -> dict[str, Any]:
    vscode_ok = state["venv_has_requests"] if state["vscode_interpreter"] == "venv" else True
    terminal_python = "/project/.venv/bin/python" if state["terminal_venv_active"] else "/usr/bin/python"
    return {**state, "vscode_import_works": vscode_ok, "terminal_python": terminal_python}


def _derive_declarative(state: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Generated worlds (60-dialogue collection): each derived flag is true when any of its `any_of` conditions matches
    the raw state. Rules are evaluated in order, so a later rule may use an earlier derived flag."""
    derived = dict(state)
    for rule in rules:
        derived[rule["name"]] = any(all(derived.get(k) == v for k, v in cond.items()) for cond in rule["any_of"])
    return derived


DERIVERS = {"printer_network_v1": _derive_printer, "python_env_v1": _derive_python}


def derive(world: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if world["derive"] == "declarative_v1":
        return _derive_declarative(state, world.get("derived_rules", []))
    return DERIVERS[world["derive"]](state)


def _matches(when: dict[str, Any], derived: dict[str, Any]) -> bool:
    return all(derived.get(key) == value for key, value in when.items())


def initial_state(world: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(world["initial_state"])


def resolver_catalogue(world: dict[str, Any]) -> list[dict[str, Any]]:
    """What the world resolver (Sol) sees: check ids, what they are, preconditions. Hidden world facts are passed
    separately; observation texts are not needed for mapping and are withheld."""
    return [{"check_id": cid, "description": check["description"], "preconditions": check.get("preconditions", "")}
            for cid, check in world["checks"].items()]


def apply_check(world: dict[str, Any], state: dict[str, Any], check_id: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if check_id not in world["checks"]:
        raise KeyError(f"unknown check id {check_id}")
    check = world["checks"][check_id]
    new_state = copy.deepcopy(state)
    before = derive(world, state)
    for key, value in (check.get("effects") or {}).items():
        new_state[key] = value
    for conditional in check.get("conditional_effects") or []:
        if _matches(conditional["when"], before):
            new_state.update(conditional["set"])
    derived = derive(world, new_state)
    for variant in check["observations"]:
        if _matches(variant.get("when", {}), derived) and _matches(variant.get("when_before", {}), before):
            text = variant["text"].format(**derived)
            record = {"check_id": check_id, "state_before": state, "state_after": new_state,
                      "matched_when": variant.get("when", {}), "simulated": True}
            return text, new_state, record
    raise ValueError(f"world table has no observation for {check_id} in state {derived}")


def validate_world(world: dict[str, Any]) -> list[str]:
    """Every check must produce an observation in every reachable combination of the state flags it depends on."""
    problems = []
    keys = list(world["initial_state"])
    domains = world.get("state_domains", {})
    import itertools
    combos = itertools.product(*[domains.get(k, [world["initial_state"][k]]) for k in keys])
    for combo in combos:
        state = dict(zip(keys, combo))
        for cid in world["checks"]:
            try:
                apply_check(world, state, cid)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"{cid} @ {state}: {exc}")
    return problems
