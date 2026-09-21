"""Idempotent call registry and the programme-wide GPU ledger for dialogue v2.

Sol has no call cap for this work (owner, 17 Sept); every call is still reserved before it is sent and recorded.
The GPU ledger counts against the shared dialogue programme cap: pilot ledger spend + this ledger's spend.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import pathlib
import sqlite3
import threading
from typing import Any

from common import PILOT_RUNTIME, V2_RUNTIME, append_jsonl, atomic_json, canonical, read_jsonl, utcnow

TOTAL_CAP_EUR = 10.0          # owner, 17 Sept: another EUR 5 on top of the original EUR 5 dialogue ceiling
OPERATIONAL_STOP_EUR = 9.0    # keeps the original EUR 1 reserve below the cap
RESERVE_EUR = 1.0
DEFAULT_EUR_PER_USD = 0.95
DEV_TAG = "development_demo"


class BudgetExceeded(RuntimeError):
    pass


class CallAlreadyAttempted(RuntimeError):
    """A reserved/failed/ambiguous call exists: never silently retry a possibly charged call."""

    def __init__(self, message: str, call_id: str = ""):
        super().__init__(message)
        self.call_id = call_id


class CallLedger:
    """SQLite reservations make replay idempotent; JSONL is the append-only audit stream."""

    _lock = threading.Lock()

    def __init__(self, runtime: str | pathlib.Path, run_tag: str):
        self.runtime = pathlib.Path(runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.run_tag = run_tag
        self.db_path = self.runtime / "call_registry.sqlite"
        self.log_path = self.runtime / "call_ledger.jsonl"
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS calls(
                  call_id TEXT PRIMARY KEY, provider TEXT NOT NULL, phase TEXT NOT NULL, run_tag TEXT NOT NULL,
                  status TEXT NOT NULL, reserved_utc TEXT NOT NULL, completed_utc TEXT,
                  request TEXT NOT NULL, result TEXT, error TEXT, wall_seconds REAL);
            """)

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.db_path, timeout=60)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=60000")
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, call_id: str, provider: str, phase: str, request: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM calls WHERE call_id=?", (call_id,)).fetchone()
            if old:
                if old["status"] == "complete":
                    return json.loads(old["result"])
                raise CallAlreadyAttempted(f"call {call_id} already {old['status']}; never silently retry", call_id)
            when = utcnow()
            db.execute("INSERT INTO calls(call_id,provider,phase,run_tag,status,reserved_utc,request) VALUES(?,?,?,?,?,?,?)",
                       (call_id, provider, phase, self.run_tag, "reserved", when, canonical(request)))
            append_jsonl(self.log_path, {"record": "call_reserved", "call_id": call_id, "provider": provider,
                                        "phase": phase, "run_tag": self.run_tag, "created_utc": when,
                                        "request": request, "purpose": DEV_TAG})
        return None

    def finish(self, call_id: str, *, result: dict[str, Any] | None = None, error: str | None = None,
               ambiguous: bool = False, wall_seconds: float | None = None) -> None:
        status = "ambiguous" if ambiguous else "failed" if error else "complete"
        when = utcnow()
        with self._lock, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM calls WHERE call_id=?", (call_id,)).fetchone()
            if not row:
                raise RuntimeError("finish without reservation")
            if row["status"] != "reserved":
                if row["status"] == status:
                    return
                raise RuntimeError("call completion is immutable")
            db.execute("UPDATE calls SET status=?,completed_utc=?,result=?,error=?,wall_seconds=? WHERE call_id=?",
                       (status, when, canonical(result) if result is not None else None, error, wall_seconds, call_id))
            append_jsonl(self.log_path, {"record": "call_completed", "call_id": call_id, "status": status,
                                        "run_tag": self.run_tag, "created_utc": when, "result": result,
                                        "error": error, "wall_seconds": wall_seconds})

    def get(self, call_id: str) -> dict[str, Any] | None:
        with self.db() as db:
            row = db.execute("SELECT * FROM calls WHERE call_id=?", (call_id,)).fetchone()
        return dict(row) if row else None

    def counts(self) -> dict[str, Any]:
        with self.db() as db:
            rows = [dict(r) for r in db.execute(
                "SELECT provider,phase,status,count(*) AS count, sum(coalesce(wall_seconds,0)) AS wall FROM calls "
                "GROUP BY provider,phase,status ORDER BY provider,phase,status")]
        return {"run_tag": self.run_tag, "by_phase": rows,
                "sol_calls": sum(r["count"] for r in rows if r["provider"] == "sol"),
                "target_calls": sum(r["count"] for r in rows if r["provider"] == "target")}


# --------------------------------------------------------------------------------------------------------------
# GPU ledger (programme-wide accounting)
# --------------------------------------------------------------------------------------------------------------
def _parse(ts: str) -> dt.datetime:
    value = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def pilot_spend(pilot_runtime: pathlib.Path = PILOT_RUNTIME) -> dict[str, Any]:
    rows = read_jsonl(pilot_runtime / "ledger.jsonl")
    stops = [r for r in rows if r.get("record") == "gpu_stop"]
    starts = [r for r in rows if r.get("record") == "gpu_start"]
    active = [r for r in starts if r["pod_id"] not in {s["pod_id"] for s in stops}]
    return {"spent_eur": sum(float(r.get("cost_eur", 0)) for r in stops), "sessions": len(stops), "active": active}


def v2_gpu_rows(runtime: pathlib.Path = V2_RUNTIME) -> list[dict[str, Any]]:
    return read_jsonl(runtime / "gpu_ledger.jsonl")


def programme_summary(runtime: pathlib.Path = V2_RUNTIME, pilot_runtime: pathlib.Path = PILOT_RUNTIME) -> dict[str, Any]:
    pilot = pilot_spend(pilot_runtime)
    rows = v2_gpu_rows(runtime)
    stops = [r for r in rows if r.get("record") == "gpu_stop"]
    starts = [r for r in rows if r.get("record") == "gpu_start"]
    active = [r for r in starts if r["pod_id"] not in {s["pod_id"] for s in stops}]
    v2_spent = sum(float(r.get("cost_eur_charged", 0)) for r in stops)
    total = pilot["spent_eur"] + v2_spent
    return {"pilot_spent_eur": pilot["spent_eur"], "pilot_sessions": pilot["sessions"], "pilot_active": pilot["active"],
            "v2_spent_eur": v2_spent, "v2_sessions": len(stops), "v2_active": active,
            "programme_spent_eur": total, "operational_stop_eur": OPERATIONAL_STOP_EUR, "total_cap_eur": TOTAL_CAP_EUR,
            "remaining_before_operational_stop_eur": OPERATIONAL_STOP_EUR - total,
            "by_stage": {stage: sum(float(r.get("cost_eur_charged", 0)) for r in stops if r.get("stage") == stage)
                         for stage in sorted({r.get("stage") for r in stops})}}


def conservative_deadline(start_utc: str, spent_eur: float, price_usd_hr: float, eur_per_usd: float,
                          max_session_minutes: float, setup_reserve_eur: float = 0.25, safety_factor: float = 1.15) -> str:
    hourly = price_usd_hr * eur_per_usd * safety_factor
    remaining = OPERATIONAL_STOP_EUR - setup_reserve_eur - spent_eur
    if hourly <= 0 or remaining <= 0:
        raise BudgetExceeded("no safe paid runtime remains before the operational stop")
    budget_hours = remaining / hourly
    hours = min(budget_hours, max_session_minutes / 60)
    return (_parse(start_utc) + dt.timedelta(hours=hours)).isoformat()


def gpu_start(pod_id: str, stage: str, price_usd_hr: float, post_utc: str, max_session_minutes: float,
              eur_per_usd: float = DEFAULT_EUR_PER_USD, runtime: pathlib.Path = V2_RUNTIME) -> dict[str, Any]:
    if not pod_id or price_usd_hr <= 0 or eur_per_usd <= 0:
        raise ValueError("positive price/rate and pod id required")
    summary = programme_summary(runtime)
    if summary["v2_active"] or summary["pilot_active"]:
        raise ValueError("another GPU session is recorded as active")
    if any(r.get("record") == "gpu_start" and r.get("pod_id") == pod_id for r in v2_gpu_rows(runtime)):
        raise ValueError("pod start already recorded")
    deadline = conservative_deadline(post_utc, summary["programme_spent_eur"], price_usd_hr, eur_per_usd,
                                     max_session_minutes)
    row = {"record": "gpu_start", "pod_id": pod_id, "stage": stage, "price_usd_hr": price_usd_hr,
           "eur_per_usd": eur_per_usd, "post_utc": post_utc, "recorded_utc": utcnow(),
           "shutdown_deadline_utc": deadline, "programme_spent_before_eur": summary["programme_spent_eur"],
           "operational_stop_eur": OPERATIONAL_STOP_EUR, "total_cap_eur": TOTAL_CAP_EUR, "purpose": DEV_TAG}
    append_jsonl(runtime / "gpu_ledger.jsonl", row)
    return row


def gpu_stop(pod_id: str, api_created_at: str | None = None, api_terminated_at: str | None = None,
             runtime: pathlib.Path = V2_RUNTIME) -> dict[str, Any]:
    rows = v2_gpu_rows(runtime)
    starts = [r for r in rows if r.get("record") == "gpu_start" and r.get("pod_id") == pod_id]
    if not starts:
        raise ValueError("no gpu_start for pod")
    if any(r.get("record") == "gpu_stop" and r.get("pod_id") == pod_id for r in rows):
        raise ValueError("pod stop already recorded")
    start = starts[-1]
    now = utcnow()
    begin = min(_parse(start["post_utc"]), _parse(api_created_at)) if api_created_at else _parse(start["post_utc"])
    end = max(_parse(now), _parse(api_terminated_at)) if api_terminated_at else _parse(now)
    seconds = max(0.0, (end - begin).total_seconds())
    rate = float(start["price_usd_hr"]) * float(start["eur_per_usd"])
    cost = seconds / 3600 * rate
    row = {"record": "gpu_stop", "pod_id": pod_id, "stage": start["stage"], "stop_utc": now,
           "api_created_at": api_created_at, "api_terminated_at": api_terminated_at,
           "billing_basis": "upper bound: earliest of POST/API createdAt to latest of local stop/API terminatedAt",
           "wall_seconds_charged": seconds, "cost_eur_charged": cost, "purpose": DEV_TAG}
    append_jsonl(runtime / "gpu_ledger.jsonl", row)
    atomic_json(runtime / "cost_ledger.json", {**programme_summary(runtime), "updated_utc": utcnow()})
    return row
