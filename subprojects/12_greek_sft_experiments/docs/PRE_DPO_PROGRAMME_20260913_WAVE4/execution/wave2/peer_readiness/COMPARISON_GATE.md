# MultiChallenge comparison gate

The v1.5 run may generate the 213-item diagnostic subset, but that output is not comparison-ready by itself. The 49 excluded IDs are 18.70% of the 262 eligible items, and the subset was derived with the v1.5 tokenizer and native chat template.

Before reporting a peer difference:

1. Preserve the full 262-ID eligible ledger and the 49-ID exclusion ledger.
2. Render and tokenize the same 262 items with the native tokenizer and chat template of every compared model: original Krikri, v1.5, and G3F2P1 where included.
3. Require `input_tokens + 1024 <= model_context_limit` for every model on every shared item. If any of the current 213 IDs fails for one model, derive a new intersection and regenerate every model on that exact intersection.
4. Recompute historical peers from row-level outputs on the resulting shared IDs. Never compare the 213-item result with an old 262-item aggregate.
5. Label the result as a diagnostic subset and report `n/262` plus excluded IDs. A later matched longer-context run over all 262 items for all models is the preferred supplementary measurement.

The frozen first v1.5 batch does not claim to satisfy steps 2–4. Its role is to produce the missing v1.5 row-level outputs while preventing silent truncation.
