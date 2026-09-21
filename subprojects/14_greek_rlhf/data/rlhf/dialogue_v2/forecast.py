"""EUR forecast for the D1/D2 collection session and the D1 branch session, from measured timings (plan §9)."""
from __future__ import annotations

import json
import statistics
from typing import Any

from common import V2_RUNTIME, atomic_json, read_json, read_jsonl, sha256_file, utcnow
from contracts import CANDIDATES_MAX, MAX_ASSISTANT_TURNS
from ledger import DEFAULT_EUR_PER_USD, OPERATIONAL_STOP_EUR, programme_summary

MEASURED = {
    # POST -> ACTIVE from pilot/round logs: 6.6 min (lambdalabs us-east-1), 4.6 min (lambdalabs), ~2.5 min (massedcompute L40S)
    "provisioning_minutes_observed": [6.6, 4.6, 2.5],
    # remote setup (preflight, vLLM install, Hub download, sha, serve ready): pilot sessions 18:10:45-18:14:14,
    # 18:54:29-18:57:55, 21:53:31-21:57:03
    "setup_minutes_observed": [3.5, 3.4, 3.5],
    "teardown_minutes": 1.5,
    "target_reply_seconds_p90_pilot": 5.8,
}


def _p90(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, int(0.9 * len(values)))]


def sol_latency_from_dryrun() -> dict[str, Any]:
    rows = read_jsonl(V2_RUNTIME / "dryrun" / "rgd" / "call_ledger.jsonl") + read_jsonl(V2_RUNTIME / "dryrun" / "dvi" / "call_ledger.jsonl")
    reserved = {r["call_id"]: r for r in rows if r.get("record") == "call_reserved"}
    by_phase: dict[str, list[float]] = {}
    for r in rows:
        if r.get("record") == "call_completed" and r.get("status") == "complete" and r.get("wall_seconds"):
            phase = reserved.get(r["call_id"], {}).get("phase", "?")
            if reserved.get(r["call_id"], {}).get("provider") == "sol":
                by_phase.setdefault(phase, []).append(float(r["wall_seconds"]))
    return {phase: {"n": len(v), "median": round(statistics.median(v), 1), "p90": round(_p90(v), 1), "max": round(max(v), 1)}
            for phase, v in by_phase.items()}


def build(price_usd_hr: float, eur_per_usd: float = DEFAULT_EUR_PER_USD, case_set: str = "v2",
          branch_completions_override: int | None = None) -> dict[str, Any]:
    lat = sol_latency_from_dryrun()
    # Review R1-7: the dry run had turn-1 prompts only; six-turn prompts are longer, so double the observed maximum.
    user_p90 = max(2 * lat.get("user_simulation", {}).get("max", 30.0), 45.0)
    actions_p90 = max(lat.get("user_actions", {}).get("max", 30.0), 15.0)
    resolver_p90 = max(lat.get("world_resolver", {}).get("max", 30.0), 15.0)
    repair_allowance = 0.25 * user_p90
    target = MEASURED["target_reply_seconds_p90_pilot"] * 3  # longer six-turn contexts, concurrency on one GPU
    per_turn_plain = target + user_p90 + repair_allowance
    per_turn_troubleshooting = per_turn_plain + actions_p90 + resolver_p90
    collection_minutes = MAX_ASSISTANT_TURNS * per_turn_troubleshooting / 60 * 1.3  # slowest conversation, 30% margin
    n_conversations, workers, branch_completions = 10, 10, 4 * CANDIDATES_MAX
    if case_set == "c60":
        # 60 conversations, 24 concurrent (one codex app-server); waves of the slowest conversation, no final-assessment call
        from contracts import C60_CANDIDATES
        n_conversations, workers, branch_completions = 60, 24, 60 * 2 * C60_CANDIDATES
        collection_minutes = -(-n_conversations // workers) * collection_minutes
    if branch_completions_override:                 # the 32-reply run: 112 points x 32, not 2 points x 4 per dialogue
        branch_completions = branch_completions_override
    provisioning = max(MEASURED["provisioning_minutes_observed"]) + 2
    setup = max(MEASURED["setup_minutes_observed"]) + 2.5
    session1 = provisioning + setup + collection_minutes + MEASURED["teardown_minutes"]
    branch_sampling_minutes = max(2.0, branch_completions * MEASURED["target_reply_seconds_p90_pilot"] * 3 / 16 / 60)
    session2 = provisioning + setup + branch_sampling_minutes + MEASURED["teardown_minutes"]
    rate = price_usd_hr * eur_per_usd / 60
    programme = programme_summary()
    remaining = programme["remaining_before_operational_stop_eur"]
    upper1, upper2 = session1 * rate, session2 * rate
    admitted = upper1 + upper2 <= remaining - 0.25
    return {
        "created_utc": utcnow(), "case_set": case_set, "conversations": n_conversations, "concurrent_conversations": workers,
        "branch_completions_upper": branch_completions, "price_cap_usd_hr": price_usd_hr, "eur_per_usd": eur_per_usd,
        "basis": ("upper bound: provisioning counted as billed; setup from three pilot sessions + 2.5 min; collection = six turns x "
                  "(target p90 x3 + Sol user-step max latency from the dry run + 25% repair allowance + troubleshooting actions and "
                  "resolver max latency) x 1.3 for the slowest of ten concurrent conversations; branch session samples 64 replies "
                  "with 16 concurrent requests; VAT/FX: EUR/USD 0.95 as in the pilot ledger"),
        "measured_inputs": MEASURED, "sol_latency_dry_run": lat,
        "session1_collect_minutes": round(session1, 1), "session1_upper_eur": round(upper1, 4),
        "session2_branch_minutes": round(session2, 1), "session2_upper_eur": round(upper2, 4),
        "total_upper_eur": round(upper1 + upper2, 4),
        "programme_spent_eur": programme["programme_spent_eur"], "remaining_before_operational_stop_eur": remaining,
        "safety_margin_eur": 0.25, "admission_status": "admitted" if admitted else "shortfall",
        "shortfall_eur": 0.0 if admitted else round(upper1 + upper2 - (remaining - 0.25), 4),
        # Watchdog caps: generous enough that a slow Sol phase does not kill a healthy collection, and further bounded at
        # run time by ledger.conservative_deadline (programme spend, operational stop minus EUR 0.25, 15% price margin).
        "session_caps_minutes": {"collect": max(50.0, round(session1 * 1.5, 1)), "branch": max(30.0, round(session2 * 1.5, 1))},
        "sol": "no call cap (owner); calls recorded, not a gate",
    }


def freeze(forecast: dict[str, Any]) -> dict[str, Any]:
    path = V2_RUNTIME / "forecast.json"
    atomic_json(path, forecast)
    receipt_path = V2_RUNTIME / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    receipt["artifacts"]["forecast.json"] = {"sha256": sha256_file(path), "frozen": True, "created_utc": utcnow()}
    atomic_json(receipt_path, receipt)
    return receipt


def verify_frozen(stage: str) -> dict[str, Any]:
    path = V2_RUNTIME / "forecast.json"
    receipt = read_json(V2_RUNTIME / "receipt.json")["artifacts"]["forecast.json"]
    if not receipt.get("frozen") or receipt["sha256"] != sha256_file(path):
        raise SystemExit("forecast receipt missing, unfrozen or hash mismatch")
    forecast = read_json(path)
    if forecast["admission_status"] != "admitted":
        raise SystemExit(f"forecast not admitted: shortfall EUR {forecast['shortfall_eur']}")
    programme = programme_summary()
    if programme["v2_active"] or programme["pilot_active"]:
        raise SystemExit("a GPU session is already recorded as active")
    needed = forecast["session1_upper_eur"] if stage == "collect" else forecast["session2_upper_eur"]
    if programme["programme_spent_eur"] + needed > OPERATIONAL_STOP_EUR - 0.1:
        raise SystemExit(f"stage {stage} forecast EUR {needed} would cross the operational stop")
    return {"stage": stage, "max_session_minutes": forecast["session_caps_minutes"][stage],
            "price_cap_usd_hr": forecast["price_cap_usd_hr"], "programme_spent_eur": programme["programme_spent_eur"]}


if __name__ == "__main__":
    print(json.dumps(build(1.99), indent=1))
