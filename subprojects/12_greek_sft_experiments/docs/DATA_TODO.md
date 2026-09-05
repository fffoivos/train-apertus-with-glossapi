# Dataset improvement backlog (long-running)

Owner's intent (Sat 5 Sep 2026): the Greek SFT datasets keep improving long after the 1 October 2026 Swiss AI small-grant deadline; the Max
subscription sits idle for long stretches and this backlog is what to spend it on. Items are ordered by expected value per subscription-hour.
Each item names the evidence that put it here. Move done items to the bottom with the date.

## A. Generation (Sol writes, Sol corrects, judge screens, owner reads)
1. **Real passages for the administrative genres of the rewriting set.** Tonight's 2,000 rows use Sol-written passages: plausible fiction on real
   names (row gr_rw_00939: a Nafplio regulation with invented fines and phone number). Source real public-sector texts instead: Μίτος procedure
   texts (open API, 4,332 procedures, open data licence), municipal regulations, ministry circulars; Sol writes only the instruction and the answer.
2. **Topic breadth.** 40 topics for 2,000 rows means each recurs about 50 times. Next batch: a topic list ten times longer, or Sol picks the topic
   within a named domain; add genres (contracts, medical leaflets, school reports, sports reports, product reviews).
3. **Greek generation for the census gaps** (judge census of our set, Sat 00:00: reasoning 1%, code 5%, constraint following 5%, tool use 0,
   science 0, puzzles 0): (a) Greek constraint following with the IFEval checkers ported to Greek, so rows are verified not judged; (b) Greek
   reasoning and puzzles with a checker; (c) Greek coding prompts with tests; (d) Greek tool-use dialogues in the Apertus native tool format;
   (e) Greek science and knowledge QA with vouched sources.
4. **Safety refusals in our voice** (stage 2): warm, no boilerplate, Greek frame; replaces the 2024 WildGuardMix/CoCoNot style rows.
5. **Personality set** (`SFT_ROUND2_PLAN.md` §3): ΕΕΛΛΑΚ-made, Greek users, local model downloaded from HF; needs the owner's identity facts.

## B. Screening and verification
6. **Precise IF, full Sol screen** of the 137k (27% unusable in the spot-check; only 20k screened for stage 1). About 95 h of Sol at 24 workers.
7. **Coding, full Sol screen** of the 60k Python Algorithms rows (6.7% wrong; 20k screened for stage 1), or find execution-testable code data.
8. **Science**: 44% of Dolci's science answers judged wrong; screen the rest of the 99k or replace the source.
9. **Nemotron half B and the 141k top-up**: screen with Luna light + routing; recover the WildChat-seeded prompts by hashing WildChat-1M
   against `seed_prompt_sha256` (41% of the chat split).
10. **A mannerism classifier** instead of the opener/closer lexicon for the unlabelled blocks; and a Greek mannerism list.
11. **Identity patterns for all EU languages** (today: en, fr, de, it, es, pt, el) and a paraphrase check by a judge on a sample per block.
12. **Deduplicate the cluster copies** of the Dolci exports (the double-read shards); local copies are clean.

## C. Experiments that decide the design
13. **Screened versus unscreened control arm** (same Greek data, foreign rows raw): tests the owner's hypothesis that language-neutral framing
    does not matter when Greek covers every category. Needs the cap raised (about 2 × stage-1 cost).
14. **Greek repeat factor** 2 → 3 in stage 1 if the interviews show the vantage slipping.
15. **Constraint-following share** revisit once Precise IF is fully screened (decision 4 in the plan).
16. **Tool-use format**: wire the Apertus template's native tool format before tool rows carry weight (decision 6).

## D. Licences and provenance
17. Qwen-generated ifeval-like rows and Llama-generated OpenMath rows: attribution clauses (plan §7 decision 2).
18. Every generated set carries its prompt version, model, effort and the correction-pass version in the receipt.

## Done
- (move items here with the date)

19. **Complete the Nemotron inspection (judge window).** Round two judged Nemotron with Luna's 3,000/9,000-character window: 58% of rows cut, 27% of assistant text unseen (plan §3, "Judge window"). When the subscription is idle, re-judge the cut rows (about 40,000 across halves A and B; ids = rows whose rendered conversation exceeds 9,000 characters) with the Sol window 12,000/24,000, or with Luna at 12,000/24,000 for tone only; drop or repair what the tail reveals. Rough cost: 40k rows at 4× the tokens of a Luna row, about two overnight runs. Owner's standing preference: the most complete inspection possible; shortcuts are decisions to be documented, not defects to be buried.

20. **Categorized adaptation + Greek reference registry (owner, Saturday 5 Sep, 17:30).** Luna's adapt verdicts are worth keeping, but each reason needs a different response: delete the identity line; substitute the Greek institution where one exists (IRS → ΑΑΔΕ, NHS → ΕΟΠΥΥ, 911 → 112/166, FDA → ΕΟΦ); keep the foreign source where nothing Greek covers it (CDC guidance, row 154377) and say so; convert units and currency; rewrite procedure-bound answers on the Greek procedure (Μίτος, item 1). Steps: (a) write adapt notes for the 3,184 adapt rows that have none (light rubric dropped the field); (b) categorize all 5,400 notes (first keyword pass: identity 38%, culture/places 20%, tax/law/government 17%, health 2.5%, units 1%, 34% uncategorized); (c) build the registry: Greek institution or site → domain → what it covers → foreign counterparts → mention counts; (d) check the references exist in the model's knowledge before substituting: exact-match counts in the CPT corpus (one CPU pass over 51.8M docs, or an n-gram index built once) AND a direct knowledge probe of the CPT checkpoint (fact sheets from Μίτος and the institutions, graded by match or Sol), since the pretraining data behind the foreign-language rows cannot be scanned; (e) run the adaptation pass (round-one Γ contract) per category.

21. **Ancient and polytonic Greek fluency set (owner, Saturday 5 Sep, 23:50).** A separate dataset: Ancient → Modern translation, interpretation of passages, explanation of terms, morphology, Katharevousa → Demotic, polytonic ↔ monotonic. Verifiable parts first: polytonic → monotonic conversion is deterministic (a checker), monotonic → polytonic and morphology can be checked against Morpheus/Perseus; translation and interpretation need a judge or aligned public-domain translations (Pallis' Iliad 1904, Polylas' Odyssey 1875, Greek Wikisource). Sources with clear licences: Perseus and First1KGreek (CC BY-SA / CC BY, Greek texts with English translations), LSJ via Perseus for terms, 19th-century press and Wikisource for Katharevousa; the Greek-language portal's modern translations are restricted. Tokenizer caveat measured on the CPT tokenizer: modern monotonic Greek 5.2 chars per token, Katharevousa polytonic 3.3, Homeric polytonic 2.5, with accented capitals (Ἄ) split into byte fragments; polytonic output will be slower and harder to keep fluent, and the polytonic tokenizer extension from subproject 02_1 was never adopted. Check how much polytonic text the CPT corpus holds before sizing.
