#!/usr/bin/env python3
"""Score a frozen response file with equiv500_v2 into a new output file."""
import argparse
import collections
import json
from pathlib import Path

import equiv500_v2 as E


parser = argparse.ArgumentParser()
parser.add_argument("--problems", required=True)
parser.add_argument("--responses", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--prediction-locale", required=True, choices=("el", "en"))
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
by_level = collections.defaultdict(lambda: [0, 0])
by_subject = collections.defaultdict(lambda: [0, 0])
for response in responses:
    problem = bench[response["id"]]
    extracted = E.extract(response.get("response") or "")
    passed = E.equiv500(problem["answer"], extracted, args.prediction_locale)
    by_level[problem["level"]][0] += passed
    by_level[problem["level"]][1] += 1
    by_subject[problem["subject"]][0] += passed
    by_subject[problem["subject"]][1] += 1
    rows.append({
        "id": response["id"], "level": problem["level"], "subject": problem["subject"],
        "answer": problem["answer"], "extracted": extracted, "equiv500_v2": bool(passed),
        "truncated": response.get("finish_reason") == "length",
    })

summary = {
    "schema_version": "equiv500_v2_score_v1", "n": len(rows),
    "prediction_locale": args.prediction_locale,
    "equiv500_v2_acc": round(sum(row["equiv500_v2"] for row in rows) / len(rows), 4),
    "truncated": sum(row["truncated"] for row in rows),
    "by_level": {str(k): round(v[0] / v[1], 4) for k, v in sorted(by_level.items())},
    "by_subject": {k: round(v[0] / v[1], 4) for k, v in sorted(by_subject.items())},
    "rows": rows,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False))
