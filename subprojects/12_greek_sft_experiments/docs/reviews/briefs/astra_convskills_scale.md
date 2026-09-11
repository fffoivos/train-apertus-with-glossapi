# Review brief: conversation suite at scale (v2, 4,000 attempts, 2026-09-11) — after the editor pass and re-verification

## What it is
The conversation suite teaches deterministic multi-turn skills with mechanically verifiable targets, built from our own single-turn Greek rows stitched into dialogues; the target turn is written by Sol and checked by regex/invariants (docs/DIALOGUE_REVIEW_AND_SUITE_20260909.md §7). Lanes: S1 the conversation as an object (first question, quote message n, count, list of requests as summaries, what did you say about X); S2 standing instructions kept over 5–9 later turns, revoked in half the rows (one sentence, ≤20 words, no questions back, formal plural, bullets, end phrase, greeklish); S3 edit my previous answer (shorter, without a word, one item, bullets, prose, for a child) with protected propositions; S3c two chained edits in either order; S4 stop this habit (a planted tic in two masked context answers, then the stop request; later answers lack it; non-empty acknowledgement); S5m inference memory (name, city, budget, limitation stated early, unrelated exchanges, then a plan that must use them).

## What changed since the pilot you reviewed (docs/reviews/ASTRA_convskills_pilot_20260910.md)
All your pilot dispositions were applied before scaling: complete records in this packet (no clipping); S4 planted tics present in both context turns with train=false (verified 75/75 in the pilot, and again here by the re-verification); protected-proposition invariants on S3/S3c; «στο μισό» band 35–65% of the previous answer; three phrasings per edit operation and both S3c orders; four S5m intro templates, facts split over two turns in half the rows, vocatives fixed; S1 list check now stem-tolerant (Greek inflection) and rejects verbatim copies; S2 `no_questions` counts only questions to the user, `one_sentence` ignores URLs/abbreviations and rejects run-ons; post-edit re-verification of every lane check on the final rows (data/convskills/reverify_suite.py) with a manifest; the editor never empties a turn nor changes a sentence quoted later.

## Numbers
Generated at 48 workers, 246 KB/s Wi-Fi after the Codex catalog fix. Attempts: S1 800, S2 1,000, S3 500, S3c 500, S4 400, S5m 800. Verified at generation: 3,437 rows. Editor pass and re-verification results are in the manifest appended below (data/convskills/v2/reverify/manifest.json). Rows in this packet are the FINAL rows (edited, re-verified).

## What to judge (adversarial; quote row ids)
1. Per lane, is the target a correct demonstration of the skill on the FINAL text (after editing)? Count failures the mechanical checks missed: wrong quotes/counts (S1), a later turn breaking the standing instruction or the revocation not honoured (S2), edits that drop a qualifier, number or condition (S3/S3c), a tic surviving or an empty acknowledgement (S4), a plan that ignores the limitation or exceeds the budget (S5m).
2. Naturalness of the stitched user side: do the requests read as one person's conversation; are the transitions abrupt; is the base-row reuse visible (same source prompt in several rows)?
3. Editor damage: any row where the language edit changed meaning, a number, a quoted span or a constraint-bearing span.
4. Coverage and balance: lane sizes vs the skills MultiChallenge-el measures (retention, inference memory, versioned editing, self-coherence); what is thin; S2 subtype balance and the revoked share.
5. Anything that would teach a wrong habit (mechanical acknowledgements, «Εντάξει» openers, list-copying, over-literal edits).
6. Compare with your pilot findings: which are fixed, which persist, what is new.

## Disposition
BLOCKER/HIGH findings are applied to the final rows by filtering or by a targeted repair before the training assembly (no re-generation this round; budget); MEDIUM/LOW logged in docs/DATA_TODO.md.

---

