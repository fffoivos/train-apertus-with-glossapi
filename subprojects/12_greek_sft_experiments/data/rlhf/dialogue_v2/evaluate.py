"""Evaluator view (plan §5-§6, §8 review): prefix-local turn evaluations and hindsight conversation reviews.

Turn packets end at the judged reply and never contain later turns; at most one packet per conversation per call.
Evaluations separate target-model errors from simulator/world/learner errors.
"""
from __future__ import annotations

import concurrent.futures as futures
import json
import pathlib
from typing import Any

from common import append_jsonl, read_jsonl, run_tag_for, runtime_dir_for, sha256_json, utcnow, word_count
from contracts import (CONVERSATION_REVIEW_SCHEMA, CONVERSATION_REVIEW_VERSION, DEV_TAGS, TURN_EVAL_SCHEMA,
                       TURN_EVAL_VERSION, prompt_text)
from glossary import Glossary
from ledger import CallLedger
from rollout import Context, _sol, latest_trajectories

EVAL_EFFORT = "medium"   # owner, 17 Sept: all pipeline Sol calls at medium


def _snapshots(runtime: pathlib.Path, case_id: str) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for row in read_jsonl(runtime / "user_state_snapshots.jsonl"):
        if row["case_id"] == case_id and row["row_id"].endswith(":next_turn"):
            out[int(row["after_user_decision_for_turn"])] = row["state"]
    return out


def state_before_reply(seed: dict[str, Any], runtime: pathlib.Path, turn: int) -> dict[str, Any]:
    from user_state import init_state
    snaps = _snapshots(runtime, seed["case_id"])
    return snaps[turn - 1] if turn > 1 and (turn - 1) in snaps else init_state(seed)


def evaluator_reference(seed: dict[str, Any]) -> dict[str, Any]:
    ref = {"evaluator_reference": seed["evaluator_reference"]}
    if seed["category"] == "writing":
        ref["illustrative_reference_draft"] = seed["user_view_extras"]["reference_draft"]
    if seed.get("world"):
        ref["hidden_world"] = {"root_cause": seed["world"]["root_cause"], "hidden_facts": seed["world"]["hidden_facts"]}
    if seed.get("learner"):
        ref["learner_seed"] = {"transfer_question": seed["learner"]["transfer_question"],
                               "practice_text": seed["learner"].get("practice_text")}
    return ref


def turn_packets(seed: dict[str, Any], trajectory: dict[str, Any], runtime: pathlib.Path) -> list[dict[str, Any]]:
    messages = trajectory["messages"]
    positions = [i for i, m in enumerate(messages) if m["role"] == "assistant"]
    packets = []
    for turn, pos in enumerate(positions, 1):
        state = state_before_reply(seed, runtime, turn)
        packet = {"packet_id": f"{seed['case_id']}:a{turn}", "case_id": seed["case_id"], "category": seed["category"],
                  "language": seed["language"], "labels": seed["labels"], "judged_assistant_turn": turn,
                  "visible_conversation_through_judged_reply": messages[:pos + 1],
                  "prefix_sha256": sha256_json(messages[:pos]),
                  "judged_reply_word_count": word_count(messages[pos]["content"]),
                  "disclosed_preferences_at_this_point": state["disclosed_preferences"],
                  "undisclosed_preferences_at_this_point": [p["text"] for p in state["private_preferences"]],
                  **evaluator_reference(seed)}
        if seed.get("world"):
            packet["observations_revealed_before_this_reply"] = state["observations_obtained"]
        if seed.get("learner"):
            packet["learner_state_before_this_reply"] = state["learner"]
        packets.append(packet)
    return packets


LABEL_SECTIONS = ("attitude", "register", "interaction", "difficulty", "detail", "task")


def label_union(label_sets: list[dict[str, str]]) -> dict[str, list[str]]:
    """Every label value the packets carry gets its glossary definition; maths is always defined (maths content)."""
    out: dict[str, set[str]] = {section: set() for section in LABEL_SECTIONS}
    for labels in label_sets:
        for section in LABEL_SECTIONS:
            if section in labels:
                out[section].add(labels[section])
    out["task"].add("math")
    return {k: sorted(v) for k, v in out.items() if v}


def _eval_block(glossary: Glossary, label_sets: list[dict[str, str]]) -> str:
    return glossary.block(label_union(label_sets), dialogue=[("Reference-guided dialogue categories", None),
                                                             ("Role views", ["evaluator view"])])


def turn_eval_prompt(glossary: Glossary, packets: list[dict[str, Any]]) -> str:
    return (prompt_text("turn_eval_v1.txt") + "\n\n" + _eval_block(glossary, [p["labels"] for p in packets])
            + "\n\nPACKETS (JSON):\n" + json.dumps(packets, ensure_ascii=False, indent=1))


def evaluate_turns(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str]) -> dict[str, Any]:
    by_tag: dict[str, list[str]] = {}
    for cid in case_ids:
        by_tag.setdefault(run_tag_for(cid), []).append(cid)
    written = 0
    calls = 0
    for tag, cids in by_tag.items():
        runtime = ctx.runtime(cids[0])
        ledger = CallLedger(runtime, tag)
        trajectories = latest_trajectories(runtime)
        done = {r["packet_id"] for r in read_jsonl(runtime / "turn_evaluations.jsonl")}
        packets_by_turn: dict[int, list[dict[str, Any]]] = {}
        for cid in cids:
            if cid not in trajectories:
                continue
            for packet in turn_packets(seeds[cid], trajectories[cid], runtime):
                if packet["packet_id"] not in done:
                    packets_by_turn.setdefault(packet["judged_assistant_turn"], []).append(packet)

        def run(turn: int, packets: list[dict[str, Any]]):
            prompt = turn_eval_prompt(ctx.glossary, packets)
            ids = [p["packet_id"] for p in packets]
            call_id = f"sol:turn_eval:{tag}:t{turn}:{sha256_json(ids)[:12]}"
            result = _sol(ctx, ledger, call_id, "turn_evaluation", prompt, TURN_EVAL_SCHEMA, EVAL_EFFORT,
                          {"packet_ids": ids, "turn_eval_version": TURN_EVAL_VERSION})
            return call_id, packets, result

        with futures.ThreadPoolExecutor(max_workers=6) as pool:
            for call_id, packets, result in pool.map(lambda kv: run(*kv), sorted(packets_by_turn.items())):
                calls += 1
                by_id = {e["packet_id"]: e for e in result.get("evaluations", [])}
                missing = [p["packet_id"] for p in packets if p["packet_id"] not in by_id]
                if missing:
                    raise ValueError(f"turn evaluation missing packets {missing}")
                for packet in packets:
                    row = {**by_id[packet["packet_id"]], "case_id": packet["case_id"],
                           "assistant_turn": packet["judged_assistant_turn"], "prefix_sha256": packet["prefix_sha256"],
                           "source_call_id": call_id, "turn_eval_version": TURN_EVAL_VERSION,
                           "glossary_sha16": ctx.glossary.sha16, "created_utc": utcnow(), **DEV_TAGS}
                    append_jsonl(runtime / "turn_evaluations.jsonl", row)
                    written += 1
    return {"written": written, "calls": calls}


def review_packet(seed: dict[str, Any], runtime: pathlib.Path) -> dict[str, Any]:
    cid = seed["case_id"]
    trajectory = latest_trajectories(runtime)[cid]
    user_turns = [r for r in read_jsonl(runtime / "user_turns.jsonl") if r["case_id"] == cid]
    world_events = [r for r in read_jsonl(runtime / "world_events.jsonl") if r["case_id"] == cid]
    evals = [r for r in read_jsonl(runtime / "turn_evaluations.jsonl") if r["case_id"] == cid]
    snaps = [r for r in read_jsonl(runtime / "user_state_snapshots.jsonl") if r["case_id"] == cid]
    keep_user = ("row_id", "user_turn_index", "follows_assistant_turn", "mode", "message", "move", "new_information",
                 "trigger", "changes_task", "assistance_level", "perceived_latest_reply", "revealed_private_preference_ids",
                 "task_progress", "knowledge_updates", "misconception_status", "transfer_attempt", "private_note",
                 "allowed_moves", "policy_violations_after_repair", "repair_used", "state_transition", "observations_given")
    return {"case_id": cid, "category": seed["category"], "language": seed["language"], "labels": seed["labels"],
            "public_transcript": trajectory["messages"], "ending_reason": trajectory["ending_reason"],
            "ending_detail": trajectory["ending_detail"],
            "initial_user_state": seed["user_state"], "learner_seed": seed.get("learner"),
            "user_turn_records": [{k: r.get(k) for k in keep_user} for r in user_turns],
            "final_user_state": snaps[-1]["state"] if snaps else None,
            "world_events": [{k: r[k] for k in ("after_assistant_turn", "actions", "skipped_suggestions", "resolutions",
                                                "observations", "world_state_before", "world_state_after")}
                             for r in world_events],
            "turn_evaluations": [{k: r[k] for k in ("assistant_turn", "local_quality", "decisive_evidence", "error_summary",
                                                    "factual_or_subject_errors", "maths_content", "used_latest_guidance",
                                                    "retained_earlier_constraints", "needs_human_review")} for r in evals],
            **evaluator_reference(seed)}


def review_prompt(glossary: Glossary, packet: dict[str, Any]) -> str:
    block = glossary.block(label_union([packet["labels"]]), moves=True,
                           dialogue=[("Sampling points", None), ("Ending reasons", None), ("User state", None),
                                     ("Role views", ["user view", "world resolver", "learner view", "evaluator view"]),
                                     ("Reference-guided dialogue categories", None)])
    return (prompt_text("conversation_review_v1.txt") + "\n\n" + block + "\n\nCONVERSATION RECORD (JSON):\n"
            + json.dumps(packet, ensure_ascii=False, indent=1))


def review_conversations(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str]) -> dict[str, Any]:
    def run(cid: str):
        runtime = ctx.runtime(cid)
        if any(r["case_id"] == cid for r in read_jsonl(runtime / "conversation_reviews.jsonl")):
            return cid, None
        if cid not in latest_trajectories(runtime):
            return cid, None
        ledger = CallLedger(runtime, run_tag_for(cid))
        packet = review_packet(seeds[cid], runtime)
        prompt = review_prompt(ctx.glossary, packet)
        call_id = f"sol:conversation_review:{cid}:{sha256_json(packet)[:12]}"
        result = _sol(ctx, ledger, call_id, "conversation_review", prompt, CONVERSATION_REVIEW_SCHEMA, EVAL_EFFORT,
                      {"case_id": cid, "conversation_review_version": CONVERSATION_REVIEW_VERSION})
        row = {**result, "case_id": cid, "source_call_id": call_id, "packet_sha256": sha256_json(packet),
               "conversation_review_version": CONVERSATION_REVIEW_VERSION, "glossary_sha16": ctx.glossary.sha16,
               "created_utc": utcnow(), **DEV_TAGS}
        append_jsonl(runtime / "conversation_reviews.jsonl", row)
        return cid, call_id

    with futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run, case_ids))
    return {"reviewed": [cid for cid, call in results if call], "skipped": [cid for cid, call in results if not call]}


# ---------------------------------------------------------------------------------------------------------------
# 60-dialogue collection: one combined post-trajectory review per conversation (amendment, minimal check 3)
# ---------------------------------------------------------------------------------------------------------------
def _reply_facts(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    return {"words": word_count(text), "non_empty_lines": sum(1 for ln in lines if ln.strip()),
            "paragraphs": sum(1 for block in text.split("\n\n") if block.strip()),
            "bullet_lines": sum(1 for ln in lines if ln.lstrip().startswith(("-", "*", "•"))),
            "numbered_lines": sum(1 for ln in lines if ln.lstrip()[:3].rstrip(".)").isdigit())}


def combined_packet(seed: dict[str, Any], runtime: pathlib.Path) -> dict[str, Any]:
    cid = seed["case_id"]
    trajectory = latest_trajectories(runtime)[cid]
    messages = trajectory["messages"]
    positions = [i for i, m in enumerate(messages) if m["role"] == "assistant"]
    per_reply = []
    for turn, pos in enumerate(positions, 1):
        state = state_before_reply(seed, runtime, turn)
        item = {"assistant_turn": turn, "prefix_sha256": sha256_json(messages[:pos]),
                "requirements_disclosed_before_this_reply": state["disclosed_preferences"],
                "preferences_still_undisclosed_at_this_reply": [p["text"] for p in state["private_preferences"]],
                "computed_facts": _reply_facts(messages[pos]["content"])}
        if seed.get("world"):
            item["observations_revealed_before_this_reply"] = state["observations_obtained"]
        if seed.get("learner"):
            item["learner_state_before_this_reply"] = state["learner"]
        per_reply.append(item)
    user_turns = [r for r in read_jsonl(runtime / "user_turns.jsonl") if r["case_id"] == cid and r.get("mode") != "opening"]
    world_events = [r for r in read_jsonl(runtime / "world_events.jsonl") if r["case_id"] == cid]
    keep_user = ("user_turn_index", "follows_assistant_turn", "message", "move", "done", "new_information", "trigger",
                 "changes_task", "assistance_level", "perceived_latest_reply", "revealed_private_preference_ids",
                 "knowledge_updates", "misconception_status", "transfer_attempt", "policy_violations_after_repair", "repair_used")
    return {"case_id": cid, "category": seed["category"], "language": seed["language"], "labels": seed["labels"],
            "public_transcript": messages, "ending_reason": trajectory["ending_reason"], "ending_detail": trajectory["ending_detail"],
            "initial_user_state": seed["user_state"], "per_reply": per_reply,
            "user_turn_records": [{k: r.get(k) for k in keep_user} for r in user_turns],
            "world_events": [{k: r[k] for k in ("after_assistant_turn", "actions", "resolutions", "observations")} for r in world_events],
            **evaluator_reference(seed)}


def combined_prompt(glossary: Glossary, packet: dict[str, Any]) -> str:
    block = glossary.block(label_union([packet["labels"]]), moves=True,
                           dialogue=[("Ending reasons", None), ("User state", None),
                                     ("Role views", ["evaluator view"]), ("Reference-guided dialogue categories", None)])
    return (prompt_text("combined_review_c60_v1.txt") + "\n\n" + block + "\n\nCONVERSATION RECORD (JSON):\n"
            + json.dumps(packet, ensure_ascii=False, indent=1))


def review_combined(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str], workers: int = 10) -> dict[str, Any]:
    from contracts import C60_REVIEW_SCHEMA, C60_REVIEW_VERSION

    def run(cid: str):
        runtime = ctx.runtime(cid)
        if any(r["case_id"] == cid for r in read_jsonl(runtime / "conversation_reviews.jsonl")):
            return cid, "already_reviewed"
        if cid not in latest_trajectories(runtime):
            return cid, "no_trajectory"
        ledger = CallLedger(runtime, run_tag_for(cid))
        packet = combined_packet(seeds[cid], runtime)
        call_id = f"sol:combined_review:{cid}:{sha256_json(packet)[:12]}"
        result = _sol(ctx, ledger, call_id, "combined_review", combined_prompt(ctx.glossary, packet), C60_REVIEW_SCHEMA,
                      EVAL_EFFORT, {"case_id": cid, "review_version": C60_REVIEW_VERSION})
        turns_seen = sorted(t["assistant_turn"] for t in result["turns"])
        expected = [p["assistant_turn"] for p in packet["per_reply"]]
        if turns_seen != expected:
            raise ValueError(f"{cid}: review annotated turns {turns_seen}, expected {expected}")
        prefix = {p["assistant_turn"]: p["prefix_sha256"] for p in packet["per_reply"]}
        for t in result["turns"]:   # the per-turn rows keep the old shape so points, report and page read them unchanged
            append_jsonl(runtime / "turn_evaluations.jsonl", {**t, "case_id": cid, "prefix_sha256": prefix[t["assistant_turn"]],
                                                              "source_call_id": call_id, "turn_eval_version": C60_REVIEW_VERSION,
                                                              "glossary_sha16": ctx.glossary.sha16, "created_utc": utcnow(), **DEV_TAGS})
        append_jsonl(runtime / "conversation_reviews.jsonl", {**result, "case_id": cid, "source_call_id": call_id,
                                                              "packet_sha256": sha256_json(packet), "conversation_review_version": C60_REVIEW_VERSION,
                                                              "glossary_sha16": ctx.glossary.sha16, "created_utc": utcnow(), **DEV_TAGS})
        return cid, call_id

    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, case_ids))
    return {"reviewed": [c for c, s in results if s.startswith("sol:")], "other": {c: s for c, s in results if not s.startswith("sol:")}}
