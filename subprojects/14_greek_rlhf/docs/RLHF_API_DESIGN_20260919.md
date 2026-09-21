# RLHF programme API — design

19 September 2026. Status: **evaluation layer built and in production use; Sol seam built; the rest is proposal.** Nothing existing was moved.

## Why

The round-1 DPO work ran on ~120 scripts written under time pressure, and five independent reviews
on 19 September found the same class of defect again and again. None were exotic:

| what went wrong | root cause |
|---|---|
| A "configuration interaction" published, then withdrawn | two runs compared whose **prompts differed** (the date) — nothing checked |
| "GreekMMLU" 15 points off the official number | the **protocol** was not part of the result's identity |
| 16,632 raw rows labelled as the 16,159 clean subset | the **item population** was not part of the result's identity |
| Global-MMLU deltas 1.3 pp too favourable | one scalar per benchmark, aggregation re-implemented ad hoc |
| A failed job reported success; a blind review filed as a verdict | success = exit status, not validated output |
| "The arm that did not train" (it trained 129/129 steps) | a claim in prose that no code derived from a receipt |
| Seed SD quoted as precision | statistics chosen per claim, by hand |

The API exists to make those **impossible by construction**, not to tidy directories.

## Shape

One Python package, `rlhf/`, standard library only, with a CLI (`python -m rlhf …`). Each stage is
a function over **records in, records out**, every record carries its provenance, and every stage
writes a **receipt**. An HTTP face can sit on top later exactly as Codex's
`prompt_generator/api.py` does; the library is the contract, HTTP is a transport.

```
rlhf/
  sol.py            the ONE Sol client. wraps data/math/codex_server.py: effort policy (medium for
                    pipeline, xhigh for review), budget telemetry, LaTeX-escape guard, no code_mode flag
  records.py        Prompt, Reply, Judgement, Pair, RunManifest — schema + validation
  prompts/
    seeds.py        seed-instance generator      (wraps data/rlhf/generator_v02)
    forums.py       forum sample → gate → select (wraps forum_sample/forum_gate/forum_select)
    dialogues.py    dialogue openings + rollouts (wraps data/rlhf/dialogue_v2)
    registry.py     the prompt registry          (wraps data/rlhf/registry/registry.py)
  generate.py       n replies per prompt from a served model (sample.py, rlhf_sample.sh)
  judge/
    general.py      rank-4 under the frozen rubric (judge_rank4 + judge_batches)
    maths.py        solve-inside-the-call maths judge (maths_judge v2)
    multiturn.py    turn-scoped judging (source + applies_now, 3-valued)
  pairs.py          judgements → preference pairs; splits with no group leakage; length balance; the pairs doc
  train/
    dpo.py          config → parameter table vs the previous run (every change flagged) → submit → receipt
  evals/            ← BUILT FIRST, see below
    manifest.py     what a result IS: weights, protocol, prompt digest, config, item population
    compare.py      refuses any comparison whose manifests differ in more than the declared variable
    stats.py        paired item tests, seed-level bootstrap — one implementation
    lanes.py        lm_eval / served / greekmmlu-official runners, fail-closed
  report/
    page.py         the artifact: every number rendered from data, none typed into prose
  review.py         cross-vendor review runner (cluster/run_review.sh), refuses a blind review
  cli.py
```

**Wrap, do not move.** `prompt_generator/` is Codex-owned and other sessions are live in
`dialogue_v2/` and `generator_v02/`. The package imports their entry points and adapts records at the
boundary. Files move only when an owner says a module is frozen.

## The five invariants

1. **A result has an identity.** `RunManifest` = weights id, benchmark, **protocol**, **prompt digest**
   (hash over every rendered prompt), generation config, tokenizer hash, **item-id digest**, harness
   versions. A number without a manifest cannot enter the results store.
2. **Comparisons declare their variable.** `compare(a, b, varying={"weights"})` raises unless the
   manifests are identical in everything else. Today's date confound, the config confound and the
   raw-vs-clean mix-up are all the same error and all fail this one check.
3. **Success is a validated receipt.** A stage is done when its output passes its validator (row
   count, population, schema, booleans that are booleans) — never because a process exited 0.
4. **One statistics implementation.** Paired item-level tests by default; between-seed spread,
   same-seed repeat gap and item sampling error are three named quantities that cannot be swapped.
5. **Claims are derived.** The report renders from the results store. "Arm X trained N steps" comes
   from `trainer_state.json`, not from a sentence.

## Build order

| # | slice | state |
|---|---|---|
| 1 | `evals/` — `manifest`, `compare`, `stats`, `weights`, `result`, `store` | **built, 42 tests, in production use.** Eleven reviews attacked it; every defeat is a regression test. It gates the re-run launched 19 Sept |
| 2 | `sol.py` — the one Sol client | **built, 6 tests.** Not yet adopted by the six call sites; adopting them is a separate, coordinated change |
| 3 | `report/page.py` on the results store | next. The artifact still reads JSON files directly; numbers in prose remain possible |
| 4 | `train/dpo.py` — parameter table vs the previous run, receipts | after 3 |
| 5 | `judge/*`, `generate.py`, `pairs.py` over `sol.py` | needs the generation session at a stopping point |
| 6 | `prompts/*` adapters (seeds, forums, dialogues) | needs Codex + the dialogue session at a stopping point |

### What slice 1 cost, and what it caught

Eleven reviews (R-DPO6 … R-DPO12) over one day. The evaluation layer was rewritten three times because
each round of attacks got through the previous design:

1. *manifest + compare* — caught the prompt-date confound and the generation-config confound in the
   already-published results.
2. *sealed `Result`* — a caller could edit a manifest after building it, or pair a genuine manifest with
   fabricated outcomes.
3. *evaluator-written receipts* — identity arrived as builder arguments, so the parent's config could be
   sealed onto an arm, or one result file presented as two models.

The defects it found in **published numbers**: the run date inside every prompt; Global-MMLU averaged
over aggregates and their children; a "configuration effect" that never existed; and — found only because
the guard demanded effective model geometry — every trained model loaded with the wrong rotary base in
the lm_eval environment, which is why the mathematics and multilingual "regressions" are now unproven
rather than published findings.

The last one is the argument for the whole package. It was visible a day earlier as a finalizer refusing
the checkpoints for "geometry drift", and it was dismissed as a false alarm. A guard that no human has to
remember to consult is the difference.

## Not decided here (owner calls)

- **A checkpoint commit before slice 2.** 204 files in this subproject are uncommitted. The package
  only adds files, but retrofitting touches results; a commit first makes everything reversible.
- Whether slices 5–6 should wait for the generation and dialogue sessions to reach a stopping point.
- HTTP face: recommended only if something other than Python will call it.
