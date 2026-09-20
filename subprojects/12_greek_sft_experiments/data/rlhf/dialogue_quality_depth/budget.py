"""Atomic call accounting, GPU cost ledger, and deadline watchdog helpers."""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import math
import pathlib
import sqlite3
from dataclasses import asdict
from typing import Any

from common import append_jsonl, atomic_json, canonical, read_json, read_jsonl, utcnow


class BudgetExceeded(RuntimeError):
    pass


class CallLedger:
    """SQLite makes reservations atomic; JSONL is the immutable audit stream."""
    def __init__(self, state: str | pathlib.Path, config: dict[str, Any] | None = None):
        self.state = pathlib.Path(state)
        self.state.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state / "registry.sqlite"
        self.log_path = self.state / "ledger.jsonl"
        self.config = config or self._load_config()
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS calls(
                  call_id TEXT PRIMARY KEY, provider TEXT NOT NULL, phase TEXT NOT NULL,
                  status TEXT NOT NULL, reserved_utc TEXT NOT NULL, completed_utc TEXT,
                  request TEXT NOT NULL, result TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS family_reservations(
                  content_family TEXT PRIMARY KEY, split TEXT NOT NULL, stage TEXT NOT NULL,
                  instance_hash TEXT UNIQUE NOT NULL, trajectory_id TEXT UNIQUE NOT NULL);
            """)

    def _load_config(self) -> dict[str, Any]:
        for name in ("source_config.json", "manifest.json"):
            path = self.state / name
            if path.exists():
                value = read_json(path)
                return value.get("config", value)
        return {"budget": {"max_new_sol_calls": 120, "sol_reservations": {}}}

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        try:
            with db:
                yield db
        finally:
            db.close()

    def _sol_limits(self) -> tuple[int, dict[str, int]]:
        budget = self.config.get("budget", {})
        base_total = int(budget.get("max_new_sol_calls", 120))
        total = base_total
        reservations = {str(k): int(v) for k, v in budget.get("sol_reservations", {}).items()}
        forecast_path = self.state / "forecast.json"
        if forecast_path.exists():
            forecast = read_json(forecast_path)
            moved = forecast.get("sol_reservations")
            if moved is not None:
                moved = {str(k): int(v) for k, v in moved.items()}
                if sum(moved.values()) != base_total or any(v < 0 for v in moved.values()):
                    raise BudgetExceeded("invalid forecast Sol reallocation")
                reservations = moved
            extensions = forecast.get("extensions") or {}
            if not isinstance(extensions, dict):
                raise BudgetExceeded("invalid forecast Sol extensions")
            for phase, extension in extensions.items():
                if not isinstance(extension, dict) or not str(extension.get("authorised_by", "")).strip():
                    raise BudgetExceeded(f"invalid Sol extension authorization: {phase}")
                allowance = int(extension.get("max_new_sol_calls", 0))
                if allowance <= 0:
                    raise BudgetExceeded(f"invalid Sol extension allowance: {phase}")
                total += allowance
                reservations[str(phase)] = reservations.get(str(phase), 0) + allowance
        return total, reservations

    def reserve(self, call_id: str, provider: str, phase: str, request: dict[str, Any]) -> dict[str, Any] | None:
        """Return a completed result for idempotent replay, otherwise reserve once."""
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM calls WHERE call_id=?", (call_id,)).fetchone()
            if old:
                if old["status"] == "complete":
                    return json.loads(old["result"])
                raise RuntimeError(f"call {call_id} already {old['status']}; never silently retry")
            if provider == "sol":
                total, reservations = self._sol_limits()
                used_total = db.execute("SELECT count(*) FROM calls WHERE provider='sol'").fetchone()[0]
                used_phase = db.execute("SELECT count(*) FROM calls WHERE provider='sol' AND phase=?", (phase,)).fetchone()[0]
                if used_total >= total:
                    raise BudgetExceeded("Sol total call cap exhausted")
                if phase not in reservations:
                    raise BudgetExceeded(f"no Sol reservation for phase {phase}")
                if used_phase >= reservations[phase]:
                    raise BudgetExceeded(f"Sol phase reservation exhausted: {phase}")
            when = utcnow()
            db.execute("INSERT INTO calls(call_id,provider,phase,status,reserved_utc,request) VALUES(?,?,?,?,?,?)",
                       (call_id, provider, phase, "reserved", when, canonical(request)))
            append_jsonl(self.log_path, {"record": "call_reserved", "call_id": call_id, "provider": provider,
                                        "phase": phase, "created_utc": when, "request": request})
        return None

    def finish(self, call_id: str, *, result: dict[str, Any] | None = None, error: str | None = None,
               ambiguous: bool = False) -> None:
        status = "ambiguous" if ambiguous else "failed" if error else "complete"
        when = utcnow()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM calls WHERE call_id=?", (call_id,)).fetchone()
            if not row:
                raise RuntimeError("finish without reservation")
            if row["status"] != "reserved":
                if row["status"] == status:
                    return
                raise RuntimeError("call completion is immutable")
            db.execute("UPDATE calls SET status=?,completed_utc=?,result=?,error=? WHERE call_id=?",
                       (status, when, canonical(result) if result is not None else None, error, call_id))
            append_jsonl(self.log_path, {"record": "call_completed", "call_id": call_id, "status": status,
                                        "created_utc": when, "result": result, "error": error})

    def get(self, call_id: str) -> dict[str, Any] | None:
        with self.db() as db:
            row = db.execute("SELECT * FROM calls WHERE call_id=?", (call_id,)).fetchone()
        return dict(row) if row else None

    def counts(self) -> dict[str, Any]:
        with self.db() as db:
            by = [dict(row) for row in db.execute("SELECT provider,phase,status,count(*) AS count FROM calls GROUP BY provider,phase,status")]
        return {"calls": by, "sol_reserved_attempts": sum(r["count"] for r in by if r["provider"] == "sol")}


def gpu_start(state: str | pathlib.Path, pod_id: str, price_usd_hr: float, eur_per_usd: float,
              now: str | None = None) -> dict[str, Any]:
    if not pod_id or price_usd_hr <= 0 or eur_per_usd <= 0:
        raise ValueError("positive price/rate and pod id required")
    path = pathlib.Path(state) / "ledger.jsonl"
    rows = read_jsonl(path)
    if any(r.get("record") == "gpu_start" and r.get("pod_id") == pod_id for r in rows):
        raise ValueError("pod start already recorded")
    if gpu_summary(state)["active"]:
        raise ValueError("another GPU session is already active")
    started = now or utcnow()
    spent = gpu_summary(state)["spent_eur"]
    deadline = conservative_deadline(started, spent, price_usd_hr, eur_per_usd)
    row = {"record": "gpu_start", "pod_id": pod_id, "price_usd_hr": price_usd_hr,
           "eur_per_usd": eur_per_usd, "created_utc": started, "shutdown_deadline_utc": deadline,
           "operational_stop_eur": 4.0, "total_cap_eur": 5.0, "reserve_eur": 1.0}
    append_jsonl(path, row)
    return row


def gpu_stop(state: str | pathlib.Path, pod_id: str | None = None, other_eur: float = 0,
             now: str | None = None) -> dict[str, Any]:
    if other_eur < 0:
        raise ValueError("other fees cannot be negative")
    path = pathlib.Path(state) / "ledger.jsonl"
    rows = read_jsonl(path)
    starts = [r for r in rows if r.get("record") == "gpu_start"]
    stopped = {r["pod_id"] for r in rows if r.get("record") == "gpu_stop"}
    candidates = [r for r in starts if r["pod_id"] not in stopped and (pod_id is None or r["pod_id"] == pod_id)]
    if len(candidates) != 1:
        raise ValueError("exactly one active matching pod required")
    start = candidates[0]
    end = now or utcnow()
    seconds = max(0.0, (dt.datetime.fromisoformat(end) - dt.datetime.fromisoformat(start["created_utc"])).total_seconds())
    cost = seconds / 3600 * float(start["price_usd_hr"]) * float(start["eur_per_usd"]) + other_eur
    row = {"record": "gpu_stop", "pod_id": start["pod_id"], "created_utc": end,
           "wall_seconds": seconds, "other_eur": other_eur, "cost_eur": cost}
    append_jsonl(path, row)
    write_cost_ledger(state)
    return row


def gpu_summary(state: str | pathlib.Path) -> dict[str, Any]:
    rows = read_jsonl(pathlib.Path(state) / "ledger.jsonl")
    stops = [r for r in rows if r.get("record") == "gpu_stop"]
    active = [r for r in rows if r.get("record") == "gpu_start" and r.get("pod_id") not in {s.get("pod_id") for s in stops}]
    return {"spent_eur": sum(float(r.get("cost_eur", 0)) for r in stops), "active": active,
            "completed_sessions": len(stops)}


def conservative_deadline(start_utc: str, spent_eur: float, price_usd_hr: float, eur_per_usd: float,
                          operational_stop_eur: float = 4.0, setup_reserve_eur: float = 0.25,
                          safety_factor: float = 1.15) -> str:
    hourly = price_usd_hr * eur_per_usd * safety_factor
    remaining = operational_stop_eur - setup_reserve_eur - spent_eur
    if hourly <= 0 or remaining <= 0:
        raise BudgetExceeded("no safe paid runtime remains")
    deadline = dt.datetime.fromisoformat(start_utc) + dt.timedelta(hours=remaining / hourly)
    return deadline.isoformat()


def shutdown_due(deadline_utc: str, now_utc: str | None = None) -> bool:
    now = dt.datetime.fromisoformat(now_utc) if now_utc else dt.datetime.now(dt.timezone.utc)
    deadline = dt.datetime.fromisoformat(deadline_utc)
    return now >= deadline


def write_cost_ledger(state: str | pathlib.Path) -> dict[str, Any]:
    summary = gpu_summary(state)
    summary.update({"cap_eur": 5.0, "operational_stop_eur": 4.0, "reserve_eur": 1.0,
                    "updated_utc": utcnow()})
    atomic_json(pathlib.Path(state) / "cost_ledger.json", summary)
    return summary
