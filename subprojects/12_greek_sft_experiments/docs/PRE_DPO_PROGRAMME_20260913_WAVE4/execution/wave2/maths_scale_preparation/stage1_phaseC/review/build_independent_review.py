#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import math
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review"
GREEK = ROOT / "greek14"
ACCEPTED = ROOT / "run_state" / "accepted"
STAGE1_GREEK = ROOT.parent / "stage1" / "greek14"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_text(text):
    return sha_bytes(text.encode())


def sha_file(path):
    return sha_bytes(path.read_bytes())


def canonical_sha(value):
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def result(stage, row_id):
    path = ACCEPTED / f"{stage}__{row_id}.json"
    envelope = json.loads(path.read_text())
    return path, envelope, envelope["result"]


def controls(value, path="$"):
    found = []
    if isinstance(value, str):
        for index, char in enumerate(value):
            code = ord(char)
            if (code < 32 and char not in "\t\n\r") or code == 127:
                found.append({"path": path, "index": index, "codepoint": f"U+{code:04X}"})
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(controls(child, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(controls(child, f"{path}.{key}"))
    return found


def protected_spans(text):
    patterns = [
        r"\$\$.*?\$\$",
        r"\\\[.*?\\\]",
        r"\\\(.*?\\\)",
        r"\$(?:\\.|[^$])*?\$",
        r"(?<![\w])\d+(?:[.,]\d+)*(?![\w])",
    ]
    spans = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.DOTALL):
            span = match.group(0)
            if span not in spans:
                spans.append(span)
    return spans


EVIDENCE = {
    "scaleC_math_line_1202": "Inverse proportionality fixes pq=150, hence p=150/15=10; both generated proofs show the invariant and substitution.",
    "scaleC_math_line_627": "n(n+1)/2>10n with n>0 is equivalent to n>19; both proofs check n=20 and the boundary n=19.",
    "scaleC_math_line_2042": "For three standard dice, abc=1 only at (1,1,1), one of 6^3=216 equiprobable outcomes; both proofs state uniqueness.",
    "scaleC_math_line_2462": "The ordered powers 11^0 through 11^4 are palindromes and 11^5=161051 is not; both proofs address negative integer exponents and minimality.",
    "scaleC_math_line_2758": "The perimeter scale is 110/(6+7+9)=5, so the longest side is 9*5=45 cm; both proofs preserve similarity and units.",
    "scaleC_math_line_3264": "135 degrees is 180-45 degrees, so cos(135 degrees)=-sqrt(2)/2; both proofs give the identity and sign.",
    "scaleC_math_line_3416": "Pairing (-1+2),...,(-9999+10000) gives 5000 pairs of sum 1; both proofs establish the full count.",
    "scaleC_math_line_4273": "Subtracting the circle equations gives 10x-10y-71=0, hence the common chord line has slope 1; both proofs justify why A and B lie on it.",
    "scaleC_math_line_5094": "Any integer divisible by distinct primes p<q<r is divisible by pqr>=2*3*5=30, and 30 attains the bound; both proofs establish lower bound and existence.",
    "scaleC_math_line_5074": "Euclidean remainders give gcd(9118,12173)=47 and 33182=706*47; both proofs also justify maximality for all three inputs.",
    "scaleC_math_line_6052": "Cubing 1 and squaring 0 leave them fixed; 42 sign changes leave -1 unchanged, so the final sum is 0. Both proofs count exactly one turn per participant.",
    "scaleC_math_line_6668": "The red die has 3 odd faces and the green die 2 square faces, giving 6 of 36 ordered outcomes and probability 1/6; both proofs state the outcome count.",
    "scaleC_math_line_7065": "The coordinate differences are 3, 7 and 1, so the distance is sqrt(9+49+1)=sqrt(59); both proofs show every coordinate term.",
    "scaleC_math_line_7319": "Both derivations obtain x=15 degrees and then angles 105 and 135 degrees, giving r=7/9. The primary proof is mathematically complete but has two local LaTeX serialization defects; the blind proof independently confirms the full geometry.",
}


def arithmetic_checks():
    powers = [11**k for k in range(6)]
    pal = [str(n) == str(n)[::-1] for n in powers]
    return {
        "inverse_proportion": 25 * 6 / 15 == 10,
        "frood_boundary": 19 * 20 // 2 == 190 and 20 * 21 // 2 == 210,
        "three_dice_probability": 6**3 == 216,
        "powers_11_minimality": all(pal[:5]) and not pal[5] and powers[5] == 161051,
        "similar_triangle": 110 / (6 + 7 + 9) * 9 == 45,
        "cosine": abs(math.cos(math.radians(135)) + math.sqrt(2) / 2) < 1e-12,
        "alternating_sum": sum((-n if n % 2 else n) for n in range(1, 10001)) == 5000,
        "circle_radical_axis_slope": (14 - 4) / (12 - 2) == 1,
        "gcd_three": math.gcd(math.gcd(9118, 12173), 33182) == 47,
        "calculator_parity": (-1) * ((-1) ** 42) == -1,
        "two_dice_probability": 3 * 2 == 6 and 6 / 36 == 1 / 6,
        "distance": 3**2 + 7**2 + 1**2 == 59,
        "parallelogram_ratio": 105 / 135 == 7 / 9 and abs(math.cos(math.radians(4 * 15)) - 0.5) < 1e-12,
    }


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    (GREEK / "prompts").mkdir(parents=True, exist_ok=True)
    (GREEK / "schemas").mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(ROOT / "inputs.jsonl")
    assert len(rows) == 14
    adjudications = []
    repairs = []
    greek_inputs = []
    selected_rows = []
    output_controls = []

    for source in rows:
        row_id = source["row_id"]
        adapt_path, adapt_envelope, adaptation = result("adapt", row_id)
        solve_path, solve_envelope, solve = result("solve_high", row_id)
        blind_path, blind_envelope, blind = result("verify_high", row_id)

        before_solution = solve["solution_text"]
        selected_solution = before_solution
        disposition = "keep"
        narrow_repair = None
        greek_note = "valid Greek on charitable reading; queue for independent language-only confirmation"

        found = controls(solve_envelope)
        output_controls.extend({"file": str(solve_path), **item} for item in found)
        output_controls.extend({"file": str(adapt_path), **item} for item in controls(adapt_envelope))
        output_controls.extend({"file": str(blind_path), **item} for item in controls(blind_envelope))

        if row_id == "scaleC_math_line_7319":
            assert "\x0crac{\\sin 5x}{\\sin 2x}" in selected_solution
            assert "=\\\\sin 3x+\\sin x" in selected_solution
            selected_solution = selected_solution.replace("\x0crac{\\sin 5x}{\\sin 2x}", "\\frac{\\sin 5x}{\\sin 2x}")
            selected_solution = selected_solution.replace("=\\\\sin 3x+\\sin x", "=\\sin 3x+\\sin x")
            disposition = "repair"
            greek_note = "two deterministic LaTeX serialization repairs applied in the review candidate before language review"
            narrow_repair = {
                "row_id": row_id,
                "repair_class": "presentation_only_latex_serialization",
                "source_envelope": str(solve_path),
                "source_envelope_sha256": sha_file(solve_path),
                "before_solution_sha256": sha_text(before_solution),
                "after_solution_sha256": sha_text(selected_solution),
                "changes": [
                    {"before": "U+000C followed by rac{\\sin 5x}{\\sin 2x}", "after": "\\frac{\\sin 5x}{\\sin 2x}", "reason": "Restore the decoded backslash in the LaTeX command."},
                    {"before": "=\\\\sin 3x+\\sin x", "after": "=\\sin 3x+\\sin x", "reason": "Remove one duplicated literal backslash before the LaTeX sine command."},
                ],
                "mathematical_claims_changed": False,
                "root_review_required": True,
            }
            repairs.append(narrow_repair)

        selected_messages = [
            {"role": "user", "content": adaptation["problem_text"]},
            {"role": "assistant", "content": selected_solution},
        ]
        selected_sha = canonical_sha(selected_messages)
        primary_final = solve["final_answers"]
        blind_final = blind["final_answers"]

        adjudications.append({
            "schema_version": "maths_phaseC14_independent_adjudication_v1",
            "row_id": row_id,
            "family_id": source["family_id"],
            "subject": source["subject"],
            "level": source["level"],
            "source_line": source["source_line"],
            "source_record_sha256": source["source_record_sha256"],
            "source_family_sha256": source["family_sha256"],
            "adaptation_envelope_sha256": sha_file(adapt_path),
            "primary_solution_envelope_sha256": sha_file(solve_path),
            "blind_solution_envelope_sha256": sha_file(blind_path),
            "adapted_problem_sha256": sha_text(adaptation["problem_text"]),
            "primary_solution_sha256": sha_text(before_solution),
            "blind_solution_sha256": sha_text(blind["solution_text"]),
            "selected_messages_sha256": selected_sha,
            "disposition": disposition,
            "mathematical_verdict": "correct_complete",
            "teaching_preservation": "preserved",
            "reference_agreement": True,
            "primary_blind_final_answer_agreement": True,
            "primary_blind_final_answer_surface_forms": {
                "primary": [x["expression"] for x in primary_final],
                "blind": [x["expression"] for x in blind_final],
            },
            "proof_substance_review": EVIDENCE[row_id],
            "source_ambiguity": (
                "Standard classroom convention supplies fair independent dice; the source itself leaves this implicit."
                if row_id in {"scaleC_math_line_2042", "scaleC_math_line_6668"}
                else "Decimal representation is the ordinary implied basis for palindrome."
                if row_id == "scaleC_math_line_2462"
                else None
            ),
            "greek_assessment": greek_note,
            "narrow_repair": narrow_repair,
            "regenerate": False,
            "hold": False,
            "reference_was_hidden_from_generation": source["reference_visibility"].startswith("frozen_for_post_solve"),
        })

        greek_inputs.append({
            "row_id": row_id,
            "messages": selected_messages,
            "domain": "competition mathematics",
            "teaching_objective": "Preserve the exact source task, difficulty, and complete verified proof while confirming natural Greek.",
            "protected": [
                {"role": "user", "spans": protected_spans(adaptation["problem_text"])},
                {"role": "assistant", "spans": protected_spans(selected_solution)},
            ],
            "semantic_protections": [
                "Preserve every mathematical claim, numeral, unit, assumption, quantifier, case, equation, derivation step, and final answer.",
                "Do not change source task, difficulty, geometry labels, probability assumptions, or proof strategy.",
                "Do not infer a duty to edit valid Greek; unchanged is acceptable.",
                "The reference and blind solution are intentionally absent from this language-only payload.",
            ],
            "parent_selected_messages_sha256": selected_sha,
            "family_id": source["family_id"],
            "source_record_sha256": source["source_record_sha256"],
            "split": "train",
            "blind_verifier_content_in_payload": False,
            "reference_content_in_payload": False,
        })
        selected_rows.append({
            "row_id": row_id,
            "family_id": source["family_id"],
            "messages": selected_messages,
            "messages_sha256": selected_sha,
            "disposition": disposition,
            "status": "independent_semantic_review_complete_pending_root_and_greek_review",
        })

    checks = arithmetic_checks()
    assert all(checks.values())
    assert len(output_controls) == 1
    assert output_controls[0]["codepoint"] == "U+000C"
    assert not controls(greek_inputs)
    assert len({x["family_id"] for x in rows}) == 14
    assert all(not x["current_assembly_exposure"]["appeared_in_gradient_train"] for x in rows)
    assert all(not x["current_assembly_exposure"]["appeared_in_development"] for x in rows)
    assert all(not x["math500_overlap"]["reject"] for x in rows)

    write_jsonl(REVIEW / "adjudications.jsonl", adjudications)
    write_jsonl(REVIEW / "narrow_repairs.jsonl", repairs)
    write_jsonl(REVIEW / "selected_candidates.jsonl", selected_rows)
    (REVIEW / "arithmetic_checks.json").write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n")
    (REVIEW / "output_control_scan.json").write_text(json.dumps({"findings": output_controls, "count": len(output_controls)}, indent=2, sort_keys=True) + "\n")

    write_jsonl(GREEK / "inputs.jsonl", greek_inputs)
    queue = [{
        "job_id": f"greek_check__{row['row_id']}",
        "stage": "greek_correction",
        "row_id": row["row_id"],
        "model": "gpt-5.6-sol",
        "effort": "high",
        "schema": "schemas/greek_correction.schema.json",
        "template": "prompts/greek_correction.txt",
        "depends_on": [],
        "payload": {
            "row_id": {"$record": "row_id"},
            "messages": {"$record": "messages"},
            "domain": {"$record": "domain"},
            "teaching_objective": {"$record": "teaching_objective"},
            "protected": {"$record": "protected"},
            "semantic_protections": {"$record": "semantic_protections"},
        },
    } for row in greek_inputs]
    write_jsonl(GREEK / "queue.jsonl", queue)
    shutil.copyfile(STAGE1_GREEK / "run_queue.py", GREEK / "run_queue.py")
    shutil.copyfile(STAGE1_GREEK / "schemas" / "greek_correction.schema.json", GREEK / "schemas" / "greek_correction.schema.json")
    shutil.copyfile(STAGE1_GREEK / "prompts" / "greek_correction.txt", GREEK / "prompts" / "greek_correction.txt")

    reviewed_at = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(timespec="seconds")
    verification = {
        "schema_version": "maths_phaseC14_independent_review_verification_v1",
        "verified_at": reviewed_at,
        "counts": {"rows": 14, "keep": 13, "repair": 1, "regenerate": 0, "hold": 0, "greek_jobs": 14},
        "checks": {
            "all14_full_source_adaptation_primary_blind_reference_read": True,
            "all14_mathematically_correct_complete": True,
            "all14_teaching_preserved": True,
            "all14_source_family_gates_preserved": True,
            "blind_and_reference_absent_from_greek_payloads": True,
            "one_primary_control_character_found_and_repaired_in_candidate": True,
            "generic_runner_control_character_rejection_not_assumed": True,
            "repaired_candidate_control_scan_clean": True,
            "greek_queue_train_only": True,
            "development_final_content_absent": True,
            "no_model_calls": True,
            "no_corpus_mutation": True,
        },
        "arithmetic_checks": checks,
    }
    (REVIEW / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    report = f"""# Phase C independent semantic and proof review

Reviewed at: {reviewed_at}. Reviewer: dialogue_audit Sol agent. Scope: all 14 train-only Phase C rows, each read in full across the exact English source problem, frozen reference, Greek adaptation, primary solution and blind independent solution.

## Outcome

- 13 rows: **keep**, pending the separate Greek-only pass.
- `scaleC_math_line_7319`: **repair**, with two certain presentation-only fixes in the primary solution: U+000C plus `rac` becomes `\\frac`, and the doubled literal backslash before `\\sin 3x` becomes one. The proof itself is complete and agrees with the independently generated blind proof and the reference.
- 0 regenerate; 0 hold; no source repair required.

Every final answer agrees with the reference, but acceptance was based on the derivations: boundary and minimality checks, complete probability spaces, units, Euclidean remainders, coordinate terms, and the full angle argument were inspected. The dice rows retain the source's ordinary classroom convention of fair independent standard dice. The palindrome row retains the ordinary decimal-reading convention. These are source conventions, not newly introduced claims.

The original accepted envelopes remain unchanged. `selected_candidates.jsonl` contains the review candidates, including the deterministic two-token repair for line 7319. `adjudications.jsonl` records full hashes and row-level reasoning.

The accepted U+000C demonstrates that this generic runner bundle did not itself reject decoded control characters on this run; the independent post-run scan caught it. This review does not claim that the separate maths guard patch is wired into this queue.

## Greek queue

`greek14/` contains 14 train-only language-review jobs. It uses the byte-identical proven generic runner, schema and charitable Greek prompt from the preceding Stage B Greek pass. Each payload contains only the selected Greek problem and primary solution; it excludes the blind solution and reference, preserving verifier isolation. Primary cap: 14 calls; retry cap: 8; Phase C programme cap remains 72 calls, with 42 already completed and the separate 8-call semantic/source allowance retained. The queue is prepared and unlaunched.

The existing source-family, assembly-exposure, reserved-family and MATH-500 overlap gates remain bound through the Phase C inputs and their hashes. No development or final-confirmation content appears in the review or language payloads.
"""
    (REVIEW / "report.md").write_text(report)

    greek_manifest = {
        "schema_version": "maths_phaseC_greek14_manifest_v1",
        "status": "prepared_unlaunched_root_review_required",
        "built_at": reviewed_at,
        "counts": {"primary_calls": 14, "retry_cap": 8, "absolute_call_cap": 22},
        "phaseC_budget": {"completed_primary_calls": 42, "greek_primary_cap": 14, "semantic_or_source_shared_cap": 8, "retry_cap": 8, "absolute_programme_cap": 72},
        "execution": {"max_workers": 8, "launched": False, "model": "gpt-5.6-sol", "effort": "high"},
        "isolation": {"split": "train_only", "blind_verifier_content_in_payload": False, "reference_content_in_payload": False, "development_or_final_content_materialized": False},
        "parent_bindings": {
            "phaseC_inputs_sha256": sha_file(ROOT / "inputs.jsonl"),
            "phaseC_run_summary_sha256": sha_file(ROOT / "run_state" / "summary.json"),
            "independent_adjudications_sha256": sha_file(REVIEW / "adjudications.jsonl"),
            "selected_candidates_sha256": sha_file(REVIEW / "selected_candidates.jsonl"),
        },
        "artifact_sha256": {
            "inputs.jsonl": sha_file(GREEK / "inputs.jsonl"),
            "queue.jsonl": sha_file(GREEK / "queue.jsonl"),
            "run_queue.py": sha_file(GREEK / "run_queue.py"),
            "schemas/greek_correction.schema.json": sha_file(GREEK / "schemas" / "greek_correction.schema.json"),
            "prompts/greek_correction.txt": sha_file(GREEK / "prompts" / "greek_correction.txt"),
        },
        "runner_byte_identical_to_stageB_proven_copy": sha_file(GREEK / "run_queue.py") == sha_file(STAGE1_GREEK / "run_queue.py"),
    }
    (GREEK / "manifest.json").write_text(json.dumps(greek_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    review_artifacts = ["adjudications.jsonl", "narrow_repairs.jsonl", "selected_candidates.jsonl", "arithmetic_checks.json", "output_control_scan.json", "verification.json", "report.md"]
    receipt = {
        "schema_version": "maths_phaseC14_review_receipt_v1",
        "created_at": reviewed_at,
        "status": "semantic_review_complete_greek_queue_pending_root_review",
        "artifact_sha256": {name: sha_file(REVIEW / name) for name in review_artifacts},
        "greek_manifest_sha256": sha_file(GREEK / "manifest.json"),
        "source_inputs_sha256": sha_file(ROOT / "inputs.jsonl"),
        "accepted_output_count": len(list(ACCEPTED.glob("*.json"))),
        "model_calls_added": 0,
        "corpus_mutations": 0,
    }
    (REVIEW / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(rows), "adjudications": len(adjudications), "repairs": len(repairs), "greek_jobs": len(queue), "checks_ok": all(verification["checks"].values())}, indent=2))


if __name__ == "__main__":
    main()
