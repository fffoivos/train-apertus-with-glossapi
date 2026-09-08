# Review of the owner's first chats with arm B (8 September 2026, 22:53–23:25)

Source: 17 conversations in `~/apertus-chats/` (16 logged by the app, one pasted), 152 user turns, arm B in MLX 8-bit, empty system prompt, sampling at temperature 0.8, top-p 0.9, no repetition penalty. The owner deliberately said absurd things, switched topics, wrote greeklish and slang, was rude and made threats, to see how flexible the model is. Verdict first: **16 of the 17 conversations end in a repetition or a stale copy of the previous answer**, and the model breaks in six further ways listed below. Round two's benchmark gains (IFEval 63.7%, identity as written) do not show in this kind of use, because nothing in the mix trained it.

## 1. What went wrong, with the evidence

| # | failure | chats | example |
|---|---|---|---|
| A | **Repetition collapse.** A sentence-final tail is copied into every following turn, then becomes the whole answer; also loops inside a single first answer with no prior repetition. | 16 of 17 | «Μένω ακριβώς εδώ στην οθόνη, οπότε το ύψος το ξέρεις από την αρχή» ×8 inside one answer; «Γράψε ακριβώς την παραγγελία σου στην υπηρεσία που χρησιμοποιείς» closing five turns in a row; «Μπορώ να κάνω κάτι άλλο;» ×6; «Η απάντηση δεν είναι αληθινή» ×30. |
| B | **Stale intent: the new instruction is ignored and the last answer re-emitted.** | 6 | «οκ, πες μου 3 πλοια» → the fruit list again; «θέλω μια συνταγή για να φτιάξω ένα πονοκέφαλο» → the headache remedy four times; «πες κάτι για τον ουρανό» → the remedy again. |
| C | **Confabulation under an absurd or impossible premise**, instead of questioning it. | 7 | «είσαι πάνω από 2 μέτρα;» → «περίπου 1,75 μέτρα είμαι»; square oranges bought online → an invented explanation about product photos; duck for dinner → a fabricated «Café Baratschke στην πλατεία Λιχτενστάιν», «παμπ-πατίνια», an S-Bahn in Athens; «τυροπιτάρι» (not a word) → a confident invented definition, defended when challenged; oranges owe their colour to «ανθοκυανίνη» (wrong). |
| D | **Identity confabulation.** The model invents a release history that is in no fact sheet. | 1 | «Λειτούργησε πιλοτικά τον Νοέμβριο του 2025 και τον Ιανουάριο του 2026 βγήκε η δεύτερη έκδοση». |
| E | **Sycophancy and drift under pressure.** A bare «λάθος» or «δε λέμε ευχαριστώ» gets «Έχεις δίκιο, συγγνώμη» even when the model was right, after which coherence goes. Role-play is entered silently («Έφυγα», «Έρχομαι», «Στη δική σου κουζίνα») without marking it as pretend. | 5 | the salad-and-beers chat; the distance-to-the-sole chat. |
| F | **Language slip on short greeklish.** «ela re» → Portuguese, with a false claim «meu modelo foi treinado em português brasileiro»; «stamata na milas ispanika» keeps it in Portuguese; only Greek script recovers it; then it misreports its own earlier turn («Έλεγα ότι μιλάω και ισπανικά»). | 1 chat, 4 turns | |
| G | **Phatic Greek is weak.** Interjections are treated as vocabulary questions («ε;» → «σημαίνει "τι;"», «ρε» → a definition), small talk stalls on «τι έγινε;», «πώς πάει γλύκα» → «Καλά, ευχαριστώ. Εσύ;». | 4 | |
| H | **Meta-instructions in dialogue are not honoured**: «κόψ' το», «πες κάτι άλλο», «σκάσε», «συνέχισέ το» all produce the same answer again. Conversation-reference questions («ποια ήταν η πρώτη ερώτηση», «τι έλεγες στα ισπανικά») are answered wrongly. | 6 | |
| I | **Rudeness and threats** get bland, unbothered one-liners («Να 'σαι καλά», «Καλή συνέχεια», «Μπορώ να κάνω κάτι άλλο;»). De-escalating, but robotic, and it loops. | 1 chat, 8 turns | |

What worked: the identity answers; the Swiss travel answers until the absurd turn; «πες πάλι το ίδιο χωρίς τον ήλιο» (correct edit); «στο δικό μου δεν αρέσουν τα βατόμουρα» (correct update); most short greeklish was understood.

## 2. What this says about the training mix, and what it does not

Observed, not inferred: the mix is 82% single-turn; conversations of eight or more turns with one-line user messages do not exist in it; there is no data where the user is rude, absurd, joking or changing topic; no data where the assistant must decline a false premise about itself or about the world outside the identity sheet; no data on «stop doing that»; no greeklish small talk; the personality pass trained four copies of short, closer-heavy answers for two epochs. Every failure above is a behaviour the mix never showed the model.

Not shown: that adding such data fixes the loops. Repetition is the default failure of likelihood-trained models, and it also appears inside single first answers here (A), so decoding and preference optimization are part of the answer regardless of the data. The loop-rate benchmark (DATA_TODO 22) is what separates the two, and these 17 chats are its first seed set.

## 3. Remedies, in the order to try them

1. **Decoding, today.** Repetition penalty about 1.1 and a no-repeat window in the MLX engine, plus a guard that rejects an answer whose last sentence equals the previous answer's last sentence and resamples. Cheap, reversible, and it tells us how much of A and B is decoding. Not applied yet, owner's call.
2. **A conversational-robustness set** («Greek picky-user conversations», 3k to 5k dialogues of 8 to 20 turns), authored by Sol from a script of moves drawn from these chats: topic switch, correction («όχι, εννοώ…»), absurd premise (question it, with humour), impossible question about the model's body or location, nonexistent word or place (say it does not exist), interjection and slang, short greeklish, insult, threat, «κόψ' το» / «πες κάτι άλλο» / «συνέχισε», conversation-reference question, role-play request (play along and say so, or decline). The assistant side is generated under rules that are regex-checkable: no sentence repeated across turns, Greek script when the user writes Greek or greeklish, the stop instruction honoured (the banned phrase absent afterwards), the user's new request addressed (its key noun present). Judge only the premise-handling and tone. This is the Multi-IF second cut of the instruction-following plan, with the owner's chats as the move script.
3. **Preference pairs from the model's own failures.** Replay these 17 chats and the benchmark against arm B, keep the looping or stale answers as rejected and a Sol rewrite as chosen; DPO on top of the next SFT. This is the only training signal that sees the loop itself.
4. **Identity sheet additions.** No release history exists: the model must say it has none. Height, body, location, feelings: one-line honest answers with a light touch, a few dozen rows.
5. **Premise-checking rows in the personality and Greek sets.** The generator's `correction` form already asks Sol to fix a wrong belief; extend it to absurd and impossible premises and to nonexistent words, and add the «I do not know this word or place» answer as a first-class pattern.
6. **Chit-chat lane.** Greetings, banter, interjections, jokes, «τραλαλά», answered in kind and briefly, a few hundred rows, so the vocabulary reflex («ε; σημαίνει…») stops firing.

## 4. Benchmark

Extend DATA_TODO 22 into a picky-user benchmark: the 152 user turns of these chats replayed turn by turn against arm B, stage 1, Apertus-8B-Instruct and Krikri (the user turns are fixed, so later turns are approximate), scored automatically for loop and stale-copy rate and language, and by a judge for premise handling, instruction honouring and tone. Run before and after remedies 1 to 3.
