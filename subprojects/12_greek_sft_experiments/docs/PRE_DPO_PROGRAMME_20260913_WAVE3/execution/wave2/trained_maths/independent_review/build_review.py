#!/usr/bin/env python3
"""Freeze the independent semantic adjudication of trained-maths rows."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SEED = "trained-maths-independent-controls-v1"
SEP = "\\0"  # two printable characters, recorded literally in the selection contract


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


rows = {row["row_id"]: row for row in load_jsonl(BASE / "sample.jsonl")}
raw = {}
raw_file = {}
for path in sorted((BASE / "accepted").glob("*.json")):
    for row in json.loads(path.read_text())["rows"]:
        raw[row["row_id"]] = row
        raw_file[row["row_id"]] = path.name

flagged = sorted(row_id for row_id, review in raw.items() if review["overall"] != "no_defect_found")
assert len(flagged) == 13
known_controls = [row_id for row_id, row in rows.items() if row["stratum"] == "known_failure_control"]
assert known_controls == ["gm_nat_618_4", "gm_nat_301_3"]

# One accepted, raw-unflagged row per stratum; choose the row and then twelve strata
# by independent seeded SHA-256 ranks. This makes the control choice reproducible.
best_by_stratum = {}
for row_id, row in rows.items():
    if raw.get(row_id, {}).get("overall") != "no_defect_found" or row["stratum"] == "known_failure_control":
        continue
    stratum = row["stratum"]
    key = (rank(f"{SEED}{SEP}{stratum}{SEP}{row_id}"), row_id)
    if stratum not in best_by_stratum or key < best_by_stratum[stratum][0]:
        best_by_stratum[stratum] = (key, row_id)
selected_strata = sorted(best_by_stratum, key=lambda s: (rank(f"{SEED}{SEP}stratum{SEP}{s}"), s))[:12]
unflagged_controls = [best_by_stratum[stratum][1] for stratum in selected_strata]
assert len(unflagged_controls) == 12 and len(set(unflagged_controls)) == 12

# final_verdict values intentionally separate substantive defects, small local
# improvements, charitable readings, and clean controls.
DECISIONS = {
    "gm_math_1372": {
        "final_verdict": "keep_optional_presentation_polish",
        "correctness": "correct",
        "source_reading": "unambiguous",
        "greek": "valid",
        "editor_effect": "small_language_improvement",
        "finding": "The integer answer 73 and modular reasoning are correct. Writing ν < 10,14 without an approximation mark is imprecise exposition, but because ν is integral it does not admit a wrong integer or invalidate the conclusion. Prefer 71/7 ≈ 10,14 or go directly to ν=10.",
        "raw_adjudication": "narrow",
    },
    "gm_gsm_4161": {
        "final_verdict": "keep_charitable_classroom_reading",
        "correctness": "correct_under_evident_intended_scope",
        "source_reading": "ambiguous_but_resolvable_from_supplied_percentages",
        "greek": "valid",
        "editor_effect": "language_expansion_without_damage",
        "finding": "The literal phrase 'each camper' could imply 96, but the immediately preceding percentages have no purpose unless it means each camper who wants to toast one. Under that ordinary classroom reading, 64×50% + 32×75% = 56 is correct. A prompt clarification would improve strictness but is not required to understand the task.",
        "raw_adjudication": "overturn_repair_requirement",
    },
    "gm_nat_738_1": {
        "final_verdict": "repair_prompt_keep_solution",
        "correctness": "solution_correct_for_table_and_affine_model",
        "source_reading": "internally_conflicting",
        "greek": "grammatical_but_semantically_conflicting",
        "editor_effect": "unchanged",
        "finding": "'Το ίδιο ποσό' makes the visit fee and the per-metre fee equal, whereas the table gives β=90 and α=14. Replace it with a constant charge per metre. The calculation K(x)=14x+90 and x=22 then needs no change.",
        "raw_adjudication": "confirm",
    },
    "gm_math_2231": {
        "final_verdict": "repair_proof_keep_answer",
        "correctness": "answer_correct_with_minor_domain_gap",
        "source_reading": "unambiguous",
        "greek": "valid",
        "editor_effect": "language_improvement",
        "finding": "The value 24 is correct and the example 1·2·3·4 proves maximality. The binomial identity is not defined for every negative starting integer under the ordinary elementary convention. Add a one-line divisibility argument or handle nonpositive blocks; this is a proof-completeness repair, not a wrong result.",
        "raw_adjudication": "confirm_with_scope",
    },
    "gm_nat_618_4": {
        "final_verdict": "repair_output_unit_keep_mathematics",
        "correctness": "calculation_correct_output_unit_not_followed",
        "source_reading": "unambiguous",
        "greek": "valid",
        "editor_effect": "unchanged",
        "finding": "The volume, litre conversion, cost, and rounding are correct. The requested answer is in euro cents, so the final form should be 362 λεπτά rather than 3,62 €. This is a local output-unit defect, not substantive mathematical wrongness.",
        "raw_adjudication": "confirm_with_scope",
    },
    "gm_nat_635_0": {
        "final_verdict": "keep_valid_greek",
        "correctness": "correct",
        "source_reading": "unambiguous_in_context",
        "greek": "valid_but_orthographically_ambiguous",
        "editor_effect": "unchanged",
        "finding": "'Το κατάστημα της έκανε έκπτωση' is readily understood in context as 'the shop gave her a discount'. Accentuation as 'τής' would disambiguate it from a possessive, but the unaccented weak pronoun is common and this is not enough to call the row defective. Arithmetic is correct.",
        "raw_adjudication": "overturn",
    },
    "gm_gsm_4211": {
        "final_verdict": "repair_prompt_before_reuse",
        "correctness": "underdetermined_as_written",
        "source_reading": "missing_time_or_rate_unit",
        "greek": "valid",
        "editor_effect": "unchanged",
        "finding": "The source and Greek prompt give 22 euros per hour but only count three dogs. The step 3×22 needs an unstated one-hour-per-dog assumption. Specify the walking time or change the rate to per dog before retaining 216 €.",
        "raw_adjudication": "confirm",
    },
    "gm_gsm_4140": {
        "final_verdict": "keep_valid_greek",
        "correctness": "correct_under_simple_yield_convention",
        "source_reading": "ordinary_simple_yield_classroom_reading",
        "greek": "both_declined_and_indeclinable_name_forms_are_defensible",
        "editor_effect": "acceptable_variant_no_semantic_damage",
        "finding": "Treating the foreign name Έμμα as indeclinable in 'της Έμμα' is defensible Greek, while 'της Έμμας' is also natural when the name is integrated into Greek declension. The editor changed only the answer, causing a mild style inconsistency, not a language defect or semantic error. The 10 € result is correct under the task's simple annual-return convention.",
        "raw_adjudication": "overturn",
    },
    "gm_gsm_5274": {
        "final_verdict": "keep_optional_presentation_polish",
        "correctness": "correct_magnitude",
        "source_reading": "approximate_rate",
        "greek": "valid",
        "editor_effect": "unchanged",
        "finding": "Ten drops per minute for sixty minutes at 0,05 mL gives about 30 mL. Restoring 'περίπου' in the result would preserve the source precision more explicitly, but omission of the qualifier is a local presentation issue rather than wrong arithmetic.",
        "raw_adjudication": "narrow",
    },
    "gm_gsm_1514": {
        "final_verdict": "repair_prompt_keep_solution",
        "correctness": "solution_correct_for_evident_intended_coreference",
        "source_reading": "ambiguous_pronoun_hardened_the_wrong_way_in_adaptation",
        "greek": "valid",
        "editor_effect": "language_improvement_without_semantic_damage",
        "finding": "The English pronoun is ambiguous, but the only supplied quantity makes Sabrina/Sofia the intended giver of the ten cookies. The Greek prompt instead makes the mother the natural subject of 'είχε δώσει', leaving that amount unknown. Clarify the prompt; the 20−10+5 calculation and final 5 can then remain.",
        "raw_adjudication": "confirm",
    },
    "gm_gsm_4519": {
        "final_verdict": "keep_charitable_classroom_reading",
        "correctness": "correct_under_evident_multiplier_reading",
        "source_reading": "slightly_ambiguous_but_resolvable",
        "greek": "valid",
        "editor_effect": "language_and_precision_improvement",
        "finding": "'Three times later' is loose source wording, but the data and elementary-task form clearly signal a delay three times as large. The editor's 'η καθυστέρηση ... ήταν τριπλάσια' states that interpretation accurately in the solution. The 165-minute answer is suitable to keep.",
        "raw_adjudication": "confirm_keep",
    },
    "gm_gsm_2098": {
        "final_verdict": "repair_adapted_prompt_keep_solution",
        "correctness": "solution_correct_for_source_intent",
        "source_reading": "adaptation_makes_special_extra_car_ambiguous",
        "greek": "valid",
        "editor_effect": "unchanged",
        "finding": "A caboose is a separately counted special car in the source. 'Το τελευταίο βαγόνι του συρμού' sounds like a position and can already be one of the passenger or cargo cars, so subtracting two vehicles is not compelled. State that the engine and one additional service/end car are counted separately; the answer 44 then remains correct.",
        "raw_adjudication": "confirm",
    },
    "gm_math_550": {
        "final_verdict": "keep_concise_proof",
        "correctness": "correct",
        "source_reading": "unambiguous",
        "greek": "valid",
        "editor_effect": "unchanged",
        "finding": "The solution is concise but adequate for the elementary task: five digits can attain sum 11 only as one 3 and four 2s, and placing 3 first maximizes that length. The adjacent observation that five 2s already sum to 10 makes the five-digit bound apparent; adding 'six digits sum to at least 12' would be optional exposition, not a necessary repair.",
        "raw_adjudication": "overturn",
    },
    "gm_nat_301_3": {
        "final_verdict": "repair_local_terminology_keep_mathematics",
        "correctness": "correct",
        "source_reading": "unambiguous",
        "greek": "minor_mathematical_terminology_defect",
        "editor_effect": "unchanged",
        "finding": "The first product 1,2×0,5=0,6 m² is the base area, not 'ένα μέρος του όγκου'. The phrase can be guessed as shorthand for part of the volume calculation, but its stated square-metre unit makes 'Υπολογίζουμε το εμβαδόν της βάσης' the proper local repair. Every later calculation and 360-litre answer is correct.",
        "raw_adjudication": "new_defect_in_unflagged_known_control",
    },
    "gm_nat_16_2": {"final_verdict": "keep_control", "finding": "The LCM argument identifies 216 as the first admissible multiple; the editor fixes an awkward range expression without changing the task.", "editor_effect": "language_improvement"},
    "gm_gsm_3835": {"final_verdict": "keep_control", "finding": "The sector totals 300 and 920 seats are correct; the editor repairs a collocation only.", "editor_effect": "language_improvement"},
    "gm_math_2731": {"final_verdict": "keep_control", "finding": "All three principal roots equal 2 and their product is 8.", "editor_effect": "unchanged"},
    "gm_gsm_3096": {"final_verdict": "keep_control", "finding": "Under the ordinary rate reading, 120 seconds divided by 3 seconds gives 40 sneezes.", "editor_effect": "unchanged"},
    "gm_math_3507": {"final_verdict": "keep_control", "finding": "The slope −2/3 and perpendicular slope 3/2 are correct; the editor improves the Greek term for negative reciprocal.", "editor_effect": "language_improvement"},
    "gm_math_1054": {"final_verdict": "keep_control", "finding": "The sum of squares is 385, exactly divisible by 11, so the remainder is 0.", "editor_effect": "unchanged"},
    "gm_math_1745": {"final_verdict": "keep_control", "finding": "Area gives a lower bound of 100 unit triangles and the standard subdivision attains it; the editor adds a needed article only.", "editor_effect": "language_improvement"},
    "gm_math_3924": {"final_verdict": "keep_control", "finding": "Of the 100 numerator roots, the ten perfect squares through 100 are excluded by the denominator, leaving 90.", "editor_effect": "unchanged"},
    "gm_nat_1080_1": {"final_verdict": "keep_control", "finding": "The tomato cost is 6 €, leaving 12,75 €; division by 8,50 €/kg gives 1,5 kg.", "editor_effect": "unchanged"},
    "gm_math_837": {"final_verdict": "keep_control", "finding": "The inverse-percentage calculation 10,5/0,25=42 ounces is correct and the retained unit does not alter the task.", "editor_effect": "unchanged"},
    "gm_nat_710_2": {"final_verdict": "keep_control", "finding": "The remainder is 3/5 of 174,60 €, namely 104,76 €.", "editor_effect": "unchanged"},
    "gm_math_3807": {"final_verdict": "keep_control", "finding": "The editor correctly replaces the wrong term 'συγγραμμική'; periodicity gives sec(−300°)=sec(60°)=2.", "editor_effect": "semantic_terminology_improvement"},
}

ordered = []
for row_id in flagged + known_controls + unflagged_controls:
    if row_id not in ordered:
        ordered.append(row_id)
assert len(ordered) == 26 and set(ordered) == set(DECISIONS), {
    "ordered_count": len(ordered),
    "decision_count": len(DECISIONS),
    "missing_decisions": sorted(set(ordered) - set(DECISIONS)),
    "unused_decisions": sorted(set(DECISIONS) - set(ordered)),
    "controls": unflagged_controls,
}

records = []
for row_id in ordered:
    row = rows[row_id]
    decision = dict(DECISIONS[row_id])
    scope = (
        "raw_flagged_or_uncertain" if row_id in flagged else
        "targeted_known_failure_control" if row_id in known_controls else
        "deterministic_unflagged_control"
    )
    decision.setdefault("correctness", "correct")
    decision.setdefault("source_reading", "unambiguous")
    decision.setdefault("greek", "valid")
    decision.setdefault("raw_adjudication", "confirm_no_defect")
    record = {
        "row_id": row_id,
        "review_scope": scope,
        "is_raw_flagged_or_uncertain": row_id in flagged,
        "is_targeted_known_failure_control": row_id in known_controls,
        "is_deterministic_unflagged_control": row_id in unflagged_controls,
        "stratum": row["stratum"],
        "raw_audit_overall": raw.get(row_id, {}).get("overall"),
        "raw_audit_file": raw_file.get(row_id),
        **decision,
        "lineage_check": {
            "actual_training_equals_after": row["actual_training_messages"] == row["complete_after_messages"],
            "training_occurrences": row["training_occurrences"],
            "roles": [message["role"] for message in row["actual_training_messages"]],
            "editor_changed": row["editor_changed"],
        },
    }
    records.append(record)

with (HERE / "adjudications.jsonl").open("w") as handle:
    for record in records:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

receipt = {
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "reviewer": "Sol agent",
    "method": "full manual semantic read of originals, before, after, actual training messages, and raw audit for every selected row",
    "additional_model_subprocess_calls": 0,
    "selection_seed": SEED,
    "counts": {"raw_flagged_or_uncertain": len(flagged), "known_failure_control_slots": len(known_controls), "deterministic_unflagged_controls": len(unflagged_controls), "distinct_rows": len(records)},
    "flagged_ids": flagged,
    "known_control_ids": known_controls,
    "unflagged_control_ids": unflagged_controls,
    "unflagged_control_strata": [rows[row_id]["stratum"] for row_id in unflagged_controls],
    "verdict_counts": dict(Counter(record["final_verdict"] for record in records)),
    "lineage": {
        "all_actual_training_equal_after": all(record["lineage_check"]["actual_training_equals_after"] for record in records),
        "all_single_occurrence": all(record["lineage_check"]["training_occurrences"] == 1 for record in records),
        "all_user_then_assistant": all(record["lineage_check"]["roles"] == ["user", "assistant"] for record in records),
    },
    "source_hashes": {
        "sample.jsonl": digest(BASE / "sample.jsonl"),
        "accepted_files": {name: digest(BASE / "accepted" / name) for name in sorted(set(raw_file[row_id] for row_id in ordered if row_id in raw_file))},
    },
    "adjudications_sha256": digest(HERE / "adjudications.jsonl"),
}
(HERE / "verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
