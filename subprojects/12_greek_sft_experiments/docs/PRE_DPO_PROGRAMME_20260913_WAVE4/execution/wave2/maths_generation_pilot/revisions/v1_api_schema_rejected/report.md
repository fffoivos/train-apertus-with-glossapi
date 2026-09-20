# Revised maths generation pilot — prepared, not launched

## Scope and frozen inputs

This bundle prepares 32 problems and 88 primary model calls. It has not launched a model call, changed a production corpus, or changed an official score. `inputs.jsonl` keeps the reference solution or final only for later adjudication; no solve, xhigh comparison, or blind-verification payload includes those fields.

The 16 fresh rows come from the locally cached public MATH training split at the exact path and SHA-256 in `manifest.json`. The project documentation records MATH as MIT licensed. Selection uses seed `maths-generation-pilot-v1-20260913`, Level 5 only, deterministic subject-local hash ordering, and these quotas: Algebra 2; Intermediate Algebra 2; Prealgebra 2; Geometry 3; Number Theory 2; Counting & Probability 3; Precalculus 2. It excludes prior-wave normalized matches, all MATH-500 exact normalized matches, every candidate sharing any normalized 13-gram with a MATH-500 row, every candidate sharing more than half its normalized 8-grams with one MATH-500 row, and every problem containing a diagram/figure dependency marker. This is a contamination screen against the local benchmark cache, not a claim of universal deduplication.

Fresh IDs are:

- Algebra: `fresh_math5_line_1379`, `fresh_math5_line_1334`
- Intermediate Algebra: `fresh_math5_line_3775`, `fresh_math5_line_4646`
- Prealgebra: `fresh_math5_line_5977`, `fresh_math5_line_6029`
- Geometry: `fresh_math5_line_3093`, `fresh_math5_line_2676`, `fresh_math5_line_3125`
- Number Theory: `fresh_math5_line_5324`, `fresh_math5_line_4821`
- Counting & Probability: `fresh_math5_line_2429`, `fresh_math5_line_2507`, `fresh_math5_line_1950`
- Precalculus: `fresh_math5_line_6930`, `fresh_math5_line_7113`

The eight repair rows are seven substantive first-wave cases with valid displayed Greek tasks plus one independently confirmed Level-4 proof repair: `math5_139`, `math5_77`, `math5_537`, `math5_1014`, `math5_630`, `gsm_1253`, `math5_436`, and `gm_math_2231`. `gsm_1334` was removed because its only remaining issue was optional unit presentation, not a substantive repair. The displayed problems for `math5_77`, `math5_537`, and `math5_630` are frozen after narrow control-character restoration (`\frac`, `\cos`, `\angle`); every replacement and its count is recorded in `source_problem_repairs`. These are markup repairs before solving. They do not alter a premise or force a reference answer. For `math5_630`, the exact displayed variant is the pilot input; the unresolved historical variant pairing remains documented rather than inferred.

The eight controls are `gm_gsm_3835`, `gm_gsm_3096`, `gm_math_2731`, `gm_math_1054`, `gm_math_1745`, `gm_math_837`, `gm_math_3507`, and `gm_math_3924`. They span GSM and MATH Levels 1–4 and were independently adjudicated as controls. Regeneration is compared with the retained row; it is not presumed to improve it.

## Calls and batches

| Stage | Calls | Effort | Purpose |
|---|---:|---|---|
| Fresh problem adaptation | 16 | high | English MATH problem to a faithful Greek problem, with no solution |
| Worked solution | 32 | high | Solve each settled Greek problem from scratch |
| Hard comparison | 8 | xhigh | Independent solve for four fresh and four known-hard repair rows |
| Solution-blind verification | 32 | high | Second from-scratch solve with no candidate/reference output |
| Primary total | **88** | | Frozen in `queue.jsonl` |
| Conditional source review | at most 8 | high | Only for blocked, ambiguous, contradictory, or text-only-impossible problems |
| Conditional Greek correction | at most 16 | high | Only after semantic acceptance identifies a language-only defect |
| Retry allowance | at most 24 | same as job | Maximum two attempts for any one job |
| Absolute total | **at most 136** | | Runtime-enforced ceiling; below the requested 160 |

The eight preselected high-versus-xhigh rows are `fresh_math5_line_3775`, `fresh_math5_line_1379`, `fresh_math5_line_4646`, `fresh_math5_line_6930`, `repair_math5_1014`, `repair_math5_630`, `repair_math5_139`, and `repair_math5_436`. The master queue is unchanged when a four-call probe is used. `probe_queue.jsonl` is a frozen exact subset containing the first four fresh adaptation jobs, and `probe_payloads.jsonl` materializes their outbound data for review. The read-only plan is `run_queue.py --queue probe_queue.jsonl --limit-new-calls 4`; execution remains separately gated.

`batches.json` enumerates the four logical batches. Dependencies gate execution: a fresh solve or verification can use an adaptation only when its schema-valid output has `status: candidate` and a nonempty `problem_text`. `blocked` and null text cannot silently satisfy the dependency. A source repair candidate is not solved until a reviewer accepts it and freezes a new problem hash.

## Prompt and output sizes

The frozen prompt templates have these exact base lengths before the per-row JSON payload is inserted: adaptation 6,064 characters / 859 whitespace words; high solution 2,746 / 394; blind verification 2,808 / 395; source review 6,257 / 883; Greek correction 3,766 / 539. Fresh English problems range from 101–512 characters and 19–87 whitespace words. Reused repair Greek problems range from 116–1,230 characters; controls range from 95–305 characters.

Expected schema-conforming adaptation outputs are usually 1,000–4,000 characters because they include invariants and change receipts. Worked solutions and blind verifications are expected to be roughly 800–8,000 characters, depending on proof complexity. These ranges are planning estimates, not acceptance constraints: the canonical solution prompt explicitly rejects arbitrary word bands and requires enough reasoning to verify the result.

## Acceptance and adjudication gates

The runner accepts an individual call artifact only when it validates against the declared generic JSON schema, reproduces the exact `row_id`, and matches the frozen input, payload, template, schema, model, effort, and final prompt hashes. It records immutable attempt receipts, per-call event JSONL, stderr, PID, elapsed time, exit code, and reported usage. A cross-process file lock prevents duplicate runners in one state directory. Calls use the clean project invocation (`--ignore-user-config`, `-C /tmp`, read-only sandbox, disabled apps/plugins/code host), a 1,200-second timeout, stop-on-quota/rate-limit behavior, at most two attempts per job, up to eight workers, an optional four-new-call probe, and a runtime cap no larger than the manifest's 136.

Schema acceptance is only transport acceptance. Promotion needs semantic review after outputs exist:

1. Confirm each adaptation preserves quantities, roles, units, domains, conditions, requested parts, and intended difficulty. Source ambiguity stays separate from adaptation and solution repair. A diagram-dependent task without sufficient information is blocked.
2. Compare high and solution-blind derivations without exposing either to the stored reference. Check all requested parts, domains, cases, units, and final expressions. Agreement is evidence, not proof; disagreement requires adjudication.
3. Reveal the frozen reference only after independent solving. Treat a reference mismatch as a claim to investigate; do not rewrite a valid problem or derivation to force the reference.
4. Use the eight xhigh calls only as a reasoning-effort comparison on the preselected hard set. Do not select rows after seeing outcomes.
5. Run Greek correction only for a named language defect after mathematical acceptance. Preserve equations, quantities, units, assumptions, proof logic, and final answers. Valid concise proofs and idioms remain valid; in particular the prior independent review preserves concise `math_550`, idiomatic `κατάστημα της`, and acceptable uninflected `Έμμα` where those controls recur.
6. Keep all outputs as candidates. Promotion into training data requires row-level semantic acceptance and a new reviewed assembly receipt outside this pilot.

## Provenance and reproducibility

`manifest.json` binds all local source caches and every dispatch-relevant input, queue, schema, prompt, and runner file by SHA-256. The outbound payload contains public MATH/GSM problem text, project-generated Greek candidates for existing rows, and non-sensitive stage metadata. It contains no credentials or private conversations. `adaptation_receipts_reused.jsonl` preserves the adaptation-to-solution handoff for the 16 existing Greek problems; the 16 fresh handoffs will be produced by the adaptation jobs. `build_pilot.py` reproduces deterministic selection and all frozen preparation artifacts from the cited local caches.
