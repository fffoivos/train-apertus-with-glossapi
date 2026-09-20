# Balanced correcting-dialogue pilot — revision 2 contract

This is a prepared, unlaunched sibling of the original pilot. The original four primary-call receipts and accepted artifacts remain byte-for-byte in `../run_state/train`; revision 2 binds their hashes and schedules four semantic-repair probe calls against those existing candidates. It does not repeat or erase the four primary calls.

The first revision-2 draft is preserved byte-for-byte under `../prelaunch_subrevisions/revision2_draft1`, with a per-file snapshot receipt. The current prelaunch revision adds one narrow correction after a 32-row decision-core audit: false or partial status claims that could be read as authoritative new user updates are now explicitly tied to the text record the assistant just displayed.

## What changed

All 32 training specifications now require an authoritative **user** context turn before the correction decision. The turn contains a frozen evidence core. An assistant may restate that state for conversational flow, but the prompt and protected record explicitly say that the assistant statement is not independent evidence. The user decision also has a frozen core: a tone cue may surround it, but it may not add or remove a fact, value, referent, state change, or operation.

Five demonstrated decision-core ambiguities were repaired: `pilot48_02_false`, `pilot48_02_partial`, `pilot48_04_partial`, `pilot48_10_false`, and `pilot48_10_partial`. Each now says that the disputed status is what appears in the catalogue/list just shown; any following imperative remains a distinct authoritative new instruction. The remaining false/partial version-edit rows already use explicit historical or “latest version” wording, while inference rows explicitly reason from visible facts. No other training core was changed. Tone wrappers are additionally forbidden from changing a declarative core into a question or altering its punctuation.

The train unresolved cases were corrected before any further authoring:

- `pilot48_01_unresolved` exposes only the current grocery snapshot and says older versions are unavailable. The hidden initial apple/event history is removed from this row.
- `pilot48_04_unresolved` exposes only the current packing snapshot and says the addition history is unavailable. The hidden order event is removed.
- `pilot48_03_unresolved` has no hidden value 60. Its atom is an unresolved prior-duration reference, and the user wording remains exactly “Κράτα τη διάρκεια που είχαμε συμφωνήσει.”
- `pilot48_02_unresolved` preserves two possible feminine referents.
- `pilot48_06_unresolved` is phrased as an inference from watering dates, rather than an authoritative new moisture observation.
- `pilot48_07_unresolved` makes the university claim an inference from an incomplete route excerpt.
- `pilot48_08_unresolved` makes the delivery-date claim an inference from inventory counts, rather than a reported new date.
- `pilot48_10_unresolved` leaves two text-list cancellation targets available and does not pick one silently.

All cancellation rows now operate on an explicit text catalogue inside the conversation. Their contract forbids claiming that a scheduled reminder, notification, calendar item, or other external action changed without a supplied tool result. A clear new user instruction still changes the specified text state even if its historical preface is false. An ambiguous reference leaves the text state unchanged and asks which entry.

The same general authoring contract is bound to the 8 dev and 8 sealed final-confirmation inputs before generation. Final content remains outside tuning and selection; the visible gate summary contains counts and hashes only. The silence case remains quarantined. Family partitions and the accepted scale allocation remain 600 training decisions plus 60 dev and 60 final-confirmation decisions.

## Probe and cumulative budget

The next queue contains four train-only semantic repairs for `pilot48_01_true`, `pilot48_06_false`, `pilot48_10_partial`, and `pilot48_03_unresolved`. Its payloads include the immutable prior accepted candidate, the revised visible-evidence contract, and the named defect. The queue has been assembled and hash-bound, but not launched.

The original absolute budget remains 118 calls:

| Call accounting | Count |
|---|---:|
| Primary calls already consumed in revision 1 | 4 |
| Revision 2 semantic-repair probe reserved | 4 |
| Remaining primary authoring | 43 |
| Remaining retry allowance | 12 |
| Remaining semantic-repair allowance after probe | 8 |
| Greek correction allowance | 47 |
| Cumulative maximum | 118 |

Because revision 2 has its own run-state directory, its runner-level ceiling is 114 **additional** calls. Adding the four immutable prior calls gives the unchanged cumulative maximum of 118. The next run must use the four-job probe queue first, with at most four workers and four new calls.

## Verification

The prelaunch verifier recomputes all 48 truth labels and before/after states from their revised evidence, confirms the 8/8/8/8 training-label balance, verifies 32 user-visible training evidence contracts, checks family disjointness and the silence quarantine, binds all 43 remaining primary payloads plus the four repair payloads, validates strict schemas, and confirms the 114-additional/118-cumulative budget. The generic runner also accepted the probe bundle in read-only plan mode as four pending semantic-repair jobs. No calls were launched and no final-confirmation content was exposed in this report.
