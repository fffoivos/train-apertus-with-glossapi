#!/usr/bin/env python3
"""DPO01 entrypoint (DPO01_EXECUTION_PLAN_20260918.md §5-§6): one full-parameter, one-epoch sigmoid DPO run against the frozen SFT parent.
Single process; launch distribution with Accelerate. Tokenizer, chat template and control-token safeguards are reused from sft_train.py.

  python cluster/dpo_train.py --config cluster/configs/G4F6P1_DPO01.yaml --dry-run
  accelerate launch --config_file cluster/configs/zero3_dpo01.yaml cluster/dpo_train.py --config cluster/configs/G4F6P1_DPO01.yaml --out-dir runs/G4F6P1--DPO01

RESOURCES: nodes=1 gpus=4 walltime=01:00 mem=480GB
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
from typing import Any
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import torch, yaml
from datasets import Dataset
from transformers import AutoModelForCausalLM, set_seed
from trl import DPOConfig, DPOTrainer

class AnchoredDPOTrainer(DPOTrainer):
    """DPO plus alpha * (per-example mean negative log-likelihood of the chosen completion), per DPO_EXPERIMENT_COMPARISON §2.
    The DPO term keeps TRL's summed, completion-only log probabilities. The anchor is computed from the same forward pass
    (no second forward): per-example token mean over the chosen completion, then a mean over the examples in the batch.
    alpha = 0 leaves the objective bit-for-bit plain DPO."""
    def __init__(self, *args, chosen_nll_alpha: float = 0.0, **kw):
        super().__init__(*args, **kw); self.chosen_nll_alpha = float(chosen_nll_alpha)
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        from trl.trainer.utils import selective_log_softmax
        loss, outputs = super().compute_loss(model, inputs, return_outputs=True, num_items_in_batch=num_items_in_batch)
        if self.chosen_nll_alpha:
            shift_logits = outputs.logits[..., :-1, :]
            shift_labels = inputs["input_ids"][..., 1:]
            shift_mask = inputs["completion_mask"][..., 1:]
            half = shift_logits.shape[0] // 2                       # TRL concatenates chosen then rejected
            logps = selective_log_softmax(shift_logits[:half], shift_labels[:half])
            mask = shift_mask[:half]
            nll = (-(logps * mask).sum(-1) / mask.sum(-1).clamp(min=1)).mean()
            mode = "train" if self.model.training else "eval"
            self._metrics[mode]["loss/dpo"].append(float(loss.detach()))
            self._metrics[mode]["loss/chosen_nll"].append(float(nll.detach()))
            loss = loss + self.chosen_nll_alpha * nll
        return (loss, outputs) if return_outputs else loss

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sft_train import ConfigError, prepare_tokenizer  # the validated tokenizer/template/control-id path

def sha16(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]

def read_pairs(path: str | Path) -> list[dict[str, Any]]:
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for i, r in enumerate(rows):
        for key in ("prompt", "chosen", "rejected"):
            if not isinstance(r.get(key), list) or not r[key]:
                raise ConfigError(f"{path}:{i + 1}: '{key}' must be a non-empty message list")
        if r["prompt"][-1]["role"] != "user":
            raise ConfigError(f"{path}:{i + 1}: prompt must end on a user turn")
        for key in ("chosen", "rejected"):
            if len(r[key]) != 1 or r[key][0]["role"] != "assistant":
                raise ConfigError(f"{path}:{i + 1}: '{key}' must be exactly one assistant message")
        if r["chosen"][0]["content"].strip() == r["rejected"][0]["content"].strip():
            raise ConfigError(f"{path}:{i + 1}: chosen and rejected are the same text")
    return rows

def token_lengths(tokenizer, rows: list[dict[str, Any]]) -> list[int]:
    out = []
    for r in rows:
        prompt = tokenizer.apply_chat_template(r["prompt"], tokenize=True, add_generation_prompt=True)
        longest = max(len(tokenizer(c[0]["content"], add_special_tokens=False)["input_ids"]) for c in (r["chosen"], r["rejected"]))
        out.append(len(prompt) + longest + 2)
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir")
    ap.add_argument("--dry-run", action="store_true", help="resolve data, tokenizer and the update plan; touch no GPU")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N training pairs (smoke runs)")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text())
    out_dir = Path(a.out_dir or cfg["output_dir"])
    set_seed(int(cfg.get("seed", 42)))
    tokenizer, control_ids = prepare_tokenizer(cfg)
    train_rows = read_pairs(cfg["train_file"]); dev_rows = read_pairs(cfg["dev_file"])
    if a.limit: train_rows = train_rows[: a.limit]
    max_len = int(cfg.get("max_length", 4096))
    lens = token_lengths(tokenizer, train_rows + dev_rows)
    over = [i for i, n in enumerate(lens) if n > max_len]
    if over:                                   # plan §4.6: never truncate silently
        raise ConfigError(f"{len(over)} example(s) exceed max_length={max_len}; the exporter must drop them, not the trainer")
    world = int(os.environ.get("WORLD_SIZE", "1"))
    per_device = int(cfg.get("per_device_train_batch_size", 1)); accum = int(cfg.get("gradient_accumulation_steps", 2))
    global_batch = per_device * accum * world
    updates = math.ceil(len(train_rows) / global_batch)
    warmup = int(cfg.get("warmup_steps", 2))                      # comparison plan §3: two warmup steps, then constant LR
    plan = dict(train_pairs=len(train_rows), dev_pairs=len(dev_rows), world_size=world, per_device=per_device,
                gradient_accumulation_steps=accum, effective_global_batch=global_batch, optimizer_updates=updates,
                warmup_updates=warmup, max_length=max_len, token_length_max=max(lens), token_length_median=sorted(lens)[len(lens) // 2],
                beta=float(cfg.get("beta", 0.1)), learning_rate=float(cfg["learning_rate"]), epochs=float(cfg.get("num_train_epochs", 1)),
                chosen_nll_alpha=float(cfg.get("chosen_nll_alpha", 0.0)), schedule=cfg.get("lr_scheduler_type", "constant_with_warmup"),
                arm=cfg.get("run_name"), epochs_saved=cfg.get("save_every_epoch", True),
                seed=int(cfg.get("seed", 42)), precompute_ref_log_probs=bool(cfg.get("precompute_ref_log_probs", True)),
                model=cfg["model_name_or_path"], train_sha16=sha16(cfg["train_file"]), dev_sha16=sha16(cfg["dev_file"]),
                config_sha16=sha16(a.config), trainer_sha16=sha16(__file__), control_ids=control_ids)
    # R-DPO13 [HIGH]: this was `loss_type="sigmoid"` hardcoded in DPOConfig, so a config asking for
    # another objective trained sigmoid anyway and said nothing. Two runs labelled "IPO beta 10" were
    # in fact anchored sigmoid DPO, and a whole falsification argument was built on the label. The
    # objective now comes from the config and an unsupported value stops the run.
    SUPPORTED = ("sigmoid", "ipo", "hinge", "robust", "exo_pair", "bco_pair", "sppo_hard", "nca_pair",
                 "aot", "aot_pair", "apo_zero", "apo_down")
    plan["loss_type"] = str(cfg.get("loss_type", "sigmoid"))
    if plan["loss_type"] not in SUPPORTED:
        raise ConfigError("loss_type %r is not one TRL supports: %s" % (plan["loss_type"], ", ".join(SUPPORTED)))
    try:
        import trl, inspect
        sig = inspect.signature(trl.DPOConfig.__init__)
        if "loss_type" not in sig.parameters:
            raise ConfigError("installed TRL %s has no loss_type on DPOConfig" % getattr(trl, "__version__", "?"))
    except ImportError:
        pass
    print("PLAN " + json.dumps(plan, ensure_ascii=False), flush=True)
    if a.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "dry_run_plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
        return 0
    train_ds, dev_ds = Dataset.from_list(train_rows), Dataset.from_list(dev_rows)
    dpo_args = DPOConfig(
        output_dir=str(out_dir), beta=plan["beta"], loss_type=plan["loss_type"], label_smoothing=float(cfg.get("label_smoothing", 0.0)),
        max_length=max_len, learning_rate=plan["learning_rate"], num_train_epochs=plan["epochs"],
        per_device_train_batch_size=per_device, gradient_accumulation_steps=accum, per_device_eval_batch_size=1,
        lr_scheduler_type=cfg.get("lr_scheduler_type", "constant_with_warmup"), warmup_steps=int(cfg.get("warmup_steps", 2)),
        max_grad_norm=float(cfg.get("max_grad_norm", 1.0)), weight_decay=float(cfg.get("weight_decay", 0.0)),
        adam_beta1=float(cfg.get("adam_beta1", 0.9)), adam_beta2=float(cfg.get("adam_beta2", 0.99)), adam_epsilon=float(cfg.get("adam_epsilon", 1e-8)),
        bf16=True, gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        precompute_ref_log_probs=plan["precompute_ref_log_probs"], seed=plan["seed"], logging_steps=1, report_to=[],
        save_strategy=cfg.get("save_strategy", "epoch"), save_total_limit=int(cfg.get("save_total_limit", 3)),
        eval_strategy="no", remove_unused_columns=False,
        dataset_num_proc=1, model_init_kwargs=None)
    dtype = torch.float32 if cfg.get("fp32_master_weights", True) else torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(cfg["model_name_or_path"], dtype=dtype, attn_implementation=cfg.get("attn_implementation", "sdpa"))
    model.config.use_cache = False
    for module in model.modules():                                  # plan §5: no dropout while likelihoods are compared
        if isinstance(module, torch.nn.Dropout): module.p = 0.0
    ref_model = None
    if not plan["precompute_ref_log_probs"]:
        ref_model = AutoModelForCausalLM.from_pretrained(cfg["model_name_or_path"], dtype=dtype, attn_implementation=cfg.get("attn_implementation", "sdpa"))
        ref_model.eval()
        for p in ref_model.parameters(): p.requires_grad_(False)
    trainer = AnchoredDPOTrainer(model=model, ref_model=ref_model, args=dpo_args, train_dataset=train_ds, eval_dataset=dev_ds,
                                 processing_class=tokenizer, chosen_nll_alpha=float(cfg.get("chosen_nll_alpha", 0.0)))
    started = time.time()
    result = trainer.train()
    trainer.save_model(str(out_dir / "final")); tokenizer.save_pretrained(str(out_dir / "final"))
    metrics = trainer.evaluate()
    receipt = dict(plan=plan, train_runtime_s=round(time.time() - started, 1), train_metrics=result.metrics, dev_metrics=metrics,
                   parent=cfg["model_name_or_path"], out=str(out_dir / "final"), world_size=world,
                   torch=torch.__version__, cuda=torch.version.cuda, finished_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if int(os.environ.get("RANK", "0")) == 0:                    # one writer only: four ranks writing concatenated the JSON
        (out_dir / "run_receipt.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False, default=str))
    print("DPO_DONE " + json.dumps({k: receipt[k] for k in ("train_runtime_s", "dev_metrics")}, ensure_ascii=False, default=str), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
