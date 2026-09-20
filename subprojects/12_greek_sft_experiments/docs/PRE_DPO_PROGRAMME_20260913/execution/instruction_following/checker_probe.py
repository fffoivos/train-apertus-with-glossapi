#!/usr/bin/env python3
"""Hand-built, benchmark-row-free probes for the IFBench-el words family.

This script imports the repository checker but never reads IFBench_test.jsonl or
prompts_el_final.jsonl. It distinguishes source-evaluator parity from exploratory
Greek protocol decisions; only the parity change is proposed as a patch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


GREEK_RANGE = "\u0370-\u03ff\u1f00-\u1fff"


def load_checker(project: Path):
    checker_dir = project / "data/benchmarks_el/ifbench"
    sys.path.insert(0, str(checker_dir))
    import instructions_el as current  # type: ignore
    from instructions_registry_el import INSTRUCTION_DICT  # type: ignore
    return current, INSTRUCTION_DICT


def current_check(registry, instruction_id: str, text: str, kwargs: dict) -> bool:
    inst = registry[instruction_id](instruction_id)
    inst.build_description(**kwargs)
    return bool(inst.check_following(text))


def upstream_parity_gate(raw_result: bool, text: str) -> bool:
    """Exactly restore upstream evaluation_lib.py's response.strip() guard."""
    return bool(text.strip()) and raw_result


def token_initial_start_verb_candidate(current, text: str) -> bool:
    tokens = current.toks(text)
    if not tokens:
        return False
    first = current.fold(tokens[0])
    # Exploratory token-POS interpretation only. Clitic-first verb phrases and
    # ambiguous forms such as «ηχώ» require a protocol decision, so no source
    # patch is proposed from this function.
    known_nonverbs = {"σασ", "ενταξει"}
    return first not in known_nonverbs and current.looks_like_verb_el(tokens[0])


def proposed_consonant_clusters(current, text: str) -> bool:
    """Treat slash-separated alphabetic spans as words and reject vacuity."""
    words = re.findall(rf"[{GREEK_RANGE}]+|[A-Za-z]+", text)
    if not words:
        return False
    for token in words:
        word = current.fold(token)
        if re.search(r"[A-Za-z]", word):
            return False  # Greek protocol has no disclosed Latin cluster rule.
        if any(ch in current.GREEK_DOUBLE_CONSONANTS for ch in word):
            continue
        if not any(
            word[i] in current.GREEK_CONSONANTS
            and word[i + 1] in current.GREEK_CONSONANTS
            for i in range(len(word) - 1)
        ):
            return False
    return True


def proposed_vowel(current, text: str) -> bool:
    """Conservative Greek-only interpretation; requires protocol review for Latin names."""
    words = re.findall(rf"[{GREEK_RANGE}]+|[A-Za-z]+", text)
    if not words or any(re.search(r"[A-Za-z]", word) for word in words):
        return False
    used = {char for char in current.fold(text) if char in current.GREEK_VOWELS}
    return len(used) <= current.SingleVowelParagraphChecker.MAX_VOWELS


def proposed_prime_lengths(current, text: str) -> bool:
    """Count letters, not punctuation codepoints, and reject empty input."""
    words = re.findall(
        rf"[{GREEK_RANGE}A-Za-z]+(?:['’-][{GREEK_RANGE}A-Za-z]+)*", text
    )
    if not words:
        return False
    return all(
        sum(ch.isalpha() for ch in current.nfc(word)) in current._PRIMES
        for word in words
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    current, registry = load_checker(args.project.resolve())

    probes = [
        # Positive controls.
        ("alphabet_positive", "words:alphabet", "Αυριο βλεπω γη.", {}, True),
        ("vowel_positive", "words:vowel", "Μια καλη μερα.", {}, True),
        ("consonants_positive", "words:consonants", "στρες μπλε", {}, True),
        ("prime_positive", "words:prime_lengths", "ναι καλος", {}, True),
        ("verb_positive", "words:start_verb", "Γραψε καθαρα.", {}, True),
        ("repeats_positive", "words:repeats", "ενα δυο τρια", {"small_n": 5}, True),
        ("syllables_positive", "words:odd_even_syllables", "Ναι μερα θαλασσα", {}, True),
        ("last_first_positive", "words:last_first", "Ηρθε η μερα. Μερα καλη.", {}, True),
        ("paragraph_positive", "words:paragraph_last_first", "Μερα καλη μερα", {}, True),
        ("no_consecutive_positive", "words:no_consecutive", "Ενα βιβλιο γραφω", {}, True),
        ("position_positive", "words:words_position", "Η θαλασσα ειναι θαλασσα σημερα", {"keyword": "θαλασσα"}, True),
        # Ordinary negative controls.
        ("alphabet_negative", "words:alphabet", "Αυριο γη.", {}, False),
        ("consonants_negative", "words:consonants", "στρες και", {}, False),
        ("prime_negative", "words:prime_lengths", "νερο", {}, False),
        ("verb_negative", "words:start_verb", "Το σπιτι μενει.", {}, False),
        ("repeats_negative", "words:repeats", "ναι ναι ναι ναι ναι ναι", {"small_n": 5}, False),
        ("syllables_negative", "words:odd_even_syllables", "Ναι φως", {}, False),
        ("last_first_negative", "words:last_first", "Ηρθε η μερα. Καλη μερα.", {}, False),
        ("paragraph_negative", "words:paragraph_last_first", "Μερα καλη νυχτα", {}, False),
        ("no_consecutive_negative", "words:no_consecutive", "Ενα εργο", {}, False),
        # Adversarial semantic probes that establish current false positives/negatives.
        ("empty_consonants", "words:consonants", "", {}, False),
        ("empty_prime", "words:prime_lengths", "", {}, False),
        ("empty_syllables", "words:odd_even_syllables", "", {}, False),
        ("empty_last_first", "words:last_first", "", {}, False),
        ("empty_paragraph", "words:paragraph_last_first", "", {}, False),
        ("empty_no_consecutive", "words:no_consecutive", "", {}, False),
        ("latin_vowels_protocol", "words:vowel", "aeiou", {}, None),
        ("digits_as_words_protocol", "words:vowel", "123", {}, None),
        ("slash_word_boundary_protocol", "words:consonants", "στρες/και", {}, None),
        ("clitic_first_verb_phrase_protocol", "words:start_verb", "Σας ενημερωνω.", {}, None),
        ("interjection_is_not_verb", "words:start_verb", "Ενταξει προχωραμε.", {}, False),
        ("echo_verb_positive_regression", "words:start_verb", "Ηχω οταν μιλω.", {}, True),
        ("echo_noun_ambiguity", "words:start_verb", "Ηχω παντου.", {}, None),
        ("hyphen_letter_count_protocol", "words:prime_lengths", "καλο-νεο", {}, None),
        ("punctuation_only_protocol", "words:prime_lengths", "!!!", {}, None),
    ]

    rows = []
    for name, instruction_id, text, kwargs, expected in probes:
        raw = current_check(registry, instruction_id, text, kwargs)
        parity = upstream_parity_gate(raw, text)
        candidate = parity
        if instruction_id == "words:start_verb":
            candidate = token_initial_start_verb_candidate(current, text)
        elif instruction_id == "words:vowel":
            candidate = proposed_vowel(current, text)
        elif instruction_id == "words:consonants":
            candidate = proposed_consonant_clusters(current, text)
        elif instruction_id == "words:prime_lengths":
            candidate = proposed_prime_lengths(current, text)
        adjudicated = expected is not None
        rows.append(
            {
                "name": name,
                "instruction_id": instruction_id,
                "text": text,
                "kwargs": kwargs,
                "semantic_expected": expected,
                "current": raw,
                "upstream_parity": parity,
                "exploratory_protocol_candidate": candidate,
                "adjudicated": adjudicated,
                "current_matches_expected": (raw == expected) if adjudicated else None,
                "upstream_parity_matches_expected": (parity == expected) if adjudicated else None,
                "exploratory_candidate_matches_expected": (candidate == expected) if adjudicated else None,
            }
        )

    result = {
        "benchmark_rows_used": 0,
        "probe_count": len(rows),
        "adjudicated_probe_count": sum(row["adjudicated"] for row in rows),
        "protocol_decision_probe_count": sum(not row["adjudicated"] for row in rows),
        "current_mismatches_on_adjudicated": sum(row["current_matches_expected"] is False for row in rows),
        "upstream_parity_mismatches_on_adjudicated": sum(row["upstream_parity_matches_expected"] is False for row in rows),
        "exploratory_candidate_mismatches_on_adjudicated": sum(row["exploratory_candidate_matches_expected"] is False for row in rows),
        "safe_patch_scope": "restore response.strip() guard only",
        "probes": rows,
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
