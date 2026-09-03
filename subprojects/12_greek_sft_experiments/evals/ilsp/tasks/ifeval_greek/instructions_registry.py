"""Registry for the 25 instruction ids in ``ilsp/ifeval_greek``."""

from . import instructions


INSTRUCTION_DICT = {
    "keywords:existence": instructions.KeywordChecker,
    "keywords:frequency": instructions.KeywordFrequencyChecker,
    "keywords:forbidden_words": instructions.ForbiddenWords,
    "keywords:letter_frequency": instructions.LetterFrequencyChecker,
    "language:response_language": instructions.ResponseLanguageChecker,
    "length_constraints:number_sentences": instructions.NumberOfSentences,
    "length_constraints:number_paragraphs": instructions.ParagraphChecker,
    "length_constraints:number_words": instructions.NumberOfWords,
    "length_constraints:nth_paragraph_first_word": instructions.ParagraphFirstWordCheck,
    "detectable_content:number_placeholders": instructions.PlaceholderChecker,
    "detectable_content:postscript": instructions.PostscriptChecker,
    "detectable_format:number_bullet_lists": instructions.BulletListChecker,
    "detectable_format:constrained_response": instructions.ConstrainedResponseChecker,
    "detectable_format:number_highlighted_sections": instructions.HighlightSectionChecker,
    "detectable_format:multiple_sections": instructions.SectionChecker,
    "detectable_format:json_format": instructions.JsonFormat,
    "detectable_format:title": instructions.TitleChecker,
    "combination:two_responses": instructions.TwoResponsesChecker,
    "combination:repeat_prompt": instructions.RepeatPromptThenAnswer,
    "startend:end_checker": instructions.EndChecker,
    "change_case:capital_word_frequency": instructions.CapitalWordFrequencyChecker,
    "change_case:capital": instructions.CapitalLettersGreekChecker,
    "change_case:lowercase": instructions.LowercaseLettersGreekChecker,
    "punctuation:no_comma": instructions.CommaChecker,
    "startend:quotation": instructions.QuotationChecker,
}
