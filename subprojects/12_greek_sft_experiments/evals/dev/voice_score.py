#!/usr/bin/env python3
"""Score Greek dev generations against the no_robots-el reference voice."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
from pathlib import Path
from typing import Any, Iterable, NoReturn

DEFAULT_STYLE_SCRIPT = (
    Path.home() / "Projects" / "natural-greek-sft" / "scripts" / "style_compare.py"
)
HF_DATASET = "fffoivos/Greek-SFT-translated-and-adapted"
HF_CONFIG = "no_robots"


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        fail(f"JSONL file not found: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                fail(f"invalid JSON at {path}:{line_number}: {exc.msg}")
    return rows


def load_style_module(path: Path):
    if not path.is_file():
        fail(f"natural-greek-sft stylometry script not found: {path}")
    spec = importlib.util.spec_from_file_location("natural_greek_style_compare", path)
    if spec is None or spec.loader is None:
        fail(f"cannot import stylometry script: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        fail(f"cannot import stylometry script {path}: {exc}")
    required = ("clean", "features", "words", "chunks", "delta_frame", "centroid", "delta")
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        fail(f"stylometry script lacks required functions: {', '.join(missing)}")
    return module


def assistant_turns(rows: Iterable[dict[str, Any]], field: str = "el_messages") -> list[str]:
    turns: list[str] = []
    for row in rows:
        messages = row.get(field)
        if not isinstance(messages, list):
            continue
        for message in messages:
            if (
                isinstance(message, dict)
                and message.get("role") == "assistant"
                and isinstance(message.get("content"), str)
            ):
                turns.append(message["content"])
    return turns


def load_reference(path: Path | None) -> tuple[list[str], str]:
    if path is not None:
        rows = read_jsonl(path)
        return assistant_turns(rows), str(path)
    try:
        from datasets import DatasetDict, load_dataset

        loaded = load_dataset(HF_DATASET, HF_CONFIG, token=True)
        if isinstance(loaded, DatasetDict):
            rows = (row for split in loaded.values() for row in split)
        else:
            rows = iter(loaded)
        return assistant_turns(rows), f"hf://datasets/{HF_DATASET}/{HF_CONFIG}"
    except Exception as exc:
        fail(f"could not load HF no_robots reference (use --reference for an export): {exc}")


def generated_greek(rows: list[dict[str, Any]]) -> list[str]:
    texts = []
    for row in rows:
        if row.get("language") != "el":
            continue
        text = row.get("text")
        if not isinstance(text, str):
            text = str(row.get("raw_text", "")).replace("<|assistant_end|>", "")
        if text.strip():
            texts.append(text)
    return texts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generations", type=Path)
    parser.add_argument(
        "--reference",
        type=Path,
        help="Local no_robots JSONL export; default is the private HF no_robots config",
    )
    parser.add_argument("--style-script", type=Path, default=DEFAULT_STYLE_SCRIPT)
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()

    style = load_style_module(args.style_script.expanduser())
    generation_rows = read_jsonl(args.generations)
    generated = [style.clean(text) for text in generated_greek(generation_rows)]
    reference, reference_source = load_reference(args.reference)
    reference = [style.clean(text) for text in reference if text.strip()]
    if not generated:
        fail("no non-empty Greek generations found")
    if len(reference) < 2:
        fail("reference needs at least two assistant turns")

    shuffled = list(reference)
    random.Random(args.seed).shuffle(shuffled)
    half = len(shuffled) // 2
    corpora = {
        "reference_a": style.chunks(shuffled[:half], 1000),
        "reference_b": style.chunks(shuffled[half:], 1000),
        "generated": style.chunks(generated, 1000),
    }
    empty = [name for name, chunks in corpora.items() if not chunks]
    if empty:
        counts = {
            "reference_a": sum(len(style.words(text)) for text in shuffled[:half]),
            "reference_b": sum(len(style.words(text)) for text in shuffled[half:]),
            "generated": sum(len(style.words(text)) for text in generated),
        }
        fail(f"need at least 1,000 words in each Delta corpus; word counts={counts}")

    _vocab, zscores = style.delta_frame(corpora, top=150)
    centres = {name: style.centroid(values) for name, values in zscores.items()}
    reference_centre = style.centroid(zscores["reference_a"] + zscores["reference_b"])
    floor = style.delta(centres["reference_a"], centres["reference_b"])
    distance = style.delta(centres["generated"], reference_centre)
    report = {
        "source": str(args.generations),
        "reference": reference_source,
        "method_source": str(args.style_script.expanduser()),
        "seed": args.seed,
        "n_turns": {"generated_el": len(generated), "reference_assistant": len(reference)},
        "word_counts": {
            "generated_el": sum(len(style.words(text)) for text in generated),
            "reference_assistant": sum(len(style.words(text)) for text in reference),
        },
        "delta": {
            "generated_vs_no_robots": distance,
            "parroting_floor_reference_split_half": floor,
            "below_parroting_floor": distance < floor,
            "top_words": 150,
            "chunk_words": 1000,
            "chunks": {name: len(chunks) for name, chunks in corpora.items()},
        },
        "biber_style_rates_per_1000_words": {
            "generated": style.features(generated),
            "no_robots": style.features(reference),
        },
    }
    output = args.generations.parent / "voice.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Delta={distance:.3f} parroting_floor={floor:.3f} "
        f"generated_el={len(generated)} reference_turns={len(reference)}"
    )
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
