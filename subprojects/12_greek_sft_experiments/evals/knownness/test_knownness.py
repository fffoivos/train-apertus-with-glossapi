#!/usr/bin/env python3
"""Dependency-free tests for the knownness decision logic."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from corpus_presence import AhoCorasick, corpus_records, document_text, normalize
from make_questions import (
    contains_greek as generation_prompt_contains_greek,
    prompt_for_batch,
    validate_response,
)
from score_claims import aggregate_rows, build_prompt, normalized_contains, score_records


def claim(
    claim_id: str,
    row_key: str,
    row_index: int,
    claim_index: int,
    question: str,
    gold: str,
) -> dict[str, object]:
    source, row_id, occurrence = row_key.split(":")
    return {
        "claim_id": claim_id,
        "row_key": row_key,
        "row_index": row_index,
        "row_occurrence": int(occurrence),
        "source": source,
        "row_id": row_id,
        "claim_index": claim_index,
        "claim": f"Synthetic claim {claim_id}",
        "kind": "test",
        "basis": "known",
        "language": "en",
        "question": question,
        "gold": gold,
        "entities": [gold],
        "corpus_presence": None,
    }


def fake_model(prompts: list[str]) -> list[tuple[str, list[str]]]:
    outputs: list[tuple[str, list[str]]] = []
    for prompt in prompts:
        if "Q-KNOWN-ONE" in prompt:
            outputs.append(("Blue.", ["Blue", "Blue", "Blue", "Blue"]))
        elif "Q-WEAK" in prompt:
            outputs.append(("Orange", ["Violet", "Green", "Deep blue", "White"]))
        elif "Q-KNOWN-TWO" in prompt:
            outputs.append(("The short answer is seven.", ["Seven"] * 4))
        elif "Q-UNKNOWN-ONE" in prompt:
            outputs.append(("North", ["South", "East", "West", "North"]))
        elif "Q-UNKNOWN-TWO" in prompt:
            outputs.append(("Copper", ["Tin", "Iron", "Gold", "Silver"]))
        else:
            raise AssertionError("unexpected prompt")
    return outputs


def test_knownness() -> None:
    records = [
        claim("c0", "unit:r0:0", 0, 0, "Q-KNOWN-ONE", "blue"),
        claim("c1", "unit:r0:0", 0, 1, "Q-WEAK", "deep blue"),
        claim("c2", "unit:r1:0", 1, 0, "Q-KNOWN-TWO", "seven"),
        claim("c3", "unit:r1:0", 1, 1, "Q-UNKNOWN-ONE", "centre"),
        claim("c4", "unit:r2:0", 2, 0, "Q-UNKNOWN-TWO", "platinum"),
    ]
    scored = score_records(records, fake_model, batch_size=2)
    assert [row["knowledge_label"] for row in scored] == [
        "known", "weakly_known", "known", "unknown", "unknown"
    ]
    universe = [
        {"source": "unit", "row_id": "r0"},
        {"source": "unit", "row_id": "r1"},
        {"source": "unit", "row_id": "r2"},
        {"source": "unit", "row_id": "r3"},
    ]
    rows = aggregate_rows(scored, universe)
    assert {row["row_id"]: row["knownness"] for row in rows} == {
        "r0": "known", "r1": "mixed", "r2": "unknown", "r3": "none"
    }
    assert normalized_contains("  ATHÍNA! ", "athina")
    assert not normalized_contains("twelve", "two")
    assert "Q-KNOWN-ONE" in build_prompt("en", "Q-KNOWN-ONE")
    french_prompt = prompt_for_batch("fr", [{"claim_id": "synthetic", "claim": "Un fait synthétique."}])
    assert not generation_prompt_contains_greek(french_prompt)

    patterns = [normalize("Alpha Entity"), normalize("Beta")]
    matcher = AhoCorasick(patterns)
    assert matcher.find(normalize("Beta and Alpha Entity occur here.")) == {0, 1}
    assert matcher.find(normalize("Nothing relevant.")) == set()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        corpus_path = root / "corpus.jsonl"
        corpus_path.write_text(
            json.dumps({"text": "Alpha Entity and Beta share this synthetic document."}) + "\n"
            + json.dumps({"text": "An unrelated synthetic document."}) + "\n",
            encoding="utf-8",
        )
        args = SimpleNamespace(corpus_glob=str(corpus_path))
        corpus = list(corpus_records(args))
        assert len(corpus) == 2
        assert matcher.find(normalize(document_text(corpus[0], "text"))) == {0, 1}

        response_path = root / "strict.json"
        response_path.write_text(
            json.dumps(
                {"items": [{"id": "synthetic", "question": "Question?", "answer": "Answer", "entities": ["Entity"]}]}
            ),
            encoding="utf-8",
        )
        assert validate_response(response_path, ["synthetic"])[0]["answer"] == "Answer"


def main() -> None:
    test_knownness()
    print("OK")


if __name__ == "__main__":
    main()
