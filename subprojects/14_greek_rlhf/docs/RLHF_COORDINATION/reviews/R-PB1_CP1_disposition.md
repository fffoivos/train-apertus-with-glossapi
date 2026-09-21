# R-PB1 — CP1 independent review of the prompt bank, and what was done about it

21 September 2026 · reviewer: a fresh Opus agent (not a fork), given the code, the claims and 14 lines of attack,
not the author's reasoning · scope: `rlhf/prompts/*`, its tests, `run_experiment.py`, the plan, E0 ·
**verdict: 0 BLOCKER · 3 HIGH · 9 MEDIUM · 8 LOW** · commit reviewed: `77339793`.

> core provenance/no-duplicate/no-overshoot guarantees hold under real multi-process stress, but set_status()
> breaks the quota guarantee, seeded.py can strand claims permanently, and E0's hold-rate gate can never fire

## What it verified as sound (its own runs, not mine)

- **8 real processes** hammering `claim()+submit()` on one file, 300 sources, quota 40, astrovox cap 3: 40 claims, 40
  distinct, 0 double-claimed, coverage 40/40 and 3/3, 0 left claimed, no "database is locked".
- 6 claimers + 4 processes submitting on unclaimed sources, quota 25: exactly 25/25, 215 refusals, audit clean.
- `supersede()` rolls back on every failure path it could reach (duplicate, near-duplicate, quota full on a held
  prompt, source rejected since).
- `claim()` order identical with the bank built in **reversed** insertion order — stronger than my own test.
- Migration re-run into scratch: 1,042/1,042, 0 refusals, legacy file md5 identical before and after, 12/12 sampled
  lineages correct, all legacy ids resolvable.
- `slots.py` label sampling is unbiased (the rejection region is a union of axis-aligned conditions).

## Findings and disposition

| | finding | disposition |
|---|---|---|
| **H1** | `set_status()` was a bare UPDATE: `held→active` overshot a quota (`el 2>1`), `rejected→active` likewise. My claim "cannot be overshot by any caller" was **false**. | **Fixed.** Transactional; dead prompts stay dead; becoming `active` re-checks room. 4 tests. |
| **H2** | Any exception after `generate.py` returned (malformed JSON, missing file) left the whole batch `claimed` — reserving plan places for ever. | **Fixed.** `try/finally` releases whatever is still claimed; `release_stale()` added; subprocess timeout (L7). Tested with a stub generator in 6 failure modes. |
| **H3** | `hold_rate_of_generated` was **0.0 by construction** (generator 0.2 never writes held text). E0's true rate was 54/60. The plan's one gate for broken generator memory could never fire. | **Fixed.** Rate counted from the generator's own held events over slots issued. E0 now reads 94.7%. |
| M1 | "FK enforced even for raw SQL on a second connection" holds only for a second `PromptBank`: `PRAGMA foreign_keys` is per-connection. | **Fixed** wording + tests on a bare `sqlite3` connection: NOT NULL and the one-live-prompt index are schema-level; the FK is *detectable* (`audit()`), not unbreakable. |
| M2 | Greedy `claim()` strands satisfiable plans; `feasibility()` stayed silent afterwards. | **Fixed** the visibility: joint purpose×language attainability by max-flow. `claim()` is still greedy — documented as "never overshoot ≠ will complete". |
| M3 | Accent-stripped Greek was neither an exact nor a near duplicate (J = 0.0); prompts under 5 words were all-or-nothing. | **Fixed.** Shingles fold diacritics; under 8 words, character 4-grams. |
| M4 | 66 of 1,042 prompts (6.3%) carry a purpose different from their source's, so `supply()`/`feasibility()` account on the wrong cell at that rate. | **Logged.** Legitimate relabels from the legacy round; documented. Accounting on the final cell is a follow-up. |
| M5 | `slot_id` was inside a seed's identity: same seed, new experiment prefix → new source. | **Fixed.** Identity is content; `slot_id` is a label. |
| M6 | A consumed source whose prompt was archived accepted a brand-new live prompt, for a different plan, audit clean. | **Fixed.** Refused unless via `supersede()` (or `legacy=True`, used only by `migrate.py`). |
| M7 | A direct `submit()` can take the last place while a claimed worker is mid-call — wasted calls, correctness intact. | **Logged**, documented. |
| M8 | `slots`, `seeded`, `migrate`, `run_experiment`, `set_status` had no tests; the plan gated S1/S2 on "tests green". | **Fixed.** `test_prompt_bank_cp1.py`, 26 tests. **16 fail against `77339793`** — checked, so they are not vacuous. |
| M9 | `submit(status='archived')` on an available source silently burned it. | **Fixed.** Only a live prompt (or a legacy replay) consumes. |
| L1 | `apportion()` accepted negative / NaN weights. | **Fixed.** |
| L2 | Every prompt with no user turn shared one shingle. | **Fixed.** |
| L3 | `add_source` silently ignores differing fields on re-add (2 of 1,914 forum URLs have a divergent derived purpose). | Logged. |
| L4 | Doc drift: test count; feasibility figures predated the retire-legacy fix. | **Fixed.** |
| L5 | `fill()`'s end probe claimed-then-released. | **Fixed.** `claim(peek=True)`. |
| L6 | Schema errors escape as `sqlite3.IntegrityError`, not `BankError`. | Logged. |
| L7 | `subprocess.run` without a timeout. | **Fixed** (with H2). |
| L8 | "Zero refusals" is narrower than it reads: non-live legacy prompts are never near-duplicate-checked. | Logged; stated in the doc. |

## What it could not verify, carried into E1

It never ran the real generator, so `prompts.jsonl`'s real shape, whether held text is truly never written, and whether
the symlinked-runs isolation actually carries the generator's memory over are **unverified by the reviewer**. E1 is
where those get tested, and H3's repaired gate is what would show a broken hand-off.
