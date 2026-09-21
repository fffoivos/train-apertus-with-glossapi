# R-PG2 reply, cycle 1 (17 Sept 2026)

No second review cycle for R-PG2 (owner rule: do not block on reviews). Code: `data/rlhf/registry/registry.py` (previous version kept as `registry_v1_backup.py`); report rebuilt.

1. Held maths pairs counted as yield: fixed. Held rows are excluded from both numerator and denominator. Maths yield comes from the specialist-judge calibration (8 of 20 round-2 maths prompts with an eligible positive and a lower reply, verified references only), labelled provisional, lower bound widened by 25%.
2. Dialogue yield: deferred to the dialogue workstream (R-PG6). Single-turn allocation does not depend on it; dialogue openings are built by the dialogue track, not by this manifest.
3. Joint rounding: fixed. Iterative proportional fitting plus controlled rounding; row and column sums now match both margins exactly (N=500: el 350, en 100, fr/de/es/it/pt 10 each; N=750: 525, 150, 15 each), asserted in code.
4. A ledger: fixed in part. Maths-content posts are no longer excluded from A. No owner-review status exists for forum posts, so A is labelled "provisional available inventory (gate-accepted)" in the report rather than invented.
5. Relabel false negatives: handled downstream. Every prompt entering round-3 sampling gets a maths-content check under the frozen T5 definition before judging, so arithmetic inside advice routes to the maths judge; the bulk relabel of unused posts is not rerun now.
6. CURRENT_VERSIONS: fixed (registry, relabel and report registered as current; inventory.py superseded).
7. Unused seed status: fixed; recovered seeds with no bound prompt are `unselected`.
