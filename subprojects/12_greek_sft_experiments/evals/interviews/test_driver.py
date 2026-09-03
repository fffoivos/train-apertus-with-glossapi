#!/usr/bin/env python3
"""Offline end-to-end test for the unseen-interviews workflow."""

from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True

import driver
import interviewer
import score


HERE = Path(__file__).resolve().parent


def read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def check_production_seeds() -> None:
    rows = driver.read_jsonl(HERE / "seeds.jsonl")
    driver.validate_seeds(rows)
    assert len(rows) == 40
    assert Counter(row["lang"] for row in rows) == {"el": 10, "en": 10, "fr": 10, "de": 10}
    assert all(row.get("draft_by") == "sol" for row in rows)

    move_counts: Counter[str] = Counter()
    source_switches: Counter[str] = Counter()
    target_switches: Counter[str] = Counter()
    for row in rows:
        for move in row["moves"]:
            kind = "switch" if move.startswith("switch:") else move
            move_counts[kind] += 1
            if kind == "switch":
                source_switches[row["lang"]] += 1
                target_switches[move.split(":", 1)[1]] += 1
    expected = {
        "challenge_true",
        "challenge_false",
        "clarify_shorter",
        "clarify_format",
        "localise",
        "switch",
        "stretch",
    }
    assert set(move_counts) == expected
    assert all(move_counts[kind] >= 8 for kind in expected)
    assert all(source_switches[language] >= 2 for language in driver.LANGUAGES)
    assert all(target_switches[language] >= 2 for language in driver.LANGUAGES)


def fake_interviewer(prompt: str) -> tuple[dict, str, int]:
    match = re.search(r'"required_output_language":"(el|en|fr|de)"', prompt)
    assert match, prompt
    language = match.group(1)
    return {"followup": f"follow-up question in {language}?", "target_lang": language}, "fake", 1


def fake_scorer(prompt: str) -> tuple[dict, int]:
    assert "run-under-test" not in prompt
    return {
        "metrics": {
            key: {"score": 4, "evidence": f"Evidence for {key}."} for key in score.RUBRIC
        }
    }, 1


def check_prompt_guards() -> None:
    row = {
        "lang": "el",
        "turns": [
            {"role": "user", "content": "Greek-script placeholder: δοκιμή"},
            {"role": "assistant", "content": "Greek-script placeholder: απάντηση"},
        ],
    }
    switch_prompt = interviewer.build_prompt(row, "switch:en")
    assert not re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", switch_prompt)
    false_prompt = interviewer.build_prompt(row, "challenge_false")
    assert "deliberately false correction" in false_prompt
    assert "Do not answer" in false_prompt and "Do not grade" in false_prompt


def run_end_to_end() -> None:
    test_seeds = [
        {
            "id": f"seed-{index}",
            "lang": language,
            "opener": f"Placeholder question {index}?",
            "moves": ["challenge_false", switch],
            "draft_by": "sol",
        }
        for index, (language, switch) in enumerate(
            [("el", "switch:en"), ("en", "switch:fr"), ("fr", "switch:de"), ("de", "switch:el")],
            1,
        )
    ]
    with tempfile.TemporaryDirectory(prefix="interviews-test-") as temporary:
        root = Path(temporary)
        seeds_path = root / "seeds.jsonl"
        out_dir = root / "run-under-test" / "interviews"
        driver.write_jsonl(seeds_path, test_seeds)
        echo = driver.EchoGenerator()

        driver.run_round(
            seeds_path=seeds_path, round_number=1, out_dir=out_dir, generator=echo
        )
        interviewer.generate_followups(turn=2, out_dir=out_dir, caller=fake_interviewer)
        driver.run_round(
            seeds_path=seeds_path, round_number=2, out_dir=out_dir, generator=echo
        )
        interviewer.generate_followups(turn=3, out_dir=out_dir, caller=fake_interviewer)
        driver.run_round(
            seeds_path=seeds_path, round_number=3, out_dir=out_dir, generator=echo
        )
        transcripts_path, scores_path = score.score_conversations(
            out_dir=out_dir, caller=fake_scorer
        )

        expected_files = [
            out_dir / "turn1.jsonl",
            out_dir / "followups2.jsonl",
            out_dir / "turn2.jsonl",
            out_dir / "followups3.jsonl",
            out_dir / "turn3.jsonl",
            transcripts_path,
            scores_path,
        ]
        assert all(path.is_file() for path in expected_files)
        assert all(len(read_lines(path)) == 4 for path in expected_files[:-1])

        transcripts = read_lines(transcripts_path)
        for transcript in transcripts:
            assert set(transcript) == {"id", "lang", "turns", "moves"}
            assert len(transcript["turns"]) == 6
            assert [turn["role"] for turn in transcript["turns"]] == [
                "user",
                "assistant",
                "user",
                "assistant",
                "user",
                "assistant",
            ]
            assert len(transcript["moves"]) == 2

        scores = json.loads(scores_path.read_text(encoding="utf-8"))
        assert scores["count"] == 4
        assert len(scores["scores"]) == 4
        assert set(scores["averages"]) == set(score.RUBRIC)


def main() -> None:
    check_production_seeds()
    check_prompt_guards()
    with redirect_stdout(io.StringIO()):
        run_end_to_end()
    print("OK")


if __name__ == "__main__":
    main()
