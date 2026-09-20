#!/usr/bin/env python3
"""Prepare an independent, nonlaunching canonical data-stage contract for OpenMath."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
OPENMATH = ROOT / "english_competition_math"
SCRIPT = OPENMATH / "pilot_intake.py"
CONTRACT = OPENMATH / "pilot_contract.prebind.json"
EXPECTED_SCRIPT = "33505d07b73e596dceefe1a09c0d7f409eeec8608649f18d27b073ff209b95d2"
EXPECTED_CONTRACT = "1cf73a4038a0ca55b8b5a9b2ea69686edb775e9404f4defc06dfbf66f72031ed"
REMOTE_CODE = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_openmath_original_pilot/code")
REMOTE_RUN = Path("/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_openmath_original_pilot/run")
CANONICAL = Path("/iopsstor/scratch/cscs/fffoivos/orchestration/apertus-cscs-efficiency/01f4b7e21f39f346-dolci-tool200")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(SCRIPT) == EXPECTED_SCRIPT
assert sha(CONTRACT) == EXPECTED_CONTRACT
value = {
    "schema_version": "apertus_data_stage_v1",
    "stage_id": "openmath-original-pilot",
    "execution_target": {"kind": "clariden", "name": "clariden"},
    "code_root": str(CANONICAL), "run_root": str(REMOTE_RUN),
    "live_cluster_receipt": {
        "path": "/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_openmath_original_pilot/live_cluster_receipt.json",
        "bytes": 0, "sha256": "0" * 64,
    },
    "resource_profiles": {
        "cpu-debug": {
            "resource_class": "debug", "account": "a0140", "partition": "debug", "nodes": 1,
            "time_limit_seconds": 1800, "max_array_parallel": 1, "cpus_per_task": 8,
            "memory_mb": 64000, "gpus_per_node": 0,
        }
    },
    "tasks": [{
        "id": "intake-openmath-original", "stage": "validate", "resource_profile_id": "cpu-debug",
        "argv": [
            "uenv", "run", "--view=default", "pytorch/v2.9.1:v2", "--",
            "/iopsstor/scratch/cscs/fffoivos/venvs/sft5/bin/python",
            str(REMOTE_CODE / "pilot_intake.py"), "--contract", str(REMOTE_CODE / "pilot_contract.json"),
            "--expected-contract-sha256", EXPECTED_CONTRACT,
        ],
        "depends_on": [], "max_attempts": 1,
        "expected_receipt": {"path": "receipts/openmath.json", "schema_version": "openmath_original_pilot_v1", "accepted_status": ["passed"]},
    }],
    "approval": {"approved_by": "pending-root-review", "approved_at": datetime.now(timezone.utc).isoformat(),
                 "scope_sha256": "", "allow_preparation_submission": False},
}
out = HERE / "openmath_data_stage_contract.prebind.json"
out.write_text(json.dumps(value, indent=2) + "\n")
print(sha(out))
