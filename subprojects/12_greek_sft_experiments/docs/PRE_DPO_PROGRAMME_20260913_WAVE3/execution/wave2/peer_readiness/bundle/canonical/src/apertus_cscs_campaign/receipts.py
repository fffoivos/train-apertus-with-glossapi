"""Hash bindings and immutable receipt primitives for campaign evidence."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

PASS_STATUSES = {"accepted", "completed", "frozen", "passed", "promoted", "proven"}
# AGENTS.md rides inside the bundle so the rules and the code that enforces them
# cannot drift apart: a bundle carries the operating guidance it was frozen with.
# The cost is deliberate -- editing the wording requalifies the OPERATIONAL
# digest (never the scientific one), which is the correct blast radius for a
# change to how the runner must be operated.
CODE_FIXED_PATHS = ("pyproject.toml", "AGENTS.md")
GUIDANCE_CATALOG = "guidance/cscs-skills.json"
CODE_RECURSIVE_ROOTS = (
    "bin",
    "scripts",
    "src",
    "slurm/campaign",
    "slurm/checkpoint",
    "slurm/data_stage",
    "schemas",
)
FORBIDDEN_CODE_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache"}
FORBIDDEN_CODE_SUFFIXES = {".pyc", ".pyo"}
IGNORED_ROOT_ENTRIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
}


class SchemaToolingUnavailable(RuntimeError):
    """JSON-Schema tooling is absent from this interpreter."""


def schema_tooling() -> tuple[Any, Any, Any, Any]:
    """Import the schema stack lazily.

    The campaign worker runs in an isolated interpreter (`-I -B`, only the frozen
    bundle on sys.path) so that nothing can shadow the code bundle. That
    interpreter has no site-packages, so a module-level third-party import here
    makes every worker unimportable -- which on 2026-08-16 killed two `normal`
    allocations, one of them 16 nodes, nine seconds after they started.

    Authoring and compilation happen where the tooling exists and remain fully
    schema-validated; the worker re-checks identity by digest instead.
    """

    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
    except ImportError as exc:  # pragma: no cover - exercised on the worker
        raise SchemaToolingUnavailable(str(exc)) from exc
    return Draft202012Validator, FormatChecker, Registry, Resource


def schema_tooling_available() -> bool:
    try:
        schema_tooling()
    except SchemaToolingUnavailable:
        return False
    return True


def validate_json_schema(value: Any, schema_name: str, *, required: bool = True) -> bool:
    """Validate a public contract against the checked-in Draft 2020-12 schema.

    Returns True when the schema was actually checked. With ``required=False``
    an interpreter without the tooling reports False instead of raising, so a
    caller that has already proven the artifact by digest can proceed without
    silently claiming the schema was verified.
    """

    try:
        Draft202012Validator, FormatChecker, Registry, Resource = schema_tooling()
    except SchemaToolingUnavailable:
        if required:
            raise
        return False

    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource

    schema_root = Path(__file__).resolve().parents[2] / "schemas"
    schemas = [json.loads(path.read_text(encoding="utf-8")) for path in schema_root.glob("*.json")]
    registry = Registry()
    for schema in schemas:
        schema_id = schema.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, Resource.from_contents(schema))
    schema = next(
        (schema for schema in schemas if Path(str(schema.get("$id", ""))).name == schema_name),
        None,
    )
    if schema is None:
        raise FileNotFoundError(f"JSON schema is missing: {schema_name}")
    errors = sorted(
        Draft202012Validator(
            schema,
            registry=registry,
            format_checker=FormatChecker(),
        ).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(f"{schema_name} validation failed at {location}: {first.message}")
    return True


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path}: expected a JSON object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def file_binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise FileNotFoundError(resolved)
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def verify_binding(binding: dict[str, Any]) -> Path:
    if not isinstance(binding, dict):
        raise TypeError("file binding must be an object")
    path = Path(str(binding.get("path", ""))).resolve()
    if (
        not path.is_file()
        or path.is_symlink()
        or path.stat().st_size != int(binding.get("bytes", -1))
        or sha256_file(path) != binding.get("sha256")
    ):
        raise ValueError(f"file binding drift: {path}")
    return path


def enumerate_code_paths(
    root: Path,
    *,
    recorded_paths: set[str] | None = None,
) -> list[Path]:
    """Enumerate the complete executable surface and reject runtime caches."""

    resolved = root.resolve()
    paths = [
        resolved / relative
        for relative in CODE_FIXED_PATHS
        if recorded_paths is None or relative in recorded_paths
    ]
    for relative_root in CODE_RECURSIVE_ROOTS:
        source = resolved / relative_root
        root_was_recorded = recorded_paths is None or any(
            relative == relative_root or relative.startswith(f"{relative_root}/")
            for relative in recorded_paths
        )
        # The signed inventory defines which roots were executable when the
        # historical bundle was frozen.  A later verifier must not retroactively
        # treat a pre-existing docs/helper subtree as executable merely because
        # today's canonical surface includes it.
        if not root_was_recorded:
            continue
        if not source.is_dir() or source.is_symlink():
            # Verification must remain able to authenticate bundles frozen
            # before a new canonical subtree was introduced.  Such a subtree
            # is optional only when the signed historical inventory contains
            # no file beneath it.  New bundle creation passes no inventory and
            # therefore continues to require every current canonical root.
            raise FileNotFoundError(f"canonical code root missing: {source}")
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"unsafe executable-tree symlink: {path}")
            if any(part in FORBIDDEN_CODE_PARTS for part in path.parts):
                if path.is_file():
                    raise ValueError(f"runtime cache present in code bundle: {path}")
                continue
            if path.is_file():
                if path.is_symlink() or path.suffix in FORBIDDEN_CODE_SUFFIXES:
                    raise ValueError(f"unsafe executable-tree entry: {path}")
                paths.append(path)
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise FileNotFoundError("canonical campaign code bundle is incomplete")
    relative_paths = [str(path.relative_to(resolved)) for path in paths]
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("duplicate path in executable code bundle")
    return sorted(paths, key=lambda path: str(path.relative_to(resolved)))


def enumerate_root_entries(root: Path) -> list[str]:
    """Bind the bundle root namespace that can influence imports and launch paths."""

    resolved = root.resolve()
    entries: list[str] = []
    for path in sorted(resolved.iterdir(), key=lambda item: item.name):
        if path.name in IGNORED_ROOT_ENTRIES:
            continue
        if path.is_symlink():
            raise ValueError(f"unsafe code-bundle root symlink: {path}")
        if path.name in FORBIDDEN_CODE_PARTS or path.suffix in FORBIDDEN_CODE_SUFFIXES:
            raise ValueError(f"runtime cache present in code-bundle root: {path}")
        entries.append(path.name)
    return entries


def guidance_projection(catalog: dict[str, Any]) -> dict[str, Any]:
    """The part of the guidance catalog that is a rule rather than an observation.

    The catalog cites a live scheduler probe, and refreshing that probe rewrites
    its locator, timestamp and hash. Binding the catalog verbatim would therefore
    requalify every bundle each time somebody looked at the cluster -- churn that
    says nothing about what the guidance requires. The projection keeps the
    directives and the source's identity, and drops the observation itself.
    """

    projection = copy.deepcopy(catalog)
    for source in projection.get("evidence_sources", []):
        if source.get("type") == "live_probe_receipt":
            for volatile in ("locator", "observed_at", "content_sha256"):
                source.pop(volatile, None)
    return projection


def guidance_binding(root: Path) -> dict[str, Any] | None:
    path = root / GUIDANCE_CATALOG
    if not path.is_file():
        return None
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {
        "relative_path": GUIDANCE_CATALOG,
        "catalog_revision": catalog.get("catalog_revision"),
        "projection_sha256": digest(guidance_projection(catalog)),
    }


def code_bundle_binding(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    root_entries = enumerate_root_entries(resolved)
    files = []
    for path in enumerate_code_paths(resolved):
        binding = file_binding(path)
        binding["relative_path"] = str(path.relative_to(resolved))
        files.append(binding)
    guidance = guidance_binding(resolved)
    material = [
        {"root_entries": root_entries},
        {"guidance": guidance},
        *[
            {
                "relative_path": row["relative_path"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
            }
            for row in files
        ],
    ]
    return {
        "schema_version": "apertus_campaign_code_bundle_v2",
        "root": str(resolved),
        "root_entries": root_entries,
        "tree_sha256": digest(material),
        "guidance": guidance,
        "files": files,
    }


def verify_code_bundle(binding: dict[str, Any], executing_root: Path) -> None:
    expected_root = executing_root.resolve()
    if (
        binding.get("schema_version") != "apertus_campaign_code_bundle_v2"
        or Path(str(binding.get("root", ""))).resolve() != expected_root
    ):
        raise ValueError("executing code bundle root drift")
    files = binding.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("executing code bundle file list missing")
    observed_root_entries = enumerate_root_entries(expected_root)
    if binding.get("root_entries") != observed_root_entries:
        raise ValueError(
            "executing code-bundle root namespace drift: "
            f"recorded={binding.get('root_entries')}, observed={observed_root_entries}"
        )
    recorded_paths = {str(row.get("relative_path", "")) for row in files}
    observed_paths = {
        str(path.relative_to(expected_root))
        for path in enumerate_code_paths(expected_root, recorded_paths=recorded_paths)
    }
    if observed_paths != recorded_paths:
        raise ValueError(
            "executing code bundle path-set drift: "
            f"added={sorted(observed_paths - recorded_paths)}, "
            f"missing={sorted(recorded_paths - observed_paths)}"
        )
    observed_guidance = guidance_binding(expected_root)
    guidance_was_recorded = "guidance" in binding
    if guidance_was_recorded and binding.get("guidance") != observed_guidance:
        raise ValueError(
            "executing code-bundle guidance drift: the bundle's operating guidance "
            "is not the guidance it was frozen with"
        )
    material = [{"root_entries": observed_root_entries}]
    if guidance_was_recorded:
        material.append({"guidance": observed_guidance})
    for row in files:
        relative = str(row.get("relative_path", ""))
        expected_path = (expected_root / relative).resolve()
        if expected_path != Path(str(row.get("path", ""))).resolve():
            raise ValueError(f"executing code bundle path drift: {relative}")
        verify_binding(row)
        material.append(
            {
                "relative_path": relative,
                "bytes": row["bytes"],
                "sha256": row["sha256"],
            }
        )
    if digest(material) != binding.get("tree_sha256"):
        raise ValueError("executing code bundle tree digest drift")


def atomic_json(path: Path, value: dict[str, Any], *, exclusive: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == payload:
            return
        if exclusive:
            raise FileExistsError(f"refusing to replace non-identical receipt: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_utc(value: str) -> dt.datetime:
    observed = dt.datetime.fromisoformat(value)
    return observed if observed.tzinfo else observed.replace(tzinfo=dt.timezone.utc)
