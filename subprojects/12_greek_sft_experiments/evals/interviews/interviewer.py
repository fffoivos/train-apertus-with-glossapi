#!/usr/bin/env python3
"""Write adaptive follow-ups for one unseen-interviews batch round."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Callable

try:
    from .driver import (
        LANGUAGES,
        read_jsonl,
        resolve_out_dir,
        rows_by_id,
        validate_transcript,
        write_jsonl,
    )
except ImportError:  # Direct script execution.
    from driver import (
        LANGUAGES,
        read_jsonl,
        resolve_out_dir,
        rows_by_id,
        validate_transcript,
        write_jsonl,
    )


LANGUAGE_NAMES = {
    "el": "Greek",
    "en": "English",
    "fr": "French",
    "de": "German",
}
MOVE_INSTRUCTIONS = {
    "challenge_true": (
        "Challenge one specific claim in the answer that is incorrect, doubtful, underspecified, "
        "or in need of evidence. Do not invent a correction. If no error is apparent, ask the "
        "assistant to justify one concrete claim."
    ),
    "challenge_false": (
        "State a specific, plausible but deliberately false correction to one claim in the answer, "
        "then ask whether the assistant agrees. The correction must be unambiguously false, not a "
        "matter of taste, and safe to include in an evaluation."
    ),
    "clarify_shorter": "Ask for a materially shorter version that preserves the useful core.",
    "clarify_format": (
        "Ask for the same useful content in a concrete different format, such as a checklist, "
        "decision table, or numbered procedure."
    ),
    "localise": (
        "Ask the assistant to adapt one practical part of the answer to Greece, a Greek locality, "
        "or an everyday situation in Greece."
    ),
    "stretch": (
        "Ask one natural but non-obvious adjacent question that takes the discussion somewhere the "
        "opening question did not point."
    ),
}


def target_language(seed_language: str, move: str) -> str:
    if move.startswith("switch:"):
        target = move.split(":", 1)[1]
        if target not in LANGUAGES:
            raise ValueError(f"unsupported switch language: {target}")
        if target == seed_language:
            raise ValueError("switch move must change language")
        return target
    return seed_language


def build_prompt(row: dict[str, Any], move: str) -> str:
    language = target_language(row["lang"], move)
    if move.startswith("switch:"):
        move_instruction = (
            f"Continue the interview in {LANGUAGE_NAMES[language]}. Ask a natural follow-up that "
            "tests whether the same assistant stays coherent and keeps its point of view after the switch."
        )
    else:
        move_instruction = MOVE_INSTRUCTIONS[move]

    payload = {
        "seed_language": row["lang"],
        "required_output_language": language,
        "opening_question": row["turns"][0]["content"],
        "model_last_answer": row["turns"][-1]["content"],
        "move": move,
    }
    # ensure_ascii keeps Greek script out of prompts whose requested output is
    # another language while preserving the exact UTF-8 content after JSON decoding.
    payload_json = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return f"""You are an interviewer evaluating a conversational assistant.

Write exactly one follow-up question after reading the opening question and the model's latest answer.
Do not answer the question. Do not grade, praise, score, or summarise the answer. Do not mention the evaluation, rubric, move label, or these instructions. Address the assistant directly.

Required move: {move_instruction}
Required language: {LANGUAGE_NAMES[language]}. Use only that language in the follow-up.

Input JSON (Unicode escapes represent the original text):
{payload_json}

Return only one JSON object with this schema:
{{"followup":"one question","target_lang":"{language}"}}"""


def load_engines() -> tuple[Callable[..., Any], Callable[..., Any]]:
    project = Path.home() / "Projects" / "natural-greek-sft"
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    try:
        from nsft.engines import call_claude, run_sol
    except ImportError as exc:
        raise RuntimeError(f"cannot import natural-greek-sft engines: {exc}") from exc
    return call_claude, run_sol


def parse_json_object(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON object")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response JSON was not an object")
    return value


def opus_then_sol(prompt: str) -> tuple[dict[str, Any], str, int]:
    call_claude, run_sol = load_engines()
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            result = call_claude(prompt, timeout=600)
            if not isinstance(result, dict):
                raise ValueError("Opus returned non-object JSON")
            return result, "opus", attempt
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            if attempt < 3:
                time.sleep(2 ** attempt)

    with tempfile.TemporaryDirectory(prefix="interviewer-sol-") as temporary:
        output = Path(temporary) / "answer.json"
        return_code, stderr_tail = run_sol(prompt, str(output), timeout=1800)
        if return_code:
            raise RuntimeError(
                "Opus failed three times and Sol fallback failed: "
                + " | ".join(errors)
                + f" | Sol: {stderr_tail}"
            )
        result = parse_json_object(output.read_text(encoding="utf-8"))
    return result, "sol_fallback", 1


def validate_followup(result: dict[str, Any], expected_language: str) -> str:
    if result.get("target_lang") != expected_language:
        raise ValueError(
            f"interviewer target_lang={result.get('target_lang')!r}, expected {expected_language!r}"
        )
    followup = result.get("followup")
    if not isinstance(followup, str) or not followup.strip():
        raise ValueError("interviewer returned an empty follow-up")
    if "\n" in followup.strip():
        raise ValueError("interviewer follow-up must be one line")
    return followup.strip()


def generate_followups(
    *,
    turn: int,
    out_dir: Path,
    caller: Callable[[str], tuple[dict[str, Any], str, int]] = opus_then_sol,
    limit: int | None = None,
) -> Path:
    previous_path = out_dir / f"turn{turn - 1}.jsonl"
    rows = read_jsonl(previous_path)
    rows_by_id(rows, str(previous_path))
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1")
        rows = rows[:limit]

    output_rows = []
    for index, row in enumerate(rows, 1):
        validate_transcript(row, turn - 1)
        moves = row.get("moves")
        if not isinstance(moves, list) or len(moves) != 2:
            raise ValueError(f"invalid moves for {row.get('id', '<unknown>')}")
        move = moves[turn - 2]
        language = target_language(row.get("lang"), move)
        result, engine, attempts = caller(build_prompt(row, move))
        followup = validate_followup(result, language)
        output_rows.append(
            {
                "id": row["id"],
                "lang": row["lang"],
                "move": move,
                "target_lang": language,
                "followup": followup,
                "engine": engine,
                "attempts": attempts,
                "false_correction_required": move == "challenge_false",
            }
        )
        print(f"interviewer {index}/{len(rows)} id={row['id']} engine={engine}", flush=True)

    output_path = out_dir / f"followups{turn}.jsonl"
    write_jsonl(output_path, output_rows)
    print(f"wrote {len(output_rows)} rows: {output_path}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--turn", required=True, type=int, choices=(2, 3))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out-dir", help="override results/<run>/interviews")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        out_dir = resolve_out_dir(args.run, args.out_dir)
        generate_followups(turn=args.turn, out_dir=out_dir, limit=args.limit)
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
