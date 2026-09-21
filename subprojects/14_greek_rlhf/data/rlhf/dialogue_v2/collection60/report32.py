#!/usr/bin/env python3
"""Read-out for the 32-reply run: pairs, the verified acceptability rate at scale, how far escalation had to go, and
what it cost in calls. Checks the outcome against what the 4-reply run predicted (20% of points yield a clean reply at
4 replies, 67% at 32, on a verified per-reply rate of 5.9%).
Usage: python3 data/rlhf/dialogue_v2/collection60/report32.py
"""
from __future__ import annotations

import collections, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent))
from common import C60_RUNTIME, read_jsonl  # noqa: E402

GROUP = {"C60C": "correction", "C60T": "troubleshooting", "C60L": "learning"}
group_of = lambda cid: GROUP[cid[:4]]


def main() -> None:
    rt = C60_RUNTIME
    rows = read_jsonl(rt / "branch_judgements_32.jsonl")
    pairs = read_jsonl(rt / "branch_pairs_32.jsonl")
    points = {p["point_id"]: p for p in read_jsonl(rt / "branch_points.jsonl")}
    if not rows:
        print("no judgements yet"); return

    print(f"points judged: {len(rows)} of {len(points)}")
    print("results:", dict(collections.Counter(r["result"] for r in rows)))
    print()

    t1 = [p for p in pairs if p["tier"] == 1]
    t2 = [p for p in pairs if p["tier"] == 2]
    print(f"TIER 1 pairs (clean winner, rejected meaningfully worse): {len(t1)}     [4-reply run gave 21]")
    print(f"TIER 2 pairs (winner better but imperfect):               {len(t2)}")
    for label, group in (("kind", lambda p: p["point_kind"]), ("group", lambda p: group_of(p["case_id"])),
                         ("single-turn material", lambda p: p.get("single_turn_material"))):
        print(f"  tier1 by {label}: {dict(collections.Counter(group(p) for p in t1))}")
    print(f"  minimal pairs (>0.80 similar): {sum(1 for p in t1 if p['minimal_pair'])} of {len(t1)} tier 1")
    print()

    # what the ranker and the verifier each saw across the whole field
    ranked = noms = verified = clean = 0
    for r in rows:
        for b in r["batches"]:
            ranked += len(b["verdicts"])
            noms += sum(1 for v in b["verdicts"].values() if v == "reinforce")
        verified += len(r["verifications"])
        clean += sum(1 for v in r["verifications"] if v["verdict"] == "clean")
    print(f"replies ranked: {ranked}   nominated reinforce: {noms} ({100*noms/max(ranked,1):.1f}%)"
          f"   [4-reply run: 13.2%]")
    print(f"nominations verified: {verified}   clean: {clean} ({100*clean/max(verified,1):.0f}% precision)"
          f"   [4-reply run: 45%]")
    print(f"implied verified clean rate per reply: {100*(noms/max(ranked,1))*(clean/max(verified,1)):.1f}%"
          f"   [4-reply run: 5.9%]")
    obs = sum(1 for r in rows if r["result"] == "pair_accepted") / len(rows)
    print(f"points yielding a clean pair: {100*obs:.1f}%   [predicted at 32 replies: 67%, at 4 replies: 20%]")
    print()

    used = collections.Counter(len(r["batches"]) for r in rows)
    print("batches of 8 needed per point:", dict(sorted(used.items())))
    print("  (a point stops at the first verified-clean reply; 4 batches means the whole field of 32 was judged)")
    calls = collections.Counter()
    for r in rows:
        calls.update(r["calls"])
    print(f"calls: ranking {calls['ranking']}, verification {calls['verification']}, total {sum(calls.values())}"
          f"   [forecast ~520]")
    vpos = collections.Counter(v["rank_position"] for r in rows for v in r["verifications"] if v["verdict"] == "clean")
    print("rank position of the clean reply, when one was found:", dict(sorted(vpos.items())))


if __name__ == "__main__":
    main()
