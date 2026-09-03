#!/usr/bin/env python3
"""Count corpus documents containing all key entities for each claim."""

from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import os
import tempfile
import time
import unicodedata
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Iterator


DEFAULT_DATASET = "fffoivos/apertus-8b-greek-cpt-modern-greek-train"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(text.split())


class AhoCorasick:
    """Small dependency-free multi-pattern matcher."""

    def __init__(self, patterns: list[str]):
        self.goto: list[dict[str, int]] = [{}]
        self.fail: list[int] = [0]
        self.output: list[list[int]] = [[]]
        for pattern_id, pattern in enumerate(patterns):
            state = 0
            for char in pattern:
                if char not in self.goto[state]:
                    self.goto[state][char] = self._new_state()
                state = self.goto[state][char]
            self.output[state].append(pattern_id)
        queue: deque[int] = deque()
        for state in self.goto[0].values():
            queue.append(state)
        while queue:
            current = queue.popleft()
            for char, nxt in self.goto[current].items():
                queue.append(nxt)
                fallback = self.fail[current]
                while fallback and char not in self.goto[fallback]:
                    fallback = self.fail[fallback]
                self.fail[nxt] = self.goto[fallback].get(char, 0)
                self.output[nxt].extend(self.output[self.fail[nxt]])

    def _new_state(self) -> int:
        self.goto.append({})
        self.fail.append(0)
        self.output.append([])
        return len(self.goto) - 1

    def find(self, text: str) -> set[int]:
        found: set[int] = set()
        state = 0
        for char in text:
            while state and char not in self.goto[state]:
                state = self.fail[state]
            state = self.goto[state].get(char, 0)
            found.update(self.output[state])
        return found


def load_questions(path: Path, limit: int | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    if limit == 0:
        return records
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            claim_id = row.get("claim_id")
            entities = row.get("entities")
            if not isinstance(claim_id, str) or claim_id in seen:
                raise ValueError(f"invalid or duplicate claim_id at line {line_number}")
            if not isinstance(entities, list) or any(not isinstance(x, str) for x in entities):
                raise ValueError(f"invalid entities at line {line_number}")
            seen.add(claim_id)
            records.append(row)
            if limit is not None and len(records) >= limit:
                break
    return records


def flatten_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from flatten_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from flatten_strings(nested)


def dotted_value(record: dict[str, Any], field: str) -> Any:
    value: Any = record
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(field)
        value = value[part]
    return value


def document_text(record: Any, text_field: str | None) -> str:
    if isinstance(record, str):
        return record
    if not isinstance(record, dict):
        return ""
    if text_field:
        value = dotted_value(record, text_field)
        return "\n".join(flatten_strings(value))
    for candidate in ("text", "content", "document", "raw_text"):
        if candidate in record:
            return "\n".join(flatten_strings(record[candidate]))
    return "\n".join(flatten_strings(record))


def iter_jsonl(path: str) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"bad JSON in {path}:{line_number}: {exc}") from exc


def corpus_records(args: argparse.Namespace) -> Iterable[Any]:
    if args.corpus_glob:
        paths = sorted(glob.glob(args.corpus_glob, recursive=True))
        if not paths:
            raise ValueError(f"--corpus-glob matched no files: {args.corpus_glob}")
        jsonl = [path for path in paths if path.endswith((".jsonl", ".jsonl.gz"))]
        if len(jsonl) == len(paths):
            def chained() -> Iterator[dict[str, Any]]:
                for path in paths:
                    yield from iter_jsonl(path)
            return chained()
        suffixes = {Path(path.removesuffix(".gz")).suffix.lower() for path in paths}
        builders = {".json": "json", ".jsonl": "json", ".parquet": "parquet", ".txt": "text"}
        if len(suffixes) != 1 or next(iter(suffixes)) not in builders:
            raise ValueError("--corpus-glob must resolve to one supported type: jsonl, json, parquet, or txt")
        from datasets import load_dataset

        return load_dataset(builders[next(iter(suffixes))], data_files=paths, split="train", streaming=True)

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from datasets import load_dataset

    kwargs: dict[str, Any] = {"split": args.split, "streaming": True}
    if args.dataset_config:
        kwargs["name"] = args.dataset_config
    return load_dataset(args.dataset, **kwargs)


def selected_for_sample(text: str, index: int, fraction: float, seed: int) -> bool:
    if fraction >= 1.0:
        return True
    prefix = f"{seed}\0{index}\0".encode("ascii")
    digest = hashlib.blake2b(prefix + text[:512].encode("utf-8", "ignore"), digest_size=8).digest()
    value = int.from_bytes(digest, "big") / 2**64
    return value < fraction


def atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-config")
    parser.add_argument("--split", default="train")
    parser.add_argument("--corpus-glob")
    parser.add_argument("--text-field")
    parser.add_argument("--sample-fraction", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 < args.sample_fraction <= 1:
        raise SystemExit("ERROR: --sample-fraction must be in (0, 1]")
    if not args.questions.is_file():
        raise SystemExit(f"ERROR: questions file not found: {args.questions}")
    questions = load_questions(args.questions, args.limit)
    entity_values = sorted(
        {
            normalized
            for row in questions
            for entity in row["entities"]
            if (normalized := normalize(entity))
        }
    )
    print(
        json.dumps(
            {
                "questions": len(questions),
                "unique_entities": len(entity_values),
                "source": args.corpus_glob or args.dataset,
                "split": args.split,
                "sample_fraction_requested": args.sample_fraction,
                "out": str(args.out),
                "dry_run": args.dry_run,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if args.dry_run:
        return 0

    pattern_id = {value: index for index, value in enumerate(entity_values)}
    required: list[frozenset[int]] = []
    entity_to_claims: dict[int, set[int]] = {index: set() for index in range(len(entity_values))}
    for claim_index, row in enumerate(questions):
        ids = frozenset(pattern_id[value] for entity in row["entities"] if (value := normalize(entity)))
        required.append(ids)
        for entity_id in ids:
            entity_to_claims[entity_id].add(claim_index)

    matcher = AhoCorasick(entity_values)
    observed = [0] * len(questions)
    seen_docs = selected_docs = 0
    started = last_heartbeat = time.monotonic()
    for index, record in enumerate(corpus_records(args)):
        try:
            raw_text = document_text(record, args.text_field)
        except KeyError:
            raise SystemExit(f"ERROR: text field not found: {args.text_field}")
        seen_docs += 1
        if selected_for_sample(raw_text, index, args.sample_fraction, args.seed):
            selected_docs += 1
            matched = matcher.find(normalize(raw_text)) if entity_values else set()
            candidates: set[int] = set()
            for entity_id in matched:
                candidates.update(entity_to_claims[entity_id])
            for claim_index in candidates:
                if required[claim_index] and required[claim_index].issubset(matched):
                    observed[claim_index] += 1
        now = time.monotonic()
        if now - last_heartbeat >= 60:
            print(f"HB step={seen_docs} loss=na tok/s=na mem=na", flush=True)
            last_heartbeat = now

    actual_fraction = selected_docs / seen_docs if seen_docs else 0.0
    outputs: list[dict[str, Any]] = []
    for row, count, needed in zip(questions, observed, required):
        scaled = round(count / actual_fraction) if actual_fraction and needed else 0
        outputs.append(
            {
                "claim_id": row["claim_id"],
                "doc_count": scaled,
                "sampled_fraction": actual_fraction,
                "observed_doc_count": count,
                "entities": row["entities"],
                "entity_match_rule": "all_normalized_entities_in_same_document",
                "documents_scanned": seen_docs,
                "sampled_documents": selected_docs,
                "sample_seed": args.seed,
            }
        )
    atomic_jsonl(args.out, outputs)
    elapsed = time.monotonic() - started
    print(
        f"wrote {len(outputs)} claims to {args.out}; docs_seen={seen_docs} "
        f"docs_sampled={selected_docs} sampled_fraction={actual_fraction:.8f} seconds={elapsed:.1f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from None
