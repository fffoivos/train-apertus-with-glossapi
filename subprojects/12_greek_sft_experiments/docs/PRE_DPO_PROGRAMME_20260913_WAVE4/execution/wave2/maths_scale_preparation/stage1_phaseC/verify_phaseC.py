#!/usr/bin/env python3
"""Verify Phase C lineage, exclusions, queue dependencies, assets, and simple references."""

from __future__ import annotations

import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
STAGE1 = BASE / "stage1"
MATH = Path("/Users/foivoskarounos-zamparloukos/sft_annot/math_src/math_train.jsonl")
SPLITS = BASE / "proposed_family_splits.jsonl"
INVENTORY = BASE / "math7500_family_inventory.jsonl"
QUARANTINE = BASE.parent / "candidate_register/family_resolution/dispositions.jsonl"
DIAGRAM = re.compile(r"(?i)\\begin\{asy\}|\[asy\]|\b(?:diagram|figure|pictured|shown below|as shown)\b")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True))


manifest = json.loads((ROOT / "manifest.json").read_text())
inputs = read_jsonl(ROOT / "inputs.jsonl")
queue = read_jsonl(ROOT / "queue.jsonl")
bindings = read_jsonl(ROOT / "payload_bindings.jsonl")
deltas = read_jsonl(ROOT / "replacement_delta.jsonl")
source_reads = read_jsonl(ROOT / "source_read_receipt.jsonl")
partition = json.loads((ROOT / "partition_receipt.json").read_text())
conditional = json.loads((ROOT / "conditional_jobs.json").read_text())
splits = read_jsonl(SPLITS)
inventory = read_jsonl(INVENTORY)
inventory_by_id = {row["family_id"]: row for row in inventory}
math_rows = read_jsonl(MATH)
phase_b_delta = read_jsonl(STAGE1 / "phaseB_selection_delta.jsonl")
quarantine = read_jsonl(QUARANTINE)

checks = {}
checks["manifest_artifact_hashes"] = all(sha_file(ROOT / name) == digest for name, digest in manifest["artifact_sha256"].items())

asset_names = [
    "run_queue.py", "prompts/adaptation.txt", "prompts/solution_blind.txt", "prompts/verification_blind.txt",
    "prompts/greek_correction.txt", "prompts/source_review.txt", "schemas/adaptation.schema.json",
    "schemas/solution.schema.json", "schemas/greek_correction.schema.json", "schemas/source_review.schema.json",
]
checks["stage1_assets_byte_identical"] = all(sha_file(ROOT / name) == sha_file(STAGE1 / name) for name in asset_names)
checks["runner_known_proven_digest"] = sha_file(ROOT / "run_queue.py") == "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"

checks["fourteen_unique_train_rows"] = (
    len(inputs) == len({row["row_id"] for row in inputs}) == len({row["family_id"] for row in inputs}) == 14
    and all(row["source_split"] == "MATH train" for row in inputs)
)
checks["source_line_record_and_family_bindings"] = all(
    row["source_record_sha256"] == record_sha(math_rows[row["source_line"] - 1])
    and row["problem_en"] == math_rows[row["source_line"] - 1]["problem"]
    and row["reference_solution"] == math_rows[row["source_line"] - 1]["solution"]
    and row["family_sha256"] == inventory_by_id[row["family_id"]]["family_sha256"]
    and row["source_line"] == inventory_by_id[row["family_id"]]["canonical_source_line"]
    and row["source_record_sha256"] in inventory_by_id[row["family_id"]]["source_record_sha256s"]
    for row in inputs
)

phase_c_original = [row for row in splits if row["execution_phase"] == "C_complete_stage1"]
original_ids = {row["family_id"] for row in phase_c_original}
selected_ids = {row["family_id"] for row in inputs}
replacement_ids = {row["new"]["family_id"] for row in deltas}
unchanged_ids = selected_ids - replacement_ids
checks["twelve_original_plus_two_replacements"] = len(phase_c_original) == 14 and len(unchanged_ids) == 12 and len(replacement_ids) == 2 and unchanged_ids <= original_ids
checks["replacement_lines_exact"] = {(row["old"]["source_line"], row["new"]["source_line"]) for row in deltas} == {(63, 627), (2670, 2758)}
checks["replacement_same_subject_level"] = all(row["old"]["subject"] == row["new"]["subject"] and row["old"]["level"] == row["new"]["level"] for row in deltas)

reserved = {row["family_id"] for row in splits}
phase_b_replacements = {row["new"]["family_id"] for row in phase_b_delta}
math5_77_family = {
    row["family_id"] for row in quarantine
    if row.get("row_id") == "repair_math5_77" and row.get("disposition") == "quarantine_frozen_math500_overlap_gate"
}
checks["replacement_disjoint_all_reserved"] = not (replacement_ids & reserved)
checks["replacement_disjoint_phaseB_replacements"] = not (replacement_ids & phase_b_replacements)
checks["math5_77_quarantine_preserved"] = math5_77_family == {"mathfam_f91a56318d28452a3d95"} and not (selected_ids & math5_77_family)
checks["all_selected_exposure_and_contamination_gates"] = all(
    not row["metadata_conflict"]
    and not row["prior_pilot_memberships"]
    and not row["cut2_candidate_ids"]
    and not row["math500_overlap"]["reject"]
    and not row["current_assembly_exposure"]["appeared_in_gradient_train"]
    and not row["current_assembly_exposure"]["appeared_in_development"]
    and not row["current_assembly_exposure"]["assembly_excluded_rows"]
    for row in inputs
)
checks["all_selected_problem_text_is_self_contained_by_gate"] = all(not DIAGRAM.search(row["problem_en"]) and not row["diagram_or_figure_dependency"] for row in inputs)

checks["queue_has_42_unique_jobs"] = len(queue) == len({row["job_id"] for row in queue}) == 42
checks["queue_stage_counts"] = all(sum(row["stage"] == stage for row in queue) == 14 for stage in ("adaptation", "solution_high", "verification_blind_high"))
checks["queue_high_only_no_automatic_xhigh"] = all(row["effort"] == "high" for row in queue) and "xhigh" not in (ROOT / "queue.jsonl").read_text()
checks["independent_solve_verify_dependencies"] = all(
    row["depends_on"] == ["adapt__" + row["row_id"]]
    for row in queue if row["stage"] in {"solution_high", "verification_blind_high"}
)
checks["references_absent_from_payloads"] = all("reference" not in json.dumps(row["payload"], ensure_ascii=False).lower() for row in queue)
checks["payload_bindings_complete"] = len(bindings) == 42 and {row["job_id"] for row in bindings} == {row["job_id"] for row in queue} and all(not row["reference_solution_in_payload"] for row in bindings)

checks["source_read_all14_bound"] = (
    len(source_reads) == 14
    and {row["row_id"] for row in source_reads} == {row["row_id"] for row in inputs}
    and all(not row["obvious_ambiguity"] and row["source_reference_consistent"] for row in source_reads)
)
checks["development_final_preserved_without_content"] = (
    partition["development_count"] == 14
    and partition["final_confirmation_count"] == 14
    and not partition["development_or_final_content_materialized"]
    and not partition["development_or_final_identity_in_inputs"]
)
checks["call_envelope"] = (
    manifest["counts"]["primary_calls"] == 42
    and manifest["counts"]["conditional_greek_correction_cap"] == 14
    and manifest["counts"]["conditional_semantic_or_source_shared_cap"] == 8
    and manifest["counts"]["retry_cap"] == 8
    and manifest["counts"]["absolute_call_cap"] == 72
    and conditional["absolute_call_cap"] == 72
    and not conditional["semantic_or_source_repair_shared_pool"]["automatic_xhigh_selection"]
)
checks["prepared_not_launched"] = manifest["status"] == "prepared_unlaunched_root_review_required" and not manifest["execution"]["launched"]

# Simple executable checks of every selected reference result; no generated code is run.
math_checks = {
    "line_1202": Fraction(25 * 6, 15) == 10,
    "line_627": next(n for n in range(1, 100) if n * (n + 1) // 2 > 10 * n) == 20,
    "line_3416": sum((-n if n % 2 else n) for n in range(1, 10001)) == 5000,
    "line_4273": Fraction(10, 10) == 1,
    "line_6052": 1**(3**42) + 0**(2**42) + (-1) * ((-1) ** 42) == 0,
    "line_6668": Fraction(3 * 2, 36) == Fraction(1, 6),
    "line_2758": Fraction(110, 6 + 7 + 9) * 9 == 45,
    "line_3264": abs(math.cos(math.radians(135)) + math.sqrt(2) / 2) < 1e-12,
    "line_5094": 2 * 3 * 5 == 30,
    "line_5074": math.gcd(math.gcd(9118, 12173), 33182) == 47,
    "line_2042": Fraction(1, 6) ** 3 == Fraction(1, 216),
    "line_2462": [11**n for n in range(6) if str(11**n) != str(11**n)[::-1]] == [161051],
    "line_7065": 3**2 + 7**2 + 1**2 == 59,
    "line_7319": Fraction(105, 135) == Fraction(7, 9),
}
checks["all14_simple_reference_checks"] = all(math_checks.values()) and len(math_checks) == 14

result = {
    "verified_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).astimezone().isoformat(timespec="seconds"),
    "ok": all(checks.values()),
    "checks": checks,
    "mathematical_checks": math_checks,
    "selected_family_ids": sorted(selected_ids),
    "replacement_family_ids": sorted(replacement_ids),
    "explicit_quarantine_family_ids": sorted(math5_77_family),
}
(ROOT / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
raise SystemExit(0 if result["ok"] else 1)
