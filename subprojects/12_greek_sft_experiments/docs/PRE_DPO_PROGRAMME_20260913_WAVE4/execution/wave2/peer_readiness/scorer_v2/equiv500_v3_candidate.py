#!/usr/bin/env python3
"""Experiment-side candidate MATH-500 equivalence scorer, version 3.

This module deliberately does not modify the frozen historical scorer.  It fixes
three demonstrated defects and removes general-purpose parsing of model text.
Ambiguous separators and unsupported symbolic forms are explicit review states.
"""

from __future__ import annotations

import re
from fractions import Fraction


CATEGORICAL = {
    "έλλειψη": "ellipse", "παραβολή": "parabola", "υπερβολή": "hyperbola",
    "κύκλος": "circle", "σημείο": "point", "ευθεία": "line",
    "δύο ευθείες": "two lines", "κενό": "empty", "άρτιος": "even",
    "ζυγός": "even", "περιττός": "odd", "μονός": "odd",
    "ανατολικά": "east", "ανατολή": "east", "δυτικά": "west",
    "βόρεια": "north", "νότια": "south", "ναι": "yes", "όχι": "no",
    "αληθές": "true", "ψευδές": "false", "δευτέρα": "monday",
    "τρίτη": "tuesday", "τετάρτη": "wednesday", "πέμπτη": "thursday",
    "παρασκευή": "friday", "σάββατο": "saturday", "κυριακή": "sunday",
    "άρτια": "even", "ζυγή": "even", "ζυγά": "even",
    "περιττή": "odd", "περιττά": "odd", "μονή": "odd",
}

UNIT_WORDS = {
    "cm", "m", "km", "mm", "inch", "inches", "feet", "ft", "cent",
    "cents", "degree", "degrees", "dollar", "dollars", "unit", "units",
    "sq", "square", "εκατοστό", "εκατοστά", "εκ.", "εκ", "μέτρο",
    "μέτρα", "μ.", "μ", "ίντσα", "ίντσες", "σεντ", "μοίρα", "μοίρες",
    "ευρώ", "€", "$",
    "second", "seconds", "sec", "s", "minute", "minutes", "hour", "hours",
}


def _balanced_boxed_candidates(resp: str) -> list[dict[str, object]]:
    candidates = []
    i = 0
    while True:
        i = resp.find("\\boxed", i)
        if i < 0:
            break
        j = resp.find("{", i)
        if j < 0:
            i += 6
            continue
        depth = 0
        k = j
        while k < len(resp):
            if resp[k] == "{":
                depth += 1
            elif resp[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if k < len(resp):
            candidates.append({"kind": "boxed", "start": i, "end": k + 1, "value": resp[j + 1 : k].strip()})
        i = k if k > i else i + 6
    return candidates


def _clean_rhs(value: str) -> str:
    value = value.strip().strip("*").strip()
    if '[{"display_answers"' in value:
        value = value.split('[{"display_answers"', 1)[0].rstrip()
    boxes = _balanced_boxed_candidates(value)
    if boxes:
        return str(boxes[-1]["value"])
    if value.startswith("$$") and "$$" in value[2:]:
        return value[2 : value.find("$$", 2)].strip()
    if value.startswith("$") and "$" in value[1:]:
        return value[: value.find("$", 1) + 1].strip()
    if value.startswith("\\(") and "\\)" in value[2:]:
        return value[: value.find("\\)", 2) + 2].strip()
    return value


def _rhs(line: str, marker: re.Match[str]) -> str:
    return _clean_rhs(line[marker.end() :])


def _surface_key(value: str) -> str:
    value = value.strip().strip("*").strip()
    if value.startswith("$") and value.endswith("$"):
        value = value[1:-1]
    if value.startswith("\\(") and value.endswith("\\)"):
        value = value[2:-2]
    boxes = _balanced_boxed_candidates(value)
    if len(boxes) == 1 and boxes[0]["start"] == 0 and boxes[0]["end"] == len(value):
        value = str(boxes[0]["value"])
    return re.sub(r"\s+", "", value).strip(".").lower()


def extract_result(resp: str) -> dict[str, object]:
    """Extract a position-aware answer and expose competing final constructions."""
    boxes = _balanced_boxed_candidates(resp)
    markers = re.compile(
        r"(?i)(?:^\s*\**\s*(?:Απάντηση|Answer|Final\s+answer)\s*\**\s*:\s*\**\s*|"
        r"(?:The\s+final\s+answer\s+is|Η\s+τελική\s+απάντηση\s+είναι)\s*:?\s*)"
    )
    markers_found = []
    offset = 0
    lines = resp.splitlines()
    for index, line in enumerate(lines):
        matches = list(markers.finditer(line))
        if matches:
            marker = matches[-1]
            value = _rhs(line, marker)
            eligible = True
            if ":" not in marker.group(0) and value and not re.match(r"[$\\(\[{+\-\d.]", value):
                eligible = False
            if eligible and value in {"$$", "\\[", "\\("}:
                value = ""
            if eligible and not value:
                value = next((candidate.strip() for candidate in lines[index + 1 :] if candidate.strip() and candidate.strip() not in {"$$", "\\[", "\\(", "\\]", "\\)"}), "")
                if value:
                    value = _clean_rhs(value)
            if eligible and value:
                markers_found.append({"kind": "marker", "start": offset + matches[-1].start(), "end": offset + len(line), "value": value})
        offset += len(line) + 1
    if markers_found:
        chosen = markers_found[-1]
        competitors = [markers_found[-2]] if len(markers_found) > 1 else []
        competitors.extend(box for box in boxes if int(box["start"]) > int(chosen["start"]))
        conflicts = [item for item in competitors if _surface_key(str(item["value"])) != _surface_key(str(chosen["value"]))]
        if conflicts:
            return {"status": "review", "reason": "competing_final_constructions", "value": chosen["value"], "candidates": [*conflicts, chosen]}
        return {"status": "ok", "reason": "explicit_marker", "value": chosen["value"]}
    if boxes:
        return {"status": "ok", "reason": "last_boxed", "value": boxes[-1]["value"]}
    nonempty = [line.strip() for line in resp.strip().splitlines() if line.strip()]
    return {"status": "ok", "reason": "last_nonempty_line", "value": nonempty[-1] if nonempty else ""}


def extract(resp: str) -> str:
    """Compatibility accessor. Scoring code must inspect ``extract_result``."""
    return str(extract_result(resp)["value"])


def _fix_fracs(s: str) -> str:
    parts = s.split("\\frac")
    out = parts[0]
    for part in parts[1:]:
        out += "\\frac"
        if part and part[0] == "{":
            out += part
        elif len(part) < 2:
            return s
        else:
            a, b = part[0], part[1]
            out += "{" + a + "}{" + b + "}" + part[2:] if b != "{" else "{" + a + "}" + b + part[2:]
    return out


def _fix_a_slash_b(s: str) -> str:
    if len(s.split("/")) != 2:
        return s
    a, b = s.split("/")
    try:
        return "\\frac{" + str(int(a)) + "}{" + str(int(b)) + "}"
    except Exception:
        return s


def _fix_sqrt(s: str) -> str:
    if "\\sqrt" not in s:
        return s
    parts = s.split("\\sqrt")
    out = parts[0]
    for part in parts[1:]:
        out += ("\\sqrt{" + part[0] + "}" + part[1:]) if part and part[0] != "{" else "\\sqrt" + part
    return out


def _strip_real_trailing_unit(s: str) -> str:
    match = re.search(r"\\(?:text|mbox|mathrm)\{\s*([^{}]*)\s*\}(\^\d)?\s*$", s)
    if match:
        content = match.group(1).strip().lower()
        unit_tokens = [x for x in re.split(r"(?:/|\bper\b|\s+)", content) if x]
        unit_tokens = [re.sub(r"\^\d+$", "", x) for x in unit_tokens]
        if content in UNIT_WORDS or (unit_tokens and all(x in UNIT_WORDS for x in unit_tokens)):
            return s[: match.start()].strip()
    plain = "|".join(sorted((re.escape(x) for x in UNIT_WORDS), key=len, reverse=True))
    return re.sub(rf"\s+(?:{plain})(?:\^\d)?\s*$", "", s, flags=re.IGNORECASE).strip()


def strip_string(s: str) -> str:
    s = s.replace("\n", "").replace("\\!", "").replace("\\\\", "\\")
    s = s.replace("tfrac", "frac").replace("dfrac", "frac")
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("^{\\circ}", "").replace("^\\circ", "")
    s = s.replace("\\$", "").replace("$", "")
    s = _strip_real_trailing_unit(s)
    s = s.replace("\\%", "").replace("%", "").replace(" .", " 0.").replace("{.", "{0.")
    if s and s[0] == ".":
        s = "0" + s
    if "=" in s and len(s.split("=")[0]) <= 2:
        s = s.split("=", 1)[1]
    s = _fix_sqrt(s).replace(" ", "")
    s = _fix_fracs(s)
    s = re.sub(r"\\frac\{([^{}]*)\}(\w)(?!\})", r"\\frac{\1}{\2}", s)
    # A single sentence-ending full stop after an otherwise closed expression
    # is punctuation, not part of the answer.  Keep this deliberately narrower
    # than generic prose-tail or last-number extraction.
    if s.endswith(".") and not s.endswith(".."):
        body = s[:-1]
        math_token = r"(?:\\frac|\\sqrt|\\pi|\\cdot|\\times|\d+(?:\.\d+)?|[A-Za-z]|[+\-*/^(){}])"
        if body and re.fullmatch(math_token + r"+", body):
            s = body
    if s == "0.5":
        s = "\\frac{1}{2}"
    return _fix_a_slash_b(s)


def categorical(s: str) -> str | None:
    text = re.sub(r"\\(?:text|mbox|textbf|mathrm)\{([^}]*)\}", r"\1", s)
    text = text.strip().strip(".").lower()
    if re.search(r"\d", text) or len(text) > 30:
        return None
    if not re.fullmatch(r"[a-zA-Zα-ωά-ώϊϋΐΰ\s]+", text):
        return None
    return CATEGORICAL.get(text, text)


def option_map_from_problem(*problem_texts: str) -> dict[str, set[str]]:
    options: dict[str, set[str]] = {}
    for problem in problem_texts:
        for match in re.finditer(r"\(([A-F])\)\s*([^\n]+)", problem):
            options.setdefault(match.group(1), set()).add(match.group(2).strip().strip(".").lower())
    return options


def _unwrapped_text(s: str) -> str:
    text = re.sub(r"^\\(?:text|mbox|textbf|mathrm)\{([^}]*)\}$", r"\1", s.strip())
    return text.strip().strip(".").strip()


def categorical_result(ref: str, pred: str, option_map: dict[str, set[str]] | None = None) -> dict[str, object] | None:
    reference_text = _unwrapped_text(ref)
    prediction_text = _unwrapped_text(pred)
    ref_label = re.fullmatch(r"\(?([A-F])\)?", reference_text, re.IGNORECASE)
    if ref_label:
        expected = ref_label.group(1).upper()
        bare = re.fullmatch(r"\(?([A-F])\)?", prediction_text, re.IGNORECASE)
        named = re.fullmatch(r"(?:\(([A-F])\)|([A-F])\))\s+(.+)", prediction_text, re.IGNORECASE)
        label = bare.group(1) if bare else (named.group(1) or named.group(2) if named else None)
        if not label or label.upper() != expected:
            return {"decision": "fail", "reason": "option_label"}
        name = named.group(3).strip() if named else ""
        if not name:
            return {"decision": "pass", "reason": "option_label"}
        if not option_map or expected not in option_map:
            return {"decision": "review", "reason": "option_label_name_requires_problem"}
        canonical_name = CATEGORICAL.get(name.lower(), name.lower())
        allowed = {CATEGORICAL.get(value, value) for value in option_map[expected]}
        return {"decision": "pass" if canonical_name in allowed else "fail", "reason": "option_label_with_validated_name"}
    ca, cb = categorical(ref), categorical(pred)
    if ca is None and cb is None:
        return None
    passed = ca is not None and ca == cb
    return {"decision": "pass" if passed else "fail", "reason": "categorical"}


def _fraction(decimal_text: str) -> Fraction:
    sign = -1 if decimal_text.startswith("-") else 1
    unsigned = decimal_text.lstrip("-")
    if "." not in unsigned:
        return Fraction(sign * int(unsigned), 1)
    whole, fractional = unsigned.split(".", 1)
    return Fraction(sign * int((whole or "0") + fractional), 10 ** len(fractional))


def numeric_interpretations(s: str, role: str = "prediction") -> set[Fraction] | None:
    """Return readings without inferring prediction notation from language.

    Benchmark references are pinned English-source MATH answers and therefore
    use their source convention. Predictions retain every defensible reading.
    """
    if role not in {"reference", "prediction"}:
        raise ValueError("role must be reference or prediction")
    text = s.replace(" ", "")
    if not re.fullmatch(r"-?\d[\d.,]*", text):
        return None
    values: set[Fraction] = set()
    conventions = ((".", ","),) if role == "reference" else ((".", ","), (",", "."))
    for decimal, group in conventions:
        if text.count(decimal) > 1:
            continue
        if decimal in text:
            integer, fractional = text.rsplit(decimal, 1)
            if not fractional.isdigit():
                continue
            groups = integer.lstrip("-").split(group)
            if len(groups) > 1 and (not 1 <= len(groups[0]) <= 3 or any(len(x) != 3 for x in groups[1:])):
                continue
            normalized = integer.replace(group, "") + "." + fractional
        else:
            groups = text.lstrip("-").split(group)
            if len(groups) > 1 and (not 1 <= len(groups[0]) <= 3 or any(len(x) != 3 for x in groups[1:])):
                continue
            normalized = text.replace(group, "")
        try:
            values.add(_fraction(normalized))
        except ValueError:
            pass
    return values or None


class UnsupportedSafeExpression(Exception):
    pass


TOKEN = re.compile(r"\\frac|\\sqrt|\\pi|\\cdot|\\times|\d+(?:\.\d+)?|[A-Za-z]|[+\-*/^(){}]")


class SafeParser:
    """Small arithmetic grammar. It constructs SymPy objects without eval/parsers."""

    def __init__(self, source: str):
        if len(source) > 256:
            raise UnsupportedSafeExpression("expression_too_long")
        self.tokens = []
        position = 0
        while position < len(source):
            if source[position].isspace():
                position += 1
                continue
            match = TOKEN.match(source, position)
            if not match:
                raise UnsupportedSafeExpression("unsupported_token")
            token = match.group(0)
            if token[0].isdigit() and len(token.replace(".", "")) > 20:
                raise UnsupportedSafeExpression("numeric_literal_too_long")
            self.tokens.append(token)
            position = match.end()
        if len(self.tokens) > 96:
            raise UnsupportedSafeExpression("too_many_tokens")
        self.index = 0
        self.nodes = 0

    def peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def pop(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise UnsupportedSafeExpression("unexpected_token")
        self.index += 1
        return token

    def node(self):
        self.nodes += 1
        if self.nodes > 64:
            raise UnsupportedSafeExpression("too_many_nodes")

    def parse(self):
        value = self.expr(0)
        if self.peek() is not None:
            raise UnsupportedSafeExpression("trailing_token")
        return value

    def expr(self, depth: int):
        if depth > 24:
            raise UnsupportedSafeExpression("too_deep")
        value = self.term(depth + 1)
        while self.peek() in {"+", "-"}:
            operator = self.pop()
            rhs = self.term(depth + 1)
            self.node()
            value = value + rhs if operator == "+" else value - rhs
        return value

    def term(self, depth: int):
        value = self.unary(depth + 1)
        atom_starts = {"(", "{", "\\frac", "\\sqrt", "\\pi"}
        while self.peek() in {"*", "/", "\\cdot", "\\times"} or (
            self.peek() is not None and (self.peek() in atom_starts or self.peek()[0].isalnum())
        ):
            operator = self.pop() if self.peek() in {"*", "/", "\\cdot", "\\times"} else "*"
            rhs = self.unary(depth + 1)
            self.node()
            value = value / rhs if operator == "/" else value * rhs
        return value

    def power(self, depth: int):
        value = self.atom(depth + 1)
        if self.peek() == "^":
            self.pop("^")
            exponent = self.unary(depth + 1)
            if not bool(exponent.is_integer) or not bool(exponent.is_number) or abs(int(exponent)) > 20:
                raise UnsupportedSafeExpression("unsupported_exponent")
            self.node()
            value = value ** exponent
        return value

    def unary(self, depth: int):
        if self.peek() in {"+", "-"}:
            operator = self.pop()
            value = self.unary(depth + 1)
            self.node()
            return value if operator == "+" else -value
        # Exponentiation binds more tightly than a leading sign: -x^2 means
        # -(x^2), while a signed exponent remains valid in x^-2.
        return self.power(depth + 1)

    def group(self, depth: int):
        opening = self.pop()
        if opening not in {"(", "{"}:
            raise UnsupportedSafeExpression("group_expected")
        closing = ")" if opening == "(" else "}"
        value = self.expr(depth + 1)
        self.pop(closing)
        return value

    def atom(self, depth: int):
        import sympy
        token = self.peek()
        self.node()
        if token is None:
            raise UnsupportedSafeExpression("missing_atom")
        if token in {"(", "{"}:
            return self.group(depth + 1)
        if token == "\\frac":
            self.pop()
            numerator = self.group(depth + 1)
            denominator = self.group(depth + 1)
            return numerator / denominator
        if token == "\\sqrt":
            self.pop()
            return sympy.sqrt(self.group(depth + 1))
        if token == "\\pi":
            self.pop()
            return sympy.pi
        if token[0].isdigit():
            self.pop()
            return sympy.Rational(token)
        if re.fullmatch(r"[A-Za-z]", token):
            self.pop()
            return sympy.Symbol(token)
        raise UnsupportedSafeExpression("unsupported_atom")


def safe_symbolic(s: str):
    return SafeParser(s).parse()


def equiv500_result(ref: str, pred: str, option_map: dict[str, set[str]] | None = None) -> dict[str, object]:
    if not ref or not pred:
        return {"decision": "fail", "reason": "missing_answer"}
    category = categorical_result(ref, pred, option_map)
    if category is not None:
        return category
    a, b = strip_string(ref), strip_string(pred)
    if not a or not b:
        return {"decision": "fail", "reason": "empty_after_normalization"}
    if a == b:
        return {"decision": "pass", "reason": "normalized_exact"}
    na, nb = numeric_interpretations(a, "reference"), numeric_interpretations(b, "prediction")
    if na is not None and nb is not None:
        overlap = na & nb
        if not overlap:
            return {"decision": "fail", "reason": "numeric_disjoint"}
        if len(na) > 1 or len(nb) > 1:
            return {
                "decision": "review", "reason": "ambiguous_numeric_separator",
                "reference_values": [str(x) for x in sorted(na)],
                "prediction_values": [str(x) for x in sorted(nb)],
            }
        return {"decision": "pass", "reason": "numeric_exact"}
    try:
        import sympy
        left, right = safe_symbolic(a), safe_symbolic(b)
        difference = sympy.cancel(left - right)
        passed = difference == 0
        return {"decision": "pass" if passed else "fail", "reason": "bounded_symbolic"}
    except UnsupportedSafeExpression as error:
        return {"decision": "review", "reason": f"unsupported_symbolic:{error}"}
    except Exception as error:
        return {"decision": "review", "reason": f"safe_symbolic_error:{type(error).__name__}"}


def equiv500(ref: str, pred: str, option_map: dict[str, set[str]] | None = None) -> bool:
    """Boolean compatibility API; review states raise instead of silently scoring."""
    result = equiv500_result(ref, pred, option_map)
    if result["decision"] == "review":
        raise ValueError(result["reason"])
    return result["decision"] == "pass"
