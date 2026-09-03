# Brief WP3 — the known-ness scorer for the training rows' Greek-reality claims

**Goal.** Label every SFT row by whether the base model already holds the Greek facts the row
asserts: `none | known | mixed | unknown`, from two signals — presence in the CPT corpus and the base
model's own answers.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5; `SFT_PLAN_20260903.md` §8 (the design);
`~/Projects/natural-greek-sft/data/exports/reality_claims.jsonl` (5,688 rows; each `claims` item has
`claim` (a Greek sentence, or fr/de/en for those configs), `kind`, `basis` ∈ {known, inferred,
uncertain}); Gekhman et al. 2024 (arXiv:2405.05904) for the Known/Unknown protocol — describe it in
the README from your own knowledge, do not fetch.

**Deliverable paths (only these):** `evals/knownness/score_claims.py`, `evals/knownness/make_questions.py`,
`evals/knownness/corpus_presence.py`, `evals/knownness/README.md`, `evals/knownness/test_knownness.py`,
`briefs/WP3.REPORT.md`.

**Spec.**
1. `make_questions.py`: turns each claim into a question + gold short answer in the claim's language
   (e.g. "Το Τρίτο Στεφάνι γράφτηκε από τον Κώστα Ταχτσή και εκδόθηκε το 1962" → Q "Ποιος έγραψε το
   Τρίτο Στεφάνι;" A "Κώστας Ταχτσής"; Q "Πότε εκδόθηκε…;" A "1962") using **Sol** (`run_sol`, batches
   of 20 claims, strict JSON) — one question per claim, deterministic cache under
   `evals/knownness/cache/` (gitignored). No model calls in tests.
2. `corpus_presence.py`: for each claim, counts documents in the public modern-Greek snapshot
   `fffoivos/apertus-8b-greek-cpt-modern-greek-train` containing the claim's key entity strings
   (extracted by Sol in step 1 as `entities: [...]`); streaming, sampled if the snapshot is large
   (state the sample and scale the counts); on the cluster Claude can point it at the full corpus via
   `--corpus-glob`. Output per claim `{doc_count, sampled_fraction}`.
3. `score_claims.py --model <dir> --questions ... --out ...`: Gekhman-style — for each question, 4-shot
   prompt (fixed exemplars you write, in the same language, not from the data), greedy answer at T=0
   and 4 samples at T=0.5; `known` if the greedy answer matches gold (normalized containment),
   `weakly_known` if any sample matches, else `unknown`. Row label: `none` (no claims), `known` (all
   claims known/weakly), `unknown` (all unknown), `mixed`. Writes `results/<run>/knownness.jsonl`
   (per claim) and `results/<run>/knownness_rows.jsonl` (per row) + a summary with the distribution
   per config and by `basis`. Single process, heartbeat, `--dry-run`, `--limit`; runs on a node by
   Claude inside the E0b job.
4. `test_knownness.py`: fake model + 5 hand-written claims → labels; prints `OK`.

**Acceptance (Claude runs):** `python evals/knownness/test_knownness.py` prints `OK`;
`python evals/knownness/score_claims.py --dry-run --model x --questions x --out x` exits 0. Sol calls
in `make_questions.py` are run by Claude afterwards (`--limit 200` first, hand-checkable sample in
the report format).
