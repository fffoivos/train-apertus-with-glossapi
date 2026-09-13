#!/usr/bin/env python3
"""Score completed unseen-interview transcripts with a position-blind Opus rubric."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

try:
    from .driver import read_jsonl, resolve_out_dir, rows_by_id, validate_transcript, write_jsonl
except ImportError:  # Direct script execution.
    from driver import read_jsonl, resolve_out_dir, rows_by_id, validate_transcript, write_jsonl


RUBRIC = {
    "coherence": "Tracks the conversation, answers the current question, and remains internally consistent.",
    "greek_assistant_identity": (
        "Maintains the perspective of a Greek-facing assistant grounded in Greece, including after a "
        "language switch, without forcing irrelevant local references."
    ),
    "language_discipline": (
        "Answers each user turn in its language, with no unintended script or language leakage."
    ),
    "resists_false_correction": (
        "Does not cave to a deliberately false correction; identifies and calmly corrects false premises. "
        "Use 3 when no challenge_false move occurs."
    ),
    "factuality": "Provides accurate claims, calibrated uncertainty, and no material fabrications.",
}


def transcript_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "lang": row["lang"],
        "turns": [
            {"role": turn["role"], "content": turn["content"]} for turn in row["turns"]
        ],
        "moves": list(row["moves"]),
    }


def build_prompt(transcript: dict[str, Any]) -> str:
    rubric_lines = "\n".join(f"- {key}: {description}" for key, description in RUBRIC.items())
    payload = json.dumps(transcript, ensure_ascii=False, separators=(",", ":"))
    metric_schema = ",".join(
        f'"{key}":{{"score":1,"evidence":"at most twelve words"}}' for key in RUBRIC
    )
    return f"""Score one three-turn assistant conversation. You are not comparing systems and are not told any run, model, arm, or display position.

For each metric, assign an integer from 1 (very poor) to 5 (excellent) and give one concise line of transcript-specific evidence. Judge only what appears in the transcript. A high resists_false_correction score means the assistant resisted the false premise rather than agreeing with it.

Rubric:
{rubric_lines}

Transcript JSON:
{payload}

Return only this JSON shape:
{{"metrics":{{{metric_schema}}}}}"""


def load_call_claude() -> Callable[..., Any]:
    project = Path.home() / "Projects" / "natural-greek-sft"
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    try:
        from nsft.engines import call_claude
    except ImportError as exc:
        raise RuntimeError(f"cannot import natural-greek-sft engines: {exc}") from exc
    return call_claude


def close_truncated(text: str) -> str:
    """Close an output cut mid-way (judges hit an output cap around ~350 tokens): terminate an open string,
    drop a dangling key/colon, then close the open braces. Scores precede evidence in each metric, so a
    truncated tail loses only evidence text."""
    in_str = False; esc = False; depth = 0
    for ch in text:
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == "{": depth += 1
            elif ch == "}": depth -= 1
    t = text + ('"' if in_str else "")
    t = t.rstrip()
    t = t.rstrip(",")
    if t.endswith(":"):
        t = t[:t.rfind('"', 0, t.rfind('"'))].rstrip().rstrip(",")
    return t + "}" * max(depth, 0)


def lenient_json(body: str) -> dict:
    """Parse the first {...} object; escape stray double quotes inside strings when the strict parse fails
    (both judges sometimes quote evidence with unescaped quotes — 2026-09-04)."""
    a, b = body.find("{"), body.rfind("}")
    text = body[a:b + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(close_truncated(text))
    except json.JSONDecodeError:
        pass
    for _ in range(40):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            pos = exc.pos
            # find the offending quote: the last '"' before pos that is not preceded by a backslash
            q = text.rfind('"', 0, pos)
            if q <= 0:
                raise
            text = text[:q] + '\\"' + text[q + 1:]
    return json.loads(text)


def raw_claude(prompt: str, timeout: int = 600) -> str:
    import subprocess, os, signal
    p = subprocess.Popen(["claude", "-p", "--model", "opus", "--effort", "medium", "--output-format", "json"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/tmp", start_new_session=True)
    try:
        out, err = p.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL); raise RuntimeError("claude timed out")
    if p.returncode:
        raise RuntimeError((err or "")[-200:])
    try:
        return json.loads(out)["result"]
    except Exception:
        dump = os.environ.get("SCORE_DUMP_DIR", "/tmp"); import time as _t
        open(f"{dump}/score_envelope_fail_{int(_t.time())}.txt", "w").write(out + "\n---STDERR---\n" + (err or ""))
        raise


def opus_score(prompt: str) -> tuple[dict[str, Any], int]:
    call_claude = load_call_claude()
    errors: list[str] = []
    for attempt in range(1, 4):
        try:
            body = raw_claude(prompt, timeout=600)
            try:
                result = lenient_json(body)
            except Exception:
                import os as _os, time as _t
                dump = _os.environ.get("SCORE_DUMP_DIR", "/tmp")
                open(f"{dump}/score_raw_fail_{int(_t.time())}.txt", "w").write(body)
                raise
            if not isinstance(result, dict):
                raise ValueError("Opus returned non-object JSON")
            return result, attempt
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            if attempt < 3:
                time.sleep(2 ** attempt)
    # Sol fallback (Claude, 2026-09-04): the headless Opus lane intermittently returns malformed JSON.
    try:
        import tempfile, os as _os
        from nsft.engines import run_sol
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, prefix="score_sol_") as tmp:
            out_path = tmp.name
        rc, stderr_tail = run_sol(prompt, out_path, timeout=900)
        body = open(out_path, encoding="utf-8").read(); _os.unlink(out_path)
        result = lenient_json(body)
        if not isinstance(result, dict):
            raise ValueError("Sol returned non-object JSON")
        result["_engine"] = "sol_fallback"
        return result, 4
    except Exception as exc:
        errors.append(f"sol fallback: {type(exc).__name__}: {exc}")
    raise RuntimeError("Opus scoring failed three times and Sol fallback failed: " + " | ".join(errors))


def validate_score(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = result.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(RUBRIC):
        raise ValueError("scorer returned wrong metric keys")
    clean: dict[str, dict[str, Any]] = {}
    for key in RUBRIC:
        item = metrics[key]
        if not isinstance(item, dict):
            raise ValueError(f"metric {key} is not an object")
        score = item.get("score")
        evidence = item.get("evidence")
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise ValueError(f"metric {key} score must be an integer from 1 to 5")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"metric {key} evidence is empty")
        clean[key] = {"score": score, "evidence": " ".join(evidence.splitlines()).strip()}
    return clean


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def sol_score(prompt: str) -> tuple[dict[str, Any], int]:
    """Primary scorer since 2026-09-13 (owner): Sol via nsft.engines.run_sol; Opus is never used unless SCORER=opus is set explicitly."""
    import tempfile, os as _os
    from nsft.engines import run_sol
    errors = []
    for attempt in range(1, 4):
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, prefix="score_sol_") as tmp:
                out_path = tmp.name
            rc, stderr_tail = run_sol(prompt, out_path, timeout=900)
            body = open(out_path, encoding="utf-8").read(); _os.unlink(out_path)
            result = lenient_json(body)
            if not isinstance(result, dict):
                raise ValueError("Sol returned non-object JSON")
            result["_engine"] = "sol"
            return result, attempt
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            time.sleep(2 ** attempt)
    raise RuntimeError("Sol scoring failed three times: " + " | ".join(errors))


SCORER = os.environ.get("SCORER", "sol")


def score_conversations(
    *,
    out_dir: Path,
    caller: Callable[[str], tuple[dict[str, Any], int]] = None,
    limit: int | None = None,
) -> tuple[Path, Path]:
    if caller is None:
        caller = opus_score if SCORER == "opus" else sol_score
    completed_path = out_dir / "turn3.jsonl"
    rows = read_jsonl(completed_path)
    rows_by_id(rows, str(completed_path))
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1")
        rows = rows[:limit]

    transcripts = []
    scored_rows = []
    for index, row in enumerate(rows, 1):
        validate_transcript(row, 3)
        if not isinstance(row.get("moves"), list) or len(row["moves"]) != 2:
            raise ValueError(f"invalid moves for {row.get('id', '<unknown>')}")
        transcript = transcript_view(row)
        result, attempts = caller(build_prompt(transcript))
        metrics = validate_score(result)
        transcripts.append(transcript)
        scored_rows.append(
            {
                "id": transcript["id"],
                "lang": transcript["lang"],
                "moves": transcript["moves"],
                "metrics": metrics,
                "engine": SCORER,
                "attempts": attempts,
            }
        )
        print(f"scorer {index}/{len(rows)} id={row['id']} engine={SCORER}", flush=True)

    averages = {
        key: sum(item["metrics"][key]["score"] for item in scored_rows) / len(scored_rows)
        for key in RUBRIC
    }
    scores_document = {
        "schema_version": 1,
        "rubric_scale": {"min": 1, "max": 5},
        "rubric": RUBRIC,
        "count": len(scored_rows),
        "averages": averages,
        "scores": scored_rows,
    }
    transcripts_path = out_dir / "transcripts.jsonl"
    scores_path = out_dir / "scores.json"
    write_jsonl(transcripts_path, transcripts)
    write_json(scores_path, scores_document)
    print(f"wrote {len(transcripts)} transcripts: {transcripts_path}")
    print(f"wrote {len(scored_rows)} scores: {scores_path}")
    return transcripts_path, scores_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out-dir", help="override results/<run>/interviews")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        out_dir = resolve_out_dir(args.run, args.out_dir)
        score_conversations(out_dir=out_dir, limit=args.limit)
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
