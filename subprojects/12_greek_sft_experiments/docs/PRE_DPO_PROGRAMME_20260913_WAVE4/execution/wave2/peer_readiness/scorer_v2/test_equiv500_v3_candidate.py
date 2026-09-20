#!/usr/bin/env python3
import equiv500_v3_candidate as v3


def test_categorical_content_is_not_erased():
    assert v3.equiv500_result(r"\text{ellipse}", r"\text{circle}")["decision"] == "fail"
    assert v3.equiv500_result(r"\text{ellipse}", r"\text{ellipse}")["decision"] == "pass"
    assert v3.equiv500_result(r"\text{ellipse}", "έλλειψη")["decision"] == "pass"
    assert v3.strip_string(r"\text{ellipse}")


def test_real_units_only_are_removed():
    assert v3.equiv500_result("12", r"12\text{ cm}")["decision"] == "pass"
    assert v3.equiv500_result(r"12\pi", r"12\pi\text{ inches/second}")["decision"] == "pass"


def test_final_answer_phrase_and_following_line():
    assert v3.extract("Work.\nThe final answer is: $9$") == "$9$"
    assert v3.extract("Work.\nThe final answer is:\n\n$9$\nThanks") == "$9$"
    assert v3.extract("Λύση.\nΗ τελική απάντηση είναι: $9$") == "$9$"
    assert v3.equiv500_result("9", v3.extract("The final answer is: $9$"))["decision"] == "pass"
    assert v3.extract('The final answer is 9.[{"display_answers": {"answers": ["9"]}}]') == "9."
    assert v3.extract("The final answer is:\n$$\n\\boxed{9}\n$$\nThanks") == "9"
    conflict = v3.extract_result("The final answer is: 9\nLater correction: \\boxed{8}")
    assert conflict["status"] == "review"


def test_ambiguous_separators_require_review():
    for token in ("1.000", "1,000"):
        assert v3.equiv500_result("1", token)["decision"] == "review"
        assert v3.equiv500_result("1000", token)["decision"] == "review"
    assert v3.equiv500_result("36", "36.00")["decision"] == "pass"
    assert v3.equiv500_result("58,500", "58500")["decision"] == "pass"


def test_bounded_symbolic_parser_is_mathematically_sound_for_fraction():
    assert v3.equiv500_result("x+x", "2*x")["decision"] == "pass"
    assert v3.equiv500_result(r"\frac{a}{b}", "a*b")["decision"] == "fail"
    assert v3.equiv500_result(r"\frac{a}{b}", "a/b")["decision"] == "pass"


def test_power_precedence_and_negative_exponents():
    assert v3.equiv500_result("-x^2", "x^2")["decision"] == "fail"
    assert v3.equiv500_result("-x^2", "-(x^2)")["decision"] == "pass"
    assert v3.equiv500_result("(-x)^2", "x^2")["decision"] == "pass"
    assert v3.equiv500_result("x^-2", "1/x^2")["decision"] == "pass"


def test_terminal_period_after_closed_math_expression():
    for value in ("3", "6", "36", "4", "225", r"\\frac{1}{2}", "x^2"):
        assert v3.equiv500_result(value, value + ".")["decision"] == "pass"
    # Decimal/grouping ambiguity retains its explicit review state.
    assert v3.equiv500_result("1", "1.000")["decision"] == "review"


def test_narrow_option_and_inflection_rules():
    options = {"C": {"plane", "επίπεδο"}, "E": {"hyperbola", "υπερβολή"}}
    assert v3.equiv500_result(r"\text{(E)}", r"\text{E}", options)["decision"] == "pass"
    assert v3.equiv500_result(r"\text{even}", r"\text{άρτια}")["decision"] == "pass"
    assert v3.equiv500_result(r"\text{(C)}", r"\text{C) Plane}", options)["decision"] == "pass"
    assert v3.equiv500_result(r"\text{(C)}", r"\text{C) Circle}", options)["decision"] == "fail"


def test_unsupported_or_code_like_text_is_reviewed_without_general_parser():
    cases = ["__import__('os').system('false')", "sin(x)", "x_1", "a,b"]
    for candidate in cases:
        result = v3.equiv500_result("x", candidate)
        assert result["decision"] in {"fail", "review"}
        assert result["decision"] != "pass"


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
            print("PASS", name)
