"""Stage A: baseline and run manifest (no target-model generation)."""
from __future__ import annotations

import json
import subprocess
import sys
from difflib import SequenceMatcher
from typing import Any

from common import (GLOSSARY_PATH, HERE, PILOT_RUNTIME, RGD_RUNTIME, RLHF, SUBPROJECT, V2_RUNTIME, atomic_json,
                    read_json, read_jsonl, sha256_file, utcnow)
from contracts import (DEV_TAGS, MAX_ASSISTANT_TURNS, MODEL_ID, MODEL_REVISION, MODEL_SHA256, PROTOCOL_VERSION,
                       SAMPLING, SERVED_CONTEXT, component_versions)
from ledger import programme_summary

QUOTA_POINTERS = [
    "data/rlhf/target_distribution_v1.json",
    "data/rlhf/pool/inventory.jsonl",
    "data/rlhf/pool/inventory_summary.json",
    "data/rlhf/pool/round1_all.jsonl",
    "data/rlhf/pool/round2_all.jsonl",
    "data/rlhf/dialogue_quality_depth/runtime/manifest.json",
    "data/rlhf/dialogue_quality_depth/runtime/measurement/preferences.jsonl",
    "docs/RLHF_COORDINATION/CURRENT_VERSIONS.md",
]


def quota_snapshot() -> dict[str, Any]:
    out = {}
    for rel in QUOTA_POINTERS:
        path = SUBPROJECT / rel
        if path.exists():
            entry = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            if path.suffix == ".jsonl":
                entry["rows"] = sum(1 for line in path.open(encoding="utf-8") if line.strip())
            out[rel] = entry
        else:
            out[rel] = {"missing": True}
    return out


def me021_reproduction() -> dict[str, Any]:
    rows = [r for r in read_jsonl(PILOT_RUNTIME / "measurement" / "trajectories.jsonl") if r["trajectory_id"] == "ME021"]
    latest = rows[-1]
    messages = latest["messages"]
    assistants = [m["content"] for m in messages if m["role"] == "assistant"]
    users = [m["content"] for m in messages if m["role"] == "user"]
    similarity = [round(SequenceMatcher(None, assistants[i - 1], assistants[i]).ratio(), 3) for i in range(1, len(assistants))]
    annotations = [r for r in read_jsonl(PILOT_RUNTIME / "measurement" / "annotations.jsonl") if r["trajectory_id"] == "ME021"]
    return {
        "snapshots_in_append_only_log": len(rows), "used": "latest snapshot (not the first line)",
        "assistant_turns": latest["assistant_turns"], "terminal_code": latest["terminal_code"],
        "terminal_detail_excerpt": (latest.get("terminal_detail") or "")[:320],
        "context_arithmetic": "2,597 prompt tokens + 1,500 reserved output tokens = 4,097 > 4,096 served context: the sixth reply was never generated",
        "user_turn_readings": [
            {"user_turn": 2, "reading": "restatement of the dialogue requirement (no new information)"},
            {"user_turn": 3, "reading": "points to the defect (significance still narrated, not shown in dialogue); asks for an entirely new version"},
            {"user_turn": 4, "reading": "adds an exclusion: drop the manor and the old plot"},
            {"user_turn": 5, "reading": "repeats the exclusion with explicit banned words (manor, mansion, father, hidden passage)"},
            {"user_turn": 6, "reading": "first concrete alternative: a second character explains that the map records rare plants to be saved before demolition"}],
        "user_turn_6_excerpt": users[5][:400] if len(users) > 5 else None,
        "assistant_consecutive_similarity": similarity,
        "pilot_annotation_quality_by_turn": [(a["turn_index"], a["local_quality"]) for a in annotations],
        "finding": ("Reproduced: repeated requests and exclusions for four user turns, useful concrete detail only at user turn 6, "
                    "and the next assistant call stopped by the context reservation. That unobserved reply is not a model failure."),
    }


def active_pods() -> dict[str, Any]:
    proc = subprocess.run([sys.executable, str(HERE / "pod" / "dv2_provision.py"), "pods"], capture_output=True, text=True, timeout=120)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}"
    try:
        return {"checked_utc": utcnow(), **json.loads(line)}
    except json.JSONDecodeError:
        return {"checked_utc": utcnow(), "error": proc.stdout[-300:] + proc.stderr[-300:]}


def build_baseline() -> dict[str, Any]:
    hub = read_json(V2_RUNTIME / "hub_identity_check.json") if (V2_RUNTIME / "hub_identity_check.json").exists() else {}
    pilot_calls = [r for r in read_jsonl(PILOT_RUNTIME / "ledger.jsonl") if r.get("record") == "call_reserved"]
    baseline = {
        "created_utc": utcnow(), "stage": "A", "protocol_version": PROTOCOL_VERSION, **DEV_TAGS,
        "model_identity": {
            "alias": "G4F6P1", "hub_repo": MODEL_ID, "hub_revision_pinned": MODEL_REVISION,
            "expected_model_safetensors_sha256": MODEL_SHA256,
            "hub_api_lfs_sha256_now": (hub.get("files", {}).get("model.safetensors") or {}).get("lfs_sha256"),
            "hub_revision_now": hub.get("sha_revision"),
            "prior_serving_evidence": ["pilot pod logs DQP_MODEL_SHA_OK on 3 sessions (2026-09-16 18:14Z, 18:57Z, 21:57Z)",
                                       "round 2 pod sha256 match (logs/prime_round2.log 17:58Z)"],
            "serving_verification_this_run": "dv2_pod_setup.sh downloads the pinned revision and refuses to serve unless sha256(model.safetensors) matches",
            "served_context_tokens": SERVED_CONTEXT,
            "chat_template_overhead_tokens": "prompt_tokens = content tokens + 59 + 2 x messages (measured on 126 pilot replies)"},
        "me021": me021_reproduction(),
        "first_experiment_quota_pointers_sha256": quota_snapshot(),
        "quota_rule": "development rows never decrement these; the same hashes are re-checked before the review package",
        "prime_intellect": {"programme": programme_summary(), "provider_state": active_pods()},
        "sol": {"pilot_calls_recorded": len(pilot_calls), "cap_for_this_work": "none (owner, 17 Sept); every call recorded",
                "access": "data/math/codex_server.py, gpt-5.6-sol, codex-cli 0.154.0", "astra": "not used"},
        "glossary": {"path": str(GLOSSARY_PATH.relative_to(SUBPROJECT)), "sha16_at_stage_a": sha256_file(GLOSSARY_PATH)[:16],
                     "sha16_in_brief": "84b30fabd02a15cc", "note": "the glossary was re-synced to spec v0.5 during the run; each call records the sha16 it read"},
        "coordination": {"other_executor_active_files_in_owned_paths": [],
                         "board_state": "orchestrator (Fable) owns prompt generation PG1-PG6 and CURRENT_VERSIONS.md rows other than dialogue v2; no other executor writes data/rlhf/dialogue_v2 or reference_guided_dialogue_demo"},
        "sampling_baseline": {"pilot": {"temperature": 0.8, "top_p": 0.95, "max_tokens": 1500, "n": 1, "system_prompt": None},
                              "this_run": {**SAMPLING, "system_prompt": None},
                              "change": "max_tokens 1500 -> 1024 for every D1/D2 reply and branch candidate (context fit); recorded as dv2-sampling-v1"},
        "versions": component_versions(),
    }
    atomic_json(V2_RUNTIME / "baseline.json", baseline)
    return baseline


def build_run_manifest() -> dict[str, Any]:
    d2 = read_json(RLHF / "reference_guided_dialogue_demo" / "seeds" / "rgd_seeds.json")["seeds"]
    d1_specs = read_json(HERE / "seeds" / "dvi_seed_specs.json")["seeds"]
    cases = [{"case_id": s["case_id"], "run": "D1", "kind": s["d1_kind"], "language": s["language"],
              "labels": s["labels"], "source_family": f"dvi:{s['case_id']}"} for s in d1_specs]
    cases += [{"case_id": s["case_id"], "run": "D2", "kind": s["category"], "language": s["language"],
               "labels": s["labels"], "source_family": s["source_family"], "maths_content": s.get("maths_content", False)}
              for s in d2]
    manifest = {
        "created_utc": utcnow(), "protocol_version": PROTOCOL_VERSION, "generator_version": "0.3-dev", **DEV_TAGS,
        "cases": cases,
        "counts": {"D1": 4, "D2": 6, "D1_languages": {"el": 3, "en": 1}, "D2_languages": {"el": 4, "en": 2},
                   "D2_categories": {"writing": 2, "troubleshooting": 2, "learning": 2}},
        "source_family_reservation": "dvi:* and rgd:* families are development-only, reserved from formal evaluation; later variants stay on the development side",
        "model": {"alias": "G4F6P1", "repo": MODEL_ID, "revision": MODEL_REVISION, "sha256": MODEL_SHA256},
        "sampling": SAMPLING, "max_assistant_turns": MAX_ASSISTANT_TURNS,
        "bounds": {"D1_raw_replies_max": 24, "D2_raw_replies_max": 36, "D1_branch_replies_max": 64,
                   "branch_points_per_D1_conversation_max": 2, "candidates_per_point": "4 judged first, up to 8"},
        "budgets": {"prime_intellect_total_cap_eur": 5.0, "operational_stop_eur": 4.0, "reserve_eur": 1.0,
                    "sol": "no call cap (owner, 17 Sept); all calls recorded"},
        "outputs": {"D1": str(V2_RUNTIME.relative_to(SUBPROJECT)), "D2": str(RGD_RUNTIME.relative_to(SUBPROJECT)),
                    "review": "data/rlhf/dialogue_v2/review/", "gpu_ledger": "data/rlhf/dialogue_v2/runtime/gpu_ledger.jsonl"},
        "no_training": True, "no_pool_import": True,
    }
    atomic_json(V2_RUNTIME / "run_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    b = build_baseline()
    m = build_run_manifest()
    print(json.dumps({"baseline": "ok", "me021": b["me021"]["finding"], "pods": b["prime_intellect"]["provider_state"],
                      "programme_spent_eur": b["prime_intellect"]["programme"]["programme_spent_eur"], "cases": len(m["cases"])}, ensure_ascii=False))
