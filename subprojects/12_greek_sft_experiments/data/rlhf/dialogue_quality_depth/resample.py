"""Owner-authorized escalating resampling for P/R prefixes without a positive."""
from __future__ import annotations

import collections
import pathlib
import random
from typing import Any

import export_pairs
import rank
from budget import CallLedger, gpu_summary
from clients import SolClient, TargetClient
from common import append_jsonl, atomic_json, estimate_tokens, read_json, read_jsonl, sha256_json, sha256_text, utcnow
from rollout import SAMPLING, ensure_runtime_config, target_result_dict, target_result_from_dict
from schemas import Candidate, Preference, Selection, prefix_sha256

BATCH_SIZE = 4
MAX_FRESH = 32
MAX_BATCHES = MAX_FRESH // BATCH_SIZE
RESAMPLE_RULE_VERSION = "escalating-resample-2026-09-17-v1"


def _resample_selections(state: pathlib.Path, stage: str) -> list[dict[str, Any]]:
    return [row for row in read_jsonl(state / stage / "selection.jsonl")
            if row.get("inclusion_receipt", {}).get("origin") == "resample"]


def _latest_trajectories(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        latest[row["trajectory_id"]] = row
    return latest


def register_targets(state: str | pathlib.Path, stage: str,
                     targets_path: str | pathlib.Path) -> tuple[list[dict[str, Any]], int]:
    """Append stable RS selections while leaving every existing row byte-for-byte intact."""
    if stage != "measurement":
        raise ValueError("resampling is measurement-only")
    state = pathlib.Path(state)
    target_path = pathlib.Path(targets_path)
    targets = read_json(target_path)
    if not isinstance(targets, list) or not targets:
        raise ValueError("resample targets must be a non-empty JSON list")
    normalized = []
    seen_targets: set[tuple[str, str, int]] = set()
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError("each resample target must be an object")
        tid = str(target.get("trajectory_id", ""))
        kind = str(target.get("kind", ""))
        depth = target.get("depth")
        if not tid or kind not in {"P", "R"} or not isinstance(depth, int) or depth < 1:
            raise ValueError("resample target requires trajectory_id, kind P/R and positive integer depth")
        identity = (tid, kind, depth)
        if identity in seen_targets:
            raise ValueError(f"duplicate resample target: {identity}")
        seen_targets.add(identity)
        normalized.append({"trajectory_id": tid, "kind": kind, "depth": depth})
    targets_sha256 = sha256_json(normalized)

    manifest = read_json(state / "manifest.json")
    seeds = {row["trajectory_id"]: row for row in manifest["seeds"] if row["stage"] == stage}
    trajectories = _latest_trajectories(state / stage / "trajectories.jsonl")
    path = state / stage / "selection.jsonl"
    prior_rows = read_jsonl(path)
    existing = {row["selection_id"]: row for row in prior_rows}
    expected_ids = {f"RS{index:03d}" for index in range(1, len(normalized) + 1)}
    unexpected = [row["selection_id"] for row in prior_rows
                  if row.get("inclusion_receipt", {}).get("origin") == "resample"
                  and row["selection_id"] not in expected_ids]
    if unexpected:
        raise ValueError(f"registered resample selections are not in the target file: {unexpected}")

    written = 0
    registered: list[dict[str, Any]] = []
    for index, target in enumerate(normalized, 1):
        sid = f"RS{index:03d}"
        tid = target["trajectory_id"]
        if tid not in seeds or tid not in trajectories:
            raise ValueError(f"resample target trajectory is unavailable: {tid}")
        messages = trajectories[tid]["messages"]
        assistants = [(position, message) for position, message in enumerate(messages)
                      if message["role"] == "assistant"]
        if target["depth"] > len(assistants):
            raise ValueError(f"resample target depth is unavailable: {tid} depth {target['depth']}")
        assistant_position, original = assistants[target["depth"] - 1]
        prefix = messages[:assistant_position]
        prefix_hash = prefix_sha256(prefix)
        for old in prior_rows:
            if (old.get("inclusion_receipt", {}).get("origin") != "resample"
                    and old.get("trajectory_id") == tid and old.get("depth") == target["depth"]
                    and old.get("prefix_sha256") != prefix_hash):
                raise ValueError("resample prefix disagrees with existing selection at the same depth")
        row = Selection(
            selection_id=sid, trajectory_id=tid, kind=target["kind"], depth=target["depth"],
            prefix_messages=prefix, prefix_sha256=prefix_hash, original_response=original["content"],
            inclusion_receipt={"origin": "resample", "targets_sha256": targets_sha256,
                               "target_index": index - 1, "protocol": RESAMPLE_RULE_VERSION},
            language=seeds[tid]["language"], task=seeds[tid]["task"],
        ).to_dict()
        if sid in existing:
            if existing[sid] != row:
                raise ValueError(f"registered resample selection changed: {sid}")
        else:
            append_jsonl(path, row)
            existing[sid] = row
            written += 1
        registered.append(row)
    return registered, written


def sample_responses(state: str | pathlib.Path, stage: str, targets_path: str | pathlib.Path,
                     max_fresh: int, target: TargetClient, endpoint: str, model: str,
                     checkpoint_sha256: str, crash_hook=None) -> dict[str, int]:
    if max_fresh < BATCH_SIZE or max_fresh > MAX_FRESH or max_fresh % BATCH_SIZE:
        raise ValueError("max-fresh must be a multiple of four from 4 through 32")
    state = pathlib.Path(state)
    selections, registered = register_targets(state, stage, targets_path)
    manifest = read_json(state / "manifest.json")
    ledger = CallLedger(state, manifest["config"])
    ensure_runtime_config(state, target, endpoint, model, checkpoint_sha256, ledger)
    path = state / stage / "resample_candidates.jsonl"
    existing_rows = read_jsonl(path)
    existing = {row["candidate_id"]: row for row in existing_rows}
    if len(existing) != len(existing_rows):
        raise ValueError("duplicate resample candidate id")
    written = 0
    for selection in selections:
        actual_hash = prefix_sha256(selection["prefix_messages"])
        if actual_hash != selection["prefix_sha256"]:
            raise ValueError("registered resample prefix changed")
        for sample_index in range(1, max_fresh + 1):
            candidate_id = f"{selection['selection_id']}:r{sample_index:02d}"
            if candidate_id in existing:
                if (existing[candidate_id].get("prefix_sha256") != actual_hash
                        or existing[candidate_id].get("sample_index") != sample_index):
                    raise ValueError(f"resample candidate changed: {candidate_id}")
                continue
            call_id = f"target:resample:{stage}:{selection['selection_id']}:s{sample_index:02d}"
            request = {"kind": "resample", "selection_id": selection["selection_id"],
                       "candidate_id": candidate_id, "prefix_sha256": actual_hash,
                       "checkpoint_sha256": checkpoint_sha256, "sampling": SAMPLING}
            cached = ledger.reserve(call_id, "target", "resample_sampling", request)
            if cached is None:
                try:
                    result = target.complete(selection["prefix_messages"], model=model, **SAMPLING)
                    ledger.finish(call_id, result=target_result_dict(result))
                except Exception as exc:
                    ledger.finish(call_id, error=str(exc)[:1000], ambiguous=isinstance(exc, TimeoutError))
                    raise
            else:
                result = target_result_from_dict(cached)
            if crash_hook:
                crash_hook("after_target_completion", selection["selection_id"], sample_index)
            row = Candidate(candidate_id, selection["selection_id"], "new", result.text,
                            sha256_text(result.text), actual_hash, result.finish_reason,
                            result.model, result.usage).to_dict()
            row.update({"origin": "resample", "sample_index": sample_index,
                        "batch_index": (sample_index - 1) // BATCH_SIZE,
                        "wall_seconds": result.wall_seconds, "source_call_id": call_id,
                        "created_utc": utcnow()})
            append_jsonl(path, row)
            existing[candidate_id] = row
            written += 1
    return {"targets": len(selections), "registered": registered, "written": written,
            "existing": len(existing_rows), "max_fresh": max_fresh}


def _ranking_row(selection_id: str, batch_index: int, letter_to_id: dict[str, str],
                 value: dict[str, Any], call_id: str) -> dict[str, Any]:
    if len(value.get("ranking", [])) != 4 or set(value["ranking"]) != set(rank.RESAMPLE_LETTERS):
        raise ValueError("resample ranking must contain A, B, C and D exactly once")
    return {"selection_id": selection_id, "batch_index": batch_index,
            "letter_to_candidate_id": letter_to_id,
            "ranking_candidate_ids": [letter_to_id[letter] for letter in value["ranking"]],
            "ties_candidate_ids": [[letter_to_id[letter] for letter in group] for group in value["ties"]],
            "unusable_candidate_ids": [letter_to_id[letter] for letter in value["unusable"]],
            "verdicts": {letter_to_id[letter]: verdict for letter, verdict in value["verdicts"].items()},
            "issues": {letter_to_id[letter]: issues for letter, issues in value["issues"].items()},
            "notes": {letter_to_id[letter]: note for letter, note in value["notes"].items()},
            "best_vs_worst": value["best_vs_worst"], "confidence": value["confidence"],
            "rubric_sha16": rank.RUBRIC_SHA16, "source_call_id": call_id, "created_utc": utcnow()}


def _lowest_ranked(rankings: list[dict[str, Any]], candidates: dict[str, dict[str, Any]]) -> str:
    severity = {"reinforce": 0, "neutral": 1, "discourage": 2}
    scored = []
    for row in rankings:
        for position, candidate_id in enumerate(row["ranking_candidate_ids"]):
            scored.append((severity[row["verdicts"][candidate_id]], position,
                           row["batch_index"], candidates[candidate_id]["sample_index"], candidate_id))
    if not scored:
        raise ValueError("no judged resample candidate")
    return max(scored)[-1]


def judge_resamples(state: str | pathlib.Path, stage: str, sol: SolClient) -> dict[str, int]:
    if stage != "measurement":
        raise ValueError("resample judging is measurement-only")
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    ledger = CallLedger(state, manifest["config"])
    selections = {row["selection_id"]: row for row in _resample_selections(state, stage)}
    candidate_rows = read_jsonl(state / stage / "resample_candidates.jsonl")
    candidates = {row["candidate_id"]: row for row in candidate_rows}
    by_selection: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in candidate_rows:
        by_selection[row["selection_id"]].append(row)
    ranking_path = state / stage / "resample_rankings.jsonl"
    existing_rankings = {(row["selection_id"], row["batch_index"]): row
                         for row in read_jsonl(ranking_path)}
    result_path = state / stage / "resample_judgments.jsonl"
    existing_results = {row["selection_id"]: row for row in read_jsonl(result_path)}
    calls = written_rankings = completed = 0
    for selection_id in sorted(selections):
        if selection_id in existing_results:
            completed += 1
            continue
        rows = sorted(by_selection.get(selection_id, []), key=lambda row: row["sample_index"])
        if len(rows) != MAX_FRESH or [row["sample_index"] for row in rows] != list(range(1, MAX_FRESH + 1)):
            raise ValueError(f"selection {selection_id} requires exactly 32 ordered fresh candidates")
        judged: list[dict[str, Any]] = []
        winning_id = None
        winning_ranking = None
        for batch_index in range(MAX_BATCHES):
            batch = [row for row in rows if row["batch_index"] == batch_index]
            if len(batch) != BATCH_SIZE:
                raise ValueError(f"selection {selection_id} batch {batch_index} requires four candidates")
            key = (selection_id, batch_index)
            ranking_row = existing_rankings.get(key)
            if ranking_row is None:
                shuffled = list(batch)
                random.Random(f"9162602|resample|{selection_id}|{batch_index}").shuffle(shuffled)
                letter_to_id = {letter: row["candidate_id"]
                                for letter, row in zip(rank.RESAMPLE_LETTERS, shuffled)}
                prompt = rank.resample_ranking_prompt(
                    selections[selection_id]["prefix_messages"],
                    {letter: row["text"] for letter, row in zip(rank.RESAMPLE_LETTERS, shuffled)},
                )
                call_id = f"sol:resample:{stage}:{selection_id}:b{batch_index}"
                request = {"selection_id": selection_id, "batch_index": batch_index,
                           "candidate_ids": [row["candidate_id"] for row in batch],
                           "prompt_sha256": sha256_text(prompt), "rubric_sha16": rank.RUBRIC_SHA16,
                           "estimated_input_tokens": estimate_tokens(prompt)}
                cached = ledger.reserve(call_id, "sol", "resample", request)
                if cached is None:
                    try:
                        value = sol.call(prompt, rank.RESAMPLE_RANK_SCHEMA,
                                         model="gpt-5.6-sol", effort="high", timeout=900)
                        ledger.finish(call_id, result=value)
                    except Exception as exc:
                        ledger.finish(call_id, error=str(exc)[:1000])
                        raise
                    calls += 1
                else:
                    value = cached
                ranking_row = _ranking_row(selection_id, batch_index, letter_to_id, value, call_id)
                append_jsonl(ranking_path, ranking_row)
                existing_rankings[key] = ranking_row
                written_rankings += 1
            judged.append(ranking_row)
            reinforces = [candidate_id for candidate_id in ranking_row["ranking_candidate_ids"]
                          if ranking_row["verdicts"].get(candidate_id) == "reinforce"]
            if reinforces:
                winning_id = reinforces[0]
                winning_ranking = ranking_row
                break
        lowest_id = _lowest_ranked(judged, candidates)
        if winning_id is None:
            summary = {"selection_id": selection_id, "trajectory_id": selections[selection_id]["trajectory_id"],
                       "kind": selections[selection_id]["kind"], "status": "no_reinforce_at_32",
                       "batches_judged": MAX_BATCHES, "samples_needed": "no_reinforce_at_32",
                       "samples_judged": MAX_FRESH, "winning_candidate_id": None,
                       "lowest_ranked_candidate_id": lowest_id, "clear_margin": False,
                       "ranking_call_ids": [row["source_call_id"] for row in judged],
                       "protocol": RESAMPLE_RULE_VERSION, "created_utc": utcnow()}
        else:
            summary = {"selection_id": selection_id, "trajectory_id": selections[selection_id]["trajectory_id"],
                       "kind": selections[selection_id]["kind"], "status": "reinforce_found",
                       "batches_judged": len(judged), "samples_needed": BATCH_SIZE * len(judged),
                       "samples_judged": BATCH_SIZE * len(judged), "winning_candidate_id": winning_id,
                       "lowest_ranked_candidate_id": lowest_id,
                       "clear_margin": winning_ranking["best_vs_worst"] == "clear",
                       "winning_batch_index": winning_ranking["batch_index"],
                       "ranking_call_ids": [row["source_call_id"] for row in judged],
                       "protocol": RESAMPLE_RULE_VERSION, "created_utc": utcnow()}
        append_jsonl(result_path, summary)
        existing_results[selection_id] = summary
        completed += 1
    return {"targets": len(selections), "completed": completed, "sol_calls": calls,
            "rankings_written": written_rankings}


def export_resamples(state: str | pathlib.Path, stage: str) -> dict[str, int]:
    if stage != "measurement":
        raise ValueError("resample export is measurement-only")
    state = pathlib.Path(state)
    directory = state / stage
    selections = {row["selection_id"]: row for row in _resample_selections(state, stage)}
    candidates = {row["candidate_id"]: row for row in read_jsonl(directory / "resample_candidates.jsonl")}
    judgments = {row["selection_id"]: row for row in read_jsonl(directory / "resample_judgments.jsonl")}
    if set(judgments) != set(selections):
        raise ValueError("every resample selection must have a completed judgment")
    source_names = ("resample_candidates.jsonl", "resample_rankings.jsonl", "resample_judgments.jsonl")
    source_sha256 = sha256_text("\0".join((directory / name).read_text(encoding="utf-8")
                                          for name in source_names))
    report_path = directory / "resample_report.json"
    old_report = read_json(report_path) if report_path.exists() else {}
    export_utc = (old_report.get("created_utc") if old_report.get("protocol") == RESAMPLE_RULE_VERSION
                  and old_report.get("source_sha256") == source_sha256 else None) or utcnow()
    pref_path = directory / "preferences.jsonl"
    rejected_path = directory / "rejected_pairs.jsonl"
    preference_rows = [row for row in read_jsonl(pref_path) if row.get("origin") != "resample"]
    rejected_rows = [row for row in read_jsonl(rejected_path) if row.get("origin") != "resample"]
    target_report = []
    accepted = rejected = 0
    for selection_id in sorted(selections):
        selection = selections[selection_id]
        judgment = judgments[selection_id]
        reason = None
        if judgment["status"] == "no_reinforce_at_32":
            reason = "no_reinforce_at_32"
        elif not judgment.get("clear_margin"):
            reason = "no_clear_margin"
        chosen_id = judgment.get("winning_candidate_id")
        rejected_id = judgment.get("lowest_ranked_candidate_id")
        if reason is None and (chosen_id not in candidates or rejected_id not in candidates):
            reason = "candidate_missing"
        pair_exported = reason is None
        if reason:
            rejected_rows.append({"selection_id": selection_id, "trajectory_id": selection["trajectory_id"],
                                  "reason": reason, "origin": "resample",
                                  "samples_needed": judgment["samples_needed"], "judgment": judgment,
                                  "created_utc": export_utc, "protocol": RESAMPLE_RULE_VERSION})
            rejected += 1
        else:
            chosen = candidates[chosen_id]
            bad = candidates[rejected_id]
            if (chosen["prefix_sha256"] != bad["prefix_sha256"]
                    or chosen["prefix_sha256"] != selection["prefix_sha256"]
                    or prefix_sha256(selection["prefix_messages"]) != selection["prefix_sha256"]):
                raise ValueError("resample export prefix changed")
            receipt = {"selection_id": selection_id, "candidate_ids": [chosen_id, rejected_id],
                       "origin": "resample", "samples_needed": judgment["samples_needed"],
                       "ranking_call_ids": judgment["ranking_call_ids"],
                       "rubric_sha16": rank.RUBRIC_SHA16, "protocol": RESAMPLE_RULE_VERSION,
                       "completion_mask": "all prefix/history tokens ignored; only chosen/rejected completion tokens trained"}
            row = Preference(id=f"PAIR-{selection_id}", prefix_messages=selection["prefix_messages"],
                             prefix_sha256=selection["prefix_sha256"], chosen=chosen["text"],
                             rejected=bad["text"], chosen_source=chosen["source"],
                             rejected_source=bad["source"], selection_kind=selection["kind"],
                             depth=selection["depth"], language=selection["language"], task=selection["task"],
                             trajectory_id=selection["trajectory_id"], receipt=receipt).to_dict()
            row.update({"origin": "resample", "samples_needed": judgment["samples_needed"]})
            preference_rows.append(row)
            accepted += 1
        target_report.append({**judgment, "pair_exported": pair_exported,
                              "export_rejection_reason": reason})
    export_pairs._atomic_jsonl(pref_path, preference_rows)
    export_pairs._atomic_jsonl(rejected_path, rejected_rows)

    histogram = dict(collections.Counter(str(row["samples_needed"]) for row in judgments.values()))
    by_kind = {}
    for kind in ("P", "R"):
        rows = [row for row in target_report if row["kind"] == kind]
        by_kind[kind] = {"targets": len(rows),
                         "reinforce_found": sum(row["status"] == "reinforce_found" for row in rows),
                         "no_reinforce_at_32": sum(row["status"] == "no_reinforce_at_32" for row in rows),
                         "pairs_exported": sum(row["pair_exported"] for row in rows)}
    no_reinforce = sum(row["status"] == "no_reinforce_at_32" for row in target_report)
    counts = CallLedger(state).counts()["calls"]
    sol_calls = sum(row["count"] for row in counts
                    if row["provider"] == "sol" and row["phase"] == "resample")
    report = {"protocol": RESAMPLE_RULE_VERSION, "source_sha256": source_sha256,
              "created_utc": export_utc, "targets": target_report,
              "aggregate": {"target_count": len(target_report), "pairs_exported": accepted,
                            "rejected_targets": rejected, "samples_needed_histogram": histogram,
                            "no_reinforce_at_32": no_reinforce,
                            "share_no_reinforce_at_32": no_reinforce / len(target_report) if target_report else None,
                            "by_kind": by_kind,
                            "cost": {"gpu_spent_eur_total": gpu_summary(state)["spent_eur"],
                                     "sol_resample_calls_reserved": sol_calls,
                                     "fresh_target_completions": len(candidates)}}}
    atomic_json(report_path, report)
    receipt_path = state / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    for name, path in ((f"{stage}/preferences.jsonl", pref_path),
                       (f"{stage}/rejected_pairs.jsonl", rejected_path),
                       (f"{stage}/resample_report.json", report_path)):
        receipt.setdefault("artifacts", {})[name] = {
            "sha256": sha256_text(path.read_text(encoding="utf-8")), "created_utc": export_utc,
            "frozen": True, "pair_rule_version": export_pairs.PAIR_RULE_VERSION,
            "resample_protocol": RESAMPLE_RULE_VERSION}
    atomic_json(receipt_path, receipt)
    return {"accepted": accepted, "rejected": rejected, "targets": len(selections)}
