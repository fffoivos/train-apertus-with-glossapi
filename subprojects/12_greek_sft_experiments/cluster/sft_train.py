#!/usr/bin/env python3
"""Single-process TRL SFT entrypoint; launch distribution with Accelerate.

RESOURCES: nodes=1 gpus=4 walltime=01:30 mem=480GB
"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# All Hub reads in this program are cache-only. Setting these before importing
# Transformers also makes an accidentally added Hub read fail instead of using
# an allocation's network connection.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
import yaml
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GPT2Config,
    TrainerCallback,
    set_seed,
)
from trl import SFTConfig, SFTTrainer
from trl.chat_template_utils import (
    has_generation_markers,
    is_chat_template_stop_token_trained,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_END = "<|assistant_end|>"
ASSISTANT_END_ID = 68
# The brief calls these "13 control tokens" while the stated inclusive ID
# interval 61..72 contains twelve. These are the twelve Apertus role/tool
# controls; together with BOS <s> they are the thirteen structural tokens.
APERTUS_CONTROL_IDS = {
    "<|system_start|>": 61,
    "<|system_end|>": 62,
    "<|developer_start|>": 63,
    "<|developer_end|>": 64,
    "<|user_start|>": 65,
    "<|user_end|>": 66,
    "<|assistant_start|>": 67,
    "<|assistant_end|>": 68,
    "<|inner_prefix|>": 69,
    "<|inner_suffix|>": 70,
    "<|tools_prefix|>": 71,
    "<|tools_suffix|>": 72,
}
SUPPORTED_PACKING_ATTENTION = {
    "flash_attention_2",
    "flash_attention_3",
    "kernels-community/flash-attn2",
    "kernels-community/flash-attn3",
    "kernels-community/vllm-flash-attn3",
}


class ConfigError(RuntimeError):
    """An expected, user-actionable preflight failure."""


@dataclass
class ValidatedData:
    train_rows: list[dict[str, Any]]
    eval_rows: list[dict[str, Any]]
    train_tokens: int
    train_lengths: list[int]
    eval_tokens: int


def _path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise ConfigError(f"config file does not exist: {config_path}")
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigError(f"cannot parse config {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError(f"config must be a YAML mapping: {config_path}")
    payload["_config_path"] = str(config_path)
    return payload


def validate_config(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    required = {
        "run_name",
        "arm",
        "model_name_or_path",
        "tokenizer_name_or_path",
        "template_source",
        "train_file",
        "eval_file",
        "learning_rate",
        "num_train_epochs",
        "lr_scheduler_type",
        "warmup_ratio",
        "per_device_train_batch_size",
        "gradient_accumulation_steps",
        "max_length",
        "seed",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ConfigError(f"config is missing keys: {', '.join(missing)}")
    for key in ("learning_rate", "num_train_epochs"):
        if config[key] == "TODO_FROM_GRID":
            raise ConfigError(f"{key}=TODO_FROM_GRID must be resolved before this arm can run")
    if config["lr_scheduler_type"] not in {"constant_with_warmup", "cosine_with_min_lr"}:
        raise ConfigError(f"unsupported lr_scheduler_type: {config['lr_scheduler_type']}")
    if int(config["max_length"]) <= 0:
        raise ConfigError("max_length must be positive")
    if not 0.0 <= float(config["warmup_ratio"]) < 1.0:
        raise ConfigError("warmup_ratio must be in [0, 1)")
    if config["lr_scheduler_type"] == "cosine_with_min_lr":
        if float(config.get("min_lr_rate", 0.1)) != 0.1:
            raise ConfigError("cosine_with_min_lr requires min_lr_rate=0.1")
    config = dict(config)
    config["train_file"] = str(_path(config["train_file"]).resolve())
    config["eval_file"] = str(_path(config["eval_file"]).resolve())
    config["world_size"] = int(os.environ.get("WORLD_SIZE", config.get("planned_world_size", 4)))
    config["max_steps"] = args.max_steps if args.max_steps is not None else int(config.get("max_steps", -1))
    config["limit"] = args.limit
    config["out_dir"] = str(Path(args.out_dir).expanduser().resolve()) if args.out_dir else None
    if not args.dry_run and not config["out_dir"]:
        raise ConfigError("--out-dir is required unless --dry-run is used")
    if not args.dry_run:
        out_dir = Path(config["out_dir"])
        if out_dir.exists() and any(out_dir.iterdir()):
            raise ConfigError(f"output directory is not empty: {out_dir}")
    return config


def _read_jsonl(path: str, kind: str, limit: int | None) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        raise ConfigError(f"{kind} input does not exist: {source}")
    rows: list[dict[str, Any]] = []
    try:
        with source.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ConfigError(f"{kind} row {line_number} is not an object")
                messages = value.get("messages")
                if not isinstance(messages, list) or not messages:
                    raise ConfigError(f"{kind} row {line_number} has no messages list")
                assistant_count = 0
                trainable_count = 0
                for message_number, message in enumerate(messages, 1):
                    if not isinstance(message, dict):
                        raise ConfigError(
                            f"{kind} row {line_number} message {message_number} is not an object"
                        )
                    role = message.get("role")
                    content = message.get("content")
                    if role not in {"system", "user", "assistant"}:
                        raise ConfigError(
                            f"{kind} row {line_number} message {message_number} has invalid role"
                        )
                    if not isinstance(content, str) or not content.strip():
                        raise ConfigError(
                            f"{kind} row {line_number} message {message_number} has empty/non-string content"
                        )
                    train_flag = message.get("train", True)
                    if not isinstance(train_flag, bool):
                        raise ConfigError(
                            f"{kind} row {line_number} message {message_number} has a non-boolean train flag"
                        )
                    if role != "assistant" and train_flag is not True:
                        raise ConfigError(
                            f"{kind} row {line_number} message {message_number} sets train on a non-assistant message"
                        )
                    assistant_count += role == "assistant"
                    trainable_count += role == "assistant" and train_flag
                if not assistant_count:
                    raise ConfigError(f"{kind} row {line_number} has no assistant message")
                if not trainable_count:
                    raise ConfigError(f"{kind} row {line_number} has no trainable assistant message (all train=false)")
                rows.append(value)
                if limit is not None and len(rows) >= limit:
                    break
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"cannot read {kind} input {source}: {exc}") from exc
    if not rows:
        raise ConfigError(f"{kind} input is empty: {source}")
    return rows


def patch_apertus_template(template: str) -> str:
    """Add assistant-content masks without changing rendered text.

    The upstream Apertus template has no generation markers. The training data
    contract permits only string-valued system/user/assistant messages, so the
    string assistant emission and both assistant EOT sites are the only spans
    marked. Assistant-start and every other structural token remain masked;
    assistant-end is deliberately a target so the model learns to stop.
    """
    if has_generation_markers(template):
        return template
    assistant_branch = "{%- elif message.role == 'assistant' -%}"
    tool_branch = "{%- elif message.role == 'tool' -%}"
    try:
        begin = template.index(assistant_branch)
        end = template.index(tool_branch, begin)
    except ValueError as exc:
        raise ConfigError("Apertus template does not contain the expected assistant branch") from exc
    segment = template[begin:end]
    expression = "{{ message.content }}"
    if segment.count(expression) != 1:
        raise ConfigError("Apertus template assistant string emission changed upstream")
    segment = segment.replace(
        expression,
        "{% generation %}{{ message.content }}{% endgeneration %}",
    )
    template = template[:begin] + segment + template[end:]
    eot_sites = (
        "            {{ end_assistant_token }}",
        "    {{ end_assistant_token }}",
    )
    for site in eot_sites:
        if template.count(site) != 1:
            raise ConfigError("Apertus template assistant-end emission changed upstream")
        template = template.replace(
            site,
            site.replace(
                "{{ end_assistant_token }}",
                "{% generation %}{{ end_assistant_token }}{% endgeneration %}",
            ),
        )
    return template


def prepare_tokenizer(config: dict[str, Any]):
    tokenizer_name = config["tokenizer_name_or_path"]
    # The revision applies to whatever is a hub id; a local checkpoint directory (stage 2 trains from stage 1's epoch dir) takes none.
    revision = None if os.path.isdir(tokenizer_name) else config.get("revision")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name,
            revision=revision,
            local_files_only=True,
            trust_remote_code=False,
        )
        source = AutoTokenizer.from_pretrained(
            config["template_source"],
            revision=config.get("template_revision"),
            local_files_only=True,
            trust_remote_code=False,
        )
    except Exception as exc:
        raise ConfigError(f"tokenizer/template cache preflight failed: {exc}") from exc
    if not source.chat_template:
        raise ConfigError("template source tokenizer has no chat_template")

    if config.get("extend_control_tokens", False):
        tokenizer.add_special_tokens(
            {"additional_special_tokens": list(APERTUS_CONTROL_IDS)},
            False,
        )
    missing = [token for token in APERTUS_CONTROL_IDS if token not in tokenizer.get_vocab()]
    if missing:
        raise ConfigError(f"tokenizer is missing Apertus controls: {', '.join(missing)}")
    actual = {token: tokenizer.convert_tokens_to_ids(token) for token in APERTUS_CONTROL_IDS}
    if config.get("require_apertus_control_ids", True) and actual != APERTUS_CONTROL_IDS:
        raise ConfigError(f"Apertus control-token ID mismatch: {actual}")
    for token, token_id in actual.items():
        if tokenizer.encode(token, add_special_tokens=False) != [token_id]:
            raise ConfigError(f"control token is not atomic: {token}")

    # Preserve an existing pad token (GPT-2's original EOS in the local stand-in)
    # before changing EOS to the Apertus end-of-assistant token.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.chat_template = patch_apertus_template(source.chat_template)
    tokenizer.eos_token = ASSISTANT_END
    if config.get("require_apertus_control_ids", True) and tokenizer.eos_token_id != ASSISTANT_END_ID:
        raise ConfigError(f"assistant EOS must have id {ASSISTANT_END_ID}, got {tokenizer.eos_token_id}")
    if not has_generation_markers(tokenizer.chat_template):
        raise ConfigError("training chat template has no generation markers")
    if not is_chat_template_stop_token_trained(tokenizer):
        raise ConfigError("assistant end token is outside the training loss mask")

    # Verify the patched template is render-identical to upstream on a synthetic
    # ASCII probe. No dataset row is embedded or exposed here.
    probe = [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "U"},
        {"role": "assistant", "content": "A"},
    ]
    upstream_render = tokenizer.apply_chat_template(
        probe, tokenize=False, chat_template=source.chat_template
    )
    patched_render = tokenizer.apply_chat_template(probe, tokenize=False)
    if upstream_render != patched_render:
        raise ConfigError("training marker patch changed the rendered Apertus template")
    return tokenizer, actual


def _mask_runs(mask: list[int]) -> list[tuple[int, int]]:
    """Contiguous [start, end) spans of 1s in a 0/1 mask."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, bit in enumerate(list(mask) + [0]):
        if bit and start is None:
            start = index
        elif not bit and start is not None:
            runs.append((start, index))
            start = None
    return runs


def tokenize_messages(tokenizer, messages: list[dict[str, Any]]) -> dict[str, list[int]]:
    """Render a conversation and build labels for the supervised assistant turns.

    Every assistant message is supervised unless it carries ``"train": false``
    (a context-only turn: a planted failure the model must see but never
    imitate). Only role/content reach the template; the patched Apertus
    template yields exactly one contiguous generation span per assistant
    message (content followed by the assistant-end token), which is what lets
    the per-message flag map onto the token mask.
    """
    render_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    train_flags = [bool(m.get("train", True)) for m in messages if m["role"] == "assistant"]
    rendered = tokenizer.apply_chat_template(
        render_messages,
        tokenize=True,
        return_dict=True,
        return_assistant_tokens_mask=True,
    )
    input_ids = list(rendered["input_ids"])
    assistant_mask = list(rendered.get("assistant_masks", []))
    if len(input_ids) != len(assistant_mask) or not any(assistant_mask):
        raise ConfigError("chat template did not produce a non-empty assistant mask")
    # Group the template's generation spans by assistant turn: each turn's group ends with the span that carries
    # the assistant-end token. A turn can render as more than one span when its content ends in a character that
    # the byte-level tokenizer splits (an emoji): the template's offset-based mask leaves the trailing byte tokens
    # unmarked, so the content span and the end-token span are separated by one or two unmasked content tokens.
    # Those gap tokens are content, never structure (the end token follows the content directly in the Apertus
    # template); they are supervised for a target turn and masked with the rest for a context turn.
    end_id = tokenizer.convert_tokens_to_ids(ASSISTANT_END)
    control_ids = set(tokenizer.convert_tokens_to_ids(list(APERTUS_CONTROL_IDS)))
    runs = _mask_runs(assistant_mask)
    groups: list[tuple[int, int]] = []
    group_start: int | None = None
    for start, end in runs:
        if group_start is None:
            group_start = start
        if end_id in input_ids[start:end]:
            groups.append((group_start, end))
            group_start = None
    if group_start is not None or len(groups) != len(train_flags):
        raise ConfigError(
            f"assistant mask yields {len(groups)} turn groups (+{int(group_start is not None)} open) for {len(train_flags)} assistant messages"
        )
    for (start, end), flag in zip(groups, train_flags, strict=True):
        gap = [index for index in range(start, end) if not assistant_mask[index]]
        if len(gap) > 3 or any(input_ids[index] in control_ids for index in gap):
            raise ConfigError(f"unexpected unmasked tokens inside an assistant turn at {gap[:5]}")
        for index in range(start, end):
            assistant_mask[index] = 1 if flag else 0
    if not any(assistant_mask):
        raise ConfigError("row has no supervised assistant tokens after applying train=false flags")
    labels = [token_id if bit else -100 for token_id, bit in zip(input_ids, assistant_mask, strict=True)]
    return {"input_ids": input_ids, "assistant_masks": assistant_mask, "labels": labels}


def validate_and_tokenize_data(
    config: dict[str, Any], tokenizer, limit: int | None
) -> ValidatedData:
    train_rows = _read_jsonl(config["train_file"], "train", limit)
    eval_rows = _read_jsonl(config["eval_file"], "eval", limit)
    max_length = int(config["max_length"])
    train_lengths: list[int] = []
    eval_lengths: list[int] = []
    for kind, rows, lengths in (
        ("train", train_rows, train_lengths),
        ("eval", eval_rows, eval_lengths),
    ):
        for index, row in enumerate(rows, 1):
            try:
                tokenized = tokenize_messages(tokenizer, row["messages"])
            except Exception as exc:
                raise ConfigError(f"{kind} row {index} template/tokenization failed: {exc}") from exc
            length = len(tokenized["input_ids"])
            if length > max_length:
                raise ConfigError(
                    f"{kind} row {index} is {length} tokens, exceeding max_length={max_length}; truncation is forbidden"
                )
            lengths.append(length)
    return ValidatedData(
        train_rows=train_rows,
        eval_rows=eval_rows,
        train_tokens=sum(train_lengths),
        train_lengths=train_lengths,
        eval_tokens=sum(eval_lengths),
    )


def _bfd_bin_count(lengths: list[int], capacity: int) -> int:
    """Count bins with best-fit decreasing, matching TRL's BFD planning shape."""
    remaining: list[int] = []
    for length in sorted(lengths, reverse=True):
        candidates = [(space - length, index) for index, space in enumerate(remaining) if space >= length]
        if candidates:
            _, index = min(candidates)
            remaining[index] -= length
        else:
            remaining.append(capacity - length)
    return len(remaining)


def resolved_plan(config: dict[str, Any], data: ValidatedData, control_ids: dict[str, int]) -> dict[str, Any]:
    world_size = int(config["world_size"])
    micro = int(config["per_device_train_batch_size"])
    accumulation = int(config["gradient_accumulation_steps"])
    effective_batch = micro * accumulation * world_size
    packed_sequences = _bfd_bin_count(data.train_lengths, int(config["max_length"]))
    steps_per_epoch = math.ceil(packed_sequences / effective_batch)
    planned_steps = math.ceil(steps_per_epoch * float(config["num_train_epochs"]))
    if int(config["max_steps"]) > 0:
        # Transformers defines max_steps as an override of num_train_epochs,
        # not merely a cap. This is what makes smoke.yaml exactly 200 steps.
        planned_steps = int(config["max_steps"])
    return {
        "run_name": config["run_name"],
        "arm": config["arm"],
        "model": config["model_name_or_path"],
        "revision": config.get("revision"),
        "train_file": config["train_file"],
        "eval_file": config["eval_file"],
        "out_dir": config["out_dir"],
        "train_rows": len(data.train_rows),
        "eval_rows": len(data.eval_rows),
        "train_tokens": data.train_tokens,
        "eval_tokens": data.eval_tokens,
        "expected_full_train_tokens": config.get("expected_train_tokens"),
        "packed_sequences_bfd": packed_sequences,
        "steps_per_epoch": steps_per_epoch,
        "planned_optimizer_steps": planned_steps,
        "max_steps_override": config["max_steps"],
        "max_length": config["max_length"],
        "epochs": config["num_train_epochs"],
        "learning_rate": config["learning_rate"],
        "lr_scheduler_type": config["lr_scheduler_type"],
        "warmup_ratio": config["warmup_ratio"],
        "min_lr_rate": config.get("min_lr_rate"),
        "packing": True,
        "packing_strategy": "bfd",
        "padding_free": True,
        "assistant_only_loss": True,
        "per_device_train_batch_size": micro,
        "gradient_accumulation_steps": accumulation,
        "world_size": world_size,
        "effective_batch": effective_batch,
        "model_parameter_dtype": "float32",
        "compute_autocast": "bfloat16" if config.get("bf16", True) else "float32",
        "eos_token": ASSISTANT_END,
        "eos_token_id": control_ids[ASSISTANT_END],
        "offline": True,
    }


def _memory_text() -> str:
    if torch.cuda.is_available():
        return f"{torch.cuda.max_memory_allocated() / 2**30:.2f}GiB"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return f"{torch.mps.current_allocated_memory() / 2**30:.2f}GiB"
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux reports KiB.
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    return f"{peak_bytes / 2**30:.2f}GiB"


class Heartbeat:
    def __init__(self, interval_seconds: float = 30.0):
        self.interval_seconds = interval_seconds
        self.step = 0
        self.loss = float("nan")
        self.tokens = 0
        self.started = time.monotonic()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def line(self) -> str:
        elapsed = max(time.monotonic() - self.started, 1e-9)
        return (
            f"HB step={self.step} loss={self.loss:.6g} "
            f"tok/s={self.tokens / elapsed:.2f} mem={_memory_text()}"
        )

    def emit(self) -> None:
        print(self.line(), flush=True)

    def start(self) -> None:
        self.emit()

        def run() -> None:
            while not self._stop.wait(self.interval_seconds):
                self.emit()

        self._thread = threading.Thread(target=run, name="sft-heartbeat", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


class HeartbeatCallback(TrainerCallback):
    def __init__(self, heartbeat: Heartbeat):
        self.heartbeat = heartbeat

    def on_log(self, args, state, control, logs=None, **kwargs):
        logs = logs or {}
        self.heartbeat.step = int(state.global_step)
        if "loss" in logs:
            loss = float(logs["loss"])
            if not math.isfinite(loss):
                raise RuntimeError(f"non-finite training loss at step {state.global_step}")
            self.heartbeat.loss = loss
        self.heartbeat.tokens = int(getattr(state, "num_input_tokens_seen", 0) or 0)
        self.heartbeat.emit()


class EpochNamedSFTTrainer(SFTTrainer):
    """Keep Trainer/DeepSpeed's save path, then atomically name full epochs."""

    def _save_checkpoint(self, model, trial):
        super()._save_checkpoint(model, trial)
        epoch_value = float(self.state.epoch or 0.0)
        epoch_number = int(round(epoch_value))
        if epoch_number < 1 or abs(epoch_value - epoch_number) > 1e-5:
            return
        run_dir = Path(self._get_output_dir(trial=trial))
        source = run_dir / f"checkpoint-{self.state.global_step}"
        target = run_dir / f"epoch{epoch_number}"
        self.accelerator.wait_for_everyone()
        if self.args.should_save:
            if target.exists():
                raise ConfigError(f"refusing to overwrite epoch checkpoint: {target}")
            source.rename(target)
            if self.state.best_model_checkpoint == str(source):
                self.state.best_model_checkpoint = str(target)
        self.accelerator.wait_for_everyone()


def _dataset(rows: list[dict[str, Any]]) -> Dataset:
    return Dataset.from_list([{"messages": row["messages"], "config": row.get("config", "all")} for row in rows])


def _eval_datasets(rows: list[dict[str, Any]]) -> dict[str, Dataset]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("config", "all"))].append({"messages": row["messages"]})
    return {name: Dataset.from_list(values) for name, values in sorted(grouped.items())}


def _sft_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    scheduler_kwargs = None
    if config["lr_scheduler_type"] == "cosine_with_min_lr":
        scheduler_kwargs = {"min_lr_rate": float(config.get("min_lr_rate", 0.1))}
    kwargs: dict[str, Any] = {
        "output_dir": config["out_dir"],
        "run_name": config["run_name"],
        "learning_rate": float(config["learning_rate"]),
        "lr_scheduler_type": config["lr_scheduler_type"],
        "lr_scheduler_kwargs": scheduler_kwargs,
        "weight_decay": 0.0,
        "adam_beta1": float(config.get("adam_beta1", 0.9)),
        "adam_beta2": float(config.get("adam_beta2", 0.99)),
        "max_grad_norm": float(config.get("max_grad_norm", 1.0)),
        "num_train_epochs": float(config["num_train_epochs"]),
        "max_steps": int(config["max_steps"]),
        "per_device_train_batch_size": int(config["per_device_train_batch_size"]),
        "per_device_eval_batch_size": int(config.get("per_device_eval_batch_size", 1)),
        "gradient_accumulation_steps": int(config["gradient_accumulation_steps"]),
        "gradient_checkpointing": True,
        "gradient_checkpointing_kwargs": {"use_reentrant": True},
        "bf16": bool(config.get("bf16", True)),
        "fp16": False,
        "max_length": int(config["max_length"]),
        "packing": True,
        "packing_strategy": "bfd",
        "padding_free": False,  # BFD makes this true inside TRL.
        "eval_packing": False,
        "assistant_only_loss": True,
        "completion_only_loss": False,
        "shuffle_dataset": True,
        "eval_strategy": "epoch",
        "save_strategy": "steps" if int(config.get("save_steps", 0)) > 0 else "epoch",
        **({"save_steps": int(config["save_steps"])} if int(config.get("save_steps", 0)) > 0 else {}),
        "logging_strategy": "steps",
        "logging_steps": 1,
        "logging_first_step": True,
        "include_num_input_tokens_seen": True,
        "report_to": "none",
        "disable_tqdm": bool(config.get("disable_tqdm", False)),
        "seed": int(config["seed"]),
        "data_seed": int(config["seed"]),
        "save_total_limit": (int(config["save_total_limit"]) if config.get("save_total_limit") else None),
        "dataloader_num_workers": int(config.get("dataloader_num_workers", 0)),
        "dataloader_pin_memory": bool(config.get("dataloader_pin_memory", torch.cuda.is_available())),
        "optim": config.get("optim", "adamw_torch"),
        "use_cpu": bool(config.get("use_cpu", False)),
        "remove_unused_columns": True,
    }
    # Transformers 5.16 represents a ratio as a float in warmup_steps; older
    # releases expose warmup_ratio. Support both without weakening the config.
    fields = getattr(SFTConfig, "__dataclass_fields__", {})
    if "warmup_ratio" in fields:
        kwargs["warmup_ratio"] = float(config["warmup_ratio"])
    else:
        kwargs["warmup_steps"] = float(config["warmup_ratio"])
    return kwargs


def _load_model(config: dict[str, Any], tokenizer):
    print("MODEL_LOAD_BEGIN", flush=True)
    if config.get("random_standin", False):
        model_config = GPT2Config(
            vocab_size=len(tokenizer),
            n_positions=int(config["max_length"]),
            n_ctx=int(config["max_length"]),
            n_embd=int(config.get("standin_hidden_size", 32)),
            n_layer=int(config.get("standin_layers", 1)),
            n_head=int(config.get("standin_heads", 4)),
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
            use_cache=False,
        )
        model = AutoModelForCausalLM.from_config(model_config)
    else:
        kwargs: dict[str, Any] = {
            "revision": None if os.path.isdir(config["model_name_or_path"]) else config.get("revision"),
            "local_files_only": True,
            "trust_remote_code": False,
            "dtype": torch.float32,
            "use_cache": False,
        }
        if config.get("attn_implementation"):
            kwargs["attn_implementation"] = config["attn_implementation"]
        model = AutoModelForCausalLM.from_pretrained(config["model_name_or_path"], **kwargs)
    if model.get_input_embeddings().num_embeddings != len(tokenizer):
        if not config.get("extend_control_tokens", False):
            raise ConfigError(
                "model/tokenizer vocabulary mismatch and token extension is not enabled"
            )
        model.resize_token_embeddings(len(tokenizer))
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    if getattr(model, "generation_config", None) is not None:
        model.generation_config.eos_token_id = tokenizer.eos_token_id
        model.generation_config.pad_token_id = tokenizer.pad_token_id
    trainable_dtypes = {parameter.dtype for parameter in model.parameters() if parameter.requires_grad}
    if trainable_dtypes != {torch.float32}:
        raise ConfigError(f"master/model parameters are not exclusively fp32: {trainable_dtypes}")
    print(f"MODEL_LOAD_DONE params={sum(p.numel() for p in model.parameters())}", flush=True)
    return model


def _rename_epoch_checkpoints(out_dir: Path) -> list[Path]:
    epochs: list[Path] = []
    for checkpoint in sorted(out_dir.glob("checkpoint-*")):
        state_path = checkpoint / "trainer_state.json"
        if not state_path.is_file():
            continue
        state = json.loads(state_path.read_text(encoding="utf-8"))
        epoch_value = float(state.get("epoch", 0.0))
        epoch_number = int(round(epoch_value))
        if epoch_number < 1 or abs(epoch_value - epoch_number) > 1e-5:
            continue
        target = out_dir / f"epoch{epoch_number}"
        if target.exists():
            raise ConfigError(f"refusing to overwrite epoch checkpoint: {target}")
        checkpoint.rename(target)
        epochs.append(target)
    return sorted(epochs)


def _save_final_if_needed(trainer: SFTTrainer, tokenizer, out_dir: Path) -> Path:
    epochs = sorted(out_dir.glob("epoch*"))
    epochs.extend(path for path in _rename_epoch_checkpoints(out_dir) if path not in epochs)
    epochs.sort()
    if epochs:
        final = epochs[-1]
    else:
        epoch_number = max(1, int(math.ceil(float(trainer.state.epoch or 0.0))))
        final = out_dir / f"epoch{epoch_number}"
        trainer.save_model(str(final))
        tokenizer.save_pretrained(final)
    return final


def verify_reload(trainer: SFTTrainer, checkpoint: Path, tokenizer, row: dict[str, Any]) -> float:
    tokenized = tokenize_messages(tokenizer, row["messages"])
    ids = torch.tensor([tokenized["input_ids"][:32]], dtype=torch.long)
    model = trainer.model
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        before = model(input_ids=ids.to(device)).logits.detach().float().cpu()
    reloaded = AutoModelForCausalLM.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False, dtype=torch.float32
    )
    reloaded.eval()
    with torch.no_grad():
        after = reloaded(input_ids=ids).logits.detach().float().cpu()
    difference = float((before - after).abs().max().item())
    receipt = {"checkpoint": str(checkpoint), "max_abs_diff": difference, "tokens_compared": ids.numel()}
    (checkpoint.parent / "reload_check.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"RELOAD_CHECK max_abs_diff={difference:.9g}", flush=True)
    return difference


def run(config: dict[str, Any], data: ValidatedData, tokenizer) -> None:
    attn = config.get("attn_implementation")
    if not config.get("random_standin", False) and attn not in SUPPORTED_PACKING_ATTENTION:
        raise ConfigError("production BFD packing requires a TRL-supported FlashAttention implementation")
    out_dir = Path(config["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    set_seed(int(config["seed"]))
    heartbeat = Heartbeat(interval_seconds=float(config.get("heartbeat_seconds", 30)))
    heartbeat.start()
    try:
        model = _load_model(config, tokenizer)
        training_args = SFTConfig(**_sft_kwargs(config))
        trainer = EpochNamedSFTTrainer(
            model=model,
            args=training_args,
            train_dataset=_dataset(data.train_rows),
            eval_dataset=_eval_datasets(data.eval_rows),
            processing_class=tokenizer,
            callbacks=[HeartbeatCallback(heartbeat)],
        )
        trainer.train(resume_from_checkpoint=(config.get("resume_from_checkpoint") or None))
        checkpoint = _save_final_if_needed(trainer, tokenizer, out_dir)
        if config.get("verify_checkpoint_reload", False):
            difference = verify_reload(trainer, checkpoint, tokenizer, data.train_rows[0])
            if difference > float(config.get("reload_atol", 0.0)):
                raise RuntimeError(f"checkpoint reload logits differ by {difference}")
    finally:
        heartbeat.stop()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="arm YAML")
    parser.add_argument("--out-dir", help="exclusive output root (required for training)")
    parser.add_argument("--max-steps", type=int, help="override optimizer-step ceiling")
    parser.add_argument("--limit", type=int, help="read at most N rows from each input")
    parser.add_argument("--dry-run", action="store_true", help="validate and print plan; do not load model")
    args = parser.parse_args(argv)
    if args.max_steps is not None and args.max_steps <= 0:
        parser.error("--max-steps must be positive")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        config = validate_config(load_config(args.config), args)
        # File/schema and tokenizer/template checks all happen before model load.
        # Tokenization is also preflighted for every selected row so overlength
        # input is rejected rather than truncated by the packer.
        train_rows = _read_jsonl(config["train_file"], "train", args.limit)
        eval_rows = _read_jsonl(config["eval_file"], "eval", args.limit)
        tokenizer, control_ids = prepare_tokenizer(config)
        # Avoid opening files twice after the schema-only preflight above.
        data = validate_and_tokenize_data(config, tokenizer, args.limit)
        assert len(train_rows) == len(data.train_rows) and len(eval_rows) == len(data.eval_rows)
        plan = resolved_plan(config, data, control_ids)
        print("PLAN " + json.dumps(plan, ensure_ascii=True, sort_keys=True), flush=True)
        expected_tokens = config.get("expected_train_tokens")
        if args.limit is None and expected_tokens:
            relative_difference = abs(data.train_tokens - int(expected_tokens)) / int(expected_tokens)
            if relative_difference > 0.02:
                print(
                    "PLAN_WARNING exact_train_tokens_differs_from_planning_reference "
                    f"relative_difference={relative_difference:.6f}",
                    flush=True,
                )
        if args.dry_run:
            print("DRY_RUN_OK model_not_loaded=true", flush=True)
            return 0
        run(config, data, tokenizer)
        print("TRAIN_OK", flush=True)
        return 0
    except (ConfigError, OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {str(exc).replace(chr(10), ' ')}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
