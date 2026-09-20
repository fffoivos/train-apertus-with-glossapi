#!/usr/bin/env python3
"""Run Slurm test-only on the exact command rendered by canonical data-stage code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from apertus_cscs_readiness.data_stage import sbatch_command, verify_compiled


def file_binding(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


parser = argparse.ArgumentParser()
parser.add_argument("--manifest", required=True, type=Path)
parser.add_argument("--batch", required=True)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--data-stage-python", required=True, type=Path)
args = parser.parse_args()

data_stage_python = args.data_stage_python.resolve()
if not data_stage_python.is_file() or not os.access(data_stage_python, os.X_OK):
    raise SystemExit("bound data-stage worker interpreter is missing or not executable")

compiled = verify_compiled(args.manifest)
command = sbatch_command(args.manifest, args.batch, 1)
if command[0] != "sbatch" or "--test-only" in command:
    raise SystemExit("unexpected canonical scheduler command")
test_command = ["sbatch", "--test-only", *command[1:]]
if any(part.startswith("--gpus") or part.startswith("--gres") for part in test_command):
    raise SystemExit("CPU pilot unexpectedly requests a GPU")

for part in command:
    if part.startswith("--output=") or part.startswith("--error="):
        Path(part.split("=", 1)[1]).parent.mkdir(parents=True, exist_ok=True)

started = datetime.now(timezone.utc)
environment = os.environ.copy()
environment["APERTUS_DATA_STAGE_PYTHON"] = str(data_stage_python)
completed = subprocess.run(
    test_command, text=True, capture_output=True, check=False, timeout=60, env=environment
)
finished = datetime.now(timezone.utc)
receipt = {
    "schema_version": "apertus_data_stage_exact_scheduler_test_v1",
    "status": "passed" if completed.returncode == 0 else "failed",
    "started_at": started.isoformat(),
    "finished_at": finished.isoformat(),
    "elapsed_seconds": round((finished - started).total_seconds(), 3),
    "host": socket.gethostname(),
    "machine": platform.machine(),
    "manifest": file_binding(args.manifest),
    "contract_digest": compiled["contract_digest"],
    "canonical_code_tree_sha256": compiled["code_bundle"]["tree_sha256"],
    "submission_environment": {
        "APERTUS_DATA_STAGE_PYTHON": str(data_stage_python),
    },
    "batch": args.batch,
    "attempt": 1,
    "canonical_command": command,
    "tested_command": test_command,
    "returncode": completed.returncode,
    "stdout": completed.stdout,
    "stderr": completed.stderr,
    "assertions": {
        "test_only_inserted": test_command[1] == "--test-only",
        "canonical_command_otherwise_exact": test_command[2:] == command[1:],
        "no_gpu_or_gres_argument": not any(
            part.startswith("--gpus") or part.startswith("--gres") for part in test_command
        ),
        "one_array_element": "--array=0%1" in command,
        "no_requeue": "--no-requeue" in command,
        "worker_interpreter_exported_via_all": environment.get("APERTUS_DATA_STAGE_PYTHON")
        == str(data_stage_python),
    },
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
raise SystemExit(completed.returncode)
