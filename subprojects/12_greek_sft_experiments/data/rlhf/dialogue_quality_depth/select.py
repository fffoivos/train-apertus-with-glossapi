"""Deterministic P/R/C eligibility and allocation with inclusion receipts."""
from __future__ import annotations

import collections
import itertools
import math
import pathlib
import random
from fractions import Fraction
from typing import Any

from annotate import effective_annotations, latest_trajectories
from common import append_jsonl, read_json, read_jsonl, sha256_json, sha256_text, utcnow
from schemas import Selection


def largest_remainders(weights: dict[str, int], total: int, capacities: dict[str, int] | None = None) -> dict[str, int]:
    if total < 0 or any(v < 0 for v in weights.values()):
        raise ValueError("nonnegative allocation required")
    capacities = capacities or dict(weights)
    active = {k: v for k, v in weights.items() if v > 0 and capacities.get(k, 0) > 0}
    output = {k: 0 for k in weights}
    remaining = min(total, sum(capacities.get(k, 0) for k in active))
    while remaining and active:
        weight_sum = sum(active.values())
        raw = {k: Fraction(v * remaining, weight_sum) for k, v in active.items()}
        add = {k: min(int(raw[k]), capacities[k] - output[k]) for k in active}
        for key, n in add.items():
            output[key] += n
            remaining -= n
        # Allocate the same round's largest fractional remainders before
        # recomputing shares; otherwise a 3:1 allocation of three becomes 3:0.
        order = sorted(active, key=lambda k: (-(raw[k] - int(raw[k])), k))
        for key in order:
            if remaining and output[key] < capacities[key]:
                output[key] += 1
                remaining -= 1
        active = {k: weights[k] for k in active if output[k] < capacities[k]}
    return output


def depth_bin(depth: int) -> str:
    return "early" if depth <= 2 else "middle" if depth <= 5 else "late"


def eligible_points(state: str | pathlib.Path, stage: str = "measurement") -> dict[str, list[dict[str, Any]]]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    seeds = {s["trajectory_id"]: s for s in manifest["seeds"] if s["stage"] == stage}
    trajectories = latest_trajectories(state / stage / "trajectories.jsonl")
    annotations = effective_annotations(state, stage)
    by_tid: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in annotations:
        by_tid[row["trajectory_id"]].append(row)
    out = {"P": [], "R": [], "C": []}
    for tid, rows in by_tid.items():
        rows.sort(key=lambda r: r["turn_index"])
        messages = trajectories[tid]["messages"]
        assistants = [(i, m) for i, m in enumerate(messages) if m["role"] == "assistant"]
        first_serious = next((r for r in rows if r["local_quality"] == "serious"), None)
        # Boundary-dependent points require explicit root adjudication.
        if first_serious and first_serious.get("adjudicated"):
            turn = first_serious["turn_index"]
            idx, message = assistants[turn - 1]
            out["P"].append(_point(seeds[tid], "P", turn, messages[:idx], message["content"], first_serious))
            recovery = next((r for r in rows if r["turn_index"] > turn and r["recovery_opportunity"] and r.get("adjudicated")), None)
            if recovery:
                rturn = recovery["turn_index"]
                ridx, rmessage = assistants[rturn - 1]
                out["R"].append(_point(seeds[tid], "R", rturn, messages[:ridx], rmessage["content"], recovery))
        serious_turns = [r["turn_index"] for r in rows if r["local_quality"] == "serious"]
        for row in rows:
            if row["local_quality"] != "good" or any(t < row["turn_index"] for t in serious_turns):
                continue
            turn = row["turn_index"]
            idx, message = assistants[turn - 1]
            point = _point(seeds[tid], "C", turn, messages[:idx], message["content"], row)
            point["trajectory_no_observed_failure"] = not serious_turns
            out["C"].append(point)
    return out


def _point(seed: dict[str, Any], kind: str, turn: int, prefix: list[dict[str, str]], response: str,
           annotation: dict[str, Any]) -> dict[str, Any]:
    if not prefix or prefix[-1]["role"] != "user":
        raise ValueError("selected prefix must end at the user turn")
    return {"trajectory_id": seed["trajectory_id"], "kind": kind, "depth": turn,
            "depth_bin": depth_bin(turn), "prefix_messages": prefix, "prefix_sha256": sha256_json(prefix),
            "original_response": response, "annotation_id": annotation["annotation_id"],
            "language": seed["language"], "task": seed["task"]}


def allocate_points(eligible: dict[str, list[dict[str, Any]]], admitted_size: int,
                    seed: int = 9162602) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = min(24, admitted_size)
    control_target = math.ceil(.25 * target)
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    used: collections.Counter[str] = collections.Counter()
    selected_prefixes: set[str] = set()
    redistributions: list[dict[str, Any]] = []
    tie = {id(point): rng.random() for values in eligible.values() for point in values}

    def feasible(points, kind=None, distinct_only=False):
        already_kind = {p["trajectory_id"] for p in selected if kind and p["kind"] == kind}
        return [p for p in points if p["prefix_sha256"] not in selected_prefixes and used[p["trajectory_id"]] < 2
                and (not distinct_only or used[p["trajectory_id"]] == 0)
                and (not kind or p["trajectory_id"] not in already_kind)]

    def take(point):
        selected.append(point); selected_prefixes.add(point["prefix_sha256"]); used[point["trajectory_id"]] += 1

    def spread_take(points, count, kind=None, distinct_only=False, depth_apportion=True):
        taken = 0
        pool = feasible(points, kind, distinct_only)
        bin_quota = {}
        if depth_apportion and pool and count:
            caps = dict(collections.Counter(p["depth_bin"] for p in pool))
            bin_quota = largest_remainders(caps, min(count, len(pool)), caps)
        strata = collections.Counter((p["task"], p["language"]) for p in selected)
        while taken < count:
            pool = feasible(points, kind, distinct_only)
            if not pool:
                break
            with_quota = [p for p in pool if not bin_quota or bin_quota.get(p["depth_bin"], 0) > 0]
            if not with_quota:
                with_quota = pool
            with_quota.sort(key=lambda p: (
                not p.get("trajectory_no_observed_failure", False) if p["kind"] == "C" else False,
                strata[(p["task"], p["language"])], used[p["trajectory_id"]], tie[id(p)]))
            point = with_quota[0]
            take(point); taken += 1; strata[(point["task"], point["language"])] += 1
            if bin_quota.get(point["depth_bin"], 0) > 0:
                bin_quota[point["depth_bin"]] -= 1
        return taken

    def match_depth_quota(points, quota, distinct_only):
        """Match depth quotas without spending a trajectory needed by another bin."""
        pool = feasible(points, distinct_only=distinct_only)
        local_used: collections.Counter[str] = collections.Counter()
        local_prefixes: set[str] = set()

        def solve(remaining, chosen):
            if not any(remaining.values()):
                return list(chosen)
            bins = [name for name, value in remaining.items() if value]
            candidates_by_bin = {}
            for name in bins:
                candidates_by_bin[name] = [p for p in pool if p["depth_bin"] == name
                    and p["prefix_sha256"] not in local_prefixes
                    and used[p["trajectory_id"]] + local_used[p["trajectory_id"]] < 2
                    and (not distinct_only or local_used[p["trajectory_id"]] == 0)]
            name = min(bins, key=lambda value: (len(candidates_by_bin[value]), value))
            strata = collections.Counter((p["task"], p["language"]) for p in selected + chosen)
            candidates_by_bin[name].sort(key=lambda p: (
                not p.get("trajectory_no_observed_failure", False),
                strata[(p["task"], p["language"])],
                used[p["trajectory_id"]] + local_used[p["trajectory_id"]], tie[id(p)]))
            for point in candidates_by_bin[name]:
                tid = point["trajectory_id"]
                local_used[tid] += 1
                local_prefixes.add(point["prefix_sha256"])
                remaining[name] -= 1
                answer = solve(remaining, chosen + [point])
                if answer is not None:
                    return answer
                remaining[name] += 1
                local_prefixes.remove(point["prefix_sha256"])
                local_used[tid] -= 1
            return None

        return solve(dict(quota), [])

    def control_batch(points, count, distinct_only, phase):
        pool = feasible(points, distinct_only=distinct_only)
        if not pool or not count:
            return [], {name: 0 for name in ("early", "middle", "late")}, {}
        caps = {}
        for name in ("early", "middle", "late"):
            by_tid = collections.Counter(p["trajectory_id"] for p in pool if p["depth_bin"] == name)
            caps[name] = sum(min(amount, 1 if distinct_only else 2 - used[tid])
                             for tid, amount in by_tid.items())
        point_capacity = collections.Counter(p["trajectory_id"] for p in pool)
        total_capacity = sum(min(amount, 1 if distinct_only else 2 - used[tid])
                             for tid, amount in point_capacity.items())
        desired = min(count, total_capacity, len(pool))
        initial = largest_remainders(caps, desired, caps)
        bins = ("early", "middle", "late")
        matched = match_depth_quota(pool, initial, distinct_only)
        final = dict(initial)
        if matched is None:
            alternatives = []
            for values in itertools.product(*(range(caps[name] + 1) for name in bins)):
                if sum(values) != desired:
                    continue
                proposal = dict(zip(bins, values))
                distance = sum(abs(proposal[name] - initial[name]) for name in bins)
                alternatives.append((distance, -sum(value > 0 for value in values), values, proposal))
            for _, _, _, proposal in sorted(alternatives):
                matched = match_depth_quota(pool, proposal, distinct_only)
                if matched is not None:
                    final = proposal
                    break
        if matched is None:
            matched = []
            final = {name: 0 for name in bins}
        if final != initial or len(matched) < count:
            redistributions.append({"reason": "control_depth_quota_recompute", "phase": phase,
                                    "old_quota": initial, "depth_capacities": caps,
                                    "new_quota": final, "achieved": len(matched)})
        return matched, initial, final

    controls = list(eligible["C"])
    first_batch, initial_control_depth_quota, first_control_depth_quota = control_batch(
        controls, control_target, True, "distinct_trajectories")
    for point in first_batch:
        take(point)
    first_controls = len(first_batch)
    second_controls = 0
    if first_controls < control_target:
        second_batch, _, second_control_depth_quota = control_batch(
            controls, control_target - first_controls, False, "second_capacity")
        for point in second_batch:
            take(point)
        second_controls = len(second_batch)
        redistributions.append({"reason": "control_second_pass_reuses_trajectory_capacity",
                                "old_quota": {"C_distinct": control_target},
                                "achieved": {"C_distinct": first_controls},
                                "new_quota": {"C_distinct": first_controls, "C_reuse": second_controls},
                                "second_pass_depth_quota": second_control_depth_quota})
    remaining = target - len(selected)
    capacity = {kind: len({p["trajectory_id"] for p in feasible(eligible[kind], kind)}) for kind in ("P", "R")}
    quotas = largest_remainders(capacity, remaining, capacity)
    achieved = {kind: spread_take(eligible[kind], quotas[kind], kind=kind) for kind in ("P", "R")}
    if any(achieved[kind] < quotas[kind] for kind in ("P", "R")):
        remaining_capacity = {kind: len({p["trajectory_id"] for p in feasible(eligible[kind], kind)}) for kind in ("P", "R")}
        recomputed = largest_remainders(remaining_capacity, target - len(selected), remaining_capacity)
        redistributions.append({"reason": "initial_capacity_shortfall_recompute", "old_quota": dict(quotas),
                                "achieved": dict(achieved), "remaining_capacity": remaining_capacity,
                                "new_quota": recomputed})
    # Recompute from currently feasible cells until no more error point fits.
    while len(selected) < target:
        available = {kind: len({p["trajectory_id"] for p in feasible(eligible[kind], kind)}) for kind in ("P", "R")}
        if not any(available.values()):
            break
        slots = target - len(selected)
        new_quota = largest_remainders(available, slots, available)
        before = len(selected)
        round_achieved = {kind: spread_take(eligible[kind], new_quota[kind], kind=kind) for kind in ("P", "R")}
        redistributions.append({"reason": "capacity_shortfall_recompute", "old_quota": dict(quotas),
                                "achieved": dict(achieved), "remaining_capacity": available,
                                "new_quota": new_quota, "new_achieved": round_achieved})
        for kind in achieved:
            achieved[kind] += round_achieved[kind]
        quotas = new_quota
        if len(selected) == before:
            break
    if len(selected) < target:
        old = len(selected)
        fallback_batch, _, fallback_depth_quota = control_batch(
            controls, target - len(selected), False, "error_shortfall_fill")
        for point in fallback_batch:
            take(point)
        added = len(fallback_batch)
        redistributions.append({"reason": "unfilled_error_slots_to_controls", "old_quota": {"total": target, "filled": old},
                                "new_quota": {"additional_C": target - old}, "achieved": {"additional_C": added},
                                "fallback_depth_quota": fallback_depth_quota})
    receipt = {"seed": seed, "target": target, "control_target": control_target,
               "initial_control_depth_quota": initial_control_depth_quota,
               "achieved_control_depth_counts": dict(collections.Counter(
                   p["depth_bin"] for p in selected if p["kind"] == "C")),
               "eligible_distinct_trajectories": {k: len({p["trajectory_id"] for p in v}) for k, v in eligible.items()},
               "initial_error_quota": largest_remainders(capacity, remaining, capacity),
               "selected_counts": dict(collections.Counter(p["kind"] for p in selected)),
               "redistributions": redistributions, "max_per_trajectory": 2}
    return selected, receipt


def select(state: str | pathlib.Path, stage: str = "measurement") -> dict[str, Any]:
    if stage != "measurement":
        raise ValueError("selection is measurement-only")
    state = pathlib.Path(state)
    report_path = state / stage / "quality_depth_report.json"
    receipt_path = state / "receipt.json"
    if not report_path.exists() or not receipt_path.exists():
        raise ValueError("selection requires a frozen report")
    receipts = read_json(receipt_path).get("artifacts", {})
    entry = receipts.get(f"{stage}/quality_depth_report.json")
    if not entry or not entry.get("frozen") or entry["sha256"] != sha256_text(report_path.read_text(encoding="utf-8")):
        raise ValueError("frozen report receipt mismatch")
    forecast_path = state / "forecast.json"
    if not forecast_path.exists():
        raise ValueError("selection requires the frozen pre-outcome admission forecast")
    manifest = read_json(state / "manifest.json")
    admitted = read_json(forecast_path).get("admitted_size")
    if admitted is None:
        raise ValueError("forecast admitted no measurement size")
    eligible = eligible_points(state, stage)
    points, allocation = allocate_points(eligible, int(admitted), manifest["seed"])
    path = state / stage / "selection.jsonl"
    if read_jsonl(path):
        raise ValueError("selection is frozen once written")
    for index, point in enumerate(points, 1):
        inclusion = {**allocation, "eligible_count_in_kind": len(eligible[point["kind"]]),
                     "reason": f"deterministic {point['kind']} allocation at {point['depth_bin']} depth",
                     "selected_utc": utcnow()}
        row = Selection(selection_id=f"SEL{index:03d}", trajectory_id=point["trajectory_id"], kind=point["kind"],
                        depth=point["depth"], prefix_messages=point["prefix_messages"],
                        prefix_sha256=point["prefix_sha256"], original_response=point["original_response"],
                        inclusion_receipt=inclusion, language=point["language"], task=point["task"]).to_dict()
        append_jsonl(path, row)
    return {"selected": len(points), "allocation": allocation}
