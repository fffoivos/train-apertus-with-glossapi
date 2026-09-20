#!/usr/bin/env python3
"""Format check before paid collection (amendment: batch further only after a format check). Runs a few collection seeds for
three assistant turns against a stand-in target that answers generically and without following instructions, so the
simulated user must perceive failures and the scheduled strategy change fires; then one combined review and the A/B point
rule. Real Sol calls at medium; writes only under collection60/runtime/dryrun/.
Usage: python3 data/rlhf/dialogue_v2/collection60/dryrun_c60.py [--cases C60C03 C60T01 C60L01] [--turns 3]"""
from __future__ import annotations

import argparse, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent; DV2 = HERE.parent; sys.path.insert(0, str(DV2))
import evaluate, points, rollout, seeds as seeds_module              # noqa: E402
from clients import CodexSolClient, FakeTargetClient, TargetResult    # noqa: E402
from contracts import MODEL_ID                                        # noqa: E402
from glossary import Glossary                                         # noqa: E402

STAND_IN = {
    "el": "Καλή ερώτηση. Υπάρχουν πολλοί παράγοντες που μπορεί να παίζουν ρόλο. Γενικά, καλό είναι να ελέγξετε τις βασικές ρυθμίσεις και να δοκιμάσετε ξανά αργότερα. Αν χρειάζεστε κάτι πιο συγκεκριμένο, πείτε μου.",
    "en": "Good question. Many factors can play a role here. In general it is a good idea to check the basic settings and try again later. Let me know if you need something more specific.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*", default=["C60C03", "C60T01", "C60L01"])
    ap.add_argument("--turns", type=int, default=3)
    a = ap.parse_args()
    seeds = seeds_module.load_c60()
    cases = [c for c in a.cases if c in seeds]

    def responder(messages):
        case = next(cid for cid in cases if seeds[cid]["opening"] == messages[0]["content"])
        text = STAND_IN.get(seeds[case]["language"], STAND_IN["en"])
        return TargetResult(text, "stop", "dry-run-stand-in", {"prompt_tokens": 300, "completion_tokens": 60}, 0.0)

    out = HERE / "runtime" / "dryrun"
    sol = CodexSolClient(); sol.start()
    try:
        ctx = rollout.Context(FakeTargetClient(responder, [MODEL_ID]), sol, Glossary.load(), "dry-run", dry_run=True,
                              runtime_override=out, horizon=a.turns)
        collected = rollout.collect(ctx, seeds, cases, max_workers=len(cases))
        reviewed = evaluate.review_combined(ctx, seeds, cases)
        pts = points.write_points_c60(seeds, cases, lambda cid: out / "c60")
    finally:
        sol.close()
    users = [json.loads(l) for l in open(out / "c60" / "user_turns.jsonl")] if (out / "c60" / "user_turns.jsonl").exists() else []
    print("DRYRUN_DONE", json.dumps({"collected": collected, "reviewed": reviewed, "points": pts,
                                     "user_moves": [(u["case_id"], u.get("user_turn_index"), u["move"], u.get("policy_violations_after_repair"), u.get("repair_used")) for u in users]},
                                    ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
