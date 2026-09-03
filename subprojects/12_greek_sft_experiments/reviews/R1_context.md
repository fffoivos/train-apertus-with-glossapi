# R1 — certification of the SFT data build (WP0) and the trainer (WP2) before the first GPU minute

## PROJECT DOCS (read first, in this order)
- `subprojects/12_greek_sft_experiments/EXECUTION_PLAN_20260904.md` (§0–§4; the WP0/WP2 rows and caveats 1–2)
- `subprojects/12_greek_sft_experiments/SFT_PLAN_20260903.md` §5, §5a′, §10 (grid: warmup+constant lr phase A; cosine phase B), §11
- `subprojects/12_greek_sft_experiments/CLUSTER_PROTOCOL.md` §5 (the cluster clause every cluster script must satisfy)
- `subprojects/12_greek_sft_experiments/briefs/_COMMON.md`, `briefs/WP0.md`, `briefs/WP2.md` (what was asked)
- `subprojects/12_greek_sft_experiments/briefs/WP0.REPORT.md`, `briefs/WP2.REPORT.md` (what the executor, Sol/gpt-5.6-sol, CLAIMS — do not trust; re-derive)
- `subprojects/12_greek_sft_experiments/execution_state.json`, `EXECUTION_LOG.md`

## SCOPE
Git range `b26b4cf9..HEAD` in `~/Projects/train-apertus-with-glossapi` (files under `subprojects/12_greek_sft_experiments/{data,cluster,briefs}`; ignore `cluster/eval_jobs`, `cluster/workbench.sh`, `cluster/preflight.sh`, `cluster/ledger.sh`, `cluster/wb_watch.sh`, `cluster/reference_sbatch` — Claude's, out of scope).

## DATA ACCESS (read-only)
- Built arms: `subprojects/12_greek_sft_experiments/data/arms/{E1,E2,E3,E3prime}/train.jsonl`, `data/arms/dev_all.jsonl` (gitignored, on disk), `data/splits/*.dev.txt`, `data/stats.json`, `data/contamination_report.md`, `data/cache/` (the eleven source jsonl files from HF).
- Python with all deps: `/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python` (transformers, trl, torch, datasets, jinja2). HF token in `~/.cache/huggingface/token` (private dataset `fffoivos/Greek-SFT-translated-and-adapted`; base `fffoivos/apertus-8b-greek-cpt` rev `18-avg-uniform5-tokens30B-50B`; template source `swiss-ai/Apertus-8B-Instruct-2509`).
- You may run `python data/build_sft_mix.py --check`, `python cluster/sft_train.py --dry-run --config cluster/configs/<x>.yaml`, `python cluster/test_trainer_local.py` and your own scripts. Do NOT launch background jobs; do NOT touch the cluster (no ssh); do NOT modify files.

## GATES TO CHECK (verify firsthand, report raw numbers)
1. Splits: for every config, dev row_ids ⟂ train row_ids in every arm; dev = 2% rounded; `dev_all.jsonl` = union; seeds deterministic.
2. Arms: E1 = the seven Greek configs; E2 = E1 + no_robots_en_pov (`messages`); E3 = E1 + apertus_en + euroblocks_fr + euroblocks_de (adapted `el_messages`); E3prime = E3 with the raw `en.messages` for those three configs — check on samples that E3′ rows are the ORIGINAL English/French/German conversations and E3 rows the adapted ones, same row_ids.
3. No row over 4096 tokens under the Apertus-Instruct template rendered with the CPT tokenizer; excluded rows listed, not silently dropped; roles only system/user/assistant; no empty assistant turns.
4. Contamination: recompute exact overlap of train user turns vs GreekMMLU test (`dascim/GreekMMLU`), GSM8K test, IFEval, ellinika-bench prompts (`~/Projects/apertus-local-chat/benchmark/data/`); the report claims 5 exact GreekMMLU hits removed, 0 remaining — confirm.
5. Token stats: recompute E1 train tokens with the CPT tokenizer (report claims 6,182,367) and the assistant-token share.
6. Trainer: (a) the loss mask on ≥3 real rows — −100 on every system/user/control token; assistant content unmasked; `<|assistant_end|>` (id 68) unmasked as target (the report argues this is deliberate so the model learns to stop — judge whether it is right); (b) packing: no cross-example attention leakage (position ids reset / padding-free path) — state what TRL actually does with the chosen settings; (c) fp32 master weights with bf16 compute — is it really so under the accelerate/deepspeed config shipped (`cluster/configs/zero3.yaml`) and the single-GPU path?; (d) schedules: `E1_lr*_3ep_const.yaml` = warmup + constant; `*_cos.yaml` = cosine with min lr; epochs/lr as the plan says; effective batch 64 on 4 GPUs; (e) epoch checkpoints reload identically; (f) the cluster clause: `--dry-run` without model load, `--max-steps`, `--limit`, fail-fast validation, heartbeat ≤60 s, no network at runtime, outputs only under `--out-dir`, `RESOURCES:` header, no scheduler calls.
7. Nothing forbidden committed (no data rows, no checkpoints, no tokens/credentials in the diff).

## STEP FOCUS
This is checkpoint #2 of the plan (before composition: data × trainer meet the GPU next). A wrong mask or a leaked eval prompt here poisons every later run. Be adversarial about the mask, the packing and E3′.
