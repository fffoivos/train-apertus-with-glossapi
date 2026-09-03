#!/usr/bin/env python3
"""End-to-end local checks for the dev harness, with no model or dataset access."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "evals" / "dev"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def fake_rows(run_variant: str) -> list[dict[str, Any]]:
    rows = []
    greek_answer = ("Καθαρή φυσική απάντηση με σκέψη και ακρίβεια. " * 90).strip()
    foreign_answer = ("A clear direct answer with careful reasoning and concrete detail. " * 40).strip()
    for index in range(40):
        language = "el" if index < 28 else ("en" if index < 34 else "fr" if index < 37 else "de")
        if language == "el":
            prompt = "Σύντομη δοκιμαστική ερώτηση."
            answer = greek_answer + f" Παραλλαγή {run_variant}."
        elif language == "en":
            prompt = "A short synthetic question."
            answer = foreign_answer + f" Variant {run_variant}."
        elif language == "fr":
            prompt = "Une courte question artificielle."
            answer = foreign_answer + f" Variante {run_variant}."
        else:
            prompt = "Eine kurze synthetische Frage."
            answer = foreign_answer + f" Variante {run_variant}."
        row: dict[str, Any] = {
            "prompt_id": f"prompt-{index:02d}",
            "config": f"fake-{index % 11}",
            "language": language,
            "messages": [{"role": "user", "content": prompt}],
            "text": answer,
            "raw_text": answer + "<|assistant_end|>",
            "stop_reason": "assistant_end",
            "prompt_tokens": 8,
            "generated_tokens": 64,
        }
        if index == 0:
            row["transcript"] = [
                {"role": "user", "content": "Πρώτη ερώτηση."},
                {"role": "assistant", "content": "Πρώτη απάντηση."},
                {"role": "user", "content": "Διευκρίνιση."},
                {"role": "assistant", "content": "Δεύτερη απάντηση."},
                {"role": "user", "content": "Τελική ερώτηση."},
                {"role": "assistant", "content": "Τρίτη απάντηση."},
            ]
        rows.append(row)
    return rows


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="wp1c-test-") as temp_name:
        temp = Path(temp_name)
        run_a = temp / "run_a"
        run_b = temp / "run_b"
        run_a.mkdir()
        run_b.mkdir()
        gen_a = run_a / "dev_gen.jsonl"
        gen_b = run_b / "dev_gen.jsonl"
        write_jsonl(gen_a, fake_rows("A"))
        write_jsonl(gen_b, fake_rows("B"))

        gate = run(str(DEV / "format_gate.py"), str(gen_a))
        assert gate.stdout.startswith("PASS "), gate.stdout
        gate_report = json.loads((run_a / "format_gate.json").read_text(encoding="utf-8"))
        assert gate_report["passed"] is True
        assert all(value == 1.0 for value in gate_report["metrics"].values())

        reference = temp / "no_robots.jsonl"
        reference_rows = [
            {
                "row_id": f"reference-{index:02d}",
                "el_messages": [
                    {
                        "role": "assistant",
                        "content": (
                            "Φυσική απάντηση με σαφή σκέψη ακρίβεια ρυθμό και συγκεκριμένη ουσία. "
                            * 120
                        ).strip(),
                    }
                ],
            }
            for index in range(20)
        ]
        write_jsonl(reference, reference_rows)
        voice = run(str(DEV / "voice_score.py"), str(gen_a), "--reference", str(reference))
        assert voice.stdout.startswith("Delta="), voice.stdout
        voice_report = json.loads((run_a / "voice.json").read_text(encoding="utf-8"))
        assert voice_report["delta"]["generated_vs_no_robots"] >= 0
        assert voice_report["delta"]["parroting_floor_reference_split_half"] >= 0
        assert "generated" in voice_report["biber_style_rates_per_1000_words"]

        page = temp / "reading.html"
        result = run(
            str(DEV / "reading_page.py"),
            "--runs",
            str(gen_a),
            str(gen_b),
            "--out",
            str(page),
        )
        assert "prompts=40 runs=2" in result.stdout
        html = page.read_text(encoding="utf-8")
        assert "localStorage" in html and "Save + JSON" in html
        assert all(flag in html for flag in ("not Greek", "American underneath", "wrong fact"))
        assert "RUN_MAP" in html and '"run_a"' in html and '"run_b"' in html
        assert html.count("Τρίτη απάντηση.") == 2
        assert "https://fonts.googleapis.com" in html

        node = shutil.which("node")
        if node:
            scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
            assert len(scripts) == 1
            javascript = temp / "page.js"
            javascript.write_text(scripts[0], encoding="utf-8")
            checked = subprocess.run([node, "--check", str(javascript)], text=True, capture_output=True)
            assert checked.returncode == 0, checked.stderr

        dev_union = temp / "dev_all.jsonl"
        dev_rows = []
        configs = (
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
        for config in configs:
            for index in range(5):
                question = "Synthetic question" if config in configs[7:] else "Δοκιμαστική ερώτηση"
                dev_rows.append(
                    {
                        "row_id": f"{config}-{index}",
                        "config": config,
                        "category": "test",
                        "messages": [
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": "Held-out target"},
                        ],
                    }
                )
        write_jsonl(dev_union, dev_rows)
        selected = temp / "reading40.jsonl"
        run(
            str(DEV / "prompts" / "select_reading40.py"),
            "--input",
            str(dev_union),
            "--out",
            str(selected),
        )
        selected_rows = [json.loads(line) for line in selected.read_text(encoding="utf-8").splitlines()]
        assert len(selected_rows) == 40
        assert all(row["messages"][-1]["role"] == "user" for row in selected_rows)
        assert all("Held-out target" not in json.dumps(row) for row in selected_rows)

        dry = run(
            str(DEV / "dev_generate.py"),
            "--dry-run",
            "--model",
            "x",
            "--prompts",
            str(DEV / "prompts" / "reading40.jsonl"),
        )
        assert "DRY RUN OK" in dry.stdout
    print("OK")


if __name__ == "__main__":
    main()
