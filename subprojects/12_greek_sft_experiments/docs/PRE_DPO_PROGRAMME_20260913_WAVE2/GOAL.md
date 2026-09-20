# Active goal and adaptive execution contract

Owner instruction, 13 September 2026: fix a new SFT dataset mix so the trained model wins fairly against the best Krikri version across all-round benchmarks and measured dialogue quality, with high-quality Greek and transparent published datasets. Continue until the plan is done; revise the plan after every result and work quickly and effectively.

The Codex goal is active. This document records the operational definition; it does not declare that a competitive win is guaranteed or already achieved.

## Scientific completion

- Produce a frozen, corrected SFT mix with G/F/P versions assigned from actual dataset changes, and a reproducible trained checkpoint. Preserve the earlier objective of comparable capability to Apertus-8B-Instruct in English, French, German, Spanish, Portuguese and Italian, alongside the Greek competitive objective.
- Compare against current official Krikri instruction releases under matched tasks, full completion accounting, native model templates, a fixed judge configuration and declared decoding budgets. Verify which release is strongest; if releases trade wins, retain both and show the stronger peer on each endpoint. Never select the weaker release to make our claim easier.
- Freeze the critical endpoint list, subsets, scoring rules, family splits, uncertainty treatment and allowed exclusions before reading the new candidate's scores. Report every benchmark and language; an overall average cannot hide a material capability failure. Distinguish item-level estimates from family- or conversation-level uncertainty. Missing, truncated, unjudged or invalid cells cannot become wins.
- Establish broad benchmark and dialogue superiority with the agreed measurements, including problem solving, knowledge/retrieval, reasoning, instruction following, context/state handling, appropriate correction, usefulness and stopping. Ties, unresolved uncertainty and regressions remain visible and drive the next iteration; do not redefine success after seeing the result.
- Assess generated Greek for naturalness, grammar, idiom, terminology, register, cultural coherence and task fidelity in blind source-aware review. Do not equate benchmark accuracy with Greek quality, or a second Sol judgment with independent truth. Preserve legitimate Greek wording when no defect is demonstrated.

## Dataset transparency and release completion

Prepare a release package with source IDs and immutable revisions, source/license inventory, reproducible selection and adaptation recipes, exact prompts and model/effort records, correction/semantic-repair histories, rejected/uncertain counts, train/dev/test-family separation and contamination checks, tokenizer/template hashes, rendered and supervised token weights, training configuration, evaluation scripts and complete results. Explain inherited provenance gaps rather than inventing them. Where redistribution is restricted, supply an honest reconstruction recipe and state what cannot be distributed. Compare this evidence with the verified Krikri release materials before claiming greater transparency.

Publication artifacts must be ready for inspection. The existing restriction on pushes to `Greekpt/*` remains until the owner explicitly authorizes that release; preparing the package and local revisions is authorized now. Do not send messages to other people or publish private material as part of unattended execution.

## Adaptation, correction and rebuilding decisions

- Preserve sound source teaching and accepted adaptation; repair evidenced local defects.
- Re-adapt complete source examples when cultural adaptation fundamentally missed the brief, or problem premises changed.
- Regenerate solutions from valid Greek problems when derivations are defective; do not gratuitously re-adapt sound problems.
- Rebuild a scenario family when its evidence, task design or provenance cannot be trusted. Re-export tool payloads from pinned upstream sources rather than guessing lost text.
- Compare repair and fresh adaptation on the same source sample where the choice remains uncertain. Judge residual defects, task/cultural fidelity, new damage, usable coverage and cost per accepted example. Keep uncertain records out of the next training candidate until resolved.

## Iteration and efficiency

After each audit, generation pilot, repair review, measurement or training result: record the result and evidence; mark the relevant hypothesis supported, rejected or unresolved; update the plan and dataset disposition; price the next useful experiment; dispatch independent preparation/review concurrently; then run the next stage only when its dependencies pass. Keep an append-only decision log and current state file so another agent can continue without repeating completed work.

Use bounded Sol/high semantic work by default, with the measured eight-worker queue plus up to three independent Sol task owners. Increase queue concurrency only after checking quota, latency and active processes; twelve queue workers is an optional next-step ceiling, not a throughput claim. Keep each dispatched batch below 200 calls including retries and use a shared concurrency accounting policy. Scale successful families rather than waiting for every optional dataset, and avoid simultaneous uncontrolled scientific changes.

GPU time belongs to ready measurements and training. Prepare source checks, repair candidates and judging inputs while CSCS jobs run. Reuse canonical CSCS contracts and compatible qualification receipts; record exact scheduler dry-run evidence before allocation. No idle allocation should wait for Sol to finish data preparation.

## Budget and stopping boundaries

The existing cumulative SFT cap remains CHF 230. The last planning ledger estimated CHF 65.46 headroom; the owner's last portal screenshot showed CHF 2,095.08 remaining overall. These figures need launch-time reconciliation. Starting this goal does not silently raise either envelope. Reprice the main run and evaluation within that cap where possible; if a concrete required continuation cannot fit, present the priced decision while continuing independent permitted work. Preserve the conservative DPO reserve and the September month-end deadline.

The goal remains active until the required data, training, measurement and release-readiness work is actually complete and its claim is supported. Exhausting a pilot, changing a document or reaching an inconclusive comparison is not goal completion.
