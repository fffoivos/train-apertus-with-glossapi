"""Seed loading and validation for D1 (DVI001-DVI004) and D2 (RGD001-RGD006)."""
from __future__ import annotations

import json
import pathlib
from typing import Any

from common import C60_ROOT, HERE, RGD_ROOT, read_json, sha256_json
from contracts import DEV_TAGS, HELPING_ABILITY, MAX_ASSISTANT_TURNS

DVI_SEEDS = HERE / "seeds" / "dvi_seeds.json"
DVI_SPECS = HERE / "seeds" / "dvi_seed_specs.json"
RGD_SEEDS = RGD_ROOT / "seeds" / "rgd_seeds.json"
D1_IDS = ["DVI001", "DVI002", "DVI003", "DVI004"]
D2_IDS = ["RGD001", "RGD002", "RGD003", "RGD004", "RGD005", "RGD006"]
CATEGORIES = {"writing", "troubleshooting", "learning", "existing_type"}


def validate_seed(seed: dict[str, Any]) -> None:
    for key, value in DEV_TAGS.items():
        if seed.get(key) != value:
            raise ValueError(f"{seed.get('case_id')}: {key} must be {value!r}")
    for key in ("case_id", "category", "language", "labels", "opening", "user_state", "evaluator_reference",
                "source_family", "split", "run"):
        if key not in seed:
            raise ValueError(f"{seed.get('case_id')}: missing {key}")
    if seed["category"] not in CATEGORIES:
        raise ValueError(f"{seed['case_id']}: bad category")
    if seed["split"] != "development":
        raise ValueError(f"{seed['case_id']}: development split required")
    us = seed["user_state"]
    if us["helping_ability"] not in HELPING_ABILITY or us["patience"] not in {"low", "medium", "high"}:
        raise ValueError(f"{seed['case_id']}: bad user traits")
    if seed["category"] == "writing" and not seed.get("user_view_extras", {}).get("reference_draft"):
        raise ValueError(f"{seed['case_id']}: writing needs an illustrative draft")
    if seed["category"] == "troubleshooting" and not seed.get("world"):
        raise ValueError(f"{seed['case_id']}: troubleshooting needs a world")
    if seed["category"] == "learning" and not seed.get("learner"):
        raise ValueError(f"{seed['case_id']}: learning needs a learner state")
    if int(seed.get("max_assistant_turns", MAX_ASSISTANT_TURNS)) != MAX_ASSISTANT_TURNS:
        raise ValueError(f"{seed['case_id']}: horizon must be {MAX_ASSISTANT_TURNS}")


def load_d2() -> dict[str, dict[str, Any]]:
    seeds = {s["case_id"]: s for s in read_json(RGD_SEEDS)["seeds"]}
    if sorted(seeds) != D2_IDS:
        raise ValueError(f"D2 seed ids {sorted(seeds)} != {D2_IDS}")
    for seed in seeds.values():
        validate_seed(seed)
    return seeds


def load_d1(required: bool = True) -> dict[str, dict[str, Any]]:
    if not DVI_SEEDS.exists():
        if required:
            raise FileNotFoundError("D1 seeds not written yet (run: dv2.py openings)")
        return {}
    seeds = {s["case_id"]: s for s in read_json(DVI_SEEDS)["seeds"]}
    if sorted(seeds) != D1_IDS:
        raise ValueError(f"D1 seed ids {sorted(seeds)} != {D1_IDS}")
    for seed in seeds.values():
        validate_seed(seed)
    return seeds


def load_c60() -> dict[str, dict[str, Any]]:
    """60-dialogue collection seeds (collection60/seeds_c60.py). Only seeds that passed validation are frozen there."""
    path = C60_ROOT / "seeds.json"
    if not path.exists():
        raise FileNotFoundError("collection seeds not written yet (run collection60/seeds_c60.py)")
    seeds = {s["case_id"]: s for s in read_json(path)["seeds"]}
    for seed in seeds.values():
        validate_seed(seed)
    return seeds


def load_all(required_d1: bool = True) -> dict[str, dict[str, Any]]:
    return {**load_d1(required_d1), **load_d2()}


def seed_hash(seed: dict[str, Any]) -> str:
    return sha256_json(seed)
