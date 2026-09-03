# WP2 Apertus SFT trainer

`sft_train.py` is a single-process TRL entrypoint. Accelerate owns process
creation; the Python file contains no scheduler or remote-execution calls. It
reads only cache-local model/tokenizer artifacts and JSONL inputs, then writes
only below the explicitly supplied `--out-dir`.

## Local preflight

Use the Python named in the brief:

```bash
PYTHON=/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
$PYTHON cluster/sft_train.py --dry-run \
  --config cluster/configs/E1_lr1e-5_3ep_const.yaml
$PYTHON cluster/test_trainer_local.py
```

The production dry run validates both JSONL files, every selected row, the
cache-local tokenizer, the upstream template, the control-token IDs, all loss
masks, and the 4,096-token bound. It prints exact selected-row token counts and
a BFD step plan, then exits before `MODEL_LOAD_BEGIN`. WP0 must therefore have
materialized `data/arms/` first.

`mac_dryrun.yaml` uses the cached GPT-2 tokenizer plus the Apertus controls and
a randomly initialized 2M-parameter GPT-2-shaped causal model. It is an offline
stand-in for exercising the trainer, not a scientific arm.

## One-node workbench command

Before opening an allocation, the repo, all data, the two model revisions, the
Apertus-Instruct tokenizer/template, the FlashAttention kernel, and a Python
environment containing the dependencies below must already be present. From
the repo root, one command inside the existing workbench is:

```bash
srun --jobid <workbench-id> --overlap --nodes=1 --ntasks=1 --gpus=4 \
  uenv run pytorch/v2.9.1:v2 --view=default -- bash -lc '
    set -euo pipefail
    export SCRATCH=/iopsstor/scratch/cscs/fffoivos
    export HF_HOME="$HOME/.cache/huggingface"
    export HF_HUB_CACHE="$HF_HOME/hub"
    export HF_DATASETS_CACHE="$HF_HOME/datasets"
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
    export HF_DATASETS_OFFLINE=1
    export TOKENIZERS_PARALLELISM=false
    export PYTHONUNBUFFERED=1
    accelerate launch --config_file cluster/configs/zero3.yaml \
      cluster/sft_train.py \
      --config cluster/configs/smoke.yaml \
      --out-dir "$SCRATCH/greek-sft/smoke" \
      --max-steps 20
  '
```

The first GPU contact is the 20-step override above. After it passes, use the
same command/config/container without `--max-steps` for the approved run. The
phase-A configs use warmup followed by constant LR. Before running a cosine
config, replace both `TODO_FROM_GRID` values with the owner-approved phase-A
winner. The E1 cosine config uses seed 43 as the replicate; all other arms use
seed 42.

The required Python packages are `torch`, `datasets`, `transformers>=5`,
`trl`, `accelerate`, `deepspeed`, `jinja2`, `pyyaml`, and `safetensors`, plus
the cache-populated `kernels-community/vllm-flash-attn3` attention
implementation. The supplied Mac environment has everything except
`deepspeed`; no package installation was attempted. Verify the node environment
before the allocation rather than installing while it is active.

## Precision, packing, masking, and stopping

The model is explicitly loaded in fp32. With `mixed_precision: bf16`,
Accelerate/DeepSpeed uses bf16 autocast for compute while ZeRO-3 partitions the
fp32 optimizer master parameters and states. The code refuses a production
model whose trainable parameters are not fp32 before DeepSpeed wraps it. This
is mixed precision, not loading the model itself in bf16. ZeRO's
`zero3_save_16bit_model: true` gathers loadable HF-format checkpoint weights;
that checkpoint storage dtype is independent of the fp32 master weights used
during optimization.

Training uses TRL BFD packing. In TRL 1.12, BFD forces padding-free collation:
the packed dataset retains `seq_lengths`, the collator resets `position_ids` to
zero at every example, omits an all-ones attention mask, and supported
FlashAttention derives document boundaries from those resets. The trainer
therefore rejects non-FlashAttention production configs. The Mac eager kernel
does not establish GPU attention isolation; the local test verifies the exact
TRL `seq_lengths` and reset-position contract, while the GH200 20-step probe is
the remaining runtime check.

The upstream Apertus template has no `{% generation %}` markers. The trainer
uses a render-identical copy with markers around string assistant content and
the assistant end token. All system, developer, user, assistant-start, inner,
and tool controls are masked. `<|assistant_end|>` is intentionally unmasked as
the one structural training target: without it the base model cannot learn to
stop. The tokenizer and model generation config both use that token as EOS. It
is ID 68 in production.

The brief says “13 control tokens” and also gives IDs 61–72, which is a set of
12. The trainer validates the 12 role/tool controls in that interval; with BOS
`<s>` (ID 1), the rendered format has 13 structural tokens.

## Checkpoints and evaluation

Evaluation runs at every epoch end. `dev_all.jsonl` is split by its `config`
field and TRL reports a separate `eval_<config>_loss` metric for each group.
Normal epoch checkpoints are renamed to `--out-dir/epoch1/`, `epoch2/`, and so
on after training, and contain the tokenizer plus HF model files loadable by
`AutoModelForCausalLM.from_pretrained`. A step-limited probe that ends between
epoch boundaries gets a final `epoch<ceil(epoch)>/` snapshot. The Mac test
compares in-memory logits with a reload of that snapshot and requires exact
equality.

## Deviations from the vendored recipe

- Arm-specific YAML is parsed explicitly instead of with `TrlParser`, so WP2's
  `--dry-run`, `--limit`, `--max-steps`, and output-root contract can be checked
  before model construction.
- The CPT base replaces the already-instruct model; the Instruct template is
  imposed and patched only with zero-width Jinja generation markers.
- Assistant-only loss, BFD packing, per-config epoch evaluation, deterministic
  shuffling, epoch-named checkpoints, heartbeat output, cache-only loading, and
  overlength rejection are added.
- Effective batch is `1 x 16 x 4 = 64` packed sequences. The Mac stand-in is
  `1 x 1 x 1`.
- Weight decay is zero per the WP2 brief. Adam beta2 and gradient clipping stay
  at the plan values 0.99 and 1.0.
- Phase A uses 3% warmup plus constant LR; the replicate and phase-B arms use
  3% warmup plus cosine decay to 10% of peak LR.
- The reference's direct bf16 model load is replaced by fp32 model load plus
  bf16 mixed compute, specifically to retain fp32 master weights.
