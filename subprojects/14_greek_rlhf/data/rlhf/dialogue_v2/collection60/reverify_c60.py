#!/usr/bin/env python3
"""Re-verify the pairs the c60 ranking judge proposed, with turn-scoped constraints (branch_verify_v2).

Verification v1 applied the whole task's requirements to every reply, so a reply that answered the latest user turn
correctly was failed for not re-delivering the original deliverable, and constraints addressed to an earlier reply
(word limits on the first reply) were checked against later ones. v2 hands the latest user turn and the reply index to
the evaluator, re-purposes the reference as facts for truth-checking rather than a completeness checklist, and returns a
three-valued verdict so the acceptance threshold can be changed later without spending another call.

Reads the recorded judgements; writes runtime/reverification_v2.jsonl. Nothing already on disk is modified: the v1
judgements, pairs and candidates stay as they are. Development rows, training_eligible=false. Resumable.
Usage: python3 data/rlhf/dialogue_v2/collection60/reverify_c60.py [--limit N] [--workers 24] [--dry-run]
"""
from __future__ import annotations

import argparse, concurrent.futures as futures, json, pathlib, sys, types
HERE = pathlib.Path(__file__).resolve().parent; DV2 = HERE.parent; sys.path.insert(0, str(DV2))
import branch, seeds as seeds_module                                              # noqa: E402
from clients import CodexSolClient                                                # noqa: E402
from common import C60_RUNTIME, append_jsonl, read_jsonl, utcnow                  # noqa: E402
from contracts import BRANCH_VERIFY_V2_SCHEMA, BRANCH_VERIFY_V2_VERSION, prompt_text  # noqa: E402
from glossary import Glossary                                                     # noqa: E402
from ledger import CallLedger                                                     # noqa: E402
from rollout import _sol                                                          # noqa: E402
from views import public_messages                                                 # noqa: E402

OUT = "reverification_v2.jsonl"
OUT_CAND = "candidate_verification_v2.jsonl"


def packet(point, judgement, cand_by_id, seed):
    prefix = public_messages(point["prefix_messages"])
    latest = next(m["content"] for m in reversed(prefix) if m["role"] == "user")
    ch, rj = cand_by_id[judgement["chosen"]], cand_by_id[judgement["rejected"]]
    return {"prefix": prefix,
            "latest_user_turn": latest,
            "assistant_reply_index": point["before_assistant_turn"],
            "CHOSEN": {"text": ch["text"], "computed_stats": branch._stats(ch["text"])},
            "REJECTED": {"text": rj["text"], "computed_stats": branch._stats(rj["text"])},
            "reference_facts": seed["evaluator_reference"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true", help="build the packets and print one prompt, call nothing")
    ap.add_argument("--mode", choices=["pairs", "candidates"], default="pairs",
                    help="pairs: re-verify the proposed winners. candidates: verify replies the ranking judge did NOT "
                         "make the winner, to measure how well ranking orders a field of replies and what the verified "
                         "acceptability rate really is (the reinforce rate is the ranker's opinion, not a measurement).")
    ap.add_argument("--sample-neutral", type=int, default=20)
    ap.add_argument("--sample-discourage", type=int, default=10)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    runtime = C60_RUNTIME
    seeds = seeds_module.load_c60()
    points = {p["point_id"]: p for p in read_jsonl(runtime / "branch_points.jsonl")}
    cands = {c["candidate_id"]: c for c in read_jsonl(runtime / "branch_candidates.jsonl")}
    proposed = [j for j in read_jsonl(runtime / "branch_judgements.jsonl") if j.get("chosen") and j.get("rejected")]
    done = {r["point_id"] for r in read_jsonl(runtime / OUT)}
    todo = [j for j in proposed if j["point_id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    if a.mode == "pairs":
        print(f"{len(proposed)} proposed pairs, {len(done)} already re-verified, {len(todo)} to do", flush=True)
        if not todo:
            return

    base = prompt_text("branch_verify_v2.txt")
    gl = Glossary.load()

    if a.mode == "candidates":
        import random
        judgements = {j["point_id"]: j for j in read_jsonl(runtime / "branch_judgements.jsonl")}
        already = {r["chosen"] for r in read_jsonl(runtime / OUT)}
        seen = {r["candidate_id"] for r in read_jsonl(runtime / OUT_CAND)}
        reinforce, by_verdict = [], {"neutral": [], "discourage": []}
        for pid, j in judgements.items():
            rk = j.get("ranking") or {}
            order = rk.get("ranking_candidate_ids") or []
            for cid, verd in (rk.get("verdicts") or {}).items():
                if cid in already or cid in seen:
                    continue
                rank_pos = order.index(cid) + 1 if cid in order else 0
                item = {"candidate_id": cid, "point_id": pid, "ranker_verdict": verd, "rank_position": rank_pos}
                (reinforce if verd == "reinforce" else by_verdict.get(verd, [])).append(item)
        rng = random.Random(a.seed)
        rng.shuffle(by_verdict["neutral"]); rng.shuffle(by_verdict["discourage"])
        todo_c = reinforce + by_verdict["neutral"][:a.sample_neutral] + by_verdict["discourage"][:a.sample_discourage]
        if a.limit:
            todo_c = todo_c[:a.limit]
        print(f"candidates: {len(reinforce)} unverified reinforce + "
              f"{len(by_verdict['neutral'][:a.sample_neutral])} neutral + "
              f"{len(by_verdict['discourage'][:a.sample_discourage])} discourage = {len(todo_c)} calls", flush=True)
        if not todo_c:
            return

        def comparator(item):
            """A fixed foil so the packet shape matches the pair pass exactly: the pair's rejected reply, or the
            lowest-ranked other candidate at that point. Only chosen_verdict is read from these rows."""
            j = judgements[item["point_id"]]
            if j.get("rejected") and j["rejected"] != item["candidate_id"]:
                return j["rejected"]
            order = (j.get("ranking") or {}).get("ranking_candidate_ids") or []
            return next(c for c in reversed(order) if c != item["candidate_id"])

        def build_c(item):
            point = points[item["point_id"]]
            j = dict(judgements[item["point_id"]], chosen=item["candidate_id"], rejected=comparator(item))
            pkt = packet(point, j, cands, seeds[j["case_id"]])
            return base + "\n\nPAIR PACKET (JSON):\n" + json.dumps(pkt, ensure_ascii=False, indent=1)

        if a.dry_run:
            print(f"first: {todo_c[0]} -> {len(build_c(todo_c[0]))} chars")
            print(f"mean packet chars: {sum(len(build_c(i)) for i in todo_c)/len(todo_c):.0f}")
            return

        sol = CodexSolClient(); sol.start()
        ctx = types.SimpleNamespace(sol=sol, glossary=gl)
        ledger = CallLedger(runtime, "c60")
        n = 0
        try:
            def run_c(item):
                v = _sol(ctx, ledger, f"sol:c60_verify2cand:{item['candidate_id']}", "branch_verification",
                         build_c(item), BRANCH_VERIFY_V2_SCHEMA, "medium",
                         {"candidate_id": item["candidate_id"], "branch_verify_version": BRANCH_VERIFY_V2_VERSION})
                return item, v
            with futures.ThreadPoolExecutor(a.workers) as ex:
                for item, v in ex.map(run_c, todo_c):
                    append_jsonl(runtime / OUT_CAND, {"record": "candidate_verification", **item,
                                                      "case_id": judgements[item["point_id"]]["case_id"],
                                                      "verification_v2": v, "training_eligible": False,
                                                      "experiment_credit": "development_demo", "created_utc": utcnow()})
                    n += 1
                    if n % 10 == 0:
                        print(f"  {n}/{len(todo_c)}", flush=True)
        finally:
            sol.close()
        print(f"CANDIDATE_VERIFY_DONE wrote {n} rows", flush=True)
        return

    def build(j):
        point = points[j["point_id"]]
        pkt = packet(point, j, cands, seeds[j["case_id"]])
        return base + "\n\nPAIR PACKET (JSON):\n" + json.dumps(pkt, ensure_ascii=False, indent=1)

    if a.dry_run:
        p = build(todo[0])
        print(f"--- {todo[0]['point_id']}: {len(p)} chars ---\n{p[:2500]}\n...")
        print(f"mean packet chars: {sum(len(build(j)) for j in todo)/len(todo):.0f}")
        return

    sol = CodexSolClient(); sol.start()
    ctx = types.SimpleNamespace(sol=sol, glossary=gl)
    ledger = CallLedger(runtime, "c60")
    written = 0
    try:
        def run_one(j):
            prompt = build(j)
            v = _sol(ctx, ledger, f"sol:c60_verify2:{j['point_id']}", "branch_verification", prompt,
                     BRANCH_VERIFY_V2_SCHEMA, "medium",
                     {"point_id": j["point_id"], "branch_verify_version": BRANCH_VERIFY_V2_VERSION})
            return j, v
        with futures.ThreadPoolExecutor(a.workers) as ex:
            for j, v in ex.map(run_one, todo):
                row = {"record": "reverification", "point_id": j["point_id"], "case_id": j["case_id"], "kind": j["kind"],
                       "chosen": j["chosen"], "rejected": j["rejected"],
                       "v1_result": j["result"], "v1_chosen_acceptable": (j.get("verification") or {}).get("chosen_acceptable"),
                       "verification_v2": v, "branch_verify_version": BRANCH_VERIFY_V2_VERSION,
                       "training_eligible": False, "experiment_credit": "development_demo", "created_utc": utcnow()}
                append_jsonl(runtime / OUT, row)
                written += 1
                if written % 10 == 0:
                    print(f"  {written}/{len(todo)}", flush=True)
    finally:
        sol.close()
    print(f"REVERIFY_DONE wrote {written} rows to {runtime / OUT}", flush=True)


if __name__ == "__main__":
    main()
