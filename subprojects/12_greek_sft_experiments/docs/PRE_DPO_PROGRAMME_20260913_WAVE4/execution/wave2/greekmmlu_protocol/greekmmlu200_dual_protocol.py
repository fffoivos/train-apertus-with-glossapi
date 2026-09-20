#!/usr/bin/env python3
"""Score the fixed GreekMMLU-200 IDs under the frozen custom and official-label protocols."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pyarrow.parquet as pq


PARQUET_SHA = "b77d269150c4c6e3441cfb20d52534f9aebd2c8c33883d0df7d61b3bc06129f5"
IDS_SHA = "58ab651789059df8f69c19b1fc5346f3a6bc8ed7a0c08d8951b090c1feb56978"
LABELS = ["Α", "Β", "Γ", "Δ"]
OFFICIAL_PROMPT = "Αυτό είναι μια ερώτηση {}. Επίλεξε τη σωστή απάντηση!\n\nΕρώτηση: {}\n{}\n\n Απάντηση:"
SUBJECTS_GR = {
    "Economics": "Οικονομικών", "Education": "Παιδαγωγικής", "Medicine": "Ιατρικής",
    "Electrical Engineering": "Ηλεκτρολόγων Μηχανικών", "Greek Mythology": "Ελληνικής Μυθολογίας",
    "Computer Networks & Security": "Δικτύων Υπολογιστών και Ασφάλειας", "Law": "Νομικής",
    "Physics": "Φυσικής", "Government and Politics": "Διακυβέρνησης και Πολιτικής", "Art": "Τέχνης",
    "Greek Literature": "Νεοελληνικής Λογοτεχνίας", "World History": "Παγκόσμιας Ιστορίας",
    "General Knowledge": "Γενικών Γνώσεων", "World Religions": "Παγκόσμιων Θρησκειών",
    "Mathematics": "Μαθηματικών", "Clinical Knowledge": "Κλινικών Γνώσεων",
    "Driving Rules": "Κανόνων Οδικής Κυκλοφορίας", "Biology": "Βιολογίας",
    "Civil Engineering": "Πολιτικών Μηχανικών", "Computer Science": "Επιστήμης Υπολογιστών",
    "Geography": "Γεωγραφίας", "Chemistry": "Χημείας", "Prehistory": "Προϊστορίας",
    "Agriculture": "Γεωργίας", "Modern Greek Language": "Νεοελληνικής Γλώσσας",
    "Accounting": "Λογιστικής", "Greek History": "Ελληνικής Ιστορίας",
    "Management": "Διοίκησης Επιχειρήσεων", "Greek Traditions": "Ελληνικών Παραδόσεων",
    "Maritime Safety and Rescue Operations": "Ναυαγοσωστικων Λειτουργιών και Ασφάλειας στη Θάλασσα",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def old_prompt(row: dict) -> str:
    lines = ["Απάντησε επιλέγοντας τη σωστή επιλογή.", "", "Ερώτηση:", row["question"].strip(), "", "Επιλογές:"]
    lines.extend(f"{LABELS[index]}. {choice}" for index, choice in enumerate(row["choices"]))
    lines.extend(["", "Σωστή απάντηση:"])
    return "\n".join(lines)


def official_prompt(row: dict) -> str:
    subject = SUBJECTS_GR.get(row["subject"], row["subject"])
    choices = "\n".join(f"{LABELS[index]}. {choice}" for index, choice in enumerate(row["choices"]))
    return OFFICIAL_PROMPT.format(subject, row["question"], choices)


class Scorer:
    def __init__(self, model_path: Path, max_input_tokens: int, candidate_batch_size: int):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, local_files_only=True, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, dtype=torch.float32, trust_remote_code=True, local_files_only=True, low_cpu_mem_usage=True,
        ).to("cuda").eval()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.max_input_tokens = max_input_tokens
        self.candidate_batch_size = candidate_batch_size
        self.device = next(self.model.parameters()).device

    def tokenize(self, prompt: str, continuation: str) -> dict:
        prompt_ids = self.tokenizer(prompt, add_special_tokens=False)["input_ids"]
        continuation_ids = self.tokenizer(continuation, add_special_tokens=False)["input_ids"]
        if not prompt_ids or not continuation_ids:
            raise ValueError("empty prompt or continuation tokenization")
        original_prompt_tokens = len(prompt_ids)
        keep = max(1, self.max_input_tokens - len(continuation_ids))
        prompt_ids = prompt_ids[-keep:]
        return {
            "input_ids": prompt_ids + continuation_ids,
            "choice_start": len(prompt_ids) - 1,
            "choice_len": len(continuation_ids),
            "prompt_tokens": len(prompt_ids),
            "original_prompt_tokens": original_prompt_tokens,
            "continuation_tokens": len(continuation_ids),
            "truncated": len(prompt_ids) != original_prompt_tokens,
        }

    def score_batch(self, candidates: list[dict]) -> list[dict]:
        torch = self.torch
        maximum = max(len(row["input_ids"]) for row in candidates)
        pad = self.tokenizer.pad_token_id
        ids = [row["input_ids"] + [pad] * (maximum - len(row["input_ids"])) for row in candidates]
        mask = [[1] * len(row["input_ids"]) + [0] * (maximum - len(row["input_ids"])) for row in candidates]
        ids_tensor = torch.tensor(ids, dtype=torch.long, device=self.device)
        mask_tensor = torch.tensor(mask, dtype=torch.long, device=self.device)
        with torch.inference_mode():
            logits = self.model(input_ids=ids_tensor, attention_mask=mask_tensor).logits
            log_probs = torch.nn.functional.log_softmax(logits[:, :-1, :], dim=-1)
        gathered = log_probs.gather(-1, ids_tensor[:, 1:].unsqueeze(-1)).squeeze(-1)
        output = []
        for batch_index, row in enumerate(candidates):
            values = gathered[batch_index, row["choice_start"]:row["choice_start"] + row["choice_len"]]
            total = float(values.sum().item()); count = int(values.numel())
            output.append({"sum_logprob": total, "avg_logprob": total / count, "num_tokens": count,
                           "prompt_tokens": row["prompt_tokens"], "original_prompt_tokens": row["original_prompt_tokens"],
                           "truncated": row["truncated"]})
        return output

    def score_protocol(self, rows: list[dict], protocol: str) -> list[dict]:
        candidates = []
        ranges = []
        for row in rows:
            prompt = old_prompt(row) if protocol == "custom_full_text" else official_prompt(row)
            continuations = ([" " + choice.strip() for choice in row["choices"]]
                             if protocol == "custom_full_text" else LABELS[:len(row["choices"])])
            start = len(candidates)
            candidates.extend(self.tokenize(prompt, continuation) for continuation in continuations)
            ranges.append((start, len(candidates), prompt, continuations))
        scores = []
        for start in range(0, len(candidates), self.candidate_batch_size):
            scores.extend(self.score_batch(candidates[start:start + self.candidate_batch_size]))
        output = []
        rank_key = "avg_logprob" if protocol == "custom_full_text" else "sum_logprob"
        for row, (start, end, prompt, continuations) in zip(rows, ranges):
            item_scores = scores[start:end]
            pred = max(range(len(item_scores)), key=lambda index: item_scores[index][rank_key])
            output.append({
                "protocol": protocol, "prompt_sha256": text_sha(prompt),
                "continuations": continuations, "continuation_token_counts": [score["num_tokens"] for score in item_scores],
                "choice_scores": item_scores, "ranking_statistic": rank_key,
                "pred_index": pred, "answer_index": int(row["answer"]), "correct": pred == int(row["answer"]),
                "input_truncated": any(score["truncated"] for score in item_scores),
            })
        return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--model", required=True, help="PUBLIC_LABEL=/absolute/model/path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-input-tokens", type=int, default=3072)
    parser.add_argument("--candidate-batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    label, raw_model_path = args.model.split("=", 1)
    model_path = Path(raw_model_path)
    if label not in {"original_krikri", "G3F2P1"} or not model_path.is_dir():
        raise ValueError("model must be original_krikri=PATH or G3F2P1=PATH")
    if sha(args.parquet) != PARQUET_SHA or sha(args.ids) != IDS_SHA:
        raise ValueError("dataset or fixed-ID hash mismatch")
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        if not (model_path / name).is_file():
            raise FileNotFoundError(model_path / name)
    if not list(model_path.glob("*.safetensors")):
        raise FileNotFoundError(f"no safetensors under {model_path}")

    table = pq.read_table(args.parquet)
    records = table.to_pylist()
    selected = [json.loads(line) for line in args.ids.read_text(encoding="utf-8").split("\n") if line.strip()]
    if len(records) != 16632 or len(selected) != 200 or len({row["example_id"] for row in selected}) != 200:
        raise ValueError("row-count/ID gate failed")
    rows = []
    for item in selected:
        index = int(item["dataset_row_index"]); row = records[index]
        if item["example_id"] != f"greekmmlu:{index}" or row["subject"] != item["subject"] or row["level"] != item["level"]:
            raise ValueError(f"fixed-ID metadata mismatch: {item}")
        if len(row["choices"]) not in {2, 3, 4} or int(row["answer"]) not in range(len(row["choices"])):
            raise ValueError(f"invalid choices: {item['example_id']}")
        rows.append(row)

    scorer = Scorer(model_path, args.max_input_tokens, args.candidate_batch_size)
    custom = scorer.score_protocol(rows, "custom_full_text")
    official = scorer.score_protocol(rows, "official_label")
    payload_rows = []
    for item, row, old, new in zip(selected, rows, custom, official):
        payload_rows.append({"example_id": item["example_id"], "dataset_row_index": item["dataset_row_index"],
                             "subject": row["subject"], "level": row["level"], "num_choices": len(row["choices"]),
                             "custom_full_text": old, "official_label": new})
    payload = {
        "schema_version": "greekmmlu200_dual_protocol_result_v1", "model_label": label,
        "model_path": str(model_path), "model_config_sha256": sha(model_path / "config.json"),
        "tokenizer_json_sha256": sha(model_path / "tokenizer.json"), "tokenizer_config_sha256": sha(model_path / "tokenizer_config.json"),
        "dataset_revision": "6a03aa06b68beb932fb75edff3a34e50b3674649", "parquet_sha256": PARQUET_SHA,
        "selection_sha256": IDS_SHA, "items": 200, "candidate_continuations_per_protocol": sum(len(row["choices"]) for row in rows),
        "dtype": "float32", "chat_template_applied": False, "max_input_tokens": args.max_input_tokens,
        "candidate_batch_size": args.candidate_batch_size,
        "accuracy": {"custom_full_text": sum(r["correct"] for r in custom) / 200,
                     "official_label": sum(r["correct"] for r in official) / 200},
        "protocol_disagreements": sum(a["pred_index"] != b["pred_index"] for a, b in zip(custom, official)),
        "rows": payload_rows,
    }
    temporary = args.output.with_suffix(args.output.suffix + ".partial")
    if temporary.exists():
        raise FileExistsError(temporary)
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"model": label, "items": 200, "accuracy": payload["accuracy"],
                      "protocol_disagreements": payload["protocol_disagreements"]}, sort_keys=True))


if __name__ == "__main__":
    main()
