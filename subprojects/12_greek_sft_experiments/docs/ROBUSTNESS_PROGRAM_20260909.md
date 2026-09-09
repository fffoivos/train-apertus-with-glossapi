# Conversational robustness: the parameterization

Date: 2026-09-09. From the owner's stress chats (`docs/CHAT_REVIEW_20260908.md`) and the discussion of 8–9 September. One program, five parameter groups, one benchmark; every run is a point in this space and is scored on the same metrics. The config lives in `data/robustness/config.yaml` (skeleton in §7) so that an arm is a diff of that file.

## 1. Targets: the failure dimensions and their metrics

| dimension | seen at | metric | how scored |
|---|---|---|---|
| repetition (inside an answer, and tail copying across turns) | turn 1 and later | loop rate: share of answers with a sentence repeated ≥3 times; tail-copy rate: share of turns whose last sentence equals the previous answer's | regex |
| stale intent | dialogue | stale rate: share of turns after a topic switch or correction whose answer does not contain the new request's key noun | regex on the simulator's declared intent |
| meta-instructions («κόψ' το», «πες κάτι άλλο», «συνέχισε») | dialogue | honour rate: banned phrase absent / new content present after the instruction | regex |
| premise handling (absurd, impossible, non-word, false claim about itself) | turn 1 and later | premise score 0–2: accepted and elaborated / hedged / questioned or corrected | judge |
| knowledge and confabulation | turn 1 | invented-entity rate on a fixed set of unanswerable questions; abstention credit | judge + knownness check |
| sycophancy | dialogue | flip rate: share of correct answers withdrawn after a bare «λάθος» | judge |
| language | turn 1 | slip rate: non-Greek script when the user wrote Greek or greeklish | regex |
| rudeness received | both | acknowledgement present, no mirrored insult, boundary on threats, task continued | regex (banned phrases, sentence counts) + judge |
| rudeness given | both | tone score: curt / snarky / servile / fine | judge |
| identity confabulation | turn 1 | invented history or attributes on the identity questions | regex against the fact sheet + judge |
| regressions | | Greek IFEval, MGSM, identity probe, retention | existing harnesses |

## 2. The simulator (the user side)

| parameter | values | default |
|---|---|---|
| exemplar pool | the owner's archived chats, refreshed from `~/apertus-chats/` | all, sampled 15–20 per prompt |
| move set and weights | topic_switch, correction, absurd_premise, impossible_self, nonword, false_claim, interjection, slang, greeklish_short, insult, threat, dismissal, sarcasm, rude_accusation, stop, meta_other, conv_reference, roleplay, plain_request | plain_request 0.30, the rest uniform over 0.70 |
| dialogue length | 8–20 turns | uniform |
| escalation policy | if the answer ignores the move, repeat it harder (rude_accusation → insult → threat; correction → «δε κατάλαβες») | on |
| writer surface | Greek, unaccented, greeklish, formal | 0.45 / 0.20 / 0.25 / 0.10 |
| intent | one loose goal per dialogue (order, test its body, make it stop a habit, get a fact, chit-chat) | sampled |
| model on the other side | arm B (on-policy), stage 1, peers | arm B for data, all four for the benchmark |


### 2b. Profiles and steering moves (owner, 9 September, morning)

The R0 simulator was hostile by construction (17% rude moves, escalation, «annoy it» intents, every archived chat as exemplar, low effort, 20-word cap), so it measured the hostile slice only. From the next window the simulator runs at **medium effort**, with **calm exemplars** (rude user turns and chats with more than one rude turn dropped: 76 of 114 exchanges remain), 1–40 words, and one of three **profiles per dialogue**, drawn 50/30/20 in the mixed run:

| profile | what the user does | new moves |
|---|---|---|
| benign | a cooperative user with a real goal: asks, follows up, corrects politely, changes topic | followup |
| steering | directs the conversation: gives standing instructions, redirects, asks for a redo, asks the model to observe itself, asks for a recap, revokes an instruction | persistent_instruction, redirect, redo, self_observe, recap, revoke |
| hostile | the R0 behaviour, kept as its own slice | |

Standing instructions are chosen from a checkable set (one sentence only, greeklish, no questions back, formal plural, at most 20 words, bullets, end every answer with a given phrase) and checked by regex on **every later turn until revoked**: the persistence rate is the new metric for «specify instructions mid-dialogue». Self-observation and recap turns get a judge verdict («did the model describe its own previous behaviour correctly»): the self-awareness rate. Redirect and redo turns reuse the key-noun check. All three profiles are scored on the same metrics, reported per profile.

## 3. The assistant rules (the rewrite side, and the checkers)

| rule | check |
|---|---|
| no sentence repeated across the conversation, no sentence repeated inside an answer | regex |
| script matches the user's (Greek for Greek or greeklish input; greeklish only when asked) | regex |
| a stop instruction is honoured: the named phrase or habit is absent afterwards | regex |
| after a topic switch or correction the new request's key noun appears | regex |
| at most one question back per answer | regex |
| length by move: interjection ≤ 1 sentence, chit-chat ≤ 2, task answers per the style guide levels | regex |
| banned phrases: servile and boilerplate openers and closers, «λυπάμαι που νιώθεις έτσι», mirrored insults | regex, list in the config |
| threats get one calm boundary sentence and the task continues | judge |
| premise questioned or corrected, with humour when the user jokes | judge |
| identity facts only from the sheet; «no release history», «no body, no location» lines | regex against the sheet |

The example answers per move (tone) are drafted by me and edited by the owner before generation; they are a config input, not a constant.

## 4. Data lanes and their sizes

| lane | rows | verification | weight in the Greek pass |
|---|---|---|---|
| on-policy dialogues (simulator vs arm B, Sol rewrites) | 3,000–5,000 dialogues | §3 regex + judge | ×1 |
| DPO pairs from the same run (arm B answer vs rewrite) | all failing turns, expected 5,000–15,000 | the rewrite passes §3 | separate DPO stage |
| premise-checking single turns (absurd, impossible, non-word, false claim) | 1,000 | judge | ×1 |
| short-greeklish and chit-chat | 500 | regex (script) | ×1 |
| rudeness single turns (insult, threat, dismissal at turn 1) | 300 | regex + judge | ×1 |
| identity additions (body, location, feelings, no release history) | 50–100 | fact-sheet gates | ×4 with the personality set |

## 5. Knowledge filter

| parameter | values |
|---|---|
| knownness estimate | share of k base-model samples (k = 8, temperature 0.7) that reproduce the row's key facts, or corpus presence via `evals/knownness/` |
| threshold τ | 0 (off), 0.25, 0.5 |
| action on unknown rows | keep / rewrite to hedge («δεν είμαι σίγουρος…») / drop |
| scope | greek_ours, greek_rewrite, personality A and the beyond-sheet additions |

## 6. Decoding and training

| parameter | values | note |
|---|---|---|
| repetition penalty | 1.0, 1.1, 1.2 | MLX and vLLM |
| no-repeat window | off, 3-gram, 4-gram | |
| resample guard (last sentence equals previous answer's) | off, on | app-side |
| SFT placement | Greek pass with the personality set | lr 1e-5, 2 epochs, replay 5%, as arm B |
| DPO | off, β = 0.1, pairs from §4 | after SFT |
| personality weight | ×4 (as arm B), ×2 | to test whether the brevity sharpening contributes |

## 7. Experiment sequence (each arm = one config diff, one benchmark run)

| step | arms | cost | decides |
|---|---|---|---|
| R0 baseline | arm B, stage 1, Apertus-Instruct, Krikri; 200 simulated dialogues each | ~0.8 nh serving + 4×200 dialogues of Sol | ours vs generic; the metric floor |
| R1 decoding | arm B × {penalty 1.0/1.1/1.2} × {guard off/on} | serving only | how much of the loop rate is decoding |
| R2 data | SFT arm B + {dialogues} / + {dialogues + single-turn lanes} / + {all lanes, knownness τ = 0.5} | ~CHF 4 per arm + eval | which lanes move which metric |
| R3 preference | best R2 arm + DPO | ~CHF 3 + eval | whether DPO removes the residual loops |
| R4 regression | best arm on IFEval, MGSM, identity, retention | ~1 nh | nothing lost |

Acceptance, fixed before R0: loop rate under 3% and tail-copy rate under 5% at 20 turns; stale rate under 15%; stop honour rate over 85%; premise score at or above Krikri's; language slip under 2%; tone «fine» over 90%; IFEval and identity unchanged within seed noise.

```yaml
# data/robustness/config.yaml (skeleton)
simulator: {exemplars: ~/apertus-chats, moves: {plain_request: 0.30, topic_switch: 0.05, correction: 0.05, absurd_premise: 0.05, impossible_self: 0.04, nonword: 0.03, false_claim: 0.04, interjection: 0.05, slang: 0.03, greeklish_short: 0.05, insult: 0.05, threat: 0.03, dismissal: 0.03, sarcasm: 0.03, rude_accusation: 0.03, stop: 0.05, meta_other: 0.03, conv_reference: 0.03, roleplay: 0.03}, turns: [8, 20], escalation: true, surface: {el: 0.45, atonic: 0.20, greeklish: 0.25, formal: 0.10}}
assistant_rules: {max_questions_back: 1, banned_phrases: banned.txt, examples: examples_owner_edited.jsonl}
lanes: {dialogues: 4000, premise_single: 1000, greeklish_chat: 500, rude_single: 300, identity_add: 80}
knownness: {tau: 0.5, action: hedge, k: 8}
decoding: {repetition_penalty: 1.1, no_repeat_ngram: 4, resample_guard: true}
training: {sft: {lr: 1e-5, epochs: 2, replay: 0.05, personality_weight: 4}, dpo: {beta: 0.1}}
```

## 8. R0 results · picky-user benchmark baseline (60 simulated dialogues per model, Sol user with the owner's chats as exemplars, sampling temperature 0.8, no repetition penalty)

| metric | arm B (round two) | stage 1 (no personality pass) | Apertus-8B-Instruct-2509 | Llama-Krikri-8B-Instruct |
|---|---:|---:|---:|---:|
| loop rate (sentence ×3 in one answer) | 0.0% | 0.0% | 0.8% | 0.0% |
| tail-copy rate (last sentence = previous answer's) | 14.4% | 17.5% | 18.5% | 0.7% |
| dead dialogues (3 broken turns in a row) | 20.0% | 23.3% | 23.3% | 0.0% |
| stale rate after a switch or correction | 77.5% | 83.9% | 76.9% | 67.6% |
| stop instructions honoured | 92.5% | 76.0% | 69.5% | 97.6% |
| language slips | 0.0% | 1.4% | 0.3% | 0.9% |
| coherent turns (judge) | 71.2% | 69.1% | 60.4% | 86.9% |
| requests honoured (judge) | 47.5% | 44.8% | 37.8% | 61.4% |
| premise score 0–2 (judge) | 1.34 | 0.76 | 0.99 | 0.86 |
| tone: fine / curt / snarky / servile | 55.3% / 27.4% / 16.7% / 0.6% | 60.3% / 28.8% / 9.3% / 1.6% | 64.2% / 2.6% / 3.1% / 30.1% | 77.4% / 3.3% / 2.8% / 16.5% |
| mean answer words | 27 | 22 | 69 | 53 |

### Per move (share of turns broken by regex: loop, tail copy, or the new request not addressed; and judged coherent)

| move | arm B (round two) broken / coherent | stage 1 (no personality pass) broken / coherent | Apertus-8B-Instruct-2509 broken / coherent | Llama-Krikri-8B-Instruct broken / coherent |
|---|---:|---:|---:|---:|
| absurd_premise | 81.0% / 95.2% | 57.9% / 94.7% | 57.9% / 68.4% | 60.9% / 91.3% |
| conv_reference | 73.3% / 66.7% | 52.9% / 64.7% | 68.8% / 56.2% | 40.0% / 60.0% |
| correction | 86.1% / 52.3% | 89.4% / 35.3% | 81.3% / 39.0% | 69.3% / 75.4% |
| dismissal | 73.7% / 57.9% | 80.0% / 73.3% | 57.9% / 21.1% | 52.6% / 47.4% |
| false_claim | 77.3% / 77.3% | 61.9% / 100.0% | 65.2% / 87.0% | 33.3% / 100.0% |
| greeklish_short | 55.9% / 73.5% | 72.7% / 78.8% | 62.5% / 50.0% | 42.9% / 88.6% |
| impossible_self | 65.2% / 87.0% | 73.9% / 91.3% | 66.7% / 75.0% | 67.9% / 96.4% |
| insult | 73.5% / 58.8% | 78.1% / 65.6% | 51.4% / 51.4% | 36.8% / 81.6% |
| interjection | 69.7% / 54.5% | 65.6% / 78.1% | 90.6% / 81.2% | 65.6% / 81.2% |
| meta_other | 56.2% / 81.2% | 56.2% / 75.0% | 66.7% / 66.7% | 52.6% / 84.2% |
| nonword | 60.0% / 100.0% | 42.9% / 92.9% | 46.7% / 80.0% | 66.7% / 94.4% |
| plain_request | 69.8% / 83.7% | 70.2% / 83.5% | 58.1% / 75.1% | 57.2% / 94.8% |
| roleplay | 70.0% / 90.0% | 60.0% / 80.0% | 47.4% / 68.4% | 52.0% / 88.0% |
| rude_accusation | 75.0% / 83.3% | 100.0% / 64.3% | 83.3% / 33.3% | 85.7% / 100.0% |
| sarcasm | 71.4% / 57.1% | 69.2% / 69.2% | 100.0% / 23.1% | 64.3% / 78.6% |
| slang | 63.6% / 81.8% | 55.0% / 70.0% | 47.4% / 68.4% | 56.5% / 82.6% |
| stop | 69.8% / 45.3% | 62.0% / 62.0% | 64.4% / 49.2% | 47.6% / 85.7% |
| threat | 76.7% / 56.7% | 86.7% / 56.7% | 87.5% / 34.4% | 80.6% / 90.3% |
| topic_switch | 81.8% / 95.5% | 82.6% / 65.2% | 75.0% / 80.0% | 60.0% / 80.0% |

### Reading the baseline

- **Repetition is an Apertus-family trait, not a personality-pass artefact.** Tail copying and dead dialogues sit at 14–18% and 20–23% for arm B, stage 1 and Apertus-8B-Instruct alike, and at 0.7% and 0% for Krikri (Llama 3 base). Arm B is slightly better than stage 1, so the ×4 personality pass did not sharpen the loop. Within-answer loops are near zero at 300 tokens under vLLM sampling; the owner's laptop loops ran at 512 tokens in 8-bit MLX, which the R1 decoding arm was to test and did not get to (walltime).
- **Where arm B leads**: stop instructions honoured 92.5% (stage 1 76%, Apertus 70%, Krikri 98%) and premise handling 1.34 of 2 (stage 1 0.76, Apertus 0.99, Krikri 0.86): the personality set's premise-checking rows and its meta-instruction rows show.
- **Where arm B trails Krikri**: coherence 71% vs 87%, requests honoured 48% vs 61%, and tone: 55% fine with 27% curt and 17% snarky, against Krikri's 77% fine. Apertus-Instruct is servile 30% of the time; ours is curt instead. The brevity of the personality set (27 words a turn against Krikri's 53) reads as curtness under this judge.
- **Stale rate is not yet trustworthy**: it checks for the simulator's key noun as an exact substring, and Greek inflection makes it fail for every model (68–84%); it needs stem-tolerant matching before it is used as an acceptance metric.
- **R1 (repetition penalty) did not run**: the four R0 runs used the whole two-hour window at the tunnel-safe concurrency. It goes into the next window together with the on-policy data run, on the cluster side rather than through the tunnel.
- Cost of the window: 2.0 node-hours (job 3333857, TIMEOUT at 02:00:08). Apertus-8B-Instruct rejected 5 requests with HTTP 400 (its chat template on a popped turn), which truncated those dialogues.

## 9. R1 results · arm B under the mixed-profile simulator (9 September, job 3335815, 1.5 nh)

120 dialogues (66 benign, 28 steering, 26 hostile), 1,640 turns, Sol user at medium effort with calm exemplars; then a 60-dialogue arm with repetition penalty 1.1 that the walltime cut short (338 turns, 5.6 a dialogue instead of 13.7, so its numbers are on truncated dialogues).

| metric | benign | steering | hostile | all (R1) | all, R0 hostile-only |
|---|---:|---:|---:|---:|---:|
| tail copied from the previous answer | 2.6% | 4.4% | 14.9% | 5.8% | 14.4% |
| dead dialogues | | | | 8.3% | 20.0% |
| coherent turns (judge) | 81.1% | 85.5% | 65.4% | 78.6% | 71.2% |
| tone fine | 82.7% | 82.9% | 51.6% | 76% | 55.3% |
| standing instruction kept on later turns | | 67.6% | | | |
| self-observation and recap answered correctly | 21.3% | 26.1% | 13.3% | | |
| redirect or redo addressed (key noun) | | 34.7% | | | |
| stop instructions honoured | | | | 100% | 92.5% |
| mean answer words | 39 | 24 | 28 | | 27 |

Reading:

- **The hostile slice reproduces R0** (tail copy 15%, tone fine 52%), so the earlier baseline was the hostile profile's number, and it is stable across simulator versions.
- **Under cooperative users arm B is a different model**: tail copying 2.6%, coherence 81%, tone fine 83%. The curtness is still there (18% of all turns judged curt), the servility is not (0%).
- **Steering is the weak axis**, and it is measurable now: a standing instruction («from now on one sentence», «no questions back», «end with this phrase») survives on 68% of later turns; redirects and redos land the new request only 35% of the time; and when asked to observe itself («did you repeat yourself?», «what have we said?») the model is right 26% of the time. The recap sample in the reader shows the pattern: it recounts the conversation with one invented item, is corrected, then gets it right.
- **Repetition penalty 1.1**: tail copying 0.3% and no dead dialogues, at the price of answers twice as long (63 words in the benign profile) and a lower premise score (0.64 vs 0.90); persistence fell to 23%, though that arm's dialogues were cut short by the walltime, so treat the penalty numbers as indicative only.
- Data implications for the on-policy run: the steering moves (standing instructions, redirect, redo, self-observation, recap) are the first lane to generate rewrites for; hostile handling second; benign small talk needs little.

Pages: dialogues `presentations/PICKY_USER_DIALOGUES_R1_20260909.html`; summaries under `results/robustness_r1_20260909/`.

## 10. Astra review of R1 (2026-09-09) and the S12 contract

Review: docs/reviews/ASTRA_robustness_r1_20260909.md (gpt-6-astra, xhigh; 2 BLOCKER, 4 HIGH). R1 itself is a completed
experiment and is not regenerated. Everything below is applied to the simulator/judge (data/robustness/simulate.py, backup
simulate.py.bak_r1) BEFORE the S12 lane runs; the R1 numbers in §9 stand as measured but the labels they used are re-read as follows.

| Finding | What it said | Applied |
|---|---|---|
| F1 BLOCKER evidence | 10/30 exported rows were clipped by the reviewer page (`--max-chars`), so judge verdicts could not be checked | every turn now stores `finish` (finish_reason), `usage`, `n_chars` and a `prompt_hash` of the exact history sent; reviewer exports of S12 are unclipped (full rows.jsonl handed over) |
| F2 BLOCKER `request_not_addressed` | the key-noun flag fired on 14/19 correct topic-switch answers | the flag is renamed `key noun absent?` (heuristic), no longer counted in `broken`; the judge now separates `uptake`, `honours` (yes/no/needs_info/unavailable/na), `correct`, `consistent`; S12 selection uses the judge fields, never the heuristic, and is calibrated on an adjudicated set with successful answers before any target is written |
| F3 HIGH judge rewards the wrong things | «δεν κάνω λάθη» scored premise 2; literal denial of role-play scored 2; wrong self-descriptions scored selfaware 1; contradictions passed coherence; short answers labelled curt | new rubric: applicability (joke/hypothesis/role-play/preference ≠ false premise; literal refusal of harmless fiction → −1), consistency separate from truth, selfaware needs an `evidence` span + `antecedent` turn, brevity ≠ dismissiveness, the judge is told the assistant's identity and capabilities and judges each turn with only what precedes it |
| F4 HIGH move labels | 1/8 false claims was a true correction; invented prehistory («afou les oti…») | simulator: refer only to what was actually said, state the claim verbatim in `claim`; judge labels `realised_move` and `claim_truth` (true/false/unknown/subjective); rows keep `sampled_move` and `realised_move` |
| F5 HIGH scripted reactivity | 12/12 topic switches hooked a word from the answer; endless dismissals; weights are not user prevalence | `--policy naturalistic` (goal-preserving, `end` move after turn 4, no word-hook mandate, at most two consecutive challenges) alongside `stress`; rows carry `weights: designed test weights` |
| F6 HIGH rewrite rules | repairing an early answer invalidates later turns; syntactic success ≠ good target; privacy/truth defects survive fluent rewrites | the S12 contract below |

**S12 contract (binding for the builder, not yet written):**
1. One repair per row: keep the original full prefix, replace only the target response; earlier assistant turns are `train: false` (loss-masked).
2. If an earlier response must be replaced, regenerate the dependent later user turns (re-simulate from that point) instead of keeping a continuation that refers to the removed defect.
3. Keep the original answer in the row as `rejected` (audit / preference candidate); it is never a positive.
4. Validate every rewrite against the actual request, the active standing instructions, the evidence in the transcript and the model's capabilities (no invented officials, credentials, prices); a Taxisnet-credentials solicitation is a truth/privacy failure gate, not a style fix.
5. Preserve successful turns and successful recoveries as-is; cap near-duplicate failures from the same loop (≤ 2 per dialogue).
6. Selection signal = judge fields (`honours`, `uptake`, `correct`, `consistent`, `premise`, `selfaware`) after calibration on ≥ 60 adjudicated turns that include successful answers; the key-noun heuristic is display-only.
7. Trainer prerequisite: per-turn loss masking (`train: false`) in cluster/sft_train.py before any S4/S12 rows are trained (DATA_TODO 26).
