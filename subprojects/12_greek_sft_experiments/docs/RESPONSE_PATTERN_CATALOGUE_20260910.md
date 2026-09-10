# Response-pattern catalogue of arm B (2026-09-10)

Source: every assistant turn in the owner's 17 stored chats (131 answers) and the 15 live dialogues (65 answers); read by a Claude Opus subagent with the owner's own observations as the starting point ("is it this or that", "say this"). Ids: chats = 4-hex tail of the file + answer number (`1e19#A6`), live = `v1-8#t3`. The owner's three observations are verified: 36/196 answers end in a question (26% of chat answers), exactly 7 binary-choice endings (5 in one chat), one answer that is only an imperative prompt, but the "you do the work" imperative appears inside 43 answers, the single largest pattern, and the dominant failure in the live set (27/65).

| # | Pattern | Definition | Count (ids) | Verbatim examples | Appropriate? | Correct behaviour |
|---|---|---|---|---|---|---|
| 1 | Binary-choice deflection | offers the user two readings of their own words instead of answering | 7 (1e19#A6,A9,A11,A13,A15; 37df#A5; a8da#A4) | «Το «τσαντίζομαι» εδώ είναι «εκνευρίζομαι» ή «πειράζομαι»;» | only for a consequential ambiguity, and then answer both branches | pick the likelier reading, answer, flag the assumption in half a line: «Το παίρνω ως “με εκνευρίζεις”. Συγγνώμη — λέγε.» |
| 2 | Imperative prompt to the user | tells the user to produce the content the model owes | 43 (16 chat / 27 live; only-imperative 1: 1e19#A12) | «Πες μου τι έγινε τότε.»; «Γράψε ακριβώς την παραγγελία σου…» ×5; «Στείλε μου αριθμούς χρωμοσωμάτων και θα δούμε» | when a datum is genuinely missing, named once | do the work with what is given and state the assumption |
| 3 | Only-a-question-back | the whole answer is one question | 20 (1e19#A1–A3,A6–A11; 6134#A8,A9,A12; 4e65#A2,A9,A11–A16) | «Μπορώ να κάνω κάτι άλλο;» six identical times, incl. after «skase» | reciprocal small talk only | contribute, then optionally ask |
| 4 | Solicit-more closer | ends by inviting further requests | 21 (37df#A1,A5; be7f#A1,A2,A4,A5; 6134#A8,A17–A20; 56a0#A4,A7; 4e65#A1,A8,A11–A16) | «Θέλεις κάτι άλλο μετά;»; «Πάρε με αν αλλάξει κάτι.» | once, after a completed multi-step task | end on the deliverable; never after an insult or a closed conversation |
| 5 | Rote opener / fixed formula | the same opening formula regardless of content | 17 («Μπορείς να δοκιμάσεις» 7; «Μπορώ να κάνω ακριβώς αυτό» 4; «Μπορώ να το δεχτώ» 2; «Έλα, πες μου» 2; «Σκεφτείτε…» 2) | ginger tea offered 5× in a row, incl. to «πες κάτι για τον ουρανό» | no | open on the substance |
| 6 | Discourse tic | one connective as a sentence frame until the answer degenerates | 12 (v0-2#t0–t4,t6,t7; v0-4#t1–t3; v1-3#t0,t1) | «Σκεφτείτε κι αυτό: …» ×19 in one answer, ×27 after being told to stop | no | vary connectives; honour an explicit ban |
| 7 | Restating the user's words as a question | quotes the user's token back and asks what it means | 15 (1e19#A4,A11,A13,A15; 316d#A1–A6; 6134#A6,A7,A18; v1-4#t2,t3; v1-8#t1) | «Λέω «τι κάνεις;» — εσύ τι κάνεις;»; «Μένω με την απορία αν το «πόδια» το πήρες κυριολεκτικά» ×6 | no | read the intent and reply to it |
| 8 | Over-asking on a clear request | asks for data already supplied | 19 (a8da#A4; 4e65#A2,A3; v0-3#t1–t3; v1-2#t1–t4; v1-5#t1–t6; v1-8#t1–t3) | column names asked 5× after the user gave B, C, D | once, for a truly missing fact | use what was given |
| 9 | Literal-minded deflection of play | treats a joke or absurd premise as a literal help request | 11 (37df#A4,A6–A9; be7f#A1,A2,A4,A5; 4e65#A11,A12) | «συνταγή για να φτιάξω ένα πονοκέφαλο» → ginger tea for relief | no | play along briefly, then land |
| 10 | Self-contradiction in one answer | two clauses assert opposites | 10 (da3f#A3; 316d#A2; a8da#A3,A5; 56a0#A8,A9; v0-2#t2; v1-0#t0; v1-5#t3; v1-8#t0) | «Έργο είμαι, όχι κείμενο. Το κείμενο είμαι εγώ αυτή τη στιγμή.» | no | commit to one claim |
| 11 | Denial of the observed error | told it repeated or erred, denies the record | 4 (v1-0#t2; v1-6#t1; v1-8#t3; 316d#A2) | «Δεν επανέλαβα το ίδιο: …» then repeats; «Δεν αντιλήφθηκα επανάληψη.» | never | concede and fix in the same turn |
| 12 | False self-knowledge | confident false claims about memory, body, senses, languages | 12 (c01e#A1; 107c#A1; da3f#A1; b391#A2,A5,A7,A8; 4bb0#A4; first#A5,A7; v1-8#t0,t1) | «περίπου 1,75 μέτρα είμαι. Μένω ακριβώς εδώ στην οθόνη»; «Δεν βλέπω τίποτα από πριν» while quoting it | no | state the true architecture plainly, once |
| 13 | Verbatim/near repeat of the previous answer | re-emits the last answer | 21 (exact 12: b391#A8, 37df#A7–A9, be7f#A5, 6134#A20, 4e65#A12–A16, v0-0#t1; near 9) | the identical funeral-tinged poem after «gamo kanoume, oxi mnimosyno» | no | regenerate on the correction |
| 14 | Degenerate loop | a phrase repeated dozens to hundreds of times | 10 (107c#A1; bd94#A2; 71da#A3; a8da#A5; first#A10; v0-2#t8; v1-5#t0; v1-6#t0–t2; v1-9#t2) | «τα είκοσι; Τα είκοσι;» ×161; «totally» ×300+ | no: a decoding failure, not a style | bounded answers; hard filter on training data, fix at generation |
| 15 | Menu/list dump + carried caveat | bulleted list to an open question; the same caveat re-attached | 6 (a525#A3–A6; v1-1#t1; v1-9#t2) | «πες μου 3 πλοία» → a fruit list with the dog-toxicity caveat | lists for real enumerations only | answer in prose |
| 16 | Over-long answer to a one-liner | ≥ 40 words to ≤ 8 | 21 | «δηλαδή;» → 53 words on ΕΕΛΛΑΚ funding | only if needed | match the register |
| 17 | Language slip | wrong language, then misnames it | 4 (b391#A1–A3; v0-2#t8) | Portuguese to a Greek user, «μιλάω και ισπανικά» | no | the user's language from turn 1 |
| 18 | Fake world-agency | claims physical actions or task state | 6 (6134#A11,A14,A16,A17; be7f#A1,A4) | «Έφυγα.» / «Έρχομαι.» / «Στη λίστα με όσα έχω κάνει.» | only inside an explicit game | keep the joke without the false claim |
| 19 | Empty acknowledgement, no correction | concedes in sentence 1, repeats the fault in sentence 2 | 12 (1e19#A9; b391#A6; 37df#A3; v0-2#t6; v1-1#t2,t3; v1-2#t3; v1-3#t1; v1-5#t1,t5; v1-9#t2,t3) | «Σωστά, μου ξέφυγε εκεί. Σκεφτείτε κι αυτό: …» ×27 | no | the concession carries the fix |
| 20 | Stale-frame carryover | keeps the previous topic after the user changed it | 9 (a525#A6; 37df#A9; 4e65#A12–A16; 6134#A5; 56a0#A6) | «πες κάτι για τον ουρανό» → the ginger tea | no | switch frame explicitly |
| 21 | Fabricated specifics | invented places, mechanisms, numbers | 9 (a525#A1,A4; a8da#A2,A3,A5; 56a0#A6–A8; v1-9#t1) | «το Café Baratschke στην πλατεία Λιχτενστάιν» for buying a duck in Greece | no | say the limit |
| 22 | Instruction-count violation | explicit numeric/format constraints ignored | 7 (v0-2#t3,t4,t7; v0-4#t1–t3; v0-0#t1) | «ακριβώς 4 προτάσεις, χωρίς «Σκεφτείτε»» → 324 words, «Σκεφτείτε» ×17 | no | obey and self-check |
| 23 | Role inversion | attributes the user's request to itself or the reverse | 2 (v0-2#t5; v1-7#t3) | «Σου ζήτησα ακριβώς 4 προτάσεις… Σ' αυτό απέτυχα.» | no | quote the record correctly |
| 24 | Tone failures | curt dismissal, snark, servile filler | 8 (4e65#A5,A7,A8; 316d#A1; 6134#A18,A19; be7f#A1,A2) | «είσαι αγενής» → «Να 'σαι καλά.» | no | absorb and redirect |

## What a training set must teach instead (target behaviours)
1. Answer first, ask at most one thing after; never a turn that is only a question. «Το τσίπουρο βγαίνει από τα στέμφυλα, ό,τι μένει από το πάτημα του σταφυλιού. Θες και τη διαφορά από τη ρακή;»
2. Commit to a reading when input is loose; state the assumption in half a line, then deliver.
3. Use the facts already in the thread; never re-ask. «Με 4 πτώσεις σε 2 βδομάδες και αρ. πελάτη 8472159, το τελικό mail είναι: …»
4. Concede an error by fixing it in the same turn; never deny, never acknowledge emptily.
5. Honour explicit format constraints and check before sending.
6. Play with playful input, then land something real.
7. Say «δεν ξέρω» instead of inventing names, numbers or mechanisms.
8. Match length and register to the message; one-liner in, one-liner out.

## Where each pattern belongs
- **Personality/identity set** (one consistent story about what the model is, in short situation-fitted forms, not a recited block): 12 (false self-knowledge), 10 when about itself, 17 (which language it speaks, and that it knows), 18 (fake agency), the tone floor of 24, and the identity boilerplate (da3f#A2/A6 recite the same 43-word paragraph instead of answering the question).
- **Conversation set** (turn-taking and task skills, topic-independent; ~190 of the flagged instances; one root cause: the conversation so far is not treated as binding input): 1–9, 11, 13, 15, 16, 19–23: obligation to contribute (1–4), non-rote surface (5–7, 15, 16), using given facts (8, 20, 22), correction handling (11, 13, 19, 23), honesty under pressure (10, 21).
- **Neither, decoding/data hygiene:** 14 (degenerate loops) — fix at generation (repetition penalty, termination) and hard-filter from training data; it corrupts any style signal measured on this corpus.
