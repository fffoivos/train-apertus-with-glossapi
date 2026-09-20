# Token-runtime provenance correction

The earlier pointer to the Codex bundled Python runtime was incorrect: that interpreter cannot import the required training stack. The original `token_inventory.json` was left unchanged.

The complete 32-row inventory has now been independently reproduced with:

```text
/Users/foivoskarounos-zamparloukos/venvs/sfttrain/bin/python \
  /Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot/final_candidates/reproduce_token_inventory.py
```

This environment reports Python 3.14.6, torch 2.14.0, transformers 5.17.0, tokenizers 0.23.2, and TRL 1.12.0. It imports the complete canonical `cluster/sft_train.py` module and calls `prepare_tokenizer` and `tokenize_messages` directly. Every per-row item, total, range, control-token ID, vocabulary size, and 4,096-token decision exactly matches the original inventory. The executable, package versions, code/data/tokenizer hashes, and comparisons are bound in `token_reproduction_receipt.json`.
