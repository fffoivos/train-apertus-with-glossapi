# R-PB2 — CP2 independent review of the generated prompts, and what was done about it

21 September 2026 · reviewer: a fresh Opus agent (not a fork), read-only, no model calls · scope: the 29 single-turn
prompts E1 and E2 generated on real Sol (19 + 10), their sources, the generator's own logs, both reports ·
**verdict: 0 BLOCKER · 3 HIGH · 7 MEDIUM · 4 LOW.** Dialogue was out of scope (stopped by the owner mid-run).

> bank guarantees hold (K1/K3/K5 confirmed, K2 lexically vacuous + one semantic dup, K4 unmeasurable at n=22 and
> misreported in E1); fix the forum social-post filter, the [MATH] leak and --report-only's fabricated zeros

## The claims

| | | measured by the reviewer |
|---|---|---|
| K1 one source per prompt | **confirmed** | 29/29 lineages, 29 distinct sources, 0 sources with two live prompts across all 901 live prompts |
| K2 E2 reused nothing, no duplicates | **partly** | sources: E2 ∩ everything before = ∅. Exact text: unique. Near-duplicate fence: **never tested** — the highest word-5-gram Jaccard of any of the 29 against 901 live prompts was 0.012 against a threshold of 0.50 — and reading found one cross-plan semantic near-paraphrase it could not see (M1) |
| K3 distribution obtained = asked | **confirmed** | E2: all 14 quota rows exact. E1: both caps held, all five single-turn purpose cells exact; the language shortfall (el 8 + en 2 + es 1 = 11) is one-to-one the 11 withdrawn dialogue places |
| K4 hold rate near 18% | **partly** | E1 1/14, E2 1/8, combined 2/22 = 9.1%, 95% interval ≈ [1%, 29%]: no power either way at this n. It verified the generator's memory **structurally** instead (955 → 962 active prompts in its registry across E1→E2; symlinks resolve to 625 historic instances). Intact. |
| K5 audit all zeros | **confirmed** | re-ran `audit()` and the SQL under it on copies of both banks |

## Findings and disposition

| | finding | disposition |
|---|---|---|
| **H1** | The forum gate's `post_kind='social'` was accepted as supply. Read, those are stories, rants and introductions with no request (74 of 81 gate-typed `share`). One reached E1: a "New Member Introductions" post. ≈5% of remaining forum supply. | **Fixed.** `ingest_forum_gate(accept_kinds=("request",))` by default — a switch, since the legacy import accepted `social` on purpose. 64 unused social sources withdrawn from the built bank. The **17 legacy live prompts** sitting on social posts are kept and reported, not dropped. |
| **H2** | The scraper's `[MATH …]` wrapper leaked into the user's own text («…είναι ακριβώς [MATH 12] φόρες μικρότερα») — E1's entire maths cell. 86 gated prompts, **68% of usable `mathematica` rows**, 523 markers. | **Fixed.** Unwrapped at render (`[MATH 12]` → `12`, `[MATH \\mathbb{R}]` → `$\\mathbb{R}$`); a prompt that still carries any `[MATH|URL|EMAIL|IMG|QUOTE|…]` spends its source instead of shipping. **17 legacy live prompts** carry a marker: reported. |
| **H3** | `--report-only` passed `[]`/`{}`/`set()` for what it had not observed, so E1's report printed **"0 held of 0 slots issued (0%)"** and `sources_reused: []` — two of the plan's five failure criteria reading green *unmeasured*. Mine. | **Fixed.** Unobserved is `null`, never zero; generator figures are read from its own receipts (E1 now reads 14 / 1 / 7.1%). |
| M1 | E1 and E2 each drew *"an online application keeps rejecting a correctly formatted address"* for el / `plan_or_organise` and rendered near-paraphrases at **Jaccard 0.000**. 17 distinct situations for 20 seeds. | **Withdrawn.** I first added a hard rule (never the same situation twice per language + subtype). The owner corrected it the same day: a seed is the *combination of all its elements*, and reusing one element is not a duplicate. The rule is gone. The real cause is M2 — the generator may drop the topic, so two seeds that differ only there render alike — and that belongs to `generate.py`. |
| M2 | The uniqueness key rests on the one axis the generator may drop: `INSTANCE_PROMPT` says *"drop the topic if it does not fit"* and **11 of 20 did**, while 14/20 reuse a person and 18/20 a situation. "Never the same triple" is true and nearly empty. | **Partly** — the scene rule above no longer depends on topic. The rest is in `generate.py`: **for the generator's owner.** Extend the person/situation pools before a 500 round. |
| M3 | The `safety` cell buys little safety: 1 of 4 is a real test; one states its own constraint («χωρίς τεχνικές οδηγίες»); the German `false_premise` prompt supplies its own refutation. Cause: answer-side conditions sit in `givens` and the renderer is told to voice every given. | **For the generator's owner.** Split `givens` into `stated_by_user` / `answer_only`. |
| M4 | One accepted prompt its own reviewer should have held (`p:d41974928e5d0d88` drops which figure came from the sheet and which from the report), and one inconsistent review on E21-S02. **Both holds were correct; nothing fine was held.** | **For the generator's owner.** |
| M5 | **25% of seeded prompts open with a demographic self-introduction** ("Είμαι 29 ετών…"), and the *reviewer* causes it: 6 of 13 round-0 reviews failed a prompt for omitting the persona blurb, and the repair injects the biography. A learnable surface feature at 500 prompts. | **For the generator's owner.** Tell the reviewer the person is a realism ingredient, not a given to be uttered. |
| M6 | Small-n apportionment is deterministically biased: the five 2% languages tie and the tie breaks on key order, so **50 plans of n=10 give de 50, fr/es/it/pt 0**. | **Fixed.** `apportion(n, shares, already)` and `plan(..., after=[...])` apportion the cumulative total; the same 50 plans now give 10 each. |
| M7 | "Plan met exactly: False" for E1 was unexplained in both artefacts — a reader scores it a failure. | **Fixed.** `--note`; E1's report now states the dialogue withdrawal. |
| L1 | `prompt_sha` in `forum_gated_v3.jsonl` is the **same constant on all 1,928 rows**. Nothing dedups on it today. | Logged. A booby trap for the next caller who trusts it. |
| L2–L4 | an internal time contradiction in one German prompt; two weak forum prompts (no context leakage found in any of the 9); a stale count in the plan. | Logged. |

## Scorecard of the 29 prompts (the reviewer's reading)

ok 9 · weak 4 · mismatch 14 · duplicate-ish 2. **11 of the 14 mismatches are the dropped topic alone**, which the
generator's own prompt sanctions. Detail ceilings were respected everywhere. No forum prompt leaks usernames, quoted
replies or thread context.

## Not verified by anyone yet

`register=greeklish` never came up in 20 slots, and `frustrated`, `playful`, `detailed` once each: the tails of every
within-seed axis are unsampled at this n. Semantic duplication was checked with TF-IDF and reading, not embeddings.
