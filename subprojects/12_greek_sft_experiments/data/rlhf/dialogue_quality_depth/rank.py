"""Three-way candidate ranking with randomized, provenance-hidden letters."""
from __future__ import annotations

import collections
import json
import pathlib
import random
from typing import Any

from budget import CallLedger
from clients import SolClient
from common import append_jsonl, estimate_tokens, read_json, read_jsonl, sha256_text, utcnow

HERE = pathlib.Path(__file__).resolve().parent
RUBRIC_PATH = HERE.parent / "prompts" / "judge_rank4_v2_en.txt"
RUBRIC = RUBRIC_PATH.read_text(encoding="utf-8")
RUBRIC_SHA16 = sha256_text(RUBRIC)[:16]
LETTERS = "ABC"
RESAMPLE_LETTERS = "ABCD"
RANK_SCHEMA = {"type": "object", "properties": {
    "ranking": {"type": "array", "items": {"type": "string", "enum": list(LETTERS)}},
    "ties": {"type": "array", "items": {"type": "array", "items": {"type": "string", "enum": list(LETTERS)}}},
    "unusable": {"type": "array", "items": {"type": "string", "enum": list(LETTERS)}},
    "verdicts": {"type": "object", "properties": {L: {"type": "string", "enum": ["reinforce", "neutral", "discourage"]} for L in LETTERS}, "required": list(LETTERS), "additionalProperties": False},
    "issues": {"type": "object", "properties": {L: {"type": "array", "items": {"type": "string"}} for L in LETTERS}, "required": list(LETTERS), "additionalProperties": False},
    "notes": {"type": "object", "properties": {L: {"type": "string"} for L in LETTERS}, "required": list(LETTERS), "additionalProperties": False},
    "best_vs_worst": {"type": "string", "enum": ["clear", "slight", "none"]},
    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
}, "required": ["ranking", "ties", "unusable", "verdicts", "issues", "notes", "best_vs_worst", "confidence"], "additionalProperties": False}
RANK_BATCH_SCHEMA = {"type": "object", "properties": {
    "rankings": {"type": "array", "items": {"type": "object", "properties": {
        "selection_id": {"type": "string"}, **RANK_SCHEMA["properties"]},
        "required": ["selection_id", *RANK_SCHEMA["required"]], "additionalProperties": False}}
    }, "required": ["rankings"], "additionalProperties": False}
RESAMPLE_RANK_SCHEMA = {"type": "object", "properties": {
    "ranking": {"type": "array", "items": {"type": "string", "enum": list(RESAMPLE_LETTERS)}},
    "ties": {"type": "array", "items": {"type": "array", "items": {"type": "string", "enum": list(RESAMPLE_LETTERS)}}},
    "unusable": {"type": "array", "items": {"type": "string", "enum": list(RESAMPLE_LETTERS)}},
    "verdicts": {"type": "object", "properties": {L: {"type": "string", "enum": ["reinforce", "neutral", "discourage"]} for L in RESAMPLE_LETTERS}, "required": list(RESAMPLE_LETTERS), "additionalProperties": False},
    "issues": {"type": "object", "properties": {L: {"type": "array", "items": {"type": "string"}} for L in RESAMPLE_LETTERS}, "required": list(RESAMPLE_LETTERS), "additionalProperties": False},
    "notes": {"type": "object", "properties": {L: {"type": "string"} for L in RESAMPLE_LETTERS}, "required": list(RESAMPLE_LETTERS), "additionalProperties": False},
    "best_vs_worst": {"type": "string", "enum": ["clear", "slight", "none"]},
    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
}, "required": ["ranking", "ties", "unusable", "verdicts", "issues", "notes", "best_vs_worst", "confidence"], "additionalProperties": False}


def ranking_prompt(prefix: list[dict[str, str]], texts_by_letter: dict[str, str]) -> str:
    conversation = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in prefix)
    candidates = "\n\n".join(f"=== CANDIDATE {letter} ===\n{texts_by_letter[letter]}" for letter in LETTERS)
    pilot = (
        "PILOT-SPECIFIC RULES: There are exactly three candidates. Their provenance is unavailable and must not be "
        "inferred. Ties are allowed. Give an absolute verdict for every candidate and place an answer first only if it "
        "is acceptable on its own. The ranking must contain A, B and C exactly once. Return JSON only."
    )
    return f"{RUBRIC}\n\n{pilot}\n\n=== CONVERSATION PREFIX ===\n{conversation}\n\n{candidates}\n\n=== END ==="


def resample_ranking_prompt(prefix: list[dict[str, str]], texts_by_letter: dict[str, str]) -> str:
    """Four-candidate packet with the frozen v2.4 rubric verbatim."""
    conversation = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in prefix)
    candidates = "\n\n".join(
        f"=== CANDIDATE {letter} ===\n{texts_by_letter[letter]}" for letter in RESAMPLE_LETTERS
    )
    pilot = (
        "RESAMPLING RULES: There are exactly four fresh candidates. Their provenance and sampling order are "
        "unavailable and must not be inferred. Ties are allowed. Give an absolute verdict for every candidate. "
        "The ranking must contain A, B, C and D exactly once. Return JSON only."
    )
    return f"{RUBRIC}\n\n{pilot}\n\n=== CONVERSATION PREFIX ===\n{conversation}\n\n{candidates}\n\n=== END ==="


def rank_candidates(state: str | pathlib.Path, stage: str, sol: SolClient) -> dict[str, int]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    selections = {r["selection_id"]: r for r in read_jsonl(state / stage / "selection.jsonl")
                  if r.get("inclusion_receipt", {}).get("origin") != "resample"}
    candidates: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in read_jsonl(state / stage / "candidates.jsonl"):
        candidates[row["selection_id"]].append(row)
    path = state / stage / "rankings.jsonl"
    existing = {r["selection_id"] for r in read_jsonl(path)}
    ledger = CallLedger(state, manifest["config"])
    written = 0
    jobs = []
    for selection_id in sorted(selections):
        if selection_id in existing:
            continue
        rows = candidates.get(selection_id, [])
        if len(rows) != 3 or len({r["candidate_id"] for r in rows}) != 3:
            raise ValueError(f"selection {selection_id} requires exactly three candidates")
        if len({r["prefix_sha256"] for r in rows}) != 1 or rows[0]["prefix_sha256"] != selections[selection_id]["prefix_sha256"]:
            raise ValueError("candidate prefixes differ")
        ordered = sorted(rows, key=lambda r: r["candidate_id"])
        random.Random(f"9162602|{selection_id}").shuffle(ordered)
        letter_to_id = {letter: row["candidate_id"] for letter, row in zip(LETTERS, ordered)}
        packet = ranking_prompt(selections[selection_id]["prefix_messages"],
                                {letter: row["text"] for letter, row in zip(LETTERS, ordered)})
        jobs.append((selection_id, letter_to_id, packet))
    for offset in range(0, len(jobs), 4):
        batch = jobs[offset:offset + 4]
        ids = [job[0] for job in batch]
        # Each packet repeats the frozen rubric deliberately: packet boundaries
        # remain explicit and no conversation can influence another ranking.
        prompt = "\n\n===== INDEPENDENT RANKING PACKET =====\n\n".join(
            f"SELECTION ID: {selection_id}\n{packet}" for selection_id, _, packet in batch)
        prompt += "\n\nReturn {\"rankings\": [...]} with one independent result and matching selection_id per packet."
        call_id = f"sol:rank:{stage}:{sha256_text('|'.join(ids))[:16]}"
        cached = ledger.reserve(call_id, "sol", "candidate_review", {"selection_ids": ids,
                                                                       "prompt_sha256": sha256_text(prompt),
                                                                       "rubric_sha16": RUBRIC_SHA16,
                                                                       "estimated_input_tokens": estimate_tokens(prompt)})
        if cached is None:
            try:
                result = sol.call(prompt, RANK_BATCH_SCHEMA, model="gpt-5.6-sol", effort="high", timeout=900)
                ledger.finish(call_id, result=result)
            except Exception as exc:
                ledger.finish(call_id, error=str(exc)[:1000])
                raise
        else:
            result = cached
        by_id = {row["selection_id"]: row for row in result.get("rankings", [])}
        if set(by_id) != set(ids):
            raise ValueError("ranking batch IDs mismatch")
        for selection_id, letter_to_id, _ in batch:
            value = by_id[selection_id]
            if len(value["ranking"]) != 3 or set(value["ranking"]) != set(LETTERS):
                raise ValueError("ranking must contain each randomized letter once")
            row = {"selection_id": selection_id, "letter_to_candidate_id": letter_to_id,
                   "ranking_candidate_ids": [letter_to_id[x] for x in value["ranking"]],
                   "ties_candidate_ids": [[letter_to_id[x] for x in group] for group in value["ties"]],
                   "unusable_candidate_ids": [letter_to_id[x] for x in value["unusable"]],
                   "verdicts": {letter_to_id[k]: v for k, v in value["verdicts"].items()},
                   "issues": {letter_to_id[k]: v for k, v in value["issues"].items()},
                   "notes": {letter_to_id[k]: v for k, v in value["notes"].items()},
                   "best_vs_worst": value["best_vs_worst"], "confidence": value["confidence"],
                   "rubric_sha16": RUBRIC_SHA16, "source_call_id": call_id, "created_utc": utcnow()}
            append_jsonl(path, row); written += 1
    return {"written": written, "existing": len(existing), "selections": len(selections)}
