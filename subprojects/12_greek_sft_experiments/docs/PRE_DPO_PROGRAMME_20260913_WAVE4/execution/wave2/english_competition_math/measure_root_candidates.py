#!/usr/bin/env python3
"""Measure root-reviewed OpenMath candidates with the actual SFT reader/tokenizer."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import tokenizers
import torch
import transformers
import trl


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
TOKENIZER_REVISION = "c7f806e268083c64ce831bc46483bf98e5ddcee1"
TOKENIZER = Path("/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--fffoivos--apertus-8b-greek-cpt/snapshots") / TOKENIZER_REVISION
TEMPLATE = Path("/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f")

sys.path.insert(0, str(PROJECT / "cluster"))
from sft_train import prepare_tokenizer, tokenize_messages  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main() -> None:
    selected_path = HERE / "root_selected_sound.v1.jsonl"
    repairs_path = HERE / "root_repairs.v1.jsonl"
    rows = load(selected_path) + load(repairs_path)
    assert len(rows) == 33
    assert len({row["family_sha256"] for row in rows}) == 33
    tokenizer, control_ids = prepare_tokenizer({
        "tokenizer_name_or_path": str(TOKENIZER),
        "template_source": str(TEMPLATE),
        "require_apertus_control_ids": True,
        "extend_control_tokens": False,
    })
    items = []
    for row in rows:
        encoded = tokenize_messages(tokenizer, row["messages"])
        input_tokens = len(encoded["input_ids"])
        supervised_tokens = sum(encoded["assistant_masks"])
        assert supervised_tokens > 0
        decoded = tokenizer.decode(
            [token for token, mask in zip(encoded["input_ids"], encoded["assistant_masks"]) if mask],
            skip_special_tokens=False,
        )
        items.append({
            "row_id": row["id"],
            "family_sha256": row["family_sha256"],
            "status": row["status"],
            "input_tokens": input_tokens,
            "assistant_supervised_tokens": supervised_tokens,
            "within_4096": input_tokens <= 4096,
            "decoded_supervision_nonempty": bool(decoded.strip()),
        })
    inventory = {
        "schema": "openmath_root_candidate_token_inventory_v1",
        "status": "pass_exact_reader_tokenizer_and_target_mask" if all(
            item["within_4096"] and item["decoded_supervision_nonempty"] for item in items
        ) else "fail",
        "training_eligible": False,
        "eligibility_note": "Token/mask passage does not replace independent mathematical and Greek-language review.",
        "inputs": {selected_path.name: sha256(selected_path), repairs_path.name: sha256(repairs_path)},
        "rows": len(items),
        "families": len({item["family_sha256"] for item in items}),
        "totals": {
            "input_tokens": sum(item["input_tokens"] for item in items),
            "assistant_supervised_tokens": sum(item["assistant_supervised_tokens"] for item in items),
        },
        "ranges": {
            "input_tokens": {"min": min(item["input_tokens"] for item in items), "max": max(item["input_tokens"] for item in items)},
            "assistant_supervised_tokens": {"min": min(item["assistant_supervised_tokens"] for item in items), "max": max(item["assistant_supervised_tokens"] for item in items)},
        },
        "environment": {
            "python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "tokenizers": tokenizers.__version__, "trl": trl.__version__,
        },
        "tokenizer": {
            "resolved_revision": TOKENIZER_REVISION,
            "tokenizer_json_sha256": sha256(TOKENIZER / "tokenizer.json"),
            "tokenizer_config_sha256": sha256(TOKENIZER / "tokenizer_config.json"),
            "template_tokenizer_config_sha256": sha256(TEMPLATE / "tokenizer_config.json"),
            "canonical_sft_train_sha256": sha256(PROJECT / "cluster/sft_train.py"),
            "vocab_size": len(tokenizer), "control_token_ids": control_ids,
        },
        "items": items,
    }
    output = HERE / "root_candidate_token_inventory.v1.json"
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: inventory[key] for key in ("status", "rows", "families", "totals", "ranges", "training_eligible")}, indent=2))
    if inventory["status"] != "pass_exact_reader_tokenizer_and_target_mask":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
