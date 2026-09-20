# Greek instruction-following repair pilot

Date: 13 September 2026

## Decision

This 20-record pilot is ready for human review as a candidate set, not for promotion. Nineteen candidates pass every applicable current deterministic checker and preserve the substantive task under a full request-response read. One record, `mixa_2026_05543`, remains blocked because its displayed atonic target and accent-folding checker define different exact-word tasks.

All 20 originals pass their current checkers. Only nine are adequate under semantic review; ten have established specification, fidelity, exact-string, or task-completion failures, and one is unresolved. This is direct evidence that checker pass alone is not an acceptance gate.

No source dataset, production artifact, official score, or benchmark result was changed. No benchmark row or translation was used to author training candidates. This was a Sol agent review with no additional model subprocesses, GPU work, or web access.

## Artifacts and provenance

- `candidates.jsonl` contains all 20 complete original rows, including the exact original user request, assistant response, turns, metadata, and constraints. Each record also carries a complete candidate row when one is proposed, an explicit constraint mapping, semantic decision, and per-row hashes.
- `checker_results.json` records the actual output of the canonical project checker for every original and candidate constraint.
- `manifest.json` gives final-assembly and edited-component source paths, line numbers, file hashes, raw-row hashes, version identity, selection class, status, and candidate hashes.
- `build_pilot.py` deterministically reconstructs the candidates and reruns the checks. It writes only inside this wave-2 output directory.

The source is the immutable final assembly at:

```text
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/greek_if/final/greek_if_sft.jsonl
SHA-256 8c96418967453c43c10c4850f7ca07f5179d0c06bc140c9a20752bbb4ee680bf
```

Every selected row was also located in its actual edited component (`v1v2/edited/rows_edited.jsonl` or `v3/edited/rows_edited.jsonl`). The complete shared `id`, `user`, `assistant`, `turns`, and `meta` fields matched the final row for all 20 records. This avoids relying on IDs alone.

The executed checker was:

```text
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/greek_if/constraints.py
```

Its exact SHA-256 is recorded in `checker_results.json` because it must be bound to the results rather than inferred later.

## Selected records

The set deliberately contains ten known semantic/specification defects, one unresolved exact-word contract, and nine controls that should remain unchanged. It spans v1, v2, and v3; one through five constraints; creative, correction, translation, summarisation, opinion, rewrite, comparison, planning, and how-to forms; exact start/end strings, wrappers, word and letter counts, paragraph structure, case, orthography, entity inclusion, JSON, and punctuation.

It is not random and is not a prevalence sample.

| Record | Class | Candidate operation | Checker result | Semantic result |
|---|---|---|---|---|
| `mixa_2026_06155` | Impossible language mechanic | Reauthor joke so it works without accents; retain atonic output and wrapper | original pass; candidate pass | candidate preserves creative task |
| `mixa_2028_05110` | Contradictory constraints | Change required ending to `Μείνε ασφαλής.`; retain forbidden `καλός` family | original pass; candidate pass | candidate satisfiable and relevant |
| `mixa_2028_03200` | Exact-string failure | Restore literal accentless `Καλη συνεχεια.` and align metadata | original pass; candidate pass | candidate satisfies displayed bytes |
| `mixa_2028_08593` | Exact end versus wrapper | Specify that only the mandatory closing quote may follow the final phrase | original pass; candidate pass | candidate specification is satisfiable |
| `mixa_2027_09179` | Source-fidelity failure | Remove unsupported gender, added mental-state claims, and speculation; reduce `ψ` from 6 to 3 | original pass; candidate pass | candidate summarizes supplied facts only |
| `mixa_2026_08572` | Translation padding | Reduce minimum from 300 to 50 words; retain one faithful translation | original pass; candidate pass | no invented project expansion |
| `mixa_2027_09553` | Summary padding | Replace 300-word minimum with 120-word maximum; reduce `ψ` from 8 to 4 | original pass; candidate pass | concise source-faithful summary |
| `mixa_2027_09689` | Format defeats requested reasons | Replace one-word output with exactly three uppercase sentences | original pass; candidate pass | choice and reasons are now possible |
| `mixa_2027_10080` | Orthography checker false positive | Restore ordinary monotonic accents | original pass; candidate pass | candidate is standard monotonic Greek |
| `mixa_2026_04027` | Irrelevant entity padding | Replace unrelated `ΕΟΠΥΥ` with task-relevant `ΚΤΕΛ Λάρισας` | original pass; candidate pass | entity supports the travel song |
| `mixa_2026_05543` | Exact-word protocol unresolved | No candidate selected | original pass; candidate blocked | requires a versioned protocol choice |
| `mixa_2026_07006` | Complex valid control | Unchanged | pass; pass | adequate |
| `mixa_2027_05368` | Monotonic valid control | Unchanged | pass; pass | adequate |
| `mixa_2026_06199` | Highlight valid control | Unchanged | pass; pass | adequate |
| `mixa_2026_04931` | Paragraph-start valid control | Unchanged | pass; pass | adequate |
| `mixa_2026_11688` | Multi-constraint valid control | Unchanged | pass; pass | adequate |
| `mixa_2026_08647` | Exact-start and wrapper control | Unchanged | pass; pass | adequate |
| `mixa_2027_09233` | Lowercase valid control | Unchanged | pass; pass | adequate |
| `mixa_2027_07834` | Placeholder/question-mark control | Unchanged | pass; pass | adequate within local evidence |
| `mixa_2027_01564` | Title/date/end control | Unchanged | pass; pass | adequate within local evidence |

## Why some repairs change the request

A response-only edit cannot preserve an impossible specification. For those rows, the candidate changes the source constraint and records the mapping rather than manufacturing padding or declaring an impossible response valid.

- In `mixa_2026_06155`, removing accents erases the requested `πότε`/`ποτέ` distinction. The new joke uses an accent-independent time metaphor while retaining the no-accent and quotation skills.
- In `mixa_2028_05110`, the mandatory `Καλή συνέχεια.` conflicts with a ban on `καλός` and its derivatives. The replacement ending keeps both an exact-ending skill and the forbidden-family skill.
- In `mixa_2028_08593`, the closing Greek quotation mark must occur after the phrase that was required to have “nothing after” it. The candidate specifies wrapper precedence and permits only that structural close.
- In `mixa_2026_08572` and `mixa_2027_09553`, length minima force invention. The proposed thresholds are tied to faithful translation or concise summary rather than to the old checker target.
- In `mixa_2027_09689`, one word cannot provide an option comparison and reasons. Three exact sentences retain a measurable format constraint and restore the substantive task.

These are candidate source reauthorings. They are not Greek language corrections and must remain a separate stage in provenance.

## Checker execution and semantic acceptance

`build_pilot.py` imported the canonical `constraints.py` directly and called `check_all(answer, constraints, request)` on every complete original and candidate. The observed result was:

```text
records: 20
originals with all checkable constraints passing: 20
executable candidates: 19
executable candidates with all checkable constraints passing: 19
blocked candidates: 1
originals adequate under bounded semantic read: 9
candidates adequate under bounded semantic read: 19
```

A separate decoded-string scan found no forbidden C0 characters in any executable candidate response. Candidate word counts were also recomputed through the checker-compatible token regex; the changed minimum/maximum rows were 68 words (`mixa_2026_08572`) and 83 words (`mixa_2027_09553`). The three-sentence candidate for `mixa_2027_09689` and all exact-start/end/wrapper candidates passed their relevant canonical predicates.

The semantic read checked whether the response still performed the requested task, used only supplied facts for rewrites/summaries, preserved constraint meaning after mapping, and avoided irrelevant material inserted solely for a count. It did not treat checker success as evidence of those properties.

## Blocked exact-word decision

`mixa_2026_05543` asks for the visibly atonic string `επιλογη` twice, while the checker accent-folds and accepts two occurrences of natural `επιλογή`. Two coherent protocols exist:

1. **Surface-exact:** the displayed target is byte-sensitive. The current answer fails and a repaired response would contain atonic forms inside otherwise accented prose. This measures orthographic copying but produces unnatural training text.
2. **Lexical identity:** accents and case are normalized. The current answer passes, but the request should display `επιλογή` or explicitly state that accented forms count. This measures word inclusion rather than exact spelling.

The pilot does not choose between them. Promotion requires a named, versioned contract and positive/negative controls for the selected interpretation.

## IFBench-el words protocol remains separate

No IFBench row, response, or translation appears in this pilot. The established upstream-parity fix remains only the nonempty `response.strip()` gate already reviewed elsewhere. The following unresolved semantics require versioned protocol choices before any new predicate or rescore:

| Family | Protocol options | Invariant | Consequence |
|---|---|---|---|
| `start_verb` | first orthographic token must have verb POS; or allow a leading object clitic as part of a verb phrase; or use a closed accepted-form list | `ηχώ` must remain ambiguous by context; no surface blacklist may reject its verb reading | `Σας ενημερώνω` differs across options; a suffix heuristic cannot adjudicate POS |
| `vowel` | restrict to Greek alphabetic words; or permit protected Latin words under an explicit exception | digits and punctuation cannot silently stand in for words unless the protocol says so | Latin names and `123` receive different labels |
| `consonants` | whitespace tokens; or Unicode alphabetic spans separated by slash/punctuation | the unit definition must be stated before scoring | `στρες/και` passes only under the whitespace-token reading |
| `prime_lengths` | count all internal code points; or count alphabetic letters only | hyphen behavior must be fixed symmetrically for all systems | `καλο-νεο` changes result |
| output gate | upstream nonempty text; or stronger alphanumeric-content requirement | historical scores remain immutable | punctuation-only behavior changes only in a new protocol version |

The options are stated from task semantics and adversarial invariants, not chosen to improve a particular system. They must be validated on development controls that are separate from held-out confirmation families. Training data must not target the benchmark rows or exploit a known checker weakness.

## Remaining promotion gates

1. Human review the 10 changed candidates and explicitly approve each source-level constraint mapping.
2. Resolve `mixa_2026_05543` or keep it quarantined.
3. Run Greek language correction only after semantic specifications are frozen; protect exact strings byte-for-byte.
4. Re-run the canonical checkers after any language edit and repeat the full task-adequacy read.
5. Perform domain/factual acceptance where the task depends on current facts, live links, health guidance, legal guidance, or technical procedures. This pilot did not externally revalidate those claims.
6. Apply the real tokenizer/chat-template and training-window gate to complete candidate rows before promotion.
7. Promote into a new versioned successor only; preserve the 30,073-row historical artifact and all old scores.
