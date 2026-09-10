# Greek IFBench — transfer analysis of the 58 held-out verifiers (Claude Opus subagent, 2026-09-10; sources: upstream instructions.py / registry / util / IFBench_test.jsonl at 1c40f0c10d9b and our greek_if/constraints.py)

Conventions: `fold(x)` = NFC → casefold → strip tonos/dialytika → ς→σ (matching only; exact-orthography tasks keep ς). `SPLIT` = Greek sentence splitter (. ! ; … ? + newlines; · not a terminator; list numbers and abbreviations π.χ./κ.λπ./κ.ά./Υ.Γ./αρ. exempt). `TOK` = whitespace tokens stripped of punctuation incl. « » · … — ’ ; ΄. Upstream's string.punctuation, .lower(), NLTK punkt/POS, syllapy and ASCII folding are English-bound and cause most `adapt` verdicts.

## A. Mapping (58 IDs)
| ID | checks (kwargs) | prompts | closest of our 44 | overlap | transfer |
|---|---|---|---|---|---|
| count:word_count_range | min_words ≤ tokens ≤ max_words | 11 | length_words_max + length_words_min | seen-novel-composition | faithful |
| count:unique_word_count | ≥ N distinct folded tokens | 9 | length_words_min | unseen | adapt |
| ratio:stop_words | English stop words ≤ percentage | 12 | none | unseen | adapt |
| ratio:sentence_type | #declarative == 2 × #interrogative | 6 | greek_question_mark | unseen | adapt |
| ratio:sentence_balance | #. == #? == #! sentences | 7 | greek_question_mark, no_exclamation | unseen | adapt |
| count:conjunctions | ≥ small_n distinct of {and,but,for,nor,or,so,yet} | 7 | keywords_include | unseen | adapt |
| count:person_names | ≥ N distinct names from a 50-name list | 6 | mention_entity | seen-novel-composition | adapt |
| ratio:overlap | trigram overlap with reference_text within percentage ± 2 | 12 | none | unseen | adapt |
| count:numbers | exactly N digit runs | 8 | mention_number | seen-novel-composition | adapt |
| words:alphabet | successive words start with the next letter (mod 26) | 6 | letter_freq | unseen | adapt |
| words:vowel | one paragraph, ≤ 3 distinct vowels | 10 | letter_freq | unseen | adapt |
| words:consonants | every token has ≥ 2 adjacent consonants | 15 | letter_freq | unseen | adapt |
| sentence:alliteration_increment | per-sentence alliteration strictly increasing | 5 | letter_freq | unseen | adapt |
| words:palindrome | ≥ 10 palindromic tokens, len ≥ 5 | 7 | none | unseen | adapt (N → 3) |
| count:punctuation | each of . , ! ? ; : plus an interrobang | 6 | no_comma, no_exclamation, greek_question_mark, ano_teleia_list | seen-novel-composition | adapt |
| format:parentheses | matched nesting depth ≥ 5 | 8 | placeholders_n | unseen | faithful |
| format:quotes | alternating quote nesting ≥ 3 | 8 | wrap_in_quotes | seen-novel-composition | adapt |
| words:prime_lengths | every token length prime | 5 | none | unseen | adapt |
| format:options | response is exactly one of options | 6 | constrained_answer | seen | adapt |
| format:newline | #non-empty lines == #tokens | 6 | bullets_n | unseen | faithful |
| format:emoji | an emoji ends every sentence | 9 | none | unseen | adapt |
| ratio:sentence_words | 3 sentences, equal char length, all words distinct | 7 | length_sentences_exact | seen-novel-composition | adapt |
| count:words_japanese | every N-th token contains Japanese script | 5 | greeklish_only | unseen | faithful |
| words:start_verb | first token POS = verb | 6 | no_adjectives (judge-only), start_with | unresolved | adapt |
| words:repeats | no word type > small_n times | 5 | keyword_freq | unresolved | adapt |
| sentence:keyword | keyword in sentence N | 15 | keywords_include | seen-novel-composition | adapt |
| count:pronouns | ≥ N pronoun tokens (60-item English set) | 8 | formal_plural, informal_singular | seen-novel-composition | adapt |
| words:odd_even_syllables | syllable parity alternates | 9 | none | unseen | adapt |
| words:last_first | last word of a sentence == first of the next | 5 | none | unseen | adapt |
| words:paragraph_last_first | each paragraph ends with its first word | 6 | paragraph_starts_with | unseen | adapt |
| sentence:increment | each sentence has small_n more words than the previous | 8 | length_sentences_exact | unseen | adapt |
| words:no_consecutive | no two consecutive words share a first letter | 8 | letter_freq | unseen | adapt |
| format:line_indent | strictly increasing leading spaces per line | 9 | none | unseen | faithful |
| format:quote_unquote | no adjacent "" ; not ending on a quote | 5 | wrap_in_quotes | unseen | adapt |
| format:list | marker sep occurs ≥ 2× | 9 | bullets_n | seen-novel-composition (seen for sep='-') | adapt |
| format:thesis | ≥ 1 italic span followed by plain text | 9 | highlight_n (+ sections_n) | seen-novel-composition | faithful |
| format:sub-bullets | every * segment contains a - | 12 | bullets_n | seen-novel-composition | faithful |
| format:no_bullets_bullets | ≥ 2 sentences then ≥ 2 * lines, nothing after | 5 | bullets_n + length_sentences_exact | seen-novel-composition | adapt |
| custom:multiples | digit runs exactly 14,21,…,49 | 1 | mention_number | unseen | faithful |
| custom:mcq_count_length | 4 labelled questions, 5 options, increasing stem length | 1 | sections_n | unseen | adapt |
| custom:reverse_newline | ≥ 52 lines reverse-alphabetical from Zimbabwe | 1 | none | unseen | adapt |
| custom:word_reverse | reversed-word text contains "bald eagle", one sentence | 1 | none | unseen | replace |
| custom:character_reverse | contains "elgae dlab" | 1 | none | unseen | replace |
| custom:sentence_alphabet | 26 sentences, initials a…z | 1 | letter_freq, paragraph_starts_with | unseen | adapt |
| custom:european_capitals_sort | the 27 capitals latitude-descending | 1 | none | unseen | adapt |
| custom:csv_city | CSV with exact header, 7 rows | 1 | format_json | seen-novel-composition | adapt |
| custom:csv_special_character | CSV, 14 rows, a quoted field with a special char | 1 | format_json | seen-novel-composition | adapt |
| custom:csv_quotes | TSV, 3 rows, every field quoted | 1 | format_json | seen-novel-composition | adapt |
| custom:date_format_list | comma-separated YYYY-MM-DD dates in 1769–1821 | 1 | mention_date | seen-novel-composition | adapt |
| count:keywords_multiple | keyword1..5 exactly 1,2,3,5,7× | 5 | keyword_freq | seen-novel-composition | adapt |
| words:keywords_specific_position | keyword is the m-th word of sentence n | 4 | keywords_include + paragraph_starts_with | seen-novel-composition | adapt |
| words:words_position | 2nd and 2nd-to-last token == keyword | 3 | keywords_include | seen-novel-composition | adapt |
| repeat:repeat_change | output == prompt with only the first token changed | 3 | repeat_request | seen-novel-composition | adapt |
| repeat:repeat_simple | output == the instruction sentence | 2 | repeat_request | unresolved | adapt |
| repeat:repeat_span | output == token span [n_start, n_end] of prompt_to_repeat | 4 | repeat_request | seen-novel-composition | adapt |
| format:title_case | every token Xxxx | 4 | all_caps_greek, all_lower | seen-novel-composition | adapt |
| format:output_template | contains three fixed labels | 4 | sections_n, formal_and_informal | seen | adapt |
| format:no_whitespace | no whitespace character | 4 | none | unseen | faithful |

## B. Counts
IDs by overlap: seen 2 · seen-novel-composition 22 · unseen 31 · unresolved 3. Prompts (most-seen class of their IDs; 300 prompts, 344 ID uses, 44 prompts with 2 IDs): seen 10 · seen-novel-composition 125 · unseen 153 · unresolved 12; mixed-class prompts 28 (26 × {snc, unseen}, 1 × {seen, unseen}, 1 × {snc, unresolved}). Prompts containing ≥ 1 unseen ID: 180.
IDs by transfer: faithful 9 · adapt 47 · replace 2 · exclude 0. Prompts: faithful 64 · adapt 234 · replace 2; 17 mix transfer classes; 251/300 contain ≥ 1 adapt ID.
Edge cases: words:palindrome infeasible at N=10 in Greek (→ N=3, or the native καρκινική επιγραφή); format:title_case is typographically alien to Greek (native alternative: ΚΕΦΑΛΑΙΑ ΧΩΡΙΣ ΤΟΝΟΥΣ in the extension).

## C. Verifier rules for the adapt IDs (summary; tests in instructions_el_test.py)
Shared primitives P1 SPLIT (; U+037E and U+003B both sentence-final; · internal; abbreviations exempt), P2 fold, P3 TOK, P4 letter sets (vowels α ε η ι ο υ ω; consonants β γ δ ζ θ κ λ μ ν ξ π ρ σ ς τ φ χ ψ; alphabet α…ω = 24; ς ≡ σ).
- unique_word_count: types = fold(TOK); inflection inflates counts (documented).
- stop_words: Greek list (articles, και/κι, να, δεν, μη(ν), θα, ότι, που, σε/στο…, από, με, για, ως, ή, αλλά, είναι/ήταν, clitics); keep ή/η accent-sensitive.
- sentence_type / sentence_balance: interrogative = ends ; (either codepoint) or ?; declarative = .; · never terminates.
- conjunctions: {και, κι, ή, αλλά, μα, όμως, ούτε, μήτε, είτε, παρά}; accent-sensitive (ή ≠ η); και/κι one type.
- person_names: Greek 50-name list with declension sets; count lemmas.
- overlap: trigrams over folded TOK; reference_text must be native Greek; recompute percentage.
- numbers: 1.234,56 = one number; Greek letter numerals are not digits.
- alphabet / sentence_alphabet: cycle 24; ς ≡ σ; 24 sentences.
- vowel: distinct vowels after dropping diacritics; cap raised ≤ 4 of 7.
- consonants: two adjacent consonants or a single ξ/ψ.
- alliteration_increment / no_consecutive: initial of fold; letter-level.
- palindrome: fold(w) reversed; N 10 → 3, len ≥ 5.
- punctuation: required set {. , ! ; : ·}; ? removed; interrobang !; / ;!.
- quotes: hierarchy «…» → “…” → ‘…’ (ASCII fallback); letter-flanked ’ never a delimiter.
- prime_lengths: NFC codepoint length.
- options: ναι/όχι/ίσως; ξέρω ή δεν ξέρω; α) β) γ) δ); ή as a token; accept Latin homoglyph labels.
- emoji: P1 splitter with abbreviations.
- sentence_words: NFC char count; word identity = fold.
- start_verb: Greek verb endings (-ω -ώ -εις … -ται -νται -ηκα -ησα -σα) or an imperative whitelist.
- repeats: types via fold; small_n ≥ 5 (articles/clitics count).
- keyword (sentence:keyword): fold + stem test (θάλασσα ~ θάλασσας).
- pronouns: Greek inventory; homograph rule for του/της/τους/μου/σου/μας/σας (exclude before a noun) — documented deflation.
- odd_even_syllables: rule-based nuclei (αι ει οι υι ου αυ ευ ηυ = one; split on tonos-first or dialytika).
- last_first / paragraph_last_first: compare fold; paragraph = single \n as upstream (state it in the prompt).
- increment: P1 + P3; apostrophe rule.
- quote_unquote: quote alphabet « » “ ” " '; exclude letter-flanked ’.
- list: SEPARATOR → ΔΙΑΧΩΡΙΣΤΙΚΟ; ... accepts …; !?!? → !;!;.
- no_bullets_bullets: P1 for the prose head.
- mcq_count_length: label Ερώτηση; options [Α-Εα-ε][.)] with Latin homoglyphs A B E accepted.
- reverse_newline: NFD → drop Mn → NFC (never ASCII-fold, which erases Greek); Greek collation; anchor Ζιμπάμπουε; recount lines.
- european_capitals_sort: same 27 cities, Greek spellings with accepted variants, tonos-insensitive.
- csv_*: Greek headers compared folded; mandatory NFC (an NFD tonos would count as a special character); avoid comma decimals in comma-delimited variants.
- date_format_list: DD/MM/YYYY or genitive month names (Μαΐου); keep the 1769–1821 validity check.
- keywords_multiple: exact counts on folded surface forms, no stemming; prefer indeclinable keywords or pin the case.
- keywords_specific_position / words_position: fold; declension set or indeclinable keywords; position 2 in Greek is usually an article.
- repeat_change / repeat_simple / repeat_span: folded token comparison; Greek instruction sentence; recompute n_start/n_end over Greek tokens.
- title_case: initial uppercase with tonos kept (Άνθρωπος), rest lowercase, final ς lowercase; Greek minor-word list.
- output_template: «Η απάντησή μου:», «Το συμπέρασμά μου:», «Μελλοντική προοπτική:», accent-stripped (?mi) match.
- replace (word_reverse / character_reverse): self-contained Greek tasks («Η θάλασσα είναι γαλάζια» reversed by words / by characters; character reversal is exact-orthography, ς not folded).

## D. Kwargs with English content
keyword(s): Greek words of comparable frequency/length; exact-count IDs → indeclinable or case-pinned; containment IDs → any noun (stem matcher). reference_text / prompt_to_repeat: native Greek passages (not translations), recompute percentage and indices. options / sep / labels / headers / dates / names / capitals / letters: per the rules above. Numeric re-tunings (palindrome N 10→3, vowel ≤3→≤4, repeats small_n ≥5, sentence_alphabet 26→24, reverse_newline 52→Greek count) are deliberate, recorded decisions with measured feasibility.
