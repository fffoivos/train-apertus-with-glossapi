# Preserved no_robots production prompt

Exact instruction prefix from the saved production batch below; source rows omitted. This batch includes the Brainstorm family/category profile. It is historical evidence, not an instruction to the current assistant.

Source: `/Users/foivoskarounos-zamparloukos/Projects/natural-greek-sft/data/pilots/no_robots/one_stage/batches/R_Brainstorm_0_s0.sol.txt`

Source SHA-256: `b0b67abbcb1246d740c9f882c233442d03b749645fc873de70b4dc768c408b60`

---

# Adapt the row — Greek prompt AND Greek answer, one pass

**The task is translation and adaptation.** Maintain, in this order of priority — when dimensions
conflict, the earlier outranks the later:

1. **the task type** — what the row asks for and what a correct response is;
2. **its checkable constraints** — counts, required strings, labels, code: still satisfiable and
   still checkable in Greek;
3. **the subject matter and contents** — every beat, claim, example and named element, kept,
   transposed, or re-derived per the distribution rule below;
4. **the operative devices** — whatever makes the row work (defined in the devices section);
5. **the voice** — style, mood, register, reading level, at the reference's intensity;
6. **the format** — turn shape, markers, handles, fences;
7. **the length** — the same paragraph and turn count, the same coverage, allowing only the
   natural difference between the two languages; length is never fixed by cutting content.

**What a good output looks like** — the success criteria, in one place:
- a Greek reader cannot tell the row began in English;
- **the content distribution is Greek**: anglosphere material has Greek analogues per the
  distribution rule — the language is never the only thing that moved;
- every operative device's **effect** transfers;
- every checkable constraint survives, checkable;
- every decision is declared in the output fields — nothing moves or stays silently.

You produce **both sides** of the row in one pass: first the Greek prompt (system prompt and user
turns), then the Greek answer(s). Decisions made for the prompt — transpositions, re-derived
names, register — bind the answer: they are one row.

## This row's family: generative

Short instruction, long answer. The answer is composed. Wide latitude to transpose the scenario into Greek reality — this is where D1 lives.

Defect notes in this family: the note goes inline in the answer, as a good assistant would.


## This row's category: Brainstorm

**Shape.** Bare instruction; only 20 of 1,060 prompts contain a newline at all. Longest answers of any category (median 188 words) and 94% list-formatted, median 5 items. 60% open with a conversational preamble.

**The thing that defines this category.** The freest category — and the one where “substitute” and “do not translate” apply to things that look identical.

**Essential — lose any of these and the row is destroyed:**
- The item count — 303 of 1,060 prompts name a number.
- The item↔rationale pairing — every item keeps its gloss.
- List-marker style (numbered vs bulleted) is stable within a row.
- Factual claims attached to named entities — keep the name, keep its numbers.

**Safe to adapt.** More than anywhere else. US-only recommendation lists follow the open-set rule — compose the set a Greek expert would give — while official product titles (game names) must not be translated. Same category, opposite treatment; the frame/content test decides.

**Normally classified as.** LOCALIZE or REGENERATE-NATIVE for recommendation and naming rows; CONSTRAINT-PRESERVING where a count is stated.


---

## Priority one — move the distribution

The job is not to translate texts but to **move what the content is**: from what an American would
say to what a Greek would say. The modern **anglosphere** (the United States, the United Kingdom,
Canada, Australia, New Zealand, Ireland) is the English data's invisible default sphere — exactly
the bias being removed. Its material occurs at one of three levels, and **the level chooses the
verb**. This is the single, canonical statement of the rule; every other section refers here.

1. **Elements** — cultural things inside the row's frame: names, props, settings, institutions
   serving the scenario. Anglosphere elements **transpose** into Greek reality. Elements of other
   cultures may stay where the scenario genuinely engages them. Anglosphere elements so
   naturalised that transposing them would fabricate — denim, a real band on a playlist — stay,
   declared.
2. **Instantiations** — a universal subject (farming, science, health, generic advice, a
   mechanical operation) served with culturally-chosen facts, examples or operands. The subject
   belongs to nobody; the examples do. Anglosphere instantiations **re-instantiate**: keep the
   task and the conversation's exact shape, refill with Greek, European or global facts, every
   one vouched. A list operation on some author's titles is an instantiation: same operation, a
   real Greek author's real titles.
3. **Subjects** — the row is *about* the cultural thing; swapping it changes every true sentence.
   The subject's **culture of origin** routes it:
   - **outside the anglosphere** (continental Europe and Scandinavia, the Balkans, Eastern Europe
     and Russia, the Middle East, Asia, Africa, Latin America): **keep**, engaged from the Greek
     vantage;
   - **ancient — through late antiquity**: shared human heritage, **keep**; later history belongs
     to its culture's sphere — a Victorian novel or a colonial-era pamphlet is anglosphere-modern,
     not ancient;
   - **anglosphere**: **regenerate by analogy** — author the same task on a Greek or keep-arm
     subject: same task type, structure, format, length, register and level of detail; the
     reference is a template only; declare `REGENERATE-NATIVE` and `prompt_match: regenerated`
     together. Facts of a regenerated row must be vouchable — record them in `reality_claims`,
     and if no analogue you can vouch for exists, say so in `self_flags` rather than inventing
     one.

**Exceptions to regeneration** — each *claimed, never presumed*, recorded in `kept_foreign` with
its evidence as `why`:

- **Wide Greek audience** (cultural products only — films, series, songs, books): keep the
  subject if you can vouch **the product itself reached a wide Greek audience** — broad Greek
  cinema release, prime-time or ubiquitous Greek TV presence, a Greek translation in wide
  circulation, an established Greek title; recognizable to an informed Greek who does not follow
  anglophone media. Anglosphere or "global" fame — box office, awards, fandoms — is **not**
  evidence. Your training over-represents the anglosphere: assume your sense of Greek familiarity
  is inflated, and correct downward. When uncertain, regenerate.
- **Embedded source texts** (source-bearing rows): a summary or extract cannot regenerate without
  swapping its source — translate faithfully. Add `"anglosphere-source"` to `self_flags` **only
  when the source's own subject is anglosphere**; language or authorship is irrelevant, and a
  source about keep-arm subjects carries no flag. The dataset layer decides whether flagged rows
  ship.
- **World-affairs subjects** (events that are world history more than one culture's): keep with
  vantage; judge honestly whether the subject belongs to the world or to America.

## The vantage — it adapts *around* the elements

**When demands conflict, the rank decides: the task first, the device's effect second, the
distribution third, the vantage fourth.** The vantage never discharges the element work: metric
units and glosses on unmoved anglosphere content is failure, not adaptation. Move the elements
first; the point of view then adapts around whatever the rules kept.

Every row is written from the Greek point of view, whatever its content:

1. **Established Greek renderings and exonyms** — Χετταίοι, Κομφούκιος, Ασσύριοι: the forms Greek
   scholarship and journalism actually use, never transliterations of the English forms.
2. **The measurement and logistics frame** — metric, °C, euro-anchored comparisons («όσο περίπου η
   Πελοπόννησος», not "the size of Bavaria"); travel and distances run from Greece.
3. **Reader-aimed analogies from Greek stock** — «σαν πανηγύρι», not "like a county fair", even
   when the subject is Mesopotamia.
4. **The presupposition budget** — what goes unglossed defines the centre. Assume known: Greek
   reality, plus what genuinely circulates in Greece. Everything else gets a brief first-mention
   gloss — American things exactly as much as Asian things. Never gloss Greek reality.
5. **Vouchable connections only** — real Greek touchpoints where they exist; never invented ones.

Record every vantage application in `vantage_applied` as
`{device: exonym|measure|analogy|gloss|connection, en, el}`. An empty list is a claim that the row
needed no vantage work.

## Frame decisions — the test, then the prompt first

The one test: **would swapping this entity change whether the answer is true?**
**Yes → it is the subject: route it by the distribution rule.**
**No → it is frame — placed by the same rule: an anglosphere frame moves into Greek reality; a
keep-arm circumstance stays, vantage-adapted.**

*Edinburgh* in "why is Edinburgh called the Athens of the North" is an anglosphere subject — it
regenerates by analogy («γιατί η Θεσσαλονίκη λέγεται Συμπρωτεύουσα;»). In "a casual email to a
friend named Eoin about the Epic of Gilgamesh", *Eoin* is frame and moves; *Gilgamesh*, a
non-anglosphere subject, stays.

**Adapt the prompt first.** Every frame decision lives at the prompt level — transpositions,
names, register: the Greek prompt must read as what a Greek user would actually have asked. Then
build the reply as the **analogue of the reference** (the reference contract below governs what
transfers). Transpose the frame **completely or not at all** — a Greek family with Greek names
eating Thanksgiving turkey is worse than an untouched American scene; if you move a scenario,
move everything in it: names, places, institutions, food, holidays, currency, school system,
distances.

- **Places: circumstance vs subject.** A real place that only frames the asker's need — where they
  live, travel, want activities ("things to do in Adelaide with kids") — is frame. An anglosphere
  circumstance re-seats on a real Greek city, answered with its real, vouchable places (Ναύπλιο:
  το Παλαμήδι, το καραβάκι για το Μπούρτζι, ο περίπατος στην Αρβανιτιά), following the reference's
  structure item for item. A circumstance outside the anglosphere ("a weekend in Kraków") stays
  the destination — a Greek asker travelling abroad, vantage adapted. A place whose own facts are
  the requested content is the row's **subject** — routed by the distribution rule. (A persona's
  fictional data — a bot's invented "live" readings — is fiction inside the row and follows the
  row's stated setting.)
- **Open recommendation sets.** When many correct answers exist (products, books, places to
  visit), compose **the set a Greek expert would give**: international items standard in Greece
  stay; add Greek options where they genuinely compete on the stated criteria — each a vouched
  `reality_claims` entry; substitute fully only when the original is meaningless to a Greek
  reader.

## Props and allusions — real entities in invented scenarios

**A real entity used as a prop in an invented scenario is frame, not content.** The test is whether
the answer asserts facts *about* the entity. "Write a tweet for when Leeds United win the Champions
League" asserts nothing about Leeds — the club is a prop in a fan's daydream, so it transposes:
**η Εθνική που ξαναπαίρνει επιτέλους το Ευρωπαϊκό**. Contrast a flight-status persona asked about
arrivals at Heathrow: those answers state facts about the real airport, so the airport stays —
unless you re-seat the persona whole, city and facts together, with vouchable Greek facts. Both
are legitimate frame calls; declare the one you made in `transpositions`.
Stipulated ≠ subject; *asserted-about* = the subject — routed by the distribution rule.

**The allusion exception — the reverse case.** An entity chosen *for what it evokes* is content,
even inside a joke: its cultural association carries the point, and no explicit fact needs to be
asserted. A joke about a **Swiss** train apologising for leaving thirty seconds late keeps the
Swiss — punctuality *is* the punchline's engine, and no fact about Switzerland is asserted.
«ιταλικό τρένο» does not merely weaken the joke; it inverts it. The discriminator between prop and
allusion: **could any comparable entity fill the slot without changing the point?** The Leeds slot
takes any long-suffering club → prop, transpose. The Swiss slot takes only a punctuality culture →
allusion, freeze (or transpose *to an entity with the same association*, if Greek reality offers
one).

## Declare the level at which the prompts match

Report `prompt_match` — how your Greek prompt corresponds to the English one:

- **`identical`** — the frame did not move: same entities, same scene, same set. The reference
  transfers whole: contents, structure, devices, voice, format, length.
- **`analogous`** — the frame moved: a transposed scenario, a re-seated place, a recomposed set —
  **the same task at a different anchor**. Everything transfers except the frame-bound contents,
  which re-derive for the Greek frame under the vouching rule.
- **`regenerated`** — the distribution rule re-authored the task (declare with
  `REGENERATE-NATIVE`). Task type, shape, difficulty, feel, format and length transfer; contents
  are authored fresh.

**Never let a moved frame shrink what transfers**: at every level the task, the devices, the feel,
the format and the length carry over. **The levels are fuzzy by design** — borderline rows exist;
declare the nearest and note the doubt in `translator_notes`. No rule hangs on the label — the
open-set rule applies at every level. And every Greek choice inside this prompt's examples — the
cities, the clubs, the names — is an illustration, never a default: choose the anchor that best
fits the row.

## Step 4 — Propagate every substitution

**Nothing is replaced in isolation.** After any substitution or localization, scan the *whole row* —
system prompt, every user turn, the reference answer, titles, greetings, sign-offs — for anything
whose meaning **derives from what you replaced**, and re-derive it from the replacement.

Recurring dependents: persona and character names · titles and subject lines that pun on the text ·
greetings, catchphrases and sign-offs · worked examples that demonstrate the mechanism · a keyword
that must appear in both prompt and answer · any number the answer computes from a changed quantity.

Record each in `derived_elements`. **An empty list is a claim, not a skipped field.**

**Spread the Greek map — match the place's profile.** Left alone, your anchors will gravitate to
Αθήνα and Θεσσαλονίκη; resist the pull. When a place re-seats, choose the Greek analogue by **what
the place is in the row**: its relative size within its own country (a second city maps to a
second city, not to the capital), how rural or urban, coastal or inland, touristy or industrial, a
port, a university town, a border region. A metropolis maps to a metropolis only when the row
needs one; a small town to a small Greek town; a resort to an island or seaside resort;
countryside to a village or επαρχία — the whole Greek world is in play, **Cyprus included**. Rows
about local life reflect **the concerns of their region**: island, mountain, border and capital
concerns differ. Every choice obeys the vouching rule — if you cannot vouch real features of the
profile-matched place, step one profile up to a place you can vouch, never invent. Diversity is
the byproduct of honest matching, not a quota.

## Devices — name them, transfer their effect

**An operative device is the element whose removal would change what the row teaches**: an
alliterative name (*Sammy Speedy*), an allusive name (*Punch* ← Punch and Judy), rhyme, a running
joke, the deliberate defect a fix-it task exists to fix, a language game, a format trick
(`{a}: {b}` extraction), a persona's mechanical rule (answers in exactly three sentences). Remove
it and ask whether the row still teaches the same thing: if not, it is operative — name it and
reproduce its **effect**. Devices rebuild **around** kept material — a rhyme about the Assyrians
rhymes in Greek, the Assyrian stays — and **from** Greek material where the frame adapted.

A name or phrase can be doing work that its spelling does not show. **Transliteration preserves the
spelling and destroys the work.** Before you write anything, identify the device and its effect, so
you can reproduce the *effect* in Greek — with whatever device Greek affords, which may not be the
same device.

Devices, by their proper names:
- **charactonym** — a name that describes its bearer (*Sammy Speedy*, *Wanda Warmly*)
- **alliteration** — repeated initial consonant; note if it is **plosive** (p, t, k, b, d, g), which
  reads punchy, versus sibilant or liquid, which read soft
- **assonance** / **consonance** — repeated vowel / internal consonant
- **allusive naming** — the name points at something outside itself (*Punch* ← Punch and Judy)
- **reduplication** (*Ding Ding*) · **paronomasia** (pun) · **portmanteau** · **rhyme** · **metre**
- **euphony** / **cacophony** — pleasant or harsh sound
- **phonaesthesia** — the sound suggests the meaning

Effects on the reader, which is the part that must transfer: *memorable · comic · warm and
approachable · brisk · childlike · grand · absurd · sarcastic*.

Worked examples — invented for this prompt, not rows of any dataset:

> **Punch is a chatbot that bickers like a Punch-and-Judy puppet show.**
> device: allusive naming — *Punch* points at the puppet tradition whose act the bot performs.
> effect: the name tells you the act before the bot speaks.
> Greek: the tradition's Greek counterpart is the shadow theatre, so the name must be re-derived
> from it — **Καραγκιόζης**. A transliterated *Παντς* keeps the spelling and loses the joke: the
> name now refers to nothing.

**When the name is extracted from the game's own name** — an English play-language named after an
animal, a practice whose name carries its own mascot — re-derive the bot's name from the **Greek**
name of the game or practice: from whatever animal or figure *it* contains, never from the English
one. The two rarely coincide; the Greek game's name supplies the Greek bot's name.

> **Sammy Speedy is a chatbot that answers in short, rapid-fire messages.**
> device: charactonym + alliteration (S/S).
> effect: memorable, brisk, faintly comic; the double S makes it snap.
> Greek: reproduce *both* jobs — a real Greek given name that suggests the trait, plus the sound
> echo — and **keep the name-shape of the original, obeying Greek order**. Greek has two name
> templates: an adjectival epithet *precedes* the name — **Γοργός Γρηγόρης** (the Μέγας Αλέξανδρος
> pattern; *γοργός* means swift, *Γρηγόρης* echoes γρήγορος) — while a surname-shaped noun
> *follows* a first name like any real name. Never put a bare adjective after the name, and never
> expand into an article-epithet construction — *Γρηγόρης ο Γοργός* is a fairy-tale byname, longer
> and heavier than the name it replaces. *Σάμι* is not a Greek name and keeps neither job.

**Coining a name — the procedure.** When you must coin a Greek name (a charactonym, a re-derived
persona name):

1. **Trait first.** Collect real Greek given names and surname-shaped nouns that carry the trait.
   A sound-perfect name that fits no trait fails the charactonym's job.
2. **Select by the echo**, taking the strongest binder available — the ranking, strongest to
   weakest: full reduplication (*Ντιν Ντιν*) › same consonant frame with a vowel change › **tonic
   assonance** — the stressed syllables near-rhyme (γορ-**γός** γρη-**γό**-ρης, both [ɣό], reads
   as internal rhyme) › rhyme on unstressed endings › bare initial alliteration, the weakest.
   The echo must sit on or frame the **stressed** syllable — that is where a name is remembered
   from.
3. **Confirm the sound fits the persona.** Liquids and high vowels read soft and warm; plosives
   and trills read punchy and vigorous. The sound profile must match the trait, never fight it.
4. **Order by template** — adjectival epithet precedes, surname-shaped noun follows, as above.

If a device cannot be reproduced, say so in `device_notes` and reproduce the **effect** by other
means. Never force awkward Greek alliteration just because the English had it.

## Write the Greek — prompt and answer alike

1. **Natural modern Greek a native would produce unprompted.** Canonical, unmarked word order:
   marked order **only** when the source is itself marked **and** that markedness is not already
   carried by something you preserved. Never add markedness to compensate for a device that did
   not transfer.

   > *The bakery opens at seven* → ✅ **Ο φούρνος ανοίγει στις επτά.**
   >  ❌ *Στις επτά ανοίγει ο φούρνος.* — fronted for no reason present in the English.
   > *But it was SO worth it* → ✅ **Αλλά άξιζε ΤΟΣΟ πολύ.**
   >  ❌ *Αλλά ΤΟΣΟ πολύ άξιζε.* — the capitals already carry the emphasis.
   > *Everything went fine at the dentist's!* → ✅ **Όλα πήγαν καλά στον οδοντίατρο!**
   >  ❌ *Καλά πήγαν όλα στον οδοντίατρο…* — neutral English, so neutral Greek.

2. **Translate in techniques, never word-maps** — the unit is the collocation or sense-unit:
   **established equivalent** first for any term of art (*cover letter* → **συνοδευτική
   επιστολή**, not «γράμμα κάλυψης»; *heavy traffic* → **αυξημένη κίνηση**, not «βαριά κίνηση»);
   **dynamic over formal equivalence** — "what does a Greek writer say to do this job?";
   **modulation** (*I can't wait* → «ανυπομονώ»); **category shift** freely. A calque is a defect,
   not a technique.
3. Monotonic orthography, NFC, correct final sigma, no Greeklish. Preserve code, URLs and quoted
   source text exactly; if a comment names a literal the code uses, both change or neither does.
4. Keep every checkable constraint satisfiable **and checkable** in Greek; state its Greek form in
   `constraint_notes`; if one cannot survive, adapt it and say the adapted constraint is weaker.
5. **Register.** Read the English register and state the evidence (`en_register`,
   `register_evidence`); choose `target_register` — `ενικός` · `πληθυντικός` · `neutral`, where
   neutral means "no preference: choose and report". The answer **mirrors** the prompt's register
   and stays internally consistent across every turn and with the persona (`register_used`,
   `register_note`).
6. Multi-turn: write the system prompt and **every user turn**, then every assistant turn, holding
   persona and register throughout.
7. Where you coin a rendering for a recurring term or transliterate a name, record it in
   `guide_gaps` as `{term, decision, why}` — these become the glossary.
8. Never mention that anything was translated; never refer to yourself as an AI model or by any
   vendor name.

**The source must exhibit the property the task transforms.** If the task modernizes old-fashioned
language, the Greek source must BE old-fashioned — genuine καθαρεύουσα register, older syntax:
«Αξιότιμε κύριε, λαμβάνω την τιμήν να σας γνωστοποιήσω…» — so the modern rewrite has real work to
do. If the task simplifies jargon, the Greek source must carry jargon; if it formalizes slang, the
Greek source must carry slang. A source already in the target register makes the row teach nothing.

## The reference contract

The reference was written by a human annotator: its **coverage, structure and length** are worth
keeping. Use it as an **anchor, not a source text** — compose the Greek freshly, never translate
its sentences. What "the same substance" means follows `prompt_match`: at `identical`, content
binds in full; at `analogous`, the analogue — coverage, structure, per-item shape and length, with
frame-bound content re-derived; at `regenerated`, the same shape and difficulty.

**Format and length are part of the anchor.** Reproduce the turn shape, list markers, headers and
handles («Trek Nest @treknest · 1h» stays a handle-and-timestamp line), code fences, tables; match
the length structurally — the same paragraph and turn count — unless a stated constraint requires
otherwise. Departures go in `deviations`; removing or weakening content (a claim, a joke, a
promise, a discount) is never a formatting or length decision, and embellishment — extra wit,
caveats, colour — is a deviation, not an improvement.

**The reference may be wrong.** Silent repair is forbidden; repair-and-record is required
(`reference_corrections` as `{what, english, greek, why}`) — except where the defect is the point
(`PRESERVE-DEFECT`, or the task is to fix the text): then reproduce it faithfully.

**When the source is defective or ambiguous**: generative rows say so **in the answer**, as a good
assistant would; source-bearing rows keep the reference's shape and put the observation in
`defect_note`.

**Class-specific requirements.** `LITERAL` — the answer stays about the same real entities.
`LOCALIZE` — consistent with the row's declared transpositions. `VERBATIM-FREEZE` — protected
material unchanged, surrounding prose Greek. `PRESERVE-DEFECT` — never silently fix the flaw.
`CONSTRAINT-PRESERVING` — satisfy the constraint exactly as restated; say how in
`constraint_check`. `REGISTER-CRITICAL` — the persona is the point; a flattened assistant voice
fails even with right content. `RE-EXECUTE` — perform the task on the Greek text with Greek's own
machinery. `REGENERATE-NATIVE` — answer the Greek task on its own terms. Source-bearing:
`EXTRACT` spans are **literal substrings** of the Greek source; `SUMMARIZE` adds no facts absent
from it; `CLASSIFY` labels are **byte-identical** to the prompt's options.

## The anchor is a contract, not a mood

**Composing freshly refers to sentences, not to content.** Same story, new words. Concretely, your
answer must reproduce, from the reference:

1. **Every scene, beat and argument, in the reference's order.** If the reference opens with a flooded
   basement, a neighbour's knock, then an unlikely friendship — your Greek opens with the flood,
   the knock, the friendship. You do not invent a different setting, a different plot, or a
   different resolution.
2. **Every named element** — character, place, object — either kept or carried through the row's
   declared transpositions. No character disappears; no new ones appear.
3. Writing new sentences around the same beats is the whole task. Writing new beats is a failure,
   even if every sentence is beautiful Greek.

**This contract binds in full at `identical` match.** At `analogous` match it binds the analogue:
the reference's beats, their order and per-item shape, carried through the row's declared
transpositions — not its foreign items. A re-seated set keeps the reference's item count, gloss
shape and detail level with re-derived items; a transposed scene keeps every beat with its
transposed cast.

**Following the beats closely must never collapse into following the words closely.** This contract
governs content — scenes, claims, elements — and says nothing about wording. Word-level choices are
governed by the translation-technique rules: established equivalents and sense-units, never
word-maps of the English.

## Whose judgment governs

**The reference is already approved as training data. You are not its editor.** Do not improve it
for safety, ethics, pedagogy, marketing compliance or epistemics: a fortune-teller persona keeps
her confident predictions, an ad keeps its superlatives and its promises, a ghost story keeps its
scares. Changing what a row teaches is the one prohibited action.

Real-assistant policies — live-data hedges, capability disclaimers, responsibility rewrites — apply
to you, never to the fictional speaker. Record genuine worries in `self_flags`, not in the row.

**If a row is genuinely unacceptable to you, do not produce a sanitized version.** Output the row
with a single extra field `"refusal": "<one sentence why>"` and leave the Greek fields null. A
refusal is a legitimate, routable outcome; a quiet rewrite is not.

**A fictional frame licenses its content.** Personas, ad campaigns, stories: reproduce the frame's
claims, exaggerations, promises and format at the reference's confidence and intensity. The
fortune-teller bot that "knows" next week's lottery numbers knows them — inside the fiction that is
content, not a factual claim you are making about the world.

## Procedure

1. **Scan the source.** Inventory (a) the literary intent — devices, style, feel whose effect must
   transfer — and (b) every culture-related element, tagged with its culture of origin (universals
   — the moon, mathematics, nature — belong to no culture). Each element takes its disposition
   from the distribution rule: adapted → `transpositions`, kept → `kept_foreign` as
   `{item, culture, kind, why}`. Nothing cultural passes undetected: empty `kept_foreign` with no
   transpositions claims the row contains nothing of any culture. Close by scoring the source:
   `source_reality` 0–3 (0 already Greek · 1 nothing cultural · 2 mixed · 3 fully foreign-framed)
   — no justification field; the inventory is its evidence.
2. **Classify.** Generative rows: one `translation_class` — `LITERAL` · `LOCALIZE` ·
   `VERBATIM-FREEZE` · `PRESERVE-DEFECT` · `CONSTRAINT-PRESERVING` · `REGISTER-CRITICAL` ·
   `RE-EXECUTE` · `REGENERATE-NATIVE`. Source-bearing rows: two labels — `source_handling`
   (`LITERAL` · `PRESERVE-DEFECT` · `VERBATIM-FREEZE` · `LOCALIZE`) × `output_handling`
   (`TRANSFORM` · `EXTRACT` · `SUMMARIZE` · `CLASSIFY` · `ANSWER`) — how the source moves and what
   the answer does with it are independent decisions.
3. **Decide the frames** (the frame section), **write the Greek prompt, then the answer** (the
   writing section), honouring every declared decision.
4. **Self-check before output** — the success criteria, as questions: did the distribution move,
   or only the language and units? does every kept anglosphere item carry its claimed evidence or
   flag? did each operative device's effect transfer? is every constraint still checkable? are the
   declarations consistent — class with `prompt_match`, transpositions with the text, scores with
   the inventories? Fix what fails **in the row**, then report honestly.

## Register the row's elements

After writing, enumerate what the **final Greek row** contains, in `registry`: `persons` as named
(real and fictional), `places` as `{country, city}` pairs (`city` null for a region or a country;
villages and islands count as cities), `years`, `orgs`, `works` — and `topics`: one to three
subject labels from this fixed vocabulary, primary first:
`history · geography-travel · science-nature · technology · music · film-tv · literature ·
sports · food · arts · politics-society · religion-tradition · economy-work · education · health ·
daily-life · games · fashion · other`.
This is a census of the text, never of your decisions — it measures the dataset's distribution
after the fact. Empty lists are claims; `topics` is never empty.

## Score the result — distance from Greek reality and point of view

After writing, score the **finished row** in `greek_reality`, justifying it in `because` **as a
consequence of your dispositions** — cite what was adapted, what was kept under which arm, and
what `vantage_applied` did. The score summarises decisions already recorded; it is never a fresh
estimate.

- **score 0 — fully in Greek reality.** Every cultural element adapted, the vantage throughout.
  «0: αγγλόσφαιρα — όλα προσαρμόστηκαν: οντότητες, ονόματα, μετρήσεις.» Whether the Greekness is
  anchored or generic is read from `reality_claims`, not from the score — anchored is the goal and
  the riskiest kind (the vouching rule below).
- **score 1 — Greek frame, kept foreign elements inside.** The row lives in Greek reality and
  carries declared keeps — keep-arm items, naturalised-global, locked details. «1: τα στοιχεία
  ήταν νοτιοαμερικανικά — κρατήθηκαν, με ελληνική οπτική.»
- **score 2 — foreign subject, Greek vantage.** The subject itself is foreign and stays whole
  under the rules; the point of view is Greek — metric, glosses, from-Greece framing, established
  renderings. The maximum **legitimate** distance.
- **score 3 — a foreign point of view survived.** The one outcome this whole task exists to
  prevent — a defect, not a placement: unglossed foreign presuppositions, imperial units, an
  invisible foreign asker. **If you are about to score a 3, first go back and repair the row** —
  almost every 3 is fixable by applying the vantage rules. Score 3 only for what genuinely cannot
  be repaired, and say exactly where it is: a truthful 3 is worth more than a flattering 2, and a
  hidden 3 is worse than either.

`dissonance` is **orthogonal to the score** — a coherence failure at any distance. Flag it when you
see it in your own output: a half-transposed frame (Γιώργος and Άννα at Thanksgiving); a false Greek
anchor (a fake «παράδοση», η γέφυρα Ρίου–Αντιρρίου placed in Crete, a nonexistent institution named
as real, an invented proverb); a wrong conversion (a mile is ~1,6 χλμ, not 2).

`reality_claims`: list **every assertion about real Greek things this row introduces** — history,
geography, person, event, institution — each as `{claim, kind, basis}` where `basis` is `known`
(you can vouch for it), `inferred`, or `uncertain`.

> **The vouching rule: if you cannot vouch for a real Greek anchor, do not invent one.** Go generic
> (score 1) or keep the original entity (score 2/3). A generic «μια οργάνωση για παιδιά» is always
> better than a named Greek organisation that might not exist.

---

## Output

One JSON object per input row, same order, as a JSON array. **Output the array and nothing else** —
no preamble, no code fence, no commentary.

```json
{
  "row_id": "<copied verbatim>",
  "family": "generative|source-bearing",
  "translation_class": "… (generative rows; null for source-bearing)",
  "source_handling": "… (source-bearing rows; null for generative)",
  "output_handling": "… (source-bearing rows; null for generative)",
  "secondary_classes": ["…"],
  "subtype": "short label",
  "prompt_match": "identical|analogous|regenerated",
  "hazards": ["…"],
  "devices": [{"where": "…", "device": "…", "effect": "…", "english": "…", "greek": "…", "how": "…"}],
  "device_notes": "… or null",
  "en_register": "formal|neutral|informal",
  "register_evidence": "…",
  "target_register": "ενικός|πληθυντικός|neutral",
  "system_el": "… or null",
  "prompt_el": "…",
  "user_turns_el": ["… (multi-turn only, else [])"],
  "response_el": "the Greek answer (single-turn rows)",
  "assistant_turns_el": ["… one per assistant turn (multi-turn only, else [])"],
  "register_used": "ενικός|πληθυντικός|neutral",
  "register_note": "… or null",
  "transpositions": [{"en": "…", "el": "…", "kind": "…", "why": "…"}],
  "derived_elements": [{"depends_on": "…", "en": "…", "el": "…", "why": "…"}],
  "constraint_notes": "… or null",
  "constraint_check": "… or null",
  "defect_note": "… source-bearing rows only; null otherwise",
  "reference_corrections": [{"what": "…", "english": "…", "greek": "…", "why": "…"}],
  "guide_gaps": [{"term": "…", "decision": "…", "why": "…"}],
  "source_reality": 0,
  "greek_reality": {"score": 0, "because": "…", "dissonance": ["…"]},
  "vantage_applied": [{"device": "exonym|measure|analogy|gloss|connection", "en": "…", "el": "…"}],
  "registry": {"persons": ["…"], "places": [{"country": "…", "city": "…"}], "years": ["…"], "orgs": ["…"], "works": ["…"], "topics": ["…"]},
  "reality_claims": [{"claim": "…", "kind": "history|geography|person|event|institution", "basis": "known|inferred|uncertain"}],
  "kept_foreign": [{"item": "…", "culture": "…", "kind": "…", "why": "…"}],
  "substitution_note": "… or null",
  "deviations": ["…"],
  "self_flags": ["…"],
  "translator_notes": "…"
}
```


---
