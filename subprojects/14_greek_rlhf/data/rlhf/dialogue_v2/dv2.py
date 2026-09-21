#!/usr/bin/env python3
"""Dialogue v2 development CLI (Workstream B). Every command prints one DV2_OK/DV2_FAIL line.

Commands:
  baseline                          Stage A baseline.json + run_manifest.json
  openings                          D1 openings from person-and-story seeds (one Sol call; cached on rerun)
  seeds-check                       validate D1/D2 seed packets and the troubleshooting worlds
  dry-run [--cases ...] [--turns 2] real Sol user/world/learner calls against stand-in replies (runtime/dryrun only)
  forecast --price-cap 1.99 [--freeze]
  gate --stage collect|branch       frozen forecast + ledger checks before provisioning (used by pod/run_stage.sh)
  ledger gpu-start|gpu-stop|show    programme GPU ledger (development_demo tag)
  preflight --endpoint URL          served model id check (records runtime_config.json)
  collect --endpoint URL            D1+D2 raw trajectories (GPU session)
  evaluate [--cases ...]            prefix-local turn evaluations, then conversation reviews
  points                            possible sampling points (D1+D2) and D1 selection
  branch-sample --endpoint URL      8 candidates per selected D1 point (GPU session)
  branch-judge                      escalating 4-then-8 ranking, verification and pair export
  report                            review HTML under review/
  status
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from common import RGD_RUNTIME, V2_RUNTIME, atomic_json, read_json, read_jsonl, utcnow  # noqa: E402
from contracts import MODEL_ID, MODEL_REVISION, MODEL_SHA256, SAMPLING, component_versions  # noqa: E402

ALL_CASES = ["DVI001", "DVI002", "DVI003", "DVI004", "RGD001", "RGD002", "RGD003", "RGD004", "RGD005", "RGD006"]


def case_set(args) -> tuple[dict[str, Any], list[str]]:
    """--set v2 (the first ten development cases) or --set c60 (60-dialogue collection, amended protocol)."""
    import seeds as seeds_module
    if getattr(args, "set", "v2") == "c60":
        seeds = seeds_module.load_c60()
        return seeds, (getattr(args, "cases", None) or sorted(seeds))
    return seeds_module.load_all(), (getattr(args, "cases", None) or ALL_CASES)


def emit(command: str, values: dict[str, Any], ok: bool = True) -> None:
    print(("DV2_OK " if ok else "DV2_FAIL ") + command + " " + json.dumps(values, ensure_ascii=False, sort_keys=True, default=str))


def with_sol(fn):
    from clients import CodexSolClient
    sol = CodexSolClient()
    sol.start()
    try:
        return fn(sol)
    finally:
        sol.close()


def cmd_dry_run(args) -> dict[str, Any]:
    import rollout
    import seeds as seeds_module
    from clients import FakeTargetClient, TargetResult
    from dryrun_replies import REPLIES
    from glossary import Glossary
    seeds = seeds_module.load_all()

    def responder(messages):
        case = next(cid for cid, s in seeds.items() if s["opening"] == messages[0]["content"])
        turn = sum(m["role"] == "assistant" for m in messages)
        text = REPLIES[case][min(turn, len(REPLIES[case]) - 1)]
        return TargetResult(text, "stop", "dry-run-stand-in", {"prompt_tokens": 0, "completion_tokens": 0}, 0.0)

    out_dir = V2_RUNTIME / "dryrun"
    def run(sol):
        ctx = rollout.Context(FakeTargetClient(responder, [MODEL_ID]), sol, Glossary.load(), "dry-run",
                              dry_run=True, runtime_override=out_dir, horizon=args.turns)
        started = time.monotonic()
        result = rollout.collect(ctx, seeds, args.cases or ALL_CASES)
        return {"results": result, "wall_seconds": round(time.monotonic() - started, 1), "out": str(out_dir)}
    return with_sol(run)


def cmd_collect(args) -> dict[str, Any]:
    import rollout
    import seeds as seeds_module
    from clients import HTTPApertusClient
    from glossary import Glossary
    seeds, cases = case_set(args)
    runtime_config = V2_RUNTIME / "runtime_config.json"
    if not runtime_config.exists():
        raise SystemExit("run preflight first")
    def run(sol):
        ctx = rollout.Context(HTTPApertusClient(args.endpoint), sol, Glossary.load(), args.endpoint,
                              model=args.model, checkpoint_sha256=args.checkpoint_sha256)
        started = time.monotonic()
        result = rollout.collect(ctx, seeds, cases, max_workers=24 if args.set == "c60" else 10)
        return {"results": result, "wall_seconds": round(time.monotonic() - started, 1)}
    return with_sol(run)


def cmd_preflight(args) -> dict[str, Any]:
    from clients import HTTPApertusClient
    ids = HTTPApertusClient(args.endpoint, timeout=30).models()
    if args.model not in ids:
        raise SystemExit(f"served models {ids} do not include {args.model}")
    config = {"endpoint": args.endpoint, "requested_model": args.model, "served_models": ids,
              "model_revision": MODEL_REVISION, "checkpoint_sha256": args.checkpoint_sha256,
              "sha_verified_on_pod_by": "dv2_pod_setup.sh (DV2_MODEL_SHA_OK before serving)", "sampling": SAMPLING,
              "no_system_prompt": True, "recorded_utc": utcnow(), "stage": args.stage}
    atomic_json(V2_RUNTIME / f"runtime_config_{args.stage}.json", config)
    if args.stage == "collect":
        atomic_json(V2_RUNTIME / "runtime_config.json", config)
    return {"served_models": ids}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline")
    sub.add_parser("openings")
    sub.add_parser("seeds-check")
    d = sub.add_parser("dry-run"); d.add_argument("--cases", nargs="*"); d.add_argument("--turns", type=int, default=2)
    f = sub.add_parser("forecast"); f.add_argument("--price-cap", type=float, default=1.99); f.add_argument("--freeze", action="store_true")
    f.add_argument("--branch-completions", type=int)
    f.add_argument("--set", choices=["v2", "c60"], default="v2")
    g = sub.add_parser("gate"); g.add_argument("--stage", choices=["collect", "branch"], required=True)
    le = sub.add_parser("ledger"); le.add_argument("action", choices=["gpu-start", "gpu-stop", "show"])
    le.add_argument("--pod-id"); le.add_argument("--stage", choices=["collect", "branch"]); le.add_argument("--price-usd-hr", type=float)
    le.add_argument("--post-utc"); le.add_argument("--max-session-minutes", type=float); le.add_argument("--teardown-record")
    for name in ("preflight", "collect", "branch-sample"):
        c = sub.add_parser(name); c.add_argument("--set", choices=["v2", "c60"], default="v2")
        c.add_argument("--endpoint", required=True); c.add_argument("--model", default=MODEL_ID)
        c.add_argument("--checkpoint-sha256", default=MODEL_SHA256); c.add_argument("--cases", nargs="*")
        if name == "preflight":
            c.add_argument("--stage", choices=["collect", "branch"], default="collect")
    e = sub.add_parser("evaluate"); e.add_argument("--cases", nargs="*"); e.add_argument("--set", choices=["v2", "c60"], default="v2")
    pt = sub.add_parser("points"); pt.add_argument("--set", choices=["v2", "c60"], default="v2")
    bj = sub.add_parser("branch-judge"); bj.add_argument("--set", choices=["v2", "c60"], default="v2")
    bs = sub.choices["branch-sample"]; bs.add_argument("--topup-points", nargs="*")
    bs.add_argument("--candidates", type=int, help="replies per point, overriding the stored plan (32-reply run)")
    sub.add_parser("report")
    sub.add_parser("status")
    args = p.parse_args(argv)
    try:
        if args.command == "baseline":
            import baseline
            b = baseline.build_baseline(); m = baseline.build_run_manifest()
            out = {"me021_terminal": b["me021"]["terminal_code"], "cases": len(m["cases"])}
        elif args.command == "openings":
            import openings
            from glossary import Glossary
            out = with_sol(lambda sol: openings.write_openings(sol, Glossary.load()))
        elif args.command == "seeds-check":
            import seeds as seeds_module
            import worlds
            all_seeds = seeds_module.load_all()
            problems = {cid: worlds.validate_world(s["world"]) for cid, s in all_seeds.items() if s.get("world")}
            if any(problems.values()):
                raise SystemExit(f"world tables incomplete: {problems}")
            out = {"seeds": sorted(all_seeds), "worlds_ok": sorted(problems)}
        elif args.command == "dry-run":
            out = cmd_dry_run(args)
        elif args.command == "forecast":
            import forecast
            value = forecast.build(args.price_cap, case_set=args.set, branch_completions_override=getattr(args, "branch_completions", None))
            if args.freeze:
                forecast.freeze(value)
            out = {k: value[k] for k in ("session1_upper_eur", "session2_upper_eur", "total_upper_eur",
                                         "remaining_before_operational_stop_eur", "admission_status", "shortfall_eur")}
        elif args.command == "gate":
            import forecast
            out = forecast.verify_frozen(args.stage)
        elif args.command == "ledger":
            import ledger
            if args.action == "gpu-start":
                out = ledger.gpu_start(args.pod_id, args.stage, args.price_usd_hr, args.post_utc, args.max_session_minutes)
            elif args.action == "gpu-stop":
                created = terminated = None
                if args.teardown_record and pathlib.Path(args.teardown_record).exists():
                    rows = [r for r in read_jsonl(args.teardown_record) if r.get("pod_id") == args.pod_id]
                    if rows:
                        rec = rows[-1].get("record") or {}
                        created, terminated = rec.get("createdAt"), rec.get("terminatedAt")
                out = ledger.gpu_stop(args.pod_id, created, terminated)
            else:
                out = ledger.programme_summary()
        elif args.command == "preflight":
            out = cmd_preflight(args)
        elif args.command == "collect":
            out = cmd_collect(args)
        elif args.command == "evaluate":
            import evaluate
            import rollout
            import seeds as seeds_module
            from clients import FakeTargetClient
            from glossary import Glossary
            seeds, cases = case_set(args)
            def run(sol):
                ctx = rollout.Context(FakeTargetClient(lambda m: RuntimeError("no target in evaluation")), sol,
                                      Glossary.load(), "none")
                if args.set == "c60":                  # amendment: one combined review per conversation
                    return {"combined_reviews": evaluate.review_combined(ctx, seeds, cases)}
                turns = evaluate.evaluate_turns(ctx, seeds, cases)
                reviews = evaluate.review_conversations(ctx, seeds, cases)
                return {"turn_evaluations": turns, "reviews": reviews}
            out = with_sol(run)
        elif args.command == "points":
            import points
            import seeds as seeds_module
            from common import runtime_dir_for
            seeds, cases = case_set(args)
            out = (points.write_points_c60(seeds, cases, runtime_dir_for) if args.set == "c60"
                   else points.write_points(seeds, ALL_CASES, runtime_dir_for))
        elif args.command == "branch-sample":
            import branch
            import rollout
            from clients import HTTPApertusClient
            from glossary import Glossary
            ctx = rollout.Context(HTTPApertusClient(args.endpoint), None, Glossary.load(), args.endpoint,
                                  model=args.model, checkpoint_sha256=args.checkpoint_sha256)
            if args.set == "c60":
                _, cases = case_set(args)
                out = branch.sample_candidates(ctx, cases, topup_point_ids=set(args.topup_points or []),
                                               candidates_override=getattr(args, "candidates", None))
            else:
                out = branch.sample_candidates(ctx, [c for c in (args.cases or ALL_CASES) if c.startswith("DVI")])
        elif args.command == "branch-judge":
            import branch
            import rollout
            import seeds as seeds_module
            from clients import FakeTargetClient
            from glossary import Glossary
            seeds, cases = case_set(args)
            def run(sol):
                ctx = rollout.Context(FakeTargetClient(lambda m: RuntimeError("no target")), sol, Glossary.load(), "none")
                if args.set == "c60":
                    return branch.judge_points_c60(ctx, seeds, cases)
                return branch.judge_points(ctx, seeds, [c for c in ALL_CASES if c.startswith("DVI")])
            out = with_sol(run)
        elif args.command == "report":
            import report
            out = report.build()
        elif args.command == "status":
            import ledger
            out = {"programme": ledger.programme_summary(),
                   "dvi_calls": ledger.CallLedger(V2_RUNTIME, "dvi").counts(),
                   "rgd_calls": ledger.CallLedger(RGD_RUNTIME, "rgd").counts(),
                   "versions": component_versions()}
        else:
            raise AssertionError(args.command)
        emit(args.command, out)
        return 0
    except SystemExit as exc:
        emit(args.command, {"error": str(exc)}, ok=False)
        return 2
    except Exception as exc:  # noqa: BLE001
        emit(args.command, {"error": f"{type(exc).__name__}: {exc}"}, ok=False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
