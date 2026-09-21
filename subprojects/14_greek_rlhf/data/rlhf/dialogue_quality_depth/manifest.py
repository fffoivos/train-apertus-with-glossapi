"""Deterministic seed allocation and source-family reservation."""
from __future__ import annotations

import collections
import hashlib
import itertools
import math
import json
import pathlib
import random
import sqlite3
import sys
from typing import Any

from budget import CallLedger
from common import append_jsonl, atomic_json, sha256_json, utcnow
from schemas import Seed

HERE = pathlib.Path(__file__).resolve().parent
GENERATOR = HERE.parent / "prompt_generator"

TASK_FAMILIES = {
    "everyday": ["e_plan", "e_edit", "e_explain", "s_general", "e_troubleshoot", "s_actions", "e_write", "s_update"],
    "instruction": ["if_format", "if_preserve", "if_composite", "if_conditional"],
    "factual": ["f_grounded", "f_closed", "f_missing", "f_premise", "f_conflict"],
    "safety": ["safe_benign", "safe_protective", "safe_fiction", "safe_harmful", "safe_ambiguous"],
    "math": ["m_arithmetic", "m_linear", "m_geometry", "m_probability", "m_quadratic"],
}

SMOKE_SCENARIOS = [
    ("ordinary_continuation", "everyday", "el", "followup"),
    ("changing_requirement", "instruction", "el", "revision"),
    ("retaining_constraint", "instruction", "el", "constraint_retention"),
    ("verifiable_correction", "math", "el", "revision"),
    ("genuine_completion", "everyday", "en", "followup"),
    ("underspecified_task", "factual", "en", "uncertainty"),
]

SCENARIO_INSTRUCTIONS = {
    "ordinary_continuation": "Begin a task that naturally supports an ordinary follow-up or elaboration.",
    "changing_requirement": "Begin a task whose requirement can plausibly be revised after the first answer.",
    "retaining_constraint": "State a concrete constraint that should remain relevant across later requests.",
    "verifiable_correction": "Ask a verifiable question. A later correction is allowed only if the visible answer actually warrants it; never manufacture an error.",
    "genuine_completion": "Begin a bounded task that may genuinely finish without padding to the horizon.",
    "underspecified_task": "Begin a genuinely uncertain or underspecified task where clarification may be appropriate.",
}

INTERACTION_TASKS = {
    "followup": {"everyday", "instruction", "factual", "safety", "math"},
    "revision": {"everyday", "instruction"},
    "constraint_retention": {"everyday", "instruction"},
    "recall": {"everyday", "instruction", "factual"},
    "uncertainty": {"everyday", "instruction", "factual", "safety"},
}

INTERACTION_FAMILIES = {
    "revision": {"e_edit", "e_plan", "if_format", "if_preserve", "if_composite", "if_conditional"},
    "constraint_retention": {"e_edit", "e_plan", "e_write", "s_update", "if_format", "if_preserve", "if_composite", "if_conditional"},
    "recall": {"s_general", "s_query", "s_actions", "s_multi", "s_update", "e_edit", "e_explain", "e_plan",
               "if_format", "if_preserve", "if_composite", "if_conditional", "f_grounded", "f_closed", "f_conflict"},
    "uncertainty": {"e_troubleshoot", "e_plan", "e_tools", "if_conditional", "f_missing", "f_premise", "f_conflict", "safe_ambiguous"},
}


def _generator_modules():
    if str(GENERATOR) not in sys.path:
        sys.path.insert(0, str(GENERATOR))
    import fixtures
    import core
    return fixtures, core


def _external_reservations() -> tuple[set[str], set[str]]:
    dbpath = GENERATOR / "runtime" / "registry.sqlite"
    if not dbpath.exists():
        return set(), set()
    # A normal read-only connection participates in SQLite WAL visibility;
    # immutable=1 could conceal newly committed generator reservations.
    uri = f"file:{dbpath}?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        db.execute("BEGIN")  # one consistent live snapshot across both tables
        families = {str(r[0]) for r in db.execute("SELECT id FROM content_families")}
        instances = {str(r[0]) for r in db.execute("SELECT hash FROM instances")}
        return families, instances
    finally:
        db.close()


def _spread(rows: list[dict[str, Any]], name: str, counts: dict[str, int], rng: random.Random,
            compatible=None) -> None:
    values = [value for value, n in counts.items() for _ in range(n)]
    if len(values) != len(rows):
        raise ValueError(f"{name} quota size mismatch")
    rng.shuffle(values)
    # Deterministic bipartite repair by taking the first compatible remaining value.
    order = list(range(len(rows)))
    rng.shuffle(order)
    for idx in order:
        choices = [i for i, value in enumerate(values) if compatible is None or compatible(rows[idx], value)]
        if not choices:
            raise ValueError(f"infeasible {name} assignment")
        pick = choices[0]
        rows[idx][name] = values.pop(pick)


def _measurement_slots(config: dict[str, Any], rng: random.Random) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    measurement = config["measurement"]
    rows: list[dict[str, Any]] = []
    for task, languages in measurement["task_language_counts"].items():
        for language, count in languages.items():
            rows.extend({"task": task, "language": language} for _ in range(count))
    rng.shuffle(rows)
    # Preserve an unconstrained before-image as evidence, then repair with a
    # deterministic compatible matching while retaining exact margins.
    _spread(rows, "interaction", measurement["interaction"], rng)
    before_interaction = [{"slot": i, "task": row["task"], "interaction": row["interaction"]}
                          for i, row in enumerate(rows) if row["task"] not in INTERACTION_TASKS[row["interaction"]]]
    before_joint = dict(sorted(collections.Counter(f"{row['task']}|{row['interaction']}" for row in rows).items()))
    for row in rows:
        row.pop("interaction")
    compatible_interaction = lambda row, value: row["task"] in INTERACTION_TASKS[value]
    _spread(rows, "interaction", measurement["interaction"], rng, compatible_interaction)
    _spread(rows, "attitude", measurement["attitude"], rng)
    _spread(rows, "register", measurement["register"], rng,
            lambda row, value: value != "greeklish" or row["language"] == "el")
    _spread(rows, "difficulty", measurement["difficulty"], rng)
    after_incompatible = [{"slot": i, "task": row["task"], "interaction": row["interaction"]}
                          for i, row in enumerate(rows) if row["task"] not in INTERACTION_TASKS[row["interaction"]]]
    return rows, {"before_incompatible_task_interactions": before_interaction,
                  "after_incompatible_task_interactions": after_incompatible,
                  "before_task_interaction_counts": before_joint,
                  "after_task_interaction_counts": dict(sorted(collections.Counter(
                      f"{row['task']}|{row['interaction']}" for row in rows).items())),
                  "interaction_repairs": len(before_interaction),
                  "rules": {key: sorted(value) for key, value in INTERACTION_TASKS.items()}}


def _counts(rows: list[dict[str, Any]], axes: tuple[str, ...]) -> dict[str, dict[str, int]]:
    out = {axis: dict(sorted(collections.Counter(row[axis] for row in rows).items())) for axis in axes}
    for joint in (("task", "language"), ("task", "interaction"), ("language", "register"),
                  ("task", "language", "interaction", "attitude", "register", "difficulty")):
        name = "__".join(joint)
        out[name] = dict(sorted(collections.Counter("|".join(str(row[a]) for a in joint) for row in rows).items()))
    return out


def family_compatible(row: dict[str, Any], family: str) -> bool:
    if row.get("stage") == "smoke" and row.get("scenario") == "verifiable_correction":
        return family.startswith("m_")
    allowed = INTERACTION_FAMILIES.get(row["interaction"])
    return allowed is None or family in allowed


def count_accepted(rows: list[dict[str, Any]], axis: str, accepted_statuses=("completed", "horizon", "truncated_output", "context_limit")) -> dict[str, int]:
    """Quota summaries never count merely planned or failed trajectories."""
    return dict(collections.Counter(r[axis] for r in rows if r.get("terminal_code") in accepted_statuses))


def _apportion_counts(weights: dict[Any, int], n: int) -> dict[Any, int]:
    total = sum(weights.values())
    raw = {k: v * n / total for k, v in weights.items()}
    out = {k: math.floor(v) for k, v in raw.items()}
    for key in sorted(weights, key=lambda k: (-(raw[k] - out[k]), str(k)))[:n - sum(out.values())]:
        out[key] += 1
    return out


def _exact_margin_subset(rows: list[dict[str, Any]], cell_target: dict[tuple[str, str], int],
                         axis_target: dict[str, dict[str, int]], random_seed: int
                         ) -> tuple[list[dict[str, Any]] | None, dict[str, int]]:
    """Solve all frozen largest-remainder margins, preserving task/language cells.

    Grouping by task/language keeps the search small.  Equivalent combinations
    are collapsed by their four-axis count vector before a memoized exact match.
    """
    axes = tuple(axis_target)
    dimensions = tuple((axis, value) for axis in axes for value in sorted(axis_target[axis]))
    groups: list[list[tuple[tuple[int, ...], tuple[dict[str, Any], ...]]]] = []
    for cell in sorted(cell_target, key=str):
        candidates = sorted((r for r in rows if (r["task"], r["language"]) == cell),
                            key=lambda r: r["trajectory_id"])
        keep = cell_target[cell]
        options: dict[tuple[int, ...], tuple[dict[str, Any], ...]] = {}
        for combination in itertools.combinations(candidates, keep):
            vector = tuple(sum(row[axis] == value for row in combination) for axis, value in dimensions)
            incumbent = options.get(vector)
            candidate_key = sha256_json([random_seed, [r["trajectory_id"] for r in combination]])
            incumbent_key = (sha256_json([random_seed, [r["trajectory_id"] for r in incumbent]])
                             if incumbent else None)
            if incumbent is None or candidate_key < incumbent_key:
                options[vector] = combination
        groups.append(sorted(((vector, combination) for vector, combination in options.items()),
                             key=lambda item: sha256_json(
                                 [random_seed, [r["trajectory_id"] for r in item[1]]])))

    suffix_min = [[0] * len(dimensions) for _ in range(len(groups) + 1)]
    suffix_max = [[0] * len(dimensions) for _ in range(len(groups) + 1)]
    for index in range(len(groups) - 1, -1, -1):
        for dimension in range(len(dimensions)):
            values = [option[0][dimension] for option in groups[index]]
            suffix_min[index][dimension] = min(values) + suffix_min[index + 1][dimension]
            suffix_max[index][dimension] = max(values) + suffix_max[index + 1][dimension]

    target = tuple(axis_target[axis][value] for axis, value in dimensions)
    memo: set[tuple[int, tuple[int, ...]]] = set()

    def solve(index: int, remaining: tuple[int, ...]) -> tuple[dict[str, Any], ...] | None:
        key = (index, remaining)
        if key in memo:
            return None
        if index == len(groups):
            return () if not any(remaining) else None
        for vector, combination in groups[index]:
            after = tuple(value - used for value, used in zip(remaining, vector))
            if any(value < suffix_min[index + 1][i] or value > suffix_max[index + 1][i]
                   for i, value in enumerate(after)):
                continue
            tail = solve(index + 1, after)
            if tail is not None:
                return combination + tail
        memo.add(key)
        return None

    result = solve(0, target)
    proof = {"task_language_groups": len(groups),
             "candidate_margin_vectors": sum(len(group) for group in groups),
             "failed_states_exhausted": len(memo)}
    return (list(result) if result is not None else None), proof


def _fallback_margin_subset(rows: list[dict[str, Any]], cell_target: dict[tuple[str, str], int],
                            axis_target: dict[str, dict[str, int]], random_seed: int) -> list[dict[str, Any]]:
    """Deterministic best-effort fallback used only after exact infeasibility."""
    axes = tuple(axis_target)
    remaining = {axis: dict(values) for axis, values in axis_target.items()}
    rng = random.Random(random_seed)
    chosen: list[dict[str, Any]] = []
    for cell in sorted(cell_target, key=str):
        candidates = [r for r in rows if (r["task"], r["language"]) == cell]
        rng.shuffle(candidates)
        for _ in range(cell_target[cell]):
            candidates.sort(key=lambda r: (
                -sum(max(0, remaining[axis].get(r[axis], 0)) for axis in axes),
                r["trajectory_id"]))
            pick = candidates.pop(0)
            chosen.append(pick)
            for axis in axes:
                remaining[axis][pick[axis]] = remaining[axis].get(pick[axis], 0) - 1
    return chosen


def reduced_admission(seeds: list[dict[str, Any]], n: int, random_seed: int = 9162602) -> dict[str, Any]:
    """Choose a pre-outcome subset and audit every required frozen margin."""
    rows = [s for s in seeds if s["stage"] == "measurement"]
    if n > len(rows) or n < 0:
        raise ValueError("admission size outside measurement panel")
    cells = collections.Counter((r["task"], r["language"]) for r in rows)
    cell_target = _apportion_counts(dict(cells), n)
    axes = ("interaction", "attitude", "register", "difficulty")
    axis_target = {axis: _apportion_counts(dict(collections.Counter(r[axis] for r in rows)), n) for axis in axes}
    chosen, proof = _exact_margin_subset(rows, cell_target, axis_target, random_seed)
    exact = chosen is not None
    if chosen is None:
        chosen = _fallback_margin_subset(rows, cell_target, axis_target, random_seed)
    counts = _counts(chosen, ("task", "language", *axes))
    target_counts = {"task_language": {f"{k[0]}|{k[1]}": v for k, v in cell_target.items()},
                     **axis_target}
    actual_required = {"task_language": counts["task__language"],
                       **{axis: counts[axis] for axis in axes}}
    deviations = []
    omitted = []
    available = {"task_language": dict(collections.Counter(
                     f"{r['task']}|{r['language']}" for r in rows)),
                 **{axis: dict(collections.Counter(r[axis] for r in rows)) for axis in axes}}
    for axis, targets in target_counts.items():
        for value in sorted(set(available[axis]) | set(targets) | set(actual_required[axis])):
            target_value = targets.get(value, 0)
            actual_value = actual_required[axis].get(value, 0)
            if target_value != actual_value:
                deviations.append({"axis": axis, "cell": value, "target": target_value,
                                   "actual": actual_value, "delta": actual_value - target_value})
            if actual_value == 0:
                omitted.append({"axis": axis, "cell": value, "target": target_value,
                                "available": available[axis].get(value, 0)})
    return {"trajectory_ids": [r["trajectory_id"] for r in sorted(chosen, key=lambda r: r["trajectory_id"])],
            "target_counts": target_counts,
            "actual_counts": counts,
            "omitted_task_language_cells": [f"{task}|{language}" for (task, language), count in cell_target.items() if count == 0],
            "omitted_cells": omitted,
            "deviations": deviations,
            "feasibility": {"exact_required_margins": exact,
                            "solver": "exhaustive grouped dynamic program with suffix margin bounds",
                            "proof": proof,
                            "reason": None if exact else
                            "no subset satisfies all frozen largest-remainder margins while preserving task-language quotas"},
            "method": "exact grouped margin solver; deterministic audited fallback only when infeasible"}


def seeds_for_stage(state: str | pathlib.Path, stage: str) -> list[dict[str, Any]]:
    state = pathlib.Path(state)
    manifest_data = json.loads((state / "manifest.json").read_text(encoding="utf-8"))
    rows = [s for s in manifest_data["seeds"] if s["stage"] == stage]
    if stage == "measurement":
        forecast_path = state / "forecast.json"
        if not forecast_path.exists():
            raise ValueError("measurement requires a frozen smoke forecast/admission")
        admitted = json.loads(forecast_path.read_text(encoding="utf-8"))
        receipt_path = state / "receipt.json"
        if not receipt_path.exists():
            raise ValueError("forecast receipt missing")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        frozen = receipt.get("artifacts", {}).get("forecast.json")
        current_hash = hashlib.sha256(forecast_path.read_bytes()).hexdigest()
        if not frozen or not frozen.get("frozen") or frozen.get("sha256") != current_hash:
            raise ValueError("forecast is not frozen or its receipt hash mismatches")
        ids = set(admitted.get("admitted_trajectory_ids") or [])
        if not ids or admitted.get("admitted_size") != len(ids):
            raise ValueError("forecast has no valid admitted measurement subset")
        rows = [s for s in rows if s["trajectory_id"] in ids]
    return rows


def validate_generator_isolation(state: str | pathlib.Path, stage: str) -> dict[str, Any] | None:
    if stage != "measurement":
        return None
    state = pathlib.Path(state)
    rows = seeds_for_stage(state, stage)
    external_families, external_instances = _external_reservations()
    family_hits = sorted({row["content_family"] for row in rows} & external_families)
    instance_hits = sorted({row["instance_hash"] for row in rows} & external_instances)
    dbpath = GENERATOR / "runtime" / "registry.sqlite"
    walpath = pathlib.Path(str(dbpath) + "-wal")
    snapshot = {
        "checked_utc": utcnow(), "stage": stage, "admitted_trajectory_ids": [row["trajectory_id"] for row in rows],
        "generator_registry": str(dbpath), "generator_family_count": len(external_families),
        "generator_instance_count": len(external_instances), "registry_sha256": hashlib.sha256(dbpath.read_bytes()).hexdigest(),
        "wal_present": walpath.exists(), "wal_sha256": hashlib.sha256(walpath.read_bytes()).hexdigest() if walpath.exists() else None,
        "family_collisions": family_hits, "instance_collisions": instance_hits,
    }
    append_jsonl(state / "generator_registry_checks.jsonl", snapshot)
    atomic_json(state / "generator_registry_check.json", snapshot)
    receipt_path = state / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {"artifacts": {}}
    receipt.setdefault("artifacts", {})["generator_registry_check.json"] = {
        "sha256": hashlib.sha256((state / "generator_registry_check.json").read_bytes()).hexdigest(),
        "created_utc": snapshot["checked_utc"], "frozen": False}
    atomic_json(receipt_path, receipt)
    if family_hits or instance_hits:
        raise ValueError(f"live generator registry collision: families={family_hits} instances={instance_hits}")
    return snapshot


def initialize(state: str | pathlib.Path, config_path: str | pathlib.Path) -> dict[str, Any]:
    state = pathlib.Path(state)
    state.mkdir(parents=True, exist_ok=True)
    config = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    if config.get("seed") != 9162602:
        raise ValueError("pilot seed must be 9162602")
    existing = state / "manifest.json"
    if existing.exists():
        old = json.loads(existing.read_text(encoding="utf-8"))
        if old.get("source_config_sha256") != sha256_json(config):
            raise ValueError("state already initialized with another config")
        if old.get("manifest_schema_version") != 3:
            # Safe Phase-0 migration only: never rewrite after any model call
            # or measurement artifact. The reviewed runtime has zero calls.
            db_path = state / "registry.sqlite"
            if db_path.exists():
                with sqlite3.connect(db_path) as db:
                    call_count = db.execute("SELECT count(*) FROM calls").fetchone()[0]
                    if call_count:
                        raise ValueError("cannot regenerate manifest after model calls")
                    db.execute("DELETE FROM family_reservations")
            nonempty = [p for p in (state / "measurement").glob("*.jsonl") if p.stat().st_size]
            if nonempty:
                raise ValueError("cannot regenerate manifest after measurement artifacts")
            existing.unlink()
            return initialize(state, config_path)
        receipt_path = state / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {"artifacts": {}}
        receipt.setdefault("artifacts", {})["manifest.json"] = {
            "sha256": __import__("hashlib").sha256(existing.read_bytes()).hexdigest(),
            "created_utc": receipt.get("artifacts", {}).get("manifest.json", {}).get("created_utc", utcnow()), "frozen": True}
        atomic_json(receipt_path, receipt)
        if not (state / "cost_ledger.json").exists():
            from budget import write_cost_ledger
            write_cost_ledger(state)
        return old
    atomic_json(state / "source_config.json", config)
    ledger = CallLedger(state, config)
    fixtures, core = _generator_modules()
    external_families, external_instances = _external_reservations()
    rng = random.Random(config["seed"])
    planned: list[dict[str, Any]] = []
    for scenario, task, language, interaction in SMOKE_SCENARIOS:
        planned.append({"stage": "smoke", "split": "smoke", "scenario": scenario, "task": task,
                        "language": language, "interaction": interaction, "attitude": "cooperative",
                        "register": "standard", "difficulty": "compositional", "max_assistant_turns": 3})
    measurement_rows, repair_receipt = _measurement_slots(config, rng)
    for row in measurement_rows:
        planned.append({"stage": "measurement", "split": "train", "scenario": None,
                        "max_assistant_turns": 8, **row})
    used_families: set[str] = set()
    used_instances: set[str] = set()
    family_incompatibility_skips = 0
    seeds: list[dict[str, Any]] = []
    for index, row in enumerate(planned, 1):
        family_options = TASK_FAMILIES[row["task"]]
        for attempt in range(10000):
            family = family_options[(index + attempt) % len(family_options)]
            if not family_compatible(row, family):
                family_incompatibility_skips += 1
                continue
            fixture_rng = random.Random(int(sha256_json([config["seed"], index, attempt]), 16))
            fixture = fixtures.build(family, fixture_rng, row["difficulty"], row["language"])
            if fixtures.validate(fixture):
                continue
            content_family = core.content_family_key(family, fixture)
            instance_hash = core.digest({"structure": fixture["structure_id"], "parameters": fixture["parameters"],
                                         "interaction": row["interaction"]})
            if content_family in external_families | used_families or instance_hash in external_instances | used_instances:
                continue
            trajectory_id = ("SM" if row["stage"] == "smoke" else "ME") + f"{sum(s['stage'] == row['stage'] for s in seeds)+1:03d}"
            seed = Seed(trajectory_id=trajectory_id, stage=row["stage"], split=row["split"],
                        instance_hash=instance_hash, content_family=content_family, family=family,
                        task=row["task"], language=row["language"], difficulty=row["difficulty"],
                        interaction=row["interaction"], attitude=row["attitude"], register=row["register"],
                        max_assistant_turns=row["max_assistant_turns"], fixture=fixture).to_dict()
            if row["scenario"]:
                seed["scenario"] = row["scenario"]
                seed["scenario_instruction"] = SCENARIO_INSTRUCTIONS[row["scenario"]]
            with ledger.db() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO family_reservations VALUES(?,?,?,?,?)",
                           (content_family, row["split"], row["stage"], instance_hash, trajectory_id))
            seeds.append(seed)
            used_families.add(content_family)
            used_instances.add(instance_hash)
            break
        else:
            raise RuntimeError(f"could not allocate unique source family for slot {index}")
    axes = ("task", "language", "interaction", "attitude", "register", "difficulty")
    measurement_rows = [row for row in seeds if row["stage"] == "measurement"]
    manifest = {
        "version": config["version"], "manifest_schema_version": 3, "created_utc": utcnow(), "seed": config["seed"],
        "source_config_sha256": sha256_json(config), "config": config,
        "horizon_override": {"generator_default": 4, "smoke": 3, "measurement": 8},
        "source_registry": {"generator_registry_mode": "read_only", "external_family_count": len(external_families)},
        "planned_joint_counts": _counts(measurement_rows, axes),
        "actual_joint_counts": _counts(measurement_rows, axes),
        "joint_assignment_repairs": repair_receipt,
        "family_compatibility_rules": {key: sorted(value) for key, value in INTERACTION_FAMILIES.items()},
        "seeds": seeds,
    }
    manifest["joint_assignment_repairs"]["family_incompatibility_skips_before_selection"] = family_incompatibility_skips
    atomic_json(existing, manifest)
    atomic_json(state / "receipt.json", {"artifacts": {"manifest.json": {
        "sha256": __import__("hashlib").sha256(existing.read_bytes()).hexdigest(),
        "created_utc": utcnow(), "frozen": True}}})
    from budget import write_cost_ledger
    write_cost_ledger(state)
    for stage in ("smoke", "measurement"):
        (state / stage).mkdir(exist_ok=True)
        for name in ("user_events.jsonl", "trajectories.jsonl", "annotations.jsonl", "adjudications.jsonl",
                     "selection.jsonl", "candidates.jsonl", "rankings.jsonl", "preferences.jsonl", "rejected_pairs.jsonl"):
            (state / stage / name).touch(exist_ok=True)
    return manifest
