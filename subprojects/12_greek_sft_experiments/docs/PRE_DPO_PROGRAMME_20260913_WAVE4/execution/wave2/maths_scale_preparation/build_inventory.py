#!/usr/bin/env python3
"""Build a read-only MATH-family inventory and proposed disjoint scale split.

This script reads local metadata and text only. It does not call a model, repair
source data, or write anywhere except its own output directory.
"""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
REA = HERE.parents[4]
PROJECT = Path("/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments")
MATH = Path("/Users/foivoskarounos-zamparloukos/sft_annot/math_src/math_train.jsonl")
OPENMATH = Path("/Users/foivoskarounos-zamparloukos/sft_annot/core_export/openmath_gsm_raw.jsonl")
CUT1 = PROJECT / "data/math/cut1/edited/rows_edited.jsonl"
CUT1_SUMMARY = PROJECT / "data/math/cut1/out/summary.json"
CUT2 = PROJECT / "data/math/cut2"
ARM = PROJECT / "data/arms/R3_single"
MATH500 = PROJECT / "data/benchmarks_el/math500/source/test.jsonl"
ASSEMBLER = PROJECT / "data/assemble_mix_r2.py"
PILOT_INPUTS = REA / "outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot/inputs.jsonl"
SEED = "maths-scale-family-split-v1-20260913"


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            if raw.strip():
                yield line_no, json.loads(raw)


def rows(path: Path) -> int:
    return sum(1 for _n, _r in read_jsonl(path))


def pilot_norm(text: str) -> str:
    """Exact pilot normalization from maths_generation_pilot/build_pilot.py."""
    text = unicodedata.normalize("NFD", text).lower()
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def grams_from_norm(normalized: str, n: int) -> set[str]:
    words = normalized.split()
    return {" ".join(words[i : i + n]) for i in range(max(0, len(words) - n + 1))}


def controls(text: str) -> int:
    return sum((ord(c) < 32 and c not in "\t\n\r") or ord(c) == 127 for c in text)


def clean_subject(value: str) -> str:
    return value.replace("_", " ").title().replace(" And ", " & ")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# Load the complete public MATH train inventory and group its eight normalized duplicates.
math_rows = []
by_norm: dict[str, list[dict]] = collections.defaultdict(list)
for line_no, row in read_jsonl(MATH):
    normalized = pilot_norm(row["problem"])
    item = {
        "line": line_no,
        "record_sha256": sha_text(json.dumps(row, ensure_ascii=False, sort_keys=True)),
        "normalized": normalized,
        "level": row.get("level"),
        "subject": clean_subject(row.get("type") or row.get("subject") or ""),
    }
    math_rows.append(item)
    by_norm[normalized].append(item)

# Actual current split membership for all 14,215 Greek maths source IDs.
arm_ids = {}
arm_config_counts = {}
for split in ("train", "dev"):
    ids = set()
    count = 0
    for _line, row in read_jsonl(ARM / f"{split}.jsonl"):
        if row.get("config") == "greek_math":
            ids.add(row["id"])
            count += 1
    arm_ids[split] = ids
    arm_config_counts[split] = count

cut1_by_family: dict[str, list[dict]] = collections.defaultdict(list)
cut1_source_counts = collections.Counter()
cut1_status_counts = collections.Counter()
cut1_unmapped_math_ids = []
for _line, row in read_jsonl(CUT1):
    meta = row.get("meta") or {}
    source = meta.get("src")
    cut1_source_counts[source] += 1
    if row["id"] in arm_ids["train"]:
        status = "gradient_train"
    elif row["id"] in arm_ids["dev"]:
        status = "development"
    else:
        status = "assembly_excluded"
    cut1_status_counts[(source, status)] += 1
    if source == "math":
        normalized = pilot_norm(meta.get("original") or "")
        if normalized not in by_norm:
            cut1_unmapped_math_ids.append(row["id"])
        cut1_by_family[normalized].append({"id": row["id"], "status": status})

# The English assembled maths import is exhaustively metadata-counted and exactly joined.
openmath_source_counts = collections.Counter()
openmath_by_family: dict[str, list[dict]] = collections.defaultdict(list)
for line_no, row in read_jsonl(OPENMATH):
    openmath_source_counts[row.get("problem_source")] += 1
    normalized = pilot_norm(row.get("problem") or "")
    if normalized in by_norm:
        openmath_by_family[normalized].append(
            {"line": line_no, "problem_source": row.get("problem_source"), "source_row": row.get("_row")}
        )

# Cut-2 gives source identities plus append-only attempts. Conflicting attempts remain conflicts.
cut2_candidates: dict[str, dict] = {}
for _line, row in read_jsonl(CUT2 / "prep/level5_candidates_en.jsonl"):
    cut2_candidates[row["id"]] = row


def attempt_index(path: Path, field: str):
    values: dict[str, list[str]] = collections.defaultdict(list)
    bad = collections.Counter()
    for _line, row in read_jsonl(path):
        value = row.get(field) or ""
        values[row["id"]].append(value)
        bad[row["id"]] += controls(value)
    return values, bad


cut2_problem_values, cut2_problem_controls = attempt_index(CUT2 / "out/level5_problems_el.jsonl", "problem_el")
cut2_solution_values, cut2_solution_controls = attempt_index(CUT2 / "out/level5_solutions_el.jsonl", "solution_el")
cut2_by_family: dict[str, list[str]] = collections.defaultdict(list)
for cid, row in cut2_candidates.items():
    cut2_by_family[pilot_norm(row["problem_en"])].append(cid)


def cut2_status(ids: list[str]) -> str:
    if not ids:
        return "not_in_cut2_candidate_set"
    statuses = []
    for cid in ids:
        pv = cut2_problem_values.get(cid, [])
        sv = cut2_solution_values.get(cid, [])
        if not pv:
            statuses.append("source_only_no_problem_output")
        elif not sv:
            statuses.append("problem_only_no_solution_output")
        elif (
            len(set(pv)) == 1
            and len(set(sv)) == 1
            and cut2_problem_controls[cid] == 0
            and cut2_solution_controls[cid] == 0
        ):
            statuses.append("paired_mechanically_clean_nonconflicting")
        else:
            statuses.append("paired_conflicting_or_control")
    return statuses[0] if len(set(statuses)) == 1 else "mixed_cut2_status"


# Pilot membership. “fresh” denotes selection novelty inside that pilot only.
pilot_by_family: dict[str, list[dict]] = collections.defaultdict(list)
cut1_id_to_norm = {x["id"]: n for n, vals in cut1_by_family.items() for x in vals}
for _line, row in read_jsonl(PILOT_INPUTS):
    normalized = pilot_norm(row.get("problem_en") or "")
    source_id = row.get("source_row_id")
    if source_id in cut1_id_to_norm:
        normalized = cut1_id_to_norm[source_id]
    if normalized in by_norm:
        pilot_by_family[normalized].append({"row_id": row["row_id"], "pilot_group": row["pilot_group"]})

# Reproduce the pilot MATH-500 exact / 13-gram / candidate-denominator 8-gram gate.
test_norms = []
post8: dict[str, list[int]] = collections.defaultdict(list)
all13 = set()
for test_i, (_line, row) in enumerate(read_jsonl(MATH500)):
    normalized = pilot_norm(row["problem"])
    test_norms.append(normalized)
    for gram in grams_from_norm(normalized, 8):
        post8[gram].append(test_i)
    all13.update(grams_from_norm(normalized, 13))
test_norm_set = set(test_norms)

inventory = []
for normalized, group in sorted(by_norm.items(), key=lambda kv: min(x["line"] for x in kv[1])):
    canonical = min(group, key=lambda x: x["line"])
    g8 = grams_from_norm(normalized, 8)
    hit_counts = collections.Counter(i for gram in g8 for i in post8.get(gram, []))
    max_share = (max(hit_counts.values(), default=0) / len(g8)) if g8 else 0.0
    any13 = bool(grams_from_norm(normalized, 13) & all13)
    cut = cut1_by_family.get(normalized, [])
    om = openmath_by_family.get(normalized, [])
    pilot = pilot_by_family.get(normalized, [])
    cut2_ids = cut2_by_family.get(normalized, [])
    levels = sorted({x["level"] for x in group})
    subjects = sorted({x["subject"] for x in group})
    item = {
        "family_id": "mathfam_" + sha_text(normalized)[:20],
        "family_sha256": sha_text(normalized),
        "canonical_source_line": canonical["line"],
        "source_lines": [x["line"] for x in group],
        "source_record_sha256s": [x["record_sha256"] for x in group],
        "normalized_duplicate_count": len(group) - 1,
        "level": levels[0] if len(levels) == 1 else None,
        "subject": subjects[0] if len(subjects) == 1 else None,
        "metadata_conflict": len(levels) != 1 or len(subjects) != 1,
        "current_assembly": {
            "greek_source_rows": cut,
            "english_import_exact_rows": om,
            "appeared_in_gradient_train": any(x["status"] == "gradient_train" for x in cut),
            "appeared_in_development": any(x["status"] == "development" for x in cut),
            "assembly_excluded_rows": [x["id"] for x in cut if x["status"] == "assembly_excluded"],
        },
        "cut2": {"candidate_ids": cut2_ids, "asset_status": cut2_status(cut2_ids)},
        "pilot": pilot,
        "math500_gate": {
            "exact_normalized": normalized in test_norm_set,
            "any_13gram": any13,
            "max_share_candidate_8grams_in_one_test_item": round(max_share, 6),
            "reject": normalized in test_norm_set or any13 or max_share > 0.5,
        },
    }
    inventory.append(item)

# Freeze a modest, disjoint source-family option set. Final identities contain no source text.
eligible = [
    x
    for x in inventory
    if not x["metadata_conflict"]
    and x["level"] in {f"Level {i}" for i in range(1, 6)}
    and not x["current_assembly"]["appeared_in_gradient_train"]
    and not x["current_assembly"]["appeared_in_development"]
    and not x["current_assembly"]["assembly_excluded_rows"]
    and not x["pilot"]
    and not x["math500_gate"]["reject"]
]
subjects = [
    "Algebra",
    "Intermediate Algebra",
    "Prealgebra",
    "Geometry",
    "Number Theory",
    "Counting & Probability",
    "Precalculus",
]
used = set()
split_rows = []


def ranked(pool, lane):
    return sorted(pool, key=lambda x: sha_text(f"{SEED}|{lane}|{x['family_id']}"))


def take_one(subject, level, lane, prefer_old=False, forbid_cut2=False):
    pool = [x for x in eligible if x["family_id"] not in used and x["subject"] == subject and x["level"] == level]
    if forbid_cut2:
        pool = [x for x in pool if not x["cut2"]["candidate_ids"]]
    if prefer_old:
        old = [x for x in pool if x["cut2"]["asset_status"] == "paired_mechanically_clean_nonconflicting"]
        if old:
            pool = old
    if not pool:
        raise RuntimeError(f"no candidate for {lane} {subject} {level}")
    item = ranked(pool, lane)[0]
    used.add(item["family_id"])
    split_rows.append(
        {
            "family_id": item["family_id"],
            "family_sha256": item["family_sha256"],
            "source_line": item["canonical_source_line"],
            "subject": subject,
            "level": level,
            "lane": lane,
            "cut2_candidate_ids": item["cut2"]["candidate_ids"],
            "old_greek_asset_status": item["cut2"]["asset_status"],
            "source_text_in_manifest": False,
        }
    )


# Final first, from source-only families, then development; neither is used to develop prompts.
for si, subject in enumerate(subjects):
    for j, level_no in enumerate((((2 * si) % 5) + 1, ((2 * si + 2) % 5) + 1)):
        take_one(subject, f"Level {level_no}", "final_confirmation", forbid_cut2=True)
for si, subject in enumerate(subjects):
    for j, level_no in enumerate((((2 * si + 1) % 5) + 1, ((2 * si + 3) % 5) + 1)):
        take_one(subject, f"Level {level_no}", "development", forbid_cut2=True)

# Stage 1 has one family per subject/level cell; stage 2 adds two more per cell.
for subject in subjects:
    for level_no in range(1, 6):
        take_one(subject, f"Level {level_no}", "train_stage1", prefer_old=(level_no == 5))
for subject in subjects:
    for level_no in range(1, 6):
        take_one(subject, f"Level {level_no}", "train_stage2", prefer_old=(level_no == 5))
        take_one(subject, f"Level {level_no}", "train_stage2", prefer_old=(level_no == 5))

# Execution phases are advisory and deterministic. They do not authorize calls.
probe_ids = set()
for si, subject in enumerate(subjects):
    wanted_levels = {f"Level {(si % 4) + 1}", f"Level {((si + 2) % 4) + 1}"}
    probe_ids.update(
        x["family_id"]
        for x in split_rows
        if x["lane"] == "train_stage1" and x["subject"] == subject and x["level"] in wanted_levels
    )
for row in split_rows:
    if row["lane"] == "train_stage1" and row["old_greek_asset_status"] == "paired_mechanically_clean_nonconflicting":
        row["execution_phase"] = "A_existing_asset_full_review"
    elif row["lane"] == "train_stage1" and row["family_id"] in probe_ids:
        row["execution_phase"] = "B_source_generation_probe14"
    elif row["lane"] == "train_stage1":
        row["execution_phase"] = "C_complete_stage1"
    elif row["lane"] == "development":
        row["execution_phase"] = "C_development_gate"
    elif row["lane"] == "train_stage2":
        row["execution_phase"] = "D_after_stage1_and_quota_gate"
    else:
        row["execution_phase"] = "E_final_only_after_prompt_freeze"

# Write detailed, content-free inventory and split identities.
with (HERE / "math7500_family_inventory.jsonl").open("w", encoding="utf-8") as f:
    for row in inventory:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
with (HERE / "proposed_family_splits.jsonl").open("w", encoding="utf-8") as f:
    for row in split_rows:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

cut2_pair_ids = set(cut2_problem_values) & set(cut2_solution_values)
cut2_clean_ids = {
    cid
    for cid in cut2_pair_ids
    if len(set(cut2_problem_values[cid])) == 1
    and len(set(cut2_solution_values[cid])) == 1
    and cut2_problem_controls[cid] == 0
    and cut2_solution_controls[cid] == 0
}
family_status = collections.Counter()
for x in inventory:
    if x["current_assembly"]["appeared_in_gradient_train"]:
        family_status["gradient_train"] += 1
    if x["current_assembly"]["appeared_in_development"]:
        family_status["development"] += 1
    if x["current_assembly"]["assembly_excluded_rows"]:
        family_status["assembly_excluded"] += 1
    if x["pilot"]:
        family_status["maths_generation_pilot"] += 1
    if x["math500_gate"]["reject"]:
        family_status["math500_gate_reject"] += 1

source_paths = [
    MATH,
    OPENMATH,
    CUT1,
    CUT1_SUMMARY,
    CUT2 / "prep/level5_candidates_en.jsonl",
    CUT2 / "out/level5_problems_el.jsonl",
    CUT2 / "out/level5_solutions_el.jsonl",
    CUT2 / "out/solutions_el.jsonl",
    CUT2 / "out/fidelity_sample.jsonl",
    ARM / "train.jsonl",
    ARM / "dev.jsonl",
    ARM / "receipt.json",
    ARM / "ledger.json",
    ARM / "contamination_ledger_summary.json",
    MATH500,
    ASSEMBLER,
    PILOT_INPUTS,
]
source_manifest = {
    "built_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "scope": "local metadata and small text scans; no model calls or source mutation",
    "files": {
        str(path): {"sha256": sha_file(path), "bytes": path.stat().st_size, **({"rows": rows(path)} if path.suffix == ".jsonl" else {})}
        for path in source_paths
    },
}
write_json(HERE / "source_manifest.json", source_manifest)

arm_receipt = json.loads((ARM / "receipt.json").read_text(encoding="utf-8"))
receipt_blocks = {x["block"]: x for x in arm_receipt["blocks"] if x["block"] in {"greek_math", "openmath_gsm"}}
eligible_by_cell = {
    subject: {
        f"Level {level_no}": sum(x["subject"] == subject and x["level"] == f"Level {level_no}" for x in eligible)
        for level_no in range(1, 6)
    }
    for subject in subjects
}
eligible_clean_cut2_by_subject = {
    subject: sum(
        x["subject"] == subject and x["cut2"]["asset_status"] == "paired_mechanically_clean_nonconflicting"
        for x in eligible
    )
    for subject in subjects
}

summary = {
    "math_train": {
        "rows": len(math_rows),
        "normalized_families": len(inventory),
        "normalized_duplicate_rows": len(math_rows) - len(inventory),
        "levels": dict(collections.Counter(x["level"] for x in math_rows)),
        "subjects": dict(collections.Counter(x["subject"] for x in math_rows)),
    },
    "current_greek_math_source": {
        "rows": sum(cut1_source_counts.values()),
        "by_source": dict(cut1_source_counts),
        "math_rows_by_actual_assembly_status": {
            status: cut1_status_counts[("math", status)] for status in ("gradient_train", "development", "assembly_excluded")
        },
        "unmapped_math_rows": cut1_unmapped_math_ids,
        "actual_arm_config_counts": arm_config_counts,
        "assembly_receipt": receipt_blocks["greek_math"],
    },
    "english_import": {
        "rows": sum(openmath_source_counts.values()),
        "problem_source_counts": dict(openmath_source_counts),
        "exact_math_family_matches": len(openmath_by_family),
        "assembly_receipt": receipt_blocks["openmath_gsm"],
    },
    "family_status_counts_nonexclusive": dict(family_status),
    "cut2_level5_assets": {
        "candidate_ids": len(cut2_candidates),
        "problem_output_ids": len(cut2_problem_values),
        "solution_output_ids": len(cut2_solution_values),
        "paired_ids": len(cut2_pair_ids),
        "paired_mechanically_clean_nonconflicting_ids": len(cut2_clean_ids),
        "paired_ids_requiring_attempt_reconciliation_or_control_repair": len(cut2_pair_ids - cut2_clean_ids),
        "problem_only_ids": len(set(cut2_problem_values) - set(cut2_solution_values)),
        "source_only_ids": len(set(cut2_candidates) - set(cut2_problem_values)),
    },
    "eligible_families_after_current_train_dev_pilot_and_math500_gates": len(eligible),
    "eligible_families_by_subject_level": eligible_by_cell,
    "eligible_mechanically_clean_cut2_level5_by_subject": eligible_clean_cut2_by_subject,
    "proposed_counts": dict(collections.Counter(x["lane"] for x in split_rows)),
    "proposed_old_asset_counts": {
        lane: dict(collections.Counter(x["old_greek_asset_status"] for x in split_rows if x["lane"] == lane))
        for lane in sorted({x["lane"] for x in split_rows})
    },
}
write_json(HERE / "inventory_summary.json", summary)

verification = {
    "ok": True,
    "checks": {
        "math_rows_7500": len(math_rows) == 7500,
        "all_cut1_math_originals_mapped": not cut1_unmapped_math_ids,
        "actual_greek_arm_counts_match_receipt": arm_config_counts == {"train": 14070, "dev": 142},
        "english_import_exhaustive": sum(openmath_source_counts.values()) == 100000,
        "english_import_is_gsm8k_only": openmath_source_counts == {"gsm8k": 100000},
        "split_family_ids_unique": len(split_rows) == len({x["family_id"] for x in split_rows}),
        "split_excludes_current_gradient_train": all(
            not next(i for i in inventory if i["family_id"] == x["family_id"])["current_assembly"]["appeared_in_gradient_train"]
            for x in split_rows
        ),
        "split_excludes_current_development": all(
            not next(i for i in inventory if i["family_id"] == x["family_id"])["current_assembly"]["appeared_in_development"]
            for x in split_rows
        ),
        "split_excludes_pilot": all(not next(i for i in inventory if i["family_id"] == x["family_id"])["pilot"] for x in split_rows),
        "split_passes_math500_gate": all(
            not next(i for i in inventory if i["family_id"] == x["family_id"])["math500_gate"]["reject"] for x in split_rows
        ),
        "final_manifest_contains_no_source_text": all(
            not x["source_text_in_manifest"] for x in split_rows if x["lane"] == "final_confirmation"
        ),
        "train_stage1_one_per_subject_level": all(
            sum(x["lane"] == "train_stage1" and x["subject"] == s and x["level"] == f"Level {lv}" for x in split_rows) == 1
            for s in subjects for lv in range(1, 6)
        ),
        "train_stage2_two_per_subject_level": all(
            sum(x["lane"] == "train_stage2" and x["subject"] == s and x["level"] == f"Level {lv}" for x in split_rows) == 2
            for s in subjects for lv in range(1, 6)
        ),
    },
    "gate_contract": {
        "normalization": "NFD + lowercase + combining-mark removal + non-word replacement + whitespace collapse (exact pilot implementation)",
        "exact": "reject complete normalized equality with a MATH-500 test item",
        "13gram": "reject any shared normalized word 13-gram with MATH-500",
        "8gram": "reject when more than 50% of the candidate MATH-train problem's distinct normalized word 8-grams occur in one MATH-500 item",
        "denominator": "candidate MATH-train problem distinct 8-grams; not test-item 8-grams",
    },
}
verification["ok"] = all(verification["checks"].values())
write_json(HERE / "verification.json", verification)

timestamp = source_manifest["built_at"]
report = f"""# Competition-maths scale source inventory

Built at `{timestamp}` by a local, read-only metadata/text scan. No model subprocess, production transform, source edit, GPU job, or remote job was run.

## What the complete lineage scan establishes

The cached MATH training split has **7,500 rows and 7,492 normalized source families**. Eight rows repeat an existing normalized problem. The current Greek maths source has 14,215 rows: 5,823 translated GSM8K, 3,284 translated MATH, and 5,108 native rows. In the actual assembled split, the MATH portion contributes **3,241 rows / 3,240 families to gradient training**, 40 rows / 40 families to development, and three rows / three families excluded during assembly. One normalized family accounts for two gradient-training rows.

The English `openmath_gsm_raw.jsonl` import was exhaustively scanned: all **100,000** rows declare `problem_source=gsm8k`, and none exactly matches a normalized MATH-train family. Its assembly receipt records 99,971 available after its prior keep-list stage, 29 contamination exclusions, 99,942 taken, 98,943 train, and 999 development rows. This supports a zero exact MATH-family contribution from that named import; it is not a claim about unrelated blocks without MATH lineage metadata.

The 32-row generation pilot contains 29 MATH-family rows and three GSM8K rows. Its 16 `fresh_level5` items are new to that pilot's audited sample selection. None maps to the current Greek MATH train/dev rows, but that does **not** establish that the problems were unseen in pretraining, earlier checkpoints, evaluator development, or any source outside the enumerated assembly lineage.

## Old Greek Level-5 material

Cut 2 names 1,500 Level-5 source candidates. Append-only output files contain 1,457 problem IDs and 1,168 solution IDs, giving 1,168 paired IDs. Only **104 paired IDs** have no decoded disallowed control character and no conflicting saved problem or solution text across attempts. The other 1,064 pairs need attempt reconciliation or control repair; 289 have only a problem output and 43 have no problem output. “Mechanically clean and nonconflicting” is an inventory gate, not semantic or mathematical acceptance.

The proposed training options reuse 21 of the 104 mechanically clean pairs: seven in stage 1 and 14 in stage 2. Every reused pair still requires a full source-fidelity, derivation, answer, Greek, and provenance review before promotion.

## Identity and benchmark gates

Family identity uses the exact normalization already used by the pilot: NFD, lowercase, combining-mark removal, non-word replacement, and whitespace collapse, followed by SHA-256. Candidate source families are rejected for the MATH-500 test when any of these holds:

- complete normalized equality;
- any shared normalized word 13-gram;
- more than 50% of the **candidate MATH-train problem's distinct 8-grams** occur in one test item.

The denominator in the current pilot code is candidate 8-grams. Prose that calls these “test 8-grams” is inaccurate. Across the complete source, 180 normalized families trigger at least one of the MATH-500 gates. The family inventory records the exact result and maximum share for every family.

Assembly decontamination is a separate implementation. It uses NFKC + casefold + word extraction, then drops a training user turn when at least 50% of that candidate turn's distinct 8-grams occur anywhere in the loaded evaluation-gram index. The receipt reports zero matches in final train for the specifically loaded inventories: English originals, Greek MMLU, GSM8K, IFBench-el, IFEval, math500-el, MGSM-el, MultiChallenge-el, four named native sets, XSTest-el, and Ellinika Bench. This audit makes no decontamination claim for omitted datasets, pretraining, selection exposure, or unrecorded sources.

## Frozen family options

The content-free split manifest freezes **133 disjoint family identities** after excluding current train, current development, assembly-excluded rows, all pilot families, ambiguous metadata, and the MATH-500 gates.

| Lane | Families | Coverage | Existing Greek candidates |
|---|---:|---|---:|
| Train stage 1 | 35 | one per 7 subjects × 5 levels | 7 clean Level-5 pairs |
| Train stage 2 | 70 | two additional per subject × level cell | 14 clean Level-5 pairs |
| Development | 14 | two per subject, with levels rotated | 0 |
| Final confirmation | 14 | two per subject, with levels rotated | 0 |

Final-confirmation entries contain identity hash, source line, subject, and level, but no source problem text. Future authoring, reviewer, prompt-development, retry, and selection payloads must exclude those 14 identities and their content. They should be materialized only after prompts and gates are frozen, and their outcomes must not drive another prompt revision.

## Modest execution sequence

The last supplied account observation was **49% weekly quota remaining**; this scan did not refresh it. Given that shared and possibly stale limit, the next scale should stay staged:

1. Fully review the seven existing Greek pairs in phase A without generation. Any semantic or mathematical defect becomes a separately tracked repair; conflicting historical attempts are not silently selected.
2. Run only the 14-family source-generation probe in phase B. Under the prior fresh-row shape—adaptation, high solve, blind verification, and xhigh on half—this is about **49 primary calls**, before separately capped correction or retry work.
3. If that gate passes and the current usage check supports it, complete the remaining 14 stage-1 training families and the 14 development families. The 42 source-only train/development families in the complete stage-1 envelope correspond to about **147 primary calls** under the same shape. Freeze conditional correction and retry caps before dispatch.
4. Defer stage 2, which adds 70 families, until stage-1 quality and a fresh quota check justify it. It includes 14 old Greek pairs and 56 source-only families.
5. Generate and review the 14 final-confirmation families only after prompt freeze. Their approximately 49 primary calls are outside development and selection.

All local inventory work is appropriate on the Mac. Any bulk materialization, corpus-wide transformation, or larger batch assembly should be routed to CSCS with its own source hashes and receipts. This report prepares options only; it does not launch or authorize generation.

## Artifacts

- `math7500_family_inventory.jsonl`: all 7,492 normalized families, content-free identity and lineage flags.
- `proposed_family_splits.jsonl`: the 133 disjoint options and execution phases, without problem text.
- `source_manifest.json`: exact input hashes, sizes, and JSONL row counts.
- `inventory_summary.json`: checkable aggregate counts and source receipts.
- `verification.json`: executable gate and split invariants.
- `build_inventory.py`: deterministic builder.
"""
(HERE / "report.md").write_text(report, encoding="utf-8")

artifacts = ["build_inventory.py", "math7500_family_inventory.jsonl", "proposed_family_splits.jsonl", "source_manifest.json", "inventory_summary.json", "verification.json", "report.md"]
write_json(HERE / "artifact_hashes.json", {name: sha_file(HERE / name) for name in artifacts})

if not verification["ok"]:
    raise SystemExit("verification failed")
print(json.dumps(summary, ensure_ascii=False, indent=2))
