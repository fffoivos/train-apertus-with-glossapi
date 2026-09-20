#!/usr/bin/env python3
"""Read-only consistency checks for the two frozen CPU-stage preparations."""

from __future__ import annotations

import ast
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
OPENMATH = HERE.parent / "english_competition_math"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


checks: dict[str, object] = {}

# Every committed JSON artifact must parse, and every Python artifact must parse
# without importing project dependencies or writing bytecode.
json_paths = sorted(HERE.rglob("*.json")) + sorted(OPENMATH.glob("*.json"))
for path in json_paths:
    json.loads(path.read_text())
py_paths = sorted(HERE.rglob("*.py")) + [OPENMATH / "pilot_intake.py"]
for path in py_paths:
    ast.parse(path.read_text(), filename=str(path))
checks["json_files_parsed"] = len(json_paths)
checks["python_files_ast_parsed"] = len(py_paths)

# Dolci source selection and its identity digest.
inventory_path = HERE / "source_inventory.json"
inventory = json.loads(inventory_path.read_text())
selected = inventory["selected"]
require(inventory["target"] == 200 and len(selected) == 200, "Dolci target drift")
typed_ids = {(type(row["source_id"]).__name__, canonical(row["source_id"])) for row in selected}
locators = {
    (
        row["source_locator"]["file"],
        row["source_locator"]["row_group"],
        row["source_locator"]["row_in_group"],
    )
    for row in selected
}
require(len(typed_ids) == 200, "Dolci source IDs are not unique")
require(len(locators) == 200, "Dolci locators are not unique")
strata = Counter(row["stratum"] for row in selected)
require(
    strata
    == {
        "data/train-00013-of-00015.parquet": 100,
        "data/train-00014-of-00015.parquet": 100,
    },
    "Dolci shard balance drift",
)
locator_digest = hashlib.sha256(canonical(selected).encode()).hexdigest()
require(locator_digest == inventory["selected_locator_sha256"], "Dolci locator digest drift")
require(sum(row["rows"] for row in inventory["files"]) == 2_152_112, "Dolci row count drift")
require(sum(row["tool_use_rows"] for row in inventory["files"]) == 227_579, "Dolci Tool Use count drift")
require(sum(row["selected"] for row in inventory["files"]) == 200, "Dolci file selection count drift")
require(sha(HERE / "remote_bundle" / "source_inventory.json") == sha(inventory_path), "Dolci inventory copy drift")
checks["dolci_selection"] = {
    "rows": len(selected),
    "unique_typed_source_ids": len(typed_ids),
    "unique_locators": len(locators),
    "strata": dict(strata),
    "locator_sha256": locator_digest,
}

# Dolci runner and immutable science bindings.
pilot_contract_path = HERE / "remote_bundle" / "pilot_contract.json"
pilot_contract = json.loads(pilot_contract_path.read_text())
require(sha(pilot_contract_path) == "d1ed83ff7049ccfa49a7e12d1492f20a2ef512330abc542b2bc5bc80a29b09e7", "Dolci contract drift")
for binding in pilot_contract["implementation"].values():
    require(sha(HERE / "remote_bundle" / binding["path"]) == binding["sha256"], f"implementation drift: {binding['path']}")
require(sha(HERE / "pilot_run.py") == sha(HERE / "remote_bundle" / "pilot_run.py"), "runner copy drift")
checks["dolci_contract_sha256"] = sha(pilot_contract_path)

# OpenMath source-worker self-binding.
openmath_contract_path = OPENMATH / "pilot_contract.prebind.json"
openmath_script_path = OPENMATH / "pilot_intake.py"
require(sha(openmath_contract_path) == "1cf73a4038a0ca55b8b5a9b2ea69686edb775e9404f4defc06dfbf66f72031ed", "OpenMath contract drift")
require(sha(openmath_script_path) == "33505d07b73e596dceefe1a09c0d7f409eeec8608649f18d27b073ff209b95d2", "OpenMath worker drift")
openmath_contract = json.loads(openmath_contract_path.read_text())
require(openmath_contract["implementation_sha256"] == sha(openmath_script_path), "OpenMath worker binding drift")
checks["openmath_contract_sha256"] = sha(openmath_contract_path)
checks["openmath_worker_sha256"] = sha(openmath_script_path)

# Data-stage bounds and independence. These are prebind templates: they remain
# deliberately nonlaunching and use placeholder live receipt bindings.
stage_summaries = {}
for label, path, expected_payload_sha in (
    ("dolci", HERE / "data_stage_contract.prebind.json", checks["dolci_contract_sha256"]),
    ("openmath", HERE / "openmath_data_stage_contract.prebind.json", checks["openmath_contract_sha256"]),
):
    stage = json.loads(path.read_text())
    profile = stage["resource_profiles"]["cpu-debug"]
    task = stage["tasks"][0]
    require(profile["gpus_per_node"] == 0, f"{label}: GPU request")
    require(profile["time_limit_seconds"] == 1800, f"{label}: time limit drift")
    require(profile["max_array_parallel"] == 1, f"{label}: array cap drift")
    require(task["max_attempts"] == 1, f"{label}: attempt budget drift")
    require(task["depends_on"] == [], f"{label}: unexpected dependency")
    require(stage["approval"]["allow_preparation_submission"] is False, f"{label}: prebind became launchable")
    marker = task["argv"].index("--expected-contract-sha256")
    require(task["argv"][marker + 1] == expected_payload_sha, f"{label}: payload hash argv drift")
    stage_summaries[label] = {
        "stage_id": stage["stage_id"],
        "run_root": stage["run_root"],
        "data_stage_contract_sha256": sha(path),
        "payload_sha256": expected_payload_sha,
        "max_attempts": task["max_attempts"],
        "time_limit_seconds": profile["time_limit_seconds"],
        "cpus_per_task": profile["cpus_per_task"],
        "memory_mb": profile["memory_mb"],
        "gpus_per_node": profile["gpus_per_node"],
    }
require(stage_summaries["dolci"]["run_root"] != stage_summaries["openmath"]["run_root"], "run roots overlap")
checks["data_stages"] = stage_summaries

# Local canonical compiles prove schema/routing shape only. They do not prove
# staged bytes, the live remote binding, or scheduler acceptance.
for label, name, expected_task in (
    ("dolci", "compiled_data_stage.local_validation.json", "export-validate-tool200"),
    ("openmath", "compiled_openmath_data_stage.local_validation.json", "intake-openmath-original"),
):
    compiled = json.loads((HERE / name).read_text())
    require(compiled["schema_version"] == "apertus_compiled_data_stage_v1", f"{label}: compiled schema")
    require(len(compiled["batches"]) == 1, f"{label}: expected one batch")
    require(compiled["batches"][0]["task_ids"] == [expected_task], f"{label}: batch task drift")
checks["local_canonical_compile"] = {"dolci": "passed", "openmath": "passed"}

remote_scheduler = {}
for label in ("dolci", "openmath"):
    receipt_path = HERE / "remote_readiness" / label / "scheduler_test_only_v2.json"
    receipt = json.loads(receipt_path.read_text())
    assertions = receipt["assertions"]
    require(receipt["status"] == "passed" and receipt["returncode"] == 0, f"{label}: scheduler test failed")
    require(all(assertions.values()), f"{label}: scheduler-test assertion failed")
    require(receipt["tested_command"][1] == "--test-only", f"{label}: not test-only")
    require(receipt["submission_environment"]["APERTUS_DATA_STAGE_PYTHON"].endswith("/wave2_data_stage_runner_venv/bin/python"), f"{label}: worker runtime drift")
    remote_scheduler[label] = {
        "receipt_sha256": sha(receipt_path),
        "manifest_sha256": receipt["manifest"]["sha256"],
        "contract_digest": receipt["contract_digest"],
        "status": receipt["status"],
    }
checks["remote_scheduler_test_only"] = remote_scheduler

# Final root-reviewed manifests. These coexist with the immutable nonlaunching
# prebind evidence above. Each approved contract must be the contract embedded
# by the canonical compiler, retain the reviewed resource limits, and match the
# exact manifest tested by Slurm.
approved_expected = {
    "dolci": {
        "contract_sha256": "45f646258665067b814b3706ef580bc5669d3fb3462ea24d55e200544a54ea2d",
        "manifest_sha256": "62670ea9d50284a5b758c21971faeace43c140bb9e1121fb2caf49177ca330fb",
        "contract_digest": "953b052353217ae9d53dfee34abf15c30d8231a75c3878a17789243e8f25d4c4",
        "display_id": "3391276",
    },
    "openmath": {
        "contract_sha256": "def6b28bd300a5b0d9f316164a291edf98dd30f00fdc5348bdbbe42675505dd2",
        "manifest_sha256": "53a0710412c799ad5bdafe05dae6e5b276d048058fca4b3692617646d3a631d6",
        "contract_digest": "462a925790a5dbd76d0b4a627ea90e8ebe69c92f480a7141ac98fa10257b9c1d",
        "display_id": "3391277",
    },
}
approved = {}
for label, expected in approved_expected.items():
    root = HERE / "remote_readiness" / label
    contract_path = root / "data_stage_contract.approved.json"
    manifest_path = root / "compiled_data_stage.approved.json"
    scheduler_path = root / "scheduler_test_only_approved.json"
    contract = json.loads(contract_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    scheduler = json.loads(scheduler_path.read_text())
    require(sha(contract_path) == expected["contract_sha256"], f"{label}: approved contract drift")
    require(sha(manifest_path) == expected["manifest_sha256"], f"{label}: approved manifest drift")
    # The canonical compiler intentionally reduces the live receipt binding to
    # its path after verifying the supplied hash and byte count. Compare the
    # remaining contract exactly and assert that preserved path separately.
    compiled_contract = manifest["contract"]
    source_without_live = {k: v for k, v in contract.items() if k != "live_cluster_receipt"}
    compiled_without_live = {k: v for k, v in compiled_contract.items() if k != "live_cluster_receipt"}
    require(compiled_without_live == source_without_live, f"{label}: compiled contract differs from approved contract")
    require(
        compiled_contract["live_cluster_receipt"]["path"] == contract["live_cluster_receipt"]["path"],
        f"{label}: compiled live receipt path drift",
    )
    require(manifest["contract_digest"] == expected["contract_digest"], f"{label}: approved digest drift")
    require(contract["approval"]["allow_preparation_submission"] is True, f"{label}: approval disabled")
    require(contract["approval"]["approved_by"] == "root-review-2026-09-13", f"{label}: reviewer drift")
    profile = contract["resource_profiles"]["cpu-debug"]
    task = contract["tasks"][0]
    require(profile["gpus_per_node"] == 0, f"{label}: approved GPU request")
    require(profile["time_limit_seconds"] == 1800, f"{label}: approved time drift")
    require(profile["max_array_parallel"] == 1, f"{label}: approved array cap drift")
    require(task["max_attempts"] == 1, f"{label}: approved attempt cap drift")
    require(scheduler["status"] == "passed" and scheduler["returncode"] == 0, f"{label}: approved scheduler test failed")
    require(all(scheduler["assertions"].values()), f"{label}: approved scheduler assertion failed")
    require(scheduler["manifest"]["sha256"] == expected["manifest_sha256"], f"{label}: tested wrong manifest")
    require(scheduler["contract_digest"] == expected["contract_digest"], f"{label}: tested wrong contract digest")
    require(scheduler["tested_command"][1] == "--test-only", f"{label}: approved test was not test-only")
    require(expected["display_id"] in scheduler["stderr"], f"{label}: display ID drift")
    approved[label] = {
        "contract_sha256": sha(contract_path),
        "manifest_sha256": sha(manifest_path),
        "contract_digest": manifest["contract_digest"],
        "scheduler_test_only_receipt_sha256": sha(scheduler_path),
        "scheduler_display_id": expected["display_id"],
        "approval": contract["approval"],
        "resource": {
            "nodes": profile["nodes"],
            "time_limit_seconds": profile["time_limit_seconds"],
            "gpus_per_node": profile["gpus_per_node"],
            "max_attempts": task["max_attempts"],
        },
    }
checks["approved_final_manifests"] = approved

receipt = {
    "schema_version": "wave2_cpu_preparations_validation_v1",
    "status": "approved_exact_test_only_passed_ready_for_root_apply_review",
    "checks": checks,
    "remote_scheduler_test": {
        "status": "passed_for_approved_final_manifests",
        "boundary": "The approved bytes are scheduler-valid, but this validation did not submit either job. Root retains the apply boundary.",
    },
    "billing_bounds_chf": {
        "dolci_max": 1.345,
        "openmath_max": 1.345,
        "combined_only_if_both_separately_launched": 2.69,
    },
}
parser = argparse.ArgumentParser()
parser.add_argument("--output")
args = parser.parse_args()
rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
if args.output:
    Path(args.output).write_text(rendered)
print(rendered, end="")
