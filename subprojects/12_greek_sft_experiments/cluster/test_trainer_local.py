#!/usr/bin/env python3
"""End-to-end local acceptance test for cluster/sft_train.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
import yaml
from datasets import Dataset, disable_progress_bars
from transformers import AutoModelForCausalLM
from trl.data_utils import pack_dataset
from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

import sft_train


ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "cluster" / "sft_train.py"
MAC_CONFIG = ROOT / "cluster" / "configs" / "mac_dryrun.yaml"
disable_progress_bars()


def _candidate_rows() -> tuple[list[dict], str]:
    arm_file = ROOT / "data" / "arms" / "E1" / "train.jsonl"
    if arm_file.is_file():
        rows = []
        with arm_file.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
                if len(rows) >= 2000:
                    break
        return rows, str(arm_file)

    # WP0 may be executing in parallel. The already-cached upstream no_robots
    # Arrow file supplies genuine conversation rows without embedding or
    # quoting any dataset example in this test source.
    cache_root = Path.home() / ".cache" / "huggingface" / "datasets"
    candidates = sorted(cache_root.glob("HuggingFaceH4___no_robots/**/no_robots-train.arrow"))
    if not candidates:
        raise AssertionError(
            "three real rows unavailable: run WP0 or pre-populate the HuggingFaceH4/no_robots cache"
        )
    dataset = Dataset.from_file(str(candidates[0]))
    rows = [
        {
            "messages": row["messages"],
            "row_id": row.get("prompt_id", f"cache-{index}"),
            "config": "no_robots",
        }
        for index, row in enumerate(dataset.select(range(min(500, len(dataset)))))
    ]
    return rows, str(candidates[0])


def _select_three_real_rows(tokenizer, standin_tokenizer) -> tuple[list[dict], str]:
    candidates, source = _candidate_rows()
    selected = []
    tokenizer.model_max_length = 10**9
    standin_tokenizer.model_max_length = 10**9
    for row in candidates:
        messages = row.get("messages")
        if not isinstance(messages, list):
            continue
        try:
            tokenized = sft_train.tokenize_messages(tokenizer, messages)
            standin = sft_train.tokenize_messages(standin_tokenizer, messages)
        except Exception:
            continue
        # Keep the real run small while leaving enough room for the complete
        # assistant answer and its stop token.
        if (
            72 <= len(tokenized["input_ids"]) <= 256
            and 72 <= len(standin["input_ids"]) <= 256
        ):
            selected.append(row)
        if len(selected) == 3:
            return selected, source
    raise AssertionError(f"could not find three valid <=256-token real rows in {source}")


def _assert_masks(tokenizer, rows: list[dict]) -> None:
    control_ids = {
        tokenizer.convert_tokens_to_ids(token) for token in sft_train.APERTUS_CONTROL_IDS
    }
    assistant_end_id = tokenizer.convert_tokens_to_ids(sft_train.ASSISTANT_END)
    for index, row in enumerate(rows, 1):
        tokenized = sft_train.tokenize_messages(tokenizer, row["messages"])
        ids = tokenized["input_ids"]
        masks = tokenized["assistant_masks"]
        labels = tokenized["labels"]
        for token_id, mask, label in zip(ids, masks, labels, strict=True):
            assert (label == token_id) == bool(mask)
            if token_id in control_ids and token_id != assistant_end_id:
                assert mask == 0, f"row {index}: structural control token was unmasked"
            if token_id == assistant_end_id:
                assert mask == 1, f"row {index}: stop target was masked"
        expected = "".join(
            message["content"] + sft_train.ASSISTANT_END
            for message in row["messages"]
            if message["role"] == "assistant"
        )
        decoded = tokenizer.decode(
            [token_id for token_id, mask in zip(ids, masks, strict=True) if mask],
            clean_up_tokenization_spaces=False,
        )
        assert decoded == expected, f"row {index}: assistant span mismatch"
        print(f"UNMASKED row={index} decoded={decoded!r}")


def _assert_packing_boundaries(tokenizer, rows: list[dict]) -> None:
    examples = [sft_train.tokenize_messages(tokenizer, row["messages"]) for row in rows]
    capacity = sum(len(example["input_ids"]) for example in examples)
    dataset = Dataset.from_list(
        [{"input_ids": example["input_ids"], "labels": example["labels"]} for example in examples]
    )
    packed = pack_dataset(dataset, seq_length=capacity, strategy="bfd")
    assert len(packed) == 1
    packed_row = packed[0]
    assert sorted(packed_row["seq_lengths"]) == sorted(
        len(example["input_ids"]) for example in examples
    )
    collator = DataCollatorForLanguageModeling(
        pad_token_id=tokenizer.pad_token_id,
        padding_free=True,
    )
    batch = collator([packed_row])
    assert "attention_mask" not in batch
    positions = batch["position_ids"][0].tolist()
    starts = []
    cursor = 0
    for length in packed_row["seq_lengths"]:
        starts.append(cursor)
        assert positions[cursor : cursor + length] == list(range(length))
        assert batch["labels"][0, cursor].item() == -100
        cursor += length
    assert starts == [0, *[sum(packed_row["seq_lengths"][:i]) for i in range(1, len(examples))]]
    print(
        "PACK_BOUNDARIES_OK seq_lengths="
        f"{packed_row['seq_lengths']} position_resets={starts} attention_mask=absent"
    )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _run(command: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"
    environment["HF_DATASETS_DISABLE_PROGRESS_BARS"] = "1"
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    print(result.stdout, end="")
    assert result.returncode == 0, f"command failed with {result.returncode}: {' '.join(command)}"
    return result


def main() -> None:
    base_config = sft_train.load_config(MAC_CONFIG)
    standin_tokenizer, _ = sft_train.prepare_tokenizer(base_config)
    production_config = sft_train.load_config(
        ROOT / "cluster" / "configs" / "E1_lr1e-5_3ep_const.yaml"
    )
    tokenizer, production_ids = sft_train.prepare_tokenizer(production_config)
    assert production_ids == sft_train.APERTUS_CONTROL_IDS
    rows, source = _select_three_real_rows(tokenizer, standin_tokenizer)
    print(f"REAL_ROWS source={source} count={len(rows)}")
    _assert_masks(tokenizer, rows)
    _assert_packing_boundaries(tokenizer, rows)

    with tempfile.TemporaryDirectory(prefix="wp2-local-") as temp_name:
        temp = Path(temp_name)
        train_file = temp / "train.jsonl"
        eval_file = temp / "dev_all.jsonl"
        # Eighteen real conversations guarantee at least five BFD batches even
        # if some pair perfectly at max_length=256.
        train_rows = []
        for repeat in range(6):
            for row in rows:
                clone = dict(row)
                clone["row_id"] = f"{row.get('row_id', 'row')}:{repeat}"
                clone["config"] = "no_robots"
                train_rows.append(clone)
        _write_jsonl(train_file, train_rows)
        _write_jsonl(eval_file, rows)

        config = {key: value for key, value in base_config.items() if not key.startswith("_")}
        config["train_file"] = str(train_file)
        config["eval_file"] = str(eval_file)
        config_path = temp / "mac.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        dry = _run([sys.executable, str(TRAINER), "--dry-run", "--config", str(config_path)])
        assert "DRY_RUN_OK model_not_loaded=true" in dry.stdout
        assert "MODEL_LOAD_BEGIN" not in dry.stdout
        assert '"train_tokens"' in dry.stdout and '"planned_optimizer_steps"' in dry.stdout
        print("DRY_RUN_NO_MODEL_OK")

        out_dir = temp / "output"
        trained = _run(
            [
                sys.executable,
                str(TRAINER),
                "--config",
                str(config_path),
                "--out-dir",
                str(out_dir),
                "--max-steps",
                "5",
            ]
        )
        assert "HB step=" in trained.stdout
        assert "TRAIN_OK" in trained.stdout
        assert "RELOAD_CHECK max_abs_diff=0" in trained.stdout
        checkpoints = sorted(out_dir.glob("epoch*"))
        assert checkpoints, "no epoch checkpoint"
        checkpoint = checkpoints[-1]
        reloaded = AutoModelForCausalLM.from_pretrained(
            checkpoint, local_files_only=True, trust_remote_code=False, dtype=torch.float32
        )
        assert reloaded.config.eos_token_id == standin_tokenizer.eos_token_id
        receipt = json.loads((out_dir / "reload_check.json").read_text(encoding="utf-8"))
        assert receipt["max_abs_diff"] == 0.0
        print(f"CHECKPOINT_RELOAD_OK path={checkpoint} max_abs_diff=0")
        print("HEARTBEAT_OK")

    print("OK")


if __name__ == "__main__":
    main()
