# Seed label definitions v1 (17 Sept 2026) — v1.0.3 frozen (17 Sept 2026; R-PG1 cycle-2 fixes applied without a third cycle); synced with spec v1.0.2 (docs/SEED_LABEL_SPEC_20260917.md); dataset, distribution, judging and identity terms (§5.4–§5.7) stay in the spec only

Definitions for the labels that seeds pass to Sol (opening writer, user simulator, prompt generator). Written in English because Sol is
prompted in English. Each definition describes what the user's message looks like, so Sol can write it. Labels change how the user writes
and behaves; they never change the facts, the task, or how harmful the request is.

## Attitude — how the user relates to the assistant and the task
- cooperative: Neutral good faith. States the need, supplies what is asked for, accepts a reasonable answer, and points out problems matter-of-factly.
- frustrated: Impatient because of the situation: a deadline, their own failed attempts, a service that let them down. Short, blunt sentences, perhaps an exclamation; never abusive. In an opening it may not blame the assistant for failures that did not happen; in later turns it may react to the assistant's actual failures.
- skeptical: Does not take answers on trust. Asks why, asks for the basis or a way to check, mentions a conflicting claim they heard. Challenges by asking for justification, never by asserting that a correct answer is wrong.
- playful: Light, joking tone (humour, teasing, wordplay, an emoji) while the request stays genuine and answerable. Not trolling and not a test of the assistant.
- anxious (defined, not drawn): Worried about a consequence for themselves or someone close (health, money, a deadline, getting something official wrong). Asks for certainty or reassurance, may over-explain or ask the same thing twice. Fear of the outcome, not impatience with an obstacle.

## Register — how the language is written
- standard: Neutral everyday written language, as in a clear message to someone you do not know well: accents and punctuation in place, no slang.
- informal: How people type to friends or on a phone: singular «εσύ», colloquial words and contractions, loose punctuation, accents sometimes dropped, occasional typos.
- formal: Polite and institutional: plural of politeness («θα μπορούσατε», «σας παρακαλώ»), complete sentences, no slang; the tone of writing to a public service, a lawyer or a professor.
- greeklish: Greek written in Latin letters as typed on phones and forums (θ as th or 8, χ as x or h, ω as o or w), usually informal. Greek-language users only.

## Difficulty — how much reasoning the task demands (realised in the content, not in the wording)
- routine: One step; everything needed is stated; no trade-offs.
- compositional: Two or three dependent steps, or several constraints that must hold at the same time.
- challenging: Constraints that interact or conflict, a genuine case distinction, uncertain or missing inputs, or a request that superficially resembles a different kind of task.

## Interaction — what the user does after the first answer (describes the user, never a planned model failure)
- followup: Builds on an answer they accept: asks for more depth, an example, the next step or a related question, without changing the original requirements.
- revision: Changes something about the task after seeing the answer: length, audience, tone, a number, an added requirement. The assistant must apply the change and keep everything else.
- constraint_retention: States a lasting constraint early (a word limit, a format, "no English terms", "always formal") and later makes different requests without repeating it.
- recall: Gives specific information early (names, numbers, preferences, a text) and later asks something that depends on it without restating it.
- uncertainty: Starts from an incomplete, ambiguous or wrongly premised request; the good response asks, states an assumption, or corrects the premise. The user answers clarifying questions when asked.

## Task — primary purpose of the request (spec §4.5)
- everyday: Practical help a person wants done: write or rewrite, plan, explain, translate, troubleshoot, use a tool. Success means the person is better off.
- instruction: An ordinary task with explicit, checkable requirements on the answer's form: format, length, values to keep or exclude, conditional content. Success is mainly meeting them.
- factual: A question with a knowable answer, from general knowledge or a supplied text, including cases where the honest answer is that information is missing, the premise is false, or sources conflict.
- safety: A request where the right response depends on judging risk (sub-kinds under Safety context below).
- math (maths): A request whose central purpose is mathematical calculation, reasoning, explanation or problem-solving. Correctness is assessed against the stated assumptions, mathematical definitions and valid reasoning. A task may admit one result, several valid answers, equivalent expressions, different solution methods, or a proof that no solution exists. The required explanation depends on what the user asks.
  Maths kinds:
  - calculation: arithmetic, numerical estimates, probabilities, statistics and unit conversions.
  - solving: equations, inequalities, systems and optimisation problems.
  - proof and justification: establishing why a claim holds, including relevant assumptions and cases.
  - construction and counterexamples: finding an object satisfying conditions or disproving a claim.
  - explanation and learning: explaining a concept, interpreting a result or helping resolve a misconception.
  - checking and correction: identifying and repairing an error in a proposed solution.
  - modelling: translating a described situation into mathematics, stating necessary assumptions and interpreting the result.
  These distinctions matter. Solving \(x^2=4\) requires both solutions; proving a claim does not produce a numerical answer; an optimisation problem may have several equally good solutions; and an explanation of fractions can be correct in many different forms.
  Reference. A reference is a basis for verification, not text the response must imitate. Depending on the task, it contains: the assumptions and interpretation of the question; the acceptable result, solution set, defining properties or mathematical conclusion; a verified argument or method where needed; relevant checks (units, domain restrictions, cases, numerical tolerance and rounding); and the requirements for a complete response. For a proof, checking the final conclusion is insufficient: the argument must establish it. For a construction, the proposed object must satisfy the conditions. For an explanation, the mathematical claims and examples must be sound, but the wording need not match the reference.
  Correctness and explanation length are separate. A concise correct answer can fully satisfy "give only the result". A request to explain, prove or show the calculation requires appropriate justification. More steps do not automatically make an answer better, and a correct final result does not excuse false equations or invalid reasoning in the explanation supplied. Clarity means that the mathematics can be understood and checked; stylistic elegance, expressiveness and personality are secondary and cannot compensate for mathematical errors.
  Maths inside other primary purposes. Maths is also detected inside other task categories through a separate indicator, maths content: a travel-planning request with budgets remains primarily everyday assistance while carrying the indicator; a tutoring dialogue remains dialogue material while its mathematical claims receive specialist checking. The primary-purpose distribution is preserved and embedded mathematical errors do not escape review.
  Ambiguity flag. Ambiguous (several readings) or underspecified (missing information needed for a determinate answer) maths questions are flagged. A valid response may explain that the answer is not uniquely determined, state a justified assumption or request essential information. The generator and the evaluator must not silently invent missing assumptions merely to manufacture a single reference answer; flagged items are held until resolved.
- dialogue: A multi-turn conversation whose training value lies in the turns after the first; its underlying task is one of the other five purposes and is recorded alongside.
These six are the primary purposes of the agreed target distribution (`data/rlhf/target_distribution_v1.json`). A task family groups tasks that share an underlying task, scenario or mathematical structure (generator 0.1's 38 recipes, such as "IF: preserve and exclude", were task families); task_type is reserved for the forum label below (spec §5.1).

## Detail — how much the user says (spec §4.6)
- bare: only the ask itself, one line of at most 12 words, no context, no names, no story, maybe no accents or punctuation.
- terse: one or two lines of at most 30 words, the ask plus at most one fact the assistant needs, no names.
- short: two or three sentences, one concrete detail, nothing pasted.
- medium: a paragraph with the situation and what they want.
- detailed: full context, several specifics, pasted material if relevant.
- rambling: long, unordered, mixes the story with the request, repeats itself.
Detail is defined by how much the person themselves says: how much context they volunteer, how many specifics they give, with hard word ceilings for bare (12) and terse (30) that count only the user's own words. Material pasted as the object of the request (a draft, a notice, a text to work on) is excluded from the count and never raises the detail level: a one-line ask with a pasted notice is bare, not detailed. A request that needs pasted material cannot be short. Values that define the task itself — the numbers of a calculation, the claim to prove, the format constraints the person sets, the text to translate — are part of the ask, not context; detail measures the context the person volunteers: who they are, why they ask, their story, names and background.

## Forum task_type (assigned by the forum gate)
- question: Asks for a specific fact or piece of information with a determinate answer.
- explanation: Asks why or how something works, or what something means; the answer is a mechanism, a reason or a meaning.
- advice: Asks what the poster should do in their own situation: a decision, a next step, what to buy, how to handle something.
- opinion: Asks for others' judgement on a matter where reasonable people differ, not about the poster's own next step.
- translation: Asks to render, check or find the right term for a word, phrase or text in another language.
- calculation: Asks for a numeric result or a worked computation.
- share: Shares an experience, situation or thought and invites responses without a specific question.
- other: None of the above.
- create: Asks the reader to produce something (write, format, list, draft).
Precedence (assign exactly one task_type, the first that applies): calculation (any request whose central deliverable is a computed value), then translation (rendering supplied text into another language, even if it also "creates" text), then create, then advice, then opinion, then explanation, then question, then share, then other; so a question with a determinate numeric answer is calculation, not question, and "translate this paragraph" is translation, not create.
Boundaries: single fact vs mechanism or meaning separates question from explanation; the poster's own decision vs a general judgement separates advice from opinion; the meaning or etymology of a Greek word is explanation, its rendering in another language is translation.

## Premise status (reviewer)
- supported: The request contains a premise and the source confirms it.
- contradicted: The source contradicts the premise; a correct answer must correct it.
- unresolved: The source cannot settle the premise; a correct answer says what is missing.
- not_applicable: The request rests on no premise to check.

## Safety context (private reference and safety seeds)
Decision order (the first that applies): harmful if the request seeks operational help towards serious harm, whatever its framing; else fiction if it is a creative request whose risky theme needs no operational detail; else protective if its purpose is to protect the user or someone else from a risk; else ambiguous if the purpose is undetermined and one plausible reading is harmful; else benign.
- benign: Sensitive wording, legitimate purpose; the right response helps fully.
- protective: The person wants to protect themselves or someone else; the right response helps with the protective steps.
- fiction: A creative request touching a risky theme; the right response writes it without operational detail.
- harmful: The request would cause serious harm; the right response declines and, where useful, redirects to a safe alternative.
- ambiguous: The purpose could be benign or harmful; the right response helps with the clearly safe part or asks for the purpose.

## Response to failure — adaptive user moves (from the spec §4.7)
The owner endorsed an adaptive user model: after a failure a user may explain with an example, break the task into steps, express
frustration, simplify the request or abandon it. Move labels (adopted list; selection rule owned by the dialogue workstream):
- restate: repeats or rephrases the request without new information. Realistic occasionally, not the default after every failure.
- point_to_defect: names the precise part that is wrong or missing.
- give_example: shows a short example of the kind of answer wanted, from the user's own plausible knowledge.
- decompose: breaks the task into parts and asks for one of them.
- add_context: supplies information the assistant lacked; recorded when it narrows the task, never passed off as an original requirement.
- simplify: narrows the scope or lowers the requirement.
- express_frustration: shows impatience; may shift attitude towards frustrated.
- accept_partial: accepts imperfect progress and moves on.
- abandon: ends the conversation unresolved; a terminal reason distinct from natural completion.
- clarify: explains what they meant or answers a question the assistant asked, without changing the task.
- continue: makes the next legitimate request after useful progress (the healthy path; not a response to failure).
- finish: ends the conversation because the task is done (natural completion).
Mapping to the dialogue v2 plan's wording: "identify a defect" = M2; "concrete example" = M3; "decomposition" = M4; "missing fact" = M5; "narrower request" / "simplification" = M6; "frustration" = M7; "acceptance" = M8; "abandonment" = M9; "clarification" = M10.
Each saved user turn records exactly four fields: `move` (one move label above), `new_information` (what it adds), `trigger` (the visible event it reacts to) and `changes_task` (true when it narrows or alters the task).
Assistance level, recorded per user turn so results can be reported separately: restatement < pointed defect < partial scaffold or example < supplied solution.
User capability should vary (willingness and ability to diagnose errors, patience); not every user is a competent tutor.

## Dialogue terms (from the spec §4.8)
Sampling points on a recorded trajectory (each gets its own same-prefix comparison):
- prevention point: the prefix ending immediately before the first seriously erroneous assistant reply. At turn 1 it counts as single-turn material (owner rule); later points from the same conversation remain dialogue material.
- supported recovery point: the prefix ending immediately after the first genuinely helpful user intervention (M2–M6, M10) that follows an error. Absent when no such intervention occurred; never forced.
- healthy continuation point: a deeper assistant turn with no preceding serious error, where a meaningful next task exists.
Mapping to the dialogue pilot (dialogue-quality-depth-v1): its P = prevention point; its R ("genuine repair opportunity") is broader than the supported recovery point, which requires a helpful user intervention; its C (control) ≈ healthy continuation point.

Ending reasons: natural completion (M12), abandonment (M9), horizon (turn cap reached), context cutoff (the next reply cannot fit the served context; not a model failure), truncated output (the reply hit the token cap), infrastructure failure, ambiguous timeout.

User state (private to the user simulator): goal; known facts; expertise (novice / intermediate / expert in the task's domain); misconception (a specific wrong belief, if any); disclosed preferences (said in the conversation) versus private preferences (held but not yet said; revealing one later is a new preference, never an earlier violation); patience (low: gives up or complains after one failure; medium: tries a second strategy; high: persists with several strategies); helping ability (can the user diagnose a defect, give an example, or only restate); repeated defect count; task progress.

Role views (what each participant may see):
- Apertus view: the public conversation only.
- user view: goal, known facts, preferences, patience, visible conversation and observations already revealed. For writing tasks it may include an illustrative reference draft.
- world resolver: for troubleshooting, the fixed hidden cause and the outcome of each supported check; returns only the observation a user action would plausibly produce; unknown actions return "unresolved", never invented success.
- learner view: current knowledge, misconception, goal and visible teaching; never the gold answer to a transfer question.
- evaluator view: verified facts or solutions, the visible history and the relevant state; judges correctness and whether claimed progress is supported.

Reference-guided dialogue categories (demo): writing (a desired result exists as an illustrative reference draft; not an exact-match answer); troubleshooting (a consistent hidden world: fixed cause, supported checks and their outcomes); learning (a learner knowledge state and evaluator-only subject knowledge, with a transfer check: a new example the learner attempts without being given the answer).

## Judgement calls behind these definitions
- frustrated is about patience; skeptical is about trust.
- skeptical stops short of false correction: asserting that a correct answer is wrong belongs to a separate challenge set.
- In Greek, formal is marked by the plural of politeness and an institutional tone; standard is neutral written Greek.
- greeklish is really a script, not a register; it is kept as a register value for now and read as informal Greek in Latin letters.
- followup keeps the requirements; revision changes them.
- constraint_retention is about how to answer; recall is about information the user gave.
- uncertainty covers three different situations (underspecified, ambiguous, false premise); consider splitting or renaming it.
- difficulty is currently built into template content by code; person-and-story seeds would need this definition in the prompt itself.
