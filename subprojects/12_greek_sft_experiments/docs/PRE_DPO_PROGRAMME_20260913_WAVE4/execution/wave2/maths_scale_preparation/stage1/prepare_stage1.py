#!/usr/bin/env python3
"""Prepare phase-A adjudications and an unlaunched phase-B queue."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
REA = HERE.parents[5]
PROJECT = Path("/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments")
MATH = Path("/Users/foivoskarounos-zamparloukos/sft_annot/math_src/math_train.jsonl")
CUT2 = PROJECT / "data/math/cut2"
PILOT = REA / "outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot"
SPLITS = PARENT / "proposed_family_splits.jsonl"
INVENTORY = PARENT / "math7500_family_inventory.jsonl"
SELECTION_SEED = "phaseB-replacement-v1"
DIAGRAM = re.compile(r"(?i)\\begin\{asy\}|\[asy\]|\b(?:diagram|figure|pictured|shown below|as shown)\b")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_text(value: str) -> str:
    return sha_bytes(value.encode("utf-8"))


def canonical_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def record_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True))


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            if raw.strip():
                yield line_no, json.loads(raw)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pilot_norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text).lower()
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def controls(text: str) -> list[dict]:
    return [
        {"offset": i, "codepoint": f"U+{ord(c):04X}"}
        for i, c in enumerate(text)
        if (ord(c) < 32 and c not in "\t\n\r") or ord(c) == 127
    ]


split_rows = [row for _n, row in read_jsonl(SPLITS)]
inventory = [row for _n, row in read_jsonl(INVENTORY)]
inventory_by_id = {row["family_id"]: row for row in inventory}
math_rows = [row for _n, row in read_jsonl(MATH)]
used_family_ids = {row["family_id"] for row in split_rows}

# Preserve the earlier split and record narrow same-cell replacements for diagram-dependent phase-B sources.
phase_a = [x for x in split_rows if x["execution_phase"] == "A_existing_asset_full_review"]
phase_b_original = [x for x in split_rows if x["execution_phase"] == "B_source_generation_probe14"]
phase_b = []
selection_delta = []
for original in phase_b_original:
    source = math_rows[original["source_line"] - 1]
    if not DIAGRAM.search(source["problem"]):
        chosen = dict(original)
        chosen["selection_revision"] = "unchanged_from_proposed_family_splits"
        phase_b.append(chosen)
        continue
    pool = [
        x
        for x in inventory
        if x["family_id"] not in used_family_ids
        and x["subject"] == original["subject"]
        and x["level"] == original["level"]
        and not x["metadata_conflict"]
        and not x["current_assembly"]["appeared_in_gradient_train"]
        and not x["current_assembly"]["appeared_in_development"]
        and not x["current_assembly"]["assembly_excluded_rows"]
        and not x["pilot"]
        and not x["math500_gate"]["reject"]
        and not x["cut2"]["candidate_ids"]
        and not DIAGRAM.search(math_rows[x["canonical_source_line"] - 1]["problem"])
    ]
    pool.sort(key=lambda x: sha_text(f"{SELECTION_SEED}|{original['family_id']}|{x['family_id']}"))
    if not pool:
        raise RuntimeError(f"no same-cell text-only replacement for {original['family_id']}")
    replacement = pool[0]
    used_family_ids.add(replacement["family_id"])
    chosen = {
        "family_id": replacement["family_id"],
        "family_sha256": replacement["family_sha256"],
        "source_line": replacement["canonical_source_line"],
        "subject": replacement["subject"],
        "level": replacement["level"],
        "lane": "train_stage1",
        "execution_phase": "B_source_generation_probe14",
        "cut2_candidate_ids": [],
        "old_greek_asset_status": "not_in_cut2_candidate_set",
        "source_text_in_manifest": False,
        "selection_revision": "same_cell_text_only_replacement",
        "replaces_family_id": original["family_id"],
        "replaces_source_line": original["source_line"],
    }
    phase_b.append(chosen)
    selection_delta.append(
        {
            "reason": "diagram_or_figure_dependency_rejected_by_existing_pilot_gate",
            "old": {k: original[k] for k in ("family_id", "family_sha256", "source_line", "subject", "level")},
            "new": {k: chosen[k] for k in ("family_id", "family_sha256", "source_line", "subject", "level")},
            "selection_seed": SELECTION_SEED,
        }
    )

phase_b.sort(key=lambda x: (x["subject"], x["level"], x["family_id"]))
with (HERE / "phaseB_selection_delta.jsonl").open("w", encoding="utf-8") as f:
    for row in selection_delta:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

# Bind every saved attempt for the seven historical pairs; never use implicit last-line selection.
cut2_candidates = {row["id"]: row for _n, row in read_jsonl(CUT2 / "prep/level5_candidates_en.jsonl")}


def attempts(path: Path):
    out = collections.defaultdict(list)
    for line_no, row in read_jsonl(path):
        out[row["id"]].append({"line": line_no, "record": row, "record_sha256": record_sha(row)})
    return out


problem_attempts = attempts(CUT2 / "out/level5_problems_el.jsonl")
solution_attempts = attempts(CUT2 / "out/level5_solutions_el.jsonl")
manual = {
    "math5_173": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "valid_natural",
        "evidence": "Positive factor pairs of 133 are (1,133) and (7,19); these give square sums 8845 and 205, so 205 is minimal.",
        "notes": [],
    },
    "math5_528": {
        "disposition": "repair",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "one_certain_typo",
        "evidence": "The repeated tail gives c_k=k+1/(k+c_k), hence c_k^2=k^2+1 and sum(k^2,1..11)+11=506+11=517.",
        "notes": ["Replace ‘Πολλασιάζοντας’ with ‘Πολλαπλασιάζοντας’; no mathematical text changes."],
    },
    "math5_534": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "valid_natural",
        "evidence": "There are C(4,2)=6 company pairs and 4×4=16 cross-company handshakes per pair, giving 96.",
        "notes": [],
    },
    "math5_492": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "valid_natural",
        "evidence": "The auxiliary isosceles trapezoid gives EC=2; cosine law gives (DE+1)^2=141; two 5-unit projections yield AB=9+sqrt(141), so p+q=150.",
        "notes": [],
    },
    "math5_488": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "valid_natural",
        "evidence": "Valuation constraints and gcd(m+n,210)=1 force the first deficient prime to be at least 11; exhaustive valuation search below 407 finds no pair, while (m,n)=(286,121) satisfies all conditions.",
        "notes": [],
    },
    "math5_473": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete",
        "greek_verdict": "valid_natural",
        "evidence": "Exact counts for 0..3 substitutions are 1, 121, 13310, and 1317690; their sum is 1331122, congruent to 122 mod 1000.",
        "notes": [],
    },
    "math5_138": {
        "disposition": "keep",
        "mathematical_verdict": "correct_complete_and_repairs_reference_typo",
        "greek_verdict": "valid_natural",
        "evidence": "For x=sin(theta/2) in (0,1), 2x(1-x^2) has equality at x=1/sqrt(3) and maximum 4sqrt(3)/9.",
        "notes": ["The English reference says x=1/3 at one equality step but then uses arcsin(1/sqrt(3)); the Greek candidate correctly uses x=1/sqrt(3)."],
    },
}

bound_pairs = []
adjudications = []
candidate_rows = []
for selected in sorted(phase_a, key=lambda x: x["subject"]):
    cid = selected["cut2_candidate_ids"][0]
    source = math_rows[selected["source_line"] - 1]
    candidate = cut2_candidates[cid]
    pa, sa = problem_attempts[cid], solution_attempts[cid]
    problem_texts = {x["record"]["problem_el"] for x in pa}
    solution_texts = {x["record"]["solution_el"] for x in sa}
    if len(problem_texts) != 1 or len(solution_texts) != 1:
        raise RuntimeError(f"phase-A historical variants conflict for {cid}")
    problem_el = next(iter(problem_texts))
    solution_el = next(iter(solution_texts))
    if controls(problem_el) or controls(solution_el):
        raise RuntimeError(f"phase-A selected variant has disallowed controls for {cid}")
    if pilot_norm(source["problem"]) != pilot_norm(candidate["problem_en"]):
        raise RuntimeError(f"source mismatch for {cid}")
    pair = {
        "row_id": cid,
        "family_id": selected["family_id"],
        "family_sha256": selected["family_sha256"],
        "source": {
            "path": str(MATH),
            "line": selected["source_line"],
            "record_sha256": record_sha(source),
            "record": source,
        },
        "cut2_candidate": {
            "path": str(CUT2 / "prep/level5_candidates_en.jsonl"),
            "id": cid,
            "record_sha256": record_sha(candidate),
            "record": candidate,
        },
        "problem_attempts": {
            "path": str(CUT2 / "out/level5_problems_el.jsonl"),
            "count": len(pa),
            "records": pa,
            "distinct_problem_texts": len(problem_texts),
            "selected_line": pa[0]["line"],
            "selected_record_sha256": pa[0]["record_sha256"],
            "selected_problem_el": problem_el,
        },
        "solution_attempts": {
            "path": str(CUT2 / "out/level5_solutions_el.jsonl"),
            "count": len(sa),
            "records": sa,
            "distinct_solution_texts": len(solution_texts),
            "selected_line": sa[0]["line"],
            "selected_record_sha256": sa[0]["record_sha256"],
            "selected_solution_el": solution_el,
        },
        "selection_rule": "all saved attempts inspected; select only because every saved text variant is identical and contains no decoded disallowed control",
    }
    pair_sha = canonical_sha(pair)
    bound_pairs.append(pair)
    judgement = manual[cid]
    repaired_solution = solution_el.replace("Πολλασιάζοντας", "Πολλαπλασιάζοντας") if cid == "math5_528" else solution_el
    adjudications.append(
        {
            "row_id": cid,
            "family_id": selected["family_id"],
            "subject": selected["subject"],
            "level": selected["level"],
            "bound_pair_record_sha256": pair_sha,
            **judgement,
            "selected_problem_sha256": sha_text(problem_el),
            "selected_solution_before_sha256": sha_text(solution_el),
            "candidate_solution_after_sha256": sha_text(repaired_solution),
            "semantic_change": False,
            "source_reference_disagreement": cid == "math5_138",
            "reviewer": "dialogue_audit Sol agent",
            "review_scope": "full original problem, full reference, all Greek saved variants, complete derivation, answer, and charitable Greek",
        }
    )
    candidate_rows.append(
        {
            "row_id": cid,
            "family_id": selected["family_id"],
            "messages": [
                {"role": "user", "content": problem_el},
                {"role": "assistant", "content": repaired_solution},
            ],
            "disposition": judgement["disposition"],
            "source_line": selected["source_line"],
            "bound_pair_record_sha256": pair_sha,
            "problem_sha256": sha_text(problem_el),
            "solution_sha256": sha_text(repaired_solution),
            "candidate_only_no_source_mutation": True,
        }
    )

for name, data in (("phaseA_bound_pairs.jsonl", bound_pairs), ("phaseA_adjudications.jsonl", adjudications), ("phaseA_candidate_rows.jsonl", candidate_rows)):
    with (HERE / name).open("w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

# Copy the verified generic runner and strict prompt/schema assets byte-for-byte.
for directory in (HERE / "prompts", HERE / "schemas"):
    directory.mkdir(parents=True, exist_ok=True)
shutil.copyfile(PILOT / "run_queue.py", HERE / "run_queue.py")
for name in ("adaptation.txt", "solution_blind.txt", "verification_blind.txt", "greek_correction.txt", "source_review.txt"):
    shutil.copyfile(PILOT / "prompts" / name, HERE / "prompts" / name)
for name in ("adaptation.schema.json", "solution.schema.json", "greek_correction.schema.json", "source_review.schema.json"):
    shutil.copyfile(PILOT / "schemas" / name, HERE / "schemas" / name)

# Freeze phase-B source rows. References remain in inputs for later human comparison,
# but are absent from adaptation, solve, and blind-verification payloads.
inputs = []
for rank, selected in enumerate(phase_b, 1):
    source = math_rows[selected["source_line"] - 1]
    inv = inventory_by_id[selected["family_id"]]
    inputs.append(
        {
            "row_id": f"scaleB_math_line_{selected['source_line']}",
            "family_id": selected["family_id"],
            "family_sha256": selected["family_sha256"],
            "pilot_group": "maths_scale_phaseB_train_probe",
            "selection_rank": rank,
            "selection_revision": selected["selection_revision"],
            "replaces_family_id": selected.get("replaces_family_id"),
            "source_path": str(MATH),
            "source_line": selected["source_line"],
            "source_split": "MATH train",
            "source_license": "MIT (project documentation)",
            "source_record_sha256": record_sha(source),
            "problem_en": source["problem"],
            "problem_el_seed": None,
            "reference_solution": source["solution"],
            "reference_visibility": "frozen_for_post_solve_human_comparison_only; not present in queued payloads",
            "level": selected["level"],
            "subject": selected["subject"],
            "math500_overlap": inv["math500_gate"],
            "diagram_or_figure_dependency": False,
            "current_assembly_exposure": inv["current_assembly"],
            "adaptation_state": "call_required",
            "solution_state": "two_independent_high_calls_required",
        }
    )

with (HERE / "inputs.jsonl").open("w", encoding="utf-8") as f:
    for row in inputs:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

jobs = []
for row in inputs:
    rid = row["row_id"]
    adapt = f"adapt__{rid}"
    jobs.append(
        {
            "job_id": adapt,
            "stage": "adaptation",
            "row_id": rid,
            "model": "gpt-5.6-sol",
            "effort": "high",
            "schema": "schemas/adaptation.schema.json",
            "template": "prompts/adaptation.txt",
            "depends_on": [],
            "payload": {
                "row_id": {"$record": "row_id"},
                "source_identity": {"$record": "source_record_sha256"},
                "source_split": {"$record": "source_split"},
                "level": {"$record": "level"},
                "subject": {"$record": "subject"},
                "problem_text": {"$record": "problem_en"},
            },
        }
    )
    reqs = [
        {"dependency": adapt, "field": "status", "op": "equals", "value": "candidate"},
        {"dependency": adapt, "field": "problem_text", "op": "nonempty_string"},
    ]
    payload = {
        "row_id": {"$record": "row_id"},
        "problem_text": {"$dependency": adapt, "field": "problem_text"},
    }
    jobs.append(
        {
            "job_id": f"solve_high__{rid}",
            "stage": "solution_high",
            "row_id": rid,
            "model": "gpt-5.6-sol",
            "effort": "high",
            "schema": "schemas/solution.schema.json",
            "template": "prompts/solution_blind.txt",
            "depends_on": [adapt],
            "dependency_requirements": reqs,
            "payload": payload,
        }
    )
    jobs.append(
        {
            "job_id": f"verify_high__{rid}",
            "stage": "verification_blind_high",
            "row_id": rid,
            "model": "gpt-5.6-sol",
            "effort": "high",
            "schema": "schemas/solution.schema.json",
            "template": "prompts/verification_blind.txt",
            "depends_on": [adapt],
            "dependency_requirements": reqs,
            "payload": payload,
        }
    )

with (HERE / "queue.jsonl").open("w", encoding="utf-8") as f:
    for row in jobs:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

conditional = {
    "status": "blueprints_only_not_in_primary_queue",
    "shared_source_or_repair_pool": {
        "cap": 8,
        "triggers": [
            "Adaptation reports blocked or a substantive source issue.",
            "Human comparison finds an unresolved mathematical disagreement between the two independent high outputs.",
            "A source-valid repair is frozen under a new problem hash before re-solving.",
        ],
        "source_review": {"template": "prompts/source_review.txt", "schema": "schemas/source_review.schema.json", "model": "gpt-5.6-sol", "effort": "high"},
        "observed_case_escalation": {"template": "prompts/solution_blind.txt", "schema": "schemas/solution.schema.json", "model": "gpt-5.6-sol", "effort": "xhigh"},
        "automatic_xhigh_selection": False,
        "continuation_gate": "Every conditional job is separately instantiated and human-reviewed; the shared eight-call pool cannot be exceeded.",
    },
    "greek_correction": {
        "cap": 14,
        "trigger": "Human semantic comparison accepts the mathematics and identifies a language-only defect.",
        "template": "prompts/greek_correction.txt",
        "schema": "schemas/greek_correction.schema.json",
        "model": "gpt-5.6-sol",
        "effort": "high",
    },
    "retry_cap": 8,
    "instantiation_rule": "Create a separate reviewed queue, preserve the same run-state call ledger, and add its hash to manifest.json before execution. Do not edit queue.jsonl or reset the 72-call cap.",
}
write_json(HERE / "conditional_jobs.json", conditional)

# Review bindings: adaptation prompts can be fully hashed now; dependent prompts bind at runtime.
records = {row["row_id"]: row for row in inputs}
bindings = []
for job in jobs:
    template_path = HERE / job["template"]
    schema_path = HERE / job["schema"]
    binding = {
        "job_id": job["job_id"],
        "row_id": job["row_id"],
        "stage": job["stage"],
        "model": job["model"],
        "effort": job["effort"],
        "job_spec_sha256": canonical_sha(job),
        "input_record_sha256": canonical_sha(records[job["row_id"]]),
        "template_sha256": sha_file(template_path),
        "schema_sha256": sha_file(schema_path),
        "depends_on": job["depends_on"],
        "reference_solution_in_payload": False,
    }
    if not job["depends_on"]:
        record = records[job["row_id"]]
        payload = {
            "row_id": record["row_id"],
            "source_identity": record["source_record_sha256"],
            "source_split": record["source_split"],
            "level": record["level"],
            "subject": record["subject"],
            "problem_text": record["problem_en"],
        }
        prompt = template_path.read_text(encoding="utf-8").replace("{{INPUT_JSON}}", json.dumps(payload, ensure_ascii=False, indent=2))
        binding.update(payload_sha256=canonical_sha(payload), prompt_sha256=sha_text(prompt), runtime_dependency_binding=False)
    else:
        binding.update(payload_sha256=None, prompt_sha256=None, runtime_dependency_binding=True)
    bindings.append(binding)
with (HERE / "payload_bindings.jsonl").open("w", encoding="utf-8") as f:
    for row in bindings:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

preserved = {
    "parent_split_manifest": str(SPLITS),
    "parent_split_manifest_sha256": sha_file(SPLITS),
    "development_identity_digest": canonical_sha(sorted(x["family_id"] for x in split_rows if x["lane"] == "development")),
    "development_count": sum(x["lane"] == "development" for x in split_rows),
    "final_confirmation_identity_digest": canonical_sha(sorted(x["family_id"] for x in split_rows if x["lane"] == "final_confirmation")),
    "final_confirmation_count": sum(x["lane"] == "final_confirmation" for x in split_rows),
    "final_content_read_or_materialized_here": False,
    "final_identity_in_phaseB_inputs": False,
    "train_only_replacements": len(selection_delta),
}
write_json(HERE / "partition_receipt.json", preserved)

report = f"""# Competition-maths stage-one preparation

Prepared locally at `{dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}`. No model subprocess, queue dispatch, production write, GPU allocation, or CSCS job was run.

## Phase A: seven historical Greek Level-5 pairs

Every selected pair was matched to its exact MATH source line and reference solution. All saved Greek problem and solution records were inspected; the full source, full reference, every historical record, line number, record hash, and chosen full text are stored in `phaseA_bound_pairs.jsonl`. Selection never relies on the last record for an ID.

| ID | Subject | Disposition | Finding |
|---|---|---|---|
| math5_173 | Algebra | keep | Complete factor-pair proof; minimum is 205. |
| math5_528 | Intermediate Algebra | repair | Mathematics and 517 are correct; change the single typo `Πολλασιάζοντας` to `Πολλαπλασιάζοντας`. |
| math5_534 | Prealgebra | keep | Complete double-counting proof; 96 handshakes. |
| math5_492 | Geometry | keep | Auxiliary construction, cosine law, and 150 are correct. |
| math5_488 | Number Theory | keep | Valuation lower bound and candidate verification are correct; executable search confirms first pair `(286,121)` at sum 407. |
| math5_473 | Counting & Probability | keep | Ordered substitution recurrence and remainder 122 are correct. |
| math5_138 | Precalculus | keep | Candidate correctly uses `x=1/√3`; the English reference's isolated `x=1/3` equality is a typo contradicted by its own next expression. |

The result is six unchanged keeps and one language-only repair. There are no regenerate or hold decisions. `phaseA_candidate_rows.jsonl` contains the seven review candidates without modifying historical files.

## Phase B: frozen train-only 14-row queue

The earlier proposal contained four problems with an Asymptote or explicit figure dependency. The current pilot's source gate rejects these. `phaseB_selection_delta.jsonl` records four deterministic same-subject, same-level train-only replacements. Development and final-confirmation identities remain unchanged. No final-confirmation problem or solution content was read into or materialized in this bundle.

The primary queue contains exactly:

- 14 high-effort Greek adaptations;
- 14 high-effort blind solves;
- 14 independent high-effort blind verifications.

The solve and verification jobs depend only on the accepted Greek adaptation and do not see each other. Reference solutions are frozen in `inputs.jsonl` for post-solve human comparison but occur in no queued payload. There is no automatic xhigh lane.

The absolute envelope is **72 calls**: 42 primary, at most 14 Greek corrections, a shared maximum of 8 source-review/semantic-repair/observed-case escalation calls, and at most 8 retries. An xhigh solve can be instantiated only for a human-observed unresolved case inside that shared eight-call pool. Conditional jobs require a separate reviewed queue and retain the same cumulative cap.

The copied generic runner is byte-identical to the verified maths-pilot runner, SHA-256 `c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005`. It defaults to plan mode, permits at most eight workers, and requires the explicit execution flag plus its reviewed-payload acknowledgement. Root will review and dispatch after the current Greek dialogue queue; this preparation does not launch it.

## Files

- `phaseA_bound_pairs.jsonl`: complete, explicit source/attempt/selection bindings.
- `phaseA_adjudications.jsonl`: seven full semantic and Greek verdicts.
- `phaseA_candidate_rows.jsonl`: six unchanged candidates and one proposed typo repair.
- `inputs.jsonl`, `queue.jsonl`, `payload_bindings.jsonl`: frozen phase-B inputs and 42 primary jobs.
- `conditional_jobs.json`: shared conditional and retry caps.
- `partition_receipt.json`: preserved development/final identity digests and sealing assertion.
- `manifest.json`: source and artifact hashes.
- `verify_stage1.py`, `verification.json`: executable lineage, queue, mask, and mathematical checks.
"""
(HERE / "report.md").write_text(report, encoding="utf-8")

manifest = {
    "version": 1,
    "status": "prepared_unlaunched_root_review_required",
    "built_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "scope": "seven phase-A full adjudications and fourteen train-only phase-B source generation rows",
    "counts": {
        "phaseA_rows": 7,
        "phaseA_keep": sum(x["disposition"] == "keep" for x in adjudications),
        "phaseA_repair": sum(x["disposition"] == "repair" for x in adjudications),
        "phaseA_regenerate": sum(x["disposition"] == "regenerate" for x in adjudications),
        "phaseA_hold": sum(x["disposition"] == "hold" for x in adjudications),
        "phaseB_rows": 14,
        "adaptation_calls": 14,
        "solution_high_calls": 14,
        "blind_verification_high_calls": 14,
        "primary_calls": 42,
        "conditional_greek_correction_cap": 14,
        "conditional_source_or_repair_shared_cap": 8,
        "retry_cap": 8,
        "absolute_call_cap": 72,
    },
    "execution": {
        "launched": False,
        "default_effort": "high",
        "automatic_xhigh": False,
        "xhigh_gate": "Only a separately reviewed conditional job for an observed unresolved case may use xhigh, inside the shared eight-call source/repair pool.",
        "max_workers": 8,
        "runner_source": str(PILOT / "run_queue.py"),
        "runner_source_sha256": sha_file(PILOT / "run_queue.py"),
        "runner_copy_byte_identical": sha_file(PILOT / "run_queue.py") == sha_file(HERE / "run_queue.py"),
    },
    "source_files": {
        str(MATH): {"sha256": sha_file(MATH), "rows": len(math_rows)},
        str(SPLITS): {"sha256": sha_file(SPLITS), "rows": len(split_rows)},
        str(INVENTORY): {"sha256": sha_file(INVENTORY), "rows": len(inventory)},
        str(CUT2 / "prep/level5_candidates_en.jsonl"): {"sha256": sha_file(CUT2 / "prep/level5_candidates_en.jsonl")},
        str(CUT2 / "out/level5_problems_el.jsonl"): {"sha256": sha_file(CUT2 / "out/level5_problems_el.jsonl")},
        str(CUT2 / "out/level5_solutions_el.jsonl"): {"sha256": sha_file(CUT2 / "out/level5_solutions_el.jsonl")},
    },
    "artifact_sha256": {},
    "notes": [
        "Reference solutions are frozen in inputs for post-solve human comparison but absent from every queued payload.",
        "Solve and verification are independent high-effort jobs depending only on the accepted Greek problem adaptation.",
        "Four train-only phase-B identities were replaced within the same subject/level cells because their source problems trigger the existing pilot diagram/figure dependency gate.",
        "Development and final-confirmation identities are preserved; no final-confirmation problem or solution content is present here.",
    ],
}
assets = [
    "inputs.jsonl", "queue.jsonl", "run_queue.py", "conditional_jobs.json", "payload_bindings.jsonl",
    "phaseB_selection_delta.jsonl", "partition_receipt.json", "phaseA_bound_pairs.jsonl",
    "phaseA_adjudications.jsonl", "phaseA_candidate_rows.jsonl",
    "prompts/adaptation.txt", "prompts/solution_blind.txt", "prompts/verification_blind.txt",
    "prompts/greek_correction.txt", "prompts/source_review.txt", "schemas/adaptation.schema.json",
    "schemas/solution.schema.json", "schemas/greek_correction.schema.json", "schemas/source_review.schema.json",
    "verify_stage1.py", "report.md",
]
manifest["artifact_sha256"] = {name: sha_file(HERE / name) for name in assets}
write_json(HERE / "manifest.json", manifest)
print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
