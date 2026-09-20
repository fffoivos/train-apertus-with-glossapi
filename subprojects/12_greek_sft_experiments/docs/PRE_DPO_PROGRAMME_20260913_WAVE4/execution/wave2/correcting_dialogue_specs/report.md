# Correcting/dialogue authoring wave: frozen pilot specifications

**Frozen:** 13 September 2026, 16:15:01 Europe/Athens  
**Artifact unit:** one labelled assistant decision, not one conversation or one raw turn  
**Current scope:** 48 input specifications only; no bulk conversations and no production dataset were generated.

## Pilot balance

The pilot contains twelve isolated scenario families, with one true, false, partial, and unresolved decision in each family. It therefore has exactly 48 labelled decisions:

| Truth category | Pilot decisions |
|---|---:|
| True | 12 |
| False | 12 |
| Partial | 12 |
| Unresolved | 12 |

The pilot is deliberately category-balanced for authoring review. The frozen 600-decision scale target remains 200 true, 200 false, 100 partial, and 100 unresolved.

Tone is also balanced at specification level: 12 cooperative, 12 neutral, 12 assertive, and 12 frustrated-but-civil decisions. Each spec carries a concrete tone instruction. The generated user turn must realize that tone while keeping the evidence-linked claim atoms unchanged.

## Family isolation and split plan

Every family is assigned wholly to one split before authoring:

- Train: eight families and 32 pilot decisions.
- Development: two families and 8 pilot decisions.
- Final confirmation: two sealed families and 8 pilot decisions.

The twelve families cover grocery-note editing, a volunteer roster, a workshop schedule, a packing list, a café order, plant-care inference, a bus-route graph, storeroom inventory, a library hold, reminder cancellation, recipe revision, and delivery cancellation. All are newly specified fictional everyday settings. None derives from a public benchmark.

The scale manifest allocates 200 families without leakage:

- 100 four-label families contribute one decision in each category.
- 100 paired families contribute one true and one false decision.
- Train receives 140 families and 420 decisions: 140 true, 140 false, 70 partial, 70 unresolved.
- Development receives 30 families and 90 decisions: 30 true, 30 false, 15 partial, 15 unresolved.
- Final confirmation receives 30 families and 90 decisions with the same category totals as development.

This arithmetic gives the requested 600 decisions exactly. The pilot's twelve families occupy four-label slots. The manifest records the remaining family slots separately for each split.

The family identifier, entities, state graph, evidence pattern, paraphrases, and numeric template must remain in their assigned split. Final-confirmation families are sealed after specification and may not guide prompt tuning.

## Teaching contract incorporated

Each specification contains one decision and separates the evidence-backed historical claim from any current user request. In false-history cases, a new personal preference, list change, or cancellation instruction is still applied as authoritative current state. For example, the café family records that the prior order was decaffeinated, corrects a false recollection that it was regular, and still changes it to regular when the user asks for that change now.

True claims require a useful acknowledgement and state update. False claims require a brief correction and execution of any valid current instruction. Partial claims require the response to separate valid and invalid atoms. Unresolved claims require one targeted question and no invented state.

Every optional prior assistant turn is an input-context device only. It must be derived from the evidence, marked `train:false`, and preserved rather than silently rewritten during target authoring. The generated target may not use an assistant assertion as oracle evidence.

All targets prohibit stock argumentative endings, generic follow-up offers, and automatic agreement or disagreement. The response should stop once it has adjudicated the claim and completed the active request.

## Executable oracles

`verify_specs.py` independently recomputes every truth category and state outcome from the supplied evidence:

- **Version editing:** replays ordered `set`, `add`, and `remove` events to reconstruct the current version, evaluates the historical claim, and then applies a separately represented current update.
- **State inference:** evaluates arithmetic, date-index, Boolean, and graph-reachability formulas from the evidence values. Missing facts remain unknown rather than being inferred from the expected label.
- **Cancellation:** replays task statuses, distinguishes historical cancellation from a valid cancel-now instruction, preserves unrelated active tasks, and checks exact acknowledgement when requested.

The verifier passed all 48 records, with 24 version-edit decisions, 16 state-inference decisions, and 8 cancellation decisions. It also validates the 600-target arithmetic, one-split-per-family rule, balanced tones, masked-context requirements, and the exact `Ακυρώθηκε.` acknowledgement fixture.

One cancellation spec, `pilot48_12_unresolved`, is intentionally blocked. Its command “Άσ' το και μη γράψεις τίποτα” has an ambiguous task reference and requests silence without defining how silence is represented as a trainable target. Under the dialogue contract, the authoring queue must return blocked rather than invent an empty or “Understood” assistant message.

## Files

- `family_split_manifest.json` freezes pilot families, split membership, remaining scale slots, target quotas, and leakage rules.
- `pilot48_input_specs.jsonl` contains the 48 decision-level authoring inputs, evidence, claim atoms, current requests, tone requirements, mask plans, oracle states, and expected response moves.
- `verify_specs.py` is the independent executable oracle.
- `verification.json` records counts and hashes from construction.
- `oracle_verification.json` records the independent verifier pass.
- `build_specs.py` recreates the frozen artifacts deterministically apart from the receipt timestamp.

These artifacts prepare the bounded authoring queue. They do not authorize the 600-row build, promote any candidate into training, or replace the required Greek and semantic review of generated dialogues.
