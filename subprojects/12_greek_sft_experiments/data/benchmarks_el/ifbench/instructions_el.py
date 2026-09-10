#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Greek (el) port of the 58 held-out IFBench verifiers.

Follows TRANSFER_ANALYSIS.md exactly: shared primitives P1-P4, the per-id `adapt`
rules of section C, the `replace` tasks of section D and the kwargs rules.

Contract kept identical to upstream `ifbench/instructions.py` so that the upstream
`evaluation_lib.py` can drive these classes unchanged:
  cls(instruction_id) -> .build_description(**kwargs) -> .get_instruction_args()
  -> .get_instruction_args_keys() -> .check_following(value) -> bool

Pure stdlib (re + unicodedata + csv/io): no NLTK, no spaCy, no `emoji`, no `syllapy`,
no network.  Every Greek-specific decision carries a comment.
"""
from __future__ import annotations

import csv
import io
import random
import re
import string
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

# --------------------------------------------------------------------------------------
# Our Greek conventions live in data/greek_if/constraints.py.  Import them so that word /
# sentence tokenisation stays byte-identical with the Greek-IF dataset checkers; fall back
# to local copies of the same definitions if the file is not on disk.
# --------------------------------------------------------------------------------------
_GREEK_IF_DIR = Path(__file__).resolve().parents[2] / "greek_if"
try:  # pragma: no cover - exercised implicitly by the test suite
    if str(_GREEK_IF_DIR) not in sys.path:
        sys.path.insert(0, str(_GREEK_IF_DIR))
    from constraints import strip_accents as _gi_strip_accents  # type: ignore
    from constraints import words as _gi_words  # type: ignore
    _HAVE_GREEK_IF = True
except Exception:  # pragma: no cover
    _HAVE_GREEK_IF = False
    _GI_GREEK = r"Ͱ-Ͽἀ-῿"

    def _gi_strip_accents(s: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFD", s)
                       if unicodedata.category(c) != "Mn")

    def _gi_words(s: str) -> list:
        return re.findall(rf"[{_GI_GREEK}A-Za-z0-9]+(?:['’-][{_GI_GREEK}A-Za-z0-9]+)*", s)

_InstructionArgsDtype = Optional[Dict[str, Union[int, str, Sequence[str]]]]

# ======================================================================================
# P2  fold  --  NFC -> casefold -> strip tonos/dialytika -> final sigma folded to sigma.
# ======================================================================================
def strip_diacritics(s: str) -> str:
    """NFD -> drop combining marks (Mn) -> NFC.  Never ASCII-folds (that would erase Greek).

    The mark-dropping step is greek_if/constraints.py `strip_accents()` itself, so tonos and
    dialytika are handled exactly as in the Greek-IF checkers; NFC recomposes afterwards.
    """
    return unicodedata.normalize("NFC", _gi_strip_accents(s))


def fold(s: str) -> str:
    """Matching normal form for Greek: case-, accent- and final-sigma-insensitive.

    Exact-orthography tasks (custom:character_reverse) deliberately do NOT use this.
    """
    s = unicodedata.normalize("NFC", s)
    s = s.casefold()
    s = strip_diacritics(s)
    return s.replace("ς", "σ")  # ς -> σ


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# ======================================================================================
# P4  letter sets  --  the 24-letter monotonic alphabet; ς is a positional variant of σ.
# ======================================================================================
GREEK_ALPHABET = "αβγδεζηθικλμνξοπρστυφχψω"          # 24 letters (upstream: 26 latin)
GREEK_VOWELS = set("αεηιουω")                        # 7 vowel letters
GREEK_CONSONANTS = set("βγδζθκλμνξπρσςτφχψ")         # 17 consonant letters (ς == σ)
GREEK_DOUBLE_CONSONANTS = set("ξψ")                  # ξ = κσ, ψ = πσ: a cluster in one glyph

# ======================================================================================
# P3  TOK  --  whitespace tokens stripped of punctuation, Greek marks included.
# ======================================================================================
GREEK_QUESTION_MARK = "\u037e"   # GREEK QUESTION MARK (NFC-folds onto U+003B)
ANO_TELEIA = "\u0387"        # '·' (U+0387 GREEK ANO TELEIA NFC-folds onto U+00B7)
_GREEK_PUNCT = "\u00ab\u00bb\u2039\u203a\u2026\u2014\u2013\u2015\u2018\u2019\u201c\u201d\u201e\u0384\u00b4\u00a8\u203d\u037e\u0387\u00b7"
_PUNCT_CHARS = string.punctuation + _GREEK_PUNCT
_PUNCT_TABLE = str.maketrans("", "", _PUNCT_CHARS)
_PUNCT_NO_QUOTE = "".join(c for c in _PUNCT_CHARS if c != '"')


def drop_punct(s: str) -> str:
    """Upstream's `translate(string.punctuation)` extended with the Greek marks."""
    return s.translate(_PUNCT_TABLE)


def toks(text: str) -> list:
    """P3: whitespace tokens with edge punctuation removed (« » · … — ’ ; ΄ + ASCII)."""
    out = []
    for raw in text.split():
        t = raw.strip(_PUNCT_CHARS)
        if t:
            out.append(t)
    return out


def words_el(text: str) -> list:
    """Word count convention shared with greek_if/constraints.py `words()`."""
    return _gi_words(text)


def paragraphs_nl(text: str) -> list:
    """Upstream convention: a paragraph is a single-newline-delimited block."""
    return text.split("\n")


# ======================================================================================
# P1  SPLIT  --  Greek sentence splitter.
#   * both ';' (U+003B) and ';' (U+037E) are sentence-final (Greek question mark)
#   * '·' (ano teleia) is INTERNAL punctuation, never a terminator
#   * the abbreviations below and list numbers ("1.") do not end a sentence
# ======================================================================================
ABBREVIATIONS_EL = ("π.χ.", "κ.λπ.", "κ.ά.", "Υ.Γ.", "αρ.")
_DOT_SENTINEL = "\ue000"  # private-use char: stands in for a protected '.'
_TERMINATORS = ".!?;\u037e\u2026"


def _abbrev_patterns():
    pats = []
    for abbr in ABBREVIATIONS_EL:
        # accept the accented and the accent-stripped spelling (κ.ά. / κ.α.)
        for variant in {abbr, strip_diacritics(abbr)}:
            pats.append(re.compile(re.escape(variant), re.IGNORECASE))
    return pats


_ABBREV_PATTERNS = _abbrev_patterns()


def split_sentences_el(text: str) -> list:
    """P1 splitter.  Returns sentences with their terminator attached."""
    s = nfc(text).strip()
    for pat in _ABBREV_PATTERNS:                      # protect abbreviation dots
        s = pat.sub(lambda m: m.group(0).replace(".", _DOT_SENTINEL), s)
    # list numbering «1.» is not a sentence end (same rule as greek_if/constraints.py)
    s = re.sub(r"(?<!\S)(\d+)\.(?=\s)", lambda m: m.group(1) + _DOT_SENTINEL, s)
    parts = re.split(rf"(?<=[{re.escape(_TERMINATORS)}])\s+|\n+", s)
    out = []
    for p in parts:
        p = p.replace(_DOT_SENTINEL, ".")
        # keep any part with real content: a letter, a digit or a symbol (an emoji-only
        # part is a sentence for format:emoji); pure punctuation is dropped
        if any((not ch.isspace()) and (ch not in _PUNCT_CHARS) for ch in p):
            out.append(p)
    return out


_CLOSERS = "»\"'”’)]}"


def sentence_final_char(sentence: str) -> str:
    """Last meaningful char of a sentence, ignoring trailing quotes/brackets/space."""
    s = nfc(sentence).rstrip()
    while s and s[-1] in _CLOSERS:
        s = s[:-1].rstrip()
    return s[-1] if s else ""


def is_interrogative(sentence: str) -> bool:
    # Greek question mark: ';' U+003B (and U+037E, which NFC-maps onto it) or a Latin '?'
    return sentence_final_char(sentence) in (";", GREEK_QUESTION_MARK, "?")


def is_declarative(sentence: str) -> bool:
    return sentence_final_char(sentence) == "."


def is_exclamatory(sentence: str) -> bool:
    return sentence_final_char(sentence) == "!"


# ======================================================================================
# Greek syllable counter (words:odd_even_syllables).
#   Vowel digraphs αι ει οι υι ου αυ ευ ηυ are ONE nucleus, unless
#     * the FIRST vowel carries a tonos  (γά-ι-δα-ρος)  or
#     * the SECOND vowel carries dialytika (προ-ϊ-όν).
#   Synizesis (καρδιά = 2 syllables in speech) is deliberately NOT modelled: it is
#   lexical, not predictable from spelling, so we follow the school-grammar rule and
#   count καρ-δι-ά = 3.  Documented decision, kept deterministic.
# ======================================================================================
_VOWEL_DIGRAPHS = {"αι", "ει", "οι", "υι", "ου", "αυ", "ευ", "ηυ"}
_TONOS_MARKS = {"\u0301"}       # COMBINING ACUTE (tonos)
_DIALYTIKA = {"\u0308"}         # COMBINING DIAERESIS


def _base_letter(ch: str) -> str:
    return strip_diacritics(ch).lower()


def _marks(ch: str) -> set:
    return {c for c in unicodedata.normalize("NFD", ch) if unicodedata.category(c) == "Mn"}


def count_syllables_el(word: str) -> int:
    w = nfc(word).lower()
    i, n, syl = 0, len(w), 0
    while i < n:
        ch = w[i]
        base = _base_letter(ch)
        if base in GREEK_VOWELS:
            nxt = w[i + 1] if i + 1 < n else ""
            pair = base + (_base_letter(nxt) if nxt else "")
            if (nxt and pair in _VOWEL_DIGRAPHS
                    and not (_marks(ch) & _TONOS_MARKS)          # tonos on the first splits
                    and not (_marks(nxt) & _DIALYTIKA)):         # dialytika on the second splits
                syl += 1
                i += 2
                continue
            syl += 1
        i += 1
    return syl


# ======================================================================================
# Greek verb-form rule (words:start_verb).  Suffix test + imperative whitelist +
# a blacklist of frequent non-verbs that end in -ω/-ει (adverbs and pronouns).
# ======================================================================================
VERB_SUFFIXES_EL = (
    # active present / future
    "ω", "ώ", "εις", "είς", "άς", "ει", "εί", "άει", "ουμε", "ούμε", "άμε",
    "ετε", "είτε", "άτε", "ουν", "ούν", "άνε", "ούνε", "ανε",
    # medio-passive
    "μαι", "σαι", "ται", "ναι", "μαστε", "σαστε", "στε", "νται", "όμουν", "όσουν", "όταν",
    # past tenses
    "ηκα", "ήκα", "θηκα", "ήθηκα", "ησα", "ήσα", "ξα", "ψα", "αγα", "ούσα",
    "ούσε", "ησε", "ήσε", "ξε", "ψε", "αμε", "ατε", "αν",
)
IMPERATIVES_EL = {
    "δες", "κάνε", "πες", "πάρε", "δώσε", "γράψε", "σκέψου", "θυμήσου", "πρόσεξε",
    "ξεκίνα", "μάθε", "δείξε", "βάλε", "φτιάξε", "έλα", "άκου", "διάβασε", "εξήγησε",
    "περίγραψε", "ανάλυσε", "συνέχισε", "σύγκρινε", "φαντάσου", "σημείωσε", "δοκίμασε",
    "πρόσθεσε", "άφησε", "μείνε", "έχε", "στείλε", "ρώτα", "κοίτα", "πήγαινε", "τρέξε",
}
# frequent irregular forms whose ending no suffix rule catches (aorist 3sg in -ε)
IRREGULAR_VERBS_EL = {
    "είπε", "είπα", "είπες", "είπαν", "ήρθε", "ήρθα", "ήρθαν", "πήγε", "πήγα", "βρήκε",
    "βρήκα", "είδε", "είδα", "έφυγε", "έδωσε", "έκανε", "έμεινε", "πήρε", "έβαλε",
    "έγινε", "ήθελε", "μπόρεσε", "έδειξε", "έφερε", "έμαθε", "είχε", "είχα", "είχαν",
}
# adverbs / pronouns that end in a verb-looking suffix and must not pass
NON_VERBS_EL = {
    "εγώ", "εσύ", "ενώ", "εδώ", "εκεί", "πάνω", "κάτω", "γύρω", "πίσω", "έξω", "μέσω",
    "ίσως", "όπως", "αυτό", "αυτή", "αυτοί", "όχι", "ναι", "μόνο", "πλέον", "σαν",
    "όταν", "αφού", "καθώς", "παρότι", "εφόσον", "πριν", "όσο", "όποτε", "εκτός",
}


def looks_like_verb_el(token: str) -> bool:
    """Heuristic Greek finite/imperative verb test (no POS tagger is available)."""
    t = fold(token)
    if t in {fold(w) for w in NON_VERBS_EL}:
        return False
    if t in {fold(w) for w in IMPERATIVES_EL} | {fold(w) for w in IRREGULAR_VERBS_EL}:
        return True
    if len(t) < 3:
        return False
    return any(t.endswith(fold(sfx)) for sfx in VERB_SUFFIXES_EL)


# ======================================================================================
# Greek collation (custom:reverse_newline).  Sorting keys are built on the folded string
# so that tonos never changes the order; spaces and hyphens are ignored.
# ======================================================================================
_ALPHA_INDEX = {ch: i for i, ch in enumerate(GREEK_ALPHABET)}


def greek_sort_key(s: str):
    key = []
    for ch in fold(s):
        if ch in _ALPHA_INDEX:
            key.append((0, _ALPHA_INDEX[ch]))
        elif ch in " -\u2010\u2011":
            continue                                  # ignore word separators
        else:
            key.append((1, ord(ch)))                  # non-Greek letters sort last
    return key


# ======================================================================================
# Latin<->Greek homoglyphs: accepted for OPTION and MCQ labels only (never inside fold).
# ======================================================================================
HOMOGLYPHS_TO_GREEK = {
    "A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η", "I": "Ι", "K": "Κ", "M": "Μ",
    "N": "Ν", "O": "Ο", "P": "Ρ", "T": "Τ", "X": "Χ", "Y": "Υ",
    "a": "α", "b": "β", "e": "ε", "o": "ο", "i": "ι", "k": "κ", "n": "ν", "p": "ρ",
    "t": "τ", "x": "χ", "y": "υ", "v": "ν", "c": "γ", "d": "δ",
}


def degreek_homoglyphs(s: str) -> str:
    return "".join(HOMOGLYPHS_TO_GREEK.get(c, c) for c in s)


# ======================================================================================
# Emoji detection.  The upstream `emoji` package is a third-party dependency; we use the
# codepoint ranges instead (documented approximation, no network / no extra deps).
# ======================================================================================
_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF), (0x1F1E6, 0x1F1FF), (0x2600, 0x27BF), (0x2B00, 0x2BFF),
    (0x1F300, 0x1F5FF), (0x2049, 0x2049), (0x203C, 0x203C), (0x2122, 0x2122),
    (0x2139, 0x2139), (0x24C2, 0x24C2), (0x3030, 0x3030), (0x303D, 0x303D),
    (0x3297, 0x3299), (0xFE0F, 0xFE0F),
)


def is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _EMOJI_RANGES)


# ======================================================================================
# Elision apostrophes: «σ’ αυτό», «απ’ την» — the ’ is not a quote delimiter.
# ======================================================================================
_ELIDED = ("σ", "μ", "τ", "ν", "γι", "απ", "κατ", "μετ", "παρ", "αντ", "υπ", "εφ", "αφ",
           "ολ", "θ", "δι", "επ")
_ELISION_RE = re.compile(r"(?<![^\W\d_])(" + "|".join(_ELIDED) + r")[’']", re.IGNORECASE)


def strip_elision_apostrophes(text: str) -> str:
    """Drop ’ used for Greek elision and ’ flanked by letters (never a quote mark)."""
    text = re.sub(r"(?<=[^\W\d_])[’](?=[^\W\d_])", "", text)   # letter-flanked
    return _ELISION_RE.sub(lambda m: m.group(1), text)


# ======================================================================================
# Stem containment (sentence:keyword) — same convention as greek_if/constraints.py:
# drop the final (inflectional) character of the keyword and test containment on the
# folded text, so θάλασσα matches θάλασσας / θάλασσες.
# ======================================================================================
def contains_stem(text: str, keyword: str) -> bool:
    kw = fold(keyword).strip()
    if not kw:
        return False
    stem = kw[:-1] if len(kw) >= 4 else kw
    return stem in fold(text)


# ======================================================================================
# Greek word inventories
# ======================================================================================
# ratio:stop_words — articles, contracted prepositions, particles, clitics, copula and
# the highest-frequency adverbs.  Matching is ACCENT-SENSITIVE on purpose: «που»/«πως»
# (relative/complementiser, function words) must not be conflated with the interrogatives
# «πού»/«πώς», and «ή» (or) must not be conflated with the article «η».
STOP_WORDS_EL = {
    # articles
    "ο", "η", "το", "οι", "τα", "του", "της", "των", "τον", "την", "τη", "τους", "τις",
    "ένας", "μια", "μία", "ένα", "ενός", "μιας", "έναν",
    # σε + article (contracted) and bare prepositions
    "σε", "στο", "στη", "στην", "στον", "στους", "στις", "στα", "στου", "στης", "στων",
    "από", "με", "για", "ως", "προς", "κατά", "μετά", "πριν", "χωρίς", "μέχρι", "παρά",
    "αντί", "σαν", "έως", "περί", "υπό", "επί", "μεταξύ", "δίχως",
    # conjunctions / particles / negation
    "και", "κι", "ή", "αλλά", "μα", "όμως", "ούτε", "μήτε", "είτε", "ότι", "πως", "που",
    "να", "θα", "ας", "μην", "μη", "δεν", "γιατί", "αν", "όταν", "ενώ", "καθώς",
    "επειδή", "αφού", "λοιπόν", "δηλαδή", "επίσης", "ώστε", "όπως", "όσο", "αλλιώς",
    # weak (clitic) pronouns
    "μου", "σου", "μας", "σας", "με", "σε", "τον", "την", "το",
    # copula / auxiliaries
    "είναι", "ήταν", "είμαι", "είσαι", "είμαστε", "είστε", "ήμουν", "έχει", "έχω",
    "έχουν", "έχουμε", "είχε", "θα",
    # frequent adverbs / demonstratives
    "αυτό", "αυτός", "αυτή", "αυτά", "αυτοί", "αυτές", "εκείνο", "εκείνος", "εκείνη",
    "πολύ", "πιο", "ήδη", "ακόμα", "ακόμη", "μόνο", "έτσι", "τότε", "τώρα", "εδώ",
    "εκεί", "όχι", "ναι", "πάλι", "κάθε", "όλα", "όλοι", "όλες",
}

# count:conjunctions — coordinating conjunctions only; accent-sensitive (ή ≠ η).
# «και» and «κι» are the same conjunction, so they collapse to one type.
CONJUNCTIONS_EL = {"και", "κι", "ή", "αλλά", "μα", "όμως", "ούτε", "μήτε", "είτε", "παρά"}
_CONJ_LEMMA = {"κι": "και"}

# count:pronouns — Greek pronoun inventory.
PRONOUNS_EL_UNAMBIGUOUS = {
    # personal (strong forms)
    "εγώ", "εμένα", "μένα", "εσύ", "εσένα", "σένα", "εμείς", "εμάς", "εσείς", "εσάς",
    "αυτός", "αυτή", "αυτό", "αυτοί", "αυτές", "αυτά", "αυτόν", "αυτήν", "αυτού",
    "αυτής", "αυτών", "αυτούς",
    # demonstrative
    "εκείνος", "εκείνη", "εκείνο", "εκείνοι", "εκείνες", "εκείνα", "εκείνον", "εκείνων",
    "τούτος", "τούτη", "τούτο", "τούτοι", "τούτα",
    # reflexive / emphatic
    "εαυτός", "εαυτό", "εαυτού", "εαυτόν", "ίδιος", "ίδια", "ίδιο", "ίδιοι",
    # interrogative / relative
    "ποιος", "ποια", "ποιο", "ποιον", "ποιαν", "ποιου", "ποιανού", "ποιοι", "ποιες",
    "τι", "όποιος", "όποια", "όποιο", "όσος", "όσοι", "όσες", "όσα", "οποίος", "οποία",
    "οποίο", "οποίοι", "οποίες", "ό,τι",
    # indefinite
    "κάποιος", "κάποια", "κάποιο", "κάποιον", "κάποιοι", "κανείς", "κανένας", "κανένα",
    "καμία", "καμιά", "τίποτα", "τίποτε", "καθένας", "καθεμία", "καθένα", "μερικοί",
    "μερικές", "μερικά", "άλλος", "άλλη", "άλλο", "άλλοι", "κάτι", "όλοι", "όλες",
    "δικός", "δική", "δικό", "δικοί",
}
# Homograph rule (TRANSFER_ANALYSIS §C): του/της/τους/μου/σου/μας/σας are weak pronouns
# only when they are NOT the article of a following noun.  Same phenomenon for the
# accusative articles τον/την/το/τη/τα/τις, so the gate covers them too.
# We count a clitic when the next token is a verb form («μου είπε»), or when nothing
# follows it («το βιβλίο μου»).  This DEFLATES the count: a post-nominal possessive that
# is followed by more text is missed.  Documented, deliberate under-count.
PRONOUNS_EL_HOMOGRAPH = {"μου", "σου", "του", "της", "μας", "σας", "τους",
                         "τον", "την", "το", "τη", "τα", "τις", "με", "σε"}

# format:title_case — Greek minor words that stay lowercase in a title.
MINOR_WORDS_EL = {
    "ο", "η", "το", "οι", "τα", "του", "της", "των", "τον", "την", "τη", "τους", "τις",
    "ένας", "μια", "μία", "ένα", "σε", "στο", "στη", "στην", "στον", "στους", "στις",
    "στα", "από", "με", "για", "ως", "προς", "κατά", "και", "κι", "ή", "αλλά", "μα",
    "ούτε", "είτε", "που", "να", "θα", "δεν", "μην", "παρά", "αντί", "χωρίς", "μέχρι",
}

# count:person_names — 50 Greek given names.  Each lemma expands to its declension set
# so that «τον Γιώργο» / «του Γιώργου» / «Γιώργε» all count as the same person.
NAMES_EL = [
    "Γιώργος", "Δημήτρης", "Νίκος", "Κώστας", "Γιάννης", "Χρήστος", "Παναγιώτης",
    "Βασίλης", "Θανάσης", "Αντώνης", "Μιχάλης", "Πέτρος", "Στέλιος", "Ανδρέας",
    "Ηλίας", "Θεόδωρος", "Αλέξανδρος", "Σπύρος", "Μάριος", "Φώτης", "Λευτέρης",
    "Σωτήρης", "Στέφανος", "Παύλος", "Άγγελος",
    "Μαρία", "Ελένη", "Κατερίνα", "Σοφία", "Βασιλική", "Γεωργία", "Δήμητρα",
    "Αναστασία", "Ευαγγελία", "Ιωάννα", "Χριστίνα", "Αγγελική", "Παρασκευή",
    "Δέσποινα", "Ειρήνη", "Κωνσταντίνα", "Ζωή", "Νίκη", "Αθηνά", "Όλγα", "Φωτεινή",
    "Στέλλα", "Άννα", "Ελισάβετ", "Δανάη",
]
_NAME_OVERRIDES = {
    "Ελισάβετ": {"Ελισάβετ"},                     # indeclinable
    "Δανάη": {"Δανάη", "Δανάης"},
    "Άγγελος": {"Άγγελος", "Αγγέλου", "Άγγελο", "Άγγελε"},   # accent shifts in the genitive
    "Αλέξανδρος": {"Αλέξανδρος", "Αλεξάνδρου", "Αλέξανδρο", "Αλέξανδρε"},
    "Θεόδωρος": {"Θεόδωρος", "Θεοδώρου", "Θεόδωρο", "Θεόδωρε"},
}


def _decline_name(lemma: str) -> set:
    """Rule-based Modern Greek given-name declension (nominative/genitive/accusative/vocative)."""
    if lemma in _NAME_OVERRIDES:
        return set(_NAME_OVERRIDES[lemma])
    if lemma.endswith("ος"):                       # Πέτρος -> Πέτρου / Πέτρο / Πέτρε
        st = lemma[:-2]
        return {lemma, st + "ου", st + "ο", st + "ε"}
    if lemma.endswith("ης") or lemma.endswith("ής"):   # Γιάννης -> Γιάννη
        return {lemma, lemma[:-1]}
    if lemma.endswith("ας") or lemma.endswith("άς"):   # Κώστας -> Κώστα
        return {lemma, lemma[:-1]}
    if lemma[-1] in "αάηήωώ":                      # Μαρία -> Μαρίας, Ζωή -> Ζωής
        return {lemma, lemma + "ς"}
    return {lemma}


NAME_FORMS_EL = {lemma: {fold(f) for f in _decline_name(lemma)} for lemma in NAMES_EL}

# custom:european_capitals_sort — the same 27 capitals (latitude descending), in Greek.
# Each entry lists the accepted spellings; comparison is tonos-insensitive (fold).
EUROPEAN_CAPITALS_EL = [
    ("Ρέικιαβικ", ("Ρέικιαβικ", "Ρεϊκιαβίκ", "Ρέυκιαβικ", "Ρεικιαβικ")),
    ("Ελσίνκι", ("Ελσίνκι",)),
    ("Όσλο", ("Όσλο",)),
    ("Ταλίν", ("Ταλίν", "Ταλλίν")),
    ("Στοκχόλμη", ("Στοκχόλμη", "Στοκχόλμ")),
    ("Ρίγα", ("Ρίγα",)),
    ("Μόσχα", ("Μόσχα",)),
    ("Κοπεγχάγη", ("Κοπεγχάγη",)),
    ("Βίλνιους", ("Βίλνιους", "Βίλνο")),
    ("Μινσκ", ("Μινσκ",)),
    ("Δουβλίνο", ("Δουβλίνο",)),
    ("Βερολίνο", ("Βερολίνο",)),
    ("Άμστερνταμ", ("Άμστερνταμ",)),
    ("Βαρσοβία", ("Βαρσοβία",)),
    ("Λονδίνο", ("Λονδίνο",)),
    ("Βρυξέλλες", ("Βρυξέλλες",)),
    ("Πράγα", ("Πράγα",)),
    ("Λουξεμβούργο", ("Λουξεμβούργο",)),
    ("Παρίσι", ("Παρίσι",)),
    ("Βιέννη", ("Βιέννη",)),
    ("Μπρατισλάβα", ("Μπρατισλάβα",)),
    ("Βουδαπέστη", ("Βουδαπέστη",)),
    ("Βαντούζ", ("Βαντούζ", "Φαντούτς")),
    ("Κισινάου", ("Κισινάου", "Κισινιόφ", "Χισινάου")),
    ("Βέρνη", ("Βέρνη",)),
    ("Λιουμπλιάνα", ("Λιουμπλιάνα",)),
    ("Ζάγκρεμπ", ("Ζάγκρεμπ",)),
]

# custom:reverse_newline — the 54 African states, Greek names.
AFRICAN_COUNTRIES_EL = [
    "Αγκόλα", "Αίγυπτος", "Αιθιοπία", "Ακτή Ελεφαντοστού", "Αλγερία",
    "Γκάμπια", "Γκαμπόν", "Γκάνα", "Γουινέα", "Γουινέα-Μπισάου",
    "Ερυθραία", "Εσουατίνι", "Ζάμπια", "Ζιμπάμπουε", "Ισημερινή Γουινέα",
    "Καμερούν", "Κένυα", "Κεντροαφρικανική Δημοκρατία", "Κομόρες", "Κονγκό",
    "Λαϊκή Δημοκρατία του Κονγκό", "Λεσότο", "Λιβερία", "Λιβύη",
    "Μαδαγασκάρη", "Μαλάουι", "Μάλι", "Μαρόκο", "Μαυρίκιος", "Μαυριτανία",
    "Μοζαμβίκη", "Μπενίν", "Μποτσουάνα", "Μπουρκίνα Φάσο", "Μπουρούντι",
    "Ναμίμπια", "Νίγηρας", "Νιγηρία", "Νότια Αφρική", "Νότιο Σουδάν",
    "Ουγκάντα", "Πράσινο Ακρωτήριο", "Ρουάντα", "Σάο Τομέ και Πρίνσιπε",
    "Σενεγάλη", "Σεϋχέλλες", "Σιέρα Λεόνε", "Σομαλία", "Σουδάν",
    "Τανζανία", "Τζιμπουτί", "Τόγκο", "Τσαντ", "Τυνησία",
]
REVERSE_NEWLINE_ANCHOR = "Ζιμπάμπουε"
# In Greek collation Ζιμπάμπουε is NOT the last name (Τυνησία is), so the number of lines
# that must follow the anchor in reverse-alphabetical order is recounted here.
REVERSE_NEWLINE_MIN_LINES = sum(
    1 for c in AFRICAN_COUNTRIES_EL
    if greek_sort_key(c) <= greek_sort_key(REVERSE_NEWLINE_ANCHOR))

# custom:date_format_list — Greek genitive month names (Μαΐου keeps its dialytika).
MONTHS_GEN_EL = ("Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
                 "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου",
                 "Δεκεμβρίου")

# format:options / format:list — kwargs rules (§D): the English option and separator
# banks are mapped onto their Greek counterparts so upstream rows still evaluate.
OPTIONS_MAP_EL = {
    "yes/no/maybe": "ναι/όχι/ίσως",
    "I know or I don't know": "ξέρω ή δεν ξέρω",
    "a), b), c), d)": "α), β), γ), δ)",
}
SEP_MAP_EL = {
    "SEPARATOR": "ΔΙΑΧΩΡΙΣΤΙΚΟ",
    "!?!?": "!;!;",          # the Greek question mark replaces '?'
    "...": "...",            # '…' is accepted as an equivalent at check time
    "-": "-",
}

# ======================================================================================
# Deliberate numeric re-tunings (TRANSFER_ANALYSIS §C / §D), one line of reason each.
# ======================================================================================
RETUNED = {
    "words:palindrome": {
        "upstream": 10, "greek": 3,
        "reason": "Greek has almost no ≥5-letter single-word palindromes; 10 is infeasible, 3 is reachable."},
    "words:vowel": {
        "upstream": 3, "greek": 4,
        "reason": "Greek has 7 vowel letters and vowel-heavy morphology; ≤3 distinct vowels leaves no usable lexicon."},
    "words:repeats": {
        "upstream": 1, "greek": 5,
        # cross-check #3: the floor is the EFFECTIVE value -- LimitedWordRepeatChecker.effective_small_n()
        # is the single source of truth and is used by build_description() and check_following() alike,
        # so the prompt always states the number the checker actually enforces (kwargs keep the upstream one).
        "reason": "Greek articles/clitics (ο, η, το, και, να, του) recur unavoidably, so small_n is floored at 5; "
                  "the effective value is effective_small_n(small_n) = max(small_n, 5)."},
    "custom:sentence_alphabet": {
        "upstream": 26, "greek": 24,
        "reason": "The Greek alphabet has 24 letters, so the story has 24 sentences (α…ω)."},
    "custom:reverse_newline": {
        "upstream": 52, "greek": REVERSE_NEWLINE_MIN_LINES,
        "reason": "Ζιμπάμπουε is not last in Greek collation; only the countries sorting ≤ it follow the anchor."},
    # cross-check #11: deliberate TIGHTENING (not a numeric port) -- upstream compares counts only, so an
    # answer with no sentence terminators at all satisfied 0 == 2*0 / 0 == 0 == 0.  We require at least one
    # sentence of each mandated type, and the descriptions now say so.
    "ratio:sentence_type": {
        "upstream": 0, "greek": 1,
        "reason": "Tightening: at least one interrogative sentence is required, so 0 == 2*0 is no longer a free pass."},
    "ratio:sentence_balance": {
        "upstream": 0, "greek": 1,
        "reason": "Tightening: at least one sentence of each of the three types is required, so 0 == 0 == 0 is no longer a free pass."},
}


# ======================================================================================
# DESCRIPTIONS_EL — the Greek instruction wording for every id.  Values are templates
# whose placeholders are the upstream kwargs names; build_description() formats them and
# the prompt translator reuses the exact same strings.
# ======================================================================================
DESCRIPTIONS_EL = {
    "count:word_count_range":
        "Η απάντηση πρέπει να έχει από {min_words} έως {max_words} λέξεις.",
    "count:unique_word_count":
        "Χρησιμοποίησε τουλάχιστον {N} διαφορετικές λέξεις στην απάντηση.",
    "ratio:stop_words":
        "Φρόντισε οι λέξεις-εργαλεία (άρθρα, προθέσεις, σύνδεσμοι, μόρια, αδύνατοι τύποι) "
        "να μην ξεπερνούν το {percentage}% του συνόλου των λέξεων της απάντησης.",
    # cross-check #11: the ≥1 requirement is disclosed, because the checker now enforces it.
    "ratio:sentence_type":
        "Κράτησε αναλογία 2:1 ανάμεσα στις αποφαντικές προτάσεις (που κλείνουν με τελεία) "
        "και στις ερωτηματικές (που κλείνουν με ελληνικό ερωτηματικό «;»)· πρέπει να υπάρχει "
        "τουλάχιστον μία ερωτηματική πρόταση.",
    "ratio:sentence_balance":
        "Φρόντισε οι τρεις τύποι προτάσεων να είναι ισάριθμοι: αποφαντικές (τελεία), "
        "ερωτηματικές (ελληνικό ερωτηματικό «;») και θαυμαστικές (θαυμαστικό)· πρέπει να "
        "υπάρχει τουλάχιστον μία πρόταση από κάθε τύπο.",
    "count:conjunctions":
        "Χρησιμοποίησε τουλάχιστον {small_n} διαφορετικούς παρατακτικούς συνδέσμους από τους "
        "εξής: και/κι, ή, αλλά, μα, όμως, ούτε, μήτε, είτε, παρά.",
    "count:person_names":
        "Ανάφερε τουλάχιστον {N} διαφορετικά ονόματα προσώπων από την παρακάτω λίστα: {names}.",
    # cross-check #1: the reference text must be VISIBLE and identifiable in the prompt, not
    # referred to as "the text you were given" (the assembler passes the Greek task body).
    "ratio:overlap":
        "Κράτησε επικάλυψη τριγραμμάτων {percentage}% (±2%) με το ακόλουθο κείμενο αναφοράς: "
        "«{reference_text}»",
    "count:numbers":
        "Συμπερίλαβε ακριβώς {N} αριθμούς γραμμένους με ψηφία στην απάντηση.",
    "words:alphabet":
        "Κάθε λέξη πρέπει να αρχίζει με το επόμενο γράμμα του ελληνικού αλφαβήτου, "
        "και μετά το «ω» να ξαναρχίζεις από το «α».",
    "words:vowel":
        "Γράψε μία μόνο παράγραφο με λέξεις που περιέχουν συνολικά το πολύ τέσσερα "
        "διαφορετικά φωνήεντα (οι τόνοι δεν μετρούν ως διαφορετικό φωνήεν).",
    # cross-check #12: spell out that ordinary function words are excluded (no code change).
    "words:consonants":
        "Κάθε λέξη της απάντησης πρέπει να έχει τουλάχιστον ένα σύμπλεγμα συμφώνων, "
        "δηλαδή δύο σύμφωνα στη σειρά· το «ξ» ή το «ψ» μετρούν από μόνα τους ως σύμπλεγμα "
        "(αυτό αποκλείει λέξεις χωρίς σύμπλεγμα συμφώνων όπως και, το, να, με).",
    "sentence:alliteration_increment":
        "Κάθε πρόταση πρέπει να έχει μεγαλύτερη σειρά διαδοχικών λέξεων που αρχίζουν με το ίδιο "
        "γράμμα (παρήχηση) από την προηγούμενη πρόταση.",
    "words:palindrome":
        "Συμπερίλαβε τουλάχιστον {N} καρκινικές λέξεις (που διαβάζονται το ίδιο και ανάποδα), "
        "τουλάχιστον 5 γραμμάτων η καθεμία.",
    "count:punctuation":
        "Χρησιμοποίησε τουλάχιστον μία φορά καθένα από τα σημεία στίξης: τελεία, κόμμα, "
        "θαυμαστικό, ελληνικό ερωτηματικό «;», άνω και κάτω τελεία «:» και άνω τελεία «·», "
        "καθώς και μία φορά τον συνδυασμό έκπληξης-ερώτησης «!;».",
    "format:parentheses":
        "Φώλιασε παρενθέσεις (και [αγκύλες {και άγκιστρα}]) σε τουλάχιστον 5 επίπεδα.",
    "format:quotes":
        "Βάλε εισαγωγικά μέσα σε εισαγωγικά μέσα σε εισαγωγικά, τουλάχιστον 3 επίπεδα, "
        "με την ελληνική ιεραρχία «…» → “…” → ‘…’.",
    "words:prime_lengths":
        "Χρησιμοποίησε μόνο λέξεις των οποίων το πλήθος των γραμμάτων είναι πρώτος αριθμός.",
    "format:options":
        "Απάντησε με μία από τις εξής επιλογές: {options}. Μην δώσεις καμία εξήγηση.",
    "format:newline":
        "Γράψε κάθε λέξη σε δική της γραμμή.",
    "format:emoji":
        "Βάλε ένα emoji στο τέλος κάθε πρότασης.",
    "ratio:sentence_words":
        "Απάντησε με τρεις προτάσεις που έχουν ακριβώς τον ίδιο αριθμό χαρακτήρων και "
        "χωρίς να επαναλαμβάνεται καμία λέξη.",
    "count:words_japanese":
        "Κάθε {N}η λέξη της απάντησης πρέπει να είναι γραμμένη στα ιαπωνικά.",
    "words:start_verb":
        "Η απάντηση πρέπει να ξεκινά με ρήμα.",
    "words:repeats":
        "Καμία λέξη δεν πρέπει να επαναλαμβάνεται πάνω από {small_n} φορές στην απάντηση.",
    "sentence:keyword":
        "Η {N}η πρόταση της απάντησης πρέπει να περιέχει τη λέξη «{word}».",
    # cross-check #2: disclose WHAT is counted -- strong forms always, clitics only in the
    # pre-verbal / clause-final position that the homograph rule in check_following() accepts.
    "count:pronouns":
        "Η απάντηση πρέπει να περιέχει τουλάχιστον {N} αντωνυμίες, μετρώντας ισχυρούς τύπους "
        "(εγώ, εσύ, αυτός/αυτή/αυτό, εμείς, εσείς, εκείνος, κάποιος, κανείς, τίποτα, όλοι, "
        "όποιος, ό,τι …) και τα κλιτικά μου/σου/του/της/μας/σας/τους/τον/την/το/τα/τις μόνο "
        "όταν ακολουθεί ρήμα ή τελειώνει η πρόταση.",
    "words:odd_even_syllables":
        "Εναλλάσσε λέξεις με μονό και ζυγό αριθμό συλλαβών σε όλη την απάντηση.",
    "words:last_first":
        "Η τελευταία λέξη κάθε πρότασης πρέπει να γίνεται η πρώτη λέξη της επόμενης πρότασης.",
    "words:paragraph_last_first":
        "Κάθε παράγραφος πρέπει να τελειώνει με την ίδια λέξη με την οποία ξεκίνησε· "
        "χώρισε τις παραγράφους με μία αλλαγή γραμμής.",
    # cross-check #4: {words_more} carries the grammatical number -- «1 λέξη περισσότερη» vs
    # «3 λέξεις περισσότερες»; build_description() is the only place that fills it.
    "sentence:increment":
        "Κάθε πρόταση πρέπει να έχει ακριβώς {small_n} {words_more} από την προηγούμενη.",
    "words:no_consecutive":
        "Δύο διαδοχικές λέξεις δεν επιτρέπεται να αρχίζουν με το ίδιο γράμμα.",
    "format:line_indent":
        "Φτιάξε σκαλοπάτια: κάθε νέα γραμμή να ξεκινά με περισσότερα κενά από την προηγούμενη.",
    # cross-check #6: state what is actually tested; the checker never verifies that a quoted
    # phrase is explained, so that (unenforced) wording is dropped.
    "format:quote_unquote":
        "Μην βάζεις ποτέ δύο εισαγωγικά το ένα δίπλα στο άλλο (αν αφαιρεθούν τα κενά) και "
        "μην τελειώνεις την απάντηση με εισαγωγικό: μετά από κάθε κλείσιμο εισαγωγικών πρέπει "
        "να ακολουθεί κείμενο εκτός εισαγωγικών.",
    "format:list":
        "Απάντησε με λίστα σημείων· αντί για κουκκίδες χρησιμοποίησε {sep}.",
    # cross-check #5: the checker only requires ONE such section and accepts <em> as well as <i>.
    "format:thesis":
        "Τουλάχιστον μία ενότητα ξεκινά με μια θέση σε πλάγια γραφή (<i>…</i> ή <em>…</em>) "
        "ακολουθούμενη από κανονικό κείμενο.",
    "format:sub-bullets":
        "Η απάντηση πρέπει να έχει κουκκίδες με «*» και κάθε κουκκίδα να έχει τουλάχιστον "
        "μία υπο-κουκκίδα με «-».",
    "format:no_bullets_bullets":
        "Η απάντηση πρέπει να έχει πρώτα τουλάχιστον δύο προτάσεις που κλείνουν με τελεία και "
        "μετά τουλάχιστον δύο κουκκίδες που ξεκινούν με «*», χωρίς τίποτα άλλο στο τέλος.",
    "custom:multiples":
        "Μέτρα από το 10 ως το 50, αλλά γράψε μόνο τα πολλαπλάσια του 7.",
    "custom:mcq_count_length":
        "Φτιάξε 4 ερωτήσεις πολλαπλής επιλογής με 5 επιλογές η καθεμία για την «ιστορία της τέχνης "
        "του 20ού αιώνα». Κάθε ερώτηση να ξεκινά με την ετικέτα «Ερώτηση» και τον αριθμό της, "
        "και οι επιλογές να σημειώνονται με Α) Β) Γ) Δ) Ε). Οι ερωτήσεις να γίνονται σταδιακά "
        "μεγαλύτερες. Μην δώσεις καμία εξήγηση.",
    "custom:reverse_newline":
        "Γράψε τις χώρες της Αφρικής σε αντίστροφη αλφαβητική σειρά σύμφωνα με το ελληνικό "
        "αλφάβητο, κάθε μία σε νέα γραμμή.",
    "custom:word_reverse":
        "Τι χρώμα έχει η θάλασσα; Απάντησε με την πρόταση «Η θάλασσα είναι γαλάζια», γράφοντας "
        "όμως τις λέξεις της με αντίστροφη σειρά.",
    # cross-check #8: the target now contains a final sigma, so the ς rule is actually exercised.
    "custom:character_reverse":
        "Τι χρώμα έχει ο ουρανός; Απάντησε με την πρόταση «Ο ουρανός είναι γαλάζιος», γράφοντας "
        "όμως όλους τους χαρακτήρες της με αντίστροφη σειρά, με τους τόνους και το τελικό σίγμα "
        "ακριβώς όπως πέφτουν.",
    "custom:sentence_alphabet":
        "Πες μου μια ιστορία {N} προτάσεων, όπου η πρώτη λέξη κάθε πρότασης αρχίζει με τα "
        "γράμματα του ελληνικού αλφαβήτου στη σειρά, από το «α» ως το «ω».",
    # cross-check #7 (amended -- see the note on EuropeanCapitalsSortChecker): the reference set is
    # named exactly so that Κίεβο is not invited, WITHOUT the false «27 κράτη-μέλη της ΕΕ» claim.
    "custom:european_capitals_sort":
        "Γράψε τα ονόματα όλων των πρωτευουσών των ευρωπαϊκών κρατών —των 27 κρατών-μελών της "
        "Ευρωπαϊκής Ένωσης και της ΕΖΕΣ (Ισλανδία, Νορβηγία, Ελβετία, Λιχτενστάιν), καθώς και "
        "του Ηνωμένου Βασιλείου, της Ρωσίας, της Λευκορωσίας και της Μολδαβίας— που βρίσκονται "
        "σε γεωγραφικό πλάτος μεγαλύτερο από 45 μοίρες· είναι 27 πρωτεύουσες συνολικά. Μόνο τις "
        "πρωτεύουσες, χωρίς τα κράτη, χωρισμένες με κόμματα, ταξινομημένες από το μεγαλύτερο "
        "προς το μικρότερο γεωγραφικό πλάτος.",
    "custom:csv_city":
        "Δημιούργησε δεδομένα CSV: οι στήλες είναι [\"Κωδικός\", \"Χώρα\", \"Πόλη\", \"Έτος\", "
        "\"Πλήθος\"] και τα δεδομένα χωρίζονται με κόμμα. Δώσε 7 γραμμές δεδομένων και "
        "χρησιμοποίησε τελεία για τα δεκαδικά, ποτέ κόμμα.",
    "custom:csv_special_character":
        "Δημιούργησε δεδομένα CSV: οι στήλες είναι [\"ΚωδικόςΠροϊόντος\", \"Κατηγορία\", "
        "\"Μάρκα\", \"Τιμή\", \"Απόθεμα\"] και τα δεδομένα χωρίζονται με κόμμα. Δώσε 14 γραμμές "
        "δεδομένων και βάλε ένα πεδίο που περιέχει ειδικό χαρακτήρα μέσα σε διπλά εισαγωγικά. "
        "Χρησιμοποίησε τελεία για τα δεκαδικά, ποτέ κόμμα.",
    "custom:csv_quotes":
        "Δημιούργησε δεδομένα CSV: οι στήλες είναι [\"ΚωδικόςΜαθητή\", \"Μάθημα\", \"Βαθμός\", "
        "\"Εξάμηνο\", \"Μονάδες\"] και τα δεδομένα χωρίζονται με στηλοθέτη (tab). Δώσε 3 γραμμές "
        "δεδομένων και κλείσε κάθε πεδίο σε διπλά εισαγωγικά.",
    "custom:date_format_list":
        "Γράψε τις ημερομηνίες έναρξης όλων των μαχών του Ναπολέοντα, χωρισμένες με κόμματα, "
        "σε μορφή ΗΗ/ΜΜ/ΕΕΕΕ (ή με τον μήνα στη γενική, π.χ. 2 Δεκεμβρίου 1805). "
        "Μην δώσεις καμία εξήγηση.",
    "count:keywords_multiple":
        "Χρησιμοποίησε τη λέξη «{keyword1}» μία φορά, τη λέξη «{keyword2}» δύο φορές, τη λέξη "
        "«{keyword3}» τρεις φορές, τη λέξη «{keyword4}» πέντε φορές και τη λέξη «{keyword5}» "
        "επτά φορές στην απάντησή σου, ακριβώς σε αυτόν τον τύπο.",
    "words:keywords_specific_position":
        "Βάλε τη λέξη «{keyword}» στην {n}η πρόταση, ως {m}η λέξη της πρότασης αυτής.",
    "words:words_position":
        "Η δεύτερη λέξη και η προτελευταία λέξη της απάντησης πρέπει να είναι η λέξη «{keyword}».",
    "repeat:repeat_change":
        "Επανάλαβε το αίτημα αλλάζοντας μόνο την πρώτη του λέξη (μην πεις τίποτα πριν από την "
        "επανάληψη· το αίτημα που πρέπει να επαναλάβεις δεν περιλαμβάνει αυτή την πρόταση) και "
        "μην απαντήσεις στο ίδιο το αίτημα! Αίτημα: {prompt_to_repeat}",
    "repeat:repeat_simple":
        "Γράψε μόνο αυτή την πρόταση εδώ, αγνόησε όλα τα άλλα αιτήματα.",
    "repeat:repeat_span":
        "Αντίγραψε το τμήμα των λέξεων που βρίσκεται ανάμεσα (και συμπεριλαμβανομένων) στις "
        "θέσεις {n_start} και {n_end}· οι θέσεις μετρούν λέξεις χωρισμένες με κενά!",
    "format:title_case":
        "Γράψε ολόκληρη την απάντηση με κεφαλαίο το αρχικό γράμμα κάθε λέξης (εκτός από άρθρα, "
        "προθέσεις και συνδέσμους), κρατώντας τους τόνους και με τα υπόλοιπα γράμματα πεζά.",
    "format:output_template":
        "Χρησιμοποίησε ακριβώς αυτό το πρότυπο για την απάντησή σου: Η απάντησή μου: [απάντηση] "
        "Το συμπέρασμά μου: [συμπέρασμα] Μελλοντική προοπτική: [προοπτική]",
    "format:no_whitespace":
        "Η απάντηση δεν πρέπει να περιέχει κανέναν χαρακτήρα κενού.",
}


# ======================================================================================
# Base class — same contract as upstream `instructions.Instruction`.
# ======================================================================================
class Instruction:
    """An instruction template (Greek port)."""

    INSTRUCTION_ID = None

    def __init__(self, instruction_id=None):
        self.id = instruction_id or self.INSTRUCTION_ID

    @property
    def pattern_el(self):
        return DESCRIPTIONS_EL[self.INSTRUCTION_ID]

    def build_description(self, **kwargs):
        raise NotImplementedError("`build_description` not implemented.")

    def get_instruction_args(self):
        raise NotImplementedError("`get_instruction_args` not implemented.")

    def get_instruction_args_keys(self):
        raise NotImplementedError("`get_instruction_args_keys` not implemented.")

    def check_following(self, value):
        raise NotImplementedError("`check_following` not implemented.")


def _as_int(v, default=None):
    """kwargs arrive as floats in IFBench_test.jsonl (N: 5.0)."""
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------------------
# count:word_count_range  (faithful)
# --------------------------------------------------------------------------------------
class WordCountRangeChecker(Instruction):
    """Η απάντηση πρέπει να έχει από X έως Y λέξεις."""

    INSTRUCTION_ID = "count:word_count_range"

    def build_description(self, *, min_words=None, max_words=None):
        self._min_words = _as_int(min_words, -1)
        self._max_words = _as_int(max_words, -1)
        if self._min_words is None or self._min_words < 0:
            self._min_words = random.randint(100, 500)
        if self._max_words is None or self._max_words < 0:
            self._max_words = self._min_words + random.randint(
                int(self._min_words * 0.05), int(self._min_words * 0.1))
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(min_words=self._min_words,
                                                max_words=self._max_words)

    def get_instruction_args(self):
        return {"min_words": self._min_words, "max_words": self._max_words}

    def get_instruction_args_keys(self):
        return ["min_words", "max_words"]

    def check_following(self, value):
        # word count uses the greek_if `words()` convention (Greek + Latin + digits,
        # internal apostrophe/hyphen kept: «σ’ αυτό» = 2 words, «Γουινέα-Μπισάου» = 1)
        return self._min_words <= len(words_el(value)) <= self._max_words


# --------------------------------------------------------------------------------------
# count:unique_word_count  (adapt)
# --------------------------------------------------------------------------------------
class UniqueWordCountChecker(Instruction):
    """Τουλάχιστον N διαφορετικές λέξεις."""

    INSTRUCTION_ID = "count:unique_word_count"

    def build_description(self, *, N=None):
        self._num_unique_words = _as_int(N, -1)
        if self._num_unique_words is None or self._num_unique_words < 0:
            self._num_unique_words = random.randint(100, 500)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self._num_unique_words)

    def get_instruction_args(self):
        return {"N": self._num_unique_words}

    def get_instruction_args_keys(self):
        return ["N"]

    def check_following(self, value):
        # Types are folded (case/accent/final-sigma insensitive).  NOTE: Greek inflection
        # still inflates the count — «λέξη» and «λέξεις» are two types.  Documented in
        # TRANSFER_ANALYSIS §C; no lemmatiser is available without third-party deps.
        return len({fold(t) for t in toks(value)}) >= self._num_unique_words


# --------------------------------------------------------------------------------------
# ratio:stop_words  (adapt)
# --------------------------------------------------------------------------------------
class StopWordPercentageChecker(Instruction):
    """Οι λέξεις-εργαλεία να μην ξεπερνούν το X% των λέξεων."""

    INSTRUCTION_ID = "ratio:stop_words"

    def build_description(self, *, percentage=None):
        self._percentage = _as_int(percentage, -1)
        if self._percentage is None or self._percentage < 0:
            self._percentage = random.randint(1, 100)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(percentage=self._percentage)

    def get_instruction_args(self):
        return {"percentage": self._percentage}

    def get_instruction_args_keys(self):
        return ["percentage"]

    def check_following(self, value):
        tokens = words_el(value)
        if not tokens:
            return False
        # accent-sensitive lookup: «που»/«πως» are stop words, «πού»/«πώς» are not
        num_stop = sum(1 for t in tokens if nfc(t).lower() in STOP_WORDS_EL)
        return (num_stop / len(tokens)) * 100 <= self._percentage


# --------------------------------------------------------------------------------------
# ratio:sentence_type  (adapt)
# --------------------------------------------------------------------------------------
class SentTypeRatioChecker(Instruction):
    """Αναλογία 2:1 αποφαντικών προς ερωτηματικές."""

    INSTRUCTION_ID = "ratio:sentence_type"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        declarative = sum(1 for s in sentences if is_declarative(s))
        interrogative = sum(1 for s in sentences if is_interrogative(s))
        # cross-check #11 (RETUNED, deliberate tightening): ≥1 interrogative, so an answer with
        # no terminators at all no longer passes on 0 == 2*0.  The description says so.
        if interrogative < 1:
            return False
        return declarative == 2 * interrogative


# --------------------------------------------------------------------------------------
# ratio:sentence_balance  (adapt)
# --------------------------------------------------------------------------------------
class SentBalanceChecker(Instruction):
    """Ισάριθμες αποφαντικές / ερωτηματικές / θαυμαστικές."""

    INSTRUCTION_ID = "ratio:sentence_balance"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        d = sum(1 for s in sentences if is_declarative(s))
        i = sum(1 for s in sentences if is_interrogative(s))
        e = sum(1 for s in sentences if is_exclamatory(s))
        # cross-check #11 (RETUNED, deliberate tightening): ≥1 of each type, so 0 == 0 == 0 is
        # no longer a free pass.  The description says so.
        if min(d, i, e) < 1:
            return False
        return d == i == e


# --------------------------------------------------------------------------------------
# count:conjunctions  (adapt)
# --------------------------------------------------------------------------------------
class ConjunctionCountChecker(Instruction):
    """Τουλάχιστον small_n διαφορετικοί παρατακτικοί σύνδεσμοι."""

    INSTRUCTION_ID = "count:conjunctions"

    def build_description(self, *, small_n=None):
        self._num_conjunctions = _as_int(small_n, -1)
        if self._num_conjunctions is None or self._num_conjunctions < 0:
            self._num_conjunctions = random.randint(2, 6)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(small_n=self._num_conjunctions)

    def get_instruction_args(self):
        return {"small_n": self._num_conjunctions}

    def get_instruction_args_keys(self):
        return ["small_n"]

    def check_following(self, value):
        found = set()
        for t in toks(value):
            # accent-sensitive: the conjunction «ή» must not be matched by the article «η»
            w = nfc(t).lower()
            if w in CONJUNCTIONS_EL:
                found.add(_CONJ_LEMMA.get(w, w))   # και / κι = one type
        return len(found) >= self._num_conjunctions


# --------------------------------------------------------------------------------------
# count:person_names  (adapt)
# --------------------------------------------------------------------------------------
class PersonNameCountChecker(Instruction):
    """Τουλάχιστον N διαφορετικά ελληνικά ονόματα προσώπων."""

    INSTRUCTION_ID = "count:person_names"

    def build_description(self, *, N=None):
        self._num_person_names = _as_int(N, -1)
        if self._num_person_names is None or self._num_person_names < 0:
            self._num_person_names = random.randint(1, 50)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self._num_person_names,
                                                names=", ".join(NAMES_EL))

    def get_instruction_args(self):
        return {"N": self._num_person_names}

    def get_instruction_args_keys(self):
        return ["N"]

    def check_following(self, value):
        # Count LEMMAS, not surface forms: any case form of the same name counts once.
        present = {fold(t) for t in toks(value)}
        found = {lemma for lemma, forms in NAME_FORMS_EL.items() if forms & present}
        return len(found) >= self._num_person_names


# --------------------------------------------------------------------------------------
# ratio:overlap  (adapt)
# --------------------------------------------------------------------------------------
class NGramOverlapChecker(Instruction):
    """Επικάλυψη τριγράμμων X% (±2%) με το κείμενο αναφοράς."""

    INSTRUCTION_ID = "ratio:overlap"

    def build_description(self, *, reference_text=None, percentage=None):
        self._reference_text = reference_text
        self._percentage = _as_int(percentage, -1)
        if self._percentage is None or self._percentage < 0:
            self._percentage = random.randint(1, 100)
        self._description_pattern = self.pattern_el
        # cross-check #1: render the reference text INTO the prompt so it is identifiable.
        return self._description_pattern.format(
            percentage=self._percentage,
            reference_text=(self._reference_text or "").strip())

    def get_instruction_args(self):
        return {"reference_text": self._reference_text, "percentage": self._percentage}

    def get_instruction_args_keys(self):
        return ["reference_text", "percentage"]

    @staticmethod
    def _trigrams(text):
        t = [fold(x) for x in toks(text)]           # folded tokens, Greek-aware
        return {tuple(t[i:i + 3]) for i in range(len(t) - 2)}

    def check_following(self, value):
        if not self._reference_text:
            return False
        ngrams = self._trigrams(value)
        if not ngrams:
            return False
        ref = self._trigrams(self._reference_text)
        overlap = len(ngrams & ref) / len(ngrams)
        return self._percentage - 2 <= overlap * 100 <= self._percentage + 2


# --------------------------------------------------------------------------------------
# count:numbers  (adapt)
# --------------------------------------------------------------------------------------
_NUMBER_RE = re.compile(r"\d+(?:[.,:/\-]\d+)*")


class NumbersCountChecker(Instruction):
    """Ακριβώς N αριθμοί με ψηφία."""

    INSTRUCTION_ID = "count:numbers"

    def build_description(self, *, N=None):
        self._count_numbers = _as_int(N, -1)
        if self._count_numbers is None or self._count_numbers < 0:
            self._count_numbers = random.randint(1, 6)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self._count_numbers)

    def get_instruction_args(self):
        return {"N": self._count_numbers}

    def get_instruction_args_keys(self):
        return ["N"]

    def check_following(self, value):
        # Greek writes thousands with '.' and decimals with ',': 1.234,56 is ONE number.
        # Dates/fractions/times joined by / - : also count as one, as upstream's
        # punctuation-stripping did.  Greek letter numerals (ιθ΄) are not digits.
        return len(_NUMBER_RE.findall(nfc(value))) == self._count_numbers


# --------------------------------------------------------------------------------------
# words:alphabet  (adapt)
# --------------------------------------------------------------------------------------
class AlphabetLoopChecker(Instruction):
    """Κάθε λέξη ξεκινά με το επόμενο γράμμα του αλφαβήτου (κύκλος 24)."""

    INSTRUCTION_ID = "words:alphabet"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        tokens = toks(value)
        if not tokens:
            return False
        first = fold(tokens[0])[:1]                 # ς ≡ σ through fold
        if first not in _ALPHA_INDEX:
            return False
        idx = _ALPHA_INDEX[first]
        for tok in tokens[1:]:
            f = fold(tok)
            if not f:
                continue
            idx = (idx + 1) % 24                    # 24-letter cycle, not 26
            if f[0] != GREEK_ALPHABET[idx]:
                return False
        return True


# --------------------------------------------------------------------------------------
# words:vowel  (adapt, RETUNED ≤4)
# --------------------------------------------------------------------------------------
class SingleVowelParagraphChecker(Instruction):
    """Μία παράγραφος με το πολύ 4 διαφορετικά φωνήεντα."""

    INSTRUCTION_ID = "words:vowel"
    MAX_VOWELS = RETUNED["words:vowel"]["greek"]

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        paragraphs = value.strip().split("\n")
        if len(paragraphs) != 1:
            return False
        # diacritics dropped first: ά/ᾶ/ϊ are the same vowel letter as α/ι
        used = {c for c in fold(paragraphs[0]) if c in GREEK_VOWELS}
        return len(used) <= self.MAX_VOWELS


# --------------------------------------------------------------------------------------
# words:consonants  (adapt)
# --------------------------------------------------------------------------------------
class ConsonantClusterChecker(Instruction):
    """Κάθε λέξη με σύμπλεγμα συμφώνων (ή ξ/ψ)."""

    INSTRUCTION_ID = "words:consonants"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        for tok in toks(value):
            w = fold(tok)
            # ξ and ψ are single glyphs spelling a cluster (κσ / πσ) — they qualify alone
            if any(c in GREEK_DOUBLE_CONSONANTS for c in w):
                continue
            if not any(w[i] in GREEK_CONSONANTS and w[i + 1] in GREEK_CONSONANTS
                       for i in range(len(w) - 1)):
                return False
        return True


# --------------------------------------------------------------------------------------
# sentence:alliteration_increment  (adapt)
# --------------------------------------------------------------------------------------
class IncrementingAlliterationChecker(Instruction):
    """Αύξουσα παρήχηση ανά πρόταση."""

    INSTRUCTION_ID = "sentence:alliteration_increment"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        prev_score = -1
        for sentence in sentences:
            initials = [fold(t)[0] for t in toks(sentence) if fold(t)]
            score, running = 0, False
            for i in range(len(initials) - 1):
                if initials[i] == initials[i + 1]:   # initial of the folded token
                    score += 1 if running else 2
                    running = True
                else:
                    running = False
            if score <= prev_score:
                return False
            prev_score = score
        return True


# --------------------------------------------------------------------------------------
# words:palindrome  (adapt, RETUNED N=3)
# --------------------------------------------------------------------------------------
class PalindromeChecker(Instruction):
    """Τουλάχιστον 3 καρκινικές λέξεις ≥5 γραμμάτων."""

    INSTRUCTION_ID = "words:palindrome"
    NUM_PALINDROMES = RETUNED["words:palindrome"]["greek"]

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self.NUM_PALINDROMES)

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # folded comparison: ΣΑΡΑΣ/σαρας reads the same backwards once ς ≡ σ and the
        # tonos is dropped (νομονόμον → νομονομον)
        found = [w for w in (fold(t) for t in toks(value)) if len(w) >= 5 and w == w[::-1]]
        return len(found) >= self.NUM_PALINDROMES


# --------------------------------------------------------------------------------------
# count:punctuation  (adapt)
# --------------------------------------------------------------------------------------
class PunctuationCoverChecker(Instruction):
    """Όλα τα σημεία στίξης + ο συνδυασμός «!;»."""

    INSTRUCTION_ID = "count:punctuation"
    REQUIRED = (".", ",", "!", ";", ":", "·")   # '?' is not Greek punctuation

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # NFC maps ';' (U+037E) onto ';' and '·' (U+0387) onto '·'
        v = nfc(value)
        if not ("!;" in v or ";!" in v or "‽" in v):
            return False
        new_v = v.replace("!;", "", 1)
        if len(new_v) == len(v):
            new_v = v.replace(";!", "", 1)
        remaining = set(self.REQUIRED)
        for ch in new_v:
            remaining.discard(ch)
        return not remaining


# --------------------------------------------------------------------------------------
# format:parentheses  (faithful)
# --------------------------------------------------------------------------------------
class NestedParenthesesChecker(Instruction):
    """Φώλιασμα παρενθέσεων ≥5 επιπέδων."""

    INSTRUCTION_ID = "format:parentheses"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        levels, min_levels, max_depth = [], 5, 0
        for char in value:
            if char in "([{":
                levels.append(char)
                max_depth = max(max_depth, len(levels))
            elif char in ")]}":
                if levels and ((levels[-1] == "(" and char == ")")
                               or (levels[-1] == "[" and char == "]")
                               or (levels[-1] == "{" and char == "}")):
                    levels.pop()
                    if max_depth >= min_levels and len(levels) < max_depth:
                        return True
                else:
                    levels, max_depth = [], 0
        return False


# --------------------------------------------------------------------------------------
# format:quotes  (adapt)
# --------------------------------------------------------------------------------------
class NestedQuotesChecker(Instruction):
    """Φώλιασμα εισαγωγικών ≥3 επιπέδων με ελληνική ιεραρχία."""

    INSTRUCTION_ID = "format:quotes"
    # Greek quote hierarchy: « » outermost, then “ ”, then ‘ ’; ASCII " ' accepted too.
    OPEN_TO_CLOSE = {"«": "»", "“": "”", "‘": "’",
                     "„": "“", '"': '"', "'": "'"}

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # a letter-flanked or elision ’ («σ’ αυτό») is an apostrophe, never a delimiter
        v = strip_elision_apostrophes(nfc(value))
        stack, reached, depth = [], 0, 0
        for char in v:
            if stack and char == stack[-1]:
                stack.pop()
                depth -= 1
                if reached - depth >= 3:
                    return True
            elif char in self.OPEN_TO_CLOSE:
                stack.append(self.OPEN_TO_CLOSE[char])
                depth += 1
                reached = max(reached, depth)
        return False


# --------------------------------------------------------------------------------------
# words:prime_lengths  (adapt)
# --------------------------------------------------------------------------------------
_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
           73, 79, 83, 89, 97}


class PrimeLengthsChecker(Instruction):
    """Μόνο λέξεις με πλήθος γραμμάτων πρώτο αριθμό."""

    INSTRUCTION_ID = "words:prime_lengths"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # length = NFC codepoints, so a tonos never adds a character (ά = 1, not 2)
        return all(len(nfc(t)) in _PRIMES for t in toks(value))


# --------------------------------------------------------------------------------------
# format:options  (adapt)
# --------------------------------------------------------------------------------------
class OptionsResponseChecker(Instruction):
    """Απάντηση με μία από τις δοσμένες επιλογές."""

    INSTRUCTION_ID = "format:options"

    def build_description(self, *, options=None):
        options_bank = list(OPTIONS_MAP_EL.values())
        if options is None:
            options = random.choice(options_bank)
        # §D kwargs rule: an English option bank from upstream data maps onto the Greek one
        options = OPTIONS_MAP_EL.get(options.strip(), options)
        # multiple-choice letters are matched strictly, text options leniently
        self._strict = re.match(r"\W*[αΑaA]\W*[βΒbB]\W*[γΓcC]\W*",
                                self._label_norm(options)) is not None
        if "/" in options:
            separator = "/"
        elif " ή " in options:                      # Greek disjunction, upstream's "or"
            separator = " ή "
        else:
            separator = ","
        self._options = [o.strip() for o in options.split(separator)]
        self._options_text = options
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(options=self._options_text)

    def get_instruction_args(self):
        return {"options": self._options_text}

    def get_instruction_args_keys(self):
        return ["options"]

    @staticmethod
    def _label_norm(s):
        """cross-check #9: labels are case-insensitive and Latin/Greek uppercase homoglyphs
        (A B C D E / Α Β Γ Δ Ε) fold onto the lowercase Greek labels α β γ δ ε."""
        return degreek_homoglyphs(nfc(s).lower())

    def check_following(self, value):
        if self._strict:
            # cross-check #9: «Α)», «A)», «α)» and «a)» are all the same option label
            v = self._label_norm(value).strip()
            return v in [self._label_norm(o).strip() for o in self._options]
        # cross-check #9: the same label normalisation also applies in loose mode
        v = fold(self._label_norm(value)).strip(_PUNCT_CHARS + " ")
        return any(fold(self._label_norm(o)).strip(_PUNCT_CHARS + " ") == v
                   for o in self._options)


# --------------------------------------------------------------------------------------
# format:newline  (faithful)
# --------------------------------------------------------------------------------------
class NewLineWordsChecker(Instruction):
    """Κάθε λέξη σε δική της γραμμή."""

    INSTRUCTION_ID = "format:newline"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        v = drop_punct(value)
        lines = [l for l in v.strip().split("\n") if l.strip()]
        return len(lines) == len(v.strip().split())


# --------------------------------------------------------------------------------------
# format:emoji  (adapt — P1 splitter with the Greek abbreviations)
# --------------------------------------------------------------------------------------
class EmojiSentenceChecker(Instruction):
    """Ένα emoji στο τέλος κάθε πρότασης."""

    INSTRUCTION_ID = "format:emoji"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if not sentences:
            return False
        for i, sentence in enumerate(sentences):
            stripped = drop_punct(sentence).strip()
            if not stripped:
                return False
            last_char = stripped[-1]
            second_last = stripped[-2] if len(stripped) > 1 else stripped[-1]
            if not is_emoji(last_char) and not is_emoji(second_last):
                if i < len(sentences) - 1:
                    nxt = drop_punct(sentences[i + 1]).strip()
                    if not nxt or not is_emoji(nxt[0]):
                        return False
                else:
                    return False
        return True


# --------------------------------------------------------------------------------------
# ratio:sentence_words  (adapt)
# --------------------------------------------------------------------------------------
class CharacterCountUniqueWordsChecker(Instruction):
    """Τρεις προτάσεις ίδιου μήκους, χωρίς επανάληψη λέξης."""

    INSTRUCTION_ID = "ratio:sentence_words"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if len(sentences) != 3:
            return False
        # NFC codepoint count: a precomposed ά must not count as two characters
        char_count = len(nfc(sentences[0].strip()))
        if any(len(nfc(s.strip())) != char_count for s in sentences):
            return False
        # word identity is folded («Θάλασσα» == «θάλασσα»)
        w = [fold(t) for t in toks(" ".join(sentences))]
        return len(w) == len(set(w))


# --------------------------------------------------------------------------------------
# count:words_japanese  (faithful)
# --------------------------------------------------------------------------------------
class NthWordJapaneseChecker(Instruction):
    """Κάθε Nη λέξη στα ιαπωνικά."""

    INSTRUCTION_ID = "count:words_japanese"
    _JAPANESE = re.compile(r"[぀-ヿ一-鿿]")

    def build_description(self, *, N=None):
        self._japanese_position = _as_int(N, -1)
        if self._japanese_position is None or self._japanese_position < 0:
            self._japanese_position = random.randint(1, 30)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self._japanese_position)

    def get_instruction_args(self):
        return {"N": self._japanese_position}

    def get_instruction_args_keys(self):
        return ["N"]

    def check_following(self, value):
        tokens = [t.strip(_PUNCT_CHARS) for t in value.split()]
        for i, word in enumerate(tokens):
            if (i + 1) % self._japanese_position == 0 and word and not word.isdigit():
                if not self._JAPANESE.search(word):
                    return False
        return True


# --------------------------------------------------------------------------------------
# words:start_verb  (adapt)
# --------------------------------------------------------------------------------------
class StartWithVerbChecker(Instruction):
    """Η απάντηση ξεκινά με ρήμα."""

    INSTRUCTION_ID = "words:start_verb"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        tokens = toks(value)
        # no POS tagger: Greek verb endings + an imperative whitelist (see looks_like_verb_el)
        return bool(tokens) and looks_like_verb_el(tokens[0])


# --------------------------------------------------------------------------------------
# words:repeats  (adapt, RETUNED small_n floored at 5)
# --------------------------------------------------------------------------------------
class LimitedWordRepeatChecker(Instruction):
    """Καμία λέξη πάνω από small_n φορές."""

    INSTRUCTION_ID = "words:repeats"
    MIN_SMALL_N = RETUNED["words:repeats"]["greek"]

    @classmethod
    def effective_small_n(cls, small_n=None):
        """cross-check #3: the ONE value the prompt states and the checker enforces.

        kwargs keep the upstream `small_n`; the RETUNED floor (Greek function words recur
        unavoidably) is applied here so build_description() and check_following() can never
        disagree about the number the answer is graded against.
        """
        n = _as_int(small_n, -1)
        if n is None or n < 0:
            n = random.randint(1, 5)
        return max(n, cls.MIN_SMALL_N)

    def build_description(self, *, small_n=None, small_n_upstream=None):
        # cross-check #3: `small_n_upstream` is the un-floored kwarg the assembler records; it is
        # accepted and ignored here so the effective value stays the single source of truth.
        self._small_n_upstream = _as_int(small_n_upstream, None)
        self._max_repeats = self.effective_small_n(small_n)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(small_n=self._max_repeats)

    def get_instruction_args(self):
        return {"small_n": self._max_repeats}

    def get_instruction_args_keys(self):
        return ["small_n"]

    def check_following(self, value):
        counts = Counter(fold(t) for t in toks(value))
        # cross-check #3: the same effective value that build_description() put in the prompt
        return all(c <= self._max_repeats for c in counts.values())


# --------------------------------------------------------------------------------------
# sentence:keyword  (adapt)
# --------------------------------------------------------------------------------------
class IncludeKeywordChecker(Instruction):
    """Η Nη πρόταση περιέχει τη λέξη word."""

    INSTRUCTION_ID = "sentence:keyword"

    def build_description(self, *, word=None, N=None):
        self._keyword = word if word else random.choice(
            ["θάλασσα", "σχολείο", "χρόνος", "ευθύνη", "παράδειγμα"])
        self._keyword_position = _as_int(N, -1)
        if self._keyword_position is None or self._keyword_position < 0:
            self._keyword_position = random.randint(1, 20)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(word=self._keyword,
                                                N=self._keyword_position)

    def get_instruction_args(self):
        return {"word": self._keyword, "N": self._keyword_position}

    def get_instruction_args_keys(self):
        return ["word", "N"]

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if len(sentences) < self._keyword_position:
            return False
        # containment id -> stem match, so θάλασσα is satisfied by θάλασσας/θάλασσες
        return contains_stem(sentences[self._keyword_position - 1], self._keyword)


# --------------------------------------------------------------------------------------
# count:pronouns  (adapt)
# --------------------------------------------------------------------------------------
class PronounCountChecker(Instruction):
    """Τουλάχιστον N αντωνυμίες."""

    INSTRUCTION_ID = "count:pronouns"

    def build_description(self, *, N=None):
        self._num_pronouns = _as_int(N, -1)
        if self._num_pronouns is None or self._num_pronouns < 0:
            self._num_pronouns = random.randint(1, 25)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self._num_pronouns)

    def get_instruction_args(self):
        return {"N": self._num_pronouns}

    def get_instruction_args_keys(self):
        return ["N"]

    def check_following(self, value):
        # '/' separates pronoun sets («αυτός/αυτή»), same normalisation as upstream
        tokens = toks(nfc(value).replace("/", " "))
        folded = [fold(t) for t in tokens]
        strong = {fold(p) for p in PRONOUNS_EL_UNAMBIGUOUS}
        clitics = {fold(p) for p in PRONOUNS_EL_HOMOGRAPH}
        count = 0
        for i, w in enumerate(folded):
            if w in strong:
                count += 1
            elif w in clitics:
                # homograph rule: article before a noun («του σπιτιού») does not count;
                # a clitic before a verb («μου είπε») or at the end of a clause does.
                nxt = folded[i + 1] if i + 1 < len(folded) else None
                if nxt is None or looks_like_verb_el(nxt):
                    count += 1
        return count >= self._num_pronouns


# --------------------------------------------------------------------------------------
# words:odd_even_syllables  (adapt)
# --------------------------------------------------------------------------------------
class AlternateParitySyllablesChecker(Instruction):
    """Εναλλαγή μονών/ζυγών συλλαβών."""

    INSTRUCTION_ID = "words:odd_even_syllables"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        parity = [count_syllables_el(t) % 2 for t in toks(value)]
        return all(parity[i] != parity[i + 1] for i in range(len(parity) - 1))


# --------------------------------------------------------------------------------------
# words:last_first  (adapt)
# --------------------------------------------------------------------------------------
class LastWordFirstNextChecker(Instruction):
    """Η τελευταία λέξη κάθε πρότασης = πρώτη της επόμενης."""

    INSTRUCTION_ID = "words:last_first"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        for i in range(len(sentences) - 1):
            a, b = toks(sentences[i]), toks(sentences[i + 1])
            if not a or not b:
                return False
            if fold(a[-1]) != fold(b[0]):     # folded: «Θάλασσα.» == «θάλασσα»
                return False
        return True


# --------------------------------------------------------------------------------------
# words:paragraph_last_first  (adapt)
# --------------------------------------------------------------------------------------
class ParagraphLastFirstWordMatchChecker(Instruction):
    """Κάθε παράγραφος τελειώνει με τη λέξη που ξεκίνησε."""

    INSTRUCTION_ID = "words:paragraph_last_first"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # paragraph = single newline, as upstream (the Greek prompt states this)
        for paragraph in paragraphs_nl(value):
            tokens = toks(paragraph)
            if not tokens:
                continue
            if fold(tokens[0]) != fold(tokens[-1]):
                return False
        return True


# --------------------------------------------------------------------------------------
# sentence:increment  (adapt)
# --------------------------------------------------------------------------------------
class IncrementingWordCountChecker(Instruction):
    """Κάθε πρόταση με small_n λέξεις περισσότερες."""

    INSTRUCTION_ID = "sentence:increment"

    def build_description(self, *, small_n=None):
        self._num_increment = _as_int(small_n, -1)
        if self._num_increment is None or self._num_increment < 0:
            self._num_increment = random.randint(1, 5)
        self._description_pattern = self.pattern_el
        # cross-check #4: grammatical number -- «1 λέξη περισσότερη», «2 λέξεις περισσότερες»
        words_more = ("λέξη περισσότερη" if self._num_increment == 1
                      else "λέξεις περισσότερες")
        return self._description_pattern.format(small_n=self._num_increment,
                                                words_more=words_more)

    def get_instruction_args(self):
        return {"small_n": self._num_increment}

    def get_instruction_args_keys(self):
        return ["small_n"]

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if not sentences:
            return False
        # P3 tokens: an elided «σ’ αυτό» written with a space counts as two words,
        # «σ’αυτό» as one — the apostrophe is only stripped at token edges.
        prev = len(toks(sentences[0]))
        for sentence in sentences[1:]:
            n = len(toks(sentence))
            if n != prev + self._num_increment:
                return False
            prev = n
        return True


# --------------------------------------------------------------------------------------
# words:no_consecutive  (adapt)
# --------------------------------------------------------------------------------------
class NoConsecutiveFirstLetterChecker(Instruction):
    """Καμία διαδοχική λέξη με το ίδιο αρχικό γράμμα."""

    INSTRUCTION_ID = "words:no_consecutive"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        initials = [fold(t)[0] for t in toks(value) if fold(t)]
        return all(initials[i] != initials[i + 1] for i in range(len(initials) - 1))


# --------------------------------------------------------------------------------------
# format:line_indent  (faithful)
# --------------------------------------------------------------------------------------
class IndentStairsChecker(Instruction):
    """Αύξουσα εσοχή σε κάθε γραμμή."""

    INSTRUCTION_ID = "format:line_indent"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # upstream mutates the list while iterating (a bug that keeps some blank lines);
        # we filter properly, which is the documented intent
        lines = [l for l in value.split("\n") if l.strip()]
        for i in range(len(lines) - 1):
            if (len(lines[i + 1]) - len(lines[i + 1].lstrip(" "))
                    <= len(lines[i]) - len(lines[i].lstrip(" "))):
                return False
        return True


# --------------------------------------------------------------------------------------
# format:quote_unquote  (adapt)
# --------------------------------------------------------------------------------------
class QuoteExplanationChecker(Instruction):
    """Καμία διπλανή παράθεση· το κείμενο δεν τελειώνει σε εισαγωγικό."""

    INSTRUCTION_ID = "format:quote_unquote"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        v = strip_elision_apostrophes(nfc(value))
        # the Greek quote alphabet collapses onto " for the adjacency test
        v = re.sub(r"[«»“”‹›„‘’']", '"', v)
        v = v.replace("'\"'", "")            # a literal reference to the character '"'
        v = "".join(v.split())               # remove all whitespace
        if '""' in v:
            return False
        stripped = v.strip(string.digits + _PUNCT_NO_QUOTE)
        return not (stripped and stripped[-1] == '"')


# --------------------------------------------------------------------------------------
# format:list  (adapt)
# --------------------------------------------------------------------------------------
class SpecialBulletPointsChecker(Instruction):
    """Λίστα με δείκτη sep αντί για κουκκίδες."""

    INSTRUCTION_ID = "format:list"

    def build_description(self, *, sep=None):
        if sep is None:
            sep = random.choice(list(SEP_MAP_EL.values()))
        # §D kwargs rule: SEPARATOR -> ΔΙΑΧΩΡΙΣΤΙΚΟ, !?!? -> !;!;
        self._bullet_marker = SEP_MAP_EL.get(sep, sep)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(sep=self._bullet_marker)

    def get_instruction_args(self):
        return {"sep": self._bullet_marker}

    def get_instruction_args_keys(self):
        return ["sep"]

    def _marker_regex(self):
        pat = re.escape(self._bullet_marker)
        pat = pat.replace(re.escape("..."), r"(?:\.\.\.|…)")   # '…' == '...'
        pat = pat.replace(";", "[;\u037e]")            # either question mark
        return pat

    def check_following(self, value):
        return len(re.findall(self._marker_regex(), nfc(value))) >= 2


# --------------------------------------------------------------------------------------
# format:thesis  (faithful)
# --------------------------------------------------------------------------------------
class ItalicsThesisChecker(Instruction):
    """Θέση σε πλάγια (HTML) ακολουθούμενη από απλό κείμενο."""

    INSTRUCTION_ID = "format:thesis"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        for open_tag, close_tag in (("<i>", "</i>"), ("<em>", "</em>")):
            start = value.find(open_tag)
            if start == -1:
                continue
            rest = value[start + len(open_tag):]
            end = rest.find(close_tag)
            if end == -1:
                continue
            # upstream slices with a hard-coded 3/4 offset (wrong for <em>); fixed here
            if rest[:end].strip() and rest[end + len(close_tag):].strip():
                return True
        return False


# --------------------------------------------------------------------------------------
# format:sub-bullets  (faithful)
# --------------------------------------------------------------------------------------
class SubBulletPointsChecker(Instruction):
    """Κάθε κουκκίδα «*» έχει υπο-κουκκίδα «-»."""

    INSTRUCTION_ID = "format:sub-bullets"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        bullets = value.split("*")
        for bullet in bullets[1:]:
            if "-" not in bullet:
                return False
        return True


# --------------------------------------------------------------------------------------
# format:no_bullets_bullets  (adapt — P1 splitter for the prose head)
# --------------------------------------------------------------------------------------
class SomeBulletPointsChecker(Instruction):
    """Δύο προτάσεις και μετά ≥2 κουκκίδες «*»."""

    INSTRUCTION_ID = "format:no_bullets_bullets"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        lines = value.split("\n")
        in_prose, count_sentences, count_bullets = True, 0, 0
        for line in lines:
            if line.strip().startswith("*"):
                in_prose = False
                if count_sentences < 2:
                    return False
                count_bullets += 1
            elif in_prose:
                if line.strip():
                    count_sentences += len(split_sentences_el(line.strip()))
            elif line.strip():
                return False        # nothing but bullets after the first bullet
        return count_bullets >= 2


# --------------------------------------------------------------------------------------
# custom:multiples  (faithful)
# --------------------------------------------------------------------------------------
class PrintMultiplesChecker(Instruction):
    """Πολλαπλάσια του 7 από το 10 ως το 50."""

    INSTRUCTION_ID = "custom:multiples"

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        value = value.replace(",", ", ")
        numbers = re.findall(r"\d+", value)
        return numbers == [str(i) for i in range(14, 51, 7)]


# --------------------------------------------------------------------------------------
# custom:mcq_count_length  (adapt)
# --------------------------------------------------------------------------------------
class MultipleChoiceQuestionsChecker(Instruction):
    """4 ερωτήσεις «Ερώτηση N» με 5 επιλογές, αύξουσας έκτασης."""

    INSTRUCTION_ID = "custom:mcq_count_length"
    LABEL = "Ερώτηση"
    # option labels Α–Ε / α–ε, plus the Latin homoglyphs A, B, E (a, b, e)
    _OPTION_RE = re.compile(r"^[ΑΒΓΔΕαβγδεABEabe][.)]\s*\S+")

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        value = nfc(value)
        idx = value.find(self.LABEL)
        if idx == -1 or value[idx:] != value:
            return False        # no preamble allowed ("μην δώσεις εξήγηση")
        questions = re.split(rf"\n*(?:{self.LABEL}\s*\d+[.):;]?\s*)", value)
        questions = [q.strip() for q in questions if q.strip()]
        if len(questions) != 4:
            return False
        lengths = []
        for q in questions:
            question_text, option_count, done = "", 0, False
            for line in q.split("\n"):
                if self._OPTION_RE.match(line.strip()):
                    option_count += 1
                    done = True
                elif not done:
                    question_text += " " + line.strip()
            if option_count != 5:
                return False
            lengths.append(len(question_text.strip()))
        return all(lengths[i] < lengths[i + 1] for i in range(len(lengths) - 1))


# --------------------------------------------------------------------------------------
# custom:reverse_newline  (adapt, RETUNED line count)
# --------------------------------------------------------------------------------------
class ReverseNewlineChecker(Instruction):
    """Οι χώρες της Αφρικής σε αντίστροφη αλφαβητική σειρά."""

    INSTRUCTION_ID = "custom:reverse_newline"
    MIN_LINES = RETUNED["custom:reverse_newline"]["greek"]

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        lines = [l.strip(_PUNCT_CHARS + " ") for l in nfc(value).split("\n")]
        lines = [l for l in lines if l]
        anchor = fold(REVERSE_NEWLINE_ANCHOR)
        try:
            start = next(i for i, l in enumerate(lines) if anchor in fold(l))
        except StopIteration:
            return False
        target = lines[start:]
        if len(target) < self.MIN_LINES:
            return False
        # NFD -> drop Mn -> NFC inside fold(): never ASCII-fold, that would erase Greek.
        keys = [greek_sort_key(l) for l in target]
        return keys == sorted(keys, reverse=True)


# --------------------------------------------------------------------------------------
# custom:word_reverse  (replace — Greek self-contained task, §D)
# --------------------------------------------------------------------------------------
class WordReverseOrderChecker(Instruction):
    """«Η θάλασσα είναι γαλάζια» με αντίστροφη σειρά λέξεων."""

    INSTRUCTION_ID = "custom:word_reverse"
    TARGET_SENTENCE = "Η θάλασσα είναι γαλάζια"

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # word order is a matching task -> folded comparison (accents/case irrelevant)
        v = " ".join(fold(t) for t in toks(value)[::-1])
        if fold(self.TARGET_SENTENCE).strip() not in v:
            return False
        # and the un-reversed answer must be a single sentence
        return len(split_sentences_el(value)) == 1


# --------------------------------------------------------------------------------------
# custom:character_reverse  (replace — exact orthography, §D)
# --------------------------------------------------------------------------------------
class CharacterReverseOrderChecker(Instruction):
    """«Ο ουρανός είναι γαλάζιος» με αντίστροφη σειρά χαρακτήρων."""

    INSTRUCTION_ID = "custom:character_reverse"
    # cross-check #8: the target carries a FINAL SIGMA (ουρανός, γαλάζιος) so the exact-orthography
    # ς rule is actually exercised; «Η θάλασσα είναι γαλάζια» never tested it.
    TARGET_SENTENCE = "Ο ουρανός είναι γαλάζιος"

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    @classmethod
    def expected(cls):
        """The exact reversal: accents stay where they fall, ς stays ς."""
        return nfc(cls.TARGET_SENTENCE)[::-1]

    def check_following(self, value):
        # EXACT ORTHOGRAPHY: no fold() here — ς is NOT folded to σ and the tonos is not
        # stripped; only the sentence-initial capital is case-normalised.
        v = nfc(value)
        expected = self.expected()
        return expected in v or expected.lower() in v.lower()


# --------------------------------------------------------------------------------------
# custom:sentence_alphabet  (adapt, RETUNED 24)
# --------------------------------------------------------------------------------------
class SentenceAlphabetChecker(Instruction):
    """24 προτάσεις με αρχικά α…ω."""

    INSTRUCTION_ID = "custom:sentence_alphabet"
    NUM_SENTENCES = RETUNED["custom:sentence_alphabet"]["greek"]

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(N=self.NUM_SENTENCES)

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if len(sentences) != self.NUM_SENTENCES:
            return False
        for i, sentence in enumerate(sentences):
            stripped = fold(sentence).lstrip(_PUNCT_CHARS + string.whitespace)
            if not stripped:
                return False
            if stripped[0] != GREEK_ALPHABET[i]:    # ς ≡ σ via fold
                return False
        return True


# --------------------------------------------------------------------------------------
# custom:european_capitals_sort  (adapt)
# --------------------------------------------------------------------------------------
class EuropeanCapitalsSortChecker(Instruction):
    """Οι 27 πρωτεύουσες κατά φθίνον γεωγραφικό πλάτος.

    cross-check #7 (amended): the finding asked to call these «οι πρωτεύουσες των 27 κρατών-μελών
    της ΕΕ».  That is false for this list -- it holds Μόσχα, Μινσκ, Λονδίνο, Βαντούζ, Βέρνη,
    Κισινάου, Ρέικιαβικ and Όσλο (non-EU) and omits Αθήνα, Ρώμη, Μαδρίτη, Λισαβόνα, Σόφια,
    Βουκουρέστι, Λευκωσία and Βαλέτα (EU, but below 45°N).  The description therefore names the
    reference set exactly (EU-27 + EFTA + UK + RU + BY + MD, latitude > 45°) which is the same 27
    cities and, by naming the states, leaves Κίεβο (50.45°N, the one genuine omission) out.
    """

    INSTRUCTION_ID = "custom:european_capitals_sort"

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        capitals = [c.strip() for c in nfc(value).split(",") if c.strip()]
        if len(capitals) != len(EUROPEAN_CAPITALS_EL):
            return False
        for given, (_canonical, variants) in zip(capitals, EUROPEAN_CAPITALS_EL):
            # tonos-insensitive comparison against the accepted Greek spellings
            if fold(given) not in {fold(v) for v in variants}:
                return False
        return True


# --------------------------------------------------------------------------------------
# custom:csv_city  (adapt)
# --------------------------------------------------------------------------------------
class CityCSVChecker(Instruction):
    """CSV με ελληνικές επικεφαλίδες και 7 γραμμές."""

    INSTRUCTION_ID = "custom:csv_city"
    HEADER = ["Κωδικός", "Χώρα", "Πόλη", "Έτος", "Πλήθος"]

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # NFC is mandatory: an NFD «ό» would carry a separate combining mark
        data = list(csv.reader(io.StringIO(nfc(value))))
        if len(data) != 8:
            return False
        # headers are compared folded (tonos/case insensitive)
        if [fold(h.strip()) for h in data[0]] != [fold(h) for h in self.HEADER]:
            return False
        return all(len(row) == 5 for row in data[1:])


# --------------------------------------------------------------------------------------
# custom:csv_special_character  (adapt)
# --------------------------------------------------------------------------------------
class SpecialCharacterCSVChecker(Instruction):
    """CSV, 14 γραμμές, ένα πεδίο με ειδικό χαρακτήρα σε εισαγωγικά."""

    INSTRUCTION_ID = "custom:csv_special_character"
    HEADER = ["ΚωδικόςΠροϊόντος", "Κατηγορία", "Μάρκα", "Τιμή", "Απόθεμα"]

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        value = nfc(value)          # an NFD tonos would look like a "special character"
        header = value.split("\n")[0].strip()
        cells = [c.strip().strip('"') for c in header.split(",")]
        if [fold(c) for c in cells] != [fold(h) for h in self.HEADER]:
            return False
        value = value.replace('"', '"""')
        data = list(csv.reader(io.StringIO(value)))
        if len(data) != 15:
            return False
        found_special = False
        for row in data[1:]:
            if len(row) != 5:
                return False
            if any(re.match(r'".*[^\d\w\s].*"', field) for field in row):
                found_special = True
        return found_special


# --------------------------------------------------------------------------------------
# custom:csv_quotes  (adapt)
# --------------------------------------------------------------------------------------
class QuotesCSVChecker(Instruction):
    """TSV, 3 γραμμές, κάθε πεδίο σε εισαγωγικά."""

    INSTRUCTION_ID = "custom:csv_quotes"
    HEADER = ["ΚωδικόςΜαθητή", "Μάθημα", "Βαθμός", "Εξάμηνο", "Μονάδες"]

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        value = nfc(value)
        header = value.split("\n")[0].strip()
        cells = [c.strip().strip('"') for c in header.split("\t")]
        if [fold(c) for c in cells] != [fold(h) for h in self.HEADER]:
            return False
        value = value.replace('"', '"""')
        data = list(csv.reader(io.StringIO(value), delimiter="\t"))
        if len(data) != 4:
            return False
        for row in data:
            if len(row) != 5:
                return False
            if not all(field.strip() and field.strip()[0] == '"'
                       and field.strip()[-1] == '"' for field in row):
                return False
        return True


# --------------------------------------------------------------------------------------
# custom:date_format_list  (adapt)
# --------------------------------------------------------------------------------------
class DateFormatListChecker(Instruction):
    """Ημερομηνίες ΗΗ/ΜΜ/ΕΕΕΕ (ή με μήνα στη γενική), 1769–1821."""

    INSTRUCTION_ID = "custom:date_format_list"
    _NUMERIC = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

    def build_description(self, **kwargs):
        self._description_pattern = self.pattern_el
        self._month_re = re.compile(
            r"^(\d{1,2})\s+(" + "|".join(fold(m) for m in MONTHS_GEN_EL) + r")\s+(\d{4})$")
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    @staticmethod
    def _valid(day, month, year):
        if year < 1769 or year > 1821:          # Napoleon's lifetime, kept from upstream
            return False
        if month < 1 or month > 12 or day < 1:
            return False
        if month in (1, 3, 5, 7, 8, 10, 12) and day > 31:
            return False
        if month in (4, 6, 9, 11) and day > 30:
            return False
        if month == 2 and day > 29:
            return False
        return day <= 31

    def check_following(self, value):
        month_re = getattr(self, "_month_re", None)
        if month_re is None:
            self.build_description()
            month_re = self._month_re
        dates = [d.strip() for d in nfc(value).strip().split(",")]
        if not dates or dates == [""]:
            return False
        for date in dates:
            m = self._NUMERIC.match(date)        # Greek order: day/month/year
            if m:
                day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                m = month_re.match(fold(date))   # «2 Δεκεμβρίου 1805»
                if not m:
                    return False
                day = int(m.group(1))
                month = [fold(x) for x in MONTHS_GEN_EL].index(m.group(2)) + 1
                year = int(m.group(3))
            if not self._valid(day, month, year):
                return False
        return True


# --------------------------------------------------------------------------------------
# count:keywords_multiple  (adapt)
# --------------------------------------------------------------------------------------
class KeywordsMultipleChecker(Instruction):
    """Πέντε λέξεις με ακριβείς συχνότητες 1, 2, 3, 5, 7."""

    INSTRUCTION_ID = "count:keywords_multiple"
    COUNTS = (1, 2, 3, 5, 7)

    def build_description(self, *, keyword1=None, keyword2=None, keyword3=None,
                         keyword4=None, keyword5=None):
        defaults = ["ουρανός", "θάλασσα", "χρόνος", "δρόμος", "φως"]
        given = [keyword1, keyword2, keyword3, keyword4, keyword5]
        self._keywords = [(k.strip() if k else defaults[i]) for i, k in enumerate(given)]
        (self._keyword1, self._keyword2, self._keyword3,
         self._keyword4, self._keyword5) = self._keywords
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(
            keyword1=self._keyword1, keyword2=self._keyword2, keyword3=self._keyword3,
            keyword4=self._keyword4, keyword5=self._keyword5)

    def get_instruction_args(self):
        return {"keyword1": self._keyword1, "keyword2": self._keyword2,
                "keyword3": self._keyword3, "keyword4": self._keyword4,
                "keyword5": self._keyword5}

    def get_instruction_args_keys(self):
        return ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]

    def check_following(self, value):
        folded_value = fold(value)
        for keyword, count in zip(self._keywords, self.COUNTS):
            # EXACT counts on the folded SURFACE form, no stemming: an inflected form
            # («ουρανού») is a different word here, so prompts must pin the case or use
            # an indeclinable keyword (§D).  \b is Unicode-aware in Python's re.
            pattern = r"\b{}\b".format(re.escape(fold(keyword)))
            if len(re.findall(pattern, folded_value)) != count:
                return False
        return True


# --------------------------------------------------------------------------------------
# words:keywords_specific_position  (adapt)
# --------------------------------------------------------------------------------------
class KeywordSpecificPositionChecker(Instruction):
    """Η λέξη keyword ως mη λέξη της nης πρότασης."""

    INSTRUCTION_ID = "words:keywords_specific_position"

    def build_description(self, keyword=None, n=None, m=None):
        self._keyword = keyword.strip() if keyword else "θάλασσα"
        self._n = _as_int(n) or random.randint(20, 30)
        self._m = _as_int(m) or random.randint(30, 40)
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(keyword=self._keyword, n=self._n, m=self._m)

    def get_instruction_args(self):
        return {"keyword": self._keyword, "n": self._n, "m": self._m}

    def get_instruction_args_keys(self):
        return ["keyword", "n", "m"]

    def check_following(self, value):
        sentences = split_sentences_el(value)
        if len(sentences) < self._n:
            return False
        # NOTE (§C): position 2 in a Greek sentence is usually an article, so prompts
        # should use an indeclinable keyword or pin the case.
        w = toks(sentences[self._n - 1])
        if len(w) < self._m:
            return False
        return fold(w[self._m - 1]) == fold(self._keyword)


# --------------------------------------------------------------------------------------
# words:words_position  (adapt)
# --------------------------------------------------------------------------------------
class WordsPositionChecker(Instruction):
    """Η 2η και η προτελευταία λέξη = keyword."""

    INSTRUCTION_ID = "words:words_position"

    def build_description(self, *, keyword=None):
        self._keyword = keyword.strip() if keyword else "θάλασσα"
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(keyword=self._keyword)

    def get_instruction_args(self):
        return {"keyword": self._keyword}

    def get_instruction_args_keys(self):
        return ["keyword"]

    def check_following(self, value):
        w = [fold(t) for t in toks(value)]
        if len(w) < 2:
            return False
        return w[1] == w[-2] == fold(self._keyword)


# --------------------------------------------------------------------------------------
# repeat:repeat_change  (adapt)
# --------------------------------------------------------------------------------------
class RepeatChangeChecker(Instruction):
    """Επανάληψη του αιτήματος με αλλαγμένη μόνο την πρώτη λέξη."""

    INSTRUCTION_ID = "repeat:repeat_change"

    def build_description(self, *, prompt_to_repeat=None):
        if not prompt_to_repeat:
            raise ValueError("prompt_to_repeat must be set.")
        self._prompt_to_repeat = prompt_to_repeat
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(prompt_to_repeat=self._prompt_to_repeat)

    def get_instruction_args(self):
        return {"prompt_to_repeat": self._prompt_to_repeat}

    def get_instruction_args_keys(self):
        return ["prompt_to_repeat"]

    def check_following(self, value):
        # folded whitespace tokens: capitalising the new first word must not matter
        src = [fold(t) for t in self._prompt_to_repeat.split()]
        got = [fold(t) for t in value.split()]
        if src == got:
            return False                 # the first word has to change
        return src[1:] == got[1:] and len(got) == len(src)


# --------------------------------------------------------------------------------------
# repeat:repeat_simple  (adapt)
# --------------------------------------------------------------------------------------
class RepeatSimpleChecker(Instruction):
    """Έξοδος = ακριβώς η ελληνική πρόταση της εντολής."""

    INSTRUCTION_ID = "repeat:repeat_simple"

    def build_description(self, *, instruction_el=None):
        """`instruction_el` optionally pins the exact Greek sentence used in the prompt.

        Upstream takes no kwargs and the sentence is fixed by the description; the Greek
        prompt translator may word it slightly differently, and passing it here keeps the
        checker and the prompt from drifting apart.  Defaults to DESCRIPTIONS_EL.
        """
        self._description_pattern = instruction_el.strip() if instruction_el else self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return {"instruction_el": self._description_pattern}

    def get_instruction_args_keys(self):
        return ["instruction_el"]

    def check_following(self, value):
        return fold(value.strip()) == fold(self._description_pattern.strip())


# --------------------------------------------------------------------------------------
# repeat:repeat_span  (adapt)
# --------------------------------------------------------------------------------------
class RepeatSpanChecker(Instruction):
    """Αντιγραφή του εύρους λέξεων [n_start, n_end]."""

    INSTRUCTION_ID = "repeat:repeat_span"

    def build_description(self, prompt_to_repeat=None, n_start=None, n_end=None):
        if not prompt_to_repeat:
            raise ValueError("prompt_to_repeat must be set.")
        self._prompt_to_repeat = prompt_to_repeat
        # indices are recomputed over the GREEK whitespace tokens (§D)
        num_words = len(self._prompt_to_repeat.split())
        self._n_start = _as_int(n_start)
        if self._n_start is None:
            self._n_start = random.randint(0, max(num_words - 2, 0))
        self._n_end = _as_int(n_end)
        if self._n_end is None:
            self._n_end = random.randint(self._n_start + 1, max(num_words - 1,
                                                               self._n_start + 1))
        self._description_pattern = self.pattern_el
        return self._description_pattern.format(n_start=self._n_start, n_end=self._n_end)

    def get_instruction_args(self):
        return {"n_start": self._n_start, "n_end": self._n_end,
                "prompt_to_repeat": self._prompt_to_repeat}

    def get_instruction_args_keys(self):
        return ["n_start", "n_end", "prompt_to_repeat"]

    def check_following(self, value):
        w = self._prompt_to_repeat.split()
        expected = " ".join(w[self._n_start:self._n_end + 1])
        return fold(value.strip()) == fold(expected.strip())


# --------------------------------------------------------------------------------------
# format:title_case  (adapt)
# --------------------------------------------------------------------------------------
class TitleCaseChecker(Instruction):
    """Κεφαλαίο αρχικό σε κάθε λέξη, τόνοι διατηρημένοι."""

    INSTRUCTION_ID = "format:title_case"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        minor = {fold(w) for w in MINOR_WORDS_EL}
        tokens = toks(nfc(value))
        if not tokens:
            return False
        for i, word in enumerate(tokens):
            if not word[0].isalpha():
                continue
            # Greek title case keeps the tonos on the capital (Άνθρωπος, not ΑΝΘΡΩΠΟΣ)
            if i > 0 and fold(word) in minor:
                continue                      # articles/prepositions may stay lowercase
            if len(word) == 1:
                if word[0].islower():
                    return False
                continue
            rest = word[1:]
            if not word[0].isupper():
                return False
            # final ς is a lowercase letter, so «Άνθρωπος» passes and «ΑνθρωποΣ» fails
            if any(c.isalpha() and c.isupper() for c in rest):
                return False
        return True


# --------------------------------------------------------------------------------------
# format:output_template  (adapt)
# --------------------------------------------------------------------------------------
class OutputTemplateChecker(Instruction):
    """Τρεις σταθερές ελληνικές ετικέτες."""

    INSTRUCTION_ID = "format:output_template"
    LABELS = ("Η απάντησή μου:", "Το συμπέρασμά μου:", "Μελλοντική προοπτική:")

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        # accent-stripped, case-insensitive, multiline match: «Η ΑΠΑΝΤΗΣΗ ΜΟΥ:» passes
        haystack = strip_diacritics(nfc(value))
        for label in self.LABELS:
            needle = strip_diacritics(label)
            if not re.search(re.escape(needle), haystack, re.IGNORECASE | re.MULTILINE):
                return False
        return True


# --------------------------------------------------------------------------------------
# format:no_whitespace  (faithful)
# --------------------------------------------------------------------------------------
class NoWhitespaceChecker(Instruction):
    """Καμία κενή θέση."""

    INSTRUCTION_ID = "format:no_whitespace"

    def build_description(self):
        self._description_pattern = self.pattern_el
        return self._description_pattern

    def get_instruction_args(self):
        return None

    def get_instruction_args_keys(self):
        return []

    def check_following(self, value):
        return not any(char.isspace() for char in value)
