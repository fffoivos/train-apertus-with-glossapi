#!/usr/bin/env python3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PRIOR = ROOT.parent
TARGETS = {
    "v4_H07_07": "deployment_and_closure_patch.jsonl",
    "v4_I00_05": "deployment_and_closure_patch.jsonl",
    "v4_I01_10": "deployment_and_closure_patch.jsonl",
    "F05_03": "world_fact_verification.jsonl",
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()]


def canon_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


deltas = {x["row_id"]: x for x in read_jsonl(ROOT / "root_deltas.jsonl")}
receipt = json.loads((ROOT / "receipt.json").read_text())
receipt_by_name = {Path(x["path"]).name: x for x in receipt["files"]}
current = {}
prior = {}
for row_id, name in TARGETS.items():
    current[row_id] = next(x for x in read_jsonl(ROOT / name) if x["row_id"] == row_id)
    prior[row_id] = next(x for x in read_jsonl(PRIOR / name) if x["row_id"] == row_id)

assessments = {
    "v4_H07_07": {
        "decision": "accept",
        "user_intent": "Close the exchange after saying the CV work will continue tomorrow.",
        "semantic_basis": "The last user turn is a farewell, not a request for a memory guarantee. The two-word answer is natural Greek and neither promises future recall nor adds an unsolicited persistence warning.",
        "deployment_claim_check": "No memory, persistence, session-visibility, release, or runtime-capability claim remains.",
        "precise_defect": None,
    },
    "v4_I00_05": {
        "decision": "accept",
        "user_intent": "Obtain defensible information for an article about conversation retention and training use.",
        "semantic_basis": "The answer identifies the provider privacy policy as the evidence source and supplies the relevant questions: storage, retention period, and training use. It removes unrelated checkpoint, licence, weights, and data-release assertions.",
        "deployment_claim_check": "It does not claim knowledge of the active provider's data handling; uncertainty is explicit and correctly provider-dependent.",
        "precise_defect": None,
    },
    "v4_I01_10": {
        "decision": "accept",
        "user_intent": "Offer a recipe photograph so its quantities can be scaled to eight people.",
        "semantic_basis": "The answer directly accepts the offer conditionally, provides a text fallback, and asks for the denominator needed to scale the recipe. It preserves the cooking task rather than merely discussing image support.",
        "deployment_claim_check": "Both image sending and readability are conditional on the application and observed rendering; no unsupported vision capability is asserted.",
        "precise_defect": None,
    },
    "F05_03": {
        "decision": "accept",
        "user_intent": "Understand why the user's landlord may have avoided a discussion of the Greek Civil War.",
        "semantic_basis": "The revision restores the exact relationship stated by the user (landlord), limits the personal explanation to a possibility, and preserves the previously sourced legal chronology and low-pressure conversational advice.",
        "deployment_claim_check": "No deployment-dependent claim is introduced. The correction removes the false implication that the landlord is the user's relative.",
        "precise_defect": None,
    },
}

rows = []
for row_id in TARGETS:
    delta = deltas[row_id]
    cur = current[row_id]
    old = prior[row_id]
    messages = cur["candidate_row"]["messages"]
    checks = {
        "prior_record_hash_matches_delta": canon_hash(old) == delta["before_candidate_sha256"],
        "candidate_messages_hash_matches_delta": canon_hash(messages) == delta["after_messages_sha256"],
        "delta_after_matches_last_assistant": messages[-1]["role"] == "assistant" and messages[-1]["content"] == delta["after"],
        "conversation_roles_valid": all(m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str) and m["content"] for m in messages),
        "no_c0_or_del": not any((ord(ch) < 32 and ch not in "\n\t\r") or ord(ch) == 127 for m in messages for ch in m["content"]),
    }
    rows.append({
        "row_id": row_id,
        "review_scope": "independent_full_conversation_root_delta_review",
        **assessments[row_id],
        "checks": checks,
        "candidate_messages_sha256": canon_hash(messages),
        "source_identity_preserved": cur.get("source_identity") == old.get("source_identity"),
        "historical_source_mutated": False,
    })

for item in receipt["files"]:
    path = ROOT / Path(item["path"]).name
    if file_hash(path) != item["sha256"]:
        raise SystemExit(f"receipt hash mismatch: {path}")
if any(not all(r["checks"].values()) for r in rows):
    raise SystemExit("delta integrity check failed")
if any(not r["source_identity_preserved"] for r in rows):
    raise SystemExit("source identity changed")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "adjudications.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))

report = """# Independent review of four root personality deltas

## Verdict

All four deltas are accepted after reading the complete conversation. No remaining defect was found in the revised final assistant turns. The review covers only the four changed rows; the 38 unchanged rows retain root's review status and were not independently re-adjudicated here.

| Row | Verdict | Full-context basis |
|---|---|---|
| `v4_H07_07` | Accept | The user closes with “τα λέμε”; “Τα λέμε αύριο.” is a natural farewell and makes no promise about memory or persistence. |
| `v4_I00_05` | Accept | The answer stays on the privacy question, points to the provider policy, and removes unsupported release, licence, weights, and dataset claims. |
| `v4_I01_10` | Accept | It answers the offer to send a recipe image, makes application support and readability conditional, and supplies a useful text fallback plus the scaling denominator. |
| `F05_03` | Accept | It correctly refers to the user's landlord rather than a relative, preserves bounded uncertainty about motive, and retains the source-grounded legal chronology. |

## Integrity checks

- Each previous candidate's canonical record hash matches `before_candidate_sha256` in `root_deltas.jsonl`.
- Each revised conversation's canonical message hash matches `after_messages_sha256`.
- Every delta's `after` text is exactly the final assistant message in the corresponding root candidate.
- Source-identity objects are unchanged from the prior candidate package.
- Both candidate files match the hashes recorded in `receipt.json`.
- The four conversations have valid nonempty user/assistant messages and no C0 or DEL control characters.

## Scope and disposition

This is an independent semantic and integrity review of the four root deltas, with no additional model subprocesses. It does not modify historical or production data. The four root revisions are ready to retain in the candidate package.
"""
(OUT / "REPORT.md").write_text(report)

artifacts = []
for name in ["adjudications.jsonl", "REPORT.md"]:
    p = OUT / name
    artifacts.append({"path": name, "sha256": file_hash(p), "bytes": p.stat().st_size})
manifest = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "scope": "four root personality deltas only",
    "accepted": 4,
    "held": 0,
    "rejected": 0,
    "unchanged_root_rows_not_independently_read": 38,
    "production_applied": False,
    "root_input_hashes": {
        "root_deltas.jsonl": file_hash(ROOT / "root_deltas.jsonl"),
        "deployment_and_closure_patch.jsonl": file_hash(ROOT / "deployment_and_closure_patch.jsonl"),
        "world_fact_verification.jsonl": file_hash(ROOT / "world_fact_verification.jsonl"),
        "receipt.json": file_hash(ROOT / "receipt.json"),
    },
    "artifacts": artifacts,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
