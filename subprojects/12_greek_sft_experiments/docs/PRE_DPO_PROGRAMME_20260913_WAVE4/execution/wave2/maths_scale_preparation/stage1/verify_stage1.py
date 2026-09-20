#!/usr/bin/env python3
"""Deterministically verify stage-one bindings, arithmetic, and queue guards."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_sha(value) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def read_jsonl(name: str):
    return [json.loads(line) for line in (ROOT / name).read_text().split("\n") if line.strip()]


def factor(n: int) -> dict[int, int]:
    out = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def valuation(n: int, p: int) -> int:
    value = 0
    while n % p == 0:
        value += 1
        n //= p
    return value


def power_divides(m: int, n: int) -> bool:
    """Whether n**n divides m**m, without constructing either power."""
    return all(m * valuation(m, p) >= n * a for p, a in factor(n).items())


def first_number_theory_pairs(limit: int = 407):
    valid = []
    for total in range(2, limit + 1):
        for m in range(1, total):
            n = total - m
            if math.gcd(total, 210) == 1 and m % n != 0 and power_divides(m, n):
                valid.append((m, n, total))
        if valid:
            return valid
    return []


manifest = json.loads((ROOT / "manifest.json").read_text())
inputs = read_jsonl("inputs.jsonl")
queue = read_jsonl("queue.jsonl")
pairs = read_jsonl("phaseA_bound_pairs.jsonl")
adjudications = read_jsonl("phaseA_adjudications.jsonl")
candidates = read_jsonl("phaseA_candidate_rows.jsonl")
deltas = read_jsonl("phaseB_selection_delta.jsonl")
partition = json.loads((ROOT / "partition_receipt.json").read_text())

checks = {}
checks["all_manifest_artifacts_match"] = all(sha_file(ROOT / name) == expected for name, expected in manifest["artifact_sha256"].items())
checks["runner_copy_matches_verified_source"] = manifest["execution"]["runner_copy_byte_identical"] and sha_file(ROOT / "run_queue.py") == "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"
checks["phaseA_counts"] = len(pairs) == len(adjudications) == len(candidates) == 7
checks["phaseA_dispositions"] = {x["row_id"]: x["disposition"] for x in adjudications} == {
    "math5_173": "keep", "math5_528": "repair", "math5_534": "keep", "math5_492": "keep",
    "math5_488": "keep", "math5_473": "keep", "math5_138": "keep",
}
pair_by_id = {x["row_id"]: x for x in pairs}
checks["phaseA_full_pair_bindings"] = all(
    x["bound_pair_record_sha256"] == canonical_sha(pair_by_id[x["row_id"]])
    and x["selected_problem_sha256"] == sha_text(pair_by_id[x["row_id"]]["problem_attempts"]["selected_problem_el"])
    and x["selected_solution_before_sha256"] == sha_text(pair_by_id[x["row_id"]]["solution_attempts"]["selected_solution_el"])
    for x in adjudications
)
checks["phaseA_all_attempts_explicit"] = all(
    p["problem_attempts"]["count"] == len(p["problem_attempts"]["records"])
    and p["solution_attempts"]["count"] == len(p["solution_attempts"]["records"])
    and p["problem_attempts"]["distinct_problem_texts"] == 1
    and p["solution_attempts"]["distinct_solution_texts"] == 1
    for p in pairs
)
candidate_by_id = {x["row_id"]: x for x in candidates}
old_528 = pair_by_id["math5_528"]["solution_attempts"]["selected_solution_el"]
new_528 = candidate_by_id["math5_528"]["messages"][1]["content"]
checks["only_phaseA_text_change_is_exact_typo"] = (
    new_528 == old_528.replace("Πολλασιάζοντας", "Πολλαπλασιάζοντας")
    and old_528.count("Πολλασιάζοντας") == 1
    and all(
        candidate_by_id[rid]["messages"][1]["content"] == pair_by_id[rid]["solution_attempts"]["selected_solution_el"]
        for rid in candidate_by_id if rid != "math5_528"
    )
)

checks["phaseB_14_unique_train_rows"] = len(inputs) == len({x["row_id"] for x in inputs}) == len({x["family_id"] for x in inputs}) == 14
checks["phaseB_queue_42"] = len(queue) == 42
checks["phaseB_stages"] = sorted([sum(x["stage"] == stage for x in queue) for stage in ("adaptation", "solution_high", "verification_blind_high")]) == [14, 14, 14]
checks["phaseB_high_only"] = all(x["effort"] == "high" for x in queue) and "xhigh" not in (ROOT / "queue.jsonl").read_text()
checks["phaseB_no_reference_in_payloads"] = all("reference" not in json.dumps(x["payload"], ensure_ascii=False).lower() for x in queue)
checks["phaseB_independent_solve_verify"] = all(
    x["depends_on"] == ["adapt__" + x["row_id"]] for x in queue if x["stage"] in {"solution_high", "verification_blind_high"}
)
checks["phaseB_no_diagram_dependencies"] = all(x["diagram_or_figure_dependency"] is False for x in inputs) and all(
    not re.search(r"(?i)\\begin\{asy\}|\[asy\]|\b(?:diagram|figure|pictured|shown below|as shown)\b", x["problem_en"])
    for x in inputs
)
checks["phaseB_passes_math500_gate"] = all(not x["math500_overlap"]["reject"] for x in inputs)
checks["phaseB_not_current_train_or_dev"] = all(
    not x["current_assembly_exposure"]["appeared_in_gradient_train"]
    and not x["current_assembly_exposure"]["appeared_in_development"]
    and not x["current_assembly_exposure"]["assembly_excluded_rows"]
    for x in inputs
)
checks["four_same_cell_replacements"] = len(deltas) == 4 and all(d["old"]["subject"] == d["new"]["subject"] and d["old"]["level"] == d["new"]["level"] for d in deltas)
checks["dev_final_preserved_and_sealed"] = (
    partition["development_count"] == 14
    and partition["final_confirmation_count"] == 14
    and partition["final_content_read_or_materialized_here"] is False
    and partition["final_identity_in_phaseB_inputs"] is False
)
checks["call_caps"] = manifest["counts"]["primary_calls"] == 42 and manifest["counts"]["absolute_call_cap"] == 72 and manifest["counts"]["retry_cap"] == 8

# Executable mathematical evidence for every phase-A result.
factor_pairs = [(1, 133), (7, 19)]
square_sums = [((a + b) // 2) ** 2 + ((b - a) // 2) ** 2 for a, b in factor_pairs]
checks["math5_173"] = square_sums == [8845, 205]
checks["math5_528"] = sum(k * k for k in range(1, 12)) + 11 == 517
checks["math5_534"] = math.comb(4, 2) * 4 * 4 == 96
de = math.sqrt(141) - 1
checks["math5_492"] = abs((de * de + 2 * de) - 140) < 1e-12 and 9 + 141 == 150
checks["math5_488"] = first_number_theory_pairs() == [(286, 121, 407)]
sub_counts = [1]
for k in range(1, 4):
    sub_counts.append(11 * (12 - k) * sub_counts[-1])
checks["math5_473"] = sub_counts == [1, 121, 13310, 1317690] and sum(sub_counts) % 1000 == 122
x = 1 / math.sqrt(3)
checks["math5_138"] = abs(2 * x * (1 - x * x) - 4 * math.sqrt(3) / 9) < 1e-12

result = {
    "verified_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).astimezone().isoformat(timespec="seconds"),
    "ok": all(checks.values()),
    "checks": checks,
    "number_theory_first_valid_pairs": first_number_theory_pairs(),
    "substitution_counts": sub_counts,
    "square_sums_by_factor_pair": {"1x133": square_sums[0], "7x19": square_sums[1]},
}
(ROOT / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["ok"] else 1)
