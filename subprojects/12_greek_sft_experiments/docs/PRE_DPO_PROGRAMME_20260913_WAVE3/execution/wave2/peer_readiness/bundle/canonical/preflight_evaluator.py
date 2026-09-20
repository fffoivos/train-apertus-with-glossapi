#!/usr/bin/env python3
"""Allocation-free evaluator preflight: live paths and runtime imports.

Issues #87 and #88 are one failure shape seen twice: an evaluation that dies
seconds into a granted allocation on a question that was answerable for free.
A frozen manifest bound files under a staging directory that had been renamed
away (21 s of debug node, no scoring); the selected runtime lacked
`accelerate`, and its predecessor lacked an importable `datasets` (22 s and
24 s, no scoring).

Five check families, all runnable from a login shell before any `salloc`:

* **bindings** — walk any receipt/manifest JSON for binding-shaped objects
  (`{path, bytes, sha256}`) and verify each against the live filesystem with
  the canonical `verify_binding`. A placeholder digest fails: a frozen
  evaluation manifest that binds nothing is not evaluable.
* **imports** — run the exact evaluator interpreter and import the declared
  dependency set, recording each module's version. The refusal names the
  missing package; discovering it inside the allocation is the failure this
  tool exists to prevent.
* **token extrema** — token-binary IDs against the TOKENIZER vocabulary (not
  the padded model dimension, which is exactly how out-of-range IDs hid
  until a device-side assert, issue #27).
* **env-root integrity** — runtime roots whose `.py` sources are symlinks
  into `__pycache__` or dangle entirely (the scratch-cleaner damage of
  issue #123), refused even while the links still resolve.
* **binding comparison** — two or more receipt documents whose bindings must
  agree position-by-position before their losses are compared (issue #78).

The receipt binds the interpreter, the uenv markers visible in the
environment, per-module versions, and per-binding results. Read-only except
for the declared receipt.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apertus_cscs_campaign.receipts import utc_now, verify_binding

SHA256 = re.compile(r"^[0-9a-f]{64}$")


def discover_bindings(value: Any, trail: str = "$") -> list[tuple[str, dict[str, Any]]]:
    """Every binding-shaped object in a JSON document, with its path for naming.

    The `{path, bytes, sha256}` triple is the ecosystem's one universal binding
    shape, so a walk finds every file a manifest claims regardless of which
    experiment's schema wraps it.
    """

    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        if (
            isinstance(value.get("path"), str)
            and "bytes" in value
            and isinstance(value.get("sha256"), str)
        ):
            found.append((trail, value))
        for key, item in value.items():
            found.extend(discover_bindings(item, f"{trail}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(discover_bindings(item, f"{trail}[{index}]"))
    return found


def check_bindings(manifest_path: Path) -> list[dict[str, Any]]:
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = []
    for trail, binding in discover_bindings(document):
        row: dict[str, Any] = {"at": trail, "path": binding["path"]}
        sha = str(binding.get("sha256", ""))
        if not SHA256.match(sha) or len(set(sha)) <= 1:
            row.update(status="failed", reason="placeholder or malformed sha256")
        elif not Path(str(binding["path"])).exists():
            row.update(status="failed", reason="path does not exist")
        else:
            try:
                verify_binding({key: binding[key] for key in ("path", "bytes", "sha256")})
                row.update(status="passed")
            except (OSError, TypeError, ValueError) as error:
                row.update(status="failed", reason=str(error))
        results.append(row)
    return results


def check_imports(python: Path, modules: list[str]) -> list[dict[str, Any]]:
    results = []
    for module in modules:
        probe = subprocess.run(
            [str(python), "-c",
             f"import {module}; print(getattr({module}, '__version__', 'unversioned'))"],
            capture_output=True, text=True, check=False, timeout=300,
        )
        if probe.returncode == 0:
            results.append({"module": module, "status": "passed",
                            "version": probe.stdout.strip()})
        else:
            results.append({"module": module, "status": "failed",
                            "reason": probe.stderr.strip()[-300:]})
    return results


def check_env_root_integrity(env_root: Path) -> list[dict[str, Any]]:
    """Refuse runtime roots that only LOOK intact.

    Issue #123: two shared lm-eval installs had top-level .py sources
    materialized as symlinks into __pycache__/ (an install-time dedup no
    canonical tool performs), and the iopsstor scratch cleaner later reaped
    the unread bytecode by atime -- leaving directories every `ls` shows as
    intact and every import finds dead. Two refusals: a .py that is a symlink
    into __pycache__ is structurally wrong even while it still resolves, and
    any dangling symlink is damage already done.
    """

    results: list[dict[str, Any]] = []
    if not env_root.is_dir():
        return [{"path": str(env_root), "status": "failed",
                 "reason": "environment root does not exist"}]
    for dirpath, _dirnames, filenames in os.walk(env_root):
        for name in filenames:
            path = Path(dirpath) / name
            if not path.is_symlink():
                continue
            target = os.readlink(path)
            if name.endswith(".py") and "__pycache__" in target:
                results.append({
                    "path": str(path), "status": "failed",
                    "reason": f"source materialized as a symlink into a cache "
                              f"({target}): the scratch cleaner reaps unread "
                              f"bytecode by atime, and this file dies with it",
                })
            elif not path.exists():
                results.append({
                    "path": str(path), "status": "failed",
                    "reason": f"dangling symlink (target {target} is gone)",
                })
    if not results:
        results.append({"path": str(env_root), "status": "passed"})
    return results


def check_token_extrema(bin_path: Path, vocab_size: int, dtype: str) -> dict[str, Any]:
    """Refuse validation binaries whose token IDs exceed the model vocabulary.

    Issue #27: a 1.5B qualification trained cleanly through update 25 and then
    died in the first online-validation panel with a device-side assert -- the
    bound tokenizer vocabulary was 148,480 while the frozen binaries carried
    IDs up to 148,991. The two facts were both on disk the whole time; the GPU
    was the most expensive possible place to compare them. `vocab_size` is the
    TOKENIZER vocabulary (valid IDs 0..N-1), not the padded model dimension --
    padding is exactly how out-of-range IDs hid.
    """

    row: dict[str, Any] = {"path": str(bin_path), "vocab_size": vocab_size}
    try:
        import numpy
    except ImportError:
        row.update(status="failed",
                   reason="numpy is required for token-extrema checks; run under "
                          "`uv run` or the pinned uenv interpreter")
        return row
    if not bin_path.is_file():
        row.update(status="failed", reason="binary does not exist")
        return row
    tokens = numpy.memmap(bin_path, dtype=numpy.dtype(dtype), mode="r")
    if tokens.size == 0:
        row.update(status="failed", reason="binary is empty")
        return row
    low, high = int(tokens.min()), int(tokens.max())
    row.update(min_id=low, max_id=high, token_count=int(tokens.size))
    if low < 0 or high >= vocab_size:
        row.update(
            status="failed",
            reason=(f"token IDs span [{low}, {high}] against vocabulary "
                    f"{vocab_size} (valid 0..{vocab_size - 1}); the first "
                    f"validation panel would device-side assert"),
        )
    else:
        row.update(status="passed")
    return row


def compare_binding_documents(paths: list[Path]) -> dict[str, Any]:
    """Report binding divergence across receipt documents.

    Issue #78: two validation-receipt roots exposed the same nine panel names
    and the same tokenization label while their binary and index digests
    differed -- so online-validation losses looked comparable and were not.
    Names lie; digests do not. Divergence here does not change training
    science, but any cross-trajectory loss comparison must route through an
    exactly-matching receipt or the frozen decontaminated suite.
    """

    # POSITIONAL comparison: the same trail must carry the same digest in
    # every document. A digest-set comparison is wrong in both directions --
    # a binding present in only one document is not automatically divergence
    # by itself elsewhere, and two documents whose panels are SWAPPED share
    # an identical digest set while agreeing on nothing.
    per_document: dict[str, dict[str, dict[str, Any]]] = {}
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        per_document[str(path)] = {
            trail: {"path": binding["path"], "sha256": binding["sha256"]}
            for trail, binding in discover_bindings(document)
        }
    trails = sorted(set().union(*per_document.values())) if per_document else []
    divergent = []
    for trail in trails:
        rows = {name: bindings.get(trail) for name, bindings in per_document.items()}
        digests = {row["sha256"] for row in rows.values() if row is not None}
        if len(digests) > 1 or any(row is None for row in rows.values()):
            divergent.append({"at": trail, "bindings": rows})
    report = {
        "documents": {
            name: {trail: row["sha256"] for trail, row in sorted(bindings.items())}
            for name, bindings in per_document.items()
        },
        "divergent_bindings": divergent,
        "status": "passed" if not divergent else "failed",
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", default=[],
                        help="receipt/manifest JSON whose bindings must be live "
                             "(repeatable)")
    parser.add_argument("--runtime-python", type=Path,
                        help="the exact evaluator interpreter to probe")
    parser.add_argument("--imports",
                        help="comma-separated modules the evaluator needs, e.g. "
                             "datasets,accelerate,transformers,torch")
    parser.add_argument("--extra-probe", nargs=argparse.REMAINDER,
                        help="one extra command that must exit 0 (e.g. a no-GPU "
                             "loader construction); everything after this flag")
    parser.add_argument("--token-bin", type=Path, action="append", default=[],
                        help="token binary whose ID extrema must fit the vocabulary "
                             "(repeatable)")
    parser.add_argument("--vocab-size", type=int,
                        help="TOKENIZER vocabulary size (valid IDs 0..N-1), not the "
                             "padded model dimension")
    parser.add_argument("--token-dtype", default="int32",
                        help="numpy dtype of the token binaries (default int32)")
    parser.add_argument("--env-root", type=Path, action="append", default=[],
                        help="runtime root that must contain no cache-symlinked "
                             "sources or dangling links (repeatable)")
    parser.add_argument("--compare", type=Path, nargs="+",
                        help="two or more receipt documents whose bindings must not "
                             "diverge (e.g. the validation receipts of two "
                             "trajectories before comparing their losses)")
    parser.add_argument("--output", type=Path, help="write the receipt here")
    args = parser.parse_args(argv)

    if not any([args.manifest, args.runtime_python, args.token_bin,
                args.compare, args.env_root, args.extra_probe]):
        parser.error("nothing to check: give --manifest, --runtime-python, "
                     "--token-bin, --env-root, --compare, and/or --extra-probe")
    if bool(args.runtime_python) != bool(args.imports):
        parser.error("--runtime-python and --imports go together")
    if bool(args.token_bin) != bool(args.vocab_size):
        parser.error("--token-bin and --vocab-size go together")
    if args.compare and len(args.compare) < 2:
        parser.error("--compare needs at least two documents")

    bindings: list[dict[str, Any]] = []
    for manifest in args.manifest:
        bindings.extend(check_bindings(manifest.resolve()))

    imports: list[dict[str, Any]] = []
    if args.runtime_python:
        python = args.runtime_python.resolve()
        if not python.is_file():
            imports = [{"module": "(interpreter)", "status": "failed",
                        "reason": f"interpreter does not exist: {python}"}]
        else:
            modules = [m.strip() for m in str(args.imports).split(",") if m.strip()]
            imports = check_imports(python, modules)

    # Independent of the import probe: nesting it there silently skipped the
    # declared probe whenever --runtime-python was absent or the interpreter
    # was missing, while the receipt still said extra_probe: null, passed.
    probe_result: dict[str, Any] | None = None
    if args.extra_probe:
        extra = subprocess.run(args.extra_probe, capture_output=True,
                               text=True, check=False, timeout=600)
        probe_result = {
            "command": args.extra_probe,
            "status": "passed" if extra.returncode == 0 else "failed",
            "output_tail": (extra.stdout + extra.stderr).strip()[-300:],
        }

    env_integrity: list[dict[str, Any]] = []
    for env_root in args.env_root:
        env_integrity.extend(check_env_root_integrity(env_root.resolve()))

    token_extrema = [
        check_token_extrema(path.resolve(), int(args.vocab_size), args.token_dtype)
        for path in args.token_bin
    ]
    comparison = (
        compare_binding_documents([path.resolve() for path in args.compare])
        if args.compare
        else None
    )

    failures = (
        [row for row in bindings if row["status"] != "passed"]
        + [row for row in imports if row["status"] != "passed"]
        + [row for row in token_extrema if row["status"] != "passed"]
        + [row for row in env_integrity if row["status"] != "passed"]
        + ([probe_result] if probe_result and probe_result["status"] != "passed" else [])
        + ([comparison] if comparison and comparison["status"] != "passed" else [])
    )
    receipt = {
        "schema_version": "apertus_evaluator_preflight_v1",
        "status": "failed" if failures else "passed",
        "recorded_at": utc_now(),
        "allocation_required": False,
        "runtime_python": str(args.runtime_python) if args.runtime_python else None,
        "uenv_environment": {key: value for key, value in os.environ.items()
                             if key.startswith("UENV")},
        "bindings": bindings,
        "imports": imports,
        "token_extrema": token_extrema,
        "env_integrity": env_integrity,
        "binding_comparison": comparison,
        "extra_probe": probe_result,
    }
    if args.output:
        # Atomic, and deliberately NOT exclusive: a preflight is rerun until
        # it passes, so the receipt must be replaceable -- but never readable
        # half-written.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        staging = args.output.with_name(args.output.name + ".tmp")
        staging.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        os.replace(staging, args.output)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
