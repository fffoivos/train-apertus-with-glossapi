#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registry of the Greek IFBench instructions — same 58 ids as the upstream OOD set.

Drop-in replacement for `ifbench/instructions_registry.py`: `INSTRUCTION_DICT[id]` gives
a class with the upstream constructor / build_description / check_following contract, so
upstream's `evaluation_lib.py` can score Greek responses unchanged.
"""
from __future__ import annotations

try:  # package-style import
    from . import instructions_el  # type: ignore
except ImportError:  # plain-directory import
    import instructions_el

INSTRUCTION_DICT = {
    "count:word_count_range": instructions_el.WordCountRangeChecker,
    "count:unique_word_count": instructions_el.UniqueWordCountChecker,
    "ratio:stop_words": instructions_el.StopWordPercentageChecker,
    "ratio:sentence_type": instructions_el.SentTypeRatioChecker,
    "ratio:sentence_balance": instructions_el.SentBalanceChecker,
    "count:conjunctions": instructions_el.ConjunctionCountChecker,
    "count:person_names": instructions_el.PersonNameCountChecker,
    "ratio:overlap": instructions_el.NGramOverlapChecker,
    "count:numbers": instructions_el.NumbersCountChecker,
    "words:alphabet": instructions_el.AlphabetLoopChecker,
    "words:vowel": instructions_el.SingleVowelParagraphChecker,
    "words:consonants": instructions_el.ConsonantClusterChecker,
    "sentence:alliteration_increment": instructions_el.IncrementingAlliterationChecker,
    "words:palindrome": instructions_el.PalindromeChecker,
    "count:punctuation": instructions_el.PunctuationCoverChecker,
    "format:parentheses": instructions_el.NestedParenthesesChecker,
    "format:quotes": instructions_el.NestedQuotesChecker,
    "words:prime_lengths": instructions_el.PrimeLengthsChecker,
    "format:options": instructions_el.OptionsResponseChecker,
    "format:newline": instructions_el.NewLineWordsChecker,
    "format:emoji": instructions_el.EmojiSentenceChecker,
    "ratio:sentence_words": instructions_el.CharacterCountUniqueWordsChecker,
    "count:words_japanese": instructions_el.NthWordJapaneseChecker,
    "words:start_verb": instructions_el.StartWithVerbChecker,
    "words:repeats": instructions_el.LimitedWordRepeatChecker,
    "sentence:keyword": instructions_el.IncludeKeywordChecker,
    "count:pronouns": instructions_el.PronounCountChecker,
    "words:odd_even_syllables": instructions_el.AlternateParitySyllablesChecker,
    "words:last_first": instructions_el.LastWordFirstNextChecker,
    "words:paragraph_last_first": instructions_el.ParagraphLastFirstWordMatchChecker,
    "sentence:increment": instructions_el.IncrementingWordCountChecker,
    "words:no_consecutive": instructions_el.NoConsecutiveFirstLetterChecker,
    "format:line_indent": instructions_el.IndentStairsChecker,
    "format:quote_unquote": instructions_el.QuoteExplanationChecker,
    "format:list": instructions_el.SpecialBulletPointsChecker,
    "format:thesis": instructions_el.ItalicsThesisChecker,
    "format:sub-bullets": instructions_el.SubBulletPointsChecker,
    "format:no_bullets_bullets": instructions_el.SomeBulletPointsChecker,
    "custom:multiples": instructions_el.PrintMultiplesChecker,
    "custom:mcq_count_length": instructions_el.MultipleChoiceQuestionsChecker,
    "custom:reverse_newline": instructions_el.ReverseNewlineChecker,
    "custom:word_reverse": instructions_el.WordReverseOrderChecker,
    "custom:character_reverse": instructions_el.CharacterReverseOrderChecker,
    "custom:sentence_alphabet": instructions_el.SentenceAlphabetChecker,
    "custom:european_capitals_sort": instructions_el.EuropeanCapitalsSortChecker,
    "custom:csv_city": instructions_el.CityCSVChecker,
    "custom:csv_special_character": instructions_el.SpecialCharacterCSVChecker,
    "custom:csv_quotes": instructions_el.QuotesCSVChecker,
    "custom:date_format_list": instructions_el.DateFormatListChecker,
    "count:keywords_multiple": instructions_el.KeywordsMultipleChecker,
    "words:keywords_specific_position": instructions_el.KeywordSpecificPositionChecker,
    "words:words_position": instructions_el.WordsPositionChecker,
    "repeat:repeat_change": instructions_el.RepeatChangeChecker,
    "repeat:repeat_simple": instructions_el.RepeatSimpleChecker,
    "repeat:repeat_span": instructions_el.RepeatSpanChecker,
    "format:title_case": instructions_el.TitleCaseChecker,
    "format:output_template": instructions_el.OutputTemplateChecker,
    "format:no_whitespace": instructions_el.NoWhitespaceChecker,
}
