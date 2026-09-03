#!/usr/bin/env python3
"""Select the fixed, config-stratified 40-prompt reading set from WP0's dev union."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, NoReturn

CONFIGS = (
    "no_robots",
    "coconot",
    "personas_if",
    "smolcon",
    "oasst",
    "everyday",
    "systemchats",
    "no_robots_en_pov",
    "apertus_en",
    "euroblocks_fr",
    "euroblocks_de",
)
LANGUAGE = {
    **{name: "el" for name in CONFIGS[:7]},
    "no_robots_en_pov": "en",
    "apertus_en": "en",
    "euroblocks_fr": "fr",
    "euroblocks_de": "de",
}
# Four from each Greek config and three from each remaining config: 28 + 12 = 40.
QUOTA = {name: (4 if index < 7 else 3) for index, name in enumerate(CONFIGS)}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def prompt_messages(row: dict[str, Any]) -> list[dict[str, str]]:
    messages = row.get("messages")
    if not isinstance(messages, list):
        fail(f"row {row.get('row_id')} has no messages list")
    if not all(isinstance(message, dict) for message in messages):
        fail(f"row {row.get('row_id')} has a non-object message")
    last_assistant = max(
        (index for index, message in enumerate(messages) if message.get("role") == "assistant"),
        default=-1,
    )
    prefix = messages[:last_assistant] if last_assistant >= 0 else messages
    if not prefix or prefix[-1].get("role") != "user":
        fail(f"row {row.get('row_id')} does not yield a prompt ending in a user turn")
    clean = []
    for message in prefix:
        if message.get("role") not in {"system", "user", "assistant"} or not isinstance(
            message.get("content"), str
        ):
            fail(f"row {row.get('row_id')} has an invalid message")
        clean.append({"role": message["role"], "content": message["content"]})
    return clean


def stable_key(seed: int, config: str, row_id: str) -> str:
    return hashlib.sha256(f"{seed}\0{config}\0{row_id}".encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/arms/dev_all.jsonl"))
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("reading40.jsonl"))
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()
    if not args.input.is_file():
        fail(f"WP0 dev union not found: {args.input}")

    groups: dict[str, list[dict[str, Any]]] = {name: [] for name in CONFIGS}
    seen: set[str] = set()
    with args.input.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"invalid JSON at {args.input}:{line_number}: {exc.msg}")
            config = row.get("config")
            row_id = str(row.get("row_id") or "")
            if config not in groups or not row_id:
                fail(f"unknown config or missing row_id at {args.input}:{line_number}")
            identity = f"{config}:{row_id}"
            if identity in seen:
                fail(f"duplicate row identity: {identity}")
            seen.add(identity)
            groups[config].append(row)

    selected = []
    for config in CONFIGS:
        candidates = sorted(
            groups[config], key=lambda row: stable_key(args.seed, config, str(row["row_id"]))
        )
        if len(candidates) < QUOTA[config]:
            fail(f"config {config} has {len(candidates)} rows; need {QUOTA[config]}")
        for row in candidates[: QUOTA[config]]:
            selected.append(
                {
                    "prompt_id": f"{config}:{row['row_id']}",
                    "row_id": row["row_id"],
                    "config": config,
                    "category": row.get("category"),
                    "language": LANGUAGE[config],
                    "messages": prompt_messages(row),
                }
            )
    if len(selected) != 40:
        fail(f"internal quota error: selected {len(selected)}, expected 40")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(selected)} fixed prompts to {args.out}")
    print("per_config=" + json.dumps(QUOTA, sort_keys=True))


if __name__ == "__main__":
    main()
