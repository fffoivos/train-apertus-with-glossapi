#!/usr/bin/env python3
"""Build the review-only development authoring package. Never dispatch calls."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNNER_SHA = "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"
GLOBAL_CAP = 118
CONSUMED = 68
PACKAGE_CAP = 20
FALSE_ID = "pilot48_05_false"
FALSE_BEFORE = "Είχα πει κανονικό καφέ, όχι ντεκαφεϊνέ. Κάν' τον τώρα κανονικό."
FALSE_AFTER = "Η τρέχουσα παραγγελία είναι κανονικός καφές, όχι ντεκαφεϊνέ. Κάν' τον τώρα κανονικό."


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows))


def author_job(row_id: str) -> dict[str, Any]:
    return {
        "job_id": f"author__{row_id}",
        "stage": "dialogue_authoring",
        "row_id": row_id,
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/author_dialogue.schema.json",
        "template": "prompts/author_dialogue.txt",
        "depends_on": [],
        "payload": {
            "row_id": {"$record": "row_id"},
            "family_id": {"$record": "family_id"},
            "split": {"$record": "split"},
            "message_plan": {"$record": "message_plan"},
            "protected": {"$record": "protected"},
            "scenario_spec": {"$record": "scenario_spec"},
        },
    }


def greek_job(row: dict[str, Any]) -> dict[str, Any]:
    rid = row["row_id"]
    author = f"author__{rid}"
    plan = row["message_plan"]
    allowed = [
        plan["optional_context_user_id"],
        plan["optional_context_assistant_id"],
        plan["decision_user_id"],
        plan["target_assistant_id"],
    ]
    return {
        "job_id": f"greek__{rid}",
        "stage": "greek_correction",
        "row_id": rid,
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/greek_correction.schema.json",
        "template": "prompts/greek_correction.txt",
        "depends_on": [author],
        "dependency_requirements": [
            {"dependency": author, "field": "status", "op": "equals", "value": "candidate"},
            {"dependency": author, "field": "checks_needed", "op": "equals", "value": []},
            {"dependency": author, "field": "issues", "op": "equals", "value": []},
        ],
        "payload": {
            "row_id": {"$record": "row_id"},
            "messages": {"$dependency": author, "field": "messages"},
            "domain": "native Greek dialogue",
            "teaching_objective": {"$record": "teaching_objective"},
            "allowed_edit_locations": allowed,
            "protected": {
                "family_id": {"$record": "family_id"},
                "split": {"$record": "split"},
                "truth_category": {"$record": "scenario_spec.truth_category"},
                "oracle": {"$record": "scenario_spec.oracle"},
                "claims": {"$record": "scenario_spec.claim_atoms"},
                "current_request": {"$record": "scenario_spec.current_request"},
                "exact_response": {"$record": "scenario_spec.expected.exact_response"},
                "action_contract": {"$record": "scenario_spec.action_contract"},
                "scope_rules": [
                    "A displayed record is not a claim about every earlier version or the whole world.",
                    "A clearly stated new user value or instruction applies immediately.",
                    "Missing values and ambiguous references must remain missing or ambiguous.",
                    "A text-record edit does not perform an external action.",
                ],
            },
        },
    }


def static_binding(job: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    def get(value: Any, dotted: str) -> Any:
        for key in dotted.split("."):
            value = value[key]
        return value

    def resolve(value: Any) -> Any:
        if isinstance(value, list):
            return [resolve(x) for x in value]
        if not isinstance(value, dict):
            return value
        if set(value) == {"$record"}:
            return get(record, value["$record"])
        if "$dependency" in value:
            raise ValueError("dependency output is intentionally unavailable before authoring")
        return {key: resolve(child) for key, child in value.items()}

    payload = resolve(job["payload"])
    template = (HERE / job["template"]).read_text()
    prompt = template.replace("{{INPUT_JSON}}", json.dumps(payload, ensure_ascii=False, indent=2))
    return {
        "job_id": job["job_id"],
        "row_id": job["row_id"],
        "stage": job["stage"],
        "job_spec_sha256": canonical_sha(job),
        "input_record_sha256": canonical_sha(record),
        "payload_sha256": canonical_sha(payload),
        "template_sha256": sha(HERE / job["template"]),
        "schema_sha256": sha(HERE / job["schema"]),
        "assembled_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "prompts").mkdir(exist_ok=True)
    (HERE / "schemas").mkdir(exist_ok=True)

    source = PARENT / "inputs/dev.jsonl"
    original_rows = read_jsonl(source)
    assert len(original_rows) == 8
    rows = copy.deepcopy(original_rows)
    changed = next(row for row in rows if row["row_id"] == FALSE_ID)
    spec = changed["scenario_spec"]
    assert spec["user_decision_semantic_content_el"] == FALSE_BEFORE
    assert spec["decision_surface_contract"]["frozen_core_el"] == FALSE_BEFORE
    assert changed["protected"]["decision_surface_contract"]["frozen_core_el"] == FALSE_BEFORE
    spec["user_decision_semantic_content_el"] = FALSE_AFTER
    spec["decision_surface_contract"]["frozen_core_el"] = FALSE_AFTER
    changed["protected"]["decision_surface_contract"]["frozen_core_el"] = FALSE_AFTER
    assert spec["expected"]["response_moves"][0] == "correct_historical_claim_briefly"
    spec["expected"]["response_moves"][0] = "correct_current_record_claim_briefly"
    changed["preparation_lineage"] = {
        "source": "../inputs/dev.jsonl",
        "source_file_sha256": sha(source),
        "source_record_sha256": canonical_sha(next(row for row in original_rows if row["row_id"] == FALSE_ID)),
        "candidate_source_repair": "history_to_explicit_current_record_scope",
        "original_preserved": True,
    }
    for row in rows:
        row.setdefault("preparation_lineage", {
            "source": "../inputs/dev.jsonl",
            "source_file_sha256": sha(source),
            "source_record_sha256": canonical_sha(next(x for x in original_rows if x["row_id"] == row["row_id"])),
            "candidate_source_repair": None,
            "original_preserved": True,
        })

    write_jsonl(HERE / "inputs.jsonl", rows)
    write_jsonl(HERE / "source_semantic_repairs.jsonl", [{
        "row_id": FALSE_ID,
        "status": "candidate_source_repair_for_root_review",
        "defect": "The old core's historical clause is true in the visible initial state, while the false oracle evaluates the current state after the decaf update.",
        "before": FALSE_BEFORE,
        "after": FALSE_AFTER,
        "unchanged_claim_atom": {"field": "coffee", "asserted": "κανονικός"},
        "unchanged_current_request": {"kind": "version_ops", "ops": [{"op": "set", "field": "coffee", "value": "κανονικός"}], "current_update_authority": True},
        "unchanged_oracle": spec["oracle"],
        "response_move_before": "correct_historical_claim_briefly",
        "response_move_after": "correct_current_record_claim_briefly",
        "source_record_sha256": canonical_sha(next(row for row in original_rows if row["row_id"] == FALSE_ID)),
        "prepared_record_sha256": canonical_sha(changed),
        "model_calls": 0,
    }])

    authors = [author_job(row["row_id"]) for row in rows]
    combined = authors + [greek_job(row) for row in rows]
    write_jsonl(HERE / "queue_author8.jsonl", authors)
    write_jsonl(HERE / "queue_author8_then_greek8.jsonl", combined)

    shutil.copyfile(PARENT / "run_queue.py", HERE / "run_queue.py")
    shutil.copyfile(PARENT / "prompts/author_dialogue.txt", HERE / "prompts/author_dialogue.txt")
    shutil.copyfile(PARENT / "greek_train32/prompts/greek_correction.txt", HERE / "prompts/greek_correction.txt")
    shutil.copyfile(PARENT / "prompts/semantic_repair.txt", HERE / "prompts/semantic_repair.txt")
    shutil.copyfile(PARENT / "schemas/author_dialogue.schema.json", HERE / "schemas/author_dialogue.schema.json")
    shutil.copyfile(PARENT / "schemas/greek_correction.schema.json", HERE / "schemas/greek_correction.schema.json")
    shutil.copyfile(PARENT / "schemas/semantic_repair.schema.json", HERE / "schemas/semantic_repair.schema.json")
    assert sha(HERE / "run_queue.py") == RUNNER_SHA

    by_id = {row["row_id"]: row for row in rows}
    bindings = [static_binding(job, by_id[job["row_id"]]) for job in authors]
    for job in combined[8:]:
        bindings.append({
            "job_id": job["job_id"],
            "row_id": job["row_id"],
            "stage": job["stage"],
            "job_spec_sha256": canonical_sha(job),
            "input_record_sha256": canonical_sha(by_id[job["row_id"]]),
            "template_sha256": sha(HERE / job["template"]),
            "schema_sha256": sha(HERE / job["schema"]),
            "depends_on": job["depends_on"],
            "assembled_prompt_sha256": None,
            "deferred_reason": "The exact Greek payload binds the reviewed author output at runtime; no candidate has been generated in preparation.",
        })
    write_jsonl(HERE / "payload_bindings.jsonl", bindings)

    write_json(HERE / "conditional_calls.json", {
        "status": "templates_only_not_dispatchable_until_observed_defect_or_failed_attempt",
        "semantic_repair": {
            "cap": 2,
            "model": "gpt-5.6-sol",
            "effort": "high",
            "schema": "schemas/semantic_repair.schema.json",
            "template": "prompts/semantic_repair.txt",
            "instantiation_gate": "Root records a concrete semantic defect after reading an authored candidate; candidate and named finding are then hash-bound.",
        },
        "retry": {
            "cap": 2,
            "max_attempts_per_job": 2,
            "instantiation_gate": "Only a failed primary attempt may retry; successful candidates are not sampled again.",
        },
        "no_cap_reset": True,
    })
    write_json(HERE / "launch_sequence.json", {
        "status": "review_only_do_not_launch_from_preparation",
        "steps": [
            "Review inputs.jsonl, the single source repair, both prompts, schemas and bindings.",
            "Run queue_author8.jsonl with at most eight workers and --limit-new-calls 8.",
            "Read all eight authored dialogues semantically; do not infer quality from schema acceptance.",
            "Instantiate at most two semantic repairs only for concrete observed defects, preserving the same run-state and package cap. If a repair is used, freeze a reviewed queue variant whose Greek job depends on that repair and reads candidate_messages; do not let Greek correction read the superseded author messages.",
            "After semantic acceptance, run the Greek jobs from queue_author8_then_greek8.jsonl with --limit-new-calls 8 when no repair was needed, or from the newly hash-bound reviewed variant when a repair was accepted.",
            "Adjudicate Greek proposals as language-only changes before accepting development rows.",
        ],
        "author_command_template": "python3 run_queue.py --queue queue_author8.jsonl --inputs inputs.jsonl --state-dir run_state/dev --max-workers 8 --call-cap 20 --limit-new-calls 8 --execute --acknowledge-reviewed-payload PREPARED_PAYLOAD_REVIEWED",
        "greek_command_template": "python3 run_queue.py --queue queue_author8_then_greek8.jsonl --inputs inputs.jsonl --state-dir run_state/dev --max-workers 8 --call-cap 20 --limit-new-calls 8 --execute --acknowledge-reviewed-payload PREPARED_PAYLOAD_REVIEWED",
        "manual_gate_between_queues": True,
        "concurrency_policy": "Do not launch concurrently with another eight-worker queue.",
    })
    write_json(HERE / "partition_receipt.json", {
        "development": {
            "rows": 8,
            "families": dict(Counter(row["family_id"] for row in rows)),
            "truth_categories": dict(Counter(row["scenario_spec"]["truth_category"] for row in rows)),
            "source_sha256": sha(source),
        },
        "train": {
            "accepted_rows": 32,
            "accepted_receipt": "../accepted_train32/receipt.json",
            "accepted_receipt_sha256": sha(PARENT / "accepted_train32/receipt.json"),
            "content_copied_into_development_package": False,
        },
        "final_confirmation": {
            "row_count": 8,
            "dispatchable": 7,
            "quarantined": 1,
            "gate_summary": "../sealed/final_confirmation/gate_summary.json",
            "gate_summary_sha256": sha(PARENT / "sealed/final_confirmation/gate_summary.json"),
            "content_read_or_materialized_by_this_builder": False,
        },
        "silence_quarantine": {
            "row_id": "pilot48_12_unresolved",
            "count": 1,
            "quarantine_receipt": "../quarantine/silence_unspecified.jsonl",
            "quarantine_receipt_sha256": sha(PARENT / "quarantine/silence_unspecified.jsonl"),
        },
        "family_disjointness": "Inherited from frozen revision2 prelaunch verification; final identities remain sealed and were not independently reopened here.",
    })

    report_time = utc()
    (HERE / "report.md").write_text(f"""# Development-8 authoring preparation

Prepared at `{report_time}`. This package contains the eight frozen development decisions only: four outcomes for `cf05_cafe_order` and four for `cf09_library_hold`. No model calls were made and no run-state directory was created.

## Semantic source review

Seven source decisions recompute cleanly from visible user evidence. `pilot48_05_false` needed one narrow candidate source repair before authoring. Its old wording, “Είχα πει κανονικό καφέ”, is historically true because the initial order was regular coffee; the false oracle concerns the current record after the later decaf update. The prepared wording explicitly asserts the current record and keeps the second sentence as an authoritative new update to regular coffee. The original development file is unchanged, and `source_semantic_repairs.jsonl` binds both versions.

## Dispatch envelope

The primary envelope is eight authoring calls followed, only after full semantic review, by eight Greek language checks. Up to two observed semantic defects may use the existing semantic-repair contract, and up to two failed jobs may retry. That is 16 primary plus at most four conditional calls, or 20 additional calls. With 68 pilot calls already consumed, the maximum becomes 88 of the unchanged global cap of 118, leaving 30 calls of headroom.

`queue_author8.jsonl` is the first dispatch. `queue_author8_then_greek8.jsonl` reuses the accepted author envelopes and exposes the Greek jobs only through their dependencies. Schema acceptance is not a semantic quality verdict; all eight author outputs must be read before the second queue. Both stages retain high effort, at most eight workers, and the frozen generic runner.

If semantic repair is needed, the corresponding Greek job must be rebound to the accepted repair's `candidate_messages`; the current combined queue must not be used for that row because it deliberately points to the original author result. The reviewed queue variant and its new hashes must be frozen without resetting the 20-call package cap.

## Partition boundary

The accepted train32 package is referenced by receipt and is not copied here. Final-confirmation content was not read or materialized by this builder: its frozen gate still reports seven dispatchable rows, while the one silence case remains quarantined. The prior revision2 family-disjoint verification is inherited; this preparation does not reopen sealed final identities.
""")

    artifacts = {}
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "verification.json", "runner_plan_author8.json", "runner_plan_combined.json"}:
            artifacts[str(path.relative_to(HERE))] = sha(path)
    manifest = {
        "version": 1,
        "created_at": utc(),
        "status": "prepared_not_launched",
        "scope": "eight development decisions only",
        "counts": {
            "primary_authoring": 8,
            "greek_correction": 8,
            "semantic_repair_cap": 2,
            "retry_cap": 2,
            "absolute_call_cap": PACKAGE_CAP,
        },
        "cumulative_budget": {
            "pilot_calls_consumed_before_package": CONSUMED,
            "package_max_additional_calls": PACKAGE_CAP,
            "projected_cumulative_at_package_cap": CONSUMED + PACKAGE_CAP,
            "global_pilot_absolute_cap": GLOBAL_CAP,
            "headroom_after_package_cap": GLOBAL_CAP - CONSUMED - PACKAGE_CAP,
            "no_cap_reset": True,
        },
        "runner": {"max_workers": 8, "sha256": RUNNER_SHA},
        "manual_semantic_gate_before_greek": True,
        "source_repair_count": 1,
        "original_dev_source_preserved": True,
        "prompt_tuning": False,
        "final_materialization": False,
        "model_calls_during_preparation": 0,
        "artifact_sha256": artifacts,
    }
    write_json(HERE / "manifest.json", manifest)


if __name__ == "__main__":
    main()
