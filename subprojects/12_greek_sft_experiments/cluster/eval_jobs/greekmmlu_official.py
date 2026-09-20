#!/usr/bin/env python3
"""Full-suite GreekMMLU under BOTH protocols for one model (R4 plan §5, astra's GreekMMLU protocol finding): the prompt constants, the
official-label prompt (Α/Β/Γ/Δ ranked by summed log-prob) and the Scorer class are copied verbatim (ast-extracted) from astra's accepted
greekmmlu200_dual_protocol.py (bundle 78817cefad7f8e54_r3); only the data loading (full pinned parquet, all rows) and the output differ.
Runs on one GPU (fp32, no chat template, as in the diagnostic). Usage:
  python greekmmlu_official.py --parquet <All/test-*.parquet> --model LABEL=/path --output out.json [--protocols official_label,custom_full_text] [--limit N]"""
from __future__ import annotations

import argparse

import hashlib

import json

import math

from pathlib import Path

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

INSTRUCTION_EL = "Απάντησε μόνο με το γράμμα (Α, Β, Γ ή Δ) της σωστής επιλογής."
def chat_prompt(tokenizer, row, instructed):
    """Instruct-adapted protocol (owner, 14 Sept): the official text as the USER turn of the model's own chat template (+ one instruction line when
    instructed=True); the letters are ranked at the start of the assistant turn. Same items, same ranking rule; only the framing changes."""
    body = official_prompt(row).rsplit("\n\n Απάντηση:", 1)[0] + ("\n\n" + INSTRUCTION_EL if instructed else "")   # no trailing completion cue inside a chat turn; the instruction is the last line
    return tokenizer.apply_chat_template([{"role": "user", "content": body}], tokenize=False, add_generation_prompt=True)


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
            if protocol == "custom_full_text": prompt = old_prompt(row)
            elif protocol == "official_label": prompt = official_prompt(row)
            elif protocol in ("chat_official", "chat_instructed"): prompt = chat_prompt(self.tokenizer, row, protocol == "chat_instructed")
            else: raise ValueError(protocol)
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

def load_rows(path, limit=None):
    """JSONL projection of the pinned parquet (converted on the Mac with pandas; the cluster venv has no pandas): one row per dataset row in order."""
    rows = []
    for line in open(path, encoding='utf-8'):
        if not line.strip(): continue
        r = json.loads(line); i = int(r['dataset_row_index'])
        rows.append(dict(dataset_row_index=i, example_id=f"greekmmlu:{i}", question=str(r['question']), choices=[str(c) for c in r['choices']], answer=int(r['answer']), subject=str(r['subject']), level=str(r.get('level', ''))))
        if limit and len(rows) >= limit: break
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True); parser.add_argument("--model", required=True, help="LABEL=/absolute/model/path")
    parser.add_argument("--output", type=Path, required=True); parser.add_argument("--protocols", default="official_label,custom_full_text", help="comma list of official_label, custom_full_text, chat_official, chat_instructed")
    parser.add_argument("--save-choice-scores", action="store_true", help="persist per-choice sum/avg logprobs; needed to calibrate the label prior. Off by default: it changes the output shape validate_official_result.py pins.")
    parser.add_argument("--max-input-tokens", type=int, default=3072); parser.add_argument("--candidate-batch-size", type=int, default=16); parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    label, raw = args.model.split("=", 1); model_path = Path(raw)
    if not model_path.is_dir() or not list(model_path.glob("*.safetensors")): raise FileNotFoundError(model_path)
    rows = [r for r in load_rows(args.parquet, args.limit) if len(r["choices"]) in {2, 3, 4} and r["answer"] in range(len(r["choices"]))]
    scorer = Scorer(model_path, args.max_input_tokens, args.candidate_batch_size); results = {}
    for protocol in args.protocols.split(","):
        out = scorer.score_protocol(rows, protocol); results[protocol] = out
        print(json.dumps(dict(model=label, protocol=protocol, items=len(rows), accuracy=sum(r["correct"] for r in out) / len(rows))), flush=True)
        part = args.output.with_suffix(f".{protocol}.partial.json"); part.write_text(json.dumps(dict(model_label=label, protocol=protocol, items=len(rows), accuracy=sum(r["correct"] for r in out) / len(rows), rows=[dict(example_id=r["example_id"], subject=r["subject"], level=r["level"], answer_index=r["answer"], pred_index=o["pred_index"], correct=o["correct"]) for r, o in zip(rows, out)]), ensure_ascii=False) + "\n", encoding="utf-8")   # per-protocol save (a walltime cut keeps finished protocols)
    by_subject = {}
    for protocol, out in results.items():
        acc = {}
        for r, o in zip(rows, out): a = acc.setdefault(r["subject"], [0, 0]); a[0] += o["correct"]; a[1] += 1
        by_subject[protocol] = {k: round(v[0] / v[1], 4) for k, v in sorted(acc.items())}
    payload = dict(schema_version="greekmmlu_full_dual_protocol_v1", model_label=label, model_path=str(model_path), parquet=str(args.parquet), parquet_sha256=sha(args.parquet),
                   model_config_sha256=sha(model_path / "config.json"), items=len(rows), dtype="float32", chat_template_applied=any(p.startswith("chat_") for p in args.protocols.split(",")), max_input_tokens=args.max_input_tokens,
                   accuracy={p: sum(r["correct"] for r in out) / len(rows) for p, out in results.items()}, by_subject=by_subject,
                   protocol_disagreements=(sum(a["pred_index"] != b["pred_index"] for a, b in zip(*results.values())) if len(results) == 2 else None),
                   rows=[dict(example_id=r["example_id"], subject=r["subject"], level=r["level"], answer_index=r["answer"], **{p: dict(pred_index=o["pred_index"], correct=o["correct"], **({"choice_scores": o["choice_scores"]} if args.save_choice_scores else {})) for p, o in zip(results, [results[p][i] for p in results])}) for i, r in enumerate(rows)])
    tmp = args.output.with_suffix(args.output.suffix + ".partial"); tmp.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8"); tmp.replace(args.output)
    print(json.dumps(dict(model=label, items=len(rows), accuracy=payload["accuracy"], protocol_disagreements=payload["protocol_disagreements"]), sort_keys=True))


if __name__ == "__main__":
    main()
