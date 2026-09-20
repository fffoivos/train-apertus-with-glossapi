#!/usr/bin/env python3
"""Freeze the experiment adapter contract and non-launching data-stage draft."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "remote_bundle"
REMOTE_BUNDLE = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_tool_reexport_pilot/code")
REMOTE_RUN = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_tool_reexport_pilot/run")
CANONICAL = Path("/iopsstor/scratch/cscs/fffoivos/orchestration/apertus-cscs-efficiency/01f4b7e21f39f346-dolci-tool200")
SNAPSHOT = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home/hub/datasets--allenai--Dolci-Instruct-SFT/snapshots/bd3c8f3a9b2cc5a9682e44b96ddd0bb2ff027221")
TOKENIZER = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


implementation = {}
for key, rel in {
    "pilot_runner": "pilot_run.py",
    "export_core": "frozen_science/export_core.py",
    "consumer": "frozen_science/assemble_mix_r2.py",
    "vantage_scan": "frozen_science/vantage_scan.py",
    "sft_train": "frozen_science/sft_train.py",
}.items():
    implementation[key] = {"path": rel, "sha256": sha(BUNDLE / rel)}
if implementation["export_core"]["sha256"] != "d508a4e9b4b94406e82ab20adb7bf92a9c03ece1ef323a354f28aa3c55f2b39f":
    raise SystemExit("applied export_core hash drift")

pilot = {
    "schema_version": "dolci_tool200_pilot_v1",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "target_rows": 200,
    "max_tokens": 4032,
    "source": {
        "dataset": "allenai/Dolci-Instruct-SFT",
        "revision": "bd3c8f3a9b2cc5a9682e44b96ddd0bb2ff027221",
        "snapshot": str(SNAPSHOT),
        "inventory_path": "source_inventory.json",
        "inventory_sha256": sha(BUNDLE / "source_inventory.json"),
        "selected_shards": [
            {"file": "data/train-00013-of-00015.parquet", "bytes": 252776199,
             "sha256": "f9e7f3ce84bb64da974ccdb3762d2158d6cc303fdc651868906038fbdc82b72a"},
            {"file": "data/train-00014-of-00015.parquet", "bytes": 659412194,
             "sha256": "83524879c6aefd376b15c52361f642a8bd543c93f22d509f94c842a260dd0b86"},
        ],
        "required_source_dataset": "Dolci Instruct Tool Use",
    },
    "implementation": implementation,
    "tokenizer": {
        "model": "swiss-ai/Apertus-8B-Instruct-2509",
        "revision": "b946d40447b2b597999b9c86d44bee0b452c919f",
        "path": str(TOKENIZER),
        "files": {
            "tokenizer.json": "bb201fb226cde11f66c3cf51c5344fb37b1611f00c21e75c324546d854eff2e1",
            "tokenizer_config.json": "b89e07508603d6e1f2c8642f366c2469063c3eddae0585f1e67934ee98498ab1",
            "chat_template.jinja": "56f72c27fa2e565312a830b7315a455c79fb452fdbe7a5b7595d8a094f282b07",
        },
    },
    "acceptance": {
        "exact_native_roundtrip": "200/200",
        "schemas": "every nonempty functions field parses as JSON Schema wrappers",
        "calls": "every call parses, names a declared function, and validates literal arguments against its visible schema",
        "rendered_consumer_survival": "all schemas, calls, results, and any upstream IDs survive the actual consumer",
        "source_identity": "source_dataset, typed source_id, locator, and revision exact",
        "length": "exclude rather than clip rows above 4032 rendered tokens",
        "semantic_review": "40 deterministic structurally stratified rows, required before promotion",
    },
}
(BUNDLE / "pilot_contract.json").write_text(json.dumps(pilot, ensure_ascii=False, indent=2) + "\n")
pilot_contract_sha = sha(BUNDLE / "pilot_contract.json")

data_stage = {
    "schema_version": "apertus_data_stage_v1",
    "stage_id": "dolci-tool200-lossless",
    "execution_target": {"kind": "clariden", "name": "clariden"},
    "code_root": str(CANONICAL),
    "run_root": str(REMOTE_RUN),
    "live_cluster_receipt": {
        "path": "/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_tool_reexport_pilot/live_cluster_receipt.json",
        "bytes": 0,
        "sha256": "0" * 64,
    },
    "resource_profiles": {
        "cpu-debug": {
            "resource_class": "debug", "account": "a0140", "partition": "debug",
            "nodes": 1, "time_limit_seconds": 1800, "max_array_parallel": 1,
            "cpus_per_task": 8, "memory_mb": 64000, "gpus_per_node": 0,
        }
    },
    "tasks": [{
        "id": "export-validate-tool200", "stage": "validate", "resource_profile_id": "cpu-debug",
        "argv": [
            "uenv", "run", "--view=default", "pytorch/v2.9.1:v2", "--",
            "/iopsstor/scratch/cscs/fffoivos/venvs/sft5/bin/python",
            str(REMOTE_BUNDLE / "pilot_run.py"), "--contract", str(REMOTE_BUNDLE / "pilot_contract.json"),
            "--expected-contract-sha256", pilot_contract_sha,
        ],
        "depends_on": [], "max_attempts": 1,
        "expected_receipt": {"path": "receipts/tool200.json", "schema_version": "dolci_tool200_pilot_receipt_v1", "accepted_status": ["passed"]},
    }],
    "approval": {
        "approved_by": "pending-root-review", "approved_at": datetime.now(timezone.utc).isoformat(),
        "scope_sha256": "", "allow_preparation_submission": False,
    },
}
# A live receipt is deliberately rebound after staging and immediately before compile.
(HERE / "data_stage_contract.prebind.json").write_text(json.dumps(data_stage, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"pilot_contract_sha256": pilot_contract_sha, "data_stage_status": "prebind_nonlaunching"}, indent=2))
