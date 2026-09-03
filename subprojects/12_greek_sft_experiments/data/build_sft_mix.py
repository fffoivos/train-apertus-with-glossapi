#!/usr/bin/env python3
"""Build deterministic Greek SFT train/dev mixtures and contamination receipts.

The generated JSONL files retain conversations as a ``messages`` column. TRL's
SFTTrainer applies the Apertus Instruct template at training time; this script
uses the same template and the Greek-CPT tokenizer only to calculate receipts.
No dataset content is printed or included in the Markdown report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("DATASETS_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# Some datasets helpers consult module-level Hugging Face cache constants even
# when a per-call cache_dir is supplied. Keep that transient metadata writable
# and outside the repository; durable JSONL caches are still under data/cache.
_TRANSIENT_HF_ROOT = Path(tempfile.gettempdir()) / "greek-sft-wp0-hf-runtime"
os.environ.setdefault("HF_HOME", str(_TRANSIENT_HF_ROOT))
os.environ.setdefault("HF_HUB_CACHE", str(_TRANSIENT_HF_ROOT / "hub"))
os.environ.setdefault("HF_DATASETS_CACHE", str(_TRANSIENT_HF_ROOT / "datasets"))
os.environ.setdefault("HF_ASSETS_CACHE", str(_TRANSIENT_HF_ROOT / "assets"))
os.environ.setdefault("HF_XET_CACHE", str(_TRANSIENT_HF_ROOT / "xet"))

from datasets import DownloadConfig, disable_progress_bar, get_dataset_config_names, get_dataset_split_names, load_dataset
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import HfHubHTTPError
from transformers import AutoTokenizer
from transformers.utils import logging as transformers_logging

disable_progress_bar()
transformers_logging.set_verbosity_error()


SEED = 1234
DEV_FRACTION = 0.02
MAX_LENGTH = 4096
NGRAM_SIZE = 8
CONTAINMENT_THRESHOLD = 0.5
TEMPLATE_DATE = "2026-09-04"

DATASET_REPO = "fffoivos/Greek-SFT-translated-and-adapted"
BASE_TOKENIZER_REPO = "fffoivos/apertus-8b-greek-cpt"
BASE_TOKENIZER_REVISION = "18-avg-uniform5-tokens30B-50B"
TEMPLATE_TOKENIZER_REPO = "swiss-ai/Apertus-8B-Instruct-2509"

GREEK_CONFIGS = (
    "no_robots",
    "coconot",
    "personas_if",
    "smolcon",
    "oasst",
    "everyday",
    "systemchats",
)
IMPORTED_CONFIGS = ("apertus_en", "euroblocks_fr", "euroblocks_de")
CONFIGS = GREEK_CONFIGS + ("no_robots_en_pov",) + IMPORTED_CONFIGS
RAW_VARIANT_CONFIGS = frozenset(IMPORTED_CONFIGS)

ARMS: dict[str, tuple[tuple[str, str], ...]] = {
    "E1": tuple((config, "adapted") for config in GREEK_CONFIGS),
    "E2": tuple((config, "adapted") for config in GREEK_CONFIGS)
    + (("no_robots_en_pov", "adapted"),),
    "E3": tuple((config, "adapted") for config in GREEK_CONFIGS)
    + tuple((config, "adapted") for config in IMPORTED_CONFIGS),
    "E3prime": tuple((config, "adapted") for config in GREEK_CONFIGS)
    + tuple((config, "raw") for config in IMPORTED_CONFIGS),
}

EXPECTED_ARM_TOKENS = {"E1": 9_340_000, "E2": 12_600_000, "E3": 12_190_000}

# Text-only control tokens emitted by the template: BOS plus the twelve
# role/tool delimiters. The template also contains the literal sentinel
# <|image|> solely in a validation branch; neither tokenizer defines it, and
# text-only WP0 rows never emit it.
REQUIRED_CONTROL_TOKENS = (
    "<s>",
    "<|system_start|>",
    "<|system_end|>",
    "<|developer_start|>",
    "<|developer_end|>",
    "<|user_start|>",
    "<|user_end|>",
    "<|assistant_start|>",
    "<|assistant_end|>",
    "<|inner_prefix|>",
    "<|inner_suffix|>",
    "<|tools_prefix|>",
    "<|tools_suffix|>",
)

SCRIPT_PATH = Path(__file__).resolve()
DATA_DIR = SCRIPT_PATH.parent
REPO_ROOT = DATA_DIR.parent
CACHE_DIR = DATA_DIR / "cache"
SPLITS_DIR = DATA_DIR / "splits"
ARMS_DIR = DATA_DIR / "arms"
STATS_PATH = DATA_DIR / "stats.json"
REPORT_PATH = DATA_DIR / "contamination_report.md"
ELLINIKA_ROOT = Path.home() / "Projects/apertus-local-chat/benchmark/data"


class BuildError(RuntimeError):
    """Expected, user-readable build or verification failure."""


@dataclass(frozen=True)
class EvalPrompt:
    suite: str
    eval_id: str
    text: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def output_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def jsonl_line(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    temporary.replace(path)


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(jsonl_line(public_row(row)))
    temporary.replace(path)


def rows_digest(rows: Iterable[dict[str, Any]]) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        digest.update(jsonl_line(public_row(row)))
        count += 1
    return digest.hexdigest(), count


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": row["messages"],
        "row_id": row["row_id"],
        "config": row["config"],
        "category": row["category"],
    }


def read_hf_token() -> str | None:
    for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    token_path = Path.home() / ".cache/huggingface/token"
    if token_path.is_file():
        token = token_path.read_text(encoding="utf-8").strip()
        return token or None
    return None


def load_existing_stats() -> dict[str, Any] | None:
    if not STATS_PATH.is_file():
        return None
    with STATS_PATH.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise BuildError(f"invalid JSON object: {STATS_PATH.relative_to(REPO_ROOT)}")
    return value


def resolve_identities(check: bool, refresh: bool, token: str | None) -> dict[str, Any]:
    existing = load_existing_stats()
    if check:
        if existing is None:
            raise BuildError("data/stats.json is required for --check")
        return existing["identity"]
    if existing is not None and not refresh:
        return existing["identity"]

    api = HfApi(token=token)
    dataset_sha = api.dataset_info(DATASET_REPO, token=token).sha
    base_sha = api.model_info(
        BASE_TOKENIZER_REPO, revision=BASE_TOKENIZER_REVISION, token=token
    ).sha
    template_sha = api.model_info(TEMPLATE_TOKENIZER_REPO, token=token).sha
    if not dataset_sha or not base_sha or not template_sha:
        raise BuildError("Hugging Face did not return immutable source revisions")

    eval_sources: dict[str, dict[str, Any]] = {}
    for suite, repo, config, split in (
        ("greek_mmlu", "dascim/GreekMMLU", "All", "test"),
        ("gsm8k", "openai/gsm8k", "main", "test"),
        ("ifeval", "google/IFEval", "default", "train"),
    ):
        info = api.dataset_info(repo, token=token)
        eval_sources[suite] = {
            "status": "available",
            "repo": repo,
            "revision": info.sha,
            "config": config,
            "split": split,
        }

    native = {
        "status": "unavailable",
        "repo": "fffoivos/native-greek-suite",
        "reason": "not accessible via HfApi at build time",
    }
    try:
        info = api.dataset_info(native["repo"], token=token)
        native = {
            "status": "available",
            "repo": native["repo"],
            "revision": info.sha,
            "config": None,
            "split": None,
        }
    except (HfHubHTTPError, OSError):
        pass
    eval_sources["native_greek_suite"] = native

    return {
        "source_dataset": {
            "repo": DATASET_REPO,
            "revision": dataset_sha,
            "files": {},
        },
        "base_tokenizer": {
            "repo": BASE_TOKENIZER_REPO,
            "requested_revision": BASE_TOKENIZER_REVISION,
            "revision": base_sha,
        },
        "chat_template": {
            "repo": TEMPLATE_TOKENIZER_REPO,
            "revision": template_sha,
            "render_date": TEMPLATE_DATE,
        },
        "evaluation_sources": eval_sources,
    }


def source_cache_path(config: str, revision: str) -> Path:
    return CACHE_DIR / "sources" / f"{config}.{revision}.jsonl"


def ensure_source_files(identity: dict[str, Any], token: str | None) -> dict[str, Path]:
    revision = identity["source_dataset"]["revision"]
    paths: dict[str, Path] = {}
    recorded_files = identity["source_dataset"].setdefault("files", {})
    for config in CONFIGS:
        destination = source_cache_path(config, revision)
        if not destination.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="wp0-hf-source-") as staging:
                downloaded = hf_hub_download(
                    repo_id=DATASET_REPO,
                    repo_type="dataset",
                    revision=revision,
                    filename=f"data/natural_greek_sft_{config}.jsonl",
                    cache_dir=staging,
                    token=token,
                )
                shutil.copyfile(downloaded, destination)
        actual = {"bytes": destination.stat().st_size, "sha256": sha256_file(destination)}
        expected = recorded_files.get(config)
        if expected is not None and expected != actual:
            raise BuildError(f"source cache identity mismatch for config {config}")
        recorded_files[config] = actual
        paths[config] = destination
    return paths


def read_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise BuildError(f"invalid JSON in {path.name}:{line_number}: {error.msg}") from error
            if not isinstance(value, dict):
                raise BuildError(f"non-object JSON in {path.name}:{line_number}")
            yield line_number, value


def conversation_from_row(
    source: dict[str, Any], config: str, variant: str
) -> tuple[list[dict[str, str]] | None, str | None]:
    if variant == "raw":
        nested = source.get("en")
        conversation = nested.get("messages") if isinstance(nested, dict) else None
    elif config == "no_robots_en_pov":
        conversation = source.get("messages")
    else:
        conversation = source.get("el_messages")

    if not isinstance(conversation, list) or not conversation:
        return None, "missing_conversation"
    cleaned: list[dict[str, str]] = []
    assistant_count = 0
    for index, message in enumerate(conversation):
        if not isinstance(message, dict):
            return None, "invalid_message"
        role = message.get("role")
        content = message.get("content")
        if role not in {"system", "user", "assistant"}:
            return None, "invalid_role"
        if not isinstance(content, str):
            return None, "non_string_content"
        if role == "system" and index != 0:
            return None, "misplaced_system"
        if role == "assistant":
            assistant_count += 1
            if not content.strip():
                return None, "empty_assistant"
        cleaned.append({"role": role, "content": content})
    if assistant_count == 0:
        return None, "missing_assistant"
    return cleaned, None


def load_records(
    source_paths: dict[str, Path],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, dict[str, Any]],
]:
    adapted: dict[str, list[dict[str, Any]]] = {}
    raw: dict[str, list[dict[str, Any]]] = {}
    diagnostics: dict[str, dict[str, Any]] = {}
    for config in CONFIGS:
        adapted_rows: list[dict[str, Any]] = []
        raw_rows: list[dict[str, Any]] = []
        source_count = 0
        reasons: Counter[str] = Counter()
        raw_reasons: Counter[str] = Counter()
        seen: set[str] = set()
        for _, source in read_jsonl(source_paths[config]):
            source_count += 1
            if "row_id" not in source or source["row_id"] is None:
                raise BuildError(f"missing row_id in config {config}")
            row_id = str(source["row_id"])
            if "\n" in row_id or "\r" in row_id:
                raise BuildError(f"newline in row_id for config {config}")
            if row_id in seen:
                raise BuildError(f"duplicate row_id in config {config}: {row_id}")
            seen.add(row_id)
            category_value = source.get("category", "")
            category = "" if category_value is None else str(category_value)

            messages, reason = conversation_from_row(source, config, "adapted")
            if reason is None:
                adapted_rows.append(
                    {
                        "messages": messages,
                        "row_id": row_id,
                        "config": config,
                        "category": category,
                        "_variant": "adapted",
                    }
                )
            else:
                reasons[reason] += 1

            if config in RAW_VARIANT_CONFIGS:
                raw_messages, raw_reason = conversation_from_row(source, config, "raw")
                if raw_reason is None:
                    raw_rows.append(
                        {
                            "messages": raw_messages,
                            "row_id": row_id,
                            "config": config,
                            "category": category,
                            "_variant": "raw",
                        }
                    )
                else:
                    raw_reasons[raw_reason] += 1

        adapted[config] = adapted_rows
        if config in RAW_VARIANT_CONFIGS:
            raw[config] = raw_rows
        diagnostics[config] = {
            "source_rows": source_count,
            "adapted_eligible_rows": len(adapted_rows),
            "adapted_dropped": dict(sorted(reasons.items())),
        }
        if config in RAW_VARIANT_CONFIGS:
            diagnostics[config].update(
                {
                    "raw_eligible_rows": len(raw_rows),
                    "raw_dropped": dict(sorted(raw_reasons.items())),
                }
            )
    return adapted, raw, diagnostics


def split_ids(rows: Sequence[dict[str, Any]], config: str) -> set[str]:
    count = max(1, math.floor(len(rows) * DEV_FRACTION + 0.5))
    ranked = sorted(
        (row["row_id"] for row in rows),
        key=lambda row_id: (
            hashlib.sha256(f"{SEED}\0{config}\0{row_id}".encode("utf-8")).digest(),
            row_id,
        ),
    )
    return set(ranked[:count])


def derive_splits(adapted: dict[str, list[dict[str, Any]]]) -> dict[str, set[str]]:
    return {config: split_ids(adapted[config], config) for config in CONFIGS}


def split_text(row_ids: set[str]) -> str:
    return "".join(f"{row_id}\n" for row_id in sorted(row_ids))


def load_ellinika_prompts() -> tuple[list[EvalPrompt], dict[str, Any]]:
    if not ELLINIKA_ROOT.is_dir():
        raise BuildError(f"ellinika-bench prompt directory not found: {ELLINIKA_ROOT}")
    prompts: list[EvalPrompt] = []
    digest = hashlib.sha256()
    files = sorted(ELLINIKA_ROOT.rglob("*.jsonl"))
    for path in files:
        relative = path.relative_to(ELLINIKA_ROOT).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        for index, row in read_jsonl(path):
            prompt = row.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise BuildError(f"missing prompt in ellinika-bench {relative}:{index}")
            identifier = str(row.get("id", index))
            prompts.append(EvalPrompt("ellinika_bench", f"{relative}:{identifier}", prompt))
    return prompts, {
        "status": "available",
        "path": "~/Projects/apertus-local-chat/benchmark/data",
        "files": len(files),
        "prompts": len(prompts),
        "sha256": digest.hexdigest(),
    }


def eval_cache_path(suite: str, revision: str) -> Path:
    return CACHE_DIR / "evals" / f"{suite}.{revision}.jsonl"


def choose_prompt_field(row: dict[str, Any]) -> str | None:
    for field in ("prompt", "question", "instruction", "input"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def materialize_hf_eval_prompts(
    suite: str, spec: dict[str, Any], token: str | None
) -> list[EvalPrompt]:
    revision = spec["revision"]
    cache = eval_cache_path(suite, revision)
    if cache.is_file():
        return read_eval_cache(cache, suite)

    prompts: list[EvalPrompt] = []
    with tempfile.TemporaryDirectory(prefix=f"wp0-{suite}-") as staging:
        download_config = DownloadConfig(cache_dir=staging, token=token)
        configs: list[str | None]
        if suite == "native_greek_suite" and spec.get("config") is None:
            configs = get_dataset_config_names(
                spec["repo"],
                revision=revision,
                download_config=download_config,
                token=token,
            )
        else:
            configs = [spec.get("config")]
        for config in configs:
            if suite == "native_greek_suite" and spec.get("split") is None:
                splits = get_dataset_split_names(
                    spec["repo"],
                    config_name=config,
                    revision=revision,
                    download_config=download_config,
                    token=token,
                )
                split = "test" if "test" in splits else splits[0]
            else:
                split = spec["split"]
            dataset = load_dataset(
                spec["repo"],
                config,
                split=split,
                revision=revision,
                cache_dir=staging,
                token=token,
                download_config=download_config,
            )
            for index, row in enumerate(dataset):
                prompt = choose_prompt_field(row)
                if prompt is None:
                    raise BuildError(f"no supported prompt field in {suite} row {index}")
                identifier_value = row.get("id", row.get("key", index))
                config_label = config if config is not None else "default"
                prompts.append(
                    EvalPrompt(suite, f"{config_label}:{split}:{identifier_value}", prompt)
                )
    cache.parent.mkdir(parents=True, exist_ok=True)
    # A cache-specific serializer avoids exposing any prompt in tracked files.
    with tempfile.NamedTemporaryFile(dir=cache.parent, prefix=f".{cache.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        for item in prompts:
            handle.write(
                (
                    canonical_json({"eval_id": item.eval_id, "suite": item.suite, "text": item.text})
                    + "\n"
                ).encode("utf-8")
            )
    temporary.replace(cache)
    return prompts


def read_eval_cache(path: Path, suite: str) -> list[EvalPrompt]:
    prompts: list[EvalPrompt] = []
    for _, row in read_jsonl(path):
        prompts.append(EvalPrompt(suite, str(row["eval_id"]), str(row["text"])))
    return prompts


def load_eval_prompts(
    identity: dict[str, Any], token: str | None
) -> tuple[list[EvalPrompt], dict[str, Any]]:
    ellinika, ellinika_receipt = load_ellinika_prompts()
    all_prompts = list(ellinika)
    receipts: dict[str, Any] = {"ellinika_bench": ellinika_receipt}
    for suite, spec in identity["evaluation_sources"].items():
        if spec["status"] != "available":
            receipts[suite] = dict(spec)
            continue
        prompts = materialize_hf_eval_prompts(suite, spec, token)
        all_prompts.extend(prompts)
        receipts[suite] = {
            **spec,
            "prompts": len(prompts),
            "cache_sha256": sha256_file(eval_cache_path(suite, spec["revision"])),
        }
    return all_prompts, receipts


WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(WORD_RE.findall(normalized))


def ngrams(normalized: str) -> frozenset[tuple[str, ...]]:
    words = normalized.split()
    if not words:
        return frozenset()
    if len(words) < NGRAM_SIZE:
        return frozenset({tuple(words)})
    return frozenset(tuple(words[index : index + NGRAM_SIZE]) for index in range(len(words) - NGRAM_SIZE + 1))


def arms_for_variant(config: str, variant: str) -> list[str]:
    return [arm for arm, members in ARMS.items() if (config, variant) in members]


def scan_contamination(
    records: Sequence[dict[str, Any]], eval_prompts: Sequence[EvalPrompt]
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    eval_norms: list[str] = []
    eval_grams: list[frozenset[tuple[str, ...]]] = []
    exact_index: dict[str, list[int]] = defaultdict(list)
    postings: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, prompt in enumerate(eval_prompts):
        normalized = normalize_text(prompt.text)
        grams = ngrams(normalized)
        eval_norms.append(normalized)
        eval_grams.append(grams)
        if normalized:
            exact_index[normalized].append(index)
        for gram in grams:
            postings[gram].append(index)

    hits: list[dict[str, Any]] = []
    exact_rows: set[tuple[str, str]] = set()
    seen_hits: set[tuple[str, str, str, int, str, str]] = set()
    for row in records:
        for turn_index, message in enumerate(row["messages"]):
            if message["role"] != "user":
                continue
            normalized = normalize_text(message["content"])
            user_grams = ngrams(normalized)
            if not normalized or not user_grams:
                continue
            candidates: Counter[int] = Counter()
            for gram in user_grams:
                candidates.update(postings.get(gram, ()))
            candidates.update({index: 0 for index in exact_index.get(normalized, ())})
            for eval_index, shared in candidates.items():
                exact = normalized == eval_norms[eval_index]
                denominator = min(len(user_grams), len(eval_grams[eval_index]))
                containment = shared / denominator if denominator else 0.0
                if exact:
                    containment = 1.0
                if not exact and containment < CONTAINMENT_THRESHOLD:
                    continue
                prompt = eval_prompts[eval_index]
                key = (
                    row["config"],
                    row["row_id"],
                    row["_variant"],
                    turn_index,
                    prompt.suite,
                    prompt.eval_id,
                )
                if key in seen_hits:
                    continue
                seen_hits.add(key)
                hit = {
                    "type": "exact" if exact else "near",
                    "config": row["config"],
                    "row_id": row["row_id"],
                    "variant": row["_variant"],
                    "user_turn": turn_index,
                    "arms": arms_for_variant(row["config"], row["_variant"]),
                    "eval_suite": prompt.suite,
                    "eval_id": prompt.eval_id,
                    "containment": round(containment, 6),
                }
                hits.append(hit)
                if exact:
                    exact_rows.add((row["config"], row["row_id"]))
    hits.sort(
        key=lambda hit: (
            hit["type"] != "exact",
            hit["config"],
            hit["row_id"],
            hit["variant"],
            hit["user_turn"],
            hit["eval_suite"],
            hit["eval_id"],
        )
    )
    return hits, exact_rows


def load_tokenizers(identity: dict[str, Any], token: str | None):
    base_spec = identity["base_tokenizer"]
    template_spec = identity["chat_template"]
    base = AutoTokenizer.from_pretrained(
        base_spec["repo"], revision=base_spec["revision"], token=token
    )
    reference = AutoTokenizer.from_pretrained(
        template_spec["repo"], revision=template_spec["revision"], token=token
    )
    if not reference.chat_template:
        raise BuildError("reference tokenizer has no chat_template")
    base_added = base.get_added_vocab()
    reference_added = reference.get_added_vocab()
    token_checks: dict[str, dict[str, Any]] = {}
    for control in REQUIRED_CONTROL_TOKENS:
        base_id = base_added.get(control)
        reference_id = reference_added.get(control)
        ok = base_id is not None and base_id == reference_id
        token_checks[control] = {
            "base_id": base_id,
            "reference_id": reference_id,
            "in_base_added_vocab": base_id is not None,
            "same_id": ok,
        }
        if not ok:
            raise BuildError(f"control token mismatch: {control}")
    base.chat_template = reference.chat_template
    return base, reference, {
        "chat_template_sha256": sha256_bytes(reference.chat_template.encode("utf-8")),
        "required_text_control_tokens": token_checks,
        "text_control_token_count": len(REQUIRED_CONTROL_TOKENS),
        "non_emitted_template_sentinel": {
            "token": "<|image|>",
            "base_vocab_member": "<|image|>" in base.get_vocab(),
            "reference_vocab_member": "<|image|>" in reference.get_vocab(),
            "reason": "template validation sentinel; WP0 rows are text-only",
        },
        "base_vocab_size": base.vocab_size,
        "base_tokenizer_size_with_added_tokens": len(base),
        "base_eos_token": base.eos_token,
        "base_eos_token_id": base.eos_token_id,
        "base_bos_token": base.bos_token,
        "base_bos_token_id": base.bos_token_id,
    }


def chunks(values: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def tokenize_records(records: Sequence[dict[str, Any]], tokenizer: Any, reference_tokenizer: Any) -> None:
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in records:
        unique[(row["config"], row["row_id"], row["_variant"])] = row
    values = list(unique.values())
    for batch in chunks(values, 128):
        conversations = [row["messages"] for row in batch]
        encoded = tokenizer.apply_chat_template(
            conversations,
            tokenize=True,
            return_dict=False,
            add_generation_prompt=False,
            strftime_now=lambda _format: TEMPLATE_DATE,
        )
        reference_encoded = reference_tokenizer.apply_chat_template(
            conversations,
            tokenize=True,
            return_dict=False,
            add_generation_prompt=False,
            strftime_now=lambda _format: TEMPLATE_DATE,
        )
        if len(encoded) != len(batch):
            raise BuildError("tokenizer returned an unexpected batch size")
        if len(reference_encoded) != len(batch):
            raise BuildError("reference tokenizer returned an unexpected batch size")
        assistant_texts: list[str] = []
        assistant_counts: list[int] = []
        for row in batch:
            texts = [message["content"] for message in row["messages"] if message["role"] == "assistant"]
            assistant_counts.append(len(texts))
            assistant_texts.extend(texts)
        assistant_lengths: list[int] = []
        if assistant_texts:
            assistant_encoded = tokenizer(
                assistant_texts,
                add_special_tokens=False,
                padding=False,
                truncation=False,
            )["input_ids"]
            assistant_lengths = [len(ids) for ids in assistant_encoded]
        offset = 0
        for row, ids, reference_ids, count in zip(
            batch, encoded, reference_encoded, assistant_counts
        ):
            row["_tokens"] = len(ids)
            row["_planning_reference_tokens"] = len(reference_ids)
            row["_assistant_tokens"] = sum(assistant_lengths[offset : offset + count])
            offset += count


def summarize(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    tokens = sum(row["_tokens"] for row in rows)
    planning_reference_tokens = sum(row["_planning_reference_tokens"] for row in rows)
    assistant_tokens = sum(row["_assistant_tokens"] for row in rows)
    lengths = [row["_tokens"] for row in rows]
    return {
        "rows": len(rows),
        "tokens": tokens,
        "planning_reference_tokens": planning_reference_tokens,
        "assistant_content_tokens": assistant_tokens,
        "assistant_token_share": round(assistant_tokens / tokens, 8) if tokens else 0.0,
        "max_length": max(lengths, default=0),
        "rows_over_4096": sum(length > MAX_LENGTH for length in lengths),
    }


def select_rows(
    rows: Sequence[dict[str, Any]],
    dev_ids: set[str],
    want_dev: bool,
    exact_rows: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        in_dev = row["row_id"] in dev_ids
        if in_dev != want_dev:
            continue
        if not want_dev and (row["config"], row["row_id"]) in exact_rows:
            continue
        if row.get("_tokens", 0) > MAX_LENGTH:
            continue
        selected.append(row)
    return selected


def derive_outputs(
    adapted: dict[str, list[dict[str, Any]]],
    raw: dict[str, list[dict[str, Any]]],
    splits: dict[str, set[str]],
    exact_rows: set[tuple[str, str]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    arm_rows: dict[str, list[dict[str, Any]]] = {}
    for arm, members in ARMS.items():
        rows: list[dict[str, Any]] = []
        for config, variant in members:
            source = adapted[config] if variant == "adapted" else raw[config]
            rows.extend(select_rows(source, splits[config], False, exact_rows))
        random.Random(SEED).shuffle(rows)
        arm_rows[arm] = rows
    dev_all: list[dict[str, Any]] = []
    for config in CONFIGS:
        dev_all.extend(select_rows(adapted[config], splits[config], True, set()))
    return arm_rows, dev_all


def build_stats(
    identity: dict[str, Any],
    token_checks: dict[str, Any],
    diagnostics: dict[str, dict[str, Any]],
    adapted: dict[str, list[dict[str, Any]]],
    raw: dict[str, list[dict[str, Any]]],
    splits: dict[str, set[str]],
    exact_rows: set[tuple[str, str]],
    arm_rows: dict[str, list[dict[str, Any]]],
    dev_all: list[dict[str, Any]],
    eval_receipts: dict[str, Any],
    hits: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    config_stats: dict[str, Any] = {}
    for config in CONFIGS:
        adapted_train = select_rows(adapted[config], splits[config], False, exact_rows)
        adapted_dev = select_rows(adapted[config], splits[config], True, set())
        entry = {
            **diagnostics[config],
            "split_dev_ids": len(splits[config]),
            "adapted": {
                "train": summarize(adapted_train),
                "dev": summarize(adapted_dev),
                "all_output": summarize(adapted_train + adapted_dev),
            },
            "exact_contamination_rows_dropped_from_train": 0,
            "adapted_overlength_rows_excluded": sum(
                row["_tokens"] > MAX_LENGTH for row in adapted[config]
            ),
        }
        entry["exact_contamination_rows_dropped_from_train"] = sum(
            (config, row["row_id"]) in exact_rows and row["row_id"] not in splits[config]
            for row in adapted[config]
        )
        if config in RAW_VARIANT_CONFIGS:
            raw_train = select_rows(raw[config], splits[config], False, exact_rows)
            raw_dev = select_rows(raw[config], splits[config], True, set())
            entry["raw"] = {
                "train": summarize(raw_train),
                "dev": summarize(raw_dev),
                "all_output": summarize(raw_train + raw_dev),
            }
            entry["raw_overlength_rows_excluded"] = sum(
                row["_tokens"] > MAX_LENGTH for row in raw[config]
            )
        config_stats[config] = entry

    arm_stats: dict[str, Any] = {}
    for arm, rows in arm_rows.items():
        summary = summarize(rows)
        expected = EXPECTED_ARM_TOKENS.get(arm)
        if expected is not None:
            summary["expected_tokens"] = expected
            summary["planning_reference_relative_error"] = round(
                abs(summary["planning_reference_tokens"] - expected) / expected, 8
            )
            rounded_actual = round(summary["planning_reference_tokens"] / 1_000_000, 2)
            rounded_expected = round(expected / 1_000_000, 2)
            summary["planning_reference_tokens_millions_at_reported_precision"] = rounded_actual
            summary["planning_reference_relative_error_at_reported_precision"] = round(
                abs(rounded_actual - rounded_expected) / rounded_expected, 8
            )
            summary["planning_reference_within_2_percent"] = (
                summary["planning_reference_relative_error_at_reported_precision"] <= 0.02
            )
        arm_stats[arm] = {"train": summary, "dev": summarize(dev_all)}

    exact_hits = sum(hit["type"] == "exact" for hit in hits)
    near_hits = sum(hit["type"] == "near" for hit in hits)
    return {
        "schema_version": "greek_sft_wp0_stats_v1",
        "parameters": {
            "seed": SEED,
            "dev_fraction": DEV_FRACTION,
            "max_length": MAX_LENGTH,
            "ngram_size": NGRAM_SIZE,
            "containment_threshold": CONTAINMENT_THRESHOLD,
            "split_method": "lowest sha256(seed\\0config\\0row_id), exact rounded 2% count",
            "assistant_token_definition": "tokens in assistant content, excluding role control tokens",
            "tokens_definition": "rendered template tokenized with the Greek-CPT tokenizer",
            "planning_reference_tokens_definition": "same render tokenized with the unextended Apertus Instruct tokenizer; retained only to audit the supplied section 5a-prime estimates",
            "planning_estimate_comparison": "2 percent comparison is performed at the 0.01M precision of the approximate section 5a-prime figures; unrounded counts and errors are also retained",
        },
        "identity": identity,
        "template_validation": token_checks,
        "evaluation_sources": eval_receipts,
        "configs": config_stats,
        "arms": arm_stats,
        "dev_all": summarize(dev_all),
        "contamination": {
            "pre_drop_exact_hits": exact_hits,
            "pre_drop_near_hits": near_hits,
            "train_rows_dropped": len(exact_rows),
            "final_exact_hits": 0,
        },
    }


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def contamination_report(
    stats: dict[str, Any], hits: Sequence[dict[str, Any]]
) -> str:
    exact = [hit for hit in hits if hit["type"] == "exact"]
    near = [hit for hit in hits if hit["type"] == "near"]
    lines = [
        "# SFT contamination report",
        "",
        "This report contains identifiers and scores only; it does not reproduce training or evaluation text.",
        "",
        "## Method",
        "",
        f"User turns were normalized with Unicode NFKC, case-folding, punctuation removal, and whitespace collapse. Distinct word {NGRAM_SIZE}-grams were compared with containment `intersection / min(train_ngrams, eval_ngrams)`; texts shorter than {NGRAM_SIZE} words use their complete token tuple. Near duplicate threshold: `{CONTAINMENT_THRESHOLD}`. Exact means the complete normalized strings match.",
        "",
        "Only rows assigned to train were scanned. If any user turn had an exact match, the complete `(config, row_id)` was removed from every arm and every adapted/raw variant before files and token statistics were written. Dev rows were not contamination-filtered because the requested gate applies to train rows.",
        "",
        "## Evaluation prompt receipts",
        "",
        "| suite | status | prompts | revision or identity |",
        "| --- | --- | ---: | --- |",
    ]
    for suite, receipt in sorted(stats["evaluation_sources"].items()):
        revision = receipt.get("revision", receipt.get("sha256", receipt.get("reason", "")))
        lines.append(
            f"| {markdown_escape(suite)} | {markdown_escape(receipt['status'])} | {receipt.get('prompts', 0)} | `{markdown_escape(revision)}` |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Exact hits before removal: **{len(exact)}**",
            f"- Unique train rows removed: **{stats['contamination']['train_rows_dropped']}**",
            "- Exact hits in final train files: **0**",
            f"- Near-duplicate hits (not removed): **{len(near)}**",
            "",
            "## Exact hits removed",
            "",
        ]
    )
    lines.extend(hit_table(exact))
    lines.extend(["", "## Near-duplicate hits retained", ""])
    lines.extend(hit_table(near))
    lines.append("")
    return "\n".join(lines)


def hit_table(hits: Sequence[dict[str, Any]]) -> list[str]:
    if not hits:
        return ["None."]
    lines = [
        "| config | row_id | variant | user turn | arms | eval suite | eval id | containment |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: |",
    ]
    for hit in hits:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape(hit["config"]),
                    markdown_escape(hit["row_id"]),
                    markdown_escape(hit["variant"]),
                    str(hit["user_turn"]),
                    markdown_escape(",".join(hit["arms"])),
                    markdown_escape(hit["eval_suite"]),
                    markdown_escape(hit["eval_id"]),
                    f"{hit['containment']:.6f}",
                ]
            )
            + " |"
        )
    return lines


def validate_in_memory(
    stats: dict[str, Any],
    adapted: dict[str, list[dict[str, Any]]],
    splits: dict[str, set[str]],
    exact_rows: set[tuple[str, str]],
    arm_rows: dict[str, list[dict[str, Any]]],
    dev_all: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for config in CONFIGS:
        eligible_ids = {row["row_id"] for row in adapted[config]}
        if not splits[config] <= eligible_ids:
            errors.append(f"split contains unknown row_id for {config}")
        train_ids = eligible_ids - splits[config]
        if train_ids & splits[config]:
            errors.append(f"train/dev split intersects for {config}")
    for arm, rows in arm_rows.items():
        for row in rows:
            if row["row_id"] in splits[row["config"]]:
                errors.append(f"dev row present in {arm} train: {row['config']}/{row['row_id']}")
            if (row["config"], row["row_id"]) in exact_rows:
                errors.append(f"exact-contaminated row present in {arm}")
            public = public_row(row)
            if set(public) != {"messages", "row_id", "config", "category"}:
                errors.append(f"schema mismatch in {arm}")
            if any(message["role"] not in {"system", "user", "assistant"} for message in row["messages"]):
                errors.append(f"invalid role in {arm}")
    for row in dev_all:
        if row["row_id"] not in splits[row["config"]]:
            errors.append(f"non-dev row present in dev_all: {row['config']}/{row['row_id']}")
    for arm, arm_stats in stats["arms"].items():
        if arm_stats["train"]["rows_over_4096"]:
            errors.append(
                f"{arm} has {arm_stats['train']['rows_over_4096']} rows over {MAX_LENGTH} tokens "
                f"(max={arm_stats['train']['max_length']})"
            )
    if stats["dev_all"]["rows_over_4096"]:
        errors.append(f"dev_all has rows over {MAX_LENGTH} tokens")
    if stats["contamination"]["final_exact_hits"] != 0:
        errors.append("final exact contamination is nonzero")
    for arm in EXPECTED_ARM_TOKENS:
        if not stats["arms"][arm]["train"]["planning_reference_within_2_percent"]:
            errors.append(
                f"{arm} planning-reference token total "
                f"{stats['arms'][arm]['train']['planning_reference_tokens']} is outside the 2% "
                f"window around {EXPECTED_ARM_TOKENS[arm]} (Greek-CPT total is "
                f"{stats['arms'][arm]['train']['tokens']})"
            )
    return errors


def compare_artifacts(
    stats: dict[str, Any],
    report: str,
    splits: dict[str, set[str]],
    arm_rows: dict[str, list[dict[str, Any]]],
    dev_all: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if not STATS_PATH.is_file() or json.loads(STATS_PATH.read_text(encoding="utf-8")) != stats:
        errors.append("data/stats.json differs from re-derived statistics")
    if not REPORT_PATH.is_file() or REPORT_PATH.read_text(encoding="utf-8") != report:
        errors.append("data/contamination_report.md differs from re-derived report")
    for config, row_ids in splits.items():
        path = SPLITS_DIR / f"{config}.dev.txt"
        if not path.is_file() or path.read_text(encoding="utf-8") != split_text(row_ids):
            errors.append(f"split artifact differs: {config}")
    expected_outputs = {ARMS_DIR / "dev_all.jsonl": dev_all}
    for arm, rows in arm_rows.items():
        expected_outputs[ARMS_DIR / arm / "train.jsonl"] = rows
        expected_outputs[ARMS_DIR / arm / "dev.jsonl"] = dev_all
    for path, rows in expected_outputs.items():
        expected_digest, expected_count = rows_digest(rows)
        if not path.is_file():
            errors.append(f"missing output: {path.relative_to(REPO_ROOT)}")
            continue
        actual_digest = sha256_file(path)
        if actual_digest != expected_digest:
            errors.append(
                f"output differs: {path.relative_to(REPO_ROOT)} ({expected_count} expected rows)"
            )
    return errors


def write_artifacts(
    stats: dict[str, Any],
    report: str,
    splits: dict[str, set[str]],
    arm_rows: dict[str, list[dict[str, Any]]],
    dev_all: list[dict[str, Any]],
) -> None:
    for config, row_ids in splits.items():
        atomic_write_text(SPLITS_DIR / f"{config}.dev.txt", split_text(row_ids))
    write_jsonl(ARMS_DIR / "dev_all.jsonl", dev_all)
    for arm, rows in arm_rows.items():
        write_jsonl(ARMS_DIR / arm / "train.jsonl", rows)
        write_jsonl(ARMS_DIR / arm / "dev.jsonl", dev_all)
    atomic_write_text(STATS_PATH, output_json(stats))
    atomic_write_text(REPORT_PATH, report)


def run(check: bool, refresh_revisions: bool) -> None:
    token = read_hf_token()
    identity = resolve_identities(check, refresh_revisions, token)
    source_paths = ensure_source_files(identity, token)
    adapted, raw, diagnostics = load_records(source_paths)
    splits = derive_splits(adapted)

    eval_prompts, eval_receipts = load_eval_prompts(identity, token)
    tokenizer, reference_tokenizer, token_checks = load_tokenizers(identity, token)
    rows_to_tokenize: list[dict[str, Any]] = []
    for config in CONFIGS:
        rows_to_tokenize.extend(adapted[config])
        rows_to_tokenize.extend(raw.get(config, ()))
    tokenize_records(rows_to_tokenize, tokenizer, reference_tokenizer)

    contamination_candidates: list[dict[str, Any]] = []
    for config in CONFIGS:
        contamination_candidates.extend(
            row
            for row in adapted[config]
            if row["row_id"] not in splits[config] and row["_tokens"] <= MAX_LENGTH
        )
        if config in RAW_VARIANT_CONFIGS:
            contamination_candidates.extend(
                row
                for row in raw[config]
                if row["row_id"] not in splits[config] and row["_tokens"] <= MAX_LENGTH
            )
    hits, exact_rows = scan_contamination(contamination_candidates, eval_prompts)
    arm_rows, dev_all = derive_outputs(adapted, raw, splits, exact_rows)

    stats = build_stats(
        identity,
        token_checks,
        diagnostics,
        adapted,
        raw,
        splits,
        exact_rows,
        arm_rows,
        dev_all,
        eval_receipts,
        hits,
    )
    report = contamination_report(stats, hits)

    errors = validate_in_memory(stats, adapted, splits, exact_rows, arm_rows, dev_all)
    if check:
        errors.extend(compare_artifacts(stats, report, splits, arm_rows, dev_all))
    if errors:
        raise BuildError("; ".join(errors))
    if check:
        print("OK")
    else:
        write_artifacts(stats, report, splits, arm_rows, dev_all)
        totals = " ".join(
            f"{arm}={stats['arms'][arm]['train']['tokens']}" for arm in ARMS
        )
        print(f"BUILT {totals}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive and verify all committed and ignored artifacts without rewriting them",
    )
    parser.add_argument(
        "--refresh-revisions",
        action="store_true",
        help="resolve current Hub revisions instead of reusing the identities in data/stats.json",
    )
    args = parser.parse_args(argv)
    if args.check and args.refresh_revisions:
        parser.error("--check and --refresh-revisions cannot be combined")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run(args.check, args.refresh_revisions)
    except (BuildError, HfHubHTTPError, OSError, KeyError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
