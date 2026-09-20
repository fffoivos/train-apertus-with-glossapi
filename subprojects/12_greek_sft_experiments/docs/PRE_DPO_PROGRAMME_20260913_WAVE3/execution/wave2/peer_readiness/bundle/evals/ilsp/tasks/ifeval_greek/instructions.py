# Derived from EleutherAI lm-evaluation-harness's IFEval implementation and
# Google Research's Apache-2.0 IFEval checkers. Language-bound behavior is
# adapted for the manually translated ILSP Greek data.
"""Greek-aware implementations of the 25 ILSP IFEval constraints."""

from __future__ import annotations

import json
import re
import unicodedata


try:  # The harness IFEval extra normally supplies this dependency.
    import langdetect
except ImportError:  # The required local environment intentionally lacks it.
    langdetect = None


_COMPARISON_RELATION = ("less than", "at least")
_GREEK_RANGES = ((0x0370, 0x03FF), (0x1F00, 0x1FFF))
_GREEK_CONSTRAINED_RESPONSES = (
    "Η απάντησή μου είναι ναι",
    "Η απάντησή μου είναι όχι",
    "Η απάντησή μου είναι ίσως",
)


def _is_greek_character(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _GREEK_RANGES)


def greek_script_share(text: str) -> float:
    """Return Greek letters divided by all alphabetic characters."""
    letters = [character for character in text if character.isalpha()]
    if not letters:
        return 0.0
    return sum(_is_greek_character(character) for character in letters) / len(letters)


def _detect_language(text: str) -> str | None:
    if langdetect is not None:
        try:
            langdetect.DetectorFactory.seed = 0
            return langdetect.detect(text)
        except langdetect.LangDetectException:
            pass
    return "el" if greek_script_share(text) >= 0.6 else None


def accent_insensitive_casefold(text: str) -> str:
    """Unicode casefold plus combining-mark removal for Greek keyword matching."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )


def _strip_edge_punctuation(token: str) -> str:
    while token and unicodedata.category(token[0])[0] in {"P", "S"}:
        token = token[1:]
    while token and unicodedata.category(token[-1])[0] in {"P", "S"}:
        token = token[:-1]
    return token


def whitespace_words(text: str) -> list[str]:
    """Split on whitespace and ignore punctuation-only tokens."""
    return [
        word
        for token in text.split()
        if (word := _strip_edge_punctuation(token))
    ]


def _compare(actual: int, expected: int | float, relation: str) -> bool:
    if relation == "less than":
        return actual < expected
    if relation == "at least":
        return actual >= expected
    raise ValueError(f"Unsupported comparison relation: {relation!r}")


class Instruction:
    def __init__(self, instruction_id: str):
        self.id = instruction_id

    def get_instruction_args(self):
        return getattr(self, "_args", None)

    def get_instruction_args_keys(self):
        return list((self.get_instruction_args() or {}).keys())


class ResponseLanguageChecker(Instruction):
    def build_description(self, *, language=None):
        self._language = language or "el"
        self._args = {"language": self._language}
        return f"The response language must be {self._language}."

    def check_following(self, value):
        return isinstance(value, str) and _detect_language(value) == self._language


class NumberOfSentences(Instruction):
    def build_description(self, *, num_sentences=None, relation=None):
        self._num_sentences = num_sentences if num_sentences is not None else 1
        self._relation = relation or "at least"
        self._args = {"num_sentences": self._num_sentences, "relation": self._relation}
        return "Sentence-count constraint."

    def check_following(self, value):
        sentences = [part for part in re.split(r"[.!?;]+", value) if part.strip()]
        return _compare(len(sentences), self._num_sentences, self._relation)


class PlaceholderChecker(Instruction):
    def build_description(self, *, num_placeholders=None):
        self._num_placeholders = num_placeholders if num_placeholders is not None else 1
        self._args = {"num_placeholders": self._num_placeholders}
        return "Placeholder-count constraint."

    def check_following(self, value):
        return len(re.findall(r"\[.*?\]", value)) >= self._num_placeholders


class BulletListChecker(Instruction):
    def build_description(self, *, num_bullets=None):
        self._num_bullets = num_bullets if num_bullets is not None else 1
        self._args = {"num_bullets": self._num_bullets}
        return "Bullet-count constraint."

    def check_following(self, value):
        bullets = re.findall(r"^\s*(?:\*[^*]|-).*$", value, flags=re.MULTILINE)
        return len(bullets) == self._num_bullets


class ConstrainedResponseChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Constrained response."

    def check_following(self, value):
        folded = value.casefold()
        return any(option.casefold() in folded for option in _GREEK_CONSTRAINED_RESPONSES)


class HighlightSectionChecker(Instruction):
    def build_description(self, *, num_highlights=None):
        self._num_highlights = num_highlights if num_highlights is not None else 1
        self._args = {"num_highlights": self._num_highlights}
        return "Highlight-count constraint."

    def check_following(self, value):
        singles = [x for x in re.findall(r"\*[^\n*]*\*", value) if x.strip("*").strip()]
        doubles = [
            x
            for x in re.findall(r"\*\*[^\n*]*\*\*", value)
            if x.removeprefix("**").removesuffix("**").strip()
        ]
        return len(singles) + len(doubles) >= self._num_highlights


class SectionChecker(Instruction):
    def build_description(self, *, section_spliter=None, num_sections=None):
        self._splitter = section_spliter.strip() if section_spliter else "Ενότητα"
        self._num_sections = num_sections if num_sections is not None else 1
        self._args = {"section_spliter": self._splitter, "num_sections": self._num_sections}
        return "Section-count constraint."

    def check_following(self, value):
        pattern = rf"\s?{re.escape(self._splitter)}\s?\d+\s?"
        return len(re.split(pattern, value)) - 1 >= self._num_sections


class ParagraphChecker(Instruction):
    def build_description(self, *, num_paragraphs=None):
        self._num_paragraphs = num_paragraphs if num_paragraphs is not None else 1
        self._args = {"num_paragraphs": self._num_paragraphs}
        return "Paragraph-count constraint."

    def check_following(self, value):
        paragraphs = re.split(r"\s?\*\*\*\s?", value)
        if any(not paragraph.strip() for paragraph in paragraphs[1:-1]):
            return False
        return len([paragraph for paragraph in paragraphs if paragraph.strip()]) == self._num_paragraphs


class PostscriptChecker(Instruction):
    def build_description(self, *, postscript_marker=None):
        self._marker = postscript_marker.strip() if postscript_marker else "Υ.Γ."
        self._args = {"postscript_marker": self._marker}
        return "Postscript constraint."

    def check_following(self, value):
        pattern = rf"(?m)^\s*{re.escape(self._marker.casefold())}"
        return bool(re.search(pattern, value.casefold()))


class KeywordChecker(Instruction):
    def build_description(self, *, keywords=None):
        self._keywords = sorted(keywords or [])
        self._args = {"keywords": self._keywords}
        return "Required-keywords constraint."

    def check_following(self, value):
        folded = accent_insensitive_casefold(value)
        return all(accent_insensitive_casefold(keyword) in folded for keyword in self._keywords)


class KeywordFrequencyChecker(Instruction):
    def build_description(self, *, keyword=None, frequency=None, relation=None):
        self._keyword = (keyword or "").strip()
        self._frequency = frequency if frequency is not None else 1
        self._relation = relation or "at least"
        self._args = {"keyword": self._keyword, "frequency": self._frequency, "relation": self._relation}
        return "Keyword-frequency constraint."

    def check_following(self, value):
        keyword = accent_insensitive_casefold(self._keyword)
        actual = accent_insensitive_casefold(value).count(keyword) if keyword else 0
        return _compare(actual, self._frequency, self._relation)


class NumberOfWords(Instruction):
    def build_description(self, *, num_words=None, relation=None):
        self._num_words = num_words if num_words is not None else 1
        self._relation = relation or "at least"
        self._args = {"num_words": self._num_words, "relation": self._relation}
        return "Word-count constraint."

    def check_following(self, value):
        return _compare(len(whitespace_words(value)), self._num_words, self._relation)


class JsonFormat(Instruction):
    def build_description(self):
        self._args = None
        return "JSON format constraint."

    def check_following(self, value):
        candidate = value.strip()
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate).strip()
        try:
            json.loads(candidate)
        except (TypeError, ValueError):
            return False
        return True


class ParagraphFirstWordCheck(Instruction):
    def build_description(self, num_paragraphs=None, nth_paragraph=None, first_word=None):
        self._num_paragraphs = num_paragraphs if num_paragraphs is not None else 1
        self._nth_paragraph = int(nth_paragraph if nth_paragraph is not None else 1)
        self._first_word = first_word or ""
        self._args = {
            "num_paragraphs": self._num_paragraphs,
            "nth_paragraph": self._nth_paragraph,
            "first_word": self._first_word,
        }
        return "Paragraph-first-word constraint."

    def check_following(self, value):
        paragraphs = [paragraph.strip() for paragraph in value.split("\n\n") if paragraph.strip()]
        if len(paragraphs) != self._num_paragraphs or self._nth_paragraph > len(paragraphs):
            return False
        token = _strip_edge_punctuation(paragraphs[self._nth_paragraph - 1].split()[0])
        return token.casefold() == self._first_word.casefold()


class ForbiddenWords(Instruction):
    def build_description(self, forbidden_words=None):
        self._forbidden_words = sorted(set(forbidden_words or []))
        self._args = {"forbidden_words": self._forbidden_words}
        return "Forbidden-words constraint."

    def check_following(self, value):
        folded = accent_insensitive_casefold(value)
        for word in self._forbidden_words:
            pattern = rf"(?<!\w){re.escape(accent_insensitive_casefold(word))}(?!\w)"
            if re.search(pattern, folded):
                return False
        return True


class TwoResponsesChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Two-response constraint."

    def check_following(self, value):
        responses = value.split("******")
        if any(not response.strip() for response in responses[1:-1]):
            return False
        valid = [response.strip() for response in responses if response.strip()]
        return len(valid) == 2 and valid[0] != valid[1]


class RepeatPromptThenAnswer(Instruction):
    def build_description(self, *, prompt_to_repeat=None):
        if not prompt_to_repeat:
            raise ValueError("prompt_to_repeat must be set")
        self._prompt = prompt_to_repeat
        self._args = {"prompt_to_repeat": self._prompt}
        return "Repeat-prompt constraint."

    def check_following(self, value):
        return value.strip().casefold().startswith(self._prompt.strip().casefold())


class EndChecker(Instruction):
    def build_description(self, *, end_phrase=None):
        self._end_phrase = end_phrase.strip() if end_phrase else ""
        self._args = {"end_phrase": self._end_phrase}
        return "End-phrase constraint."

    def check_following(self, value):
        return value.strip().strip('"').casefold().endswith(self._end_phrase.casefold())


class TitleChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Title constraint."

    def check_following(self, value):
        return any(title.strip() for title in re.findall(r"<<([^\n]+)>>", value))


class LetterFrequencyChecker(Instruction):
    def build_description(self, *, letter=None, let_frequency=None, let_relation=None):
        self._letter = letter or ""
        self._frequency = let_frequency if let_frequency is not None else 1
        self._relation = let_relation or "at least"
        self._args = {"letter": self._letter, "let_frequency": self._frequency, "let_relation": self._relation}
        return "Letter-frequency constraint."

    def check_following(self, value):
        letter = accent_insensitive_casefold(self._letter)
        actual = accent_insensitive_casefold(value).count(letter) if letter else 0
        return _compare(actual, self._frequency, self._relation)


def _greek_case_letters(value: str) -> list[str]:
    return [character for character in value if _is_greek_character(character) and character.isalpha()]


class CapitalLettersGreekChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Greek-uppercase constraint."

    def check_following(self, value):
        letters = _greek_case_letters(value)
        return bool(letters) and all(character.isupper() for character in letters)


class LowercaseLettersGreekChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Greek-lowercase constraint."

    def check_following(self, value):
        letters = _greek_case_letters(value)
        return bool(letters) and all(character.islower() for character in letters)


class CommaChecker(Instruction):
    def build_description(self):
        self._args = None
        return "No-comma constraint."

    def check_following(self, value):
        return "," not in value


class CapitalWordFrequencyChecker(Instruction):
    def build_description(self, capital_frequency=None, capital_relation=None):
        self._frequency = capital_frequency if capital_frequency is not None else 1
        self._relation = capital_relation or "at least"
        self._args = {"capital_frequency": self._frequency, "capital_relation": self._relation}
        return "Capital-word-frequency constraint."

    def check_following(self, value):
        capital_words = 0
        for word in whitespace_words(value):
            greek_letters = _greek_case_letters(word)
            if greek_letters and all(letter.isupper() for letter in greek_letters):
                capital_words += 1
        return _compare(capital_words, self._frequency, self._relation)


class QuotationChecker(Instruction):
    def build_description(self):
        self._args = None
        return "Quotation constraint."

    def check_following(self, value):
        value = value.strip()
        return len(value) > 1 and value[0] == '"' and value[-1] == '"'
