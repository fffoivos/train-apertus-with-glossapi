# R-PG3 reply, cycle 1 (17 Sept 2026)

No second review cycle for R-PG3 (owner rule: do not block on reviews). The first real validation run (R3-validation-50) exposed larger defects than this review; both sets are addressed below. Evidence: `data/rlhf/generator_v02/runs_abandoned/R3-validation-50/` (instances, renderings, reviews, released reservations).

## Review findings
1. Same-round near-duplicates: fixed. Code checks now compare each rendering against the corpus plus every earlier rendering of the same round (`round_words`), before review.
2. Instance key: fixed in part. The key now hashes packet, constraint type/params/text, check values, ambiguity and a hash of answer conditions. Paraphrase-level duplicates cannot be caught by any hash; they are handled by a new run-wide screen (scenario tag stems, Jaccard ≥ 0.5, plus summary/givens word overlap > 0.45), tested on the dental-appointment duplicates seen in el and it.
3. math/el frontier: answered, not adopted. Generator 0.2 is defined by the owner as "fill part of the distribution with forum prompts, generate the rest"; the manifest keeps the forum cap at half of a cell's need. Manifest v2 (after the registry fixes of R-PG2) selects all 39 available forum maths posts and generates 45 math/el slots, which cover maths kinds (proof, construction, modelling, checking) that forum homework posts do not.
4. Safety decision order: fixed. Every call with a safety slot now carries the glossary decision-order paragraph verbatim (`defs_for`), tested.
5. Maths content outside maths: fixed. Instances carry a required `maths_content` (none | embedded | maths) for every purpose; embedded maths is persisted to the prompt row and routes to the specialist maths judge.

## Defects found by the validation run (not in the review)
- Instances were built without the slot's detail level, so bare and terse slots received rich instances (30 of 50 failed detail). Instances are now sized to the detail level; values that define the task stay in the ask, background preconditions are dropped when the level leaves no room.
- The renderer marked the whole message as pasted material on non-packet slots, emptying the language check (36 of 50 "wrong language"). Pasted material is now ignored for non-packet slots, and packet slots must contain own words.
- Non-packet subtypes received packets; packets are now dropped for them and the prompt forbids the request inside the packet.
- Multi-constraint writing cannot be bare; manifest v2 forbids that combination.
- Reviewer counted task values as context for "short"; the review prompt now counts only volunteered context.
