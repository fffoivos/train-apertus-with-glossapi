"""Strict same-prefix preference export and completion-only masking helpers."""
from __future__ import annotations

import collections
import os
import pathlib
import tempfile

from budget import gpu_summary
from common import atomic_json, canonical, read_json, read_jsonl, sha256_text, utcnow
from schemas import Preference, prefix_sha256

PAIR_RULE_VERSION = "owner-pair-rule-2026-09-16-evening-v2"


def _atomic_jsonl(path: pathlib.Path, rows: list[dict]) -> None:
    """Replace a JSONL artifact as one fsynced file, including the empty case."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("".join(canonical(row) + "\n" for row in rows))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _tied_with_next(ranking: dict, chosen_id: str, next_id: str) -> bool:
    return any(chosen_id in group and next_id in group
               for group in ranking.get("ties_candidate_ids", []))


def _pair_ids(ranking: dict) -> tuple[str | None, str | None, str | None]:
    """Return owner-rule chosen/rejected IDs, or the rejection reason."""
    order = ranking.get("ranking_candidate_ids", [])
    verdicts = ranking.get("verdicts", {})
    if not order:
        return None, None, "no_acceptable_chosen"
    chosen_id = order[0]
    if verdicts.get(chosen_id) != "reinforce":
        return None, None, "no_acceptable_chosen"
    if chosen_id in ranking.get("unusable_candidate_ids", []):
        return None, None, "chosen_unusable"
    if len(order) < 2:
        return None, None, "no_acceptable_rejected"
    if _tied_with_next(ranking, chosen_id, order[1]):
        return None, None, "tie"
    if ranking.get("best_vs_worst") != "clear":
        return None, None, "no_substantive_preference"
    rejected_id = order[-1]
    if rejected_id == chosen_id or verdicts.get(rejected_id) not in {"neutral", "discourage"}:
        return None, None, "no_acceptable_rejected"
    return chosen_id, rejected_id, None


def completion_only_labels(history_token_ids: list[int], completion_token_ids: list[int], ignore_index: int = -100) -> list[int]:
    """Reference adapter behavior: history is masked, completion predicts itself."""
    return [ignore_index] * len(history_token_ids) + list(completion_token_ids)


def export(state: str | pathlib.Path, stage: str = "measurement") -> dict[str, int]:
    state = pathlib.Path(state)
    directory = state / stage
    selections = {r["selection_id"]: r for r in read_jsonl(directory / "selection.jsonl")
                  if r.get("inclusion_receipt", {}).get("origin") != "resample"}
    candidates = {r["candidate_id"]: r for r in read_jsonl(directory / "candidates.jsonl")
                  if r.get("selection_id") in selections}
    rankings = {r["selection_id"]: r for r in read_jsonl(directory / "rankings.jsonl")
                if r.get("selection_id") in selections}
    pref_path = directory / "preferences.jsonl"
    rejected_path = directory / "rejected_pairs.jsonl"
    # New resample registrations must not perturb the frozen base export's identity.
    source_sha256 = sha256_text("\0".join(
        "".join(canonical(row) + "\n" for row in rows)
        for rows in (list(selections.values()), list(candidates.values()), list(rankings.values()))
    ))
    summary_path = directory / "pair_export_receipt.json"
    previous_summary = read_json(summary_path) if summary_path.exists() else {}
    if (previous_summary.get("pair_rule_version") == PAIR_RULE_VERSION
            and previous_summary.get("source_sha256") == source_sha256):
        export_utc = previous_summary["created_utc"]
    else:
        export_utc = utcnow()
    accepted = rejected = 0
    preserved_preferences = [row for row in read_jsonl(pref_path) if row.get("origin") == "resample"]
    preserved_rejections = [row for row in read_jsonl(rejected_path) if row.get("origin") == "resample"]
    preference_rows: list[dict] = []
    rejected_rows: list[dict] = []
    yield_by_kind: collections.Counter[str] = collections.Counter()
    yield_by_depth: collections.Counter[str] = collections.Counter()
    yield_by_task: collections.Counter[str] = collections.Counter()
    yield_by_language: collections.Counter[str] = collections.Counter()
    contributing: set[str] = set()
    for selection_id, selection in selections.items():
        ranking = rankings.get(selection_id)
        reason = None
        if not ranking:
            reason = "missing_ranking"
        else:
            chosen_id, rejected_id, reason = _pair_ids(ranking)
            if reason is None and (chosen_id not in candidates or rejected_id not in candidates):
                reason = "candidate_missing"
        if reason:
            rejected_rows.append({"selection_id": selection_id, "trajectory_id": selection["trajectory_id"],
                                  "reason": reason, "ranking": ranking, "created_utc": export_utc,
                                  "pair_rule_version": PAIR_RULE_VERSION})
            rejected += 1
            continue
        chosen = candidates[chosen_id]; bad = candidates[rejected_id]
        if chosen["prefix_sha256"] != bad["prefix_sha256"] or chosen["prefix_sha256"] != selection["prefix_sha256"]:
            raise ValueError("export candidate prefixes are not identical")
        if prefix_sha256(selection["prefix_messages"]) != selection["prefix_sha256"]:
            raise ValueError("export prefix content changed")
        receipt = {"selection_id": selection_id, "candidate_ids": [chosen_id, rejected_id],
                   "ranking_call_id": ranking["source_call_id"], "rubric_sha16": ranking["rubric_sha16"],
                   "pair_rule_version": PAIR_RULE_VERSION,
                   "completion_mask": "all prefix/history tokens ignored; only chosen/rejected completion tokens trained"}
        row = Preference(id=f"PAIR-{selection_id}", prefix_messages=selection["prefix_messages"],
                         prefix_sha256=selection["prefix_sha256"], chosen=chosen["text"], rejected=bad["text"],
                         chosen_source=chosen["source"], rejected_source=bad["source"],
                         selection_kind=selection["kind"], depth=selection["depth"], language=selection["language"],
                         task=selection["task"], trajectory_id=selection["trajectory_id"], receipt=receipt).to_dict()
        preference_rows.append(row); accepted += 1; yield_by_kind[selection["kind"]] += 1
        yield_by_depth[str(selection["depth"])] += 1; yield_by_task[selection["task"]] += 1
        yield_by_language[selection["language"]] += 1; contributing.add(selection["trajectory_id"])
    preference_rows.extend(preserved_preferences)
    rejected_rows.extend(preserved_rejections)
    _atomic_jsonl(pref_path, preference_rows)
    _atomic_jsonl(rejected_path, rejected_rows)
    gpu = gpu_summary(state)
    summary = {"accepted_pairs": accepted, "rejected_prefixes": rejected,
               "yield_by_kind": dict(yield_by_kind), "yield_by_depth": dict(yield_by_depth),
               "yield_by_task": dict(yield_by_task), "yield_by_language": dict(yield_by_language),
               "contributing_trajectories": len(contributing), "gpu_cost_eur": gpu["spent_eur"],
               "gpu_cost_per_usable_pair_eur": gpu["spent_eur"] / accepted if accepted else None,
               "pair_rule_version": PAIR_RULE_VERSION, "source_sha256": source_sha256,
               "created_utc": export_utc}
    atomic_json(summary_path, summary)
    receipt_path = state / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    receipt.setdefault("artifacts", {})[f"{stage}/preferences.jsonl"] = {
        "sha256": sha256_text(pref_path.read_text(encoding="utf-8")), "created_utc": export_utc, "frozen": True,
        "pair_rule_version": PAIR_RULE_VERSION}
    receipt["artifacts"][f"{stage}/rejected_pairs.jsonl"] = {
        "sha256": sha256_text(rejected_path.read_text(encoding="utf-8")), "created_utc": export_utc, "frozen": True,
        "pair_rule_version": PAIR_RULE_VERSION}
    atomic_json(receipt_path, receipt)
    recommendation = directory / "final_recommendation.md"
    recommendation.write_text(
        "# Dialogue preference pilot recommendation\n\n"
        f"Exported {accepted} clear pairs; {rejected} selected prefixes yielded no pair. "
        f"Yield by P/R/C: {dict(yield_by_kind)}. Contributing trajectories: {len(contributing)}. "
        "Pair yield is a feasibility measure, not evidence that prevention or recovery training is superior. "
        "A production allocation should retain a good-context control slice and be chosen only after comparing meaningful "
        "yield and verified fixes across P/R/C, depth, task and language.\n\n"
        "Known gaps: simulator bias; sparse non-Greek language cells; observed-horizon no-error censoring; no trained-model "
        "comparison; no causal demonstration that a locally preferred reply prevents later failure.\n",
        encoding="utf-8")
    return {"accepted": accepted, "rejected": rejected}
