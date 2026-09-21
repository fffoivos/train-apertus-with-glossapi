# Prompt bank — wiring plan and small experiments

21 September 2026. Owner's ask: *a plan, independent Opus reviewers at given checkpoints, and small
experiments generating 10–30 prompts of all types under the given distribution.*

## Goal

Show, on real generated prompts and not only on migrated ones, that the bank delivers its three
guarantees end to end: every prompt traces to one source, nothing is duplicated, and the distribution
asked for is the distribution obtained. "All types" means the three that generator 0.3 defines:

| type | source | how the prompt text is made |
|---|---|---|
| **forum** | one gated forum thread (URL) | the forum gate already rewrote it; no model call |
| **seed** (single-turn) | one slot: purpose × subtype × language × difficulty/attitude/register/detail × person/situation/topic | `generator_v02/generate.py`: instance → render → code checks → independent review → ≤2 repairs (Sol, medium) |
| **dialogue** (opening) | the same slot schema; primary purpose `dialogue`, the underlying purpose kept in labels | the same `generate.py`, as collection60 did |

`template` (generator 0.1) is defunct and is not generated.

## Constraints

- `generate.py` is **not modified**: other sessions have it open. It is driven as a subprocess through
  the flags it already has (`--manifest --slots --registry --runs-dir --fake`).
- Codex-owned paths are not edited. All Sol calls at **medium**. No new stages.
- Every experiment runs on a **copy** of the bank under `data/rlhf/bank/experiments/<id>/`. The built
  bank is not written to until the owner says so.
- The generator keeps its own duplicate memory in a registry + `runs/*/instances.jsonl`. It gets a copy
  of the most complete legacy registry (collection60's, 1,102 prompts) and symlinks to every earlier
  run, so it still avoids what it has made before. The bank then enforces the same thing independently.

## Steps and gates

| # | step | spend | done when |
|---|---|---|---|
| S1 | `rlhf/prompts/slots.py` — build slots for the cells a plan still needs; person/situation/topic never reused against anything already in the bank | none | tests green |
| S2 | `rlhf/prompts/seeded.py` — claim sources → run `generate.py` on exactly those slots → `submit` active, `submit(status='held')` held, reject the unrenderable | none | tests green with `--fake` |
| S3 | `run_experiment.py` — one plan, three types, a report | none | runs end to end on fake Sol |
| **E0** | the full 30-prompt experiment on **fake Sol** | none | wiring proven: forum quota exact, every claimed source ends terminal, nothing reused, audit all zeros. *Not* "plan filled": `fake_sol.py` returns the same canned text for every slot, so `generate.py`'s own near-duplicate fence holds most seeded rows — correct behaviour, and it means only real Sol can fill the seeded cells |
| **CP1** | **independent Opus review: the plan, `bank.py`, `flows.py`, `slots.py`, `seeded.py`, E0's report** | none | BLOCKER/HIGH fixed |
| **E1** | the same experiment, **real Sol** — n = 30 | ~40 medium calls | report written |
| **E2** | n = 10 on the **same** bank copy, straight after E1 — tests small-n apportionment and that a second plan cannot reuse E1's sources or near-duplicate its prompts | ~15 medium calls | report written |
| **CP2** | **independent Opus review: the generated prompts themselves** — provenance spot-checks, duplicates the bank missed, distribution obtained vs asked, quality of what was held vs accepted | none | findings dispositioned |

Reviewers are fresh Opus agents (owner rule, 19 Sept: spawned agents run on Opus, never forks). They
get the artefacts and the claims, not my reasoning. BLOCKER/HIGH are fixed before advancing; MEDIUM/LOW
are logged.

## The experiment plan (n = 30)

Shares from `target_distribution_v1.json`, apportioned by largest remainder:

- **purpose** — dialogue 11 · everyday 8 · instruction 4 · factual 3 · safety 3 · math 1
- **language** — el 21 · en 6 · three of the five minor languages 1 each (at n = 30 the 2% shares are 0.6 of a prompt; largest remainder gives three of them one and two of them none, by key order — a small-n artefact the report must state)
- **caps** — `kind=forum` ≤ 6 (the legacy share of forum among single-turn prompts, ≈ ⅓ of 19), `forum=astrovox` ≤ 0 (3% of 6 rounds down to none)

Forum sources are Greek and only `everyday`/`factual`/`math`, so forum fills from those cells first and
seeds take the rest. Dialogue is all seed-made.

## What would count as failure

- a prompt in the experiment bank whose `lineage()` does not return a source, or returns one that
  another live prompt also uses
- the obtained distribution differing from the quotas in any cell, without `fill()` having said why
- E2 drawing a source E1 consumed, or registering a near-duplicate of an E1 prompt
- `audit()` non-zero anywhere
- the generator's hold rate far from its 18% baseline (would mean the isolation broke its memory)

## Known limits going in

- `feasibility()` is per-dimension. The experiment builds slots *for* the cells it needs, so it does not
  test the joint-cell shortfall case.
- n = 30 cannot show that 2% languages come out at 2%. It can show they come out at their quota.
- The near-duplicate threshold (0.5 on word 5-grams) is a choice. CP2 is asked to look for paraphrase
  duplicates it lets through.

## E0 result (fake Sol, 21 Sept) and what building it turned up

Forum 6 of 6 with astrovox at 0; 60 slot sources built, every one ended `consumed` or `rejected`, none left
`claimed`; no source reused; audit all zeros. Seeded/dialogue 3 + 3 active, the rest held by the generator's
near-duplicate fence against the fake's canned text.

Four things surfaced on the way, none of them about the fake:

1. **The persona axes are exhausted.** All 172 Greek and all 70 English personas are already used, situations
   127 of 130, and the legacy manifests were already reusing personas (49 more than once, one six times).
   Strict no-reuse is impossible; slots are drawn least-used-first and never repeat a person+situation+topic
   triple. `slots.exhaustion()` reports it. Extending `generator_v02/axes` is a supply task for the next round.
2. **Legacy leftovers were offered as fresh supply.** The first migration carried `held`/`unselected` legacy seeds
   as `available`, and `claim()` duly handed one to the generator. They are now `retired`.
3. **Generator 0.2 never writes the text of a held prompt** (checked across every legacy run). So a held slot has
   nothing to register: it is released for a fresh attempt while rounds remain, then spent with the generator's
   own reason. The bank's `held` status stays, for a generator that does keep the text.
4. **A held prompt must not fill a quota** — 0.2 holds ~18% of what it renders, so counting them would let a
   plan read "full" while part of it was unusable. Only `active` fills; `held` still occupies its source.

## Outcome (21 Sept)

| | result |
|---|---|
| **CP1** | 0 BLOCKER / 3 HIGH / 9 MEDIUM — all HIGH and 8 MEDIUM fixed before any model call. `reviews/R-PB1_CP1_disposition.md` |
| **E1** | forum 6/6, seed 13/13, every single-turn cell exact, audit clean, generator held 1 of 14. **Dialogue stopped by the owner mid-run**; 10 openings marked rejected, the driver is now forum + seed by default. |
| **E2** | n = 10 on E1's bank: **every cell exact**, zero sources reused, audit clean, 18 Sol calls, 4 minutes. |
| **CP2** | 0 BLOCKER / 3 HIGH / 7 MEDIUM. Bank guarantees confirmed on real data; defects were in the content (social posts, `[MATH]` markers) and in my own `--report-only`. `reviews/R-PB2_CP2_disposition.md` |

Against "what would count as failure": no prompt without a source, no source with two live prompts, no cell off its
quota, E2 drew nothing E1 consumed, audit zeros throughout. One criterion was **not** cleanly met: a near-duplicate
*did* get through across plans — semantically, at a lexical similarity of 0.000 — and the hold-rate criterion cannot be
judged at n = 22. Both are stated rather than rounded up to a pass.

Four findings belong to `generate.py`, which this work deliberately did not touch: the dropped topic axis, self-refuting
safety/false-premise prompts, one reviewer miss, and persona self-introductions injected by the reviewer's own repairs.
