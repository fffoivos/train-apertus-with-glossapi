#!/usr/bin/env python3
"""Escalating judging over a large field of replies (32 per point), for the 60-dialogue collection.

Measured on the 4-reply run (88 verified replies), which is what this design rests on:
- the ranker's screen has no false negatives worth chasing: 0 of 30 non-reinforce replies verified clean, so
  non-reinforce replies are never verified here;
- its ordering inside reinforce carries no signal (rank 1 45% clean, rank 2 46%), so EVERY nomination is verified in
  rank order, never just the top one;
- the verified acceptability rate is 5.9% per reply, not the 13.2% reinforce rate, so a point needs a big field before
  it is likely to contain a clean reply (20% at 4 replies, 67% at 32).

Flow per point: rank a batch of 8 -> verify each reinforce nomination with the turn-scoped verifier (branch_verify_v2)
-> stop at the first verified-clean reply -> pair it against the lowest-ranked reply of that same batch. Pairs are formed
inside one ranking call, as in round 3. A rejected reply may itself be a reinforce reply when the verifier confirms the
gap: at 32 replies a point can nominate several, and requiring the rejected to be non-reinforce loses those points.

Usage: python3 data/rlhf/dialogue_v2/collection60/judge32.py [--cases ...] [--points ...] [--batch-size 8]
                                                             [--max-batches 4] [--workers 8] [--dry-run]
"""
from __future__ import annotations

import argparse, collections, concurrent.futures as futures, difflib, json, pathlib, random, string, sys, types
HERE = pathlib.Path(__file__).resolve().parent; DV2 = HERE.parent; sys.path.insert(0, str(DV2))
import branch, seeds as seeds_module                                              # noqa: E402
from clients import CodexSolClient                                                # noqa: E402
from common import C60_RUNTIME, RUBRIC_PATH, append_jsonl, read_jsonl, sha16_file, sha256_json, utcnow  # noqa: E402
from contracts import (BRANCH_VERIFY_V2_SCHEMA, BRANCH_VERIFY_V2_VERSION, C60_BRANCH_RULE_VERSION,  # noqa: E402
                       prompt_text)
from glossary import Glossary                                                     # noqa: E402
from ledger import CallLedger                                                     # noqa: E402
from rollout import _sol                                                          # noqa: E402
from reverify_c60 import packet as verify_packet                                  # noqa: E402

JUDGE_VERSION = "c60-escalate8-v1"
OUT_JUDGE, OUT_PAIRS = "branch_judgements_32.jsonl", "branch_pairs_32.jsonl"

MULTITURN = (
    "MULTI-TURN SCOPE: these candidates answer the LATEST user turn of an ongoing conversation, not the whole task. "
    "Later turns narrow, replace and withdraw earlier ones. A candidate that correctly does what the latest turn asks "
    "is not deficient for leaving out parts of the task the user is no longer asking about, and a candidate that offers "
    "something the user has just excluded is the worse for it. A standing instruction the user has not withdrawn still "
    "counts, and dropping it is an error.")


def ranking_prompt(rubric: str, prefix: list[dict], texts: dict[str, str]) -> str:
    conversation = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in prefix)
    candidates = "\n\n".join(f"=== CANDIDATE {L} ===\n{texts[L]}" for L in texts)
    n = len(texts)
    rules = (f"BRANCH RULES (60-dialogue collection): There are exactly {n} distinct fresh candidate replies to the final "
             "user turn of this saved conversation (exact duplicates were removed before judging). Earlier assistant turns "
             "are fixed history and are not judged. Candidate provenance and order are unavailable and must not be inferred. "
             "Give an absolute verdict for every candidate (reinforce means acceptable to reinforce), list its substantive "
             "errors in issues, rank all of them (ties allowed), and state the gap between best and worst. If the latest "
             "request is contradictory or impossible, a reply that names the conflict or asks for clarification can be "
             "acceptable; literal compliance with an impossible request is not required. Return JSON only.")
    return f"{rubric}\n\n{rules}\n\n{MULTITURN}\n\n=== CONVERSATION PREFIX ===\n{conversation}\n\n{candidates}\n\n=== END ==="


def batches_for(rows: list[dict], point_id: str, size: int) -> list[list[dict]]:
    order = list(rows)
    random.Random(f"c60v2|{point_id}").shuffle(order)          # blind the sampling order, deterministically
    return [order[i:i + size] for i in range(0, len(order), size)]


def unique_candidates(runtime: pathlib.Path, point_id: str) -> tuple[list[dict], dict[str, str]]:
    rows = sorted((r for r in read_jsonl(runtime / "branch_candidates.jsonl") if r["point_id"] == point_id),
                  key=lambda r: r["candidate_index"])
    seen, keep, dup = {}, [], {}
    for r in rows:
        first = seen.get(r["text_sha256"])
        if first:
            dup[r["candidate_id"]] = first
        else:
            seen[r["text_sha256"]] = r["candidate_id"]; keep.append(r)
    return keep, dup


def judge_point(ctx, ledger, point, seed, rubric, batch_size, max_batches, runtime):
    rows, dup = unique_candidates(runtime, point["point_id"])
    out = {"record": "judgement32", "point_id": point["point_id"], "case_id": point["case_id"], "kind": point["kind"],
           "judge_version": JUDGE_VERSION, "branch_rule_version": C60_BRANCH_RULE_VERSION,
           "rubric_sha16": sha16_file(RUBRIC_PATH), "branch_verify_version": BRANCH_VERIFY_V2_VERSION,
           "sampled": len(rows) + len(dup), "unique_texts": len(rows), "duplicate_of": dup,
           "batches": [], "verifications": [], "training_eligible": False, "experiment_credit": "development_demo",
           "created_utc": utcnow()}
    by_id = {r["candidate_id"]: r for r in rows}
    pair = tier2 = None

    for bi, batch in enumerate(batches_for(rows, point["point_id"], batch_size)[:max_batches]):
        letters = string.ascii_uppercase[:len(batch)]
        # the call id carries a signature of the exact field judged, so a verdict is only ever replayed for the same
        # set of replies: a trial over 4 replies can never be resumed as an answer about a field of 32
        bsig = sha256_json(sorted(r["candidate_id"] for r in batch))[:8]
        letter_to_id = {L: r["candidate_id"] for L, r in zip(letters, batch)}
        prompt = ranking_prompt(rubric, point["prefix_messages"], {L: r["text"] for L, r in zip(letters, batch)})
        rank = _sol(ctx, ledger, f"sol:c60v2_rank:{point['point_id']}:b{bi}:{bsig}", "branch_ranking", prompt,
                    branch._rank_schema(letters), "medium",
                    {"point_id": point["point_id"], "batch": bi, "batch_signature": bsig, "field_size": len(batch),
                     "judge_version": JUDGE_VERSION})
        # The ranker occasionally returns an incomplete ranking (C60C27:B:a2 b1: five candidates in, four letters back).
        # Judge only what it actually ranked rather than inventing a position for the dropped reply or losing the batch:
        # an unranked candidate is simply not considered here, and the omission is recorded.
        seen_letters, ranked = set(), []
        for L in rank["ranking"]:
            if L in letter_to_id and L not in seen_letters:
                seen_letters.add(L); ranked.append(L)
        missing = [L for L in letters if L not in seen_letters]
        order = [letter_to_id[L] for L in ranked]
        verdicts = {letter_to_id[L]: v for L, v in rank["verdicts"].items() if L in seen_letters}
        if len(order) < 2:
            out["batches"].append({"batch": bi, "ranking_incomplete": missing, "unusable": True,
                                   "ranking_candidate_ids": order, "verdicts": verdicts})
            continue
        out["batches"].append({"batch": bi, "ranking_candidate_ids": order, "verdicts": verdicts,
                               "ranking_incomplete": missing,
                               "issues": {letter_to_id[L]: v for L, v in rank["issues"].items()},
                               "notes": {letter_to_id[L]: v for L, v in rank["notes"].items()},
                               "best_vs_worst": rank["best_vs_worst"], "confidence": rank["confidence"]})

        nominations = [c for c in order if verdicts.get(c) == "reinforce"]      # rank order only decides the queue
        for cand in nominations:
            rejected = next((c for c in reversed(order) if c != cand), None)
            if rejected is None:
                continue
            j = {"case_id": point["case_id"], "chosen": cand, "rejected": rejected}
            vprompt = prompt_text("branch_verify_v2.txt") + "\n\nPAIR PACKET (JSON):\n" + json.dumps(
                verify_packet(point, j, by_id, seed), ensure_ascii=False, indent=1)
            v = _sol(ctx, ledger, f"sol:c60v2_verify:{cand}:{bsig}", "branch_verification", vprompt, BRANCH_VERIFY_V2_SCHEMA,
                     "medium", {"candidate_id": cand, "batch": bi, "branch_verify_version": BRANCH_VERIFY_V2_VERSION})
            out["verifications"].append({"candidate_id": cand, "rejected": rejected, "batch": bi,
                                         "rank_position": order.index(cand) + 1, "verdict": v["chosen_verdict"],
                                         "responsive": v["chosen_responsive"], "truthful": v["chosen_truthful"],
                                         "rejected_meaningfully_worse": v["rejected_meaningfully_worse"],
                                         "violations": v["chosen_violations"], "notes": v["notes"]})
            if not v["rejected_meaningfully_worse"]:
                continue
            if v["chosen_verdict"] == "clean":
                pair = (cand, rejected, bi, v); break
            if v["chosen_verdict"] == "flawed_but_better" and tier2 is None:
                tier2 = (cand, rejected, bi, v)
        if pair:
            break

    chosen = pair or tier2
    if chosen:
        cand, rejected, bi, v = chosen
        a, b = by_id[cand]["text"], by_id[rejected]["text"]
        sim = difflib.SequenceMatcher(None, a, b).ratio()
        out["result"] = "pair_accepted" if pair else "tier2_only"
        out["pair"] = {"pair_id": f"C60PAIR32-{point['point_id'].replace(':', '-')}", "tier": 1 if pair else 2,
                       "chosen": cand, "rejected": rejected, "batch": bi, "similarity": round(sim, 3),
                       "minimal_pair": sim > 0.80, "point_kind": point["kind"],
                       "change_type": point.get("change_type"), "single_turn_material": point.get("single_turn_material")}
    else:
        nominated = any(v["verdict"] for v in out["verifications"])
        out["result"] = "no_clean_reply" if nominated else "no_nomination"
        out["pair"] = None
    out["calls"] = {"ranking": len(out["batches"]), "verification": len(out["verifications"])}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*"); ap.add_argument("--points", nargs="*")
    ap.add_argument("--batch-size", type=int, default=8); ap.add_argument("--max-batches", type=int, default=4)
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    runtime = C60_RUNTIME
    seeds = seeds_module.load_c60()
    points = [p for p in read_jsonl(runtime / "branch_points.jsonl")
              if (not a.cases or p["case_id"] in a.cases) and (not a.points or p["point_id"] in a.points)]
    done = {r["point_id"] for r in read_jsonl(runtime / OUT_JUDGE)}
    todo = [p for p in points if p["point_id"] not in done]
    have = collections.Counter(r["point_id"] for r in read_jsonl(runtime / "branch_candidates.jsonl"))
    short = [p["point_id"] for p in todo if have[p["point_id"]] < a.batch_size]
    print(f"{len(points)} points, {len(done)} judged, {len(todo)} to do; "
          f"replies per point: min {min(have[p['point_id']] for p in todo) if todo else 0}, "
          f"max {max(have[p['point_id']] for p in todo) if todo else 0}", flush=True)
    if short:
        print(f"  WARNING {len(short)} points have fewer replies than one batch, e.g. {short[:3]}", flush=True)
    if a.dry_run or not todo:
        if todo:
            p = todo[0]; rows, _ = unique_candidates(runtime, p["point_id"])
            b = batches_for(rows, p["point_id"], a.batch_size)[0]
            pr = ranking_prompt(RUBRIC_PATH.read_text(encoding="utf-8"), p["prefix_messages"],
                                {L: r["text"] for L, r in zip(string.ascii_uppercase, b)})
            print(f"  first ranking prompt: {len(pr)} chars over {len(b)} candidates "
                  f"(v1 was ~17693 chars over 4); multi-turn scope present: {MULTITURN[:28]!r} in prompt = {MULTITURN in pr}")
        return

    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    sol = CodexSolClient(); sol.start()
    ctx = types.SimpleNamespace(sol=sol, glossary=Glossary.load())
    n = 0
    try:
        def run(p):
            ledger = CallLedger(runtime, "c60")
            return judge_point(ctx, ledger, p, seeds[p["case_id"]], rubric, a.batch_size, a.max_batches, runtime)
        with futures.ThreadPoolExecutor(a.workers) as ex:
            for out in ex.map(run, todo):
                append_jsonl(runtime / OUT_JUDGE, out)
                if out["pair"]:
                    append_jsonl(runtime / OUT_PAIRS, {"record": "pair32", **out["pair"], "case_id": out["case_id"],
                                                       "point_id": out["point_id"], "judge_version": JUDGE_VERSION,
                                                       "training_eligible": False, "created_utc": utcnow()})
                n += 1
                if n % 10 == 0:
                    print(f"  {n}/{len(todo)}", flush=True)
    finally:
        sol.close()
    rows = read_jsonl(runtime / OUT_JUDGE)
    res = collections.Counter(r["result"] for r in rows)
    calls = collections.Counter()
    for r in rows:
        calls.update(r["calls"])
    print(f"JUDGE32_DONE points {len(rows)} results {dict(res)} calls {dict(calls)}", flush=True)


if __name__ == "__main__":
    main()
