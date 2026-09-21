"""Smoke-measured Phase 1 admission forecast."""
from __future__ import annotations

import collections
import datetime as dt
import math
import json
import hashlib
import pathlib
import re
from typing import Any

from annotate import latest_trajectories
from budget import CallLedger, gpu_summary
from common import append_jsonl, atomic_json, read_json, read_jsonl, utcnow
from manifest import reduced_admission

CONSERVATIVE_MARGIN_FRACTION = 0.15


def estimate_for_size(size: int, max_turns: int, annotation_packets_per_call: float,
                      cost_per_target_completion_eur: float, target_rates: dict[str, float] | None = None,
                      sol_input_tokens_per_call: float = 0, productive_seconds_per_completion: float = 0,
                      gpu_cost_per_second_eur: float = 0, sol_latency_per_smoke_wave_seconds: float = 0,
                      smoke_batches_per_wave: float = 1, conservative_margin_fraction: float = 0) -> dict[str, Any]:
    turns = size * max_turns
    prefix_target = min(24, size)
    target_completions = turns + prefix_target * 2
    continuation_waves = max(0, max_turns - 1)
    batches_per_wave = math.ceil(size / 8)
    batch_scale = batches_per_wave / max(1.0, smoke_batches_per_wave)
    idle_per_wave = sol_latency_per_smoke_wave_seconds * batch_scale
    sol_idle_seconds = idle_per_wave * continuation_waves
    productive_seconds = target_completions * productive_seconds_per_completion
    margin_multiplier = 1 + conservative_margin_fraction
    base_gpu_eur = target_completions * cost_per_target_completion_eur
    idle_gpu_eur = sol_idle_seconds * gpu_cost_per_second_eur
    result = {
        "size": size, "raw_target_completions": turns,
        "candidate_target_completions": prefix_target * 2,
        "target_completions_total": target_completions,
        "estimated_gpu_eur": (base_gpu_eur + idle_gpu_eur) * margin_multiplier,
        "gpu_estimate": {
            "productive_wall_seconds_before_margin": productive_seconds,
            "continuation_waves": continuation_waves,
            "continuation_batches_per_wave": batches_per_wave,
            "measured_smoke_batches_per_wave": smoke_batches_per_wave,
            "sol_idle_seconds_per_wave_before_margin": idle_per_wave,
            "sol_idle_seconds_total_before_margin": sol_idle_seconds,
            "base_completion_cost_eur_before_margin": base_gpu_eur,
            "sol_idle_cost_eur_before_margin": idle_gpu_eur,
            "conservative_margin_fraction": conservative_margin_fraction,
            "estimated_billed_wall_seconds": (productive_seconds + sol_idle_seconds) * margin_multiplier,
        },
        "sol_calls": {
            "openings": math.ceil(size / 8),
            # User batches cannot cross depth waves: reserve every possible
            # post-response wave independently at the full admitted width.
            "user_continuation": sum(math.ceil(size / 8) for _ in range(max_turns - 1)),
            "annotation": math.ceil(turns / max(1.0, annotation_packets_per_call)),
            "candidate_review": math.ceil(prefix_target / 4),
        },
    }
    rates = target_rates or {}
    result["estimated_target_prompt_tokens"] = math.ceil((turns + prefix_target * 2) * rates.get("prompt_tokens", 0))
    result["estimated_target_completion_tokens"] = math.ceil((turns + prefix_target * 2) * rates.get("completion_tokens", 0))
    result["estimated_target_wall_seconds_serial_conservative"] = math.ceil((turns + prefix_target * 2) * rates.get("wall_seconds", 0))
    result["estimated_sol_input_tokens"] = math.ceil(sum(result["sol_calls"].values()) * sol_input_tokens_per_call)
    return result


def _timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


def gpu_rate_model(state: str | pathlib.Path, ledger: CallLedger) -> dict[str, Any]:
    """Build a billed rate only from sessions that observed target completions."""
    rows = read_jsonl(pathlib.Path(state) / "ledger.jsonl")
    starts = {row["pod_id"]: row for row in rows if row.get("record") == "gpu_start"}
    stops = {row["pod_id"]: row for row in rows if row.get("record") == "gpu_stop"}
    observed = {}
    for row in rows:
        if row.get("record") == "observed_completion" and row.get("provider") == "target":
            observed[(row.get("trajectory_id"), row.get("turn_index"))] = row
    with ledger.db() as db:
        continuation = [dict(row) for row in db.execute(
            "SELECT call_id,reserved_utc,completed_utc FROM calls "
            "WHERE provider='sol' AND status='complete' AND call_id LIKE 'sol:user:smoke:wave%'"
        )]
    continuation = [{**row, "latency_seconds": max(0.0, (
        _timestamp(row["completed_utc"]) - _timestamp(row["reserved_utc"])).total_seconds())}
        for row in continuation if row.get("reserved_utc") and row.get("completed_utc")]

    included = []
    excluded = []
    for pod_id, start in sorted(starts.items(), key=lambda item: item[1]["created_utc"]):
        stop = stops.get(pod_id)
        if stop is None:
            excluded.append({"pod_id": pod_id, "reason": "active_session_not_billed"})
            continue
        begin = _timestamp(start["created_utc"])
        end = _timestamp(stop["created_utc"])
        completions = [row for row in observed.values() if begin <= _timestamp(row["created_utc"]) <= end]
        sol_calls = [row for row in continuation
                     if begin <= _timestamp(row["reserved_utc"]) and _timestamp(row["completed_utc"]) <= end]
        detail = {"pod_id": pod_id, "started_utc": start["created_utc"], "stopped_utc": stop["created_utc"],
                  "billed_seconds": float(stop.get("wall_seconds", 0)),
                  "billed_eur": float(stop.get("cost_eur", 0)),
                  "observed_target_completions": len(completions),
                  "sol_continuation_idle_seconds": sum(row["latency_seconds"] for row in sol_calls)}
        if completions:
            included.append(detail)
        else:
            detail["reason"] = "zero_observed_target_completions"
            excluded.append(detail)
    if not included:
        raise ValueError("no completed GPU session with an observed target completion")

    basis_seconds = sum(row["billed_seconds"] for row in included)
    basis_eur = sum(row["billed_eur"] for row in included)
    basis_completions = sum(row["observed_target_completions"] for row in included)
    if basis_seconds <= 0 or basis_eur <= 0 or basis_completions <= 0:
        raise ValueError("successful GPU rate basis has no positive billed usage")
    productive_seconds = sum(max(0.0, row["billed_seconds"] - row["sol_continuation_idle_seconds"])
                             for row in included)
    productive_eur = sum(row["billed_eur"] *
                         max(0.0, row["billed_seconds"] - row["sol_continuation_idle_seconds"]) /
                         row["billed_seconds"] for row in included if row["billed_seconds"] > 0)
    wave_latencies: dict[str, float] = collections.defaultdict(float)
    wave_batches: collections.Counter[str] = collections.Counter()
    included_pods = {row["pod_id"] for row in included}
    for call in continuation:
        call_time = _timestamp(call["reserved_utc"])
        session = next((row for row in included if _timestamp(row["started_utc"]) <= call_time <=
                        _timestamp(row["stopped_utc"])), None)
        if session is None or session["pod_id"] not in included_pods:
            continue
        match = re.search(r":(wave\d+):", call["call_id"])
        wave = match.group(1) if match else call["call_id"]
        wave_latencies[wave] += call["latency_seconds"]
        wave_batches[wave] += 1
    latency_per_wave = sum(wave_latencies.values()) / len(wave_latencies) if wave_latencies else 0.0
    batches_per_wave = sum(wave_batches.values()) / len(wave_batches) if wave_batches else 1.0
    return {
        "included_sessions": included,
        "excluded_sessions": excluded,
        "exclusion_rule": "sessions with zero observed target completions remain spent but do not set the rate",
        "basis_billed_seconds": basis_seconds,
        "basis_billed_eur": basis_eur,
        "basis_observed_target_completions": basis_completions,
        "observed_sol_continuation_latency_by_wave_seconds": dict(sorted(wave_latencies.items())),
        "measured_sol_continuation_latency_per_wave_seconds": latency_per_wave,
        "measured_smoke_batches_per_wave": batches_per_wave,
        "productive_seconds_excluding_sol_idle": productive_seconds,
        "productive_eur_excluding_sol_idle": productive_eur,
        "productive_seconds_per_target_completion": productive_seconds / basis_completions,
        "productive_eur_per_target_completion": productive_eur / basis_completions,
        "basis_gpu_eur_per_second": basis_eur / basis_seconds,
        "conservative_margin_fraction": CONSERVATIVE_MARGIN_FRACTION,
        "conservative_margin_applies_to": "modeled productive GPU time/cost and explicit Sol-wave idle time/cost",
    }


def reallocate_sol_reservations(total: int, configured: dict[str, int], used: dict[str, int],
                                required_future: dict[str, int]) -> tuple[dict[str, int] | None, dict[str, Any]]:
    """Fund required future phases in priority order without increasing the cap."""
    phases = list(configured)
    minima = {phase: max(0, int(used.get(phase, 0))) for phase in phases}
    for phase in ("adjudication", "repairs"):
        minima[phase] = max(minima.get(phase, 0), 1)
    priority = ("annotation", "user_continuation", "openings", "candidate_review")
    for phase in priority:
        minima[phase] = minima.get(phase, 0) + int(required_future.get(phase, 0))
    required_total = sum(minima.values())
    receipt = {"priority": list(priority), "used_calls": dict(sorted(used.items())),
               "required_future_calls": dict(sorted(required_future.items())),
               "minimum_phase_caps": dict(sorted(minima.items())), "minimum_total": required_total,
               "overall_cap": total, "fundable": required_total <= total}
    if required_total > total:
        return None, receipt
    allocation = dict(minima)
    # Preserve all unused capacity as annotation contingency; adjudication and
    # repairs stay deliberately small and non-zero.
    allocation["annotation"] = allocation.get("annotation", 0) + total - required_total
    receipt["final_phase_caps"] = dict(sorted(allocation.items()))
    receipt["unallocated_calls"] = 0
    return allocation, receipt


def forecast(state: str | pathlib.Path, stage: str = "smoke", admit: int | None = None) -> dict[str, Any]:
    if stage != "smoke":
        raise ValueError("admission forecast is based on smoke only")
    state = pathlib.Path(state)
    forecast_path = state / "forecast.json"
    measurement_dir = state / "measurement"
    observed = [p.name for p in measurement_dir.glob("*") if p.is_file() and p.stat().st_size > 0]
    if observed:
        raise ValueError("cannot forecast after measurement artifacts exist: " + ",".join(sorted(observed)))
    revision_of = None
    if forecast_path.exists():
        prior = read_json(forecast_path)
        legacy_revised_plan = (prior.get("admission_status") == "smoke_only_revised_plan_required"
                               and prior.get("admitted_size") is None
                               and not prior.get("smoke", {}).get("gpu_rate_model")
                               and not prior.get("sol_reallocation"))
        if not legacy_revised_plan:
            raise ValueError("forecast is already frozen and cannot be overwritten")
        revision_of = hashlib.sha256(forecast_path.read_bytes()).hexdigest()
        append_jsonl(state / "forecast_revisions.jsonl", {
            "record": "superseded_forecast", "sha256": revision_of,
            "reason": "CK2 corrected zero-completion GPU rate basis and Sol phase reallocation",
            "superseded_utc": utcnow(), "forecast": prior})
        forecast_path.unlink()
    manifest = read_json(state / "manifest.json")
    config = manifest["config"]
    trajectories = latest_trajectories(state / "smoke" / "trajectories.jsonl")
    if len(trajectories) != config["smoke"]["trajectories"] or any(not t.get("terminal_code") for t in trajectories.values()):
        raise ValueError("complete smoke trajectories are required before forecast")
    turns = sum(t["assistant_turns"] for t in trajectories.values())
    if turns <= 0:
        raise ValueError("smoke observed no target completions")
    mean_turns = turns / len(trajectories)
    annotations = read_jsonl(state / "smoke" / "annotations.jsonl")
    if len(annotations) != turns:
        raise ValueError("all smoke turns must be annotated before forecast")
    ledger = CallLedger(state, config)
    counts = ledger.counts()["calls"]
    with ledger.db() as db:
        annotation_calls = db.execute(
            "SELECT count(*) FROM calls WHERE provider='sol' AND status='complete' AND call_id LIKE 'sol:annotation:smoke:%'"
        ).fetchone()[0]
    if annotation_calls <= 0:
        raise ValueError("smoke annotation call receipts are required before forecast")
    observed_packet_rate = len(annotations) / annotation_calls
    # Full-depth measurement prefixes may cross the long-packet threshold, so
    # never forecast more than the contract's four long packets per call.
    packet_rate = min(4.0, observed_packet_rate)
    gpu = gpu_summary(state)
    if gpu["spent_eur"] <= 0:
        raise ValueError("record a completed smoke GPU session before admission")
    with ledger.db() as db:
        target_rows = [dict(r) for r in db.execute("SELECT result FROM calls WHERE provider='target' AND phase='raw_rollout' AND status='complete'")]
        sol_rows = [dict(r) for r in db.execute("SELECT request FROM calls WHERE provider='sol' AND status='complete'")]
    target_results = [json.loads(r["result"]) for r in target_rows if r.get("result")]
    prompt_tokens = sum(int((r.get("usage") or {}).get("prompt_tokens", 0)) for r in target_results)
    completion_tokens = sum(int((r.get("usage") or {}).get("completion_tokens", 0)) for r in target_results)
    target_wall = sum(float(r.get("wall_seconds", 0)) for r in target_results)
    target_rates = {"prompt_tokens": prompt_tokens / max(1, len(target_results)),
                    "completion_tokens": completion_tokens / max(1, len(target_results)),
                    "wall_seconds": target_wall / max(1, len(target_results))}
    sol_input = [int(json.loads(r["request"]).get("estimated_input_tokens", 0)) for r in sol_rows]
    sol_input_per_call = sum(sol_input) / max(1, len(sol_input))
    rate_model = gpu_rate_model(state, ledger)
    configured_reservations = {k: int(v) for k, v in config["budget"]["sol_reservations"].items()}
    used = {phase: sum(r["count"] for r in counts if r["provider"] == "sol" and r["phase"] == phase)
            for phase in configured_reservations}
    total_sol_used = sum(r["count"] for r in counts if r["provider"] == "sol")
    total_sol_cap = int(config["budget"]["max_new_sol_calls"])
    remaining_operational = config["budget"]["operational_stop_eur"] - gpu["spent_eur"]
    options = []
    for size in config["measurement"]["admission_sizes"]:
        estimate = estimate_for_size(size, config["measurement"]["max_assistant_turns"], packet_rate,
                                     rate_model["productive_eur_per_target_completion"], target_rates,
                                     sol_input_per_call,
                                     rate_model["productive_seconds_per_target_completion"],
                                     rate_model["basis_gpu_eur_per_second"],
                                     rate_model["measured_sol_continuation_latency_per_wave_seconds"],
                                     rate_model["measured_smoke_batches_per_wave"],
                                     CONSERVATIVE_MARGIN_FRACTION)
        calls = estimate["sol_calls"]
        allocation, allocation_receipt = reallocate_sol_reservations(
            total_sol_cap, configured_reservations, used, calls)
        annotation_ok = allocation is not None and (
            used.get("annotation", 0) + calls["annotation"] <= allocation["annotation"])
        phase_ok = allocation is not None and all(
            used.get(phase, 0) + calls.get(phase, 0) <= allocation.get(phase, 0) for phase in calls)
        total_ok = total_sol_used + sum(calls.values()) <= total_sol_cap and allocation is not None
        cost_ok = estimate["estimated_gpu_eur"] <= remaining_operational
        estimate.update({"annotation_funded": annotation_ok, "phase_reservations_funded": phase_ok,
                         "total_sol_funded": total_ok, "gpu_funded_to_operational_stop": cost_ok,
                         "admissible": annotation_ok and phase_ok and total_ok and cost_ok,
                         "sol_reallocation": allocation_receipt,
                         "proposed_sol_reservations": allocation})
        options.append(estimate)
    feasible = [o for o in options if o["admissible"]]
    selected = max(feasible, key=lambda o: o["size"]) if feasible else None
    if admit is not None:
        matching = next((o for o in options if o["size"] == admit), None)
        if matching is None:
            raise ValueError("--admit must be one of 35,28,21,14")
        if not matching["admissible"]:
            raise ValueError("requested size is not fully funded, including annotation reservation")
        selected = matching
    allocation_option = selected or next((option for option in options if option["proposed_sol_reservations"]), None)
    reservations = (allocation_option["proposed_sol_reservations"] if allocation_option else
                    configured_reservations)
    forecast_row = {
        "version": manifest["version"], "created_utc": utcnow(), "basis_stage": "smoke",
        "smoke": {"trajectories": len(trajectories), "assistant_turns": turns, "mean_turns": mean_turns,
                  "gpu_spent_eur": gpu["spent_eur"],
                  "gpu_remaining_to_operational_stop_eur": remaining_operational,
                  "cost_per_target_completion_eur": rate_model["productive_eur_per_target_completion"],
                  "annotation_packets_per_call": packet_rate, "target_prompt_tokens": prompt_tokens,
                  "observed_annotation_packets_per_call": observed_packet_rate,
                  "target_completion_tokens": completion_tokens, "target_wall_seconds": target_wall,
                  "target_completion_tokens_per_second": completion_tokens / target_wall if target_wall else None,
                  "target_average_rates": target_rates, "sol_calls": len(sol_rows),
                  "sol_estimated_input_tokens": sum(sol_input), "sol_estimated_input_tokens_per_call": sol_input_per_call,
                  "gpu_rate_model": rate_model},
        "options": options, "admitted_size": selected["size"] if selected else None,
        "admission_status": "admitted" if selected else "smoke_only_revised_plan_required",
        "sol_reservations": reservations,
        "sol_reallocation": {"configured_phase_caps": configured_reservations,
                             "effective_phase_caps": reservations,
                             "based_on_size": allocation_option["size"] if allocation_option else None,
                             "calls_used_before_measurement": total_sol_used,
                             "overall_cap": total_sol_cap,
                             "cap_increased": False,
                             "receipt": allocation_option["sol_reallocation"] if allocation_option else None},
        "notes": ["Admission chosen before measurement outcomes are observed.",
                  "Annotation reservation is checked independently and cannot be consumed by candidates.",
                  "Raw generation and annotation reserve the full eight-turn admitted horizon; user batches are summed per depth wave.",
                  "Zero-completion GPU sessions remain deducted spend but are excluded from the completion-rate basis.",
                  "Measured Sol continuation latency is removed from the base completion rate and added explicitly per future depth wave.",
                  f"A {CONSERVATIVE_MARGIN_FRACTION:.0%} conservative margin is applied to modeled GPU productive and Sol-idle cost/time.",
                  "Sol phase reservations are reallocated in this frozen forecast without increasing the 120-call cap."],
    }
    if revision_of:
        forecast_row["revision_of_forecast_sha256"] = revision_of
        forecast_row["revision_reason"] = (
            "Prior smoke-only revised-plan forecast used zero-completion sessions in its rate and config phase caps.")
    if selected:
        admission = reduced_admission(manifest["seeds"], selected["size"], manifest["seed"])
        forecast_row["admitted_trajectory_ids"] = admission["trajectory_ids"]
        forecast_row["admitted_planned_counts"] = admission["actual_counts"]
        forecast_row["admission_allocation"] = admission
    else:
        forecast_row["admitted_trajectory_ids"] = []
    atomic_json(forecast_path, forecast_row)
    receipt_path = state / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    receipt.setdefault("artifacts", {})["forecast.json"] = {
        "sha256": hashlib.sha256(forecast_path.read_bytes()).hexdigest(),
        "created_utc": forecast_row["created_utc"], "frozen": True}
    atomic_json(receipt_path, receipt)
    return forecast_row
