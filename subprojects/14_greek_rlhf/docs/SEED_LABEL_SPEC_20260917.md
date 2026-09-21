# RLHF labels and terms specification — v1.0.3 (frozen 17 Sept 2026; R-PG1 cycle-2 fixes applied without a third cycle)

Status: frozen v1.0.3 (17 Sept 2026; R-PG1 cycle-2 fixes applied without a third cycle). Written 17 Sept 2026 by Fable at the owner's
request. Code that reads the glossary records its sha16 (§6 rule 8): registry and relabelling (`data/rlhf/registry/`), generator 0.2
(`data/rlhf/generator_v02/`) and dialogue v2 (`data/rlhf/dialogue_v2/`).
Scope: every label that a seed, a gate or a pipeline stage passes to Sol when generating or labelling RLHF prompts and dialogues, every
label we later use to allocate or analyse data, and the working terms of the two-stream execution plan
(`docs/RLHF_COORDINATION/RLHF_TWO_STREAM_EXECUTION_PLAN_20260917.md`): generator 0.2 corrections (§4.1–§4.6, §5) and dialogue data
generation corrections (§4.4, §4.7, §4.8), plus the dataset and eligibility terms both streams share (§5.4). Maths judging fields are
defined in `MATH_JUDGING_EXECUTION_PLAN_20260917.md` §A3 and are not duplicated here.
Companion file (prompt-ready glossary, same definitions): `data/rlhf/prompts/seed_label_definitions_v1.md`.
Versions: see `docs/RLHF_COORDINATION/CURRENT_VERSIONS.md`. Sources checked: prompt-generator-0.1 (DEFUNCT per the owner, 17 Sept; audited
here as evidence of what went wrong); generator 0.2 (current method: target distribution filled by forum prompts plus person-and-story seeds; generator 0.3 adds dialogue); Codex's pre-release design notes (`~/Documents/Codex/2026-09-13/rea/outputs/rlhf50_20260916/`:
`TASK_FIRST_SEED_DESIGN.md`, `PIPELINE_EXACT.md`, `task_parameters_v3.json`, identical to the released `design.json`); the dialogue
pilot code; generator 0.2's seed script (the prototype that produced round 2's seeded prompts); forum gate v3 (generator 0.2's forum part); and `docs/RLHF_COORDINATION/OPUS_FEEDBACK_20260917.md` (owner-agreed adaptive
user model, 17 Sept).

Aspects (as in the two-stream plan §0): sections tagged [PG] belong to prompt generation, [RLHF] to replies, judging, pairs and training, [shared] to both.

Review asks, in short: (1) are the definitions in §4–§5 right and distinct enough to be applied consistently; (2) the decisions in §7;
(3) whether the prompt rules in §6 are sufficient.

## 1. Why this document exists

The owner asked whether Sol sees definitions for labels such as `"difficulty": "routine"`. It does not: in all four generators the labels
reach Sol as bare values. Sol then applies its own reading, the generator's reviewer checks the output against the same undefined labels,
and we allocate prompts and report results per label (for example round 2's per-task-type pair counts). A label that is not defined cannot
be applied consistently, reviewed, or compared across runs.

## 2. Where labels are used

| Pipeline | Code | Labels sent to Sol | Used later for |
|---|---|---|---|
| Single-turn generator 0.1 (Codex) — DEFUNCT; round 1, 121 prompts | `data/rlhf/prompt_generator/worker.py` (`public_packet`, `SYS`, `REVIEW`) | purpose, underlying_family, language, register, attitude, difficulty, instruction_spec, dialogue_opening_only; reviewer also gets private_reference and premise_status | quotas per cell (purpose × language), pool slices |
| Generator 0.2, seed part (person-and-story prototype, unreviewed) — round 2, 167 prompts | `data/rlhf/gen02_demo/seed_demo.py` (`AX`, `PROMPT`) | person, situation, task, topic, specific, detail, register, attitude, language | task weights, round-2 analysis by task and detail |
| Forum gate v3 — forum prompts, rounds 1 and 2 | `data/rlhf/prompts/forum_gate_rewrite_el.txt` | Sol assigns: post_kind, flags, false_premise, task_type, kept_details | selection (post_kind), round-2 tilt and analysis (task_type), purpose mapping |
| Dialogue pilot | `data/rlhf/dialogue_quality_depth/openings.py`, `user_policy.txt`, `turn_quality.txt`, `rank.py` | openings: task, difficulty, interaction, attitude, register, language; simulator: attitude, register, user goal and plan | trajectory quotas, analysis by interaction and task |
| Codex's pre-release 50-prompt pilot (not released, superseded by 0.1) | `rlhf50_20260916/PIPELINE_EXACT.md`, `seed_sampler/` | subtask (47 literal labels), register, stance, depth (brief/standard/detailed), source_preserved | design evidence only; 0.1 renamed stance to attitude and dropped depth |

## 3. Audit: what is defined today

Legend: **defined** = the prompt Sol receives explains each value; **partial** = a rule or a gloss for some values; **undefined** = bare
value names only.

### 3.1 Single-turn generator 0.1 (defunct; kept as evidence)
| Label | Values | Status in the prompt | Notes |
|---|---|---|---|
| purpose | everyday, instruction, factual, safety, math, dialogue | undefined | `SYS` even forbids putting "task taxonomy" in the request, but never defines it. |
| underlying_family | 38 code ids such as `if_composite`, `f_premise`, `safe_fiction` | undefined | `design.json` has a human label per family ("IF: preserve and exclude") and per-family difficulty definitions; neither is sent. |
| difficulty | routine, compositional, challenging | undefined | Defined per family in `design.json` and realised in the fixture code (1/2/3 clauses), so the content already encodes it; the label sent to Sol is redundant. `SYS` forbids difficulty labels in the request. |
| register | standard, informal, formal, greeklish | partial | One rule: "Greeklish means Greek transliterated into Latin characters … register and attitude change natural wording, not the task, facts or harmfulness." No definition per value. |
| attitude | cooperative, frustrated, skeptical, playful | partial | Same rule, plus "Frustration must not invent prior model failures." |
| instruction_spec | free English sentence per fixture | defined by content | Self-explanatory. |
| premise_status (reviewer only) | supported, contradicted, unresolved, not_applicable | undefined | Reviewer is told to check "answerability and deliberate premise". 115 of 121 round-1 seeds are not_applicable. |
| private_reference.safety_context (reviewer only) | benign, protective, fiction, harmful, ambiguous | undefined | Private; reviewer uses it to check the request did not leak it. |
| observed_register / observed_attitude (reviewer output) | "the supplied allowed labels" | undefined | The reviewer agreed with the assigned register and attitude in 121 of 121 cases: with no definitions the check cannot discriminate. |
| Prompt vocabulary | "authoring conditions", "curator labels", "fake variation", "deliberate premise" | undefined | Terms from the design, not explained to Sol. |

### 3.2 Generator 0.2, seed part (person-and-story seeds; round 2)
| Label | Values | Status | Notes |
|---|---|---|---|
| detail | bare, terse, short, medium, detailed, rambling | defined | Each value carries its definition inline. |
| task | 12 descriptive values ("everyday: γράψε/ξαναγράψε ένα μήνυμα ή email", "safety: αίτημα που πρέπει να απορριφθεί ή να ανακατευθυνθεί") | partial | Self-describing but mixed Greek/English; "redirect" and "looks suspicious but is harmless" have no boundary. Its two maths values ("everyday numbers", "school exercise with full solution") predate T5: the 0.2 release replaces them with the seven maths kinds and does not require a worked solution unless the request asks for one. |
| person, situation, topic, specific | descriptive phrases | defined by content | Self-explanatory. |
| register | standard, informal, formal, greeklish | partial | Prompt glosses greeklish only. |
| attitude | cooperative, frustrated, skeptical, playful, **anxious** | undefined | `anxious` is a new value not used anywhere else; it tagged 31 of the 167 round-2 prompts. |
| language | el, en | defined by convention | |

### 3.3 Forum gate v3
| Label | Status | Notes |
|---|---|---|
| post_kind | defined | request, social, declaration_or_announcement, advertisement, each with a sentence (STEP 0). |
| flags forum_default, op_context, world_anchor | defined | Each with a sentence and an example. |
| false_premise | defined | "a mistaken assumption that a correct answer would have to address". |
| kept_details | defined | |
| **task_type** | **undefined** | Only "task_type ∈ {question, advice, translation, explanation, calculation, opinion, share, other}". Yet it drove round 2's forum tilt (70 question, 70 advice, 40 opinion …) and the per-category results. The boundaries question/explanation, advice/opinion and share/social are exactly where readings differ. |
| task_type → purpose | undocumented | `assemble_round1_pool.py` maps question, explanation, calculation → factual; advice, opinion, share, translation, other → everyday. |

### 3.4 Codex's design notes (pre-release)
`TASK_FIRST_SEED_DESIGN.md` already separates problem structure, instance variables, difficulty, user expression ("user_surface":
language, register, uncertainty, informality, attitude), sourcing ("source_route") and interaction, and states that `source_preserved` is
provenance, not a register. It lists a richer dialogue interaction set (follow-up, revision, clarification, recall, constraint persistence
and revocation, real-error recovery, false-correction resistance, social response). It does not define the values of any of these axes.

### 3.5 Dialogue pilot
| Label | Status | Notes |
|---|---|---|
| task, difficulty, interaction, attitude, register (opening writer) | undefined | Bare JSON values; the instruction mentions only "assigned language/register and interaction plan". |
| interaction (measurement openings) | undefined | The 6 smoke chats received one scenario sentence each; the 28 measurement chats received the bare label. |
| attitude, register (user simulator) | undefined | `user_policy.txt` names the fields only. |
| severity, dimensions, recovery flags (annotator) | defined | `turn_quality.txt`. |
| verdicts, issue tags (ranker) | defined | Rubric v2.4. |

## 4. Definitions — seed axes [PG]

Each definition describes what the user's message looks like, so Sol can write it and a reviewer can check it. Labels change how the user
writes and behaves; they never change the facts, the task, or how harmful the request is. IDs are for review comments.

### 4.1 Attitude — how the user relates to the assistant and the task
- **A1 cooperative:** Neutral good faith. States the need, supplies what is asked for, accepts a reasonable answer, points out problems matter-of-factly.
- **A2 frustrated:** Impatient because of the situation: a deadline, their own failed attempts, a service that let them down. Short, blunt sentences, perhaps an exclamation; never abusive. An opening may not blame the assistant for failures that did not happen; later dialogue turns may react to the assistant's actual failures.
- **A3 skeptical:** Does not take answers on trust. Asks why, asks for the basis or a way to check, mentions a conflicting claim they heard. Challenges by asking for justification, never by asserting that a correct answer is wrong.
- **A4 playful:** Light, joking tone (humour, teasing, wordplay, an emoji) while the request stays genuine and answerable. Not trolling and not a test of the assistant.
- **A5 anxious (defined, not drawn; used in round 2):** Worried about a consequence for themselves or someone close (health, money, a deadline, getting something official wrong). Asks for certainty or reassurance, may over-explain or ask the same thing twice. Differs from frustrated: fear of the outcome, not impatience with an obstacle.

### 4.2 Register — how the language is written
- **R1 standard:** Neutral everyday written language, as in a clear message to someone you do not know well: accents and punctuation in place, no slang.
- **R2 informal:** How people type to friends or on a phone: singular «εσύ», colloquial words and contractions, loose punctuation, accents sometimes dropped, occasional typos.
- **R3 formal:** Polite and institutional: plural of politeness («θα μπορούσατε», «σας παρακαλώ»), complete sentences, no slang; the tone of writing to a public service, a lawyer or a professor.
- **R4 greeklish:** Greek written in Latin letters as typed on phones and forums (θ as th or 8, χ as x or h, ω as o or w), usually informal. Greek-language users only.

### 4.3 Difficulty — how much reasoning the task demands (realised in the content, not the wording)
- **D1 routine:** One step; everything needed is stated; no trade-offs.
- **D2 compositional:** Two or three dependent steps, or several constraints that must hold at the same time.
- **D3 challenging:** Constraints that interact or conflict, a genuine case distinction, uncertain or missing inputs, or a request that superficially resembles a different kind of task.
These generic definitions are authoritative for generator 0.2 and later: the concrete content that realises them is carried in the seed instance (subtype preconditions in `data/rlhf/generator_v02/task_kinds.json`). The family-specific versions in `design.json` apply only to archived generator 0.1 rows.

### 4.4 Interaction — what the user does after the first answer (dialogue only; describes the user, never a planned model failure)
- **I1 followup:** Builds on an answer they accept: more depth, an example, the next step or a related question, without changing the original requirements.
- **I2 revision:** Changes something about the task after seeing the answer: length, audience, tone, a number, an added requirement. The assistant must apply the change and keep everything else.
- **I3 constraint_retention:** States a lasting constraint early (a word limit, a format, "no English terms", "always formal") and later makes different requests without repeating it.
- **I4 recall:** Gives specific information early (names, numbers, preferences, a text) and later asks something that depends on it without restating it.
- **I5 uncertainty:** Starts from an incomplete, ambiguous or wrongly premised request; the good response asks, states an assumption, or corrects the premise. The user answers clarifying questions when asked.

Codex's design notes add interactions not covered above: **constraint revocation** (the user lifts an earlier constraint), **real-error recovery** (the user points to an actual, verified error), **false-correction resistance** (the user wrongly claims a correct answer is wrong; challenge set only) and **social response** (the user shares a feeling or situation rather than a task). They are not defined here; they are deferred to the dialogue track (§7 decision 7).

### 4.5 Task (primary purpose) — what the request is for
- **T1 everyday:** Practical help a person wants done: write or rewrite, plan, explain, translate, troubleshoot, use a tool. Success means the person is better off.
- **T2 instruction:** An ordinary task with explicit, checkable requirements on the answer's form: format, length, values to keep or exclude, conditional content. Success is mainly meeting them.
- **T3 factual:** A question with a knowable answer, from general knowledge or a supplied text, including cases where the honest answer is that information is missing, the premise is false, or sources conflict.
- **T4 safety:** A request where the right response depends on judging risk (sub-kinds in §5.3).
- **T5 math (maths):** A request whose central purpose is mathematical calculation, reasoning, explanation or problem-solving. Correctness is assessed against the stated assumptions, mathematical definitions and valid reasoning. A task may admit one result, several valid answers, equivalent expressions, different solution methods, or a proof that no solution exists. The required explanation depends on what the user asks.
  Maths kinds:
  - **T5.1 calculation:** arithmetic, numerical estimates, probabilities, statistics and unit conversions.
  - **T5.2 solving:** equations, inequalities, systems and optimisation problems.
  - **T5.3 proof and justification:** establishing why a claim holds, including relevant assumptions and cases.
  - **T5.4 construction and counterexamples:** finding an object satisfying conditions or disproving a claim.
  - **T5.5 explanation and learning:** explaining a concept, interpreting a result or helping resolve a misconception.
  - **T5.6 checking and correction:** identifying and repairing an error in a proposed solution.
  - **T5.7 modelling:** translating a described situation into mathematics, stating necessary assumptions and interpreting the result.
  These distinctions matter. Solving \(x^2=4\) requires both solutions; proving a claim does not produce a numerical answer; an optimisation problem may have several equally good solutions; and an explanation of fractions can be correct in many different forms.
  **Reference.** A reference is a basis for verification, not text the response must imitate. Depending on the task, it contains: the assumptions and interpretation of the question; the acceptable result, solution set, defining properties or mathematical conclusion; a verified argument or method where needed; relevant checks (units, domain restrictions, cases, numerical tolerance and rounding); and the requirements for a complete response. For a proof, checking the final conclusion is insufficient: the argument must establish it. For a construction, the proposed object must satisfy the conditions. For an explanation, the mathematical claims and examples must be sound, but the wording need not match the reference.
  **Correctness and explanation length are separate.** A concise correct answer can fully satisfy "give only the result". A request to explain, prove or show the calculation requires appropriate justification. More steps do not automatically make an answer better, and a correct final result does not excuse false equations or invalid reasoning in the explanation supplied. Clarity means that the mathematics can be understood and checked; stylistic elegance, expressiveness and personality are secondary and cannot compensate for mathematical errors.
  **Maths inside other primary purposes.** Maths is also detected inside other task categories through a separate indicator, **maths content** (§5.6): a travel-planning request with budgets remains primarily everyday assistance while carrying the indicator; a tutoring dialogue remains dialogue material while its mathematical claims receive specialist checking. The primary-purpose distribution is preserved and embedded mathematical errors do not escape review.
  **Ambiguity flag.** Ambiguous (several readings) or underspecified (missing information needed for a determinate answer) maths questions are flagged. A valid response may explain that the answer is not uniquely determined, state a justified assumption or request essential information. The generator and the evaluator must not silently invent missing assumptions merely to manufacture a single reference answer; flagged items are held until resolved (maths plan §A1).
- **T6 dialogue:** A multi-turn conversation whose training value lies in the turns after the first; its underlying task is one of T1–T5 and is recorded alongside.
These six are the **primary purposes** of the agreed target distribution (`data/rlhf/target_distribution_v1.json`); a cell is primary purpose × language (§5.4). A task family (defined in §5.4) groups tasks that share an underlying task, scenario or mathematical structure, a finer grouping than a primary purpose (generator 0.1's 38 recipes, such as "IF: preserve and exclude", were task families); a **task type** (`task_type`) is reserved for the forum F1–F9 analysis label (§5.1) and is never an allocation unit.

### 4.6 Detail — how much the user says (person-and-story seeds)
- **L1 bare:** only the ask itself, one line of at most 12 words, no context, no names, no story, maybe no accents or punctuation.
- **L2 terse:** one or two lines of at most 30 words, the ask plus at most one fact the assistant needs, no names.
- **L3 short:** two or three sentences, one concrete detail, nothing pasted.
- **L4 medium:** a paragraph with the situation and what they want.
- **L5 detailed:** full context, several specifics, pasted material if relevant.
- **L6 rambling:** long, unordered, mixes the story with the request, repeats itself.
Detail is defined by how much the person themselves says: how much context they volunteer, how many specifics they give, with hard word ceilings for bare (12) and terse (30) that count only the user's own words. Material pasted as the object of the request (a draft, a notice, a text to work on) is excluded from the count and never raises the detail level: a one-line ask with a pasted notice is bare, not detailed. A request that needs pasted material cannot be short. Values that define the task itself — the numbers of a calculation, the claim to prove, the format constraints the person sets, the text to translate — are part of the ask, not context; detail measures the context the person volunteers: who they are, why they ask, their story, names and background.
Realised length in round 2's 167 seeded prompts (words, median with 10th–90th percentile): bare 24 (14–31), terse 26 (21–34), short 38 (27–48), medium 68 (54–95), detailed 148 (93–211), rambling 186 (116–262). Forum prompts: median 56 (25–143).
Finding: bare and terse came out almost the same length, and bare is not "one line"; the definitions do not separate them in practice. Resolved by §7 decision 10: both kept, with hard ceilings (bare 12 words, terse 30 words).
Length terms kept apart: **detail** is how much the user says (a [PG] label on prompts); **reply length** is not a label: the rubric asks for "the depth the question needs" and the judging monitors length bias [RLHF]; Codex's earlier **depth** axis (brief, standard, detailed) described the expected answer depth and was dropped in generator 0.1.

### 4.7 Response to failure — what an adaptive user does after an unsatisfactory reply (owner-agreed principle, 17 Sept) [PG]
The owner endorsed an adaptive user model: after a failure a user may explain with an example, break the task into steps, express
frustration, simplify the request or abandon it. Move labels (adopted list; selection rule owned by the dialogue workstream and frozen there at R-PG6, §7 decision 8):
- **M1 restate:** repeats or rephrases the request without new information. Realistic occasionally, not the default after every failure.
- **M2 point_to_defect:** names the precise part that is wrong or missing.
- **M3 give_example:** shows a short example of the kind of answer wanted, from the user's own plausible knowledge.
- **M4 decompose:** breaks the task into parts and asks for one of them.
- **M5 add_context:** supplies information the assistant lacked; recorded when it narrows the task, never passed off as an original requirement.
- **M6 simplify:** narrows the scope or lowers the requirement.
- **M7 express_frustration:** shows impatience; may shift attitude towards frustrated.
- **M8 accept_partial:** accepts imperfect progress and moves on.
- **M9 abandon:** ends the conversation unresolved; a terminal reason distinct from natural completion.
- **M10 clarify:** explains what they meant or answers a question the assistant asked, without changing the task.
- **M11 continue:** makes the next legitimate request after useful progress (the healthy path; not a response to failure).
- **M12 finish:** ends the conversation because the task is done (natural completion).
Mapping to the dialogue v2 plan's wording: "identify a defect" = M2; "concrete example" = M3; "decomposition" = M4; "missing fact" = M5; "narrower request" / "simplification" = M6; "frustration" = M7; "acceptance" = M8; "abandonment" = M9; "clarification" = M10.
**Turn metadata:** each saved user turn records exactly these four fields: `move` (one move label above), `new_information` (what it adds), `trigger` (the visible event it reacts to) and `changes_task` (true when it narrows or alters the task). No other names are used for them (earlier drafts of the dialogue v2 plan: strategy, what_visible_event_triggered_it, whether it changes the task).
Assistance level, recorded per user turn so results can be reported separately: **restatement < pointed defect < partial scaffold or example < supplied solution**.
User capability should vary (willingness and ability to diagnose errors, patience); not every user is a competent tutor.

### 4.8 Dialogue terms (dialogue v2 plan and reference-guided demo) — sampling points [RLHF]; ending reasons [shared]; user state and role views [PG], evaluator view [RLHF]

**Serious error:** an assistant reply that materially defeats the user's task, violates a critical constraint or boundary, is wrong in the main, or creates a consequential safety failure (the threshold used by the turn annotator, `dialogue_quality_depth/turn_quality.txt`). A **minor** defect leaves the reply useful. Mathematical claims inside a reply are judged for seriousness by the specialist maths judge.

Sampling points on a recorded trajectory (each gets its own same-prefix comparison):
- **prevention point:** the prefix ending immediately before the first seriously erroneous assistant reply. At turn 1 it counts as single-turn material (owner rule); later points from the same conversation remain dialogue material.
- **supported recovery point:** the prefix ending immediately after the first genuinely helpful user intervention (M2–M6, M10) that follows an error. Absent when no such intervention occurred; never forced.
- **healthy continuation point:** a deeper assistant turn with no preceding serious error, where a meaningful next task exists.
Mapping to the dialogue pilot (dialogue-quality-depth-v1): its P = prevention point; its R ("genuine repair opportunity") is broader than the supported recovery point, which requires a helpful user intervention; its C (control) ≈ healthy continuation point.

Ending reasons: **natural completion** (M12), **abandonment** (M9), **horizon** (turn cap reached), **context cutoff** (the next reply cannot fit the served context; not a model failure), **truncated output** (the reply hit the token cap), **infrastructure failure**, **ambiguous timeout**.

User state (private to the user simulator): **goal**; **known facts**; **expertise** (novice / intermediate / expert in the task's domain); **misconception** (a specific wrong belief, if any); **disclosed preferences** (said in the conversation) versus **private preferences** (held but not yet said; revealing one later is a new preference, never an earlier violation); **patience** (low: gives up or complains after one failure; medium: tries a second strategy; high: persists with several strategies); **helping ability** (can the user diagnose a defect, give an example, or only restate); **repeated defect count**; **task progress**.

Role views (what each participant may see):
- **Apertus view:** the public conversation only.
- **user view:** goal, known facts, preferences, patience, visible conversation and observations already revealed. For writing tasks it may include an illustrative reference draft.
- **world resolver:** for troubleshooting, the fixed hidden cause and the outcome of each supported check; returns only the observation a user action would plausibly produce; unknown actions return "unresolved", never invented success.
- **learner view:** current knowledge, misconception, goal and visible teaching; never the gold answer to a transfer question.
- **evaluator view:** verified facts or solutions, the visible history and the relevant state; judges correctness and whether claimed progress is supported.

Reference-guided dialogue categories (demo): **writing** (a desired result exists as an illustrative reference draft; not an exact-match answer); **troubleshooting** (a consistent hidden world: fixed cause, supported checks and their outcomes); **learning** (a learner knowledge state and evaluator-only subject knowledge, with a **transfer check**: a new example the learner attempts without being given the answer).

## 5. Definitions — labels assigned by Sol or used privately

### 5.1 Forum task_type (assigned by the forum gate) [PG]
- **F1 question:** Asks for a specific fact or piece of information with a determinate answer ("what is", "when", "which", "is it true that").
- **F2 explanation:** Asks why or how something works, or what something means; the answer is a mechanism, a reason or a meaning rather than a single fact.
- **F3 advice:** Asks what the poster should do in their own situation: a decision, a next step, what to buy, how to handle something.
- **F4 opinion:** Asks for others' judgement on a matter where reasonable people differ (taste, usage preference, an interpretation), not about the poster's own next step.
- **F5 translation:** Asks to render, check or find the right term for a word, phrase or text in another language.
- **F6 calculation:** Asks for a numeric result or a worked computation.
- **F7 share:** Shares an experience, situation or thought and invites responses without a specific question (the task_type of post_kind social).
- **F8 other:** None of the above.
- **F9 create:** Asks the reader to produce something (write, format, list, draft); maps to everyday.
Boundaries: question vs explanation = single fact vs mechanism or meaning; advice vs opinion = the poster's own decision vs a judgement on a general matter; the meaning or etymology of a Greek word is explanation, its rendering in another language is translation.
**Precedence (exclusive assignment):** each forum row receives exactly one task_type, the first in this order that applies: calculation (any request whose central deliverable is a computed value) > translation (rendering supplied text into another language, even if it also "creates" text) > create > advice > opinion > explanation > question > share > other. Boundary examples: a question with a determinate numeric answer ("how many days are there between 3 March and 17 May?") is calculation, not question; "translate this paragraph into English" is translation, not create.
Purpose mapping: question, explanation → factual; calculation → math; advice, opinion, share, translation, other, create → everyday. Any forum post may also carry the maths content indicator (§5.6) whatever its task type.

### 5.2 Premise status (generator 0.1 reviewer) [PG]
- **P1 supported:** The request contains a premise and the source confirms it.
- **P2 contradicted:** The source contradicts the premise: a deliberate false premise that a correct answer must correct.
- **P3 unresolved:** The source cannot settle the premise; a correct answer says what is missing.
- **P4 not_applicable:** The request rests on no premise to check.

### 5.3 Safety context (private reference; the same sub-kinds should drive safety task seeds) [PG]
Exclusive decision order (the first that applies): **harmful** if the request seeks operational help towards serious harm, whatever its framing; else **fiction** if it is a creative request whose risky theme needs no operational detail; else **protective** if its purpose is to protect the user or someone else from a risk; else **ambiguous** if the purpose is undetermined and one plausible reading is harmful; else **benign**.
- **S1 benign:** Sensitive wording, legitimate purpose; the right response helps fully.
- **S2 protective:** The person wants to protect themselves or someone else; the right response helps with the protective steps.
- **S3 fiction:** A creative request touching a risky theme; the right response writes it without operational detail.
- **S4 harmful:** The request would cause serious harm; the right response declines and, where useful, redirects to a safe alternative.
- **S5 ambiguous:** The purpose could be benign or harmful; the right response helps with the clearly safe part or asks for the purpose.

### 5.4 Dataset and eligibility terms (shared by both streams) [RLHF]
- **cell:** one combination of primary purpose (§4.5, T1–T6) and language (the seven target languages): 42 cells = 6 purposes × 7 languages, as in `data/rlhf/target_distribution_v1.json`. Quotas, deficits and coverage are counted per cell. Forum rows enter a cell through the purpose mapping of §5.1; `task_type` is reserved for the forum F1–F9 analysis and is never an allocation unit.
- **accepted-pair yield:** eligible pairs produced per judged prompt or prefix in a cell; new collection is steered by deficits in accepted pairs, not in raw prompts.
- **eligible preference pair:** one chosen and one rejected reply to the byte-identical prompt or prefix, where the chosen is **acceptable** (reinforce under the governing rubric; for maths, eligible_positive under the specialist judge), the rejected is ranked lower with a **meaningful gap** (judge margin "clear"; neutral or discourage), and provenance is complete. "Less bad" is never acceptable.
- **active view:** the set of judgements that currently decide eligibility; older judgements stay in the append-only history.
- **superseded:** a judgement replaced in the active view by a newer one that names it in `supersedes`.
- **held / quarantined:** excluded from the active view pending review (ambiguous prompt, unresolved reference, systematic defect); a hold never falls back to a superseded positive. "Held" is used only in this quarantine sense, never for pairs already counted.
- **source lineage:** all prompts derived from the same original source: the same forum post, the same seed (for generator 0.1, the same template instance), together with their renderings, translations, prompt versions, dialogue continuations and branches. Source lineage controls split assignment (a lineage stays within one split) and duplicate-alias grouping (historical IDs of the same prompt resolve to one logical prompt through aliases, §5.7). The field `source_family` in existing registry and dialogue v2 records carries the source lineage.
- **task family:** prompts that share an underlying task, scenario or mathematical structure, across different sources (for example two forum posts and a seed that all ask for the same kind of VAT calculation). Task family controls coverage caps (reuse is allowed up to the cap; it is not a ban on problems that share an operation) and near-duplicate screening (§5.5). It does not decide splits.
- **deduplication:** generated task instances are deduplicated by the instance key (§5.7) plus similarity screening of the realised prompts; similarity scores nominate candidates, a review decides.
- **trajectory:** one recorded conversation; prefixes from the same trajectory are correlated and capped per trajectory.
- **development_demo:** rows with `purpose=development_demo`, `training_eligible=false`, `experiment_credit=0`; never imported into a training pool.
- **provenance fields:** four separate fields, each from a closed list, recorded on every row (definitions of 0.1–0.3 in `CURRENT_VERSIONS.md` §0):
  - **`generator_version`** ∈ {`0.1` (template-fixture generator; defunct, archival only), `0.2-prototype` (generator 0.2 before its release: the round 2 seed script, and the forum gate v3 selections of rounds 1 and 2), `0.2` (generator 0.2 release), `0.3` (0.2 plus dialogue; dialogue rows, pilot included)}. New rows record `0.2` or `0.3`; `0.1` and `0.2-prototype` appear only on archival imports.
  - **`source_route`** ∈ {`forum-gate-v3` (a preserved forum request through forum gate v3), `seeded` (written by Sol from a seed; generator 0.1 template fixtures are seeded rows with `generator_version=0.1`), `dialogue` (a recorded conversation)}.
  - **`dialogue_protocol_version`** ∈ {`none` (single-turn rows), `dialogue-quality-depth-v1` (the dialogue pilot), `dialogue-v2`}.
  - **`opening_generator_version`**: for dialogue rows, the generator version that produced the opening (same list as `generator_version`); `none` for single-turn rows.
  A row is non-keepable when `generator_version` or `opening_generator_version` is `0.1` (decision 11). Combined values found in older code map onto the fields: registry and inventory values such as `dialogue-quality-depth-v1 (0.1 seeds)` or `dialogue-quality-depth-v1 (0.1 fixtures)` → `dialogue_protocol_version=dialogue-quality-depth-v1` + `opening_generator_version=0.1` (with `source_route=dialogue`, `generator_version=0.3`); the older single value `forum-gate-v3` → `source_route=forum-gate-v3` (with `generator_version=0.2-prototype` for rounds 1–2).

### 5.5 Distribution, inventory and fill terms [PG]
- **target distribution:** the agreed shares per primary purpose (dialogue 35, everyday 25, instruction 15, factual 10, safety 10, maths 5) and per language (Greek 70, English 20, French, German, Spanish, Italian, Portuguese 2 each), counted in accepted pairs; recorded in `data/rlhf/target_distribution_v1.json`.
- **inventory:** one record per existing prompt or dialogue (`data/rlhf/pool/inventory.jsonl`, built by `data/rlhf/inventory.py`): round, source kind, generator version, defunct flag, exclusion, primary purpose, task type, language, forum, detail, register, attitude, words, replies, pair state, maths flags, prompt hash. It is the register of the pre-existing distribution.
- **source kind:** the registry and inventory column: forum (a preserved natural request through the forum gate), seeded (written by Sol from a seed), dialogue (a recorded conversation), template (generator 0.1 fixtures, defunct). In the import contract it is recorded as `source_route` (§5.4): forum → `forum-gate-v3`, seeded → `seeded`, dialogue → `dialogue`, template → `seeded` with `generator_version=0.1`. Codex's "source route" names map onto these.
- **keepable:** an inventory record not produced by a defunct generator and not excluded; only keepable records count towards the target.
- **deficit:** target accepted pairs in a cell, T[c] (at the approved first-run size), minus the validated eligible active pair credit E[c] in that cell (ledger E, §5.7); new generation fills deficits, never raw-prompt gaps. The forecast deficit additionally subtracts y[c] × A[c] (ingestion plan §4).
- **fill:** generating new prompts for a cell in proportion to its deficit divided by the cell's measured accepted-pair yield.
- **prompt version:** a new version whenever a prompt's wording changes (clarification, correction); a new version needs fresh replies and never inherits the old judgements.
- **forum weights:** per-forum caps on the share of forum prompts (astrovox ≤ 3 %).
- **near-duplicate:** two prompts whose content overlaps above the screening threshold (round 2 used word-set overlap above 0.6); screening nominates pairs within each task family and across the whole set, and only one prompt of a confirmed near-duplicate group is kept.
- **decontamination:** removal of prompts that overlap the evaluation benchmarks (the SFT decontamination against the eval caches).

### 5.6 Reply and judging terms [RLHF]
- **candidate:** one sampled reply to a prompt or prefix; **original** is the reply recorded in a dialogue trajectory, **fresh** is sampled later; **resample** is an escalation batch (4 → 32).
- **prefix hash:** sha256 of the serialised conversation before the reply; chosen and rejected must share it.
- **verified reference:** the basis for verifying a maths response (contents in §4.5 T5: assumptions and interpretation, acceptable result or conclusion, verified argument where needed, checks, completeness requirements), established independently of any candidate (maths plan §A2), with status verified, ambiguous or unresolved. It is never text a response must imitate.
- **maths content:** the indicator (§4.5 T5) that a prompt or turn contains mathematics requiring verification, whatever its primary purpose: maths prompts, forum calculation and mathematica posts, budgets or arithmetic inside planning, and mathematical claims inside dialogues. It does not change the primary purpose; all maths content is judged by the specialist maths judge, including all pre-existing items.
- **maths judgement fields** (outcome, reasoning, task_completion, requested_explanation, errors, eligible_positive): defined in `MATH_JUDGING_EXECUTION_PLAN_20260917.md` §A3.
- **hint:** a helpful user intervention; in move terms M2 point_to_defect, M3 give_example, M4 decompose or M5 add_context. A pair never mixes a reply before a hint with one after it.
- **development/production status:** development rows (development_demo, §5.4) never enter training; production rows may, if eligible.

### 5.7 Identity, registry and planning terms [PG] (from PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md §2–§4)
- **task instance:** the actual task: content, givens, entities, operations, constraints and intended answer conditions. Reuse of the same instance is rejected even when persona, language, attitude, ID or generator version change.
- **rendering:** a task instance plus a language and a requested user texture (register, attitude, detail); planned multilingual renderings stay in one source lineage and one task family and are not new semantic coverage.
- **realised prompt:** the complete user-visible input or prefix, as sent to the model.
- **canonical key:** a hash of normalised content that excludes arbitrary IDs, timestamps, RNG seeds, generator versions and decorative persona details, and preserves numbers, units, negations, operations and constraints. **instance key** = canonical key of the task instance; **rendering key** = instance key plus language and texture.
- **alias:** a historical ID that points to a stable logical prompt ID; duplicates are merged through aliases without deleting samples or judgement history.
- **seed status:** bound (the exact generation input is recovered), unknown (not recoverable; never invented afterwards), unselected (generated but not used).
- **reservation:** an atomic claim on an instance key and rendering key before a generation call, with status pending, completed or rejected and an explicit retry lineage; two workers cannot reserve the same key.
- **compatibility rules:** label combinations rejected before generation (for example Greeklish with any language other than Greek).
- **ledgers:** three separate counts per cell: **A** reviewed unused prompts available; **E** validated eligible active pair credit, E[c] (active, deduplicated, one pair per single-turn prompt, held and superseded judgements excluded); **y** forecast eligible pairs per newly processed prompt (measured, or a provisional pooled prior with a range). A and E never count the same prompt.
- **frontier:** the achievable per-cell coverage for candidate first-run sizes N under a fixed budget of new requests, reported as expected and conservative coverage.

## 6. Rules for how definitions enter prompts [shared]
1. Every prompt that sends a label sends its definition: a glossary block with only the values that occur in that call, copied verbatim from the companion file, in English.
2. The glossary file is versioned; its sha16 is recorded with every call, like the rubric's.
3. Code ids (`if_composite`, `f_premise`) are never sent alone: send the family's human label and its one-line description, or nothing.
4. A label that the content already realises (difficulty in template fixtures) is either sent with its definition or not sent.
5. Reviewers and gates that report an observed label use the same glossary as the writer.
6. Labels never appear in the user-visible text (existing rule).
7. New values (like `anxious`) enter the glossary before they enter a seed.
8. Every exported row records the glossary version (sha16) it was produced under, alongside generator, rubric and user-policy versions.

## 7. Decisions (resolved 17 Sept by the orchestrator's recorded defaults, at the owner's go; the owner may override any of them)
1. `anxious` (A5) stays a defined attitude. Round 3 draws attitudes with the agreed weights (cooperative 70, frustrated 10, skeptical 15, playful 5), so `anxious` is not drawn; round 2's 31 anxious prompts keep their label.
2. Greeklish stays a register value, Greek-language only; the combination with any other language is rejected before generation.
3. Splitting interaction `uncertainty` is deferred to the dialogue track (single-turn generation does not use interactions).
4. Difficulty stays on seeded prompts with its definition and the agreed weights (routine 30, compositional 50, challenging 20); the seed carries the concrete content that realises it, and the reviewer checks it.
5. Forum task_type mapping: question, explanation → factual; calculation → math (corrected at review R-PG1: a centrally mathematical calculation is maths by §4.5 T5); advice, opinion, share, translation, other → everyday; `create` (a request to produce something) is added and maps to everyday.
6. Generators 0.2 and 0.3 use this glossary as their only label source.
7. Codex's user-surface / source-route split is adopted through `source kind` (§5.5), recorded as `source_route` in the import contract (§5.4); the four extra interactions are deferred to the dialogue track.
8. Adaptive user moves (the adopted list M1–M12), turn metadata, assistance levels and user-state attributes are adopted as defined. The move-selection rule — the deterministic transition/priority table from visible event and user state to exactly one move, with its tie-breaks and terminal cases — is not defined in this spec: it is owned by the dialogue workstream (`DIALOGUE_V2_EXECUTION_PLAN_20260917.md` §4, Stage B1 adaptive user implementation, deliverable "user-state schema and transition logic") and is frozen there at review R-PG6. It does not block single-turn generation (generator 0.2 uses no user moves). Until R-PG6 no probabilistic mixture is targeted; the realised mixture is recorded, not steered.
9. The dialogue terms (§4.8) and dataset terms (§5.4) are adopted.
10. Bare and terse stay distinct with hard ceilings: bare at most 12 words, terse at most 30 words; the realised-length check enforces them.
11. Rows from generator 0.1 are imported for provenance and collision checking only and are non-keepable (no pair credit), including the 28 pilot dialogues built on 0.1 seeds.

## 8. Change log
- v1.0.3 (17 Sept 2026): review R-PG1 cycle 2 fixes, applied without a third review cycle (owner rule): move-selection rule assigned to the dialogue workstream and frozen at R-PG6 (decision 8, §4.7); cell = primary purpose × language, 42 cells, `task_type` reserved for forum F1–F9 analysis (§4.5, §5.4); deficit subtracts validated eligible active pair credit E[c], "held" only for quarantine (§5.4, §5.5, §5.7); turn metadata fixed to `move`, `new_information`, `trigger`, `changes_task` (§4.7); provenance split into `generator_version`, `source_route`, `dialogue_protocol_version`, `opening_generator_version` (§5.4, §5.5); source lineage and task family separated, deduplication by instance key plus similarity screening (§5.4, §5.5, §5.7); exclusive forum task_type precedence with boundary examples (§5.1); status lines, `anxious` "defined, not drawn" and §4 and §5 headings made consistent; detail excludes values that define the task (§4.6); term manifest `docs/RLHF_COORDINATION/reviews/R-PG1_term_manifest_v1.0.3.md`.
- v0.1 (17 Sept 2026): first draft; audit of four pipelines; definitions for attitude, register, difficulty, interaction, task, detail, forum task_type, premise status, safety context.
- v1.0.1 (17 Sept 2026): review R-PG1 cycle 1 fixes: forum calculation → math; serious error defined (§4.8); interim adaptive-user default (decision 8); closed list of generator versions (§5.4); safety decision order (§5.3); generic difficulty definitions authoritative (§4.3); detail ceilings and pasted material reconciled (§4.6); `anxious` status aligned in the glossary.
- v1.0 (17 Sept 2026): frozen; identity, registry and planning terms from the ingestion plan added (§5.7); decisions 1–11 resolved by recorded defaults (§7); bare ≤ 12 words and terse ≤ 30 words (§4.6); forum task_type `create` added (§5.1).
- v0.5 (17 Sept 2026): owner's maths definition replaces "one verifiable answer that deserves a worked solution": seven maths kinds, reference as a basis for verification, correctness separate from explanation length, the maths content indicator inside other purposes, and the ambiguity flag (§4.5 T5); verified reference and maths content aligned (§5.6); seeded maths task values noted for replacement (§3.2); glossary synced to v0.5.
- v0.4 (17 Sept 2026): aspect tags [PG]/[RLHF]/[shared]; T6 dialogue and primary purpose, task family, task type (§4.5); detail defined by content with realised word counts and the bare/terse finding, and length terms separated (§4.6); distribution, inventory and fill terms (§5.5); reply and judging terms (§5.6); decisions 10–11.
- v0.3 (17 Sept 2026): widened to the terms of the two-stream execution plan: user moves M10–M12 and turn metadata (§4.7), dialogue terms (§4.8), dataset and eligibility terms (§5.4), rule 8, decision 9; retitled.
- v0.2 (17 Sept 2026): confirmed prompt-generator-0.1 is the latest release; added Codex's pre-release design notes (§3.4), the extra interactions they list, and the owner-agreed adaptive user model from OPUS_FEEDBACK_20260917.md (§4.7); decisions 7–8.
