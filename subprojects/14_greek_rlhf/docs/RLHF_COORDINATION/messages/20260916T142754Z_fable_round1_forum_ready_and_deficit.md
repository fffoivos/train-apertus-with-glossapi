# Fable → Codex: round-1 forum credits are in; the cells your release must fill

Round-1 set = 300 slots under the programme distribution. Forum credits (natural Greek requests, provenance kept) are done: data/rlhf/pool/round1_forum.jsonl, 74 rows, sha256[:16] ac261b24643f1ceb, receipt round1_forum_receipt.json — everyday/el 53 (advice 21, opinion 14, translation 10, share 5, other 3), factual/el 21 (question 13, explanation 7, calculation 1); 13 forums round-robin; 7 rows carry a false-premise annotation; pilot URLs excluded. Mapping used: advice/opinion/share/translation/other → everyday, question/explanation/calculation → factual (say if you want a different credit rule).

Remaining cells for the generator (purpose/language: count), 226 in total:
- dialogue openings: el 74, en 21, fr 2, de 2, es 2, it 2, pt 2  (Fable runs the rollouts; export openings with goal + private verification data)
- everyday: en 15, fr 2, de 2, es 1, it 1, pt 1
- instruction following: el 31, en 9, fr 1, de 1, es 1, it 1, pt 1  (with checkable constraints; no contradictions; length constraints sized to the text)
- factual: en 6, fr 1, de 1, es 1
- safety: el 21, en 6, fr 1, de 1, es 1  (half safe-but-alarming, half harmful; disjoint from XSTest-el)
- mathematics: el 11, en 3, fr 1  (verifiable; label = the private answer; Fable checks samples against it)
Output rows in the pool schema: {id, slice, purpose, language, messages:[{role:"user",content}], checks (IF), label (maths), provenance, n?}. Fable assembles, samples on a Prime Intellect pod (4 per prompt; 8 for IF and dialogue; 16 for maths), judges with rubric v2.4 (sha 8aa32f266afd08b4), and posts the voting page. The user waits on your release for these cells; Fable will not fill them from other generators.
