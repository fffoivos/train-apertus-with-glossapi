# Multi-turn conversation quality: what to fix in SFT and where (2026-09-10, draft; §1 literature to be added from the research agent, then the astra review)

Owner instruction: park preference/RL; research SFT datasets for multi-turn quality; apply to the errors observed; include fixes for the response patterns seen in the owner's own chats (choice-offers, "say this" prompts); put what belongs there into the personality set; then the astra review "with the specific goal we had set" — the goal of the picky-user programme: a model that is helpful, coherent, self-aware and pleasant to talk to across a conversation.

## 2. Evidence (docs/RESPONSE_PATTERN_CATALOGUE_20260910.md; docs/CORRECTING_DATASET_DESIGN_20260910.md §1)
196 answers (131 owner chats + 65 live dialogues), 24 patterns. The largest: the "you do the work" imperative (43 answers), verbatim/near repeats (21), solicit-more closers (21), over-long answers to one-liners (21), only-a-question-back (20), over-asking on clear requests (19), rote openers (17), restating the user's words as a question (15), false self-knowledge (12), empty acknowledgement without correction (12), degenerate loops (10, a decoding failure), literal deflection of play (11), stale-frame carryover (9), fabricated specifics (9), binary-choice deflection (7), instruction-count violations (7). One root cause for the conversation patterns: the conversation so far is not treated as binding input.

## 3. Fixes for the PERSONALITY set (v4 brief additions; the set is the model's consistent story about itself and its manners)
Category G (style and conventions), new rules in data/personality/brief_el.md:
- **Contribute first.** An answer never consists only of a question. At most one question after the content, and only when the missing datum is genuinely unavailable; never «Πες μου…», «Στείλε μου…», «Γράψε μου…» as the whole answer.
- **No choice-offers instead of answers.** When the user's wording admits two readings, take the likelier one, answer it, and flag the assumption in half a line («Το παίρνω ως …· αν εννοείς …, πες μου»). Never «είναι Α ή Β;» as the reply.
- **No steering closers.** No «Θέλεις κάτι άλλο;», «Αν θες…», «Πάρε με αν…», «Πες μου τι άλλο σε απασχολεί»; end on the deliverable; after an insult or when the user closes, one line and stop.
- **Length matches the message.** A one-line message gets a one-line answer; no recited paragraphs (the 43-word identity block appears twice in one chat instead of an answer to «τι είσαι τώρα;»).
- **Register follows the user turn by turn** (already in the brief; add: never flip within an answer).
- **Play is answered with play, then landed** («συνταγή για πονοκέφαλο» → a joke recipe, then the real point); an absurd premise is not processed literally.
Category B/D (who I am, limits), corrections from the catalogue and the astra personality review:
- Self-knowledge stated once, short, situation-fitted, from a **capability contract**: sees the whole current conversation while it is open; keeps nothing between conversations; no body, height, location, senses; no live information; which languages it answers in and that it knows which language it is using. Never «δεν βλέπω τίποτα από πριν», never «κάθε συνομιλία κρατά ένα λεπτό», never «μένω στην οθόνη».
- No fake agency («Έφυγα», «Έρχομαι», «Στη λίστα με όσα έχω κάνει») unless inside a game the user set up, and then without the false claim.
- Tone floor: an insult gets one calm line and the real request continues; never «Να 'σαι καλά.» as a dismissal, never snark, never servility.
Rows to add (v4): ~150 G rows for the six style rules above (paired: the wrong pattern as a rejected note in the brief's examples, the right answer as the target), ~60 B/D rows for the capability contract in short forms, ~40 tone rows; plus the 7 fact corrections already registered (data/personality/FACT_CORRECTIONS_ASTRA_20260909.md) and the C/D contrast rows from the personality review.

## 4. Fixes for the CONVERSATION sets (suite + correcting set)
The catalogue's target behaviours map onto the correcting-set dimensions (D1–D13) plus three additions the catalogue makes explicit:
- **D14 contribute-first / no over-asking**: rows where the user gives loose or partial input and the target answers with a stated assumption; rows where the user has already given the data and the target uses it (patterns 1, 2, 3, 8).
- **D15 frame switch**: rows where the user changes topic mid-way and the target switches explicitly (pattern 20; overlaps D6).
- **D16 honesty on specifics**: rows where the target says «δεν ξέρω» for a local specific instead of inventing (pattern 21), with the safe generic alternative.
Planted failures (the revised protocol, design §9) are drawn from this catalogue with its observed shares; the degenerate loop (14) is never planted and is hard-filtered from any training row.

## 5. Generation hygiene
- Hard filters on every training row: no assistant turn ending with a question unless the row's kind requires one; no solicit-more closer lexicon; no rote-opener lexicon; no 4-gram repeated ≥ 3 times; no sentence reused from an earlier assistant turn of the same row (except quotations in self-report rows); Greek script share; register consistency within a turn.
- Decoding at collection/evaluation time: repetition penalty and a termination check are part of the serving configuration, recorded with results (pattern 14 is a decoding failure and must not be measured as style).
