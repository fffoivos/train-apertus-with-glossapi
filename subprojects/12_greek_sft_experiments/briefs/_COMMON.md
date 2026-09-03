## Common context (every brief)

You are executing ONE work package of `EXECUTION_PLAN_20260904.md` (read §0–§2) under
`CLUSTER_PROTOCOL.md` (read §5 — the cluster clause binds you). Repository root for this package is
the current directory (`subprojects/12_greek_sft_experiments`). Python: use
`/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python`
(has datasets, transformers 5.x, jinja2, torch, trl, peft, pytest); do not install packages — list any
you would need in your report. Do not `git commit`; do not touch files outside your deliverable paths;
do not write under `results/`. Do not use `ssh`, `sbatch`, `salloc`, `srun`, `scancel`. Never quote a
dataset row as an example in code or prompts. Keep Greek script out of any prompt that must produce
another language. When done, write `briefs/<WP>.REPORT.md`: what you built, the exact commands you ran
locally and their output, what you could not test, open questions. Do not claim anything you did not run.

Facts you may rely on (verified 2026-09-04 by Claude):
- Data: private HF dataset `fffoivos/Greek-SFT-translated-and-adapted`, configs `no_robots, coconot,
  personas_if, smolcon, oasst, everyday, systemchats` (Greek; field `el_messages` = the conversation,
  `en.messages` = the English source, `category`, `row_id`, `edit`, `sol`), `euroblocks_fr`,
  `euroblocks_de`, `apertus_en` (same schema; `el_messages` holds the fr/de/en conversation),
  `no_robots_en_pov` (`messages` = English conversation, `el_messages` = Greek twin, `pair`).
  Files: `data/natural_greek_sft_<config>.jsonl`. The HF token is in `~/.cache/huggingface/token`.
- Base model: `fffoivos/apertus-8b-greek-cpt` revision `18-avg-uniform5-tokens30B-50B` (vocab 148,992,
  no chat_template set, eos `</s>` id 2, bos `<s>`). The chat template to impose is
  `swiss-ai/Apertus-8B-Instruct-2509`'s; all 13 of its control tokens exist in the CPT tokenizer with
  the SAME ids (`<|system_start|>`=61 … `<|tools_suffix|>`=72). Rendered example:
  `<s><|system_start|>S<|system_end|><|developer_start|>Deliberation: disabled\nTool Capabilities: disabled<|developer_end|><|user_start|>U<|user_end|><|assistant_start|>A<|assistant_end|>`
- Terminal checkpoint for the E1-last arm: revision `17-step18284-tokens77B` (= `main`).
- Reference trainer: `references/apertus-finetuning-recipes/sft_train.py` (TRL `SFTTrainer`, `TrlParser`
  over `(ScriptArguments, SFTConfig, ModelConfig)`, config `references/apertus-finetuning-recipes/configs/sft_full.yaml`).
- Cluster (Claude runs it, you don't): Clariden GH200 nodes (4 GPUs, Grace CPU, aarch64), uenv
  `pytorch/v2.9.1:v2`, `$SCRATCH=/iopsstor/scratch/cscs/fffoivos`, HF cache `~/.cache/huggingface`.
  Assume aarch64 + CUDA 12 + torch 2.9 on the node; the Mac is arm64 + MPS/CPU for dry runs.
- Token counts (Apertus template): Greek seven configs 9.34 M; no_robots_en_pov 3.25 M; apertus_en 2.31 M;
  euroblocks fr+de 0.53 M. Arms: E1 = the seven Greek configs; E2 = E1 + no_robots_en_pov; E3 = E1 +
  apertus_en + euroblocks_fr + euroblocks_de; E3′ = E3 but with the raw source conversation
  (`en.messages`) of those three configs instead of the adapted one.
