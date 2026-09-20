# Balanced correcting-dialogue authoring pilot — prepared, not launched

This package freezes 48 decision-level native Greek dialogue specifications under the revision-2 family split. It prepares 47 authoring calls and quarantines the one unresolved cancellation-plus-silence item whose trainable silence representation is unspecified. No dialogue model call or production write was made.

The split remains 32 train, 8 development, and 8 final-confirmation specifications. Families, state graphs, entities, and numeric templates occur in one split only. Final-confirmation inputs and queues live under `sealed/final_confirmation`; root-facing review is limited to aggregate gate summaries, and final content cannot influence prompt tuning or candidate selection.

The initial probe is a fixed subset of four train calls. It contains one true, one false, one partial, and one unresolved decision and covers version editing, state inference, and cancellation. Only after all four pass complete semantic, oracle, mask, speaker-ownership, and Greek review does the plan allow the remaining train queue, with at most eight workers.

The call envelope is 47 primary authoring calls, at most 12 retries, at most 12 conditional semantic-repair calls, and at most 47 separate Greek-correction calls: an absolute cap of 118. The retry budget is operationally bounded to four calls in each split state. The split call ceilings are 76 train, 22 development, and 20 final confirmation, which also sum to 118. The four probe calls are part of the 47, not extra. Planning usage is about 360,000 input and 133,400 output tokens; the receipt gives a price formula because no applicable contracted Sol token rate is asserted here.

Every input preassigns stable message IDs. User turns are unsupervised; any earlier assistant context is fixed and `train:false`; exactly one final assistant decision is `train:true`. Exact acknowledgements are protected. Historical claims and authoritative current updates are represented separately. The quarantined silence item is never dispatched and cannot be replaced with an invented “Understood” target.

Semantic repair and Greek correction use different prompt/schema pairs and different gates. Semantic repair may change only demonstrated state, ownership, masking, or task defects. Greek correction runs only on a semantically settled candidate and cannot change truth, state, action, quantities, masks, or protected strings.

`verify_prelaunch.py` recomputes split, family, quarantine, probe, call-cap, runner-hash, prompt-marker, artifact-hash, and strict-schema invariants. `verify_outputs.py` is ready for post-run message-ID, train-mask, exact-response, truth-label, and state-transition checks; these deterministic checks do not replace full semantic or Greek reading.

The active goal authorizes later execution after the listed gates pass; specifications alone are not quality-ready for scale. This bounded task stops at preparation and does not add another blanket approval requirement.
