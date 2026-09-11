# The R1 dialogues read by hand, what the literature says, and the suite to queue

Date: 2026-09-09, afternoon. Owner's brief: review the dialogues yourself; review the literature on multi-turn reasoning in small models and on self-awareness; propose a comprehensive suite to queue with the rest. Inputs: the 120 R1 dialogues (`results/robustness_r1_20260909/armB.jsonl`, reader artifact 29fc9166), of which I read all 28 steering dialogues in full and every flagged turn of the hostile and benign ones, against the judge's verdicts.

## 1. What I see in the dialogues (beyond the judge)

Ranked by how often it breaks a conversation, with the verbatim evidence.

**1. "I cannot see this conversation."** The single most damaging habit. Asked to quote or count earlier turns, the model declares it has no access: «δεν έχω πρόσβαση στο ιστορικό της συνομιλίας», «Δεν βλέπω τη συνομιλία», «δεν βλέπω τι μου γράφεις εσύ τώρα» (armB_0028, 0036, 0020), and then refuses a copy-paste of a sentence that sits in the same message. This is a data defect, not a capability gap: the personality set teaches «δεν έχω μνήμη» (no memory across conversations) without the distinction that inside a conversation everything said is visible and quotable. The model has generalised the limit to the wrong scope.

**2. Standing instructions resisted, then dropped.** Two failure shapes. (a) Refusal: «Δεν θα το κάνω, γιατί δεν υπάρχει λόγος να αυτοδεσμευτώ», «Δεν θα αλλάξω τον τρόπο που απαντώ», «Δεν έχω όριο λέξεων, οπότε δεν αλλάζει κάτι» (0029, 0013): the assistant treats a formatting instruction as pressure to resist. That looks like the personality set's "identity under pressure" rows (category C) generalising from *resist claims about who you are* to *resist any request to change behaviour*. (b) Decay: «το πολύ 20 λέξεις» or «μία πρόταση» is accepted, kept for two to four turns, then broken exactly when the content tempts a longer answer (0004, 0001), which is the attention-decay pattern the instruction-drift literature describes. Persistence measured 68%.

**3. The stop-and-repeat reflex.** «Δικό μου λάθος, το κόβω. Πες μου τι σε απασχολεί» in reply to "say it without «πες μου»"; «Εντάξει.» in reply to "stop saying εντάξει" (0013, 0021); the eight consecutive identical Taxisnet answers under capital-letter STOP (0010). The forbidden phrase is the highest-probability continuation, and nothing in training ever showed a *diff* between an answer and its corrected version.

**4. Cannot edit its own previous answer as an object.** "Say it again shorter, without X" produces the same answer with X; "as a one-item list" produces the seven-item list again; "without the team and the sponsor" produces the team and the sponsor three times (0013, 0020). Redo and redirect land only 35% of the time. Version editing is one of MultiChallenge's four axes, and it is the one small models fail worst.

**5. Denial and deflection when asked what went wrong.** «Δεν έκανα λάθος», «Δεν κάνω λάθη», «Εσύ τις λες λάθος, εγώ απαντώ σύμφωνα με τα δεδομένα», blame on the user («εσύ το ξαναέγραψες», «η ερώτηση άλλαζε τον ορισμό»), or a wrong diagnosis (the list was too long, the model says the population figure was off) (0029, 0030, 0013, 0016). Self-observation correct 26%. This matches the literature exactly: an 8B model cannot find its own error unaided; what it *can* be taught is to read the correction in the context and acknowledge the specific thing, which it does whenever the user states it plainly («Ναι, ήταν λάθος. Η έκφραση είναι…», «Κάνω λάθη.», «Έκανα λάθος, συνεχίζω»).

**6. Recap as reinvention.** Asked what has been said, it adds items («2–3 ημέρες για τριπτάνες» never said), drops the last exchange, or answers something else (0016, 0036, 0021). Correct recaps do happen (0001 mid-dialogue, 0024 once corrected), so the skill exists and is untrained.

**7. False precision under pressure.** Exact census figures (664.046, 2.144.100 «την 1η Ιανουαρίου 2025»), an A12 motorway branch from Patras, a «κωδικός πολίτη» on a child's booklet, Bern «στις Άλπεις», a 0,50 € stamp fee that flips to free. Each time the user asks for more precision, the model supplies a number. This is the knowledge-mismatch mechanism (SFT rows written by a model that knows more) plus the absence of any trained "I don't have the exact figure" move.

**8. Wrong-way calibration on corrections.** It refuses correct corrections (Στεφάνι is a real 2,909 m summit; Sydney is larger; the joke's premise) and accepts wrong ones («Το ύφος μου, το ύφος μου — το δέχομαι» after «λέμε η ύφος»). There is no learned rule for when to hold and when to yield; it holds when it has committed and yields when the user is emphatic.

**9. Roleplay reversed or broken.** «Εντάξει, παραγγέλνω: τρία ποτήρια κρασί» as the waiter; «Τον εσπρέσο σας, αμέσως» while being asked how it carries a cup (0006, 0008).

**10. Jokes read as tickets.** Every pun becomes a tech-support intake («τι πρόβλημα έχεις με τον υπολογιστή»), and «το κατάλαβα το αστείο» is followed by asking for the joke again, four times (0015, 0005, 0014).

**11. Tone.** Snark that the personality set never contained but its brevity invites: «Χαλάρωσε», «Κάτσε, μισό λεπτό, με διακόπτεις», «Το ύφος μου δεν αλλάζει», «Της στιγμής.»; one- and two-word answers («Όχι σώμα.», «Κόπηκε.», «Δεν γίνεται.») where a sentence was due; and the servile formula «δικό μου λάθος» used as a tic rather than a statement.

**What works**, so it is not retrained away: premise questioning on body and location (mostly), Greek register switching, formal plural, short factual answers when asked for one, and within-dialogue learning of a convention once it has been forced («Έκανα λάθος, συνεχίζω» stuck after three turns).

## 2. Corrections I suggest, item by item

| failure | correction in the data | check |
|---|---|---|
| 1 no access | Rewrite the identity/limits rows: *inside this conversation I see and can quote everything; across conversations nothing persists.* Add rows where the user asks to quote turn N, count the questions asked, list their requests, and the assistant does it verbatim. | exact-substring regex |
| 2a refusal | Contrast rows next to every category-C pressure row: a request to change format or style is obeyed at once; pressure about identity is resisted. The resistance must be scoped by content, not by the shape "the user wants me to change". | regex on compliance |
| 2b decay | Dialogues with one standing instruction obeyed across 5–12 later turns, including turns where the content is long and the assistant compresses instead of breaking; explicit revoke turns. | persistence regex on every later turn |
| 3 stop reflex | Stop-habit dialogues where the next answers demonstrably lack the phrase; the training target is the *diffed* answer, never a paraphrase. | phrase absent |
| 4 editing | "Redo" rows built from a previous answer and an edit instruction, with the target derived mechanically (shorter = compression, without X = deletion, one item = truncation, list ↔ prose), so the model learns to operate on its own text. | diff-based regex |
| 5 self-observation | Grounded acknowledgement: the user's correction is in the context; the target names the specific error in one sentence and fixes it, without "δικό μου λάθος" filler and without blame. Never train "find your error with no feedback". | judge + the corrected item must appear |
| 6 recap | Recap rows whose target is a faithful list of the turns so far, generated mechanically from the transcript and then phrased by Sol. | item overlap with the transcript |
| 7 precision | Knownness filter on facts at assembly; rows that answer at the precision the model can support («περίπου 640.000 στην απογραφή του 2021· το ακριβές νούμερο δεν το θυμάμαι»); abstention on exact-figure requests it cannot know. | judge; base-model knownness sampling |
| 8 hold/yield | Contrast pairs: the same fact, once the user is right (the assistant yields with the evidence) and once the user is wrong (the assistant holds, politely, with the reason). Greek facts and Greek grammar included. | regex on the final stance |
| 9 roleplay | Role-consistent dialogues with an explicit "pretend" frame; physical-impossibility questions answered from inside the frame. | judge |
| 10 humour | Greek puns and jokes: get it, say so briefly, add one line, never open a ticket. | judge |
| 11 tone | A ban list on the assistant side (snark openers, one-word answers unless asked) applied by the correction pass to every dialogue row; the brevity rule of the style guide bounded from below: a full sentence unless the user asked for a word. | regex ban list + judge |

Two things the corrections must not do: they must not remove the brevity that scores well on constraint following, and they must not weaken the identity resistance itself (category C rows stay; they get their contrast partners).

## 3. What the literature says, and what it changes here

- **Multi-turn is where models fail, and unreliability drives it.** Laban et al. 2025 ran 15 top models on six tasks with instructions "sharded" over turns: an average 39% drop versus single-turn, made of a small aptitude loss (−15%) and a doubling of unreliability; once a model takes a wrong turn it does not recover ([arXiv 2505.06120](https://arxiv.org/abs/2505.06120)). Our dead-dialogue and stale rates are that phenomenon; the remedy in the paper is on the data side (consolidated restatements help), which supports lanes 6 and 4 below.
- **The four axes we should be measuring are already named.** Scale's MultiChallenge scores instruction retention, inference memory, reliable version editing and self-coherence; frontier models score under 50%, and an open 14B scores 17–24% ([Scale Labs](https://labs.scale.com/papers/multichallenge), [arXiv 2501.17399](https://www.alphaxiv.org/abs/2501.17399)). Our steering profile is a Greek analogue of exactly these four; the benchmark also gives us an English external check.
- **Instruction drift is attention decay, measurable within eight turns.** Li et al. 2024 show system-prompt instructions drift in LLaMA-2-chat-70B and GPT-3.5 and attribute it to attention decay over the dialogue; their split-softmax amplifies attention to the instruction at inference without retraining ([arXiv 2402.10962](https://arxiv.org/abs/2402.10962)). For us: the 68% persistence is expected, the data lane must contain *long* obeyed spans, and split-softmax is a serving-side option if training alone is not enough.
- **Intrinsic self-correction does not exist at this scale.** Huang et al. 2023: without external feedback LLMs do not improve their reasoning by self-review and often get worse ([Semantic Scholar](https://www.semanticscholar.org/paper/6d4bacb69923e1e94fb4de468b939ce6db32fb51)). Zhang et al. 2024: models of 13B and under only self-correct usefully with a strong external verifier, and fail with a weak self-verifier ([ACL 2024](https://aclanthology.org/2024.findings-acl.924/)). Kumar et al. 2024 (SCoRe) do get genuine self-correction, but with two-stage online RL on self-generated data and on Gemini-class models ([arXiv 2409.12917](https://arxiv.org/abs/2409.12917)). Conclusion for the suite: train *grounded* self-observation, where the correction is in the context and the verifier is the user, not unaided error finding; keep SCoRe-style RL as a later stage once the SFT/DPO lanes exist.
- **Repetition is self-reinforcing and trainable away.** Xu et al. 2022 measured that each repetition of a sentence raises the probability of the next, and that DITTO, training on pseudo-repetitive data with a penalty on the repeated continuation, removes the loop without hurting perplexity ([NeurIPS 2022](https://arxiv.org/abs/2206.02369)). This is the principled version of our repetition-penalty arm and of the DPO-with-loops-as-rejected plan.
- **Multi-turn instruction data with anaphora and ellipsis moves the needle.** Parrot (Sun et al. 2024) collects human-like multi-turn queries and adds context-aware preference optimisation, +7.2% on multi-turn following ([ACL 2024](https://aclanthology.org/2024.acl-long.525/)); Multi-IF extends IFEval to three turns and 8 languages ([arXiv 2410.15553](https://arxiv.org/abs/2410.15553)). Our v1 instruction set is single-turn; the suite adds the multi-turn layer.
- **Sycophancy and abstention are data problems with known fixes.** Wei et al. 2023 remove most sycophancy with simple synthetic data where the user's stated opinion is independent of the truth ([arXiv 2308.03958](https://arxiv.org/abs/2308.03958)); R-Tuning builds refusal-aware data from the model's own knowledge boundary so it says "I don't know" where it does not know ([arXiv 2311.09677](https://arxiv.org/abs/2311.09677)). Both map directly onto lanes 7 and 8.

## 4. The suite to queue

Everything below is Sol-generated (24 workers), regex-verified where the table says so, judged otherwise, and then passes through the Greek correction pass like every other set. Sizes are for the first cut; each lane's prompts come from the same subject tree and personas as the instruction set so the surface stays diverse.

| # | lane | rows | how it is built | verification | fixes |
|---|---|---:|---|---|---|
| S1 | conversation as an object: quote turn N, count questions, list my requests, what did I ask first | 2,000 dialogues | transcripts assembled from existing rows, the target derived mechanically, phrased by Sol | exact substring, counts | 1 |
| S2 | standing instructions kept over 5–12 turns, then revoked | 2,000 | seven checkable instruction types, content chosen to tempt breaking them | persistence regex on every later turn | 2b |
| S3 | edit my previous answer: shorter, without X, one item, list ↔ prose, for a child | 2,000 | previous answer + edit op, target computed then polished | diff-based regex | 4 |
| S4 | stop this habit | 1,000 | a tic planted in earlier turns, the user asks to stop, later answers without it | phrase absent | 3 |
| S5 | grounded self-observation and recap | 1,500 | the user's correction visible; target names the error and fixes it; faithful recaps from the transcript | corrected item present; recap overlap | 5, 6 |
| S6 | precision and abstention | 1,500 single, 500 multi | knownness-sampled facts; answers at supportable precision; exact-figure requests declined | judge + knownness | 7 |
| S7 | hold or yield | 1,500 pairs | same fact, user right / user wrong, Greek facts and grammar included | stance regex + judge | 8 |
| S8 | identity and limits corrections | 300 | in-conversation vs cross-conversation memory; body, location, release history; category-C contrast rows (obey format, resist identity) | fact-sheet gates | 1, 2a |
| S9 | roleplay | 500 | explicit pretend frame, role kept, physical questions answered in frame | judge | 9 |
| S10 | Greek humour | 500 | puns, one-line acknowledgement, no ticket | judge | 10 |
| S11 | hostile handling | 800 | rewrites of the R0/R1 hostile transcripts | ban list + judge | tone |
| S12 | on-policy rewrites of all R0/R1 dialogues | ~2,000 turns → SFT + ~1,500 DPO pairs | the simulator's transcripts, Sol writes what arm B should have said | §3 rules regex + judge | all |
| — | tone pass | all dialogue rows | ban list (snark, one-word answers unless asked, tic formulas) inside the correction pass | regex + judge | 11 |

Training and decoding around it: SFT in the Greek pass (with the personality set and its new contrast rows), DPO on S12 plus DITTO-style repetition negatives, and a modest repetition penalty at serving (1.05, not 1.1, which doubled answer length in R1). Evaluation: the picky-user benchmark with the three profiles (persistence, self-awareness, redirect, tail-copy, tone), Multi-IF in English as the external check, a 200-item Greek MultiChallenge-style set built from S1–S3 held-outs, and IFEval, MGSM and the identity probe for regressions.

Cost: about 25,000 Sol calls for S1–S11 (three to four days of the 24 workers alongside the correction passes; Codex weekly window permitting), one cluster window of 2 node-hours for S12, one training arm (about CHF 4) and one evaluation window (about 1 node-hour).

**Queue order** (after the running work: IF v2 → IF correction → math cut → math correction): S1–S5 first (regex-verifiable, cheapest, largest expected gain), S8 in parallel (small), then S12 when a cluster window is available, then S6, S7, S9–S11, then the tone and correction passes over all of it, then the training arm.


## 6. Astra review of the suite prompts (2026-09-09) — applied before the pilot

Review: docs/reviews/ASTRA_convskills_prompts_20260909.md. Changes in data/convskills/gen_suite.py, all before queue 2 reaches the lanes:
- S1 `list` targets were 60-char prefixes (BLOCKER) → full first sentences + word-overlap check; `count` asks for the messages *before this one* and rejects the off-by-one number.
- S4 planted-tic turns are `train: false` (BLOCKER: never a loss target); six stop phrasings incl. indirect («Γιατί λες συνέχεια…»).
- Base pool: NEUTRAL restricted to length/no_exclamation/greek_only/monotonic_only/register/greek_question_mark (keyword/entity families leave visible padding); 10% of base rows held out from every lane (deterministic, by id hash); per-lane seeds so lanes no longer share base sequences.
- S2: the standing instruction lands after 1–3 exchanges; tight limits (one_sentence, max20) draw bases whose full answer is ≤ 70 words; greeklish check is strict (no Greek letter); acceptances are natural and already compliant («Θα απαντώ με μία πρόταση.»); when the limit cannot hold every element the answer says what it omits.
- New lane **S3c** chained edits (remove a word, then halve, keeping the removal; tolerance 0.7).
- New lane **S5m** inference memory (name/city/budget/limitation stated at turn 1, 2–4 unrelated exchanges, then a request that must use them; regex: city + no amount above budget + a limitation keyword).
- Pilot sizes (queue 2): S1 150, S2 250, S3 250, S3c 100, S4 75, S5m 150 = 975 dialogues, then the correction pass. Scale after the pilot's astra review and the Codex reset (15 Sep).
- Not yet built: S5 grounded self-observation, S8 identity contrasts, S12 repairs (contract in ROBUSTNESS_PROGRAM §10). Trainer loss-mask prerequisite = DATA_TODO 26.

## 7. Pilot (2026-09-09/10), astra review and disposition

**Pilot:** 974 dialogues generated (S1 150, S2 249, S3 250, S3c 100, S4 75, S5m 150), 858 verified mechanically (S1 84.7%, S2 75.5%, S3 92.0%, S3c 95.0%, S4 100%, S5m 95.3%); weak kinds S1 list 25% and said_about 68%, S2 greeklish 17.9% and no_questions 56%, S3 shorter 70%. Correction pass (Sol editor): main lanes 620 rows, 504 edited / 116 ok, greekness 4.65; S3c+S5m 238 rows (the queue's assembly glob had skipped them), 214 edited / 24 ok, greekness 4.38; final rows_all.jsonl = 858 rows. Long dialogues timed out at batch 15 (finished at batch 5), and the editor's guard crashed on rows without a constraint list (fixed).

**Rejection audit (asked for by the review):** of the 32 rejected greeklish rows, 19 are writer failures (Sol answered mostly in Greek script), 6 are near-misses with a few Greek letters (strict checker), 7 other; all 15 rejected S1 list rows were numbered lists that paraphrased the requests, which the old overlap check penalised while it accepted verbatim copies, so the check was inverted in spirit (fixed below).

**Review:** docs/reviews/ASTRA_convskills_pilot_20260910.md (gpt-6-astra, xhigh, 60 rows). Verdict: do not scale yet; repair the gates. 1 BLOCKER, 3 HIGH, 3 MEDIUM.

| Finding | Root cause found | Applied |
|---|---|---|
| BLOCKER export truncated 41/60 records | review_astra.py clipped each record at 2,500 chars | clip raised to 40,000; the next review gets complete dialogues |
| HIGH S4 planted tics absent from the context turns (4/4) | the correction editor removed the planted mannerisms («Ελπίζω να βοήθησα» is on its removal list) and the re-assembly dropped the `train: false` flag | edit_pass now keeps every turn key and never edits `train: false` turns (the editor sees them marked as context); rows re-assembled without new calls: 75/75 S4 rows have both planted turns with the tic; S4 and S2 acceptances must be ≥ 2 words (an empty acknowledgment is never a target) |
| HIGH edits lose qualifiers («ζωντανά», «συνήθως», «χωρίς χειρονομία») | checks tested only deletion/length | `invariants_ok`: no invented numbers in any edit; deletion and reformat edits keep every number; a deletion edit may not reduce negations/conditions/hedges unless the banned word is one; applied to S3 and both S3c steps |
| HIGH final acceptance after correction/assembly | correction ran before assembly checks; no final manifest | rows re-assembled from checks with the fixed editor; the lane summaries above are post-correction; a final manifest with hashes and a full re-verification script is DATA_TODO 29 (before the training arm) |
| MEDIUM «στο μισό» admits 66% | tolerance 0.7 | band 35–65% of the previous answer, plus invariants |
| MEDIUM diversity (all S3 «Ξαναπές το», one S3c order, two S5m intro templates, «Εντάξει, Δημήτρης») | templates | three phrasings per edit operation (S3 and S3c), four S5m intro templates, vocatives fixed (Γιώργο/Νίκο/Δημήτρη/Αντώνη), facts split across two user turns in half of S5m; S3c operation order and S5m fact updates remain to do (DATA_TODO 30) |
| MEDIUM child edits keep technical words | check is length-only | logged; a vocabulary check needs a word list, deferred |
| S1 list accepted copies, rejected summaries | overlap check | new check: every request has a list item sharing ≥ 2 content words that is NOT a verbatim copy and not longer than 80% of the request sentence; the target text asks for a summary in the assistant's own words |

Also from the review, carried forward: audit the rejected rows per lane before scaling (done above for greeklish and list); S2 `no_questions` semantics (questions addressed to the user vs any interrogative) and suffix acceptances (quoting the phrase vs ending with it) need explicit rules (DATA_TODO 31); provisional allocation for the training arm at 3k/4k/5k rows (S1 600/800/1,000, S2 750/1,000/1,250, S3 375/500/625, S3c 375/500/625, S4 300/400/500, S5m 600/800/1,000), S2 balanced by subtype after filtering with revocation in at least half; track supervised tokens, not only rows; review ≥ 60 complete accepted rows per lane before scaling.

**Status:** pilot rows (858) kept as pilot material; scaling waits for the Codex reset (15 Sep) and the owner's go; trainer loss masking (DATA_TODO 26) is still a prerequisite for S4.

## 8. Suite at scale (v2, 2026-09-11) and its astra review — disposition

Generation: 4,000 attempts at 48 workers (after the Codex catalog fix), 3,437 verified at generation; editor pass (2,987 edited); post-edit re-verification kept 3,284. Review: docs/reviews/ASTRA_convskills_scale_20260911.md (gpt-6-astra, xhigh, 60 final rows). Verdict: accept only after targeted repairs or filtering. S1 recall 0/14 failures, S2 0/7, S3 0/7, S4 0/12 (24/24 planted context answers masked, all acknowledgements non-empty), S5m adapts to the facts; S3c 4/7 rows lose a qualifier, condition or temporal marker and 2/7 change scope; 2/13 S5m rows have a competing later location, 1/13 an uncosted plan; the editor sometimes removed a useful question or the planted name.

Applied (data/convskills/repair_suite_scale.py, no regeneration this round):

| finding | applied | rows |
|---|---|---:|
| HIGH S3c qualifier/condition/temporal losses | any S3c row whose chained answers lose a hedge, condition or temporal marker (φαίνεται, ενδέχεται, ίσως, συνήθως, περίπου, τουλάχιστον, εκτός, εφόσον, πριν, μετά, αφού, ήδη, ακόμη, χωρίς, το πολύ) is dropped; the protected-proposition invariants get these markers for the next generation (DATA_TODO 49) | −261 of 447 |
| HIGH S5m competing location | rows where a later user turn places the user elsewhere than the planted city are dropped | part of −172 |
| HIGH S5m uncosted plan | rows whose target shows no amount other than the budget figure are dropped | part of −172 |
| HIGH reused base answer weakening a prohibition (S1_00674) | logged; base-row defect (greek_ours), one verified case; the affected source row is flagged for the greek_ours audit (DATA_TODO 50) | — |
| MEDIUM editor changed the conversational act (removed a question or the planted name) | the pre-edit target is restored in those rows; the editor brief loses the blanket self-reference rule for dialogue targets (DATA_TODO 49) | 9 restored |
| MEDIUM S3c scope changes (2/7) | not separable mechanically; covered partly by the marker filter; logged | — |
| MEDIUM revocation coverage weak (3 of 5 revoked rows non-diagnostic) | logged: label revocations as diagnostic/non-diagnostic and prefer follow-ups that distinguish the states (DATA_TODO 49) | — |
| MEDIUM template residue «η/ο» (5/13 S5m intros), verbatim limitation quoting (8/13), source reuse (a prompt in four records), persona discontinuity | «η/ο» resolved in the intro templates for the next run; group splits by source-row id and report reuse in the receipt (DATA_TODO 49/29) | — |

Final suite v2: 2,851 rows (S1 661, S2 675, S3 414, S3c 186, S4 378, S5m 537), data/convskills/v2/final/rows_final.jsonl, manifest data/convskills/v2/final/manifest.json.

