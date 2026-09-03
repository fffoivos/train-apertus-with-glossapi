#!/usr/bin/env python3
# RESOURCES: nodes=1 gpus=4 walltime=01:00 mem=64GB
"""Score short-answer questions against a causal language model."""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


EXEMPLARS: dict[str, tuple[tuple[str, str], ...]] = {
    "el": (
        ("Ποια είναι η πρωτεύουσα της Ιταλίας;", "Ρώμη"),
        ("Ποιος έγραψε την Οδύσσεια;", "Όμηρος"),
        ("Πόσες πλευρές έχει ένα εξάγωνο;", "Έξι"),
        ("Ποιος πλανήτης είναι γνωστός ως ο κόκκινος πλανήτης;", "Άρης"),
    ),
    "en": (
        ("What is the capital of Italy?", "Rome"),
        ("Who wrote Pride and Prejudice?", "Jane Austen"),
        ("How many sides does a hexagon have?", "Six"),
        ("Which planet is known as the Red Planet?", "Mars"),
    ),
    "fr": (
        ("Quelle est la capitale de l'Italie ?", "Rome"),
        ("Qui a écrit Madame Bovary ?", "Gustave Flaubert"),
        ("Combien de côtés possède un hexagone ?", "Six"),
        ("Quelle planète est appelée la planète rouge ?", "Mars"),
    ),
    "de": (
        ("Was ist die Hauptstadt Italiens?", "Rom"),
        ("Wer schrieb Die Verwandlung?", "Franz Kafka"),
        ("Wie viele Seiten hat ein Sechseck?", "Sechs"),
        ("Welcher Planet wird der rote Planet genannt?", "Mars"),
    ),
}


def contains_greek(text: str) -> bool:
    return any("\u0370" <= char <= "\u03ff" or "\u1f00" <= char <= "\u1fff" for char in text)


def normalize_answer(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text).casefold()
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    tokens = re.findall(r"[^\W_]+", without_marks, flags=re.UNICODE)
    return " ".join(tokens)


def normalized_contains(answer: str, gold: str) -> bool:
    normalized_answer = normalize_answer(answer)
    normalized_gold = normalize_answer(gold)
    if not normalized_gold:
        return False
    return f" {normalized_gold} " in f" {normalized_answer} "


def build_prompt(language: str, question: str) -> str:
    if language not in EXEMPLARS:
        raise ValueError(f"unsupported language: {language}")
    labels = {
        "el": ("Ερώτηση", "Σύντομη απάντηση"),
        "en": ("Question", "Short answer"),
        "fr": ("Question", "Réponse courte"),
        "de": ("Frage", "Kurze Antwort"),
    }[language]
    parts: list[str] = []
    for exemplar_question, exemplar_answer in EXEMPLARS[language]:
        parts.append(f"{labels[0]}: {exemplar_question}\n{labels[1]}: {exemplar_answer}")
    parts.append(f"{labels[0]}: {question}\n{labels[1]}:")
    prompt = "\n\n".join(parts)
    if language != "el" and contains_greek(prompt):
        raise ValueError(f"Greek script found in {language} model prompt")
    return prompt


def clean_completion(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def validate_apertus_tokenizer(tokenizer: Any) -> None:
    if tokenizer.eos_token_id != 2 or tokenizer.eos_token != "</s>":
        raise ValueError("tokenizer is not the expected Apertus tokenizer: eos must be </s> id 2")
    if tokenizer.bos_token != "<s>":
        raise ValueError("tokenizer is not the expected Apertus tokenizer: bos must be <s>")
    if len(tokenizer) != 148_992:
        raise ValueError(f"tokenizer is not the expected Apertus vocabulary: got {len(tokenizer)}")


def classify_answers(gold: str, greedy: str, samples: Sequence[str]) -> str:
    if normalized_contains(greedy, gold):
        return "known"
    if any(normalized_contains(sample, gold) for sample in samples):
        return "weakly_known"
    return "unknown"


Generator = Callable[[list[str]], list[tuple[str, list[str]]]]


def score_records(
    records: list[dict[str, Any]], generator: Generator, batch_size: int = 4
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        prompts = [build_prompt(row["language"], row["question"]) for row in batch]
        generations = generator(prompts)
        if len(generations) != len(batch):
            raise ValueError("generator returned the wrong number of results")
        for row, (greedy, samples) in zip(batch, generations):
            if len(samples) != 4:
                raise ValueError("generator must return exactly four sampled answers")
            greedy = clean_completion(greedy)
            samples = [clean_completion(sample) for sample in samples]
            scored.append(
                {
                    **row,
                    "greedy_answer": greedy,
                    "sample_answers": samples,
                    "knowledge_label": classify_answers(row["gold"], greedy, samples),
                }
            )
    return scored


def load_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if limit == 0:
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"bad JSON at {path}:{line_number}: {exc}") from exc
            if limit is not None and len(rows) >= limit:
                break
    return rows


def validate_questions(records: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    required = {
        "claim_id", "row_key", "row_index", "row_occurrence", "source", "row_id",
        "claim_index", "claim", "kind", "basis", "language", "question", "gold", "entities",
    }
    for index, row in enumerate(records):
        if not required.issubset(row):
            missing = sorted(required - set(row))
            raise ValueError(f"question record {index} is missing {missing}")
        if row["claim_id"] in seen:
            raise ValueError(f"duplicate claim_id: {row['claim_id']}")
        seen.add(row["claim_id"])
        if row["language"] not in EXEMPLARS:
            raise ValueError(f"unsupported language in {row['claim_id']}: {row['language']}")
        if not isinstance(row["question"], str) or not isinstance(row["gold"], str):
            raise ValueError(f"invalid question or gold in {row['claim_id']}")
        if row["basis"] not in {"known", "inferred", "uncertain"}:
            raise ValueError(f"invalid basis in {row['claim_id']}")


def load_presence(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    presence: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or claim_id in presence:
            raise ValueError("presence file has an invalid or duplicate claim_id")
        presence[claim_id] = row
    return presence


def attach_presence(
    records: list[dict[str, Any]], presence: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if presence:
        missing = [row["claim_id"] for row in records if row["claim_id"] not in presence]
        if missing:
            raise ValueError(f"presence file is missing {len(missing)} selected claim_ids")
    attached: list[dict[str, Any]] = []
    for row in records:
        signal = presence.get(row["claim_id"])
        attached.append(
            {
                **row,
                "corpus_presence": None if signal is None else {
                    "doc_count": signal.get("doc_count"),
                    "sampled_fraction": signal.get("sampled_fraction"),
                    "observed_doc_count": signal.get("observed_doc_count"),
                },
            }
        )
    return attached


def aggregate_rows(
    claims: list[dict[str, Any]], row_universe: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[str, dict[str, Any]] = {}
    for claim in claims:
        grouped[claim["row_key"]].append(claim)
        metadata[claim["row_key"]] = {
            "row_key": claim["row_key"],
            "row_index": claim["row_index"],
            "row_occurrence": claim["row_occurrence"],
            "source": claim["source"],
            "row_id": claim["row_id"],
        }
    if row_universe:
        occurrences: Counter[tuple[str, str]] = Counter()
        next_index = max((int(row["row_index"]) for row in metadata.values()), default=-1) + 1
        for offset, row in enumerate(row_universe):
            source = row.get("source") or row.get("config")
            row_id = row.get("row_id")
            if not isinstance(source, str) or not isinstance(row_id, str):
                raise ValueError("row-universe records need string source/config and row_id")
            pair = (source, row_id)
            occurrence = occurrences[pair]
            occurrences[pair] += 1
            row_key = f"{source}:{row_id}:{occurrence}"
            metadata.setdefault(
                row_key,
                {
                    "row_key": row_key,
                    "row_index": next_index + offset,
                    "row_occurrence": occurrence,
                    "source": source,
                    "row_id": row_id,
                },
            )

    output: list[dict[str, Any]] = []
    for row_key, meta in metadata.items():
        row_claims = grouped.get(row_key, [])
        labels = [row["knowledge_label"] for row in row_claims]
        if not labels:
            label = "none"
        elif all(item in {"known", "weakly_known"} for item in labels):
            label = "known"
        elif all(item == "unknown" for item in labels):
            label = "unknown"
        else:
            label = "mixed"
        output.append(
            {
                **meta,
                "knownness": label,
                "claim_count": len(labels),
                "claim_labels": dict(sorted(Counter(labels).items())),
            }
        )
    return sorted(output, key=lambda row: (int(row["row_index"]), row["row_key"]))


def expand_row_universe(patterns: list[str]) -> list[dict[str, Any]]:
    paths: list[str] = []
    for pattern in patterns:
        matched = glob.glob(pattern, recursive=True)
        if not matched and Path(pattern).is_file():
            matched = [pattern]
        paths.extend(matched)
    unique_paths = sorted(set(paths))
    if patterns and not unique_paths:
        raise ValueError("--rows-glob matched no files")
    rows: list[dict[str, Any]] = []
    for path_string in unique_paths:
        path = Path(path_string)
        inferred_source = path.stem.removeprefix("natural_greek_sft_")
        for row in load_jsonl(path):
            if "source" not in row and "config" not in row:
                row = {**row, "source": inferred_source}
            rows.append(row)
    return rows


def build_summary(claims: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    def nested_distribution(key: str) -> dict[str, dict[str, int]]:
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for row in claims:
            grouped[str(row[key])][row["knowledge_label"]] += 1
        return {group: dict(sorted(counts.items())) for group, counts in sorted(grouped.items())}

    presence_bins: Counter[str] = Counter()
    for claim in claims:
        presence = claim.get("corpus_presence")
        if presence is None:
            presence_bins["not_run"] += 1
        elif (presence.get("doc_count") or 0) > 0:
            presence_bins["present"] += 1
        else:
            presence_bins["absent_in_sample"] += 1
    row_config_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        row_config_counts[str(row["source"])][row["knownness"]] += 1
    presence_knowledge: dict[str, Counter[str]] = defaultdict(Counter)
    for row in claims:
        presence = row.get("corpus_presence")
        presence_key = "not_run" if presence is None else (
            "present" if (presence.get("doc_count") or 0) > 0 else "absent_in_sample"
        )
        presence_knowledge[presence_key][row["knowledge_label"]] += 1
    return {
        "claims": len(claims),
        "rows": len(rows),
        "claim_distribution": dict(sorted(Counter(row["knowledge_label"] for row in claims).items())),
        "row_distribution": dict(sorted(Counter(row["knownness"] for row in rows).items())),
        "claims_by_config": nested_distribution("source"),
        "claims_by_basis": nested_distribution("basis"),
        "rows_by_config": {
            config: dict(sorted(counts.items())) for config, counts in sorted(row_config_counts.items())
        },
        "corpus_presence_distribution": dict(sorted(presence_bins.items())),
        "knowledge_by_corpus_presence": {
            key: dict(sorted(counts.items())) for key, counts in sorted(presence_knowledge.items())
        },
        "protocol": {
            "shots": 4,
            "greedy_temperature": 0,
            "sample_count": 4,
            "sample_temperature": 0.5,
            "match": "normalized_token_containment",
        },
    }


def atomic_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


class TransformersGenerator:
    def __init__(
        self,
        model_path: str,
        device: str,
        dtype: str,
        max_new_tokens: int,
        seed: int,
    ):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        validate_apertus_tokenizer(self.tokenizer)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "left"
        resolved_device = device
        if device == "auto":
            resolved_device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        dtype_map = {
            "auto": "auto",
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            local_files_only=True,
            dtype=dtype_map[dtype],
        ).to(resolved_device)
        self.model.eval()
        self.device = resolved_device
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        self.calls = 0

    def _decode_new(self, generated: Any, prompt_width: int) -> list[str]:
        return self.tokenizer.batch_decode(generated[:, prompt_width:], skip_special_tokens=True)

    def __call__(self, prompts: list[str]) -> list[tuple[str, list[str]]]:
        torch = self.torch
        encoded = self.tokenizer(prompts, return_tensors="pt", padding=True).to(self.device)
        width = encoded["input_ids"].shape[1]
        with torch.inference_mode():
            greedy_ids = self.model.generate(
                **encoded,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            torch.manual_seed(self.seed + self.calls)
            if self.device == "cuda":
                torch.cuda.manual_seed_all(self.seed + self.calls)
            sample_ids = self.model.generate(
                **encoded,
                do_sample=True,
                temperature=0.5,
                top_p=1.0,
                num_return_sequences=4,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        greedy = self._decode_new(greedy_ids, width)
        sampled = self._decode_new(sample_ids, width)
        self.calls += 1
        return [(answer, sampled[index * 4 : index * 4 + 4]) for index, answer in enumerate(greedy)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--presence", type=Path)
    parser.add_argument("--rows-glob", action="append", default=[])
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=48)
    parser.add_argument("--device", choices=("auto", "cuda", "mps", "cpu"), default="auto")
    parser.add_argument("--dtype", choices=("auto", "float32", "float16", "bfloat16"), default="bfloat16")
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-steps", type=int, help="maximum generation batches")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size < 1 or args.max_new_tokens < 1:
        raise SystemExit("ERROR: batch size and max new tokens must be positive")
    if args.limit is not None and args.limit < 0:
        raise SystemExit("ERROR: --limit must be non-negative")
    if args.max_steps is not None and args.max_steps < 0:
        raise SystemExit("ERROR: --max-steps must be non-negative")
    effective_limit = args.limit
    if args.max_steps is not None:
        step_limit = args.max_steps * args.batch_size
        effective_limit = step_limit if effective_limit is None else min(effective_limit, step_limit)
    question_count = None
    if args.questions.is_file():
        with args.questions.open(encoding="utf-8") as handle:
            question_count = sum(1 for line in handle if line.strip())
        if effective_limit is not None:
            question_count = min(question_count, effective_limit)
    prompt_token_count: int | str = "unavailable: model or questions path does not exist"
    if args.dry_run and args.questions.is_file() and Path(args.model).is_dir():
        from transformers import AutoTokenizer

        dry_questions = load_jsonl(args.questions, effective_limit)
        validate_questions(dry_questions)
        dry_tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
        validate_apertus_tokenizer(dry_tokenizer)
        prompt_token_count = sum(
            len(dry_tokenizer(build_prompt(row["language"], row["question"]), add_special_tokens=True)["input_ids"])
            for row in dry_questions
        )
    plan = {
        "model": args.model,
        "model_exists": Path(args.model).is_dir(),
        "questions": str(args.questions),
        "questions_exist": args.questions.is_file(),
        "question_count": question_count,
        "planned_generations": None if question_count is None else question_count * 5,
        "planned_max_new_tokens": None if question_count is None else question_count * 5 * args.max_new_tokens,
        "prompt_token_count": prompt_token_count,
        "presence": None if args.presence is None else str(args.presence),
        "rows_glob": args.rows_glob or ["data/natural_greek_sft_*.jsonl (auto if present)"],
        "out_dir": str(args.out),
        "batch_size": args.batch_size,
        "max_new_tokens": args.max_new_tokens,
        "limit": effective_limit,
        "steps": ["validate inputs", "load tokenizer", "load model", "greedy plus four samples", "aggregate rows"],
        "dry_run": args.dry_run,
    }
    print(json.dumps(plan, sort_keys=True), flush=True)
    # The acceptance contract intentionally permits placeholder paths in dry-run;
    # their existence is reported above. Real execution fails before model load.
    if args.dry_run:
        return 0
    if not args.questions.is_file():
        raise SystemExit(f"ERROR: questions file not found: {args.questions}")
    if args.presence is not None and not args.presence.is_file():
        raise SystemExit(f"ERROR: presence file not found: {args.presence}")
    if not Path(args.model).is_dir():
        raise SystemExit(f"ERROR: model directory not found: {args.model}")

    random.seed(args.seed)
    questions = load_jsonl(args.questions, effective_limit)
    validate_questions(questions)
    presence = load_presence(args.presence)
    questions = attach_presence(questions, presence)
    row_patterns = args.rows_glob
    if not row_patterns and glob.glob("data/natural_greek_sft_*.jsonl"):
        row_patterns = ["data/natural_greek_sft_*.jsonl"]
    row_universe = expand_row_universe(row_patterns) if row_patterns else None
    if row_universe is None:
        print("warning: no row universe found; claim-free rows cannot be emitted as none", flush=True)
    generator = TransformersGenerator(args.model, args.device, args.dtype, args.max_new_tokens, args.seed)

    started = last_heartbeat = time.monotonic()
    scored: list[dict[str, Any]] = []
    for start in range(0, len(questions), args.batch_size):
        batch = questions[start : start + args.batch_size]
        scored.extend(score_records(batch, generator, batch_size=len(batch)))
        now = time.monotonic()
        if now - last_heartbeat >= 60 or start + len(batch) == len(questions):
            memory = "na"
            try:
                import torch
                if torch.cuda.is_available():
                    memory = f"{torch.cuda.max_memory_allocated() / 2**30:.2f}GiB"
            except Exception:
                pass
            print(f"HB step={start + len(batch)} loss=na tok/s=na mem={memory}", flush=True)
            last_heartbeat = now

    rows = aggregate_rows(scored, row_universe)
    summary = build_summary(scored, rows)
    summary["run"] = {
        "model": args.model,
        "questions": str(args.questions),
        "presence": None if args.presence is None else str(args.presence),
        "row_universe_patterns": row_patterns,
        "seed": args.seed,
        "dtype": args.dtype,
        "device": generator.device,
        "batch_size": args.batch_size,
        "max_new_tokens": args.max_new_tokens,
        "limit": effective_limit,
    }
    atomic_jsonl(args.out / "knownness.jsonl", scored)
    atomic_jsonl(args.out / "knownness_rows.jsonl", rows)
    atomic_json(args.out / "knownness_summary.json", summary)
    print(f"wrote claims={len(scored)} rows={len(rows)} to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from None
