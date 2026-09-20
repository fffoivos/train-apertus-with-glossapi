"""Answer extraction and exact-match scoring for Greek MGSM."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


_NUMBER_RE = re.compile(
    r"[+\-−–]?\s*(?:\d{1,3}(?:[.\s'’]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
)


def _normalise_number(token: str) -> Decimal | None:
    token = token.strip().replace("−", "-").replace("–", "-").replace(" ", "")
    token = token.replace("'", "").replace("’", "")

    if "," in token and "." in token:
        # Greek notation: periods group thousands and comma marks decimals.
        token = token.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[+\-]?\d{1,3}(?:,\d{3})+", token):
        token = token.replace(",", "")
    elif "," in token:
        token = token.replace(",", ".")
    elif re.fullmatch(r"[+\-]?\d{1,3}(?:\.\d{3})+", token):
        token = token.replace(".", "")

    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def extract_last_number(text: str) -> Decimal | None:
    """Extract and normalize the final numeric token in a generated answer."""
    matches = list(_NUMBER_RE.finditer(text))
    if not matches:
        return None
    return _normalise_number(matches[-1].group(0))


def process_results(doc, results):
    prediction = extract_last_number(results[0])
    reference = _normalise_number(str(doc["answer_number"]))
    return {"exact_match": prediction is not None and prediction == reference}
