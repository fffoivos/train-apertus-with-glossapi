#!/usr/bin/env python3
"""Audit candidate v3 against recorded frozen scores without rerunning parse_expr."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import equiv500_v3_candidate as candidate


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--additional-dir", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
project = Path(args.project)
output = Path(args.output)
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")

frozen_path = project / "data/benchmarks_el/math500/equiv500.py"
spec = importlib.util.spec_from_file_location("frozen_helpers", frozen_path)
frozen = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(frozen)
problems_path = project / "data/benchmarks_el/math500/problems_el_final.jsonl"
problems = {row["id"]: row for row in map(json.loads, problems_path.read_text().splitlines())}

response_paths = sorted((project / "results/peers_20260913").glob("bench_*/math500_*.jsonl"))
response_paths += sorted((project / "results/R3_single").glob("bench_*/math500_*.jsonl"))
response_paths += sorted(Path(args.additional_dir).glob("math500_*.jsonl"))
files = []
decisions = []

for path in response_paths:
    try:
        rel = str(path.relative_to(project))
    except ValueError:
        rel = str(path)
    score_path = path.with_name(path.stem + "_score.json")
    if not score_path.exists():
        raise SystemExit(f"missing recorded frozen score: {score_path}")
    responses = list(map(json.loads, path.read_text().splitlines()))
    score = json.loads(score_path.read_text())
    recorded = {row["id"]: bool(row["equiv500"]) for row in score["rows"]}
    ids = {row["id"] for row in responses}
    if len(responses) != 500 or len(ids) != 500 or ids != set(problems) or ids != set(recorded):
        raise SystemExit(f"identity/count gate failed: {path}")
    counts = {
        "rows": 500, "frozen_pass": sum(recorded.values()),
        "candidate_pass": 0, "candidate_fail": 0, "candidate_review": 0,
        "unsafe_fallback_reached": 0, "unsafe_fallback_recorded_pass": 0,
        "unsafe_fallback_recorded_pass_candidate_fail": 0,
        "ambiguous_numeric_review": 0, "unsupported_symbolic_review": 0,
        "empty_collapse_recorded_pass": 0,
        "empty_collapse_recorded_pass_candidate_fail": 0,
        "empty_collapse_recorded_pass_candidate_review": 0,
        "empty_collapse_recorded_pass_candidate_pass": 0,
        "explicit_answer_recorded_fail_candidate_pass": 0,
        "frozen_fail_candidate_pass": 0, "frozen_pass_candidate_fail": 0,
        "frozen_pass_candidate_review": 0, "frozen_fail_candidate_review": 0,
    }
    for response in responses:
        row_id = response["id"]
        ref = problems[row_id]["answer"]
        text = response.get("response") or ""
        old_extracted = frozen.extract(text)
        extraction = candidate.extract_result(text)
        extracted = str(extraction["value"])
        problem = problems[row_id]
        options = candidate.option_map_from_problem(problem.get("problem_en", ""), problem.get("problem_el", ""))
        result = ({"decision": "review", "reason": extraction["reason"]}
                  if extraction["status"] == "review"
                  else candidate.equiv500_result(ref, extracted, options))
        old_pass = recorded[row_id]
        counts["candidate_" + str(result["decision"])] += 1

        unsafe = False
        empty_collapse = False
        if ref and old_extracted:
            a, b = frozen.strip_string(ref), frozen.strip_string(old_extracted)
            empty_collapse = a == b == ""
            if a != b:
                ca, cb = frozen.categorical(ref), frozen.categorical(old_extracted)
                if ca is None and cb is None:
                    na, nb = frozen._nums(a), frozen._nums(b)
                    unsafe = not na and not nb
        counts["unsafe_fallback_reached"] += unsafe
        counts["unsafe_fallback_recorded_pass"] += unsafe and old_pass
        counts["unsafe_fallback_recorded_pass_candidate_fail"] += unsafe and old_pass and result["decision"] == "fail"
        counts["ambiguous_numeric_review"] += result["reason"] == "ambiguous_numeric_separator"
        counts["unsupported_symbolic_review"] += str(result["reason"]).startswith(("unsupported_symbolic", "safe_symbolic_error"))
        counts["empty_collapse_recorded_pass"] += empty_collapse and old_pass
        counts["empty_collapse_recorded_pass_candidate_fail"] += empty_collapse and old_pass and result["decision"] == "fail"
        counts["empty_collapse_recorded_pass_candidate_review"] += empty_collapse and old_pass and result["decision"] == "review"
        counts["empty_collapse_recorded_pass_candidate_pass"] += empty_collapse and old_pass and result["decision"] == "pass"
        explicit = old_extracted != extracted
        counts["explicit_answer_recorded_fail_candidate_pass"] += explicit and not old_pass and result["decision"] == "pass"
        counts["frozen_fail_candidate_pass"] += not old_pass and result["decision"] == "pass"
        counts["frozen_pass_candidate_fail"] += old_pass and result["decision"] == "fail"
        counts["frozen_pass_candidate_review"] += old_pass and result["decision"] == "review"
        counts["frozen_fail_candidate_review"] += not old_pass and result["decision"] == "review"
        if old_pass != (result["decision"] == "pass") or result["decision"] == "review" or unsafe:
            decisions.append({
                "file": rel, "id": row_id, "reference": ref,
                "frozen_extracted": old_extracted, "candidate_extracted": extracted,
                "frozen_recorded_pass": old_pass, "candidate": result,
                "extraction": extraction,
                "finish_reason": response.get("finish_reason"),
                "unsafe_frozen_parser_reached": unsafe,
                "empty_collapse": empty_collapse,
            })
    files.append({
        "path": rel, "sha256": sha256(path),
        "recorded_score_path": str(score_path), "recorded_score_sha256": sha256(score_path),
        **counts,
    })

sum_keys = [key for key in files[0] if key not in {"path", "sha256", "recorded_score_path", "recorded_score_sha256"}]
totals = {key: sum(row[key] for row in files) for key in sum_keys}
receipt = {
    "schema_version": "equiv500_v3_candidate_audit_v1",
    "status": "candidate_tri_state_not_pinned",
    "safety": "Recorded frozen row decisions are read from score ledgers. The audit never invokes frozen equiv500 or parse_expr on response text.",
    "frozen_scorer": {"path": str(frozen_path), "sha256": sha256(frozen_path)},
    "candidate_scorer": {"path": str(Path(candidate.__file__)), "sha256": sha256(Path(candidate.__file__))},
    "problems": {"path": str(problems_path), "sha256": sha256(problems_path), "rows": len(problems)},
    "scope": {"model_columns": 11, "language_cells": len(files), "rows": totals["rows"]},
    "totals": totals,
    "files": files,
    "decision_review_ledger": decisions,
    "publication_gate": "Do not replace historical scores or compare adjusted values until candidate review states are resolved and one digest is pinned for all cells.",
}
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"scope": receipt["scope"], "totals": totals, "ledger_rows": len(decisions)}, ensure_ascii=False, indent=2))
