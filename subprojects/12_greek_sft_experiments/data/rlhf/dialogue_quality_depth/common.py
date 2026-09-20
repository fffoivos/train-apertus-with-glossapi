"""Small dependency-free helpers shared by the dialogue pilot."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any, Iterable


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(canonical(value))


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
    # A single O_APPEND write keeps records intact across cooperating processes.
    data = (canonical(row) + "\n").encode("utf-8")
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
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def ensure_jsonl(path: os.PathLike[str] | str) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)


def latest_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[str(row[key])] = row
    return out


def estimate_tokens(value: Any) -> int:
    """Conservative tokenizer-free estimate used only for batching/admission."""
    text = value if isinstance(value, str) else canonical(value)
    return max(1, (len(text.encode("utf-8")) + 2) // 3)


def stage_dir(state: os.PathLike[str] | str, stage: str) -> pathlib.Path:
    if stage not in {"smoke", "measurement"}:
        raise ValueError("stage must be smoke or measurement")
    return pathlib.Path(state) / stage

