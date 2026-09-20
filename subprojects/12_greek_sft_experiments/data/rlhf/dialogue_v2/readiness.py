"""Stage C readiness record: offline gate tests, dry-run evidence, reviewer verdict, versions (plan §7)."""
from __future__ import annotations

import io
import json
import sys
import unittest
from collections import Counter
from typing import Any

from common import HERE, V2_RUNTIME, atomic_json, atomic_text, read_jsonl, utcnow
from contracts import component_versions
from glossary import Glossary

GATE_TESTS = {
    "1 role views cannot leak hidden diagnosis or gold transfer answers": ["Gate1AccessSeparation", "Gate1ResolverReasonNeverReachesUser"],
    "2 revealed observations remain consistent": ["Gate2WorldConsistency"],
    "3 hidden writing preference is not an earlier instruction": ["Gate3HiddenPreferences"],
    "4 adaptive user can finish, help, change strategy or abandon": ["Gate4AdaptiveUser"],
    "5 ME021 history permits a concrete example without reference leak": ["Gate5ME021"],
    "6 prevention/recovery boundaries and identical pair prefix hashes": ["Gate6PrefixBoundaries"],
    "7 context overflow distinct from model failure, no trimming": ["Gate7ContextOverflow"],
    "8 development outputs excluded from counters and automatic import": ["Gate8DevelopmentOnly"],
    "9 resumption without duplicate charged calls; no blind retry": ["Gate9Resumption", "Gate9SolFailureRetry"],
    "10 completion-only export; trainer integration unverified": ["Gate10CompletionOnlyExport"],
    "pod runner: trap, teardown, gate before provisioning, secrets": ["PodRunnerOffline"],
}


def run_tests() -> dict[str, Any]:
    sys.path.insert(0, str(HERE))
    import test_dialogue_v2 as module
    out: dict[str, Any] = {}
    for gate, classes in GATE_TESTS.items():
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, c)) for c in classes)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
        out[gate] = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                     "status": "pass" if result.wasSuccessful() else "fail",
                     "detail": [str(t[1])[-400:] for t in result.failures + result.errors]}
    return out


def dry_run_summary() -> dict[str, Any]:
    rows = read_jsonl(V2_RUNTIME / "dryrun" / "dvi" / "user_turns.jsonl") + read_jsonl(V2_RUNTIME / "dryrun" / "rgd" / "user_turns.jsonl")
    decisions = [r for r in rows if r.get("mode") in {"next_turn", "final_assessment"}]
    events = read_jsonl(V2_RUNTIME / "dryrun" / "rgd" / "world_events.jsonl")
    return {"note": "real Sol user/world/learner calls against hand-written stand-in replies (not Apertus, not data), 2 turns per case",
            "decisions": len(decisions), "moves": dict(Counter(r["move"] for r in decisions)),
            "repairs": sum(bool(r.get("repair_used")) for r in decisions),
            "policy_deviations": sum(bool(r.get("policy_violations_after_repair")) for r in decisions),
            "revealed_private_preferences": {r["row_id"]: r["revealed_private_preference_ids"] for r in decisions if r.get("revealed_private_preference_ids")},
            "resolver_mappings": [(o["action"][:70], o["check_id"], o["status"]) for e in events for o in e["observations"]],
            "manual_inspection": [
                "RGD003 user view after the network report contains the revealed SSID only as an observation; no root cause or hidden fact.",
                "RGD004 user reported exact simulated outputs; the resolver mapped all three actions to supported checks.",
                "RGD005 learner updates carried verbatim evidence quotes; the transfer attempt followed the grouping explanation given.",
                "RGD001/RGD002 revealed private preferences as new preferences (changes_task=true, ids P1/P2 and P2/P3).",
                "DVI003 pointed to the six-bullet defect precisely; DVI002 named both clashes; no manufactured failure on DVI004.",
                "Label noise observed: RGD003 reporting requested observations was labelled continue; user_policy_v2 now states that this is clarify."]}


def build(reviewer: dict[str, Any] | None = None) -> dict[str, Any]:
    gates = run_tests()
    record = {"created_utc": utcnow(), "stage": "C", "gates": gates, "all_offline_gates_pass": all(g["status"] == "pass" for g in gates.values()),
              "dry_run": dry_run_summary(), "independent_review": reviewer or {"status": "not recorded"},
              "glossary_sha16": Glossary.load().sha16, "versions": component_versions()}
    atomic_json(V2_RUNTIME / "readiness.json", record)
    lines = ["# Dialogue v2 readiness report (Stage C)", "", f"Created {record['created_utc']}. Protocol dialogue-v2-dev-0.1, generator 0.3-dev.", "",
             "| Gate | Tests | Status |", "|---|---|---|"]
    lines += [f"| {gate} | {g['tests']} | {g['status']} |" for gate, g in gates.items()]
    lines += ["", f"All offline gates pass: {record['all_offline_gates_pass']}.", "",
              "Trainer integration: no DPO trainer exists in the repository, so tokenized-mask inspection is not possible; exports state completion-only loss and mark trainer integration unverified.", "",
              "## Dry run", "", json.dumps(record["dry_run"], ensure_ascii=False, indent=1), "",
              "## Independent review", "", json.dumps(record["independent_review"], ensure_ascii=False, indent=1), ""]
    atomic_text(V2_RUNTIME / "readiness_report.md", "\n".join(lines))
    return {"all_offline_gates_pass": record["all_offline_gates_pass"], "gates": {k: v["status"] for k, v in gates.items()}}


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
