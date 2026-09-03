#!/usr/bin/env python3
# RESOURCES: nodes=1 gpus=4 walltime=00:30 mem=200GB
"""Generate deterministic continuations for the fixed development prompts."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, NoReturn

# A populated cache is a prerequisite on Clariden. These flags prevent an
# accidental network request after an allocation has started.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ASSISTANT_END = "<|assistant_end|>"
ASSISTANT_END_ID = 68
CONTROL_TOKENS = [
    "<|system_start|>",
    "<|system_end|>",
    "<|developer_start|>",
    "<|developer_end|>",
    "<|user_start|>",
    "<|user_end|>",
    "<|assistant_start|>",
    ASSISTANT_END,
    "<|inner_prefix|>",
    "<|inner_suffix|>",
    "<|tools_prefix|>",
    "<|tools_suffix|>",
]
TEMPLATE_SOURCE = "swiss-ai/Apertus-8B-Instruct-2509"


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def load_prompts(path: Path, allow_placeholders: bool) -> list[dict[str, Any]]:
    if not path.is_file():
        fail(f"prompts file not found: {path}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"invalid JSON at {path}:{line_number}: {exc.msg}")
            prompt_id = str(row.get("prompt_id") or row.get("row_id") or "")
            if not prompt_id or prompt_id in seen:
                fail(f"missing or duplicate prompt_id at {path}:{line_number}")
            seen.add(prompt_id)
            if row.get("placeholder"):
                if not allow_placeholders:
                    fail("reading40.jsonl is still a placeholder; run select_reading40.py after WP0")
            else:
                messages = row.get("messages")
                if not isinstance(messages, list) or not messages:
                    fail(f"prompt {prompt_id} has no messages")
                for message in messages:
                    if (
                        not isinstance(message, dict)
                        or message.get("role") not in {"system", "user", "assistant"}
                        or not isinstance(message.get("content"), str)
                    ):
                        fail(f"prompt {prompt_id} has an invalid message")
                if messages[-1]["role"] != "user":
                    fail(f"prompt {prompt_id} must end in a user turn")
                if row.get("language") not in {"el", "en", "fr", "de"}:
                    fail(f"prompt {prompt_id} has an invalid language")
            rows.append(row)
    if not rows:
        fail(f"prompts file is empty: {path}")
    return rows


def resolved_limit(total: int, limit: int | None, max_steps: int | None) -> int:
    caps = [total]
    if limit is not None:
        if limit < 1:
            fail("--limit must be positive")
        caps.append(limit)
    if max_steps is not None:
        if max_steps < 1:
            fail("--max-steps must be positive")
        caps.append(max_steps)
    return min(caps)


def load_and_validate_tokenizer(model_name: str):
    from transformers import AutoTokenizer

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    except Exception as exc:
        fail(f"cannot load tokenizer from the offline cache/model dir: {exc}")
    if not tokenizer.chat_template:
        try:
            source = AutoTokenizer.from_pretrained(TEMPLATE_SOURCE, local_files_only=True)
        except Exception as exc:
            fail(f"model has no chat template and cached {TEMPLATE_SOURCE} is unavailable: {exc}")
        if not source.chat_template:
            fail(f"cached {TEMPLATE_SOURCE} tokenizer has no chat template")
        tokenizer.chat_template = source.chat_template
        template_origin = TEMPLATE_SOURCE
    else:
        template_origin = model_name

    ids = [tokenizer.convert_tokens_to_ids(token) for token in CONTROL_TOKENS]
    expected = list(range(61, 73))
    if ids != expected:
        fail(f"Apertus control-token ids mismatch: got {ids}, expected {expected}")
    if tokenizer.convert_tokens_to_ids(ASSISTANT_END) != ASSISTANT_END_ID:
        fail(f"{ASSISTANT_END} is not token id {ASSISTANT_END_ID}")
    if tokenizer.bos_token != "<s>" or tokenizer.bos_token_id != 1:
        fail(f"Apertus BOS mismatch: got {tokenizer.bos_token!r} id {tokenizer.bos_token_id}, expected '<s>' id 1")
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            fail("tokenizer has neither pad_token_id nor eos_token_id")
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    return tokenizer, template_origin


def memory_string() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return f"{torch.cuda.max_memory_allocated() / 2**30:.1f}GB"
    except Exception:
        pass
    return "n/a"


class Heartbeat:
    def __init__(self) -> None:
        self.step = 0
        self.tokens = 0
        self.started = time.monotonic()
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def line(self) -> None:
        elapsed = max(time.monotonic() - self.started, 1e-9)
        print(
            f"HB step={self.step} loss=nan tok/s={self.tokens / elapsed:.2f} mem={memory_string()}",
            flush=True,
        )

    def _loop(self) -> None:
        while not self.done.wait(30):
            self.line()

    def __enter__(self) -> "Heartbeat":
        self.line()
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.done.set()
        self.thread.join(timeout=2)
        self.line()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Local model directory or cached HF model id")
    parser.add_argument("--prompts", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="Output dev_gen.jsonl (required unless --dry-run)")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-steps", type=int, help="Probe alias: cap the number of generated prompts")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        fail("--batch-size must be positive")
    rows = load_prompts(args.prompts, allow_placeholders=args.dry_run)
    count = resolved_limit(len(rows), args.limit, args.max_steps)
    selected = rows[:count]
    placeholder_count = sum(bool(row.get("placeholder")) for row in selected)
    messages = sum(len(row.get("messages", [])) for row in selected)
    chars = sum(len(m.get("content", "")) for row in selected for m in row.get("messages", []))
    config = {
        "model": args.model,
        "prompts": str(args.prompts.resolve()),
        "out": str(args.out.resolve()) if args.out else None,
        "prompt_records": count,
        "placeholder_records": placeholder_count,
        "prompt_messages": messages,
        "prompt_characters": chars,
        "prompt_token_counts": "computed after tokenizer validation; unavailable in no-model dry-run",
        "planned_steps": count,
        "batch_size": args.batch_size,
        "do_sample": False,
        "max_new_tokens": 512,
        "stop_token": ASSISTANT_END,
        "stop_token_id": ASSISTANT_END_ID,
        "offline": True,
        "single_process": True,
    }
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)
    if args.dry_run:
        print("DRY RUN OK (model not loaded; no output written)")
        return
    if args.out is None:
        fail("--out is required unless --dry-run")
    if placeholder_count:
        fail("placeholder prompts cannot be generated")

    tokenizer, template_origin = load_and_validate_tokenizer(args.model)
    rendered: list[str] = []
    prompt_token_counts: list[int] = []
    for row in selected:
        try:
            text = tokenizer.apply_chat_template(
                row["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
        except Exception as exc:
            fail(f"chat template rejected prompt {row['prompt_id']}: {exc}")
        if not text.endswith("<|assistant_start|>"):
            fail(f"rendered prompt {row['prompt_id']} does not end on assistant start")
        rendered.append(text)
        prompt_token_counts.append(len(tokenizer.encode(text, add_special_tokens=False)))
    print(
        json.dumps(
            {
                "template_origin": template_origin,
                "prompt_tokens_total": sum(prompt_token_counts),
                "prompt_tokens_min": min(prompt_token_counts),
                "prompt_tokens_max": max(prompt_token_counts),
            },
            indent=2,
        ),
        flush=True,
    )

    import torch
    from transformers import AutoModelForCausalLM

    if torch.cuda.is_available():
        device = "cuda"
        load_kwargs = {"dtype": torch.bfloat16, "device_map": "auto", "local_files_only": True}
    elif torch.backends.mps.is_available():
        device = "mps"
        load_kwargs = {"dtype": torch.float16, "local_files_only": True}
    else:
        device = "cpu"
        load_kwargs = {"dtype": torch.float32, "local_files_only": True}
    try:
        model = AutoModelForCausalLM.from_pretrained(args.model, **load_kwargs)
        if device != "cuda":
            model.to(device)
        model.eval()
    except Exception as exc:
        fail(f"cannot load model from the offline cache/model dir: {exc}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    temp_out = args.out.with_name(args.out.name + ".tmp")
    try:
        with temp_out.open("w", encoding="utf-8") as handle, Heartbeat() as heartbeat:
            with torch.inference_mode():
                for start in range(0, count, args.batch_size):
                    batch_rows = selected[start : start + args.batch_size]
                    batch_text = rendered[start : start + args.batch_size]
                    inputs = tokenizer(batch_text, return_tensors="pt", padding=True)
                    input_width = inputs["input_ids"].shape[1]
                    target_device = next(model.parameters()).device
                    inputs = {key: value.to(target_device) for key, value in inputs.items()}
                    sequences = model.generate(
                        **inputs,
                        do_sample=False,
                        max_new_tokens=512,
                        eos_token_id=ASSISTANT_END_ID,
                        pad_token_id=tokenizer.pad_token_id,
                        use_cache=True,
                    )
                    generated = sequences[:, input_width:].detach().cpu().tolist()
                    for offset, (row, token_ids) in enumerate(zip(batch_rows, generated)):
                        # generate() pads completed batch members; retain tokens only through first EOT.
                        if ASSISTANT_END_ID in token_ids:
                            end = token_ids.index(ASSISTANT_END_ID) + 1
                            token_ids = token_ids[:end]
                            stop_reason = "assistant_end"
                        elif len(token_ids) >= 512:
                            stop_reason = "max_length"
                        else:
                            stop_reason = "other"
                        response_ids = token_ids[:-1] if stop_reason == "assistant_end" else token_ids
                        record = {
                            "prompt_id": row["prompt_id"],
                            "row_id": row.get("row_id"),
                            "config": row.get("config"),
                            "category": row.get("category"),
                            "language": row["language"],
                            "messages": row["messages"],
                            "text": tokenizer.decode(response_ids, skip_special_tokens=True),
                            "raw_text": tokenizer.decode(token_ids, skip_special_tokens=False),
                            "stop_reason": stop_reason,
                            "prompt_tokens": prompt_token_counts[start + offset],
                            "generated_tokens": len(token_ids),
                        }
                        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                        handle.flush()
                        heartbeat.tokens += len(token_ids)
                    heartbeat.step += len(batch_rows)
                    heartbeat.line()
        temp_out.replace(args.out)
    except BaseException:
        if temp_out.exists():
            temp_out.unlink()
        raise
    print(f"wrote {count} generations to {args.out}")


if __name__ == "__main__":
    main()
