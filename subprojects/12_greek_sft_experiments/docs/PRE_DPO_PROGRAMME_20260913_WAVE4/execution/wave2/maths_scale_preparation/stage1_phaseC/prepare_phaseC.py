#!/usr/bin/env python3
"""Freeze the unlaunched, train-only Phase C competition-maths queue."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
STAGE1 = BASE / "stage1"
MATH = Path("/Users/foivoskarounos-zamparloukos/sft_annot/math_src/math_train.jsonl")
SPLITS = BASE / "proposed_family_splits.jsonl"
INVENTORY = BASE / "math7500_family_inventory.jsonl"
PHASE_B_DELTA = STAGE1 / "phaseB_selection_delta.jsonl"
QUARANTINE = BASE.parent / "candidate_register/family_resolution/dispositions.jsonl"
SELECTION_SEED = "phaseC-replacement-v1"
REQUIRED_REPLACEMENT_LINES = {63, 2670}
DIAGRAM = re.compile(r"(?i)\\begin\{asy\}|\[asy\]|\b(?:diagram|figure|pictured|shown below|as shown)\b")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def record_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True))


split_rows = read_jsonl(SPLITS)
inventory = read_jsonl(INVENTORY)
inventory_by_id = {row["family_id"]: row for row in inventory}
math_rows = read_jsonl(MATH)
phase_b_delta = read_jsonl(PHASE_B_DELTA)
quarantine_rows = read_jsonl(QUARANTINE)

phase_c_original = [row for row in split_rows if row["execution_phase"] == "C_complete_stage1"]
assert len(phase_c_original) == 14
assert {row["source_line"] for row in phase_c_original if DIAGRAM.search(math_rows[row["source_line"] - 1]["problem"])} == REQUIRED_REPLACEMENT_LINES

reserved_families = {row["family_id"] for row in split_rows}
phase_b_replacements = {row["new"]["family_id"] for row in phase_b_delta}
quarantined_math5_77 = {
    row["family_id"] for row in quarantine_rows
    if row.get("row_id") == "repair_math5_77" and row.get("disposition") == "quarantine_frozen_math500_overlap_gate"
}
assert quarantined_math5_77 == {"mathfam_f91a56318d28452a3d95"}
replacement_exclusions = reserved_families | phase_b_replacements | quarantined_math5_77

selected = []
replacement_delta = []
for original in phase_c_original:
    source = math_rows[original["source_line"] - 1]
    if original["source_line"] not in REQUIRED_REPLACEMENT_LINES:
        chosen = dict(original)
        chosen["selection_revision"] = "unchanged_from_proposed_family_splits"
        selected.append(chosen)
        continue

    pool = [
        row for row in inventory
        if row["family_id"] not in replacement_exclusions
        and row["subject"] == original["subject"]
        and row["level"] == original["level"]
        and not row["metadata_conflict"]
        and not row["current_assembly"]["appeared_in_gradient_train"]
        and not row["current_assembly"]["appeared_in_development"]
        and not row["current_assembly"]["assembly_excluded_rows"]
        and not row["pilot"]
        and not row["math500_gate"]["reject"]
        and not row["cut2"]["candidate_ids"]
        and not DIAGRAM.search(math_rows[row["canonical_source_line"] - 1]["problem"])
    ]
    pool.sort(key=lambda row: sha_text(f"{SELECTION_SEED}|{original['family_id']}|{row['family_id']}"))
    if not pool:
        raise RuntimeError(f"no same-cell text-only replacement for {original['family_id']}")
    repl = pool[0]
    replacement_exclusions.add(repl["family_id"])
    chosen = {
        "family_id": repl["family_id"],
        "family_sha256": repl["family_sha256"],
        "source_line": repl["canonical_source_line"],
        "subject": repl["subject"],
        "level": repl["level"],
        "lane": "train_stage1",
        "execution_phase": "C_complete_stage1",
        "cut2_candidate_ids": [],
        "old_greek_asset_status": "not_in_cut2_candidate_set",
        "source_text_in_manifest": False,
        "selection_revision": "same_cell_text_only_replacement",
        "replaces_family_id": original["family_id"],
        "replaces_source_line": original["source_line"],
    }
    selected.append(chosen)
    replacement_delta.append({
        "reason": "diagram_dependency_rejected_by_existing_stage1_source_gate",
        "old": {key: original[key] for key in ("family_id", "family_sha256", "source_line", "subject", "level")},
        "new": {key: chosen[key] for key in ("family_id", "family_sha256", "source_line", "subject", "level")},
        "selection_seed": SELECTION_SEED,
        "replacement_pool_excluded_all_133_reserved_families": True,
        "replacement_pool_excluded_phaseB_replacements": sorted(phase_b_replacements),
    })

selected.sort(key=lambda row: (row["subject"], row["level"], row["family_id"]))
write_jsonl(HERE / "replacement_delta.jsonl", replacement_delta)

# Copy the proven Stage 1 execution assets byte-for-byte.
for directory in (HERE / "prompts", HERE / "schemas"):
    directory.mkdir(parents=True, exist_ok=True)
shutil.copyfile(STAGE1 / "run_queue.py", HERE / "run_queue.py")
for name in ("adaptation.txt", "solution_blind.txt", "verification_blind.txt", "greek_correction.txt", "source_review.txt"):
    shutil.copyfile(STAGE1 / "prompts" / name, HERE / "prompts" / name)
for name in ("adaptation.schema.json", "solution.schema.json", "greek_correction.schema.json", "source_review.schema.json"):
    shutil.copyfile(STAGE1 / "schemas" / name, HERE / "schemas" / name)

inputs = []
for rank, item in enumerate(selected, 1):
    source = math_rows[item["source_line"] - 1]
    inv = inventory_by_id[item["family_id"]]
    inputs.append({
        "row_id": f"scaleC_math_line_{item['source_line']}",
        "family_id": item["family_id"],
        "family_sha256": item["family_sha256"],
        "group": "maths_scale_phaseC_train",
        "selection_rank": rank,
        "selection_revision": item["selection_revision"],
        "replaces_family_id": item.get("replaces_family_id"),
        "replaces_source_line": item.get("replaces_source_line"),
        "source_path": str(MATH),
        "source_line": item["source_line"],
        "source_split": "MATH train",
        "source_license": "MIT (project documentation)",
        "source_record_sha256": record_sha(source),
        "problem_en": source["problem"],
        "problem_el_seed": None,
        "reference_solution": source["solution"],
        "reference_visibility": "frozen_for_post_solve_human_comparison_only; absent from every queued payload",
        "level": item["level"],
        "subject": item["subject"],
        "math500_overlap": inv["math500_gate"],
        "diagram_or_figure_dependency": False,
        "current_assembly_exposure": inv["current_assembly"],
        "prior_pilot_memberships": inv["pilot"],
        "cut2_candidate_ids": inv["cut2"]["candidate_ids"],
        "metadata_conflict": inv["metadata_conflict"],
        "adaptation_state": "call_required",
        "solution_state": "two_independent_high_calls_required",
    })
write_jsonl(HERE / "inputs.jsonl", inputs)

jobs = []
for row in inputs:
    rid = row["row_id"]
    adapt = f"adapt__{rid}"
    jobs.append({
        "job_id": adapt,
        "stage": "adaptation",
        "row_id": rid,
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/adaptation.schema.json",
        "template": "prompts/adaptation.txt",
        "depends_on": [],
        "payload": {
            "row_id": {"$record": "row_id"},
            "source_identity": {"$record": "source_record_sha256"},
            "source_split": {"$record": "source_split"},
            "level": {"$record": "level"},
            "subject": {"$record": "subject"},
            "problem_text": {"$record": "problem_en"},
        },
    })
    requirements = [
        {"dependency": adapt, "field": "status", "op": "equals", "value": "candidate"},
        {"dependency": adapt, "field": "problem_text", "op": "nonempty_string"},
    ]
    payload = {"row_id": {"$record": "row_id"}, "problem_text": {"$dependency": adapt, "field": "problem_text"}}
    jobs.append({
        "job_id": f"solve_high__{rid}",
        "stage": "solution_high",
        "row_id": rid,
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/solution.schema.json",
        "template": "prompts/solution_blind.txt",
        "depends_on": [adapt],
        "dependency_requirements": requirements,
        "payload": payload,
    })
    jobs.append({
        "job_id": f"verify_high__{rid}",
        "stage": "verification_blind_high",
        "row_id": rid,
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/solution.schema.json",
        "template": "prompts/verification_blind.txt",
        "depends_on": [adapt],
        "dependency_requirements": requirements,
        "payload": payload,
    })
write_jsonl(HERE / "queue.jsonl", jobs)

records = {row["row_id"]: row for row in inputs}
bindings = []
for job in jobs:
    template = HERE / job["template"]
    schema = HERE / job["schema"]
    binding = {
        "job_id": job["job_id"],
        "row_id": job["row_id"],
        "stage": job["stage"],
        "model": job["model"],
        "effort": job["effort"],
        "job_spec_sha256": canonical_sha(job),
        "input_record_sha256": canonical_sha(records[job["row_id"]]),
        "template_sha256": sha_file(template),
        "schema_sha256": sha_file(schema),
        "depends_on": job["depends_on"],
        "reference_solution_in_payload": False,
    }
    if not job["depends_on"]:
        record = records[job["row_id"]]
        payload = {
            "row_id": record["row_id"], "source_identity": record["source_record_sha256"],
            "source_split": record["source_split"], "level": record["level"],
            "subject": record["subject"], "problem_text": record["problem_en"],
        }
        prompt = template.read_text(encoding="utf-8").replace("{{INPUT_JSON}}", json.dumps(payload, ensure_ascii=False, indent=2))
        binding.update(payload_sha256=canonical_sha(payload), prompt_sha256=sha_text(prompt), runtime_dependency_binding=False)
    else:
        binding.update(payload_sha256=None, prompt_sha256=None, runtime_dependency_binding=True)
    bindings.append(binding)
write_jsonl(HERE / "payload_bindings.jsonl", bindings)

evidence = {
    1202: "Inverse proportionality gives pq=150, hence p=10 when q=15.",
    627: "n(n+1)/2>10n for positive n reduces to n>19, so the least n is 20.",
    3416: "Pairing (-1+2)+...+(-9999+10000) gives 5000 pairs of value 1.",
    4273: "Subtracting the circle equations gives 10x-10y-71=0, whose slope is 1.",
    6052: "Repeated cubing and squaring keep 1 and 0 fixed; 42 negations return -1, so the sum is 0.",
    6668: "The independent favorable counts are 3 odd red faces and 2 square green faces out of 36, giving 1/6.",
    2758: "The original perimeter is 22, so the scale factor is 5 and the longest side is 45.",
    3264: "The unit-circle value is cos(135 degrees)=-sqrt(2)/2.",
    5094: "The product of the three least distinct primes is 2*3*5=30.",
    5074: "Euclidean reduction gives gcd(9118,12173)=47, and 33182 is divisible by 47.",
    2042: "Three positive standard-die values have product 1 only for (1,1,1), probability 1/216.",
    2462: "Powers 11^0 through 11^4 are palindromes; 11^5=161051 is the first non-palindrome value.",
    7065: "The squared coordinate differences sum to 9+49+1=59, so the distance is sqrt(59).",
    7319: "The stated angle relations and parallelogram diagonal bisection yield theta=15 degrees, then 105/135=7/9.",
}
source_reads = []
for row in inputs:
    source_reads.append({
        "row_id": row["row_id"],
        "family_id": row["family_id"],
        "source_line": row["source_line"],
        "problem_sha256": sha_text(row["problem_en"]),
        "reference_solution_sha256": sha_text(row["reference_solution"]),
        "reviewer": "Sol agent",
        "review_scope": "complete selected source task and reference solution; obvious ambiguity and internal consistency",
        "obvious_ambiguity": False,
        "source_reference_consistent": True,
        "disposition": "accept_for_adaptation_queue",
        "evidence": evidence[row["source_line"]],
    })
write_jsonl(HERE / "source_read_receipt.jsonl", source_reads)

conditional = {
    "status": "blueprints_only_not_in_primary_queue",
    "greek_correction": {
        "cap": 14,
        "trigger": "Human semantic comparison accepts the mathematics and identifies a language-only defect.",
        "template": "prompts/greek_correction.txt", "schema": "schemas/greek_correction.schema.json",
        "model": "gpt-5.6-sol", "effort": "high",
    },
    "semantic_or_source_repair_shared_pool": {
        "cap": 8,
        "triggers": [
            "Adaptation reports blocked or a substantive source issue.",
            "Human comparison finds an unresolved mathematical disagreement between the two independent high outputs.",
            "A source-valid repair is frozen under a new problem hash before re-solving.",
        ],
        "automatic_xhigh_selection": False,
        "observed_unresolved_escalation_only": True,
    },
    "retry_cap": 8,
    "absolute_call_cap": 72,
    "instantiation_rule": "Use a separately reviewed conditional queue and the same cumulative state ledger; never reset the 72-call cap.",
}
write_json(HERE / "conditional_jobs.json", conditional)

partition = {
    "parent_split_manifest": str(SPLITS),
    "parent_split_manifest_sha256": sha_file(SPLITS),
    "original_phaseC_count": 14,
    "train_only_selected_count": 14,
    "replacement_count": len(replacement_delta),
    "development_identity_digest": canonical_sha(sorted(row["family_id"] for row in split_rows if row["lane"] == "development")),
    "development_count": sum(row["lane"] == "development" for row in split_rows),
    "final_confirmation_identity_digest": canonical_sha(sorted(row["family_id"] for row in split_rows if row["lane"] == "final_confirmation")),
    "final_confirmation_count": sum(row["lane"] == "final_confirmation" for row in split_rows),
    "development_or_final_content_materialized": False,
    "development_or_final_identity_in_inputs": False,
}
write_json(HERE / "partition_receipt.json", partition)

report = f"""# Stage 1 Phase C: frozen train-only maths queue

Prepared at {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}. The queue is ready for root review and has not been launched. No model call, GPU allocation, CSCS job, production transform, or source mutation occurred.

## Selection

The 14 `C_complete_stage1` train identities were read from the frozen 133-family split manifest. Source lines 63 and 2670 were replaced because their problem text depends on a diagram. `replacement_delta.jsonl` records the deterministic `phaseC-replacement-v1` selection:

- Algebra Level 4: line 63 -> text-only line 627.
- Geometry Level 1: line 2670 -> text-only line 2758.

Each replacement is from the same subject and level. The candidate pool excluded all 133 reserved families, all four Phase B replacement families, current Greek gradient-train and development families, assembly exclusions, prior pilot families, cut2 candidates, frozen MATH-500 gate failures, metadata conflicts, and diagram-dependent problem text. `repair_math5_77` resolves to `mathfam_f91a56318d28452a3d95` and remains quarantined by the frozen 13-gram gate; it was explicitly excluded and was not reselected.

The other 12 Phase C identities remain exactly as proposed. Development and final-confirmation identity sets are unchanged, and no development or final-confirmation source content appears in this bundle.

## Source read

All 14 selected English tasks and complete reference solutions were read for obvious ambiguity and internal inconsistency. Each is self-contained in its problem text and accepted for adaptation. `source_read_receipt.jsonl` records the task and reference hashes plus a concise mathematical check for every row. This is a source suitability read, not approval of any future generated Greek problem or solution.

## Queue and cap

The primary queue has 42 high-effort jobs: 14 adaptations, 14 blind solves, and 14 independent blind verifications. Solve and verification share only the accepted adaptation dependency and cannot see each other or the frozen reference solution. There is no automatic xhigh selection.

The absolute cap is 72 calls: 42 primary, at most 14 Greek corrections, a shared maximum of 8 semantic/source-repair or observed-unresolved escalation calls, and at most 8 retries. Conditional work must use the same cumulative ledger, so a new state directory cannot reset the cap. Maximum concurrency remains eight workers.

The runner, prompts, and schemas are byte-identical copies of the proven Stage 1 assets. `manifest.json`, `payload_bindings.jsonl`, and `verification.json` bind and check the exact queue.
"""
(HERE / "report.md").write_text(report, encoding="utf-8")

assets = [
    "inputs.jsonl", "queue.jsonl", "payload_bindings.jsonl", "replacement_delta.jsonl",
    "source_read_receipt.jsonl", "conditional_jobs.json", "partition_receipt.json", "run_queue.py",
    "prompts/adaptation.txt", "prompts/solution_blind.txt", "prompts/verification_blind.txt",
    "prompts/greek_correction.txt", "prompts/source_review.txt", "schemas/adaptation.schema.json",
    "schemas/solution.schema.json", "schemas/greek_correction.schema.json", "schemas/source_review.schema.json",
    "prepare_phaseC.py", "report.md",
]
manifest = {
    "version": 1,
    "status": "prepared_unlaunched_root_review_required",
    "built_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "scope": "fourteen train-only C_complete_stage1 source families",
    "counts": {
        "rows": 14, "replacements": 2, "adaptation_calls": 14, "solution_high_calls": 14,
        "blind_verification_high_calls": 14, "primary_calls": 42,
        "conditional_greek_correction_cap": 14, "conditional_semantic_or_source_shared_cap": 8,
        "retry_cap": 8, "absolute_call_cap": 72,
    },
    "execution": {
        "launched": False, "default_effort": "high", "automatic_xhigh": False,
        "max_workers": 8,
        "runner_source": str(STAGE1 / "run_queue.py"),
        "runner_source_sha256": sha_file(STAGE1 / "run_queue.py"),
        "runner_copy_byte_identical": sha_file(STAGE1 / "run_queue.py") == sha_file(HERE / "run_queue.py"),
    },
    "source_files": {
        str(MATH): {"sha256": sha_file(MATH), "rows": len(math_rows)},
        str(SPLITS): {"sha256": sha_file(SPLITS), "rows": len(split_rows)},
        str(INVENTORY): {"sha256": sha_file(INVENTORY), "rows": len(inventory)},
        str(PHASE_B_DELTA): {"sha256": sha_file(PHASE_B_DELTA), "rows": len(phase_b_delta)},
        str(QUARANTINE): {"sha256": sha_file(QUARANTINE), "rows": len(quarantine_rows)},
    },
    "artifact_sha256": {name: sha_file(HERE / name) for name in assets},
    "notes": [
        "Reference solutions are stored only for later human comparison and are absent from all queued payloads.",
        "Every queued row is MATH train; no development or final-confirmation content is materialized.",
        "The repair_math5_77 family remains quarantined and is absent from selection.",
    ],
}
write_json(HERE / "manifest.json", manifest)
print(json.dumps(manifest["counts"], indent=2))
