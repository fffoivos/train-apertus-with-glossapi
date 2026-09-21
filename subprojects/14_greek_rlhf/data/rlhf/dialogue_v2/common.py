"""Dependency-free helpers for dialogue v2 (copied from dialogue_quality_depth/common.py, extended)."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib
import tempfile
import threading
from typing import Any, Iterable

HERE = pathlib.Path(__file__).resolve().parent
RLHF = HERE.parent
SUBPROJECT = RLHF.parent.parent
V2_RUNTIME = HERE / "runtime"
C60_ROOT = HERE / "collection60"
C60_RUNTIME = C60_ROOT / "runtime"
RGD_ROOT = RLHF / "reference_guided_dialogue_demo"
RGD_RUNTIME = RGD_ROOT / "runtime"
PILOT_RUNTIME = RLHF / "dialogue_quality_depth" / "runtime"
GLOSSARY_PATH = RLHF / "prompts" / "seed_label_definitions_v1.md"
RUBRIC_PATH = RLHF / "prompts" / "judge_rank4_v2_en.txt"

_append_lock = threading.Lock()


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(canonical(value))


def sha256_file(path: os.PathLike[str] | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha16_file(path: os.PathLike[str] | str) -> str:
    return sha256_file(path)[:16]


def read_json(path: os.PathLike[str] | str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: os.PathLike[str] | str) -> list[dict[str, Any]]:
    p = pathlib.Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: os.PathLike[str] | str, row: dict[str, Any]) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = (canonical(row) + "\n").encode("utf-8")
    with _append_lock:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic_json(path: os.PathLike[str] | str, value: Any) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, 0o644)
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_text(path: os.PathLike[str] | str, text: str) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, 0o644)
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def latest_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[str(row[key])] = row
    return out


def estimate_tokens(value: Any) -> int:
    text = value if isinstance(value, str) else canonical(value)
    return max(1, (len(text.encode("utf-8")) + 2) // 3)


def word_count(text: str) -> int:
    return len([w for w in text.replace("—", " ").split() if any(ch.isalnum() for ch in w)])


def runtime_dir_for(case_id: str) -> pathlib.Path:
    if case_id.startswith("DVI"):
        return V2_RUNTIME
    if case_id.startswith("RGD"):
        return RGD_RUNTIME
    if case_id.startswith("C60"):
        return C60_RUNTIME
    raise ValueError(f"unknown case id {case_id!r}")


def run_tag_for(case_id: str) -> str:
    if case_id.startswith("C60"):
        return "c60"
    return "dvi" if case_id.startswith("DVI") else "rgd"


def is_c60(case_id: str) -> bool:
    """The 60-dialogue collection (DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md) runs the amended protocol."""
    return case_id.startswith("C60")
