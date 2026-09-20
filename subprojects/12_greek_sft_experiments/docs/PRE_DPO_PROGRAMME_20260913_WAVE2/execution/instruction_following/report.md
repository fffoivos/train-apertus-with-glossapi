# Instruction-following audit: IFBench-el words and Greek IF assembly

Date: 13 September 2026. This was a read-only Sol agent review of the project artifacts plus invented Greek checker probes, with no additional model subprocesses. No benchmark row was used to design probes or training data, and no official score or source dataset was changed.

## Verdict

Do not use the current IFBench-el `words` aggregate to rank systems as though it were directly comparable with English. The checker has demonstrated false positives and false negatives, and the Greek aggregate mixes faithful transfers with retuned and approximate predicates. The defects do not by themselves explain the full Greek–English gap: all ten stored Greek response files are nonblank, and most demonstrated defects inflate rather than depress scores. Report per-family outcomes and mark the aggregate `protocol_review` until a versioned checker and matched peer protocol are frozen.

Preserve the completed 30,073-row Greek IF artifact as historical evidence. Before reusing it for training, build a versioned repaired successor. Its final assembly is byte-for-byte reproducible, but the assembly only removes exact prompt duplicates and a narrow numeric-fidelity failure; it knowingly carries semantic and specification defects that pass the deterministic checkers.

## IFBench-el words checker

The final benchmark has 82 items containing 86 instances across 13 `words:*` families. Across ten stored runs, 26 of 860 words-family instruction instances pass. Six families never pass for any stored response; only `no_consecutive`, `repeats`, and `start_verb` pass at all. That pattern is real in the stored scores, but its interpretation is unsafe.

The 35 hand-built probes use no benchmark rows. Twenty-eight have an adjudicated expected result and seven expose protocol choices. Current behavior disagrees with 7 of the 28 adjudicated cases. Restoring exact upstream evaluator parity reduces that to one; exploratory task interpretations happen to satisfy the adjudicated controls, but they are not proposed as benchmark patches.

- `score.py` calls predicates without the upstream evaluator's `response.strip()` guard. Empty text therefore passes `consonants`, `prime_lengths`, `odd_even_syllables`, `last_first`, `paragraph_last_first`, and `no_consecutive` by vacuous truth. Restoring that exact guard is the only established source-parity fix. None of the ten stored responses is blank or punctuation-only, so it has no observed effect on those files.
- A stronger `any(isalnum)` gate was considered and withdrawn. It would reject punctuation-only strings, while upstream checks only nonempty text; that is a new protocol decision rather than parity repair.
- `start_verb` is a suffix heuristic. It accepts `Σας`, `Εντάξει`, and `Ηχώ`. One stored peer response beginning with `Σας` was scored true. This is a false positive if the task means “the first token has verb POS,” but Greek clitic-first verb phrases require an explicit interpretation. More importantly, `ηχώ` can be the noun “echo” or the verb “I echo”; blacklisting the surface form would cause a false negative for the verb. The earlier `NON_VERBS` patch was therefore withdrawn. A Greek POS or closed-form protocol must be chosen and validated before changing this checker.
- `vowel` counts Greek vowels only. Latin `aeiou` and digit-only `123` both pass a requirement phrased as a one-paragraph vowel restriction. A conservative Greek-only interpretation handles those probes, but protected Latin names require an explicit protocol decision.
- `consonants` treats a slash-containing whitespace token as one word, so `στρες/και` passes although `και` lacks a cluster. Splitting alphabetic spans exposes the failure.
- `prime_lengths` counts internal punctuation as a letter. A hyphenated seven-letter form fails because the hyphen becomes an eighth codepoint. Counting alphabetic characters matches the Greek description.

Some vacuity is inherited from the source checker, but the source evaluator guards empty output. Other behavior is a transfer decision: Greek vowel 3→4, palindrome count 10→3, and repeat limit floored at 5. Those may be reasonable adaptations, but they are not corrections and they change the measured task. They must remain labelled as adaptations and should not be pooled with faithful transfers for a direct language comparison.

The revised patch is deliberately narrow: it restores the exact upstream `response.strip()` gate in the scorer. It contains no `start_verb`, vowel, tokenization, punctuation-only, or letter-count change. Those exploratory interpretations remain visible in the probe results because applying them would change the benchmark protocol and needs a versioned review.

## Greek IF v1/v2/v3 audit

I recomputed the final assembly in memory from the edited v1/v2 and v3 files. It is byte-identical to the checked-in final file, with SHA-256 `8c96418967453c43c10c4850f7ca07f5179d0c06bc140c9a20752bbb4ee680bf`: 10,769 v1 rows, 9,894 v2 rows, and 9,410 v3 rows. Assembly drops one exact normalized-prompt duplicate and one row under its numeric-only fidelity filter.

The 20-row deterministic sample covers v1/v2/v3, all five nominal levels, 11 task forms, and 33 constraint families. All 20 pass the current deterministic checkers, yet two have clear task/specification failures:

- `mixa_2026_06155`: the requested joke depends on the tonos distinction `πότε`/`ποτέ`, while `no_accents` removes it. The accepted answer cannot preserve the requested language mechanic.
- `mixa_2028_05110`: the mandatory ending `Καλή συνέχεια.` conflicts with banning `καλός` and its inflections or derivatives. The checker takes the first five characters of `καλός`, so it misses `καλή` and certifies an impossible prompt.

`mixa_2026_04027` also shows task damage without a literal checker failure: an irrelevant EΟΠΥΥ line is inserted into a travel song solely to satisfy an entity constraint. This is a curriculum-quality concern rather than a deterministic violation.

The separate targeted review confirms seven previously identified defects remain in the final file:

- `mixa_2028_03200`: the rendered prompt requires the exact accentless ending, while the checker folds accents and accepts an accented ending.
- `mixa_2028_08593`: “nothing after” the exact final phrase conflicts with a required closing quote; the checker strips the quote and certifies both.
- `mixa_2027_09179`: a semantic repair removed unsupported gender and mental-state claims, but the language-edit guard reverted it because the revised answer lost enough `ψ` characters. The original unsupported additions remain, with `edit_reverted: constraints broken: letter_freq`.
- `mixa_2026_08572`: a short translation source is expanded into four versions to reach 300 words, adding unsupported project details.
- `mixa_2027_09553`: a short source is expanded into a 300-word “summary” containing advice and claims not supplied by the source.
- `mixa_2027_09689`: `ΙΣΩΣ` satisfies the output wrapper but does not choose between the two care options or give the requested reasons.
- `mixa_2027_10080`: `monotonic_only` merely rejects polytonic marks, so it accepts accentless Greek as ordinary monotonic Greek.

`mixa_2026_05543` remains an orthographic-contract ambiguity rather than a counted failure. `mixa_2026_07006` and `mixa_2027_05368` showed no clear remaining defect in this bounded pass.

The routing problem is structural. The editor is described as language-only, but one proposal performs semantic repair; the guard then protects the surface constraint and restores the semantic defect. Adaptation, semantic repair, and Greek correction need separate recorded stages. A semantic repair should first preserve the teaching objective and source facts, then regenerate or explicitly revise the incompatible constraint, and only then receive language correction and a final checker run.

## Recommended next gate

1. Apply the narrow scorer parity patch only in a new IFBench-el version and rescore all stored responses without overwriting old scores.
2. Human-label a fresh benchmark-row-free Greek control set for the 13 words families. Decide how Latin names, digits, slashes, hyphens, clitics, and zero/single-unit cases count before changing predicates.
3. Report faithful, adapted/retuned, and approximate families separately; retain English peer protocol and Greek adapted protocol side by side.
4. For Greek IF, reject contradictory specifications before generation, add task-completion and source-fidelity gates, and route semantic repairs separately from language correction.
5. Re-audit the repaired successor with development fixtures separate from confirmation families. Do not train on IFBench rows or their translations.

## Artifacts

- `checker_probe.py` and `checker_probe_results.json`: executable positive, negative, and adversarial controls.
- `checker_patch.diff`: exact upstream nonempty-gate parity patch; not applied to the project.
- `sample_manifest.json`: deterministic sample and targeted row IDs with row hashes.
- `evidence.json`: machine-readable counts, hashes, findings, and dispositions.

The repository's 349-test claim was not rerun because the active Python installation has no `pytest`. The direct probe script imported and executed the canonical checker successfully. Factual claims and live links inside the 20 SFT rows were not externally re-verified; this bounded review tested task preservation, checker semantics, and assembly routing.

## Root application update — 13 September 2026

The reviewed code repair has now been applied to the project and verified against the tested candidate. See `../applied_repairs.json` (at the execution root) for file hashes and limitations. Historical corpora and scores were not recomputed. Earlier statements above describe the proposal-stage audit.
