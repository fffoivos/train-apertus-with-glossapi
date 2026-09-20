#!/usr/bin/env python3
"""Freeze the independent full-row review of the twenty IF v3 candidates."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
SOURCE = V3 / "candidates.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = [json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
assert len(rows) == 20 and len({row["row_id"] for row in rows}) == 20

DECISIONS = {
    "mixa_2026_06155": ("keep", "faithful_repair", "complete", "none_observed", "The impossible accent-dependent πότε/ποτέ device is replaced by an accent-independent time-flight/return joke. The atonic output remains wholly inside Greek quotation marks and still performs the birthday-wish task."),
    "mixa_2028_05110": ("keep", "faithful_repair", "complete", "none_observed", "The conflicting ending is replaced at prompt level, the obsolete contradiction preface is removed, and the five-step anti-fraud answer is useful and obeys both surviving constraints."),
    "mixa_2028_03200": ("repair_candidate", "narrow_factual_wording_issue", "complete", "official source review supports availability and a mailed cheek-swab kit", "Dating the scenario and avoiding an unproved claim about last year's history are good repairs. However, the response says the recipient will receive an envelope 'with the application and instructions for the oral swab', while the recorded source finding supports an application followed by a mailed cheek-swab kit. Say 'θα λάβεις κιτ στοματικού επιχρίσματος με οδηγίες' so the training answer matches the verified procedure."),
    "mixa_2028_08593": ("keep", "faithful_repair", "complete_with_device_specific_boundary", "official source review supports default port/read protocol; device details are expressly deferred to its manual", "The repaired prompt resolves the wrapper/end conflict. The answer does not assume a management port or universal IP method, distinguishes ping from service reachability, and ties registers, scaling, byte order, Unit ID, and port to the actual device configuration."),
    "mixa_2027_09179": ("keep", "faithful_repair", "complete", "none_observed", "The summary removes invented gender, mental pressure, and speculation while preserving every material fact in the supplied note. Three highlighted spans and three natural ψ occurrences survive."),
    "mixa_2026_08572": ("keep", "faithful_repair", "complete", "none_observed", "Reducing the incompatible 300-word minimum restores a single faithful English translation. The names, place, amount, purposes, partnership, and later hosting possibility all survive without padding."),
    "mixa_2027_09553": ("keep", "faithful_repair", "complete", "none_observed", "The 120-word maximum fits the summarization task. The response retains public-system terms, exclusions, one card per student, and the temporary replacement certificate while meeting the ψ constraint naturally."),
    "mixa_2027_09689": ("keep", "faithful_repair", "complete", "official source review supports the public/private distinction and hospital escalation", "The three uppercase sentences give a conditional choice, reasons, private-payment boundary, and a separate emergency hospital route for breathing, swallowing, or major-swelling symptoms. The repair does not promise private appointment speed."),
    "mixa_2027_10080": ("keep", "faithful_orthography_repair", "complete", "general ergonomic effects are stated conditionally", "Restoring ordinary monotonic accents is exactly the requested orthographic repair. The practical comparison remains conditional and asks for the worker's input rather than replacing medical guidance."),
    "mixa_2026_04027": ("keep", "faithful_repair", "complete", "none_observed", "Replacing the unrelated EOPYY mention with KTEL Larissas removes padding while preserving all five operative constraints and the Piraeus–Larissa–Elassona travel sequence."),
    "mixa_2026_05543": ("keep_candidate_repair_metadata", "candidate_row_faithful_metadata_stale", "complete", "none_observed", "The v3 user instruction now explicitly chooses accent-insensitive lexical identity, displays standard επιλογή, and the response contains it twice while paragraph two starts with Τελικά. The candidate is sound, but the top-level constraint_mapping, expected_result, changes, issues, and semantic_read still describe the earlier unresolved protocol and should be regenerated to match root_revision."),
    "mixa_2026_07006": ("keep", "source_faithful", "complete", "none_observed", "The corrected bank message preserves the suspected ticket-payment facts and asks about stopping the charge and required documents. It is valid JSON and satisfies the orthographic and lexical devices."),
    "mixa_2027_05368": ("keep", "source_faithful", "complete", "cost is treated as a quotation constraint rather than a guaranteed market fact", "The comparison addresses weight, access, power failure, exit, maintenance, children, and the 1,500-euro ceiling. Asking for an inclusive quote avoids inventing a current installed price."),
    "mixa_2026_06199": ("keep_with_source_gate", "source_faithful", "complete", "named EODY and Civil Protection attributions were not independently source-checked in this review", "The answer directly addresses the supplied 39°C outdoor practice, gives a clear safer alternative and emergency symptoms, and satisfies the two-highlight device. Keep the row, but verify the exact linked attributions before promotion because they are external health claims."),
    "mixa_2026_04931": ("keep", "source_faithful", "complete", "none_observed", "This is an editing task rather than disposal advice: the response preserves all quantities and asks the agent for the lawful procedure and receipt. The forced paragraph start is satisfied without adding a legal claim."),
    "mixa_2026_11688": ("repair_response", "source_faithful", "semantically_incomplete_constraint_execution", "none_observed", "The arguments fairly cover equality and recognition of excellence, and the lexical/count constraints pass. But the two requested versions are not actually in politeness plural versus friendly singular: neither version addresses the reader in its specified person, and their register difference is weak. Reauthor the two versions with explicit second-person plural and singular framing while preserving the arguments and six ψ occurrences."),
    "mixa_2026_08647": ("keep", "source_faithful", "complete", "pharmacy availability is investigated rather than asserted", "The plan schedules exactly 12 calls and six visits over three field days, assigns two reporters, allocates exactly 90 euros, and reserves Thursday/Friday for synthesis and delivery. The exact start, wrapper, Greek numbering, and singular address survive."),
    "mixa_2027_09233": ("keep", "source_faithful", "complete", "the approximate pH range is a stable general claim but not externally checked here", "The response is fully lowercase, gives the ordinary approximate pH range of lemon juice, and correctly explains that dilution depends on amounts and water composition."),
    "mixa_2027_07834": ("keep", "faithful_source_checked_revision", "complete", "official source review supports the conditional misleading-presentation analysis and complaint route", "The legal application remains conditional, does not promise a refund, cites the relevant directive provisions, asks a question with the Greek question mark, and supplies more than three useful placeholders."),
    "mixa_2027_01564": ("keep", "source_faithful_creative_execution", "complete", "the scene avoids a numeric legal threshold; its date and personal details are fictional task content", "The scene preserves the three characters, 127 absences, possible repetition, school setting, meeting context, title, date, and exact ending. Invented illness/documents function as coherent fictional development rather than unsupported claims about the user."),
}

assert set(DECISIONS) == {row["row_id"] for row in rows}
out = []
for row in rows:
    verdict, fidelity, completeness, unsupported, finding = DECISIONS[row["row_id"]]
    candidate = row["candidate_row"]
    original = row["original_row"]
    out.append({
        "row_id": row["row_id"],
        "selection_class": row["selection_class"],
        "verdict": verdict,
        "source_fidelity": fidelity,
        "semantic_completeness": completeness,
        "unsupported_facts": unsupported,
        "constraints_preserved": verdict != "repair_response",
        "repair_introduced_new_defect": row["row_id"] == "mixa_2028_03200",
        "finding": finding,
        "source_row_sha256": row["source_identity"]["raw_row_sha256"],
        "original_content_sha256": hashlib.sha256(json.dumps({"user": original.get("user"), "assistant": original.get("assistant")}, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "candidate_content_sha256": hashlib.sha256(json.dumps({"user": candidate.get("user"), "assistant": candidate.get("assistant")}, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "v3_checker_all_pass": all(result.get("ok") for result in row["v3_checker_results"]),
    })

with (HERE / "adjudications.jsonl").open("w") as handle:
    for record in out:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

receipt = {
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "reviewer": "Sol agent",
    "reviewed_rows": len(out),
    "method": "independent full read of every original request/response and v3 candidate request/response plus constraints and recorded source checks",
    "additional_model_subprocess_calls": 0,
    "verdict_counts": dict(Counter(record["verdict"] for record in out)),
    "source_sha256": sha(SOURCE),
    "adjudications_sha256": sha(HERE / "adjudications.jsonl"),
    "checker_pass_all": all(record["v3_checker_all_pass"] for record in out),
}
(HERE / "verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
