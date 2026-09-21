#!/usr/bin/env python3
"""Single orchestrator CLI for the dialogue quality-depth pilot."""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
from typing import Any

import analyse
import annotate as annotation_module
import budget
import candidates as candidate_module
import export_pairs
import forecast as forecast_module
import manifest as manifest_module
import openings as openings_module
import rank as rank_module
import resample as resample_module
import rollout as rollout_module
import select as selection_module
from clients import CodexSolClient, HTTPApertusClient
from common import read_json, read_jsonl


class CLIParseError(ValueError):
    pass


class MachineArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CLIParseError(message)

    def parse_args(self, args=None, namespace=None):
        parsed = super().parse_args(args, namespace)
        if getattr(parsed, "command", None) == "rollout":
            try:
                rollout_module.validate_stage_horizon(parsed.stage, parsed.max_turns)
            except ValueError as exc:
                self.error(str(exc))
        return parsed


def summary(command: str, values: dict[str, Any], ok: bool = True) -> None:
    fields = []
    for key in sorted(values):
        value = values[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        fields.append(f"{key}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))}")
    print(("DQD_OK" if ok else "DQD_FAIL") + f" {command}" + (" " + " ".join(fields) if fields else ""))


def with_sol(fn):
    sol = CodexSolClient()
    sol.start()
    try:
        return fn(sol)
    finally:
        sol.close()


def status(state: pathlib.Path) -> dict[str, Any]:
    result: dict[str, Any] = {"initialized": (state / "manifest.json").exists()}
    if not result["initialized"]:
        return result
    manifest = read_json(state / "manifest.json")
    ledger = budget.CallLedger(state, manifest["config"])
    result["calls"] = ledger.counts()
    result["gpu"] = budget.gpu_summary(state)
    result["forecast"] = read_json(state / "forecast.json").get("admitted_size") if (state / "forecast.json").exists() else None
    result["stages"] = {}
    for stage in ("smoke", "measurement"):
        latest = {}
        for row in read_jsonl(state / stage / "trajectories.jsonl"):
            latest[row["trajectory_id"]] = row
        result["stages"][stage] = {
            "openings": sum(r.get("turn_index") == 0 for r in read_jsonl(state / stage / "user_events.jsonl")),
            "trajectories": len(latest),
            "terminal": dict(collections.Counter(r.get("terminal_code") or "active" for r in latest.values())),
            "annotations": len(read_jsonl(state / stage / "annotations.jsonl")),
            "selected": len(read_jsonl(state / stage / "selection.jsonl")),
            "candidates": len(read_jsonl(state / stage / "candidates.jsonl")),
            "pairs": len(read_jsonl(state / stage / "preferences.jsonl")),
        }
    return result


def parser() -> argparse.ArgumentParser:
    p = MachineArgumentParser(description=__doc__)
    p.add_argument("--state", default="runtime")
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init"); init.add_argument("--config", required=True)
    op = commands.add_parser("openings"); op.add_argument("stage", choices=["smoke", "measurement"]); op.add_argument("--limit", type=int)
    ro = commands.add_parser("rollout"); ro.add_argument("stage", choices=["smoke", "measurement"]); ro.add_argument("--endpoint", required=True); ro.add_argument("--model", required=True); ro.add_argument("--checkpoint-sha256", required=True); ro.add_argument("--max-turns", type=int, choices=[3, 8]); ro.add_argument("--concurrency", type=int, default=8)
    an = commands.add_parser("annotate"); an.add_argument("stage", choices=["smoke", "measurement"])
    ca = commands.add_parser("calibration"); ca.add_argument("stage", choices=["smoke", "measurement"]); ca.add_argument("--n", type=int, default=24)
    ad = commands.add_parser("adjudicate"); ad.add_argument("stage", choices=["smoke", "measurement"]); ad.add_argument("--decisions", required=True)
    re = commands.add_parser("report"); re.add_argument("stage", choices=["smoke", "measurement"])
    se = commands.add_parser("select"); se.add_argument("stage", choices=["measurement"])
    cn = commands.add_parser("candidates"); cn.add_argument("stage", choices=["measurement"]); cn.add_argument("--endpoint", required=True); cn.add_argument("--model", required=True); cn.add_argument("--checkpoint-sha256", required=True)
    ra = commands.add_parser("rank"); ra.add_argument("stage", choices=["measurement"])
    ex = commands.add_parser("export"); ex.add_argument("stage", choices=["measurement"])
    rs = commands.add_parser("resample"); rs.add_argument("stage", choices=["measurement"]); rs.add_argument("--targets", required=True); rs.add_argument("--max-fresh", type=int, default=32); rs.add_argument("--endpoint"); rs.add_argument("--model"); rs.add_argument("--checkpoint-sha256")
    rj = commands.add_parser("resample-judge"); rj.add_argument("stage", choices=["measurement"])
    rx = commands.add_parser("resample-export"); rx.add_argument("stage", choices=["measurement"])
    fo = commands.add_parser("forecast"); fo.add_argument("stage", choices=["smoke"]); fo.add_argument("--admit", type=int, choices=[35, 28, 21, 14])
    le = commands.add_parser("ledger")
    le.add_argument("action", nargs="?", default="show", choices=["gpu-start", "gpu-stop", "show"])
    le.add_argument("--pod-id"); le.add_argument("--price-usd-hr", type=float); le.add_argument("--eur-per-usd", type=float); le.add_argument("--other-eur", type=float, default=0)
    commands.add_parser("status")
    return p


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
    except CLIParseError as exc:
        summary("parse", {"error": str(exc)}, ok=False)
        return 2
    state = pathlib.Path(args.state)
    command = args.command
    try:
        if command == "init":
            result = manifest_module.initialize(state, args.config)
            output = {"seeds": len(result["seeds"]), "version": result["version"]}
        elif command == "openings":
            output = with_sol(lambda sol: openings_module.generate_openings(state, args.stage, sol, args.limit))
        elif command == "rollout":
            target = HTTPApertusClient(args.endpoint)
            output = with_sol(lambda sol: rollout_module.rollout(state, args.stage, target, sol, args.endpoint,
                                                                  args.model, args.checkpoint_sha256,
                                                                  args.max_turns, args.concurrency))
        elif command == "annotate":
            output = with_sol(lambda sol: annotation_module.annotate(state, args.stage, sol))
        elif command == "calibration":
            rows = annotation_module.calibration_sample(state, args.stage, args.n)
            output = {"sampled": len(rows), "path": str(state / args.stage / "calibration.jsonl")}
        elif command == "adjudicate":
            output = annotation_module.adjudicate(state, args.stage, args.decisions)
        elif command == "report":
            report = analyse.freeze_report(state, args.stage)
            output = {"trajectories": report["trajectory_count"], "turns": report["observed_turns"], "frozen": True}
        elif command == "select":
            output = selection_module.select(state, args.stage)
        elif command == "candidates":
            output = candidate_module.generate_candidates(state, args.stage, HTTPApertusClient(args.endpoint),
                                                          args.endpoint, args.model, args.checkpoint_sha256)
        elif command == "rank":
            output = with_sol(lambda sol: rank_module.rank_candidates(state, args.stage, sol))
        elif command == "export":
            output = export_pairs.export(state, args.stage)
        elif command == "resample":
            runtime = read_json(state / "runtime_config.json") if (state / "runtime_config.json").exists() else {}
            endpoint = args.endpoint or runtime.get("endpoint")
            model = args.model or runtime.get("requested_model")
            checkpoint_sha256 = args.checkpoint_sha256 or runtime.get("checkpoint_sha256")
            if not endpoint or not model or not checkpoint_sha256:
                raise ValueError("resample requires endpoint, model and checkpoint SHA-256 (arguments or runtime_config.json)")
            output = resample_module.sample_responses(
                state, args.stage, args.targets, args.max_fresh, HTTPApertusClient(endpoint),
                endpoint, model, checkpoint_sha256,
            )
        elif command == "resample-judge":
            output = with_sol(lambda sol: resample_module.judge_resamples(state, args.stage, sol))
        elif command == "resample-export":
            output = resample_module.export_resamples(state, args.stage)
        elif command == "forecast":
            output = forecast_module.forecast(state, args.stage, args.admit)
        elif command == "ledger":
            if args.action == "gpu-start":
                if not args.pod_id or args.price_usd_hr is None or args.eur_per_usd is None:
                    raise ValueError("gpu-start requires --pod-id --price-usd-hr --eur-per-usd")
                output = budget.gpu_start(state, args.pod_id, args.price_usd_hr, args.eur_per_usd)
            elif args.action == "gpu-stop":
                output = budget.gpu_stop(state, args.pod_id, args.other_eur)
            else:
                output = {**budget.gpu_summary(state), "calls": budget.CallLedger(state).counts()}
        elif command == "status":
            output = status(state)
        else:
            raise AssertionError(command)
        summary(command, output)
        return 0
    except Exception as exc:
        summary(command, {"error": str(exc)}, ok=False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
