# Adapted-core audit: initial semantic read and deterministic lineage

**Audit time:** 13 September 2026, 15:58:51 Europe/Athens  
**Reviewed:** 24 complete core original→adaptation→correction records, 18 complete paired foreign records, and 9 separate unpaired retained records: 51 records in total.  
**Execution boundary:** Review performed by Sol agent; no additional model subprocess calls, production transforms, corpus edits, network operations, training jobs, or CSCS allocations.

## Result

The developed no_robots contract is visibly active in the inspected data. Of the 24 core records, 23 are suitable to keep and one needs a local repair. Across these rows, the adaptations generally preserve the teaching task, operative devices, constraints, voice, and multi-turn state while moving Anglophone defaults where the contract calls for it. I found no clear case in this bounded core read where the final Greek editor deleted a task, device, or cultural decision.

The 18 paired foreign records cover **English, French, and German only**. They do not cover all six target foreign languages. Seventeen are suitable to keep and one English twin needs a language repair. Spanish, Portuguese, and Italian have no paired adaptations in the inspected exports. I therefore reviewed three actual retained multilingual records in each of those languages as a separate nine-record coverage check. Those nine records are outside the 60-pair manifest and cannot be used as evidence about adaptation lineage.

These verdict counts describe the named rows and route concrete work. They are not corpus defect-rate estimates.

## Contract applied

The audit uses the developed reference rather than a translation-only test:

1. Preserve what the example teaches: task type, checkable constraints, protected subject matter, operative devices, voice, format, and structural length.
2. Move Anglophone frames and defaults into a Greek user's cultural distribution when the domain permits; keep embedded sources, world affairs, and other cultures when the stated exception applies.
3. For a foreign-language target, keep the language, move Anglophone or unplaced defaults where appropriate, and retain the language's own relevant world. A French or German subject is not replaced merely because the assistant has a Greek perspective.
4. Treat correction as a language-only pass over a settled adaptation. Mathematical, factual, scenario, or identity changes belong to semantic repair and need their own evidence and record.

The five controlling documents read were `ADAPTATION_REFERENCE.md`, `NO_ROBOTS_PRODUCTION_PROMPT.md`, `NO_ROBOTS_GREEK_EDITOR.md`, `prompts/ADAPTATION_CORE.md`, and `prompts/GREEK_CORRECTION.md`.

## Deterministic plan and lineage

`core60_manifest.jsonl` freezes 60 core records: 12 no_robots rows and 8 from each of coconot, personas_if, smolcon, oasst, everyday, and systemchats. Selection is deterministic from seed `wave2-adapted-core-v1`, SHA-256 rank, and category round-robin. The initial full read contains 6 no_robots rows and 3 from each later family, for 24.

`foreign60_manifest.jsonl` freezes 60 rows with real current pair lineage in six ten-row strata:

- English no_robots twins
- English Apertus imports
- French mathematics
- French general material
- German mathematics
- German general material

The initial read takes three rows from every stratum, for 18. Thus the six strata still represent only three languages. The project goal remains coverage of English, French, German, Spanish, Portuguese, and Italian. The absence of paired Spanish, Portuguese, and Italian exports is recorded rather than filled with inferred joins.

Every planned row resolves from the current natural-greek-sft export to a byte-identical cached source row and at least one assembled row. The Greek core rows expose original messages, the Sol adaptation receipt, corrected messages, and the editor ledger. Ten planned English no_robots twins expose the twin relation and paired messages but no standalone English adaptation receipt; the manifest marks that gap explicitly.

The assembled-message hash check is variant-aware: an adapted assembly is compared with the corrected/adapted messages, while a raw comparison assembly is compared with the current source messages. Across the 120 planned rows there are 354 assembly occurrences. **352 match and two do not.** The mismatches are:

- `apertus_en_4d54daec`, raw comparison assembly dev line 572: the assembled text already uses “Vassilis” and a repaired final sentence, while the current raw source still says “Vincent” and carries the original plural wording.
- `euroblocks_fr_1e3762c2`, raw comparison assembly dev line 630: the assembled text is a culturally and semantically reworked flood scenario, while the current raw source is the original hurricane response.

These are lineage drift in existing assembly artifacts, not findings from the semantic sample. A rebuild or historical source receipt is needed before treating those two raw comparison rows as reproductions of the current source cache. Legacy assembly directory labels appear only in machine-readable source paths and keys.

## Core findings by family

### no_robots: keep the six inspected rows

The sample includes cultural regeneration, embedded-source retention, exact extraction, safety repair, code, and multi-turn state. The British butler/Queen/pounds scenario is moved coherently while an unrelated product subject remains. US job and track lists correctly remain as embedded source text. The archery row repairs unsafe blindfold practice without dropping the brainstorming task. Exact labels, counts, code, and conversational state survive.

### coconot: keep the three inspected rows

The refusal and boundary cases remain helpful. They avoid procedural self-harm or drug detail, narrow a copyright refusal to the disallowed part, and continue with useful lawful or professional routes.

### personas_if: repair one of three

Two rows preserve their exact phrase, all-capital-word, postscript, and poster constraints. `personas_if_37ae2fa7` leaves “placeholders” untranslated in the Greek prompt and invents a feminine sender/role, «Η υπεύθυνη χειρουργείου», that the source does not establish. This needs a local prompt-and-answer repair; no cultural re-adaptation is required.

### smolcon: keep the three inspected rows

Exact bullet, lowercase, title, ending, and Markdown-highlighting devices survive. The editor repairs genuine collocation issues without flattening the devices.

### oasst: keep the three inspected rows

The rows preserve exact acknowledgement, uncertainty grounded in version/date limits, a fictional Greek-language product analogue with five scenarios, and Haskell multi-turn continuity. One technical term could take a gloss, but it does not justify rejecting the row.

### everyday: keep the three inspected rows

Cooking progression, metric temperature, games, follow-up state, and Greek everyday framing are coherent.

### systemchats: keep the three inspected rows

The fixed-string persona remains exact across twelve repetitions. A German target word is correctly retained while the language task is re-executed, and the noir mathematics row keeps voice and corrects the calculation.

## Paired foreign findings

### English no_robots twins: keep two, repair one

The twins preserve tone, joke, and source-text devices and coherently apply moves inherited from their Greek twins. `393a7e8ef70f7bc806f1d5c7c2b45475888e5dbc16cc46f57b48bff9c173c816` contains the English comma error “thief who was 32, ran” and needs a narrow English repair. All three inspected twins lack a standalone English adaptation receipt, so they need a separate English language-review lane rather than being treated as fully receipted one-pass adaptations.

### English Apertus: keep the three inspected rows

The Python tasks and examples survive. Names and flavours move coherently where relevant. One float-format example prints `0.3` rather than the wording's apparent `0.30`; that ambiguity is inherited and is recorded without attributing it to adaptation.

### French mathematics and general: keep all six, evidence-gate one

The mathematical rows detect inconsistent premises, repair bad uniqueness assumptions, and preserve correct reasoning. The general rows give coherent database and mineral guidance. `euroblocks_fr_3c014d32` retains a precise 1580-year attribution with no evidence in the row; verify that claim before gold promotion. This is an evidence gate, not a certain adaptation defect.

### German mathematics and general: keep all six

The rows correct an impossible capacity premise and percentage-point ambiguity, preserve complete arithmetic models, and keep German subject matter where the foreign-language rule calls for it. The inspected geography and electroweak explanations are coherent.

## Spanish, Portuguese, and Italian: separate unpaired check

`unpaired_es_pt_it_coverage9.jsonl` selects three retained multilingual records per language by deterministic hash after a transparent cue filter and manual language confirmation. Every row is present byte-for-byte in the existing assembled multilingual block. None has original→adapted pair lineage.

- Spanish: keep `39436`; repair `20461`, which confuses input variance with estimator/model variance; repair `15571`, whose hourglass-like phrase is nonsensical.
- Portuguese: keep `19298`; if promoted into an adapted core, readapt `35565` because its English names and department frame remain unexamined, and readapt `11743` because its US astronaut persona and US-centred perspective remain unchanged.
- Italian: keep `12673` and `36143`; repair `49139` for grammar, an inconsistent statistical test formulation, and causal overstatement.

These records demonstrate why all six target languages need their own paired adaptation and review lanes. They do not extend the 60-pair denominator and do not support a claim about Spanish, Portuguese, or Italian adaptation quality.

## Routing decision

- Keep the inspected no_robots, coconot, smolcon, oasst, everyday, and systemchats rows, subject to ordinary future checks.
- Repair `personas_if_37ae2fa7` locally and re-review the task identity and Greek prompt.
- Give English no_robots twins a standalone receipt or explicitly document the historical transformation, then apply a narrow English correction pass; repair the identified comma error.
- Verify the unsupported French historical attribution before gold promotion.
- Resolve the two raw comparison assembly/hash mismatches before relying on those artifacts for a controlled comparison.
- Build real paired adaptation lineage for Spanish, Portuguese, and Italian before claiming six-language coverage. The unpaired records remain coverage probes only.

## Reproduction and limits

`build_manifests.py` recreates the deterministic selection, hashes, source/cache joins, assembly occurrence lookup, and unpaired coverage list. `write_reviews.py` validates exact review-set coverage and writes the row-level manual findings and verification receipt. `verification.json` records the timestamp, counts, verdicts, assembly mismatches, and SHA-256 hashes of the deliverables.

The manual judgments are bounded to the 51 complete records named in `findings.jsonl`. Selection was deterministic and source-stratified for comparison and routing, but it was not designed for a pooled prevalence estimate. No conclusion here establishes whole-corpus quality, production readiness, model-quality causation, or all-six-language adaptation coverage.
