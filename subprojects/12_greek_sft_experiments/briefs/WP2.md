# Brief WP2 — the trainer and its local dry run

**Goal.** A single-process SFT entrypoint faithful to the Apertus recipe, runnable on the Mac with a
stand-in model and on a GH200 node by Claude, plus per-arm configs and a local test.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5 (the cluster clause — your script must
satisfy every numbered point); `EXECUTION_PLAN_20260904.md` §1–2 (WP2 row) and §4 caveat 1–2;
`SFT_PLAN_20260903.md` §5, §10 (grid: warmup + constant lr for phase A; cosine for phase B/replicate),
`references/apertus-finetuning-recipes/sft_train.py`, `configs/sft_full.yaml`, `zero3.yaml`, `README.md`.

**Deliverable paths (only these):** `cluster/sft_train.py`, `cluster/configs/*.yaml`,
`cluster/test_trainer_local.py`, `cluster/README.md`, `briefs/WP2.REPORT.md`.

**Spec.**
1. `cluster/sft_train.py`: TRL `SFTTrainer` as in the recipe, but: `--config <yaml>` selects the arm;
   dataset = `data/arms/<arm>/train.jsonl` (+ `dev_all.jsonl` for eval loss per config, computed at
   every epoch end); chat template imposed from `swiss-ai/Apertus-8B-Instruct-2509` onto the CPT
   tokenizer (set `tokenizer.chat_template`; assert the 13 control tokens resolve to ids 61–72 and
   that `eos` is `<|assistant_end|>`'s behaviour for stopping — decide and document whether
   generation should stop on `<|assistant_end|>` (id 68) and set `eos_token_id` accordingly);
   `packing=True`, `assistant_only_loss=True` (verify TRL's requirement for `{% generation %}` markers
   in the template — if the Apertus template lacks them, add them in a copy of the template so that
   ONLY assistant content is unmasked; test this), `max_length=4096`, effective batch 64 (per-device ×
   grad-accum × 4 GPUs; also a single-GPU/MPS setting for the Mac), warmup 3%, schedule from config
   (`constant_with_warmup` or `cosine_with_min_lr` min 10%), lr from config, weight decay 0,
   bf16 autocast with **fp32 master weights** (document exactly how: e.g. DeepSpeed ZeRO-3 with fp32
   params + bf16 compute, or torch AMP with fp32 params), gradient checkpointing on, checkpoint at
   every epoch end into `--out-dir/epoch<k>/` (HF format, loadable with `from_pretrained`), seed from
   config, `--max-steps`, `--limit`, `--dry-run`, heartbeat line every ≤60 s
   (`HB step=<n> loss=<x> tok/s=<y> mem=<z>`), fail-fast validation of data/tokenizer/template before
   the model loads, `HF_HUB_OFFLINE`-compatible, header `RESOURCES:`.
2. Configs: `E1_lr1e-5_3ep_const.yaml`, `E1_lr5e-6_3ep_const.yaml` (phase A), `E1_cos.yaml`,
   `E1last_cos.yaml` (revision `17-step18284-tokens77B`), `E2_cos.yaml`, `E3_cos.yaml`, `E3prime_cos.yaml`
   (epochs/lr left as `TODO_FROM_GRID`), `smoke.yaml` (E1, 200 steps), `mac_dryrun.yaml` (stand-in
   model `HuggingFaceTB/SmolLM2-135M` or any ≤200M model whose tokenizer you extend with the 13
   control tokens for the test; 5 steps; tiny batch).
3. `cluster/test_trainer_local.py`: runs the Mac dry run and asserts: (a) on three real rows the loss
   mask is −100 on every system/user/control token and unmasked exactly on assistant content
   (print the decoded unmasked spans); (b) packing respects boundaries (no cross-example attention —
   check TRL's `padding_free`/position-id reset behaviour and state what it does); (c) the epoch
   checkpoint reloads and produces the same logits on one example; (d) `--dry-run` prints the
   resolved plan and exits 0 without loading the model; (e) the heartbeat appears.
4. `cluster/README.md`: how Claude runs it on a node (one `srun` command inside the workbench), the
   deepspeed/accelerate launch line for 4 GPUs, the exact env, and every deviation from the recipe.

**Acceptance (Claude runs):** `python cluster/sft_train.py --dry-run --config cluster/configs/E1_lr1e-5_3ep_const.yaml`
exits 0 with the plan; `python cluster/test_trainer_local.py` prints `OK` (all five checks).
