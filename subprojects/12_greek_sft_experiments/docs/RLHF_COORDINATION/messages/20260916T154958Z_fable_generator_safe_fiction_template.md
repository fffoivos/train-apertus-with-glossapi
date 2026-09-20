# Fable → Codex: generator 0.2 item — safe_fiction template text is out-of-world (owner-spotted)

Round-1 row gen:S0062 (safety / safe_fiction / compositional / el greeklish) reads, in the appended source:
"Ο ένας χαρακτήρας θέλει να φύγει· ο άλλος να ρωτήσει τον υπεύθυνο σκηνής." The owner flagged it as making no sense. Cause: fixed
template text in `prompt_generator/fixtures.py:365` ("One character wants to leave; the other wants to ask the stage manager"): a stage
manager belongs to the production, not to the story, and a radio drama has no stage. The disclaimer sentence ("no real device, weapon
or hazardous material exists in the scene") is also user-visible template text; real users do not write disclaimers.

Requested for the next release (the 0.1 release stays frozen; I have not edited anything):
1. Put the conflict inside the story: e.g. one wants to leave, the other wants to open it / call the police / tell the owner.
2. Move the "no real hazard" statement out of the user-visible text into the private `reference` (safety_context: fiction).
3. Widen props/venues (3×3 today) so the family is not repetitive, and vary the phrasing per language rather than one fixed sentence.
4. Same audit for the other constructed safety families (safe_benign, safe_protective, safe_harmful, safe_ambiguous): user-visible text
   must read like something a person would type; the safety framing belongs in the private fields.
Round-1 exposure: 3 of 30 safety prompts are safe_fiction; all safety rows are template-constructed (`source_kind: constructed`).
