#!/usr/bin/env python3
"""Turn reality claims into short-answer knowledge questions with Sol.

The cache key covers the prompt version, language, and exact batch payload.  A
cached response is reused only after it passes the same strict validation as a
new response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PROMPT_VERSION = "knownness-questions-v1"
DEFAULT_CLAIMS = Path.home() / "Projects/natural-greek-sft/data/exports/reality_claims.jsonl"
DEFAULT_CACHE = Path(__file__).resolve().parent / "cache"
LANGUAGE_BY_SOURCE = {
    "apertus_en": "en",
    "no_robots_en_pov": "en",
    "euroblocks_fr": "fr",
    "euroblocks_de": "de",
}
LANGUAGE_NAMES = {"el": "Greek", "en": "English", "fr": "French", "de": "German"}


def contains_greek(text: str) -> bool:
    return any("\u0370" <= char <= "\u03ff" or "\u1f00" <= char <= "\u1fff" for char in text)


def run_sol(prompt_text: str, out_path: str | os.PathLike[str], timeout: int = 1800) -> tuple[int, str]:
    """Run Sol in a neutral directory and write only its final response."""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "codex", "exec", "-m", "gpt-5.6-sol",
        "-c", "model_reasoning_effort=medium",
        "-c", "project_doc_max_bytes=0",
        "--skip-git-repo-check", "--ephemeral", "-o", str(target), "-",
    ]
    try:
        completed = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/tmp",
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "Sol call timed out"
    return completed.returncode, (completed.stderr or "")[-600:]


def language_for_source(source: str) -> str:
    return LANGUAGE_BY_SOURCE.get(source, "el")


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    occurrences: Counter[tuple[str, str]] = Counter()
    with path.open(encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            source = row.get("source")
            row_id = row.get("row_id")
            claims = row.get("claims")
            if not isinstance(source, str) or not isinstance(row_id, str) or not isinstance(claims, list):
                raise ValueError(f"invalid claims row at input line {row_index + 1}")
            pair = (source, row_id)
            occurrence = occurrences[pair]
            occurrences[pair] += 1
            row_key = f"{source}:{row_id}:{occurrence}"
            for claim_index, item in enumerate(claims):
                if not isinstance(item, dict):
                    raise ValueError(f"invalid claim at input line {row_index + 1}")
                claim = item.get("claim")
                basis = item.get("basis")
                kind = item.get("kind")
                if not isinstance(claim, str) or not claim.strip():
                    raise ValueError(f"empty claim at input line {row_index + 1}")
                if basis not in {"known", "inferred", "uncertain"} or not isinstance(kind, str):
                    raise ValueError(f"invalid claim metadata at input line {row_index + 1}")
                rows.append(
                    {
                        "claim_id": f"{row_key}:{claim_index}",
                        "row_key": row_key,
                        "row_index": row_index,
                        "row_occurrence": occurrence,
                        "source": source,
                        "row_id": row_id,
                        "claim_index": claim_index,
                        "claim": claim.strip(),
                        "kind": kind,
                        "basis": basis,
                        "language": language_for_source(source),
                    }
                )
    return rows


def prompt_for_batch(language: str, claims: list[dict[str, Any]]) -> str:
    language_name = LANGUAGE_NAMES[language]
    instructions = {
        "el": (
            "Μετέτρεψε κάθε ισχυρισμό σε μία ερώτηση γνώσεων και μία σύντομη χρυσή απάντηση. "
            "Η ερώτηση και η απάντηση πρέπει να είναι στα Ελληνικά. Η απάντηση πρέπει να είναι "
            "η ελάχιστη φράση που αρκεί για αυτόματο έλεγχο. Εξήγαγε επίσης τα κύρια ονόματα, "
            "τοπωνύμια, οργανισμούς, τίτλους ή διακριτούς αριθμούς που είναι απαραίτητα για τον "
            "ισχυρισμό. Μην προσθέσεις γνώσεις και μην εξηγήσεις την απάντηση."
        ),
        "en": (
            "Turn each claim into one factual question and one short gold answer. The question "
            "and answer must be in English. Make the answer the shortest phrase sufficient for "
            "automatic checking. Also extract the key named people, places, organizations, titles, "
            "or distinctive numbers needed by the claim. Add no facts and give no explanation."
        ),
        "fr": (
            "Transformez chaque affirmation en une question factuelle et une réponse de référence "
            "courte. La question et la réponse doivent être en français. La réponse doit être la "
            "formulation minimale permettant une vérification automatique. Extrayez aussi les noms "
            "de personnes, lieux, organismes, titres ou nombres distinctifs indispensables. "
            "N'ajoutez aucun fait et ne donnez aucune explication."
        ),
        "de": (
            "Forme jede Behauptung in eine Faktenfrage und eine kurze Musterantwort um. Frage und "
            "Antwort müssen auf Deutsch sein. Die Antwort soll die kürzeste für eine automatische "
            "Prüfung ausreichende Formulierung sein. Extrahiere außerdem die wesentlichen Namen, "
            "Orte, Organisationen, Titel oder markanten Zahlen. Füge keine Fakten und keine "
            "Erklärung hinzu."
        ),
    }[language]
    schema = (
        'Return strict JSON only, with exactly this shape: '
        '{"items":[{"id":"...","question":"...","answer":"...","entities":["..."]}]}. '
        "Return one item for every input id, in input order. Do not use Markdown."
    )
    # The schema is deliberately ASCII/English for every language; it contains no
    # Greek script and therefore cannot leak Greek into French/German/English jobs.
    payload = [{"id": item["claim_id"], "claim": item["claim"]} for item in claims]
    prompt = f"{instructions}\n\nOutput language: {language_name}.\n{schema}\n\nInput:\n"
    prompt += json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if language != "el" and contains_greek(prompt):
        raise ValueError(f"Greek script found in {language} question-generation prompt")
    return prompt


def validate_response(path: Path, expected_ids: list[str]) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"response is not strict JSON: {exc}") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"items"} or not isinstance(parsed["items"], list):
        raise ValueError('response root must be exactly {"items": [...]}')
    items = parsed["items"]
    if len(items) != len(expected_ids):
        raise ValueError(f"expected {len(expected_ids)} items, got {len(items)}")
    for expected_id, item in zip(expected_ids, items):
        if not isinstance(item, dict) or set(item) != {"id", "question", "answer", "entities"}:
            raise ValueError("response item has wrong keys")
        if item["id"] != expected_id:
            raise ValueError("response ids are missing, duplicated, or out of order")
        if not isinstance(item["question"], str) or not item["question"].strip():
            raise ValueError(f"empty question for {expected_id}")
        if not isinstance(item["answer"], str) or not item["answer"].strip():
            raise ValueError(f"empty answer for {expected_id}")
        entities = item["entities"]
        if not isinstance(entities, list) or any(not isinstance(x, str) or not x.strip() for x in entities):
            raise ValueError(f"invalid entities for {expected_id}")
        item["question"] = item["question"].strip()
        item["answer"] = item["answer"].strip()
        item["entities"] = list(dict.fromkeys(x.strip() for x in entities))
    return items


def batched(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def cache_path(cache_dir: Path, language: str, prompt: str) -> Path:
    digest = hashlib.sha256((PROMPT_VERSION + "\0" + prompt).encode("utf-8")).hexdigest()
    return cache_dir / f"{language}-{digest}.json"


def atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--limit", type=int, default=None, help="maximum number of claims")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size < 1 or args.batch_size > 20:
        raise SystemExit("ERROR: --batch-size must be between 1 and 20")
    if args.limit is not None and args.limit < 0:
        raise SystemExit("ERROR: --limit must be non-negative")
    if not args.claims.is_file():
        raise SystemExit(f"ERROR: claims file not found: {args.claims}")
    claims = load_rows(args.claims)
    if args.limit is not None:
        claims = claims[: args.limit]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        grouped[claim["language"]].append(claim)
    print(
        json.dumps(
            {
                "claims": len(claims),
                "by_language": {key: len(value) for key, value in sorted(grouped.items())},
                "batch_size": args.batch_size,
                "cache_dir": str(args.cache_dir),
                "out": str(args.out),
                "dry_run": args.dry_run,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if args.dry_run:
        return 0

    generated: dict[str, dict[str, Any]] = {}
    total_batches = sum((len(group) + args.batch_size - 1) // args.batch_size for group in grouped.values())
    completed_batches = 0
    for language in ("el", "en", "fr", "de"):
        for batch in batched(grouped.get(language, []), args.batch_size):
            prompt = prompt_for_batch(language, batch)
            cached = cache_path(args.cache_dir, language, prompt)
            expected_ids = [item["claim_id"] for item in batch]
            try:
                responses = validate_response(cached, expected_ids)
                status = "cached"
            except ValueError:
                rc, stderr = run_sol(prompt, cached, timeout=args.timeout)
                if rc != 0:
                    raise SystemExit(f"ERROR: Sol failed rc={rc}: {stderr}")
                try:
                    responses = validate_response(cached, expected_ids)
                except ValueError as exc:
                    raise SystemExit(f"ERROR: invalid Sol response {cached.name}: {exc}") from exc
                status = "generated"
            for item in responses:
                generated[item["id"]] = item
            completed_batches += 1
            print(f"batch={completed_batches}/{total_batches} language={language} status={status}", flush=True)

    output: list[dict[str, Any]] = []
    for claim in claims:
        response = generated[claim["claim_id"]]
        output.append(
            {
                **claim,
                "question": response["question"],
                "gold": response["answer"],
                "entities": response["entities"],
                "question_generator": "gpt-5.6-sol",
                "prompt_version": PROMPT_VERSION,
            }
        )
    atomic_write_jsonl(args.out, output)
    print(f"wrote {len(output)} questions to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from None
