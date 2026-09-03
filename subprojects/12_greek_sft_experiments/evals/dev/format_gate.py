#!/usr/bin/env python3
"""Apply termination, language-script, and turn-structure gates to dev generations."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ASSISTANT_END = "<|assistant_end|>"
ROLE_TOKENS = re.compile(
    r"<\|(?:system|developer|user|assistant)_(?:start|end)\|>|"
    r"<\|(?:inner|tools)_(?:prefix|suffix)\|>"
)
THRESHOLDS = {"ended_on_stop": 0.95, "language_ok": 0.98, "single_assistant_turn": 0.95}


def greek_script_share(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    greek = sum("GREEK" in unicodedata.name(char, "") for char in letters)
    return greek / len(letters)


def evaluate(row: dict[str, Any]) -> dict[str, Any]:
    raw = str(row.get("raw_text", row.get("text", "")))
    language = row.get("language")
    share = greek_script_share(str(row.get("text", raw.replace(ASSISTANT_END, ""))))
    ended = row.get("stop_reason") == "assistant_end" and raw.rstrip().endswith(ASSISTANT_END)
    if language == "el":
        language_ok = share >= 0.90
    elif language in {"en", "fr", "de"}:
        language_ok = share < 0.02
    else:
        language_ok = False
    role_tokens = ROLE_TOKENS.findall(raw)
    single_turn = ended and role_tokens == [ASSISTANT_END]
    return {
        "prompt_id": row.get("prompt_id"),
        "language": language,
        "greek_script_share": share,
        "ended_on_stop": ended,
        "language_ok": language_ok,
        "single_assistant_turn": single_turn,
        "role_tokens": role_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generations", type=Path)
    args = parser.parse_args()
    if not args.generations.is_file():
        raise SystemExit(f"ERROR: generations file not found: {args.generations}")
    rows = []
    with args.generations.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"ERROR: invalid JSON at line {line_number}: {exc.msg}")
    if not rows:
        raise SystemExit("ERROR: generations file is empty")
    details = [evaluate(row) for row in rows]
    metrics = {
        name: sum(bool(item[name]) for item in details) / len(details) for name in THRESHOLDS
    }
    passed = all(metrics[name] >= threshold for name, threshold in THRESHOLDS.items())
    report = {
        "source": str(args.generations),
        "n": len(details),
        "thresholds": THRESHOLDS,
        "metrics": metrics,
        "passed": passed,
        "failures": [item for item in details if not all(item[name] for name in THRESHOLDS)],
    }
    output = args.generations.parent / "format_gate.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verdict = "PASS" if passed else "FAIL"
    print(
        f"{verdict} ended_on_stop={metrics['ended_on_stop']:.3f} "
        f"language_ok={metrics['language_ok']:.3f} "
        f"single_assistant_turn={metrics['single_assistant_turn']:.3f} n={len(details)}"
    )
    print(f"wrote {output}")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
