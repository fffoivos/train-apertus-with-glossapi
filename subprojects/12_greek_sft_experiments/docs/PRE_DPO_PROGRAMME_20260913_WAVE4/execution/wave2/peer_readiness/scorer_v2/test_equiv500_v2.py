#!/usr/bin/env python3
import equiv500_v2 as v2


def test_categorical_content_is_not_erased():
    assert not v2.equiv500(r"\text{ellipse}", r"\text{circle}", "en")
    assert v2.equiv500(r"\text{ellipse}", r"\text{ellipse}", "en")
    assert v2.equiv500(r"\text{ellipse}", "έλλειψη", "el")
    assert v2.strip_string(r"\text{ellipse}") != ""


def test_real_units_are_still_removed():
    assert v2.equiv500("12", r"12\text{ cm}", "en")
    assert v2.equiv500("12", r"12\mbox{ cm}", "en")
    assert v2.equiv500(r"12\pi", r"12\pi\text{ inches/second}", "en")


def test_final_answer_phrase():
    assert v2.extract("Work.\nThe final answer is: $9$") == "$9$"
    assert v2.equiv500("9", v2.extract("Work.\nThe final answer is: $9$"), "en")
    assert v2.extract("Λύση.\nΗ τελική απάντηση είναι: $9$") == "$9$"
    assert v2.extract("The final answer is 9.") == "9."
    assert v2.extract("The final answer is:\n\n$9$") == "$9$"


def test_separators_have_one_locale_specific_reading():
    assert v2.equiv500("1", "1.000", "en")
    assert not v2.equiv500("1000", "1.000", "en")
    assert v2.equiv500("1000", "1.000", "el")
    assert not v2.equiv500("1", "1.000", "el")
    assert v2.equiv500("1000", "1,000", "en")
    assert not v2.equiv500("1", "1,000", "en")
    assert v2.equiv500("1", "1,000", "el")
    assert not v2.equiv500("1000", "1,000", "el")
    assert v2.equiv500("36", "36.00", "el")


def test_missing_values_and_symbolic_basics():
    assert not v2.equiv500("", "1", "en")
    assert not v2.equiv500("1", "", "en")
    assert v2.equiv500(r"\frac{1}{2}", "0.5", "en")


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
            print("PASS", name)
