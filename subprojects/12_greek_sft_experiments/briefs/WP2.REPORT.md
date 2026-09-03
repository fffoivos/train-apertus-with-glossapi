# WP2 report — trainer and local dry run

Date: 2026-09-04

## Built

- `cluster/sft_train.py`: a cache-only, single-process TRL `SFTTrainer`
  entrypoint with YAML arm selection, pre-model data/tokenizer/template
  validation, `--dry-run`, `--max-steps`, `--limit`, explicit output roots,
  BFD packing, assistant-only loss, per-config epoch evaluation, epoch-named HF
  checkpoints, fp32 model/master parameters with configurable bf16 compute,
  deterministic seeds, and a 30-second heartbeat.
- Nine arm/runtime configs plus `cluster/configs/zero3.yaml`: two phase-A
  constant-LR runs, the cosine replicate and E1-last, E2/E3/E3prime, 200-step
  smoke, and the 5-step 2M-parameter random local stand-in. Phase-B/replicate LR and epochs
  remain `TODO_FROM_GRID` and fail closed if selected before G3 resolves them.
- `cluster/test_trainer_local.py`: five local checks over three genuine cached
  no_robots conversations (or WP0's E1 rows when available): loss masking,
  packed document metadata/position resets, exact checkpoint-logit reload,
  no-model dry-run, and heartbeat emission.
- `cluster/README.md`: one workbench `srun` command, the four-process Accelerate
  launch, exact runtime environment, precision/packing semantics, dependencies,
  stopping decision, checkpoint behavior, and deviations from the recipe.

The upstream template is rendered unchanged but patched with Jinja generation
markers. All non-assistant tokens and all structural controls except
`<|assistant_end|>` are masked. ID 68 is deliberately an unmasked target and is
also tokenizer/model EOS: masking it would prevent the base model from learning
to stop. The brief's “13 control tokens” conflicts arithmetically with IDs
61–72 (12 tokens); the implementation validates those 12 role/tool tokens and
documents BOS `<s>` as the thirteenth structural token.

## Local commands and output

### Syntax compilation

Command:

```bash
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python -m py_compile cluster/sft_train.py cluster/test_trainer_local.py
```

Output: none. Exit code: `0`.

### Production tokenizer/template preflight

Command:

```bash
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python - <<'PY'
import sys
sys.path.insert(0, 'cluster')
import sft_train
cfg=sft_train.load_config('cluster/configs/E1_lr1e-5_3ep_const.yaml')
tok, ids=sft_train.prepare_tokenizer(cfg)
print('TOKENIZER_OK', len(tok), tok.eos_token, tok.eos_token_id, ids)
print('STOP_TRAINED', sft_train.is_chat_template_stop_token_trained(tok))
PY
```

Output:

```text
[transformers] `rope_parameters`'s original_max_position_embeddings field must be less than max_position_embeddings, got 8192 and max_position_embeddings=4096
TOKENIZER_OK 148992 <|assistant_end|> 68 {'<|system_start|>': 61, '<|system_end|>': 62, '<|developer_start|>': 63, '<|developer_end|>': 64, '<|user_start|>': 65, '<|user_end|>': 66, '<|assistant_start|>': 67, '<|assistant_end|>': 68, '<|inner_prefix|>': 69, '<|inner_suffix|>': 70, '<|tools_prefix|>': 71, '<|tools_suffix|>': 72}
STOP_TRAINED True
```

Exit code: `0`. The first line is a Transformers warning emitted while loading
the cached CPT tokenizer configuration; it did not fail the preflight.

### Requested production dry run

Command:

```bash
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python cluster/sft_train.py --dry-run --config cluster/configs/E1_lr1e-5_3ep_const.yaml
```

The initial attempt, before WP0 finished materializing the arms, produced:

```text
ERROR: train input does not exist: /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/arms/E1/train.jsonl
```

Exit code: `2`. This is the intended fail-fast behavior. WP0 had created its
builder/cache but had not yet materialized `data/arms/E1/train.jsonl` or
`data/arms/dev_all.jsonl`; weakening input validation to force exit 0 would
violate cluster-clause point 3.

After WP0 produced the files, the exact same command was rerun. Output:

```text
[transformers] `rope_parameters`'s original_max_position_embeddings field must be less than max_position_embeddings, got 8192 and max_position_embeddings=4096
PLAN {"arm": "E1", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 64, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 3, "eval_file": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/arms/dev_all.jsonl", "eval_rows": 658, "eval_tokens": 236834, "expected_full_train_tokens": 9340000, "gradient_accumulation_steps": 16, "learning_rate": 1e-05, "lr_scheduler_type": "constant_with_warmup", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": null, "model": "fffoivos/apertus-8b-greek-cpt", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 1512, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 72, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "E1_lr1e-5_3ep_const", "steps_per_epoch": 24, "train_file": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/arms/E1/train.jsonl", "train_rows": 17602, "train_tokens": 6182367, "warmup_ratio": 0.03, "world_size": 4}
PLAN_WARNING exact_train_tokens_differs_from_planning_reference relative_difference=0.338076
DRY_RUN_OK model_not_loaded=true
```

Final exit code: `0`. The exact rendered-token count is 6,182,367, while the
config retains the brief's 9,340,000 planning reference. With BFD packing the
resolved plan is 1,512 packed sequences, 24 optimizer steps per epoch, and 72
steps over three epochs.

### Full local acceptance

The full command was run directly and exited `0`. For a concise exact receipt,
it was run once more with its acceptance lines selected:

```bash
set -o pipefail
/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python cluster/test_trainer_local.py 2>&1 | rg '^(REAL_ROWS|UNMASKED|PACK_BOUNDARIES_OK|DRY_RUN_OK|DRY_RUN_NO_MODEL_OK|HB step=0|RELOAD_CHECK|CHECKPOINT_RELOAD_OK|HEARTBEAT_OK|OK$)'
```

Output:

```text
REAL_ROWS source=/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/arms/E1/train.jsonl count=3
UNMASKED row=1 decoded='lowercase_names = names.map{ |name| name.downcase }<|assistant_end|>'
UNMASKED row=2 decoded='Φεγγάρι έρπει\nΛύκος ουρλιάζει μακριά\nΚαταχνιά πνίγει<|assistant_end|>'
UNMASKED row=3 decoded='Δεν έχω προσωπικές στιγμές ή αίσθημα ντροπής· μπορώ όμως να αναγνωρίσω μια άβολη κατάσταση και να τη συζητήσω μαζί σου.<|assistant_end|>'
PACK_BOUNDARIES_OK seq_lengths=[113, 103, 102] position_resets=[0, 113, 216] attention_mask=absent
DRY_RUN_OK model_not_loaded=true
DRY_RUN_NO_MODEL_OK
HB step=0 loss=nan tok/s=0.00 mem=0.72GiB
RELOAD_CHECK max_abs_diff=0
CHECKPOINT_RELOAD_OK path=/var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/wp2-local-ka1jjwl9/output/epoch1 max_abs_diff=0
HEARTBEAT_OK
OK
```

Exit code: `0`. The unfiltered run also printed one heartbeat for every optimizer
step, `eval_no_robots_loss`, `TRAIN_OK`, and TRL's expected warning that eager
CPU attention is not a supported document-aware padding-free kernel.

## Not tested

- No CPT model weights were loaded and no 8B training was attempted locally.
- No GH200, CUDA, four-process Accelerate, DeepSpeed ZeRO-3, or cached
  FlashAttention execution was run. The Mac environment does not contain
  `deepspeed`; the node environment must provide it before an allocation.
- The local eager-attention stand-in verifies TRL's BFD `seq_lengths`, absence
  of a flat all-ones attention mask, and zeroed position IDs at every document
  start. It cannot prove the GH200 FlashAttention kernel's document isolation;
  that remains part of the 20-step watched probe. Production configs reject an
  attention implementation outside TRL's supported FlashAttention set.
- ZeRO-3 checkpoint gathering/reload was not tested. The local HF checkpoint
  reloaded with exactly identical logits (`max_abs_diff=0`).

No packages were installed. The Mac environment lacks `deepspeed`; the cluster
also needs the cache-populated `kernels-community/vllm-flash-attn3` artifact in
addition to the packages listed in `cluster/README.md`.

## Open questions before cluster use

1. The literal requested settings resolve to 24 optimizer steps per epoch,
   whereas `SFT_PLAN_20260903.md` estimated approximately 270. TRL BFD makes a
   training item a packed 4,096-token sequence, so `1 x 16 x 4 = 64` means 64
   packed sequences per optimizer step rather than 64 source rows. Claude/the
   owner should confirm this optimizer-step and token-batch interpretation
   before the first GPU minute; changing it is a scientific configuration
   decision, not a WP2 implementation detail.
2. The full dry run counted 6,182,367 rendered tokens for E1; the brief's
   planning reference is 9,340,000 and WP0 records a separate 9,164,728
   `planning_reference_tokens`. Confirm which accounting basis controls budget
   estimates. The trainer reports the exact tokenizer count and does not
   silently replace it with the planning reference.
3. Does the prepared node environment contain `deepspeed` and the exact
   FlashAttention kernel cache required by the production configs?
4. After the phase-A readout, which learning rate and epoch count replace
   `TODO_FROM_GRID` in the five cosine configs?
5. The first 20-step probe must confirm document isolation, fp32 master/bf16
   compute behavior under ZeRO-3, memory, throughput, heartbeat cadence, and a
   gathered checkpoint reload before any longer run.
