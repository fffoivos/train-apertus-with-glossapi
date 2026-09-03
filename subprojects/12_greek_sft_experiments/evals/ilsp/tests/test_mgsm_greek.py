from decimal import Decimal

import pytest

from evals.ilsp.tasks.mgsm_greek.utils import extract_last_number, process_results


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1.234,5", Decimal("1234.5")),
        ("1,234", Decimal("1234")),
        ("12", Decimal("12")),
        ("−3", Decimal("-3")),
        ("Απάντηση: 42", Decimal("42")),
    ],
)
def test_answer_extraction(text, expected):
    assert extract_last_number(text) == expected


def test_last_number_wins_and_scores_exactly():
    assert process_results({"answer_number": 42}, ["Υπολογισμός 40 + 2. Απάντηση: 42"])[
        "exact_match"
    ]
    assert not process_results({"answer_number": 41}, ["Απάντηση: 42"])["exact_match"]
