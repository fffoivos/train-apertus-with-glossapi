from pathlib import Path
from tempfile import gettempdir

from datasets import load_dataset

from evals.ilsp.tasks.ifeval_greek import instructions
from evals.ilsp.tasks.ifeval_greek.instructions_registry import INSTRUCTION_DICT


def checker(checker_class, **kwargs):
    instance = checker_class("test")
    instance.build_description(**kwargs)
    return instance


def test_greek_uppercase_and_lowercase_pass_and_fail():
    uppercase = checker(instructions.CapitalLettersGreekChecker)
    assert uppercase.check_following("ΑΥΤΗ ΕΙΝΑΙ ΜΙΑ ΆΡΙΣΤΗ ΔΟΚΙΜΗ.")
    assert not uppercase.check_following("ΑΥΤΗ η ΔΟΚΙΜΗ ΑΠΟΤΥΓΧΑΝΕΙ.")

    lowercase = checker(instructions.LowercaseLettersGreekChecker)
    assert lowercase.check_following("αυτή είναι μία ήρεμη δοκιμή.")
    assert not lowercase.check_following("αυτή η Δοκιμή αποτυγχάνει.")


def test_greek_capital_word_frequency_pass_and_fail():
    rule = checker(
        instructions.CapitalWordFrequencyChecker,
        capital_frequency=2,
        capital_relation="at least",
    )
    assert rule.check_following("ΔΥΟ ΛΕΞΕΙΣ και άλλες.")
    assert not rule.check_following("ΜΙΑ λέξη και άλλες.")


def test_greek_letter_frequency_pass_and_fail():
    rule = checker(
        instructions.LetterFrequencyChecker,
        letter="α",
        let_frequency=3,
        let_relation="at least",
    )
    assert rule.check_following("Άλφα και άλμα")
    assert not rule.check_following("βήμα")


def test_whitespace_word_count_with_greek_punctuation_pass_and_fail():
    rule = checker(instructions.NumberOfWords, num_words=3, relation="at least")
    assert rule.check_following("Μία, δύο· τρεις!")
    assert not rule.check_following("Μία — δύο.")


def test_greek_language_fallback_pass_and_fail(monkeypatch):
    monkeypatch.setattr(instructions, "langdetect", None)
    rule = checker(instructions.ResponseLanguageChecker, language="el")
    assert rule.check_following("Αυτό είναι καθαρά ελληνικό κείμενο με αρκετές λέξεις.")
    assert not rule.check_following("This response is entirely in English.")


def test_keywords_are_casefolded_and_accent_insensitive():
    rule = checker(instructions.KeywordChecker, keywords=["ΑΘΗΝΑ", "καφες"])
    assert rule.check_following("Στην Αθήνα ο ΚΑΦΕΣ είναι καλός.")
    assert not rule.check_following("Στην πόλη ο ΚΑΦΕΣ είναι καλός.")


def test_forbidden_words_are_casefolded_accent_insensitive_and_bounded():
    rule = checker(instructions.ForbiddenWords, forbidden_words=["καφές"])
    assert rule.check_following("Το καφετί χρώμα επιτρέπεται.")
    assert not rule.check_following("Ο ΚΑΦΕΣ απαγορεύεται εδώ.")


def test_end_phrase_is_taken_from_kwargs():
    rule = checker(instructions.EndChecker, end_phrase="Αυτό ήταν όλο!")
    assert rule.check_following("Μικρό κείμενο. Αυτό ήταν όλο!")
    assert not rule.check_following("Αυτό ήταν όλο! Πρόσθετη λέξη.")


def test_first_word_is_taken_from_kwargs():
    rule = checker(
        instructions.ParagraphFirstWordCheck,
        num_paragraphs=2,
        nth_paragraph=2,
        first_word="δεύτερη",
    )
    assert rule.check_following("Πρώτη παράγραφος.\n\n«Δεύτερη» παράγραφος.")
    assert not rule.check_following("Πρώτη παράγραφος.\n\nΆλλη παράγραφος.")


def test_postscript_marker_is_taken_from_kwargs():
    rule = checker(instructions.PostscriptChecker, postscript_marker="Υ.Γ.")
    assert rule.check_following("Κύριο κείμενο.\nΥ.Γ. Μία τελευταία σκέψη.")
    assert not rule.check_following("Κύριο κείμενο χωρίς υστερόγραφο.")


def test_all_541_rows_load_and_instruction_ids_resolve():
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    token = token_path.read_text().strip() if token_path.exists() else None
    cache_dir = Path(gettempdir()) / "wp1d-ilsp-test-cache"
    dataset = load_dataset(
        "ilsp/ifeval_greek", split="train", token=token, cache_dir=str(cache_dir)
    )
    assert len(dataset) == 541

    observed = set()
    for row in dataset:
        assert len(row["instruction_id_list"]) == len(row["kwargs"])
        for instruction_id, raw_kwargs in zip(row["instruction_id_list"], row["kwargs"]):
            assert instruction_id in INSTRUCTION_DICT
            observed.add(instruction_id)
            instance = INSTRUCTION_DICT[instruction_id](instruction_id)
            kwargs = {key: value for key, value in raw_kwargs.items() if value is not None}
            instance.build_description(**kwargs)

    assert observed == set(INSTRUCTION_DICT)
