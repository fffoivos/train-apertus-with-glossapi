#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for instructions_el.py.

Coverage rule (TRANSFER_ANALYSIS §C): every `adapt` checker gets at least four cases —
positive, negative, boundary and Unicode (accents / case / final sigma / NFD / Greek
punctuation) — and every `faithful` checker at least two.  Run with:

    ~/venvs/sftdata/bin/python -m pytest instructions_el_test.py -q
"""
from __future__ import annotations

import unicodedata

import pytest

import instructions_el as I
from instructions_registry_el import INSTRUCTION_DICT

GQM = ";"      # ';' GREEK QUESTION MARK
ANO = "·"      # '·' GREEK ANO TELEIA


def mk(iid, **kw):
    inst = INSTRUCTION_DICT[iid](iid)
    inst.build_description(**kw)
    return inst


def check(iid, value, **kw):
    return mk(iid, **kw).check_following(value)


def nfd(s):
    return unicodedata.normalize("NFD", s)


# ======================================================================================
# registry / wiring
# ======================================================================================
def test_registry_has_58_ids():
    assert len(INSTRUCTION_DICT) == 58
    assert len(I.DESCRIPTIONS_EL) == 58
    assert set(INSTRUCTION_DICT) == set(I.DESCRIPTIONS_EL)


def test_every_class_declares_its_id():
    for iid, cls in INSTRUCTION_DICT.items():
        assert cls.INSTRUCTION_ID == iid


def test_descriptions_are_greek():
    for iid, text in I.DESCRIPTIONS_EL.items():
        assert any("Ͱ" <= ch <= "Ͽ" for ch in text), iid


def test_retuned_dict():
    assert set(I.RETUNED) == {"words:palindrome", "words:vowel", "words:repeats",
                              "custom:sentence_alphabet", "custom:reverse_newline",
                              # cross-check #11: the two deliberate tightenings are recorded here
                              "ratio:sentence_type", "ratio:sentence_balance"}
    assert I.RETUNED["words:palindrome"]["greek"] == 3
    assert I.RETUNED["words:vowel"]["greek"] == 4
    assert I.RETUNED["words:repeats"]["greek"] == 5
    assert I.RETUNED["custom:sentence_alphabet"]["greek"] == 24
    assert I.RETUNED["custom:reverse_newline"]["greek"] == 14
    assert I.RETUNED["ratio:sentence_type"]["greek"] == 1
    assert I.RETUNED["ratio:sentence_balance"]["greek"] == 1
    # cross-check #3: the floor is documented as the EFFECTIVE value
    assert "effective_small_n" in I.RETUNED["words:repeats"]["reason"]
    for v in I.RETUNED.values():
        assert v["reason"].strip()


# ======================================================================================
# shared primitives P1–P4
# ======================================================================================
def test_p1_split_greek_question_marks_end_sentences():
    assert len(I.split_sentences_el("Πάμε; Ναι.")) == 2
    assert len(I.split_sentences_el("Πάμε" + GQM + " Ναι.")) == 2


def test_p1_ano_teleia_is_not_a_terminator():
    assert I.split_sentences_el("Ήρθε ο Νίκος" + ANO + " έφυγε η Μαρία.") == \
        ["Ήρθε ο Νίκος· έφυγε η Μαρία."]


@pytest.mark.parametrize("text", ["Πάμε π.χ. σήμερα.", "Φρούτα κ.λπ. εδώ.",
                                  "Μήλα κ.ά. εκεί.", "Υ.Γ. τα λέμε.", "Δες αρ. 5 τώρα."])
def test_p1_abbreviations_do_not_split(text):
    assert len(I.split_sentences_el(text)) == 1


def test_p2_fold():
    assert I.fold("ΟΔΌΣ") == I.fold("οδός") == "οδοσ"
    assert I.fold("ΐ") == "ι"


def test_p3_tok_strips_greek_punctuation():
    assert I.toks("«Καλημέρα», είπε — ναι" + GQM) == ["Καλημέρα", "είπε", "ναι"]


def test_p4_letter_sets():
    assert len(I.GREEK_ALPHABET) == 24
    assert I.GREEK_VOWELS == set("αεηιουω")
    assert "ς" in I.GREEK_CONSONANTS and "σ" in I.GREEK_CONSONANTS


@pytest.mark.parametrize("word,n", [("θάλασσα", 3), ("είναι", 2), ("γάιδαρος", 4),
                                    ("ρολόι", 3), ("προϊόν", 3), ("ναι", 1),
                                    ("ουρανός", 3)])
def test_syllable_counter(word, n):
    assert I.count_syllables_el(word) == n


# ======================================================================================
# count:word_count_range  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ένα δύο τρία τέσσερα", True),
    ("negative", "Ένα", False),
    ("boundary", "Ένα δύο τρία", True),
    ("unicode", "σ’ αυτό το ωραίο σπίτι", True),
])
def test_word_count_range(label, value, expected):
    assert check("count:word_count_range", value, min_words=3.0, max_words=5.0) is expected


# ======================================================================================
# count:unique_word_count  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,n,expected", [
    ("positive", "Ένα δύο τρία τέσσερα", 3.0, True),
    ("negative", "Ένα ένα ένα ένα", 3.0, False),
    ("boundary", "Ένα δύο τρία", 3.0, True),
    ("unicode", "ΘΑΛΑΣΣΑ θάλασσα θαλασσα", 2.0, False),   # fold collapses the 3 forms
])
def test_unique_word_count(label, value, n, expected):
    assert check("count:unique_word_count", value, N=n) is expected


# ======================================================================================
# ratio:stop_words  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,pct,expected", [
    ("positive", "Γράφω ωραία ποιήματα", 50.0, True),
    ("negative", "και το να με για", 50.0, False),
    ("boundary", "και τρέχω", 50.0, True),                # exactly 50%
    ("unicode", "πού πώς τρέχω γράφω", 10.0, True),       # accented interrogatives ≠ stop
    ("unicode-neg", "που πως τρέχω γράφω", 10.0, False),
])
def test_stop_words(label, value, pct, expected):
    assert check("ratio:stop_words", value, percentage=pct) is expected


# ======================================================================================
# ratio:sentence_type  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Καλά. Ωραία. Πάμε;", True),
    ("negative", "Καλά. Πάμε;", False),
    # cross-check #11: no terminators used to pass on 0 == 2*0; ≥1 interrogative is now required
    ("boundary", "Ήρθε ο Νίκος" + ANO + " έφυγε η Μαρία", False),
    ("no-question", "Καλά. Ωραία.", False),                        # cross-check #11 tightening
    ("unicode", "Καλά. Ωραία. Πάμε" + GQM, True),
])
def test_sentence_type(label, value, expected):
    assert check("ratio:sentence_type", value) is expected


def test_sentence_type_description_discloses_the_minimum():
    """cross-check #11: the ≥1-interrogative rule is stated in the prompt."""
    assert "τουλάχιστον μία ερωτηματική" in I.DESCRIPTIONS_EL["ratio:sentence_type"]


# ======================================================================================
# ratio:sentence_balance  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Καλά. Πάμε; Ωραία!", True),
    ("negative", "Καλά. Πάμε;", False),
    # cross-check #11: 0 == 0 == 0 is no longer a free pass
    ("boundary", "Χωρίς σημεία στίξης", False),
    ("missing-type", "Καλά. Ωραία.", False),                       # cross-check #11 tightening
    ("unicode", "Καλά. Πάμε" + GQM + " Ωραία!", True),
])
def test_sentence_balance(label, value, expected):
    assert check("ratio:sentence_balance", value) is expected


def test_sentence_balance_description_discloses_the_minimum():
    """cross-check #11: the ≥1-of-each rule is stated in the prompt."""
    assert "τουλάχιστον μία πρόταση από κάθε τύπο" in I.DESCRIPTIONS_EL["ratio:sentence_balance"]


# ======================================================================================
# count:conjunctions  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,n,expected", [
    ("positive", "ψωμί και τυρί αλλά όχι ελιές", 2.0, True),
    ("negative", "ψωμί και τυρί κι ελιές", 2.0, False),            # και/κι = one type
    ("boundary", "ψωμί και τυρί ή ελιές αλλά όχι", 3.0, True),
    ("unicode", "η μέρα η νύχτα και το φως", 2.0, False),          # «η» is not «ή»
    ("unicode-pos", "η μέρα ή η νύχτα και το φως", 2.0, True),
])
def test_conjunctions(label, value, n, expected):
    assert check("count:conjunctions", value, small_n=n) is expected


# ======================================================================================
# count:person_names  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,n,expected", [
    ("positive", "Ο Γιώργος και η Μαρία ήρθαν.", 2.0, True),
    ("negative", "Ο Γιώργος ήρθε.", 2.0, False),
    ("boundary", "Του Γιώργου και της Μαρίας.", 2.0, True),        # declension set
    ("unicode", "ΓΙΩΡΓΟΣ ΜΑΡΙΑ", 2.0, True),
])
def test_person_names(label, value, n, expected):
    assert check("count:person_names", value, N=n) is expected


def test_person_names_list_is_50():
    assert len(I.NAMES_EL) == len(set(I.NAMES_EL)) == 50


# ======================================================================================
# ratio:overlap  (adapt)
# ======================================================================================
REF = "Η θάλασσα είναι γαλάζια"


@pytest.mark.parametrize("label,value,pct,expected", [
    ("positive", "Η θάλασσα είναι γαλάζια", 100.0, True),
    ("negative", "Ένα δύο τρία τέσσερα", 100.0, False),
    ("boundary", "Η θάλασσα είναι γαλάζια σήμερα", 67.0, True),    # 2/3 trigrams
    ("unicode", "Η ΘΑΛΑΣΣΑ ΕΙΝΑΙ ΓΑΛΑΖΙΑ", 100.0, True),
])
def test_overlap(label, value, pct, expected):
    assert check("ratio:overlap", value, reference_text=REF, percentage=pct) is expected


def test_overlap_description_renders_the_reference_text():
    """cross-check #1: the reference text must be visible and identifiable in the prompt."""
    inst = INSTRUCTION_DICT["ratio:overlap"]("ratio:overlap")
    description = inst.build_description(reference_text=REF, percentage=50.0)
    assert REF in description
    assert "«%s»" % REF in description
    assert "50%" in description
    assert "{" not in description
    # the kwargs contract is unchanged: the reference text is still an argument
    assert inst.get_instruction_args()["reference_text"] == REF
    assert inst.get_instruction_args_keys() == ["reference_text", "percentage"]


def test_overlap_description_survives_a_missing_reference():
    inst = INSTRUCTION_DICT["ratio:overlap"]("ratio:overlap")
    assert "None" not in inst.build_description(percentage=50.0)


# ======================================================================================
# count:numbers  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,n,expected", [
    ("positive", "Κόστισε 1.234,56 ευρώ.", 1.0, True),             # Greek thousands/decimals
    ("negative", "Κόστισε 12 και 13 ευρώ.", 1.0, False),
    ("boundary", "Στις 10/09/2026 έγινε.", 1.0, True),
    ("unicode", "Το κεφάλαιο ιθ΄ έχει 5 σελίδες.", 1.0, True),     # Greek numerals ≠ digits
])
def test_numbers(label, value, n, expected):
    assert check("count:numbers", value, N=n) is expected


# ======================================================================================
# words:alphabet  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "αύριο βράδυ γράφω δυνατά", True),
    ("negative", "αύριο γράφω", False),
    ("boundary", "ώρα αύριο βράδυ", True),                          # ω -> α wrap (cycle 24)
    ("unicode", "ΣΉΜΕΡΑ ταξίδι", True),
])
def test_alphabet_loop(label, value, expected):
    assert check("words:alphabet", value) is expected


# ======================================================================================
# words:vowel  (adapt, RETUNED ≤ 4)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "τα παιδιά", True),
    ("negative", "καλημέρα κόσμε ουρανός τυρί ωραία", False),
    ("boundary", "θάλασσα μέρα ώρα ναι", True),                     # exactly 4 vowels
    ("unicode", "ΆΝΘΡΩΠΟΣ άνθρωπος", True),
    ("two-paragraphs", "θάλασσα\nμέρα", False),
])
def test_single_vowel_paragraph(label, value, expected):
    assert check("words:vowel", value) is expected


# ======================================================================================
# words:consonants  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "χρόνος σπίτι", True),
    ("negative", "καλή μέρα", False),
    ("boundary", "ξέρω", True),                                     # single ξ = a cluster
    ("unicode", "ΨΩΜΙ", True),
])
def test_consonant_cluster(label, value, expected):
    assert check("words:consonants", value) is expected


def test_consonant_cluster_description_names_the_excluded_words():
    """cross-check #12: writers must see that και/το/να/με are ruled out (no code change)."""
    text = I.DESCRIPTIONS_EL["words:consonants"]
    assert "(αυτό αποκλείει λέξεις χωρίς σύμπλεγμα συμφώνων όπως και, το, να, με)" in text
    for word in ("και", "το", "να", "με"):
        assert check("words:consonants", word) is False


# ======================================================================================
# sentence:alliteration_increment  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Καλά νέα. Μια μέρα ήρθε. Τρία τρένα τρέχουν γρήγορα.", True),
    ("negative", "Τρία τρένα τρέχουν γρήγορα. Καλά νέα.", False),
    ("boundary", "Καλά νέα.", True),                                # one sentence: 0 > -1
    ("unicode", "Καλά νέα. Μία μέρα ΜΑΖΊ πάμε.", True),
])
def test_alliteration_increment(label, value, expected):
    assert check("sentence:alliteration_increment", value) is expected


# ======================================================================================
# words:palindrome  (adapt, RETUNED N = 3)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ο σοφός Σάββας ψήφισε νόμον.", True),
    ("negative", "Ο σοφός ψήφισε νόμον.", False),
    ("boundary", "Ο σοφός, ο νόμον και η Άννα.", False),            # «Άννα» is only 4 long
    ("unicode", "ΣΟΦΟΣ ΝΟΜΟΝ ΣΑΒΒΑΣ", True),                        # ς ≡ σ, tonos dropped
])
def test_palindrome(label, value, expected):
    assert check("words:palindrome", value) is expected


# ======================================================================================
# count:punctuation  (adapt)
# ======================================================================================
FULL = "Τι κάνεις; Καλά! Ναι, όχι: αυτό" + ANO + " τέλος. Αλήθεια!;"


@pytest.mark.parametrize("label,value,expected", [
    ("positive", FULL, True),
    ("negative", "Τι κάνεις; Καλά! Ναι, όχι: τέλος. Αλήθεια!;", False),   # no ano teleia
    ("boundary", "Τι‽ Πάμε; Καλά! Ναι, όχι: αυτό" + ANO + " τέλος.", True),
    ("unicode", FULL.replace(";", GQM), True),
])
def test_punctuation_cover(label, value, expected):
    assert check("count:punctuation", value) is expected


# ======================================================================================
# format:parentheses  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ένα (δύο (τρία (τέσσερα (πέντε (έξι)))))", True),
    ("negative", "Ένα (δύο (τρία))", False),
])
def test_nested_parentheses(label, value, expected):
    assert check("format:parentheses", value) is expected


# ======================================================================================
# format:quotes  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "«Είπε “ο Νίκος ‘ναι’ απάντησε” σήμερα»", True),
    ("negative", "«Είπε “ναι”»", False),
    ("boundary", '"άλφα \'βήτα "γάμα" βήτα\' άλφα"', True),          # ASCII fallback
    ("unicode", "«σ’ αυτό “το ‘καλό’ βιβλίο” λέει»", True),          # elision ’ ≠ quote
])
def test_nested_quotes(label, value, expected):
    assert check("format:quotes", value) is expected


# ======================================================================================
# words:prime_lengths  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "ναι όχι θάλασσα", True),
    ("negative", "καλά", False),
    ("boundary", "θα ναι", True),
    ("unicode", nfd("ναί όχι"), True),                               # NFD tonos ≠ a character
])
def test_prime_lengths(label, value, expected):
    assert check("words:prime_lengths", value) is expected


# ======================================================================================
# format:options  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,options,expected", [
    ("positive", "Ναι", "ναι/όχι/ίσως", True),
    ("negative", "Ναι, ίσως", "ναι/όχι/ίσως", False),
    ("boundary", "όχι", "yes/no/maybe", True),                       # English bank -> Greek
    ("unicode", "α)", "α), β), γ), δ)", True),
    ("homoglyph", "a)", "α), β), γ), δ)", True),
    ("strict-neg", "ε)", "α), β), γ), δ)", False),
    ("or-separator", "ξέρω", "I know or I don't know", True),
    # cross-check #9: label case-insensitivity + Latin/Greek uppercase homoglyphs
    ("upper-greek", "Α)", "α), β), γ), δ)", True),
    ("upper-latin", "A)", "α), β), γ), δ)", True),
    ("latin-c", "C)", "α), β), γ), δ)", True),
    ("upper-latin-d", "D)", "α), β), γ), δ)", True),
    ("upper-greek-g", "Γ)", "α), β), γ), δ)", True),
    ("upper-latin-e-neg", "E)", "α), β), γ), δ)", False),          # ε) is not on offer
    ("loose-upper", "ΊΣΩΣ", "ναι/όχι/ίσως", True),
])
def test_options(label, value, options, expected):
    assert check("format:options", value, options=options) is expected


@pytest.mark.parametrize("value", ["α)", "Α)", "a)", "A)", "ε)", "Ε)", "e)", "E)"])
def test_options_five_labels_are_case_and_homoglyph_insensitive(value):
    """cross-check #9: A/B/C/D/E and Α/Β/Γ/Δ/Ε all map onto α) β) γ) δ) ε)."""
    assert check("format:options", value, options="α), β), γ), δ), ε)") is True


# ======================================================================================
# format:newline  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "ένα\nδύο\nτρία", True),
    ("negative", "ένα δύο\nτρία", False),
])
def test_newline_words(label, value, expected):
    assert check("format:newline", value) is expected


# ======================================================================================
# format:emoji  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Καλημέρα 🙂. Τι κάνεις; 😀", True),
    ("negative", "Καλημέρα. Τι κάνεις;", False),
    ("boundary", "Καλημέρα. 🙂 Τι κάνεις; 😀", True),          # emoji opens the next sentence
    ("unicode", "Πάμε π.χ. στη θάλασσα 🙂.", True),           # abbreviation ≠ sentence end
])
def test_emoji_sentence(label, value, expected):
    assert check("format:emoji", value) is expected


# ======================================================================================
# ratio:sentence_words  (adapt)
# ======================================================================================
THREE = "Καλή μέρα. Τρώω ψωμί. Πίνω νερό."


@pytest.mark.parametrize("label,value,expected", [
    ("positive", THREE, True),
    ("negative", "Καλή μέρα. Τρώω ψωμί.", False),
    ("boundary", "Καλή μέρα. Τρώω ψωμί. Πίνω νεράκι.", False),   # one char longer
    ("unicode", nfd(THREE), True),                               # NFD counts as NFC
    ("repeat", "Καλή μέρα. Καλή ώρα.. Πίνω νερό.", False),       # a word repeats
])
def test_sentence_words(label, value, expected):
    assert check("ratio:sentence_words", value) is expected


# ======================================================================================
# count:words_japanese  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "ένα 日本 τρία 言葉", True),
    ("negative", "ένα δύο τρία τέσσερα", False),
])
def test_words_japanese(label, value, expected):
    assert check("count:words_japanese", value, N=2.0) is expected


# ======================================================================================
# words:start_verb  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Γράψε ένα ποίημα.", True),                     # imperative whitelist
    ("negative", "Το σπίτι είναι μεγάλο.", False),
    ("boundary", "Τρέχω γρήγορα.", True),                        # -ω ending
    ("unicode", "ΓΡΆΦΩ σήμερα.", True),
    ("homograph", "Εγώ τρέχω.", False),                          # «εγώ» ends in -ώ but is a pronoun
])
def test_start_verb(label, value, expected):
    assert check("words:start_verb", value) is expected


# ======================================================================================
# words:repeats  (adapt, RETUNED small_n floored at 5)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "ένα δύο τρία", True),
    ("negative", "ναι ναι ναι ναι ναι ναι", False),              # 6 > 5
    ("boundary", "ναι ναι ναι ναι ναι", True),                   # exactly 5
    ("unicode", "Θάλασσα θαλασσα ΘΑΛΑΣΣΑ", True),
])
def test_limited_word_repeat(label, value, expected):
    assert check("words:repeats", value, small_n=2.0) is expected


def test_limited_word_repeat_floor_is_recorded():
    inst = mk("words:repeats", small_n=2.0)
    assert inst.get_instruction_args()["small_n"] == 5


def test_limited_word_repeat_effective_small_n_is_the_single_source_of_truth():
    """cross-check #3: build_description() and check_following() use the same value."""
    cls = I.LimitedWordRepeatChecker
    assert cls.effective_small_n(2.0) == 5          # floored
    assert cls.effective_small_n(7.0) == 7          # above the floor: untouched
    assert cls.effective_small_n(5) == 5            # boundary
    for small_n in (1.0, 2.0, 5.0, 7.0):
        inst = INSTRUCTION_DICT["words:repeats"]("words:repeats")
        description = inst.build_description(small_n=small_n)
        n = cls.effective_small_n(small_n)
        assert "%d" % n in description
        assert inst.get_instruction_args()["small_n"] == n
        assert inst.check_following(" ".join(["ναι"] * n)) is True
        assert inst.check_following(" ".join(["ναι"] * (n + 1))) is False


def test_limited_word_repeat_accepts_the_upstream_kwarg():
    """cross-check #3: the assembler keeps the un-floored upstream value alongside small_n."""
    inst = INSTRUCTION_DICT["words:repeats"]("words:repeats")
    description = inst.build_description(small_n=5, small_n_upstream=2)
    assert "5" in description and "2" not in description
    assert inst.get_instruction_args() == {"small_n": 5}
    assert inst.get_instruction_args_keys() == ["small_n"]


# ======================================================================================
# sentence:keyword  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Καλημέρα. Η θάλασσα είναι ήρεμη.", True),
    ("negative", "Η θάλασσα είναι ήρεμη. Καλημέρα.", False),
    ("boundary", "Η θάλασσα είναι ήρεμη.", False),               # fewer sentences than N
    ("unicode", "Καλημέρα. Το χρώμα της ΘΆΛΑΣΣΑΣ.", True),       # stem match
])
def test_include_keyword(label, value, expected):
    assert check("sentence:keyword", value, word="θάλασσα", N=2.0) is expected


# ======================================================================================
# count:pronouns  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,n,expected", [
    ("positive", "Εγώ και εσύ", 2.0, True),
    ("negative", "Το σπίτι του Γιώργου", 1.0, False),            # «του» before a noun = article
    ("boundary", "Μου είπε.", 1.0, True),                        # «μου» before a verb = pronoun
    ("unicode", "ΑΥΤΌΣ και ΕΓΏ", 2.0, True),
])
def test_pronouns(label, value, n, expected):
    assert check("count:pronouns", value, N=n) is expected


def test_pronouns_description_discloses_what_is_counted():
    """cross-check #2: strong forms are listed and the clitic rule is spelled out."""
    description = mk("count:pronouns", N=2.0).build_description(N=2.0)
    for form in ("εγώ", "εσύ", "αυτός/αυτή/αυτό", "εμείς", "εσείς", "εκείνος",
                 "κάποιος", "κανείς", "τίποτα", "όλοι", "όποιος", "ό,τι"):
        assert form in description, form
    assert "μου/σου/του/της/μας/σας/τους/τον/την/το/τα/τις" in description
    assert "μόνο όταν ακολουθεί ρήμα ή τελειώνει η πρόταση" in description
    # and the described rule is the one the checker applies
    assert check("count:pronouns", "Το σπίτι του Γιώργου", N=1.0) is False
    assert check("count:pronouns", "Του είπε.", N=1.0) is True


# ======================================================================================
# words:odd_even_syllables  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ναι μέρα θάλασσα", True),                      # 1, 2, 3
    ("negative", "Ναι φως", False),                              # 1, 1
    ("boundary", "Ναι", True),                                   # single word
    ("unicode", "μέρα προϊόν", True),                            # dialytika splits: 2, 3
])
def test_odd_even_syllables(label, value, expected):
    assert check("words:odd_even_syllables", value) is expected


# ======================================================================================
# words:last_first  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ήρθε η μέρα. Μέρα καλή.", True),
    ("negative", "Ήρθε η μέρα. Καλή μέρα.", False),
    ("boundary", "Ήρθε η μέρα.", True),                          # a single sentence passes
    ("unicode", "Ήρθε ο ΝΊΚΟΣ. Νίκος έφυγε.", True),
])
def test_last_word_first_next(label, value, expected):
    assert check("words:last_first", value) is expected


# ======================================================================================
# words:paragraph_last_first  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Μέρα καλή μέρα\nΝύχτα ήσυχη νύχτα", True),
    ("negative", "Μέρα καλή νύχτα", False),
    ("boundary", "Μέρα καλή μέρα\n\nΝύχτα ήσυχη νύχτα", True),   # blank lines skipped
    ("unicode", "Μέρα καλή ΜΈΡΑ", True),
])
def test_paragraph_last_first(label, value, expected):
    assert check("words:paragraph_last_first", value) is expected


# ======================================================================================
# sentence:increment  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ένα δύο. Ένα δύο τρία τέσσερα.", True),
    ("negative", "Ένα δύο. Ένα δύο τρία.", False),
    ("boundary", "Ένα δύο.", True),                              # one sentence
    ("unicode", "Πάμε σ’ αυτό. Θέλω να δω τη θάλασσα.", True),   # elision = two tokens
])
def test_incrementing_word_count(label, value, expected):
    assert check("sentence:increment", value, small_n=2.0) is expected


@pytest.mark.parametrize("small_n,phrase,other", [
    (1.0, "ακριβώς 1 λέξη περισσότερη", "λέξεις περισσότερες"),
    (2.0, "ακριβώς 2 λέξεις περισσότερες", "λέξη περισσότερη"),
    (5.0, "ακριβώς 5 λέξεις περισσότερες", "λέξη περισσότερη"),
])
def test_incrementing_word_count_grammatical_number(small_n, phrase, other):
    """cross-check #4: singular for small_n == 1, plural otherwise."""
    description = mk("sentence:increment", small_n=small_n).build_description(small_n=small_n)
    assert phrase in description
    assert other not in description
    assert "{" not in description


def test_incrementing_word_count_singular_case_still_checks():
    assert check("sentence:increment", "Ένα δύο. Ένα δύο τρία.", small_n=1.0) is True
    assert check("sentence:increment", "Ένα δύο. Ένα δύο τρία τέσσερα.", small_n=1.0) is False


# ======================================================================================
# words:no_consecutive  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ένα βιβλίο γράφω", True),
    ("negative", "Ένα έργο", False),
    ("boundary", "Ένα", True),
    ("unicode", "ΆΝΝΑ ανοίγει", False),                          # tonos-insensitive initials
])
def test_no_consecutive_first_letter(label, value, expected):
    assert check("words:no_consecutive", value) is expected


# ======================================================================================
# format:line_indent  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "άλφα\n βήτα\n  γάμα", True),
    ("negative", "άλφα\nβήτα", False),
])
def test_indent_stairs(label, value, expected):
    assert check("format:line_indent", value) is expected


# ======================================================================================
# format:quote_unquote  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Είπε «καλημέρα» και έφυγε.", True),
    ("negative", "Είπε «καλημέρα» «αντίο» τώρα.", False),        # adjacent quotes
    ("boundary", "Είπε «καλημέρα»", False),                      # ends on a quote
    ("unicode", "Είπε «ναι» σ’ αυτόν και έφυγε.", True),         # elision ’ ≠ quote
])
def test_quote_explanation(label, value, expected):
    assert check("format:quote_unquote", value) is expected


def test_quote_explanation_description_matches_the_checker():
    """cross-check #6: state the two tested facts; drop the unenforced «explain each quote»."""
    text = I.DESCRIPTIONS_EL["format:quote_unquote"]
    assert "δύο εισαγωγικά το ένα δίπλα στο άλλο" in text
    assert "αφαιρεθούν τα κενά" in text
    assert "μην τελειώνεις την απάντηση με εισαγωγικό" in text
    assert "εξήγηση" not in text            # the checker never verifies an explanation
    # an unexplained quotation followed by any text still passes -> the old wording was wrong
    assert check("format:quote_unquote", "Είπε «καλημέρα» και μετά σιωπή.") is True


# ======================================================================================
# format:list  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,sep,expected", [
    ("positive", "ΔΙΑΧΩΡΙΣΤΙΚΟ ένα\nΔΙΑΧΩΡΙΣΤΙΚΟ δύο", "SEPARATOR", True),
    ("negative", "ΔΙΑΧΩΡΙΣΤΙΚΟ ένα", "SEPARATOR", False),
    ("boundary", "… ένα\n… δύο", "...", True),                   # '…' accepted for '...'
    ("unicode", "!" + GQM + "!" + GQM + " ένα\n!" + GQM + "!" + GQM + " δύο", "!?!?", True),
])
def test_special_bullet_points(label, value, sep, expected):
    assert check("format:list", value, sep=sep) is expected


def test_special_bullet_points_maps_the_kwarg():
    assert mk("format:list", sep="SEPARATOR").get_instruction_args()["sep"] == "ΔΙΑΧΩΡΙΣΤΙΚΟ"
    assert mk("format:list", sep="!?!?").get_instruction_args()["sep"] == "!;!;"


# ======================================================================================
# format:thesis  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "<i>Η θέση μου</i> και μετά η ανάλυση.", True),
    ("negative", "<i>Η θέση μου</i>", False),
    ("em-tag", "<em>Η θέση μου</em> και μετά η ανάλυση.", True),
])
def test_italics_thesis(label, value, expected):
    assert check("format:thesis", value) is expected


def test_italics_thesis_description_matches_the_checker():
    """cross-check #5: one section is enough and <em> is accepted alongside <i>."""
    text = I.DESCRIPTIONS_EL["format:thesis"]
    assert text.startswith("Τουλάχιστον μία ενότητα")
    assert "<i>…</i>" in text and "<em>…</em>" in text
    assert "Κάθε ενότητα" not in text
    # only the FIRST section needs the italic thesis, exactly as the description now says
    assert check("format:thesis", "<i>Η θέση μου</i> ανάλυση.\n\nΜια ενότητα χωρίς πλάγια.") is True


# ======================================================================================
# format:sub-bullets  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "* Πρώτο\n  - υποσημείο\n* Δεύτερο\n  - υποσημείο", True),
    ("negative", "* Πρώτο\n* Δεύτερο - υποσημείο", False),
])
def test_sub_bullets(label, value, expected):
    assert check("format:sub-bullets", value) is expected


# ======================================================================================
# format:no_bullets_bullets  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Πρώτη πρόταση. Δεύτερη πρόταση.\n* ένα\n* δύο", True),
    ("negative", "Μία πρόταση μόνο.\n* ένα\n* δύο", False),
    ("boundary", "Πρώτη. Δεύτερη.\n* ένα\n* δύο\nκείμενο μετά", False),
    ("unicode", "Πάμε π.χ. σήμερα.\n* ένα\n* δύο", False),       # abbreviation ≠ two sentences
    ("unicode-pos", "Πάμε π.χ. σήμερα. Ναι.\n* ένα\n* δύο", True),
])
def test_some_bullet_points(label, value, expected):
    assert check("format:no_bullets_bullets", value) is expected


# ======================================================================================
# custom:multiples  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "14, 21, 28, 35, 42, 49", True),
    ("negative", "14, 21, 28", False),
])
def test_print_multiples(label, value, expected):
    assert check("custom:multiples", value) is expected


# ======================================================================================
# custom:mcq_count_length  (adapt)
# ======================================================================================
def _mcq(stems, labels="ΑΒΓΔΕ"):
    blocks = []
    for i, stem in enumerate(stems, 1):
        options = "\n".join("%s) επιλογή" % l for l in labels)
        blocks.append("Ερώτηση %d\n%s\n%s" % (i, stem, options))
    return "\n".join(blocks)


GOOD_STEMS = ["Ποιος ζωγράφισε;", "Ποιος ζωγράφισε τον πίνακα;",
              "Ποιος ζωγράφισε τον γνωστό πίνακα;",
              "Ποιος ζωγράφισε τον πολύ γνωστό ελληνικό πίνακα;"]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", _mcq(GOOD_STEMS), True),
    ("negative", _mcq(GOOD_STEMS[:3]), False),                      # only 3 questions
    ("boundary", _mcq(list(reversed(GOOD_STEMS))), False),          # lengths not increasing
    ("unicode", _mcq(GOOD_STEMS, labels="ABΓΔE"), True),            # Latin homoglyph labels
    ("preamble", "Ορίστε:\n" + _mcq(GOOD_STEMS), False),
])
def test_mcq_count_length(label, value, expected):
    assert check("custom:mcq_count_length", value) is expected


def test_mcq_topic_is_twentieth_century_art_history():
    """cross-check #10: the topic is «ιστορία της τέχνης του 20ού αιώνα», not «ελληνική τέχνη»."""
    text = I.DESCRIPTIONS_EL["custom:mcq_count_length"]
    assert "ιστορία της τέχνης" in text and "του 20ού αιώνα" in text
    assert "ελληνική τέχνη" not in text


# ======================================================================================
# custom:reverse_newline  (adapt, RETUNED 14 lines)
# ======================================================================================
REVERSE_OK = ["Ζιμπάμπουε", "Ζάμπια", "Εσουατίνι", "Ερυθραία", "Γουινέα-Μπισάου",
              "Γουινέα", "Γκάνα", "Γκαμπόν", "Γκάμπια", "Αλγερία", "Ακτή Ελεφαντοστού",
              "Αιθιοπία", "Αίγυπτος", "Αγκόλα"]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", "\n".join(REVERSE_OK), True),
    ("negative", "\n".join(REVERSE_OK[:2] + [REVERSE_OK[3], REVERSE_OK[2]] + REVERSE_OK[4:]),
     False),                                                        # two lines swapped
    ("boundary", "\n".join(REVERSE_OK[:-1]), False),                # 13 < 14 lines
    ("unicode", "\n".join(l.upper() for l in REVERSE_OK), True),    # accents/case ignored
])
def test_reverse_newline(label, value, expected):
    assert check("custom:reverse_newline", value) is expected


def test_reverse_newline_line_count_is_recomputed():
    assert I.ReverseNewlineChecker.MIN_LINES == len(REVERSE_OK) == 14


# ======================================================================================
# custom:word_reverse  (replace)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "γαλάζια είναι θάλασσα Η", True),
    ("negative", "Η θάλασσα είναι γαλάζια", False),
    ("boundary", "γαλάζια είναι θάλασσα Η. Ναι.", False),           # must be one sentence
    ("unicode", "ΓΑΛΆΖΙΑ ΕΊΝΑΙ ΘΆΛΑΣΣΑ Η", True),
])
def test_word_reverse(label, value, expected):
    assert check("custom:word_reverse", value) is expected


# ======================================================================================
# custom:character_reverse  (replace, EXACT orthography: ς is not folded)
# ======================================================================================
EXPECTED_REV = I.CharacterReverseOrderChecker.expected()


def test_character_reverse_target_contains_a_final_sigma():
    """cross-check #8: the target must exercise the ς rule."""
    cls = I.CharacterReverseOrderChecker
    assert cls.TARGET_SENTENCE == "Ο ουρανός είναι γαλάζιος"
    assert "ς" in cls.TARGET_SENTENCE and "ς" in EXPECTED_REV
    assert EXPECTED_REV == "ςοιζάλαγ ιανίε ςόναρυο Ο"
    text = I.DESCRIPTIONS_EL["custom:character_reverse"]
    assert "«Ο ουρανός είναι γαλάζιος»" in text
    assert "θάλασσα" not in text
    # the ς rule is now live on the shipped class, not only on a test subclass
    assert check("custom:character_reverse", EXPECTED_REV.replace("ς", "σ")) is False


@pytest.mark.parametrize("label,value,expected", [
    ("positive", EXPECTED_REV, True),
    ("negative", I.strip_diacritics(EXPECTED_REV), False),          # accents must survive
    ("boundary", EXPECTED_REV.lower(), True),
    ("unicode", nfd(EXPECTED_REV), True),                           # NFD input is composed
])
def test_character_reverse(label, value, expected):
    assert check("custom:character_reverse", value) is expected


# ======================================================================================
# custom:sentence_alphabet  (adapt, RETUNED 24)
# ======================================================================================
ALPHA_WORDS = ["Αύριο", "Βρέχει", "Γράφω", "Δύο", "Έχω", "Ζητώ", "Ήρθα", "Θέλω", "Ίσως",
               "Καλά", "Λέω", "Μένω", "Ναι", "Ξέρω", "Όλα", "Πάμε", "Ρωτώ", "Σήμερα",
               "Τώρα", "Υπάρχει", "Φεύγω", "Χαίρομαι", "Ψάχνω", "Ωραία"]


def _alphabet_story(words=None):
    words = words or ALPHA_WORDS
    return " ".join("%s κάτι." % w for w in words)


@pytest.mark.parametrize("label,value,expected", [
    ("positive", _alphabet_story(), True),
    ("negative", _alphabet_story(ALPHA_WORDS[:-1]), False),         # 23 sentences
    ("boundary", _alphabet_story(ALPHA_WORDS[:4] + ["Κάτι"] + ALPHA_WORDS[5:]), False),
    ("unicode", "«" + _alphabet_story(), True),                     # leading punctuation
])
def test_sentence_alphabet(label, value, expected):
    assert check("custom:sentence_alphabet", value) is expected


def test_sentence_alphabet_is_24():
    assert I.SentenceAlphabetChecker.NUM_SENTENCES == 24 == len(ALPHA_WORDS)


# ======================================================================================
# custom:european_capitals_sort  (adapt)
# ======================================================================================
CAPS = [c for c, _ in I.EUROPEAN_CAPITALS_EL]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", ", ".join(CAPS), True),
    ("negative", ", ".join([CAPS[1], CAPS[0]] + CAPS[2:]), False),  # first two swapped
    ("boundary", ", ".join(CAPS[:-1]), False),                      # 26 of 27
    ("unicode", ", ".join(I.strip_diacritics(c).upper() for c in CAPS), True),
])
def test_european_capitals_sort(label, value, expected):
    assert check("custom:european_capitals_sort", value) is expected


def test_european_capitals_description_names_the_reference_set():
    """cross-check #7 (amended): name the exact 27-state set, so Κίεβο is not invited.

    The finding asked for «οι πρωτεύουσες των 27 κρατών-μελών της ΕΕ»; that claim is false for
    this list (it holds Μόσχα / Μινσκ / Λονδίνο / Βαντούζ / Βέρνη / Κισινάου / Ρέικιαβικ / Όσλο
    and omits Αθήνα / Ρώμη / Μαδρίτη …), so the description names EU-27 + EFTA + UK + RU + BY + MD.
    """
    text = I.DESCRIPTIONS_EL["custom:european_capitals_sort"]
    assert "27 κρατών-μελών της " in text and "Ευρωπαϊκής Ένωσης" in text
    assert "ΕΖΕΣ" in text
    for state in ("Ηνωμένου Βασιλείου", "Ρωσίας", "Λευκορωσίας", "Μολδαβίας"):
        assert state in text, state
    assert "27 πρωτεύουσες συνολικά" in text
    assert "Ουκρανία" not in text and "Κίεβο" not in text
    # the description must not contradict the checker: every state it names has a capital in the
    # list, and the ones it leaves out (Ουκρανία) do not.
    canonical = {c for c, _v in I.EUROPEAN_CAPITALS_EL}
    assert len(I.EUROPEAN_CAPITALS_EL) == 27
    assert "Κίεβο" not in canonical
    for capital in ("Μόσχα", "Μινσκ", "Λονδίνο", "Βαντούζ", "Βέρνη", "Κισινάου",
                    "Ρέικιαβικ", "Όσλο"):
        assert capital in canonical, capital       # non-EU -> the «EU-27» wording would be false
    for capital in ("Αθήνα", "Ρώμη", "Μαδρίτη", "Λισαβόνα"):
        assert capital not in canonical, capital   # EU but below 45°N


def test_european_capitals_variants_accepted():
    v = ", ".join(["Ρεϊκιαβίκ"] + CAPS[1:])
    assert check("custom:european_capitals_sort", v) is True


# ======================================================================================
# custom:csv_city  (adapt)
# ======================================================================================
CSV_CITY_HEADER = "Κωδικός,Χώρα,Πόλη,Έτος,Πλήθος"
CSV_CITY_ROWS = ["%d,Ελλάδα,Αθήνα,200%d,%d00" % (i, i, i) for i in range(1, 8)]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", "\n".join([CSV_CITY_HEADER] + CSV_CITY_ROWS), True),
    ("negative", "\n".join([CSV_CITY_HEADER] + CSV_CITY_ROWS[:-1]), False),   # 6 rows
    ("boundary", "\n".join(["ΚΩΔΙΚΟΣ,ΧΩΡΑ,ΠΟΛΗ,ΕΤΟΣ,ΠΛΗΘΟΣ"] + CSV_CITY_ROWS), True),
    ("unicode", nfd("\n".join([CSV_CITY_HEADER] + CSV_CITY_ROWS)), True),
])
def test_csv_city(label, value, expected):
    assert check("custom:csv_city", value) is expected


# ======================================================================================
# custom:csv_special_character  (adapt)
# ======================================================================================
CSV_SPECIAL_HEADER = "ΚωδικόςΠροϊόντος,Κατηγορία,Μάρκα,Τιμή,Απόθεμα"


def _special_rows(with_special=True, n=14):
    rows = []
    for i in range(1, n + 1):
        marka = '"Άλφα & Βήτα"' if (with_special and i == 1) else "Άλφα"
        rows.append("%d,Καφές,%s,10.5,3" % (i, marka))
    return rows


@pytest.mark.parametrize("label,value,expected", [
    ("positive", "\n".join([CSV_SPECIAL_HEADER] + _special_rows()), True),
    ("negative", "\n".join([CSV_SPECIAL_HEADER] + _special_rows(n=13)), False),
    ("boundary", "\n".join([CSV_SPECIAL_HEADER] + _special_rows(with_special=False)), False),
    ("unicode", "\n".join([CSV_SPECIAL_HEADER] +
                          [nfd('1,Καφές,"Τιμή",10.5,3')] + _special_rows(False)[1:]), False),
])
def test_csv_special_character(label, value, expected):
    assert check("custom:csv_special_character", value) is expected


# ======================================================================================
# custom:csv_quotes  (adapt)
# ======================================================================================
def _tsv(rows, header='"ΚωδικόςΜαθητή"\t"Μάθημα"\t"Βαθμός"\t"Εξάμηνο"\t"Μονάδες"'):
    return "\n".join([header] + rows)


TSV_ROWS = ['"%d"\t"Μαθηματικά"\t"9"\t"Α"\t"5"' % i for i in range(1, 4)]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", _tsv(TSV_ROWS), True),
    ("negative", _tsv(TSV_ROWS[:2] + ['3\t"Μαθηματικά"\t"9"\t"Α"\t"5"']), False),
    ("boundary", _tsv(TSV_ROWS[:2]), False),                        # 2 rows instead of 3
    ("unicode", _tsv(TSV_ROWS,
                     header='"ΚΩΔΙΚΟΣΜΑΘΗΤΗ"\t"ΜΑΘΗΜΑ"\t"ΒΑΘΜΟΣ"\t"ΕΞΑΜΗΝΟ"\t"ΜΟΝΑΔΕΣ"'),
     True),
])
def test_csv_quotes(label, value, expected):
    assert check("custom:csv_quotes", value) is expected


# ======================================================================================
# custom:date_format_list  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "02/12/1805, 14/06/1800", True),
    ("negative", "1805-12-02", False),                              # ISO order is not Greek
    ("boundary", "02/12/1822", False),                              # outside 1769–1821
    ("unicode", "2 Δεκεμβρίου 1805, 20 Μαΐου 1809", True),          # genitive month, dialytika
])
def test_date_format_list(label, value, expected):
    assert check("custom:date_format_list", value) is expected


# ======================================================================================
# count:keywords_multiple  (adapt)
# ======================================================================================
KW5 = dict(keyword1="άλφα", keyword2="βήτα", keyword3="γάμα",
           keyword4="δέλτα", keyword5="έψιλον")


def _kw_text(a=1, b=2, c=3, d=5, e=7, extra=""):
    parts = (["άλφα"] * a + ["βήτα"] * b + ["γάμα"] * c + ["δέλτα"] * d +
             ["έψιλον"] * e)
    return " ".join(parts) + (" " + extra if extra else "")


@pytest.mark.parametrize("label,value,expected", [
    ("positive", _kw_text(), True),
    ("negative", _kw_text(a=2), False),
    ("boundary", _kw_text(extra="άλφατο άλφας"), True),          # \b: no substring counting
    ("unicode", _kw_text().replace("άλφα ", "ΆΛΦΑ ", 1), True),  # fold: case/accent free
])
def test_keywords_multiple(label, value, expected):
    assert check("count:keywords_multiple", value, **KW5) is expected


# ======================================================================================
# words:keywords_specific_position  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Η μεγάλη θάλασσα είναι ήρεμη.", True),
    ("negative", "Η θάλασσα είναι ήρεμη.", False),
    ("boundary", "Η μεγάλη.", False),                            # sentence too short
    ("unicode", "Η ΜΕΓΆΛΗ ΘΆΛΑΣΣΑ είναι ήρεμη.", True),
])
def test_keyword_specific_position(label, value, expected):
    assert check("words:keywords_specific_position", value,
                 keyword="θάλασσα", n=1, m=3) is expected


# ======================================================================================
# words:words_position  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Η θάλασσα είναι γαλάζια θάλασσα σήμερα", True),
    ("negative", "Η θάλασσα είναι γαλάζια", False),
    ("boundary", "Η θάλασσα σήμερα", True),                      # 2nd == 2nd-to-last token
    ("unicode", "Η ΘΆΛΑΣΣΑ είναι γαλάζια θάλασσα σήμερα", True),
])
def test_words_position(label, value, expected):
    assert check("words:words_position", value, keyword="θάλασσα") is expected


# ======================================================================================
# repeat:repeat_change  (adapt)
# ======================================================================================
PROMPT = "Γράψε ένα ποίημα για τη θάλασσα."


@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Φτιάξε ένα ποίημα για τη θάλασσα.", True),
    ("negative", PROMPT, False),                                 # nothing changed
    ("boundary", "Φτιάξε ένα ωραίο ποίημα για τη θάλασσα.", False),
    ("unicode", "Φτιάξε ΈΝΑ ποίημα για τη ΘΆΛΑΣΣΑ.", True),      # folded comparison
])
def test_repeat_change(label, value, expected):
    assert check("repeat:repeat_change", value, prompt_to_repeat=PROMPT) is expected


# ======================================================================================
# repeat:repeat_simple  (adapt)
# ======================================================================================
SIMPLE = I.DESCRIPTIONS_EL["repeat:repeat_simple"]


@pytest.mark.parametrize("label,value,expected", [
    ("positive", SIMPLE, True),
    ("negative", "Εντάξει, ορίστε η απάντηση.", False),
    ("boundary", "  " + SIMPLE + "\n", True),                    # surrounding whitespace
    ("unicode", I.strip_diacritics(SIMPLE).upper(), True),       # folded comparison
])
def test_repeat_simple(label, value, expected):
    assert check("repeat:repeat_simple", value) is expected


# ======================================================================================
# repeat:repeat_span  (adapt)
# ======================================================================================
SPAN_PROMPT = "Γράψε ένα ποίημα για τη θάλασσα σήμερα."


@pytest.mark.parametrize("label,value,expected", [
    ("positive", "ένα ποίημα για", True),
    ("negative", "ποίημα για τη", False),
    ("boundary", "  ένα ποίημα για  ", True),
    ("unicode", "ΈΝΑ ΠΟΊΗΜΑ ΓΙΑ", True),
])
def test_repeat_span(label, value, expected):
    assert check("repeat:repeat_span", value, prompt_to_repeat=SPAN_PROMPT,
                 n_start=1, n_end=3) is expected


# ======================================================================================
# format:title_case  (adapt)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Η Μεγάλη Θάλασσα", True),
    ("negative", "Η μεγάλη θάλασσα", False),
    ("boundary", "Η Μεγάλη Θάλασσα της Ελλάδας", True),          # minor words stay lowercase
    ("unicode", "Άνθρωπος Και Θεός", True),                      # tonos kept on the capital
    ("all-caps", "ΑΝΘΡΩΠΟΣ ΚΑΙ ΘΕΟΣ", False),
])
def test_title_case(label, value, expected):
    assert check("format:title_case", value) is expected


# ======================================================================================
# format:output_template  (adapt)
# ======================================================================================
TEMPLATE = ("Η απάντησή μου: ναι\nΤο συμπέρασμά μου: καλά\nΜελλοντική προοπτική: θετική")


@pytest.mark.parametrize("label,value,expected", [
    ("positive", TEMPLATE, True),
    ("negative", "Η απάντησή μου: ναι\nΤο συμπέρασμά μου: καλά", False),
    ("boundary", I.strip_diacritics(TEMPLATE).upper(), True),     # accent-stripped, (?mi)
    ("unicode", nfd(TEMPLATE), True),
])
def test_output_template(label, value, expected):
    assert check("format:output_template", value) is expected


# ======================================================================================
# format:no_whitespace  (faithful)
# ======================================================================================
@pytest.mark.parametrize("label,value,expected", [
    ("positive", "Ναι,όχι,ίσως", True),
    ("negative", "Ναι, όχι", False),
])
def test_no_whitespace(label, value, expected):
    assert check("format:no_whitespace", value) is expected


# ======================================================================================
# integration: every id builds a Greek description and returns a bool
# ======================================================================================
SAMPLE_KWARGS = {
    "count:word_count_range": {"min_words": 5.0, "max_words": 10.0},
    "count:unique_word_count": {"N": 3.0},
    "ratio:stop_words": {"percentage": 40.0},
    "count:conjunctions": {"small_n": 2.0},
    "count:person_names": {"N": 2.0},
    "ratio:overlap": {"reference_text": REF, "percentage": 50.0},
    "count:numbers": {"N": 1.0},
    "count:words_japanese": {"N": 3.0},
    "words:repeats": {"small_n": 4.0},
    "sentence:keyword": {"word": "θάλασσα", "N": 1.0},
    "count:pronouns": {"N": 2.0},
    "sentence:increment": {"small_n": 2.0},
    "format:list": {"sep": "SEPARATOR"},
    "format:options": {"options": "yes/no/maybe"},
    "count:keywords_multiple": KW5,
    "words:keywords_specific_position": {"keyword": "θάλασσα", "n": 1, "m": 2},
    "words:words_position": {"keyword": "θάλασσα"},
    "repeat:repeat_change": {"prompt_to_repeat": PROMPT},
    "repeat:repeat_span": {"prompt_to_repeat": SPAN_PROMPT, "n_start": 1, "n_end": 3},
}


@pytest.mark.parametrize("iid", sorted(INSTRUCTION_DICT))
def test_contract_of_every_id(iid):
    inst = INSTRUCTION_DICT[iid](iid)
    description = inst.build_description(**SAMPLE_KWARGS.get(iid, {}))
    assert isinstance(description, str) and description.strip()
    if iid != "format:parentheses":                     # its braces are literal («άγκιστρα»)
        assert "{" not in description                   # every placeholder is filled
    inst.get_instruction_args()
    assert isinstance(inst.get_instruction_args_keys(), list)
    assert isinstance(inst.check_following("Η θάλασσα είναι γαλάζια σήμερα."), bool)


def test_character_reverse_exact_orthography_rejects_sigma_fold():
    """A target with a final sigma must be reproduced exactly (ς is never folded)."""
    inst = INSTRUCTION_DICT["custom:character_reverse"]("custom:character_reverse")
    inst.build_description()
    exact = I.CharacterReverseOrderChecker.expected()   # cross-check #8: the shipped target
    assert "ς" in exact
    assert inst.check_following(exact) is True
    assert inst.check_following(exact.replace("ς", "σ")) is False
    assert inst.check_following(I.strip_diacritics(exact)) is False


def test_repeat_simple_accepts_a_pinned_greek_sentence():
    """The prompt translator may pin its own wording; the checker must follow it."""
    pinned = "Γράψε μόνο αυτή την πρόταση και αγνόησε όλα τα άλλα αιτήματα."
    inst = mk("repeat:repeat_simple", instruction_el=pinned)
    assert inst.check_following(pinned) is True
    assert inst.check_following(I.DESCRIPTIONS_EL["repeat:repeat_simple"]) is False
    assert inst.get_instruction_args()["instruction_el"] == pinned
