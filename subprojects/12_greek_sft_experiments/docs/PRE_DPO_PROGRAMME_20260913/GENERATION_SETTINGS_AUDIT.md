# Generation settings and Greek correction audit

13 September 2026. Read-only inspection of generators, launch scripts, logs, saved summaries and original/edited rows, plus direct local checker probes. No model generation, dataset changes or training were performed.

**Finding:** several stages already requested Sol high. The strongest verified problems concern what the model was instructed to preserve or remove, incomplete semantic verification, and execution/provenance handling. The newer unfinished maths build requests medium by default, so higher effort is a worthwhile controlled test there. We have no measured medium-versus-high quality comparison for these datasets.

## 1. How the adaptations actually worked

**Scope correction after tracing no_robots:** this audit initially omitted the canonical `natural-greek-sft` project. The [adaptation reference](ADAPTATION_REFERENCE.md) reconstructs its developed contract and actual production prompt. Adaptation includes changing the cultural distribution while preserving the training task; the canonical Greek editor deliberately leaves those decisions intact. The later shared experiment editor is a modified contract. Do not read this table as a complete history of no_robots or as evidence that language-only editing was itself an accidental omission of semantic repair.

Settings below describe the inspected implementation and launch evidence. Many row records do not store reasoning effort or a resolved model revision; this is not a claim that every historical call's effective configuration has been independently reconstructed.

| Dataset/workflow | Generation or adaptation | Subsequent correction/verification | Evidence strength |
|---|---|---|---|
| Early Greek rewriting set | Sol high by generator default, one passage/instruction/answer per call | Separate Sol high editor; this editor covers task compliance and fidelity as well as Greek | Generator plus explicit launch script; this was a different editor contract from the later generic pass |
| First Greek maths set: translated sources | Sol medium translates/localises batches of 10; Sol high solves Greek problems blind in batches of 5 | Compare final value to reference; later Greek-only Sol medium editing | Code, saved output and editor launch log agree |
| First Greek maths set: native problems | Sol high writes problem and solution in batches of 5 | Initially high-effort second solving for upper-school cases; a later repair extends Sol high verification to risky topics in batches of 10; final-value agreement filter | Production wrapper selects Sol, despite an older helper default mentioning Luna; postfix log confirms added verification |
| Greek instruction-following set | Sol medium request/answer generation; answer generator has an effective batch default of 16 although its usage comment says 8 | Deterministic constraint checks, then Sol medium Greek edit, then constraint guard/revert | Code plus editor logs; do not infer historical batch size from the current default alone |
| Conversation suite | Sol medium for the generation calls inspected | Sol medium editor, explicitly launched with `kind=if`, 5 rows/call, 48 workers; separate final lane re-verification | Explicit launch, log, manifest and before/after records |
| Behavioural correcting set | Sol high default for scenario/writer/responder calls | Sol medium editor with dialogue guards, followed by assembly checks | Generator and launch scripts; editor log confirms medium |
| New unfinished worked-maths build | One problem/call; Sol medium default for solutions and Level-5 translation; fidelity sample escalates to high | Uses source solution/reference as a guide; no completed semantic audit of all generated solutions established | Preserved launcher omits effort override; code defaults are clear; rows omit effort metadata |
| Adapted evaluation benchmarks | Sol medium translation with checks and historical review/repair | Separate language-only guarded polish; original benchmark difficulties/ambiguities preserved | Dedicated benchmark scripts and polish report; this is separate from SFT data |
| Imported foreign datasets | Existing external targets, selection/filtering, and routed reviews | Not a corpus uniformly authored by Sol | Import/review routing scripts; source-specific audit remains necessary |

Personality also had its own generation/restyling/editor history, including Claude-generated material and Sol checks. The assumption that all datasets were produced by one Sol first pass is incorrect. The same applies to the imported maths, chat and reasoning blocks.

### Recorded coverage of the generic Greek pass

| Input snapshot | Rows | Accepted edits | Reverted edits |
|---|---:|---:|---:|
| First maths build | 14,215 | 876 | None reported |
| Greek IF combined initial versions | 20,664 | 12,361 | 163 |
| Greek IF later version | 9,411 | 5,315 | 70 |
| Conversation suite before final re-verification | 3,437 | 2,987 | None reported by editor |
| Behavioural correcting dialogues | 600 | 235 | 34 |

These are editing-stage counts, not the final training mixture's row counts. Reverted means the original was retained; it does not establish that the original was semantically correct. Self-rated “Greekness” is not an independent quality measurement.

## 2. Verified issues beyond reasoning effort

### The generic Greek editor was deliberately not a maths/factual editor

Its instructions say to correct only spelling, grammar, syntax and naturalness, preserve content and not judge the correctness of information. Maths-specific instructions additionally prohibit changing numbers, operations, symbols, units or the final answer. It sees the user problem but returns only edited assistant turns; it cannot repair a defective problem statement through that output contract.

The maths guard compares the extracted old and new final answers. It does not verify each step, required units, assumptions, or all mathematical expressions. It even permits the case where both extracted answers are empty.

Two original rows remain unchanged after the editor:

- `gm_nat_301_3`: describes multiplication yielding square metres as computing “part of the volume”. The final 360 litres is correct, but that explanatory step confuses area and volume.
- `gm_nat_618_4`: the prompt asks for cents; the answer gives 3.62 euros and introduces rounding. Both the original and edited row carry `second_solve`. Agreement did not certify the requested unit or explanation.

These are specific verified defects, not an estimate of the whole dataset's error rate.

### The answer-equivalence checker ignores units

Directly calling the existing local helper returned true for both:

| First answer | Second answer | Existing `equiv` result |
|---|---|---|
| 80 λεπτά | 80 ώρες | True |
| 3,62 € | 3,62 λεπτά του ευρώ | True |

Ignoring units can be useful in a narrowly defined final-number benchmark scorer, but it cannot serve as the complete acceptance check for unit-bearing SFT targets. Add a task-specific quantity/unit check and enforce the question's requested output. A correct final number cannot certify a derivation or faithful translation.

### The shared Greek style brief can conflict with the task

The generic editor prepends task-specific instructions, then imports a personality/rewrite brief that includes blanket removal of assistant self-reference. Its final schema differs from the embedded brief's older output instructions. This needs one coherent editing contract with explicit task-preservation precedence.

In row `S2_00122`, the recorded edit removes “Θα απαντώ με μία πρόταση.” expressly because it is self-reference. That sentence is a legitimate acknowledgement of a persistent user instruction. The editor's launch used `kind=if`; rows lacked the constraint list used by that guard, so the editor stage accepted the edit. The later suite checker provided the actual protection.

Before/after comparison establishes **67 newly empty supervised assistant turns across 56 rows**. All 56 affected rows are absent from the reverified export. The full re-verification retains 3,284 of 3,437 rows, rejecting 153 in total. We have established the editor introduced the empty turns; we have not attributed all 153 failures to the editor. Nor does this show that empty targets reached training—the later gate caught these rows.

### The first maths set already had high-effort solving and extra repair

The postfix log records 2,894 additional native rows routed for second solving, 4,689 verified native rows in total, 253 incomplete multipart cases, and 350 diagram-containing translated problems quarantined. The rebuilt pool contains 14,215 rows: 9,107 reference-checked, 3,797 second-solve checked and 1,311 without a second solve.

An earlier native summary still reports the pre-postfix state. Use the correct output snapshot and rebuilt manifest rather than combining inconsistent stage summaries. Higher effort did not remove the need for these repairs, and a disagreement filter also changes the retained difficulty distribution.

### The newer maths build has operational and provenance weaknesses

- Its instructions request a complete worked solution, typically 100–250 words, with all steps. That word band may be a poor fit for some problems. It also says not to add/drop a step while asking to expand skipped source steps; distinguish unchanged mathematics from permissible explanatory expansion.
- The preserved launcher starts 72 solution workers plus 48 translation workers. The log contains many empty/invalid-JSON retries; their cause is not established by those exceptions alone. This is an execution/reliability issue, not direct proof that concurrency made individual successful solutions less accurate.
- Current saved Level-5 translations contain 2,146 records for 1,457 IDs; solutions contain 3,010 records for 1,168 IDs. These are not equivalent unique-coverage counts. Investigate duplicate launch/input/output handling before choosing a canonical record.
- Resume logic skips existing IDs without binding them to model, effort, prompt or source hashes. Re-running the same output directory at high effort would leave existing medium results untouched and could create a mixed-setting corpus.
- The common CLI wrapper requests a model and effort, but does not persist resolved per-call settings, exit status, token usage and completion details in the dataset record. It has a 1,500-second default timeout, with some callers using 900 seconds. No explicit model output-token cap or temperature is supplied there. Do not invent a historical value from provider defaults.

## 3. Recommended changes

**Aim for good first-pass targets, then verify them.** A capable model can produce useful examples in one generation call. Rewriting every valid answer through another unconstrained model pass adds cost and another opportunity to damage it.

1. Use one explicit, non-contradictory authoring contract per task. For maths: sound premises, complete solution, correct dimensions, requested units and justified rounding. Permit “source inconsistent / insufficient information” rather than forcing the reference answer.
2. Use **Sol high** as the provisional default for new maths solutions and evidence-dependent correction dialogues. Use **xhigh selectively** for the hardest competition problems and disputed cases. The older maths-solving pipeline already requested high; do not describe this as a universal upgrade from medium.
3. Keep **medium provisionally for straightforward language polish** under strict preservation checks. Repair the shared brief first; raise effort only if a controlled comparison shows fewer residual language errors without more semantic changes.
4. Use one hard problem or one complete dialogue per semantic authoring/review call. Batch simple edits by token budget. A fixed count of 15 long multi-turn rows can be much more demanding than 15 short answers. Reduced batching is a hypothesis to test, not a proven cause of historical defects.
5. Validate semantics independently: source-backed answers, executable maths/state checks, instruction satisfiability and a sampled step/translation audit. A second Sol context is useful but does not make agreement independent ground truth.
6. Route failed or doubtful rows to a **semantic repair pass**, allowed to repair the actual defect and its dependent fields with provenance. Then perform Greek correction and rerun the applicable semantic/format checks. Do not ask the language-only editor to preserve a unit error and repair it simultaneously. The [task prompt pack](prompts/README.md) preserves this distinction in its separate instructions.
7. For dialogue, protect useful acknowledgements and requested self-reference; remove only gratuitous mannerisms. Verify all supervised turns are nonempty unless an explicitly supported silence task calls for otherwise. Keep planted erroneous context masked and unchanged.
8. Record model, resolved effort, prompt/source hashes, row ID, attempt, completion status and token counts. Use a new versioned output namespace for each settings comparison. Fail the completion gate on missing IDs or unresolved duplicates.

The [official Sol model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol) confirms high and xhigh are supported. It does not establish which setting optimises these Greek datasets. Reasoning effort and final-answer length are different controls: a longer visible derivation is not evidence of greater internal reasoning, and raising effort need not imply padding every training target.

### Small settings experiment before any broad regeneration

Propose 40 frozen cases: 20 competition maths, 10 dialogue-state/correction and 10 constrained Greek editing cases. Include both ordinary cases and known failure types, held apart from final benchmark confirmation.

After repairing contradictory instructions, run the same cases at medium, high and xhigh, with identical inputs and one case per call: **120 generation calls**. Blindly assess correctness, units, premises, instruction fulfilment, Greek quality, unwanted changes, completion and cost/time. Reserve at most 80 additional review/retry calls for a first 200-call envelope, using batch review only where context permits. Record unresolved judgments rather than calling them passes.

This compares future settings under a repaired contract; it does not isolate the historical contribution of old prompts or batch sizes. A later batching comparison is conditional on residual failures. Choose the least costly setting meeting the quality requirements, then repair affected families and apply checks across the corpus. No such comparison has been executed in this audit.

## Evidence register

Source root: `/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data`.

- `math/math_pilots.py`, `math/build_math.py`, `math/postfix_cut1.py`, `math/mathlib.py`: generation, solver settings and checking contracts.
- `math/cut1/out/summary.json`, `math/cut1/edited/summary.json`, corresponding original/edited rows, `queue_runner.log`, `math/cut1/postfix.log`: saved execution and verified examples.
- `edit_pass.py`, `personality/personality_brief.py`, `gen_greek_rewrite_edit.py`: effective editing instructions and guards.
- `pipeline_stage3.sh`, `convskills/v2/edit.log`, `convskills/v2/rows_verified.jsonl`, `convskills/v2/edited/rows_edited.jsonl`, `convskills/v2/reverify/{manifest.json,rows_final.jsonl}`: suite settings and direct before/after verification.
- `robustness/build_correcting.py`, `robustness/correcting/scale/edit.log`: behavioural generation and Greek editing.
- `math/cut2/run_batches.py`, its saved output logs/JSONL, `benchmarks_el/bench_lib.py`, and the preserved maths launcher: new solution settings and resume behaviour.
- `greek_if/run_pilot.py`, `benchmarks_el/polish.py`, `benchmarks_el/polish_report.json`: IF defaults and distinct benchmark-polishing workflow.
- `/Users/foivoskarounos-zamparloukos/sft_annot/sol_chain.sh`: explicit early high-effort Greek rewriting edit and medium-effort import review routing.

The source paths above identify inspected evidence; no source file was modified. Stage summaries and current code are distinguished from complete per-call provenance, which remains incomplete.
