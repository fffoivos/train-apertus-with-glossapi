#!/usr/bin/env python3
# RESOURCES: nodes=1 gpus=4 walltime=00:30 mem=200GB
"""Generate one batch-round of the unseen-interviews evaluation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Protocol


LANGUAGES = {"el", "en", "fr", "de"}
PLAIN_MOVES = {
    "challenge_true",
    "challenge_false",
    "clarify_shorter",
    "clarify_format",
    "localise",
    "stretch",
}
CONTROL_TOKEN_IDS = {
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
MAX_NEW_TOKENS = 512
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REPO_ROOT = Path(__file__).resolve().parents[2]

# This is the plain-text-message path of swiss-ai/Apertus-8B-Instruct-2509's
# template. The full upstream template additionally supports tools and images,
# neither of which occurs in this evaluation.
APERTUS_CHAT_TEMPLATE = r"""
{{- bos_token -}}
{%- set system_token = '<|system_start|>' -%}
{%- set end_system_token = '<|system_end|>' -%}
{%- set developer_token = '<|developer_start|>' -%}
{%- set end_developer_token = '<|developer_end|>' -%}
{%- set user_token = '<|user_start|>' -%}
{%- set end_user_token = '<|user_end|>' -%}
{%- set assistant_token = '<|assistant_start|>' -%}
{%- set end_assistant_token = '<|assistant_end|>' -%}
{%- if messages and messages[0].role == 'system' -%}
{{- system_token + messages[0].content + end_system_token -}}
{%- set loop_messages = messages[1:] -%}
{%- else -%}
{{- system_token + 'You are Apertus, a helpful assistant created by the SwissAI initiative.\nKnowledge cutoff: 2024-04\nCurrent date: ' + strftime_now('%Y-%m-%d') + end_system_token -}}
{%- set loop_messages = messages -%}
{%- endif -%}
{{- developer_token + 'Deliberation: disabled\nTool Capabilities: disabled' + end_developer_token -}}
{%- for message in loop_messages -%}
{%- if message.role == 'user' -%}
{{- user_token + message.content + end_user_token -}}
{%- elif message.role == 'assistant' -%}
{{- assistant_token + message.content + end_assistant_token -}}
{%- else -%}
{{- raise_exception('Invalid message role: ' + message.role) -}}
{%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}{{- assistant_token -}}{%- endif -%}
"""


class Generator(Protocol):
    def generate(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        """Return assistant text and serialisable generation metadata."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"missing input: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"expected object at {path}:{line_number}")
            rows.append(row)
    if not rows:
        raise ValueError(f"no rows in input: {path}")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(temporary, path)


def valid_move(move: Any) -> bool:
    if move in PLAIN_MOVES:
        return True
    return isinstance(move, str) and move.startswith("switch:") and move[7:] in LANGUAGES


def validate_seeds(rows: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows, 1):
        required = {"id", "lang", "opener", "moves"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"seed {index} missing fields: {','.join(sorted(missing))}")
        seed_id = row["id"]
        if not isinstance(seed_id, str) or not seed_id or seed_id in seen:
            raise ValueError(f"seed {index} has invalid or duplicate id")
        seen.add(seed_id)
        if row["lang"] not in LANGUAGES:
            raise ValueError(f"seed {seed_id} has unsupported lang")
        if not isinstance(row["opener"], str) or not row["opener"].strip():
            raise ValueError(f"seed {seed_id} has empty opener")
        if not isinstance(row["moves"], list) or len(row["moves"]) != 2:
            raise ValueError(f"seed {seed_id} must have exactly two moves")
        if not all(valid_move(move) for move in row["moves"]):
            raise ValueError(f"seed {seed_id} has invalid move")


def validate_transcript(row: dict[str, Any], expected_assistant_turns: int) -> None:
    turns = row.get("turns")
    if not isinstance(turns, list) or len(turns) != 2 * expected_assistant_turns:
        raise ValueError(f"invalid turn count for {row.get('id', '<unknown>')}")
    for index, turn in enumerate(turns):
        expected_role = "user" if index % 2 == 0 else "assistant"
        if not isinstance(turn, dict) or turn.get("role") != expected_role:
            raise ValueError(f"invalid role order for {row.get('id', '<unknown>')}")
        if not isinstance(turn.get("content"), str) or not turn["content"].strip():
            raise ValueError(f"empty turn for {row.get('id', '<unknown>')}")


def rows_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row.get("id")
        if not isinstance(row_id, str) or row_id in result:
            raise ValueError(f"invalid or duplicate id in {label}")
        result[row_id] = row
    return result


class Heartbeat:
    def __init__(self) -> None:
        self.step = 0
        self.tokens = 0
        self.started = time.monotonic()
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _memory(self) -> str:
        try:
            import torch

            if torch.cuda.is_available():
                return f"{torch.cuda.memory_allocated() / 2**30:.2f}GB"
        except Exception:
            pass
        return "na"

    def emit(self) -> None:
        elapsed = max(time.monotonic() - self.started, 1e-9)
        print(
            f"HB step={self.step} loss=na tok/s={self.tokens / elapsed:.2f} mem={self._memory()}",
            flush=True,
        )

    def _loop(self) -> None:
        while not self._done.wait(30):
            self.emit()

    def start(self) -> None:
        self.emit()
        self._thread.start()

    def update(self, generated_tokens: int) -> None:
        self.step += 1
        self.tokens += max(generated_tokens, 0)

    def stop(self) -> None:
        self._done.set()
        self._thread.join(timeout=2)
        self.emit()


class TransformersGenerator:
    def __init__(self, model_path: str, max_new_tokens: int = MAX_NEW_TOKENS) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(f"required local dependency unavailable: {exc.name}") from exc

        self.torch = torch
        self.max_new_tokens = max_new_tokens
        print(f"loading tokenizer: {model_path}", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.tokenizer.chat_template = APERTUS_CHAT_TEMPLATE
        self._validate_tokenizer()

        print(f"loading model: {model_path}", flush=True)
        device_map = "auto" if torch.cuda.device_count() > 1 else None
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype="auto",
            device_map=device_map,
            local_files_only=True,
        )
        if device_map is None:
            if torch.cuda.is_available():
                self.model.to("cuda")
            elif torch.backends.mps.is_available():
                self.model.to("mps")
        self.model.eval()

    def _validate_tokenizer(self) -> None:
        failures = []
        for token, expected_id in CONTROL_TOKEN_IDS.items():
            actual_id = self.tokenizer.convert_tokens_to_ids(token)
            if actual_id != expected_id:
                failures.append(f"{token}={actual_id}, expected {expected_id}")
        if self.tokenizer.bos_token != "<s>" or self.tokenizer.bos_token_id != 1:
            failures.append("bos token must be <s> id 1")
        if self.tokenizer.eos_token != "</s>" or self.tokenizer.eos_token_id != 2:
            failures.append("eos token must be </s> id 2")
        rendered = self.tokenizer.apply_chat_template(
            [
                {"role": "system", "content": "S"},
                {"role": "user", "content": "U"},
                {"role": "assistant", "content": "A"},
            ],
            tokenize=False,
            add_generation_prompt=False,
        )
        expected = (
            "<s><|system_start|>S<|system_end|><|developer_start|>"
            "Deliberation: disabled\nTool Capabilities: disabled<|developer_end|>"
            "<|user_start|>U<|user_end|><|assistant_start|>A<|assistant_end|>"
        )
        if rendered != expected:
            failures.append("plain-conversation template rendering differs from Apertus-Instruct")
        if failures:
            raise ValueError("tokenizer/template mismatch: " + "; ".join(failures))

    def generate(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        input_device = next(self.model.parameters()).device
        input_ids = input_ids.to(input_device)
        attention_mask = self.torch.ones_like(input_ids)
        stop_ids = [self.tokenizer.eos_token_id, CONTROL_TOKEN_IDS["<|assistant_end|>"]]
        with self.torch.inference_mode():
            output_ids = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
                eos_token_id=stop_ids,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        new_ids = output_ids[0, input_ids.shape[1] :].tolist()
        terminal_id = new_ids[-1] if new_ids else None
        content_ids = new_ids[:-1] if terminal_id in stop_ids else new_ids
        text = self.tokenizer.decode(content_ids, skip_special_tokens=True).strip()
        if not text:
            raise RuntimeError("model generated an empty assistant turn")
        if terminal_id == CONTROL_TOKEN_IDS["<|assistant_end|>"]:
            stop_reason = "assistant_end"
        elif terminal_id == self.tokenizer.eos_token_id:
            stop_reason = "eos"
        else:
            stop_reason = "max_new_tokens"
        metadata = {
            "input_tokens": int(input_ids.shape[1]),
            "generated_tokens": len(new_ids),
            "stop_reason": stop_reason,
            "raw_text": self.tokenizer.decode(new_ids, skip_special_tokens=False),
        }
        return text, metadata


class EchoGenerator:
    """Deterministic test double; never selected by the production CLI."""

    def generate(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        text = "echo: " + messages[-1]["content"]
        return text, {
            "input_tokens": len(messages),
            "generated_tokens": len(text.split()),
            "stop_reason": "assistant_end",
            "raw_text": text + "<|assistant_end|>",
        }


def prepare_round(
    seeds: list[dict[str, Any]], round_number: int, out_dir: Path
) -> list[tuple[dict[str, Any], list[dict[str, str]]]]:
    if round_number == 1:
        return [
            (
                {
                    "id": seed["id"],
                    "lang": seed["lang"],
                    "opener": seed["opener"],
                    "moves": list(seed["moves"]),
                    **({"draft_by": seed["draft_by"]} if "draft_by" in seed else {}),
                    "turns": [{"role": "user", "content": seed["opener"]}],
                },
                [{"role": "user", "content": seed["opener"]}],
            )
            for seed in seeds
        ]

    previous_path = out_dir / f"turn{round_number - 1}.jsonl"
    followups_path = out_dir / f"followups{round_number}.jsonl"
    previous = rows_by_id(read_jsonl(previous_path), str(previous_path))
    followups = rows_by_id(read_jsonl(followups_path), str(followups_path))
    seed_ids = {seed["id"] for seed in seeds}
    if not seed_ids.issubset(previous) or not seed_ids.issubset(followups):
        raise ValueError("every selected seed needs a previous turn and follow-up")

    prepared = []
    for seed in seeds:
        seed_id = seed["id"]
        prior = previous[seed_id]
        validate_transcript(prior, round_number - 1)
        if prior.get("lang") != seed["lang"] or prior.get("moves") != seed["moves"]:
            raise ValueError(f"seed metadata changed for {seed_id}")
        followup = followups[seed_id]
        expected_move = seed["moves"][round_number - 2]
        if followup.get("move") != expected_move:
            raise ValueError(f"wrong move in follow-up for {seed_id}")
        question = followup.get("followup")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"empty follow-up for {seed_id}")
        row = {key: value for key, value in prior.items() if key != "generation"}
        row["turns"] = [*prior["turns"], {"role": "user", "content": question.strip()}]
        prepared.append((row, list(row["turns"])))
    return prepared


def run_round(
    *,
    seeds_path: Path,
    round_number: int,
    out_dir: Path,
    generator: Generator,
    limit: int | None = None,
) -> Path:
    seeds = read_jsonl(seeds_path)
    validate_seeds(seeds)
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1")
        seeds = seeds[:limit]
    prepared = prepare_round(seeds, round_number, out_dir)

    heartbeat = Heartbeat()
    heartbeat.start()
    output_rows: list[dict[str, Any]] = []
    try:
        for row, messages in prepared:
            answer, metadata = generator.generate(messages)
            row["turns"] = [*messages, {"role": "assistant", "content": answer}]
            row["generation"] = metadata
            validate_transcript(row, round_number)
            output_rows.append(row)
            heartbeat.update(int(metadata.get("generated_tokens", 0)))
    finally:
        heartbeat.stop()

    output_path = out_dir / f"turn{round_number}.jsonl"
    write_jsonl(output_path, output_rows)
    print(f"wrote {len(output_rows)} rows: {output_path}", flush=True)
    return output_path


def resolve_out_dir(run_name: str, explicit: str | None) -> Path:
    if not RUN_RE.fullmatch(run_name):
        raise ValueError("--run must contain only letters, numbers, dot, underscore, or hyphen")
    return Path(explicit).resolve() if explicit else REPO_ROOT / "results" / run_name / "interviews"


def dry_run_plan(args: argparse.Namespace, seeds: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    selected = seeds[: args.limit] if args.limit is not None else seeds
    required_inputs = [str(Path(args.seeds).resolve())]
    if args.round > 1:
        required_inputs.extend(
            [
                str(out_dir / f"turn{args.round - 1}.jsonl"),
                str(out_dir / f"followups{args.round}.jsonl"),
            ]
        )
    return {
        "dry_run": True,
        "model": args.model,
        "seeds": str(Path(args.seeds).resolve()),
        "out_dir": str(out_dir),
        "output": str(out_dir / f"turn{args.round}.jsonl"),
        "round": args.round,
        "seed_count": len(selected),
        "input_characters": sum(len(seed["opener"]) for seed in selected),
        "planned_max_new_tokens_per_seed": args.max_steps or MAX_NEW_TOKENS,
        "planned_max_generated_tokens": len(selected) * (args.max_steps or MAX_NEW_TOKENS),
        "required_inputs": required_inputs,
        "generation": "greedy",
        "network": "disabled; local model files only",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="local checkpoint directory")
    parser.add_argument("--seeds", required=True, help="seed JSONL")
    parser.add_argument("--run", required=True, help="run label used only for output routing")
    parser.add_argument("--round", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--max-steps",
        type=int,
        help="probe cap for generated tokens per answer (default: 512)",
    )
    parser.add_argument("--out-dir", help="override results/<run>/interviews")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.limit is not None and args.limit < 1:
            raise ValueError("--limit must be at least 1")
        if args.max_steps is not None and not 1 <= args.max_steps <= MAX_NEW_TOKENS:
            raise ValueError(f"--max-steps must be between 1 and {MAX_NEW_TOKENS}")
        seeds_path = Path(args.seeds).resolve()
        seeds = read_jsonl(seeds_path)
        validate_seeds(seeds)
        out_dir = resolve_out_dir(args.run, args.out_dir)
        if args.dry_run:
            print(json.dumps(dry_run_plan(args, seeds, out_dir), indent=2, ensure_ascii=False))
            return 0

        # All round-specific files are validated before tokenizer/model loading.
        selected = seeds[: args.limit] if args.limit is not None else seeds
        prepare_round(selected, args.round, out_dir)
        model_path = Path(args.model).resolve()
        if not model_path.is_dir():
            raise ValueError(f"model directory does not exist: {model_path}")
        if not (model_path / "config.json").is_file():
            raise ValueError(f"model directory has no config.json: {model_path}")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        generator = TransformersGenerator(str(model_path), args.max_steps or MAX_NEW_TOKENS)
        run_round(
            seeds_path=seeds_path,
            round_number=args.round,
            out_dir=out_dir,
            generator=generator,
            limit=args.limit,
        )
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
