"""D1 branch candidates at selected saved prefixes (plan §6): byte-identical prefix, 8 fresh replies sampled in one GPU
session, judged in escalating fours with rubric v2.4 (4 first, 4 more only if no verified acceptable reply), blinded
candidate order, verification of the chosen reply, same-prefix pairs only, no splicing of old suffixes."""
from __future__ import annotations

import concurrent.futures as futures
import json
import random
from typing import Any

from clients import AmbiguousTimeout, ContextLimitError, result_from_dict, result_to_dict
from common import RUBRIC_PATH, append_jsonl, read_jsonl, run_tag_for, sha16_file, sha256_json, sha256_text, utcnow, word_count
from contracts import (BRANCH_RANK_SCHEMA, BRANCH_RULE_VERSION, BRANCH_VERIFY_SCHEMA, BRANCH_VERIFY_VERSION,
                       CANDIDATES_FIRST, CANDIDATES_MAX, DEV_TAGS, GENERATOR_VERSION, MODEL_REVISION, SAMPLING,
                       SAMPLING_CONFIG_VERSION, USER_POLICY_VERSION, prompt_text)
from ledger import CallAlreadyAttempted, CallLedger
from rollout import Context, _sol
from views import public_messages

LETTERS = "ABCD"
RUBRIC = RUBRIC_PATH.read_text(encoding="utf-8")
RUBRIC_SHA16 = sha16_file(RUBRIC_PATH)


def branch_points(runtime) -> list[dict[str, Any]]:
    return read_jsonl(runtime / "branch_points.jsonl")


def sample_candidates(ctx: Context, case_ids: list[str], workers: int = 16, topup_point_ids: set[str] | None = None,
                      candidates_override: int | None = None) -> dict[str, Any]:
    jobs = []
    for cid in case_ids:
        runtime = ctx.runtime(cid)
        for point in branch_points(runtime):
            if point["case_id"] != cid:
                continue
            prefix = public_messages(point["prefix_messages"])
            if sha256_json(prefix) != point["prefix_sha256"] or prefix[-1]["role"] != "user":
                raise ValueError(f"{point['point_id']}: stored prefix changed or does not end with the user turn")
            planned = int(candidates_override or point.get("candidates_planned", CANDIDATES_MAX))
            if topup_point_ids and point["point_id"] in topup_point_ids:
                planned = max(planned, 8)                          # explicit top-up only (amendment: not automatic)
            for k in range(1, planned + 1):
                jobs.append((runtime, cid, point, prefix, k))
    existing: dict[str, set[str]] = {}

    def run(job):
        runtime, cid, point, prefix, k = job
        ledger = CallLedger(runtime, run_tag_for(cid))
        candidate_id = f"{point['point_id']}:c{k}"
        call_id = f"target:branch:{candidate_id}"
        request = {"kind": "branch_candidate", "point_id": point["point_id"], "candidate_index": k,
                   "prefix_sha256": point["prefix_sha256"], "model": ctx.model, "model_revision": MODEL_REVISION,
                   "checkpoint_sha256": ctx.checkpoint_sha256, "sampling": SAMPLING,
                   "sampling_config_version": SAMPLING_CONFIG_VERSION}
        try:
            cached = ledger.reserve(call_id, "target", "branch_sampling", request)
        except CallAlreadyAttempted as exc:
            return {"candidate_id": candidate_id, "error": str(exc)}
        if cached is not None:
            result = result_from_dict(cached)
        else:
            try:
                result = ctx.target.complete(prefix, model=ctx.model, **SAMPLING)
            except (ContextLimitError, AmbiguousTimeout, Exception) as exc:  # noqa: BLE001
                ledger.finish(call_id, error=str(exc)[:1000], ambiguous=isinstance(exc, AmbiguousTimeout))
                return {"candidate_id": candidate_id, "error": str(exc)[:300]}
            ledger.finish(call_id, result=result_to_dict(result), wall_seconds=result.wall_seconds)
        row = {"candidate_id": candidate_id, "point_id": point["point_id"], "case_id": cid, "candidate_index": k,
               "judging_batch": (k - 1) // CANDIDATES_FIRST, "origin": "branch_resample", "text": result.text,
               "text_sha256": sha256_text(result.text), "prefix_sha256": point["prefix_sha256"],
               "finish_reason": result.finish_reason, "usage": result.usage, "wall_seconds": result.wall_seconds,
               "served_model": result.model, "model_revision": MODEL_REVISION, "checkpoint_sha256": ctx.checkpoint_sha256,
               "sampling": SAMPLING, "sampling_config_version": SAMPLING_CONFIG_VERSION, "source_call_id": call_id,
               "created_utc": utcnow(), **DEV_TAGS}
        return {"candidate_id": candidate_id, "row": row, "runtime": runtime}

    written, errors = 0, []
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for out in pool.map(run, jobs):
            if "error" in out:
                errors.append(out)
                continue
            runtime = out["runtime"]
            key = str(runtime)
            if key not in existing:
                existing[key] = {r["candidate_id"] for r in read_jsonl(runtime / "branch_candidates.jsonl")}
            if out["candidate_id"] not in existing[key]:
                append_jsonl(runtime / "branch_candidates.jsonl", out["row"])
                existing[key].add(out["candidate_id"])
                written += 1
    return {"jobs": len(jobs), "written": written, "errors": errors}


def ranking_prompt(prefix: list[dict[str, str]], texts: dict[str, str]) -> str:
    conversation = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in prefix)
    candidates = "\n\n".join(f"=== CANDIDATE {L} ===\n{texts[L]}" for L in LETTERS)
    rules = ("BRANCH RULES (dialogue v2 development): There are exactly four fresh candidate replies to the final user turn "
             "of this saved conversation. Earlier assistant turns are part of the fixed history and are not being judged. "
             "Candidate provenance and sampling order are unavailable and must not be inferred. Ties are allowed. Give an "
             "absolute verdict for every candidate. The ranking must contain A, B, C and D exactly once. Return JSON only.")
    return f"{RUBRIC}\n\n{rules}\n\n=== CONVERSATION PREFIX ===\n{conversation}\n\n{candidates}\n\n=== END ==="


def pair_from_ranking(ranking: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Owner pair rule (dialogue_quality_depth/export_pairs.py, CK4): top reinforce, clear gap, rejected neutral/discourage."""
    order = ranking["ranking_candidate_ids"]
    verdicts = ranking["verdicts"]
    if not order or verdicts.get(order[0]) != "reinforce":
        return None, None, "no_acceptable_chosen"
    chosen = order[0]
    if chosen in ranking["unusable_candidate_ids"]:
        return None, None, "chosen_unusable"
    if any(chosen in group and order[1] in group for group in ranking["ties_candidate_ids"]):
        return None, None, "tie"
    if ranking["best_vs_worst"] != "clear":
        return None, None, "no_substantive_preference"
    rejected = order[-1]
    if verdicts.get(rejected) not in {"neutral", "discourage"}:
        return None, None, "no_acceptable_rejected"
    return chosen, rejected, None


def _stats(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    return {"words": word_count(text), "bullet_lines": sum(1 for ln in lines if ln.lstrip().startswith(("-", "*", "•"))),
            "numbered_lines": sum(1 for ln in lines if ln.lstrip()[:3].rstrip(".)").isdigit())}


def judge_points(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str]) -> dict[str, Any]:
    results = []

    def run_point(point: dict[str, Any]) -> dict[str, Any]:
        cid = point["case_id"]
        runtime = ctx.runtime(cid)
        ledger = CallLedger(runtime, run_tag_for(cid))
        candidates = sorted((r for r in read_jsonl(runtime / "branch_candidates.jsonl") if r["point_id"] == point["point_id"]),
                            key=lambda r: r["candidate_index"])
        if any(r["prefix_sha256"] != point["prefix_sha256"] for r in candidates):
            raise ValueError(f"{point['point_id']}: candidate prefix hash differs")
        outcome: dict[str, Any] = {"point_id": point["point_id"], "case_id": cid, "kind": point["kind"],
                                   "before_assistant_turn": point["before_assistant_turn"], "batches": [],
                                   "candidates_available": len(candidates)}
        for batch in range(CANDIDATES_MAX // CANDIDATES_FIRST):
            rows = [r for r in candidates if r["judging_batch"] == batch]
            if len(rows) != CANDIDATES_FIRST:
                outcome["batches"].append({"batch": batch, "status": "incomplete_batch", "available": len(rows)})
                break
            shuffled = list(rows)
            random.Random(f"dv2|{point['point_id']}|{batch}").shuffle(shuffled)
            letter_to_id = {L: r["candidate_id"] for L, r in zip(LETTERS, shuffled)}
            prompt = ranking_prompt(point["prefix_messages"], {L: r["text"] for L, r in zip(LETTERS, shuffled)})
            rank = _sol(ctx, ledger, f"sol:branch_rank:{point['point_id']}:b{batch}", "branch_ranking", prompt,
                        BRANCH_RANK_SCHEMA, "medium", {"point_id": point["point_id"], "batch": batch, "rubric_sha16": RUBRIC_SHA16})
            if sorted(rank["ranking"]) != sorted(LETTERS):
                raise ValueError("ranking must contain A-D once")
            ranking = {"ranking_candidate_ids": [letter_to_id[L] for L in rank["ranking"]],
                       "ties_candidate_ids": [[letter_to_id[L] for L in g] for g in rank["ties"]],
                       "unusable_candidate_ids": [letter_to_id[L] for L in rank["unusable"]],
                       "verdicts": {letter_to_id[L]: v for L, v in rank["verdicts"].items()},
                       "issues": {letter_to_id[L]: v for L, v in rank["issues"].items()},
                       "notes": {letter_to_id[L]: v for L, v in rank["notes"].items()},
                       "best_vs_worst": rank["best_vs_worst"], "confidence": rank["confidence"],
                       "letter_to_candidate_id": letter_to_id}
            chosen, rejected, reason = pair_from_ranking(ranking)
            record = {"batch": batch, "ranking": ranking, "pair_rule_reason": reason, "chosen": chosen, "rejected": rejected}
            if chosen:
                by_id = {r["candidate_id"]: r for r in rows}
                seed = seeds[cid]
                packet = {"prefix": point["prefix_messages"],
                          "CHOSEN": {"text": by_id[chosen]["text"], "computed_stats": _stats(by_id[chosen]["text"])},
                          "REJECTED": {"text": by_id[rejected]["text"], "computed_stats": _stats(by_id[rejected]["text"])},
                          "disclosed_requirements_note": "All requirements disclosed in the prefix apply unless the user later changed them.",
                          "evaluator_reference": seed["evaluator_reference"]}
                vprompt = (prompt_text("branch_verify_v1.txt") + "\n\n" + ctx.glossary.block({"task": "math"})
                           + "\n\nPAIR PACKET (JSON):\n" + json.dumps(packet, ensure_ascii=False, indent=1))
                verify = _sol(ctx, ledger, f"sol:branch_verify:{point['point_id']}:b{batch}", "branch_verification",
                              vprompt, BRANCH_VERIFY_SCHEMA, "medium", {"point_id": point["point_id"], "batch": batch,
                                                                      "branch_verify_version": BRANCH_VERIFY_VERSION})
                record["verification"] = verify
                if verify["maths_content"]:
                    record["decision"] = "held_for_maths_judge"
                elif verify["chosen_acceptable"] and verify["rejected_meaningfully_worse"]:
                    record["decision"] = "pair_accepted"
                else:
                    record["decision"] = "verification_failed"
            else:
                record["decision"] = "no_pair_in_batch"
            outcome["batches"].append(record)
            if record["decision"] in {"pair_accepted", "held_for_maths_judge"}:
                break
        final = outcome["batches"][-1] if outcome["batches"] else {}
        outcome["result"] = final.get("decision", "not_judged")
        judged = sum(CANDIDATES_FIRST for b in outcome["batches"] if "ranking" in b)
        outcome["samples_judged"] = judged
        outcome["verified_acceptable_found_within"] = judged if outcome["result"] == "pair_accepted" else None
        outcome["report_phrase"] = (f"verified acceptable reply found within {judged}" if outcome["result"] == "pair_accepted"
                                    else f"no verified acceptable reply within {judged}")
        # Matched-count comparison (plan §6): both points always have their first four judged; a reply accepted within
        # four is also within eight, so found_within_4 and found_within_8 are defined for every fully judged point.
        accepted_batch = next((b["batch"] for b in outcome["batches"] if b.get("decision") == "pair_accepted"), None)
        outcome["found_within_4"] = accepted_batch == 0 if outcome["batches"] and "ranking" in outcome["batches"][0] else None
        outcome["found_within_8"] = (accepted_batch is not None) if (accepted_batch is not None or judged == 8) else None
        outcome.update({"branch_rule_version": BRANCH_RULE_VERSION, "rubric_sha16": RUBRIC_SHA16,
                        "created_utc": utcnow(), **DEV_TAGS})
        append_jsonl(runtime / "branch_judgements.jsonl", outcome)
        if outcome["result"] == "pair_accepted":
            by_id = {r["candidate_id"]: r for r in candidates}
            ch, rj = by_id[final["chosen"]], by_id[final["rejected"]]
            seed = seeds[cid]
            pair = {"pair_id": f"DV2PAIR-{point['point_id']}", "case_id": cid, "prompt_id": cid,
                    "prompt_sha256": sha256_text(seed["opening"]), "prefix_messages": point["prefix_messages"],
                    "prefix_sha256": point["prefix_sha256"], "chosen": ch["text"], "rejected": rj["text"],
                    "chosen_candidate_id": ch["candidate_id"], "rejected_candidate_id": rj["candidate_id"],
                    "chosen_sha256": ch["text_sha256"], "rejected_sha256": rj["text_sha256"],
                    "sampling_point_kind": point["kind"], "single_turn_material": point["single_turn_material"],
                    "assistance_level": point["assistance_level_of_last_user_turn"], "depth": point["before_assistant_turn"],
                    "task": seed["labels"]["task"], "language": seed["language"], "source_family": seed["source_family"],
                    "generator_version": GENERATOR_VERSION, "glossary_sha16": ctx.glossary.sha16,
                    "user_policy_version": USER_POLICY_VERSION, "target_checkpoint_sha256": ctx.checkpoint_sha256,
                    "model_revision": MODEL_REVISION, "sampling": SAMPLING, "sampling_config_version": SAMPLING_CONFIG_VERSION,
                    "judge": {"rubric": "v2.4", "rubric_sha16": RUBRIC_SHA16, "branch_verify_version": BRANCH_VERIFY_VERSION},
                    "eligibility_under_pair_rule": True, "hold_reason": None, "supersedes": None, "origin": "branch_resample",
                    "split": "development", "status": "development_demo",
                    "loss_note": "completion-only: prefix/history tokens are conditioning, only chosen/rejected completion tokens are scored; trainer integration unverified (no DPO trainer exists)",
                    "created_utc": utcnow(), **DEV_TAGS}
            append_jsonl(runtime / "branch_pairs.jsonl", pair)
        return outcome

    points = [p for cid in case_ids for p in branch_points(ctx.runtime(cid)) if p["case_id"] == cid]
    done = {r["point_id"] for cid in case_ids for r in read_jsonl(ctx.runtime(cid) / "branch_judgements.jsonl")}
    with futures.ThreadPoolExecutor(max_workers=8) as pool:
        for outcome in pool.map(run_point, [p for p in points if p["point_id"] not in done]):
            results.append({k: outcome[k] for k in ("point_id", "kind", "result", "samples_judged", "report_phrase")})
    return {"judged": results}


# ---------------------------------------------------------------------------------------------------------------
# 60-dialogue collection judging (amendment, minimal check 4)
# ---------------------------------------------------------------------------------------------------------------
MATHS_RUBRIC_PATH = RUBRIC_PATH.parent / "judge_rank4_maths_en.txt"


def _rank_schema(letters: str) -> dict[str, Any]:
    from contracts import _enum, _obj, S
    return _obj({"ranking": {"type": "array", "items": _enum(letters)},
                 "ties": {"type": "array", "items": {"type": "array", "items": _enum(letters)}},
                 "unusable": {"type": "array", "items": _enum(letters)},
                 "verdicts": _obj({L: _enum(["reinforce", "neutral", "discourage"]) for L in letters}),
                 "issues": _obj({L: {"type": "array", "items": S} for L in letters}),
                 "notes": _obj({L: S for L in letters}),
                 "best_vs_worst": _enum(["clear", "slight", "none"]), "confidence": _enum(["high", "medium", "low"])})


def _ranking_prompt_n(rubric: str, prefix: list[dict[str, str]], texts: dict[str, str]) -> str:
    conversation = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in prefix)
    candidates = "\n\n".join(f"=== CANDIDATE {L} ===\n{texts[L]}" for L in texts)
    n = len(texts)
    rules = (f"BRANCH RULES (60-dialogue collection): There are exactly {n} distinct fresh candidate replies to the final user turn "
             "of this saved conversation (exact duplicates were removed before judging). Earlier assistant turns are fixed history "
             "and are not judged. Candidate provenance and order are unavailable and must not be inferred. Give an absolute verdict "
             "for every candidate (reinforce means acceptable to reinforce), list its substantive errors in issues, rank all of them "
             "(ties allowed), and state the gap between best and worst. If the latest request is contradictory or impossible, a reply "
             "that names the conflict or asks for clarification can be acceptable; literal compliance with an impossible request is not "
             "required. Return JSON only.")
    return f"{rubric}\n\n{rules}\n\n=== CONVERSATION PREFIX ===\n{conversation}\n\n{candidates}\n\n=== END ==="


def judge_points_c60(ctx: Context, seeds: dict[str, dict[str, Any]], case_ids: list[str], workers: int = 8) -> dict[str, Any]:
    from contracts import C60_BRANCH_RULE_VERSION

    def run_point(point: dict[str, Any]) -> dict[str, Any]:
        cid = point["case_id"]; seed = seeds[cid]
        runtime = ctx.runtime(cid); ledger = CallLedger(runtime, run_tag_for(cid))
        candidates = sorted((r for r in read_jsonl(runtime / "branch_candidates.jsonl") if r["point_id"] == point["point_id"]),
                            key=lambda r: r["candidate_index"])
        if any(r["prefix_sha256"] != point["prefix_sha256"] for r in candidates):
            raise ValueError(f"{point['point_id']}: candidate prefix hash differs")
        maths = seed["labels"].get("task") == "math"         # owner: maths reviewer prompt only where maths is the task
        rubric_path = MATHS_RUBRIC_PATH if maths else RUBRIC_PATH
        unique: dict[str, dict[str, Any]] = {}
        for r in candidates:
            unique.setdefault(r["text_sha256"], r)          # exact duplicates share one judgement
        outcome = {"point_id": point["point_id"], "case_id": cid, "kind": point["kind"], "before_assistant_turn": point["before_assistant_turn"],
                   "sampled": len(candidates), "unique_texts": len(unique), "rubric": rubric_path.name, "rubric_sha16": sha16_file(rubric_path),
                   "duplicate_of": {r["candidate_id"]: unique[r["text_sha256"]]["candidate_id"] for r in candidates
                                    if unique[r["text_sha256"]]["candidate_id"] != r["candidate_id"]}}
        if len(unique) < 2:
            outcome.update(result="no_pair_all_candidates_identical" if candidates else "not_sampled", acceptable_unique=None, paired=False)
        else:
            rows = list(unique.values())[:4]
            random.Random(f"c60|{point['point_id']}").shuffle(rows)
            letters = LETTERS[:len(rows)]
            letter_to_id = {L: r["candidate_id"] for L, r in zip(letters, rows)}
            prompt = _ranking_prompt_n(rubric_path.read_text(encoding="utf-8"), point["prefix_messages"], {L: r["text"] for L, r in zip(letters, rows)})
            rank = _sol(ctx, ledger, f"sol:c60_rank:{point['point_id']}:n{len(rows)}", "branch_ranking", prompt, _rank_schema(letters),
                        "medium", {"point_id": point["point_id"], "rubric_sha16": outcome["rubric_sha16"]})
            if sorted(rank["ranking"]) != sorted(letters):
                raise ValueError(f"{point['point_id']}: ranking must contain {letters} once")
            ranking = {"ranking_candidate_ids": [letter_to_id[L] for L in rank["ranking"]],
                       "ties_candidate_ids": [[letter_to_id[L] for L in g] for g in rank["ties"]],
                       "unusable_candidate_ids": [letter_to_id[L] for L in rank["unusable"]],
                       "verdicts": {letter_to_id[L]: v for L, v in rank["verdicts"].items()},
                       "issues": {letter_to_id[L]: v for L, v in rank["issues"].items()},
                       "notes": {letter_to_id[L]: v for L, v in rank["notes"].items()},
                       "best_vs_worst": rank["best_vs_worst"], "confidence": rank["confidence"], "letter_to_candidate_id": letter_to_id}
            chosen, rejected, reason = pair_from_ranking(ranking)
            outcome.update(ranking=ranking, pair_rule_reason=reason, chosen=chosen, rejected=rejected,
                           acceptable_unique=sum(1 for v in ranking["verdicts"].values() if v == "reinforce"))
            if chosen:                                        # verify only the proposed positive, never every alternative
                by_id = {r["candidate_id"]: r for r in rows}
                packet = {"prefix": point["prefix_messages"],
                          "CHOSEN": {"text": by_id[chosen]["text"], "computed_stats": _stats(by_id[chosen]["text"])},
                          "REJECTED": {"text": by_id[rejected]["text"], "computed_stats": _stats(by_id[rejected]["text"])},
                          "disclosed_requirements_note": "All requirements disclosed in the prefix apply unless the user later changed them.",
                          "evaluator_reference": seed["evaluator_reference"]}
                vprompt = (prompt_text("branch_verify_v1.txt") + "\n\n" + ctx.glossary.block({"task": "math"})
                           + "\n\nPAIR PACKET (JSON):\n" + json.dumps(packet, ensure_ascii=False, indent=1))
                verify = _sol(ctx, ledger, f"sol:c60_verify:{point['point_id']}", "branch_verification", vprompt, BRANCH_VERIFY_SCHEMA,
                              "medium", {"point_id": point["point_id"], "branch_verify_version": BRANCH_VERIFY_VERSION})
                outcome["verification"] = verify
                ok = verify["chosen_acceptable"] and verify["rejected_meaningfully_worse"]
                outcome["result"] = "pair_accepted" if ok else "verification_failed"
            else:
                outcome["result"] = "no_pair"
            outcome["paired"] = outcome["result"] == "pair_accepted"
        outcome["topup_candidate"] = (not outcome.get("paired")) and outcome["sampled"] < 8
        outcome.update(branch_rule_version=C60_BRANCH_RULE_VERSION, created_utc=utcnow(), **DEV_TAGS)
        append_jsonl(runtime / "branch_judgements.jsonl", outcome)
        if outcome.get("paired"):
            by_id = {r["candidate_id"]: r for r in candidates}
            ch, rj = by_id[outcome["chosen"]], by_id[outcome["rejected"]]
            append_jsonl(runtime / "branch_pairs.jsonl", {
                "pair_id": f"C60PAIR-{point['point_id']}", "case_id": cid, "point_kind": point["kind"], "prefix_messages": point["prefix_messages"],
                "prefix_sha256": point["prefix_sha256"], "chosen": ch["text"], "rejected": rj["text"], "chosen_candidate_id": ch["candidate_id"],
                "rejected_candidate_id": rj["candidate_id"], "chosen_sha256": ch["text_sha256"], "rejected_sha256": rj["text_sha256"],
                "depth": point["before_assistant_turn"], "single_turn_material": point["single_turn_material"],
                "change_type": point.get("change_type"), "change_quality": point.get("change_quality"),
                "task": seed["labels"]["task"], "language": seed["language"], "group": seed.get("group"), "source_family": seed["source_family"],
                "judge": {"rubric": outcome["rubric"], "rubric_sha16": outcome["rubric_sha16"], "branch_verify_version": BRANCH_VERIFY_VERSION},
                "target_checkpoint_sha256": ctx.checkpoint_sha256, "model_revision": MODEL_REVISION, "sampling": SAMPLING,
                "split": "development", "created_utc": utcnow(), **DEV_TAGS})
        return outcome

    points = [p for cid in case_ids for p in branch_points(ctx.runtime(cid)) if p["case_id"] == cid]
    done = {r["point_id"] for cid in set(case_ids) for r in read_jsonl(ctx.runtime(cid) / "branch_judgements.jsonl")}
    results = []
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for o in pool.map(run_point, [p for p in points if p["point_id"] not in done]):
            results.append({k: o.get(k) for k in ("point_id", "kind", "sampled", "unique_texts", "acceptable_unique", "result")})
    return {"judged": results}
