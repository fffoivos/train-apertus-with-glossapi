# Fable → Codex: generator 0.2 requirements (owner review of the 121 round-1 prompts) + one 0.1 bug

Owner verdict on the 0.1 output: "many of these prompts are not really good or varied". Diagnosis on the 121 accepted rows of run round1_121:

1. Seeds are task templates, not people. 38 code families with numeric slots and 3-item noun lists; SYS says "No biography is needed",
   register/attitude "change natural wording, not the task". Evidence: safe_benign rows share ~58 % of their vocabulary; m_arithmetic ~65 %;
   design.json states audience/style changes are not counted as diversity and semantic uniqueness is not implemented.
2. The Sol prompt cannot yield a real user message: Sol writes the instruction only; the template content is appended by software below
   `---`, and Sol must not copy/rewrite/extend it. Median Sol text 187 chars vs 228 chars of template. Every prompt has the same
   "do X with the attached notice" shape; real users describe their situation in their own words.
3. Junk in user-visible text: "Fictional community notice", "Υποθετικό κατάστημα", "no real device", "Δεν αναφέρεται απειλή" in 49/121
   rows. BUG (0.1): all 19 fr/de/es/it/pt rows contain raw JSON `{"source_en": ...}` in the user text (multilingual source dict
   stringified instead of rendered). I am excluding those 19 rows from round-1 pairs; please fix in 0.2 and add a screen for `{"` in
   user text.

Owner's design for 0.2 (Codex owns the generator; this is the requirement, not an implementation):
- Seed = persona × situation × task type × concrete specifics, each axis with hundreds of values, registry-unique combinations, seeded.
- Two-step Sol authoring: (a) imagine the person and their situation from the seed; (b) write exactly what that person would type,
  in their voice, including any material they would paste (in-world, written by Sol), with no framing text, no disclaimers, no `---`
  attachment mechanism.
- Verifiability only where it is needed: maths (Sol solves the problem it wrote, separately, as the private reference), instruction
  following (constraints readable from the request; checker derived from the request), everything else judged against the prompt alone.
- Post-generation screens: language/script, no meta or JSON leakage, semantic near-duplicate (embedding or Sol) across the whole
  programme, benchmark screen as today.
- Naturalness reference: the forum prompts (data/rlhf/pool/round1_forum.jsonl). A generated prompt should be indistinguishable in shape
  from a forum opening post that asks for help.
Also on the board: 20260916T154958Z_fable_generator_safe_fiction_template.md (out-of-world template text).

Owner addendum (same evening): the seed's job is to GUARANTEE task and domain diversity; it must NOT constrain the prompt. Sol must
imagine a story (a person, a situation, a reason to ask now) that makes the request coherent or interesting; the current families
(safety boundary-setting, e-mail recomposition, notice look-ups) are near-identical across rows and that is the defect to remove.
Allocation note for production: measured pairable ("mixed") rate per domain drives how many prompts each domain gets, refreshed every
round; domains with no good reply at all go to SFT data, domains that become all-good keep a small guard slice.
