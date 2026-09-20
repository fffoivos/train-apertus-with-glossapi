#!/usr/bin/env python3
"""Tri-state MATH-500 candidate scorer; never overwrites or hides reviews."""
import argparse
import collections
import json
from pathlib import Path

import equiv500_v3_candidate as E


parser = argparse.ArgumentParser()
parser.add_argument("--problems", required=True)
parser.add_argument("--responses", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
output = Path(args.output)
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")
bench = {row["id"]: row for row in map(json.loads, Path(args.problems).read_text().splitlines())}
responses = list(map(json.loads, Path(args.responses).read_text().splitlines()))
if len(responses) != 500 or len({row["id"] for row in responses}) != 500:
    raise SystemExit("expected exactly 500 unique response IDs")
if set(row["id"] for row in responses) != set(bench):
    raise SystemExit("response IDs do not exactly match benchmark IDs")

rows = []
counts = collections.Counter()
for response in responses:
    problem = bench[response["id"]]
    extraction = E.extract_result(response.get("response") or "")
    extracted = str(extraction["value"])
    options = E.option_map_from_problem(problem.get("problem_en", ""), problem.get("problem_el", ""))
    result = ({"decision": "review", "reason": extraction["reason"]}
              if extraction["status"] == "review"
              else E.equiv500_result(problem["answer"], extracted, options))
    counts[result["decision"]] += 1
    counts[result["reason"]] += 1
    rows.append({
        "id": response["id"], "answer": problem["answer"], "extracted": extracted,
        **result, "extraction": extraction, "level": problem["level"], "subject": problem["subject"],
        "truncated": response.get("finish_reason") == "length",
    })
summary = {
    "schema_version": "equiv500_v3_candidate_score_v1", "status": "candidate_tri_state",
    "n": len(rows), "pass": counts["pass"], "fail": counts["fail"],
    "review": counts["review"],
    "accuracy_all_rows_if_reviews_fail": round(counts["pass"] / len(rows), 4),
    "accuracy_decided_only": round(counts["pass"] / (counts["pass"] + counts["fail"]), 4) if counts["pass"] + counts["fail"] else None,
    "reason_counts": dict(sorted((key, value) for key, value in counts.items() if key not in {"pass", "fail", "review"})),
    "rows": rows,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, ensure_ascii=False))
