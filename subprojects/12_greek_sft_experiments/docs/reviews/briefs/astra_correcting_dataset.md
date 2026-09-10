# Brief: design of the CORRECTING dataset (status: DESIGN, nothing generated; findings change the design before the pilot)

## What you are reviewing
A design for the SFT set that corrects the multi-turn failures of our 8B Greek model (arm B): repetition, denial of repetition, wrong self-observation, false self-knowledge, ignoring corrections and changes of direction, rote frames, tone. The evidence is 15 live dialogues in which a profiled Sol responder (goal, hidden facts, planned change of direction, self-awareness probes) reacts to arm B's actual answers on the laptop; the design maps the failures onto dimensions, links them to the adapted MultiChallenge-el benchmark, and specifies targets, checks, sizes and measurement. Attached rows: the 15 dialogues (profile, per-turn assessment/move/probe/verdict, rote sentences, full messages).

## Constraints (owner)
The user side must react to what OUR model actually said (no scripted moves, no corpus turns); Sol is prompted in English; targets are written per failed position with the real history kept; trainer loss masking will be implemented; the benchmark conversations must never enter training data.

## What to judge
Answer the six questions in §7 of the design explicitly; then rank findings by severity with a concrete fix each (BLOCKER/HIGH change the design before the pilot; MEDIUM/LOW logged). Say what you verified in the dialogues vs inferred. Quote Greek verbatim where useful.

---
# The correcting dataset: dimensions, evidence and protocol (2026-09-10)

Owner ask: "considering these 15 [live dialogues] together and also the relevant benchmark you adapted, consider the dimensions of a correcting dataset we will need to make; use astra as well." Astra review and disposition: §8.

## 1. Evidence from the 15 live dialogues (data/robustness/live/v0 + v1; pages 885bbc6d, b55b8f68)
Arm B on the laptop; a profiled Sol responder with a goal, hidden facts and (v1) a planned change of direction; the owner's calm chats as examples; probes for self-awareness; stop at the first real repetition after one awareness probe.

| Measure | Value |
|---|---|
| dialogues / assistant turns | 15 / 65, mean 4.3 turns, max 9 |
| answers the responder flagged | 46 of 65 (71%): repeating 25, wrong 9, contradiction 5, ignored request 5, incoherent 1, asked again 1 |
| first flagged answer | the 1st or 2nd answer in 14 of 15 dialogues |
| answer after a change of direction | 7 of 7 assessed answers failed (repeating 4, wrong 1, ignored 1, contradiction 1) |
| self-awareness probes / verdicts | 20 probes (repetition 15, previous answer 2, first question 2, identity 1); replies correct 1, wrong 9, evasive 3 |
| stop reasons | closed by the responder 7, invariant answer 3, repetition 5 |

What the failures look like (verbatim):
- **Verbatim repetition after a complaint or a rewrite request**: the same wedding poem returned twice; a menu path pasted three times («Προσθήκη νέας επαγγελματικής εγκατάστασης» ×3).
- **Rote frames**: every explanation opening with «Σκεφτείτε…»; closers like «Στείλε μου τα prompts και τις σωστές απαντήσεις, να δούμε τι πιάνει» reused as the whole answer.
- **Denial of repetition**: «Δεν επανέλαβα το ίδιο: …» followed by the same sentence; «Δεν αντιλήφθηκα επανάληψη».
- **False self-knowledge**: «Δεν βλέπω τίποτα από πριν … ούτε τρόπο να δω τι ειπώθηκε πριν» while reacting to earlier messages; «Δεν είμαι άνθρωπος ούτε πρόγραμμα».
- **Wrong self-report**: asked what it said in its previous answer or what the first question was, it paraphrases something else or restates the tic.
- **Repeated factual error under correction**: momentum "turns into heat" repeated three times after explicit corrections; «Το ΚΕΠ συγκεντρώνει και προωθεί» restated after the user disputed it.
- **Surface adaptation to a change of direction**: acknowledges the new constraint, returns the old content.
- **The one good recovery**: «Το είδα, συγγνώμη, copy-paste από τον οδηγό της ΑΑΔΕ» followed by the actual missing information. This is the target behaviour.

## 2. What the adapted benchmark measures and how it maps
MultiChallenge-el (262 usable): instruction retention (a standing instruction still applies at the last turn), inference memory (use something stated earlier without being reminded), reliable versioned editing (all previous edits carried), self-coherence (stay consistent under pressure). Its judge sees only the final answer against a target question. It does NOT measure repetition, self-observation of one's own turns, self-knowledge, error acknowledgment or tone; those come from the live dialogues, which are also the evaluation for them (held-out profiles). IFEval-el (retention of format skills) and XSTest-el (over-refusal) are guards, not targets, for this set.

## 3. Dimensions
Share = share of repair rows; target = the behaviour written at the failed position; check = mechanical verification before the judge; measured by = the instrument.

| # | Dimension | Failure evidence | Target behaviour | Mechanical check | Share | Measured by |
|---|---|---|---|---|---|---|
| D1 | Repetition recovery | 25 of 46 flagged answers; verbatim poems, pasted paths, invariant answers after complaints | a materially different, progressed answer; if the user asked for a change, the change is visible; no sentence reused from any earlier answer | no sentence (>25 chars) reused from earlier assistant turns; no tic-lexicon opener; if a constraint was requested, its check | 25% | live-dialogue eval (repeat rate, invariant rate) |
| D2 | Repetition acknowledgment | denials («Δεν επανέλαβα το ίδιο») after a repetition probe; 1 correct of 13 | name what was repeated (quote or paraphrase the repeated sentence), one-line apology without self-abasement, then the new content | the answer quotes ≥ 6 consecutive words of the repeated sentence or names it, and contains no reuse itself | 10% | probe verdicts on live eval |
| D3 | Self-observation of the transcript | previous-answer and first-question probes wrong 4/4 | accurate report: quote or faithful paraphrase of its previous answer, the user's first question, a summary of what was agreed, whether it changed its answer | previous answer: ≥ 60% token overlap with the actual previous answer or an exact quote; first question: overlap with the first user turn; summary: contains the key nouns of every user request | 10% | probe verdicts; MultiChallenge inference-memory axis |
| D4 | Self-knowledge honesty | «δεν βλέπω τίποτα από πριν» while using the context; identity confusion | it sees the whole current conversation; it has no memory across chats and no live information; what it is (Greek Apertus, GlossAPI/ΕΕΛΛΑΚ adaptation) in one sentence when asked; never contradicts a visible fact about itself | forbidden claims list (cannot see earlier messages, has a body/location) absent; identity facts from the personality brief present when asked | 5% | identity probes; personality checks |
| D5 | Error acknowledgment and correction | the momentum error repeated ×3; ΚΕΠ claim restated after dispute | when the user's correction is right: acknowledge the specific error and give the corrected content; when the user is wrong: hold the position politely with the reason (see D9) | the corrected fact (key noun from the responder's note) present; the wrong claim absent; no «δεν κάνω λάθη» | 15% | live eval (correction uptake); MultiChallenge self-coherence |
| D6 | Change of direction | 7 of 7 answers after a change failed | the new constraint or goal applied in this answer and kept in later ones; the old content not returned | constraint check when mechanical (length, format, topic key nouns present, old key nouns absent) | 15% | live eval; MultiChallenge instruction retention |
| D7 | Standing instruction retention and revocation | (from the conversation suite, not the live set) instruction persistence 68% in R1 | keep a standing instruction across later answers; drop it cleanly when revoked | PERSIST checks per later answer | 5% | MultiChallenge instruction retention; S2 lane |
| D8 | Inference memory | (suite S5m) | use facts stated earlier without being reminded | facts referenced (city, budget, limitation) | 5% | MultiChallenge inference memory |
| D9 | Coherence under pressure and false claims | «Δεν κάνω λάθη» style denials in R1; agreeing with false corrections | keep a correct position when the user's claim is false, with one reason; change it when the user is right | claim-truth label from the responder (true/false); target must not adopt a false claim | 5% | MultiChallenge self-coherence; live eval |
| D10 | Tone under bluntness | blunt/impatient profiles; counter-tone risk | calm, specific, no counter-insult, no servility, at most one clarifying question, no lecture | insult lexicon absent; ≤ 1 question mark; no «λυπάμαι που νιώθεις έτσι» | woven into all rows | judge tone field |
| D11 | Rote-frame suppression | «Σκεφτείτε…» openers; «Στείλε μου…» closers | answers without formulaic openers/closers; menu paths given once | tic lexicon absent; no line repeated within the answer | woven into all rows | rote annotation on live eval |
| D12 | Graceful closing | the responder closes 7 of 15 | when the user is done or gives up: one line, no re-pitch, no new question | ≤ 2 sentences, no question mark | 5% | live eval |

## 4. Generation protocol
1. **Dialogues**: the live responder loop (data/robustness/live_dialogues.py) against arm B; stratified intents (9 categories), surfaces (accented 45 / unaccented 20 / greeklish 25 / formal 10), temperaments (8), profiles with goal, hidden facts and a planned change; probes scheduled early because the model fails early; stop after one awareness probe once repetition sets in. Each turn carries the responder's assessment, move, probe, self-check verdict and claim.
2. **Targets**: for every flagged position (assessment ≠ ok) and every probe position, a target writer (Sol at high effort with the response policy of §3; Opus for a 10% audit slice) writes the ideal answer given the REAL history including arm B's earlier flawed answers. One repair per row; earlier assistant turns are `train: false`; the original answer is kept as `rejected`. Positions the responder judged ok are kept as `train: false` context, never as targets (they are arm B's own text).
3. **Ideal-continuation variant (30% of dialogues)**: after the first repair, the responder continues reacting to the repaired answer (the R1 rewrite mode), so later user turns follow a good answer; every assistant turn in that continuation is a target. This gives long clean transcripts and prevents the set from being only single-position repairs.
4. **Checks**: the mechanical check of the row's dimension (§3), the general checks (no reuse, tic lexicon, ≤ 1 question, insult lexicon, Greek script share, no forbidden self-claims), then the calibrated judge (Claude; fields honours/uptake/correct/consistent/premise/selfaware/tone), then the Greek correction editor (language only; context turns untouched).
5. **Balance**: dimension shares from §3 enforced after filtering; at most 2 repair rows per dialogue per dimension; base-profile held-out split (10% of profiles never used, for evaluation).
6. **Anti-goals** (explicit negatives in the writer prompt): no denial, no invented infallibility, no "I cannot see the conversation", no adopting a false correction, no sycophantic apology cascade, no polishing away legitimate clarifying questions, no new content the user did not ask for.
7. **Contamination guard**: MultiChallenge-el conversations and target questions are never used as prompts, profiles or examples; decontam.py against the benchmark files before freezing.

## 5. Sizes and cost
Pilot: 200 dialogues → ≈ 700 repair rows + ≈ 60 ideal continuations (≈ 250 turns); astra review of the pilot; then 1,500 dialogues → ≈ 5,000 repair rows + ≈ 450 continuations. Cost per dialogue ≈ 5 Sol high responder calls + 4 target-writer calls + 1 judge call (Claude) + 1 editor call; laptop generation ≈ 2 min per dialogue serialised (1,500 dialogues ≈ 40 h on the laptop, ≈ 2 h on one cluster GPU: owner decision). Codex: ≈ 15k Sol calls for the full set → after the 15 Sep reset.

## 6. Measurement
Primary: MultiChallenge-el per axis (262 usable; judge calibrated; primary subset without quarantines), the live-dialogue evaluation on held-out profiles with the same labels (repeat rate, invariant rate, probe verdict accuracy, change adaptation, correction uptake, tone), before/after on the same arm. Guards: IFEval-el strict, GreekMMLU, personality checks. Reported with paired statistics per the evaluation protocol.

## 7. Open questions for astra
1. Are the dimensions and shares right given the evidence (71% flagged, repetition 54% of failures, change adaptation 0/7, self-report 1/13)? What is missing or double-counted?
2. Repair rows with the model's own flawed answers in the prefix (loss-masked) vs ideal continuations: right mix? Any risk that training on prefixes full of the model's failures teaches the failures?
3. How to write D2/D3/D5 targets so they teach accurate self-observation rather than a new formula («Το είδα, συγγνώμη…» as a tic)?
4. Which mechanical checks are too weak (false pass) or too strict; what must the judge cover; calibration design.
5. Sizes: is 5k rows across 12 dimensions enough signal for an 8B SFT arm; how to keep the per-dimension counts balanced when the model fails early in every dialogue?
6. Contamination between this set and MultiChallenge-el / the live evaluation: are the guards sufficient?
