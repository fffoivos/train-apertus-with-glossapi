# The prompt bank — audit of prompt generation, and what replaced the registry

21 September 2026. Code: `rlhf/prompts/` · tests: `rlhf/tests/test_prompt_bank.py` (34) + `test_prompt_bank_cp1.py` (26, regression tests from the independent review) ·
built bank: `data/rlhf/bank/bank.sqlite` (derived; rebuild with `python -m rlhf.prompts migrate`).

## The question

Two things make prompts: the **seed generator** (`data/rlhf/generator_v02`) and the **forum path**
(`forum_sample → forum_gate → forum_select`). The owner asked for a check of both, a solid high-level
API, and a data structure tying every prompt to its source so that duplicates are impossible and the
distribution is guaranteed.

## What the audit found

| | finding |
|---|---|
| **Seed path** | **Solid.** Transactional reservations with UNIQUE instance and rendering keys, written at generation time. Retries supersede: 15 seeds have 2–3 prompts, exactly one `active` each. |
| **Forum path** | **Stateless.** `forum_select.py` samples JSONL with a random seed and remembers nothing. The registry learned about forum prompts only when someone later ran `registry.py import`. Nothing stopped a second draw from returning a URL already used. |
| **Schema** | **Enforced nothing.** No foreign keys (`PRAGMA foreign_keys` = 0), no UNIQUE on content, no NOT NULL on the source link. Only `reservations` had a constraint. |
| **Data, today** | **Clean** — 0 orphans, 0 exact duplicates, 0 forum URLs used twice, 1 near-duplicate (two archived templates, Jaccard 0.53). Clean by *discipline*: the import script was careful. |
| **Distribution** | **Reported, never enforced.** astrovox is **9.4%** of active forum prompts against a **3%** cap in `target_distribution_v1.json`. `everyday` is +16 pp over target, `dialogue` is at 0% against 35%. |
| **Two registries** | Codex's `prompt_generator/` keeps its own `runtime/registry.sqlite`. Neither knows the other's prompts, so a duplicate across them would go unseen. |

Two claims I made mid-audit were wrong and the migration corrected them: I said 149, then 28, prompts
had no source entity. **All 1,042 link to a source that exists.** The legacy linkage was complete; it
was just not guaranteed.

## The data structure

One SQLite file, foreign keys **on** (the bank refuses to open if the build cannot enforce them).

```
sources    one row per thing a prompt can be made from
           UNIQUE(kind, natural_key)       forum → the URL · seed/template/dialogue → canonical JSON
           state: available → claimed → consumed | rejected | retired
           CHECK: a forum source names its forum, nothing else may

prompts    source_id NOT NULL → sources    no source, no prompt
           content_sha UNIQUE              identical text is refused, whatever its source
           UNIQUE(source_id) WHERE live    at most ONE live prompt per source; a retry must supersede
           supersedes → prompts            the retry chain

shingles   word 5-grams per prompt, indexed: exact Jaccard against every live prompt, refused at ≥ 0.5

plans      a target of n prompts
quotas     share: closed dimension, integer quotas by largest remainder (sum to n exactly)
           cap:   a ceiling on an otherwise open dimension (astrovox ≤ 3% of forum prompts)
```

Provenance, no-duplicates and distribution are each held by a constraint or a transaction, not by a
convention. The tests go around the API with raw SQL, on purpose, and require the *database* to refuse.

## The API

```python
from rlhf.prompts import PromptBank, ingest_forum_gate, ingest_seeds, fill

bank = PromptBank("data/rlhf/bank/bank.sqlite")

ingest_forum_gate(bank, "data/rlhf/pool/forum_gated_v3.jsonl")   # idempotent: re-running adds nothing
ingest_seeds(bank, seed_rows, origin="generator-0.3")

bank.plan("round4", 500, shares={"purpose": {...}, "language": {...}}, caps={"forum": {"astrovox": 4}})
bank.feasibility("round4")        # what the unused supply cannot meet -- before any work is done

fill(bank, "round4", "forum", 150, run="R4-forum", generator="forum-gate-v3")
fill(bank, "round4", "seed",  350, run="R4-seed",  generator="generator-0.3", render=render_with_sol)

bank.coverage("round4")           # target / filled / claimed / remaining
bank.lineage("p:8eae749bed869801")    # prompt → source verbatim → every earlier attempt; legacy ids work as aliases
bank.audit()                      # every invariant, counted
```

Underneath `fill()`: `claim()` reserves one **unused** source whose cell still has room (forums fill
evenly, least-loaded first; order within a forum is a hash, identical on every machine), `submit()`
registers the prompt or raises `SourceError` / `DuplicateError` / `NearDuplicateError` / `QuotaError`,
`supersede()` does a retry atomically. CLI: `python -m rlhf.prompts migrate|audit|stats|supply|coverage|feasibility|lineage`.

## Proof it holds

- **Migration as audit.** All 2,688 legacy sources and 1,042 prompts were carried in through `submit()`
  — the same door new prompts use. Zero refusals; audit all zeros. The legacy file is opened read-only.
- **Dry run on a copy.** A 150-prompt forum plan with the astrovox cap: 150 previously-unused sources,
  12–13 per forum, astrovox **2.7%** (was 9.4%). Re-ingesting the same gate file: 1,914 already known, 0 added.
- **A real bug the tests caught in the new code:** SQLite's `INSERT OR IGNORE` swallows `CHECK`
  violations as well as uniqueness ones, so a malformed source vanished silently while `add_source`
  returned an id for a row that did not exist. Replaced with an explicit existence check.

## What the feasibility check says about the next round

Planning 500 prompts at the target distribution fails before it starts: `dialogue` short by 175,
English by 100, `instruction` by 75, `safety` by 50, and the minor languages have no unused sources at all
(figures recomputed after legacy leftovers were retired rather than offered as supply). For forums that is a hard limit. For seeds it means *generate seeds first* — seed
supply is elastic, but only if someone makes it.

## What is and is not guaranteed (after the independent review, R-PB1)

- **Never overshoot: guaranteed.** Verified by the reviewer under 8 real processes. `submit()`, `supersede()` and
  `set_status()` all re-check the quota inside the transaction. (`set_status()` did not, originally — the review's H1.)
- **Completion: not guaranteed.** `claim()` is greedy and can spend the one source a later joint cell needed.
  `feasibility()` now checks joint purpose×language attainability by max-flow, so the dead end is visible.
- **Provenance:** `source_id NOT NULL` and one-live-prompt-per-source are schema-level and hold for any tool that opens
  the file. The foreign key is enforced per connection, so through a bare `sqlite3` connection it is *detectable*
  (`audit()` counts orphans), not unbreakable.
- **Near-duplicates:** accent-, case- and punctuation-insensitive word 5-grams; character 4-grams under 8 words. Still
  lexical: a paraphrase gets through.
- **The migration's "zero refusals"** is narrower than it reads: only live prompts are near-duplicate-checked, so the
  170 archived/rejected legacy prompts never were (including the known J = 0.53 template pair).
- **66 of 1,042 legacy prompts (6.3%) were relabelled** to a purpose other than their source's. `supply()` and
  `feasibility()` account on the source's cell, so they are off by about that rate for legacy data.
- A direct `submit()` can take the last place in a cell while a claimed worker is mid-call. Correctness holds; the
  worker's call is wasted. `fill()` and `generate_into()` release and stop.

## Not done, deliberately

- **The generators are not wired to the bank yet.** `generator_v02/generate.py` still writes the legacy
  registry and `forum_select.py` still exists. The bank is ready to be the single write path; switching
  the generators over touches code other sessions have open, so it waits for a go.
- **Codex's registry is not merged.** `prompt_generator/` is Codex-owned and was not edited. Its accepted
  prompts should be ingested as sources + prompts here so cross-registry duplicates become visible.
- **`feasibility()` is per-dimension**, so it is necessary, not sufficient: enough Greek and enough maths
  does not prove enough Greek maths.
- **The near-duplicate threshold (0.5 on word 5-grams) is a choice, not a measurement.** It catches
  light rewordings; it will not catch a paraphrase. An embedding check could be added behind the same
  `NearDuplicateError`.
