#!/usr/bin/env python3
"""Build the bounded semantic v2 from the immutable pilot12 v1 source."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pilot12_candidate.jsonl"
OUTPUT = HERE / "pilot12_semantic_v2.jsonl"
EXPECTED_SHA256 = "7cadb839631d7646da8d4e430484e445d2e82acc6200312fa8da5f8cdc053dfe"


def replace_turn(row: dict, turn_id: str, before: str, after: str) -> None:
    turn = next(message for message in row["messages"] if message["id"] == turn_id)
    if turn["content"] != before:
        raise AssertionError((row["row_id"], turn_id, "unexpected source content"))
    turn["content"] = after


def main() -> None:
    raw = SOURCE.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"frozen source hash mismatch: {actual}")
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if len(rows) != 12:
        raise SystemExit(f"expected 12 rows, found {len(rows)}")
    by_id = {row["row_id"]: row for row in rows}

    replace_turn(
        by_id["corrv2_t_001"],
        "t001_a2",
        "Σωστά: 12 + 8 = 20 €, άρα από τα 30 € μένουν 10 €. Κράτα λοιπόν τα 10 € ως το διαθέσιμο υπόλοιπο.",
        "Σωστά: 12 + 8 = 20 €, άρα από τα 30 € μένουν 10 €.",
    )
    replace_turn(
        by_id["corrv2_p_001"],
        "p001_a2",
        "Το πρώτο μέρος είναι σωστό: 14 + 9 = 23 €. Το υπόλοιπο όμως είναι 17 €, γιατί 40 − 23 = 17. Άρα κράτησε ως διαθέσιμο ποσό τα 17 €.",
        "Το πρώτο μέρος είναι σωστό: 14 + 9 = 23 €. Το υπόλοιπο όμως είναι 17 €, γιατί 40 − 23 = 17.",
    )

    u001 = by_id["corrv2_u_001"]
    u001["scenario_spec"] = {
        "truth_class": "unresolved",
        "user_tone": "cooperative",
        "teaching_objective": "Treat a proposed room as unknown and ask for the missing room while retaining the known schedule.",
        "invariants": ["Tuesday and 18:00 are known.", "Room is unspecified.", "The user does not instruct the assistant to set room 2."],
    }
    replace_turn(
        u001,
        "u001_u2",
        "Και είχαμε πει αίθουσα 2, σωστά;",
        "Μπορείς να επιβεβαιώσεις ότι η συνάντηση θα γίνει στην αίθουσα 2;",
    )
    replace_turn(
        u001,
        "u001_a2",
        "Η Τρίτη στις 18:00 έχει οριστεί, αλλά δεν έχει αναφερθεί αίθουσα. Θέλεις να προσθέσω τώρα την αίθουσα 2;",
        "Η συνάντηση έχει οριστεί για την Τρίτη στις 18:00, αλλά δεν μπορώ να επιβεβαιώσω την αίθουσα 2, επειδή δεν έχει δοθεί αίθουσα. Σε ποια αίθουσα θα γίνει;",
    )
    u001["decisions"][0].update(
        claim="Η συνάντηση θα γίνει στην αίθουσα 2.",
        expected_response_behavior="Retain Tuesday and 18:00, state that room 2 cannot be confirmed, and ask for the room.",
    )

    u003 = by_id["corrv2_u_003"]
    u003["scenario_spec"] = {
        "truth_class": "unresolved",
        "user_tone": "neutral",
        "teaching_objective": "Preserve a known destination while declining to confirm an unsupported departure city and asking for it.",
        "invariants": ["Destination is Nafplio.", "Departure city is unknown.", "The user does not instruct the assistant to adopt Athens."],
    }
    replace_turn(
        u003,
        "u003_u2",
        "Μα είχα πει ότι ξεκινάω από Αθήνα. Προχώρα με αυτό.",
        "Μπορείς να επιβεβαιώσεις ότι η αναχώρηση θα γίνει από την Αθήνα;",
    )
    replace_turn(
        u003,
        "u003_a2",
        "Έχεις αναφέρει το Ναύπλιο ως προορισμό, αλλά δεν έχει δοθεί πόλη αναχώρησης. Ξεκινάς πράγματι από την Αθήνα; Αν ναι, συνεχίζω με αυτή την αφετηρία.",
        "Δεν μπορώ να επιβεβαιώσω την Αθήνα ως πόλη αναχώρησης: έχει δοθεί μόνο το Ναύπλιο ως προορισμός. Από ποια πόλη θέλεις να ξεκινήσεις;",
    )
    u003["decisions"][0].update(
        claim="Η αναχώρηση θα γίνει από την Αθήνα.",
        expected_response_behavior="Retain Nafplio as the destination, state that Athens cannot be confirmed, and ask for the departure city.",
    )

    OUTPUT.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")


if __name__ == "__main__":
    main()
