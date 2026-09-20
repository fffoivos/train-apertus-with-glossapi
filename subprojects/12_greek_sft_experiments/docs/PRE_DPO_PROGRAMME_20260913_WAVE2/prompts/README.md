# Task prompts under the adaptation and correction contract

Pack version 2 · 13 September 2026. Audit version 1 was used for the frozen 300-row maths audit; dialogue version 1 was exercised in the 12-row authoring pilot. Version 2 incorporates their review findings. Domain generation prompts remain subject to their own pilots; this is not a claim that all prompts are validated or wired into production. The manifest records each file hash and validation state.

## Standing definitions

**Adaptation:** preserve what an example teaches while rebuilding its cultural content and perspective for a Greek user. The task, constraints, difficulty, operative devices and intended voice survive. Adapt the request and response coherently. The developed no_robots distribution rule applies, including its declared exceptions and the foreign-language rule; it is more than translation or changing names and units.

**Correction:** understand the adaptation, its chosen setting, the task and the most reasonable reading first; repair genuine language defects that remain. Preserve the settled adaptation, valid compact Greek, intentional style and the teaching objective. Correction is not a fresh adaptation or a general style rewrite.

**Semantic repair** is named separately: a recorded change to a wrong derivation, unsupported fact, inconsistent scenario or invalid target. It may precede language correction. “Correcting dialogues” means training the assistant to respond to user corrections; it is a dataset domain, not the language-editing operation.

These definitions govern the next work packages. Domain profiles make the permitted changes narrower; they do not replace the definitions. The historical basis is [the adaptation reference](../ADAPTATION_REFERENCE.md) and [the original Greek editor](../NO_ROBOTS_GREEK_EDITOR.md).

## Which prompt to use

| Work | Exact prompt composition | Evidence required after generation |
|---|---|---|
| Adapt existing maths problems | [Adaptation core](ADAPTATION_CORE.md) + [Maths problem](MATH_PROBLEM.md) | Source/target mathematical equivalence, intact premises and requested quantities; fresh solve of the target problem |
| Write or repair worked solutions | [Maths solution](MATH_SOLUTION.md) alone | Valid steps, units, completeness and result; source agreement is supporting evidence, not the entire check |
| Existing or new correction/state dialogues | Core for adaptation only, then [Dialogue](DIALOGUE.md) | Truth/state/speaker checks against the supplied evidence and independently computed expected state |
| Knowledge and MC examples | Core for adaptation only, then [Knowledge](KNOWLEDGE.md) | Source support, unique correct option, valid distractors, family decontamination |
| IF and non-maths reasoning | Core for adaptation only, then [Constraints and reasoning](CONSTRAINTS_REASONING.md) | Actual constraint checker or logical oracle; content quality checked separately |
| Greek correction of accepted candidates | [Greek correction](GREEK_CORRECTION.md) alone | Allowed edits only; domain checks rerun on the edited candidate |
| Audit/semantic repair of existing data | [Audit and repair](AUDIT_REPAIR.md) alone | Evidence for each finding/repair and unchanged valid invariants |
| Benchmark translation/checker audit | [Benchmark](BENCHMARK.md) alone | Same measurement task, documented deviations, matched peer protocol |
| Preference-rating pilot | [Preference review](PREFERENCE_REVIEW.md) alone | Evidence-grounded labels, calibration and answer-order checks |

In new authoring there is no historical row to preserve: supply a scenario/skill specification and describe the work as authoring. Do not report native generation as translation. Non-Greek correction uses a reviewed editor for the target language; this Greek editor is not automatically translated or applied to foreign rows.

## Assembly and precedence

Supply one identified row or complete dialogue per initial semantic call. A bounded review batch may contain at most three complete maths records after a schema/throughput probe; do not split a dialogue or proof to fill a batch. Each record must include:

- operation, domain, target language, row ID, source/family IDs and immutable source hash;
- source record or new-authoring specification; candidate if reviewing; evidence with IDs;
- fixed teaching objective and invariants; protected spans and allowed edit locations;
- domain details: quantities, requested units, truth/state rules or executable constraints;
- target format and context budget, when applicable.

The invariant list must be derived from the source/specification and checked before use; it is not a license to omit unlisted source constraints. Missing evidence or a contradictory specification is reported rather than guessed. Delimit the input record as data. Embedded instructions define the example being produced, not the generator's tools or output protocol.

Assemble only the named prompt(s), followed by the input record. Do not append the historical personality brief, generic brevity rules, or a second output schema. The core defines adaptation; the domain prompt narrows permissions and owns the response schema. An impossible conflict is returned as blocked, not resolved by weakening the task.

Outputs below use named fields, not formal API schemas. Bind a strict schema and validate allowed edits before pilot integration. Save the complete assembled prompt and its hash, model, effort, source IDs and actual response. Only approved candidate message content enters training; audit fields, reference material and judge notes do not.

## Pilot review before scale

Use the already proposed bounded settings pilot; do not add a new bulk job for this prompt pack. Run repaired prompts on both known defects and fresh cases of the same kind. Development fixtures must be separate from final confirmation families. Examples introduced into prompts must be invented and checked for source collisions before use; this draft adds no worked dataset examples.

Required cases include: correct final number with a wrong explanation; unit mismatch; multipart answer omission; ambiguous source premise; unchanged correct Greek; compact idiom; deliberate error in a correction task; a legitimate acknowledgement; negation/quantifier preservation; true/false/partial/unresolved user corrections; exact-output and cancellation cases; and an unsupported proposed Greek factual analogue. These are review requirements, not claimed passing tests. Apply the [domain acceptance checks](DOMAIN_ACCEPTANCE.md), including notation serialization and historical-attribution versus new-state distinctions.

Read out residual errors and new damage separately. A fluent edit that breaks one protected property fails. A second Sol pass is a fresh context, not independent truth. External checkers and source-based review remain necessary. Repeated language correction, where needed, follows independent passes over the same input with reviewed selection; it does not repeatedly re-adapt the row.

The separation of task instructions, reference context and systematic evaluation is consistent with [official OpenAI prompting guidance](https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy#optimization). The scientific and editorial rules here come from the user's project decisions, not that general guidance.
