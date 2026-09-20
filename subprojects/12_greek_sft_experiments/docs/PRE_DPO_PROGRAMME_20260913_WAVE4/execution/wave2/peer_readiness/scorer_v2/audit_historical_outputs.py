#!/usr/bin/env python3
"""Compare the frozen equiv500 scorer with v2 over exact historical outputs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import equiv500_v2 as v2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--additional-dir")
args = parser.parse_args()
project = Path(args.project)
output = Path(args.output)
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")

frozen_path = project / "data/benchmarks_el/math500/equiv500.py"
spec = importlib.util.spec_from_file_location("equiv500_frozen", frozen_path)
frozen = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(frozen)
problems_path = project / "data/benchmarks_el/math500/problems_el_final.jsonl"
problems = {row["id"]: row for row in map(json.loads, problems_path.read_text().splitlines())}

response_paths = sorted((project / "results/peers_20260913").glob("bench_*/math500_*.jsonl"))
response_paths += sorted((project / "results/R3_single").glob("bench_*/math500_*.jsonl"))
if args.additional_dir:
    response_paths += sorted(Path(args.additional_dir).glob("math500_*.jsonl"))
files = []
examples = {"empty_collapse_old_only": [], "final_phrase_recovered": [], "separator_old_only": []}
changed_decisions = []

for path in response_paths:
    try:
        rel = str(path.relative_to(project))
    except ValueError:
        rel = str(path)
    locale = "el" if path.name == "math500_el.jsonl" else "en"
    rows = list(map(json.loads, path.read_text().splitlines()))
    if len(rows) != 500 or len({row["id"] for row in rows}) != 500 or set(row["id"] for row in rows) != set(problems):
        raise SystemExit(f"identity/count gate failed: {path}")
    counts = {
        "old_pass": 0, "v2_pass": 0, "old_only": 0, "v2_only": 0,
        "empty_collapse_old_true": 0, "empty_collapse_old_only": 0,
        "final_phrase_extraction_changed": 0, "final_phrase_recovered": 0,
        "separator_locale_sensitive": 0, "separator_old_only": 0,
    }
    for row in rows:
        ref = problems[row["id"]]["answer"]
        response = row.get("response") or ""
        old_extracted = frozen.extract(response)
        new_extracted = v2.extract(response)
        old_pass = bool(frozen.equiv500(ref, old_extracted))
        new_pass = bool(v2.equiv500(ref, new_extracted, locale))
        counts["old_pass"] += old_pass
        counts["v2_pass"] += new_pass
        counts["old_only"] += old_pass and not new_pass
        counts["v2_only"] += new_pass and not old_pass
        empty = bool(ref and old_extracted and frozen.strip_string(ref) == "" and frozen.strip_string(old_extracted) == "")
        counts["empty_collapse_old_true"] += empty and old_pass
        counts["empty_collapse_old_only"] += empty and old_pass and not new_pass
        if empty and old_pass and not new_pass and len(examples["empty_collapse_old_only"]) < 12:
            examples["empty_collapse_old_only"].append({
                "file": rel, "id": row["id"], "reference": ref,
                "old_extracted": old_extracted, "v2_extracted": new_extracted,
            })
        final_phrase = bool(re.search(r"(?i)(?:the\s+final\s+answer\s+is|η\s+τελική\s+απάντηση\s+είναι)\s*:", response))
        counts["final_phrase_extraction_changed"] += final_phrase and old_extracted != new_extracted
        counts["final_phrase_recovered"] += final_phrase and new_pass and not old_pass
        if final_phrase and new_pass and not old_pass and len(examples["final_phrase_recovered"]) < 12:
            examples["final_phrase_recovered"].append({
                "file": rel, "id": row["id"], "reference": ref,
                "old_extracted": old_extracted, "v2_extracted": new_extracted,
            })
        # A result is locale-sensitive when the same answer token has the opposite
        # truth value under the other locale. This flags the old scorer's two-reading
        # acceptance surface without asserting which locale is semantically intended.
        alternate = "en" if locale == "el" else "el"
        sensitive = False
        if re.fullmatch(r"-?\d{1,3}[.,]\d{3}", v2.strip_string(new_extracted)):
            alt_pass = bool(v2.equiv500(ref, new_extracted, alternate))
            sensitive = new_pass != alt_pass
            counts["separator_locale_sensitive"] += sensitive
            counts["separator_old_only"] += sensitive and old_pass and not new_pass
            if sensitive and old_pass and not new_pass and len(examples["separator_old_only"]) < 12:
                examples["separator_old_only"].append({
                    "file": rel, "id": row["id"], "reference": ref,
                    "extracted": new_extracted, "declared_locale": locale,
                })
        if old_pass != new_pass:
            changed_decisions.append({
                "file": rel, "id": row["id"], "locale": locale,
                "reference": ref, "frozen_extracted": old_extracted,
                "candidate_extracted": new_extracted, "frozen_pass": old_pass,
                "candidate_pass": new_pass,
                "flags": {
                    "empty_collapse": empty, "explicit_final_phrase": final_phrase,
                    "separator_locale_sensitive": sensitive,
                },
            })
    files.append({
        "path": rel, "sha256": sha256(path), "rows": len(rows), "locale": locale,
        **counts, "old_accuracy": counts["old_pass"] / 500,
        "v2_candidate_accuracy": counts["v2_pass"] / 500,
    })

totals = {key: sum(item[key] for item in files) for key in (
    "rows", "old_pass", "v2_pass", "old_only", "v2_only",
    "empty_collapse_old_true", "empty_collapse_old_only",
    "final_phrase_extraction_changed", "final_phrase_recovered",
    "separator_locale_sensitive", "separator_old_only",
)}
receipt = {
    "schema_version": "equiv500_v2_historical_audit_v1",
    "status": "candidate_only_not_comparable_adjusted_scores",
    "frozen_scorer": {"path": str(frozen_path), "sha256": sha256(frozen_path)},
    "candidate_scorer": {"path": str(Path(v2.__file__)), "sha256": sha256(Path(v2.__file__))},
    "problems": {"path": str(problems_path), "sha256": sha256(problems_path), "rows": len(problems)},
    "scope": {
        "response_files": len(files), "rows": totals["rows"],
        "additional_dir": args.additional_dir,
    },
    "totals": totals,
    "files": files,
    "changed_decisions": changed_decisions,
    "examples": examples,
    "interpretation_gate": (
        "Historical scores are preserved. Candidate scores must not be compared across models "
        "until every selected model, including Krikri v1.5, is rescored from the same frozen responses."
    ),
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"scope": receipt["scope"], "totals": totals}, ensure_ascii=False, indent=2))
