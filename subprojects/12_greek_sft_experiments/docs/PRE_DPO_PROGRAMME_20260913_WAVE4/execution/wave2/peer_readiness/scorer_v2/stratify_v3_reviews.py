#!/usr/bin/env python3
"""Structural stratification of v3 review states; no semantic scoring."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


def ref_form(ref: str) -> str:
    compact = ref.replace(" ", "")
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", compact): return "scalar_numeric"
    if "\\begin{pmatrix}" in ref: return "matrix_or_vector"
    if "\\in" in ref or "infty" in ref: return "interval_or_set"
    if "\\pm" in ref: return "plus_minus_set"
    if "\\frac" in ref: return "fraction"
    if "\\sqrt" in ref: return "radical"
    if "\\text" in ref or "\\mbox" in ref: return "categorical_text"
    if re.search(r"[A-Za-z]", ref): return "algebraic_symbolic"
    if "," in ref: return "tuple_or_list"
    return "other"


def surface_bucket(row: dict) -> str:
    reason = row["candidate"]["reason"]
    if reason == "ambiguous_numeric_separator": return "ambiguous_separator"
    if reason == "competing_final_constructions": return "conflicting_final_constructions"
    value = row["candidate_extracted"].strip()
    if row.get("finish_reason") == "length" and (len(value) > 128 or re.search(r"(?:[=+\-*/^]|\\frac|\\sqrt)\s*$", value)):
        return "likely_no_complete_answer_truncated"
    if value in {"", "$$", "\\[", "\\]", "\\(", "\\)"} or re.search(r"(?:[=+\-*/^]|\\frac|\\sqrt)\s*$", value):
        return "likely_no_complete_answer_malformed"
    if len(value) > 256:
        return "long_surface_needs_bounded_tail_extraction"
    without_commands = re.sub(r"\\[A-Za-z]+", "", value)
    prose_words = re.findall(r"[A-Za-zΑ-Ωα-ωά-ώϊϋΐΰ]{3,}", without_commands)
    has_math_token = bool(re.search(r"\d|\\frac|\\sqrt|\\pi|[+\-*/^=(),\[\]{}]", value))
    if not prose_words and has_math_token:
        return "likely_extractable_compact_math"
    if prose_words and has_math_token:
        return "likely_extractable_tail_answer_in_prose"
    return "likely_no_closed_answer_prose"


parser = argparse.ArgumentParser()
parser.add_argument("--audit", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
output = Path(args.output)
if output.exists(): raise SystemExit(f"refusing to overwrite {output}")
audit_path = Path(args.audit)
audit = json.loads(audit_path.read_text())
reviews = [row for row in audit["decision_review_ledger"] if row["candidate"]["decision"] == "review"]
reason_counts = collections.Counter()
form_counts = collections.Counter()
surface_counts = collections.Counter()
cross = collections.Counter()
rows = []
for row in reviews:
    reason = row["candidate"]["reason"]
    form = ref_form(row["reference"])
    surface = surface_bucket(row)
    reason_counts[reason] += 1; form_counts[form] += 1; surface_counts[surface] += 1; cross[(form, surface)] += 1
    rows.append({"file": row["file"], "id": row["id"], "reason": reason, "reference_form": form, "surface_bucket": surface, "finish_reason": row.get("finish_reason")})
receipt = {
    "schema_version": "equiv500_v3_review_stratification_v1", "status": "structural_not_semantic",
    "audit": {"path": str(audit_path), "sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest()},
    "review_rows": len(reviews),
    "by_parser_reason": dict(reason_counts.most_common()),
    "by_reference_form": dict(form_counts.most_common()),
    "by_surface_bucket": dict(surface_counts.most_common()),
    "top_reference_form_surface_cells": [{"reference_form": key[0], "surface_bucket": key[1], "rows": value} for key, value in cross.most_common(30)],
    "bounded_route": [
        {"priority": 1, "scope": "runner metadata and math delimiters", "action": "Keep exact suffix removal and delimiter/boxed extraction regressions; these are source-independent rendering artifacts."},
        {"priority": 2, "scope": "scalar, fraction, radical and polynomial references", "action": "Add only observed closed tokens to the bounded grammar, with positive, collision and complexity tests."},
        {"priority": 3, "scope": "terminal answer-bearing prose", "action": "Add anchored English/Greek tail rules and audit every newly changed decision; do not use a generic last-number rule."},
        {"priority": 4, "scope": "matrix, vector, interval, tuple and plus-minus references", "action": "Use dedicated structural normalizers keyed to reference form; keep unordered/ordered semantics explicit."},
        {"priority": 5, "scope": "no closed answer or incomplete truncation", "action": "Count as deterministic extraction failure (zero) and report separately from mathematical inequivalence."},
        {"priority": 6, "scope": "ambiguous separators and conflicting final constructions", "action": "Keep abstention plus blinded context adjudication; never choose the interpretation that matches the reference."},
    ],
    "rows": rows,
}
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: receipt[key] for key in ["review_rows", "by_parser_reason", "by_reference_form", "by_surface_bucket"]}, ensure_ascii=False, indent=2))
