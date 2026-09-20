#!/usr/bin/env python3
"""Experiment-side candidate MATH-500 equivalence scorer, version 2.

This module deliberately does not modify the frozen historical scorer.  It fixes
three demonstrated defects: arbitrary trailing ``\\text``/``\\mbox`` content is
no longer erased, explicit final-answer prose is extracted, and separators are
interpreted with an explicit answer locale instead of accepting both readings.
"""

from __future__ import annotations

import re


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
}

UNIT_WORDS = {
    "cm", "m", "km", "mm", "inch", "inches", "feet", "ft", "cent",
    "cents", "degree", "degrees", "dollar", "dollars", "unit", "units",
    "sq", "square", "εκατοστό", "εκατοστά", "εκ.", "εκ", "μέτρο",
    "μέτρα", "μ.", "μ", "ίντσα", "ίντσες", "σεντ", "μοίρα", "μοίρες",
    "ευρώ", "€", "$",
    "second", "seconds", "sec", "s", "minute", "minutes", "hour", "hours",
}


def _balanced_boxed(resp: str) -> str | None:
    last = None
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
            last = resp[j + 1 : k]
        i = k if k > i else i + 6
    return last.strip() if last is not None else None


def _rhs(line: str, marker: str) -> str:
    value = line[marker.end() :].strip().strip("*").strip()
    if value.startswith("$") and "$" in value[1:]:
        return value[: value.find("$", 1) + 1].strip()
    if value.startswith("\\(") and "\\)" in value[2:]:
        return value[: value.find("\\)", 2) + 2].strip()
    return value


def extract(resp: str) -> str:
    """Extract the final answer while keeping the frozen scorer's precedence."""
    boxed = _balanced_boxed(resp)
    if boxed is not None:
        return boxed
    markers = re.compile(
        r"(?i)(?:(?:Απάντηση|Answer)\s*:\s*|"
        r"(?:The\s+final\s+answer\s+is|Η\s+τελική\s+απάντηση\s+είναι)\s*:?\s*)"
    )
    candidates = []
    for line in resp.splitlines():
        matches = list(markers.finditer(line))
        if matches:
            value = _rhs(line, matches[-1])
            if value:
                candidates.append(value)
    if candidates:
        return candidates[-1]
    lines = [line.strip() for line in resp.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


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


def numeric_value(s: str, locale: str) -> float | None:
    """Parse one number under one explicit locale; never return two readings."""
    if locale not in {"en", "el"}:
        raise ValueError("locale must be 'en' or 'el'")
    text = s.replace(" ", "")
    if not re.fullmatch(r"-?\d[\d.,]*", text):
        return None
    decimal, group = (".", ",") if locale == "en" else (",", ".")
    # With one separator type, a three-digit suffix follows the declared locale;
    # a non-three-digit suffix is unambiguously treated as a decimal, allowing
    # conventional mathematical dots in otherwise Greek prose.
    present = {mark for mark in ".," if mark in text}
    if len(present) == 1:
        mark = next(iter(present))
        count = text.count(mark)
        parts = text.lstrip("-").split(mark)
        if count == 1 and len(parts[1]) != 3:
            normalized = text.replace(mark, ".")
        elif mark == group and 1 <= len(parts[0]) <= 3 and all(len(x) == 3 for x in parts[1:]):
            normalized = text.replace(group, "")
        elif mark == decimal and count == 1:
            normalized = text.replace(decimal, ".")
        elif mark == group and count > 1 and 1 <= len(parts[0]) <= 3 and all(len(x) == 3 for x in parts[1:]):
            normalized = text.replace(group, "")
        else:
            return None
    elif len(present) == 2:
        if text.count(decimal) > 1:
            return None
        integer, fraction = text.rsplit(decimal, 1)
        if not fraction.isdigit():
            return None
        groups = integer.lstrip("-").split(group)
        if len(groups) > 1 and (not (1 <= len(groups[0]) <= 3) or any(len(x) != 3 for x in groups[1:])):
            return None
        normalized = integer.replace(group, "") + "." + fraction
    else:
        normalized = text
    try:
        return float(normalized)
    except ValueError:
        return None


def equiv500(ref: str, pred: str, pred_locale: str) -> bool:
    if not ref or not pred:
        return False
    ca, cb = categorical(ref), categorical(pred)
    if ca is not None or cb is not None:
        return ca is not None and ca == cb
    a, b = strip_string(ref), strip_string(pred)
    if not a or not b:
        return False
    if a == b:
        return True
    na, nb = numeric_value(a, "en"), numeric_value(b, pred_locale)
    if na is not None and nb is not None:
        return abs(na - nb) <= 1e-9 * max(1.0, abs(na))
    if na is not None or nb is not None:
        return False
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
        convert = lambda x: x.replace("^", "**").replace("\\frac", "").replace("{", "(").replace("}", ")")
        return sympy.simplify(parse_expr(convert(a)) - parse_expr(convert(b))) == 0
    except Exception:
        return False
